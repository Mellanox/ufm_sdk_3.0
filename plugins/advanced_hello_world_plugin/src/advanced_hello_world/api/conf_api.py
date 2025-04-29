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
# @author: Anan Al-Aghbar
# @date:   Jan 26, 2023
#
from flask import make_response, request
from http import HTTPStatus

from utils.flask_server.base_flask_api_server import BaseAPIApplication
from utils.config_parser import InvalidConfRequest
from utils.logger import Logger, LOG_LEVELS
from utils.json_schema_validator import validate_schema

from mgr.hello_world_configurations_mgr import HelloWorldConfigParser


class UFMHelloWorldPluginConfigurationsAPI(BaseAPIApplication):

    def __init__(self):
        super(UFMHelloWorldPluginConfigurationsAPI, self).__init__()
        self.conf = HelloWorldConfigParser()

        # for debugging
        # self.conf_schema_path = "plugins/advanced_hello_world_plugin/src/advanced_hello_world/schemas/set_conf.schema.json"

        # for production with docker
        self.conf_schema_path = "advanced_hello_world_plugin/src/advanced_hello_world/schemas/set_conf.schema.json"

    def _get_error_handlers(self):
        return [
            (InvalidConfRequest,
             lambda e: (str(e), HTTPStatus.BAD_REQUEST))
        ]

    def _get_routes(self):
        return {
            self.get_conf: dict(urls=["/"], methods=["GET"]),
            self.update_conf: dict(urls=["/"], methods=["PUT"])
        }

    def get_conf(self):
        try:
            _response = self.conf.conf_to_dict(self.conf_schema_path)
            return make_response(_response)
        except Exception as e:
            Logger.log_message("Error occurred while getting the current plugin configurations: " + str(e),
                               LOG_LEVELS.ERROR)
            raise e

    def update_conf(self):
        Logger.log_message('Updating the plugin configurations',
                           LOG_LEVELS.DEBUG)
        try:
            request_data = request.json
            # validate the new data
            validate_schema(self.conf_schema_path, request_data)
            # update the new values
            self.conf.update_config_file_values(request_data)
            self.conf.update_config_file(self.conf.config_file)
            ####
            _response = self.conf.conf_to_dict(self.conf_schema_path)
            return make_response(_response)
        except Exception as ex:
            Logger.log_message(f'Updating the plugin configurations has been failed: {str(ex)}',
                               LOG_LEVELS.ERROR)
            raise ex
