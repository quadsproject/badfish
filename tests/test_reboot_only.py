import json
from unittest.mock import patch

from tests.config import (
    BOOT_SEQ_RESPONSE_DIRECTOR,
    INIT_RESP,
    RESET_TYPE_NG_RESP,
    RESET_TYPE_RESP,
    RESPONSE_REBOOT_ONLY_ALREADY_ON,
    RESPONSE_REBOOT_ONLY_FAILED_GRACE_AND_FORCE,
    RESPONSE_REBOOT_ONLY_FAILED_SEND_RESET,
    RESPONSE_REBOOT_ONLY_SUCCESS,
    RESPONSE_REBOOT_ONLY_SUCCESS_WITH_NG_RT,
    STATE_DOWN_RESP,
    STATE_OFF_RESP,
    STATE_ON_RESP,
)
from tests.test_base import TestBase


def _reset_types_sent(mock_post):
    return [
        json.loads(call.kwargs["data"])["ResetType"]
        for call in mock_post.call_args_list
        if call.args[0].endswith("/Actions/ComputerSystem.Reset")
    ]


class TestRebootOnly(TestBase):
    option_arg = "--reboot-only"

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_reboot_only_success(self, mock_get, mock_post, mock_delete):
        responses = INIT_RESP + [
            RESET_TYPE_RESP,
            STATE_ON_RESP,
            STATE_OFF_RESP,
            STATE_ON_RESP,
        ]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 204, 204], "OK", True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.boot_seq = BOOT_SEQ_RESPONSE_DIRECTOR
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == RESPONSE_REBOOT_ONLY_SUCCESS

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_reboot_only_already_on_after_graceful_restart(self, mock_get, mock_post, mock_delete):
        responses = INIT_RESP + [RESET_TYPE_RESP, STATE_ON_RESP, STATE_OFF_RESP]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 204, 409], "OK", True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg]

        _, err = self.badfish_call()

        assert err == RESPONSE_REBOOT_ONLY_ALREADY_ON
        assert _reset_types_sent(mock_post) == ["GracefulRestart", "On"]

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_reboot_only_powered_off(self, mock_get, mock_post, mock_delete):
        responses = INIT_RESP + [RESET_TYPE_RESP, STATE_OFF_RESP]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 204], "OK", True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg]

        _, err = self.badfish_call()

        assert err == (
            "- INFO     - Current server state is OFF.\n"
            "- INFO     - Issuing a power-on request to the iDRAC.\n"
            "- INFO     - Command passed to On server, code return is 204.\n"
        )
        assert _reset_types_sent(mock_post) == ["On"]

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_power_cycle_already_on(self, mock_get, mock_post, mock_delete):
        responses = INIT_RESP + [RESET_TYPE_RESP, STATE_ON_RESP, STATE_OFF_RESP]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 204, 409], "OK", True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = ["--power-cycle"]

        _, err = self.badfish_call()

        assert err == (
            "- INFO     - Current server state is ON.\n"
            "- INFO     - Command passed to ForceOff server, code return is 204.\n"
            "- INFO     - Polling for host state: Not Down\n"
            "- INFO     - Command failed to On server, host appears to be already in that state.\n"
        )
        assert _reset_types_sent(mock_post) == ["ForceOff", "On"]

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_reboot_only_already_on_with_alternate_reset_type(self, mock_get, mock_post, mock_delete):
        responses = INIT_RESP + [RESET_TYPE_NG_RESP, STATE_ON_RESP, STATE_OFF_RESP]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 204, 409], "OK", True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg]

        _, err = self.badfish_call()

        assert err == (
            "- INFO     - Current server state is ON.\n"
            "- INFO     - Command passed to RestartNow server, code return is 204.\n"
            "- INFO     - Polling for host state: Not Down\n"
            "- INFO     - Command failed to On server, host appears to be already in that state.\n"
        )
        assert _reset_types_sent(mock_post) == ["RestartNow", "On"]

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_reboot_only_success_with_polling_down(self, mock_get, mock_post, mock_delete):
        responses = INIT_RESP + [
            RESET_TYPE_RESP,
            STATE_ON_RESP,
            STATE_DOWN_RESP,
            STATE_ON_RESP,
        ]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 204, 204], "OK", True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.boot_seq = BOOT_SEQ_RESPONSE_DIRECTOR
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == RESPONSE_REBOOT_ONLY_SUCCESS

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_reboot_only_failed_send_reset(self, mock_get, mock_post, mock_delete):
        responses = INIT_RESP + [
            RESET_TYPE_RESP,
            STATE_ON_RESP,
            STATE_DOWN_RESP,
            STATE_ON_RESP,
        ]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 400], ["OK", "Bad Request"], True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.boot_seq = BOOT_SEQ_RESPONSE_DIRECTOR
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == RESPONSE_REBOOT_ONLY_FAILED_SEND_RESET

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_reboot_only_success_with_ng_rt(self, mock_get, mock_post, mock_delete):
        responses = INIT_RESP + [
            RESET_TYPE_NG_RESP,
            STATE_ON_RESP,
            STATE_DOWN_RESP,
            STATE_ON_RESP,
        ]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 204, 204], "OK", True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.boot_seq = BOOT_SEQ_RESPONSE_DIRECTOR
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == RESPONSE_REBOOT_ONLY_SUCCESS_WITH_NG_RT

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.get")
    @patch("aiohttp.ClientSession.post")
    def test_reboot_only_failed_grace_and_force(self, mock_post, mock_get, mock_delete):
        responses = INIT_RESP + [
            RESET_TYPE_RESP,
            STATE_ON_RESP,
        ]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 409, 409, 409], "Conflict", True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg, "--retries", "1"]
        _, err = self.badfish_call()
        assert err == RESPONSE_REBOOT_ONLY_FAILED_GRACE_AND_FORCE
        assert _reset_types_sent(mock_post) == ["GracefulRestart", "ForceOff", "On"]
