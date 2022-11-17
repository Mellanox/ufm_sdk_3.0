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
# @author: Anan Al-Aghbar
# @date:   Nov 16, 2022
#

from http import HTTPStatus
from flask import make_response, request
from utils.config_parser import InvalidConfRequest
from utils.logger import LOG_LEVELS, Logger
from utils.json_schema_validator import validate_schema
from utils.flask_server.base_flask_api_server import BaseAPIApplication


class UFMTelemetryGrafanaConfigurationsAPI(BaseAPIApplication):

    def __init__(self, conf):
        super(UFMTelemetryGrafanaConfigurationsAPI, self).__init__()
        self.conf = conf

        # for debugging
        # self.conf_schema_path = "plugins/grafana_infiniband_telemetry_plugin/src/schemas/set_conf.schema.json"

        # for production with docker
        self.conf_schema_path = "grafana_infiniband_telemetry_plugin/src/schemas/set_conf.schema.json"

    def _get_error_handlers(self):
        return [
            (InvalidConfRequest,
             lambda e: (str(e), HTTPStatus.BAD_REQUEST))
        ]

    def _get_routes(self):
        return {
            self.get: dict(urls=["/"], methods=["GET"]),
            self.put: dict(urls=["/"], methods=["PUT"])
        }

    def get(self):
        try:
            conf_dict = self.conf.conf_to_dict(self.conf_schema_path)
            return make_response(conf_dict)
        except Exception as e:
            Logger.log_message("Error occurred while getting the current plugin configurations: " + str(e), LOG_LEVELS.ERROR)

    def put(self):
        Logger.log_message('Updating the plugin configurations', LOG_LEVELS.DEBUG)
        try:
            request_data = request.json
            # validate the new data
            validate_schema(self.conf_schema_path, request_data)
            # update the new values
            self.conf.update_config_file_values(request_data)
            self.conf.update_config_file(self.conf.config_file)
            return make_response("set configurations has been done successfully")
        except Exception as ex:
            Logger.log_message(f'Updating the plugin configurations has been failed: {str(ex)}', LOG_LEVELS.ERROR)
            raise ex