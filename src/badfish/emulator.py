# -*- coding: utf-8 -*-
"""Badfish Redfish emulator: a mock iDRAC served over HTTP(S).

Architecture is inspired by the sushy-tools emulator (OpenStack project,
Apache License 2.0): JSON template resources on top of a fake driver that
holds mutable per-system state. This is an independent implementation written
for badfish under the GPL-3.0-or-later license; no sushy-tools source is used.

Static resource shapes live as JSON documents in emulator/templates/ so a
vendor mockup bundle can feed the same store later. Run it with:

    badfish --redfish-emulator --port 8443

The emulator always runs as a persistent server until interrupted; there is no
separate daemon flag because that is its only mode.
"""

import asyncio
import base64
import copy
import json
import os
import secrets
import ssl
from pathlib import Path

from aiohttp import web

ROOT = "/redfish/v1"

_BASE = Path(__file__).parent
_TEMPLATES = _BASE / "emulator" / "templates"
_CERTS = _BASE / "emulator" / "certs"

# Default credentials are intentionally generic (quads/quads mirrors the
# quads project's IPMI user convention). Override per run with env vars.
USERNAME = os.environ.get("BADFISH_EMULATOR_USER", "quads")
PASSWORD = os.environ.get("BADFISH_EMULATOR_PASSWORD", "quads")

# Single source of truth for the fake host's hardware identity. Changing a
# value here changes every resource that reports it; no template editing needed.
SYSCONF = {
    "system_id": "System.Embedded.1",
    "manager_id": "iDRAC.Embedded.1",
    "chassis_id": "System.Embedded.1",
    "model": "PowerEdge R740",
    "manufacturer": "Dell Inc.",
    "serial": "EMUL8V1",
    "uuid": "27946b59-9e44-4fa7-8e91-f3527a1ef094",
    "bios_version": "2.60.60.60",
    "boot_devices": [
        {"index": 0, "name": "NIC.Integrated.1-1-1", "enabled": True},
        {"index": 1, "name": "Optical.iDRACVirtual.1-1", "enabled": True},
        {"index": 2, "name": "Disk.SATAEmbedded.0-1", "enabled": True},
    ],
    "nics": [
        {"id": "NIC.Integrated.1-1-1", "mac": "00:5c:52:31:3a:9c", "speed": 25000, "link": "Up"},
        {"id": "NIC.Integrated.1-2-1", "mac": "00:5c:52:31:3a:9d", "speed": 25000, "link": "Up"},
    ],
    "cpus": [
        {
            "id": "CPU.Socket.1",
            "model": "Intel(R) Xeon(R) Gold 6230R CPU @ 2.10GHz",
            "manufacturer": "Intel",
            "cores": 26,
            "threads": 52,
            "max": 2100,
        },
        {
            "id": "CPU.Socket.2",
            "model": "Intel(R) Xeon(R) Gold 6230R CPU @ 2.10GHz",
            "manufacturer": "Intel",
            "cores": 26,
            "threads": 52,
            "max": 2100,
        },
    ],
    "dimms": [
        {"id": "DIMM.Socket.A1", "cap": 32768, "manufacturer": "Micron", "type": "DDR4", "speed": 2933},
        {"id": "DIMM.Socket.B1", "cap": 32768, "manufacturer": "Micron", "type": "DDR4", "speed": 2933},
    ],
    "firmware": [
        {
            "id": "iDRAC-with-LCC",
            "name": "Integrated Dell Remote Access Controller",
            "version": "6.00.00.00",
            "manufacturer": "Dell Inc.",
        },
        {"id": "BIOS", "name": "BIOS", "version": "2.60.60.60", "manufacturer": "Dell Inc."},
    ],
}

SYSTEM = f"{ROOT}/Systems/{SYSCONF['system_id']}"
MANAGER = f"{ROOT}/Managers/{SYSCONF['manager_id']}"
CHASSIS = f"{ROOT}/Chassis/{SYSCONF['chassis_id']}"
UPDATESERVICE = f"{ROOT}/UpdateService"
FIRMWARE = f"{UPDATESERVICE}/FirmwareInventory"

_RESTART_TYPES = {"GracefulRestart", "ForceRestart"}  # rebooted: off then on
_RESET_STATES = {  # one-shot power targets
    "On": "On",
    "ForceOn": "On",
    "PowerCycle": "On",
    "ForceOff": "Off",
    "GracefulShutdown": "Off",
}


class _StateKey(web.AppKey):
    pass


_STATE_KEY = _StateKey("state", object)


class State:
    """Mutable fake-driver state shared by the mock BMC's resources."""

    def __init__(self):
        self.power = "Off"
        self.boot_target = "None"
        self.boot_enabled = "Disabled"
        self.vmedia_image = None
        self.jobs = {}
        self.sessions = {}
        self._job_n = 0
        self._restart_task = None


# --- template store ---------------------------------------------------------

_STATIC = {}


def _load_templates():
    for path in _TEMPLATES.glob("*.json"):
        with open(path) as fh:
            _STATIC[path.stem] = json.load(fh)


_load_templates()


def _tmpl(key):
    return copy.deepcopy(_STATIC[key])


def _static_doc(key, uri):
    if key is None:
        return None
    data = copy.deepcopy(_STATIC[key])
    data["@odata.id"] = uri
    return data


def _collection(resource_name, base, members):
    return {
        "@odata.type": f"#{resource_name}Collection.{resource_name}Collection",
        "Name": f"{resource_name} Collection",
        "Members@odata.count": len(members),
        "Members": [{"@odata.id": f"{base}/{m}"} for m in members],
    }


# Static leaf resources, keyed by full URI. Anything not listed here is built
# from SYSCONF/state (collections and members below) so identity stays single-sourced.
_STATIC_URI = {
    ROOT: "service_root",
    f"{ROOT}/SessionService": "session_service",
    f"{ROOT}/Systems": "systems",
    f"{SYSTEM}/Bios": "bios",
    f"{SYSTEM}/Bios/Settings": "bios_settings",
    f"{SYSTEM}/Bios/BiosRegistry": "bios_registry",
    f"{SYSTEM}/BootSources": "boot_sources",
    f"{SYSTEM}/NetworkAdapters": "network_adapters",
    f"{SYSTEM}/NetworkAdapters/NIC.Integrated.1": "network_adapter",
    f"{SYSTEM}/NetworkAdapters/NIC.Integrated.1/NetworkPorts": "network_ports",
    f"{SYSTEM}/NetworkAdapters/NIC.Integrated.1/NetworkPorts/Port0": "network_port",
    f"{SYSTEM}/NetworkAdapters/NIC.Integrated.1/NetworkDeviceFunctions": "network_device_functions",
    f"{SYSTEM}/NetworkAdapters/NIC.Integrated.1/NetworkDeviceFunctions/NIC.Integrated.1-1-1": "network_device_function",
    f"{SYSTEM}/NetworkAdapters/NIC.Integrated.1/NetworkDeviceFunctions/NIC.Integrated.1-1-1/Oem/Dell/DellNetworkAttributes/NIC.Integrated.1-1-1": "dell_network_attributes",
    f"{ROOT}/Managers": "managers",
    MANAGER: "manager",
    f"{CHASSIS}": "chassis",
    UPDATESERVICE: "update_service",
    f"{ROOT}/Dell/Managers/{SYSCONF['manager_id']}/DellJobService": "dell_job_service",
    f"{ROOT}/Dell/Systems/{SYSCONF['system_id']}/DellOSDeploymentService": "dell_os_deployment_service",
    f"{CHASSIS}/Power": "chassis_power",
}


def _collection_uri(uri, state):
    if uri == f"{SYSTEM}/EthernetInterfaces":
        return _collection("EthernetInterface", uri, [n["id"] for n in SYSCONF["nics"]])
    if uri == f"{SYSTEM}/Processors":
        return _collection("Processor", uri, [c["id"] for c in SYSCONF["cpus"]])
    if uri == f"{SYSTEM}/Memory":
        return _collection("Memory", uri, [d["id"] for d in SYSCONF["dimms"]])
    if uri == FIRMWARE:
        return _collection("SoftwareInventory", uri, [f"{f['id']}-{f['id']}-Installed" for f in SYSCONF["firmware"]])
    if uri == f"{MANAGER}/Jobs":
        return _collection("Job", uri, list(state.jobs.keys()))
    if uri == f"{ROOT}/SessionService/Sessions":
        return _collection("Session", uri, [s["id"] for s in state.sessions.values()])
    if uri == f"{MANAGER}/VirtualMedia":
        return _collection("VirtualMedia", uri, ["CD"])
    return None


def _member(tmpl_key, items, member_id, uri, fill=None):
    item = next((i for i in items if i["id"] == member_id), None)
    if item is None:
        return None
    data = _tmpl(tmpl_key)
    data["@odata.id"] = uri
    if fill:
        fill(data, item)
    return data


def _m_nic(uri, state):
    member_id = uri.rsplit("/", 1)[-1]

    def fill(data, nic):
        data["MACAddress"] = nic["mac"]
        data["SpeedMbps"] = nic["speed"]
        data["LinkStatus"] = nic["link"]

    return _member("ethernet_interface", SYSCONF["nics"], member_id, uri, fill)


def _m_processor(uri, state):
    member_id = uri.rsplit("/", 1)[-1]

    def fill(data, cpu):
        data["Manufacturer"] = cpu["manufacturer"]
        data["Model"] = cpu["model"]
        data["TotalCores"] = cpu["cores"]
        data["TotalThreads"] = cpu["threads"]
        data["MaxSpeedMHz"] = cpu["max"]

    return _member("processor", SYSCONF["cpus"], member_id, uri, fill)


def _m_dimm(uri, state):
    member_id = uri.rsplit("/", 1)[-1]

    def fill(data, dimm):
        data["CapacityMiB"] = dimm["cap"]
        data["Manufacturer"] = dimm["manufacturer"]
        data["MemoryDeviceType"] = dimm["type"]
        data["OperatingSpeedMhz"] = dimm["speed"]

    return _member("memory", SYSCONF["dimms"], member_id, uri, fill)


def _m_firmware(uri, state):
    member_id = uri.rsplit("/", 1)[-1]

    def fill(data, fw):
        data["Id"] = member_id
        data["Name"] = fw["name"]
        data["Version"] = fw["version"]
        data["Manufacturer"] = fw["manufacturer"]

    item = next((f for f in SYSCONF["firmware"] if f["id"] in member_id), None)
    if item is None:
        return None
    data = _tmpl("software_inventory")
    data["@odata.id"] = uri
    fill(data, item)
    return data


def _m_job(uri, state):
    job_id = uri.rsplit("/", 1)[-1]
    job = state.jobs.get(job_id)
    if job is None:
        return None
    data = _tmpl("job")
    data["@odata.id"] = uri
    data["Id"] = job_id
    data["Name"] = job.get("Name", "Configure: BIOS.Setup.1-1")
    data["Message"] = "Job completed successfully."
    data["PercentComplete"] = 100
    data["JobState"] = "Completed"
    if "SystemConfiguration" in job:
        data["SystemConfiguration"] = {"ComponentResults": [], "Id": "SystemConfiguration"}
    return data


def _m_session(uri, state):
    session_id = uri.rsplit("/", 1)[-1]
    for token, info in state.sessions.items():
        if str(info["id"]) == session_id:
            data = _tmpl("session")
            data["@odata.id"] = uri
            data["Id"] = session_id
            data["UserName"] = info["username"]
            return data
    return None


def _m_vmedia(uri, state):
    data = _tmpl("virtual_media_cd")
    data["@odata.id"] = uri
    data["ImageName"] = state.vmedia_image or ""
    data["Inserted"] = bool(state.vmedia_image)
    return data


def _m_task(uri, state):
    data = _tmpl("task")
    data["@odata.id"] = uri
    data["Id"] = uri.rsplit("/", 1)[-1]
    return data


def _m_registry_file(uri, state):
    return _static_doc("network_attributes_registry", uri)


_MEMBER_PREFIXES = (
    (f"{SYSTEM}/EthernetInterfaces/", _m_nic),
    (f"{SYSTEM}/Processors/", _m_processor),
    (f"{SYSTEM}/Memory/", _m_dimm),
    (f"{FIRMWARE}/", _m_firmware),
    (f"{MANAGER}/Jobs/", _m_job),
    (f"{ROOT}/SessionService/Sessions/", _m_session),
    (f"{MANAGER}/VirtualMedia/", _m_vmedia),
    (f"{ROOT}/TaskService/Tasks/", _m_task),
    (f"{ROOT}/Registries/NetworkAttributesRegistry_", _m_registry_file),
)


def _get_system(uri, state):
    data = _tmpl("system")
    data["@odata.id"] = uri
    s = SYSCONF
    data["Model"] = s["model"]
    data["Manufacturer"] = s["manufacturer"]
    data["SerialNumber"] = s["serial"]
    data["UUID"] = s["uuid"]
    data["PowerState"] = state.power
    data["Boot"]["BootSourceOverrideTarget"] = state.boot_target
    data["Boot"]["BootSourceOverrideEnabled"] = state.boot_enabled
    data["ProcessorSummary"] = {
        "Model": s["cpus"][0]["model"],
        "Count": len(s["cpus"]),
        "LogicalProcessorCount": sum(c["threads"] for c in s["cpus"]),
    }
    data["MemorySummary"] = {"TotalSystemMemoryGiB": sum(d["cap"] for d in s["dimms"]) // 1024}
    return data


def _resource(uri, state):
    """Resolve a Redfish resource for a URI against the fake system."""
    uri = uri.rstrip("/") or "/"
    data = _static_doc(_STATIC_URI.get(uri), uri)
    if data is not None:
        return data
    if uri == SYSTEM:
        return _get_system(uri, state)
    if uri == f"{CHASSIS}/Power":
        data = _static_doc("chassis_power", uri)
        data["PowerControl"][0]["PowerConsumedWatts"] = 320 if state.power == "On" else 120
        return data
    data = _collection_uri(uri, state)
    if data is not None:
        return data
    for prefix, handler in _MEMBER_PREFIXES:
        if uri.startswith(prefix):
            return handler(uri, state)
    return None


# --- responses and helpers --------------------------------------------------


def _error(message, resolution=None):
    payload = {
        "error": {
            "code": "Base.1.0.GeneralError",
            "message": "A general error has occurred. See ExtendedInfo for more information.",
            "@Message.ExtendedInfo": [
                {
                    "MessageId": "Base.1.0.GeneralError",
                    "Message": message,
                    "Resolution": resolution or "Retry the operation.",
                }
            ],
        }
    }
    return payload


def _json(data, status=200, headers=None):
    return web.json_response(data, status=status, headers=headers)


def _bad_request(message):
    return _json(_error(message), status=400)


def _unauthorized(message):
    return _json(_error(message), status=401)


def _not_found(uri):
    return _json(_error(f"Resource at {uri} was not found.", "Verify the URI."), status=404)


def _method_not_allowed(uri, method):
    return _json(_error(f"{method} is not supported on {uri}."), status=405)


def _delete_session(state, session_id):
    for token in list(state.sessions):
        if str(state.sessions[token]["id"]) == session_id:
            del state.sessions[token]
            return True
    return False


def _basic_ok(auth_header):
    if not auth_header.startswith("Basic "):
        return False
    try:
        user, _, password = base64.b64decode(auth_header[6:]).decode().partition(":")
    except (ValueError, UnicodeDecodeError):
        return False
    return (user, password) == (USERNAME, PASSWORD)


async def _read_json(request):
    try:
        return await request.json()
    except (ValueError, json.JSONDecodeError):
        return None


def _make_session(state, username):
    token = secrets.token_hex(16)
    state._job_n += 1
    session_id = str(state._job_n)
    state.sessions[token] = {"id": session_id, "username": username}
    uri = f"{ROOT}/SessionService/Sessions/{session_id}"
    body = _static_doc("session", uri)
    body["Id"] = session_id
    body["UserName"] = username
    return body, token, uri


# --- auth middleware --------------------------------------------------------


@web.middleware
async def _auth(request, handler):
    state = request.app[_STATE_KEY]
    path = request.path.rstrip("/")
    if path in ("", "/") or not path.startswith(ROOT):
        return await handler(request)
    if path == ROOT:  # the service root is public in Redfish
        return await handler(request)
    if request.method == "POST" and path in (f"{ROOT}/SessionService/Sessions", f"{ROOT}/Sessions"):
        return await handler(request)
    if request.headers.get("X-Auth-Token") in state.sessions:
        return await handler(request)
    if _basic_ok(request.headers.get("Authorization", "")):
        return await handler(request)
    return _unauthorized("Authentication required. Create a session via POST /redfish/v1/SessionService/Sessions.")


# --- HTTP handlers ----------------------------------------------------------


async def _get(_request):
    state = _request.app[_STATE_KEY]
    uri = _request.path
    data = _resource(uri, state)
    if data is None:
        return _not_found(uri)
    return _json(data)


async def _post(_request):
    state = _request.app[_STATE_KEY]
    path = _request.path.rstrip("/")

    if path in (f"{ROOT}/SessionService/Sessions", f"{ROOT}/Sessions"):
        body = await _read_json(_request)
        if body is None or body.get("UserName") != USERNAME or body.get("Password") != PASSWORD:
            return _unauthorized("Authentication failed. Verify your credentials.")
        resource, token, location = _make_session(state, body.get("UserName"))
        return _json(resource, status=201, headers={"X-Auth-Token": token, "Location": location})

    if path == f"{SYSTEM}/Actions/ComputerSystem.Reset":
        body = await _read_json(_request)
        if body is None:
            return _bad_request("Malformed JSON body.")
        reset_type = body.get("ResetType")
        if reset_type in _RESTART_TYPES:
            state.power = "Off"

            async def _power_back_on():
                try:
                    await asyncio.sleep(2.0)
                    state.power = "On"
                except asyncio.CancelledError:
                    pass

            state._restart_task = asyncio.get_running_loop().create_task(_power_back_on())
        elif reset_type in _RESET_STATES:
            state.power = _RESET_STATES[reset_type]
        else:
            return _bad_request(f"Unsupported ResetType '{reset_type}'.")
        return web.Response(status=204)

    if path == f"{SYSTEM}/Bios/Actions/Bios.ResetBios":
        return _json({"Settings": f"{SYSTEM}/Bios/Settings"})
    if path == f"{SYSTEM}/Bios/Actions/Bios.ChangePassword":
        return web.Response(status=204)
    if path == f"{MANAGER}/Actions/Manager.Reset":
        return web.Response(status=204)

    if path == f"{MANAGER}/Jobs":
        body = await _read_json(_request)
        if body is None:
            return _bad_request("Malformed JSON body.")
        state._job_n += 1
        job_id = f"JID_{state._job_n:016d}"
        state.jobs[job_id] = {"TargetSettingsURI": body.get("TargetSettingsURI")}
        return _json(
            _m_job(f"{MANAGER}/Jobs/{job_id}", state), status=200, headers={"Location": f"{MANAGER}/Jobs/{job_id}"}
        )

    if path == f"{MANAGER}/VirtualMedia/CD/Actions/VirtualMedia.InsertMedia":
        body = await _read_json(_request)
        if body is None:
            return _bad_request("Malformed JSON body.")
        state.vmedia_image = body.get("Image")
        return web.Response(status=204)
    if path == f"{MANAGER}/VirtualMedia/CD/Actions/VirtualMedia.EjectMedia":
        state.vmedia_image = None
        return web.Response(status=204)

    if path == f"{ROOT}/Dell/Managers/{SYSCONF['manager_id']}/DellJobService/Actions/DellJobService.DeleteJobQueue":
        state.jobs.clear()
        return _json({"Message": "Job queue cleared."})

    if path == (
        f"{ROOT}/Dell/Systems/{SYSCONF['system_id']}/DellOSDeploymentService/"
        "Actions/DellOSDeploymentService.GetAttachStatus"
    ):
        return _json({"ISOAttachStatus": "Detached"})
    if path == (
        f"{ROOT}/Dell/Systems/{SYSCONF['system_id']}/DellOSDeploymentService/"
        "Actions/DellOSDeploymentService.BootToNetworkISO"
    ):
        return _json(
            {"Message": "Successfully Requested"}, status=202, headers={"Location": f"{ROOT}/TaskService/Tasks/1"}
        )
    if path == (
        f"{ROOT}/Dell/Systems/{SYSCONF['system_id']}/DellOSDeploymentService/"
        "Actions/DellOSDeploymentService.DetachISOImage"
    ):
        return web.Response(status=204)

    if path.endswith("/Actions/Oem/EID_674_Manager.ExportSystemConfiguration"):
        state._job_n += 1
        job_id = f"JID_{state._job_n:016d}"
        state.jobs[job_id] = {"Export": True}
        return web.Response(status=202, headers={"Location": f"{MANAGER}/Jobs/{job_id}"})
    if path.endswith("/Actions/Oem/EID_674_Manager.ImportSystemConfiguration"):
        state._job_n += 1
        job_id = f"JID_{state._job_n:016d}"
        return web.Response(status=202, headers={"Location": f"{ROOT}/TaskService/Tasks/{job_id}"})

    if "DellLCService" in path and "ExportServerScreenShot" in path:
        return _not_found(path)
    return _method_not_allowed(path, "POST")


async def _patch(_request):
    state = _request.app[_STATE_KEY]
    path = _request.path.rstrip("/")

    if path in (SYSTEM,):
        body = await _read_json(_request)
        if body is None:
            return _bad_request("Malformed JSON body.")
        boot = body.get("Boot", {})
        state.boot_target = boot.get("BootSourceOverrideTarget", state.boot_target)
        state.boot_enabled = boot.get("BootSourceOverrideEnabled", state.boot_enabled)
        return web.Response(status=200)

    if path == f"{SYSTEM}/Bios/Settings":
        return web.Response(status=200)
    if path == f"{SYSTEM}/BootSources/Settings":
        return web.Response(status=200)
    if "DellNetworkAttributes" in path and path.endswith("/Settings"):
        return web.Response(status=204)
    return _method_not_allowed(path, "PATCH")


async def _delete(_request):
    state = _request.app[_STATE_KEY]
    path = _request.path.rstrip("/")

    if path.startswith(f"{ROOT}/SessionService/Sessions/"):
        session_id = path.rsplit("/", 1)[-1]
        if _delete_session(state, session_id):
            return web.Response(status=200)
        return _not_found(path)
    if path.startswith(f"{MANAGER}/Jobs/"):
        job_id = path.rsplit("/", 1)[-1]
        if job_id == "JID_CLEARALL_FORCE":
            state.jobs.clear()
        else:
            state.jobs.pop(job_id, None)
        return web.Response(status=200)
    return _method_not_allowed(path, "DELETE")


def create_app():
    app = web.Application(middlewares=[_auth])
    app[_STATE_KEY] = State()
    app.router.add_get("/{path:.*}", _get)
    app.router.add_post("/{path:.*}", _post)
    app.router.add_patch("/{path:.*}", _patch)
    app.router.add_delete("/{path:.*}", _delete)
    return app


def run_daemon(args):
    app = create_app()
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(str(_CERTS / "emulator.crt"), str(_CERTS / "emulator.key"))
    host = args.get("bind") or "127.0.0.1"
    port = int(args.get("port") or 8443)
    web.run_app(app, host=host, port=port, ssl_context=context)
