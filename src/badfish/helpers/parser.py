import argparse

from badfish import __version__
from badfish.config import RETRIES, TIMEOUT


def _positive_int(value):
    try:
        ivalue = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{value!r} is not an integer")
    if ivalue <= 0:
        raise argparse.ArgumentTypeError(f"{value} must be a positive integer")
    return ivalue


def create_parser():
    parser = argparse.ArgumentParser(
        prog="badfish",
        description="Tool for managing server hardware via the Redfish API.",
        allow_abbrev=False,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("-H", "--host", help="BMC host address")
    parser.add_argument("-u", help="BMC username")
    parser.add_argument("-p", help="BMC password")
    parser.add_argument("-i", help="Path to interfaces yaml", default=None)
    parser.add_argument("-t", help="Type of host as defined on interfaces yaml")
    parser.add_argument("-l", "--log", help="Optional argument for logging results to a file")
    parser.add_argument(
        "-o",
        "--output",
        choices=["json", "yaml"],
        help="Optional argument for choosing a special output format (json/yaml), otherwise our normal format is used.",
    )
    parser.add_argument(
        "-f",
        "--force",
        dest="force",
        action="store_true",
        help="Optional argument for forced clear-jobs",
    )
    parser.add_argument(
        "--host-list",
        help="Path to a plain text file with a list of hosts",
        default=None,
    )
    parser.add_argument("--pxe", help="Set next boot to one-shot boot PXE", action="store_true")
    parser.add_argument("--boot-to", help="Set next boot to one-shot boot to a specific device")
    parser.add_argument(
        "--boot-to-type",
        help="Set next boot to one-shot boot to a specific type as defined on interfaces yaml",
    )
    parser.add_argument(
        "--boot-to-mac",
        help="Set next boot to one-shot boot to a specific MAC address on the target",
    )
    parser.add_argument("--reboot-only", help="Flag for only rebooting the host", action="store_true")
    parser.add_argument(
        "--power-cycle",
        help="Flag for sending ForceOff instruction to the host",
        action="store_true",
    )
    parser.add_argument(
        "--power-state",
        help="Get power state",
        action="store_true",
    )
    parser.add_argument(
        "--power-on",
        help="Power on host",
        action="store_true",
    )
    parser.add_argument(
        "--power-off",
        help="Power off host",
        action="store_true",
    )
    parser.add_argument(
        "--get-power-consumed",
        help="Get current consumed watts on host(s)",
        action="store_true",
    )
    parser.add_argument(
        "--racreset",
        help="(Dell iDRAC) Flag for Dell iDRAC reset",
        action="store_true",
    )
    parser.add_argument(
        "--wait",
        help="(Dell iDRAC) Wait for Dell iDRAC to be responsive after reset",
        action="store_true",
    )
    parser.add_argument("--bmc-reset", help="Flag for BMC reset", action="store_true")
    parser.add_argument(
        "--factory-reset",
        help="Reset BIOS to default factory settings",
        action="store_true",
    )
    parser.add_argument(
        "--check-boot",
        help="Flag for checking the host boot order",
        action="store_true",
    )
    parser.add_argument(
        "--toggle-boot-device",
        help="Change the enabled status of a boot device",
        default="",
    )
    parser.add_argument(
        "--firmware-inventory",
        help="Get firmware inventory",
        action="store_true",
    )
    parser.add_argument(
        "--delta",
        help="Address of the other host between which the delta should be made",
        default="",
    )
    parser.add_argument(
        "--clear-jobs",
        help="Clear any scheduled jobs from the queue",
        action="store_true",
    )
    parser.add_argument(
        "--check-job",
        help="Check a job status and details",
    )
    parser.add_argument(
        "--ls-jobs",
        help="List any scheduled jobs in queue",
        action="store_true",
    )
    parser.add_argument(
        "--ls-interfaces",
        help="List Network interfaces",
        action="store_true",
    )
    parser.add_argument(
        "--ls-processors",
        help="List Processor Summary",
        action="store_true",
    )
    parser.add_argument(
        "--ls-gpu",
        help="List GPU's on host",
        action="store_true",
    )
    parser.add_argument(
        "--ls-memory",
        help="List Memory Summary",
        action="store_true",
    )
    parser.add_argument(
        "--ls-serial",
        help="List 'Serial Number'/'Service Tag'",
        action="store_true",
    )
    parser.add_argument(
        "--check-virtual-media",
        help="Check for mounted iso images",
        action="store_true",
    )
    parser.add_argument(
        "--mount-virtual-media",
        help="Mount iso image to virtual CD. Arguments should be the address/path to the iso.",
        default="",
    )
    parser.add_argument(
        "--unmount-virtual-media",
        help="Unmount any mounted iso images",
        action="store_true",
    )
    parser.add_argument(
        "--boot-to-virtual-media",
        help="Boot to virtual media (Cd).",
        action="store_true",
    )
    parser.add_argument(
        "--check-remote-image",
        help="Check the attach status of network ISO.",
        action="store_true",
    )
    parser.add_argument(
        "--boot-remote-image",
        help="Boot to network ISO, through NFS, takes two arguments 'hostname:path' and name of the ISO 'linux.iso'.",
        default="",
    )
    parser.add_argument(
        "--detach-remote-image",
        help="Remove attached network ISO.",
        action="store_true",
    )
    parser.add_argument(
        "--get-sriov",
        help="Gets global SRIOV mode state",
        action="store_true",
    )
    parser.add_argument(
        "--enable-sriov",
        help="Enables global SRIOV mode",
        action="store_true",
    )
    parser.add_argument(
        "--disable-sriov",
        help="Disables global SRIOV mode",
        action="store_true",
    )
    parser.add_argument(
        "--get-bios-attribute",
        help="Get a BIOS attribute value",
        action="store_true",
    )
    parser.add_argument(
        "--set-bios-attribute",
        help="Set a BIOS attribute value",
        action="store_true",
    )
    parser.add_argument(
        "--attribute",
        help="BIOS attribute name",
        default="",
    )
    parser.add_argument(
        "--value",
        help="BIOS attribute value",
        default="",
    )
    parser.add_argument(
        "--set-bios-password",
        help="Set the BIOS password",
        action="store_true",
    )
    parser.add_argument(
        "--remove-bios-password",
        help="Removes BIOS password",
        action="store_true",
    )
    parser.add_argument(
        "--new-password",
        help="The new password value",
        default="",
    )
    parser.add_argument(
        "--old-password",
        help="The old password value",
        default="",
    )
    parser.add_argument(
        "--screenshot",
        help="Take a screenshot of the system an store it in jpg format",
        action="store_true",
    )
    parser.add_argument("-v", "--verbose", help="Verbose output", action="store_true")
    parser.add_argument(
        "-r",
        "--retries",
        help="Number of retries for executing actions.",
        default=RETRIES,
    )
    parser.add_argument(
        "--timeout",
        help="Timeout in seconds for each REST API call (must be > 0).",
        default=TIMEOUT,
        type=_positive_int,
    )
    parser.add_argument(
        "--insecure",
        help="Disable SSL/TLS certificate verification (insecure, use only for testing)",
        action="store_true",
    )
    parser.add_argument(
        "--get-scp-targets",
        help="(Dell iDRAC) Get allowable target values to export or import with iDRAC SCP."
        " Choices=['Export', 'Import']",
        choices=["Export", "Import"],
        default="",
    )
    parser.add_argument(
        "--scp-targets",
        help="(Dell iDRAC) Comma separated targets which configs should be exported with Dell iDRAC SCP.",
        default="ALL",
    )
    parser.add_argument(
        "--scp-include-read-only",
        help="(Dell iDRAC) Flag for including read only attributes in Dell iDRAC SCP export.",
        action="store_true",
    )
    parser.add_argument(
        "--export-scp",
        help="(Dell iDRAC) Export system config using Dell iDRAC SCP, argument specifies where file should be saved.",
        default="",
    )
    parser.add_argument(
        "--import-scp",
        help="(Dell iDRAC) Import system config using iDRAC SCP, argument specifies which JSON file"
        " contains config that should be imported.",
        default="",
    )
    parser.add_argument(
        "--get-nic-fqdds",
        help="List FQDDs for all NICs.",
        action="store_true",
    )
    parser.add_argument(
        "--get-nic-attribute",
        help="Get a NIC attribute values, specify a NIC FQDD.",
        default="",
    )
    parser.add_argument(
        "--set-nic-attribute",
        help="Set a NIC attribute value",
        default="",
    )
    return parser


def parse_arguments(argv=None):
    """Parse command line arguments using the configured parser."""
    parser = create_parser()
    return vars(parser.parse_args(argv))
