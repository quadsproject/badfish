from unittest.mock import PropertyMock, patch

from badfish.helpers.exceptions import ResourceNotFound
from tests.config import (
    DEVICE_NIC_I,
    DEVICE_NIC_S,
    INIT_RESP,
    NETWORK_ADAPTERS_RESP,
    NETWORK_DEV_FUNC_DET_RESP,
    NETWORK_DEV_FUNC_RESP,
    NETWORK_PORTS_RESP,
    NETWORK_PORTS_ROOT_RESP,
    RESPONSE_LS_ETHERNET,
    RESPONSE_LS_INTERFACES,
    RESPONSE_LS_INTERFACES_NOT_SUPPORTED,
    RESPONSE_LS_INTERFACES_VALUE_ERROR,
)
from tests.test_base import TestBase


class TestLsInterfaces(TestBase):
    option_arg = "--ls-interfaces"

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_ls_interfaces_adapters(self, mock_get, mock_post, mock_delete):
        responses_add = [
            NETWORK_ADAPTERS_RESP,
            NETWORK_PORTS_ROOT_RESP % (DEVICE_NIC_I, DEVICE_NIC_I),
            NETWORK_DEV_FUNC_RESP % (DEVICE_NIC_I, DEVICE_NIC_I),
            NETWORK_PORTS_RESP % DEVICE_NIC_I,
            NETWORK_DEV_FUNC_DET_RESP,
            NETWORK_PORTS_ROOT_RESP % (DEVICE_NIC_S, DEVICE_NIC_S),
            NETWORK_DEV_FUNC_RESP % (DEVICE_NIC_S, DEVICE_NIC_S),
            NETWORK_PORTS_RESP % DEVICE_NIC_S,
            NETWORK_DEV_FUNC_DET_RESP,
        ]
        responses = INIT_RESP + responses_add
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == RESPONSE_LS_INTERFACES

    @patch("rich.console.Console.is_terminal", new_callable=PropertyMock, return_value=True)
    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_ls_interfaces_table(self, mock_get, mock_post, mock_delete, mock_is_terminal):
        responses_add = [
            NETWORK_ADAPTERS_RESP,
            NETWORK_PORTS_ROOT_RESP % (DEVICE_NIC_I, DEVICE_NIC_I),
            NETWORK_DEV_FUNC_RESP % (DEVICE_NIC_I, DEVICE_NIC_I),
            NETWORK_PORTS_RESP % DEVICE_NIC_I,
            NETWORK_DEV_FUNC_DET_RESP,
            NETWORK_PORTS_ROOT_RESP % (DEVICE_NIC_S, DEVICE_NIC_S),
            NETWORK_DEV_FUNC_RESP % (DEVICE_NIC_S, DEVICE_NIC_S),
            NETWORK_PORTS_RESP % DEVICE_NIC_S,
            NETWORK_DEV_FUNC_DET_RESP,
        ]
        responses = INIT_RESP + responses_add
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert "- ERROR" not in err
        assert "MACAddress" in err

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_ls_interfaces_network_value_error(self, mock_get, mock_post, mock_delete):
        responses_add = [
            "",
        ]
        responses = INIT_RESP + responses_add
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == RESPONSE_LS_INTERFACES_VALUE_ERROR

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    @patch("badfish.main.Badfish.find_network_adapters_resource")
    @patch("badfish.main.Badfish.check_supported_network_interfaces")
    @patch("badfish.main.Badfish.get_ethernet_interfaces")
    def test_ls_interfaces_ethernet(
        self, mock_get_ethernet, mock_check_support, mock_find_network, mock_get, mock_post, mock_delete
    ):
        # Mock the support checks: NetworkAdapters not supported, EthernetInterfaces supported
        mock_find_network.side_effect = ResourceNotFound("Network adapters not supported by this host.")
        mock_check_support.side_effect = [True]

        # Mock the ethernet interfaces data
        ethernet_data = {
            "NIC.Slot.1-1-1": {
                "Name": "System Ethernet Interface",
                "MACAddress": "F8:BC:12:22:89:E1",
                "Status": {"Health": "OK", "State": "Enabled"},
                "SpeedMbps": 10240,
            },
            "NIC.Integrated.1-1-1": {
                "Name": "System Ethernet Interface",
                "MACAddress": "F8:BC:12:22:89:E0",
                "Status": {"Health": "OK", "State": "Enabled"},
                "SpeedMbps": 10240,
            },
        }
        mock_get_ethernet.return_value = ethernet_data

        self.set_mock_response(mock_get, 200, INIT_RESP)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == RESPONSE_LS_ETHERNET

    @patch("rich.console.Console.is_terminal", new_callable=PropertyMock, return_value=True)
    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    @patch("badfish.main.Badfish.find_network_adapters_resource")
    @patch("badfish.main.Badfish.check_supported_network_interfaces")
    @patch("badfish.main.Badfish.get_ethernet_interfaces")
    def test_ls_interfaces_ethernet_table(
        self,
        mock_get_ethernet,
        mock_check_support,
        mock_find_network,
        mock_get,
        mock_post,
        mock_delete,
        mock_is_terminal,
    ):
        mock_find_network.side_effect = ResourceNotFound("Network adapters not supported by this host.")
        mock_check_support.side_effect = [True]
        ethernet_data = {
            "NIC.Slot.1-1-1": {
                "Name": "System Ethernet Interface",
                "MACAddress": "F8:BC:12:22:89:E1",
                "Status": {"Health": "OK", "State": "Enabled"},
                "SpeedMbps": 10240,
            },
        }
        mock_get_ethernet.return_value = ethernet_data
        self.set_mock_response(mock_get, 200, INIT_RESP)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert "- ERROR" not in err
        assert "OK" in err

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    @patch("badfish.main.Badfish.find_network_adapters_resource")
    @patch("badfish.main.Badfish.check_supported_network_interfaces")
    def test_ls_interfaces_ethernet_not_supported(
        self, mock_check_support, mock_find_network, mock_get, mock_post, mock_delete
    ):
        # Mock the support checks: both NetworkAdapters and EthernetInterfaces not supported
        mock_find_network.side_effect = ResourceNotFound("Network adapters not supported by this host.")
        mock_check_support.side_effect = [False]

        self.set_mock_response(mock_get, 200, INIT_RESP)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == RESPONSE_LS_INTERFACES_NOT_SUPPORTED

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_ls_interfaces_ethernet_value_error(self, mock_get, mock_post, mock_delete):
        responses_add = [
            "",
        ]
        responses = INIT_RESP + responses_add
        status_codes = [200, 200, 200, 200, 200, 404, 200, 200]
        self.set_mock_response(mock_get, status_codes, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == RESPONSE_LS_INTERFACES_VALUE_ERROR

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    @patch("badfish.main.Badfish.find_network_adapters_resource")
    @patch("badfish.main.Badfish.check_supported_network_interfaces")
    def test_ls_interfaces_none_supported(
        self, mock_check_support, mock_find_network, mock_get, mock_post, mock_delete
    ):
        # Mock the support checks: both NetworkAdapters and EthernetInterfaces not supported
        mock_find_network.side_effect = ResourceNotFound("Network adapters not supported by this host.")
        mock_check_support.side_effect = [False]

        self.set_mock_response(mock_get, 200, INIT_RESP)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == RESPONSE_LS_INTERFACES_NOT_SUPPORTED
