#!/usr/bin/python3

# MIT License
#
# (C) Copyright [2023] Hewlett Packard Enterprise Development LP
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

"""
Control power on Server Tech iPDU outlets by group or single outlet.

Example usage:
    ./servertech_pdu.py --status --pdus [FE80::20A:9CFF:FE62:4EE%bond0.hmn0] \
        --groups Critical --user admn

    ./servertech_pdu.py --off --pdus [FE80::20A:9CFF:FE62:4EE%bond0.hmn0] \
        --outlets AA1,AA2,BA1,BA2 --user admn

    ./servertech_pdu.py --off --pdus [FE80::20A:9CFF:FE62:4EE%bond0.hmn0] \
        --outlets AA1,AA2,BA1,BA2 --file power-off.json --user admn

    ./servertech_pdu.py --file power-off.json

    ./servertech_pdu.py --file power-off.json --status

Functions:
    print_outlet_status(string, dict, list):
        Print outlet status in a simple table.
    get_outlet_staus(dict) -> int:
        Prepare outlet lists for status print
    load_arguments(dict, dict) -> dict:
        Load arguments from the command line.
"""

import argparse
import sys
import json
import getpass
import signal

from multiprocessing.dummy import Pool as ThreadPool

from pdu.pdu import PDU

VERSION = '0.2.0'
DEF_THREADS = 10

def sighandler(_sig, _frame):
    """ Handle CTRL-C """
    print('Exiting.')
    sys.exit(0)

signal.signal(signal.SIGINT, sighandler)

def print_outlet_status(pdu: str, outlet_status: dict, outlets: list) -> None:
    """
    Print outlet status in a simple table.

    Parameters:
        pdu_dev(string):
            iPDU to display.
        outlets_status(dict):
            Complete list of outlets and their status from the iPDU.
        outlets(list):
            List of outlets we want the status of to be printed to the screen.

    Returns:
        0 for success, 1 for error
    """
    print('')
    count = 0
    for outlet in outlet_status:
        for target in outlets:
            if outlet['id'] == target:
                print('%-40s %-6s %s' % (pdu, outlet['id'], outlet['state']))
                count += 1

    if count < len(outlets):
        for target in outlets:
            found = False
            for outlet in outlet_status:
                if outlet['id'] == target:
                    found = True
                    break
            if not found:
                print('%-40s %-6s INVALID OUTLET NAME' % (pdu, target))

def get_outlet_status(pdu: str, opts: dict) -> int:
    """
    Prepare outlet lists for status print

    Parameters:
        opts(dict):
            Program arguments pulled from a file and/or the command line.

    Returns:
        0 for success, 1 for error
    """

    noutlets = []
    ret = 0

    pdu_dev = PDU(pdu, opts['user'], opts['passwd'])

    if 'groups' in opts and len(opts['groups']) > 0:
        group_list = pdu_dev.get_group_information()

        if group_list is None:
            print('Failed to retrieve group information from %s.' % pdu_dev.get_host())
        else:
            for pdu_group in group_list:
                for group in opts['groups']:
                    if pdu_group['name'] == group['name']:
                        noutlets.extend(pdu_group['outlet_access'])

    if 'outlets' in opts and len(opts['outlets']) > 0:
        for outlet in opts['outlets']:
            noutlets.append(outlet['name'])

    if len(noutlets) > 0:
        noutlets = list(set(noutlets))
        outlet_status = pdu_dev.get_outlet_status_all()

        if outlet_status is None:
            print('Failed to retrieve outlet status from %s.' % pdu_dev.get_host())
            return 1

        print_outlet_status(pdu_dev.get_host(), outlet_status, noutlets)

    return ret

def do_group_power_control(pdu: str, opts: dict):
    """
    Thread wrapper for PDU.do_group_power_control
    """
    pdu_dev = PDU(pdu, opts['user'], opts['passwd'])
    pdu_dev.do_group_power_control(opts['groups'])

def do_outlet_power_control(pdu: str, opts: dict):
    """
    Thread wrapper for PDU.do_outlet_power_control
    """
    pdu_dev = PDU(pdu, opts['user'], opts['passwd'])
    pdu_dev.do_outlet_power_control(opts['groups'])

def load_arguments(opts: dict, args: dict) -> dict:
    """
    Load arguments from the command line. These will override any arguments set
    from a file passed in.

    Arguments:
        opts(dict):
            Options dictionary that may be preloaded with values from a file.
        args(dict):
            Command line arguments.

    Returns:
        An update options dictionary with no duplicate pdus, outlets, or groups.
        Prelaoded values from a file are overwritten by the command line
        options. None is returned if something is invalid.
    """
    if args.on:
        opts['operation'] = 'on'

    if args.off:
        if "operation" in opts:
            return None
        opts['operation'] = 'off'

    if args.reboot:
        if "operation" in opts:
            return None
        opts['operation'] = 'reboot'

    if args.status:
        if "operation" in opts:
            return None
        opts['operation'] = 'status'

    if args.pdus is not None and len(args.pdus) > 0:
        if 'pdus' not in opts:
            opts['pdus'] = []
        opts['pdus'].extend(args.pdus.split(','))
        # Create a uniq list of PDUs
        opts['pdus'] = list(set(opts['pdus']))

    if args.groups is not None and len(args.groups) > 0:
        if 'operation' not in opts:
            return None
        # Create a uniq list of groups
        cli_groups = list(set(args.groups.split(',')))
        if 'groups' not in opts:
            opts['groups'] = []
        for grp in cli_groups:
            # Override previously set group entry if there is one
            opts['groups'] = [ele for ele in opts['groups'] if ele['name'] != grp]
            group = {}
            group['name'] = grp
            group['operation'] = opts['operation']
            opts['groups'].append(group)

    if args.outlets is not None and len(args.outlets) > 0:
        if 'operation' not in opts:
            return None
        # Create a uniq list of outlets
        cli_outlets = list(set(args.outlets.split(',')))
        if 'outlets' not in opts:
            opts['outlets'] = []
        for otl in cli_outlets:
            # Override previously set outlet entry if there is one
            opts['outlets'] = [ele for ele in opts['outlets'] if ele['name'] != otl]
            outlet = {}
            outlet['name'] = otl
            outlet['operation'] = opts['operation']
            opts['outlets'].append(outlet)

    if args.user is not None:
        opts['user'] = args.user

    if args.passwd is not None:
        opts['passwd'] = args.passwd

    opts['threads'] = DEF_THREADS
    if args.threads is not None:
        if args.threads > 0:
            opts['threads'] = args.threads
        else:
            print(f'Too few threads selected, using default {DEF_THREADS}')

    return opts

def main():
    """ Main Program """
    parser = argparse.ArgumentParser(description='Server Tech iPDU control.')
    parser.add_argument('--on', action='store_true',
                        help='turn selected outlets/groups On')
    parser.add_argument('--off', action='store_true',
                        help='turn selected outlets/groups Off')
    parser.add_argument('--reboot', action='store_true',
                        help='reboot selected outlets/groups')
    parser.add_argument('--status', action='store_true',
                        help='get status of outlet or group')
    parser.add_argument('--pdus', help='iPDU controller hostnames, IPv4 ' \
                                        'addrs, and/or IPv6 addrs')
    parser.add_argument('--outlets', help='target outlets')
    parser.add_argument('--groups', help='target groups')
    parser.add_argument('--user', help='Jaws user name')
    parser.add_argument('--passwd', help='Jaws password')
    parser.add_argument('--file',help='power sequence file in json, command ' \
                                        'line overrides values in the file')
    parser.add_argument('--threads', type=int, help='number of threads to use')
    parser.add_argument('--version', action='store_true',
                        help='print script version information and exit')
    args = parser.parse_args()

    if args.version is True:
        print('%s: %s' % (__file__, VERSION))
        return 0

    opts = {}

    if args.file is not None:
        try:
            jsonfile = open(args.file)
        except IOError as io_err:
            print('open() failed', io_err)
            sys.exit(1)

        with jsonfile:
            data = jsonfile.read()

        try:
            opts = json.loads(data)
        except json.JSONDecodeError as json_error:
            print("Failed to parse json from file: ", json_error)
            sys.exit(1)

    opts = load_arguments(opts, args)
    if opts is None:
        print('Invalid arguments.')
        return 1

    if 'user' not in opts:
        opts['user'] = input('Enter username for iPDU: ')

    if 'passwd' not in opts:
        opts['passwd'] = getpass.getpass('Enter password for %s: ' % opts['user'])

    if ('pdus' not in opts and len(opts['pdus']) == 0) or \
       (('groups' not in opts or len(opts['groups']) == 0) and \
       ('outlets' not in opts or len(opts['outlets']) == 0)):
        print('Invalid arguments.')
        return 1

    tpool = ThreadPool(opts['threads'])

    targs = []
    for pdu in opts['pdus']:
        targs.append((pdu,opts))

    if 'operation' in opts and opts['operation'] == 'status':
        tpool.starmap(get_outlet_status, targs)
    else:
        if 'groups' in opts and len(opts['groups']) > 0:
            tpool.starmap(do_group_power_control, targs)

        if 'outlets' in opts and len(opts['outlets']) > 0:
            tpool.starmap(do_outlet_power_control, targs)

    tpool.close()
    tpool.join()

    return 0

if __name__ == '__main__':
    sys.exit(main())
