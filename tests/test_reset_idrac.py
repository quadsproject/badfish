from unittest.mock import patch, PropertyMock, AsyncMock

from tests.config import (
    BOOT_SEQ_RESPONSE_DIRECTOR,
    INIT_RESP,
    INIT_RESP_SUPERMICRO,
    RESET_TYPE_RESP,
    RESPONSE_RESET,
    RESPONSE_RESET_FAIL,
    RESPONSE_RESET_WRONG_VENDOR,
    ROOT_RESP,
)
from tests.test_base import TestBase


class TestResetIdrac(TestBase):
    option_arg = "--racreset"

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_reset_idrac(self, mock_get, mock_post, mock_delete):
        responses = INIT_RESP + [RESET_TYPE_RESP]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 204], "OK", True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.boot_seq = BOOT_SEQ_RESPONSE_DIRECTOR
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == RESPONSE_RESET % ("204", "iDRAC", "iDRAC")

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_reset_idrac_fail(self, mock_get, mock_post, mock_delete):
        responses = INIT_RESP + [RESET_TYPE_RESP]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 400], ["OK", "Bad Request"], True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.boot_seq = BOOT_SEQ_RESPONSE_DIRECTOR
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == RESPONSE_RESET_FAIL

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_reset_idrac_wrong_vendor(self, mock_get, mock_post, mock_delete):
        responses = INIT_RESP_SUPERMICRO + [RESET_TYPE_RESP]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 204], "OK", True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.boot_seq = BOOT_SEQ_RESPONSE_DIRECTOR
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == RESPONSE_RESET_WRONG_VENDOR % ("Dell", "Supermicro or HPE", "--bmc-reset")

    @patch("badfish.main.Badfish.wait_for_idrac_ready", new_callable=AsyncMock)
    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_reset_idrac_with_wait_timeout(self, mock_get, mock_post, mock_delete, mock_wait):
        responses = INIT_RESP + [RESET_TYPE_RESP]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 204], "OK", True)
        self.set_mock_response(mock_delete, 200, "OK")
        mock_wait.return_value = False

        self.boot_seq = BOOT_SEQ_RESPONSE_DIRECTOR
        self.args = [self.option_arg, "--wait"]
        _, err = self.badfish_call()
        assert "Status code 204 returned for POST command to reset iDRAC" in err
        assert "iDRAC reset initiated. Waiting for iDRAC to come back online" in err
        assert "iDRAC did not respond after 30 retry attempts" in err

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_reset_idrac_with_wait_success(self, mock_get, mock_post, mock_delete):
        responses = INIT_RESP + [RESET_TYPE_RESP] + [ROOT_RESP] * 15
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 204], "OK", True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.boot_seq = BOOT_SEQ_RESPONSE_DIRECTOR
        self.args = [self.option_arg, "--wait"]
        _, err = self.badfish_call()
        assert "Status code 204 returned for POST command to reset iDRAC" in err
        assert "iDRAC reset initiated. Waiting for iDRAC to come back online" in err
        assert "Polling for iDRAC" in err
        assert "iDRAC is ready" in err
        assert "iDRAC is now responsive" in err

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_reset_idrac_with_wait_delayed(self, mock_get, mock_post, mock_delete):
        responses = INIT_RESP + [RESET_TYPE_RESP] + ["Not Found"] * 5 + [ROOT_RESP] * 10
        status_list = [200] * 6 + [404] * 5 + [200] * 10
        self.set_mock_response(mock_get, status_list, responses)
        self.set_mock_response(mock_post, [200, 204], "OK", True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.boot_seq = BOOT_SEQ_RESPONSE_DIRECTOR
        self.args = [self.option_arg, "--wait"]
        _, err = self.badfish_call()
        assert "Status code 204 returned for POST command to reset iDRAC" in err
        assert "iDRAC reset initiated. Waiting for iDRAC to come back online" in err
        assert "Polling for iDRAC" in err
        assert "iDRAC is ready" in err
        assert "iDRAC is now responsive" in err
