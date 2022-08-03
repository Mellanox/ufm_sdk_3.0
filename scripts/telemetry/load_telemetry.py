#!/usr/bin/python3

"""
@copyright:
    Copyright (C) 2013-2022 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.

    This software product is a proprietary product of Nvidia Corporation and its affiliates
    (the "Company") and all right, title, and interest in and to the software
    product, including all associated intellectual property rights, are and
    shall remain exclusively with the Company.

    This software product is governed by the End User License Agreement
    provided with the software product.

@author: Nasr Ajaj
@date:   Aug 1, 2022
"""
from utils.utils import Utils
import requests
import logging


from utils.args_parser import ArgsParser
from utils.config_parser import ConfigParser
from utils.logger import Logger


class UFMTelemetryConstants:

    RESULT_OUTPUT_FILE = "api_result/"

    args_list = [
        {
            "name": '--ufm_telemetry_host',
            "help": "Host or IP of UFM Telemetry endpoint"
        },{
            "name": '--ufm_telemetry_port',
            "help": "Port of UFM Telemetry endpoint"
        },{
            "name": '--ufm_telemetry_url',
            "help": "URL of UFM Telemetry endpoint"
        }
    ]


class UFMTelemetryConfigParser(ConfigParser):

    config_file = "telemetry.cfg"

    UFM_TELEMETRY_ENDPOINT_SECTION = "ufm-telemetry-endpoint"
    UFM_TELEMETRY_ENDPOINT_SECTION_HOST = "host"
    UFM_TELEMETRY_ENDPOINT_SECTION_PORT = "port"
    UFM_TELEMETRY_ENDPOINT_SECTION_URL = "url"

    def __init__(self, args):
        super().__init__(args, False)
        self.sdk_config.read(self.config_file)

    def get_telemetry_host(self):
        return self.get_config_value(self.args.ufm_telemetry_host,
                                     self.UFM_TELEMETRY_ENDPOINT_SECTION,
                                     self.UFM_TELEMETRY_ENDPOINT_SECTION_HOST)

    def get_telemetry_port(self):
        return self.safe_get_int(self.args.ufm_telemetry_port,
                                 self.UFM_TELEMETRY_ENDPOINT_SECTION,
                                 self.UFM_TELEMETRY_ENDPOINT_SECTION_PORT,
                                 9001)

    def get_telemetry_url(self):
        return self.get_config_value(self.args.ufm_telemetry_url,
                                     self.UFM_TELEMETRY_ENDPOINT_SECTION,
                                     self.UFM_TELEMETRY_ENDPOINT_SECTION_URL,
                                     "labels/csv/metrics")


class UFMTelemetry:

    def __init__(self, config_parser):
        self.config_parser = config_parser
        self.ufm_telemetry_host = self.config_parser.get_telemetry_host()
        self.ufm_telemetry_port = self.config_parser.get_telemetry_port()
        self.ufm_telemetry_url = self.config_parser.get_telemetry_url()

    def get_metrics(self):
        _host = f'[{self.ufm_telemetry_host}]' if Utils.is_ipv6_address(self.ufm_telemetry_host) else self.ufm_telemetry_host
        url = f'http://{_host}:{self.ufm_telemetry_port}/{self.ufm_telemetry_url}'
        logging.info(f'Send UFM Telemetry Endpoint Request, Method: GET, URL: {url}')
        try:
            response = requests.get(url)
            return response.text
        except Exception as e:
            logging.error(e)
            return None


if __name__ == "__main__":
    # init app args
    args = ArgsParser.parse_args("UFM Telemetry", UFMTelemetryConstants.args_list)

    # init app config parser & load config files
    config_parser = UFMTelemetryConfigParser(args)

    # init logs configs
    logs_file_name = config_parser.get_logs_file_name()
    logs_level = config_parser.get_logs_level()
    Logger.init_logs_config(logs_file_name, logs_level)

    telemetry = UFMTelemetry(config_parser)

    Utils.write_json_to_file(f'{UFMTelemetryConstants.RESULT_OUTPUT_FILE}{Utils.get_timebased_filename()}', telemetry.get_metrics())
