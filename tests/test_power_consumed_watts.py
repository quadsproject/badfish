from unittest.mock import patch

from tests.config import (
    INIT_RESP,
    NO_POWER,
    NVIDIA_POWER_RESP,
    POWER_CONSUMED_RESP,
    POWER_MISSING,
    POWER_SUBSYSTEM_NO_SUPPLIES,
    POWER_SUBSYSTEM_RESP,
    POWER_SUPPLIES_RESP,
    POWER_SUPPLIES_RESP_EMPTY,
    POWER_SUPPLIES_RESP_NO_ODATA_ID,
    PSU_METRICS_1_RESP,
    PSU_METRICS_2_RESP,
    PSU_METRICS_NO_INPUT_RESP,
    RESPONSE_NO_POWER_CONSUMED,
    RESPONSE_POWER_CONSUMED_OK,
    RESPONSE_POWER_CONSUMED_VAL_ERR,
    RESPONSE_POWER_SUBSYSTEM_OK,
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
        responses = INIT_RESP + [NO_POWER, POWER_SUBSYSTEM_NO_SUPPLIES]
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
        responses = INIT_RESP + [NVIDIA_POWER_RESP, POWER_SUBSYSTEM_NO_SUPPLIES]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK", True)
        self.set_mock_response(mock_delete, 200, "OK")
        _, err = self.badfish_call()
        assert err == RESPONSE_NO_POWER_CONSUMED

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_power_consumed_subsystem_fallback_missing_field(self, mock_get, mock_post, mock_delete):
        # A host whose PowerControl entry lacks PowerConsumedWatts but exposes
        # PowerSubsystem should report the sum of PSU input power instead of N/A.
        responses = INIT_RESP + [
            NVIDIA_POWER_RESP,
            POWER_SUBSYSTEM_RESP,
            POWER_SUPPLIES_RESP,
            PSU_METRICS_1_RESP,
            PSU_METRICS_2_RESP,
        ]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK", True)
        self.set_mock_response(mock_delete, 200, "OK")
        _, err = self.badfish_call()
        assert err == RESPONSE_POWER_SUBSYSTEM_OK

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_power_consumed_subsystem_fallback_on_404(self, mock_get, mock_post, mock_delete):
        # Hosts that removed the deprecated /Power endpoint but expose
        # PowerSubsystem should still report consumption.
        from tests.test_base import MockResponse

        from badfish.main import Badfish

        responses = INIT_RESP + [POWER_SUBSYSTEM_RESP, POWER_SUPPLIES_RESP, PSU_METRICS_1_RESP, PSU_METRICS_2_RESP]
        self.set_mock_response(mock_get, 200, responses)
        self.set_mock_response(mock_post, 200, "OK", True)
        self.set_mock_response(mock_delete, 200, "OK")

        real_get_request = Badfish.get_request

        async def _get(request_self, uri, _continue=False, _get_token=False):
            if uri.endswith("/Power"):
                return MockResponse(POWER_MISSING, 404)
            return await real_get_request(request_self, uri, _continue, _get_token)

        with patch("badfish.main.Badfish.get_request", new=_get):
            _, err = self.badfish_call()
        assert err == RESPONSE_POWER_SUBSYSTEM_OK

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

    def _route_subsystem(self, mock_get, mock_post, mock_delete, post_responses, route):
        """Run --get-power-consumed with a get_request URI router.

        `route(uri)` returns a (text, status) pair for URIs it handles,
        otherwise defers to the mocked ClientSession.get response queue set
        in `post_responses`.
        """
        from tests.test_base import MockResponse

        from badfish.main import Badfish

        real_get_request = Badfish.get_request

        async def _get(request_self, uri, _continue=False, _get_token=False):
            handled = route(uri)
            if handled is not None:
                text, status = handled
                return MockResponse(text, status)
            return await real_get_request(request_self, uri, _continue, _get_token)

        with patch("badfish.main.Badfish.get_request", new=_get):
            self.set_mock_response(mock_get, 200, post_responses)
            self.set_mock_response(mock_post, 200, "OK", True)
            self.set_mock_response(mock_delete, 200, "OK")
            return self.badfish_call()

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_power_consumed_subsystem_supplies_404(self, mock_get, mock_post, mock_delete):
        # The PowerSubsystem endpoint is present but the PowerSupplies
        # collection cannot be read (non-200). Degrade to N/A, not an error.
        def route(uri):
            # classic /Power -> not found; PowerSupplies -> server error
            if uri.endswith("/Power"):
                return (POWER_MISSING, 404)
            if "/PowerSupplies" in uri and "/Metrics" not in uri:
                return ('{"error": "Server Error"}', 500)
            return None

        post = INIT_RESP + [POWER_SUBSYSTEM_RESP]
        _, err = self._route_subsystem(mock_get, mock_post, mock_delete, post, route)
        assert err == RESPONSE_NO_POWER_CONSUMED

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_power_consumed_subsystem_member_no_odata_id(self, mock_get, mock_post, mock_delete):
        # A PowerSupplies member without a usable @odata.id is skipped rather
        # than raising; here both members are skipped, so no PSU is consulted.
        def route(uri):
            if uri.endswith("/Power"):
                return (POWER_MISSING, 404)
            return None

        post = INIT_RESP + [
            POWER_SUBSYSTEM_RESP,
            POWER_SUPPLIES_RESP_NO_ODATA_ID,
            PSU_METRICS_1_RESP,
            PSU_METRICS_2_RESP,
        ]
        _, err = self._route_subsystem(mock_get, mock_post, mock_delete, post, route)
        # Both members lack a usable @odata.id (one is empty, one absent), so
        # neither PSU is consulted and the function degrades to N/A.
        assert err == RESPONSE_NO_POWER_CONSUMED

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_power_consumed_subsystem_metrics_404(self, mock_get, mock_post, mock_delete):
        # All PSU metrics endpoints return non-200, so every PSU is skipped and
        # the reader degrades to N/A rather than crashing.
        def route(uri):
            if uri.endswith("/Power"):
                return (POWER_MISSING, 404)
            if "/Metrics" in uri:
                return ('{"error": "Not Found"}', 404)
            return None

        post = INIT_RESP + [POWER_SUBSYSTEM_RESP, POWER_SUPPLIES_RESP]
        _, err = self._route_subsystem(mock_get, mock_post, mock_delete, post, route)
        # Both PSU metrics endpoints return non-200, so both PSUs are skipped.
        assert err == RESPONSE_NO_POWER_CONSUMED

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_power_consumed_subsystem_missing_input_power(self, mock_get, mock_post, mock_delete):
        # A PSU metrics body without InputPowerWatts (e.g. a chassis that only
        # reports output) is skipped rather than raising KeyError.
        def route(uri):
            if uri.endswith("/Power"):
                return (POWER_MISSING, 404)
            return None

        post = INIT_RESP + [
            POWER_SUBSYSTEM_RESP,
            POWER_SUPPLIES_RESP,
            PSU_METRICS_NO_INPUT_RESP,
            PSU_METRICS_2_RESP,
        ]
        _, err = self._route_subsystem(mock_get, mock_post, mock_delete, post, route)
        # PSU.Slot.1's metrics lack InputPowerWatts and are skipped; only
        # PSU.Slot.2's 238.25 contributes, so we report 238, not an error.
        assert err == "- INFO     - Current watts consumed: 238\n"

    @patch("aiohttp.ClientSession.delete")
    @patch("aiohttp.ClientSession.post")
    @patch("aiohttp.ClientSession.get")
    def test_power_consumed_subsystem_empty_supplies(self, mock_get, mock_post, mock_delete):
        # A PowerSupplies collection with no members yields no total and
        # degrades to N/A rather than crashing.
        def route(uri):
            if uri.endswith("/Power"):
                return (POWER_MISSING, 404)
            return None

        post = INIT_RESP + [POWER_SUBSYSTEM_RESP, POWER_SUPPLIES_RESP_EMPTY]
        _, err = self._route_subsystem(mock_get, mock_post, mock_delete, post, route)
        assert err == RESPONSE_NO_POWER_CONSUMED
