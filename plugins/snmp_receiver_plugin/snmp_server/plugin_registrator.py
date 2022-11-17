#
# Copyright © 2013-2022 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
#
# @author: Alexander Tolikin
# @date:   November, 2022
#
import logging
import socket
import time

import helpers


class PluginRegistrator:
    def __init__(self):
        self.switch_ips = set()

    def get_ufm_switches(self):
        resource = "/resources/systems?type=switch"
        response = helpers.get_request(resource)
        switch_ips = set()
        for switch in response.json():
            ip = switch["ip"]
            if not ip == helpers.EMPTY_IP:
                switch_ips.add(switch["ip"])
        logging.info(f"List of switches to register plugin on: {switch_ips}")
        return switch_ips

    def register_switches(self, switches, unregister=False):
        resource = "/actions"
        local_hostname = socket.gethostname()
        local_ip = socket.gethostbyname(local_hostname)
        cli = f"snmp-server host {local_ip} traps"
        if unregister:
            cli = "no " + cli
        payload = {
            "action": "run_cli",
            "identifier": "ip",
            "params": {
                "commandline": [cli]
            },
            "description": "register plugin as SNMP traps receiver",
            "object_ids": list(switches),
            "object_type": "System"
        }
        response = helpers.post_request(resource, json=payload)
        logging.info(f"Registration status code: {response.status_code},\nresponse: {response.text}")

    def run(self):
        while True:
            new_switch_ips = self.get_ufm_switches()
            switches_to_register = new_switch_ips - self.switch_ips
            if switches_to_register:
                self.switch_ips = new_switch_ips
                self.register_switches(switches_to_register)
            time.sleep(60)


if __name__ == "__main__":
    plugin_registrator = PluginRegistrator()
    plugin_registrator.run()