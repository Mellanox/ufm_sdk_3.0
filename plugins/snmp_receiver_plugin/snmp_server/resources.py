#
# Copyright © 2013-2023 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
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
import csv
from flask_restful import Resource
from flask import request
from http import HTTPStatus
import json
import os

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
        return self.report_error(HTTPStatus.METHOD_NOT_ALLOWED, "Method is not allowed")

    @staticmethod
    def get_cli(ip, unregister=False):
        # TODO: change to sha512 and aes-256
        cli_register_v1_v2 = f"snmp-server host {ip} traps port {helpers.ConfigParser.snmp_port}"
        cli_register_v3 = cli_register_v1_v2 + f" version 3 user {helpers.ConfigParser.snmp_user} \
                          auth sha {helpers.ConfigParser.snmp_password} priv aes-128 {helpers.ConfigParser.snmp_priv}"
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
        logging.info(f"GET /plugin/snmp/switch_list")
        return list(self.registered_switches), HTTPStatus.OK

    def post(self):
        return self.report_error(HTTPStatus.METHOD_NOT_ALLOWED, "Method is not allowed")

class TrapList(UFMResource):
    def get(self):
        logging.info(f"GET /plugin/snmp/trap_list")
        with open(helpers.TRAPS_POLICY_FILE, 'r') as traps_info_file:
            result = []
            csvreader = csv.reader(traps_info_file)
            for row in csvreader:
                result.append(row)
            return result, HTTPStatus.OK

    def post(self):
        return self.report_error(HTTPStatus.METHOD_NOT_ALLOWED, "Method is not allowed")

# internal API
class Trap(UFMResource):
    def get(self):
        return self.report_error(HTTPStatus.METHOD_NOT_ALLOWED, "Method is not allowed")

    @staticmethod
    def update_csv(trap, disable=False):
        status = "Disabled" if disable else "Enabled"
        csv_traps_info = []
        field_names = []
        with open(helpers.TRAPS_POLICY_FILE, 'r') as traps_info_file:
            csv_traps_info_reader = csv.DictReader(traps_info_file)
            field_names = csv_traps_info_reader.fieldnames
            for trap_info in csv_traps_info_reader:
                if trap_info["Name"] == trap:
                    trap_info["Status"] = status
                csv_traps_info.append(trap_info)
        with open(helpers.TRAPS_POLICY_FILE, 'w') as traps_info_file:
            csv_traps_info_writer = csv.DictWriter(traps_info_file, field_names)
            csv_traps_info_writer.writeheader()
            csv_traps_info_writer.writerows(csv_traps_info)

    @staticmethod
    def get_cli(trap, disable=False):
        cli_enable_traps = f"snmp-server notify event {trap}"
        cli_disable_traps = f"no snmp-server notify event {trap}"
        return cli_disable_traps if disable else cli_enable_traps

    def post(self, disable=False):
        # TODO: add trap check list - if no such trap, then error
        resource = "disable_trap" if disable == True else "enable_trap"
        logging.info(f"POST /plugin/snmp/{resource}")
        if not request.json:
            return self.report_error(HTTPStatus.BAD_REQUEST, "Upload request is empty")
        else:
            json_data = request.get_json(force=True)
            switches = []
            try:
                traps = json_data["traps"]
            except KeyError as ke:
                return self.report_error(HTTPStatus.BAD_REQUEST, f"No key {ke} found")
            switches = list(self.switch_dict.keys())
            incorrect_switches = set(switches) - set(self.switch_dict.keys())
            if incorrect_switches:
                return self.report_error(HTTPStatus.BAD_REQUEST, f"Switches {incorrect_switches} don't exist in the fabric or don't have an ip")
            description = "UFM event monitoring settings"
            for trap in traps:
                self.update_csv(trap, disable)
                status_code, text = helpers.post_provisioning_api(self.get_cli(trap, disable), description, switches)
                if not helpers.succeded(status_code):
                    return self.report_error(status_code, text)
            return self.report_success()

class EnableTrap(Trap):
    def post(self):
        return super().post()

class DisableTrap(Trap):
    def post(self):
        return super().post(disable=True)

class Version(UFMResource):
    def get(self):
        logging.info("GET /plugin/ndt/version")
        version_file = "release.json"
        return self.read_json_file(version_file), HTTPStatus.OK

    def post(self):
        return self.report_error(HTTPStatus.METHOD_NOT_ALLOWED, "Method is not allowed")

class Dummy(UFMResource):
    def get(self):
        logging.info("GET /plugin/snmp/dummy")
        print("Hello from dummy resource!", flush=True)
        return self.report_success()

    def post(self):
        return self.report_error(HTTPStatus.METHOD_NOT_ALLOWED, "Method is not allowed")
