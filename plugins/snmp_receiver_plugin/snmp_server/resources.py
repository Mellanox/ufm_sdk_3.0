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
from datetime import datetime
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
        self.datetime_format = "%Y-%m-%d %H:%M:%S"

    def get_timestamp(self):
        return str(datetime.now().strftime(self.datetime_format))

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
    
    def update_registered_switches(self, switches, unregister=False):
        if unregister:
            self.registered_switches = self.registered_switches - set(switches)
        else:
            self.registered_switches.update(switches)
        with open(helpers.SWITCHES_FILE, "w") as file:
            json.dump(list(self.registered_switches), file)

    @staticmethod
    def get_cli(ip, unregister=False):
        # TODO: change to sha512 and aes-256
        cli_register = f"snmp-server host {ip} traps port {helpers.ConfigParser.snmp_port}"
        if helpers.ConfigParser.snmp_version == 1:
            cli_register += " " + helpers.ConfigParser.community
        if helpers.ConfigParser.snmp_version == 3:
            cli_register += f" version 3 user {helpers.ConfigParser.snmp_user} \
                auth sha {helpers.ConfigParser.snmp_password} priv aes-128 {helpers.ConfigParser.snmp_priv}"
        cli_unregister = f"no snmp-server host {ip}"
        return cli_unregister if unregister else cli_register

    def post(self, unregister=False):
        resource = "unregister" if unregister else "register"
        if not request.data or not request.json:
            switches = list(self.switch_dict.keys())
            hosts = []
        else:
            json_data = request.get_json(force=True)
            try:
                switches = json_data["switches"]
            except (KeyError, TypeError) as e:
                return self.report_error(HTTPStatus.BAD_REQUEST, f"Incorrect format: {e}")
            hosts = json_data.get("hosts", [])
        if not hosts:
            hosts.append(helpers.LOCAL_IP)
        switches_set = set(switches)
        incorrect_switches = list(switches_set - set(self.switch_dict.keys()))
        if incorrect_switches:
            return self.report_error(HTTPStatus.NOT_FOUND, f"Switches {incorrect_switches} don't exist in the fabric or don't have an ip")
        not_registered = switches_set - set(self.registered_switches)
        if unregister:
            if not_registered == switches_set:
                return self.report_error(HTTPStatus.BAD_REQUEST, f"Provided switches are not registered")
            switches = list(switches_set - not_registered)
        else:
            if not not_registered:
                return self.report_error(HTTPStatus.BAD_REQUEST, f"Provided switches have been already registered")
            switches = list(not_registered)
        prefix = "un" if unregister else ""
        description = f"Plugin {prefix}registration as SNMP traps receiver"
        for ip in hosts:
            status_code, guid_to_response = helpers.get_provisioning_output(self.get_cli(ip, unregister), description, switches)
            if not helpers.succeded(status_code):
                return self.report_error(status_code, guid_to_response)
            for guid, (status, summary) in guid_to_response.items():
                if status == helpers.COMPLETED_WITH_ERRORS:
                    logging.error(f"Failed to {resource} switch {guid}: {summary}")
                    for ip, switch in self.switch_dict.items():
                        if switch.guid == guid:
                            switches.remove(ip)
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
        return list(self.registered_switches), HTTPStatus.OK

    def post(self):
        return self.report_error(HTTPStatus.METHOD_NOT_ALLOWED, "Method is not allowed")

class TrapList(UFMResource):
    def get(self):
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
    def update_csv(trap, disable):
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

    def validate_request(self, trap, disable):
        expected_status = "Enabled" if disable else "Disabled"
        with open(helpers.TRAPS_POLICY_FILE, 'r') as traps_info_file:
            csv_traps_info_reader = csv.DictReader(traps_info_file)
            trap_found = False
            for trap_info in csv_traps_info_reader:
                if trap_info["Name"] == trap:
                    trap_found = True
                    status = trap_info["Status"]
                    if expected_status != status:
                        return f"Trap {trap} is already {status}"
            if not trap_found:
                return f"Trap {trap} is not in the list of known plugin traps, see 'trap_list'"
        return ""

    @staticmethod
    def get_cli(trap, disable=False):
        cli_enable_traps = f"snmp-server notify event {trap}"
        cli_disable_traps = f"no snmp-server notify event {trap}"
        return cli_disable_traps if disable else cli_enable_traps

    def post(self, disable=False):
        # TODO: add trap check list - if no such trap, then error
        resource = "disable_trap" if disable == True else "enable_trap"
        if not request.data or not request.json:
            return self.report_error(HTTPStatus.BAD_REQUEST, "Upload request is empty")
        else:
            json_data = request.get_json(force=True)
            switches = []
            try:
                traps = json_data["traps"]
            except (KeyError, TypeError) as e:
                return self.report_error(HTTPStatus.BAD_REQUEST, f"Incorrect format: {e}")
            switches = list(self.switch_dict.keys())
            incorrect_switches = set(switches) - set(self.switch_dict.keys())
            if incorrect_switches:
                return self.report_error(HTTPStatus.NOT_FOUND, f"Switches {incorrect_switches} don't exist in the fabric or don't have an ip")
            description = "UFM event monitoring settings"
            one_succeeded = False
            for trap in traps:
                error = self.validate_request(trap, disable)
                if error:
                    return self.report_error(HTTPStatus.BAD_REQUEST, error)
                status_code, guid_to_response = helpers.get_provisioning_output(self.get_cli(trap, disable), description, switches)
                if not helpers.succeded(status_code):
                    return self.report_error(status_code, guid_to_response)
                for guid, (status, summary) in guid_to_response.items():
                    if status == helpers.COMPLETED_WITH_ERRORS:
                        logging.error(f"Failed to {resource} {trap} on switch {guid}: {summary}")
                    else:
                        one_succeeded = True
                if one_succeeded:
                    logging.warning(f"Succeded to {resource} on some switches, updating trap info")
                    self.update_csv(trap, disable)
                else:
                    return self.report_error(HTTPStatus.BAD_REQUEST, f"Failed to {resource} {trap}, check logs for more information")
            return self.report_success()

class EnableTrap(Trap):
    def post(self):
        return super().post()

class DisableTrap(Trap):
    def post(self):
        return super().post(disable=True)

class Version(UFMResource):
    def get(self):
        version_file = "release.json"
        return self.read_json_file(version_file), HTTPStatus.OK

    def post(self):
        return self.report_error(HTTPStatus.METHOD_NOT_ALLOWED, "Method is not allowed")

class Date(UFMResource):
    def get(self):
        return {"date": self.get_timestamp()}, HTTPStatus.OK

    def post(self):
        return self.report_error(HTTPStatus.METHOD_NOT_ALLOWED, "Method is not allowed")

class Dummy(UFMResource):
    def get(self):
        print("Hello from dummy resource!", flush=True)
        return self.report_success()

    def post(self):
        return self.report_error(HTTPStatus.METHOD_NOT_ALLOWED, "Method is not allowed")
