#!/usr/bin/env python3
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from badfish.main import Badfish
from badfish.helpers.exceptions import BadfishException, ResourceNotFound

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

BOOT_SOURCES = "%s/BootSources" % SYSTEM_RESOURCE
OEM_BOOT_SOURCES = "%s/Oem/Dell/DellBootSources" % SYSTEM_RESOURCE
BOOT_SOURCES_SETTINGS = "%s/Settings" % OEM_BOOT_SOURCES
UEFI_BOOT_SEQ = [
    {"Index": 0, "Name": "NIC.PxeDevice.1-1", "Enabled": True, "Id": "id-1"},
    {"Index": 1, "Name": "RAID.SL.1-2", "Enabled": True, "Id": "id-2"},
    {"Index": 2, "Name": "NIC.PxeDevice.2-1", "Enabled": True, "Id": "id-3"},
]
BOOT_SOURCES_RESP = {"Attributes": {"UefiBootSeq": UEFI_BOOT_SEQ}}

JOBS = "%s/Jobs" % MANAGER_RESOURCE
OEM_JOBS = "%s/Oem/Dell/Jobs" % MANAGER_RESOURCE
DELL_JOB_SERVICE_LEGACY = "%s/Dell/Managers/iDRAC.Embedded.1/DellJobService" % REDFISH_URI
OEM_DELL_JOB_SERVICE = "%s/Oem/Dell/DellJobService" % MANAGER_RESOURCE
DELL_LC_SERVICE_LEGACY = "%s/Dell/Managers/iDRAC.Embedded.1/DellLCService" % REDFISH_URI
OEM_DELL_LC_SERVICE = "%s/Oem/Dell/DellLCService" % MANAGER_RESOURCE
NA_SYSTEM = "%s/NetworkAdapters" % SYSTEM_RESOURCE
NA_CHASSIS = "%s/Chassis/System.Embedded.1/NetworkAdapters" % REDFISH_URI
JOB_ID = "JID_123"


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


class TestFindBootSourcesResource:
    @pytest.mark.asyncio
    async def test_idrac9_boot_sources(self, badfish_instance):
        badfish_instance.get_request = AsyncMock(side_effect=router({url(BOOT_SOURCES): make_response()}))

        assert await badfish_instance.find_boot_sources_resource() == BOOT_SOURCES

    @pytest.mark.asyncio
    async def test_idrac10_falls_back_to_oem(self, badfish_instance):
        badfish_instance.get_request = AsyncMock(side_effect=router({url(OEM_BOOT_SOURCES): make_response()}))

        assert await badfish_instance.find_boot_sources_resource() == OEM_BOOT_SOURCES

    @pytest.mark.asyncio
    async def test_cached_resource(self, badfish_instance):
        badfish_instance.boot_sources_resource = OEM_BOOT_SOURCES
        badfish_instance.get_request = AsyncMock()

        assert await badfish_instance.find_boot_sources_resource() == OEM_BOOT_SOURCES
        badfish_instance.get_request.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_resource_found(self, badfish_instance):
        badfish_instance.get_request = AsyncMock(side_effect=router({}))

        with pytest.raises(BadfishException):
            await badfish_instance.find_boot_sources_resource()


class TestGetBootDevicesIdrac10:
    @pytest.mark.asyncio
    async def test_reads_uefi_boot_seq_from_oem_resource(self, badfish_instance):
        badfish_instance.get_boot_seq = AsyncMock(return_value="UefiBootSeq")
        badfish_instance.get_request = AsyncMock(
            side_effect=router({url(OEM_BOOT_SOURCES): make_response(payload=BOOT_SOURCES_RESP)})
        )

        await badfish_instance.get_boot_devices()

        assert badfish_instance.boot_devices == UEFI_BOOT_SEQ
        assert badfish_instance.boot_sources_resource == OEM_BOOT_SOURCES

    @pytest.mark.asyncio
    async def test_raises_when_no_boot_sources_supported(self, badfish_instance):
        badfish_instance.get_boot_seq = AsyncMock(return_value="UefiBootSeq")
        badfish_instance.get_request = AsyncMock(side_effect=router({}))

        with pytest.raises(BadfishException):
            await badfish_instance.get_boot_devices()


class TestPatchBootSeqIdrac10:
    @pytest.mark.asyncio
    async def test_patches_oem_settings_resource(self, badfish_instance):
        badfish_instance.get_boot_seq = AsyncMock(return_value="UefiBootSeq")
        badfish_instance.get_request = AsyncMock(side_effect=router({url(OEM_BOOT_SOURCES): make_response()}))
        badfish_instance.patch_request = AsyncMock(return_value=make_response(status=200))

        await badfish_instance.patch_boot_seq(UEFI_BOOT_SEQ)

        expected = url(BOOT_SOURCES_SETTINGS)
        assert badfish_instance.patch_request.call_args[0][0] == expected
        assert badfish_instance.patch_request.call_args[0][1] == {"Attributes": {"UefiBootSeq": UEFI_BOOT_SEQ}}
        assert badfish_instance.boot_sources_resource == OEM_BOOT_SOURCES
        assert badfish_instance.patch_request.await_count == 1

    @pytest.mark.asyncio
    async def test_accepts_204_no_content_as_success(self, badfish_instance):
        badfish_instance.get_boot_seq = AsyncMock(return_value="UefiBootSeq")
        badfish_instance.get_request = AsyncMock(side_effect=router({url(OEM_BOOT_SOURCES): make_response()}))
        badfish_instance.patch_request = AsyncMock(return_value=make_response(status=204))
        badfish_instance.error_handler = AsyncMock()

        await badfish_instance.patch_boot_seq(UEFI_BOOT_SEQ)

        badfish_instance.error_handler.assert_not_called()
        assert badfish_instance.patch_request.await_count == 1

    @pytest.mark.asyncio
    async def test_accepts_202_accepted_as_success(self, badfish_instance):
        badfish_instance.get_boot_seq = AsyncMock(return_value="UefiBootSeq")
        badfish_instance.get_request = AsyncMock(side_effect=router({url(OEM_BOOT_SOURCES): make_response()}))
        badfish_instance.patch_request = AsyncMock(return_value=make_response(status=202))
        badfish_instance.error_handler = AsyncMock()

        await badfish_instance.patch_boot_seq(UEFI_BOOT_SEQ)

        badfish_instance.error_handler.assert_not_called()
        assert badfish_instance.patch_request.await_count == 1


class TestFindJobsResource:
    @pytest.mark.asyncio
    async def test_idrac9_jobs(self, badfish_instance):
        badfish_instance.get_request = AsyncMock(side_effect=router({url(JOBS): make_response()}))

        assert await badfish_instance.find_jobs_resource() == JOBS

    @pytest.mark.asyncio
    async def test_idrac10_falls_back_to_oem(self, badfish_instance):
        badfish_instance.get_request = AsyncMock(side_effect=router({url(OEM_JOBS): make_response()}))

        assert await badfish_instance.find_jobs_resource() == OEM_JOBS

    @pytest.mark.asyncio
    async def test_cached_resource(self, badfish_instance):
        badfish_instance.jobs_resource = OEM_JOBS
        badfish_instance.get_request = AsyncMock()

        assert await badfish_instance.find_jobs_resource() == OEM_JOBS
        badfish_instance.get_request.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_resource_found(self, badfish_instance):
        badfish_instance.get_request = AsyncMock(side_effect=router({}))

        with pytest.raises(BadfishException):
            await badfish_instance.find_jobs_resource()


class TestFindDellJobServiceResource:
    @pytest.mark.asyncio
    async def test_idrac9_legacy(self, badfish_instance):
        badfish_instance.get_request = AsyncMock(side_effect=router({url(DELL_JOB_SERVICE_LEGACY): make_response()}))

        assert await badfish_instance.find_dell_job_service_resource() == DELL_JOB_SERVICE_LEGACY

    @pytest.mark.asyncio
    async def test_idrac10_oem(self, badfish_instance):
        badfish_instance.get_request = AsyncMock(side_effect=router({url(OEM_DELL_JOB_SERVICE): make_response()}))

        assert await badfish_instance.find_dell_job_service_resource() == OEM_DELL_JOB_SERVICE

    @pytest.mark.asyncio
    async def test_no_resource_found(self, badfish_instance):
        badfish_instance.get_request = AsyncMock(side_effect=router({}))

        with pytest.raises(BadfishException):
            await badfish_instance.find_dell_job_service_resource()


class TestFindDellLCServiceResource:
    @pytest.mark.asyncio
    async def test_idrac9_legacy(self, badfish_instance):
        badfish_instance.get_request = AsyncMock(side_effect=router({url(DELL_LC_SERVICE_LEGACY): make_response()}))

        assert await badfish_instance.find_dell_lc_service_resource() == DELL_LC_SERVICE_LEGACY

    @pytest.mark.asyncio
    async def test_idrac10_oem(self, badfish_instance):
        badfish_instance.get_request = AsyncMock(side_effect=router({url(OEM_DELL_LC_SERVICE): make_response()}))

        assert await badfish_instance.find_dell_lc_service_resource() == OEM_DELL_LC_SERVICE

    @pytest.mark.asyncio
    async def test_no_resource_found(self, badfish_instance):
        badfish_instance.get_request = AsyncMock(side_effect=router({}))

        with pytest.raises(BadfishException):
            await badfish_instance.find_dell_lc_service_resource()


class TestFindNetworkAdaptersResource:
    @pytest.mark.asyncio
    async def test_idrac9_system(self, badfish_instance):
        badfish_instance.get_request = AsyncMock(side_effect=router({url(NA_SYSTEM): make_response()}))

        assert await badfish_instance.find_network_adapters_resource() == NA_SYSTEM

    @pytest.mark.asyncio
    async def test_idrac10_chassis(self, badfish_instance):
        badfish_instance.get_request = AsyncMock(side_effect=router({url(NA_CHASSIS): make_response()}))

        assert await badfish_instance.find_network_adapters_resource() == NA_CHASSIS

    @pytest.mark.asyncio
    async def test_cached_resource(self, badfish_instance):
        badfish_instance.network_adapters_resource = NA_CHASSIS
        badfish_instance.get_request = AsyncMock()

        assert await badfish_instance.find_network_adapters_resource() == NA_CHASSIS
        badfish_instance.get_request.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_resource_found(self, badfish_instance):
        badfish_instance.get_request = AsyncMock(side_effect=router({}))

        with pytest.raises(BadfishException):
            await badfish_instance.find_network_adapters_resource()

    @pytest.mark.asyncio
    async def test_raises_on_auth_error(self, badfish_instance):
        badfish_instance.get_request = AsyncMock(side_effect=router({url(NA_SYSTEM): make_response(status=403)}))

        with pytest.raises(BadfishException):
            await badfish_instance.find_network_adapters_resource()
        badfish_instance.get_request.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_raises_on_server_error(self, badfish_instance):
        badfish_instance.get_request = AsyncMock(side_effect=router({url(NA_SYSTEM): make_response(status=500)}))

        with pytest.raises(BadfishException):
            await badfish_instance.find_network_adapters_resource()
        badfish_instance.get_request.assert_awaited_once()


class TestCreateBiosConfigJobIdrac10:
    @pytest.mark.asyncio
    async def test_posts_to_oem_jobs_resource(self, badfish_instance):
        badfish_instance.get_request = AsyncMock(side_effect=router({url(OEM_JOBS): make_response()}))
        badfish_instance.post_request = AsyncMock(return_value=make_response(status=200, payload={"JobID": JOB_ID}))
        badfish_instance._extract_job_id_from_response = MagicMock(return_value=JOB_ID)

        result = await badfish_instance.create_bios_config_job("/Oem/Dell/DellBootSources/Settings")

        assert result == JOB_ID
        assert badfish_instance.post_request.call_args[0][0] == url(OEM_JOBS)
        assert badfish_instance.post_request.call_args[0][1] == {
            "TargetSettingsURI": "/redfish/v1/Oem/Dell/DellBootSources/Settings"
        }

    @pytest.mark.asyncio
    async def test_accepts_201_created(self, badfish_instance):
        # Dell Redfish returns 201 Created when a job is accepted.
        badfish_instance.get_request = AsyncMock(side_effect=router({url(OEM_JOBS): make_response()}))
        badfish_instance.post_request = AsyncMock(return_value=make_response(status=201, payload={"JobID": JOB_ID}))
        badfish_instance._extract_job_id_from_response = MagicMock(return_value=JOB_ID)

        result = await badfish_instance.create_bios_config_job("/Oem/Dell/DellBootSources/Settings")

        assert result == JOB_ID


class TestGetIdracFwVersionIdrac10:
    @pytest.mark.asyncio
    async def test_detects_idrac10_from_17g_model(self, badfish_instance):
        badfish_instance.get_request = AsyncMock(
            side_effect=router(
                {
                    url(MANAGER_RESOURCE + "/"): make_response(
                        payload={"FirmwareVersion": "1.30.30.52", "Model": "17G Monolithic"}
                    )
                }
            )
        )

        version = await badfish_instance.get_idrac_fw_version()

        assert version == 1303052
        assert badfish_instance._idrac10 is True

    @pytest.mark.asyncio
    async def test_nic_attribute_registry_allows_idrac10(self, badfish_instance):
        badfish_instance.get_request = AsyncMock(
            side_effect=router(
                {
                    url(MANAGER_RESOURCE + "/"): make_response(
                        payload={"FirmwareVersion": "1.30.30.52", "Model": "17G Monolithic"}
                    ),
                    url(
                        "/redfish/v1/Registries/NetworkAttributesRegistry_NIC.Slot.4-1-1/"
                        "NetworkAttributesRegistry_NIC.Slot.4-1-1.json"
                    ): make_response(payload={"RegistryEntries": {"Attributes": [{"AttributeName": "WakeOnLan"}]}}),
                }
            )
        )

        registry = await badfish_instance.get_nic_attribute_registry("NIC.Slot.4-1-1")

        assert registry == [{"AttributeName": "WakeOnLan"}]


class TestBootSeqFallback:
    @pytest.mark.asyncio
    async def test_reads_uefi_boot_seq_when_bootseq_empty(self, badfish_instance):
        # Simulate the BootMode read failing and badfish assuming Bios, so
        # get_boot_seq() picks "BootSeq", which is empty on a UEFI host.
        badfish_instance.boot_mode_readable = False
        badfish_instance.get_boot_seq = AsyncMock(return_value="BootSeq")
        badfish_instance.get_request = AsyncMock(
            side_effect=router(
                {
                    url(OEM_BOOT_SOURCES): make_response(
                        payload={"Attributes": {"BootSeq": [], "UefiBootSeq": UEFI_BOOT_SEQ}}
                    )
                }
            )
        )

        await badfish_instance.get_boot_devices()

        assert badfish_instance.boot_seq_attr == "UefiBootSeq"
        assert badfish_instance.boot_devices == UEFI_BOOT_SEQ

    @pytest.mark.asyncio
    async def test_does_not_fall_back_to_uefi_when_boot_mode_readable(self, badfish_instance):
        # A genuine Bios host (BootMode read successfully) with an empty BootSeq
        # must not be retargeted to UefiBootSeq (which does not govern legacy
        # boot order); it should error instead.
        badfish_instance.boot_mode_readable = True
        badfish_instance.get_boot_seq = AsyncMock(return_value="BootSeq")
        badfish_instance.get_request = AsyncMock(
            side_effect=router(
                {
                    url(OEM_BOOT_SOURCES): make_response(
                        payload={"Attributes": {"BootSeq": [], "UefiBootSeq": UEFI_BOOT_SEQ}}
                    )
                }
            )
        )

        with pytest.raises(BadfishException):
            await badfish_instance.get_boot_devices()

    @pytest.mark.asyncio
    async def test_patch_boot_seq_uses_resolved_boot_seq_attr(self, badfish_instance):
        badfish_instance.boot_seq_attr = "UefiBootSeq"
        badfish_instance.get_request = AsyncMock(side_effect=router({url(OEM_BOOT_SOURCES): make_response()}))
        badfish_instance.get_boot_seq = AsyncMock(return_value="BootSeq")
        badfish_instance.patch_request = AsyncMock(return_value=make_response(status=200))

        await badfish_instance.patch_boot_seq(UEFI_BOOT_SEQ)

        assert badfish_instance.patch_request.call_args[0][1] == {"Attributes": {"UefiBootSeq": UEFI_BOOT_SEQ}}
        badfish_instance.get_boot_seq.assert_not_awaited()


class TestCheckSupportedIdracVersion:
    @pytest.mark.asyncio
    async def test_returns_false_when_dell_job_service_unsupported(self, badfish_instance):
        # Hosts without a DellJobService (e.g. Supermicro) must fall back to
        # force-clearing rather than let the resolver exception propagate.
        badfish_instance.get_request = AsyncMock(side_effect=router({}))

        assert await badfish_instance.check_supported_idrac_version() is False

    @pytest.mark.asyncio
    async def test_returns_true_when_service_supported(self, badfish_instance):
        badfish_instance.get_request = AsyncMock(side_effect=router({url(DELL_JOB_SERVICE_LEGACY): make_response()}))

        assert await badfish_instance.check_supported_idrac_version() is True


class TestDeleteJobQueueDell:
    @pytest.mark.asyncio
    async def test_legacy_candidate_uses_single_slash_action_url(self, badfish_instance):
        badfish_instance.get_request = AsyncMock(side_effect=router({url(DELL_JOB_SERVICE_LEGACY): make_response()}))
        badfish_instance.post_request = AsyncMock(return_value=make_response(status=200))

        await badfish_instance.delete_job_queue_dell(False)

        action_url = badfish_instance.post_request.call_args[0][0]
        assert action_url == "%s/Actions/DellJobService.DeleteJobQueue" % url(DELL_JOB_SERVICE_LEGACY)
        assert "//Actions" not in action_url

    @pytest.mark.asyncio
    async def test_oem_candidate_uses_single_slash_action_url(self, badfish_instance):
        badfish_instance.get_request = AsyncMock(side_effect=router({url(OEM_DELL_JOB_SERVICE): make_response()}))
        badfish_instance.post_request = AsyncMock(return_value=make_response(status=200))

        await badfish_instance.delete_job_queue_dell(False)

        action_url = badfish_instance.post_request.call_args[0][0]
        assert action_url == "%s/Actions/DellJobService.DeleteJobQueue" % url(OEM_DELL_JOB_SERVICE)
        assert "//Actions" not in action_url


class TestListInterfacesNetworkAdapters:
    @pytest.mark.asyncio
    async def test_uses_resolver_on_idrac10_chassis(self, badfish_instance):
        badfish_instance._use_tables = False
        badfish_instance.get_request = AsyncMock(side_effect=router({url(NA_CHASSIS): make_response()}))
        badfish_instance.get_network_adapters = AsyncMock(return_value={})

        assert await badfish_instance.list_interfaces() is True
        badfish_instance.get_network_adapters.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_falls_back_to_ethernet_interfaces(self, badfish_instance):
        badfish_instance._use_tables = False
        badfish_instance.find_network_adapters_resource = AsyncMock(
            side_effect=ResourceNotFound("Network adapters not supported by this host.")
        )
        badfish_instance.check_supported_network_interfaces = AsyncMock(return_value=True)
        badfish_instance.get_ethernet_interfaces = AsyncMock(return_value={})

        assert await badfish_instance.list_interfaces() is True
        badfish_instance.get_ethernet_interfaces.assert_awaited_once()


class TestGetIdracFwVersionIdrac10Firmware:
    @pytest.mark.asyncio
    async def test_detects_idrac10_when_model_lacks_17g(self, badfish_instance):
        badfish_instance.get_request = AsyncMock(
            side_effect=router(
                {
                    url(MANAGER_RESOURCE + "/"): make_response(
                        payload={"FirmwareVersion": "1.30.30.52", "Model": "PowerEdge R670"}
                    )
                }
            )
        )

        version = await badfish_instance.get_idrac_fw_version()

        assert version == 1303052
        assert badfish_instance._idrac10 is True


class TestGetJobQueueWhenJobsUnsupported:
    @pytest.mark.asyncio
    async def test_returns_empty_when_jobs_not_supported(self, badfish_instance):
        badfish_instance.get_request = AsyncMock(side_effect=router({}))

        assert await badfish_instance.get_job_queue() == []
