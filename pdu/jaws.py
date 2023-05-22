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

""" Low level communication with iPDU JAWS API

Makes the http calls using the requests module to the JAWS API of the Server
Tech iPDU. API calls are limited to those required for status query and patching
of the power status for groups and outlets.

Typical usage example:
    jaws = Jaws(hostname|IPv4|IPv6, username, password)
    outlet_status = jaws.get_outlet_status_all()
    groups = jaws.get_group_information()


"""

import json
from http import HTTPStatus
import logging
import requests
import urllib3

logging.basicConfig(level=logging.INFO,
            format="%(levelname)s:%(name)s:%(message)s")

class URLs:
    """ Jaws API URLs """
    GROUP_CONTROL = 'jaws/control/groups'
    GROUP_MONITOR = 'jaws/monitor/groups'
    OUTLET_CONTROL = 'jaws/control/outlets'
    OUTLET_MONITOR = 'jaws/monitor/outlets'

class Jaws:
    """
    Definition of JAWS communication interfaces for a Server Tech iPDU.

    Attributes:
        _host(string):
            IPv4, IPv6, or hostname of the iPDU.
        _basic_auth(HTTPBasicAuth):
            Authorization used with requests module.
        _headers(dictionary):
            HTTP send headers.
        _base_url(string):
            Base https URL string

    Modules:
        configure_basic_auth(string, string):
            Converts a username and password into an HTTPBasicAuth structure.
        generate_header():
            Creates a basic header for all HTTPS communication and stores it.
        get_outlet_status_all() -> dict:
            Returns a dictionary containing all the outlets and their status
            from the iPDU.
        get_group_information() -> dict:
            Returns a dictionaly containing all the groups of the iPDU.
        send_outlet_power_command(string, string) -> int:
            Sends a PATCH operation to the iPDU targeting a single outlet with
            an on/off/reboot payload.
        send_group_power_command(string, string) -> int:
            Sends a PATCH operation to the iPDU targeting a single group with
            an on/off/reboot payload.
    """
    def __init__(self, host: str, user: str, passwd: str) -> None:
        self._host = host
        self._basic_auth = None
        self._headers = ''
        self._base_url = f'https://{self._host}'
        self.configure_basic_auth(user, passwd)
        self.generate_header()
        self.logger = logging.getLogger("jaws")

    def error(self, msg: str):
        """ Log an error """
        self.logger.error(msg)

    def warning(self, msg: str):
        """ Log a warning """
        self.logger.warning(msg)

    def configure_basic_auth(self, user: str, passwd: str):
        """
        Transform user and passwd into a requets basic auth structure.

        Parameters:
            user (string): Username for the Jaws API
            passwd (string): Password for the user at the Jaws API

        Returns:
            None
        """
        self._basic_auth = requests.auth.HTTPBasicAuth(user, passwd)

    def generate_header(self):
        """
        Create a generic header for all HTTP Jaws operations

        Parameters:
            None

        Returns:
            None
        """
        self._headers = {
                'cache-control': 'no-cache',
                'Content-Type': 'application/json',
            }

    def get_outlet_status_all(self) -> dict:
        """
        Query the Jaws API for outlet status for target outlet.

        Parameters:
            None

        Returns:
            A dictionary containing all the outlets and their status
            information.
        """
        fname = 'get_outlet_status_all'
        # SSL verification is not used which results in a
        # InsecureRequestWarning. The following line disables only the
        # IsnsecureRequestWarning.
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        url = f'{self._base_url}/{URLs.OUTLET_MONITOR}'

        rsp = None
        try:
            rsp = requests.get(
                    url = url,
                    auth = self._basic_auth,
                    headers = self._headers,
                    verify = False
                )
        except requests.HTTPError as req_http_err:
            self.error(f'{fname}: HTTP Error: {req_http_err}')
        except requests.ConnectionError as req_con_err:
            self.error(f'{fname}: Connection Error: {req_con_err}')
        except requests.Timeout as req_to:
            self.error(f'{fname}: Timeout: {req_to}')
        except requests.RequestException as req_err:
            self.error(f'{fname}: {req_err}')

        if rsp is None or not rsp.text:
            return None

        if rsp.status_code >= HTTPStatus.MULTIPLE_CHOICES:
            self.warning('f{fname}: Call returned {rsp.status_code}')

        return rsp.text

    def get_group_information(self) -> dict:
        """
        Query the Jaws API for outlets associated with a group.

        Parameters:
            None

        Returns:
            A dictionary containing the group definitions and the outlets
            associated with them.
        """
        fname = 'get_group_information'
        # SSL verification is not used which results in a
        # InsecureRequestWarning. The following line disables only the
        # IsnsecureRequestWarning.
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        url = f'{self._base_url}/{URLs.GROUP_MONITOR}'

        rsp = None
        try:
            rsp = requests.get(
                    url = url,
                    auth = self._basic_auth,
                    headers = self._headers,
                    verify = False
                )

        except requests.HTTPError as req_http_err:
            self.error(f'{fname}: HTTP Error: {req_http_err}')
        except requests.ConnectionError as req_con_err:
            self.error(f'{fname}: Connection Error: {req_con_err}')
        except requests.Timeout as req_to:
            self.error(f'{fname}: Timeout: {req_to}')
        except requests.RequestException as req_err:
            self.error(f'{fname}: {req_err}')

        if rsp is None or not rsp.text:
            return None

        if rsp.status_code >= HTTPStatus.MULTIPLE_CHOICES:
            self.warning('f{fname}: Call returned {rsp.status_code}')
            return None

        return rsp.text

    def send_outlet_power_command(self, operation: str, outlet: str) -> int:
        """
        Send the power operation to the target outlet.

        Parameters:
            operation(string):
                on/off/reboot command.
            outlet(string):
                Target outlet in the iPDU.

        Returns:
            0 on success, 1 on error
        """
        fname = 'send_outlet_power_command'
        # SSL verification is not used which results in a
        # InsecureRequestWarning. The following line disables only the
        # IsnsecureRequestWarning.
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        url = f'{self._base_url}/{URLs.OUTLET_CONTROL}/{outlet}'

        payload = {
            'control_action': operation
        }

        rsp = None
        try:
            rsp = requests.patch(
                url = url,
                auth = self._basic_auth,
                headers = self._headers,
                data = json.dumps(payload),
                verify = False
            )

        except requests.HTTPError as req_http_err:
            self.error(f'{fname}: HTTP Error: {req_http_err}')
        except requests.ConnectionError as req_con_err:
            self.error(f'{fname}: Connection Error: {req_con_err}')
        except requests.Timeout as req_to:
            self.error(f'{fname}: Timeout: {req_to}')
        except requests.RequestException as req_err:
            self.error(f'{fname}: {req_err}')

        if rsp is None:
            return 1

        if rsp.status_code >= HTTPStatus.MULTIPLE_CHOICES:
            self.warning('f{fname}: ({rsp.status_code}) Failed to send ' \
                f'\'{operation}\' to outlet {outlet} in {self._host}')
            return 1

        return 0

    def send_group_power_command(self, operation: str, group: str) -> int:
        """
        Send the power operation to the target group.

        Parameters:
            operation(string):
                on/off/reboot command.
            group(string):
                Target outlet in the iPDU.

        Returns:
            0 on success, 1 on error
        """
        fname = 'send_group_power_command'
        # SSL verification is not used which results in a
        # InsecureRequestWarning. The following line disables only the
        # IsnsecureRequestWarning.
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        url = f'{self._base_url}/{URLs.GROUP_CONTROL}/{group}'

        payload = {
            'control_action': operation
        }

        rsp = None
        try:
            rsp = requests.patch(
                url = url,
                auth = self._basic_auth,
                headers = self._headers,
                data = json.dumps(payload),
                verify = False
            )

        except requests.HTTPError as req_http_err:
            self.error(f'{fname}: HTTP Error: {req_http_err}')
        except requests.ConnectionError as req_con_err:
            self.error(f'{fname}: Connection Error: {req_con_err}')
        except requests.Timeout as req_to:
            self.error(f'{fname}: Timeout: {req_to}')
        except requests.RequestException as req_err:
            self.error(f'{fname}: {req_err}')

        if rsp is None:
            return 1

        if rsp.status_code >= HTTPStatus.MULTIPLE_CHOICES:
            self.warning('f{fname}: ({rsp.status_code}) Failed to send ' \
                f'\'{operation}\' to group {group} in {self._host}')
            return 1

        return 0
