import logging
from collections import defaultdict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from badfish.main import execute_badfish


async def _execute_with_handler(handler, return_value, extra_args=None, flag=None):
    """Run execute_badfish with a single handler stubbed to `return_value`."""
    fake_badfish = MagicMock()
    setattr(fake_badfish, handler, AsyncMock(return_value=return_value))
    fake_badfish.session_id = None
    fake_badfish.logger = MagicMock()

    mock_args = defaultdict(lambda: None)
    mock_args.update({"u": "user", "p": "pass", "retries": 1})
    if flag is not None:
        mock_args[flag] = True
    if extra_args:
        mock_args.update(extra_args)

    with patch("badfish.main.badfish_factory", new_callable=AsyncMock) as mock_factory:
        mock_factory.return_value = fake_badfish
        result = await execute_badfish("test_host", mock_args, MagicMock(spec=logging.Logger), None)

    return result, fake_badfish


# Handlers whose `False` means the operation *failed* and therefore must
# drive the CLI exit code to 1 (execute_badfish returns result=False).
FAILURE_HANDLERS = [
    ("get_power_consumed", "get_power_consumed_watts", None),
    ("ls_interfaces", "list_interfaces", None),
    ("racreset", "reset_idrac", None),
    ("bmc_reset", "reset_bmc", None),
    ("mount_virtual_media", "mount_virtual_media", {"mount_virtual_media": "http://img.iso"}),
    ("unmount_virtual_media", "unmount_virtual_media", None),
    ("check_job", "check_schedule_job_status", {"check_job": "JID_1"}),
    ("set_bios_password", "set_bios_password", {"old_password": "old", "new_password": "new"}),
    ("remove_bios_password", "remove_bios_password", {"old_password": "old"}),
    ("get_scp_targets", "get_scp_targets", {"get_scp_targets": "export"}),
    ("export_scp", "export_scp", {"export_scp": "/tmp/x.json", "scp_targets": "ALL"}),
    ("import_scp", "import_scp", {"import_scp": "/tmp/x.json", "scp_targets": "ALL"}),
    ("get_nic_fqdds", "get_nic_fqdds", None),
    ("get_nic_attribute", "get_nic_attribute", None),
    ("set_nic_attribute", "set_nic_attribute", {"attribute": "x", "value": "y"}),
    ("ls_gpu", "list_gpu", None),
]


@pytest.mark.parametrize("flag, handler, extra_args", FAILURE_HANDLERS)
@pytest.mark.asyncio
async def test_handler_false_returns_failure_result(flag, handler, extra_args):
    """A False return from an operation-failure handler must yield result=False (exit 1)."""
    result, _ = await _execute_with_handler(handler, False, extra_args, flag)
    assert result == ("test_host", False)


@pytest.mark.parametrize("flag, handler, extra_args", FAILURE_HANDLERS)
@pytest.mark.asyncio
async def test_handler_true_returns_success_result(flag, handler, extra_args):
    """A True return from an operation-failure handler must yield result=True (exit 0)."""
    result, _ = await _execute_with_handler(handler, True, extra_args, flag)
    assert result == ("test_host", True)


@pytest.mark.asyncio
async def test_handler_none_success_not_treated_as_failure():
    """Handlers that return None on success (e.g. set_bios_password) must not exit 1."""
    # set_bios_password -> change_bios_password returns None on success
    result, _ = await _execute_with_handler(
        "set_bios_password", None, {"old_password": "old", "new_password": "new"}, "set_bios_password"
    )
    assert result == ("test_host", True)


@pytest.mark.asyncio
async def test_check_virtual_media_false_is_informational():
    """check_virtual_media returning False (nothing mounted) is not an operation failure."""
    result, _ = await _execute_with_handler("check_virtual_media", False, None, "check_virtual_media")
    assert result == ("test_host", True)


@pytest.mark.asyncio
async def test_check_remote_image_false_is_informational():
    """check_remote_image returning False (not attached/unsupported) is not an operation failure."""
    result, _ = await _execute_with_handler("check_remote_image", False, None, "check_remote_image")
    assert result == ("test_host", True)
