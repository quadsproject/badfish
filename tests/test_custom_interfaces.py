import pytest

from badfish.main import Badfish
from tests.config import INTERFACES_PATH
from tests.test_base import TestBase

E26_EXPECTED_INTERFACES = {
    "director": "NIC.Slot.3-1-1,HardDisk.List.1-1,NIC.Integrated.1-1-1",
    "foreman": "NIC.Integrated.1-1-1,HardDisk.List.1-1,NIC.Slot.3-1-1",
    "uefi": "NIC.Slot.3-1-1,HardDisk.List.1-1,NIC.Integrated.1-1-1",
}

E27_EXPECTED_INTERFACES = {
    "director": "NIC.Slot.3-1-1,NIC.Slot.3-2-1,NIC.Slot.6-1-1,NIC.Slot.6-2-1,NIC.Embedded.1-1-1,HardDisk.List.1-1",
    "foreman": "NIC.Embedded.1-1-1,NIC.Slot.3-1-1,NIC.Slot.3-2-1,NIC.Slot.6-1-1,NIC.Slot.6-2-1,HardDisk.List.1-1",
    "uefi": "NIC.Slot.3-1-1,HardDisk.List.1-1,NIC.Embedded.1-1-1",
}

FC640_B01_INTERFACES = {
    "uefi": "NIC.ChassisSlot.8-1-1,HardDisk.List.1-1,NIC.Integrated.1-1-1",
}

FC640_B02_INTERFACES = {
    "uefi": "NIC.ChassisSlot.4-1-1,HardDisk.List.1-1,NIC.Integrated.1-1-1",
}


class TestGetInterfaceByType(TestBase):
    @pytest.mark.asyncio
    async def test_get_interface_by_type(self):
        for host, expected in [
            ("mgmt-e26-h01-r750", E26_EXPECTED_INTERFACES),
            ("mgmt-e27-h01-r750", E27_EXPECTED_INTERFACES),
            ("mgmt-e26-h01-000-r750", E26_EXPECTED_INTERFACES),
            ("mgmt-e27-h01-000-r750", E27_EXPECTED_INTERFACES),
            ("mgmt-e99-h01-b01-fc640", FC640_B01_INTERFACES),
            ("mgmt-e99-h01-b02-fc640", FC640_B02_INTERFACES),
        ]:
            for host_type in expected:
                expected_interfaces = expected[host_type].split(",")
                with self.subTest(host=host, host_type=host_type):
                    badfish = Badfish(
                        _host=host,
                        _username="",
                        _password="",
                        _logger="",
                        _retries="",
                    )
                    interfaces = await badfish.get_interfaces_by_type(host_type, _interfaces_path=INTERFACES_PATH)
                    assert interfaces == expected_interfaces, (
                        f"{host_type} interfaces for host: {host} : "
                        f"{interfaces} does not match expected: {expected_interfaces}"
                    )


class TestGetInterfaceByTypeOverride(TestBase):
    @pytest.mark.asyncio
    async def test_explicit_rack_uloc(self):
        # Non-standard hostname; rack and uloc provided explicitly to match e27 interfaces
        badfish = Badfish(
            _host="server-r750.example.com",
            _username="",
            _password="",
            _logger="",
            _retries="",
            _rack="e27",
            _uloc="h01",
        )
        for host_type, expected_str in E27_EXPECTED_INTERFACES.items():
            expected_interfaces = expected_str.split(",")
            with self.subTest(host_type=host_type):
                interfaces = await badfish.get_interfaces_by_type(host_type, _interfaces_path=INTERFACES_PATH)
                assert interfaces == expected_interfaces, (
                    f"{host_type} interfaces with explicit rack/uloc: "
                    f"{interfaces} does not match expected: {expected_interfaces}"
                )

    @pytest.mark.asyncio
    async def test_explicit_blade(self):
        # Non-standard hostname; rack, uloc, and blade provided explicitly for blade b01
        badfish = Badfish(
            _host="server-fc640.example.com",
            _username="",
            _password="",
            _logger="",
            _retries="",
            _rack="e99",
            _uloc="h01",
            _blade="b01",
        )
        expected_interfaces = FC640_B01_INTERFACES["uefi"].split(",")
        interfaces = await badfish.get_interfaces_by_type("uefi", _interfaces_path=INTERFACES_PATH)
        assert interfaces == expected_interfaces, (
            f"uefi interfaces with explicit blade b01: "
            f"{interfaces} does not match expected: {expected_interfaces}"
        )

    @pytest.mark.asyncio
    async def test_explicit_blade_b02(self):
        # Non-standard hostname; rack, uloc, and blade provided explicitly for blade b02
        badfish = Badfish(
            _host="server-fc640.example.com",
            _username="",
            _password="",
            _logger="",
            _retries="",
            _rack="e99",
            _uloc="h01",
            _blade="b02",
        )
        expected_interfaces = FC640_B02_INTERFACES["uefi"].split(",")
        interfaces = await badfish.get_interfaces_by_type("uefi", _interfaces_path=INTERFACES_PATH)
        assert interfaces == expected_interfaces, (
            f"uefi interfaces with explicit blade b02: "
            f"{interfaces} does not match expected: {expected_interfaces}"
        )
