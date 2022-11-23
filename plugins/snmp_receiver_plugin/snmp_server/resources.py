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
from http import HTTPStatus

import helpers
import logging


class UFMResource(Resource):
    def __init__(self, switch_ip_to_name):
        self.switch_ip_to_name = switch_ip_to_name

    @staticmethod
    def report_success():
        return {}, HTTPStatus.OK

    @staticmethod
    def report_error(status_code, text):
        logging.error(text)
        return {"error": text}, status_code

    @staticmethod
    def report_not_allowed():
        return UFMResource.report_error(HTTPStatus.METHOD_NOT_ALLOWED, "Method is not allowed")

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
        status_code, text = helpers.post_request(resource, json=payload)
        return status_code, text

    def post(self, unregister=False):
        logging.info("POST /plugin/snmp/register")
        if not request.json:
            return self.report_error(HTTPStatus.BAD_REQUEST, "Upload request is empty")
        else:
            json_data = request.get_json(force=True)
            try:
                switches = json_data["switches"]
                hosts = json_data["hosts"]
            except KeyError as ke:
                return self.report_error(HTTPStatus.BAD_REQUEST, f"No key {ke} found")
            self.switch_ip_to_name = helpers.get_ufm_switches()
            incorrect_switches = set(switches) - self.switch_ip_to_name.keys()
            if incorrect_switches:
                return self.report_error(HTTPStatus.BAD_REQUEST, f"Switches {incorrect_switches} don't exist in the fabric or don't have an ip")
            for ip in hosts:
                status_code, text = self.register_switches(ip, switches, unregister)
                if not helpers.succeded(status_code):
                    return self.report_error(status_code, text)
            return self.report_success()

class Unregister(Register):
    def get(self):
        return self.report_error(HTTPStatus.METHOD_NOT_ALLOWED, "Method is not allowed")

    def post(self):
        logging.info("POST /plugin/snmp/unregister")
        return super().post(unregister=True)

class Dummy(UFMResource):
    def get(self):
        logging.info("GET /plugin/snmp/dummy")
        print("Hello from dummy resource!", flush=True)
        return self.report_success()

    def post(self):
        return self.report_error(HTTPStatus.METHOD_NOT_ALLOWED, "Method is not allowed")
