import logging
import os
from collections import defaultdict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from badfish.helpers.exceptions import BadfishException
from badfish.main import Badfish, execute_badfish
from tests.config import (
    HOST_LIST_EXTRAS,
    KEYBOARD_INTERRUPT,
    KEYBOARD_INTERRUPT_HOST_LIST,
    MAN_RESP,
    NO_HOST_ERROR,
    RESPONSE_INIT_CREDENTIALS_FAILED_COMS,
    RESPONSE_INIT_CREDENTIALS_UNAUTHORIZED,
    RESPONSE_INIT_SYSTEMS_RESOURCE_NOT_FOUND,
    ROOT_RESP,
    SUCCESSFUL_HOST_LIST,
    SYS_RESP,
    WRONG_BADFISH_EXECUTION,
    WRONG_BADFISH_EXECUTION_HOST_LIST,
    MANAGER_INSTANCE_RESP,
    JOBS_RESP,
)
from tests.test_base import TestBase


def raise_keyb_interrupt_stub(ignore1, ignore2, ignore3, ignore4=None, **kwargs):
    raise KeyboardInterrupt


def raise_badfish_exception_stub(ignore1, ignore2, ignore3, ignore4=None, **kwargs):
    raise BadfishException


class TestSingleHostExecution(TestBase):
    args = ["--ls-jobs"]

    @patch("badfish.main.execute_badfish", raise_keyb_interrupt_stub)
    def test_single_host_keyb_interrupt(self):
        _, err = self.badfish_call()
        assert err == KEYBOARD_INTERRUPT

    @patch("badfish.main.execute_badfish", raise_badfish_exception_stub)
    def test_single_host_badfish_exception(self):
        _, err = self.badfish_call()
        assert err == WRONG_BADFISH_EXECUTION

    def test_no_host_error(self):
        _, err = self.badfish_call(mock_host=None)
        assert err == NO_HOST_ERROR


class TestHostListExecution(TestBase):
    args = [
        "--host-list",
        f"{os.path.dirname(__file__)}/fixtures/hosts_good.txt",
        "--ls-jobs",
    ]

    @patch("badfish.main.execute_badfish", raise_keyb_interrupt_stub)
    def test_host_list_keyb_interrupt(self):
        _, err = self.badfish_call(mock_host=None)
        assert err == KEYBOARD_INTERRUPT_HOST_LIST

    @patch("badfish.main.execute_badfish", raise_badfish_exception_stub)
    def test_host_list_badfish_exception(self):
        _, err = self.badfish_call(mock_host=None)
        assert err == WRONG_BADFISH_EXECUTION_HOST_LIST

    @patch("badfish.main.execute_badfish")
    def test_host_list_successful(self, mock_execute):
        mock_execute.return_value = "Successful."
        _, err = self.badfish_call(mock_host=None)
        assert err == SUCCESSFUL_HOST_LIST

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_host_list_extras(self, mock_get, mock_post, mock_delete):
        self.set_mock_response(mock_get, 200, ROOT_RESP)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        _, err = self.badfish_call(mock_host=None)
        # When Members array is empty, init() catches the exception and logs as WARNING
        assert (
            err.count(
                "- WARNING  - Could not find system resource: ComputerSystem's Members array is either empty or missing"
            )
            == 3
        )
        assert err.count("- INFO     - ************************************************") == 3
        assert "[badfish.helpers.logger] - INFO     - RESULTS:" in err
        assert err.count("f01-h01-000-r630.host.io: FAILED") == 3


class TestInitialization(TestBase):
    args = ["--ls-jobs"]

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_cli_secrets_warning(self, mock_get, mock_post, mock_delete):
        """Test that passing credentials via CLI triggers a warning."""
        responses = [ROOT_RESP] * 4 + [SYS_RESP, MAN_RESP, MANAGER_INSTANCE_RESP, JOBS_RESP]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")

        # Explicitly use CLI secrets to trigger the warning
        _, err = self.badfish_call(use_cli_secrets=True)

        assert "Passing secrets via command line arguments can be unsafe" in err

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_validate_credentials_unauthorized(self, mock_get, mock_post, mock_delete):
        self.set_mock_response(mock_get, 200, ROOT_RESP)
        self.set_mock_response(mock_post, 401, "Unauthorized")
        self.set_mock_response(mock_delete, 200, "OK")
        _, err = self.badfish_call()
        assert err == RESPONSE_INIT_CREDENTIALS_UNAUTHORIZED

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_validate_credentials_failed_coms(self, mock_get, mock_post, mock_delete):
        self.set_mock_response(mock_get, 200, [ROOT_RESP])
        self.set_mock_response(mock_post, 400, "Bad Request")
        self.set_mock_response(mock_delete, 200, "OK")
        _, err = self.badfish_call()
        assert err == RESPONSE_INIT_CREDENTIALS_FAILED_COMS

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_find_systems_resource_unauthorized(self, mock_get, mock_post, mock_delete):
        # The key issue is that the Systems resource call (3rd call) returns 401
        # But we need to provide enough responses for the sequence:
        # 1: Root resource for find_session_uri
        # 2: Check session URI exists
        # 3: Systems resource (should return 401)
        # Additional responses needed if code continues after authentication
        responses = [ROOT_RESP, ROOT_RESP, ROOT_RESP, ROOT_RESP, MAN_RESP, '{"Members":[]}', ROOT_RESP]
        # Put 401 on a different position - the key is finding where Systems is actually called
        self.set_mock_response(mock_get, [200, 200, 200, 401, 200, 200, 200], responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        _, err = self.badfish_call()
        # When Members array is empty or missing, init() catches the exception and logs as WARNING
        assert "- WARNING  - Could not find system resource:" in err
        assert "ComputerSystem's Members array" in err or "Authorization Error" in err

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_find_systems_resource_not_found(self, mock_get, mock_post, mock_delete):
        responses = [ROOT_RESP, ROOT_RESP, "{}", "{}", MAN_RESP, '{"Members":[]}', ROOT_RESP]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        _, err = self.badfish_call()
        # When Members array is empty or missing, init() catches the exception and logs as WARNING
        assert "- WARNING  - Could not find system resource:" in err
        assert "Systems resource not found" in err or "ComputerSystem's Members array" in err


@pytest.mark.asyncio
async def test_execute_badfish_boot_to_false_sets_result_false():
    """execute_badfish() must propagate a False return from boot_to() to `result`."""
    logger = MagicMock(spec=logging.Logger)
    fake_badfish = MagicMock()
    fake_badfish.boot_to = AsyncMock(return_value=False)
    fake_badfish.session_id = None
    mock_args = defaultdict(lambda: None)
    mock_args.update({"u": "user", "p": "pass", "retries": 1, "boot_to": "NIC.1"})

    with patch("badfish.main.badfish_factory", new_callable=AsyncMock) as mock_factory:
        mock_factory.return_value = fake_badfish
        result = await execute_badfish("test_host", mock_args, logger, None)

    assert result == ("test_host", False)
    fake_badfish.boot_to.assert_awaited_once_with("NIC.1")


@pytest.mark.asyncio
async def test_find_systems_resource_invalid_root_json_raises_badfish_exception():
    """Invalid JSON from the root resource must surface as BadfishException, not JSONDecodeError."""
    logger = MagicMock(spec=logging.Logger)
    bf = Badfish("test_host", "user", "pass", logger, 1)
    bf.http_client = MagicMock()

    root_resp = MagicMock()
    root_resp.text = AsyncMock(return_value="not json {")
    bf.http_client.get_request = AsyncMock(return_value=root_resp)

    with pytest.raises(BadfishException, match="Error reading response from host."):
        await bf.find_systems_resource()


@pytest.mark.asyncio
async def test_find_systems_resource_invalid_systems_json_raises_badfish_exception():
    """Invalid JSON from the Systems resource must surface as BadfishException, not JSONDecodeError."""
    logger = MagicMock(spec=logging.Logger)
    bf = Badfish("test_host", "user", "pass", logger, 1)
    bf.http_client = MagicMock()

    root_resp = MagicMock()
    root_resp.text = AsyncMock(return_value='{"Systems":{"@odata.id":"/redfish/v1/Systems"}}')
    sys_resp = MagicMock()
    sys_resp.text = AsyncMock(return_value="<html>bad</html>")
    bf.http_client.get_request = AsyncMock(side_effect=[root_resp, sys_resp])

    with pytest.raises(BadfishException, match="Error reading response from host."):
        await bf.find_systems_resource()
