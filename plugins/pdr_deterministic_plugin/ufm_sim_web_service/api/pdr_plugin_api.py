#
# Copyright © 2013-2024 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
#

import json
import time
from http import HTTPStatus
from json import JSONDecodeError
from api.base_aiohttp_api import BaseAiohttpAPI

ERROR_INCORRECT_INPUT_FORMAT = "Incorrect input format"
EOL = '\n'

class PDRPluginAPI(BaseAiohttpAPI):
    '''
    class PDRPluginAPI
    '''

    def __init__(self, isolation_mgr):
        """
        Initialize a new instance of the PDRPluginAPI class.
        """
        super(PDRPluginAPI, self).__init__()
        self.isolation_mgr = isolation_mgr

        # Define routes using the base class's method
        self.add_route("GET",    "/excluded", self.get_excluded_ports)
        self.add_route("POST",   "/excluded", self.exclude_ports)
        self.add_route("DELETE", "/excluded", self.include_ports)


    async def get_excluded_ports(self, request):
        """
        Return ports from exclude list as comma separated port names
        """
        items = self.isolation_mgr.exclude_list.items()
        formatted_items = [f"{item.port_name}: {'infinite' if item.ttl_seconds == 0 else int(max(0, item.remove_time - time.time()))}" for item in items]
        response = EOL.join(formatted_items) + ('' if not formatted_items else EOL)
        return self.create_response(response)


    async def exclude_ports(self, request):
        """
        Parse input ports and add them to exclude list (or just update TTL)
        Input string example: [["0c42a10300756a04_1"],["98039b03006c73ba_2",300]]
        TTL that follows port name after the colon is optional
        """

        try:
            pairs = self.get_request_data(request)
        except (JSONDecodeError, ValueError):
            return ERROR_INCORRECT_INPUT_FORMAT + EOL, HTTPStatus.BAD_REQUEST

        if not isinstance(pairs, list) or not all(isinstance(pair, list) for pair in pairs):
            return ERROR_INCORRECT_INPUT_FORMAT + EOL, HTTPStatus.BAD_REQUEST

        response = ""
        for pair in pairs:
            if pair:
                port_name = self.fix_port_name(pair[0])
                ttl = 0 if len(pair) == 1 else int(pair[1])
                self.isolation_mgr.exclude_list.add(port_name, ttl)
                if ttl == 0:
                    response += f"Port {port_name} added to exclude list forever"
                else:
                    response += f"Port {port_name} added to exclude list for {ttl} seconds"

                response += self.get_port_warning(port_name) + EOL

        return self.create_response(response)


    async def include_ports(self, request):
        """
        Remove ports from exclude list
        Input string: comma separated port names list
        Example: ["0c42a10300756a04_1","98039b03006c73ba_2"]
        """
        try:
            port_names = self.get_request_data(request)
        except (JSONDecodeError, ValueError):
            return ERROR_INCORRECT_INPUT_FORMAT + EOL, HTTPStatus.BAD_REQUEST

        if not isinstance(port_names, list):
            return ERROR_INCORRECT_INPUT_FORMAT + EOL, HTTPStatus.BAD_REQUEST

        response = ""
        for port_name in port_names:
            port_name = self.fix_port_name(port_name)
            if self.isolation_mgr.exclude_list.remove(port_name):
                response += f"Port {port_name} removed from exclude list"
            else:
                response += f"Port {port_name} is not in exclude list"

            response += self.get_port_warning(port_name) + EOL

        return self.create_response(response)


    def get_request_data(self, request):
        """
        Deserialize request json data into object
        """
        if request.is_json:
            # Directly convert JSON data into Python object
            return request.get_json()
        else:
            # Attempt to load plain data text as JSON
            return json.loads(request.get_data(as_text=True))


    def fix_port_name(self, port_name):
        """
        Try to fix common user mistakes for input port names
        Return fixed port name
        """
        # Remove '0x' from the beginning
        if port_name.startswith('0x'):
            port_name = port_name[2:]

        # Additional corrections can be added here upon request
        return port_name

    def get_port_warning(self, port_name):
        """
        Return warning text if port does not exist in ports data and update plugin logs
        """
        if not self.isolation_mgr.test_mode:
            if not self.isolation_mgr.ports_data.get(port_name):
                self.isolation_mgr.logger.warning(f"Port {port_name} is not found in ports data")
                return " (WARNING: port is not found in ports data)"

        return ""
