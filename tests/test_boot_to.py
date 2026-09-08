import logging

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from badfish.main import Badfish
from tests.config import (
    BAD_DEVICE_NAME,
    BLANK_RESP,
    BOOT_MODE_RESP,
    BOOT_SEQ_RESP,
    BOOT_SEQ_RESPONSE_DIRECTOR,
    DEVICE_NIC_2,
    ERROR_DEV_NO_MATCH,
    INIT_RESP,
    JOB_OK_RESP,
    RESET_TYPE_RESP,
    RESPONSE_BOOT_TO,
    RESPONSE_BOOT_TO_SERVICE_BAD_REQUEST,
    RESPONSE_BOOT_TO_SERVICE_ERR_HANDLER,
    RESPONSE_BOOT_TO_SERVICE_UNAVAILABLE,
    STATE_ON_RESP,
)
from tests.test_base import TestBase


class TestBootTo(TestBase):
    option_arg = "--boot-to"

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.get")
    def test_boot_to(self, mock_get, mock_patch, mock_post, mock_delete):
        boot_seq_resp_fmt = BOOT_SEQ_RESP % str(BOOT_SEQ_RESPONSE_DIRECTOR)
        get_resp = [
            BOOT_MODE_RESP,
            boot_seq_resp_fmt.replace("'", '"'),
            BLANK_RESP,
            BOOT_MODE_RESP,
        ]
        responses = INIT_RESP + get_resp
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_patch, 200, ["OK"])
        self.set_mock_response(mock_post, 200, ["OK", JOB_OK_RESP])
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg, DEVICE_NIC_2["name"]]
        _, err = self.badfish_call()
        assert err == RESPONSE_BOOT_TO

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.get")
    def test_boot_to_service_unavailable(self, mock_get, mock_patch, mock_post, mock_delete):
        boot_seq_resp_fmt = BOOT_SEQ_RESP % str(BOOT_SEQ_RESPONSE_DIRECTOR)
        get_resp = [
            BOOT_MODE_RESP,
            boot_seq_resp_fmt.replace("'", '"'),
            BLANK_RESP,
            BOOT_MODE_RESP,
        ]
        responses = INIT_RESP + get_resp
        post_responses = ["OK"] + [JOB_OK_RESP]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_patch, [503, 200], ["Service Unavailable", "OK"])
        self.set_mock_response(mock_post, 200, post_responses)
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg, DEVICE_NIC_2["name"]]
        _, err = self.badfish_call()
        assert err == RESPONSE_BOOT_TO_SERVICE_UNAVAILABLE

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.get")
    def test_boot_to_bad_request(self, mock_get, mock_patch, mock_post, mock_delete):
        boot_seq_resp_fmt = BOOT_SEQ_RESP % str(BOOT_SEQ_RESPONSE_DIRECTOR)
        get_resp = [
            BOOT_MODE_RESP,
            boot_seq_resp_fmt.replace("'", '"'),
            BLANK_RESP,
            BOOT_MODE_RESP,
            BLANK_RESP,
            RESET_TYPE_RESP,
            STATE_ON_RESP,
        ]
        responses = INIT_RESP + get_resp
        post_responses = ["OK"] + [JOB_OK_RESP, JOB_OK_RESP, JOB_OK_RESP, JOB_OK_RESP]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_patch, [400, 200], ["Bad Request", "OK"])
        self.set_mock_response(mock_post, [200, 204, 400], post_responses, True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg, DEVICE_NIC_2["name"]]
        _, err = self.badfish_call()
        assert err == RESPONSE_BOOT_TO_SERVICE_BAD_REQUEST

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.get")
    def test_boot_to_service_err_handler(self, mock_get, mock_patch, mock_post, mock_delete):
        boot_seq_resp_fmt = BOOT_SEQ_RESP % str(BOOT_SEQ_RESPONSE_DIRECTOR)
        get_resp = [
            BOOT_MODE_RESP,
            boot_seq_resp_fmt.replace("'", '"'),
            BLANK_RESP,
            BOOT_MODE_RESP,
        ]
        responses = INIT_RESP + get_resp
        post_responses = ["OK"] + [JOB_OK_RESP]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_patch, 403, "Forbidden")
        self.set_mock_response(mock_post, 200, post_responses)
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg, DEVICE_NIC_2["name"]]
        _, err = self.badfish_call()
        assert err == RESPONSE_BOOT_TO_SERVICE_ERR_HANDLER

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.get")
    def test_boot_to_no_match(self, mock_get, mock_patch, mock_post, mock_delete):
        boot_seq_resp_fmt = BOOT_SEQ_RESP % str(BOOT_SEQ_RESPONSE_DIRECTOR)
        get_resp = [
            BOOT_MODE_RESP,
            boot_seq_resp_fmt.replace("'", '"'),
            BLANK_RESP,
        ]
        responses = INIT_RESP + get_resp
        post_responses = ["OK"] + [JOB_OK_RESP]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_patch, 200, ["OK"])
        self.set_mock_response(mock_post, 200, post_responses)
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg, BAD_DEVICE_NAME]
        _, err = self.badfish_call()
        assert err == ERROR_DEV_NO_MATCH

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.get")
    def test_boot_to_job_creation_fails(self, mock_get, mock_patch, mock_post, mock_delete):
        """Test create_job when POST to create job returns non-200 status (covers L805-806 in main.py)"""
        boot_seq_resp_fmt = BOOT_SEQ_RESP % str(BOOT_SEQ_RESPONSE_DIRECTOR)
        get_resp = [
            BOOT_MODE_RESP,
            boot_seq_resp_fmt.replace("'", '"'),
            BLANK_RESP,
            BOOT_MODE_RESP,
        ]
        responses = INIT_RESP + get_resp
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_patch, 200, ["OK"])
        # Make POST request fail with 500 to trigger error path in create_job
        self.set_mock_response(mock_post, 500, '{"error": "Internal Server Error"}')
        self.set_mock_response(mock_delete, 200, "OK")

        self.args = [self.option_arg, DEVICE_NIC_2["name"]]
        _, err = self.badfish_call()
        # The error path executes L805-806, but error_handler raises BadfishException
        # which gets caught at higher level and logs generic message
        assert "Failed to communicate" in err


@pytest.mark.asyncio
async def test_boot_to_returns_false_on_no_match():
    """boot_to() must return False (not None) when the device does not match."""
    logger = MagicMock(spec=logging.Logger)
    bf = Badfish("test_host", "user", "pass", logger, 1)
    bf.check_device = AsyncMock(return_value=False)

    result = await bf.boot_to("bad_device")

    assert result is False
