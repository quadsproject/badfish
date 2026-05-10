import base64
import os

MOCK_HOST = "f01-h01-000-r630.host.io"
MOCK_USER = "mock_user"
MOCK_PASS = "mock_pass"
JOB_ID = "JID_498218641680"
BAD_DEVICE_NAME = "BadIF.Slot.x-y-z"
DEVICE_NIC_I = "NIC.Integrated.1"
DEVICE_NIC_S = "NIC.Slot.1"
MAC_ADDRESS = "40:A6:B7:0C:01:A0"


def render_device_dict(index, device):
    device_dict = {
        "Index": index,
        "Enabled": "True",
        "Id": "BIOS.Setup.1-1#BootSeq#{name}#{hash}".format(**device),
        "Name": device["name"],
    }
    return device_dict


DEVICE_HDD_1 = {"name": "HardDisk.List.1-1", "hash": "c9203080df84781e2ca3d512883dee6f"}
DEVICE_NIC_1 = {
    "name": "NIC.Integrated.1-2-1",
    "hash": "bfa8fe2210d216298c7c53aedfc7e21b",
}
DEVICE_NIC_2 = {"name": "NIC.Slot.2-1-1", "hash": "135ac45c488549c04a21f1c199c2044a"}
DEVICE_OPTICAL_1 = {
    "name": "Optical.iDRACVirtual.1-1",
    "hash": "ak3sjf78u38i2hi29ujudh298duoijd28",
}

BOOT_SEQ_RESPONSE_DIRECTOR = [
    render_device_dict(0, DEVICE_NIC_1),
    render_device_dict(1, DEVICE_HDD_1),
    render_device_dict(2, DEVICE_NIC_2),
]
BOOT_SEQ_RESPONSE_FOREMAN = [
    render_device_dict(0, DEVICE_NIC_2),
    render_device_dict(1, DEVICE_HDD_1),
    render_device_dict(2, DEVICE_NIC_1),
]
BOOT_SEQ_RESPONSE_NO_MATCH = [
    render_device_dict(0, DEVICE_HDD_1),
    render_device_dict(1, DEVICE_NIC_1),
    render_device_dict(2, DEVICE_NIC_2),
]
BOOT_SEQ_RESPONSE_FOREMAN_SHORTER = [
    render_device_dict(0, DEVICE_NIC_1),
]
BOOT_SEQ_RESPONSE_OPTICAL = [
    render_device_dict(0, DEVICE_NIC_1),
    render_device_dict(1, DEVICE_HDD_1),
    render_device_dict(2, DEVICE_NIC_2),
    render_device_dict(3, DEVICE_OPTICAL_1),
]

RESPONSE_WITHOUT = (
    "- INFO     - Current boot order:\n"
    "- INFO     - 1: NIC.Integrated.1-2-1\n"
    "- INFO     - 2: HardDisk.List.1-1\n"
    "- INFO     - 3: NIC.Slot.2-1-1\n"
)
RESPONSE_NO_MATCH = (
    "- INFO     - Current boot order:\n"
    "- INFO     - 1: HardDisk.List.1-1\n"
    "- INFO     - 2: NIC.Integrated.1-2-1\n"
    "- INFO     - 3: NIC.Slot.2-1-1\n"
)
WARN_NO_MATCH = "- WARNING  - Current boot order does not match any of the given.\n%s" % RESPONSE_NO_MATCH
RESPONSE_DIRECTOR = "- WARNING  - Current boot order is set to: director.\n"

RESPONSE_FOREMAN = "- WARNING  - Current boot order is set to: foreman.\n"
INTERFACES_PATH = os.path.join(os.path.dirname(__file__), "../config/idrac_interfaces.yml")

# test_boot_to constants
ERROR_DEV_NO_MATCH = "- ERROR    - Device %s does not match any of the available boot devices for host %s\n" % (
    BAD_DEVICE_NAME,
    MOCK_HOST,
)
TOGGLE_DEV_OK = (
    "- INFO     - %s has now been disabled\n"
    "- WARNING  - Actions resource not found\n"
    "- ERROR    - Power state not found. Try to racreset.\n" % DEVICE_NIC_2["name"]
)
TOGGLE_DEV_NO_MATCH = (
    "- WARNING  - Accepted device names:\n"
    "- WARNING  - NIC.Integrated.1-2-1\n"
    "- WARNING  - HardDisk.List.1-1\n"
    "- WARNING  - NIC.Slot.2-1-1\n"
    "- ERROR    - Boot device name not found\n"
)
RESPONSE_BOOT_TO = (
    f"- WARNING  - Job queue already cleared for iDRAC {MOCK_HOST}, DELETE command will not execute.\n"
    "- INFO     - Command passed to set BIOS attribute pending values.\n"
)
RESPONSE_BOOT_TO_CUSTOM = (
    "- WARNING  - Job queue already cleared for iDRAC host01.example.com, DELETE command will not execute.\n"
    "- INFO     - Command passed to set BIOS attribute pending values.\n"
)
RESPONSE_BOOT_TO_BAD_TYPE = (
    "- ERROR    - Expected values for -t argument are: ['custom', 'director', 'foreman', 'uefi']\n"
)
RESPONSE_BOOT_TO_SERVICE_UNAVAILABLE = (
    f"- WARNING  - Job queue already cleared for iDRAC {MOCK_HOST}, DELETE command will not execute.\n"
    "- ERROR    - Command failed, error code is: 503.\n"
    "- INFO     - Retrying to send one time boot.\n"
    "- INFO     - Command passed to set BIOS attribute pending values.\n"
)
RESPONSE_BOOT_TO_SERVICE_BAD_REQUEST = (
    f"- WARNING  - Job queue already cleared for iDRAC {MOCK_HOST}, DELETE command will not execute.\n"
    "- ERROR    - Command failed, error code is: 400.\n"
    f"- WARNING  - Job queue already cleared for iDRAC {MOCK_HOST}, DELETE command will not execute.\n"
    "- WARNING  - Actions resource not found\n"
    "- INFO     - Status code 204 returned for POST command to reset iDRAC.\n"
    "- INFO     - iDRAC will now reset and be back online within a few minutes.\n"
    "- INFO     - Polling for host state: On\n"
    "- ERROR    - Power state not found. Try to racreset.\n"
)
RESPONSE_BOOT_TO_SERVICE_ERR_HANDLER = (
    f"- WARNING  - Job queue already cleared for iDRAC {MOCK_HOST}, DELETE command will not execute.\n"
    "- ERROR    - Command failed, error code is: 403.\n"
    "- ERROR    - Error reading response from host.\n"
)

RESPONSE_BOOT_TO_BAD_FILE = "- ERROR    - No such file or directory: bad/bad/file.\n"
RESPONSE_BOOT_TO_NO_FILE = "- ERROR    - You must provide a path to the interfaces yaml via `-i` optional argument.\n"
RESPONSE_BOOT_TO_BAD_MAC = "- ERROR    - MAC Address does not match any of the existing\n"

# test_reboot_only
RESPONSE_REBOOT_ONLY_SUCCESS = (
    "- INFO     - Command passed to GracefulRestart server, code return is 204.\n"
    "- INFO     - Polling for host state: Not Down\n"
    "- INFO     - Command passed to On server, code return is 204.\n"
)
RESPONSE_REBOOT_ONLY_FAILED_SEND_RESET = (
    "- ERROR    - Command failed to GracefulRestart server, status code is: 400.\n"
    "- ERROR    - Error reading response from host.\n"
)
RESPONSE_REBOOT_ONLY_SUCCESS_WITH_NG_RT = (
    "- INFO     - Command passed to RestartNow server, code return is 204.\n"
    "- INFO     - Polling for host state: Not Down\n"
    "- INFO     - Command passed to On server, code return is 204.\n"
)
RESPONSE_REBOOT_ONLY_FAILED_GRACE_AND_FORCE = (
    "- WARNING  - Command failed to GracefulRestart server, host appears to be already in that state.\n"
    "- INFO     - Polling for host state: Off\n"
    "- WARNING  - Unable to graceful shutdown the server, will perform forced shutdown now.\n"
    "- WARNING  - Command failed to ForceOff server, host appears to be already in that state.\n"
    "- INFO     - Polling for host state: Not Down\n"
)

# test_power
RESPONSE_POWER_ON_OK = "- INFO     - Command passed to On server, code return is 204.\n"
RESPONSE_POWER_OFF_OK = "- INFO     - Command passed to ForceOff server, code return is 204.\n"
RESPONSE_POWER_OFF_NO_STATE = "- ERROR    - Power state not found. Try to racreset.\n"
RESPONSE_POWER_OFF_ALREADY = (
    "- WARNING  - Command failed to ForceOff server, host appears to be already in that state.\n"
)
RESPONSE_POWER_OFF_MISS_STATE = "- ERROR    - Power state not found. Try to racreset.\n"
RESPONSE_POWER_ON_NOT = "- WARNING  - Command failed to On server, host appears to be already in that state.\n"
RESPONSE_POWER_OFF_NONE = "- WARNING  - Power state appears to be already set to 'off'.\n"
# test_power_consumed_watts
POWER_CONSUMED_RESP = '{"PowerControl":[{"PowerConsumedWatts":"69"}]}'
NO_POWER = '{"PowerControl":[]}'
RESPONSE_POWER_CONSUMED_OK = "- INFO     - Current watts consumed: 69\n"
RESPONSE_NO_POWER_CONSUMED = "- INFO     - Current watts consumed: N/A. Try to `--racreset`.\n"
RESPONSE_POWER_CONSUMED_VAL_ERR = "- ERROR    - Power value outside operating range.\n"
# test_reset_%s
RESPONSE_RESET = (
    "- INFO     - Status code %s returned for POST command to reset %s.\n"
    "- INFO     - %s will now reset and be back online within a few minutes.\n"
)
RESPONSE_RESET_FAIL = "- ERROR    - Status code 400 returned, error is: \nBad Request.\n"
RESPONSE_RESET_WRONG_VENDOR = "- WARNING  - Vendor isn't a %s, if you are trying this on a %s, use %s instead.\n"

# test_change_boot
RESPONSE_CHANGE_NO_BOOT_PREFIX = (
    "- WARNING  - Could not retrieve Bios Attributes.\n" "- WARNING  - Assuming boot mode is Bios.\n"
)
RESPONSE_CHANGE_BOOT = (
    f"- WARNING  - Job queue already cleared for iDRAC {MOCK_HOST}, DELETE command will not "
    "execute.\n"
    "- WARNING  - Actions resource not found\n"
    "- ERROR    - Power state not found. Try to racreset.\n"
)
RESPONSE_CHANGE_BOOT_WITH_BIOS_WARNINGS = (
    "- WARNING  - Could not retrieve Bios Attributes.\n"
    "- WARNING  - Assuming boot mode is Bios.\n"
    f"- WARNING  - Job queue already cleared for iDRAC {MOCK_HOST}, DELETE command will not "
    "execute.\n"
    "- WARNING  - Could not retrieve Bios Attributes.\n"
    "- WARNING  - Assuming boot mode is Bios.\n"
    "- WARNING  - Could not retrieve Bios Attributes.\n"
    "- WARNING  - Assuming boot mode is Bios.\n"
    "- WARNING  - Actions resource not found\n"
    "- ERROR    - Power state not found. Try to racreset.\n"
)
RESPONSE_CHANGE_BOOT_INCORRECT_PATH = "- ERROR    - No such file or directory: 'INCORRECT PATH'.\n"
RESPONSE_CHANGE_BOOT_PATCH_ERROR = (
    f"- WARNING  - Job queue already cleared for iDRAC {MOCK_HOST}, DELETE command will not "
    "execute.\n"
    "- ERROR    - There was something wrong with your request.\n"
    "- ERROR    - Error reading response from host.\n"
)
RESPONSE_CHANGE_BOOT_LESS_VALID_DEVICES = (
    f"- WARNING  - Job queue already cleared for iDRAC {MOCK_HOST}, DELETE command will not "
    "execute.\n"
    "- WARNING  - Some interfaces are not valid boot devices. Ignoring: NIC.Slot.2-1-1, HardDisk.List.1-1\n"
    "- WARNING  - No changes were made since the boot order already matches the requested.\n"
    "- WARNING  - Actions resource not found\n"
    "- ERROR    - Power state not found. Try to racreset.\n"
)
RESPONSE_CHANGE_BOOT_PXE = (
    f"- WARNING  - Job queue already cleared for iDRAC {MOCK_HOST}, DELETE command will not "
    "execute.\n"
    '- INFO     - PATCH command passed to set next boot onetime boot device to: "Pxe".\n'
    "- WARNING  - Actions resource not found\n"
    "- ERROR    - Power state not found. Try to racreset.\n"
)
RESPONSE_CHANGE_BOOT_UEFI = (
    f"- WARNING  - Job queue already cleared for iDRAC {MOCK_HOST}, DELETE command will not execute.\n"
    "- WARNING  - Could not retrieve Bios Attributes.\n"
    "- WARNING  - Could not retrieve Bios Attributes.\n"
    "- WARNING  - Could not retrieve Bios Attributes.\n"
    "- WARNING  - Could not retrieve Bios Attributes.\n"
    "- WARNING  - Could not retrieve Bios Attributes.\n"
    "- WARNING  - Could not retrieve Bios Attributes.\n"
    "- ERROR    - PxeDev1Interface not found. Please check attribute name.\n"
    "- ERROR    - PxeDev1EnDis not found. Please check attribute name.\n"
    "- ERROR    - PxeDev2Interface not found. Please check attribute name.\n"
    "- ERROR    - PxeDev2EnDis not found. Please check attribute name.\n"
    "- ERROR    - PxeDev3Interface not found. Please check attribute name.\n"
    "- ERROR    - PxeDev3EnDis not found. Please check attribute name.\n"
    "- ERROR    - Attribute not found\n"
)
RESPONSE_CHANGE_BAD_TYPE = (
    "- ERROR    - Expected values for -t argument are: ['custom', 'director', 'foreman', 'uefi']\n"
)
RESPONSE_CHANGE_TO_SAME = "- WARNING  - No changes were made since the boot order already matches the requested.\n"
RESPONSE_CHANGE_NO_INT = "- ERROR    - You must provide a path to the interfaces yaml via `-i` optional argument.\n"

ROOT_RESP = (
    '{"Managers":{"@odata.id":"/redfish/v1/Managers"},"Systems":{"@odata.id":"/redfish/v1/Systems"}, '
    '"RedfishVersion": "1.0.2","Oem":{"Dell":{"ServiceTag": "T35T7A6"}}}'
)
ROOT_RESP_SUPERMICRO = (
    '{"Managers":{"@odata.id":"/redfish/v1/Managers"},"Systems":{"@odata.id":"/redfish/v1/Systems"}, '
    '"RedfishVersion": "1.0.2","Oem":{"Supermicro":{}}}'
)
SYS_RESP = '{"Members":[{"@odata.id":"/redfish/v1/Systems/System.Embedded.1"}]}'
MAN_RESP = '{"Members":[{"@odata.id":"/redfish/v1/Managers/iDRAC.Embedded.1"}]}'
RESET_TYPE_RESP = (
    '{"Actions":{"#Manager.Reset":{"ResetType@Redfish.AllowableValues":["GracefulRestart"],'
    '"target":"/redfish/v1/Managers/iDRAC.Embedded.1/Actions/Manager.Reset"}}} '
)
RESET_TYPE_RESP_NO_ALLOWABLE_VALUES = (
    '{"Actions":{"#Manager.Reset":{"target":"/redfish/v1/Managers/1/Actions/Manager.Reset"}}} '
)
RESET_TYPE_NG_RESP = (
    '{"Actions":{"#ComputerSystem.Reset":{"ResetType@Redfish.AllowableValues":["RestartNow"],'
    '"target":"/redfish/v1/Managers/iDRAC.Embedded.1/Actions/Manager.Reset"}}} '
)
INIT_RESP = [ROOT_RESP, ROOT_RESP, SYS_RESP, ROOT_RESP, MAN_RESP]
INIT_RESP_SUPERMICRO = [
    ROOT_RESP_SUPERMICRO,
    ROOT_RESP_SUPERMICRO,
    SYS_RESP,
    ROOT_RESP_SUPERMICRO,
    MAN_RESP,
]
ROOT_RESP_HPE = (
    '{"Managers":{"@odata.id":"/redfish/v1/Managers"},"Systems":{"@odata.id":"/redfish/v1/Systems"}, '
    '"RedfishVersion": "1.0.2","Oem":{"Hpe":{"Manager":[{}]}}}'
)
MAN_RESP_HPE = '{"Members":[{"@odata.id":"/redfish/v1/Managers/1"}]}'
INIT_RESP_HPE = [
    ROOT_RESP_HPE,
    ROOT_RESP_HPE,
    SYS_RESP,
    ROOT_RESP_HPE,
    MAN_RESP_HPE,
]

RESPONSE_INIT_CREDENTIALS_UNAUTHORIZED = (
    f"- ERROR    - Failed to authenticate. Verify your credentials for {MOCK_HOST}\n"
)
RESPONSE_INIT_CREDENTIALS_FAILED_COMS = f"- ERROR    - Failed to communicate with {MOCK_HOST}\n"
RESPONSE_INIT_SYSTEMS_RESOURCE_UNAUTHORIZED = "- ERROR    - Failed to authenticate. Verify your credentials.\n"
RESPONSE_INIT_SYSTEMS_RESOURCE_NOT_FOUND = "- ERROR    - Systems resource not found\n"

STATE_OFF_RESP = '{"PowerState": "Off"}'
STATE_ON_RESP = '{"PowerState": "On"}'
STATE_DOWN_RESP = '{"PowerState": "Down"}'
RESPONSE_POWER_STATE_ON = "- INFO     - Power state:\n" f"- INFO     -     {MOCK_HOST}: 'On'\n"
RESPONSE_POWER_STATE_DOWN = "- INFO     - Power state:\n" f"- INFO     -     {MOCK_HOST}: 'Down'\n"
RESPONSE_POWER_STATE_EMPTY = f"- INFO     - Power state:\n- INFO     -     {MOCK_HOST}: 'Down'\n"

BOOT_MODE_RESP = '{"Attributes": {"BootMode": "Bios"}}'
BOOT_MODE_RESP_UEFI = '{"Attributes": {"BootMode": "UEFI"}}'
PXE_DEV_RESP = (
    '{"Attributes": {'
    '"PxeDev1Interface": "NIC.Integrated.1-2-1", "PxeDev1EnDis": "Disabled",'
    '"PxeDev2Interface": "NIC.Slot.2-1-1", "PxeDev2EnDis": "Disabled",'
    '"PxeDev3Interface": "HardDisk.List.1-1", "PxeDev3EnDis": "Disabled"'
    "}}"
)
BOOT_MODE_NO_RESP = '{"Attributes": {"NoBootMode": ""}}'
BOOT_SEQ_RESP = '{"Attributes": {"BootSeq": %s}}'

ETHERNET_INTERFACES_RESP = (
    '{"Members":['
    '{"@odata.id":"/redfish/v1/Systems/System.Embedded.1/EthernetInterfaces/NIC.Slot.1-1-1"},'
    '{"@odata.id":"/redfish/v1/Systems/System.Embedded.1/EthernetInterfaces/NIC.Integrated.1-1-1"}'
    "]}"
)
ETHERNET_INTERFACES_RESP_NIC_SLOT = (
    "{"
    '"Id": "NIC.Slot.1-1-1",'
    '"MACAddress": "F8:BC:12:22:89:E1",'
    '"Name": "System Ethernet Interface",'
    '"SpeedMbps": 10240,'
    '"Status": {"Health": "OK", "State": "Enabled"}'
    "}"
)
ETHERNET_INTERFACES_RESP_NIC_INT = (
    "{"
    '"Id": "NIC.Integrated.1-1-1",'
    '"MACAddress": "F8:BC:12:22:89:E0",'
    '"Name": "System Ethernet Interface",'
    '"SpeedMbps": 10240,'
    '"Status": {"Health": "OK", "State": "Enabled"}'
    "}"
)
NETWORK_ADAPTERS_RESP = (
    '{"Members": ['
    f'{{"@odata.id": "/redfish/v1/Chassis/System.Embedded.1/NetworkAdapters/{DEVICE_NIC_I}"}},'
    f'{{"@odata.id": "/redfish/v1/Chassis/System.Embedded.1/NetworkAdapters/{DEVICE_NIC_S}"}}'
    "]}"
)
NETWORK_PORTS_ROOT_RESP = (
    '{"Members": [' '{"@odata.id": "/redfish/v1/Chassis/System.Embedded.1/NetworkAdapters/%s/NetworkPorts/%s-1"} ' "]}"
)
NETWORK_DEV_FUNC_RESP = (
    '{"Members": ['
    '{"@odata.id": "/redfish/v1/Chassis/System.Embedded.1/NetworkAdapters/%s/NetworkDeviceFunctions/%s-1"}'
    "]}"
)
NETWORK_DEV_FUNC_DET_RESP = (
    '{"Ethernet": {"MACAddress": "B0:26:28:D8:68:C0"},' '"Oem": {"Dell": {"DellNIC": {"VendorName": "Intel"}}}}'
)
NETWORK_PORTS_RESP = '{"Id": "%s-1", "LinkStatus": "Down", "SupportedLinkCapabilities": [{"LinkSpeedMbps": 1000}]}'
RESPONSE_LS_INTERFACES = (
    "- INFO     - NIC.Integrated.1-1:\n"
    "- INFO     -     Id: NIC.Integrated.1-1\n"
    "- INFO     -     LinkStatus: Down\n"
    "- INFO     -     LinkSpeedMbps: 1000\n"
    "- INFO     -     MACAddress: B0:26:28:D8:68:C0\n"
    "- INFO     -     Vendor: Intel\n"
    "- INFO     - NIC.Slot.1-1:\n"
    "- INFO     -     Id: NIC.Slot.1-1\n"
    "- INFO     -     LinkStatus: Down\n"
    "- INFO     -     LinkSpeedMbps: 1000\n"
    "- INFO     -     MACAddress: B0:26:28:D8:68:C0\n"
    "- INFO     -     Vendor: Intel\n"
)
RESPONSE_LS_ETHERNET = (
    "- INFO     - NIC.Slot.1-1-1:\n"
    "- INFO     -     Name: System Ethernet Interface\n"
    "- INFO     -     MACAddress: F8:BC:12:22:89:E1\n"
    "- INFO     -     Health: OK\n"
    "- INFO     -     SpeedMbps: 10240\n"
    "- INFO     - NIC.Integrated.1-1-1:\n"
    "- INFO     -     Name: System Ethernet Interface\n"
    "- INFO     -     MACAddress: F8:BC:12:22:89:E0\n"
    "- INFO     -     Health: OK\n"
    "- INFO     -     SpeedMbps: 10240\n"
)
RESPONSE_LS_INTERFACES_NOT_SUPPORTED = "- ERROR    - Server does not support this functionality\n"
RESPONSE_LS_INTERFACES_VALUE_ERROR = "- ERROR    - There was something wrong getting network interfaces\n"

INTERFACES_RESP = f'{{"Id":"NIC.Integrated.1-2-1","MACAddress":"{MAC_ADDRESS}"}}'

RESPONSE_LS_JOBS = f"- INFO     - Found active jobs:\n" f"- INFO     -     JobID: {JOB_ID}\n"
RESPONSE_LS_JOBS_EMPTY = "- INFO     - Found active jobs: None\n"
RESPONSE_CLEAR_JOBS = f"- INFO     - Job queue for iDRAC {MOCK_HOST} successfully cleared.\n"
RESPONSE_CHECK_JOB = (
    f"- INFO     - JobID: {JOB_ID}\n"
    "- INFO     - Name: Task\n"
    "- INFO     - Message: Job completed successfully.\n"
    "- INFO     - PercentComplete: 100\n"
)
RESPONSE_CHECK_JOB_BAD = ""
RESPONSE_CHECK_JOB_ERROR = "- ERROR    - Command failed to check job status\n"

DELLJOBSERVICE_UNSUPPORTED = "- WARNING  - iDRAC version installed does not support DellJobService\n"
RESPONSE_CLEAR_JOBS_UNSUPPORTED = f"{RESPONSE_CLEAR_JOBS}"
RESPONSE_CLEAR_JOBS_LIST = (
    f"{RESPONSE_CLEAR_JOBS}- WARNING  - Unexpected status 200 when deleting session for {MOCK_HOST}.\n"
)
RESPONSE_CLEAR_JOBS_LIST_EXCEPTION = (
    f"{RESPONSE_CLEAR_JOBS}- WARNING  - Unexpected status 400 when deleting session for {MOCK_HOST}.\n"
)
RESPONSE_DELETE_JOBS_UNSUPPORTED_EXCEPTION = (
    f"{RESPONSE_CLEAR_JOBS}- WARNING  - Failed to delete session for {MOCK_HOST}: Failed to communicate with server.\n"
)
RESPONSE_DELETE_JOBS_SUPPORTED_EXCEPTION = "- ERROR    - Error reading response from host.\n"

FIRMWARE_INVENTORY_RESP = (
    '{"Members": ['
    '{"@odata.id": "/redfish/v1/UpdateService/FirmwareInventory/Installed-0-16.25.40.62"},'
    '{"@odata.id": "/redfish/v1/UpdateService/FirmwareInventory/Installed-0-19.5.12"}'
    "]} "
)
FIRMWARE_INVENTORY_1_RESP = (
    "{"
    '"Id": "Installed-0-16.25.40.62",'
    '"Name": "Mellanox ConnectX-5",'
    '"ReleaseDate": "00:00:00Z",'
    '"SoftwareId": "0",'
    '"Status": {"Health": "OK","State": "Enabled"},'
    '"Updateable": "True",'
    '"Version": "16.25.40.62"}'
)
FIRMWARE_INVENTORY_2_RESP = (
    "{"
    '"Id": "Installed-0-19.5.12",'
    '"Name": "Intel(R) Ethernet Network Adapter",'
    '"ReleaseDate": "00:00:00Z",'
    '"SoftwareId": "0",'
    '"Status": {"Health": "OK","State": "Enabled"},'
    '"Updateable": "True",'
    '"Version": "19.5.12"}'
)
FIRMWARE_INVENTORY_RESP_CONTAINING_ERROR = '{"error": "Something went wrong when getting firmware inventory"}'
RESPONSE_FIRMWARE_INVENTORY = (
    "- INFO     - Installed-0-16.25.40.62:\n"
    "- INFO     -     Id: Installed-0-16.25.40.62\n"
    "- INFO     -     Name: Mellanox ConnectX-5\n"
    "- INFO     -     ReleaseDate: 00:00:00Z\n"
    "- INFO     -     SoftwareId: 0\n"
    "- INFO     -     Status: {'Health': 'OK', 'State': 'Enabled'}\n"
    "- INFO     -     Updateable: True\n"
    "- INFO     -     Version: 16.25.40.62\n"
    "- INFO     - Installed-0-19.5.12:\n"
    "- INFO     -     Id: Installed-0-19.5.12\n"
    "- INFO     -     Name: Intel(R) Ethernet Network Adapter\n"
    "- INFO     -     ReleaseDate: 00:00:00Z\n"
    "- INFO     -     SoftwareId: 0\n"
    "- INFO     -     Status: {'Health': 'OK', 'State': 'Enabled'}\n"
    "- INFO     -     Updateable: True\n"
    "- INFO     -     Version: 19.5.12\n"
)
RESPONSE_FIRMWARE_INVENTORY_NOT_ABLE_TO_ACCESS = "- ERROR    - Not able to access Firmware inventory.\n"
RESPONSE_FIRMWARE_INVENTORY_NONE_RESPONSE = (
    "- INFO     - Installed-0-16.25.40.62:\n"
    "- INFO     -     Id: Installed-0-16.25.40.62\n"
    "- INFO     -     Name: Mellanox ConnectX-5\n"
    "- INFO     -     ReleaseDate: 00:00:00Z\n"
    "- INFO     -     SoftwareId: 0\n"
    "- INFO     -     Status: {'Health': 'OK', 'State': 'Enabled'}\n"
    "- INFO     -     Updateable: True\n"
    "- INFO     -     Version: 16.25.40.62\n"
)

MEMORY_MEMBERS_RESP = (
    '{"Members": ['
    '{"@odata.id": "/redfish/v1/Systems/System.Embedded.1/Memory/DIMM.Socket.A5"},'
    '{"@odata.id": "/redfish/v1/Systems/System.Embedded.1/Memory/DIMM.Socket.B2"}]}'
)
MEMORY_SUMMARY_RESP = (
    '{"MemorySummary": {'
    '"MemoryMirroring": "System",'
    '"Status": {"Health": "Unknown","HealthRollup": "Unknown","State": "Enabled"},'
    '"TotalSystemMemoryGiB": 384}}'
)
MEMORY_A5_RESP = (
    '{"CapacityMiB": 32768,'
    '"Description": "DIMM A5",'
    '"Manufacturer": "Hynix Semiconductor",'
    '"MemoryDeviceType": "DDR4",'
    '"Name": "DIMM A5",'
    '"OperatingSpeedMhz": 2933}'
)
MEMORY_B2_RESP = (
    '{"CapacityMiB": 32768,'
    '"Description": "DIMM B2",'
    '"Manufacturer": "Hynix Semiconductor",'
    '"MemoryDeviceType": "DDR4",'
    '"Name": "DIMM B2",'
    '"OperatingSpeedMhz": 2933}'
)
RESPONSE_LS_MEMORY = (
    "- INFO     - Memory Summary:\n"
    "- INFO     -     MemoryMirroring: System\n"
    "- INFO     -     TotalSystemMemoryGiB: 384\n"
    "- INFO     - DIMM A5:\n"
    "- INFO     -     CapacityMiB: 32768\n"
    "- INFO     -     Description: DIMM A5\n"
    "- INFO     -     Manufacturer: Hynix Semiconductor\n"
    "- INFO     -     MemoryDeviceType: DDR4\n"
    "- INFO     -     OperatingSpeedMhz: 2933\n"
    "- INFO     - DIMM B2:\n"
    "- INFO     -     CapacityMiB: 32768\n"
    "- INFO     -     Description: DIMM B2\n"
    "- INFO     -     Manufacturer: Hynix Semiconductor\n"
    "- INFO     -     MemoryDeviceType: DDR4\n"
    "- INFO     -     OperatingSpeedMhz: 2933\n"
)
RESPONSE_LS_MEMORY_SUMMARY_VALUE_ERROR = "- ERROR    - There was something wrong getting memory summary\n"
MEMORY_SUMMARY_RESP_FAULTY = (
    '{"MemorySum": {'
    '"MemoryMirroring": "System",'
    '"Status": {"Health": "Unknown","HealthRollup": "Unknown","State": "Enabled"},'
    '"TotalSystemMemoryGiB": 384}}'
)
RESPONSE_LS_MEMORY_SUMMARY_PROC_DATA_ERROR = "- ERROR    - Server does not support this functionality\n"
RESPONSE_LS_MEMORY_DETAILS_NOT_FOUND = (
    "- INFO     - Memory Summary:\n"
    "- INFO     -     MemoryMirroring: System\n"
    "- INFO     -     TotalSystemMemoryGiB: 384\n"
    "- ERROR    - Server does not support this functionality\n"
)
RESPONSE_LS_MEMORY_DETAILS_VALUE_ERROR = (
    "- INFO     - Memory Summary:\n"
    "- INFO     -     MemoryMirroring: System\n"
    "- INFO     -     TotalSystemMemoryGiB: 384\n"
    "- ERROR    - There was something wrong getting memory details\n"
)

PROCESSOR_SUMMARY_RESP = (
    '{"ProcessorSummary": {'
    '"Count": 2,'
    '"LogicalProcessorCount": 80,'
    '"Model": "Intel(R) Xeon(R) Gold 6230 CPU @ 2.10GHz",'
    '"Status": {"Health": "Unknown","HealthRollup": "Unknown","State": "Enabled"}}}'
)
PROCESSOR_MEMBERS_RESP = (
    '{"Members": ['
    '{"@odata.id": "/redfish/v1/Systems/System.Embedded.1/Processors/CPU.Socket.1"},'
    '{"@odata.id": "/redfish/v1/Systems/System.Embedded.1/Processors/CPU.Socket.2"}]}'
)
PROCESSOR_CPU_RESP = (
    '{"InstructionSet": "x86-64",'
    '"Id": "CPU.Socket.%s",'
    '"Manufacturer": "Intel",'
    '"MaxSpeedMHz": 4000,'
    '"Model": "Intel(R) Xeon(R) Gold 6230 CPU @ 2.10GHz",'
    '"Name": "CPU %s",'
    '"TotalCores": 20,'
    '"TotalThreads": 40}'
)
RESPONSE_LS_PROCESSORS = (
    "- INFO     - Processor Summary:\n"
    "- INFO     -     Count: 2\n"
    "- INFO     -     LogicalProcessorCount: 80\n"
    "- INFO     -     Model: Intel(R) Xeon(R) Gold 6230 CPU @ 2.10GHz\n"
    "- INFO     - CPU.Socket.1:\n"
    "- INFO     -     Name: CPU 1\n"
    "- INFO     -     InstructionSet: x86-64\n"
    "- INFO     -     Manufacturer: Intel\n"
    "- INFO     -     MaxSpeedMHz: 4000\n"
    "- INFO     -     Model: Intel(R) Xeon(R) Gold 6230 CPU @ 2.10GHz\n"
    "- INFO     -     TotalCores: 20\n"
    "- INFO     -     TotalThreads: 40\n"
    "- INFO     - CPU.Socket.2:\n"
    "- INFO     -     Name: CPU 2\n"
    "- INFO     -     InstructionSet: x86-64\n"
    "- INFO     -     Manufacturer: Intel\n"
    "- INFO     -     MaxSpeedMHz: 4000\n"
    "- INFO     -     Model: Intel(R) Xeon(R) Gold 6230 CPU @ 2.10GHz\n"
    "- INFO     -     TotalCores: 20\n"
    "- INFO     -     TotalThreads: 40\n"
)
PROCESSOR_SUMMARY_RESP_FAULTY = (
    '{"ProcessorSum": {'
    '"Count": 2,'
    '"LogicalProcessorCount": 80,'
    '"Model": "Intel(R) Xeon(R) Gold 6230 CPU @ 2.10GHz",'
    '"Status": {"Health": "Unknown","HealthRollup": "Unknown","State": "Enabled"}}}'
)
RESPONSE_LS_PROCESSORS_SUMMARY_PROC_DATA_ERROR = "- ERROR    - Server does not support this functionality\n"
RESPONSE_LS_PROCESSORS_SUMMARY_VALUE_ERROR = "- ERROR    - There was something wrong getting processor summary\n"
RESPONSE_LS_PROCESSORS_DETAILS_NOT_FOUND = (
    "- INFO     - Processor Summary:\n"
    "- INFO     -     Count: 2\n"
    "- INFO     -     LogicalProcessorCount: 80\n"
    "- INFO     -     Model: Intel(R) Xeon(R) Gold 6230 CPU @ 2.10GHz\n"
    "- ERROR    - Server does not support this functionality\n"
)
RESPONSE_LS_PROCESSORS_DETAILS_VALUE_ERROR = (
    "- INFO     - Processor Summary:\n"
    "- INFO     -     Count: 2\n"
    "- INFO     -     LogicalProcessorCount: 80\n"
    "- INFO     -     Model: Intel(R) Xeon(R) Gold 6230 CPU @ 2.10GHz\n"
    "- ERROR    - There was something wrong getting processor details\n"
)
GPU_SUMMARY_RESP = '{"GPUSummary":"AMD Instinct MI300X": 2,}'
GPU_SUMMARY_RESP_FAULTY = '{"GPUSummary":"Unknown: 1"}'
GPU_MEMBERS_RESP = (
    '{"Members": ['
    '{"@odata.id": "/redfish/v1/Systems/System.Embedded.1/Processors/ProcAccelerator.Slot.21-1"},'
    '{"@odata.id": "/redfish/v1/Systems/System.Embedded.1/Processors/ProcAccelerator.Slot.22-1"}]}'
)
GPU_MEMBERS_RESP_FAULTY = (
    '{"Members": ['
    '{"@odata.id": "/redfish/v1/Systems/System.Embedded.1/Processors/GPU.Slot.21-1"},'
    '{"@odata.id": "/redfish/v1/Systems/System.Embedded.1/Processors/GPU.Slot.22-1"}]}'
)
GPU_DATA_RESP1 = (
    '{"Model": "AMD Instinct MI300X",'
    '"Manufacturer": "Advanced Micro Devices, Inc. [AMD/ATI]",'
    '"ProcessorType": "Accelerator",'
    '"Id": "ProcAccelerator.Slot.21-1"}'
)
GPU_DATA_RESP2 = (
    '{"Model": "AMD Instinct MI300X",'
    '"Manufacturer": "Advanced Micro Devices, Inc. [AMD/ATI]",'
    '"ProcessorType": "Accelerator",'
    '"Id": "ProcAccelerator.Slot.22-1"}'
)
GPU_DATA_RESP_FAULTY = '{"GPU":"" }'
RESPONSE_LS_GPU = (
    "- INFO     - GPU Summary:\n"
    "- INFO     -   Model: AMD Instinct MI300X (Count: 2)\n"
    "- INFO     - Current GPU's on host:\n"
    "- INFO     -   ProcAccelerator.Slot.21-1:\n"
    "- INFO     -     Model: AMD Instinct MI300X\n"
    "- INFO     -     Manufacturer: Advanced Micro Devices, Inc. [AMD/ATI]\n"
    "- INFO     -     ProcessorType: Accelerator\n"
    "- INFO     -   ProcAccelerator.Slot.22-1:\n"
    "- INFO     -     Model: AMD Instinct MI300X\n"
    "- INFO     -     Manufacturer: Advanced Micro Devices, Inc. [AMD/ATI]\n"
    "- INFO     -     ProcessorType: Accelerator\n"
)

RESPONSE_LS_GPU_SUMMARY_DATA_ERROR = f"- INFO     - GPU Summary:\n- INFO     - Current GPU's on host:\n- WARNING  - Failed to delete session for {MOCK_HOST}: Failed to communicate with server.\n"
RESPONSE_LS_GPU_SUMMARY_VALUE_ERROR = "- ERROR    - There was something wrong getting GPU summary values.\n"
RESPONSE_LS_GPU_SUMMARY_BAD_JSON = "- ERROR    - There was something wrong getting GPU data\n"
RESPONSE_LS_GPU_DETAILS_NOT_FOUND = "- ERROR    - There was something wrong getting host GPU details\n"
RESPONSE_LS_GPU_DETAILS_VALUE_ERROR = (
    "- INFO     - GPU Summary:\n"
    "- INFO     -     Model: AMD Instinct MI300X OAM\n"
    "- INFO     - Current GPU's on host:\n"
    "- ERROR    - There was something wrong getting host GPU detailed values.\n"
)
DELL_REDFISH_ROOT_OEM_RESP = """
    {"Oem":
        {"Dell":
            {"@odata.context":"/redfish/v1/$metadata#DellServiceRoot.DellServiceRoot",
             "@odata.type":"#DellServiceRoot.v1_0_0.DellServiceRoot",
             "IsBranded":0,
             "ManagerMACAddress":"f4:13:37:ee:30:69",
             "ServiceTag":"HXVMC42"}
        }
    }
"""
SYSTEM_SERIAL_NUMBER_RESP = """
    {"@odata.id":"/redfish/v1/Systems/1",
    "Id":"1", "Name":"System",
    "Description":"Description of server",
    "SerialNumber":"S211337X8693420",
    "Manufacturer":"Supermicro",
    "Model":"SYS-5039MS-HUH4F" }
"""
EMPTY_OEM_RESP = '{"Oem":{}}'
RESPONSE_LS_SERIAL_SERVICE_TAG = "- INFO     - ServiceTag:\n" "- INFO     -     f01-h01-000-r630.host.io: HXVMC42\n"
RESPONSE_LS_SERIAL_NUMBER = (
    "- INFO     - Serial Number:\n" "- INFO     -     f01-h01-000-r630.host.io: S211337X8693420\n"
)
RESPONSE_LS_SERIAL_UNSUPPORTED = "- ERROR    - Server does not support this functionality\n"
RESPONSE_LS_SERIAL_SOMETHING_WRONG = "- ERROR    - There was something wrong getting serial summary\n"

BLANK_RESP = '"OK"'
TASK_OK_RESP = '{"Message": "Job completed successfully.","Id": "%s","Name": "Task","PercentComplete": "100"}' % JOB_ID
JOB_OK_RESP = '{"JobID": "%s"}' % JOB_ID
SCREENSHOT_64 = base64.b64encode(bytes("ultimate_screenshot", "utf-8"))
SCREENSHOT_RESP = '{"ServerScreenShotFile": "%s"}' % str(SCREENSHOT_64)
MOCK_HOST_SHORT_FQDN = MOCK_HOST.split(".")[0]
SCREENSHOT_NAME = f"{MOCK_HOST_SHORT_FQDN}_screenshot_now.png"
GIF_NAME = f"{MOCK_HOST_SHORT_FQDN}_screenshot_now.gif"
SCREENSHOT_NOT_SUPPORTED = "- ERROR    - The system does not support screenshots.\n"
SCREENSHOT_BAD_REQUEST = (
    "- ERROR    - POST command failed to get the server screenshot.\n"
    "- ERROR    - {'ServerScreenShotFile': \"%s\"}\n" % str(SCREENSHOT_64)
)
SCREENSHOT_FALSE_OK = "- ERROR    - Error reading response from host.\n"
SCREENSHOT_GIF_FALSE_OK = (
    "- ERROR    - POST command failed to get the server screenshot.\n"
    "- ERROR    - Error reading response from host.\n"
)

VMEDIA_CONFIG_NO_RESOURCE = "- ERROR    - Not able to access virtual media resource.\n"
VMEDIA_CONFIG_NO_CONFIG = "- ERROR    - Not able to access virtual media config.\n"
VMEDIA_GET_VM_CONFIG_RESP_DELL = """
{
    "@odata.context":"/redfish/v1/$metadata#VirtualMediaCollection.VirtualMediaCollection",
    "@odata.id":"/redfish/v1/Managers/iDRAC.Embedded.1/VirtualMedia",
    "@odata.type":"#VirtualMediaCollection.VirtualMediaCollection",
    "Description":"iDRAC Virtual Media Services Settings",
    "Members":[
        {"@odata.id":"/redfish/v1/Managers/iDRAC.Embedded.1/VirtualMedia/RemovableDisk"},
        {"@odata.id":"/redfish/v1/Managers/iDRAC.Embedded.1/VirtualMedia/CD"}
    ],
    "Members@odata.count":2,
    "Name":"Virtual Media Services"
}
"""
VMEDIA_GET_VM_CONFIG_RESP_SM = """
{
    "@odata.context":"/redfish/v1/$metadata#VirtualMediaCollection.VirtualMediaCollection",
    "@odata.type":"#VirtualMediaCollection.VirtualMediaCollection",
    "@odata.id":"/redfish/v1/Managers/1/VM1",
    "Name":"Virtual Media Collection",
    "Description":"Collection of Virtual Media for this System",
    "Members@odata.count":0,
    "Oem":{
        "Supermicro":{
            "@odata.type":"#SmcVirtualMediaExtensions.v1_0_0.VirtualMediaCollection",
            "VirtualMediaConfig":{
                "@odata.id":"/redfish/v1/Managers/1/VM1/CfgCD"
            }
        }
    }
}
"""
VMEDIA_GET_VM_CONFIG_RESP_SM_WITH_MEMBERS = """
{
    "@odata.context": "/redfish/v1/$metadata#VirtualMediaCollection.VirtualMediaCollection",
    "@odata.type": "#VirtualMediaCollection.VirtualMediaCollection",
    "@odata.id": "/redfish/v1/Managers/1/VM1",
    "Name": "Virtual Media Collection",
    "Description": "Collection of Virtual Media for this System",
    "Members": [
        {
            "@odata.id": "/redfish/v1/Managers/1/VM1/CD1"
        }
    ],
    "Members@odata.count": 1,
    "Oem": {
        "Supermicro": {
            "@odata.type": "#SmcVirtualMediaExtensions.v1_0_0.VirtualMediaCollection",
            "VirtualMediaConfig": {
                "@odata.id": "/redfish/v1/Managers/1/VM1/CfgCD"
            }
        }
    }
}
"""
VMEDIA_GET_VM_CONFIG_EMPTY_RESP_SM = "- INFO     - No virtual media mounted.\n"
VMEDIA_GET_MEMBERS_RESP_DELL = """
{"Members": [
    {"@odata.id": "/redfish/v1/Managers/iDRAC.Embedded.1/VirtualMedia/RemovableDisk"},
    {"@odata.id": "/redfish/v1/Managers/iDRAC.Embedded.1/VirtualMedia/CD"}
  ]
}
"""
VMEDIA_MEMBER_RM_DISK_RESP = """
{
  "Id":"RemovableDisk",
  "ImageName":null,
  "Inserted":false,
  "Name":"Virtual Removable Disk"
}
"""
VMEDIA_MEMBER_CD_RESP = """
{
  "Id":"CD",
  "ImageName":"TestImage",
  "Inserted":true,
  "Name":"Virtual CD"
}
"""
VMEDIA_CHECK_GOOD_DELL = """\
- INFO     - RemovableDisk:\n\
- INFO     -     Name: Virtual Removable Disk\n\
- INFO     -     ImageName: None\n\
- INFO     -     Inserted: False\n\
- INFO     - CD:\n\
- INFO     -     Name: Virtual CD\n\
- INFO     -     ImageName: TestImage\n\
- INFO     -     Inserted: True\n\
"""
VMEDIA_CHECK_GOOD_SM = """\
- INFO     - CD:\n\
- INFO     -     Name: Virtual CD\n\
- INFO     -     ImageName: TestImage\n\
- INFO     -     Inserted: True\n\
"""
VMEDIA_GET_ENDPOINT_FALSE = '{"VirtualMedia":false}'
VMEDIA_GET_ENDPOINT_EMPTY = '{"VirtualMedia": {"@odata.id":false}}'
VMEDIA_CHECK_EMPTY = """\
- WARNING  - No active VirtualMedia found\n\
"""

VMEDIA_MOUNT_SUCCESS = "- INFO     - Image mounting operation was successful.\n"
VMEDIA_MOUNT_NOT_ALLOWED = "- ERROR    - Virtual media mounting is not allowed on this server.\n"
VMEDIA_MOUNT_ALREADY_FILLED = (
    "- ERROR    - Couldn't mount virtual media, because there is virtual media mounted already.\n"
)
VMEDIA_MOUNT_SOMETHING_WRONG = "- ERROR    - There was something wrong trying to mount virtual media.\n"

VMEDIA_UNMOUNT_SUCCESS = "- INFO     - Image unmount operation was successful.\n"
VMEDIA_UNMOUNT_NOT_ALLOWED = "- ERROR    - Virtual media unmounting is not allowed on this server.\n"
VMEDIA_UNMOUNT_EMPTY = "- ERROR    - Couldn't unmount virtual media, because there isn't any virtual media mounted.\n"
VMEDIA_UNMOUNT_SOMETHING_WRONG = "- ERROR    - There was something wrong trying to unmount virtual media.\n"

VMEDIA_BOOT_TO_NO_MEDIA = "- ERROR    - No virtual CD is inserted.\n"
VMEDIA_BOOT_TO_MISSING = (
    "- ERROR    - Device Optical.iDRACVirtual.1-1 does not match any of the "
    f"available boot devices for host {MOCK_HOST}\n"
    "- ERROR    - Command failed to set next onetime boot to virtual media. No virtual optical media boot device.\n"
)
VMEDIA_BOOT_TO_SM_PASS = "- INFO     - Command passed to set next onetime boot device to virtual media.\n"
VMEDIA_BOOT_TO_SM_FAIL = "- ERROR    - Command failed to set next onetime boot device to virtual media.\n"
BOOT_SOURCE_OVERRIDE_TARGET_USBCD = """
{
    "Boot": {
        "BootSourceOverrideTarget@Redfish.AllowableValues": [
            "None", "Pxe", "Hdd", "Diags", "CD/DVD",
            "BiosSetup", "FloppyRemovableMedia",
            "UsbKey", "UsbHdd", "UsbFloppy", "UsbCd",
            "UefiUsbKey", "UefiCd", "UefiHdd",
            "UefiUsbHdd", "UefiUsbCd"
        ]
    }
}
"""
BOOT_SOURCE_OVERRIDE_TARGET_CD = """
{
    "Boot": {
        "BootSourceOverrideTarget@Redfish.AllowableValues": [
            "None", "Pxe", "Floppy", "Cd",
            "Usb", "Hdd", "BiosSetup"
        ]
    }
}
"""
VMEDIA_CHECK_DISC_VALUE_ERROR = "- ERROR    - There was something wrong getting values for VirtualMedia\n"
VMEDIA_NO_ENDPOINT_ERROR = "- ERROR    - No VirtualMedia endpoint found\n"

VMEDIA_OS_DEPLOYMENT_NOT_SUPPORTED_CHECK = (
    "- ERROR    - There was something wrong trying to check remote image attach status.\n"
)
VMEDIA_OS_DEPLOYMENT_NOT_SUPPORTED_BOOT = "- ERROR    - Command failed to boot to remote ISO. No job was created.\n"
VMEDIA_OS_DEPLOYMENT_NOT_SUPPORTED_DETACH = "- INFO     - Command to detach remote ISO was successful.\n"
VMEDIA_REMOTE_CHECK_RESP = """
{
    "@Message.ExtendedInfo": [{
        "Message":"Successfully Completed Request",
        "MessageArgs":[],
        "MessageArgs@odata.count":0,
        "MessageId":"Base.1.5.Success",
        "RelatedProperties":[],
        "RelatedProperties@odata.count":0,
        "Resolution":"None"
        ,"Severity":"OK"
    }],
    "DriversAttachStatus":"NotAttached",
    "ISOAttachStatus":"Attached"
}
"""
VMEDIA_REMOTE_CHECK_GOOD = "- INFO     - Current ISO attach status: Attached\n"
VMEDIA_REMOTE_CHECK_FAIL = "- ERROR    - Command failed to get attach status of the remote mounted ISO.\n"
VMEDIA_REMOTE_CHECK_ERROR = "- ERROR    - There was something wrong trying to check remote image attach status.\n"
VMEDIA_REMOTE_BOOT_TASK_RESP = """
{
    "@odata.context":"/redfish/v1/$metadata#Task.Task",
    "@odata.id":"/redfish/v1/TaskService/Tasks/OSDeployment",
    "@odata.type":"#Task.v1_4_2.Task",
    "Description":"Server Configuration and other Tasks running on iDRAC are listed here",
    "EndTime":"",
    "Id":"OSDeployment",
    "Messages":[{
        "Message":"",
        "MessageArgs":[],
        "MessageArgs@odata.count":0,
        "MessageId":""
    }],
    "Messages@odata.count":1,
    "Name":"BootToNetworkISO",
    "PercentComplete":null,
    "TaskState":"Running",
    "TaskStatus":"OK"
}
"""
VMEDIA_REMOTE_BOOT_TASK_FAILED_RESP = """
{
    "@odata.context":"/redfish/v1/$metadata#Task.Task",
    "@odata.id":"/redfish/v1/TaskService/Tasks/OSDeployment",
    "@odata.type":"#Task.v1_4_2.Task",
    "Description":"Server Configuration and other Tasks running on iDRAC are listed here",
    "EndTime":"",
    "Id":"OSDeployment",
    "Messages":[{
        "Message":"",
        "MessageArgs":[],
        "MessageArgs@odata.count":0,
        "MessageId":""
    }],
    "Messages@odata.count":1,
    "Name":"BootToNetworkISO",
    "PercentComplete":null,
    "TaskState":"Failed",
    "TaskStatus":"Error"
}
"""
VMEDIA_REMOTE_BOOT_GOOD = (
    "- INFO     - Command for booting to remote ISO was successful, job was created.\n"
    "- INFO     - OSDeployment task status is OK.\n"
)
VMEDIA_REMOTE_BOOT_WRONG_PATH = "- ERROR    - Wrong NFS path format.\n"
VMEDIA_REMOTE_BOOT_COMMAND_FAIL = "- ERROR    - Command failed to boot to remote ISO. No job was created.\n"
VMEDIA_REMOTE_BOOT_TASK_FAIL = (
    "- INFO     - Command for booting to remote ISO was successful, job was created.\n"
    "- ERROR    - OSDeployment task failed and couldn't be completed.\n"
)
VMEDIA_REMOTE_BOOT_SOMETHING_WRONG = (
    "- INFO     - Command for booting to remote ISO was successful, job was created.\n"
    "- ERROR    - There was something wrong trying to check remote image attach status.\n"
)
VMEDIA_REMOTE_DETACH_GOOD = "- INFO     - Command to detach remote ISO was successful.\n"
VMEDIA_REMOTE_DETACH_FAIL = "- ERROR    - Command failed to detach remote mounted ISO.\n"

BIOS_PASS_SET_GOOD = f"""\
- INFO     - Command passed to set BIOS password.
- WARNING  - Host will now be rebooted for changes to take place.
- INFO     - Command passed to On server, code return is 200.
- INFO     - JobID: {JOB_ID}
- INFO     - Name: Task
- INFO     - Message: Job completed successfully.
- INFO     - PercentComplete: 100
"""
BIOS_PASS_SET_MISS_ARG = """\
- ERROR    - Missing argument: `--new-password`
"""
BIOS_PASS_RM_GOOD = (
    """\
- INFO     - Command passed to set BIOS password.
- WARNING  - Host will now be rebooted for changes to take place.
- INFO     - Command passed to On server, code return is 200.
- INFO     - JobID: %s
- INFO     - Name: Task
- INFO     - Message: Job completed successfully.
- INFO     - PercentComplete: 100
"""
    % JOB_ID
)
BIOS_PASS_RM_MISS_ARG = """\
- ERROR    - Missing argument: `--old-password`
"""
BIOS_PASS_CHANGE_NOT_SUPPORTED = "- ERROR    - BIOS password change not supported on this system.\n"
BIOS_PASS_CHANGE_CMD_FAILED = (
    "- WARNING  - Command failed to set BIOS password\n" "- ERROR    - Error reading response from host.\n"
)
BIOS_PASS_SET_CHECK_JOB_STATUS_BAD_CODE = (
    "- INFO     - Command passed to set BIOS password.\n"
    "- WARNING  - Host will now be rebooted for changes to take place.\n"
    "- INFO     - Command passed to On server, code return is 200.\n"
    "- WARNING  - Job status response missing Message field\n"
)
BIOS_PASS_SET_CHECK_JOB_STATUS_FAIL_MSG = (
    "- INFO     - Command passed to set BIOS password.\n"
    "- WARNING  - Host will now be rebooted for changes to take place.\n"
    "- INFO     - Command passed to On server, code return is 200.\n"
)
CHECK_JOB_STATUS_FAIL_MSG = '{"Message": "Fail"}'
CHECK_JOB_STATUS_UNEXPECTED_MSG_CONTENT = '{"Message": "Unexpected content"}'

ATTRIBUTE_OK = "ProcC1E"
ATTRIBUTE_BAD = "NotThere"
ATTR_VALUE_OK = "Enabled"
ATTR_VALUE_BAD = "NotAllowed"
ATTR_VALUE_DIS = "Disabled"

BIOS_RESPONSE_OK = '{"Attributes":{"%s": "%s"}}' % (ATTRIBUTE_OK, ATTR_VALUE_OK)
BIOS_RESPONSE_DIS = '{"Attributes":{"%s": "%s"}}' % (ATTRIBUTE_OK, ATTR_VALUE_DIS)
BIOS_REGISTRY_BASE = '{"RegistryEntries": {"Attributes": %s}}'
BIOS_RESPONSE_SRIOV = '{"Attributes":{"SriovGlobalEnable": "%s"}}'
BIOS_REGISTRY_1 = {
    "AttributeName": "SystemModelName",
    "CurrentValue": "None",
    "DisplayName": "System Model Name",
    "DisplayOrder": 200,
    "HelpText": "Indicates the product name of the system.",
    "Hidden": "False",
    "Immutable": "True",
    "MaxLength": 40,
    "MenuPath": "./SysInformationRef",
    "MinLength": 0,
    "ReadOnly": "True",
    "ResetRequired": "True",
    "Type": "String",
    "ValueExpression": "None",
    "WriteOnly": "False",
}
BIOS_REGISTRY_2 = {
    "AttributeName": "ProcC1E",
    "CurrentValue": "None",
    "DisplayName": "C1E",
    "DisplayOrder": 9604,
    "HelpText": "When set to Enabled, the processor is allowed to switch to minimum performance state when idle.",
    "Hidden": "False",
    "Immutable": "False",
    "MenuPath": "./SysProfileSettingsRef",
    "ReadOnly": "False",
    "ResetRequired": "True",
    "Type": "Enumeration",
    "Value": [
        {"ValueDisplayName": "Enabled", "ValueName": "Enabled"},
        {"ValueDisplayName": "Disabled", "ValueName": "Disabled"},
    ],
    "WarningText": "None",
    "WriteOnly": "False",
}
BIOS_REGISTRY_OK = BIOS_REGISTRY_BASE % str([BIOS_REGISTRY_1, BIOS_REGISTRY_2])
BIOS_SET_OK = """\
- INFO     - Command passed to set BIOS attribute pending values.
- INFO     - Command passed to GracefulRestart server, code return is 200.
- INFO     - Polling for host state: Not Down
- INFO     - Command passed to On server, code return is 200.
"""
BIOS_SET_BAD_VALUE = (
    """\
- WARNING  - List of accepted values for '%s': ['Enabled', 'Disabled']
- ERROR    - Value not accepted
"""
    % ATTRIBUTE_OK
)
BIOS_SET_BAD_ATTR = """\
- WARNING  - Could not retrieve Bios Attributes.
- ERROR    - NotThere not found. Please check attribute name.
- ERROR    - Attribute not found
"""
BIOS_GET_ALL_OK = f"""- INFO     - {ATTRIBUTE_OK}: {ATTR_VALUE_OK}\n"""
BIOS_GET_ONE_OK = """\
- INFO     - AttributeName: ProcC1E
- INFO     - CurrentValue: Enabled
- INFO     - DisplayName: C1E
- INFO     - DisplayOrder: 9604
- INFO     - HelpText: When set to Enabled, the processor is allowed to switch to minimum performance state when idle.
- INFO     - Hidden: False
- INFO     - Immutable: False
- INFO     - MenuPath: ./SysProfileSettingsRef
- INFO     - ReadOnly: False
- INFO     - ResetRequired: True
- INFO     - Type: Enumeration
- INFO     - Value: [{'ValueDisplayName': 'Enabled', 'ValueName': 'Enabled'}, {'ValueDisplayName': 'Disabled', 'ValueName': 'Disabled'}]
- INFO     - WarningText: None
- INFO     - WriteOnly: False
"""
BIOS_GET_ONE_BAD = (
    """\
- WARNING  - Could not retrieve Bios Attributes.
- ERROR    - Unable to locate the Bios attribute: %s
"""
    % ATTRIBUTE_BAD
)
NEXT_BOOT_PXE_OK = '- INFO     - PATCH command passed to set next boot onetime boot device to: "Pxe".\n'
NEXT_BOOT_PXE_BAD = (
    "- ERROR    - Command failed, error code is 400.\n" "- ERROR    - Error reading response from host.\n"
)

SRIOV_ALREADY = "- WARNING  - SRIOV mode is already in that state. IGNORING.\n"
SRIOV_STATE = "- INFO     - Enabled\n"

IMAGE_SAVED = """- INFO     - Image saved: %s\n"""

KEYBOARD_INTERRUPT = "- WARNING  - Badfish terminated\n"
WRONG_BADFISH_EXECUTION = "- WARNING  - There was something wrong executing Badfish\n"
KEYBOARD_INTERRUPT_HOST_LIST = "[badfish.helpers.logger] - WARNING  - Badfish terminated\n"
WRONG_BADFISH_EXECUTION_HOST_LIST = (
    "[badfish.helpers.logger] - WARNING  - There was something wrong executing Badfish\n"
)
SUCCESSFUL_HOST_LIST = (
    "[badfish.helpers.logger] - INFO     - RESULTS:\n"
    "[badfish.helpers.logger] - INFO     - S: SUCCESSFUL\n"
    "[badfish.helpers.logger] - INFO     - S: SUCCESSFUL\n"
    "[badfish.helpers.logger] - INFO     - S: SUCCESSFUL\n"
)
NO_HOST_ERROR = "- ERROR    - You must specify at least either a host (-H) or a host list (--host-list).\n"
HOST_LIST_EXTRAS = (
    "[f01-h01-000-r630] - ERROR    - ComputerSystem's Members array is either empty or missing\n"
    "[f01-h01-000-r630] - INFO     - ************************************************\n"
    "[f01-h01-000-r630] - ERROR    - ComputerSystem's Members array is either empty or missing\n"
    "[f01-h01-000-r630] - INFO     - ************************************************\n"
    "[f01-h01-000-r630] - ERROR    - ComputerSystem's Members array is either empty or missing\n"
    "[f01-h01-000-r630] - INFO     - ************************************************\n"
    "[badfish.helpers.logger] - INFO     - RESULTS:\n"
    "[badfish.helpers.logger] - INFO     - f01-h01-000-r630.host.io: FAILED\n"
    "[badfish.helpers.logger] - INFO     - f01-h01-000-r630.host.io: FAILED\n"
    "[badfish.helpers.logger] - INFO     - f01-h01-000-r630.host.io: FAILED\n"
)
HOST_FILE_ERROR = "[badfish.helpers.logger] - ERROR    - There was something wrong reading from non/existent/file\n"

# TEST SCP REQUESTS
SCP_GET_TARGETS_ACTIONS_OEM_WITH_ALLOWABLES = """
{
  "Actions": {
    "Oem": {
      "OemManager.v1_0_0#OemManager.ExportSystemConfiguration": {
        "ShareParameters": {
          "Target@Redfish.AllowableValues": [
            "ALL",
            "IDRAC",
            "BIOS",
            "NIC",
            "RAID"
          ]
        },
        "target": "/redfish/v1/Managers/iDRAC.Embedded.1/Actions/Oem/EID_674_Manager.ExportSystemConfiguration"
      }
    }
  }
}
"""
SCP_GET_TARGETS_ACTIONS_OEM_WITHOUT_ALLOWABLES = """
{
  "Actions": {
    "Oem": {
      "OemManager.v1_0_0#OemManager.ExportSystemConfiguration": {
        "ShareParameters": {
        },
        "target": "/redfish/v1/Managers/iDRAC.Embedded.1/Actions/Oem/EID_674_Manager.ExportSystemConfiguration"
      }
    }
  }
}
"""
SCP_GET_TARGETS_ACTIONS_OEM_UNSUPPORTED = """
{
  "Actions": {
    "Oem": {}
  }
}
"""
SCP_MESSAGE_PERCENTAGE = """\
{
    "Oem": {
        "Dell": {
            "Message": "%sporting Server Configuration Profile.",
            "PercentComplete": %d
        }
    }
}
"""
SCP_MESSAGE_PERCENTAGE_STATE = """\
{
    "Oem": {
        "Dell": {
            "Message": "%s",
            "PercentComplete": %d,
            "JobState": "%s"
        }
    }
}
"""
SCP_EXPORT_JOB_FAILED = """\
{
    "JobState": "Failed",
    "Message": "Export operation failed due to internal error"
}
"""

# TEST SCP RESPONSES
RESPONSE_GET_SCP_TARGETS_WITH_ALLOWABLES_PASS = """\
- INFO     - The allowable SCP Export targets are:
- INFO     - ALL
- INFO     - IDRAC
- INFO     - BIOS
- INFO     - NIC
- INFO     - RAID
"""
RESPONSE_GET_SCP_TARGETS_WITHOUT_ALLOWABLES_ERR = (
    "- ERROR    - Couldn't find a list of possible targets, but Export with SCP should be allowed.\n"
)
RESPONSE_GET_SCP_TARGETS_UNSUPPORTED_ERR = "- ERROR    - iDRAC on this system doesn't seem to support SCP Export.\n"
RESPONSE_GET_SCP_TARGETS_WRONG = "- ERROR    - There was something wrong trying to get targets for SCP Export.\n"

RESPONSE_EXPORT_SCP_PASS = f"""\
- INFO     - Job for exporting server configuration successfully created. Job ID: {JOB_ID}
- INFO     - Waiting for export job to complete (typically takes 15-30 seconds)...
- INFO     - SCP export completed successfully.
- INFO     - Exported system configuration to file: ./exports/%s_targets_ALL_export.json
"""
RESPONSE_EXPORT_SCP_STATUS_FAIL = "- ERROR    - Command failed to export system configuration.\n"
RESPONSE_EXPORT_SCP_NO_LOCATION = "- ERROR    - Failed to find a job ID in headers of the response.\n"
RESPONSE_EXPORT_SCP_TIME_OUT = f"""\
- INFO     - Job for exporting server configuration successfully created. Job ID: {JOB_ID}
- INFO     - Waiting for export job to complete (typically takes 15-30 seconds)...
- ERROR    - Export job completed but SystemConfiguration not found in response.
"""
RESPONSE_EXPORT_SCP_JOB_FAILED = f"""\
- INFO     - Job for exporting server configuration successfully created. Job ID: {JOB_ID}
- INFO     - Waiting for export job to complete (typically takes 15-30 seconds)...
- ERROR    - Export job failed with state: Failed
- ERROR    - Message: Export operation failed due to internal error
"""
RESPONSE_IMPORT_SCP_INVALID_FILEPATH = "- ERROR    - File doesn't exist or couldn't be opened.\n"
RESPONSE_IMPORT_SCP_STATUS_FAIL = "- ERROR    - Command failed to import system configuration.\n"
RESPONSE_IMPORT_SCP_TIME_OUT = f"""\
- INFO     - Job for importing server configuration, successfully created. Job ID: {JOB_ID}
- INFO     - Unable to locate OEM data in JSON response, trying again.
- INFO     - Unable to get job status message, trying again.
- INFO     - Importing Server Configuration Profile., percent complete: 1
- ERROR    - Job has been timed out, took longer than 5 minutes, command failed.
"""
RESPONSE_IMPORT_SCP_FAIL_STATE = f"""\
- INFO     - Job for importing server configuration, successfully created. Job ID: {JOB_ID}
- INFO     - Importing Server Configuration Profile., percent complete: 20
- INFO     - Importing Server Configuration Profile., percent complete: 40
- INFO     - Importing Server Configuration Profile., percent complete: 60
- INFO     - Unable to complete the Import operation., percent complete: 100
- ERROR    - Command failed, job status = Failed
"""

RESPONSE_IMPORT_SCP_PASS = f"""\
- INFO     - Job for importing server configuration, successfully created. Job ID: {JOB_ID}
- INFO     - Importing Server Configuration Profile., percent complete: 15
- INFO     - Importing Server Configuration Profile., percent complete: 30
- INFO     - Importing Server Configuration Profile., percent complete: 45
- INFO     - Importing Server Configuration Profile., percent complete: 60
- INFO     - Importing Server Configuration Profile., percent complete: 75
- INFO     - Importing Server Configuration Profile., percent complete: 90
- INFO     - Importing Server Configuration Profile., percent complete: 99
- INFO     - Successfully imported and applied Server Configuration Profile., percent complete: 100
- INFO     - Command passed, job successfully marked as completed. Going to reboot.
"""
GET_NIC_FQQDS_ADAPTERS = """{
    "@odata.context":"/redfish/v1/$metadata#NetworkAdapterCollection.NetworkAdapterCollection",
    "@odata.id":"/redfish/v1/Chassis/System.Embedded.1/NetworkAdapters",
    "@odata.type":"#NetworkAdapterCollection.NetworkAdapterCollection",
    "Description":"Collection Of Network Adapter",
    "Members":[
        {"@odata.id":"/redfish/v1/Chassis/System.Embedded.1/NetworkAdapters/NIC.Embedded.1"},
        {"@odata.id":"/redfish/v1/Chassis/System.Embedded.1/NetworkAdapters/NIC.Integrated.1"},
        {"@odata.id":"/redfish/v1/Chassis/System.Embedded.1/NetworkAdapters/NIC.Slot.3"}
    ],
    "Members@odata.count":3,
    "Name":"Network Adapter Collection"
}
"""
GET_NIC_FQQDS_EMBEDDED = """{
    "@odata.context":"/redfish/v1/$metadata#NetworkDeviceFunctionCollection.NetworkDeviceFunctionCollection",
    "@odata.id":"/redfish/v1/Chassis/System.Embedded.1/NetworkAdapters/NIC.Embedded.1/NetworkDeviceFunctions",
    "@odata.type":"#NetworkDeviceFunctionCollection.NetworkDeviceFunctionCollection",
    "Description":"Collection Of Network Device Function entities",
    "Members":[
        {"@odata.id":"/redfish/v1/Chassis/System.Embedded.1/NetworkAdapters/NIC.Embedded.1/NetworkDeviceFunctions/NIC.Embedded.1-1-1"},
        {"@odata.id":"/redfish/v1/Chassis/System.Embedded.1/NetworkAdapters/NIC.Embedded.1/NetworkDeviceFunctions/NIC.Embedded.2-1-1"}
    ],
    "Members@odata.count":2,
    "Name":"Network Device Function Collection"
}
"""
GET_NIC_FQQDS_INTEGRATED = """{
    "@odata.context":"/redfish/v1/$metadata#NetworkDeviceFunctionCollection.NetworkDeviceFunctionCollection",
    "@odata.id":"/redfish/v1/Chassis/System.Embedded.1/NetworkAdapters/NIC.Integrated.1/NetworkDeviceFunctions",
    "@odata.type":"#NetworkDeviceFunctionCollection.NetworkDeviceFunctionCollection",
    "Description":"Collection Of Network Device Function entities",
    "Members":[
        {"@odata.id":"/redfish/v1/Chassis/System.Embedded.1/NetworkAdapters/NIC.Integrated.1/NetworkDeviceFunctions/NIC.Integrated.1-1-1"},
        {"@odata.id":"/redfish/v1/Chassis/System.Embedded.1/NetworkAdapters/NIC.Integrated.1/NetworkDeviceFunctions/NIC.Integrated.1-2-1"}
    ],
    "Members@odata.count":2,
    "Name":"Network Device Function Collection"
}
"""
GET_NIC_FQQDS_SLOT = """{
    "@odata.context":"/redfish/v1/$metadata#NetworkDeviceFunctionCollection.NetworkDeviceFunctionCollection",
    "@odata.id":"/redfish/v1/Chassis/System.Embedded.1/NetworkAdapters/NIC.Slot.3/NetworkDeviceFunctions",
    "@odata.type":"#NetworkDeviceFunctionCollection.NetworkDeviceFunctionCollection",
    "Description":"Collection Of Network Device Function entities",
    "Members":[
        {"@odata.id": "/redfish/v1/Chassis/System.Embedded.1/NetworkAdapters/NIC.Slot.3/NetworkDeviceFunctions/NIC.Slot.3-1-1"},
        {"@odata.id": "/redfish/v1/Chassis/System.Embedded.1/NetworkAdapters/NIC.Slot.3/NetworkDeviceFunctions/NIC.Slot.3-2-1"}
    ],
    "Members@odata.count":2,
    "Name":"Network Device Function Collection"
}
"""
RESPONSE_GET_NIC_FQQDS_OK = """\
- INFO     - NIC.Embedded.1:
- INFO     -     1: NIC.Embedded.1-1-1
- INFO     -     2: NIC.Embedded.2-1-1
- INFO     - NIC.Integrated.1:
- INFO     -     1: NIC.Integrated.1-1-1
- INFO     -     2: NIC.Integrated.1-2-1
- INFO     - NIC.Slot.3:
- INFO     -     1: NIC.Slot.3-1-1
- INFO     -     2: NIC.Slot.3-2-1
"""
RESPONSE_VENDOR_UNSUPPORTED = "- ERROR    - Operation not supported by vendor."
RESPONSE_FIRMWARE_VERSION_ERROR = "- ERROR    - Was unable to get iDRAC Firmware Version."
RESPONSE_GET_NIC_FQQDS_INVALID = "- ERROR    - Was unable to get NIC FQDDs, invalid server response.\n"
GET_NIC_ATTR_LIST = """\
{
    "@Redfish.Settings":{
        "@odata.context":"/redfish/v1/$metadata#Settings.Settings",
        "@odata.type":"#Settings.v1_3_1.Settings",
        "SettingsObject":{"@odata.id":"/redfish/v1/Chassis/System.Embedded.1/NetworkAdapters/NIC.Embedded.1/NetworkDeviceFunctions/NIC.Embedded.1-1-1/Oem/Dell/DellNetworkAttributes/NIC.Embedded.1-1-1/Settings"},
        "SupportedApplyTimes":[
            "Immediate",
            "AtMaintenanceWindowStart",
            "OnReset",
            "InMaintenanceWindowOnReset"
        ]
    },
    "@odata.context":"/redfish/v1/$metadata#DellAttributes.DellAttributes",
    "@odata.id":"/redfish/v1/Chassis/System.Embedded.1/NetworkAdapters/NIC.Embedded.1/NetworkDeviceFunctions/NIC.Embedded.1-1-1/Oem/Dell/DellNetworkAttributes/NIC.Embedded.1-1-1",
    "@odata.type":"#DellAttributes.v1_0_0.DellAttributes",
    "AttributeRegistry":"NetworkAttributeRegistry_NIC.Embedded.1-1-1",
    "Attributes":{
        "ChipMdl":"BCM5720 A0",
        "PCIDeviceID":"165F",
        "BusDeviceFunction":"04:00:00",
        "MacAddr":"C8:4B:D6:83:16:00",
        "VirtMacAddr":"C8:4B:D6:83:16:00",
        "FCoEOffloadSupport":"Unavailable",
        "iSCSIOffloadSupport":"Unavailable",
        "iSCSIBootSupport":"Unavailable",
        "PXEBootSupport":"Available",
        "FCoEBootSupport":"Unavailable",
        "NicPartitioningSupport":"Unavailable",
        "FlexAddressing":"Unavailable",
        "TXBandwidthControlMaximum":"Unavailable",
        "TXBandwidthControlMinimum":"Unavailable",
        "EnergyEfficientEthernet":"Available",
        "FamilyVersion":"22.00.6",
        "ControllerBIOSVersion":"1.39",
        "EFIVersion":"21.6.29",
        "BlnkLeds":0,
        "BannerMessageTimeout":5,
        "VLanId":1,
        "EEEControl":"Enabled",
        "LinkStatus":"Disconnected",
        "BootOptionROM":"Enabled",
        "LegacyBootProto":"NONE",
        "BootStrapType":"AutoDetect",
        "HideSetupPrompt":"Disabled",
        "LnkSpeed":"AutoNeg",
        "WakeOnLan":"Enabled",
        "VLanMode":"Disabled",
        "PermitTotalPortShutdown":"Disabled"
    },
    "Description":"DellNetworkAttributes represents the Network device attribute details.",
    "Id":"NIC.Embedded.1-1-1",
    "Name":"DellNetworkAttributes"
}
"""
RESPONSE_GET_NIC_ATTR_LIST_OK = """\
- INFO     - NIC.Embedded.1-1-1
- INFO     -     ChipMdl: BCM5720 A0
- INFO     -     PCIDeviceID: 165F
- INFO     -     BusDeviceFunction: 04:00:00
- INFO     -     MacAddr: C8:4B:D6:83:16:00
- INFO     -     VirtMacAddr: C8:4B:D6:83:16:00
- INFO     -     FCoEOffloadSupport: Unavailable
- INFO     -     iSCSIOffloadSupport: Unavailable
- INFO     -     iSCSIBootSupport: Unavailable
- INFO     -     PXEBootSupport: Available
- INFO     -     FCoEBootSupport: Unavailable
- INFO     -     NicPartitioningSupport: Unavailable
- INFO     -     FlexAddressing: Unavailable
- INFO     -     TXBandwidthControlMaximum: Unavailable
- INFO     -     TXBandwidthControlMinimum: Unavailable
- INFO     -     EnergyEfficientEthernet: Available
- INFO     -     FamilyVersion: 22.00.6
- INFO     -     ControllerBIOSVersion: 1.39
- INFO     -     EFIVersion: 21.6.29
- INFO     -     BlnkLeds: 0
- INFO     -     BannerMessageTimeout: 5
- INFO     -     VLanId: 1
- INFO     -     EEEControl: Enabled
- INFO     -     LinkStatus: Disconnected
- INFO     -     BootOptionROM: Enabled
- INFO     -     LegacyBootProto: NONE
- INFO     -     BootStrapType: AutoDetect
- INFO     -     HideSetupPrompt: Disabled
- INFO     -     LnkSpeed: AutoNeg
- INFO     -     WakeOnLan: Enabled
- INFO     -     VLanMode: Disabled
- INFO     -     PermitTotalPortShutdown: Disabled
"""
RESPONSE_GET_NIC_ATTR_LIST_INVALID = "- ERROR    - Was unable to get NIC attribute(s) info, invalid server response.\n"
GET_FW_VERSION = """\
{
    "FirmwareVersion":"5.10.50.00"
}
"""
GET_FW_VERSION_UNSUPPORTED = """\
{
    "FirmwareVersion":"4.10.50.00"
}
"""
GET_NIC_ATTR_REGISTRY = """
{
    "@odata.context": "/redfish/v1/$metadata#AttributeRegistry.AttributeRegistry",
    "@odata.id": "/redfish/v1/Registries/NetworkAttributesRegistry_NIC.Embedded.1-1-1/NetworkAttributesRegistry_NIC.Embedded.1-1-1.json",
    "@odata.type": "#AttributeRegistry.v1_3_3.AttributeRegistry",
    "Description": "This registry defines a representation of Network Attribute instances",
    "Id": "NetworkAttributesRegistry_NIC.Embedded.1-1-1",
    "Language": "en",
    "Name": "Network Attribute Registry",
    "OwningEntity": "Dell",
    "RegistryEntries": {
        "Attributes": [
            {
                "AttributeName": "ChipMdl",
                "CurrentValue": null,
                "DisplayName": "Chip Type",
                "DisplayOrder": 104,
                "HelpText": null,
                "Hidden": false,
                "Immutable": true,
                "MaxLength": 1024,
                "MenuPath": "./",
                "MinLength": 0,
                "Oem": {
                    "Dell": {
                        "@odata.type": "#DellOemAttributeRegistry.v1_0_0.Attributes",
                        "GroupDisplayName": "Main Configuration Page",
                        "GroupName": "VndrConfigPage"
                    }
                },
                "ReadOnly": true,
                "ResetRequired": true,
                "Type": "String",
                "ValueExpression": null,
                "WriteOnly": false
            },
            {
                "AttributeName": "PCIDeviceID",
                "CurrentValue": null,
                "DisplayName": "PCI Device ID",
                "DisplayOrder": 105,
                "HelpText": null,
                "Hidden": false,
                "Immutable": true,
                "MaxLength": 1024,
                "MenuPath": "./",
                "MinLength": 0,
                "Oem": {
                    "Dell": {
                        "@odata.type": "#DellOemAttributeRegistry.v1_0_0.Attributes",
                        "GroupDisplayName": "Main Configuration Page",
                        "GroupName": "VndrConfigPage"
                    }
                },
                "ReadOnly": true,
                "ResetRequired": true,
                "Type": "String",
                "ValueExpression": null,
                "WriteOnly": false
            },
            {
                "AttributeName": "BusDeviceFunction",
                "CurrentValue": null,
                "DisplayName": "PCI Address",
                "DisplayOrder": 106,
                "HelpText": null,
                "Hidden": false,
                "Immutable": true,
                "MaxLength": 1024,
                "MenuPath": "./",
                "MinLength": 0,
                "Oem": {
                    "Dell": {
                        "@odata.type": "#DellOemAttributeRegistry.v1_0_0.Attributes",
                        "GroupDisplayName": "Main Configuration Page",
                        "GroupName": "VndrConfigPage"
                    }
                },
                "ReadOnly": true,
                "ResetRequired": true,
                "Type": "String",
                "ValueExpression": null,
                "WriteOnly": false
            },
            {
                "AttributeName": "MacAddr",
                "CurrentValue": null,
                "DisplayName": "MAC Address",
                "DisplayOrder": 108,
                "HelpText": null,
                "Hidden": false,
                "Immutable": true,
                "MaxLength": 17,
                "MenuPath": "./",
                "MinLength": 17,
                "Oem": {
                    "Dell": {
                        "@odata.type": "#DellOemAttributeRegistry.v1_0_0.Attributes",
                        "GroupDisplayName": "Main Configuration Page",
                        "GroupName": "VndrConfigPage"
                    }
                },
                "ReadOnly": true,
                "ResetRequired": true,
                "Type": "String",
                "ValueExpression": null,
                "WriteOnly": false
            },
            {
                "AttributeName": "VirtMacAddr",
                "CurrentValue": null,
                "DisplayName": "Virtual MAC Address",
                "DisplayOrder": 109,
                "HelpText": null,
                "Hidden": false,
                "Immutable": false,
                "MaxLength": 17,
                "MenuPath": "./",
                "MinLength": 17,
                "Oem": {
                    "Dell": {
                        "@odata.type": "#DellOemAttributeRegistry.v1_0_0.Attributes",
                        "GroupDisplayName": "Main Configuration Page",
                        "GroupName": "VndrConfigPage"
                    }
                },
                "ReadOnly": false,
                "ResetRequired": true,
                "Type": "String",
                "ValueExpression": "^([0-9a-fA-F]{2}:){5}([0-9a-fA-F]{2})$",
                "WriteOnly": false
            },
            {
                "AttributeName": "FCoEOffloadSupport",
                "CurrentValue": null,
                "DisplayName": "FCoE Offload Support",
                "DisplayOrder": 110,
                "HelpText": null,
                "Hidden": false,
                "Immutable": true,
                "MaxLength": 12,
                "MenuPath": "./",
                "MinLength": 0,
                "Oem": {
                    "Dell": {
                        "@odata.type": "#DellOemAttributeRegistry.v1_0_0.Attributes",
                        "GroupDisplayName": "Main Configuration Page",
                        "GroupName": "VndrConfigPage"
                    }
                },
                "ReadOnly": true,
                "ResetRequired": true,
                "Type": "String",
                "ValueExpression": null,
                "WriteOnly": false
            },
            {
                "AttributeName": "iSCSIOffloadSupport",
                "CurrentValue": null,
                "DisplayName": "iSCSI Offload Support",
                "DisplayOrder": 111,
                "HelpText": null,
                "Hidden": false,
                "Immutable": true,
                "MaxLength": 12,
                "MenuPath": "./",
                "MinLength": 0,
                "Oem": {
                    "Dell": {
                        "@odata.type": "#DellOemAttributeRegistry.v1_0_0.Attributes",
                        "GroupDisplayName": "Main Configuration Page",
                        "GroupName": "VndrConfigPage"
                    }
                },
                "ReadOnly": true,
                "ResetRequired": true,
                "Type": "String",
                "ValueExpression": null,
                "WriteOnly": false
            },
            {
                "AttributeName": "iSCSIBootSupport",
                "CurrentValue": null,
                "DisplayName": "iSCSI Boot Support",
                "DisplayOrder": 112,
                "HelpText": null,
                "Hidden": false,
                "Immutable": true,
                "MaxLength": 12,
                "MenuPath": "./",
                "MinLength": 0,
                "Oem": {
                    "Dell": {
                        "@odata.type": "#DellOemAttributeRegistry.v1_0_0.Attributes",
                        "GroupDisplayName": "Main Configuration Page",
                        "GroupName": "VndrConfigPage"
                    }
                },
                "ReadOnly": true,
                "ResetRequired": true,
                "Type": "String",
                "ValueExpression": null,
                "WriteOnly": false
            },
            {
                "AttributeName": "PXEBootSupport",
                "CurrentValue": null,
                "DisplayName": "PXE Boot Support",
                "DisplayOrder": 113,
                "HelpText": null,
                "Hidden": false,
                "Immutable": true,
                "MaxLength": 12,
                "MenuPath": "./",
                "MinLength": 0,
                "Oem": {
                    "Dell": {
                        "@odata.type": "#DellOemAttributeRegistry.v1_0_0.Attributes",
                        "GroupDisplayName": "Main Configuration Page",
                        "GroupName": "VndrConfigPage"
                    }
                },
                "ReadOnly": true,
                "ResetRequired": true,
                "Type": "String",
                "ValueExpression": null,
                "WriteOnly": false
            },
            {
                "AttributeName": "FCoEBootSupport",
                "CurrentValue": null,
                "DisplayName": "FCoE Boot Support",
                "DisplayOrder": 114,
                "HelpText": null,
                "Hidden": false,
                "Immutable": true,
                "MaxLength": 12,
                "MenuPath": "./",
                "MinLength": 0,
                "Oem": {
                    "Dell": {
                        "@odata.type": "#DellOemAttributeRegistry.v1_0_0.Attributes",
                        "GroupDisplayName": "Main Configuration Page",
                        "GroupName": "VndrConfigPage"
                    }
                },
                "ReadOnly": true,
                "ResetRequired": true,
                "Type": "String",
                "ValueExpression": null,
                "WriteOnly": false
            },
            {
                "AttributeName": "NicPartitioningSupport",
                "CurrentValue": null,
                "DisplayName": "NIC Partitioning Support",
                "DisplayOrder": 115,
                "HelpText": null,
                "Hidden": false,
                "Immutable": true,
                "MaxLength": 12,
                "MenuPath": "./",
                "MinLength": 0,
                "Oem": {
                    "Dell": {
                        "@odata.type": "#DellOemAttributeRegistry.v1_0_0.Attributes",
                        "GroupDisplayName": "Main Configuration Page",
                        "GroupName": "VndrConfigPage"
                    }
                },
                "ReadOnly": true,
                "ResetRequired": true,
                "Type": "String",
                "ValueExpression": null,
                "WriteOnly": false
            },
            {
                "AttributeName": "FlexAddressing",
                "CurrentValue": null,
                "DisplayName": "FlexAddressing",
                "DisplayOrder": 116,
                "HelpText": null,
                "Hidden": false,
                "Immutable": true,
                "MaxLength": 12,
                "MenuPath": "./",
                "MinLength": 0,
                "Oem": {
                    "Dell": {
                        "@odata.type": "#DellOemAttributeRegistry.v1_0_0.Attributes",
                        "GroupDisplayName": "Main Configuration Page",
                        "GroupName": "VndrConfigPage"
                    }
                },
                "ReadOnly": true,
                "ResetRequired": true,
                "Type": "String",
                "ValueExpression": null,
                "WriteOnly": false
            },
            {
                "AttributeName": "TXBandwidthControlMaximum",
                "CurrentValue": null,
                "DisplayName": "TX Bandwidth Control Maximum",
                "DisplayOrder": 117,
                "HelpText": null,
                "Hidden": false,
                "Immutable": true,
                "MaxLength": 12,
                "MenuPath": "./",
                "MinLength": 0,
                "Oem": {
                    "Dell": {
                        "@odata.type": "#DellOemAttributeRegistry.v1_0_0.Attributes",
                        "GroupDisplayName": "Main Configuration Page",
                        "GroupName": "VndrConfigPage"
                    }
                },
                "ReadOnly": true,
                "ResetRequired": true,
                "Type": "String",
                "ValueExpression": null,
                "WriteOnly": false
            },
            {
                "AttributeName": "TXBandwidthControlMinimum",
                "CurrentValue": null,
                "DisplayName": "TX Bandwidth Control Minimum",
                "DisplayOrder": 118,
                "HelpText": null,
                "Hidden": false,
                "Immutable": true,
                "MaxLength": 12,
                "MenuPath": "./",
                "MinLength": 0,
                "Oem": {
                    "Dell": {
                        "@odata.type": "#DellOemAttributeRegistry.v1_0_0.Attributes",
                        "GroupDisplayName": "Main Configuration Page",
                        "GroupName": "VndrConfigPage"
                    }
                },
                "ReadOnly": true,
                "ResetRequired": true,
                "Type": "String",
                "ValueExpression": null,
                "WriteOnly": false
            },
            {
                "AttributeName": "EnergyEfficientEthernet",
                "CurrentValue": null,
                "DisplayName": "Energy Efficient Ethernet (EEE)",
                "DisplayOrder": 119,
                "HelpText": null,
                "Hidden": false,
                "Immutable": true,
                "MaxLength": 12,
                "MenuPath": "./",
                "MinLength": 0,
                "Oem": {
                    "Dell": {
                        "@odata.type": "#DellOemAttributeRegistry.v1_0_0.Attributes",
                        "GroupDisplayName": "Main Configuration Page",
                        "GroupName": "VndrConfigPage"
                    }
                },
                "ReadOnly": true,
                "ResetRequired": true,
                "Type": "String",
                "ValueExpression": null,
                "WriteOnly": false
            },
            {
                "AttributeName": "FamilyVersion",
                "CurrentValue": null,
                "DisplayName": "Family Firmware Version",
                "DisplayOrder": 200,
                "HelpText": null,
                "Hidden": false,
                "Immutable": true,
                "MaxLength": 20,
                "MenuPath": "./",
                "MinLength": 0,
                "Oem": {
                    "Dell": {
                        "@odata.type": "#DellOemAttributeRegistry.v1_0_0.Attributes",
                        "GroupDisplayName": "Firmware Image Properties",
                        "GroupName": "FrmwImgMenu"
                    }
                },
                "ReadOnly": true,
                "ResetRequired": true,
                "Type": "String",
                "ValueExpression": null,
                "WriteOnly": false
            },
            {
                "AttributeName": "ControllerBIOSVersion",
                "CurrentValue": null,
                "DisplayName": "Controller BIOS Version",
                "DisplayOrder": 201,
                "HelpText": null,
                "Hidden": false,
                "Immutable": true,
                "MaxLength": 16,
                "MenuPath": "./",
                "MinLength": 0,
                "Oem": {
                    "Dell": {
                        "@odata.type": "#DellOemAttributeRegistry.v1_0_0.Attributes",
                        "GroupDisplayName": "Firmware Image Properties",
                        "GroupName": "FrmwImgMenu"
                    }
                },
                "ReadOnly": true,
                "ResetRequired": true,
                "Type": "String",
                "ValueExpression": null,
                "WriteOnly": false
            },
            {
                "AttributeName": "EFIVersion",
                "CurrentValue": null,
                "DisplayName": "EFI Version",
                "DisplayOrder": 202,
                "HelpText": null,
                "Hidden": false,
                "Immutable": true,
                "MaxLength": 16,
                "MenuPath": "./",
                "MinLength": 0,
                "Oem": {
                    "Dell": {
                        "@odata.type": "#DellOemAttributeRegistry.v1_0_0.Attributes",
                        "GroupDisplayName": "Firmware Image Properties",
                        "GroupName": "FrmwImgMenu"
                    }
                },
                "ReadOnly": true,
                "ResetRequired": true,
                "Type": "String",
                "ValueExpression": null,
                "WriteOnly": false
            },
            {
                "AttributeName": "BlnkLeds",
                "CurrentValue": null,
                "DisplayName": "Blink LEDs",
                "DisplayOrder": 102,
                "HelpText": null,
                "Hidden": false,
                "Immutable": false,
                "LowerBound": 0,
                "MenuPath": "./",
                "Oem": {
                    "Dell": {
                        "@odata.type": "#DellOemAttributeRegistry.v1_0_0.Attributes",
                        "GroupDisplayName": "Main Configuration Page",
                        "GroupName": "VndrConfigPage"
                    }
                },
                "ReadOnly": false,
                "ResetRequired": true,
                "ScalarIncrement": 0,
                "Type": "Integer",
                "UpperBound": 15,
                "WarningText": null,
                "WriteOnly": false
            },
            {
                "AttributeName": "BannerMessageTimeout",
                "CurrentValue": null,
                "DisplayName": "Banner Message Timeout",
                "DisplayOrder": 304,
                "HelpText": null,
                "Hidden": false,
                "Immutable": false,
                "LowerBound": 0,
                "MenuPath": "./",
                "Oem": {
                    "Dell": {
                        "@odata.type": "#DellOemAttributeRegistry.v1_0_0.Attributes",
                        "GroupDisplayName": "NIC Configuration",
                        "GroupName": "NICConfig"
                    }
                },
                "ReadOnly": false,
                "ResetRequired": true,
                "ScalarIncrement": 0,
                "Type": "Integer",
                "UpperBound": 15,
                "WarningText": null,
                "WriteOnly": false
            },
            {
                "AttributeName": "VLanId",
                "CurrentValue": null,
                "DisplayName": "Virtual LAN ID",
                "DisplayOrder": 308,
                "HelpText": null,
                "Hidden": false,
                "Immutable": false,
                "LowerBound": 1,
                "MenuPath": "./",
                "Oem": {
                    "Dell": {
                        "@odata.type": "#DellOemAttributeRegistry.v1_0_0.Attributes",
                        "GroupDisplayName": "NIC Configuration",
                        "GroupName": "NICConfig"
                    }
                },
                "ReadOnly": true,
                "ResetRequired": true,
                "ScalarIncrement": 0,
                "Type": "Integer",
                "UpperBound": 4094,
                "WarningText": null,
                "WriteOnly": false
            },
            {
                "AttributeName": "EEEControl",
                "CurrentValue": null,
                "DisplayName": "Energy Efficient Ethernet",
                "DisplayOrder": 103,
                "HelpText": null,
                "Hidden": false,
                "Immutable": false,
                "MenuPath": "./",
                "Oem": {
                    "Dell": {
                        "@odata.type": "#DellOemAttributeRegistry.v1_0_0.Attributes",
                        "GroupDisplayName": "Main Configuration Page",
                        "GroupName": "VndrConfigPage"
                    }
                },
                "ReadOnly": false,
                "ResetRequired": true,
                "Type": "Enumeration",
                "Value": [
                    {
                        "ValueDisplayName": "Disabled",
                        "ValueName": "Disabled"
                    },
                    {
                        "ValueDisplayName": "Maximum Power Savings",
                        "ValueName": "Enabled"
                    }
                ],
                "WarningText": null,
                "WriteOnly": false
            },
            {
                "AttributeName": "LinkStatus",
                "CurrentValue": null,
                "DisplayName": "Link Status",
                "DisplayOrder": 107,
                "HelpText": null,
                "Hidden": false,
                "Immutable": true,
                "MenuPath": "./",
                "Oem": {
                    "Dell": {
                        "@odata.type": "#DellOemAttributeRegistry.v1_0_0.Attributes",
                        "GroupDisplayName": "Main Configuration Page",
                        "GroupName": "VndrConfigPage"
                    }
                },
                "ReadOnly": true,
                "ResetRequired": true,
                "Type": "Enumeration",
                "Value": [
                    {
                        "ValueDisplayName": "Disconnected",
                        "ValueName": "Disconnected"
                    },
                    {
                        "ValueDisplayName": "Connected",
                        "ValueName": "Connected"
                    }
                ],
                "WarningText": null,
                "WriteOnly": false
            },
            {
                "AttributeName": "BootOptionROM",
                "CurrentValue": null,
                "DisplayName": "Option ROM",
                "DisplayOrder": 300,
                "HelpText": null,
                "Hidden": false,
                "Immutable": false,
                "MenuPath": "./",
                "Oem": {
                    "Dell": {
                        "@odata.type": "#DellOemAttributeRegistry.v1_0_0.Attributes",
                        "GroupDisplayName": "NIC Configuration",
                        "GroupName": "NICConfig"
                    }
                },
                "ReadOnly": false,
                "ResetRequired": true,
                "Type": "Enumeration",
                "Value": [
                    {
                        "ValueDisplayName": "Disabled",
                        "ValueName": "Disabled"
                    },
                    {
                        "ValueDisplayName": "Enabled",
                        "ValueName": "Enabled"
                    }
                ],
                "WarningText": null,
                "WriteOnly": false
            },
            {
                "AttributeName": "LegacyBootProto",
                "CurrentValue": null,
                "DisplayName": "Legacy Boot Protocol",
                "DisplayOrder": 301,
                "HelpText": null,
                "Hidden": false,
                "Immutable": false,
                "MenuPath": "./",
                "Oem": {
                    "Dell": {
                        "@odata.type": "#DellOemAttributeRegistry.v1_0_0.Attributes",
                        "GroupDisplayName": "NIC Configuration",
                        "GroupName": "NICConfig"
                    }
                },
                "ReadOnly": false,
                "ResetRequired": true,
                "Type": "Enumeration",
                "Value": [
                    {
                        "ValueDisplayName": "PXE",
                        "ValueName": "PXE"
                    },
                    {
                        "ValueDisplayName": "None",
                        "ValueName": "NONE"
                    }
                ],
                "WarningText": null,
                "WriteOnly": false
            },
            {
                "AttributeName": "BootStrapType",
                "CurrentValue": null,
                "DisplayName": "Boot Strap Type",
                "DisplayOrder": 302,
                "HelpText": null,
                "Hidden": false,
                "Immutable": false,
                "MenuPath": "./",
                "Oem": {
                    "Dell": {
                        "@odata.type": "#DellOemAttributeRegistry.v1_0_0.Attributes",
                        "GroupDisplayName": "NIC Configuration",
                        "GroupName": "NICConfig"
                    }
                },
                "ReadOnly": false,
                "ResetRequired": true,
                "Type": "Enumeration",
                "Value": [
                    {
                        "ValueDisplayName": "Auto Detect",
                        "ValueName": "AutoDetect"
                    },
                    {
                        "ValueDisplayName": "BBS",
                        "ValueName": "BBS"
                    },
                    {
                        "ValueDisplayName": "Int 18h",
                        "ValueName": "Int18h"
                    },
                    {
                        "ValueDisplayName": "Int 19h",
                        "ValueName": "Int19h"
                    }
                ],
                "WarningText": null,
                "WriteOnly": false
            },
            {
                "AttributeName": "HideSetupPrompt",
                "CurrentValue": null,
                "DisplayName": "Hide Setup Prompt",
                "DisplayOrder": 303,
                "HelpText": null,
                "Hidden": false,
                "Immutable": false,
                "MenuPath": "./",
                "Oem": {
                    "Dell": {
                        "@odata.type": "#DellOemAttributeRegistry.v1_0_0.Attributes",
                        "GroupDisplayName": "NIC Configuration",
                        "GroupName": "NICConfig"
                    }
                },
                "ReadOnly": false,
                "ResetRequired": true,
                "Type": "Enumeration",
                "Value": [
                    {
                        "ValueDisplayName": "Disabled",
                        "ValueName": "Disabled"
                    },
                    {
                        "ValueDisplayName": "Enabled",
                        "ValueName": "Enabled"
                    }
                ],
                "WarningText": null,
                "WriteOnly": false
            },
            {
                "AttributeName": "LnkSpeed",
                "CurrentValue": null,
                "DisplayName": "Link Speed",
                "DisplayOrder": 305,
                "HelpText": null,
                "Hidden": false,
                "Immutable": false,
                "MenuPath": "./",
                "Oem": {
                    "Dell": {
                        "@odata.type": "#DellOemAttributeRegistry.v1_0_0.Attributes",
                        "GroupDisplayName": "NIC Configuration",
                        "GroupName": "NICConfig"
                    }
                },
                "ReadOnly": false,
                "ResetRequired": true,
                "Type": "Enumeration",
                "Value": [
                    {
                        "ValueDisplayName": "Auto Negotiated",
                        "ValueName": "AutoNeg"
                    },
                    {
                        "ValueDisplayName": "10 Mbps Half",
                        "ValueName": "10MbpsHalf"
                    },
                    {
                        "ValueDisplayName": "10 Mbps Full",
                        "ValueName": "10MbpsFull"
                    },
                    {
                        "ValueDisplayName": "100 Mbps Half",
                        "ValueName": "100MbpsHalf"
                    },
                    {
                        "ValueDisplayName": "100 Mbps Full",
                        "ValueName": "100MbpsFull"
                    }
                ],
                "WarningText": null,
                "WriteOnly": false
            },
            {
                "AttributeName": "WakeOnLan",
                "CurrentValue": null,
                "DisplayName": "Wake On LAN",
                "DisplayOrder": 306,
                "HelpText": null,
                "Hidden": false,
                "Immutable": false,
                "MenuPath": "./",
                "Oem": {
                    "Dell": {
                        "@odata.type": "#DellOemAttributeRegistry.v1_0_0.Attributes",
                        "GroupDisplayName": "NIC Configuration",
                        "GroupName": "NICConfig"
                    }
                },
                "ReadOnly": false,
                "ResetRequired": true,
                "Type": "Enumeration",
                "Value": [
                    {
                        "ValueDisplayName": "Disabled",
                        "ValueName": "Disabled"
                    },
                    {
                        "ValueDisplayName": "Enabled",
                        "ValueName": "Enabled"
                    }
                ],
                "WarningText": null,
                "WriteOnly": false
            },
            {
                "AttributeName": "VLanMode",
                "CurrentValue": null,
                "DisplayName": "Virtual LAN Mode",
                "DisplayOrder": 307,
                "HelpText": null,
                "Hidden": false,
                "Immutable": false,
                "MenuPath": "./",
                "Oem": {
                    "Dell": {
                        "@odata.type": "#DellOemAttributeRegistry.v1_0_0.Attributes",
                        "GroupDisplayName": "NIC Configuration",
                        "GroupName": "NICConfig"
                    }
                },
                "ReadOnly": false,
                "ResetRequired": true,
                "Type": "Enumeration",
                "Value": [
                    {
                        "ValueDisplayName": "Disabled",
                        "ValueName": "Disabled"
                    },
                    {
                        "ValueDisplayName": "Enabled",
                        "ValueName": "Enabled"
                    }
                ],
                "WarningText": null,
                "WriteOnly": false
            },
            {
                "AttributeName": "PermitTotalPortShutdown",
                "CurrentValue": null,
                "DisplayName": "Permit Total Port Shutdown",
                "DisplayOrder": 309,
                "HelpText": null,
                "Hidden": false,
                "Immutable": false,
                "MenuPath": "./",
                "Oem": {
                    "Dell": {
                        "@odata.type": "#DellOemAttributeRegistry.v1_0_0.Attributes",
                        "GroupDisplayName": "NIC Configuration",
                        "GroupName": "NICConfig"
                    }
                },
                "ReadOnly": false,
                "ResetRequired": true,
                "Type": "Enumeration",
                "Value": [
                    {
                        "ValueDisplayName": "Disabled",
                        "ValueName": "Disabled"
                    },
                    {
                        "ValueDisplayName": "Enabled",
                        "ValueName": "Enabled"
                    }
                ],
                "WarningText": null,
                "WriteOnly": false
            }
        ],
        "Dependencies": [],
        "Menus": []
    },
    "RegistryVersion": "1.0.0",
    "SupportedSystems": [
        {
            "FirmwareVersion": "1.7.4",
            "ProductName": "PowerEdge R750",
            "SystemId": "451YFT3"
        }
    ]
}
"""
GET_NIC_ATTRS = """
{
    "Attributes": [
        {
            "AttributeName": "WakeOnLan",
            "CurrentValue": null,
            "DisplayName": "Wake On LAN",
            "Value": [
                {
                    "ValueDisplayName": "Disabled",
                    "ValueName": "Disabled"
                },
                {
                    "ValueDisplayName": "Enabled",
                    "ValueName": "Enabled"
                }
            ]
        }
    ]
}
"""
RESPONSE_GET_NIC_ATTR_SPECIFIC = """\
- INFO     - AttributeName: WakeOnLan
- INFO     - CurrentValue: Enabled
- INFO     - DisplayName: Wake On LAN
- INFO     - DisplayOrder: 306
- INFO     - HelpText: None
- INFO     - Hidden: False
- INFO     - Immutable: False
- INFO     - MenuPath: ./
- INFO     - Oem: {'Dell': {'@odata.type': '#DellOemAttributeRegistry.v1_0_0.Attributes', 'GroupDisplayName': 'NIC Configuration', 'GroupName': 'NICConfig'}}
- INFO     - ReadOnly: False
- INFO     - ResetRequired: True
- INFO     - Type: Enumeration
- INFO     - Value: [{'ValueDisplayName': 'Disabled', 'ValueName': 'Disabled'}, {'ValueDisplayName': 'Enabled', 'ValueName': 'Enabled'}]
- INFO     - WarningText: None
- INFO     - WriteOnly: False
"""
RESPONSE_NIC_ATTR_GET_ERROR = "- ERROR    - Was unable to get network attribute info."
RESPONSE_NIC_ATTR_SET_ERROR = "- ERROR    - Was unable to set a network attribute."
RESPONSE_UNSOPPORTED_IDRAC_VERSION = "- ERROR    - Unsupported iDRAC version."
RESPONSE_GET_NIC_ATTR_SPECIFIC_VERSION_UNSUPPORTED = f"""\
{RESPONSE_UNSOPPORTED_IDRAC_VERSION}
{RESPONSE_NIC_ATTR_GET_ERROR}
"""
RESPONSE_GET_NIC_ATTR_SPECIFIC_REGISTRY_FAIL = f"""\
- ERROR    - Was unable to get network attribute registry.
{RESPONSE_NIC_ATTR_GET_ERROR}
"""
RESPONSE_GET_NIC_ATTR_SPECIFIC_LIST_FAIL = f"""\
- ERROR    - Was unable to get NIC attribute(s) info, invalid server response.
{RESPONSE_NIC_ATTR_GET_ERROR}
"""
RESPONSE_SET_NIC_ATTR_ALREADY_OK = "- WARNING  - This attribute already is set to this value. Skipping.\n"
RESPONSE_SET_NIC_ATTR_OK = """\
- INFO     - Patch command to set network attribute values and create next reboot job PASSED.
- WARNING  - No job ID returned in Location header. Changes may not persist after reboot.
- INFO     - Command passed to On server, code return is 200.
- WARNING  - Configuration change submitted but job monitoring was not possible. Please manually verify attribute value persisted after reboot.
"""
RESPONSE_SET_NIC_ATTR_RETRY_OK = f"""\
- ERROR    - Patch command to set network attribute values and create next reboot job FAILED, error code is: 503.
- INFO     - Retrying to send the patch command.
{RESPONSE_SET_NIC_ATTR_OK}"""
RESPONSE_SET_NIC_ATTR_BAD_VALUE = """\
- ERROR    - Value not allowed for this attribute.
- ERROR    - Was unable to set a network attribute.
"""
RESPONSE_SET_NIC_ATTR_INT_MAXED = f"""\
- ERROR    - Value not allowed for this attribute. (Incorrect number bounds)
{RESPONSE_NIC_ATTR_SET_ERROR}
"""
RESPONSE_SET_NIC_ATTR_STR_MAXED = f"""\
- ERROR    - Value not allowed for this attribute. (Incorrect string length)
{RESPONSE_NIC_ATTR_SET_ERROR}
"""
RESPONSE_SET_NIC_ATTR_RETRY_NOT_OK = """\
- ERROR    - Patch command to set network attribute values and create next reboot job FAILED, error code is: 400.
- INFO     - Retrying to send the patch command.
- WARNING  - Job queue already cleared for iDRAC f01-h01-000-r630.host.io, DELETE command will not execute.
- INFO     - Status code 200 returned for POST command to reset iDRAC.
- INFO     - iDRAC will now reset and be back online within a few minutes.
- INFO     - Patch command to set network attribute values and create next reboot job PASSED.
- WARNING  - No job ID returned in Location header. Changes may not persist after reboot.
- WARNING  - Actions resource not found
- INFO     - Command passed to GracefulRestart server, code return is 200.
- INFO     - Polling for host state: Not Down
- INFO     - Command passed to On server, code return is 200.
- WARNING  - Configuration change submitted but job monitoring was not possible. Please manually verify attribute value persisted after reboot.
"""
RESPONSE_GET_NIC_ATTR_FW_BAD = f"""\
{RESPONSE_VENDOR_UNSUPPORTED}
{RESPONSE_UNSOPPORTED_IDRAC_VERSION}
{RESPONSE_NIC_ATTR_GET_ERROR}
"""
RESPONSE_GET_NIC_ATTR_FW_EXC = f"""\
{RESPONSE_FIRMWARE_VERSION_ERROR}
{RESPONSE_UNSOPPORTED_IDRAC_VERSION}
{RESPONSE_NIC_ATTR_GET_ERROR}
"""
MANAGER_INSTANCE_RESP = '{"Jobs":{"@odata.id":"/redfish/v1/Managers/iDRAC.Embedded.1/Jobs"}}'
JOBS_RESP = '{"Members":[]}'

# Job monitoring responses for NIC attribute tests
JOB_STATUS_SCHEDULED = """{
    "Id": "JID_498218641680",
    "JobState": "Scheduled",
    "JobType": "NICConfiguration",
    "Message": "Task successfully scheduled.",
    "Name": "Configure: NIC.Embedded.1-1-1",
    "PercentComplete": 0,
    "StartTime": "TIME_NA",
    "TargetSettingsURI": null
}"""

JOB_STATUS_RUNNING = """{
    "Id": "JID_498218641680",
    "JobState": "Running",
    "JobType": "NICConfiguration",
    "Message": "Job in progress.",
    "Name": "Configure: NIC.Embedded.1-1-1",
    "PercentComplete": 50,
    "StartTime": "2026-04-17T20:00:00",
    "TargetSettingsURI": null
}"""

JOB_STATUS_COMPLETED = """{
    "Id": "JID_498218641680",
    "JobState": "Completed",
    "JobType": "NICConfiguration",
    "Message": "Job completed successfully.",
    "Name": "Configure: NIC.Embedded.1-1-1",
    "PercentComplete": 100,
    "StartTime": "2026-04-17T20:00:00",
    "TargetSettingsURI": null
}"""

JOB_STATUS_FAILED = """{
    "Id": "JID_498218641680",
    "JobState": "Failed",
    "JobType": "NICConfiguration",
    "Message": "Job failed: Unable to apply configuration.",
    "Name": "Configure: NIC.Embedded.1-1-1",
    "PercentComplete": 0,
    "StartTime": "2026-04-17T20:00:00",
    "TargetSettingsURI": null
}"""

# Updated NIC attribute responses for verification (after job completes)
GET_NIC_ATTR_LIST_UPDATED = """\
{
    "Attributes": {
        "WakeOnLan": "Disabled",
        "VLanMode": "Enabled",
        "VLanId": 1,
        "ChipMdl": "0",
        "BlnkLeds": 0,
        "NumberVFAdvertised": 128
    }
}"""

GET_NIC_ATTR_LIST_INTEGER_UPDATED = """\
{
    "@Redfish.Settings":{
        "@odata.context":"/redfish/v1/$metadata#Settings.Settings",
        "@odata.type":"#Settings.v1_3_1.Settings",
        "SettingsObject":{"@odata.id":"/redfish/v1/Chassis/System.Embedded.1/NetworkAdapters/NIC.Embedded.1/NetworkDeviceFunctions/NIC.Embedded.1-1-1/Oem/Dell/DellNetworkAttributes/NIC.Embedded.1-1-1/Settings"},
        "SupportedApplyTimes":[
            "Immediate",
            "AtMaintenanceWindowStart",
            "OnReset",
            "InMaintenanceWindowOnReset"
        ]
    },
    "@odata.context":"/redfish/v1/$metadata#DellAttributes.DellAttributes",
    "@odata.id":"/redfish/v1/Chassis/System.Embedded.1/NetworkAdapters/NIC.Embedded.1/NetworkDeviceFunctions/NIC.Embedded.1-1-1/Oem/Dell/DellNetworkAttributes/NIC.Embedded.1-1-1",
    "@odata.type":"#DellAttributes.v1_0_0.DellAttributes",
    "AttributeRegistry":"NetworkAttributeRegistry_NIC.Embedded.1-1-1",
    "Attributes":{
        "ChipMdl":"BCM5720 A0",
        "PCIDeviceID":"165F",
        "BusDeviceFunction":"04:00:00",
        "MacAddr":"C8:4B:D6:83:16:00",
        "VirtMacAddr":"C8:4B:D6:83:16:00",
        "FCoEOffloadSupport":"Unavailable",
        "iSCSIOffloadSupport":"Unavailable",
        "iSCSIBootSupport":"Unavailable",
        "PXEBootSupport":"Available",
        "FCoEBootSupport":"Unavailable",
        "NicPartitioningSupport":"Unavailable",
        "FlexAddressing":"Unavailable",
        "TXBandwidthControlMaximum":"Unavailable",
        "TXBandwidthControlMinimum":"Unavailable",
        "EnergyEfficientEthernet":"Available",
        "FamilyVersion":"22.00.6",
        "ControllerBIOSVersion":"1.39",
        "EFIVersion":"21.6.29",
        "BlnkLeds":12,
        "BannerMessageTimeout":5,
        "VLanId":1,
        "EEEControl":"Enabled",
        "LinkStatus":"Disconnected",
        "BootOptionROM":"Enabled",
        "LegacyBootProto":"NONE",
        "BootStrapType":"AutoDetect",
        "HideSetupPrompt":"Disabled",
        "LnkSpeed":"AutoNeg",
        "WakeOnLan":"Enabled",
        "VLanMode":"Disabled",
        "PermitTotalPortShutdown":"Disabled"
    },
    "Description":"DellNetworkAttributes represents the Network device attribute details.",
    "Id":"NIC.Embedded.1-1-1",
    "Name":"DellNetworkAttributes"
}
"""

# Expected responses for job monitoring test cases
RESPONSE_SET_NIC_ATTR_WITH_JOB_SUCCESS = """\
- INFO     - Patch command to set network attribute values and create next reboot job PASSED.
- INFO     - Network attribute configuration job created: JID_498218641680
- INFO     - Waiting for configuration job to be scheduled...
- INFO     - Job JID_498218641680 status: Scheduled - Task successfully scheduled.
- INFO     - Command passed to On server, code return is 200.
- INFO     - Monitoring job JID_498218641680 for completion...
- INFO     - JobID: JID_498218641680
- INFO     - Name: Configure: NIC.Embedded.1-1-1
- INFO     - Message: Job completed successfully.
- INFO     - PercentComplete: 100
- INFO     - Verifying attribute value was applied...
- INFO     - ✓ Successfully changed WakeOnLan from Enabled to Disabled
"""

RESPONSE_SET_NIC_ATTR_JOB_FAILED = """\
- INFO     - Patch command to set network attribute values and create next reboot job PASSED.
- INFO     - Network attribute configuration job created: JID_498218641680
- INFO     - Waiting for configuration job to be scheduled...
- INFO     - Job JID_498218641680 status: Scheduled - Task successfully scheduled.
- INFO     - Command passed to GracefulRestart server, code return is 204.
- INFO     - Polling for host state: Not Down
- WARNING  - Command failed to On server, host appears to be already in that state.
- INFO     - Monitoring job JID_498218641680 for completion...
- ERROR    - Configuration job JID_498218641680 did not complete successfully.
- ERROR    - Network attribute changes may not have been applied.
"""

RESPONSE_SET_NIC_ATTR_NO_JOB_ID = """\
- INFO     - Patch command to set network attribute values and create next reboot job PASSED.
- WARNING  - No job ID returned in Location header. Changes may not persist after reboot.
- INFO     - Command passed to On server, code return is 200.
- WARNING  - Configuration change submitted but job monitoring was not possible. Please manually verify attribute value persisted after reboot.
"""

RESPONSE_SET_NIC_ATTR_PRE_REBOOT_FAIL = """\
- INFO     - Patch command to set network attribute values and create next reboot job PASSED.
- INFO     - Network attribute configuration job created: JID_498218641680
- INFO     - Waiting for configuration job to be scheduled...
- INFO     - Job JID_498218641680 status: Failed - Job failed: Unable to apply configuration.
- ERROR    - Configuration job failed before reboot: Job failed: Unable to apply configuration.
"""

RESPONSE_SET_NIC_ATTR_VERIFY_FAILED = """\
- INFO     - Patch command to set network attribute values and create next reboot job PASSED.
- INFO     - Network attribute configuration job created: JID_498218641680
- INFO     - Waiting for configuration job to be scheduled...
- INFO     - Job JID_498218641680 status: Scheduled - Task successfully scheduled.
- INFO     - Command passed to On server, code return is 200.
- INFO     - Monitoring job JID_498218641680 for completion...
- INFO     - JobID: JID_498218641680
- INFO     - Name: Configure: NIC.Embedded.1-1-1
- INFO     - Message: Job completed successfully.
- INFO     - PercentComplete: 100
- INFO     - Verifying attribute value was applied...
- ERROR    - ✗ Attribute value did not persist. Expected: Disabled, Current: Enabled
- ERROR    - Job completed but value not applied. Possible causes: prerequisite not met, validation failure, or firmware issue.
"""

RESPONSE_SET_NIC_ATTR_FALSE_NEGATIVE = """\
- INFO     - Patch command to set network attribute values and create next reboot job PASSED.
- INFO     - Network attribute configuration job created: JID_498218641680
- INFO     - Waiting for configuration job to be scheduled...
- INFO     - Job JID_498218641680 status: Scheduled - Task successfully scheduled.
- INFO     - Command passed to On server, code return is 200.
- INFO     - Monitoring job JID_498218641680 for completion...
- ERROR    - Configuration job JID_498218641680 did not complete successfully.
- ERROR    - Network attribute changes may not have been applied.
- WARNING  - Job reported failure but attribute value is correct (WakeOnLan=Disabled). This may be a false negative.
"""

# VF Limit Validation Test Fixtures
GET_NIC_ATTR_LIST_XXV710_NPARSRIOV = """\
{
    "Attributes":{
        "DeviceName":"Intel(R) Ethernet Network Adapter XXV710",
        "VirtualizationMode":"NPARSRIOV",
        "NumberPCIFunctionsEnabled":"4",
        "NumberVFAdvertised":"64",
        "NumberVFSupported":"128",
        "WakeOnLan":"Disabled"
    }
}
"""

GET_NIC_ATTR_LIST_SINGLE_FUNCTION = """\
{
    "Attributes":{
        "DeviceName":"Intel(R) Ethernet Network Adapter XXV710",
        "VirtualizationMode":"SRIOV",
        "NumberPCIFunctionsEnabled":"1",
        "NumberVFAdvertised":"64",
        "NumberVFSupported":"128",
        "WakeOnLan":"Disabled"
    }
}
"""

GET_NIC_ATTR_LIST_VIRT_MODE_NONE = """\
{
    "Attributes":{
        "DeviceName":"Intel(R) Ethernet 25G 2P XXV710 Adapter",
        "VirtualizationMode":"NONE",
        "NumberPCIFunctionsEnabled":"1",
        "NumberVFAdvertised":"64",
        "NumberVFSupported":"128",
        "WakeOnLan":"Disabled"
    }
}
"""

RESPONSE_SET_NIC_ATTR_VF_LIMIT_XXV710_WARNING = """\
- WARNING  - Attempting to set NumberVFAdvertised to 128 on Intel XXV710.
- WARNING  - Testing has shown that Intel XXV710 NICs are limited to 64 VFs regardless of virtualization mode (SRIOV/NPARSRIOV) or firmware version.
- WARNING  - This operation will likely fail. The hardware limit appears to be 64 VFs maximum.
"""

RESPONSE_SET_NIC_ATTR_VIRT_MODE_NONE = """\
- ERROR    - Cannot set NumberVFAdvertised when VirtualizationMode is NONE (disabled).
- ERROR    - First enable SR-IOV virtualization mode with:
- ERROR    -   --set-nic-attribute NIC.Embedded.1-1-1 --attribute VirtualizationMode --value SRIOV
"""


# Corrected registry with NumberVFAdvertised
GET_NIC_ATTR_REGISTRY_WITH_VF = """
{
    "@odata.context": "/redfish/v1/$metadata#AttributeRegistry.AttributeRegistry",
    "@odata.id": "/redfish/v1/Registries/NetworkAttributesRegistry_NIC.ChassisSlot.8-2-1/NetworkAttributesRegistry_NIC.ChassisSlot.8-2-1.json",
    "@odata.type": "#AttributeRegistry.v1_3_3.AttributeRegistry",
    "Description": "This registry defines a representation of Network Attribute instances",
    "Id": "NetworkAttributesRegistry_NIC.ChassisSlot.8-2-1",
    "Language": "en",
    "Name": "Network Attribute Registry",
    "OwningEntity": "Dell",
    "RegistryEntries": {
        "Attributes": [
            {
                "AttributeName": "NumberVFAdvertised",
                "CurrentValue": null,
                "DisplayName": "PCI Virtual Functions Advertised",
                "DisplayOrder": 304,
                "HelpText": null,
                "Hidden": false,
                "Immutable": false,
                "LowerBound": 0,
                "MenuPath": "./",
                "Oem": {
                    "Dell": {
                        "@odata.type": "#DellOemAttributeRegistry.v1_0_0.Attributes",
                        "GroupDisplayName": "NIC Configuration",
                        "GroupName": "NICConfig"
                    }
                },
                "ReadOnly": false,
                "ResetRequired": true,
                "ScalarIncrement": 16,
                "Type": "Integer",
                "UpperBound": 128,
                "WarningText": null,
                "WriteOnly": false
            },
            {
                "AttributeName": "WakeOnLan",
                "CurrentValue": null,
                "DisplayName": "Wake On LAN",
                "DisplayOrder": 201,
                "HelpText": null,
                "Hidden": false,
                "Immutable": false,
                "MenuPath": "./",
                "Oem": {
                    "Dell": {
                        "@odata.type": "#DellOemAttributeRegistry.v1_0_0.Attributes",
                        "GroupDisplayName": "Device Level Configuration",
                        "GroupName": "DeviceLevelConfig"
                    }
                },
                "ReadOnly": false,
                "ResetRequired": true,
                "Type": "Enumeration",
                "Value": [
                    {
                        "ValueDisplayName": "Disabled",
                        "ValueName": "Disabled"
                    },
                    {
                        "ValueDisplayName": "Enabled",
                        "ValueName": "Enabled"
                    }
                ],
                "WarningText": null,
                "WriteOnly": false
            }
        ]
    },
    "RegistryVersion": "1.0.0",
    "SupportedSystems": []
}
"""


GET_NIC_ATTR_LIST_WITH_VF = """\
{
    "Attributes":{
        "DeviceName":"Intel(R) Ethernet Network Adapter XXV710",
        "VirtualizationMode":"SRIOV",
        "NumberPCIFunctionsEnabled":"1",
        "NumberVFAdvertised":"64",
        "NumberVFSupported":"128",
        "WakeOnLan":"Disabled"
    }
}
"""
