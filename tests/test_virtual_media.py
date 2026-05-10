from unittest.mock import patch

from tests.config import (
    BLANK_RESP,
    BOOT_MODE_RESP,
    BOOT_SEQ_RESP,
    BOOT_SEQ_RESPONSE_DIRECTOR,
    BOOT_SEQ_RESPONSE_OPTICAL,
    BOOT_SOURCE_OVERRIDE_TARGET_CD,
    BOOT_SOURCE_OVERRIDE_TARGET_USBCD,
    INIT_RESP,
    INIT_RESP_HPE,
    INIT_RESP_SUPERMICRO,
    JOB_OK_RESP,
    RESPONSE_BOOT_TO,
    VMEDIA_BOOT_TO_MISSING,
    VMEDIA_BOOT_TO_NO_MEDIA,
    VMEDIA_BOOT_TO_SM_FAIL,
    VMEDIA_BOOT_TO_SM_PASS,
    VMEDIA_CHECK_DISC_VALUE_ERROR,
    VMEDIA_CHECK_GOOD_DELL,
    VMEDIA_CHECK_GOOD_SM,
    VMEDIA_CONFIG_NO_CONFIG,
    VMEDIA_CONFIG_NO_RESOURCE,
    VMEDIA_GET_VM_CONFIG_EMPTY_RESP_SM,
    VMEDIA_GET_VM_CONFIG_RESP_DELL,
    VMEDIA_GET_VM_CONFIG_RESP_SM,
    VMEDIA_GET_VM_CONFIG_RESP_SM_WITH_MEMBERS,
    VMEDIA_MEMBER_CD_RESP,
    VMEDIA_MEMBER_RM_DISK_RESP,
    VMEDIA_MOUNT_ALREADY_FILLED,
    VMEDIA_MOUNT_NOT_ALLOWED,
    VMEDIA_MOUNT_SOMETHING_WRONG,
    VMEDIA_MOUNT_SUCCESS,
    VMEDIA_OS_DEPLOYMENT_NOT_SUPPORTED_CHECK,
    VMEDIA_OS_DEPLOYMENT_NOT_SUPPORTED_BOOT,
    VMEDIA_OS_DEPLOYMENT_NOT_SUPPORTED_DETACH,
    VMEDIA_REMOTE_BOOT_COMMAND_FAIL,
    VMEDIA_REMOTE_BOOT_GOOD,
    VMEDIA_REMOTE_BOOT_SOMETHING_WRONG,
    VMEDIA_REMOTE_BOOT_TASK_FAIL,
    VMEDIA_REMOTE_BOOT_TASK_FAILED_RESP,
    VMEDIA_REMOTE_BOOT_TASK_RESP,
    VMEDIA_REMOTE_BOOT_WRONG_PATH,
    VMEDIA_REMOTE_CHECK_ERROR,
    VMEDIA_REMOTE_CHECK_FAIL,
    VMEDIA_REMOTE_CHECK_GOOD,
    VMEDIA_REMOTE_CHECK_RESP,
    VMEDIA_REMOTE_DETACH_FAIL,
    VMEDIA_REMOTE_DETACH_GOOD,
    VMEDIA_UNMOUNT_EMPTY,
    VMEDIA_UNMOUNT_NOT_ALLOWED,
    VMEDIA_UNMOUNT_SOMETHING_WRONG,
    VMEDIA_UNMOUNT_SUCCESS,
)
from tests.test_base import TestBase


class TestCheckVirtualMedia(TestBase):
    option_arg = "--check-virtual-media"

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_config_no_resource(self, mock_get, mock_post, mock_delete):
        responses_get = [""]
        responses = INIT_RESP + responses_get
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == VMEDIA_CONFIG_NO_RESOURCE

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_config_empty_dell(self, mock_get, mock_post, mock_delete):
        responses_get = ["{}"]
        responses = INIT_RESP + responses_get
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == VMEDIA_CONFIG_NO_CONFIG

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_config_empty_sm(self, mock_get, mock_post, mock_delete):
        responses_get = ["{}"]
        responses = INIT_RESP_SUPERMICRO + responses_get
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == VMEDIA_CONFIG_NO_CONFIG

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_check_good_dell(self, mock_get, mock_post, mock_delete):
        responses_get = [
            VMEDIA_GET_VM_CONFIG_RESP_DELL,
            VMEDIA_MEMBER_RM_DISK_RESP,
            VMEDIA_MEMBER_CD_RESP,
        ]
        responses = INIT_RESP + responses_get
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == VMEDIA_CHECK_GOOD_DELL

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_check_value_error_dell(self, mock_get, mock_post, mock_delete):
        responses_get = [VMEDIA_GET_VM_CONFIG_RESP_DELL, "Bad Request"]
        responses = INIT_RESP + responses_get
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == VMEDIA_CHECK_DISC_VALUE_ERROR

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_check_good_sm(self, mock_get, mock_post, mock_delete):
        responses_get = [
            VMEDIA_GET_VM_CONFIG_RESP_SM_WITH_MEMBERS,
            VMEDIA_MEMBER_CD_RESP,
        ]
        responses = INIT_RESP_SUPERMICRO + responses_get
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == VMEDIA_CHECK_GOOD_SM

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_check_no_members_sm(self, mock_get, mock_post, mock_delete):
        responses_get = [VMEDIA_GET_VM_CONFIG_RESP_SM]
        responses = INIT_RESP_SUPERMICRO + responses_get
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == VMEDIA_GET_VM_CONFIG_EMPTY_RESP_SM


class TestMountVirtualMedia(TestBase):
    option_arg = "--mount-virtual-media"

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_mount_good_dell(self, mock_get, mock_post, mock_delete):
        responses_get = [VMEDIA_GET_VM_CONFIG_RESP_DELL]
        responses = INIT_RESP + responses_get
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 204], "OK", True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg, "http://storage.example.com/linux.iso"]
        _, err = self.badfish_call()
        assert err == VMEDIA_MOUNT_SUCCESS

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_mount_not_allowed_dell(self, mock_get, mock_post, mock_delete):
        responses_get = [VMEDIA_GET_VM_CONFIG_RESP_DELL]
        responses = INIT_RESP + responses_get
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 405], "OK", True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg, "http://storage.example.com/linux.iso"]
        _, err = self.badfish_call()
        assert err == VMEDIA_MOUNT_NOT_ALLOWED

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_mount_already_filled_dell(self, mock_get, mock_post, mock_delete):
        responses_get = [VMEDIA_GET_VM_CONFIG_RESP_DELL]
        responses = INIT_RESP + responses_get
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 500], "OK", True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg, "http://storage.example.com/linux.iso"]
        _, err = self.badfish_call()
        assert err == VMEDIA_MOUNT_ALREADY_FILLED

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_mount_something_wrong_dell(self, mock_get, mock_post, mock_delete):
        responses_get = [VMEDIA_GET_VM_CONFIG_RESP_DELL]
        responses = INIT_RESP + responses_get
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 400], "OK", True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg, "http://storage.example.com/linux.iso"]
        _, err = self.badfish_call()
        assert err == VMEDIA_MOUNT_SOMETHING_WRONG

    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_mount_good_sm(self, mock_get, mock_post, mock_delete, mock_patch):
        responses_get = [VMEDIA_GET_VM_CONFIG_RESP_SM]
        responses = INIT_RESP_SUPERMICRO + responses_get
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.set_mock_response(mock_patch, 200, "OK")
        self.args = [self.option_arg, "http://storage.example.com/linux.iso"]
        _, err = self.badfish_call()
        assert err == VMEDIA_MOUNT_SUCCESS

    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_mount_something_wrong_sm(self, mock_get, mock_post, mock_delete, mock_patch):
        responses_get = [VMEDIA_GET_VM_CONFIG_RESP_SM]
        responses = INIT_RESP_SUPERMICRO + responses_get
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 400], "OK", True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.set_mock_response(mock_patch, 200, "OK")
        self.args = [self.option_arg, "http://storage.example.com/linux.iso"]
        _, err = self.badfish_call()
        assert err == VMEDIA_MOUNT_SOMETHING_WRONG


class TestUnmountVirtualMedia(TestBase):
    option_arg = "--unmount-virtual-media"

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_unmount_good_dell(self, mock_get, mock_post, mock_delete):
        responses_get = [VMEDIA_GET_VM_CONFIG_RESP_DELL]
        responses = INIT_RESP + responses_get
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 204], "OK", True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == VMEDIA_UNMOUNT_SUCCESS

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_unmount_not_allowed_dell(self, mock_get, mock_post, mock_delete):
        responses_get = [VMEDIA_GET_VM_CONFIG_RESP_DELL]
        responses = INIT_RESP + responses_get
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 405], "OK", True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == VMEDIA_UNMOUNT_NOT_ALLOWED

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_unmount_empty_dell(self, mock_get, mock_post, mock_delete):
        responses_get = [VMEDIA_GET_VM_CONFIG_RESP_DELL]
        responses = INIT_RESP + responses_get
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 500], "OK", True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == VMEDIA_UNMOUNT_EMPTY

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_mount_something_wrong_dell(self, mock_get, mock_post, mock_delete):
        responses_get = [VMEDIA_GET_VM_CONFIG_RESP_DELL]
        responses = INIT_RESP + responses_get
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 400], "OK", True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == VMEDIA_UNMOUNT_SOMETHING_WRONG

    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_unmount_good_sm(self, mock_get, mock_post, mock_delete, mock_patch):
        responses_get = [VMEDIA_GET_VM_CONFIG_RESP_SM]
        responses = INIT_RESP_SUPERMICRO + responses_get
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.set_mock_response(mock_patch, 200, "OK")
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == VMEDIA_UNMOUNT_SUCCESS

    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_unmount_something_wrong_sm(self, mock_get, mock_post, mock_delete, mock_patch):
        responses_get = [VMEDIA_GET_VM_CONFIG_RESP_SM]
        responses = INIT_RESP_SUPERMICRO + responses_get
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 400], "OK", True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.set_mock_response(mock_patch, 200, "OK")
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == VMEDIA_UNMOUNT_SOMETHING_WRONG


class TestBootToVirtualMedia(TestBase):
    option_arg = "--boot-to-virtual-media"

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_no_media(self, mock_get, mock_post, mock_delete):
        responses_get = [VMEDIA_GET_VM_CONFIG_RESP_SM]
        responses = INIT_RESP_SUPERMICRO + responses_get
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == VMEDIA_BOOT_TO_NO_MEDIA

    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_good_dell(self, mock_get, mock_post, mock_delete, mock_patch):
        boot_seq_resp_fmt = BOOT_SEQ_RESP % str(BOOT_SEQ_RESPONSE_OPTICAL)
        responses_get = [
            VMEDIA_GET_VM_CONFIG_RESP_DELL,
            VMEDIA_MEMBER_RM_DISK_RESP,
            VMEDIA_MEMBER_CD_RESP,
            BOOT_MODE_RESP,
            boot_seq_resp_fmt.replace("'", '"'),
            BOOT_MODE_RESP,
            BOOT_MODE_RESP,
            boot_seq_resp_fmt.replace("'", '"'),
            BLANK_RESP,
        ]
        responses = INIT_RESP + responses_get
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, JOB_OK_RESP)
        self.set_mock_response(mock_delete, 200, "OK")
        self.set_mock_response(mock_patch, 200, "OK")
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == RESPONSE_BOOT_TO

    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_optical_missing_dell(self, mock_get, mock_post, mock_delete, mock_patch):
        boot_seq_resp_fmt = BOOT_SEQ_RESP % str(BOOT_SEQ_RESPONSE_DIRECTOR)
        responses_get = [
            VMEDIA_GET_VM_CONFIG_RESP_DELL,
            VMEDIA_MEMBER_RM_DISK_RESP,
            VMEDIA_MEMBER_CD_RESP,
            BOOT_MODE_RESP,
            boot_seq_resp_fmt.replace("'", '"'),
        ]
        responses = INIT_RESP + responses_get
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, JOB_OK_RESP)
        self.set_mock_response(mock_delete, 200, "OK")
        self.set_mock_response(mock_patch, 200, "OK")
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == VMEDIA_BOOT_TO_MISSING

    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_good_sm(self, mock_get, mock_post, mock_delete, mock_patch):
        responses_get = [
            VMEDIA_GET_VM_CONFIG_RESP_SM_WITH_MEMBERS,
            VMEDIA_MEMBER_CD_RESP,
            BOOT_SOURCE_OVERRIDE_TARGET_USBCD,
        ]
        responses = INIT_RESP_SUPERMICRO + responses_get
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.set_mock_response(mock_patch, 200, "OK")
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == VMEDIA_BOOT_TO_SM_PASS

    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_fail_sm(self, mock_get, mock_post, mock_delete, mock_patch):
        responses_get = [
            VMEDIA_GET_VM_CONFIG_RESP_SM_WITH_MEMBERS,
            VMEDIA_MEMBER_CD_RESP,
            BOOT_SOURCE_OVERRIDE_TARGET_CD,
        ]
        responses = INIT_RESP_SUPERMICRO + responses_get
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.set_mock_response(mock_patch, 400, "OK")
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == VMEDIA_BOOT_TO_SM_FAIL

    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_good_hpe(self, mock_get, mock_post, mock_delete, mock_patch):
        responses_get = [
            VMEDIA_GET_VM_CONFIG_RESP_DELL,
            VMEDIA_MEMBER_RM_DISK_RESP,
            VMEDIA_MEMBER_CD_RESP,
            BOOT_SOURCE_OVERRIDE_TARGET_USBCD,
        ]
        responses = INIT_RESP_HPE + responses_get
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.set_mock_response(mock_patch, 200, "OK")
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == VMEDIA_BOOT_TO_SM_PASS


class TestCheckRemoteImage(TestBase):
    option_arg = "--check-remote-image"

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_os_deployment_not_supported(self, mock_get, mock_post, mock_delete):
        responses_get = [BLANK_RESP]
        responses = INIT_RESP + responses_get
        self.set_mock_response(mock_get, [200, 200, 200, 200, 200, 404], responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == VMEDIA_OS_DEPLOYMENT_NOT_SUPPORTED_CHECK

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_check_good(self, mock_get, mock_post, mock_delete):
        responses_get = [BLANK_RESP]
        responses = INIT_RESP + responses_get
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, VMEDIA_REMOTE_CHECK_RESP)
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == VMEDIA_REMOTE_CHECK_GOOD

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_check_fail(self, mock_get, mock_post, mock_delete):
        responses_get = [BLANK_RESP]
        responses = INIT_RESP + responses_get
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 400], VMEDIA_REMOTE_CHECK_RESP, True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == VMEDIA_REMOTE_CHECK_FAIL

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_check_error(self, mock_get, mock_post, mock_delete):
        responses_get = [BLANK_RESP]
        responses = INIT_RESP + responses_get
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == VMEDIA_REMOTE_CHECK_ERROR


class TestBootRemoteImage(TestBase):
    option_arg = "--boot-remote-image"

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_boot_os_deployment_not_supported(self, mock_get, mock_post, mock_delete):
        responses_get = [BLANK_RESP]
        responses = INIT_RESP + responses_get
        self.set_mock_response(mock_get, [200, 200, 200, 200, 200, 404], responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg, "nfs.example.com:/mnt/storage/user1/linux.iso"]
        _, err = self.badfish_call()
        assert err == VMEDIA_OS_DEPLOYMENT_NOT_SUPPORTED_BOOT

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_boot_good(self, mock_get, mock_post, mock_delete):
        responses_get = [BLANK_RESP, VMEDIA_REMOTE_BOOT_TASK_RESP]
        responses = INIT_RESP + responses_get
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 202], "OK", True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg, "nfs.example.com:/mnt/storage/user1/linux.iso"]
        _, err = self.badfish_call()
        assert err == VMEDIA_REMOTE_BOOT_GOOD

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_boot_wrong_path(self, mock_get, mock_post, mock_delete):
        responses_get = [BLANK_RESP]
        responses = INIT_RESP + responses_get
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg, "wrong:path"]
        _, err = self.badfish_call()
        assert err == VMEDIA_REMOTE_BOOT_WRONG_PATH

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_boot_command_fail(self, mock_get, mock_post, mock_delete):
        responses_get = [BLANK_RESP]
        responses = INIT_RESP + responses_get
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 400], "OK", True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg, "nfs.example.com:/mnt/storage/user1/linux.iso"]
        _, err = self.badfish_call()
        assert err == VMEDIA_REMOTE_BOOT_COMMAND_FAIL

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_boot_task_fail(self, mock_get, mock_post, mock_delete):
        responses_get = [BLANK_RESP, VMEDIA_REMOTE_BOOT_TASK_FAILED_RESP]
        responses = INIT_RESP + responses_get
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 202], "OK", True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg, "nfs.example.com:/mnt/storage/user1/linux.iso"]
        _, err = self.badfish_call()
        assert err == VMEDIA_REMOTE_BOOT_TASK_FAIL

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_boot_something_wrong(self, mock_get, mock_post, mock_delete):
        responses_get = [BLANK_RESP, BLANK_RESP]
        responses = INIT_RESP + responses_get
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 202], "OK", True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg, "nfs.example.com:/mnt/storage/user1/linux.iso"]
        _, err = self.badfish_call()
        assert err == VMEDIA_REMOTE_BOOT_SOMETHING_WRONG


class TestDetachRemoteImage(TestBase):
    option_arg = "--detach-remote-image"

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_detach_os_deployment_not_supported(self, mock_get, mock_post, mock_delete):
        responses_get = [BLANK_RESP]
        responses = INIT_RESP + responses_get
        self.set_mock_response(mock_get, [200, 200, 200, 200, 200, 404], responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == VMEDIA_OS_DEPLOYMENT_NOT_SUPPORTED_DETACH

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_detach_good(self, mock_get, mock_post, mock_delete):
        responses_get = [BLANK_RESP]
        responses = INIT_RESP + responses_get
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == VMEDIA_REMOTE_DETACH_GOOD

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_detach_fail(self, mock_get, mock_post, mock_delete):
        responses_get = [BLANK_RESP]
        responses = INIT_RESP + responses_get
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, [200, 400], "OK", True)
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == VMEDIA_REMOTE_DETACH_FAIL
