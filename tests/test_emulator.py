import ssl
from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from badfish import emulator
from badfish.main import badfish_factory

_CERTS = Path(__file__).parent.parent / "src" / "badfish" / "emulator" / "certs"
_ROOT = "/redfish/v1"
ACCOUNTS = f"{_ROOT}/AccountService/Accounts"


async def _client(app):
    client = TestClient(TestServer(app))
    await client.start_server()
    return client


async def _login(client, user="quads", password="quads"):
    resp = await client.post(f"{_ROOT}/SessionService/Sessions", json={"UserName": user, "Password": password})
    assert resp.status == 201
    return resp.headers["X-Auth-Token"]


@pytest.fixture
async def client(tmp_path):
    app = emulator.create_app(str(tmp_path / "users.json"))
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


async def test_account_service_and_quads_admin(client):
    token = await _login(client)
    headers = {"X-Auth-Token": token}
    svc = await (await client.get(f"{_ROOT}/AccountService", headers=headers)).json()
    assert svc["Id"] == "AccountService"
    assert svc["Accounts"]["@odata.id"] == ACCOUNTS
    coll = await (await client.get(ACCOUNTS, headers=headers)).json()
    assert [m["@odata.id"] for m in coll["Members"]] == [f"{ACCOUNTS}/quads"]
    acct = await (await client.get(f"{ACCOUNTS}/quads", headers=headers)).json()
    assert acct["RoleId"] == "Administrator"
    assert acct["Enabled"] is True
    # real iDRAC never returns Password on account GET
    assert "Password" not in acct


async def test_admin_creates_user_and_store_persists(tmp_path):
    users_path = str(tmp_path / "users.json")
    app = emulator.create_app(users_path)
    c = await _client(app)
    token = await _login(c)
    resp = await c.post(
        ACCOUNTS,
        json={"UserName": "alice", "Password": "secret", "RoleId": "Operator"},
        headers={"X-Auth-Token": token},
    )
    assert resp.status == 201
    await c.close()

    # a fresh emulator process against the same file still knows alice
    app2 = emulator.create_app(users_path)
    c2 = await _client(app2)
    assert await _login(c2, "alice", "secret")
    await c2.close()


async def test_account_create_validation(client):
    token = await _login(client)
    headers = {"X-Auth-Token": token}
    dup = await client.post(
        ACCOUNTS, json={"UserName": "quads", "Password": "x", "RoleId": "Administrator"}, headers=headers
    )
    assert dup.status == 400
    badrole = await client.post(
        ACCOUNTS, json={"UserName": "carol", "Password": "x", "RoleId": "Superuser"}, headers=headers
    )
    assert badrole.status == 400
    nopass = await client.post(ACCOUNTS, json={"UserName": "carol", "RoleId": "Operator"}, headers=headers)
    assert nopass.status == 400


async def test_operator_mutates_but_cannot_manage_accounts(client):
    token = await _login(client)
    admin = {"X-Auth-Token": token}
    assert (
        await client.post(
            ACCOUNTS, json={"UserName": "op", "Password": "opsecret", "RoleId": "Operator"}, headers=admin
        )
    ).status == 201
    op = {"X-Auth-Token": await _login(client, "op", "opsecret")}

    reset = await client.post(
        f"{_ROOT}/Systems/System.Embedded.1/Actions/ComputerSystem.Reset", json={"ResetType": "On"}, headers=op
    )
    assert reset.status == 204

    forbidden = await client.post(
        ACCOUNTS, json={"UserName": "mallory", "Password": "x", "RoleId": "ReadOnly"}, headers=op
    )
    assert forbidden.status == 403
    forbidden = await client.delete(f"{ACCOUNTS}/op", headers=op)
    assert forbidden.status == 403


async def test_readonly_has_no_mutation_rights(client):
    token = await _login(client)
    admin = {"X-Auth-Token": token}
    assert (
        await client.post(
            ACCOUNTS, json={"UserName": "ro", "Password": "rosecret", "RoleId": "ReadOnly"}, headers=admin
        )
    ).status == 201
    ro = {"X-Auth-Token": await _login(client, "ro", "rosecret")}

    assert (await client.get(f"{_ROOT}/Systems", headers=ro)).status == 200
    reset = await client.post(
        f"{_ROOT}/Systems/System.Embedded.1/Actions/ComputerSystem.Reset", json={"ResetType": "On"}, headers=ro
    )
    assert reset.status == 403
    boot = await client.patch(f"{_ROOT}/Systems/System.Embedded.1", json={"Boot": {}}, headers=ro)
    assert boot.status == 403


async def test_change_password_action(client):
    token = await _login(client)
    admin = {"X-Auth-Token": token}
    assert (
        await client.post(
            ACCOUNTS, json={"UserName": "bob", "Password": "oldpass", "RoleId": "Operator"}, headers=admin
        )
    ).status == 201

    resp = await client.post(
        f"{_ROOT}/AccountService/Actions/AccountService.ChangePassword",
        json={"UserName": "bob", "OldPassword": "oldpass", "NewPassword": "newpass"},
        headers={"X-Auth-Token": await _login(client, "bob", "oldpass")},
    )
    assert resp.status == 204

    wrong = await client.post(f"{_ROOT}/SessionService/Sessions", json={"UserName": "bob", "Password": "oldpass"})
    assert wrong.status == 401
    assert await _login(client, "bob", "newpass")


async def test_account_patch_and_last_admin_guard(client):
    token = await _login(client)
    headers = {"X-Auth-Token": token}

    patch = await client.patch(f"{ACCOUNTS}/quads", json={"RoleId": "ReadOnly"}, headers=headers)
    assert patch.status == 200
    acct = await (await client.get(f"{ACCOUNTS}/quads", headers=headers)).json()
    assert acct["RoleId"] == "ReadOnly"

    assert (await client.patch(f"{ACCOUNTS}/quads", json={"RoleId": "Administrator"}, headers=headers)).status == 200

    disable = await client.patch(f"{ACCOUNTS}/quads", json={"Enabled": False}, headers=headers)
    assert disable.status == 400
    remove = await client.delete(f"{ACCOUNTS}/quads", headers=headers)
    assert remove.status == 400


async def test_emulator_end_to_end(monkeypatch, tmp_path):
    """Drive the real badfish client against a live HTTPS emulator."""

    async def _noop(*_args, **_kwargs):
        return None

    monkeypatch.setattr("badfish.main.asyncio.sleep", _noop)

    app = emulator.create_app(str(tmp_path / "users.json"))
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
