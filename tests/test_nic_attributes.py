from unittest.mock import patch

from tests.config import (
    GET_FW_VERSION,
    GET_FW_VERSION_UNSUPPORTED,
    GET_NIC_ATTR_LIST,
    GET_NIC_ATTR_LIST_UPDATED,
    GET_NIC_ATTR_LIST_INTEGER_UPDATED,
    GET_NIC_ATTR_LIST_XXV710_NPARSRIOV,
    GET_NIC_ATTR_LIST_SINGLE_FUNCTION,
    GET_NIC_ATTR_LIST_VIRT_MODE_NONE,
    GET_NIC_ATTR_LIST_WITH_VF,
    GET_NIC_ATTR_REGISTRY,
    GET_NIC_ATTR_REGISTRY_WITH_VF,
    GET_NIC_FQQDS_ADAPTERS,
    GET_NIC_FQQDS_EMBEDDED,
    GET_NIC_FQQDS_INTEGRATED,
    GET_NIC_FQQDS_SLOT,
    INIT_RESP,
    INIT_RESP_SUPERMICRO,
    JOB_STATUS_SCHEDULED,
    JOB_STATUS_RUNNING,
    JOB_STATUS_COMPLETED,
    JOB_STATUS_FAILED,
    RESET_TYPE_RESP,
    RESPONSE_GET_NIC_ATTR_FW_BAD,
    RESPONSE_GET_NIC_ATTR_LIST_INVALID,
    RESPONSE_GET_NIC_ATTR_LIST_OK,
    RESPONSE_GET_NIC_ATTR_SPECIFIC,
    RESPONSE_GET_NIC_ATTR_SPECIFIC_LIST_FAIL,
    RESPONSE_GET_NIC_ATTR_SPECIFIC_REGISTRY_FAIL,
    RESPONSE_GET_NIC_ATTR_SPECIFIC_VERSION_UNSUPPORTED,
    RESPONSE_GET_NIC_FQQDS_INVALID,
    RESPONSE_GET_NIC_FQQDS_OK,
    RESPONSE_SET_NIC_ATTR_ALREADY_OK,
    RESPONSE_SET_NIC_ATTR_BAD_VALUE,
    RESPONSE_SET_NIC_ATTR_INT_MAXED,
    RESPONSE_SET_NIC_ATTR_OK,
    RESPONSE_SET_NIC_ATTR_RETRY_NOT_OK,
    RESPONSE_SET_NIC_ATTR_RETRY_OK,
    RESPONSE_SET_NIC_ATTR_STR_MAXED,
    RESPONSE_SET_NIC_ATTR_VIRT_MODE_NONE,
    RESPONSE_SET_NIC_ATTR_WITH_JOB_SUCCESS,
    RESPONSE_SET_NIC_ATTR_NO_JOB_ID,
    RESPONSE_SET_NIC_ATTR_PRE_REBOOT_FAIL,
    RESPONSE_SET_NIC_ATTR_VERIFY_FAILED,
    RESPONSE_SET_NIC_ATTR_FALSE_NEGATIVE,
    RESPONSE_SET_NIC_ATTR_VF_LIMIT_XXV710_WARNING,
    RESPONSE_VENDOR_UNSUPPORTED,
    STATE_OFF_RESP,
    STATE_ON_RESP,
)
from tests.test_base import TestBase


class TestNICFQDDs(TestBase):
    option_arg = "--get-nic-fqdds"

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_get_nic_fqdds_ok(self, mock_get, mock_post, mock_delete):
        responses = INIT_RESP + [
            GET_NIC_FQQDS_ADAPTERS,
            GET_NIC_FQQDS_EMBEDDED,
            GET_NIC_FQQDS_INTEGRATED,
            GET_NIC_FQQDS_SLOT,
        ]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [
            self.option_arg,
        ]
        _, err = self.badfish_call()
        assert err == RESPONSE_GET_NIC_FQQDS_OK

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_get_nic_fqdds_supermicro(self, mock_get, mock_post, mock_delete):
        responses = INIT_RESP_SUPERMICRO
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [
            self.option_arg,
        ]
        _, err = self.badfish_call()
        assert err == f"{RESPONSE_VENDOR_UNSUPPORTED}\n"

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_get_nic_fqdds_unsupported(self, mock_get, mock_post, mock_delete):
        responses = INIT_RESP + ["{}", "{}", "{}"]
        self.set_mock_response(mock_get, 404, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [
            self.option_arg,
        ]
        _, err = self.badfish_call()
        assert err == RESPONSE_VENDOR_UNSUPPORTED + "\n"

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_get_nic_fqdds_invalid(self, mock_get, mock_post, mock_delete):
        responses = INIT_RESP + ["{}"]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [
            self.option_arg,
        ]
        _, err = self.badfish_call()
        assert err == RESPONSE_GET_NIC_FQQDS_INVALID


class TestGetNICAttribute(TestBase):
    option_arg = "--get-nic-attribute"

    # LIST ALL ATTRIBUTES FOR A NIC
    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_get_nic_attr_list_ok(self, mock_get, mock_post, mock_delete):
        responses = INIT_RESP + [
            GET_NIC_ATTR_LIST,
        ]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [
            self.option_arg,
            "NIC.Embedded.1-1-1",
        ]
        _, err = self.badfish_call()
        assert err == RESPONSE_GET_NIC_ATTR_LIST_OK

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    @patch("badfish.main.Badfish.get_nic_attribute")
    def test_get_nic_attr_list_unsupported(self, mock_get_nic_attr, mock_get, mock_post, mock_delete):
        from badfish.main import BadfishException

        # Mock get_nic_attribute to raise BadfishException with vendor unsupported message
        mock_get_nic_attr.side_effect = BadfishException("Operation not supported by vendor.")

        self.set_mock_response(mock_get, 200, INIT_RESP)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [
            self.option_arg,
            "NIC.Embedded.1-1-1",
        ]
        _, err = self.badfish_call()
        assert err == f"{RESPONSE_VENDOR_UNSUPPORTED}\n"

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_get_nic_attr_list_invalid(self, mock_get, mock_post, mock_delete):
        responses = INIT_RESP + ["{}"]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [
            self.option_arg,
            "NIC.Embedded.1-1-1",
        ]
        _, err = self.badfish_call()
        assert err == RESPONSE_GET_NIC_ATTR_LIST_INVALID

    # LIST INFO ABOUT A SPECIFIC ATTRIBUTE
    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_get_nic_attr_info_ok(self, mock_get, mock_post, mock_delete):
        responses = INIT_RESP + [
            GET_FW_VERSION,
            GET_NIC_ATTR_REGISTRY,
            GET_NIC_ATTR_LIST,
        ]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg, "NIC.Embedded.1-1-1", "--attribute", "WakeOnLan"]
        _, err = self.badfish_call()
        assert err == RESPONSE_GET_NIC_ATTR_SPECIFIC

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    @patch("badfish.main.Badfish.get_idrac_fw_version")
    def test_get_nic_attr_fw_bad(self, mock_get_fw, mock_get, mock_post, mock_delete):
        async def fake_get_fw():
            # Emit via Badfish logger name to match formatting
            from logging import getLogger

            getLogger("badfish.helpers.logger").error("Operation not supported by vendor.")
            return 0

        mock_get_fw.side_effect = fake_get_fw

        self.set_mock_response(mock_get, 200, INIT_RESP)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg, "NIC.Embedded.1-1-1", "--attribute", "WakeOnLan"]
        _, err = self.badfish_call()
        assert err == RESPONSE_GET_NIC_ATTR_FW_BAD

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_get_nic_attr_info_vendor_unsupported(self, mock_get, mock_post, mock_delete):
        responses = INIT_RESP_SUPERMICRO + [
            GET_FW_VERSION,
        ]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg, "NIC.Embedded.1-1-1", "--attribute", "WakeOnLan"]
        _, err = self.badfish_call()
        assert err == f"{RESPONSE_VENDOR_UNSUPPORTED}\n"

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_get_nic_attr_info_version_unsupported(self, mock_get, mock_post, mock_delete):
        responses = INIT_RESP + [
            GET_FW_VERSION_UNSUPPORTED,
        ]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg, "NIC.Embedded.1-1-1", "--attribute", "WakeOnLan"]
        _, err = self.badfish_call()
        assert err == RESPONSE_GET_NIC_ATTR_SPECIFIC_VERSION_UNSUPPORTED

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_get_nic_attr_info_registry_fail(self, mock_get, mock_post, mock_delete):
        responses = INIT_RESP + [GET_FW_VERSION, "{}"]
        self.set_mock_response(mock_get, [200, 200, 200, 200, 200, 200, 404], responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg, "NIC.Embedded.1-1-1", "--attribute", "WakeOnLan"]
        _, err = self.badfish_call()
        assert err == RESPONSE_GET_NIC_ATTR_SPECIFIC_REGISTRY_FAIL

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_get_nic_attr_info_registry_empty(self, mock_get, mock_post, mock_delete):
        responses = INIT_RESP + [GET_FW_VERSION, "{}"]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg, "NIC.Embedded.1-1-1", "--attribute", "WakeOnLan"]
        _, err = self.badfish_call()
        assert err == RESPONSE_GET_NIC_ATTR_SPECIFIC_REGISTRY_FAIL

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_get_nic_attr_info_list_empty(self, mock_get, mock_post, mock_delete):
        responses = INIT_RESP + [
            GET_FW_VERSION,
            GET_NIC_ATTR_REGISTRY,
            "{}",
        ]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg, "NIC.Embedded.1-1-1", "--attribute", "WakeOnLan"]
        _, err = self.badfish_call()
        assert err == RESPONSE_GET_NIC_ATTR_SPECIFIC_LIST_FAIL


class TestSetNICAttribute(TestBase):
    option_arg = "--set-nic-attribute"

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_set_nic_attr_already_ok(self, mock_get, mock_post, mock_delete):
        responses = INIT_RESP + [
            GET_FW_VERSION,
            GET_NIC_ATTR_REGISTRY,
            GET_NIC_ATTR_LIST,
        ]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [
            self.option_arg,
            "NIC.Embedded.1-1-1",
            "--attribute",
            "WakeOnLan",
            "--value",
            "Enabled",
        ]
        _, err = self.badfish_call()
        assert err == RESPONSE_SET_NIC_ATTR_ALREADY_OK

    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_set_nic_attr_ok(self, mock_get, mock_post, mock_delete, mock_patch):
        responses = INIT_RESP + [
            GET_FW_VERSION,
            GET_NIC_ATTR_REGISTRY,
            GET_NIC_ATTR_LIST,
            RESET_TYPE_RESP,
            STATE_OFF_RESP,
        ]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.set_mock_response(mock_patch, 200, "OK", headers={})
        self.args = [
            self.option_arg,
            "NIC.Embedded.1-1-1",
            "--attribute",
            "WakeOnLan",
            "--value",
            "Disabled",
        ]
        _, err = self.badfish_call()
        assert err == RESPONSE_SET_NIC_ATTR_OK

    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_set_nic_attr_retry_ok(self, mock_get, mock_post, mock_delete, mock_patch):
        responses = INIT_RESP + [
            GET_FW_VERSION,
            GET_NIC_ATTR_REGISTRY,
            GET_NIC_ATTR_LIST,
            RESET_TYPE_RESP,
            STATE_OFF_RESP,
        ]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.set_mock_response(mock_patch, [503, 200], "OK", headers={})
        self.args = [
            self.option_arg,
            "NIC.Embedded.1-1-1",
            "--attribute",
            "WakeOnLan",
            "--value",
            "Disabled",
        ]
        _, err = self.badfish_call()
        assert err == RESPONSE_SET_NIC_ATTR_RETRY_OK

    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_set_nic_attr_retry_not_ok(self, mock_get, mock_post, mock_delete, mock_patch):
        responses = INIT_RESP + [
            GET_FW_VERSION,
            GET_NIC_ATTR_REGISTRY,
            GET_NIC_ATTR_LIST,
            RESET_TYPE_RESP,
            RESET_TYPE_RESP,
            STATE_OFF_RESP,
            STATE_ON_RESP,
            STATE_OFF_RESP,
        ]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.set_mock_response(mock_patch, [400, 200, 200], "OK", headers={})
        self.args = [
            self.option_arg,
            "NIC.Embedded.1-1-1",
            "--attribute",
            "WakeOnLan",
            "--value",
            "Disabled",
        ]
        _, err = self.badfish_call()
        assert err == RESPONSE_SET_NIC_ATTR_RETRY_NOT_OK

    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_set_nic_attr_str_ok(self, mock_get, mock_post, mock_delete, mock_patch):
        responses = INIT_RESP + [
            GET_FW_VERSION,
            GET_NIC_ATTR_REGISTRY,
            GET_NIC_ATTR_LIST,
            RESET_TYPE_RESP,
            STATE_OFF_RESP,
        ]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.set_mock_response(mock_patch, 200, "OK", headers={})
        self.args = [
            self.option_arg,
            "NIC.Embedded.1-1-1",
            "--attribute",
            "ChipMdl",
            "--value",
            "512",
        ]
        _, err = self.badfish_call()
        assert err == RESPONSE_SET_NIC_ATTR_OK

    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_set_nic_attr_str_maxed(self, mock_get, mock_post, mock_delete, mock_patch):
        responses = INIT_RESP + [
            GET_FW_VERSION,
            GET_NIC_ATTR_REGISTRY,
            GET_NIC_ATTR_LIST,
            RESET_TYPE_RESP,
            STATE_OFF_RESP,
        ]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.set_mock_response(mock_patch, 200, "OK", headers={})
        self.args = [
            self.option_arg,
            "NIC.Embedded.1-1-1",
            "--attribute",
            "ChipMdl",
            "--value",
            "a" * 1025,
        ]
        _, err = self.badfish_call()
        assert err == RESPONSE_SET_NIC_ATTR_STR_MAXED

    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_set_nic_attr_int_ok(self, mock_get, mock_post, mock_delete, mock_patch):
        responses = INIT_RESP + [
            GET_FW_VERSION,
            GET_NIC_ATTR_REGISTRY,
            GET_NIC_ATTR_LIST,
            RESET_TYPE_RESP,
            STATE_OFF_RESP,
        ]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.set_mock_response(mock_patch, 200, "OK", headers={})
        self.args = [
            self.option_arg,
            "NIC.Embedded.1-1-1",
            "--attribute",
            "BlnkLeds",
            "--value",
            "12",
        ]
        _, err = self.badfish_call()
        assert err == RESPONSE_SET_NIC_ATTR_OK

    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_set_nic_attr_int_maxed(self, mock_get, mock_post, mock_delete, mock_patch):
        responses = INIT_RESP + [
            GET_FW_VERSION,
            GET_NIC_ATTR_REGISTRY,
            GET_NIC_ATTR_LIST,
            RESET_TYPE_RESP,
            STATE_OFF_RESP,
        ]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.set_mock_response(mock_patch, 200, "OK", headers={})
        self.args = [
            self.option_arg,
            "NIC.Embedded.1-1-1",
            "--attribute",
            "BlnkLeds",
            "--value",
            "30",
        ]
        _, err = self.badfish_call()
        assert err == RESPONSE_SET_NIC_ATTR_INT_MAXED

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_set_nic_attr_bad_value(self, mock_get, mock_post, mock_delete):
        responses = INIT_RESP + [
            GET_FW_VERSION,
            GET_NIC_ATTR_REGISTRY,
            GET_NIC_ATTR_LIST,
        ]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [
            self.option_arg,
            "NIC.Embedded.1-1-1",
            "--attribute",
            "WakeOnLan",
            "--value",
            "BadValue",
        ]
        _, err = self.badfish_call()
        assert err == RESPONSE_SET_NIC_ATTR_BAD_VALUE

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_set_nic_attr_supermicro(self, mock_get, mock_post, mock_delete):
        responses = INIT_RESP_SUPERMICRO
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, responses)
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [
            self.option_arg,
            "NIC.Embedded.1-1-1",
            "--attribute",
            "WakeOnLan",
            "--value",
            "Enabled",
        ]
        _, err = self.badfish_call()
        assert err == f"{RESPONSE_VENDOR_UNSUPPORTED}\n"

    # ==================== Job Monitoring Tests (Issue #523 Fix) ====================

    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_set_nic_attr_with_job_monitoring_success(self, mock_get, mock_post, mock_delete, mock_patch):
        """Test successful NIC attribute change with full job monitoring"""
        responses = INIT_RESP + [
            GET_FW_VERSION,
            GET_NIC_ATTR_REGISTRY,
            GET_NIC_ATTR_LIST,
            JOB_STATUS_SCHEDULED,  # Pre-reboot job check
            RESET_TYPE_RESP,
            STATE_OFF_RESP,
            JOB_STATUS_COMPLETED,  # Post-reboot job monitoring
            GET_FW_VERSION,
            GET_NIC_ATTR_REGISTRY,
            GET_NIC_ATTR_LIST_UPDATED,  # Final verification
        ]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")

        # Mock PATCH response with Location header containing job ID
        patch_headers = {"Location": "/redfish/v1/Managers/iDRAC.Embedded.1/Jobs/JID_498218641680"}
        self.set_mock_response(mock_patch, 202, "OK", headers=patch_headers)

        self.args = [
            self.option_arg,
            "NIC.Embedded.1-1-1",
            "--attribute",
            "WakeOnLan",
            "--value",
            "Disabled",
        ]
        _, err = self.badfish_call()
        assert err == RESPONSE_SET_NIC_ATTR_WITH_JOB_SUCCESS

    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_set_nic_attr_no_job_id_fallback(self, mock_get, mock_post, mock_delete, mock_patch):
        """Test fallback behavior when no job ID is returned (preserves old behavior)"""
        responses = INIT_RESP + [
            GET_FW_VERSION,
            GET_NIC_ATTR_REGISTRY,
            GET_NIC_ATTR_LIST,
            RESET_TYPE_RESP,
            STATE_OFF_RESP,
        ]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")

        # PATCH succeeds but no Location header
        self.set_mock_response(mock_patch, 202, "OK", headers={})

        self.args = [
            self.option_arg,
            "NIC.Embedded.1-1-1",
            "--attribute",
            "WakeOnLan",
            "--value",
            "Disabled",
        ]
        _, err = self.badfish_call()
        assert err == RESPONSE_SET_NIC_ATTR_NO_JOB_ID

    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_set_nic_attr_job_failed_pre_reboot(self, mock_get, mock_post, mock_delete, mock_patch):
        """Test detection of job failure before reboot"""
        responses = INIT_RESP + [
            GET_FW_VERSION,
            GET_NIC_ATTR_REGISTRY,
            GET_NIC_ATTR_LIST,
            JOB_STATUS_FAILED,  # Job already failed before reboot
        ]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")

        patch_headers = {"Location": "/redfish/v1/Managers/iDRAC.Embedded.1/Jobs/JID_498218641680"}
        self.set_mock_response(mock_patch, 202, "OK", headers=patch_headers)

        self.args = [
            self.option_arg,
            "NIC.Embedded.1-1-1",
            "--attribute",
            "WakeOnLan",
            "--value",
            "Disabled",
        ]
        _, err = self.badfish_call()
        assert err == RESPONSE_SET_NIC_ATTR_PRE_REBOOT_FAIL

    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_set_nic_attr_job_completed_but_value_not_changed(self, mock_get, mock_post, mock_delete, mock_patch):
        """Test detection when job completes but value didn't actually change"""
        responses = INIT_RESP + [
            GET_FW_VERSION,
            GET_NIC_ATTR_REGISTRY,
            GET_NIC_ATTR_LIST,
            JOB_STATUS_SCHEDULED,  # Pre-reboot
            RESET_TYPE_RESP,
            STATE_OFF_RESP,
            JOB_STATUS_COMPLETED,  # Job says success
            GET_FW_VERSION,
            GET_NIC_ATTR_REGISTRY,
            GET_NIC_ATTR_LIST,  # But value is still old value (Enabled)
        ]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")

        patch_headers = {"Location": "/redfish/v1/Managers/iDRAC.Embedded.1/Jobs/JID_498218641680"}
        self.set_mock_response(mock_patch, 202, "OK", headers=patch_headers)

        self.args = [
            self.option_arg,
            "NIC.Embedded.1-1-1",
            "--attribute",
            "WakeOnLan",
            "--value",
            "Disabled",
        ]
        _, err = self.badfish_call()
        assert err == RESPONSE_SET_NIC_ATTR_VERIFY_FAILED

    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_set_nic_attr_job_failed_but_value_changed(self, mock_get, mock_post, mock_delete, mock_patch):
        """Test false negative detection: job reports failure but value actually changed"""
        responses = INIT_RESP + [
            GET_FW_VERSION,
            GET_NIC_ATTR_REGISTRY,
            GET_NIC_ATTR_LIST,
            JOB_STATUS_SCHEDULED,  # Pre-reboot
            RESET_TYPE_RESP,
            STATE_OFF_RESP,
            JOB_STATUS_FAILED,  # Job reports failure
            GET_FW_VERSION,  # But verification shows value DID change
            GET_NIC_ATTR_REGISTRY,
            GET_NIC_ATTR_LIST_UPDATED,
        ]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")

        patch_headers = {"Location": "/redfish/v1/Managers/iDRAC.Embedded.1/Jobs/JID_498218641680"}
        self.set_mock_response(mock_patch, 202, "OK", headers=patch_headers)

        self.args = [
            self.option_arg,
            "NIC.Embedded.1-1-1",
            "--attribute",
            "WakeOnLan",
            "--value",
            "Disabled",
        ]
        _, err = self.badfish_call()
        assert err == RESPONSE_SET_NIC_ATTR_FALSE_NEGATIVE

    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_set_nic_attr_integer_with_job_monitoring(self, mock_get, mock_post, mock_delete, mock_patch):
        """Test integer attribute with job monitoring - Issue #523 scenario"""
        responses = INIT_RESP + [
            GET_FW_VERSION,
            GET_NIC_ATTR_REGISTRY,
            GET_NIC_ATTR_LIST,  # BlnkLeds: 0
            JOB_STATUS_SCHEDULED,
            RESET_TYPE_RESP,
            STATE_OFF_RESP,
            JOB_STATUS_COMPLETED,
            GET_FW_VERSION,
            GET_NIC_ATTR_REGISTRY,
            GET_NIC_ATTR_LIST_INTEGER_UPDATED,  # BlnkLeds: 12
        ]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")

        patch_headers = {"Location": "/redfish/v1/Managers/iDRAC.Embedded.1/Jobs/JID_498218641680"}
        self.set_mock_response(mock_patch, 202, "OK", headers=patch_headers)

        self.args = [
            self.option_arg,
            "NIC.Embedded.1-1-1",
            "--attribute",
            "BlnkLeds",
            "--value",
            "12",
        ]
        _, err = self.badfish_call()
        # Should succeed with job monitoring
        assert "✓ Successfully changed BlnkLeds" in err
        assert "from 0 to 12" in err

    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_set_nic_attr_empty_location_header(self, mock_get, mock_post, mock_delete, mock_patch):
        """Test handling of empty Location header"""
        responses = INIT_RESP + [
            GET_FW_VERSION,
            GET_NIC_ATTR_REGISTRY,
            GET_NIC_ATTR_LIST,
            RESET_TYPE_RESP,
            STATE_OFF_RESP,
        ]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")

        # Location header present but empty
        patch_headers = {"Location": ""}
        self.set_mock_response(mock_patch, 202, "OK", headers=patch_headers)

        self.args = [
            self.option_arg,
            "NIC.Embedded.1-1-1",
            "--attribute",
            "WakeOnLan",
            "--value",
            "Disabled",
        ]
        _, err = self.badfish_call()
        # Should fall back to old behavior with warning
        assert "No job ID returned in Location header" in err
        assert "Configuration change submitted but job monitoring was not possible" in err

    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_set_nic_attr_vf_limit_xxv710_warning(self, mock_get, mock_post, mock_delete, mock_patch):
        """Test VF limit warning for Intel XXV710 with >64 VFs"""
        from tests.config import (
            GET_NIC_ATTR_REGISTRY_WITH_VF,
            GET_NIC_ATTR_LIST_WITH_VF,
            GET_NIC_ATTR_LIST_XXV710_NPARSRIOV,
        )

        responses = INIT_RESP + [
            GET_FW_VERSION,
            GET_NIC_ATTR_REGISTRY_WITH_VF,
            GET_NIC_ATTR_LIST_WITH_VF,  # get_nic_attribute_info call
            GET_NIC_ATTR_LIST_XXV710_NPARSRIOV,  # VirtualizationMode check
            GET_NIC_ATTR_LIST_XXV710_NPARSRIOV,  # VF limit check
            JOB_STATUS_SCHEDULED,  # Pre-reboot job check
            RESET_TYPE_RESP,
            STATE_OFF_RESP,
            JOB_STATUS_COMPLETED,  # Post-reboot job monitoring
            GET_FW_VERSION,
            GET_NIC_ATTR_REGISTRY_WITH_VF,
            GET_NIC_ATTR_LIST_XXV710_NPARSRIOV,  # Final verification (value still 64, not 128)
        ]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")

        patch_headers = {"Location": "/redfish/v1/Managers/iDRAC.Embedded.1/Jobs/JID_498218641680"}
        self.set_mock_response(mock_patch, 202, "OK", headers=patch_headers)

        self.args = [
            "--set-nic-attribute",
            "NIC.ChassisSlot.8-2-1",
            "--attribute",
            "NumberVFAdvertised",
            "--value",
            "128",
        ]
        _, err = self.badfish_call()
        # Should warn about XXV710 hardware limit
        assert "Attempting to set NumberVFAdvertised to 128 on Intel XXV710" in err
        assert "limited to 64 VFs" in err
        assert "hardware limit" in err

    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_set_nic_attr_vf_limit_valid_value_no_warning(self, mock_get, mock_post, mock_delete, mock_patch):
        """Test that valid VF values (≤64) don't trigger warnings"""
        from tests.config import (
            GET_NIC_ATTR_REGISTRY_WITH_VF,
            GET_NIC_ATTR_LIST_WITH_VF,
        )

        # Create updated list with NumberVFAdvertised set to 48
        import json

        updated_attrs = json.loads(GET_NIC_ATTR_LIST_WITH_VF)
        updated_attrs["Attributes"]["NumberVFAdvertised"] = "48"
        GET_NIC_ATTR_LIST_VF_48 = json.dumps(updated_attrs)

        responses = INIT_RESP + [
            GET_FW_VERSION,
            GET_NIC_ATTR_REGISTRY_WITH_VF,
            GET_NIC_ATTR_LIST_WITH_VF,  # get_nic_attribute_info call (current: 64)
            GET_NIC_ATTR_LIST_WITH_VF,  # VirtualizationMode check (SRIOV mode, not NONE)
            # No VF limit check call since value ≤64
            JOB_STATUS_SCHEDULED,  # Pre-reboot job check
            RESET_TYPE_RESP,
            STATE_OFF_RESP,
            JOB_STATUS_COMPLETED,  # Post-reboot job monitoring
            GET_FW_VERSION,
            GET_NIC_ATTR_REGISTRY_WITH_VF,
            GET_NIC_ATTR_LIST_VF_48,  # Final verification (changed to 48)
        ]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")

        patch_headers = {"Location": "/redfish/v1/Managers/iDRAC.Embedded.1/Jobs/JID_498218641680"}
        self.set_mock_response(mock_patch, 202, "OK", headers=patch_headers)

        self.args = [
            "--set-nic-attribute",
            "NIC.ChassisSlot.8-2-1",
            "--attribute",
            "NumberVFAdvertised",
            "--value",
            "48",
        ]
        _, err = self.badfish_call()
        # Should NOT warn for valid values ≤64
        assert "Attempting to set NumberVFAdvertised to" not in err
        assert "limited to 64 VFs" not in err
        # Should succeed
        assert "✓ Successfully changed NumberVFAdvertised" in err

    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_set_nic_attr_vf_limit_xxv710_sriov_mode(self, mock_get, mock_post, mock_delete, mock_patch):
        """Test VF limit warning for Intel XXV710 in SRIOV mode with >64 VFs"""
        from tests.config import (
            GET_NIC_ATTR_REGISTRY_WITH_VF,
            GET_NIC_ATTR_LIST_WITH_VF,
            GET_NIC_ATTR_LIST_SINGLE_FUNCTION,
        )

        responses = INIT_RESP + [
            GET_FW_VERSION,
            GET_NIC_ATTR_REGISTRY_WITH_VF,
            GET_NIC_ATTR_LIST_WITH_VF,  # get_nic_attribute_info call
            GET_NIC_ATTR_LIST_SINGLE_FUNCTION,  # VirtualizationMode check
            GET_NIC_ATTR_LIST_SINGLE_FUNCTION,  # VF limit check
            JOB_STATUS_SCHEDULED,  # Pre-reboot job check
            RESET_TYPE_RESP,
            STATE_OFF_RESP,
            JOB_STATUS_COMPLETED,  # Post-reboot job monitoring
            GET_FW_VERSION,
            GET_NIC_ATTR_REGISTRY_WITH_VF,
            GET_NIC_ATTR_LIST_SINGLE_FUNCTION,  # Final verification
        ]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")

        patch_headers = {"Location": "/redfish/v1/Managers/iDRAC.Embedded.1/Jobs/JID_498218641680"}
        self.set_mock_response(mock_patch, 202, "OK", headers=patch_headers)

        self.args = [
            "--set-nic-attribute",
            "NIC.ChassisSlot.8-2-1",
            "--attribute",
            "NumberVFAdvertised",
            "--value",
            "128",
        ]
        _, err = self.badfish_call()
        # Should warn about XXV710 hardware limit (SRIOV mode has same limit)
        assert "Attempting to set NumberVFAdvertised to 128 on Intel XXV710" in err
        assert "limited to 64 VFs" in err
        assert "hardware limit" in err

    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_set_nic_attr_vf_limit_exception_handling(self, mock_get, mock_post, mock_delete, mock_patch):
        """Test VF limit validation gracefully handles exceptions during attribute parsing"""
        from tests.config import (
            GET_NIC_ATTR_REGISTRY_WITH_VF,
            GET_NIC_ATTR_LIST_WITH_VF,
        )

        # NIC attrs with non-integer NumberPCIFunctionsEnabled to trigger ValueError in int() conversion
        ATTRS_WITH_INVALID_FUNCTION_COUNT = """
{
    "Attributes":{
        "DeviceName":"Intel(R) Ethernet Network Adapter XXV710",
        "VirtualizationMode":"SRIOV",
        "NumberPCIFunctionsEnabled":"NotANumber",
        "NumberVFAdvertised":"64",
        "NumberVFSupported":"128"
    }
}
"""

        responses = INIT_RESP + [
            GET_FW_VERSION,
            GET_NIC_ATTR_REGISTRY_WITH_VF,
            GET_NIC_ATTR_LIST_WITH_VF,  # get_nic_attribute_info call
            ATTRS_WITH_INVALID_FUNCTION_COUNT,  # get_nic_attribute returns data with invalid function count
            JOB_STATUS_SCHEDULED,  # Pre-reboot job check
            RESET_TYPE_RESP,
            STATE_OFF_RESP,
            JOB_STATUS_COMPLETED,  # Post-reboot job monitoring
            GET_FW_VERSION,
            GET_NIC_ATTR_REGISTRY_WITH_VF,
            GET_NIC_ATTR_LIST_WITH_VF,  # Final verification
        ]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")

        patch_headers = {"Location": "/redfish/v1/Managers/iDRAC.Embedded.1/Jobs/JID_498218641680"}
        self.set_mock_response(mock_patch, 202, "OK", headers=patch_headers)

        self.args = [
            "--set-nic-attribute",
            "NIC.ChassisSlot.8-2-1",
            "--attribute",
            "NumberVFAdvertised",
            "--value",
            "128",
        ]
        _, err = self.badfish_call()
        # Should gracefully handle ValueError exception and continue without warnings
        # Exception caught at line 2568, proceeds with attempt
        assert "Attempting to set NumberVFAdvertised" not in err  # No warning due to exception

    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_set_nic_attr_nonexistent_attribute(self, mock_get, mock_post, mock_delete, mock_patch):
        """Test set_nic_attribute when attribute doesn't exist (L2522-2523)"""
        # Return empty registry that won't match the requested attribute
        empty_registry = '{"RegistryEntries": {"Attributes": []}}'

        responses = INIT_RESP + [
            GET_FW_VERSION,
            empty_registry,  # Empty registry means attribute won't be found
        ]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.set_mock_response(mock_patch, 202, "OK")

        self.args = [
            "--set-nic-attribute",
            "NIC.Embedded.1-1-1",
            "--attribute",
            "NonExistentAttribute",
            "--value",
            "SomeValue",
        ]
        _, err = self.badfish_call()
        # Should error about attribute not existing (L2522-2523)
        assert "Was unable to set a network attribute" in err
        assert "Attribute most likely doesn't exist" in err

    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_monitor_verify_job_failed_value_mismatch(self, mock_get, mock_post, mock_delete, mock_patch):
        """Test _monitor_and_verify_attribute_job when job fails and value doesn't match (L996)"""
        responses = INIT_RESP + [
            GET_FW_VERSION,
            GET_NIC_ATTR_REGISTRY,
            GET_NIC_ATTR_LIST,  # Initial get
            JOB_STATUS_SCHEDULED,  # Pre-reboot verification
            RESET_TYPE_RESP,
            STATE_OFF_RESP,
            JOB_STATUS_FAILED,  # Post-reboot: job failed
            GET_FW_VERSION,
            GET_NIC_ATTR_REGISTRY,
            GET_NIC_ATTR_LIST,  # Post-reboot verification - value unchanged (still Enabled)
        ]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")

        patch_headers = {"Location": "/redfish/v1/Managers/iDRAC.Embedded.1/Jobs/JID_498218641680"}
        self.set_mock_response(mock_patch, 202, "OK", headers=patch_headers)

        self.args = [
            "--set-nic-attribute",
            "NIC.Embedded.1-1-1",
            "--attribute",
            "WakeOnLan",
            "--value",
            "Disabled",
        ]
        _, err = self.badfish_call()
        # Job failed and value didn't match - should return False (L996)
        assert "Configuration job" in err and "did not complete successfully" in err

    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_monitor_verify_final_check_returns_none(self, mock_get, mock_post, mock_delete, mock_patch):
        """Test _monitor_and_verify_attribute_job when final verification returns None (L1023-1024)"""
        # Create a response that will cause get_nic_attribute_info to fail
        empty_or_invalid_response = '{"Attributes": {}}'  # Missing the requested attribute

        responses = INIT_RESP + [
            GET_FW_VERSION,
            GET_NIC_ATTR_REGISTRY,
            GET_NIC_ATTR_LIST,  # Initial get
            JOB_STATUS_SCHEDULED,  # Pre-reboot verification
            RESET_TYPE_RESP,
            STATE_OFF_RESP,
            JOB_STATUS_COMPLETED,  # Post-reboot: job completed
            GET_FW_VERSION,
            GET_NIC_ATTR_REGISTRY,
            empty_or_invalid_response,  # get_nic_attribute call returns invalid data
        ]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")

        patch_headers = {"Location": "/redfish/v1/Managers/iDRAC.Embedded.1/Jobs/JID_498218641680"}
        self.set_mock_response(mock_patch, 202, "OK", headers=patch_headers)

        self.args = [
            "--set-nic-attribute",
            "NIC.Embedded.1-1-1",
            "--attribute",
            "WakeOnLan",
            "--value",
            "Disabled",
        ]
        _, err = self.badfish_call()
        # Should error about unable to verify final value (L1023-1024)
        assert "Could not verify final attribute value" in err or "Was unable to get network attribute" in err

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_set_nic_attr_virt_mode_none_numbervf(self, mock_get, mock_post, mock_delete):
        """Test setting NumberVFAdvertised when VirtualizationMode is NONE"""
        responses = INIT_RESP + [
            GET_FW_VERSION,
            GET_NIC_ATTR_REGISTRY_WITH_VF,
            GET_NIC_ATTR_LIST_VIRT_MODE_NONE,
            GET_NIC_ATTR_LIST_VIRT_MODE_NONE,  # Second call for VirtualizationMode check
        ]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")

        self.args = [
            "--set-nic-attribute",
            "NIC.Embedded.1-1-1",
            "--attribute",
            "NumberVFAdvertised",
            "--value",
            "128",
        ]
        _, err = self.badfish_call()
        assert "Cannot set NumberVFAdvertised when VirtualizationMode is NONE" in err
        assert "--set-nic-attribute NIC.Embedded.1-1-1 --attribute VirtualizationMode --value SRIOV" in err

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_set_nic_attr_virt_mode_none_non_sriov_attr(self, mock_get, mock_post, mock_delete):
        """Test setting non-SRIOV attribute (BlnkLeds) when VirtualizationMode is NONE - should not error about NONE"""
        responses = INIT_RESP + [
            GET_FW_VERSION,
            GET_NIC_ATTR_REGISTRY,
            GET_NIC_ATTR_LIST_VIRT_MODE_NONE,
            GET_NIC_ATTR_LIST_VIRT_MODE_NONE,
        ]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")

        self.args = [
            "--set-nic-attribute",
            "NIC.Embedded.1-1-1",
            "--attribute",
            "BlnkLeds",
            "--value",
            "5",
        ]
        _, err = self.badfish_call()
        # Should NOT get the VirtualizationMode NONE error - BlnkLeds is not an SRIOV attribute
        assert "Cannot set BlnkLeds when VirtualizationMode is NONE" not in err

    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_set_nic_attr_virt_mode_sriov_numbervf(self, mock_get, mock_post, mock_delete, mock_patch):
        """Test setting NumberVFAdvertised when VirtualizationMode is SRIOV - should proceed"""
        responses = INIT_RESP + [
            GET_FW_VERSION,
            GET_NIC_ATTR_REGISTRY_WITH_VF,
            GET_NIC_ATTR_LIST_SINGLE_FUNCTION,
            GET_NIC_ATTR_LIST_SINGLE_FUNCTION,  # For VirtualizationMode check
        ]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.set_mock_response(mock_patch, 200, "OK", headers={})

        self.args = [
            "--set-nic-attribute",
            "NIC.Embedded.1-1-1",
            "--attribute",
            "NumberVFAdvertised",
            "--value",
            "64",
        ]
        _, err = self.badfish_call()
        # Should NOT have the NONE error
        assert "Cannot set NumberVFAdvertised when VirtualizationMode is NONE" not in err

    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_set_nic_attr_catches_patch_exception(self, mock_get, mock_post, mock_delete, mock_patch):
        """Test set_nic_attribute handles PATCH exceptions gracefully"""
        responses = INIT_RESP + [
            GET_FW_VERSION,
            GET_NIC_ATTR_REGISTRY,
            GET_NIC_ATTR_LIST,
            GET_NIC_ATTR_LIST,  # VirtualizationMode check
        ]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")

        # Make PATCH context manager raise exception
        mock_patch.return_value.__aenter__.side_effect = ValueError("Test exception")

        self.args = [
            "--set-nic-attribute",
            "NIC.Embedded.1-1-1",
            "--attribute",
            "WakeOnLan",
            "--value",
            "Disabled",
        ]
        _, err = self.badfish_call()
        # Should catch and log error (may be "Failed to communicate" or "Was unable to set")
        assert "Was unable to set" in err or "Failed to communicate" in err or "ERROR" in err
