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

import time
from http import HTTPStatus
from json import JSONDecodeError
from flask import json, request
from utils.flask_server.base_flask_api_server import BaseAPIApplication

ERROR_INCORRECT_INPUT_FORMAT = "Incorrect input format"
EOL = '\n'

class PDRPluginAPI(BaseAPIApplication):
    '''
    class PDRPluginAPI
    '''

    def __init__(self, isolation_mgr):
        """
        Initialize a new instance of the PDRPluginAPI class.
        """
        super(PDRPluginAPI, self).__init__()
        self.isolation_mgr = isolation_mgr


    def _get_routes(self):
        """
        Map URLs to function calls
        """
        return {
            self.get_excluded_ports: dict(urls=["/excluded"], methods=["GET"]),
            self.exclude_ports: dict(urls=["/excluded"], methods=["PUT"]),
            self.include_ports: dict(urls=["/excluded"], methods=["DELETE"])
        }


    def get_excluded_ports(self):
        """
        Return ports from exclude list as comma separated port names
        """
        items = self.isolation_mgr.exclude_list.items()
        formatted_items = [f"{item.port_name}: {'infinite' if item.ttl_seconds == 0 else int(max(0, item.remove_time - time.time()))}" for item in items]
        response = EOL.join(formatted_items) + ('' if not formatted_items else EOL)
        return response, HTTPStatus.OK


    def exclude_ports(self):
        """
        Parse input ports and add them to exclude list (or just update TTL)
        Input string example: [["0c42a10300756a04_1"],["98039b03006c73ba_2",300]]
        TTL that follows port name after the colon is optional
        """

        try:
            pairs = self.get_request_data()
        except JSONDecodeError:
            return ERROR_INCORRECT_INPUT_FORMAT + EOL, HTTPStatus.BAD_REQUEST
        
        response = ""
        for pair in pairs:
            if pair:
                port_name = pair[0]
                ttl = 0 if len(pair) == 1 else int(pair[1])
                self.isolation_mgr.exclude_list.add(port_name, ttl)
                response += f"Port {port_name} added to exclude list{EOL}"

        return response, HTTPStatus.OK


    def include_ports(self):
        """
        Remove ports from exclude list
        Input string: comma separated port names list
        Example: ["0c42a10300756a04_1","98039b03006c73ba_2"]
        """
        try:
            port_names = self.get_request_data()
        except JSONDecodeError:
            return ERROR_INCORRECT_INPUT_FORMAT + EOL, HTTPStatus.BAD_REQUEST

        response = ""
        for port_name in port_names:
            if self.isolation_mgr.exclude_list.remove(port_name):
                response += f"Port {port_name} removed from exclude list{EOL}"
            else:
                response += f"Port {port_name} is not in exclude list{EOL}"

        return response, HTTPStatus.OK
    
    def get_request_data(self):
        """
        Deserialize request json data into object
        """
        if request.is_json:
            # Directly convert JSON data into Python object
            return request.get_json()
        else:
            # Attempt to load plain data text as JSON
            return json.loads(request.get_data(as_text=True))
