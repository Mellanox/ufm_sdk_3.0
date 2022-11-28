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
import json
import os
from http import HTTPStatus
from flask import make_response, request
from api import InvalidConfRequest
from utils.logger import LOG_LEVELS, Logger
from utils.flask_server.base_flask_api_server import BaseAPIApplication


class JSONAPI(BaseAPIApplication):
    def __init__(self):
        super(JSONAPI, self).__init__()
        self.full = {}
        self.node = {}
        self.package_info = {}
        self.inventory = {}
        self.resource_util = {}
        self.inventory_hash = {}
        self.package_info_hash = {}
        abs_dts_sim_path = os.path.abspath(__file__)[:os.path.abspath(__file__).rfind('dts_sim')] + 'dts_sim'
        with open(os.path.join(abs_dts_sim_path, 'json_files', 'full.json'), 'r') as f:
            self.full = json.load(f)
        with open(os.path.join(abs_dts_sim_path, 'json_files', 'node.json'), 'r') as f:
            self.node = json.load(f)
        with open(os.path.join(abs_dts_sim_path, 'json_files', 'package_info.json'), 'r') as f:
            self.package_info = json.load(f)
        with open(os.path.join(abs_dts_sim_path, 'json_files', 'resource_util.json'), 'r') as f:
            self.resource_util = json.load(f)
        with open(os.path.join(abs_dts_sim_path, 'json_files', 'inventory.json'), 'r') as f:
            self.inventory = json.load(f)
        with open(os.path.join(abs_dts_sim_path, 'json_files', 'inventory_hash.json'), 'r') as f:
            self.inventory_hash = json.load(f)
        with open(os.path.join(abs_dts_sim_path, 'json_files', 'package_info_hash.json'), 'r') as f:
            self.package_info_hash = json.load(f)

    def _get_error_handlers(self):
        return [
            (InvalidConfRequest,
             lambda e: (str(e), HTTPStatus.BAD_REQUEST))
        ]

    def _get_routes(self):
        return {
            self.get: dict(urls=["/python_dict"], methods=["GET"])
        }

    def get(self):
        args = request.args.to_dict()
        result = self.full
        if "message_type" in args:
            if args["message_type"] == "PackageInfo":
                result = self.package_info
            elif args["message_type"] == "Node":
                result = self.node
            elif args["message_type"] == "Inventory":
                result = self.inventory
            elif args["message_type"] == "ResourceUtil":
                result = self.resource_util
            elif args["message_type"] == "InventoryHash":
                result = self.inventory_hash
            elif args["message_type"] == "PackageInfoHash":
                result = self.package_info_hash

        try:
            res  = make_response(result)
            res.mimetype = 'application/json'
            return res
        except Exception as e:
            Logger.log_message("Error occurred : " + str(e), LOG_LEVELS.ERROR)
