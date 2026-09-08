import json
import logging
import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from badfish.main import Badfish
from tests.config import (
    BLANK_RESP,
    INIT_RESP,
    JOB_ID,
    RESPONSE_EXPORT_SCP_JOB_FAILED,
    RESPONSE_EXPORT_SCP_NO_LOCATION,
    RESPONSE_EXPORT_SCP_PASS,
    RESPONSE_EXPORT_SCP_STATUS_FAIL,
    RESPONSE_EXPORT_SCP_TIME_OUT,
    RESPONSE_GET_SCP_TARGETS_UNSUPPORTED_ERR,
    RESPONSE_GET_SCP_TARGETS_WITH_ALLOWABLES_PASS,
    RESPONSE_GET_SCP_TARGETS_WITHOUT_ALLOWABLES_ERR,
    RESPONSE_GET_SCP_TARGETS_WRONG,
    RESPONSE_IMPORT_SCP_FAIL_STATE,
    RESPONSE_IMPORT_SCP_INVALID_FILEPATH,
    RESPONSE_IMPORT_SCP_PASS,
    RESPONSE_IMPORT_SCP_STATUS_FAIL,
    RESPONSE_IMPORT_SCP_TIME_OUT,
    SCP_EXPORT_JOB_FAILED,
    SCP_GET_TARGETS_ACTIONS_OEM_UNSUPPORTED,
    SCP_GET_TARGETS_ACTIONS_OEM_WITH_ALLOWABLES,
    SCP_GET_TARGETS_ACTIONS_OEM_WITHOUT_ALLOWABLES,
    SCP_MESSAGE_PERCENTAGE,
    SCP_MESSAGE_PERCENTAGE_STATE,
    STATE_ON_RESP,
)
from tests.test_base import TestBase


FIXED_BASE_TIME = datetime(2024, 6, 15, 10, 30, 0)


def fixed_datetime():
    fixed_datetime.counter = getattr(fixed_datetime, "counter", 0) + 1
    if fixed_datetime.counter < 5:
        return FIXED_BASE_TIME
    else:
        return FIXED_BASE_TIME + timedelta(minutes=15)


def export_dir_check():
    if not os.path.exists("exports"):
        os.makedirs("exports")


@pytest.mark.asyncio
async def test_export_scp_saves_file_inside_target_dir(tmp_path):
    """The exported file must land INSIDE the given directory (no trailing slash)."""
    logger = MagicMock(spec=logging.Logger)
    bf = Badfish("test_host", "user", "pass", logger, 1)
    bf.http_client = MagicMock()

    config_body = {"SystemConfiguration": {"Settings": {"value": 1}}}
    job_resp = MagicMock()
    job_resp.text = AsyncMock(return_value=json.dumps(config_body))

    post_resp = MagicMock()
    post_resp.status = 202
    post_resp.headers = {"Location": f"/redfish/v1/Managers/iDRAC.Embedded.1/Jobs/{JOB_ID}"}

    bf.post_request = AsyncMock(return_value=post_resp)
    bf._extract_job_id_from_response = MagicMock(return_value=JOB_ID)
    bf.get_request = AsyncMock(return_value=job_resp)

    expected_name = f"{FIXED_BASE_TIME.strftime('%Y-%m-%d_%H%M%S')}_targets_ALL_export.json"

    with patch("badfish.main.asyncio.sleep", new=AsyncMock()), patch(
        "badfish.main.get_now", return_value=FIXED_BASE_TIME
    ):
        result = await bf.export_scp(str(tmp_path), "ALL")

    assert result is True
    # os.path.join semantics: the file lives under tmp_path, not as a sibling.
    assert (tmp_path / expected_name).is_file()
    assert not (tmp_path.parent / expected_name).exists()


class TestGetSCPTargets(TestBase):
    option_arg = "--get-scp-targets"

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_with_allowables_pass(self, mock_get, mock_post, mock_delete):
        responses_add = [
            SCP_GET_TARGETS_ACTIONS_OEM_WITH_ALLOWABLES,
        ]
        responses = INIT_RESP + responses_add
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg, "Export"]
        _, err = self.badfish_call()
        assert err == RESPONSE_GET_SCP_TARGETS_WITH_ALLOWABLES_PASS

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_without_allowables_err(self, mock_get, mock_post, mock_delete):
        responses_add = [
            SCP_GET_TARGETS_ACTIONS_OEM_WITHOUT_ALLOWABLES,
        ]
        responses = INIT_RESP + responses_add
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg, "Export"]
        _, err = self.badfish_call()
        assert err == RESPONSE_GET_SCP_TARGETS_WITHOUT_ALLOWABLES_ERR

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_idrac_scp_unsupported_err(self, mock_get, mock_post, mock_delete):
        responses_add = [
            SCP_GET_TARGETS_ACTIONS_OEM_UNSUPPORTED,
        ]
        responses = INIT_RESP + responses_add
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg, "Export"]
        _, err = self.badfish_call()
        assert err == RESPONSE_GET_SCP_TARGETS_UNSUPPORTED_ERR

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_something_wrong(self, mock_get, mock_post, mock_delete):
        responses_add = [
            BLANK_RESP,
        ]
        responses = INIT_RESP + responses_add
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg, "Export"]
        _, err = self.badfish_call()
        assert err == RESPONSE_GET_SCP_TARGETS_WRONG


class TestExportSCP(TestBase):
    option_arg = "--export-scp"

    tests_dir = os.path.dirname(__file__)
    example_path = os.path.join(tests_dir, "fixtures/example_scp.json")

    @patch("badfish.main.get_now", fixed_datetime)
    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_pass(self, mock_get, mock_post, mock_delete):
        if hasattr(fixed_datetime, "counter"):
            setattr(fixed_datetime, "counter", 0)
        export_dir_check()
        scp_file = open(self.example_path, "r").read()
        # Wait-then-fetch approach: wait 45 seconds, then fetch from Jobs, fallback to Tasks
        # First GET from Jobs endpoint (no SystemConfiguration), then GET from Tasks endpoint (has it)
        responses_get = [
            SCP_MESSAGE_PERCENTAGE % ("Ex", 100),  # Jobs endpoint response (no SystemConfiguration)
            scp_file,  # Tasks endpoint response (has SystemConfiguration)
        ]
        responses = INIT_RESP + responses_get
        headers = {"Location": f"/{JOB_ID}"}
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 202], ["OK", "OK"], headers=headers, post=True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg, "./exports/"]
        _, err = self.badfish_call()
        assert err == RESPONSE_EXPORT_SCP_PASS % (fixed_datetime().strftime("%Y-%m-%d_%H%M%S"))

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_status_fail(self, mock_get, mock_post, mock_delete):
        export_dir_check()
        # Provide extra responses in case error_handler makes additional requests
        responses = INIT_RESP + [BLANK_RESP] * 10
        self.set_mock_response(mock_get, 200, responses)
        # First POST is session/auth (200), second POST is export command (400 = fail)
        self.set_mock_response(mock_post, [200, 400], ["OK", "Bad Request"], post=True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg, "./exports/"]
        _, err = self.badfish_call()
        assert err == RESPONSE_EXPORT_SCP_STATUS_FAIL

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_no_location(self, mock_get, mock_post, mock_delete):
        export_dir_check()
        responses = INIT_RESP
        headers = {}
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 202], ["OK", "OK"], headers=headers, post=True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg, "./exports/"]
        _, err = self.badfish_call()
        assert err == RESPONSE_EXPORT_SCP_NO_LOCATION

    @patch("badfish.main.get_now", fixed_datetime)
    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_time_out(self, mock_get, mock_post, mock_delete):
        if hasattr(fixed_datetime, "counter"):
            setattr(fixed_datetime, "counter", 0)
        export_dir_check()
        # Test failure: SystemConfiguration not found in either Jobs or Tasks endpoint
        responses_get = [
            SCP_MESSAGE_PERCENTAGE % ("Ex", 100),  # Jobs endpoint (no SystemConfiguration)
            SCP_MESSAGE_PERCENTAGE % ("Ex", 100),  # Tasks endpoint (no SystemConfiguration either)
        ]
        responses = INIT_RESP + responses_get
        headers = {"Location": f"/{JOB_ID}"}
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 202], ["OK", "OK"], headers=headers, post=True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg, "./exports/"]
        _, err = self.badfish_call()
        assert err == RESPONSE_EXPORT_SCP_TIME_OUT

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_job_failed(self, mock_get, mock_post, mock_delete):
        export_dir_check()
        # Test job failed state: Jobs endpoint returns JobState: "Failed"
        responses_get = [
            SCP_EXPORT_JOB_FAILED,  # Jobs endpoint response with JobState: "Failed"
        ]
        responses = INIT_RESP + responses_get
        headers = {"Location": f"/{JOB_ID}"}
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 202], ["OK", "OK"], headers=headers, post=True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg, "./exports/"]
        _, err = self.badfish_call()
        assert err == RESPONSE_EXPORT_SCP_JOB_FAILED


class TestImportSCP(TestBase):
    option_arg = "--import-scp"

    tests_dir = os.path.dirname(__file__)
    example_path = os.path.join(tests_dir, "fixtures/example_scp.json")

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_pass(self, mock_get, mock_post, mock_delete):
        export_dir_check()
        responses_get = [
            STATE_ON_RESP,
            SCP_MESSAGE_PERCENTAGE % ("Im", 15),
            SCP_MESSAGE_PERCENTAGE % ("Im", 30),
            SCP_MESSAGE_PERCENTAGE % ("Im", 45),
            SCP_MESSAGE_PERCENTAGE % ("Im", 60),
            SCP_MESSAGE_PERCENTAGE % ("Im", 75),
            SCP_MESSAGE_PERCENTAGE % ("Im", 90),
            SCP_MESSAGE_PERCENTAGE % ("Im", 99),
            SCP_MESSAGE_PERCENTAGE_STATE
            % ("Successfully imported and applied Server Configuration Profile.", 100, "Completed"),
        ]
        responses = INIT_RESP + responses_get
        headers = {"Location": f"/{JOB_ID}"}
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 202], ["OK", "OK"], headers=headers, post=True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg, self.example_path]
        _, err = self.badfish_call()
        assert err == RESPONSE_IMPORT_SCP_PASS

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_invalid_filepath(self, mock_get, mock_post, mock_delete):
        responses = INIT_RESP
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg, "no_file"]
        _, err = self.badfish_call()
        assert err == RESPONSE_IMPORT_SCP_INVALID_FILEPATH

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_status_fail(self, mock_get, mock_post, mock_delete):
        responses_get = [STATE_ON_RESP]
        responses = INIT_RESP + responses_get
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 400], ["OK", "Bad Request"], True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg, self.example_path]
        _, err = self.badfish_call()
        assert err == RESPONSE_IMPORT_SCP_STATUS_FAIL

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_no_location(self, mock_get, mock_post, mock_delete):
        export_dir_check()
        responses_get = [STATE_ON_RESP]
        responses = INIT_RESP + responses_get
        headers = {}
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 202], ["OK", "OK"], headers=headers, post=True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg, self.example_path]
        _, err = self.badfish_call()
        assert err == RESPONSE_EXPORT_SCP_NO_LOCATION

    @patch("badfish.main.get_now", fixed_datetime)
    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_time_out(self, mock_get, mock_post, mock_delete):
        if hasattr(fixed_datetime, "counter"):
            setattr(fixed_datetime, "counter", 0)
        export_dir_check()
        responses_get = [
            STATE_ON_RESP,
            "{}",
            INIT_RESP[0],
        ] + ([SCP_MESSAGE_PERCENTAGE % ("Im", 1)] * 1000000)
        responses = INIT_RESP + responses_get
        headers = {"Location": f"/{JOB_ID}"}
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 202], ["OK", "OK"], headers=headers, post=True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg, self.example_path]
        _, err = self.badfish_call()
        assert err == RESPONSE_IMPORT_SCP_TIME_OUT

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_fail_state(self, mock_get, mock_post, mock_delete):
        export_dir_check()
        responses_get = [
            STATE_ON_RESP,
            SCP_MESSAGE_PERCENTAGE % ("Im", 20),
            SCP_MESSAGE_PERCENTAGE % ("Im", 40),
            SCP_MESSAGE_PERCENTAGE % ("Im", 60),
            SCP_MESSAGE_PERCENTAGE_STATE % ("Unable to complete the Import operation.", 100, "Failed"),
        ]
        responses = INIT_RESP + responses_get
        headers = {"Location": f"/{JOB_ID}"}
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 202], ["OK", "OK"], headers=headers, post=True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg, self.example_path]
        _, err = self.badfish_call()
        assert err == RESPONSE_IMPORT_SCP_FAIL_STATE
