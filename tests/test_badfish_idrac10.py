#!/usr/bin/env python3
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from badfish.main import Badfish
from badfish.helpers.exceptions import BadfishException

HOST_URI = "https://mgmt-host.example.com"
REDFISH_URI = "/redfish/v1"
SYSTEM_RESOURCE = "/redfish/v1/Systems/System.Embedded.1"
MANAGER_RESOURCE = "/redfish/v1/Managers/iDRAC.Embedded.1"
MANAGER_VM = "%s/VirtualMedia" % MANAGER_RESOURCE
SYSTEM_VM = "%s/VirtualMedia" % SYSTEM_RESOURCE
MEMBER_CD = "%s/CD" % MANAGER_VM
MEMBER_REMOVABLE = "%s/RemovableDisk" % MANAGER_VM
MEMBER_ONE = "%s/1" % SYSTEM_VM
MEMBER_TWO = "%s/2" % SYSTEM_VM
OEM_OSD = "%s/Oem/Dell/DellOSDeploymentService" % SYSTEM_RESOURCE
LEGACY_OSD = "%s/Dell/Systems/System.Embedded.1/DellOSDeploymentService" % REDFISH_URI
OPTICAL_MEDIA_TYPES = ["CD", "DVD", "USBStick"]


def url(path):
    return "%s%s" % (HOST_URI, path)


def make_response(status=200, payload=None):
    response = MagicMock()
    response.status = status
    response.headers = {}
    response.text = AsyncMock(return_value=json.dumps(payload if payload is not None else {}))
    return response


def router(responses, default_status=404):
    """Return a side effect resolving request URIs against a response map."""

    def _resolve(uri, *args, **kwargs):
        if uri in responses:
            return responses[uri]
        return make_response(default_status, {"error": {"code": "Base.1.18.GeneralError"}})

    return _resolve


def media_collection(*members):
    return {"Members": [{"@odata.id": member} for member in members]}


@pytest.fixture
def badfish_instance():
    badfish = Badfish("mgmt-host.example.com", "r1", "u1", MagicMock(), 3, _loop=MagicMock())
    badfish.system_resource = SYSTEM_RESOURCE
    badfish.manager_resource = MANAGER_RESOURCE
    badfish.vendor = "Dell"
    return badfish


class TestIsOpticalMedia:
    def test_matches_by_id(self):
        assert Badfish.is_optical_media("CD") is True

    def test_ignores_removable_disk(self):
        assert Badfish.is_optical_media("RemovableDisk") is False

    def test_matches_by_media_types(self):
        assert Badfish.is_optical_media("1", OPTICAL_MEDIA_TYPES) is True

    def test_ignores_usb_only_media_types(self):
        assert Badfish.is_optical_media("2", ["USBStick"]) is False

    def test_ignores_numeric_id_without_media_types(self):
        assert Badfish.is_optical_media("1") is False


class TestFindVirtualMediaResource:
    @pytest.mark.asyncio
    async def test_manager_resource(self, badfish_instance):
        badfish_instance.get_request = AsyncMock(side_effect=router({url(MANAGER_VM): make_response()}))

        assert await badfish_instance.find_virtual_media_resource() == MANAGER_VM

    @pytest.mark.asyncio
    async def test_falls_back_to_system_resource(self, badfish_instance):
        badfish_instance.get_request = AsyncMock(side_effect=router({url(SYSTEM_VM): make_response()}))

        assert await badfish_instance.find_virtual_media_resource() == SYSTEM_VM

    @pytest.mark.asyncio
    async def test_supermicro_resource(self, badfish_instance):
        badfish_instance.vendor = "Supermicro"
        vm1 = "%s/VM1" % MANAGER_RESOURCE
        badfish_instance.get_request = AsyncMock(side_effect=router({url(vm1): make_response()}))

        assert await badfish_instance.find_virtual_media_resource() == vm1

    @pytest.mark.asyncio
    async def test_cached_resource(self, badfish_instance):
        badfish_instance.virtual_media_resource = SYSTEM_VM
        badfish_instance.get_request = AsyncMock()

        assert await badfish_instance.find_virtual_media_resource() == SYSTEM_VM
        badfish_instance.get_request.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_resource_found(self, badfish_instance):
        badfish_instance.get_request = AsyncMock(side_effect=router({}))

        with pytest.raises(BadfishException):
            await badfish_instance.find_virtual_media_resource()


class TestGetVirtualMediaDevice:
    @pytest.mark.asyncio
    async def test_device_by_name(self, badfish_instance):
        badfish_instance.get_request = AsyncMock()

        assert await badfish_instance.get_virtual_media_device([MEMBER_REMOVABLE, MEMBER_CD]) == MEMBER_CD
        badfish_instance.get_request.assert_not_called()

    @pytest.mark.asyncio
    async def test_device_by_media_types(self, badfish_instance):
        member_data = make_response(payload={"Id": "1", "MediaTypes": OPTICAL_MEDIA_TYPES})
        badfish_instance.get_request = AsyncMock(side_effect=router({url(MEMBER_ONE): member_data}))

        assert await badfish_instance.get_virtual_media_device([MEMBER_ONE, MEMBER_TWO]) == MEMBER_ONE

    @pytest.mark.asyncio
    async def test_no_optical_device(self, badfish_instance):
        member_data = make_response(payload={"Id": "1", "MediaTypes": ["USBStick"]})
        badfish_instance.get_request = AsyncMock(side_effect=router({url(MEMBER_ONE): member_data}))

        with pytest.raises(BadfishException):
            await badfish_instance.get_virtual_media_device([MEMBER_ONE])

    @pytest.mark.asyncio
    async def test_device_invalid_json_raises(self, badfish_instance):
        member_data = make_response(payload={"Id": "1", "MediaTypes": ["USBStick"]})
        member_data.text = AsyncMock(return_value="{not json")
        badfish_instance.get_request = AsyncMock(side_effect=router({url(MEMBER_ONE): member_data}))

        with pytest.raises(BadfishException):
            await badfish_instance.get_virtual_media_device([MEMBER_ONE])


class TestVirtualMediaActions:
    @pytest.mark.asyncio
    async def test_check_virtual_media_numeric_ids(self, badfish_instance):
        badfish_instance.virtual_media_resource = SYSTEM_VM
        responses = {
            url(SYSTEM_VM): make_response(payload=media_collection(MEMBER_ONE, MEMBER_TWO)),
            url(MEMBER_ONE): make_response(payload={"Id": "1", "Inserted": True, "MediaTypes": OPTICAL_MEDIA_TYPES}),
            url(MEMBER_TWO): make_response(payload={"Id": "2", "Inserted": False, "MediaTypes": OPTICAL_MEDIA_TYPES}),
        }
        badfish_instance.get_request = AsyncMock(side_effect=router(responses))

        assert await badfish_instance.check_virtual_media() is True

    @pytest.mark.asyncio
    async def test_unmount_virtual_media_numeric_ids(self, badfish_instance):
        badfish_instance.virtual_media_resource = SYSTEM_VM
        responses = {
            url(SYSTEM_VM): make_response(payload=media_collection(MEMBER_ONE, MEMBER_TWO)),
            url(MEMBER_ONE): make_response(payload={"Id": "1", "MediaTypes": OPTICAL_MEDIA_TYPES}),
        }
        badfish_instance.get_request = AsyncMock(side_effect=router(responses))
        badfish_instance.post_request = AsyncMock(return_value=make_response(status=204))

        assert await badfish_instance.unmount_virtual_media() is True
        assert badfish_instance.post_request.call_args[0][0] == url("%s/Actions/VirtualMedia.EjectMedia" % MEMBER_ONE)

    @pytest.mark.asyncio
    async def test_mount_virtual_media_numeric_ids(self, badfish_instance):
        badfish_instance.virtual_media_resource = SYSTEM_VM
        responses = {
            url(SYSTEM_VM): make_response(payload=media_collection(MEMBER_ONE, MEMBER_TWO)),
            url(MEMBER_ONE): make_response(payload={"Id": "1", "MediaTypes": OPTICAL_MEDIA_TYPES}),
        }
        badfish_instance.get_request = AsyncMock(side_effect=router(responses))
        badfish_instance.post_request = AsyncMock(return_value=make_response(status=204))

        assert await badfish_instance.mount_virtual_media("http://example.com/boot.iso") is True
        assert badfish_instance.post_request.call_args[0][0] == url("%s/Actions/VirtualMedia.InsertMedia" % MEMBER_ONE)


class TestOsDeploymentResource:
    @pytest.mark.asyncio
    async def test_oem_resource(self, badfish_instance):
        badfish_instance.get_request = AsyncMock(side_effect=router({url(OEM_OSD): make_response()}))

        assert await badfish_instance.find_os_deployment_resource() == OEM_OSD

    @pytest.mark.asyncio
    async def test_falls_back_to_legacy_resource(self, badfish_instance):
        badfish_instance.get_request = AsyncMock(side_effect=router({url(LEGACY_OSD): make_response()}))

        assert await badfish_instance.find_os_deployment_resource() == LEGACY_OSD

    @pytest.mark.asyncio
    async def test_resources_follow_discovered_system_id(self, badfish_instance):
        badfish_instance.system_resource = "/redfish/v1/Systems/System.Embedded.2"
        legacy = "%s/Dell/Systems/System.Embedded.2/DellOSDeploymentService" % REDFISH_URI
        badfish_instance.get_request = AsyncMock(side_effect=router({url(legacy): make_response()}))

        assert await badfish_instance.find_os_deployment_resource() == legacy

    @pytest.mark.asyncio
    async def test_cached_resource(self, badfish_instance):
        badfish_instance.os_deployment_resource = OEM_OSD
        badfish_instance.get_request = AsyncMock()

        assert await badfish_instance.find_os_deployment_resource() == OEM_OSD
        badfish_instance.get_request.assert_not_called()

    @pytest.mark.asyncio
    async def test_unsupported_resource(self, badfish_instance):
        badfish_instance.get_request = AsyncMock(side_effect=router({}))

        assert await badfish_instance.find_os_deployment_resource() is None
        assert await badfish_instance.check_os_deployment_support() is False

    @pytest.mark.asyncio
    async def test_detach_remote_image_uses_resolved_resource(self, badfish_instance):
        badfish_instance.get_request = AsyncMock(side_effect=router({url(OEM_OSD): make_response()}))
        badfish_instance.post_request = AsyncMock(return_value=make_response())

        assert await badfish_instance.detach_remote_image() is True
        expected = url("%s/Actions/DellOSDeploymentService.DetachISOImage" % OEM_OSD)
        assert badfish_instance.post_request.call_args[0][0] == expected

    @pytest.mark.asyncio
    async def test_check_remote_image_uses_resolved_resource(self, badfish_instance):
        badfish_instance.get_request = AsyncMock(side_effect=router({url(OEM_OSD): make_response()}))
        badfish_instance.post_request = AsyncMock(return_value=make_response(payload={"ISOAttachStatus": "Attached"}))

        assert await badfish_instance.check_remote_image() is True
        expected = url("%s/Actions/DellOSDeploymentService.GetAttachStatus" % OEM_OSD)
        assert badfish_instance.post_request.call_args[0][0] == expected

    @pytest.mark.asyncio
    async def test_boot_remote_image_uses_resolved_resource(self, badfish_instance):
        task = "%s/TaskService/Tasks/JID_123" % REDFISH_URI
        responses = {
            url(OEM_OSD): make_response(),
            url(task): make_response(payload={"TaskStatus": "OK"}),
        }
        badfish_instance.get_request = AsyncMock(side_effect=router(responses))
        boot_response = make_response(status=202)
        boot_response.headers = {"Location": task}
        badfish_instance.post_request = AsyncMock(return_value=boot_response)

        assert await badfish_instance.boot_remote_image("server:/path/to.iso") is True
        expected = url("%s/Actions/DellOSDeploymentService.BootToNetworkISO" % OEM_OSD)
        assert badfish_instance.post_request.call_args[0][0] == expected
