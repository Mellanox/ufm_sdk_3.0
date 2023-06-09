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
# @author: Haitham Jondi
# @date:   Nov 23, 2022
#

from http import HTTPStatus
from flask import make_response
from api import InvalidConfRequest
from utils.logger import LOG_LEVELS, Logger
from utils.flask_server.base_flask_api_server import BaseAPIApplication


class InventoryAPI(BaseAPIApplication):
    def __init__(self, dataMgr):
        super(InventoryAPI, self).__init__()
        self.dataMgr = dataMgr

    def _get_error_handlers(self):
        return [
            (InvalidConfRequest,
             lambda e: (str(e), HTTPStatus.BAD_REQUEST))
        ]

    def _get_routes(self):
        return {
            self.get: dict(urls=["/"], methods=["GET"]),
            self.get_firmware: dict(urls=["/firmware"], methods=["GET"]),
            self.get_memory: dict(urls=["/memory"], methods=["GET"]),
            self.get_cpu: dict(urls=["/cpu"], methods=["GET"])

        }

    def get(self):
        try:
            return make_response(self.dataMgr.get_inventory_data())
        except Exception as e:
            Logger.log_message("Error occurred : " + str(e), LOG_LEVELS.ERROR)

    def get_firmware(self):
        try:
            return make_response(self.dataMgr.get_memory_data("firmware"))
        except Exception as e:
            Logger.log_message("Error occurred : " + str(e), LOG_LEVELS.ERROR)

    def get_memory(self):
        try:
            return make_response(self.dataMgr.get_memory_data("memory"))
        except Exception as e:
            Logger.log_message("Error occurred : " + str(e), LOG_LEVELS.ERROR)

    def get_cpu(self):
        try:
            return make_response(self.dataMgr.get_cpu_data())
        except Exception as e:
            Logger.log_message("Error occurred : " + str(e), LOG_LEVELS.ERROR)
