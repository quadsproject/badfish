import ssl
from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from badfish import emulator
from badfish.main import badfish_factory

_CERTS = Path(__file__).parent.parent / "src" / "badfish" / "emulator" / "certs"
_ROOT = "/redfish/v1"


async def _client(app):
    client = TestClient(TestServer(app))
    await client.start_server()
    return client


async def _login(client, user="quads", password="quads"):
    resp = await client.post(f"{_ROOT}/SessionService/Sessions", json={"UserName": user, "Password": password})
    assert resp.status == 201
    return resp.headers["X-Auth-Token"]


@pytest.fixture
async def client():
    app = emulator.create_app()
    c = await _client(app)
    yield c
    await c.close()


async def test_bad_credentials_rejected(client):
    resp = await client.post(f"{_ROOT}/SessionService/Sessions", json={"UserName": "quads", "Password": "wrong"})
    assert resp.status == 401
    body = await resp.json()
    assert "error" in body


async def test_auth_required_for_resources(client):
    token = await _login(client)
    resp = await client.get(f"{_ROOT}/Systems")
    assert resp.status == 401
    resp = await client.get(f"{_ROOT}/Systems", headers={"X-Auth-Token": token})
    assert resp.status == 200
    body = await resp.json()
    assert body["Members"][0]["@odata.id"] == f"{_ROOT}/Systems/System.Embedded.1"


async def test_session_discovery_without_token(client):
    resp = await client.get(f"{_ROOT}")
    assert resp.status == 200
    body = await resp.json()
    assert body["RedfishVersion"] == "1.16.0"
    assert body["Oem"]["Dell"]["ServiceTag"] == "EMUL8V1"


async def test_system_power_roundtrip(client):
    token = await _login(client)
    headers = {"X-Auth-Token": token}

    resp = await client.get(f"{_ROOT}/Systems/System.Embedded.1", headers=headers)
    body = await resp.json()
    assert body["PowerState"] == "Off"
    assert body["Model"] == "PowerEdge R740"

    reset = await client.post(
        f"{_ROOT}/Systems/System.Embedded.1/Actions/ComputerSystem.Reset", json={"ResetType": "On"}, headers=headers
    )
    assert reset.status == 204

    resp = await client.get(f"{_ROOT}/Systems/System.Embedded.1", headers=headers)
    assert (await resp.json())["PowerState"] == "On"


async def test_boot_override_patch(client):
    token = await _login(client)
    headers = {"X-Auth-Token": token}
    resp = await client.patch(
        f"{_ROOT}/Systems/System.Embedded.1",
        json={"Boot": {"BootSourceOverrideTarget": "Pxe", "BootSourceOverrideEnabled": "Once"}},
        headers=headers,
    )
    assert resp.status == 200
    body = await (await client.get(f"{_ROOT}/Systems/System.Embedded.1", headers=headers)).json()
    assert body["Boot"]["BootSourceOverrideTarget"] == "Pxe"
    assert body["Boot"]["BootSourceOverrideEnabled"] == "Once"


async def test_jobs_lifecycle(client):
    token = await _login(client)
    headers = {"X-Auth-Token": token}
    manager = f"{_ROOT}/Managers/iDRAC.Embedded.1"
    resp = await client.post(
        f"{manager}/Jobs",
        json={"TargetSettingsURI": "/redfish/v1/Systems/System.Embedded.1/Bios/Settings"},
        headers=headers,
    )
    assert resp.status == 200
    job_id = resp.headers["Location"].split("/")[-1]
    assert job_id.startswith("JID_")

    job = await (await client.get(f"{manager}/Jobs/{job_id}", headers=headers)).json()
    assert job["JobState"] == "Completed"
    assert job["PercentComplete"] == 100

    jobs = await (await client.get(f"{manager}/Jobs", headers=headers)).json()
    assert [m["@odata.id"] for m in jobs["Members"]] == [f"{manager}/Jobs/{job_id}"]

    resp = await client.delete(f"{manager}/Jobs/{job_id}", headers=headers)
    assert resp.status == 200
    jobs = await (await client.get(f"{manager}/Jobs", headers=headers)).json()
    assert jobs["Members@odata.count"] == 0


async def test_virtual_media(client):
    token = await _login(client)
    headers = {"X-Auth-Token": token}
    vmedia = f"{_ROOT}/Managers/iDRAC.Embedded.1/VirtualMedia/CD"

    resp = await client.post(
        f"{vmedia}/Actions/VirtualMedia.InsertMedia", json={"Image": "/tmp/fake.iso"}, headers=headers
    )
    assert resp.status == 204
    body = await (await client.get(vmedia, headers=headers)).json()
    assert body["Inserted"] is True
    assert body["ImageName"] == "/tmp/fake.iso"

    resp = await client.post(f"{vmedia}/Actions/VirtualMedia.EjectMedia", json={}, headers=headers)
    assert resp.status == 204
    body = await (await client.get(vmedia, headers=headers)).json()
    assert body["Inserted"] is False


async def test_firmware_and_dell_endpoints(client):
    token = await _login(client)
    headers = {"X-Auth-Token": token}
    inv = await (await client.get(f"{_ROOT}/UpdateService/FirmwareInventory", headers=headers)).json()
    assert inv["Members@odata.count"] == 2
    member = inv["Members"][0]["@odata.id"]
    fw = await (await client.get(member, headers=headers)).json()
    assert fw["Version"]

    dell = await (await client.get(f"{_ROOT}/Dell/Managers/iDRAC.Embedded.1/DellJobService", headers=headers)).json()
    assert dell["Id"] == "DellJobService"


async def test_not_found_and_tasks(client):
    token = await _login(client)
    headers = {"X-Auth-Token": token}
    resp = await client.get(f"{_ROOT}/Systems/DoesNotExist", headers=headers)
    assert resp.status == 404
    body = await resp.json()
    assert body["error"]["@Message.ExtendedInfo"][0]["Message"]

    task = await (await client.get(f"{_ROOT}/TaskService/Tasks/1", headers=headers)).json()
    assert task["Oem"]["Dell"]["PercentComplete"] == 100


async def test_emulator_end_to_end(monkeypatch):
    """Drive the real badfish client against a live HTTPS emulator."""

    async def _noop(*_args, **_kwargs):
        return None

    monkeypatch.setattr("badfish.main.asyncio.sleep", _noop)

    app = emulator.create_app()
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(str(_CERTS / "emulator.crt"), str(_CERTS / "emulator.key"))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0, ssl_context=ctx)
    await site.start()
    host = f"127.0.0.1:{runner.addresses[0][1]}"

    bf = None
    try:
        bf = await badfish_factory(host, "quads", "quads", _insecure=True, _retries=3)
        assert bf.vendor == "Dell"

        assert await bf.get_power_state() == "Off"
        assert await bf.send_reset("On") is True
        bf.http_client.get_json.cache_clear()
        assert await bf.get_power_state() == "On"
        assert await bf.send_reset("ForceOff") is True
        bf.http_client.get_json.cache_clear()
        assert await bf.get_power_state() == "Off"

        assert await bf.get_boot_seq() == "BootSeq"
        await bf.get_boot_devices()
        assert bf.boot_devices is not None
        assert bf.boot_devices[0]["Name"] == "NIC.Integrated.1-1-1"

        job_id = await bf.create_bios_config_job(bf.bios_uri)
        assert job_id and job_id.startswith("JID_")
        assert (await bf.check_schedule_job_status(job_id)) is None

        # get_firmware_inventory logs results and returns None on success.
        assert (await bf.get_firmware_inventory()) is None
        assert await bf.mount_virtual_media("/tmp/fake.iso")
        assert await bf.check_virtual_media()
        assert await bf.unmount_virtual_media()

        await bf.get_power_consumed_watts()
        assert await bf.get_bios_boot_mode() == "Bios"
    finally:
        if bf:
            await bf.delete_session()
        await runner.cleanup()


def test_parser_has_emulator_flags():
    from badfish.helpers.parser import parse_arguments

    args = parse_arguments(["--redfish-emulator", "--port", "9000", "--bind", "localhost"])
    assert args["redfish_emulator"] is True
    assert args["port"] == 9000
    assert args["bind"] == "localhost"
