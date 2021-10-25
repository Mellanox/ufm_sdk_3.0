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
    config_file_name = "/config/ndt.conf"
    # config_file_name = "../build/config/ndt.conf"

    def __init__(self):
        self.response_file = ""
        # self.reports_dir = "reports"
        # self.ndts_dir = "ndts"
        self.reports_dir = "/data/reports"
        self.ndts_dir = "/data/ndts"
        self.reports_list_file = os.path.join(self.reports_dir, "reports_list.json")
        self.ndts_list_file = os.path.join(self.ndts_dir, "ndts_list.json")
        self.success = 200
        self.reports_to_save = 10

        self.create_reports_file(self.reports_list_file)
        self.create_reports_file(self.ndts_list_file)
        self.parse_config()

    def parse_config(self):
        ndt_config = configparser.ConfigParser()
        if os.path.exists(self.config_file_name):
            ndt_config.read(self.config_file_name)
            self.reports_to_save = ndt_config.getint("Common", "reports_to_save",
                                                     fallback=10)

    def create_reports_file(self, file_name):
        try:
            logging.info("Creating {}".format(file_name))
            if not os.path.exists(file_name):
                with open(file_name, "w") as file:
                    json.dump([], file)
        except OSError as oe:
            return self.report_error(500, "Cannot create file {}: {}".format(file_name, oe))

    def get_ndt_path(self, file_name):
        return os.path.join(self.ndts_dir, file_name)

    def get_report_path(self, file_name):
        return os.path.join(self.reports_dir, file_name)

    @staticmethod
    def read_json_file(file_name):
        try:
            with open(file_name) as file:
                data = json.load(file)
        except Exception as ex:
            logging.error(ex)
            data = {}
        return data

    def get(self):
        return self.read_json_file(self.response_file), self.success

    def post(self):
        return self.success

    @staticmethod
    def report_error(status_code, message):
        logging.error(message)
        return status_code


def get_timestamp():
    return str(datetime.now())


def get_hash(file_content):
    sha1 = hashlib.sha1()
    sha1.update(file_content.encode('utf-8'))
    return sha1.hexdigest()


class UploadMetadata(UFMResource):
    def __init__(self):
        super().__init__()
        self.file_name = ""
        self.sha1 = ""
        self.file_type = ""
        self.expected_checksum = ""

    def get(self):
        return {}, self.report_error(405, "Method is not allowed")

    def parse_request(self, json_data):
        try:
            self.file_name = json_data["file_name"]
            file_content = json_data["file"]
            self.file_type = json_data["file_type"]
            self.expected_checksum = json_data["sha-1"]
            return self.success, file_content
        except KeyError as ke:
            return self.report_error(400, "No such key in request: {}".format(ke)), {}

    def check_sha1(self, file_content):
        self.sha1 = get_hash(file_content)
        file_content = file_content.replace('\r\n', '\n')

        if self.expected_checksum != self.sha1:
            return self.report_error(400, "Provided sha-1 {} is not equal to actual one {}"
                                     .format(self.expected_checksum, self.sha1)), {}
        else:
            return self.success, file_content

    def update_ndts_list(self):
        try:
            with open(self.ndts_list_file, "r+") as file:
                data = json.load(file)
                if not os.path.exists(self.get_ndt_path(self.file_name)):
                    entry = {"file": self.file_name,
                             "timestamp": get_timestamp(),
                             "sha-1": self.sha1,
                             "file_type": self.file_type}
                    logging.debug("New NDT: {}".format(entry))
                    data.append(entry)
                else:
                    for entry in data:
                        try:
                            if entry["file"] == self.file_name:
                                entry["timestamp"] = get_timestamp()
                                entry["sha-1"] = self.sha1
                                entry["file_type"] = self.file_type
                        except KeyError as ke:
                            return self.report_error(400, "No such key in ndts list: {}".format(ke))
                file.seek(0)
                json.dump(data, file)
            return self.success
        except FileNotFoundError as fnfe:
            return self.report_error(400, "Cannot open ndts list, {}".format(fnfe))

    def save_ndt(self, file_content):
        logging.debug("Uploading file: {}".format(self.file_name))
        with open(self.get_ndt_path(self.file_name), "w") as file:
            try:
                file.write(file_content)
                return self.success
            except OSError as oe:
                return self.report_error(500, "Cannot save ndt {}: {}".format(self.file_name, oe))

    def post(self):
        logging.info("POST /plugin/ndt/upload_metadata")
        if not request.data:
            return self.report_error(400, "Upload request is empty")
        else:
            json_data = request.get_json(force=True)
            logging.debug("Parsing JSON request: {}".format(json_data))
            for file_dict in json_data:
                status_code, file_content = self.parse_request(file_dict)
                if status_code != self.success:
                    return status_code
                status_code, file_content = self.check_sha1(file_content)
                if status_code != self.success:
                    return status_code
                status_code = self.update_ndts_list()
                if status_code != self.success:
                    return status_code
                status_code = self.save_ndt(file_content)
                if status_code != self.success:
                    return status_code


class Delete(UFMResource):
    def __init__(self):
        super().__init__()
        self.ndts_to_delete = []

    def get(self):
        return {}, self.report_error(405, "Method is not allowed")

    def delete_ndt(self, file_name):
        logging.debug("Deleting file: {}".format(file_name))
        try:
            os.remove(self.get_ndt_path(file_name))
            return self.success
        except FileNotFoundError as fnfe:
            return self.report_error(400, "Cannot remove, {}".format(fnfe))

    def parse_request(self, json_data, key):
        logging.debug("Parsing JSON request: {}".format(json_data))
        try:
            return json_data[key], self.success
        except KeyError as ke:
            return "", self.report_error(400, "No such key in request: {}".format(ke))

    def update_ndts_list(self, json_data):
        try:
            with open(self.ndts_list_file, "r") as file:
                data = json.load(file)
                for ndt_dict in json_data:
                    ndt_to_delete, status_code = self.parse_request(ndt_dict, "file_name")
                    if status_code != self.success:
                        return status_code
                    for ndt_record in list(data):
                        try:
                            ndt_file, status_code = self.parse_request(ndt_record, "file")
                            if status_code != self.success:
                                return status_code
                            if ndt_to_delete == ndt_file:
                                data.remove(ndt_record)
                                self.ndts_to_delete.append(ndt_to_delete)
                        except KeyError as ke:
                            return self.report_error(400, "No such entry in ndts list: {}".format(ke))
            with open(self.ndts_list_file, "w") as file:
                json.dump(data, file)
            return self.success
        except FileNotFoundError as fnfe:
            return self.report_error(400, "Cannot open ndts list, {}".format(fnfe))

    def post(self):
        logging.info("POST /plugin/ndt/delete")
        if not request.data:
            return self.report_error(400, "Upload request is empty")
        else:
            json_data = request.get_json(force=True)
            status_code = self.update_ndts_list(json_data)
            if status_code != self.success:
                return status_code
            for ndt in self.ndts_to_delete:
                status_code = self.delete_ndt(ndt)
                if status_code != self.success:
                    return status_code


class Compare(UFMResource):
    def __init__(self, scheduler):
        super().__init__()
        self.scheduler = scheduler
        self.report_number = 0
        self.timestamp = ""
        self.interval = 0
        self.datetime_start = None
        self.datetime_end = None

    def get(self):
        return {}, self.report_error(405, "Method is not allowed")

    def update_reports_list(self, scope):
        try:
            with open(self.reports_list_file, "r+") as reports_list_file:
                data = json.load(reports_list_file)
                self.report_number = len(data) + 1
                entry = {"report_id": self.report_number,
                         "report_scope": scope,
                         "timestamp": self.timestamp}
                if self.report_number > self.reports_to_save:
                    try:
                        oldest_report = self.get_report_path("report_1.json")
                        os.remove(oldest_report)
                    except FileNotFoundError as fnfe:
                        return self.report_error(400, "Cannot remove, {}".format(fnfe))
                    data.remove(data[0])
                    for report in data:
                        report["report_id"] -= 1
                        os.rename(self.get_report_path("report_{}.json".format(report["report_id"] + 1)),
                                  self.get_report_path("report_{}.json".format(report["report_id"])))
                    self.report_number -= 1
                    entry["report_id"] = self.report_number

                data.append(entry)
                reports_list_file.seek(0)
                json.dump(data, reports_list_file)
                return self.success
        except FileNotFoundError as fnfe:
            return self.report_error(400, "Cannot open reports list, {}".format(fnfe))

    def save_report(self, file_content):
        report = os.path.join(self.reports_dir, "report_{}.json".format(self.report_number))
        logging.debug("Report file name: {}".format(report))
        try:
            with open(report, "w") as report_file:
                json.dump(file_content, report_file)
                return self.success
        except OSError as oe:
            return self.report_error(500, "Cannot save report {}: {}".format(report, oe))

    def compare(self, scope="Periodic"):
        logging.info("Run topology comparison")
        self.timestamp = get_timestamp()
        report_content = compare_topologies(self.timestamp, self.ndts_list_file)

        status_code = self.update_reports_list(scope)
        if status_code != self.success:
            return status_code
        status_code = self.save_report(report_content)
        if status_code != self.success:
            return status_code

    def parse_request(self, json_data):
        try:
            params = json_data["run"]
            start_time = params["startTime"]
            end_time = params["endTime"]
            self.interval = params["interval"]
            self.datetime_start = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
            self.datetime_end = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
            return self.success
        except KeyError as ke:
            return self.report_error(400, "No such key in request: {}".format(ke))
        except TypeError as te:
            return self.report_error(400, "Failed to parse timestamp: {}".format(te))

    def start_scheduler(self):
        while self.datetime_start <= self.datetime_end:
            self.scheduler.add_job(func=self.compare, run_date=self.datetime_start)
            self.datetime_start += timedelta(minutes=self.interval)
        try:
            self.scheduler.start()
            return self.success
        except Exception as e:
            return self.report_error(400, "Scheduler failed to start: {}".format(e))

    def post(self):
        logging.info("POST /plugin/ndt/compare")
        if request.data:
            json_data = request.get_json(force=True)
            logging.debug("Parsing JSON request: {}".format(json_data))
            status_code = self.parse_request(json_data)
            if status_code != self.success:
                return status_code
            return self.start_scheduler()
        else:
            logging.info("Running instant topology comparison")
            return self.compare("Instant")


class Cancel(UFMResource):
    def __init__(self, scheduler):
        super().__init__()
        self.scheduler = scheduler

    def post(self):
        try:
            self.scheduler.remove_all_jobs()
            return super().get()
        except Exception as e:
            return {}, self.report_error(400, "Failed to cancel scheduler jobs: {}".format(e))

    def get(self):
        return self.report_error(405, "Method is not allowed")


class ReportId(UFMResource):
    def __init__(self):
        super().__init__()
        try:
            with open(self.reports_list_file, "r") as file:
                self.data = json.load(file)
        except FileNotFoundError as fnfe:
            self.report_error(400, "Cannot open reports list, {}".format(fnfe))
            self.data = {}

    def post(self):
        return self.report_error(405, "Method is not allowed")

    def get(self, report_id):
        logging.info("GET /plugin/ndt/reports")
        for entry in self.data:
            try:
                if entry["report_id"] == int(report_id):
                    self.response_file = \
                        os.path.join(self.reports_dir,
                                     "report_{}.json".format(report_id))
                    logging.debug("Report found: {}".format(self.response_file))
                    break
            except KeyError as ke:
                return self.report_error(400, "No such key in request: {}".format(ke))
        else:
            logging.debug("Report {} not found".format(report_id))

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
