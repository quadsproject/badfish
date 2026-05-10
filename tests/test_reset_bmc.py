from unittest.mock import patch

from tests.config import (
    BOOT_SEQ_RESPONSE_DIRECTOR,
    INIT_RESP,
    INIT_RESP_HPE,
    INIT_RESP_SUPERMICRO,
    RESET_TYPE_RESP,
    RESET_TYPE_RESP_NO_ALLOWABLE_VALUES,
    RESPONSE_RESET,
    RESPONSE_RESET_FAIL,
    RESPONSE_RESET_WRONG_VENDOR,
)
from tests.test_base import TestBase


class TestResetBMC(TestBase):
    option_arg = "--bmc-reset"

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_reset_bmc(self, mock_get, mock_post, mock_delete):
        responses = INIT_RESP_SUPERMICRO + [RESET_TYPE_RESP]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 200], "OK", True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.boot_seq = BOOT_SEQ_RESPONSE_DIRECTOR
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == RESPONSE_RESET % ("200", "BMC", "BMC")

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_reset_bmc_no_allowable_values(self, mock_get, mock_post, mock_delete):
        responses = INIT_RESP_SUPERMICRO + [RESET_TYPE_RESP_NO_ALLOWABLE_VALUES]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 200], "OK", True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.boot_seq = BOOT_SEQ_RESPONSE_DIRECTOR
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == RESPONSE_RESET % ("200", "BMC", "BMC")

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_reset_bmc_fail(self, mock_get, mock_post, mock_delete):
        responses = INIT_RESP_SUPERMICRO + [RESET_TYPE_RESP]
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
    def test_reset_bmc_wrong_vendor(self, mock_get, mock_post, mock_delete):
        responses = INIT_RESP + [RESET_TYPE_RESP]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 204], "OK", True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.boot_seq = BOOT_SEQ_RESPONSE_DIRECTOR
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == RESPONSE_RESET_WRONG_VENDOR % ("Supermicro or HPE", "Dell", "--racreset")

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_reset_bmc_hpe(self, mock_get, mock_post, mock_delete):
        responses = INIT_RESP_HPE + [RESET_TYPE_RESP]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 200], "OK", True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.boot_seq = BOOT_SEQ_RESPONSE_DIRECTOR
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == RESPONSE_RESET % ("200", "BMC", "BMC")
