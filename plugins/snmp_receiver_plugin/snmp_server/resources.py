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
import json
import os
import socket

import helpers
import logging


class UFMResource(Resource):
    def __init__(self, switch_dict):
        self.switch_dict = switch_dict
        self.registered_switches = set(self.read_json_file(helpers.SWITCHES_FILE))

    def update_registered_switches(self, switches, unregister=False):
        if unregister:
            self.registered_switches = self.registered_switches - set(switches)
        else:
            self.registered_switches.update(switches)
        with open(helpers.SWITCHES_FILE, "w") as file:
            json.dump(list(self.registered_switches), file)

    @staticmethod
    def read_json_file(file_name):
        if not os.path.exists(file_name):
            return []
        with open(file_name, "r", encoding="utf-8") as file:
            # unhandled exception in case some of the files was changed manually
            data = json.load(file)
        return data

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

class Switch(UFMResource):
    def get(self):
        return self.report_error(405, "Method is not allowed")

    @staticmethod
    def get_cli(ip, unregister=False):
        # TODO: change to sha512 and aes-256
        cli_register_v3 = f"snmp-server host {ip} traps version 3 user {helpers.SNMP_USER} \
                            auth sha {helpers.SNMP_PASSWORD} priv aes-128 {helpers.SNMP_PRIV_PASSWORD}"
        cli_register_v1_v2 = f"snmp-server host {ip} traps"
        cli_register = cli_register_v3 if helpers.ConfigParser.snmp_version == 3 else cli_register_v1_v2
        cli_unregister = f"no snmp-server host {ip}"
        return cli_unregister if unregister else cli_register

    def post(self, unregister=False):
        resource = "unregister" if unregister == True else "register"
        logging.info(f"POST /plugin/snmp/{resource}")
        if not request.json:
            switches = list(self.switch_dict.keys())
            hosts = []
        else:
            json_data = request.get_json(force=True)
            try:
                switches = json_data["switches"]
            except KeyError as ke:
                return self.report_error(HTTPStatus.BAD_REQUEST, f"No key {ke} found")
            hosts = json_data.get("hosts", [])
        if not hosts:
            hosts.append(helpers.LOCAL_IP)
        incorrect_switches = set(switches) - set(self.switch_dict.keys())
        if incorrect_switches:
            return self.report_error(HTTPStatus.BAD_REQUEST, f"Switches {incorrect_switches} don't exist in the fabric or don't have an ip")
        description = "plugin registration as SNMP traps receiver"
        for ip in hosts:
            status_code, text = helpers.post_provisioning_api(self.get_cli(ip, unregister), description, switches)
            if not helpers.succeded(status_code):
                return self.report_error(status_code, text)
        self.update_registered_switches(switches, unregister)
        return self.report_success()

class RegisterSwitch(Switch):
    def post(self):
        return super().post()

class UnregisterSwitch(Switch):
    def post(self):
        return super().post(unregister=True)

class SwitchList(UFMResource):
    def get(self):
        logging.info(f"GET /plugin/snmp/register")
        return list(self.registered_switches), HTTPStatus.OK

    def post(self):
        return self.report_error(405, "Method is not allowed")

class TrapList(UFMResource):
    def _extract_job_id(self, headers):
        # extract job ID from location header
        location = headers.get("Location")
        if not location:
            return None
        job_id = location.split('/')[-1]
        return job_id

    def get(self):
        logging.info(f"GET /plugin/snmp/trap_list")
        cli = "show snmp events"
        skip_lines = ["", cli, "Events for which traps will be sent:"]
        switch = next(iter(self.switch_dict))
        status_code, guid_to_events = helpers.get_provisioning_output(cli, "Requesting the list of traps", [switch])
        if not helpers.succeded(status_code):
            return self.report_error(status_code, guid_to_events)
        events_raw = list(guid_to_events.values())[0].split("\n")
        events_lines = list(set(events_raw) - set(skip_lines))
        result = []
        for event_line in events_lines:
            try:
                # e.g.: "  cpu-util-high: CPU utilization has risen too high"
                event_arr = event_line.split()
                event = event_arr[0][:-1]
                result.append(event)
            except KeyError as ke:
                return self.report_error(HTTPStatus.INTERNAL_SERVER_ERROR, f"Failed to parse event: {ke}")
        return result, HTTPStatus.OK

    def post(self):
        return self.report_error(405, "Method is not allowed")

class Trap(UFMResource):
    def get(self):
        return self.report_error(405, "Method is not allowed")

    @staticmethod
    def get_cli(event, remove=False):
        cli_add_events = f"snmp-server notify event {event}"
        cli_remove_events = f"no snmp-server notify event {event}"
        return cli_remove_events if remove else cli_add_events

    def post(self, remove=False):
        # TODO: add trap check list - if no such trap, then error
        resource = "remove_trap" if remove == True else "add_trap"
        logging.info(f"POST /plugin/snmp/{resource}")
        if not request.json:
            return self.report_error(HTTPStatus.BAD_REQUEST, "Upload request is empty")
        else:
            json_data = request.get_json(force=True)
            switches = []
            try:
                events = json_data["traps"]
            except KeyError as ke:
                return self.report_error(HTTPStatus.BAD_REQUEST, f"No key {ke} found")
            switches = json_data.get("switches", [])
            if not switches:
                switches = list(self.switch_dict.keys())
            incorrect_switches = set(switches) - set(self.switch_dict.keys())
            if incorrect_switches:
                return self.report_error(HTTPStatus.BAD_REQUEST, f"Switches {incorrect_switches} don't exist in the fabric or don't have an ip")
            description = "UFM event monitoring settings"
            for event in events:
                status_code, text = helpers.post_provisioning_api(self.get_cli(event, remove), description, switches)
                if not helpers.succeded(status_code):
                    return self.report_error(status_code, text)
            return self.report_success()

class AddTrap(Trap):
    def post(self):
        return super().post()

class RemoveTrap(Trap):
    def post(self):
        return super().post(remove=True)

class Dummy(UFMResource):
    def get(self):
        logging.info("GET /plugin/snmp/dummy")
        print("Hello from dummy resource!", flush=True)
        return self.report_success()

    def post(self):
        return self.report_error(HTTPStatus.METHOD_NOT_ALLOWED, "Method is not allowed")
