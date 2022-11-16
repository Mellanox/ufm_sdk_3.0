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
# @date:   Nov 09, 2022
#
import os
import sys
sys.path.append(os.getcwd())

from utils.config_parser import ConfigParser


class UFMTelemetryLabelsConfigParser(ConfigParser):
    # for debugging
    # config_file = "../conf/ufm_telemetry_grafana_plugin.cfg"

    # for production with docker
    config_file = "/config/ufm_telemetry_grafana_plugin.cfg"

    UFM_TELEMETRY_ENDPOINT_SECTION = "ufm-telemetry-endpoint"
    UFM_TELEMETRY_ENDPOINT_SECTION_HOST = "host"
    UFM_TELEMETRY_ENDPOINT_SECTION_PORT = "port"
    UFM_TELEMETRY_ENDPOINT_SECTION_URL = "url"

    UFM_SECTION = "ufm"
    UFM_SECTION_PORT = "port"

    def __init__(self):
        super().__init__(read_sdk_config=False)
        self.sdk_config.read(self.config_file)

    def get_telemetry_host(self):
        return self.get_config_value(None,
                                     self.UFM_TELEMETRY_ENDPOINT_SECTION,
                                     self.UFM_TELEMETRY_ENDPOINT_SECTION_HOST,
                                     '127.0.0.1')

    def get_telemetry_port(self):
        return self.safe_get_int(None,
                                 self.UFM_TELEMETRY_ENDPOINT_SECTION,
                                 self.UFM_TELEMETRY_ENDPOINT_SECTION_PORT,
                                 9001)

    def get_telemetry_url(self):
        return self.get_config_value(None,
                                     self.UFM_TELEMETRY_ENDPOINT_SECTION,
                                     self.UFM_TELEMETRY_ENDPOINT_SECTION_URL,
                                     "enterprise")

    def get_ufm_rest_server_port(self):
        return self.safe_get_int(None,
                                 self.UFM_SECTION,
                                 self.UFM_SECTION_PORT,
                                 8000)
