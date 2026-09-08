import logging

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from badfish.main import Badfish
from tests.config import (
    BLANK_RESP,
    BOOT_MODE_RESP,
    BOOT_SEQ_RESP,
    DEVICE_HDD_1,
    DEVICE_NIC_2,
    render_device_dict,
    BOOT_SEQ_RESPONSE_DIRECTOR,
    INIT_RESP,
    INTERFACES_PATH,
    JOB_OK_RESP,
    RESET_TYPE_RESP,
    RESPONSE_BOOT_TO,
    RESPONSE_BOOT_TO_BAD_FILE,
    RESPONSE_BOOT_TO_BAD_TYPE,
    RESPONSE_BOOT_TO_CUSTOM,
    RESPONSE_BOOT_TO_NO_FILE,
    STATE_ON_RESP,
)
from tests.test_base import TestBase


class TestBootTo(TestBase):
    option_arg = "--boot-to-type"

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.get")
    def test_boot_to_type_foreman(self, mock_get, mock_patch, mock_post, mock_delete):
        boot_seq_resp_fmt = BOOT_SEQ_RESP % str(BOOT_SEQ_RESPONSE_DIRECTOR)
        get_resp = [
            BOOT_MODE_RESP,
            boot_seq_resp_fmt.replace("'", '"'),
            BLANK_RESP,
            BOOT_MODE_RESP,
            RESET_TYPE_RESP,
            STATE_ON_RESP,
            STATE_ON_RESP,
        ]
        responses = INIT_RESP + get_resp
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_patch, 200, ["OK"])
        self.set_mock_response(mock_post, 200, JOB_OK_RESP)
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = ["-i", INTERFACES_PATH, self.option_arg, "foreman"]
        _, err = self.badfish_call()
        assert err == RESPONSE_BOOT_TO

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.get")
    def test_boot_to_type_custom(self, mock_get, mock_patch, mock_post, mock_delete):
        boot_seq_resp_fmt = BOOT_SEQ_RESP % str(BOOT_SEQ_RESPONSE_DIRECTOR)
        get_resp = [
            BOOT_MODE_RESP,
            boot_seq_resp_fmt.replace("'", '"'),
            BLANK_RESP,
            BOOT_MODE_RESP,
            RESET_TYPE_RESP,
            STATE_ON_RESP,
            STATE_ON_RESP,
        ]
        responses = INIT_RESP + get_resp
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_patch, 200, ["OK"])
        self.set_mock_response(mock_post, 200, JOB_OK_RESP)
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = ["-i", INTERFACES_PATH, self.option_arg, "custom"]
        _, err = self.badfish_call(mock_host="host01.example.com")
        assert err == RESPONSE_BOOT_TO_CUSTOM

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.get")
    def test_boot_to_bad_type(self, mock_get, mock_patch, mock_post, mock_delete):
        boot_seq_resp_fmt = BOOT_SEQ_RESP % str(BOOT_SEQ_RESPONSE_DIRECTOR)
        get_resp = [
            BOOT_MODE_RESP,
            boot_seq_resp_fmt.replace("'", '"'),
            BLANK_RESP,
            BOOT_MODE_RESP,
            RESET_TYPE_RESP,
            STATE_ON_RESP,
            STATE_ON_RESP,
        ]
        responses = INIT_RESP + get_resp
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_patch, 200, ["OK"])
        self.set_mock_response(mock_post, 200, JOB_OK_RESP)
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = ["-i", INTERFACES_PATH, self.option_arg, "bad_type"]
        _, err = self.badfish_call()
        assert err == RESPONSE_BOOT_TO_BAD_TYPE

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.get")
    def test_boot_to_bad_file(self, mock_get, mock_patch, mock_post, mock_delete):
        boot_seq_resp_fmt = BOOT_SEQ_RESP % str(BOOT_SEQ_RESPONSE_DIRECTOR)
        get_resp = [
            BOOT_MODE_RESP,
            boot_seq_resp_fmt.replace("'", '"'),
            BLANK_RESP,
            BOOT_MODE_RESP,
            RESET_TYPE_RESP,
            STATE_ON_RESP,
            STATE_ON_RESP,
        ]
        responses = INIT_RESP + get_resp
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_patch, 200, ["OK"])
        self.set_mock_response(mock_post, 200, JOB_OK_RESP)
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = ["-i", "bad/bad/file", self.option_arg, "bad_type"]
        _, err = self.badfish_call()
        assert err == RESPONSE_BOOT_TO_BAD_FILE

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_boot_to_no_file(self, mock_get, mock_post, mock_delete):
        self.args = [self.option_arg, "bad_type"]
        self.set_mock_response(mock_get, 200, INIT_RESP)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        _, err = self.badfish_call()
        assert err == RESPONSE_BOOT_TO_NO_FILE

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.get")
    def test_boot_to_type_no_match(self, mock_get, mock_patch, mock_post, mock_delete):
        # Boot sequence without the custom type's first device must propagate
        # the failure so badfish exits nonzero.
        boot_seq_resp_fmt = BOOT_SEQ_RESP % str(
            [render_device_dict(0, DEVICE_HDD_1), render_device_dict(1, DEVICE_NIC_2)]
        )
        get_resp = [
            BOOT_MODE_RESP,
            boot_seq_resp_fmt.replace("'", '"'),
            BLANK_RESP,
        ]
        responses = INIT_RESP + get_resp
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_patch, 200, ["OK"])
        self.set_mock_response(mock_post, 200, ["OK", JOB_OK_RESP])
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = ["-i", INTERFACES_PATH, self.option_arg, "custom"]
        _, err = self.badfish_call(mock_host="host01.example.com")
        assert err == (
            "- ERROR    - Device NIC.Integrated.1-2-1 does not match any of the "
            "available boot devices for host host01.example.com\n"
        )


@pytest.mark.asyncio
async def test_boot_to_type_returns_false_on_no_device(tmp_path):
    """boot_to_type() must propagate False from boot_to() when no device matches."""
    logger = MagicMock(spec=logging.Logger)
    bf = Badfish("test_host", "user", "pass", logger, 1)
    iface = tmp_path / "idrac_interfaces.yml"
    iface.write_text("key: value")

    bf.get_host_types_from_yaml = AsyncMock(return_value=["foreman", "director"])
    bf.get_host_type_boot_device = AsyncMock(return_value=None)
    bf.boot_to = AsyncMock(return_value=False)

    result = await bf.boot_to_type("foreman", str(iface))

    assert result is False
