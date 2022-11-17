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
import logging


class UFMResource(Resource):
    def __init__(self):
        self.success = 200

    def report_success(self):
        return {}, self.success

    @staticmethod
    def report_error(status_code, message):
        logging.error(message)
        return {"error": message}, status_code


class Dummy(UFMResource):
    def get(self):
        logging.info("GET /plugin/ndt/dummy")
        print("Hello from dummy resource!", flush=True)
        return self.report_success()

    def post(self):
        return self.report_error(405, "Method is not allowed")
