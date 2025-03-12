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
from http import HTTPStatus
import json
import os

import helpers
import logging


class UFMResource(Resource):
    def __init__(self, switch_dict):
        self.switch_dict = switch_dict
        self.registered_switches = set(self.read_json_file(helpers.ConfigParser.switches_file))
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
