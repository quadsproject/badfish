from unittest.mock import patch

from tests.config import (
    INIT_RESP,
    NO_POWER,
    NVIDIA_POWER_RESP,
    POWER_CONSUMED_RESP,
    RESPONSE_NO_POWER_CONSUMED,
    RESPONSE_POWER_CONSUMED_OK,
    RESPONSE_POWER_CONSUMED_VAL_ERR,
    RESPONSE_VENDOR_UNSUPPORTED,
)
from tests.test_base import TestBase


class TestPowerConsumed(TestBase):
    args = ["--get-power-consumed"]

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_power_consumed(self, mock_get, mock_post, mock_delete):
        responses = INIT_RESP + [POWER_CONSUMED_RESP]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK", True)
        self.set_mock_response(mock_delete, 200, "OK")
        _, err = self.badfish_call()
        assert err == RESPONSE_POWER_CONSUMED_OK

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_power_consumed_404(self, mock_get, mock_post, mock_delete):
        # Mock the get_request method to return a 404 response that properly triggers vendor error
        with patch("badfish.main.Badfish.get_request") as mock_get_request:
            from tests.test_base import MockResponse

            # Mock get_request to return 404 for power endpoint
            mock_get_request.return_value = MockResponse('{"error": "Not Found"}', 404)

            self.set_mock_response(mock_get, 200, INIT_RESP)
            self.set_mock_response(mock_post, 200, "OK", True)
            self.set_mock_response(mock_delete, 200, "OK")
            _, err = self.badfish_call()
            assert err == f"{RESPONSE_VENDOR_UNSUPPORTED}\n"

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_no_power(self, mock_get, mock_post, mock_delete):
        responses = INIT_RESP + [NO_POWER]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK", True)
        self.set_mock_response(mock_delete, 200, "OK")
        _, err = self.badfish_call()
        assert err == RESPONSE_NO_POWER_CONSUMED

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_power_consumed_nvidia_missing_field(self, mock_get, mock_post, mock_delete):
        # NVIDIA BMCs expose a PowerControl entry that lacks PowerConsumedWatts,
        # so the DMTF field is absent. This used to raise an unhandled KeyError
        # (issue #395). It must degrade to the same "not exposed" message as an
        # empty PowerControl array.
        responses = INIT_RESP + [NVIDIA_POWER_RESP]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK", True)
        self.set_mock_response(mock_delete, 200, "OK")
        _, err = self.badfish_call()
        assert err == RESPONSE_NO_POWER_CONSUMED

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_power_consumed_value_error(self, mock_get, mock_post, mock_delete):
        responses_add = [""]
        responses = INIT_RESP + responses_add
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK", True)
        self.set_mock_response(mock_delete, 200, "OK")
        _, err = self.badfish_call()
        assert err == RESPONSE_POWER_CONSUMED_VAL_ERR
