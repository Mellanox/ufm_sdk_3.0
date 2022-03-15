"""
@copyright:
    Copyright (C) Mellanox Technologies Ltd. 2021. ALL RIGHTS RESERVED.

    This software product is a proprietary product of Mellanox Technologies
    Ltd. (the "Company") and all right, title, and interest in and to the
    software product, including all associated intellectual property rights,
    are and shall remain exclusively with the Company.

    This software product is governed by the End User License Agreement
    provided with the software product.

@author: Nahum Kilim
@date:   September 20, 2021
"""

import configparser
import json
import os
from flask_restful import Resource
from flask import request
from datetime import datetime, timedelta
from topo_diff.topo_diff import compare_topologies
import logging
import hashlib


class UFMResource(Resource):
    # config_file_name = "../build/config/ndt.conf"
    # periodic_request_file = "../build/config/periodic_request.json"
    config_file_name = "/config/ndt.conf"
    periodic_request_file = "/config/periodic_request.json"

    def __init__(self):
        self.response_file = ""
        # self.reports_dir = "reports"
        # self.ndts_dir = "ndts"
        self.reports_dir = "/config/reports"
        self.ndts_dir = "/config/ndts"
        self.reports_list_file = os.path.join(self.reports_dir, "reports_list.json")
        self.ndts_list_file = os.path.join(self.ndts_dir, "ndts_list.json")
        self.success = 200
        self.reports_to_save = 10
        self.validation_enabled = True
        self.switch_patterns = []
        self.host_patterns = []
        self.datetime_format = "%Y-%m-%d %H:%M:%S"
        self.ufm_port = 8000
        self.expected_keys = set()
        # self.version_file = "release.json"
        # self.help_file = "help.json"
        self.version_file = "/opt/ufm/ufm_plugin_ndt/ufm_sim_web_service/release.json"
        self.help_file = "/opt/ufm/ufm_plugin_ndt/ufm_sim_web_service/help.json"

        self.create_reports_file(self.reports_list_file)
        self.create_reports_file(self.ndts_list_file)
        self.parse_config()

    def parse_config(self):
        ndt_config = configparser.ConfigParser()
        if os.path.exists(self.config_file_name):
            ndt_config.read(self.config_file_name)
            self.reports_to_save = ndt_config.getint("Common", "reports_to_save", fallback=10)
            self.ufm_port = ndt_config.getint("Common", "ufm_port", fallback=8000)
            self.validation_enabled = ndt_config.getboolean("Validation", "enabled", fallback=True)
            if self.validation_enabled:
                switch_patterns_str = ndt_config.get("Validation", "switch_patterns")
                self.switch_patterns = switch_patterns_str.split(',')
                host_patterns_str = ndt_config.get("Validation", "host_patterns")
                self.host_patterns = host_patterns_str.split(',')
            else:
                self.switch_patterns = []
                self.host_patterns = []

    def get_ndt_path(self, file_name):
        return os.path.join(self.ndts_dir, file_name)

    def get_report_path(self, file_name):
        return os.path.join(self.reports_dir, file_name)

    def get(self):
        return self.read_json_file(self.response_file), self.success

    def post(self):
        return self.report_success()

    def report_success(self):
        return {}, self.success

    def check_request_keys(self, json_data):
        try:
            keys_dict = json_data.keys()
        except:
            return "Request format is incorrect", 400
        extra_keys = keys_dict - self.expected_keys
        if extra_keys:
            return "Incorrect format, extra keys in request: {}".format(extra_keys), 400
        missing_keys = self.expected_keys - keys_dict
        if missing_keys:
            return "Incorrect format, missing keys in request: {}".format(missing_keys), 400
        return self.report_success()

    @staticmethod
    def read_json_file(file_name):
        with open(file_name, "r", encoding="utf-8") as file:
            # unhandled exception in case some of the files was changed manually
            data = json.load(file)
        return data

    @staticmethod
    def create_reports_file(file_name):
        if not os.path.exists(file_name):
            logging.info("Creating {}".format(file_name))
            with open(file_name, "w") as file:
                json.dump([], file)

    @staticmethod
    def report_error(status_code, message):
        logging.error(message)
        return {"error": message}, status_code

    def get_timestamp(self):
        return str(datetime.now().strftime(self.datetime_format))


def get_hash(file_content):
    sha1 = hashlib.sha1()
    sha1.update(file_content.encode('utf-8'))
    return sha1.hexdigest()


class Upload(UFMResource):
    def __init__(self):
        super().__init__()
        self.possible_file_types = ["switch_to_switch", "switch_to_host"]
        self.file_name = ""
        self.sha1 = ""
        self.file_type = ""
        self.expected_checksum = ""
        self.expected_keys = ["file_name", "file", "file_type", "sha-1"]

    def get(self):
        return self.report_error(405, "Method is not allowed")

    def parse_request(self, json_data):
        logging.debug("Parsing JSON request: {}".format(json_data))
        response, status_code = self.check_request_keys(json_data)
        if status_code != self.success:
            return "", (response, status_code)
        self.file_name = json_data["file_name"]
        if not self.file_name:
            return "", ("File name is empty", 400)
        file_content = json_data["file"]
        self.file_type = json_data["file_type"]
        if self.file_type not in self.possible_file_types:
            return "", ("Incorrect file type. Possible file types: {}."
                        .format(",".join(self.possible_file_types)), 400)
        self.expected_checksum = json_data["sha-1"]
        return file_content, self.report_success()

    def check_sha1(self, file_content):
        self.sha1 = get_hash(file_content)
        file_content = file_content.replace('\r\n', '\n')
        if self.expected_checksum != self.sha1:
            return "", ("Provided sha-1 {} for {} is different from actual one {}"
                        .format(self.expected_checksum, self.file_name, self.sha1), 400)
        else:
            return file_content, self.report_success()

    def update_ndts_list(self):
        with open(self.ndts_list_file, "r+") as file:
            # unhandled exception in case ndts file was changed manually
            data = json.load(file)
            if not os.path.exists(self.get_ndt_path(self.file_name)):
                entry = {"file": self.file_name,
                         "timestamp": self.get_timestamp(),
                         "sha-1": self.sha1,
                         "file_type": self.file_type}
                logging.debug("New NDT: {}".format(entry))
                data.append(entry)
            else:
                for entry in data:
                    if entry["file"] == self.file_name:
                        entry["timestamp"] = self.get_timestamp()
                        entry["sha-1"] = self.sha1
                        entry["file_type"] = self.file_type
            file.seek(0)
            json.dump(data, file)
        return self.report_success()

    def save_ndt(self, file_content):
        logging.debug("Uploading file: {}".format(self.file_name))
        with open(self.get_ndt_path(self.file_name), "w") as file:
            try:
                file.write(file_content)
                return self.report_success()
            except OSError as oe:
                return self.report_error(500, "Cannot save ndt {}: {}".format(self.file_name, oe))

    def post(self):
        logging.info("POST /plugin/ndt/upload")
        error_status_code, error_response = self.success, []
        if not request.json:
            return self.report_error(400, "Upload request is empty")
        else:
            json_data = request.get_json(force=True)
            logging.debug("Parsing JSON request: {}".format(json_data))
            for file_dict in json_data:
                file_content, (response, status_code) = self.parse_request(file_dict)
                if status_code != self.success:
                    error_status_code = status_code
                    error_response.append(response)
                    continue
                file_content, (response, status_code) = self.check_sha1(file_content)
                if status_code != self.success:
                    error_status_code = status_code
                    error_response.append(response)
                    continue
                response, status_code = self.update_ndts_list()
                if status_code != self.success:
                    error_status_code = status_code
                    error_response.append(response)
                    continue
                response, status_code = self.save_ndt(file_content)
                if status_code != self.success:
                    error_status_code = status_code
                    error_response.append(response)

            if error_status_code == self.success:
                return self.report_success()
            else:
                return self.report_error(error_status_code, error_response)


class Delete(UFMResource):
    def __init__(self):
        super().__init__()
        self.ndts_to_delete = []
        self.expected_keys = ["file_name"]

    def get(self):
        return self.report_error(405, "Method is not allowed")

    def delete_ndt(self, file_name):
        logging.debug("Deleting file: {}".format(file_name))
        try:
            os.remove(self.get_ndt_path(file_name))
            return self.report_success()
        except FileNotFoundError:
            return "Cannot remove {}: file not found".format(file_name), 400

    def parse_request(self, json_data, file_name, validate_keys=True):
        logging.debug("Parsing JSON request: {}".format(json_data))
        if validate_keys:
            response, status_code = self.check_request_keys(json_data)
            if status_code != self.success:
                return "", (response, status_code)
        file = json_data[file_name]
        if not file:
            return "", ("File name is empty", 400)
        return file, self.report_success()

    def update_ndts_list(self, json_data):
        error_response = []
        with open(self.ndts_list_file, "r", encoding="utf-8") as file:
            # unhandled exception in case ndts file was changed manually
            data = json.load(file)
            for ndt_dict in json_data:
                ndt_to_delete, (response, status_code) = self.parse_request(ndt_dict, "file_name")
                if status_code != self.success:
                    error_response.append(response)
                    continue
                for ndt_record in list(data):
                    ndt_file, (response, status_code) = self.parse_request(ndt_record, "file", False)
                    if status_code != self.success:
                        error_response.append(response)
                        continue
                    if ndt_to_delete == ndt_file:
                        data.remove(ndt_record)
                        self.ndts_to_delete.append(ndt_to_delete)
                        break
                else:
                    error_response.append("Cannot remove {}: file not found".format(ndt_to_delete))
        with open(self.ndts_list_file, "w") as file:
            json.dump(data, file)
        if error_response:
            return error_response, 400
        else:
            return self.report_success()

    def post(self):
        logging.info("POST /plugin/ndt/delete")
        if not request.json:
            return self.report_error(400, "Upload request is empty")
        else:
            error_status_code, error_response = self.success, []
            json_data = request.get_json(force=True)
            response, status_code = self.update_ndts_list(json_data)
            if status_code != self.success:
                error_status_code = status_code
                error_response.extend(response)
            for ndt in self.ndts_to_delete:
                response, status_code = self.delete_ndt(ndt)
                if status_code != self.success:
                    error_status_code = status_code
                    error_response.append(response)

            if error_status_code == self.success:
                return self.report_success()
            else:
                return self.report_error(error_status_code, error_response)


class Compare(UFMResource):
    def __init__(self, scheduler):
        super().__init__()
        self.scheduler = scheduler
        self.report_number = 0
        self.timestamp = ""
        self.interval = 0
        self.datetime_start = None
        self.datetime_end = None
        self.expected_keys_first_level = ["run"]
        self.expected_keys_second_level = ["startTime", "endTime", "interval"]

    def get(self):
        return self.report_error(405, "Method is not allowed")

    def update_reports_list(self, scope):
        with open(self.reports_list_file, "r", encoding="utf-8") as reports_list_file:
            # unhandled exception in case reports file was changed manually
            data = json.load(reports_list_file)
            self.report_number = len(data) + 1
            entry = {"report_id": self.report_number,
                     "report_scope": scope,
                     "timestamp": self.timestamp}
            if self.report_number > self.reports_to_save:
                oldest_report = self.get_report_path("report_1.json")
                # unhandled exception in case report was deleted or renamed manually
                os.remove(oldest_report)
                data.remove(data[0])
                for report in data:
                    report["report_id"] -= 1
                    os.rename(self.get_report_path("report_{}.json".format(report["report_id"] + 1)),
                              self.get_report_path("report_{}.json".format(report["report_id"])))
                self.report_number -= 1
                entry["report_id"] = self.report_number
            data.append(entry)
        with open(self.reports_list_file, "w") as reports_list_file:
            json.dump(data, reports_list_file)

        return self.report_success()

    def save_report(self, file_content):
        report = os.path.join(self.reports_dir, "report_{}.json".format(self.report_number))
        logging.debug("Report file name: {}".format(report))
        try:
            with open(report, "w") as report_file:
                json.dump(file_content, report_file)
                return self.report_success()
        except OSError as oe:
            return self.report_error(500, "Cannot save report {}: {}".format(report, oe))

    def create_report(self, scope, report_content):
        response, status_code = self.update_reports_list(scope)
        if status_code != self.success:
            return response, status_code
        response, status_code = self.save_report(report_content)
        if status_code != self.success:
            return response, status_code
        return self.report_success()

    def compare(self, scope="Periodic"):
        logging.info("Run topology comparison")
        if scope == 'Periodic':
            self.parse_config()
        self.timestamp = self.get_timestamp()
        report_content = compare_topologies(self.timestamp, self.ndts_list_file,
                                            self.switch_patterns, self.host_patterns,
                                            self.ufm_port)

        if report_content["error"]:
            response, status_code = self.create_report(scope, report_content)
            if status_code != self.success:
                return response, status_code
            return self.report_error(400, report_content["error"])

        if not report_content["report"]["miss_wired"]\
                and not report_content["report"]["missing_in_ufm"]\
                and not report_content["report"]["missing_in_ndt"]:
            report_content["response"] = "NDT and UFM are fully match"
            report_content.pop("error")
            report_content.pop("report")

        response, status_code = self.create_report(scope, report_content)
        if status_code != self.success:
            return response, status_code
        return self.report_success()

    def parse_request(self, json_data):
        logging.debug("Parsing JSON request: {}".format(json_data))
        try:
            self.expected_keys = self.expected_keys_first_level
            response, status_code = self.check_request_keys(json_data)
            if status_code != self.success:
                return self.report_error(status_code, response)
            params = json_data["run"]
            self.expected_keys = self.expected_keys_second_level
            response, status_code = self.check_request_keys(params)
            if status_code != self.success:
                return self.report_error(status_code, response)
            start_time = params["startTime"]
            end_time = params["endTime"]
            self.interval = params["interval"]
            try:
                self.interval = int(self.interval)
                if self.interval < 5:
                    return self.report_error(400, "Minimal interval value is 5 minutes")
            except ValueError:
                return self.report_error(400, "Interval '{}' is not valid".format(self.interval))
            timestamp = datetime.strptime(self.get_timestamp(), self.datetime_format)
            self.datetime_start = datetime.strptime(start_time, self.datetime_format)
            while timestamp > self.datetime_start:
                self.datetime_start += timedelta(minutes=self.interval)
            self.datetime_end = datetime.strptime(end_time, self.datetime_format)
            if self.datetime_end < timestamp:
                logging.info("End time is: {}, current time is: {}"
                .format(self.datetime_end.strftime(self.datetime_format), timestamp.strftime(self.datetime_format)))
                return self.report_error(400, "End time is less than current time")
            return self.report_success()
        except TypeError:
            return self.report_error(400, "Incorrect format, failed to parse timestamp")
        except ValueError as ve:
            return self.report_error(400, "Incorrect timestamp format: {}".format(ve))

    def add_scheduler_jobs(self):
        try:
            while self.datetime_start <= self.datetime_end:
                self.scheduler.add_job(func=self.compare, run_date=self.datetime_start)
                self.datetime_start += timedelta(minutes=self.interval)
            return self.report_success()
        except Exception as e:
            return self.report_error(400, "Periodic comparison failed to start: {}".format(e))

    def post(self):
        logging.info("POST /plugin/ndt/compare")
        if request.json:
            if len(self.scheduler.get_jobs()):
                return self.report_error(400, "Periodic comparison is already running")
            json_data = request.get_json(force=True)
            with open(UFMResource.periodic_request_file, "w") as file:
                json.dump(json_data, file)
            response, status_code = self.parse_request(json_data)
            if status_code != self.success:
                return response, status_code
            return self.add_scheduler_jobs()
        else:
            logging.info("Running instant topology comparison")
            return self.compare("Instant")


class Cancel(UFMResource):
    def __init__(self, scheduler):
        super().__init__()
        self.scheduler = scheduler

    def post(self):
        try:
            if os.path.exists(UFMResource.periodic_request_file):
                os.remove(UFMResource.periodic_request_file)
            if len(self.scheduler.get_jobs()):
                self.scheduler.remove_all_jobs()
                return self.report_success()
            else:
                return self.report_error(400, "Periodic comparison is not running")
        except Exception as e:
            return self.report_error(400, "Failed to cancel periodic comparison: {}".format(e))

    def get(self):
        return self.report_error(405, "Method is not allowed")


class ReportId(UFMResource):
    def __init__(self):
        super().__init__()
        # unhandled exception in case reports file was deleted manually
        with open(self.reports_list_file, "r", encoding="utf-8") as file:
            self.data = json.load(file)

    def post(self, report_id):
        return self.report_error(405, "Method is not allowed")

    def get(self, report_id):
        logging.info("GET /plugin/ndt/reports")
        # unhandled exception in case reports file was changed manually
        try:
            report_id = int(report_id)
        except ValueError:
            return self.report_error(400, "Report id '{}' is not valid".format(report_id))
        if 1 <= report_id <= len(self.data):
            self.response_file = \
                os.path.join(self.reports_dir,
                             "report_{}.json".format(report_id))
            logging.debug("Report found: {}".format(self.response_file))
        else:
            return self.report_error(400, "Report {} not found".format(report_id))

        return super().get()


class Reports(UFMResource):
    def __init__(self):
        logging.info("GET /plugin/ndt/reports")
        super().__init__()
        self.response_file = self.reports_list_file

    def post(self):
        return self.report_error(405, "Method is not allowed")


class Ndts(UFMResource):
    def __init__(self):
        logging.info("GET /plugin/ndt/list")
        super().__init__()
        self.response_file = self.ndts_list_file

    def post(self):
        return self.report_error(405, "Method is not allowed")


class Version(UFMResource):
    def __init__(self):
        logging.info("GET /plugin/ndt/version")
        super().__init__()
        self.response_file = self.version_file

    def post(self):
        return self.report_error(405, "Method is not allowed")


class Help(UFMResource):
    def __init__(self):
        logging.info("GET /plugin/ndt/version")
        super().__init__()
        self.response_file = self.help_file

    def post(self):
        return self.report_error(405, "Method is not allowed")


class Date(UFMResource):
    def get(self):
        logging.info("GET /plugin/ndt/date")
        return {"date": self.get_timestamp()}, self.success

    def post(self):
        return self.report_error(405, "Method is not allowed")


class Dummy(UFMResource):
    def get(self):
        logging.info("GET /plugin/ndt/dummy")
        print("Hello from dummy resource!", flush=True)
        return self.report_success()

    def post(self):
        return self.report_error(405, "Method is not allowed")
