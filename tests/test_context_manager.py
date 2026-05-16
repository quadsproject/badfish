import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from badfish.main import Badfish, badfish_factory
from badfish.helpers.exceptions import BadfishException


class MockLogger:
    def __init__(self):
        self.debug_calls = []
        self.warning_calls = []
        self.info_calls = []
        self.error_calls = []

    def debug(self, message):
        self.debug_calls.append(message)

    def warning(self, message):
        self.warning_calls.append(message)

    def info(self, message):
        self.info_calls.append(message)

    def error(self, message):
        self.error_calls.append(message)


MOCK_HOST = "test-host.example.com"
MOCK_USERNAME = "test_user"
MOCK_PASSWORD = "test_password"
MOCK_RETRIES = 5


class TestContextManager:
    """Test cases for the async context manager methods."""

    @pytest.mark.asyncio
    async def test_context_manager_successful_entry_exit(self):
        """Test successful entry and exit of the context manager."""
        logger = MockLogger()
        badfish_instance = Badfish(MOCK_HOST, MOCK_USERNAME, MOCK_PASSWORD, logger, MOCK_RETRIES, _insecure=False)

        # Mock the init method
        with patch.object(badfish_instance, "init", new_callable=AsyncMock) as mock_init:
            with patch.object(badfish_instance, "delete_session", new_callable=AsyncMock) as mock_delete:
                async with badfish_instance as bf:
                    assert bf is badfish_instance
                    mock_init.assert_called_once()

                mock_delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager_exception_handling(self):
        """Test that exceptions are properly handled and logged."""
        logger = MockLogger()
        badfish_instance = Badfish(MOCK_HOST, MOCK_USERNAME, MOCK_PASSWORD, logger, MOCK_RETRIES, _insecure=False)

        # Mock the init method to raise an exception
        with patch.object(badfish_instance, "init", new_callable=AsyncMock) as mock_init:
            mock_init.side_effect = BadfishException("Test exception")

            with patch.object(badfish_instance, "delete_session", new_callable=AsyncMock) as mock_delete:
                with pytest.raises(BadfishException):
                    async with badfish_instance:
                        pass

                # When init fails, __aexit__ is not called because the exception is raised before entering the context
                mock_delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_context_manager_direct_method_calls(self):
        """Test direct calls to __aenter__ and __aexit__ methods."""
        logger = MockLogger()
        badfish_instance = Badfish(MOCK_HOST, MOCK_USERNAME, MOCK_PASSWORD, logger, MOCK_RETRIES, _insecure=False)

        with patch.object(badfish_instance, "init", new_callable=AsyncMock) as mock_init:
            with patch.object(badfish_instance, "delete_session", new_callable=AsyncMock) as mock_delete:
                # Test direct __aenter__ call
                result = await badfish_instance.__aenter__()
                assert result is badfish_instance
                mock_init.assert_called_once()

                # Test direct __aexit__ call
                await badfish_instance.__aexit__(None, None, None)
                mock_delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager_nested_usage(self):
        """Test nested usage of the context manager."""
        logger = MockLogger()
        badfish_instance = Badfish(MOCK_HOST, MOCK_USERNAME, MOCK_PASSWORD, logger, MOCK_RETRIES, _insecure=False)

        with patch.object(badfish_instance, "init", new_callable=AsyncMock) as mock_init:
            with patch.object(badfish_instance, "delete_session", new_callable=AsyncMock) as mock_delete:
                # First context manager usage
                async with badfish_instance as bf1:
                    assert bf1 is badfish_instance

                    # Nested context manager usage (should call init again)
                    async with badfish_instance as bf2:
                        assert bf2 is badfish_instance

                # delete_session should be called twice (once for each context)
                assert mock_delete.call_count == 2
                # init should be called twice (once for each context entry)
                assert mock_init.call_count == 2

    @pytest.mark.asyncio
    async def test_context_manager_integration_with_factory(self):
        """Test context manager integration with badfish_factory."""
        logger = MockLogger()

        with patch.object(Badfish, "init", new_callable=AsyncMock) as mock_init:
            with patch.object(Badfish, "delete_session", new_callable=AsyncMock) as mock_delete:
                async with await badfish_factory(
                    MOCK_HOST, MOCK_USERNAME, MOCK_PASSWORD, logger, MOCK_RETRIES
                ) as badfish:
                    assert isinstance(badfish, Badfish)
                    assert badfish.host == MOCK_HOST
                    assert badfish.username == MOCK_USERNAME
                    assert badfish.password == MOCK_PASSWORD
                    # badfish_factory calls init, then context manager calls it again
                    assert mock_init.call_count == 2

                mock_delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_badfish_factory_without_logger(self):
        """Test badfish_factory creates a default logger when none is provided."""
        with patch.object(Badfish, "init", new_callable=AsyncMock) as mock_init:
            with patch.object(Badfish, "delete_session", new_callable=AsyncMock):
                # Call badfish_factory WITHOUT a logger argument
                badfish = await badfish_factory(MOCK_HOST, MOCK_USERNAME, MOCK_PASSWORD)

                assert isinstance(badfish, Badfish)
                assert badfish.host == MOCK_HOST
                assert badfish.username == MOCK_USERNAME
                assert badfish.password == MOCK_PASSWORD
                # Verify a logger was created
                assert badfish.logger is not None
                mock_init.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager_session_cleanup(self):
        """Test that session cleanup happens even with exceptions."""
        logger = MockLogger()
        badfish_instance = Badfish(MOCK_HOST, MOCK_USERNAME, MOCK_PASSWORD, logger, MOCK_RETRIES, _insecure=False)

        with patch.object(badfish_instance, "init", new_callable=AsyncMock):
            with patch.object(badfish_instance, "delete_session", new_callable=AsyncMock) as mock_delete:
                try:
                    async with badfish_instance:
                        raise ValueError("Unexpected error")
                except ValueError:
                    pass

                # delete_session should still be called despite the exception
                mock_delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager_init_failure(self):
        """Test context manager behavior when init fails."""
        logger = MockLogger()
        badfish_instance = Badfish(MOCK_HOST, MOCK_USERNAME, MOCK_PASSWORD, logger, MOCK_RETRIES, _insecure=False)

        with patch.object(badfish_instance, "init", new_callable=AsyncMock) as mock_init:
            mock_init.side_effect = BadfishException("Init failed")

            with patch.object(badfish_instance, "delete_session", new_callable=AsyncMock) as mock_delete:
                with pytest.raises(BadfishException):
                    async with badfish_instance:
                        pass

                # When init fails, __aexit__ is not called
                mock_delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_context_manager_delete_session_failure(self):
        """Test context manager behavior when delete_session fails."""
        logger = MockLogger()
        badfish_instance = Badfish(MOCK_HOST, MOCK_USERNAME, MOCK_PASSWORD, logger, MOCK_RETRIES, _insecure=False)

        with patch.object(badfish_instance, "init", new_callable=AsyncMock):
            with patch.object(badfish_instance, "delete_session", new_callable=AsyncMock) as mock_delete:
                mock_delete.side_effect = BadfishException("Delete session failed")

                # The exception should be re-raised from __aexit__
                with pytest.raises(BadfishException):
                    async with badfish_instance:
                        pass


class TestDeleteSession:
    """Test cases for the delete_session method."""

    @pytest.mark.asyncio
    async def test_delete_session_success(self):
        """Test successful session deletion."""
        logger = MockLogger()
        badfish_instance = Badfish(MOCK_HOST, MOCK_USERNAME, MOCK_PASSWORD, logger, MOCK_RETRIES, _insecure=False)
        badfish_instance.session_id = "/redfish/v1/SessionService/Sessions/123"
        badfish_instance.token = "test_token"

        # Mock the delete_request method
        with patch.object(badfish_instance, "delete_request", new_callable=AsyncMock) as mock_delete_request:
            # Mock response with status 200
            mock_response = MagicMock()
            mock_response.status = 200
            mock_delete_request.return_value = mock_response

            await badfish_instance.delete_session()

            # Verify delete_request was called with correct parameters
            mock_delete_request.assert_called_once()
            call_args = mock_delete_request.call_args
            assert call_args[0][0] == f"https://{MOCK_HOST}/redfish/v1/SessionService/Sessions/123"
            assert call_args[1]["headers"] == {"content-type": "application/json"}

            # Verify session_id and token are cleared
            assert badfish_instance.session_id is None
            assert badfish_instance.token is None

            # Verify success message was logged
            assert any("Session successfully deleted" in call for call in logger.debug_calls)

    @pytest.mark.asyncio
    async def test_delete_session_404_status(self):
        """Test session deletion with 404 status (session not found)."""
        logger = MockLogger()
        badfish_instance = Badfish(MOCK_HOST, MOCK_USERNAME, MOCK_PASSWORD, logger, MOCK_RETRIES, _insecure=False)
        badfish_instance.session_id = "/redfish/v1/SessionService/Sessions/123"
        badfish_instance.token = "test_token"

        with patch.object(badfish_instance, "delete_request", new_callable=AsyncMock) as mock_delete_request:
            # Mock response with status 404
            mock_response = MagicMock()
            mock_response.status = 404
            mock_delete_request.return_value = mock_response

            await badfish_instance.delete_session()

            # Verify session_id and token are still cleared
            assert badfish_instance.session_id is None
            assert badfish_instance.token is None

            # Verify appropriate message was logged
            assert any("Session not found (404)" in call for call in logger.debug_calls)

    @pytest.mark.asyncio
    async def test_delete_session_unexpected_status(self):
        """Test session deletion with unexpected status code."""
        logger = MockLogger()
        badfish_instance = Badfish(MOCK_HOST, MOCK_USERNAME, MOCK_PASSWORD, logger, MOCK_RETRIES, _insecure=False)
        badfish_instance.session_id = "/redfish/v1/SessionService/Sessions/123"
        badfish_instance.token = "test_token"

        with patch.object(badfish_instance, "delete_request", new_callable=AsyncMock) as mock_delete_request:
            # Mock response with unexpected status
            mock_response = MagicMock()
            mock_response.status = 500
            mock_delete_request.return_value = mock_response

            await badfish_instance.delete_session()

            # Verify session_id and token are still cleared
            assert badfish_instance.session_id is None
            assert badfish_instance.token is None

            # Verify warning was logged
            assert any("Unexpected status 500" in call for call in logger.warning_calls)

    @pytest.mark.asyncio
    async def test_delete_session_exception_handling(self):
        """Test session deletion when delete_request raises an exception."""
        logger = MockLogger()
        badfish_instance = Badfish(MOCK_HOST, MOCK_USERNAME, MOCK_PASSWORD, logger, MOCK_RETRIES, _insecure=False)
        badfish_instance.session_id = "/redfish/v1/SessionService/Sessions/123"
        badfish_instance.token = "test_token"

        with patch.object(badfish_instance, "delete_request", new_callable=AsyncMock) as mock_delete_request:
            mock_delete_request.side_effect = BadfishException("Network error")

            await badfish_instance.delete_session()

            # Verify session_id and token are still cleared despite the exception
            assert badfish_instance.session_id is None
            assert badfish_instance.token is None

            # Verify exception was logged as warning
            assert any("Failed to delete session" in call for call in logger.warning_calls)
            assert any("Network error" in call for call in logger.warning_calls)

    @pytest.mark.asyncio
    async def test_delete_session_no_session_id(self):
        """Test delete_session when no session_id is set."""
        logger = MockLogger()
        badfish_instance = Badfish(MOCK_HOST, MOCK_USERNAME, MOCK_PASSWORD, logger, MOCK_RETRIES, _insecure=False)
        badfish_instance.session_id = None
        badfish_instance.token = "test_token"

        with patch.object(badfish_instance, "delete_request", new_callable=AsyncMock) as mock_delete_request:
            await badfish_instance.delete_session()

            # delete_request should not be called
            mock_delete_request.assert_not_called()

            # token should still be cleared
            assert badfish_instance.token is None

            # Verify appropriate message was logged
            assert any("No session ID found" in call for call in logger.debug_calls)

    @pytest.mark.asyncio
    async def test_delete_session_cleanup_always_executes(self):
        """Test that cleanup (clearing session_id and token) always executes."""
        logger = MockLogger()
        badfish_instance = Badfish(MOCK_HOST, MOCK_USERNAME, MOCK_PASSWORD, logger, MOCK_RETRIES, _insecure=False)
        badfish_instance.session_id = "/redfish/v1/SessionService/Sessions/123"
        badfish_instance.token = "test_token"

        with patch.object(badfish_instance, "delete_request", new_callable=AsyncMock) as mock_delete_request:
            # Mock response to raise an exception
            mock_delete_request.side_effect = Exception("Unexpected error")

            # The method should not raise the exception due to try/finally
            await badfish_instance.delete_session()

            # Verify session_id and token are still cleared despite the exception
            assert badfish_instance.session_id is None
            assert badfish_instance.token is None

    @pytest.mark.asyncio
    async def test_delete_session_other_exception(self):
        """Test delete_session with non-BadfishException."""
        logger = MockLogger()
        badfish_instance = Badfish(MOCK_HOST, MOCK_USERNAME, MOCK_PASSWORD, logger, MOCK_RETRIES, _insecure=False)
        badfish_instance.session_id = "/redfish/v1/SessionService/Sessions/123"
        badfish_instance.token = "test_token"

        with patch.object(badfish_instance, "delete_request", new_callable=AsyncMock) as mock_delete_request:
            # Mock response to raise a different exception
            mock_delete_request.side_effect = ValueError("Unexpected error")

            # The method should not raise the exception due to try/finally
            await badfish_instance.delete_session()

            # Verify session_id and token are still cleared
            assert badfish_instance.session_id is None
            assert badfish_instance.token is None

    @pytest.mark.asyncio
    async def test_delete_session_outer_exception_handler(self):
        """Test the outer exception handler that ensures cleanup even for unexpected exceptions."""
        logger = MockLogger()
        badfish_instance = Badfish(MOCK_HOST, MOCK_USERNAME, MOCK_PASSWORD, logger, MOCK_RETRIES, _insecure=False)
        badfish_instance.session_id = "/redfish/v1/SessionService/Sessions/123"
        badfish_instance.token = "test_token"

        # Mock the logger to raise an exception when debug is called
        # This will trigger the outer exception handler
        with patch.object(logger, "debug", side_effect=RuntimeError("Logger error")):
            with patch.object(badfish_instance, "delete_request", new_callable=AsyncMock) as mock_delete_request:
                # Mock successful response
                mock_response = MagicMock()
                mock_response.status = 200
                mock_delete_request.return_value = mock_response

                # The method should not raise the exception due to outer exception handler
                await badfish_instance.delete_session()

                # Verify session_id and token are still cleared despite the logger exception
                assert badfish_instance.session_id is None
                assert badfish_instance.token is None

                # Verify delete_request was called
                mock_delete_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_session_no_session_id_outer_exception(self):
        """Test outer exception handler when session_id is None and logger fails."""
        logger = MockLogger()
        badfish_instance = Badfish(MOCK_HOST, MOCK_USERNAME, MOCK_PASSWORD, logger, MOCK_RETRIES, _insecure=False)
        badfish_instance.session_id = None
        badfish_instance.token = "test_token"

        # Mock the logger to raise an exception when debug is called
        with patch.object(logger, "debug", side_effect=RuntimeError("Logger error")):
            with patch.object(badfish_instance, "delete_request", new_callable=AsyncMock) as mock_delete_request:
                # The method should not raise the exception due to outer exception handler
                await badfish_instance.delete_session()

                # Verify session_id and token are still cleared despite the logger exception
                assert badfish_instance.session_id is None
                assert badfish_instance.token is None

                # Verify delete_request was not called (since session_id was None)
                mock_delete_request.assert_not_called()


class TestExecuteBadfishSessionCleanup:
    """Test cases for session cleanup in execute_badfish function."""

    @pytest.mark.asyncio
    async def test_execute_badfish_session_cleanup_success(self):
        """Test successful session cleanup in execute_badfish."""
        from badfish.main import execute_badfish

        logger = MockLogger()
        args = {
            "u": MOCK_USERNAME,
            "p": MOCK_PASSWORD,
            "t": None,
            "i": None,
            "host_list": None,
            "output": None,
            "force": False,
            "pxe": False,
            "boot_to": None,
            "boot_to_type": None,
            "boot_to_mac": None,
            "reboot_only": False,
            "power_state": False,
            "power_on": False,
            "power_off": False,
            "power_cycle": False,
            "get_power_consumed": False,
            "racreset": False,
            "wait": False,
            "bmc_reset": False,
            "factory_reset": False,
            "check_boot": False,
            "toggle_boot_device": None,
            "firmware_inventory": False,
            "clear_jobs": False,
            "check_job": None,
            "ls_jobs": False,
            "ls_interfaces": False,
            "ls_processors": False,
            "ls_gpu": False,
            "ls_memory": False,
            "ls_serial": False,
            "check_virtual_media": False,
            "unmount_virtual_media": False,
            "mount_virtual_media": None,
            "boot_to_virtual_media": False,
            "check_remote_image": False,
            "boot_remote_image": None,
            "detach_remote_image": False,
            "get_sriov": False,
            "enable_sriov": False,
            "disable_sriov": False,
            "set_bios_attribute": False,
            "get_bios_attribute": False,
            "attribute": "",
            "value": "",
            "set_bios_password": False,
            "remove_bios_password": False,
            "new_password": "",
            "old_password": "",
            "screenshot": False,
            "retries": MOCK_RETRIES,
            "get_scp_targets": None,
            "scp_targets": "ALL",
            "scp_include_read_only": False,
            "export_scp": None,
            "import_scp": None,
            "get_nic_fqdds": False,
            "get_nic_attribute": None,
            "set_nic_attribute": None,
            "insecure": False,
            "timeout": 60,
        }

        with patch("badfish.main.badfish_factory") as mock_factory:
            # Mock badfish instance
            mock_badfish = MagicMock()
            mock_badfish.session_id = "/redfish/v1/SessionService/Sessions/123"
            mock_factory.return_value = mock_badfish

            # Mock successful operation
            with patch.object(mock_badfish, "delete_session", new_callable=AsyncMock) as mock_delete:
                host, result = await execute_badfish(MOCK_HOST, args, logger)

                assert host == MOCK_HOST
                assert result is True
                mock_delete.assert_called_once()
                assert any("Session closed for host" in call for call in logger.debug_calls)

    @pytest.mark.asyncio
    async def test_execute_badfish_session_cleanup_failure(self):
        """Test session cleanup failure in execute_badfish."""
        from badfish.main import execute_badfish

        logger = MockLogger()
        args = {
            "u": MOCK_USERNAME,
            "p": MOCK_PASSWORD,
            "t": None,
            "i": None,
            "host_list": None,
            "output": None,
            "force": False,
            "pxe": False,
            "boot_to": None,
            "boot_to_type": None,
            "boot_to_mac": None,
            "reboot_only": False,
            "power_state": False,
            "power_on": False,
            "power_off": False,
            "power_cycle": False,
            "get_power_consumed": False,
            "racreset": False,
            "wait": False,
            "bmc_reset": False,
            "factory_reset": False,
            "check_boot": False,
            "toggle_boot_device": None,
            "firmware_inventory": False,
            "clear_jobs": False,
            "check_job": None,
            "ls_jobs": False,
            "ls_interfaces": False,
            "ls_processors": False,
            "ls_gpu": False,
            "ls_memory": False,
            "ls_serial": False,
            "check_virtual_media": False,
            "unmount_virtual_media": False,
            "mount_virtual_media": None,
            "boot_to_virtual_media": False,
            "check_remote_image": False,
            "boot_remote_image": None,
            "detach_remote_image": False,
            "get_sriov": False,
            "enable_sriov": False,
            "disable_sriov": False,
            "set_bios_attribute": False,
            "get_bios_attribute": False,
            "attribute": "",
            "value": "",
            "set_bios_password": False,
            "remove_bios_password": False,
            "new_password": "",
            "old_password": "",
            "screenshot": False,
            "retries": MOCK_RETRIES,
            "get_scp_targets": None,
            "scp_targets": "ALL",
            "scp_include_read_only": False,
            "export_scp": None,
            "import_scp": None,
            "get_nic_fqdds": False,
            "get_nic_attribute": None,
            "set_nic_attribute": None,
            "insecure": False,
            "timeout": 60,
        }

        with patch("badfish.main.badfish_factory") as mock_factory:
            # Mock badfish instance
            mock_badfish = MagicMock()
            mock_badfish.session_id = "/redfish/v1/SessionService/Sessions/123"
            mock_factory.return_value = mock_badfish

            # Mock delete_session to raise an exception
            with patch.object(mock_badfish, "delete_session", new_callable=AsyncMock) as mock_delete:
                mock_delete.side_effect = BadfishException("Session cleanup failed")

                host, result = await execute_badfish(MOCK_HOST, args, logger)

                assert host == MOCK_HOST
                assert result is True
                mock_delete.assert_called_once()
                # Verify warning message was logged
                assert any("Failed to close session for" in call for call in logger.warning_calls)
                assert any("Session cleanup failed" in call for call in logger.warning_calls)

    @pytest.mark.asyncio
    async def test_execute_badfish_no_session_cleanup(self):
        """Test execute_badfish when no session exists to clean up."""
        from badfish.main import execute_badfish

        logger = MockLogger()
        args = {
            "u": MOCK_USERNAME,
            "p": MOCK_PASSWORD,
            "t": None,
            "i": None,
            "host_list": None,
            "output": None,
            "force": False,
            "pxe": False,
            "boot_to": None,
            "boot_to_type": None,
            "boot_to_mac": None,
            "reboot_only": False,
            "power_state": False,
            "power_on": False,
            "power_off": False,
            "power_cycle": False,
            "get_power_consumed": False,
            "racreset": False,
            "wait": False,
            "bmc_reset": False,
            "factory_reset": False,
            "check_boot": False,
            "toggle_boot_device": None,
            "firmware_inventory": False,
            "clear_jobs": False,
            "check_job": None,
            "ls_jobs": False,
            "ls_interfaces": False,
            "ls_processors": False,
            "ls_gpu": False,
            "ls_memory": False,
            "ls_serial": False,
            "check_virtual_media": False,
            "unmount_virtual_media": False,
            "mount_virtual_media": None,
            "boot_to_virtual_media": False,
            "check_remote_image": False,
            "boot_remote_image": None,
            "detach_remote_image": False,
            "get_sriov": False,
            "enable_sriov": False,
            "disable_sriov": False,
            "set_bios_attribute": False,
            "get_bios_attribute": False,
            "attribute": "",
            "value": "",
            "set_bios_password": False,
            "remove_bios_password": False,
            "new_password": "",
            "old_password": "",
            "screenshot": False,
            "retries": MOCK_RETRIES,
            "get_scp_targets": None,
            "scp_targets": "ALL",
            "scp_include_read_only": False,
            "export_scp": None,
            "import_scp": None,
            "get_nic_fqdds": False,
            "get_nic_attribute": None,
            "set_nic_attribute": None,
            "insecure": False,
            "timeout": 60,
        }

        with patch("badfish.main.badfish_factory") as mock_factory:
            # Mock badfish instance with no session_id
            mock_badfish = MagicMock()
            mock_badfish.session_id = None
            mock_factory.return_value = mock_badfish

            # Mock delete_session
            with patch.object(mock_badfish, "delete_session", new_callable=AsyncMock) as mock_delete:
                host, result = await execute_badfish(MOCK_HOST, args, logger)

                assert host == MOCK_HOST
                assert result is True
                # delete_session should not be called when session_id is None
                mock_delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_badfish_no_badfish_instance(self):
        """Test execute_badfish when badfish instance is None."""
        from badfish.main import execute_badfish

        logger = MockLogger()
        args = {
            "u": MOCK_USERNAME,
            "p": MOCK_PASSWORD,
            "t": None,
            "i": None,
            "host_list": None,
            "output": None,
            "force": False,
            "pxe": False,
            "boot_to": None,
            "boot_to_type": None,
            "boot_to_mac": None,
            "reboot_only": False,
            "power_state": False,
            "power_on": False,
            "power_off": False,
            "power_cycle": False,
            "get_power_consumed": False,
            "racreset": False,
            "wait": False,
            "bmc_reset": False,
            "factory_reset": False,
            "check_boot": False,
            "toggle_boot_device": None,
            "firmware_inventory": False,
            "clear_jobs": False,
            "check_job": None,
            "ls_jobs": False,
            "ls_interfaces": False,
            "ls_processors": False,
            "ls_gpu": False,
            "ls_memory": False,
            "ls_serial": False,
            "check_virtual_media": False,
            "unmount_virtual_media": False,
            "mount_virtual_media": None,
            "boot_to_virtual_media": False,
            "check_remote_image": False,
            "boot_remote_image": None,
            "detach_remote_image": False,
            "get_sriov": False,
            "enable_sriov": False,
            "disable_sriov": False,
            "set_bios_attribute": False,
            "get_bios_attribute": False,
            "attribute": "",
            "value": "",
            "set_bios_password": False,
            "remove_bios_password": False,
            "new_password": "",
            "old_password": "",
            "screenshot": False,
            "retries": MOCK_RETRIES,
            "get_scp_targets": None,
            "scp_targets": "ALL",
            "scp_include_read_only": False,
            "export_scp": None,
            "import_scp": None,
            "get_nic_fqdds": False,
            "get_nic_attribute": None,
            "set_nic_attribute": None,
            "insecure": False,
            "timeout": 60,
        }

        with patch("badfish.main.badfish_factory") as mock_factory:
            # Mock badfish_factory to raise an exception
            mock_factory.side_effect = BadfishException("Connection failed")

            host, result = await execute_badfish(MOCK_HOST, args, logger)

            assert host == MOCK_HOST
            assert result is False
            # No session cleanup should happen when badfish is None
            assert not any("Session closed for host" in call for call in logger.debug_calls)
            assert not any("Failed to close session for" in call for call in logger.warning_calls)
