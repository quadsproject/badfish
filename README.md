<p align="center">
  <img src="https://raw.githubusercontent.com/quadsproject/badfish/development/image/badfish-original-licensed.small.png" />
</p>

<h2 align="center">The Out-of-Band Wrangler</h2>

[![Copr build status](https://copr.fedorainfracloud.org/coprs/quadsdev/badfish/package/badfish/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/quadsdev/badfish/package/badfish/)
[![Codecov](https://codecov.io/gh/quadsproject/badfish/branch/master/graph/badge.svg?token=CNJN0CD6GN)](https://codecov.io/gh/quadsproject/badfish)
[![Container image on Quay](https://quay.io/repository/quads/badfish/status "Container image on Quay")](https://quay.io/repository/quads/badfish)
[![Tox](https://github.com/quadsproject/badfish/actions/workflows/tox.yml/badge.svg)](https://github.com/quadsproject/badfish/actions)
[![Lint](https://github.com/quadsproject/badfish/actions/workflows/lint.yml/badge.svg)](https://github.com/quadsproject/badfish/actions)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

   * [About Badfish](#badfish)
      * [Scope](#scope)
      * [Features](#features)
      * [Requirements](#requirements)
      * [Setup](#setup)
         * [Badfish RPM package](#badfish-rpm-package)
         * [Badfish Standalone CLI](#badfish-standalone-cli)
         * [Badfish Container](#badfish-container)
      * [Usage](#usage)
        * [As Python Library](#as-python-library)
        * [Via Podman](#via-podman)
        * [Via Virtualenv](#via-virtualenv)
        * [Via RPM System Package](#via-rpm-system-package)
      * [Common Operations](#common-operations)
         * [Use Environment Variables for Secrets](#using-environment-variables-for-secrets)
         * [Enforcing an OpenStack Director-style interface order](#enforcing-an-openstack-director-style-interface-order)
         * [Enforcing a Foreman-style interface order](#enforcing-a-foreman-style-interface-order)
         * [Enforcing a Custom interface order](#enforcing-a-custom-interface-order)
         * [Forcing a one time boot to a specific device](#forcing-a-one-time-boot-to-a-specific-device)
         * [Forcing a one time boot to a specific mac address](#forcing-a-one-time-boot-to-a-specific-mac-address)
         * [Forcing a one time boot to a specific type](#forcing-a-one-time-boot-to-a-specific-type)
         * [Forcing a one-time boot to PXE](#forcing-a-one-time-boot-to-pxe)
         * [Rebooting a System](#rebooting-a-system)
         * [Power Cycling a System](#power-cycling-a-system)
         * [Power State Control](#power-state-control)
         * [Check Power State](#check-power-state)
         * [Get Power Consumed](#get-power-consumed)
         * [Resetting Dell iDRAC](#resetting-dell-idrac)
         * [Resetting BMC](#resetting-bmc)
         * [BIOS factory reset](#bios-factory-reset)
         * [Check current boot order](#check-current-boot-order)
         * [Toggle boot device](#toggle-boot-device)
         * [Variable number of retries](#variable-number-of-retries)
         * [Firmware inventory](#firmware-inventory)
         * [Delta of firmware inventories](#delta-of-firmware-inventories)
         * [Clear Job Queue](#clear-job-queue)
         * [List Job Queue](#list-job-queue)
         * [Check Job Status](#check-job-status)
         * [Set Bios Password](#set-bios-password)
         * [Remove Bios Password](#remove-bios-password)
         * [List Network Interfaces](#list-network-interfaces)
         * [List Memory](#list-memory)
         * [List Processors](#list-processors)
         * [List Serial Number or Service Tag](#list-serial-number-or-service-tag)
         * [Check Virtual Media](#check-virtual-media)
         * [Mount Virtual Media](#mount-virtual-media)
         * [Unmount Virtual Media](#unmount-virtual-media)
         * [Boot to Virtual Media](#boot-to-virtual-media)
         * [Check Remote Image](#check-remote-image)
         * [Boot to Remote Image](#boot-to-remote-image)
         * [Detach Remote Image](#detach-remote-image)
         * [Get SRIOV mode](#get-sriov-mode)
         * [Set SRIOV mode](#set-sriov-mode)
         * [Get BIOS attributes](#get-bios-attributes)
         * [Get specific BIOS attribute](#get-specific-bios-attribute)
         * [Set BIOS attribute](#set-bios-attribute)
            * [Set multiple BIOS attributes](#set-multiple-bios-attributes)
         * [Change between BIOS and UEFI modes](#change-between-bios-and-uefi-modes)
            * [Querying bootmode](#querying-bootmode)
            * [Setting UEFI mode](#setting-uefi-mode)
            * [Setting BIOS mode](#setting-bios-mode)
         * [Get server screenshot](#get-server-screenshot)
         * [Targets for server configuration profile](#targets-for-server-configuration-profile)
         * [Export server configuration profile](#export-server-configuration-profile)
         * [Import server configuration profile](#import-server-configuration-profile)
         * [Bulk actions via text file with list of hosts](#bulk-actions-via-text-file-with-list-of-hosts)
         * [Verbose Output](#verbose-output)
         * [Log to File](#log-to-file)
         * [Formatted output](#formatted-output)
      * [iDRAC and Data Format](#idrac-and-data-format)
         * [Dell Foreman and PXE Interface](#dell-foreman-and-pxe-interface)
         * [Host type overrides](#host-type-overrides)
      * [Contributing](#contributing)
      * [Contact](#contact)

# Badfish
Badfish is a Redfish-based API tool for managing bare-metal systems via the [Redfish API](https://www.dmtf.org/standards/redfish)

You can read more [about badfish](https://quads.dev/about-badfish/) at the [QUADS](https://quads.dev/) website.

## Scope
Right now Badfish is focused on managing Dell, SuperMicro and HPE systems, but can potentially work with any system that supports the Redfish API.  Functionality may vary depending on the vendor Redfish implementation with Dell systems having the most functionality.

We're mostly concentrated on programmatically enforcing interface/device boot order to accommodate [TripleO](https://docs.openstack.org/tripleo-docs/latest/) based [OpenStack](https://www.openstack.org/) and [OpenShift](https://www.openshift.com/) deployments while simultaneously allowing easy management and provisioning of those same systems via [The Foreman](https://theforeman.org/).  Badfish can be useful as a general standalone, unified vendor IPMI/OOB tool however as support for more vendors is added.

## Features
* Toggle and save a persistent interface/device boot order on remote system
* Support for BIOS and EFI modes for interface/device boot operations
* Perform one-time boot to a specific interface, mac address or device listed for PXE booting
* Enforce a custom interface boot order
* Check current boot order
* Display current power consumption in watts
* Reboot host
* Reset Dell iDRAC
* View, check and clear Dell iDRAC jobs
* Revert to factory settings
* Check/set SRIOV
* Take a remote screenshot of server KVM console activity (Dell only).
* Support tokenized authentication
* Check and set BIOS attributes (e.g. setting UEFI or BIOS mode)
* Get firmware inventory of installed devices supported by the BMC
* Check/ummount virtual media en-masse across a set of systems (SuperMicro only)
* Obtain limited hardware information (CPU, Memory, Interfaces)
* Bulk actions via plain text file with list of hosts for parallel execution
* Logging to a specific path
* Containerized Badfish image

## Requirements
* (Dell) iDRAC7,8,9 or newer
* (Dell) Firmware version ```2.60.60.60``` or higher
* Any Redfish IPMI 2.0 support on non-Dell systems
* BMC administrative account
* Python >= ```3.8``` or [podman](https://podman.io/getting-started/installation) as a container.
* python3-devel >= ```3.8``` (If using standalone or RPM package below).

## Setup
### Badfish RPM package
```bash
dnf copr enable quadsdev/badfish  -y
dnf install badfish -y
```

Active RPM releases:
- All current Fedora releases
- Some older Fedora releases, check the [RPM releases here](https://copr.fedorainfracloud.org/coprs/quadsdev/badfish/)

> [!NOTE]
> RHEL and derivatives (Rocky, Alma, etc) should use [containers](#badfish-container) instead due to missing libs/dependencies.

### Badfish Standalone CLI
```bash
git clone https://github.com/quadsproject/badfish && cd badfish
python3 -m venv bf
source bf/bin/activate
python3 -m pip install --upgrade build
python3 -m build
python3 -m pip install dist/badfish-*.tar.gz
```
> [!TIP]
> This will allow Badfish to be called from the terminal via the `badfish` command
>
> This requires `python3-devel` if you see errors about missing `Python.h`.

### Badfish Container
Perhaps the easiest way to run Badfish is with Podman, you can see more usage details below on [using the Badfish container with Podman](#via-podman).  You can substitute Docker for Podman as well though not all functionality may be actively tested as we prefer Podman.

```
podman pull quay.io/quads/badfish
```

## Usage
Badfish can be consumed in several ways after successful installation. Either via the standalone cli tool or as a python library.
For an extensive use of the cli tool check the [Common Operations](#common-operations) section of this file.

> [!TIP]
> Badfish operates optionally against a YAML configuration file to toggle between key:value pair sets of boot interface/device strings.
> You just need to create your own interface config that matches your needs to easily swap/save interface/device boot ordering or select one-time boot devices.

### As Python Library
If Badfish has been properly installed in the system (RPM package install, setuptools), then the library should be available under your python path therefore it can be imported as a python library to your python project.

```python
from badfish.main import badfish_factory

badfish = await badfish_factory(
    _host=_oob_mgmt,
    _username=_username,
    _password=_password,
)
await badfish.get_boot_devices()
success = await badfish.boot_to(badfish.boot_devices[0]['Name'])
if success:
    print("Change boot device success")
result = await badfish.reboot_server()
if not result:
    print("Failed to reboot system")
```
> [!IMPORTANT]
> Badfish relies heavily on asyncio for executing multiple tasks.
> If you will be using badfish from outside an async function you will have to provide an async event loop and run via `run_until_complete`

### Via Podman
Badfish happily runs in a container image using Podman or Docker (likely, but not actively tested).
```bash
podman pull quay.io/quads/badfish
```
```bash
export BADFISH_USERNAME="my_username"
export BADFISH_PASSWORD="my_password"
podman run -it --rm --dns 1.2.3.4 quay.io/quads/badfish -H mgmt-host01.example.com --reboot-only
```

If you want to pass your user/pass variables only in podman:

```bash
BADFISH_USERNAME=my_username BADFISH_PASSWORD=my_password \
   podman run -it --env BADFISH_USERNAME --env BADFISH_PASSWORD --rm --dns 1.2.3.4 \
   quay.io/quads/badfish -H mgmt-host01.example.com --reboot-only
```

> [!IMPORTANT]
>
> If you are running Badfish against a host inside a VPN to an address without public resolution you must specify your VPN DNS server ip address with `--dns`
>
> If you would like to use a different file for `config/idrac_interfaces.yml` you can map a volume to your modified config with `-v idrac_interfaces.yml:config/idrac_interfaces.yml:Z`

> [!TIP]
> If you want to run any actions that would have output files like `--screenshot` you can map the container root volume to a directory on your local machine where you would like to have those files stored like `-v /tmp/screens:/badfish:Z`

> [!IMPORTANT]
> When mapping a volume to a container make sure to use the `:Z` suffix for appropiate labeling

### Via Virtualenv
[Virtualenv](https://docs.python.org/3/library/venv.html) is a wonderful tool to sandbox running Python applications or to separate Python versions of components from your main system libaries.  Unfortunately it can be problematic with running Badfish directly from the Git repo inside a virtualenv sandbox.

While we strongly recommend using the [podman](#via-podman) method of calling Badfish inside a virtual environment you can still do it directly from the repository via virtualenv but you would need to prepend the call to Badfish with the setting of the `PYTHONPATH` environment variable pointing at the path of your Badfish repository.

```bash
virtualenv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

* You'll need to set `PYTHONPATH` to the BADFISHREPO/src to run this way:

```bash
PYTHONPATH="./src" python3 src/badfish/main.py -h
```

### Via RPM System Package
If you choose to install Badfish via RPM package then it'll be located in `/usr/bin/badfish` and you don't need to do much else beyond know the correct command syntax for your required operations.

> [!NOTE]
> If you plan on using the `idrac_interfaces.yml` file to further customize or define pre-made boot orders you'll want to model your own [based on the repo example file](config/idrac_interfaces.yml).
>
> This file serves as an example but is specific to our internal environments so you'd most likely want to modify it to match your environment and naming conventions.

You can always retrieve our example `idrac_interfaces.yml` file via:

```
curl  https://raw.githubusercontent.com/quadsproject/badfish/master/config/idrac_interfaces.yml --output idrac_interfaces.yml
```

## Common Operations

### Use Environment Variables for Secrets
> [!IMPORTANT]
> While you can pass `-u` and `-p` for user and password env variables are more secure.
>
> `export BADFISH_USERNAME="my_username"`
>
> `export BADFISH_PASSWORD="my_password"`

### Enforcing an OpenStack Director-style interface order
In our performance/scale R&D environments TripleO-based OpenStack deployments require a specific 10/25/40GbE NIC to be the primary boot device for PXE, followed by disk, and then followed by the rest of the interfaces.
```bash
badfish -H mgmt-your-server.example.com  -i config/idrac_interfaces.yml -t director
```

### Enforcing a Foreman-style interface order
Foreman and Red Hat Satellite (as of 6.x based on Foreman) require managed systems to first always PXE from the interface that is Foreman-managed (DHCP/PXE).  If the system is not set to build it will simply boot to local disk.  In our setup we utilize a specific NIC for this interface based on system type.

```bash
badfish -H mgmt-your-server.example.com  -i config/idrac_interfaces.yml -t foreman
```

### Enforcing a Custom interface order
Badfish allows you to supply your own interface order type in addition to `director` and `foreman` modes as defined in `idrac_interfaces.yml`

* Supply your own distinct string in the first part of the key value (split by `_`)
* Refer to it via the string name
* Consequently [host type overrides](#host-type-overrides) can also be leveraged

We will use the custom interface order called **ocp5beta** as an example.

_Example_ any system you want to boot with a certain custom interface order.

```
ocp5beta_fc640_interfaces: NIC.Slot.2-4,NIC.Slot.2-1,NIC.Slot.2-2,NIC.Slot.2-3
```

_Example_ a rack of systems you want to boot with a certain custom interface order.


```
ocp5beta_f21_fc640_interfaces: NIC.Slot.2-4,NIC.Slot.2-1,NIC.Slot.2-2,NIC.Slot.2-3
```

_Example_ a specific system you want to boot with a certain custom interface order

```
ocp5beta_f21_h23_fc640_interfaces: NIC.Slot.2-4,NIC.Slot.2-1,NIC.Slot.2-2,NIC.Slot.2-3
```

Now you can run Badfish against the custom interface order type you have defined, refer to the [custom overrides](#host-type-overrides) on further usage examples.

```bash
src/main.py --host-list /tmp/hosts -u root -p password -i config/idrac_interfaces.yml -t ocp5beta
```


### Forcing a one time boot to a specific device
To force systems to perform a one-time boot to a specific device on the next subsequent reboot you can use the ```--boot-to``` option and pass as an argument the device you want the one-time boot to be set to. This will change the one time boot BIOS attributes OneTimeBootMode and OneTimeBootSeqDev and on the next reboot it will attempt to PXE boot or boot from that interface string.  You can obtain the device list via the `--check-boot` directive below.
```bash
badfish -H mgmt-your-server.example.com --boot-to NIC.Integrated.1-3-1
```

### Forcing a one time boot to a specific mac address
To force systems to perform a one-time boot to a specific mac address on the next subsequent reboot you can use the ```--boot-to-mac``` option and pass as an argument the device mac address for a specific NIC that you want the one-time boot to be set to. This will change the one time boot BIOS attributes OneTimeBootMode and OneTimeBootSeqDev and on the next reboot it will attempt to PXE boot or boot from that interface.
```bash
badfish -H mgmt-your-server.example.com --boot-to-mac A9:BB:4B:50:CA:54
```

### Forcing a one time boot to a specific type
To force systems to perform a one-time boot to a specific type on the next subsequent reboot you can use the ```--boot-to-type``` option and pass as an argument the device type, as defined on the interfaces yaml, that you want the one-time boot to be set to. For this action you must also include the path to your interfaces yaml. This will change the one time boot BIOS attributes OneTimeBootMode and OneTimeBootSeqDev and on the next reboot it will attempt to PXE boot or boot from the first interface defined for that host type on the interfaces yaml file.
```bash
badfish -H mgmt-your-server.example.com  -i config/idrac_interfaces.yml --boot-to-type foreman
```

**Note** `--boot-to`, `--boot-to-type`, and `--boot-to-mac` require you to manually perform a reboot action, these simply just batch what the system will boot to on the next boot.  For this you can use either `--power-cycle` or `--reboot-only`.

### Forcing a one-time boot to PXE
To force systems to perform a one-time boot to PXE, simply pass the `--pxe` flag to any of the commands above, by default it will pxe off the first available device for PXE booting.  This is equivalent to the ipmitool command `chassis bootdev pxe options=persistent` and should be used with SuperMicro/HPE systems or non-Dell systems that support a minimal IPMI 2.0 specification.

For Dell systems please use either  `--boot-to`, `--boot-to-mac` or `--boot-to-type` for temporary PXE to a specific interface or change the boot order permanently to achieve your desired effect.
```bash
badfish -H mgmt-your-server.example.com  -i config/idrac_interfaces.yml --pxe
```

### Rebooting a system
In certain cases you might need to only reboot the host, for this case we included the ```--reboot-only``` flag which will force a GracefulRestart on the target host. Note that this option is not to be used with any other option.
```bash
badfish -H mgmt-your-server.example.com --reboot-only
```

### Power cycling a system
For a hard reset you can use ```--power-cycle``` flag which will run a ForceOff instruction on the target host. Note that this option is not to be used with any other option.
```bash
badfish -H mgmt-your-server.example.com --power-cycle
```

### Power State Control
You can also turn a server on or off by using options `--power-on` and `--power-off` respectively.
```bash
badfish -H mgmt-your-server.example.com --power-on
```

### Check Power State
For checking the current power state of a server you can run badfish with the `--power-state` option.
```bash
badfish -H mgmt-your-server.example.com --power-state
```
Partial Output:
```
- INFO     - Power state for mgmt-your-server.example.com: On
```

### Get Power Consumed
This displays the current power usage for Dell / Supermicro server(s).
```bash
badfish -H mgmt-your-server.example.com -u root -p --get-power-consumed
```
Partial Output:
```
- INFO     - Current watts consumed: 213
```

### Resetting Dell iDRAC
For the replacement of `racadm racreset`, the optional argument `--racreset` was added. When this argument is passed to ```badfish```, a graceful restart is triggered on the iDRAC itself.
```bash
badfish -H mgmt-your-server.example.com --racreset
```
* You can also specify `--racreset --wait` and Badfish will poll the iDrac for it to complete and keep you updated on progress. 


> [!NOTE]
> Dell specific command, for Supermicro servers there is an equivalent of `--bmc-reset`

### Resetting BMC
For the replacement of `ipmitool bmc reset` or `ipmiutil reset`, the optional argument `--bmc-reset` was added. When this argument is passed to ```badfish```, a graceful restart is triggered on the BMC itself.
```bash
badfish -H mgmt-your-server.example.com --bmc-reset
```
> [!NOTE]
> Supermicro specific command, for Dell servers there is an equivalent of `--racreset`

### BIOS factory reset
> [!CAUTION]
> Use this carefully, vendor defaults differ and may be disruptive. Do not use this in the Scale Lab or ALIAS.

You can restore BIOS default settings by calling Badfish with the option `--factory-reset`.
```bash
badfish -H mgmt-your-server.example.com --factory-reset
```

### Check current boot order
To check the current boot order of a specific host you can use the ```--check-boot``` option which will return an ordered list of boot devices. Additionally you can pass the ```-i``` option which will in turn print on screen what type of host does the current boot order match as those defined on the interfaces yaml.
```bash
badfish -H mgmt-your-server.example.com  -i config/idrac_interfaces.yml --check-boot
```

### Toggle boot device
If you would like to enable or disable a boot device you can use ```--toggle-boot-device``` argument which takes the device name as input and will toggle the `Enabled` state from True to False and vice versa.
```bash
badfish -H mgmt-your-server.example.com --toggle-boot-device NIC.Integrated.1-3-1```
```

### Variable number of retries
At certain points during the execution of ```badfish``` the program might come across a non responsive resources and will automatically retry to establish connection. We have included a default value of 15 retries after failed attempts but this can be customized via the ```--retries``` optional argument which takes as input an integer with the number of desired retries.
```bash
badfish -H mgmt-your-server.example.com  -i config/idrac_interfaces.yml -t foreman --retries 20
```

### Firmware inventory
If you would like to get a detailed list of all the devices supported by the BMC you can run ```badfish``` with the ```--firware-inventory``` option which will return a list of devices with additional device info.
```bash
badfish -H mgmt-your-server.example.com --firmware-inventory
```

### Delta of firmware inventories
If you would like to get a delta between firmware inventories of two servers, you can do so with the `--delta` option. This option takes a second host address as its argument. Only the firmware that's on both servers and has different versions will get displayed.
```bash
badfish -H mgmt-your-server.example.com --firmware-inventory --delta mgmt-your-other-server.example.com
```

### Clear Job Queue
If you would like to clear all the jobs that are queued on the remote BMC you can run ```badfish``` with the ```--clear-jobs``` option which query for all active jobs in the job queue and will post a request to clear the queue.
```bash
badfish -H mgmt-your-server.example.com --clear-jobs
```

You can also force the clearing of Dell iDRAC job queues by passing the `--force` option.

```bash
badfish -H mgmt-your-server.example.com --clear-jobs --force
```

### List Job Queue
If you would like to list all active jobs that are queued on the remote BMC you can run ```badfish``` with the ```--ls-jobs``` option which query for all active jobs in the job queue and will return a list with all active items.
```bash
badfish -H mgmt-your-server.example.com --ls-jobs
```

### Check Job Status
If you would like to the status of an existing LifeCycle controller job you can run ```badfish``` with the ```--check-job``` option and passing the job id which can be obtained via ```--ls-jobs```. This will return a detail of the specific job with status and percentage of completion.
```bash
badfish -H mgmt-your-server.example.com --check-job JID_340568202796
```

### Set Bios Password
If you would like to set the bios password you can run ```badfish``` with the ```--set-bios-password``` option and passing the new password with ```--new-password```. If a password is already set you must pass this with ```--old-password``` otherwise optional.
```bash
badfish -H mgmt-your-server.example.com -u root --set-bios-password --new-password new_pass --old-password old_pass
```

### Remove Bios Password
If you would like to remove the bios password you can run ```badfish``` with the ```--remove-bios-password``` option and passing the existing password with ```--old-password```.
```bash
badfish -H mgmt-your-server.example.com -u root --remove-bios-password --old-password old_pass
```

### List Network Interfaces
For getting a list of network interfaces with individual metadata for each you can run ```badfish``` with the ```--ls-interfaces``` option.
```bash
badfish -H mgmt-your-server.example.com --ls-interfaces
```

### List Memory
For getting a detailed list of memory devices you can run ```badfish``` with the ```--ls-memory``` option.
```bash
badfish -H mgmt-your-server.example.com --ls-memory
```

### List Processors
For getting a detailed list of processors you can run ```badfish``` with the ```--ls-processors``` option.
```bash
badfish -H mgmt-your-server.example.com --ls-processors
```

### List Serial Number or Service Tag
For getting the system's serial number or on Dell servers the service tag (equivalent to `racadm getsvctag`) you can run ```badfish``` with the ```--ls-serial``` option.
```bash
badfish -H mgmt-your-server.example.com --ls-serial
```

### Check Virtual Media
If you would like to check for any active virtual media you can run ```badfish``` with the ```--check-virtual-media``` option which query for all active virtual devices.
```bash
badfish -H mgmt-your-server.example.com --check-virtual-media
```

### Mount Virtual Media
If you would like to mount an ISO from network you can run ```badfish``` with the ```--mount-virtual-media``` option which post a request for mounting the ISO virtual media (Virtual CD). Full address to the ISO is needed as an argument.
```bash
badfish -H mgmt-your-server.example.com --mount-virtual-media http://storage.example.com/folder/linux.iso
```

### Unmount Virtual Media
If you would like to unmount all active virtual media you can run ```badfish``` with the ```--unmount-virtual-media``` option which post a request for unmounting all active virtual devices.
```bash
badfish -H mgmt-your-server.example.com --unmount-virtual-media
```

### Boot to Virtual Media
If you would like to boot to virtual media (Virtual CD) you can run ```badfish``` with the ```--boot-to-virtual-media``` option which sets the onetime next boot device to virtual CD.
```bash
badfish -H mgmt-your-server.example.com --boot-to-virtual-media
```

### Check Remote Image
If you would like to check the attach status of a remote ISO in DellOSDeployment service you can run ```badfish``` with the ```--check-remote-image``` option.
```bash
badfish -H mgmt-your-server.example.com --check-remote-image
```
> [!NOTE]
> This is only supported on DELL devices.

### Boot to Remote Image
If you would like to boot to a remote ISO on NFS with DellOSDeployment service you can run ```badfish``` with the ```--boot-remote-image``` option which will attach the image and reboot the server to it. Expects the NFS path to the ISO as the argument.
```bash
badfish -H mgmt-your-server.example.com --boot-remote-image nfs-storage.example.com:/mnt/folder/linux.iso
```
> [!NOTE]
> This is only supported on DELL devices.

### Detach Remote Image
If you would like to detach an ISO from DellOSDeployment service you can run ```badfish``` with the ```--detach-remote-image``` option.
```bash
badfish -H mgmt-your-server.example.com --detach-remote-image
```
> [!NOTE]
> This is only supported on DELL devices.

### Get SRIOV mode
For checking if the global SRIOV mode is enabled you can use ```--get-sriov```
```bash
badfish -H mgmt-your-server.example.com --get-sriov
```
> [!NOTE]
> This is only supported on DELL devices.

### Set SRIOV mode
For changing the mode of the SRIOV glabal BIOS attribute, we have included 2 new arguments.
In case the setting is in disabled mode, you can enable it by passing ```--enable-sriov```
```bash
badfish -H mgmt-your-server.example.com --enable-sriov
```
On the contrary, if you would like to disable the SRIOV mode, you can now pass ```--disable-sriov```
```bash
badfish -H mgmt-your-server.example.com --disable-sriov
```
> [!NOTE]
> This is only supported on DELL devices.

### Get FQDDs for all nics
To get a list of all FQDDs for all NICs on the server you can run badfish with ```--get-nic-fqdds```.
```bash
badfish -H mgmt-your-server.example.com --get-nic-fqdds
```

### Get NIC attributes
To get a list of all NIC attributes we can potentially modify (some might be set as read-only), you can run badfish with ```--get-nic-attribute``` passing the desired FQDD and this will return a list off all NIC attributes with their current value set.
```bash
badfish -H mgmt-your-server.example.com --get-nic-attribute NIC.Integrated.1-1-1
```

### Set NIC attribute
> [!WARNING]
> This action will trigger a reboot of the server to apply the changes. Changes will be reflected after the reboot is completed.

To change the value of a NIC attribute you can use ```--set-nic-attribute``` with the desired FQDD, passing both ```--attribute``` and desired ```--value```.
```bash
badfish -H mgmt-your-server.example.com --set-nic-attribute NIC.Integrated.1-1-1 --attribute LegacyBootProto --value PXE
```

### Get BIOS attributes
To get a list of all BIOS attributes we can potentially modify (some might be set as read-only), you can run badfish with ```--get-bios-attribute``` alone and this will return a list off all BIOS attributes with their current value set.
```bash
badfish -H mgmt-your-server.example.com --get-bios-attribute
```

### Get specific BIOS attribute
In case you would like to get a more detailed view on the parameters for a BIOS attribute you can run ```--get-bios-attribute``` including the specific name of the attribute via ```--attribute```.
```bash
badfish -H mgmt-your-server.example.com --get-bios-attribute --attribute ProcC1E
```

### Set BIOS attribute
To change the value of a bios attribute you can use ```--set-bios-attribute``` passing both ```--attribute``` and ```--value```.
```bash
badfish -H mgmt-your-server.example.com --set-bios-attribute --attribute ProcC1E --value Enabled
```
#### Set multiple BIOS attributes
To set multiple BIOS attributes in one call, repeat ```--attribute-value``` with an ```attribute=value``` pair each time. All attributes are applied in a single operation and one reboot.
```bash
badfish -H mgmt-your-server.example.com --set-bios-attribute --attribute-value ProcC1E=Enabled --attribute-value BootMode=Uefi
```
> [!NOTE]
> You can get the list of allowed values you can pass for that attribute by looking at the attribute details via ```--get-bios-attribute``` for that specific one.

### Change between BIOS and UEFI modes
* Building on the get/set bios attribute commands above here's how you can manage BIOS and UEFI modes on supported servers.

> [!NOTE]
> This is only supported on Dell devices.

#### Querying bootmode
* First determine what bootmode state your server is using before proceeding.
```bash
badfish -H mgmt-your-server.example.com --get-bios-attribute --attribute BootMode
```
#### Setting UEFI mode
```bash
badfish -H mgmt-your-server.example.com --set-bios-attribute --attribute BootMode --value Uefi
```
### Setting BIOS mode
```bash
badfish -H mgmt-your-server.example.com --set-bios-attribute --attribute BootMode --value Bios
```

> [!IMPORTANT]
> Like all batch-driven actions this takes a reboot and time to process so be patient.
> You should also give it time to process before checking result via `--get-bios-attribute --attribute BootMode` as it could be cached for a minute or two after processing.

### Get server screenshot
If you would like to get a screenshot with the current state of the server you can now run badfish with ```--screenshot``` which will capture this and store it in the current directory in png format.
```bash
badfish -H mgmt-your-server.example.com --screenshot
```

### Targets for server configuration profile
If you want to get a list of allowed targets for SCP export or import you can get that with the `--get-scp-targets` command, takes either `Export` or `Import` as an argument.
```
badfish -H mgmt-your-server.example.com --get-scp-targets (Export | Import)
```
> [!NOTE]
> This is only supported on Dell devices.


### Export server configuration profile
If you would like to export a SCP as a JSON file for either some specific targets or all of them, you can run badfish with `--export-scp` and specify a path where the config should be saved to with its argument. Targets can be specified with `--scp-targets` flag that takes a comma separated list of targets as an argument. Read only arguments can be included with the `--scp-include-read-only` flag.
```
badfish -H mgmt-your-server.example.com --export-scp "./" --scp-targets IDRAC,BIOS --scp-include-read-only
```
> [!NOTE]
> This is only supported on Dell devices.

### Import server configuration profile
If you would like to import a SCP in a JSON file for either some specific targets or all of them, you can run badfish with `--import-scp`. Targets can be specified with `--scp-targets` flag that takes a comma separated list of targets as an argument. Command will reboot the server and return it to a state at the launch start of import.
```
badfish -H mgmt-your-server.example.com --import-scp "./example_export.json" --scp-targets IDRAC,BIOS
```
> [!NOTE]
> This is only supported on Dell devices.

### Bulk actions via text file with list of hosts
In the case you would like to execute a common badfish action on a list of hosts, you can pass the optional argument ```--host-list``` in place of ```-H``` with the path to a text file with the hosts you would like to action upon and any addtional arguments defining a common action for all these hosts.
```bash
badfish --host-list /tmp/bad-hosts --clear-jobs
```

### Verbose output
If you would like to see a more detailed output on console you can use the ```--verbose``` option and get a additional debug logs. > [!NOTE] this is the default log level for the ```--log``` argument.
```bash
badfish -H mgmt-your-server.example.com  -i config/idrac_interfaces.yml -t foreman --verbose
```

### Log to file
If you would like to log the output of ```badfish``` you can use the ```--log``` option and pass the path to where you want ```badfish``` to log it's output to.
```bash
badfish -H mgmt-your-server.example.com  -i config/idrac_interfaces.yml -t foreman --log /tmp/bad.log
```

### Formatted output
If you would like to easier query some information listed by badfish, you can tell badfish to output in either JSON or YAML. Formatted output is also supported for bulk actions with `--host-list`. Supported commands that list some information are:
- `--ls-*`
- `--firmware-inventory`
- `--get-bios-attribute` (also works with specified attribute by `--attribute` after)
- `--check-boot`
- `--check-virtual-media`
- `--power-state`.
```bash
badfish -H mgmt-your-server.example.com --output json/yaml --firmware-inventory
```

## iDRAC and Data Format

### Dell Foreman and PXE Interface
Your usage may vary, this is what our configuration looks like via ```config/idrac_interfaces.yml```

* Note that these are BIOS mode, EFI interfaces may be different and not yet recorded everywhere for our uses.

| Machine Type | Network Interface      |
| ------------ | ----------------------:|
| Dell fc640   |  NIC.Integrated.1-1-1  |
| Dell r620	   |  NIC.Integrated.1-3-1  |
| Dell r630    |  NIC.Slot.2-1-1        |
| Dell r930    |  NIC.Integrated.1-3-1  |
| Dell r720xd  |  NIC.Integrated.1-3-1  |
| Dell r730xd  |  NIC.Integrated.1-3-1  |
| Dell r740xd  |  NIC.Integrated.1-3-1  |
| Dell r640    |  NIC.Integrated.1-1-1  |
| Dell r650    |  NIC.Integrated.1-1-1  |
| Dell r660    |  NIC.PxeDevice.1-1     |
| Dell r750    |  NIC.Integrated.1-1-1  |

### Host type overrides
Every other method that requires passing the `-i` argument, is going to parse the key strings from this and look for the most adequate candidate for the given FQDN.
We format the key strings with the following criteria:
```
{host_type}_[{rack}_[{ULocation}_[{blade}_]]]{model}_interfaces
```
Additionally we can do a blade only override like:
```
{host_type}_[{blade}_]{model}_interfaces
```
With rack, ULocation and blade being optional in a hierarchical fashion otherwise mandatory with the exception of the blade, as we can now use the blade independently from rack and ULocation. host_type and model values are always mandatory.

#### Example for director type overrides:

| Keys defined on interfaces yaml | FQDN | Use boot order |
| :------------------------------ |:----:| --------------:|
| director_r620_interfaces         | mgmt-f21-h17-000-r620.domain.com | NO             |
| director_f21_r620_interfaces     | mgmt-f21-h17-000-r620.domain.com | NO             |
| director_f21_h17_r620_interfaces | mgmt-f21-h17-000-r620.domain.com | YES            |

| Keys defined on interfaces yaml | FQDN | Use boot order |
| :------------------------------ |:----:| --------------:|
| director_r620_interfaces         | mgmt-f21-h18-000-r620.domain.com | NO             |
| director_f21_r620_interfaces     | mgmt-f21-h18-000-r620.domain.com | YES            |
| director_f21_h17_r620_interfaces | mgmt-f21-h18-000-r620.domain.com | NO             |

| Keys defined on interfaces yaml | FQDN | Use boot order |
| :------------------------------ |:----:| --------------:|
| director_r620_interfaces         | mgmt-f22-h17-000-r620.domain.com | YES            |
| director_f21_r620_interfaces     | mgmt-f22-h17-000-r620.domain.com | NO             |
| director_f21_h17_r620_interfaces | mgmt-f22-h17-000-r620.domain.com | NO             |

## Contributing

Please refer to our contributing [guide](CONTRIBUTING.md).

* Here is some useful documentation
  - [Creating a pull request](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request)
  - [Keeping a cloned fork up to date](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/syncing-a-fork)

## Contact

* You can find us on IRC in `#badfish` (or `#quads`) on `irc.libera.chat` if you have questions or need help.
* [Click here](https://https://web.libera.chat/?channels=#quads) to join in your browser.

