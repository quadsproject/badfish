import logging
from collections import defaultdict
from unittest.mock import AsyncMock, MagicMock

import pytest

from badfish.main import Badfish


ROOT_RESP_UNKNOWN_OEM = (
    '{"Managers":{"@odata.id":"/redfish/v1/Managers"},'
    '"RedfishVersion":"1.0.2","Oem":{"Lenovo":{}}}'
)
MAN_RESP = '{"Members":[{"@odata.id":"/redfish/v1/Managers/1"}]}'


def _make_resp(body: str) -> MagicMock:
    resp = MagicMock()
    resp.status = 200
    resp.text = AsyncMock(return_value=body)
    return resp


async def _init_vendor(root_body: str) -> str:
    logger = MagicMock(spec=logging.Logger)
    bf = Badfish("test_host", "user", "pass", logger, 1)
    bf.http_client = MagicMock()
    bf.http_client.get_request = AsyncMock(
        side_effect=[_make_resp(root_body), _make_resp(MAN_RESP)]
    )
    await bf.find_managers_resource()
    return bf.vendor


@pytest.mark.asyncio
async def test_vendor_dell():
    root = (
        '{"Managers":{"@odata.id":"/redfish/v1/Managers"},'
        '"RedfishVersion":"1.0.2","Oem":{"Dell":{"ServiceTag":"T35T7A6"}}}'
    )
    assert await _init_vendor(root) == "Dell"


@pytest.mark.asyncio
async def test_vendor_supermicro():
    root = (
        '{"Managers":{"@odata.id":"/redfish/v1/Managers"},'
        '"RedfishVersion":"1.0.2","Oem":{"Supermicro":{}}}'
    )
    assert await _init_vendor(root) == "Supermicro"


@pytest.mark.asyncio
async def test_vendor_hpe():
    root = (
        '{"Managers":{"@odata.id":"/redfish/v1/Managers"},'
        '"RedfishVersion":"1.0.2","Oem":{"Hpe":{"Manager":[{}]}}}'
    )
    assert await _init_vendor(root) == "HPE"


@pytest.mark.asyncio
async def test_vendor_unknown_oem():
    assert await _init_vendor(ROOT_RESP_UNKNOWN_OEM) == "Unknown"


@pytest.mark.asyncio
async def test_vendor_no_oem():
    root = (
        '{"Managers":{"@odata.id":"/redfish/v1/Managers"},'
        '"RedfishVersion":"1.0.2"}'
    )
    assert await _init_vendor(root) == "Unknown"
