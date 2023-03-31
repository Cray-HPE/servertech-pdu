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
Allows interaction with a Server Tech iPDU

Provides a limited number of interfaces for interacting with the Server Tech
iPDU. These actions are limited to those required to get status and send power
commands to the iPDU. All calls to JAWS have a basic retry mechanism for the
expected communications issues with the iPDU controller.

Typical usage example:
    pdu = PDU(hostname|IPv4|IPv6, username, password)
    groups = pdu.get_group_information()
    outlet_status = pdu.get_outlet_status_all()

"""

import json
import time
from pdu.jaws import Jaws

class PDU:
    """
    Definition of a Server Tech iPDU

    Attributes:
        _host(string):
            IPv4, IPv6, or hostname of target iPDU.
        _user(string):
            Username to access JAWS interface of iPDU.
        _jaws(object):
            Underlying JAWS communication implementation.

    Methods:
        get_host() -> string:
            Returns hostname/IP of the iPDU.
        get_outlet_status_all() -> dict:
            Returns a dictionary containing all the outlets and their status
            from the iPDU.
        get_group_information() -> dict:
            Returns a dictionaly containing all the groups of the iPDU.
        do_outlet_power_control(list) -> int:
            Sends power operations from the list of outlets to the iPDU.
        do_group_power_control(list) -> int:
            Sends power operations from the list of groups to the iPDU.
    """
    def __init__(self, host: str, user: str, passwd: str) -> None:
        self._host = host
        self._user = user
        self._jaws = Jaws(host, user, passwd)

    def get_host(self) -> str:
        """ Return hostname/IP """
        return self._host

    def get_outlet_status_all(self) -> dict:
        """
        The status of all the outlets in the iPDU. Will retry the JAWS call if
        there is an error response or if the JSON payload returned is invalid.

        Parameters:
            None

        Returns:
            A dictionary containing all the outlets and their status
            information.
        """
        outlet_status = None
        retries = 0
        while True:
            if retries > 5:
                print('get_outlet_status_all: exceeded retries for %s, ' \
                        'giving up' % self._host)
                return None
            try:
                rsp = self._jaws.get_outlet_status_all()

                if rsp is None:
                    print('get_outlet_status_all: None returned from %s, ' \
                            'retrying ...' % self._host)
                    time.sleep(1)
                    retries += 1
                    continue

                outlet_status = json.loads(rsp)
                break
            except json.decoder.JSONDecodeError:
                print('get_outlet_status_all: JSON decode Failed from %s, ' \
                        'retrying ...' % self._host)
                time.sleep(1)
                retries += 1

        return outlet_status

    def get_group_information(self) -> dict:
        """
        The group definitions of the iPDU. Will retry the JAWS call if there is
        an error response or if the JSON payload returned is invalid.

        Parameters:
            None

        Returns:
            A dictionary containing the group definitions and the outlets
            associated with them.
        """
        group_info = None
        retries = 0
        while True:
            if retries > 5:
                print('get_group_information: exceeded retries for %s, ' \
                        'giving up' % self._host)
                return None
            try:
                rsp = self._jaws.get_group_information()

                if rsp is None:
                    print('get_group_information: None returned from %s, ' \
                            'retrying ...' % self._host)
                    time.sleep(1)
                    retries += 1
                    continue

                group_info = json.loads(rsp)
                break
            except json.decoder.JSONDecodeError:
                print('get_group_information: JSON decode failed from %s, ' \
                            'retrying ...' % self._host)
                time.sleep(1)
                retries += 1

        return group_info

    def do_outlet_power_control(self, outlets: list):
        """
        Send a power operation to the list of outlets. Will retry the JAWS call
        if there is an error response or if the JSON payload returned is
        invalid.

        Parameters:
            outlets(list):
                List of dictionaries that contain an outlet name and the
                operation to be performed.

        Returns:
            None
        """
        for outlet in outlets:
            retries = 0
            while True:
                if retries >= 5:
                    print('do_outlet_power_control: %s exceeded retries for ' \
                            'outlet %s at %s, giving up' %
                            (outlet['operation'], outlet['name'], self._host))
                    break

                retval = self._jaws.send_outlet_power_command(outlet['operation'], outlet['name'])

                if retval == 0:
                    print('do_outlet_power_control: %s sent for outlet %s at ' \
                            '%s' % (outlet['operation'], outlet['name'],
                                    self._host))
                    break
                else:
                    print('do_outlet_power_control: %s failed to send for ' \
                            'outlet %s at %s, retrying ...' %
                            (outlet['operation'], outlet['name'], self._host))
                    time.sleep(1)
                    retries += 1

    def do_group_power_control(self, groups: list):
        """
        Send a power operation to the list of groups. Will retry the JAWS call
        if there is an error response or if the JSON payload returned is
        invalid.

        Parameters:
            groups(list):
                List of dictionaries that contain a group name and the operation
                to be performed.
        """
        for group in groups:
            retries = 0
            while True:
                if retries >= 5:
                    print('do_group_power_control: %s exceeded retries for ' \
                            'group %s at %s, giving up' %
                            (group['operation'], group['name'], self._host))
                    break

                retval = self._jaws.send_group_power_command(group['operation'], group['name'])

                if retval == 0:
                    print('do_group_power_control: %s sent for group %s at %s' %
                            (group['operation'], group['name'], self._host))
                    break
                else:
                    print('do_group_power_control: %s failed to send for ' \
                            'group %s at %s, retrying ...' %
                            (group['operation'], group['name'], self._host))
                    time.sleep(1)
                    retries += 1
