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
from flask import make_response, Response
from api import InvalidConfRequest
from utils.logger import LOG_LEVELS, Logger
from utils.flask_server.base_flask_api_server import BaseAPIApplication
import json


class ResourceUtilAPI(BaseAPIApplication):
    def __init__(self, dataMgr):
        super(ResourceUtilAPI, self).__init__()
        self.dataMgr = dataMgr

    def _get_error_handlers(self):
        return [
            (InvalidConfRequest,
             lambda e: (str(e), HTTPStatus.BAD_REQUEST))
        ]

    def _get_routes(self):
        return {
            self.get: dict(urls=["/"], methods=["GET"]),
        }

    def get(self):
        try:
            package_info = self.dataMgr.get_resource_util_data()
            res = make_response(json.dumps(package_info, indent=4))
            res.mimetype = 'application/json'
            return res
        except Exception as e:
            Logger.log_message("Error occurred : " + str(e), LOG_LEVELS.ERROR)
