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
from flask_restful import Resource
from flask import request
import helpers
import logging


class UFMResource(Resource):
    def __init__(self):
        self.success = 200
        self.accepted = 202

    def succeded(self, status_code):
        return status_code in [self.success, self.accepted]

    def report_success(self):
        return {}, self.success

    @staticmethod
    def report_error(status_code, message):
        logging.error(message)
        return {"error": message}, status_code

class Register(UFMResource):
    def get(self):
        return self.report_error(405, "Method is not allowed")

    def register_switches(self, ip, switches, unregister=False):
        resource = "/actions"
        cli_register = f"snmp-server host {ip} traps"
        cli_unregister = f"no snmp-server host {ip}"
        payload = {
            "action": "run_cli",
            "identifier": "ip",
            "params": {
                "commandline": [cli_unregister if unregister else cli_register]
            },
            "description": "register plugin as SNMP traps receiver",
            "object_ids": switches,
            "object_type": "System"
        }
        return helpers.post_request(resource, json=payload)

    def post(self, unregister=False):
        logging.info("POST /plugin/snmp/register")
        if not request.json:
            return self.report_error(400, "Upload request is empty")
        else:
            json_data = request.get_json(force=True)
            try:
                switches = json_data["switches"]
                hosts = json_data["hosts"]
            except KeyError as ke:
                return self.report_error(400, f"No key {ke} found")
            existing_switches = helpers.get_ufm_switches()
            incorrect_switches = set(switches) - set(existing_switches)
            if incorrect_switches:
                return self.report_error(400, f"Switches {incorrect_switches} don't exist in the fabric or don't have an ip")
            for ip in hosts:
                response = self.register_switches(ip, switches, unregister)
                if not self.succeded(response.status_code):
                    return self.report_error(response.status_code, response.text)
            return self.report_success()

class Unregister(Register):
    def get(self):
        return self.report_error(405, "Method is not allowed")

    def post(self):
        logging.info("POST /plugin/snmp/unregister")
        return super().post(unregister=True)

class Dummy(UFMResource):
    def get(self):
        logging.info("GET /plugin/snmp/dummy")
        print("Hello from dummy resource!", flush=True)
        return self.report_success()

    def post(self):
        return self.report_error(405, "Method is not allowed")
