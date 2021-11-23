#!/usr/bin/python3

"""
@copyright:
    Copyright (C) Mellanox Technologies Ltd. 2014-2020.  ALL RIGHTS RESERVED.

    This software product is a proprietary product of Mellanox Technologies
    Ltd. (the "Company") and all right, title, and interest in and to the
    software product, including all associated intellectual property rights,
    are and shall remain exclusively with the Company.

    This software product is governed by the End User License Agreement
    provided with the software product.

@author: Anan Al-Aghbar
@date:   Nov 23, 2021
"""
import requests
import logging
import time
import datetime
from fluent import asyncsender as asycsender

try:
    from utils.utils import Utils
    from utils.ufm_rest_client import UfmRestClient, HTTPMethods
    from utils.args_parser import ArgsParser
    from utils.config_parser import ConfigParser
    from utils.logger import Logger, LOG_LEVELS
except ModuleNotFoundError as e:
    print("Error occurred while importing python modules, "
          "Please make sure that you exported your repository to PYTHONPATH by running: "
          f'export PYTHONPATH="${{PYTHONPATH}}:{os.path.dirname(os.getcwd())}"')


class UFMTelemetryConstants:
    PLUGIN_NAME = "UFM_Telemetry_Streaming"

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
        },{
            "name": '--fluentd_host',
            "help": "Host name or IP of fluentd endpoint"
        },{
            "name": '--fluentd_port',
            "help": "Port of fluentd endpoint"
        },{
            "name": '--fluentd_timeout',
            "help": "Fluentd timeout in seconds"
        },{
            "name": '--fluentd_message_tag_name',
            "help": "Tag name of fluentd endpoint message"
        }
    ]


class UFMTelemetryStreamingConfigParser(ConfigParser):
    config_file = "ufm-telemetry-stream-to-fluentd.cfg"

    UFM_TELEMETRY_ENDPOINT_SECTION = "ufm-telemetry-endpoint"
    UFM_TELEMETRY_ENDPOINT_SECTION_HOST = "host"
    UFM_TELEMETRY_ENDPOINT_SECTION_PORT = "port"
    UFM_TELEMETRY_ENDPOINT_SECTION_URL = "url"

    FLUENTD_ENDPOINT_SECTION = "fluentd-endpoint"
    FLUENTD_ENDPOINT_SECTION_HOST = "host"
    FLUENTD_ENDPOINT_SECTION_PORT = "port"
    FLUENTD_ENDPOINT_SECTION_TIMEOUT = "timeout"
    FLUENTD_ENDPOINT_SECTION_MSG_TAG_NAME = "message_tag_name"

    def __init__(self, args):
        super().__init__(args)
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
                                     "enterprise")


    def get_fluentd_host(self):
        return self.get_config_value(self.args.fluentd_host,
                                     self.FLUENTD_ENDPOINT_SECTION,
                                     self.FLUENTD_ENDPOINT_SECTION_HOST)

    def get_fluentd_port(self):
        return self.safe_get_int(self.args.fluentd_port,
                                 self.FLUENTD_ENDPOINT_SECTION,
                                 self.FLUENTD_ENDPOINT_SECTION_PORT)

    def get_fluentd_timeout(self):
        return self.safe_get_int(self.args.fluentd_port,
                                 self.FLUENTD_ENDPOINT_SECTION,
                                 self.FLUENTD_ENDPOINT_SECTION_TIMEOUT,
                                 120)

    def get_fluentd_msg_tag(self,default=None):
        return self.get_config_value(self.args.fluentd_host,
                                     self.FLUENTD_ENDPOINT_SECTION,
                                     self.FLUENTD_ENDPOINT_SECTION_MSG_TAG_NAME,
                                     default)


class UFMTelemetryStreaming:

    @staticmethod
    def get_metrics(host, port, url):
        url = f'http://{host}:{port}/{url}'
        logging.info(f'Send UFM Telemetry Endpoint Request, Method: GET, URL: {url}')
        try:
            response = requests.get(url)
            return response.text
        except Exception as e:
            logging.error(e)
            return response

    @staticmethod
    def stream_data_to_fluentd(fluentd_host,
                               fluentd_port,
                               fluentd_msg_name,
                               fluentd_timeout,data_to_stream):
        logging.info(f'Streaming to Fluentd IP: {fluentd_host} port: {fluentd_port} timeout: {fluentd_timeout}')
        try:
            fluent_sender = asycsender.FluentSender(UFMTelemetryConstants.PLUGIN_NAME,
                                                    fluentd_host,
                                                    fluentd_port, timeout=fluentd_timeout)

            fluentd_message = {
                "timestamp": datetime.datetime.fromtimestamp(int(time.time())).strftime('%Y-%m-%d %H:%M:%S'),
                "type": "full",
                "metrics": data_to_stream
            }

            fluent_sender.emit(fluentd_msg_name, fluentd_message)
            fluent_sender.close()
            logging.info(f'Finished Streaming to Fluentd Host: {fluentd_host} port: {fluentd_port}')
        except Exception as e:
            logging.error(e)

if __name__ == "__main__":
    # init app args
    args = ArgsParser.parse_args("UFM Telemetry Streaming to fluentd", UFMTelemetryConstants.args_list)

    # init app config parser & load config files
    config_parser = UFMTelemetryStreamingConfigParser(args)

    # init logs configs
    logs_file_name = config_parser.get_logs_file_name()
    logs_level = config_parser.get_logs_level()
    Logger.init_logs_config(logs_file_name, logs_level)

    ufm_telemetry_host = config_parser.get_telemetry_host()
    ufm_telemetry_port = config_parser.get_telemetry_port()
    ufm_telemetry_url = config_parser.get_telemetry_url()

    fluentd_host = config_parser.get_fluentd_host()
    fluentd_port = config_parser.get_fluentd_port()
    fluentd_timeout = config_parser.get_fluentd_timeout()
    fluentd_msg_tag = config_parser.get_fluentd_msg_tag(ufm_telemetry_host)


    metrics = UFMTelemetryStreaming.get_metrics(ufm_telemetry_host,
                                                ufm_telemetry_port,
                                                ufm_telemetry_url)

    UFMTelemetryStreaming.stream_data_to_fluentd(fluentd_host, fluentd_port, fluentd_msg_tag,
                                                 fluentd_timeout, metrics)

