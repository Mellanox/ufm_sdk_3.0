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

from utils.flask_server.base_flask_api_server import BaseAPIApplication

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
            self.exclude_ports: dict(urls=["/excluded/<excluded_ports_str>"], methods=["PUT"]),
            self.include_ports: dict(urls=["/excluded/<port_names_str>"], methods=["DELETE"])
        }


    def get_excluded_ports(self):
        """
        Return ports from exclude list as comma separated port names
        """
        items = self.isolation_mgr.exclude_list.items()
        return '\n'.join(item.port_name for item in items) + '\n'


    def exclude_ports(self, excluded_ports_str):
        """
        Parse input ports and add them to exclude list (or just update TTL)
        Input string example: 0c42a10300756a04_1,98039b03006c73ba_2:300
        TTL that follows port name after the colon is optional
        """
        ietms = excluded_ports_str.split(',')
        if not ietms:
            return "No ports to exclude\n"
        for item in excluded_ports_str.split(','):
            parts = item.strip().split(':')
            name = parts[0].strip()
            time = 0 if len(parts) == 1 or not parts[1].strip().isdigit() else int(parts[1].strip())
            self.isolation_mgr.exclude_list.add(name, time)
        return "Ports added to exclude list\n"


    def include_ports(self, port_names_str):
        """
        Remove ports from exclude list
        Input string: comma separated port names
        """
        response = ""
        names = port_names_str.split(',')
        for name in names:
            if name.strip():
                name = name.strip();
                if self.isolation_mgr.exclude_list.remove(name):
                    response += f"Port {name} removed from exclude list\n"
                else:
                    response += f"Port {name} is not in exclude list\n"

        return response
