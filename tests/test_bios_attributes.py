import json
from unittest.mock import patch

from tests.config import (
    ATTR_VALUE_BAD,
    ATTR_VALUE_DIS,
    ATTR_VALUE_DIS_2,
    ATTR_VALUE_OK,
    ATTR_VALUE_OK_2,
    ATTRIBUTE_BAD,
    ATTRIBUTE_OK,
    ATTRIBUTE_OK_2,
    BIOS_GET_ALL_OK,
    BIOS_GET_ONE_BAD,
    BIOS_GET_ONE_OK,
    BIOS_REGISTRY_MULTI,
    BIOS_REGISTRY_OK,
    BIOS_RESPONSE_DIS,
    BIOS_RESPONSE_MULTI,
    BIOS_RESPONSE_OK,
    BIOS_SET_BAD_ATTR,
    BIOS_SET_BAD_VALUE,
    BIOS_SET_MULTI_BAD_PAIR,
    BIOS_SET_MULTI_BAD_VALUE,
    BIOS_SET_OK,
    INIT_RESP,
    JOB_OK_RESP,
    RESET_TYPE_RESP,
    STATE_ON_RESP,
)
from tests.test_base import TestBase


class TestSetBiosAttribute(TestBase):
    option_arg = "--set-bios-attribute"

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.get")
    def test_set_bios_attribute_ok(self, mock_get, mock_patch, mock_post, mock_delete):
        get_resp = [
            BIOS_REGISTRY_OK.replace("'", '"'),
            BIOS_RESPONSE_DIS,
            RESET_TYPE_RESP,
            STATE_ON_RESP,
            STATE_ON_RESP,
        ]
        responses = INIT_RESP + get_resp
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_patch, 200, ["OK"])
        self.set_mock_response(mock_post, 200, ["OK", JOB_OK_RESP])
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [
            self.option_arg,
            "--attribute",
            ATTRIBUTE_OK,
            "--value",
            ATTR_VALUE_OK,
        ]
        _, err = self.badfish_call()
        assert err == BIOS_SET_OK

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.get")
    def test_set_bios_attribute_bad_value(self, mock_get, mock_patch, mock_post, mock_delete):
        get_resp = [
            BIOS_REGISTRY_OK.replace("'", '"'),
            BIOS_RESPONSE_DIS,
            BIOS_RESPONSE_DIS,
        ]
        responses = INIT_RESP + get_resp
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_patch, 200, ["OK"])
        self.set_mock_response(mock_post, 200, ["OK", JOB_OK_RESP])
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [
            self.option_arg,
            "--attribute",
            ATTRIBUTE_OK,
            "--value",
            ATTR_VALUE_BAD,
        ]
        _, err = self.badfish_call()
        assert err == BIOS_SET_BAD_VALUE

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.get")
    def test_set_bios_attribute_bad_attr(self, mock_get, mock_patch, mock_post, mock_delete):
        get_resp = [
            BIOS_REGISTRY_OK.replace("'", '"'),
            BIOS_RESPONSE_DIS,
        ]
        responses = INIT_RESP + get_resp
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_patch, 200, ["OK"])
        self.set_mock_response(mock_post, 200, ["OK", JOB_OK_RESP])
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [
            self.option_arg,
            "--attribute",
            ATTRIBUTE_BAD,
            "--value",
            ATTR_VALUE_OK,
        ]
        _, err = self.badfish_call()
        assert err == BIOS_SET_BAD_ATTR

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.get")
    def test_set_bios_attribute_multi_ok(self, mock_get, mock_patch, mock_post, mock_delete):
        get_resp = [
            BIOS_REGISTRY_MULTI.replace("'", '"'),
            BIOS_RESPONSE_MULTI,
            RESET_TYPE_RESP,
            STATE_ON_RESP,
            STATE_ON_RESP,
        ]
        responses = INIT_RESP + get_resp
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_patch, 200, ["OK"])
        self.set_mock_response(mock_post, 200, ["OK", JOB_OK_RESP])
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [
            self.option_arg,
            "--attribute-value",
            f"{ATTRIBUTE_OK}={ATTR_VALUE_OK}",
            "--attribute-value",
            f"{ATTRIBUTE_OK_2}={ATTR_VALUE_OK_2}",
        ]
        _, err = self.badfish_call()
        assert err == BIOS_SET_OK
        assert mock_patch.call_count == 1
        payload = json.loads(mock_patch.call_args.kwargs["data"])["Attributes"]
        assert payload == {ATTRIBUTE_OK: ATTR_VALUE_OK, ATTRIBUTE_OK_2: ATTR_VALUE_OK_2}

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.get")
    def test_set_bios_attribute_multi_bad_value(self, mock_get, mock_patch, mock_post, mock_delete):
        get_resp = [
            BIOS_REGISTRY_MULTI.replace("'", '"'),
            BIOS_RESPONSE_MULTI,
        ]
        responses = INIT_RESP + get_resp
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_patch, 200, ["OK"])
        self.set_mock_response(mock_post, 200, ["OK", JOB_OK_RESP])
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [
            self.option_arg,
            "--attribute-value",
            f"{ATTRIBUTE_OK}={ATTR_VALUE_OK}",
            "--attribute-value",
            f"{ATTRIBUTE_OK_2}={ATTR_VALUE_BAD}",
        ]
        _, err = self.badfish_call()
        assert err == BIOS_SET_MULTI_BAD_VALUE
        assert mock_patch.call_count == 0

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.get")
    def test_set_bios_attribute_bad_pair(self, mock_get, mock_patch, mock_post, mock_delete):
        responses = INIT_RESP
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_patch, 200, ["OK"])
        self.set_mock_response(mock_post, 200, ["OK", JOB_OK_RESP])
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg, "--attribute-value", ATTRIBUTE_OK]
        _, err = self.badfish_call()
        assert err == BIOS_SET_MULTI_BAD_PAIR
        assert mock_patch.call_count == 0

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.get")
    def test_set_bios_attribute_multi_duplicate(self, mock_get, mock_patch, mock_post, mock_delete):
        responses = INIT_RESP
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_patch, 200, ["OK"])
        self.set_mock_response(mock_post, 200, ["OK", JOB_OK_RESP])
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [
            self.option_arg,
            "--attribute-value",
            f"{ATTRIBUTE_OK}={ATTR_VALUE_OK}",
            "--attribute-value",
            f"{ATTRIBUTE_OK}={ATTR_VALUE_DIS}",
        ]
        _, err = self.badfish_call()
        assert f"Duplicate BIOS attribute supplied: {ATTRIBUTE_OK}" in err
        assert mock_patch.call_count == 0
        assert mock_post.call_count == 0

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.get")
    def test_set_bios_attribute_mixed_flags(self, mock_get, mock_patch, mock_post, mock_delete):
        responses = INIT_RESP
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_patch, 200, ["OK"])
        self.set_mock_response(mock_post, 200, ["OK", JOB_OK_RESP])
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [
            self.option_arg,
            "--attribute",
            ATTRIBUTE_OK,
            "--value",
            ATTR_VALUE_OK,
            "--attribute-value",
            f"{ATTRIBUTE_OK_2}={ATTR_VALUE_OK_2}",
        ]
        _, err = self.badfish_call()
        assert "Use either --attribute/--value or --attribute-value, not both" in err
        assert mock_patch.call_count == 0

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.get")
    def test_set_bios_attribute_missing_flag(self, mock_get, mock_patch, mock_post, mock_delete):
        responses = INIT_RESP
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_patch, 200, ["OK"])
        self.set_mock_response(mock_post, 200, ["OK", JOB_OK_RESP])
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = ["--attribute-value", f"{ATTRIBUTE_OK}={ATTR_VALUE_OK}"]
        _, err = self.badfish_call()
        assert "--attribute-value requires --set-bios-attribute" in err
        assert mock_patch.call_count == 0

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.get")
    def test_set_bios_attribute_multi_already_state(self, mock_get, mock_patch, mock_post, mock_delete):
        get_resp = [
            BIOS_REGISTRY_MULTI.replace("'", '"'),
            BIOS_RESPONSE_MULTI,
        ]
        responses = INIT_RESP + get_resp
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_patch, 200, ["OK"])
        self.set_mock_response(mock_post, 200, ["OK", JOB_OK_RESP])
        self.set_mock_response(mock_delete, 200, "OK")
        # Both values already match the running system: nothing should be
        # PATCHed and no reboot should be triggered.
        self.args = [
            self.option_arg,
            "--attribute-value",
            f"{ATTRIBUTE_OK}={ATTR_VALUE_DIS}",
            "--attribute-value",
            f"{ATTRIBUTE_OK_2}={ATTR_VALUE_DIS_2}",
        ]
        _, err = self.badfish_call()
        assert err.count("already in that state. IGNORING.") == 2
        assert "All attributes are already in the desired state" in err
        assert mock_patch.call_count == 0
        # Only the session-login POST happens; no reset/reboot POST is issued.
        assert mock_post.call_count == 1

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.patch")
    @patch("aiohttp.ClientSession.get")
    def test_set_bios_attribute_lowercase_name(self, mock_get, mock_patch, mock_post, mock_delete):
        get_resp = [
            BIOS_REGISTRY_MULTI.replace("'", '"'),
            BIOS_RESPONSE_MULTI,
            RESET_TYPE_RESP,
            STATE_ON_RESP,
            STATE_ON_RESP,
        ]
        responses = INIT_RESP + get_resp
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_patch, 200, ["OK"])
        self.set_mock_response(mock_post, 200, ["OK", JOB_OK_RESP])
        self.set_mock_response(mock_delete, 200, "OK")
        # Oddly-cased name is resolved to the registry's canonical
        # AttributeName (BootMode) before the current-value lookup and PATCH.
        self.args = [self.option_arg, "--attribute-value", f"bootmode={ATTR_VALUE_OK_2}"]
        _, err = self.badfish_call()
        assert err == BIOS_SET_OK
        assert mock_patch.call_count == 1
        payload = json.loads(mock_patch.call_args.kwargs["data"])["Attributes"]
        assert payload == {ATTRIBUTE_OK_2: ATTR_VALUE_OK_2}


class TestGetBiosAttribute(TestBase):
    option_arg = "--get-bios-attribute"

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_get_all_attributes(self, mock_get, mock_post, mock_delete):
        get_resp = [
            BIOS_RESPONSE_OK,
        ]
        responses = INIT_RESP + get_resp
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg]
        _, err = self.badfish_call()
        assert err == BIOS_GET_ALL_OK

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_get_one_attribute_ok(self, mock_get, mock_post, mock_delete):
        get_resp = [
            BIOS_REGISTRY_OK.replace("'", '"'),
            BIOS_RESPONSE_OK,
        ]
        responses = INIT_RESP + get_resp
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg, "--attribute", ATTRIBUTE_OK]
        _, err = self.badfish_call()
        assert err == BIOS_GET_ONE_OK

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_get_one_bad_attribute(self, mock_get, mock_post, mock_delete):
        get_resp = [
            BIOS_REGISTRY_OK.replace("'", '"'),
            BIOS_RESPONSE_OK,
        ]
        responses = INIT_RESP + get_resp
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK")
        self.set_mock_response(mock_delete, 200, "OK")
        self.args = [self.option_arg, "--attribute", ATTRIBUTE_BAD]
        _, err = self.badfish_call()
        assert err == BIOS_GET_ONE_BAD
