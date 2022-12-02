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
        self.resource = "/actions"
    
    @staticmethod
    def get_json_api_payload(cli, description, switches):
        return {
            "action": "run_cli",
            "identifier": "ip",
            "params": {
                "commandline": [cli]
            },
            "description": description,
            "object_ids": switches,
            "object_type": "System"
        }

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

    def post_json_api(self, cli, switches):
        payload = self.get_json_api_payload(cli, switches)
        status_code, text = helpers.post_request(self.resource, json=payload)
        return status_code, text

class Switch(UFMResource):
    def get(self):
        return self.report_error(405, "Method is not allowed")

    @staticmethod
    def get_cli(ip, unregister=False):
        cli_register = f"snmp-server host {ip} traps"
        cli_unregister = f"no snmp-server host {ip}"
        return cli_unregister if unregister else cli_register

    def post(self, unregister=False):
        resource = "unregister" if unregister == True else "register"
        logging.info(f"POST /plugin/snmp/{resource}")
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
            description = "plugin registration as SNMP traps receiver"
            for ip in hosts:
                status_code, text = self.post_json_api(self.get_cli(ip, unregister), description, switches)
                if not helpers.succeded(status_code):
                    return self.report_error(status_code, text)
            return self.report_success()

class RegisterSwitch(Switch):
    def post(self):
        return super().post()

class UnregisterSwitch(Switch):
    def post(self):
        return super().post(unregister=True)

class Event(UFMResource):
    def get(self):
        return self.report_error(405, "Method is not allowed")

    def add_event(self, events, switches, remove=False):
        for event in events:
            cli_add_events = f"snmp-server notify event {event}"
            cli_remove_events = f"no snmp-server notify event {event}"
            payload = self.get_json_api_payload(cli_remove_events if remove else cli_add_events, switches)
            status_code, text = helpers.post_request(self.resource, json=payload)
            if status_code == helpers.HTTP_ERROR:
                break
        return status_code, text

    @staticmethod
    def get_cli(event, remove=False):
        cli_add_events = f"snmp-server notify event {event}"
        cli_remove_events = f"no snmp-server notify event {event}"
        return cli_remove_events if remove else cli_add_events

    def post(self, remove=False):
        resource = "remove_event" if remove == True else "add_event"
        logging.info(f"POST /plugin/snmp/{resource}")
        if not request.json:
            return self.report_error(HTTPStatus.BAD_REQUEST, "Upload request is empty")
        else:
            json_data = request.get_json(force=True)
            try:
                switches = json_data["switches"]
                events = json_data["events"]
            except KeyError as ke:
                return self.report_error(HTTPStatus.BAD_REQUEST, f"No key {ke} found")
            self.switch_ip_to_name = helpers.get_ufm_switches()
            incorrect_switches = set(switches) - self.switch_ip_to_name.keys()
            if incorrect_switches:
                return self.report_error(HTTPStatus.BAD_REQUEST, f"Switches {incorrect_switches} don't exist in the fabric or don't have an ip")
            description = "UFM event monitoring settings"
            for event in events:
                status_code, text = self.post_json_api(self.get_cli(event, remove), description, switches)
                if not helpers.succeded(status_code):
                    return self.report_error(status_code, text)
            return self.report_success()

class AddEvent(Event):
    def post(self):
        return super().post(remove=True)

class RemoveEvent(Event):
    def post(self):
        return super().post(remove=True)

class Dummy(UFMResource):
    def get(self):
        logging.info("GET /plugin/snmp/dummy")
        print("Hello from dummy resource!", flush=True)
        return self.report_success()

    def post(self):
        return self.report_error(HTTPStatus.METHOD_NOT_ALLOWED, "Method is not allowed")
