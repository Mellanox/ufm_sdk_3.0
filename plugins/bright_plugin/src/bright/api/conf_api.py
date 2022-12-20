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
# @date:   Dec 14, 2022
#
from flask import make_response, request
from http import HTTPStatus

from utils.utils import Utils
from utils.flask_server.base_flask_api_server import BaseAPIApplication
from utils.config_parser import InvalidConfRequest
from utils.logger import Logger, LOG_LEVELS
from utils.json_schema_validator import validate_schema

from mgr.bright_configurations_mgr import BrightConfigParser
from mgr.bright_data_polling_mgr import BrightDataPollingMgr


class UFMBrightPluginConfigurationsAPI(BaseAPIApplication):

    def __init__(self):
        super(UFMBrightPluginConfigurationsAPI, self).__init__()
        self.conf = BrightConfigParser.getInstance()

        # for debugging
        # self.conf_schema_path = "plugins/bright_plugin/src/bright/schemas/set_conf.schema.json"

        # for production with docker
        self.conf_schema_path = "bright_plugin/src/bright/schemas/set_conf.schema.json"

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
            conf_dict = self.conf.conf_to_dict(self.conf_schema_path)
            return make_response(conf_dict)
        except Exception as e:
            Logger.log_message("Error occurred while getting the current plugin configurations: " + str(e), LOG_LEVELS.ERROR)
            raise e

    def update_conf(self):
        Logger.log_message('Updating the plugin configurations', LOG_LEVELS.DEBUG)
        try:
            request_data = request.json
            # validate the new data
            validate_schema(self.conf_schema_path, request_data)
            # update the new values
            self.conf.update_config_file_values(request_data)
            self.conf.update_config_file(self.conf.config_file)
            ####
            bright_config_payload_section = request_data.get(self.conf.BRIGHT_CONFIG_SECTION)
            if bright_config_payload_section:
                # if the payload contains bright-config.cert info, update the relevant files
                cert = bright_config_payload_section.get(self.conf.BRIGHT_CONFIG_SECTION_CERTIFICATE)
                if cert:
                    Utils.write_text_to_file(
                        self.conf.cert_file_path,
                        cert
                    )

                cert_key = request_data.get(self.conf.BRIGHT_CONFIG_SECTION).get(
                    self.conf.BRIGHT_CONFIG_SECTION_CERTIFICATE_KEY)
                if cert_key:
                    Utils.write_text_to_file(
                        self.conf.cert_key_file_path,
                        cert_key
                    )

                # if the payload contains the bright-config.enabled flag, update the polling
                enabled = bright_config_payload_section.get(self.conf.BRIGHT_CONFIG_SECTION_ENABLED, None)
                if enabled is not None:
                    polling_mgr = BrightDataPollingMgr.getInstance()
                    polling_mgr.trigger_polling()

            return make_response(self.conf.conf_to_dict(self.conf_schema_path))
        except Exception as ex:
            Logger.log_message(f'Updating the plugin configurations has been failed: {str(ex)}', LOG_LEVELS.ERROR)
            raise ex
