# ServerTech iPDU management and control

## Description

ServerTech iPDU PRO1 and PRO2 PDU designs provide a remote management interface
called JAWS. This tool provides a simple way to manage these PDUs via the JAWS
interface without the user needing to how to use the JAWS interface.

## Getting Started

### Prerequisites

* python3
* IP connectivity to iPDU controller

### Installation

1. Create and activate python3 virtual environment

```bash
# python3 -m venv ipdu
# cd ipdu
# . bin/activate
```

2. Clone ServerTech iPDU tool

```bash
# git clone git@github.com:Cray-HPE/servertech-pdu.git

or

# git clone https://github.com/Cray-HPE/servertech-pdu.git
```

3. Install local requirements.

```bash
# cd servertech-pdu
# pip install -r requirements.txt
```

### Usage

```bash
# ./servertech_pdu.py --help
usage: servertech_pdu.py [-h] [--on] [--off] [--reboot] [--status]
                         [--pdus PDUS] [--outlets OUTLETS] [--groups GROUPS]
                         [--user USER] [--passwd PASSWD] [--file FILE]
                         [--version]

Server Tech iPDU control.

optional arguments:
  -h, --help         show this help message and exit
  --on               turn selected outlets/groups On
  --off              turn selected outlets/groups Off
  --reboot           reboot selected outlets/groups
  --status           get status of outlet or group
  --pdus PDUS        iPDU controller hostnames, IPv4 addrs, and/or IPv6 addrs
  --outlets OUTLETS  target outlets
  --groups GROUPS    target groups
  --user USER        Jaws user name
  --passwd PASSWD    Jaws password
  --file FILE        power sequence file in json, command line overrides
                     values in the file
  --version          print script version information and exit
```

#### Query single outlet status
```bash
# ./servertech_pdu.py --pdus 10.254.1.24 --user admn --status --outlets AA1
Enter password for admn: 

10.254.1.24                              AA1    On
```
#### Query multiple outlet status
```bash
# ./servertech_pdu.py --pdus 10.254.1.24 --user admn --status --outlets AA1,AA2,AA3,BA10,BA11,BA12
Enter password for admn: 

10.254.1.24                              AA1    On
10.254.1.24                              AA2    On
10.254.1.24                              AA3    On
10.254.1.24                              BA10   On
10.254.1.24                              BA11   On
10.254.1.24                              BA12   On
```
#### Query outlet status of a single group
```bash
# ./servertech_pdu.py --pdus 10.254.1.24 --user admn --status --groups Managed
Enter password for admn: 

10.254.1.24                              BA10   On
10.254.1.24                              BA11   On
10.254.1.24                              BA12   On
10.254.1.24                              BA13   On
```
#### Query outlet status of multiple groups
```bash
# ./servertech_pdu.py --pdus 10.254.1.24 --user admn --status --groups Managed,CSM
Enter password for admn: 

10.254.1.24                              AA10   On
10.254.1.24                              AA11   On
10.254.1.24                              AA12   On
10.254.1.24                              BA10   On
10.254.1.24                              BA11   On
10.254.1.24                              BA12   On
10.254.1.24                              BA13   On
```
#### Query outlet status of groups and outlets
```bash
# ./servertech_pdu.py --pdus 10.254.1.24 --user admn --status --groups CSM --outlets BA10,BA12
Enter password for admn: 

10.254.1.24                              AA10   On
10.254.1.24                              AA11   On
10.254.1.24                              AA12   On
10.254.1.24                              BA10   On
10.254.1.24                              BA12   On
```
#### Send power command to an outlet
```bash
# ./servertech_pdu.py --pdus 10.254.1.24 --user admn --off --outlets BA10
Enter password for admn: 
Success, off sent for outlet BA10 at 10.254.1.24
```
#### Send power command to multiple outlets
```bash
# ./servertech_pdu.py --pdus 10.254.1.24 --user admn --off --outlets BA10,BA12
Enter password for admn: 
Success, off sent for outlet BA10 at 10.254.1.24
Success, off sent for outlet BA12 at 10.254.1.24
```
#### Send power command to a group
```bash
# ./servertech_pdu.py --pdus 10.254.1.24 --user admn --off --groups Managed
Enter password for admn: 
Success, off sent for group Managed at 10.254.1.24
```
#### Send power command to multiple groups
```bash
# ./servertech_pdu.py --pdus 10.254.1.24 --user admn --off --groups Managed,Critical
Enter password for admn: 
Success, off sent for group Managed at 10.254.1.24
Success, off sent for group Critical at 10.254.1.24
```
#### Send power command to groups and outlets
```bash
# ./servertech_pdu.py --pdus 10.254.1.24 --user admn --on --groups Managed --outlets AA1,AA2,AA3
Enter password for admn: 
Success, on sent for group Managed at 10.254.1.24
Success, on sent for outlet AA1 at 10.254.1.24
Success, on sent for outlet AA3 at 10.254.1.24
Success, on sent for outlet AA2 at 10.254.1.24
```
#### Create JSON for power sequencing

Create a .json file that contains the following elements:

    user, pdus, groups, outlets

At least 1 PDU is required. Hostnames, IPv4, and IPv6 are all acceptable.

Any number of groups and/or outlets can be added. The groups and outlets will be
sent their power control operation in the order listed. Groups first, outlets
last.

Valid operations: on, off, reboot

##### Groups only configuration
```json
{
	"user": "admn",
	"pdus": [
		"[FE80::20A:9CFF:FE62:4EE%bond0.hmn0]",
        "10.254.1.24"
	],
	"groups": [
		{
			"name": "Managed",
			"operation": "off"
		},
		{
			"name": "CSM",
			"operation": "off"
		},
		{
			"name": "Critical",
			"operation": "reboot"
		}
	],
	"outlets": []
}
```
Upon execution with the above file, the tool will query the user for a password.

#### Query outlet status using JSON file
```bash
# ./servertech_pdu.py --file power-off.json --status
Enter password for admn: 

[FE80::20A:9CFF:FE62:4EE%bond0.hmn0]     AA1    On
[FE80::20A:9CFF:FE62:4EE%bond0.hmn0]     AA2    On
[FE80::20A:9CFF:FE62:4EE%bond0.hmn0]     AA3    On
[FE80::20A:9CFF:FE62:4EE%bond0.hmn0]     AA10   On
[FE80::20A:9CFF:FE62:4EE%bond0.hmn0]     AA11   On
[FE80::20A:9CFF:FE62:4EE%bond0.hmn0]     AA12   On
[FE80::20A:9CFF:FE62:4EE%bond0.hmn0]     BA10   On
[FE80::20A:9CFF:FE62:4EE%bond0.hmn0]     BA11   On
[FE80::20A:9CFF:FE62:4EE%bond0.hmn0]     BA12   On
[FE80::20A:9CFF:FE62:4EE%bond0.hmn0]     BA13   On
```
#### Send power commands using JSON file
```bash
# ./servertech_pdu.py --file power-off.json
Enter password for admn: 
Success, off sent for group Managed at [FE80::20A:9CFF:FE62:4EE%bond0.hmn0]
Success, off sent for group CSM at [FE80::20A:9CFF:FE62:4EE%bond0.hmn0]
Success, reboot sent for group Critical at [FE80::20A:9CFF:FE62:4EE%bond0.hmn0]
```
#### Override power commands using JSON file
```bash
# ./servertech_pdu.py --file power-off.json --off --groups Critical
Enter password for admn: 
Success, off sent for group Managed at [FE80::20A:9CFF:FE62:4EE%bond0.hmn0]
Success, off sent for group CSM at [FE80::20A:9CFF:FE62:4EE%bond0.hmn0]
Success, off sent for group Critical at [FE80::20A:9CFF:FE62:4EE%bond0.hmn0]
```

### Communication issues
Interacting with the JAWS interface can prodcue several different kind of
errors. Some steps have been taken to initiate retries but success is not always
guaranteed. HTTP 503s and bad responses are common and do not necessarily
indicate fatal errors.

#### Common retriable errors
```text
send_group_power_command: (503) Failed to send 'off' to group CSM in [FE80::20A:9CFF:FE62:4EE%bond0.hmn0]
do_group_power_control: off failed to send for group CSM at [FE80::20A:9CFF:FE62:4EE%bond0.hmn0], retrying ...
```
```text
get_group_information: JSON decode failed from [FE80::20A:9CFF:FE62:4EE%bond0.hmn0], retrying ...
get_group_information: None returned from 10.254.1.24, retrying ...
```
```text
get_outlet_status_all: JSON decode Failed from 10.254.1.24, retrying ...
get_outlet_status_all: None returned from 10.254.1.24, retrying ...
```

## Compatibility

servertech_pdu.py 1.0.0: Sentry Switched PDU Version 8.0p

## Changelog

See the [CHANGELOG.md](CHANGELOG.md) for the changes and release history of this
project.

## License

This project is copyrighted by Hewlett Packard Enterprise Development LP and is
distributed under the MIT license. See the [LICENSE.txt](LICENSE.txt) file for
details.
