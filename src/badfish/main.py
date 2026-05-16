#!/usr/bin/env python3
import asyncio
import base64
import functools

import json
import os
import re
import sys
import time
import warnings
import yaml
import tempfile
from urllib.parse import urlparse

from io import StringIO

from rich.console import Console
from rich.table import Table

from badfish.config import TIMEOUT
from badfish.helpers import get_now
from badfish.helpers.parser import parse_arguments
from badfish.helpers.logger import BadfishLogger
from badfish.helpers.http_client import HTTPClient
from badfish.helpers.exceptions import BadfishException
from badfish.helpers.progress import polling_progress

from logging import (
    DEBUG,
    INFO,
    getLogger,
)

warnings.filterwarnings("ignore")

RETRIES = 15


async def badfish_factory(
    _host,
    _username,
    _password,
    _logger=None,
    _retries=RETRIES,
    _loop=None,
    _insecure=False,
    _console=None,
    _progress_disabled=False,
    _timeout=TIMEOUT,
):
    if not _logger:
        bfl = BadfishLogger()
        _logger = bfl.logger

    badfish = Badfish(
        _host,
        _username,
        _password,
        _logger,
        _retries,
        _loop,
        _insecure,
        _console,
        _progress_disabled,
        _timeout,
    )
    await badfish.init()
    return badfish


class Badfish:
    def __init__(
        self,
        _host,
        _username,
        _password,
        _logger,
        _retries,
        _loop=None,
        _insecure=False,
        _console=None,
        _progress_disabled=False,
        _timeout=TIMEOUT,
    ):
        self.host = _host
        self.username = _username
        self.password = _password
        self.retries = _retries
        self.host_uri = "https://%s" % _host
        self.redfish_uri = "/redfish/v1"
        self.root_uri = "%s%s" % (self.host_uri, self.redfish_uri)
        self.logger = _logger
        self.semaphore = asyncio.Semaphore(50)
        self.loop = _loop
        if not self.loop:
            self.loop = asyncio.get_event_loop()
        self.http_client = HTTPClient(_host, _username, _password, _logger, _retries, _insecure, _timeout)
        self.system_resource = None
        self.manager_resource = None
        self.bios_uri = None
        self.boot_devices = None
        self.session_uri = None
        self.session_id = None
        self.token = None
        self.vendor = None
        self.console = _console if _console is not None else Console()
        self._progress_disabled = _progress_disabled
        # Tables are useful only in the same conditions as progress bars: TTY,
        # single-host, no structured output, no log file.
        self._use_tables = not _progress_disabled

    def _log_table(self, table):
        buf = StringIO()
        tmp = Console(
            file=buf, highlight=False, force_terminal=self.console.is_terminal, no_color=self.console.no_color
        )
        tmp.print(table)
        self.logger.info(buf.getvalue().rstrip("\n"), extra={"is_table": True})

    async def __aenter__(self):
        await self.init()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.delete_session()
        if exc_type is not None:
            self.logger.debug(f"Exiting context with exception: {exc_type.__name__}: {exc_val}")
        return False

    async def init(self):
        self.session_uri = await self.find_session_uri()
        self.token = await self.validate_credentials()
        try:
            self.system_resource = await self.find_systems_resource()
            self.bios_uri = "%s/Bios/Settings" % self.system_resource[len(self.redfish_uri) :]
        except BadfishException as e:
            self.logger.warning(f"Could not find system resource: {e}. Some operations may not be available.")
            self.system_resource = None
            self.bios_uri = None
        self.manager_resource = await self.find_managers_resource()

    async def error_handler(self, _response, message=None):
        try:
            raw = await _response.text("utf-8", "ignore")
            data = json.loads(raw.strip())
        except ValueError:
            raise BadfishException("Error reading response from host.")

        detail_message = data
        if "error" in data:
            try:
                detail_message = str(data["error"]["@Message.ExtendedInfo"][0]["Message"])
                resolution = str(data["error"]["@Message.ExtendedInfo"][0]["Resolution"])
                self.logger.debug(resolution)
            except (KeyError, IndexError) as ex:
                self.logger.debug(ex)
        if message:
            self.logger.debug(detail_message)
            raise BadfishException(message)
        else:
            raise BadfishException(detail_message)

    async def get_interfaces_by_type(self, host_type, _interfaces_path):
        definitions = await self.read_yaml(_interfaces_path)

        host_name_split = self.host.split(".")[0].split("-")
        host_model = None
        rack = None
        uloc = None
        host_blade = None
        prefix = [host_type]
        if len(host_name_split) > 1:
            host_model = host_name_split[-1]
            rack = host_name_split[1]
            uloc = host_name_split[2]
            prefix.extend([rack, uloc])

        if len(host_name_split) > 4:
            host_blade = host_name_split[3]
            prefix.append(host_blade)

        if host_blade:
            key = f"{host_type}_{host_blade}_{host_model}"
            interfaces_string = definitions.get(key)
            if interfaces_string:
                return interfaces_string.split(",")

        len_prefix = len(prefix)
        key = "None"
        for _ in range(len_prefix):
            prefix_string = "_".join(prefix)
            key = prefix_string
            if host_model:
                key = "_".join([prefix_string, host_model])
            interfaces_string = definitions.get(key)
            if interfaces_string:
                return interfaces_string.split(",")
            else:
                prefix.pop()

        raise BadfishException(f"Couldn't find a valid key defined on the interfaces yaml: {key}")

    async def get_boot_seq(self):
        bios_boot_mode = await self.get_bios_boot_mode()
        if bios_boot_mode == "Uefi":
            return "UefiBootSeq"
        else:
            return "BootSeq"

    async def get_bios_boot_mode(self):
        self.logger.debug("Getting bios boot mode.")
        attribute = "BootMode"
        bios_boot_mode = await self.get_bios_attribute(attribute)
        if not bios_boot_mode:
            self.logger.warning("Assuming boot mode is Bios.")
            bios_boot_mode = "Bios"
        self.logger.debug("Current boot mode: %s" % bios_boot_mode)
        return bios_boot_mode

    async def get_sriov_mode(self):
        self.logger.debug("Getting global SRIOV mode.")
        attribute = "SriovGlobalEnable"
        sriov_mode = await self.get_bios_attribute(attribute)
        return sriov_mode

    async def get_bios_attributes_registry(self):
        self.logger.debug("Getting BIOS attribute registry.")
        _uri = "%s%s/Bios/BiosRegistry" % (self.host_uri, self.system_resource)
        data = await self.http_client.get_json(_uri)

        if not data:
            self.logger.error("Operation not supported by vendor.")
            return False

        return data

    async def get_bios_attribute_registry(self, attribute):
        data = await self.get_bios_attributes_registry()
        attribute_value = await self.get_bios_attribute(attribute)
        for entry in data["RegistryEntries"]["Attributes"]:
            entries = [low_entry.lower() for low_entry in entry.values() if isinstance(low_entry, str)]
            if attribute.lower() in entries:
                for values in entry.items():
                    if values[0] == "CurrentValue":
                        self.logger.info(f"{values[0]}: {attribute_value}")
                    else:
                        self.logger.info(f"{values[0]}: {values[1]}")
                return True
        raise BadfishException(f"Unable to locate the Bios attribute: {attribute}")

    async def get_bios_attributes(self):
        self.logger.debug("Getting BIOS attributes.")
        _uri = "%s%s/Bios" % (self.host_uri, self.system_resource)
        data = await self.http_client.get_json(_uri)

        if not data:
            self.logger.error("Operation not supported by vendor.")
            return False

        return data

    async def get_bios_attribute(self, attribute):
        data = await self.get_bios_attributes()
        try:
            bios_attribute = data["Attributes"][attribute]
            return bios_attribute
        except (KeyError, TypeError):
            self.logger.warning("Could not retrieve Bios Attributes.")
            return None

    async def set_bios_attribute(self, attributes):
        data = await self.get_bios_attributes_registry()
        accepted = False
        for entry in data["RegistryEntries"]["Attributes"]:
            entries = [low_entry.lower() for low_entry in entry.values() if isinstance(low_entry, str)]
            _warnings = []
            _not_found = []
            _remove = []
            for attribute, value in attributes.items():
                if attribute.lower() in entries:
                    for values in entry.items():
                        if values[0] == "Value":
                            accepted_values = [value["ValueName"] for value in values[1]]
                            for accepted_value in accepted_values:
                                if value.lower() == accepted_value.lower():
                                    value = accepted_value
                                    accepted = True
                            if not accepted:
                                _warnings.append(f"List of accepted values for '{attribute}': {accepted_values}")

                attribute_value = await self.get_bios_attribute(attribute)
                if attribute_value:
                    if value.lower() == attribute_value.lower():
                        self.logger.warning(f"Attribute value for {attribute} is already in that state. IGNORING.")
                        _remove.append(attribute)
                else:
                    _not_found.append(f"{attribute} not found. Please check attribute name.")
            if _warnings:
                for warning in _warnings:
                    self.logger.warning(warning)
                raise BadfishException("Value not accepted")
            if _not_found:
                for warning in _not_found:
                    self.logger.error(warning)
                raise BadfishException("Attribute not found")
            if _remove:
                for attribute in _remove:
                    attributes.pop(attribute)

        _payload = {"Attributes": attributes}

        await self.patch_bios(_payload, insist=False)
        await self.reboot_server()

    async def get_boot_devices(self):
        if not self.boot_devices:
            _boot_seq = await self.get_boot_seq()
            _uri = "%s%s/BootSources" % (self.host_uri, self.system_resource)
            _response = await self.get_request(_uri)

            if _response and _response.status == 404:
                self.logger.debug(await _response.text())
                raise BadfishException("Boot order modification is not supported by this host.")

            if not _response:
                raise BadfishException("Boot order modification is not supported by this host.")

            raw = await _response.text("utf-8", "ignore")
            data = json.loads(raw.strip())
            if "Attributes" in data:
                try:
                    self.boot_devices = data["Attributes"][_boot_seq]
                except KeyError:
                    for key in data["Attributes"].keys():
                        if "bootseq" in key.lower():
                            self.logger.debug("Boot sequence found: %s" % key)
                    raise BadfishException(
                        "The boot mode does not match the boot sequence. Try again in a few minutes."
                    )
            else:
                self.logger.debug(data)
                raise BadfishException("Boot order modification is not supported by this host.")

    async def get_job_queue(self):
        self.logger.debug("Getting job queue.")
        _url = "%s%s/Jobs" % (self.host_uri, self.manager_resource)
        _response = await self.get_request(_url)

        data = await _response.text("utf-8", "ignore")
        job_queue = re.findall(r"[JR]ID_.+?\d+", data)
        jobs = [job.strip("}").strip('"').strip("'") for job in job_queue]
        return jobs

    async def get_reset_types(self, manager=False, bmc=False):
        if manager:
            resource = self.manager_resource
            endpoint = "#Manager.Reset"
        else:
            resource = self.system_resource
            endpoint = "#ComputerSystem.Reset"

        self.logger.debug("Getting allowable reset types.")
        _url = "%s%s" % (self.host_uri, resource)
        _response = await self.get_request(_url)
        reset_types = []
        if _response:
            raw = await _response.text("utf-8", "ignore")
            data = json.loads(raw.strip())
            if "Actions" not in data:
                self.logger.warning("Actions resource not found")
            else:
                reset = data["Actions"].get(endpoint)
                if reset:
                    reset_types = reset.get("ResetType@Redfish.AllowableValues", [])
                    if not reset_types:
                        if bmc:
                            reset_types = ["GracefulRestart", "ForceRestart"]
                        else:
                            self.logger.warning("Could not get allowable reset types")
        return reset_types

    async def read_yaml(self, _yaml_file):
        with open(_yaml_file, "r") as f:
            try:
                definitions = yaml.safe_load(f)
            except yaml.YAMLError as ex:
                self.logger.debug(ex)
                raise BadfishException("Couldn't read file: %s" % _yaml_file)
        return definitions

    async def get_host_types_from_yaml(self, _interfaces_path):
        definitions = await self.read_yaml(_interfaces_path)
        host_types = set()
        for line in definitions:
            _split = line.split("_")
            host_types.add(_split[0])

        ordered_types = sorted(list(host_types))
        return ordered_types

    async def get_host_type(self, _interfaces_path):
        await self.get_boot_devices()
        if _interfaces_path:
            host_types = await self.get_host_types_from_yaml(_interfaces_path)
            for host_type in host_types:
                match = True
                try:
                    interfaces = await self.get_interfaces_by_type(host_type, _interfaces_path)
                except BadfishException as ex:
                    self.logger.debug(str(ex))
                    continue

                for device in sorted(self.boot_devices[: len(interfaces)], key=lambda x: x["Index"]):
                    if device["Name"] == interfaces[device["Index"]]:
                        continue
                    else:
                        match = False
                        break
                if match:
                    return host_type

        return None

    async def find_session_uri(self):
        response = await self.http_client.get_request(self.root_uri, _get_token=True)

        if not response:
            raise BadfishException(f"Failed to communicate with {self.host}")

        if response.status == 401:
            raise BadfishException(f"Failed to authenticate. Verify your credentials for {self.host}")

        raw = await response.text("utf-8", "ignore")
        data = json.loads(raw.strip())
        try:
            redfish_version = int(data["RedfishVersion"].replace(".", ""))
        except KeyError:
            raise BadfishException("Was unable to get Redfish Version. Please verify credentials/host.")
        session_uri = None
        if redfish_version >= 160:
            session_uri = "/redfish/v1/SessionService/Sessions"
        elif redfish_version < 160:
            session_uri = "/redfish/v1/Sessions"

        _uri = "%s%s" % (self.host_uri, session_uri)
        check_response = await self.http_client.get_request(_uri, _continue=True, _get_token=True)
        if check_response is None or check_response.status != 200:
            session_uri = "/redfish/v1/SessionService/Sessions"

        return session_uri

    async def validate_credentials(self):
        payload = {"UserName": self.username, "Password": self.password}
        headers = {"content-type": "application/json"}
        _uri = "%s%s" % (self.host_uri, self.session_uri)

        _response = await self.http_client.post_request(_uri, payload, headers, _get_token=True)

        await _response.text("utf-8", "ignore")

        status = _response.status
        if status == 401:
            raise BadfishException(f"Failed to authenticate. Verify your credentials for {self.host}")
        if status not in [200, 201]:
            raise BadfishException(f"Failed to communicate with {self.host}")

        # Extract token from response headers
        token = _response.headers.get("X-Auth-Token")
        if token:
            self.token = token
            self.http_client.token = token
            # Store session info for cleanup
            self.session_id = _response.headers.get("Location")

        return token

    async def get_interfaces_endpoints(self):
        _uri = "%s%s/EthernetInterfaces" % (self.host_uri, self.system_resource)
        data = await self.http_client.get_json(_uri)

        if not data:
            raise BadfishException("EthernetInterfaces entry point not supported by this host.")

        endpoints = []
        if data.get("Members"):
            for member in data["Members"]:
                endpoints.append(member["@odata.id"])
        else:
            raise BadfishException("EthernetInterfaces's Members array is either empty or missing")

        return endpoints

    async def get_interface(self, endpoint):
        _uri = "%s%s" % (self.host_uri, endpoint)
        data = await self.http_client.get_json(_uri)

        if not data:
            raise BadfishException("EthernetInterface entry point not supported by this host.")

        return data

    async def find_systems_resource(self):
        response = await self.http_client.get_request(self.root_uri)
        if not response:
            raise BadfishException("Failed to communicate with server.")

        raw = await response.text("utf-8", "ignore")
        data = json.loads(raw.strip())
        if "Systems" not in data:
            raise BadfishException("Systems resource not found")

        systems = data["Systems"]["@odata.id"]
        systems_response = await self.http_client.get_request(self.host_uri + systems)
        if not systems_response:
            raise BadfishException("Authorization Error: verify credentials.")

        raw = await systems_response.text("utf-8", "ignore")
        systems_data = json.loads(raw.strip())

        if systems_data.get("Members"):
            for member in systems_data["Members"]:
                systems_service = member["@odata.id"]
                self.logger.debug("Systems service: %s." % systems_service)
                return systems_service
        else:
            raise BadfishException("ComputerSystem's Members array is either empty or missing")

    async def find_managers_resource(self):
        response = await self.http_client.get_request(self.root_uri)
        if not response:
            raise BadfishException("Failed to communicate with server.")

        raw = await response.text("utf-8", "ignore")
        data = json.loads(raw.strip())
        self.vendor = "Dell" if data.get("Oem") and "Dell" in data["Oem"] else "Supermicro"

        if "Managers" not in data:
            raise BadfishException("Managers resource not found")

        managers = data["Managers"]["@odata.id"]
        managers_response = await self.http_client.get_request(self.host_uri + managers)
        managers_data = None
        if managers_response:
            raw = await managers_response.text("utf-8", "ignore")
            managers_data = json.loads(raw.strip())
        if managers_data and managers_data.get("Members"):
            for member in managers_data["Members"]:
                managers_service = member["@odata.id"]
                self.logger.debug("Managers service: %s." % managers_service)
                return managers_service
        else:
            raise BadfishException("Manager's Members array is either empty or missing")

    # HTTP client wrapper methods
    async def get_request(self, uri, _continue=False, _get_token=False):
        return await self.http_client.get_request(uri, _continue, _get_token)

    async def post_request(self, uri, payload, headers, _get_token=False):
        return await self.http_client.post_request(uri, payload, headers, _get_token)

    async def patch_request(self, uri, payload, headers, _continue=False):
        return await self.http_client.patch_request(uri, payload, headers, _continue)

    async def delete_request(self, uri, headers):
        return await self.http_client.delete_request(uri, headers)

    async def get_power_state(self):
        _uri = "%s%s" % (self.host_uri, self.system_resource)
        self.logger.debug("url: %s" % _uri)

        data = await self.http_client.get_json(_uri, _continue=True)
        if not data:
            self.logger.debug("Couldn't get power state. Retrying.")
            return "Down"

        if not data.get("PowerState"):
            raise BadfishException("Power state not found. Try to racreset.")
        else:
            self.logger.debug("Current server power state is: %s." % data["PowerState"])

        return data["PowerState"]

    async def set_power_state(self, state):
        if state.lower() not in ["on", "off"]:
            raise BadfishException("Power state not valid. 'on' or 'off' only accepted.")

        _uri = "%s%s" % (self.host_uri, self.system_resource)
        self.logger.debug("url: %s" % _uri)

        _response = await self.get_request(_uri, _continue=True)
        if not _response and state.lower() == "off":
            self.logger.warning("Power state appears to be already set to 'off'.")
            return

        status = _response.status
        if status == 200:
            raw = await _response.text("utf-8", "ignore")
            data = json.loads(raw.strip())
        else:
            raise BadfishException("Couldn't get power state.")

        if not data.get("PowerState"):
            raise BadfishException("Power state not found. Try to racreset.")
        else:
            self.logger.debug("Current server power state is: %s." % data["PowerState"])

        if state.lower() == "off":
            await self.send_reset("ForceOff")
        elif state.lower() == "on":
            await self.send_reset("On")

        return data["PowerState"]

    async def get_power_consumed_watts(self):
        _uri = "%s%s/Chassis/%s/Power" % (self.host_uri, self.redfish_uri, self.system_resource.split("/")[-1])
        _response = await self.get_request(_uri)

        if _response.status == 404:
            self.logger.error("Operation not supported by vendor.")
            return False
        try:
            raw = await _response.text("utf-8", "ignore")
            data = json.loads(raw.strip())
        except ValueError:
            raise BadfishException("Power value outside operating range.")
        try:
            cwc = data["PowerControl"][0]["PowerConsumedWatts"]
        except IndexError:
            cwc = "N/A. Try to `--racreset`."
        self.logger.info(f"Current watts consumed: {cwc}")
        return

    async def change_boot(self, host_type, interfaces_path, pxe=False):
        if interfaces_path:
            if not os.path.exists(interfaces_path):
                raise BadfishException("No such file or directory: '%s'." % interfaces_path)
            host_types = await self.get_host_types_from_yaml(interfaces_path)
            if host_type.lower() not in host_types:
                raise BadfishException(f"Expected values for -t argument are: {host_types}")
        else:
            raise BadfishException("You must provide a path to the interfaces yaml via `-i` optional argument.")
        _type = None
        if host_type.lower() != "uefi":
            _type = await self.get_host_type(interfaces_path)
        if (_type and _type.lower() != host_type.lower()) or not _type:
            await self.clear_job_queue()
            if host_type.lower() == "uefi":
                payload = dict()
                boot_mode = await self.get_bios_boot_mode()
                if boot_mode.lower() != "uefi":
                    payload["BootMode"] = "Uefi"
                interfaces = await self.get_interfaces_by_type(host_type, interfaces_path)

                for i, interface in enumerate(interfaces, 1):
                    payload[f"PxeDev{i}Interface"] = interface
                    payload[f"PxeDev{i}EnDis"] = "Enabled"

                await self.set_bios_attribute(payload)

            else:
                boot_mode = await self.get_bios_boot_mode()
                if boot_mode.lower() == "uefi":
                    self.logger.warning(
                        "Changes being requested will be valid for Bios BootMode. " "Current boot mode is set to Uefi."
                    )
                await self.change_boot_order(host_type, interfaces_path)

                if pxe:
                    await self.set_next_boot_pxe()

                await self.create_bios_config_job(self.bios_uri)

                await self.reboot_server(graceful=False)

        else:
            self.logger.warning("No changes were made since the boot order already matches the requested.")
        return True

    async def change_boot_order(self, _host_type, _interfaces_path):
        interfaces = await self.get_interfaces_by_type(_host_type, _interfaces_path)

        await self.get_boot_devices()
        devices = [device["Name"] for device in self.boot_devices]
        valid_devices = [device for device in interfaces if device in devices]
        if len(valid_devices) < len(interfaces):
            diff = [device for device in interfaces if device not in valid_devices]
            self.logger.warning("Some interfaces are not valid boot devices. Ignoring: %s" % ", ".join(diff))
        change = False
        ordered_devices = self.boot_devices.copy()
        for i, interface in enumerate(valid_devices):
            for device in ordered_devices:
                if interface == device["Name"]:
                    if device["Index"] != i:
                        device["Index"] = i
                        change = True
                    break

        if change:
            await self.patch_boot_seq(ordered_devices)
        else:
            self.logger.warning("No changes were made since the boot order already matches the requested.")

    async def patch_boot_seq(self, ordered_devices):
        _boot_seq = await self.get_boot_seq()
        boot_sources_uri = "%s/BootSources/Settings" % self.system_resource
        url = "%s%s" % (self.host_uri, boot_sources_uri)
        payload = {"Attributes": {_boot_seq: ordered_devices}}
        headers = {"content-type": "application/json"}
        response = None
        _status_code = 400

        for _ in range(self.retries):
            if _status_code != 200:
                response = await self.patch_request(url, payload, headers, True)
                if response:
                    raw = await response.text("utf-8", "ignore")
                    self.logger.debug(raw)
                    _status_code = response.status
            else:
                break

        if _status_code == 200:
            self.logger.debug("PATCH command passed to update boot order.")
        else:
            self.logger.error("There was something wrong with your request.")

            if response:
                await self.error_handler(response)

    async def set_next_boot_pxe(self):
        _url = "%s%s" % (self.host_uri, self.system_resource)
        _payload = {
            "Boot": {
                "BootSourceOverrideTarget": "Pxe",
                "BootSourceOverrideEnabled": "Once",
            }
        }
        _headers = {"content-type": "application/json"}
        _response = await self.patch_request(_url, _payload, _headers)

        await asyncio.sleep(5)

        if _response.status == 200:
            self.logger.info('PATCH command passed to set next boot onetime boot device to: "%s".' % "Pxe")
        else:
            self.logger.error("Command failed, error code is %s." % _response.status)

            await self.error_handler(_response)

    async def check_supported_idrac_version(self):
        _url = "%s/Dell/Managers/iDRAC.Embedded.1/DellJobService/" % self.root_uri
        _response = await self.get_request(_url)
        if _response.status != 200:
            self.logger.warning("iDRAC version installed does not support DellJobService")
            return False

        return True

    async def check_supported_network_interfaces(self, endpoint):
        _url = "%s%s/%s" % (self.host_uri, self.system_resource, endpoint)
        _response = await self.get_request(_url)
        if _response.status != 200:
            return False

        return True

    async def delete_job_queue_dell(self, force):
        _url = "%s/Dell/Managers/iDRAC.Embedded.1/DellJobService/Actions/DellJobService.DeleteJobQueue" % self.root_uri
        job_id = "JID_CLEARALL"
        if force:
            job_id = f"{job_id}_FORCE"
        _payload = {"JobID": job_id}
        _headers = {"content-type": "application/json"}
        response = await self.post_request(_url, _payload, _headers)
        if response.status == 200:
            self.logger.info("Job queue for iDRAC %s successfully cleared." % self.host)
        else:
            await self.error_handler(
                response,
                message="Job queue not cleared, there was something wrong with your request.",
            )

    async def delete_job_queue_force(self):
        _url = "%s%s/Jobs" % (self.host_uri, self.manager_resource)
        _headers = {"content-type": "application/json"}
        url = "%s/JID_CLEARALL_FORCE" % _url
        try:
            _response = await self.delete_request(url, _headers)
            if _response.status in [200, 204]:
                self.logger.info("Job queue for iDRAC %s successfully cleared." % self.host)
        except BadfishException as ex:
            self.logger.debug(ex)
            raise BadfishException("There was something wrong clearing the job queue.")
        return _response

    async def clear_job_list(self, _job_queue):
        _url = "%s%s/Jobs" % (self.host_uri, self.manager_resource)
        _headers = {"content-type": "application/json"}
        self.logger.warning("Clearing job queue for job IDs: %s." % _job_queue)
        for _job in _job_queue:
            job = _job.strip("'")
            url = "/".join([_url, job])
            response = await self.delete_request(url, _headers)
            if response.status != 200:
                raise BadfishException("Job queue not cleared, there was something wrong with your request.")

        self.logger.info("Job queue for iDRAC %s successfully cleared." % self.host)
        return True

    async def clear_job_queue(self, force=False):
        _job_queue = await self.get_job_queue()
        if _job_queue or force:
            supported = await self.check_supported_idrac_version()
            if supported:
                await self.delete_job_queue_dell(force)
            else:
                try:
                    _response = await self.delete_job_queue_force()
                    if _response.status == 400:
                        await self.clear_job_list(_job_queue)
                except BadfishException:
                    self.logger.info("Attempting to clear job list instead.")
                    await self.clear_job_list(_job_queue)
        else:
            self.logger.warning("Job queue already cleared for iDRAC %s, DELETE command will not execute." % self.host)

    async def list_job_queue(self):
        _job_queue = await self.get_job_queue()
        if _job_queue:
            self.logger.info("Found active jobs:")
            for job in _job_queue:
                self.logger.info("    JobID: " + job)
        else:
            self.logger.info("Found active jobs: None")

    async def create_job(self, _url, _payload, _headers, expected=None):
        if not expected:
            expected = [200, 204]
        _response = await self.post_request(_url, _payload, _headers)

        status_code = _response.status
        if status_code in expected:
            self.logger.debug("POST command passed to create target config job.")
        else:  # pragma: no cover
            # Defensive error handling: POST failures typically raise exceptions in http_client
            # before returning, making this path difficult to test in isolation
            self.logger.error("POST command failed to create BIOS config job, status_code is %s." % status_code)
            await self.error_handler(_response)

        job_id = self._extract_job_id_from_response(_response, warn_on_missing=False)
        if job_id:
            self.logger.debug("%s job ID successfully created" % job_id)
        return job_id

    async def create_bios_config_job(self, uri):
        _url = "%s%s/Jobs" % (self.host_uri, self.manager_resource)
        _payload = {"TargetSettingsURI": "%s%s" % (self.redfish_uri, uri)}
        _headers = {"content-type": "application/json"}
        return await self.create_job(_url, _payload, _headers)

    async def check_schedule_job_status(self, job_id):
        _url = f"{self.host_uri}{self.manager_resource}/Jobs/{job_id}"
        _response = await self.get_request(_url)

        if _response:
            status_code = _response.status
            raw = await _response.text("utf-8", "ignore")
            data = json.loads(raw.strip())

            if status_code == 200:
                await asyncio.sleep(10)
                # Only try to access job data if we got a successful response
                if isinstance(data, dict) and "Id" in data:
                    self.logger.info(f"JobID: {data[u'Id']}")
                    self.logger.info(f"Name: {data[u'Name']}")
                    self.logger.info(f"Message: {data[u'Message']}")
                    self.logger.info(f"PercentComplete: {str(data[u'PercentComplete'])}")
            else:
                self.logger.error(f"Command failed to check job status, return code is {status_code}")
                self.logger.debug(f"Extended Info Message: {data}")
                return False
        else:
            self.logger.error("Command failed to check job status")
            return False

    async def check_job_status(self, job_id):
        with polling_progress(self.console, self.retries, "Status", disable=self._progress_disabled) as (
            progress,
            task_id,
        ):
            for count in range(self.retries):
                _url = f"{self.host_uri}{self.manager_resource}/Jobs/{job_id}"
                self.http_client.get_request.cache_clear()
                _response = await self.get_request(_url)

                status_code = _response.status
                raw = await _response.text("utf-8", "ignore")
                data = json.loads(raw.strip())
                if status_code != 200:
                    self.logger.error(f"Command failed to check job status, return code is {status_code}")
                    self.logger.debug(f"Extended Info Message: {data}")
                    return False

                if "Message" not in data:
                    self.logger.warning("Job status response missing Message field")
                    return False

                if "Fail" in data["Message"] or "fail" in data["Message"]:
                    self.logger.debug(f"\n{job_id} job failed.")
                    return False
                elif data["Message"] == "Job completed successfully.":
                    self.logger.info(f"JobID: {data[u'Id']}")
                    self.logger.info(f"Name: {data[u'Name']}")
                    self.logger.info(f"Message: {data[u'Message']}")
                    self.logger.info(f"PercentComplete: {str(data[u'PercentComplete'])}")
                    break
                else:
                    progress.update(task_id, completed=count + 1, state=data["Message"])
                    await asyncio.sleep(30)

    def _extract_job_id_from_response(self, response, warn_on_missing=True, context=""):
        """
        Extract job ID from HTTP response Location header.

        Args:
            response: HTTP response object with headers
            warn_on_missing: If True, log warning when job ID not found. If False, log error.
            context: Additional context message to append to warning/error (optional)

        Returns:
            Job ID string or None if not found
        """
        try:
            job_id = response.headers.get("Location", "").split("/")[-1]
            if job_id:
                return job_id
            else:
                if warn_on_missing:
                    msg = "No job ID returned in Location header."
                    if context:
                        msg += f" {context}"
                    self.logger.warning(msg)
                else:
                    self.logger.error("Failed to find a job ID in headers of the response.")
                return None
        except (AttributeError, ValueError, KeyError) as e:  # pragma: no cover
            # Defensive: headers.get() raising exceptions is extremely rare in practice
            if warn_on_missing:
                msg = f"Could not extract job ID from response headers: {e}"
                if context:
                    msg += f" {context}"
                self.logger.warning(msg)
            else:
                self.logger.error(f"Failed to find a job ID in headers of the response: {e}")
            return None

    async def _verify_job_scheduled(self, job_id, context="configuration"):
        """
        Verify that a job has been scheduled and is not already failed.

        This is typically called before rebooting to ensure the job is in a good state.

        Args:
            job_id: The job ID to verify
            context: Description of the job context for error messages (default: "configuration")

        Returns:
            True if job is scheduled successfully, False if job failed or inaccessible
        """
        self.logger.info(f"Waiting for {context} job to be scheduled...")
        # Give job a moment to register in job queue
        await asyncio.sleep(2)

        # Check job status to ensure it's scheduled properly
        job_url = f"{self.host_uri}{self.manager_resource}/Jobs/{job_id}"
        try:
            job_response = await self.get_request(job_url)
            if job_response.status == 200:
                job_raw = await job_response.text("utf-8", "ignore")
                job_data = json.loads(job_raw.strip())
                job_state = job_data.get("JobState", "Unknown")
                job_message = job_data.get("Message", "No message")
                self.logger.info(f"Job {job_id} status: {job_state} - {job_message}")

                if "Fail" in job_message or "fail" in job_message or job_state == "Failed":
                    self.logger.error(f"{context.capitalize()} job failed before reboot: {job_message}")
                    return False
                return True
            else:  # pragma: no cover
                # Defensive: non-200 responses during job verification are rare
                self.logger.warning(
                    f"Could not verify job status (HTTP {job_response.status}). Proceeding with reboot."
                )
                return True  # Don't block on verification failure
        except Exception as e:  # pragma: no cover
            # Defensive: exceptions during job status check are rare in practice
            self.logger.warning(f"Could not check job status before reboot: {e}. Proceeding anyway.")
            return True  # Don't block on verification failure

    async def _monitor_and_verify_attribute_job(
        self, job_id, fqdd, attribute, expected_value, attr_type, original_value
    ):
        """
        Monitor job completion and verify the attribute value was actually applied.

        This handles the full post-reboot workflow:
        1. Wait for job to complete
        2. If job fails, still verify the actual value (detect false negatives)
        3. If job succeeds, verify the value matches expectation

        Args:
            job_id: The job ID to monitor
            fqdd: NIC FQDD (e.g., "NIC.Embedded.1-1-1")
            attribute: Attribute name (e.g., "WakeOnLan")
            expected_value: Expected value after change
            attr_type: Attribute type ("Integer", "String", "Enumeration")
            original_value: Original value before change (for logging)

        Returns:
            True if value was successfully applied, False otherwise
        """
        self.logger.info(f"Monitoring job {job_id} for completion...")
        job_success = await self.check_job_status(job_id)

        # Job reported failure - but still verify actual value to detect false negatives
        if job_success is False:
            self.logger.error(f"Configuration job {job_id} did not complete successfully.")
            self.logger.error("Network attribute changes may not have been applied.")

            verification = await self.get_nic_attribute_info(fqdd, attribute, log=False)
            if verification:
                current_val = verification.get("CurrentValue")
                if current_val == expected_value:
                    self.logger.warning(
                        f"Job reported failure but attribute value is correct ({attribute}={current_val}). "
                        "This may be a false negative."
                    )
                    return True
            return False

        # Job succeeded - verify attribute value actually changed
        self.logger.info("Verifying attribute value was applied...")
        verification = await self.get_nic_attribute_info(fqdd, attribute, log=False)
        if verification:
            current_val = verification.get("CurrentValue")
            # Handle type conversion for comparison
            if attr_type == "Integer":
                current_val = int(current_val) if current_val is not None else None
                expected_value = int(expected_value)

            if current_val == expected_value:
                self.logger.info(f"✓ Successfully changed {attribute} from {original_value} to {expected_value}")
                return True
            else:
                self.logger.error(
                    f"✗ Attribute value did not persist. Expected: {expected_value}, Current: {current_val}"
                )
                self.logger.error(
                    "Job completed but value not applied. Possible causes: "
                    "prerequisite not met, validation failure, or firmware issue."
                )
                return False
        else:
            self.logger.error("Could not verify final attribute value.")
            return False

    async def send_reset(self, reset_type):
        _url = "%s%s/Actions/ComputerSystem.Reset" % (
            self.host_uri,
            self.system_resource,
        )
        _payload = {"ResetType": reset_type}
        _headers = {"content-type": "application/json"}
        _response = await self.post_request(_url, _payload, _headers)

        status_code = _response.status
        if status_code in [200, 204]:
            self.logger.info("Command passed to %s server, code return is %s." % (reset_type, status_code))
            await asyncio.sleep(10)
            return True
        elif status_code == 409:
            self.logger.warning("Command failed to %s server, host appears to be already in that state." % reset_type)
        else:
            self.logger.error("Command failed to %s server, status code is: %s." % (reset_type, status_code))

            await self.error_handler(_response)
        return False

    async def reboot_server(self, graceful=True):
        _reset_types = await self.get_reset_types()
        reset_type = "GracefulRestart"
        if reset_type not in _reset_types:
            for rt in _reset_types:
                if "restart" in rt.lower():
                    reset_type = rt

        self.logger.debug("Rebooting server: %s." % self.host)
        power_state = await self.get_power_state()
        if power_state.lower() == "on":
            if graceful:
                response = await self.send_reset(reset_type)

                if not response:
                    host_down = await self.polling_host_state("Off")

                    if not host_down:
                        self.logger.warning("Unable to graceful shutdown the server, will perform forced shutdown now.")
                        await self.send_reset("ForceOff")
            else:
                await self.send_reset("ForceOff")

            host_not_down = await self.polling_host_state("Down", False)

            if host_not_down:
                await self.send_reset("On")

        elif power_state.lower() == "off":
            await self.send_reset("On")
        return True

    async def reset_idrac(self, wait=False):
        if self.vendor != "Dell":
            self.logger.warning("Vendor isn't a Dell, if you are trying this on a Supermicro, use --bmc-reset instead.")
            return False
        self.logger.debug("Running reset iDRAC.")
        _reset_types = await self.get_reset_types(manager=True)
        reset_type = "ForceRestart"
        if reset_type not in _reset_types:
            for rt in _reset_types:
                if "restart" in rt.lower():
                    reset_type = rt
        _url = "%s%s/Actions/Manager.Reset/" % (self.host_uri, self.manager_resource)
        _payload = {"ResetType": reset_type}
        _headers = {"content-type": "application/json"}
        self.logger.debug("url: %s" % _url)
        self.logger.debug("payload: %s" % _payload)
        self.logger.debug("headers: %s" % _headers)
        _response = await self.post_request(_url, _payload, _headers)

        status_code = _response.status
        if status_code in [200, 204]:
            self.logger.info("Status code %s returned for POST command to reset iDRAC." % status_code)
        else:
            data = await _response.text("utf-8", "ignore")
            raise BadfishException("Status code %s returned, error is: \n%s." % (status_code, data))

        if wait:
            self.logger.info("iDRAC reset initiated. Waiting for iDRAC to come back online...")
            ready = await self.wait_for_idrac_ready()
            if ready:
                self.logger.info("iDRAC is now responsive.")
            else:
                self.logger.warning("iDRAC did not respond after %d retry attempts." % self.retries)
            return ready
        else:
            self.logger.info("iDRAC will now reset and be back online within a few minutes.")
            return True

    async def reset_bmc(self):
        if self.vendor != "Supermicro":
            self.logger.warning("Vendor isn't a Supermicro, if you are trying this on a Dell, use --racreset instead.")
            return False
        self.logger.debug("Running reset BMC.")
        _reset_types = await self.get_reset_types(manager=True, bmc=True)
        reset_type = "GracefulRestart"
        if reset_type not in _reset_types:
            for rt in _reset_types:
                if "restart" in rt.lower():
                    reset_type = rt
        _url = "%s%s/Actions/Manager.Reset/" % (self.host_uri, self.manager_resource)
        _payload = {"ResetType": reset_type}
        _headers = {"content-type": "application/json"}
        self.logger.debug("url: %s" % _url)
        self.logger.debug("payload: %s" % _payload)
        self.logger.debug("headers: %s" % _headers)
        _response = await self.post_request(_url, _payload, _headers)

        status_code = _response.status
        if status_code == 200:
            self.logger.info("Status code %s returned for POST command to reset BMC." % status_code)
        else:
            data = await _response.text("utf-8", "ignore")
            raise BadfishException("Status code %s returned, error is: \n%s." % (status_code, data))

        self.logger.info("BMC will now reset and be back online within a few minutes.")
        return True

    async def reset_bios(self):
        self.logger.debug("Running BIOS reset.")
        _url = "%s%s/Bios/Actions/Bios.ResetBios/" % (
            self.host_uri,
            self.system_resource,
        )
        _payload = {}
        _headers = {"content-type": "application/json"}
        self.logger.debug("url: %s" % _url)
        self.logger.debug("payload: %s" % _payload)
        self.logger.debug("headers: %s" % _headers)
        _response = await self.post_request(_url, _payload, _headers)

        status_code = _response.status
        if status_code in [200, 204]:
            self.logger.info("Status code %s returned for POST command to reset BIOS." % status_code)
        else:
            data = await _response.text("utf-8", "ignore")
            raise BadfishException("Status code %s returned, error is: \n%s." % (status_code, data))

        self.logger.info("BIOS will now reset and be back online within a few minutes.")
        return True

    async def boot_to(self, device, skip_job=False):
        device_check = await self.check_device(device)
        if device_check:
            await self.clear_job_queue()
            await self.send_one_time_boot(device)
            if not skip_job:
                await self.create_bios_config_job(self.bios_uri)
        else:
            return False
        return True

    async def boot_to_type(self, host_type, _interfaces_path):
        if _interfaces_path:
            if not os.path.exists(_interfaces_path):
                raise BadfishException("No such file or directory: %s." % _interfaces_path)
        else:
            raise BadfishException("You must provide a path to the interfaces yaml via `-i` optional argument.")
        host_types = await self.get_host_types_from_yaml(_interfaces_path)
        if host_type.lower() not in host_types:
            raise BadfishException(f"Expected values for -t argument are: {host_types}")

        device = await self.get_host_type_boot_device(host_type, _interfaces_path)

        await self.boot_to(device, True)

    async def boot_to_mac(self, mac_address):
        interfaces_endpoints = await self.get_interfaces_endpoints()

        device = None
        for endpoint in interfaces_endpoints:
            interface = await self.get_interface(endpoint)
            if interface.get("MACAddress", "").upper() == mac_address.upper():
                device = interface.get("Id")
                break

        if device:
            await self.boot_to(device)
        else:
            raise BadfishException("MAC Address does not match any of the existing")

    async def send_one_time_boot(self, device):
        boot_seq = await self.get_boot_seq()
        _payload = {
            "Attributes": {
                "OneTimeBootMode": f"OneTime{boot_seq}",
                f"OneTime{boot_seq}Dev": device,
            }
        }
        await self.patch_bios(_payload)

    async def send_sriov_mode(self, enable):
        value = "Enabled" if enable else "Disabled"
        _payload = {
            "Attributes": {
                "SriovGlobalEnable": value,
            }
        }

        sriov_mode = await self.get_sriov_mode()
        if (sriov_mode.lower() == "enabled" and enable) or (sriov_mode.lower() == "disabled" and not enable):
            self.logger.warning("SRIOV mode is already in that state. IGNORING.")
            return

        await self.patch_bios(_payload)
        await self.reboot_server()

    async def patch_bios(self, payload, insist=True):
        _url = "%s%s" % (self.root_uri, self.bios_uri)
        _headers = {"content-type": "application/json"}
        _first_reset = False
        payload_patch = {"@Redfish.SettingsApplyTime": {"ApplyTime": "OnReset"}}
        payload_patch.update(payload)
        for i in range(self.retries):
            _response = await self.patch_request(_url, payload_patch, _headers)
            status_code = _response.status
            if status_code in [200, 202]:
                self.logger.info("Command passed to set BIOS attribute pending values.")
                break
            else:
                self.logger.error("Command failed, error code is: %s." % status_code)
                if status_code == 503 and i - 1 != self.retries:
                    self.logger.info("Retrying to send one time boot.")
                    continue
                elif status_code == 400 and insist:
                    await self.clear_job_queue()
                    if not _first_reset:
                        await self.reset_idrac()
                        await asyncio.sleep(10)
                        _first_reset = True
                        await self.polling_host_state("On")
                    continue
                await self.error_handler(_response)

    async def check_boot(self, _interfaces_path):
        if not self.boot_devices:
            await self.get_boot_devices()

        if _interfaces_path:
            _host_type = await self.get_host_type(_interfaces_path)
            if _host_type:
                self.logger.warning("Current boot order is set to: %s." % _host_type)
                return True
            else:
                self.logger.warning("Current boot order does not match any of the given.")

        self.logger.info("Current boot order:")
        if self._use_tables:
            table = Table(show_header=True, header_style="bold")
            table.add_column("#", justify="right")
            table.add_column("Device")
            table.add_column("Status")
            for device in sorted(self.boot_devices, key=lambda x: x["Index"]):
                status = "Enabled" if device["Enabled"] else "Disabled"
                table.add_row(str(int(device["Index"]) + 1), device["Name"], status)
            self._log_table(table)
        else:
            for device in sorted(self.boot_devices, key=lambda x: x["Index"]):
                enabled = "" if device["Enabled"] else " (DISABLED)"
                self.logger.info("%s: %s%s" % (int(device["Index"]) + 1, device["Name"], enabled))
        return True

    async def check_device(self, device):
        self.logger.debug("Checking device %s." % device)
        await self.get_boot_devices()
        self.logger.debug(self.boot_devices)
        boot_devices = [_device["Name"].lower() for _device in self.boot_devices]
        if device.lower() in boot_devices:
            return True
        else:
            self.logger.error(
                "Device %s does not match any of the available boot devices for host %s" % (device, self.host)
            )
            return False

    async def polling_host_state(self, state, equals=True):
        state_str = "Not %s" % state if not equals else state
        self.logger.info("Polling for host state: %s" % state_str)
        desired_state = False
        with polling_progress(self.console, self.retries, "Host state", disable=self._progress_disabled) as (
            progress,
            task_id,
        ):
            for count in range(self.retries):
                current_state = await self.get_power_state()
                if equals:
                    desired_state = current_state.lower() == state.lower()
                else:
                    desired_state = current_state.lower() != state.lower()
                await asyncio.sleep(5)
                if desired_state:
                    progress.update(task_id, completed=self.retries, state=current_state)
                    break
                progress.update(task_id, completed=count + 1, state=current_state)

        return desired_state

    async def poll_until_ready(self, check_func, description, sleep_interval=5, clear_cache=False):
        self.logger.info("Polling for %s" % description)
        with polling_progress(self.console, self.retries, "Host state", disable=self._progress_disabled) as (
            progress,
            task_id,
        ):
            for count in range(self.retries):
                if clear_cache:
                    self.http_client.get_request.cache_clear()
                ready = await check_func()
                if ready:
                    progress.update(task_id, completed=self.retries, state="Ready")
                    self.logger.info("%s is ready." % description)
                    return True
                progress.update(task_id, completed=count + 1, state="Not Ready")
                await asyncio.sleep(sleep_interval)
        self.logger.warning("%s did not become ready after %d retry attempts." % (description, self.retries))
        return False

    async def wait_for_idrac_ready(self):
        async def check_idrac_responsive():
            response = await self.get_request(self.root_uri, _continue=True)
            return response and response.status == 200

        self.logger.info("Waiting for iDRAC to be ready after reset (this may take a few minutes)...")
        await asyncio.sleep(10)
        return await self.poll_until_ready(check_idrac_responsive, "iDRAC", sleep_interval=10, clear_cache=True)

    async def get_firmware_inventory(self):
        self.logger.debug("Getting firmware inventory for all devices supported by iDRAC.")

        _url = "%s/UpdateService/FirmwareInventory/" % self.root_uri
        _response = await self.get_request(_url)

        try:
            raw = await _response.text("utf-8", "ignore")
            data = json.loads(raw.strip())
        except ValueError:
            raise BadfishException("Not able to access Firmware inventory.")
        installed_devices = []
        if "error" in data:
            self.logger.debug(data["error"])
            raise BadfishException("Not able to access Firmware inventory.")
        for device in data["Members"]:
            a = device["@odata.id"]
            a = a.replace("/redfish/v1/UpdateService/FirmwareInventory/", "")
            if "Installed" in a:
                installed_devices.append(a)

        _SKIP = {"odata", "Description", "Oem"}
        rows = []
        for device in installed_devices:
            self.logger.debug("Getting device info for %s" % device)
            _uri = "%s/UpdateService/FirmwareInventory/%s" % (self.root_uri, device)

            _response = await self.get_request(_uri, _continue=True)
            if not _response:
                continue

            raw = await _response.text("utf-8", "ignore")
            data = json.loads(raw.strip())
            row = {k: v for k, v in data.items() if not any(s in k for s in _SKIP)}
            rows.append(row)

        if rows:
            if self._use_tables:
                cols = ["Id", "Name", "Version", "Manufacturer", "Status"]
                table = Table(show_header=True, header_style="bold")
                for col in cols:
                    table.add_column(col)
                for row in rows:
                    status = row.get("Status")
                    if isinstance(status, dict):
                        status = status.get("State", "")
                    table.add_row(
                        str(row.get("Id", "")),
                        str(row.get("Name", "")),
                        str(row.get("Version", "")),
                        str(row.get("Manufacturer", "")),
                        str(status or ""),
                    )
                self._log_table(table)
            else:
                for row in rows:
                    self.logger.info("%s:" % row.get("Id", ""))
                    for k, v in row.items():
                        self.logger.info("    %s: %s" % (k, v))

    async def get_host_type_boot_device(self, host_type, _interfaces_path):
        if _interfaces_path:
            interfaces = await self.get_interfaces_by_type(host_type, _interfaces_path)
        else:
            raise BadfishException("You must provide a path to the interfaces yaml via `-i` optional argument.")

        return interfaces[0]

    async def toggle_boot_device(self, device):
        if not self.boot_devices:
            await self.get_boot_devices()

        if device not in [boot_device["Name"] for boot_device in self.boot_devices]:
            self.logger.warning("Accepted device names:")
            for device in self.boot_devices:
                self.logger.warning(f"{device['Name']}")
            raise BadfishException("Boot device name not found")

        new_boot_seq = self.boot_devices.copy()
        state = ""
        for boot_device in new_boot_seq:
            if boot_device["Name"] == device:
                boot_device["Enabled"] = not boot_device["Enabled"]
                state = "enabled" if boot_device["Enabled"] else "disabled"

        await self.patch_boot_seq(new_boot_seq)
        if state:
            self.logger.info(f"{device} has now been {state}")

        await self.create_bios_config_job(self.bios_uri)
        await self.reboot_server(graceful=False)
        return True

    async def get_virtual_media_config(self):
        vm_path = "/"
        if self.vendor == "Supermicro":
            vm_path += "VM1"
        else:
            vm_path += "VirtualMedia"

        _uri = "%s%s%s" % (self.host_uri, self.manager_resource, vm_path)
        _response = await self.get_request(_uri)
        try:
            raw = await _response.text("utf-8", "ignore")
            data = json.loads(raw.strip())
        except ValueError:
            raise BadfishException("Not able to access virtual media resource.")

        if self.vendor == "Supermicro":
            try:
                vm_path = {
                    "config": "",
                    "count": data["Members@odata.count"],
                    "members": [],
                }
                if data["Oem"].get("Supermicro"):
                    vm_path.update({"config": data["Oem"].get("Supermicro").get("VirtualMediaConfig").get("@odata.id")})
                else:
                    vm_path.update({"config": data["Oem"].get("VirtualMediaConfig").get("@odata.id")})
                if vm_path["count"] > 0:
                    for m in data["Members"]:
                        vm_path["members"].append(m.get("@odata.id"))
            except (ValueError, KeyError, TypeError):
                raise BadfishException("Not able to access virtual media config.")
        else:
            try:
                vm_path = []
                for m in data["Members"]:
                    vm_path.append(m.get("@odata.id"))
            except (ValueError, KeyError):
                raise BadfishException("Not able to access virtual media config.")
        return vm_path

    async def check_virtual_media(self):
        vm_config = await self.get_virtual_media_config()
        if self.vendor == "Supermicro":
            if vm_config.get("count") == 0:
                self.logger.info("No virtual media mounted.")
                return False
            else:
                vm_config = vm_config["members"]

        inserted = False
        for vm in vm_config:
            _uri = "%s%s" % (self.host_uri, vm)
            _response = await self.get_request(_uri)
            try:
                raw = await _response.text("utf-8", "ignore")
                _data = json.loads(raw.strip())
                self.logger.info(f"{_data.get('Id')}:")
                self.logger.info(f"    Name: {_data.get('Name')}")
                self.logger.info(f"    ImageName: {_data.get('ImageName')}")
                self.logger.info(f"    Inserted: {_data.get('Inserted')}")
                if str(_data.get("Inserted")).lower() == "true" and "CD" in str(_data.get("Id")):
                    inserted = True
            except ValueError:
                raise BadfishException("There was something wrong getting values for VirtualMedia")
        return inserted

    async def mount_virtual_media(self, path):
        vm_config = await self.get_virtual_media_config()
        _headers = {"Content-Type": "application/json"}
        if self.vendor == "Supermicro":
            parsed_path = urlparse(path)
            _payload = {
                "Host": f"{parsed_path.scheme}://{parsed_path.netloc}",
                "Path": parsed_path.path,
                "Username": "",
                "Password": "",
            }
            _uri = "%s%s" % (self.host_uri, vm_config["config"])
            _response = await self.patch_request(_uri, payload=_payload, headers=_headers)

            _uri = "%s%s/Actions/IsoConfig.Mount" % (self.host_uri, vm_config["config"])
            _response = await self.post_request(_uri, payload={}, headers=_headers)
            if _response.status in [200, 202]:
                self.logger.info("Image mounting operation was successful.")
            else:
                raise BadfishException("There was something wrong trying to mount virtual media.")
        else:
            vcd = [x for x in vm_config if "CD" in x][0]
            _uri = "%s%s/Actions/VirtualMedia.InsertMedia" % (self.host_uri, vcd)
            _payload = {"Image": path}
            _response = await self.post_request(_uri, payload=_payload, headers=_headers)
            status = _response.status
            if status == 204:
                self.logger.info("Image mounting operation was successful.")
            elif status == 405:
                self.logger.error("Virtual media mounting is not allowed on this server.")
                return False
            elif status == 500:
                self.logger.error("Couldn't mount virtual media, because there is virtual media mounted already.")
                return False
            else:
                raise BadfishException("There was something wrong trying to mount virtual media.")
        return True

    async def unmount_virtual_media(self):
        vm_config = await self.get_virtual_media_config()
        _headers = {"Content-Type": "application/json"}
        if self.vendor == "Supermicro":
            _uri = "%s%s/Actions/IsoConfig.UnMount" % (
                self.host_uri,
                vm_config["config"],
            )
            _response = await self.post_request(_uri, payload="{}", headers=_headers)
            if _response.status in [200, 202]:
                self.logger.info("Image unmount operation was successful.")
            else:
                raise BadfishException("There was something wrong trying to unmount virtual media.")
            _payload = {"Host": "", "Path": "", "Username": "", "Password": ""}
            _uri = "%s%s" % (self.host_uri, vm_config["config"])
            _response = await self.patch_request(_uri, payload=_payload, headers=_headers)
        else:
            vcd = [x for x in vm_config if "CD" in x][0]
            _uri = "%s%s/Actions/VirtualMedia.EjectMedia" % (self.host_uri, vcd)
            _response = await self.post_request(_uri, payload={}, headers=_headers)
            status = _response.status
            if status == 204:
                self.logger.info("Image unmount operation was successful.")
            elif status == 405:
                self.logger.error("Virtual media unmounting is not allowed on this server.")
                return False
            elif status == 500:
                self.logger.error("Couldn't unmount virtual media, because there isn't any virtual media mounted.")
                return False
            else:
                raise BadfishException("There was something wrong trying to unmount virtual media.")
        return True

    async def boot_to_virtual_media(self):
        og_log = self.logger
        self.logger = getLogger("Temp")
        inserted = await self.check_virtual_media()
        self.logger = og_log
        if not inserted:
            self.logger.error("No virtual CD is inserted.")
            return False

        _uri = "%s%s" % (self.host_uri, self.system_resource)
        _headers = {"Content-Type": "application/json"}
        if self.vendor == "Supermicro":
            _payload = {"Boot": {"BootSourceOverrideEnabled": "Once"}}

            _response = await self.get_request(_uri)
            try:
                raw = await _response.text("utf-8", "ignore")
                _data = json.loads(raw.strip())
                allowable_boot_targets = _data.get("Boot").get("BootSourceOverrideTarget@Redfish.AllowableValues")
            except ValueError:
                raise BadfishException("There was something wrong trying to boot to virtual media.")
            if "UsbCd" in allowable_boot_targets:
                _payload.get("Boot").update({"BootSourceOverrideTarget": "UsbCd"})
            else:
                _payload.get("Boot").update({"BootSourceOverrideTarget": "Cd"})

            _response = await self.patch_request(_uri, headers=_headers, payload=_payload)
            if _response.status == 200:
                self.logger.info("Command passed to set next onetime boot device to virtual media.")
            else:
                self.logger.error("Command failed to set next onetime boot device to virtual media.")
                return False
        else:
            vcd_check = await self.check_device("Optical.iDRACVirtual.1-1")
            if vcd_check:
                await self.boot_to("Optical.iDRACVirtual.1-1", True)
            else:
                self.logger.error(
                    "Command failed to set next onetime boot to virtual media. " "No virtual optical media boot device."
                )
                return False
        return True

    async def check_os_deployment_support(self):
        _uri = "%s/redfish/v1/Dell/Systems/System.Embedded.1/DellOSDeploymentService" % self.host_uri
        _response = await self.get_request(_uri)
        await _response.text("utf-8", "ignore")
        if _response.status != 200:
            self.logger.error(
                "iDRAC version installed doesn't support DellOSDeploymentService needed for this feature."
            )
            return False
        return True

    async def check_remote_image(self):
        if not await self.check_os_deployment_support():
            return False
        _uri = (
            "%s/redfish/v1/Dell/Systems/System.Embedded.1/DellOSDeploymentService/Actions/DellOSDeploymentService."
            "GetAttachStatus" % self.host_uri
        )
        _headers = {"Content-Type": "application/json"}
        _response = await self.post_request(_uri, payload={}, headers=_headers)
        try:
            raw = await _response.text("utf-8", "ignore")
            data = json.loads(raw.strip())
            if _response.status == 200:
                self.logger.info("Current ISO attach status: %s" % data.get("ISOAttachStatus"))
                if data.get("ISOAttachStatus") == "Attached":
                    return True
            else:
                self.logger.error("Command failed to get attach status of the remote mounted ISO.")
        except ValueError:
            raise BadfishException("There was something wrong trying to check remote image attach status.")
        return False

    async def boot_remote_image(self, nfs_path):
        if not await self.check_os_deployment_support():
            return False
        _uri = (
            "%s/redfish/v1/Dell/Systems/System.Embedded.1/DellOSDeploymentService/Actions/DellOSDeploymentService"
            ".BootToNetworkISO" % self.host_uri
        )
        _headers = {"Content-Type": "application/json"}
        try:
            split_path = str(nfs_path).split(":")
            last_slash_pos = split_path[1].rindex("/") + 1
            _payload = {
                "ShareType": "NFS",
                "IPAddress": split_path[0],
                "ShareName": split_path[1][:last_slash_pos],
                "ImageName": split_path[1][last_slash_pos:],
            }
            if len(_payload.get("ImageName")) == 0:
                raise ValueError
        except (ValueError, IndexError):
            self.logger.error("Wrong NFS path format.")
            return False
        _response = await self.post_request(_uri, payload=_payload, headers=_headers)
        if _response.status == 202:
            self.logger.info("Command for booting to remote ISO was successful, job was created.")
            try:
                task_path = _response.headers.get("Location")
                response = await self.get_request(f"{self.host_uri}{task_path}")
                raw = await response.text("utf-8", "ignore")
                data = json.loads(raw.strip())
                if data.get("TaskStatus") == "OK":
                    self.logger.info("OSDeployment task status is OK.")
                else:
                    self.logger.error("OSDeployment task failed and couldn't be completed.")
                    return False
            except (ValueError, AttributeError):
                raise BadfishException("There was something wrong trying to check remote image attach status.")
            return True
        else:
            self.logger.error("Command failed to boot to remote ISO. No job was created.")
        return False

    async def detach_remote_image(self):
        if not await self.check_os_deployment_support():
            return False
        _uri = (
            "%s/redfish/v1/Dell/Systems/System.Embedded.1/DellOSDeploymentService/Actions/DellOSDeploymentService"
            ".DetachISOImage" % self.host_uri
        )
        _headers = {"Content-Type": "application/json"}
        _response = await self.post_request(_uri, payload={}, headers=_headers)
        if _response.status == 200:
            self.logger.info("Command to detach remote ISO was successful.")
            return True
        else:
            self.logger.error("Command failed to detach remote mounted ISO.")
        return False

    async def get_network_adapters(self):
        _url = "%s%s/NetworkAdapters" % (self.host_uri, self.system_resource)
        _response = await self.get_request(_url)
        try:
            raw = await _response.text("utf-8", "ignore")
            na_data = json.loads(raw.strip())

            root_nics = []
            if na_data.get("Members"):
                for member in na_data["Members"]:
                    root_nics.append(member["@odata.id"])

            data = {}
            for nic in root_nics:
                net_ports_url = "%s%s/NetworkPorts" % (self.host_uri, nic)
                rn_response = await self.get_request(net_ports_url)
                rn_raw = await rn_response.text("utf-8", "ignore")
                rn_data = json.loads(rn_raw.strip())

                nic_ports = []
                if rn_data.get("Members"):
                    for member in rn_data["Members"]:
                        nic_ports.append(member["@odata.id"])

                net_df_url = "%s%s/NetworkDeviceFunctions" % (self.host_uri, nic)
                ndf_response = await self.get_request(net_df_url)
                ndf_raw = await ndf_response.text("utf-8", "ignore")
                ndf_data = json.loads(ndf_raw.strip())

                ndf_members = []
                if ndf_data.get("Members"):
                    for member in ndf_data["Members"]:
                        ndf_members.append(member["@odata.id"])

                for i, nic_port in enumerate(nic_ports):
                    np_url = "%s%s" % (self.host_uri, nic_port)
                    np_response = await self.get_request(np_url)
                    np_raw = await np_response.text("utf-8", "ignore")
                    np_data = json.loads(np_raw.strip())

                    interface = nic_port.split("/")[-1]

                    fields = [
                        "Id",
                        "LinkStatus",
                        "SupportedLinkCapabilities",
                    ]
                    values = {}
                    for field in fields:
                        value = np_data.get(field)
                        if value:
                            values[field] = value

                    ndf_url = "%s%s" % (self.host_uri, ndf_members[i])
                    ndf_response = await self.get_request(ndf_url)
                    ndf_raw = await ndf_response.text("utf-8", "ignore")
                    ndf_data = json.loads(ndf_raw.strip())
                    oem = ndf_data.get("Oem")
                    ethernet = ndf_data.get("Ethernet")
                    if ethernet:
                        mac_address = ethernet.get("MACAddress")
                        if mac_address:
                            values["MACAddress"] = mac_address
                    if oem:
                        dell = oem.get("Dell")
                        if dell:
                            dell_nic = dell.get("DellNIC")
                            vendor = dell_nic.get("VendorName")
                            if dell_nic.get("VendorName"):
                                values["Vendor"] = vendor

                    data.update({interface: values})

        except (ValueError, AttributeError):
            raise BadfishException("There was something wrong getting network interfaces")

        return data

    async def get_ethernet_interfaces(self):
        _url = "%s%s/EthernetInterfaces" % (self.host_uri, self.system_resource)
        _response = await self.get_request(_url)

        if _response.status == 404:
            raise BadfishException("Server does not support this functionality")

        try:
            raw = await _response.text("utf-8", "ignore")
            ei_data = json.loads(raw.strip())

            interfaces = []
            if ei_data.get("Members"):
                for member in ei_data["Members"]:
                    interfaces.append(member["@odata.id"])

            data = {}
            for interface in interfaces:
                interface_url = "%s%s" % (self.host_uri, interface)
                int_response = await self.get_request(interface_url)
                int_raw = await int_response.text("utf-8", "ignore")
                int_data = json.loads(int_raw.strip())

                int_name = int_data.get("Id")
                fields = [
                    "Name",
                    "MACAddress",
                    "Status",
                    "LinkStatus",
                    "SpeedMbps",
                ]

                values = {}
                for field in fields:
                    value = int_data.get(field)
                    if value:
                        values[field] = value

                data.update({int_name: values})

        except (ValueError, AttributeError):
            raise BadfishException("There was something wrong getting network interfaces")

        return data

    async def list_interfaces(self):
        na_supported = await self.check_supported_network_interfaces("NetworkAdapters")
        if na_supported:
            self.logger.debug("Getting Network Adapters")
            data = await self.get_network_adapters()
        else:
            ei_supported = await self.check_supported_network_interfaces("EthernetInterfaces")
            if ei_supported:
                self.logger.debug("Getting Ethernet interfaces")
                data = await self.get_ethernet_interfaces()
            else:
                self.logger.error("Server does not support this functionality")
                return False

        if self._use_tables:
            cols = {}
            for interface, properties in data.items():
                for key, value in properties.items():
                    if key == "SupportedLinkCapabilities":
                        cols["LinkSpeedMbps"] = True
                    elif key == "Status":
                        cols["Health"] = True
                    else:
                        cols[key] = True

            table = Table(show_header=True, header_style="bold")
            table.add_column("Interface")
            for col in cols:
                table.add_column(col)

            for interface, properties in data.items():
                row_vals = {"Interface": interface}
                for key, value in properties.items():
                    if key == "SupportedLinkCapabilities":
                        caps = value[0] if isinstance(value, list) and value else {}
                        row_vals["LinkSpeedMbps"] = str(caps.get("LinkSpeedMbps", ""))
                    elif key == "Status":
                        row_vals["Health"] = str(value.get("Health", ""))
                    else:
                        row_vals[key] = str(value)
                table.add_row(*[row_vals.get(c, "") for c in ["Interface"] + list(cols)])

            self._log_table(table)
        else:
            for interface, properties in data.items():
                self.logger.info(f"{interface}:")
                for key, value in properties.items():
                    if key == "SupportedLinkCapabilities":
                        speed = value[0].get("LinkSpeedMbps") if value else None
                        if speed:
                            self.logger.info(f"    LinkSpeedMbps: {speed}")
                    elif key == "Status":
                        health = value.get("Health")
                        if health:
                            self.logger.info(f"    Health: {health}")
                    else:
                        self.logger.info(f"    {key}: {value}")
        return True

    async def get_processor_summary(self):
        _url = "%s%s" % (self.host_uri, self.system_resource)
        _response = await self.get_request(_url)

        try:
            raw = await _response.text("utf-8", "ignore")
            data = json.loads(raw.strip())

            proc_data = data.get("ProcessorSummary")

            if not proc_data:
                raise BadfishException("Server does not support this functionality")

            fields = [
                "Count",
                "LogicalProcessorCount",
                "Model",
            ]

            values = {}
            for field in fields:
                value = proc_data.get(field)
                if value:
                    values[field] = value

        except (ValueError, AttributeError):
            raise BadfishException("There was something wrong getting processor summary")

        return values

    async def get_processor_details(self):
        _url = "%s%s/Processors" % (self.host_uri, self.system_resource)
        _response = await self.get_request(_url)

        if _response.status == 404:
            raise BadfishException("Server does not support this functionality")

        try:
            raw = await _response.text("utf-8", "ignore")
            data = json.loads(raw.strip())

            processors = []
            if data.get("Members"):
                for member in data["Members"]:
                    if "CPU" in member["@odata.id"]:
                        processors.append(member["@odata.id"])

            proc_details = {}
            for processor in processors:
                processor_url = "%s%s" % (self.host_uri, processor)
                proc_response = await self.get_request(processor_url)
                proc_raw = await proc_response.text("utf-8", "ignore")
                proc_data = json.loads(proc_raw.strip())

                proc_name = proc_data.get("Id")
                fields = [
                    "Name",
                    "InstructionSet",
                    "Manufacturer",
                    "MemoryDeviceType",
                    "MaxSpeedMHz",
                    "Model",
                    "TotalCores",
                    "TotalThreads",
                ]

                values = {}
                for field in fields:
                    value = proc_data.get(field)
                    if value:
                        values[field] = value

                proc_details.update({proc_name: values})

        except (ValueError, AttributeError):
            raise BadfishException("There was something wrong getting processor details")

        return proc_details

    async def get_gpu_data(self):
        _url = "%s%s/Processors" % (self.host_uri, self.system_resource)
        _response = await self.get_request(_url)

        if _response.status == 404:
            raise BadfishException("GPU endpoint not available on host.")

        try:
            raw = await _response.text("utf-8", "ignore")
            data = json.loads(raw.strip())

        except (ValueError, AttributeError):
            raise BadfishException("There was something wrong getting GPU data")
        return data

    async def get_gpu_responses(self, data):
        gpu_responses = []
        gpu_endpoints = []
        try:
            if data.get("Members"):
                for member in data["Members"]:
                    if "Video" in member["@odata.id"] or "ProcAccelerator" in member["@odata.id"]:
                        gpu_endpoints.append(member["@odata.id"])

            for gpu in gpu_endpoints:
                gpu_url = "%s%s" % (self.host_uri, gpu)
                gpu_response = await self.get_request(gpu_url)
                gpu_raw = await gpu_response.text("utf-8", "ignore")
                gpu_data = json.loads(gpu_raw.strip())
                gpu_responses.append(gpu_data)

        except (ValueError, AttributeError):  # pragma: no cover
            raise BadfishException("There was something wrong getting host GPU details")

        return gpu_responses

    async def get_gpu_summary(self, gpu_responses):
        gpu_summary = {}
        try:
            for gpu_data in gpu_responses:

                gpu_model = gpu_data["Model"]

                if not gpu_summary.get(gpu_model):
                    gpu_summary[gpu_model] = 1
                else:
                    gpu_summary[gpu_model] = gpu_summary[gpu_model] + 1

        except (ValueError, AttributeError, KeyError):
            raise BadfishException("There was something wrong getting GPU summary values.")
        return gpu_summary

    async def get_gpu_details(self, gpu_responses):
        try:
            gpu_details = {}
            for gpu_data in gpu_responses:

                gpu_name = gpu_data.get("Id")
                fields = [
                    "Model",
                    "Manufacturer",
                    "ProcessorType",
                ]

                values = {}
                for field in fields:
                    value = gpu_data.get(field)
                    if value:
                        values[field] = value

                gpu_details.update({gpu_name: values})

        except (ValueError, AttributeError):  # pragma: no cover
            raise BadfishException("There was something wrong getting host GPU details values.")

        return gpu_details

    async def get_memory_summary(self):
        _url = "%s%s" % (self.host_uri, self.system_resource)
        _response = await self.get_request(_url)

        try:
            raw = await _response.text("utf-8", "ignore")
            data = json.loads(raw.strip())

            proc_data = data.get("MemorySummary")

            if not proc_data:
                raise BadfishException("Server does not support this functionality")

            fields = [
                "MemoryMirroring",
                "TotalSystemMemoryGiB",
            ]

            values = {}
            for field in fields:
                value = proc_data.get(field)
                if value:
                    values[field] = value

        except (ValueError, AttributeError):
            raise BadfishException("There was something wrong getting memory summary")

        return values

    async def get_memory_details(self):
        _url = "%s%s/Memory" % (self.host_uri, self.system_resource)
        _response = await self.get_request(_url)

        if _response.status == 404:
            raise BadfishException("Server does not support this functionality")

        try:
            raw = await _response.text("utf-8", "ignore")
            data = json.loads(raw.strip())

            memories = []
            if data.get("Members"):
                for member in data["Members"]:
                    memories.append(member["@odata.id"])

            mem_details = {}
            for memory in memories:
                memory_url = "%s%s" % (self.host_uri, memory)
                mem_response = await self.get_request(memory_url)
                mem_raw = await mem_response.text("utf-8", "ignore")
                mem_data = json.loads(mem_raw.strip())

                mem_name = mem_data.get("Name")
                fields = [
                    "CapacityMiB",
                    "Description",
                    "Manufacturer",
                    "MemoryDeviceType",
                    "OperatingSpeedMhz",
                ]

                values = {}
                for field in fields:
                    value = mem_data.get(field)
                    if value:
                        values[field] = value

                mem_details.update({mem_name: values})

        except (ValueError, AttributeError):
            raise BadfishException("There was something wrong getting memory details")

        return mem_details

    async def get_serial_summary(self):
        _uri = "%s%s" % (self.host_uri, self.redfish_uri)
        _response = await self.get_request(_uri)

        if _response.status in [400, 404]:
            raise BadfishException("Server does not support this functionality")

        try:
            raw = await _response.text("utf-8", "ignore")
            data = json.loads(raw.strip())
            service_data = data.get("Oem").get("Dell")

            if not service_data:
                serial_uri = "%s%s/Systems/1" % (self.host_uri, self.redfish_uri)
                serial_response = await self.get_request(serial_uri)

                if _response.status in [400, 404]:
                    raise BadfishException("Server does not support this functionality")

                serial_raw = await serial_response.text("utf-8", "ignore")
                serial_data = json.loads(serial_raw.strip())
                serial_number_data = serial_data.get("SerialNumber")

                if not serial_number_data:
                    raise BadfishException("Server does not support this functionality")
                else:
                    return serial_number_data

        except (ValueError, AttributeError):
            raise BadfishException("There was something wrong getting serial summary")

        return service_data

    async def list_processors(self):
        data = await self.get_processor_summary()

        self.logger.info("Processor Summary:")
        if self._use_tables:
            summary = Table(show_header=True, header_style="bold")
            summary.add_column("Property")
            summary.add_column("Value")
            for _key, _value in data.items():
                summary.add_row(_key, str(_value))
            self._log_table(summary)
        else:
            for _key, _value in data.items():
                self.logger.info(f"    {_key}: {_value}")

        processor_data = await self.get_processor_details()

        if self._use_tables:
            detail = Table(show_header=True, header_style="bold")
            detail.add_column("Processor")
            all_keys = dict.fromkeys(k for props in processor_data.values() for k in props)
            for col in all_keys:
                detail.add_column(col)
            for _processor, _properties in processor_data.items():
                detail.add_row(_processor, *[str(_properties.get(k, "")) for k in all_keys])
            self._log_table(detail)
        else:
            for _processor, _properties in processor_data.items():
                self.logger.info(f"{_processor}:")
                for _key, _value in _properties.items():
                    self.logger.info(f"    {_key}: {_value}")

        return True

    async def list_gpu(self):
        data = await self.get_gpu_data()
        gpu_responses = await self.get_gpu_responses(data)

        summary = await self.get_gpu_summary(gpu_responses)

        self.logger.info("GPU Summary:")
        if self._use_tables:
            summary_table = Table(show_header=True, header_style="bold")
            summary_table.add_column("Model")
            summary_table.add_column("Count", justify="right")
            for _key, _value in summary.items():
                summary_table.add_row(_key, str(_value))
            self._log_table(summary_table)
        else:
            for _key, _value in summary.items():
                self.logger.info(f"  Model: {_key} (Count: {_value})")

        gpu_data = await self.get_gpu_details(gpu_responses)

        self.logger.info("Current GPU's on host:")
        if self._use_tables:
            detail = Table(show_header=True, header_style="bold")
            detail.add_column("GPU")
            all_keys = dict.fromkeys(k for props in gpu_data.values() for k in props)
            for col in all_keys:
                detail.add_column(col)
            for _gpu, _properties in gpu_data.items():
                detail.add_row(_gpu, *[str(_properties.get(k, "")) for k in all_keys])
            self._log_table(detail)
        else:
            for _gpu, _properties in gpu_data.items():
                self.logger.info(f"  {_gpu}:")
                for _key, _value in _properties.items():
                    self.logger.info(f"    {_key}: {_value}")

        return True

    async def list_memory(self):
        data = await self.get_memory_summary()

        self.logger.info("Memory Summary:")
        if self._use_tables:
            summary = Table(show_header=True, header_style="bold")
            summary.add_column("Property")
            summary.add_column("Value")
            for _key, _value in data.items():
                summary.add_row(_key, str(_value))
            self._log_table(summary)
        else:
            for _key, _value in data.items():
                self.logger.info(f"    {_key}: {_value}")

        memory_data = await self.get_memory_details()

        if self._use_tables:
            detail = Table(show_header=True, header_style="bold")
            detail.add_column("DIMM")
            all_keys = dict.fromkeys(k for props in memory_data.values() for k in props)
            for col in all_keys:
                detail.add_column(col)
            for _memory, _properties in memory_data.items():
                detail.add_row(_memory, *[str(_properties.get(k, "")) for k in all_keys])
            self._log_table(detail)
        else:
            for _memory, _properties in memory_data.items():
                self.logger.info(f"{_memory}:")
                for _key, _value in _properties.items():
                    self.logger.info(f"    {_key}: {_value}")

        return True

    async def list_serial(self):
        data = await self.get_serial_summary()

        if "ServiceTag" in data:
            self.logger.info("ServiceTag:")
            self.logger.info(f"    {self.host}: {data.get('ServiceTag')}")
        else:
            self.logger.info("Serial Number:")
            self.logger.info(f"    {self.host}: {data}")

        return True

    async def change_bios_password(self, old_password, new_password):
        _url = "%s%s/Bios/Actions/Bios.ChangePassword" % (
            self.host_uri,
            self.system_resource,
        )
        _payload = {
            "PasswordName": "SetupPassword",
            "OldPassword": old_password,
            "NewPassword": new_password,
        }
        _headers = {"content-type": "application/json"}
        _response = await self.post_request(_url, _payload, _headers)

        status_code = _response.status

        if status_code in [200, 204]:
            self.logger.info("Command passed to set BIOS password.")
        elif status_code == 404:
            self.logger.error("BIOS password change not supported on this system.")
            return False
        else:
            self.logger.warning("Command failed to set BIOS password")

            await self.error_handler(_response)

        job_id = await self.create_bios_config_job(self.bios_uri)
        self.logger.warning("Host will now be rebooted for changes to take place.")
        await asyncio.sleep(5)
        await self.reboot_server()
        await asyncio.sleep(5)
        await self.check_job_status(job_id)

    async def set_bios_password(self, old_password, new_password):
        if new_password == "":
            self.logger.error("Missing argument: `--new-password`")
            return False

        await self.change_bios_password(old_password, new_password)

    async def remove_bios_password(self, old_password):
        if old_password == "":
            self.logger.error("Missing argument: `--old-password`")
            return False
        await self.change_bios_password(old_password, "")

    async def get_screenshot(self):
        _uri = self.host_uri + self.redfish_uri + "/Dell" + self.manager_resource[11:]
        _url = "%s/DellLCService/Actions/DellLCService.ExportServerScreenShot" % _uri
        _headers = {"content-type": "application/json"}
        _payload = {"FileType": "ServerScreenShot"}
        _response = await self.post_request(_url, _payload, _headers)

        status_code = _response.status
        if status_code in [200, 202]:
            self.logger.debug("POST command passed to get server screenshot.")
        elif status_code == 404:
            raise BadfishException("The system does not support screenshots.")
        else:
            if status_code == 400:
                self.logger.error("POST command failed to get the server screenshot.")
                await self.error_handler(_response)
            else:
                return None

        try:
            raw = await _response.text("utf-8", "ignore")
            data = json.loads(raw.strip())
        except ValueError:
            raise BadfishException("Error reading response from host.")

        timestamp = time.strftime("%Y%m%d-%H%M%S")
        fqdn_short = self.host.split(".")[0]
        filename = f"{fqdn_short}_screenshot_{timestamp}.png"
        with open(filename, "wb") as fh:
            fh.write(base64.decodebytes(bytes(data["ServerScreenShotFile"], "utf-8")))
        return filename

    async def take_screenshot(self):
        filename = await self.get_screenshot()
        self.logger.info(f"Image saved: {filename}")
        return True

    async def delete_session(self):
        try:
            try:
                if not self.session_id:
                    self.logger.debug("No session ID found, skipping session deletion")
                    return
                headers = {"content-type": "application/json"}
                _uri = "%s%s" % (self.host_uri, self.session_id)
                try:
                    _response = await self.delete_request(_uri, headers=headers)
                    if _response.status in [200, 201]:
                        self.logger.debug(f"Session successfully deleted for {self.host}")
                    elif _response.status == 404:
                        self.logger.debug(f"Session not found (404) for {self.host}, may have been already deleted")
                    else:
                        self.logger.warning(
                            f"Unexpected status {_response.status} when deleting session for {self.host}."
                        )
                except Exception as ex:
                    self.logger.warning(f"Failed to delete session for {self.host}: {ex}")
            finally:
                self.session_id = None
                self.token = None
        except Exception:
            self.session_id = None
            self.token = None

    async def get_scp_targets(self, op):
        uri = "%s%s" % (self.host_uri, self.manager_resource)
        response = await self.get_request(uri)
        try:
            raw = await response.text("utf-8", "ignore")
            data = json.loads(raw.strip())
            _ = response.status
            filtered_data = [
                val for key, val in data.get("Actions").get("Oem").items() if key.endswith(f"{op}SystemConfiguration")
            ]
            if filtered_data:
                if filtered_data[0].get("ShareParameters").get("Target@Redfish.AllowableValues"):
                    self.logger.info(f"The allowable SCP {op} targets are:")
                    for i in filtered_data[0].get("ShareParameters").get("Target@Redfish.AllowableValues"):
                        self.logger.info(i)
                    return True
                else:
                    self.logger.error(
                        f"Couldn't find a list of possible targets, but {op} with SCP " f"should be allowed."
                    )
            else:
                self.logger.error(f"iDRAC on this system doesn't seem to support SCP {op}.")
        except (ValueError, AttributeError, TypeError):
            raise BadfishException(f"There was something wrong trying to get targets for SCP {op}.")
        return False

    async def export_scp(self, file_path, targets="ALL", include_read_only=False):
        uri = "%s%s/Actions/Oem/EID_674_Manager.ExportSystemConfiguration" % (self.host_uri, self.manager_resource)
        headers = {"Content-Type": "application/json"}
        payload = {
            "ExportFormat": "JSON",
            "ExportUse": "Default",
            "IncludeInExport": ("Default" if not include_read_only else "IncludeReadOnly"),
            "ShareParameters": {"Target": targets},
        }

        response = await self.post_request(uri, payload, headers)
        if response.status != 202:
            self.logger.error("Command failed to export system configuration.")
            return False

        job_id = self._extract_job_id_from_response(response, warn_on_missing=False)
        if not job_id:
            return False

        self.logger.info(f"Job for exporting server configuration successfully created. Job ID: {job_id}")

        # WORKAROUND: Dell iDRAC API returns stale/cached status even after job completes
        # Both Tasks and Jobs endpoints show "Running" indefinitely even though racadm shows completion
        # Export jobs typically complete in 15-30 seconds, so wait 45 seconds then fetch result
        self.logger.info("Waiting for export job to complete (typically takes 15-30 seconds)...")
        await asyncio.sleep(45)

        # Try to fetch the result directly from Jobs endpoint
        uri = "%s%s/Jobs/%s" % (self.host_uri, self.manager_resource, job_id)
        response = await self.get_request(uri)
        raw = await response.text("utf-8", "ignore")
        data = json.loads(raw.strip())

        # Check if job failed
        if data.get("JobState") in ["Failed", "CompletedWithErrors"]:
            self.logger.error(f"Export job failed with state: {data.get('JobState')}")
            self.logger.error(f"Message: {data.get('Message', 'No error message')}")
            return False

        # Check if SystemConfiguration is in the response
        if "SystemConfiguration" not in data:
            # Try the Tasks endpoint as fallback
            self.logger.debug("SystemConfiguration not in Jobs response, trying Tasks endpoint")
            uri = "%s/redfish/v1/TaskService/Tasks/%s" % (self.host_uri, job_id)
            response = await self.get_request(uri)
            raw = await response.text("utf-8", "ignore")
            data = json.loads(raw.strip())

        # Save the exported configuration
        if "SystemConfiguration" in data:
            now = get_now()
            filename = file_path + now.strftime(f"%Y-%m-%d_%H%M%S_targets_{targets.replace(',', '-')}_export.json")
            with open(filename, "w") as f:
                f.write(json.dumps(data, indent=4))
            self.logger.info("SCP export completed successfully.")
            self.logger.info(f"Exported system configuration to file: {filename}")
            return True
        else:
            self.logger.error("Export job completed but SystemConfiguration not found in response.")
            return False

    async def import_scp(self, file_path, targets="ALL"):
        try:
            open_file = open(file_path, "r")
        except IOError:
            self.logger.error("File doesn't exist or couldn't be opened.")
            return False
        modify_file = open_file.read()
        power_state = await self.get_power_state()
        uri = "%s%s/Actions/Oem/EID_674_Manager.ImportSystemConfiguration" % (self.host_uri, self.manager_resource)
        headers = {"Content-Type": "application/json"}
        payload = {
            "ImportBuffer": modify_file,
            "ShutdownType": "Graceful",
            "HostPowerState": power_state,
            "ShareParameters": {"Target": targets},
        }

        response = await self.post_request(uri, payload, headers)
        if response.status != 202:
            self.logger.error("Command failed to import system configuration.")
            return False

        job_id = self._extract_job_id_from_response(response, warn_on_missing=False)
        if not job_id:
            return False

        self.logger.info(f"Job for importing server configuration, successfully created. Job ID: {job_id}")
        start_time = get_now()
        percentage = 0
        fail_states = ["Failed", "CompletedWithErrors"]
        while True:
            ct = get_now() - start_time
            uri = "%s/redfish/v1/TaskService/Tasks/%s" % (self.host_uri, job_id)
            response = await self.get_request(uri)
            raw = await response.text("utf-8", "ignore")
            data = json.loads(raw.strip())
            if response.status in [200, 202]:
                await asyncio.sleep(1)
            else:
                self.logger.error("Unable to get detail for the job, command failed.")
                return False
            if str(ct)[0:7] >= "0:15:00":
                self.logger.error("Job has been timed out, took longer than 5 minutes, command failed.")
                return False
            if "Oem" not in data:
                self.logger.info("Unable to locate OEM data in JSON response, trying again.")
                await asyncio.sleep(3)
                continue
            try:
                if percentage < int(data["Oem"]["Dell"]["PercentComplete"]):
                    percentage = int(data["Oem"]["Dell"]["PercentComplete"])
                    self.logger.info(
                        "%s, percent complete: %s"
                        % (data["Oem"]["Dell"]["Message"], data["Oem"]["Dell"]["PercentComplete"])
                    )
                await asyncio.sleep(1)
                if percentage != 100:
                    continue
            except (ValueError, AttributeError, KeyError):
                self.logger.info("Unable to get job status message, trying again.")
                await asyncio.sleep(3)
                continue
            try:
                if data["Oem"]["Dell"]["JobState"] in fail_states:
                    self.logger.error(f"Command failed, job status = {data['Oem']['Dell']['JobState']}")
                    return False
                elif data["Oem"]["Dell"]["JobState"] == "Completed":
                    self.logger.info("Command passed, job successfully marked as completed. Going to reboot.")
                    break
            except (ValueError, AttributeError, KeyError):
                self.logger.info("Unable to get job status, trying again")
                await asyncio.sleep(3)
                continue
        return True

    async def get_nic_fqdds(self):
        uri = "%s%s/NetworkAdapters" % (self.host_uri, self.system_resource)
        resp = await self.get_request(uri)
        if resp.status == 404 or self.vendor == "Supermicro":
            self.logger.error("Operation not supported by vendor.")
            return False

        try:
            raw = await resp.text("utf-8", "ignore")
            data = json.loads(raw.strip())
            nic_list = [[nic[1].split("/")[-1] for nic in member.items()][0] for member in data.get("Members")]
            self.logger.debug("Detected NIC FQDDs for existing network adapters.")
            for nic in nic_list:
                uri = "%s%s/NetworkAdapters/%s/NetworkDeviceFunctions" % (self.host_uri, self.system_resource, nic)
                resp = await self.get_request(uri)
                raw = await resp.text("utf-8", "ignore")
                data = json.loads(raw.strip())
                nic_fqqds = [[fqdd[1].split("/")[-1] for fqdd in member.items()][0] for member in data.get("Members")]
                self.logger.info(f"{nic}:")
                for i, fqdd in enumerate(nic_fqqds, start=1):
                    self.logger.info(f"    {i}: {fqdd}")
        except (AttributeError, IndexError, KeyError, TypeError, ValueError):
            self.logger.error("Was unable to get NIC FQDDs, invalid server response.")
            return False
        return True

    async def get_nic_attribute(self, fqdd, log=True):
        uri = "%s/Chassis/%s/NetworkAdapters/%s/NetworkDeviceFunctions/%s/Oem/Dell/DellNetworkAttributes/%s" % (
            self.root_uri,
            self.system_resource.split("/")[-1],
            fqdd.split("-")[0],
            fqdd,
            fqdd,
        )
        resp = await self.get_request(uri)
        if resp.status == 404 or self.vendor == "Supermicro":
            self.logger.error("Operation not supported by vendor.")
            return False

        try:
            raw = await resp.text("utf-8", "ignore")
            data = json.loads(raw.strip())
            attributes_list = [(key, value) for key, value in data.get("Attributes").items()]
            if not log:
                return attributes_list
            self.logger.debug(f"All NIC attributes of {fqdd}.")
            self.logger.info(f"{fqdd}")
            for key, value in attributes_list:
                self.logger.info(f"    {key}: {value}")
        except (AttributeError, KeyError, TypeError, ValueError):
            self.logger.error("Was unable to get NIC attribute(s) info, invalid server response.")
            return False
        return True

    async def get_idrac_fw_version(self):
        idrac_fw_version = 0
        try:
            uri = "%s%s/" % (self.host_uri, self.manager_resource)
            resp = await self.get_request(uri)
            if resp.status == 404 or self.vendor == "Supermicro":
                self.logger.error("Operation not supported by vendor.")
                return 0
            raw = await resp.text("utf-8", "ignore")
            data = json.loads(raw.strip())
            idrac_fw_version = int(data["FirmwareVersion"].replace(".", ""))
        except (AttributeError, ValueError, StopIteration):
            self.logger.error("Was unable to get iDRAC Firmware Version.")
            return 0
        return idrac_fw_version

    async def get_nic_attribute_registry(self, fqdd=None):
        registry = []
        idrac_fw_version = await self.get_idrac_fw_version()
        if not idrac_fw_version or idrac_fw_version < 5100000:
            self.logger.error("Unsupported iDRAC version.")
            return []
        try:
            uri = "%s/Registries/NetworkAttributesRegistry_%s/NetworkAttributesRegistry_%s.json" % (
                self.root_uri,
                fqdd,
                fqdd,
            )
            resp = await self.get_request(uri)
            if resp.status == 404:
                self.logger.error("Was unable to get network attribute registry.")
                return []
            raw = await resp.text("utf-8", "ignore")
            data = json.loads(raw.strip())
            registry = [attr for attr in data.get("RegistryEntries").get("Attributes")]
        except (AttributeError, KeyError, TypeError, ValueError):
            self.logger.error("Was unable to get network attribute registry.")
            return []
        return registry

    async def get_nic_attribute_info(self, fqdd, attribute, log=True):
        if self.vendor == "Supermicro":
            self.logger.error("Operation not supported by vendor.")
            return False
        registry = await self.get_nic_attribute_registry(fqdd)
        if not registry:
            self.logger.error("Was unable to get network attribute info.")
            return False
        try:
            registry = [attr_dict for attr_dict in registry if attr_dict.get("AttributeName") == attribute][0]
            current_value = await self.get_nic_attribute(fqdd, False)
            current_value = [tup[1] for tup in current_value if tup[0] == attribute][0]
            registry.update({"CurrentValue": current_value})
            if not log:
                return registry
            for key, value in registry.items():
                self.logger.info(f"{key}: {value}")
        except (AttributeError, IndexError, KeyError, TypeError):
            self.logger.error("Was unable to get network attribute info.")
            return False
        return True

    async def set_nic_attribute(self, fqdd, attribute, value):
        if self.vendor == "Supermicro":
            self.logger.error("Operation not supported by vendor.")
            return False

        attr_info = await self.get_nic_attribute_info(fqdd, attribute, False)
        if not attr_info:
            self.logger.error("Was unable to set a network attribute. Attribute most likely doesn't exist.")
            return False

        # Check if VirtualizationMode is enabled for SR-IOV attributes
        sriov_attributes = ["NumberVFAdvertised", "VFDistribution", "VFAllocMult"]
        if attribute in sriov_attributes:
            all_attrs = await self.get_nic_attribute(fqdd, log=False)
            if all_attrs:
                attrs_dict = dict(all_attrs)
                virt_mode = attrs_dict.get("VirtualizationMode", "")
                if virt_mode == "NONE":
                    self.logger.error(f"Cannot set {attribute} when VirtualizationMode is NONE (disabled).")
                    self.logger.error("First enable SR-IOV virtualization mode with:")
                    self.logger.error(f"  --set-nic-attribute {fqdd} --attribute VirtualizationMode --value SRIOV")
                    return False

        # Check for known hardware VF limits on NumberVFAdvertised attribute
        if attribute == "NumberVFAdvertised":
            try:
                requested_vfs = int(value)
                if requested_vfs > 64:
                    # Get additional NIC attributes to determine hardware limits
                    all_attrs = await self.get_nic_attribute(fqdd, log=False)
                    if all_attrs:
                        attrs_dict = dict(all_attrs)
                        device_name = attrs_dict.get("DeviceName", "")

                        # Intel XXV710 hardware limitation observed across firmware versions and modes
                        if "XXV710" in device_name:
                            self.logger.warning(
                                f"Attempting to set NumberVFAdvertised to {requested_vfs} on Intel XXV710."
                            )
                            self.logger.warning(
                                "Testing has shown that Intel XXV710 NICs are limited to 64 VFs regardless of "
                                "virtualization mode (SRIOV/NPARSRIOV) or firmware version."
                            )
                            self.logger.warning(
                                "This operation will likely fail. The hardware limit appears to be 64 VFs maximum."
                            )
                            # Allow attempt - let firmware reject if truly unsupported
            except (ValueError, AttributeError, KeyError):  # pragma: no cover
                # Defensive: exception during attribute parsing is rare - bad firmware data
                pass

        try:
            type = attr_info.get("Type")
            current_value = attr_info.get("CurrentValue")
            if value == current_value:
                self.logger.warning("This attribute already is set to this value. Skipping.")
                return True
            if type == "Enumeration":
                allowed_values = [value_spec.get("ValueName") for value_spec in attr_info.get("Value")]
                if value not in allowed_values:
                    self.logger.error("Value not allowed for this attribute.")
                    self.logger.error("Was unable to set a network attribute.")
                    return False
            if type == "String":
                max, min = int(attr_info.get("MaxLength")), int(attr_info.get("MinLength"))
                if len(value) > max or len(value) < min:
                    self.logger.error("Value not allowed for this attribute. (Incorrect string length)")
                    self.logger.error("Was unable to set a network attribute.")
                    return False
            if type == "Integer":
                max, min = int(attr_info.get("UpperBound")), int(attr_info.get("LowerBound"))
                value = int(value)
                if value > max or value < min:
                    self.logger.error("Value not allowed for this attribute. (Incorrect number bounds)")
                    self.logger.error("Was unable to set a network attribute.")
                    return False
        except (AttributeError, IndexError, KeyError, TypeError):
            self.logger.error("Was unable to set a network attribute.")
            return False

        try:
            uri = (
                "%s/Chassis/System.Embedded.1/NetworkAdapters/%s/NetworkDeviceFunctions/%s/Oem/Dell/DellNetworkAttributes/%s/Settings"
                % (
                    self.root_uri,
                    fqdd.split("-")[0],
                    fqdd,
                    fqdd,
                )
            )
            self.logger.debug(uri)
        except (IndexError, ValueError):
            self.logger.error("Invalid FQDD supplied.")
            return False

        headers = {"content-type": "application/json"}
        payload = {
            "@Redfish.SettingsApplyTime": {"ApplyTime": "OnReset"},
            "Attributes": {attribute: value},
        }
        first_reset = False
        job_id = None

        try:
            for i in range(self.retries):
                response = await self.patch_request(uri, payload, headers)
                status_code = response.status
                if status_code in [200, 202]:
                    self.logger.info("Patch command to set network attribute values and create next reboot job PASSED.")

                    # Extract job ID from response headers (DMTF Redfish DSP0266 §13.6)
                    # HTTP 202 indicates async operation with job creation
                    job_id = self._extract_job_id_from_response(
                        response, warn_on_missing=True, context="Changes may not persist after reboot."
                    )
                    if job_id:
                        self.logger.info(f"Network attribute configuration job created: {job_id}")

                    break
                else:
                    self.logger.error(
                        "Patch command to set network attribute values and create next reboot job FAILED, error code is: %s."
                        % status_code
                    )
                    if status_code == 503 and i - 1 != self.retries:
                        self.logger.info("Retrying to send the patch command.")
                        continue
                    elif status_code == 400:
                        self.logger.info("Retrying to send the patch command.")
                        await self.clear_job_queue()
                        if not first_reset:
                            await self.reset_idrac()
                            await asyncio.sleep(10)
                            first_reset = True
                        continue
                    self.logger.error(
                        "Patch command to set network attribute values and create next reboot job FAILED, error code is: %s."
                        % status_code
                    )
                    self.logger.error("Was unable to set a network attribute.")
                    return False
        except (AttributeError, ValueError):
            self.logger.error("Was unable to set a network attribute.")
            return False

        # Verify job is scheduled before reboot (if job was created)
        if job_id:
            job_scheduled = await self._verify_job_scheduled(job_id, context="configuration")
            if not job_scheduled:
                return False

        # Reboot server to apply pending configuration
        await self.reboot_server()

        # Monitor job completion and verify attribute change (if job was created)
        if job_id:
            return await self._monitor_and_verify_attribute_job(
                job_id, fqdd, attribute, value, type, attr_info.get("CurrentValue")
            )
        else:
            # No job ID - can't monitor, but still return True since PATCH succeeded
            self.logger.warning(
                "Configuration change submitted but job monitoring was not possible. "
                "Please manually verify attribute value persisted after reboot."
            )
            return True


async def execute_badfish(_host, _args, logger, format_handler=None, console=None, progress_disabled=False):
    _username = _args.get("u") or os.environ.get("BADFISH_USERNAME")
    _password = _args.get("p") or os.environ.get("BADFISH_PASSWORD")

    if _args.get("p"):
        logger.warning(
            "Passing secrets via command line arguments can be unsafe. "
            "Consider using environment variables (BADFISH_USERNAME, BADFISH_PASSWORD)."
        )

    if not _username or not _password:
        logger.error("Missing credentials. Please provide credentials via CLI arguments or environment variables.")
        return _host, False

    host_type = _args["t"]
    interfaces_path = _args["i"]
    force = _args["force"]
    pxe = _args["pxe"]
    device = _args["boot_to"]
    boot_to_type = _args["boot_to_type"]
    boot_to_mac = _args["boot_to_mac"]
    reboot_only = _args["reboot_only"]
    power_state = _args["power_state"]
    power_on = _args["power_on"]
    power_off = _args["power_off"]
    power_cycle = _args["power_cycle"]
    power_consumed_watts = _args["get_power_consumed"]
    rac_reset = _args["racreset"]
    wait = _args.get("wait", False)
    bmc_reset = _args["bmc_reset"]
    factory_reset = _args["factory_reset"]
    check_boot = _args["check_boot"]
    toggle_boot_device = _args["toggle_boot_device"]
    firmware_inventory = _args["firmware_inventory"]
    clear_jobs = _args["clear_jobs"]
    check_job = _args["check_job"]
    list_jobs = _args["ls_jobs"]
    list_interfaces = _args["ls_interfaces"]
    list_gpu = _args["ls_gpu"]
    list_processors = _args["ls_processors"]
    list_memory = _args["ls_memory"]
    list_serial = _args["ls_serial"]
    check_virtual_media = _args["check_virtual_media"]
    unmount_virtual_media = _args["unmount_virtual_media"]
    mount_virtual_media = _args["mount_virtual_media"]
    boot_to_virtual_media = _args["boot_to_virtual_media"]
    check_remote_image = _args["check_remote_image"]
    boot_remote_image = _args["boot_remote_image"]
    detach_remote_image = _args["detach_remote_image"]
    get_sriov = _args["get_sriov"]
    enable_sriov = _args["enable_sriov"]
    disable_sriov = _args["disable_sriov"]
    set_bios_attribute = _args["set_bios_attribute"]
    get_bios_attribute = _args["get_bios_attribute"]
    attribute = _args["attribute"]
    value = _args["value"]
    set_bios_password = _args["set_bios_password"]
    remove_bios_password = _args["remove_bios_password"]
    new_password = _args["new_password"]
    old_password = _args["old_password"]
    screenshot = _args["screenshot"]
    retries = int(_args["retries"])
    timeout = int(_args.get("timeout", TIMEOUT))
    output = _args["output"]
    get_scp_targets = _args["get_scp_targets"]
    scp_targets = _args["scp_targets"]
    scp_include_read_only = _args["scp_include_read_only"]
    export_scp = _args["export_scp"]
    import_scp = _args["import_scp"]
    get_nic_fqdds = _args["get_nic_fqdds"]
    get_nic_attribute = _args["get_nic_attribute"]
    set_nic_attribute = _args["set_nic_attribute"]
    insecure = _args.get("insecure", False)
    result = True
    badfish = None

    try:
        badfish = await badfish_factory(
            _host=_host,
            _username=_username,
            _password=_password,
            _logger=logger,
            _retries=retries,
            _insecure=insecure,
            _console=console,
            _progress_disabled=progress_disabled,
            _timeout=timeout,
        )

        if _args["host_list"] and not _args["output"]:
            badfish.logger.info("Executing actions on host: %s" % _host)

        if device:
            await badfish.boot_to(device)
        elif boot_to_type:
            await badfish.boot_to_type(boot_to_type, interfaces_path)
        elif boot_to_mac:
            await badfish.boot_to_mac(boot_to_mac)
        elif check_boot:
            await badfish.check_boot(interfaces_path)
        elif toggle_boot_device:
            await badfish.toggle_boot_device(toggle_boot_device)
        elif firmware_inventory:
            await badfish.get_firmware_inventory()
        elif clear_jobs:
            await badfish.clear_job_queue(force)
        elif check_job:
            await badfish.check_schedule_job_status(check_job)
        elif list_jobs:
            await badfish.list_job_queue()
        elif host_type:
            await badfish.change_boot(host_type, interfaces_path, pxe)
        elif rac_reset:
            await badfish.reset_idrac(wait=wait)
        elif bmc_reset:
            await badfish.reset_bmc()
        elif factory_reset:
            await badfish.reset_bios()
        elif power_state:
            state = await badfish.get_power_state()
            logger.info("Power state:")
            logger.info(f"    {_host}: '{state}'")
        elif power_on:
            await badfish.set_power_state("on")
        elif power_off:
            await badfish.set_power_state("off")
        elif power_cycle:
            await badfish.reboot_server(graceful=False)
        elif reboot_only:
            await badfish.reboot_server()
        elif power_consumed_watts:
            await badfish.get_power_consumed_watts()
        elif list_interfaces:
            await badfish.list_interfaces()
        elif list_processors:
            await badfish.list_processors()
        elif list_gpu:
            await badfish.list_gpu()
        elif list_memory:
            await badfish.list_memory()
        elif list_serial:
            await badfish.list_serial()
        elif check_virtual_media:
            await badfish.check_virtual_media()
        elif mount_virtual_media:
            await badfish.mount_virtual_media(mount_virtual_media)
        elif unmount_virtual_media:
            await badfish.unmount_virtual_media()
        elif boot_to_virtual_media:
            await badfish.boot_to_virtual_media()
        elif check_remote_image:
            await badfish.check_remote_image()
        elif boot_remote_image:
            await badfish.boot_remote_image(boot_remote_image)
        elif detach_remote_image:
            await badfish.detach_remote_image()
        elif get_sriov:
            sriov_mode = await badfish.get_sriov_mode()
            if sriov_mode:
                logger.info(sriov_mode)
        elif enable_sriov:
            await badfish.send_sriov_mode(True)
        elif disable_sriov:
            await badfish.send_sriov_mode(False)
        elif get_bios_attribute:
            if attribute:
                await badfish.get_bios_attribute_registry(attribute)
            else:
                data = await badfish.get_bios_attributes()
                for attribute, value in data["Attributes"].items():
                    logger.info(f"{attribute}: {value}")
        elif set_bios_attribute:
            payload = {attribute: value}
            await badfish.set_bios_attribute(payload)
        elif set_bios_password:
            await badfish.set_bios_password(old_password, new_password)
        elif remove_bios_password:
            await badfish.remove_bios_password(old_password)
        elif screenshot:
            await badfish.take_screenshot()
        elif get_scp_targets:
            await badfish.get_scp_targets(get_scp_targets)
        elif export_scp:
            await badfish.export_scp(export_scp, scp_targets, scp_include_read_only)
        elif import_scp:
            await badfish.import_scp(import_scp, scp_targets)
        elif get_nic_fqdds:
            await badfish.get_nic_fqdds()
        elif get_nic_attribute:
            if attribute:
                await badfish.get_nic_attribute_info(get_nic_attribute, attribute)
            else:
                await badfish.get_nic_attribute(get_nic_attribute)
        elif set_nic_attribute:
            await badfish.set_nic_attribute(set_nic_attribute, attribute, value)

        if pxe and not host_type:
            await badfish.set_next_boot_pxe()

    except BadfishException as ex:
        logger.error(ex)
        result = False
    finally:
        if badfish and badfish.session_id:
            try:
                await badfish.delete_session()
                logger.debug(f"Session closed for host: {_host}")
            except BadfishException as ex:
                logger.warning(f"Failed to close session for {_host}: {ex}")

    if _args["host_list"]:
        logger.info("*" * 48)
        if output and result:
            format_handler.host = _host
            format_handler.parse()
    else:
        if output and result:
            format_handler.parse()

    return _host, result


def main(argv=None):
    _args = parse_arguments(argv)

    log_level = DEBUG if _args["verbose"] else INFO
    host = _args["host"]

    delta = _args["delta"]
    if _args["firmware_inventory"] and delta:
        tp = tempfile.NamedTemporaryFile()
        tp.write(f"{host}\n{delta}".encode())
        tp.flush()
        _args["host_list"] = tp.name
        if not _args["output"]:
            _args["output"] = "json"

    host_list = _args["host_list"]
    multi_host = True if host_list else False
    result = True
    output = _args["output"]
    console = Console()
    bfl = BadfishLogger(_args["verbose"], multi_host, _args["log"], output, console=console)
    progress_disabled = bool(output) or multi_host or bool(_args["log"]) or not console.is_terminal

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    tasks = []
    host_order = {}
    if host_list:
        try:
            with open(host_list, "r") as _file:
                for i, _host in enumerate(_file.readlines()):
                    if _host.isspace():
                        continue

                    host_name = _host.strip().split(".")[0]
                    host_order.update({host_name: i})
                    logger = getLogger(host_name)
                    logger.addHandler(bfl.queue_handler)
                    logger.setLevel(log_level)
                    bfl.badfish_handler.host = _host if output else None
                    fn = functools.partial(
                        execute_badfish,
                        _host.strip(),
                        _args,
                        logger,
                        bfl.queue_listener.handlers[0] if output else None,
                        console=console,
                        progress_disabled=progress_disabled,
                    )
                    tasks.append(fn)
        except IOError as ex:
            bfl.logger.debug(ex)
            bfl.logger.error("There was something wrong reading from %s" % host_list)
        results = []
        try:
            results = loop.run_until_complete(asyncio.gather(*[task() for task in tasks], return_exceptions=True))
        except KeyboardInterrupt:
            bfl.logger.warning("Badfish terminated")
            result = False
        except (asyncio.CancelledError, BadfishException) as ex:
            bfl.logger.warning("There was something wrong executing Badfish")
            bfl.logger.debug(ex)
            result = False
        if results and not output:
            result = True
            bfl.logger.info("RESULTS:")
            for res in results:
                if len(res) > 1 and res[1]:
                    bfl.logger.info(f"{res[0]}: SUCCESSFUL")
                else:
                    bfl.logger.info(f"{res[0]}: FAILED")
                    result = False
    elif not host:
        bfl.logger.error("You must specify at least either a host (-H) or a host list (--host-list).")
    else:
        try:
            _host, result = loop.run_until_complete(
                execute_badfish(
                    host,
                    _args,
                    bfl.logger,
                    bfl.queue_listener.handlers[0],
                    console=console,
                    progress_disabled=progress_disabled,
                )
            )
        except KeyboardInterrupt:
            bfl.logger.warning("Badfish terminated")
        except BadfishException as ex:
            bfl.logger.warning("There was something wrong executing Badfish")
            bfl.logger.debug(ex)
            result = False
    bfl.queue_listener.stop()

    if delta:
        bfh_output = bfl.badfish_handler.diff()
    else:
        bfh_output = bfl.badfish_handler.output(output if output else "normal", host_order)
    if _args["log"]:
        og_stdout = sys.stdout
        with open(_args["log"], "w") as f:
            sys.stdout = f
            print(bfh_output)
            sys.stdout = og_stdout
    else:
        if bfh_output:
            print(bfh_output, file=sys.stderr)

    if result:
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
