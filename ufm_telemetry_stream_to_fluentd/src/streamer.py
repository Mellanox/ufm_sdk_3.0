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
import os
import sys
sys.path.append(os.getcwd())

import requests
import logging
import time
import datetime
from fluent import asyncsender as asycsender
from streaming_scheduler import StreamingScheduler


from utils.args_parser import ArgsParser
from utils.config_parser import ConfigParser
from utils.logger import Logger, LOG_LEVELS


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
            "name": '--streaming_interval',
            "help": "Interval for telemetry streaming in seconds"
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
    config_file = "../conf/ufm-telemetry-stream-to-fluentd.cfg"

    UFM_TELEMETRY_ENDPOINT_SECTION = "ufm-telemetry-endpoint"
    UFM_TELEMETRY_ENDPOINT_SECTION_HOST = "host"
    UFM_TELEMETRY_ENDPOINT_SECTION_PORT = "port"
    UFM_TELEMETRY_ENDPOINT_SECTION_URL = "url"

    FLUENTD_ENDPOINT_SECTION = "fluentd-endpoint"
    FLUENTD_ENDPOINT_SECTION_HOST = "host"
    FLUENTD_ENDPOINT_SECTION_PORT = "port"
    FLUENTD_ENDPOINT_SECTION_TIMEOUT = "timeout"
    FLUENTD_ENDPOINT_SECTION_MSG_TAG_NAME = "message_tag_name"

    STREAMING_SECTION = "streaming"
    STREAMING_SECTION_INTERVAL = "interval"

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

    def get_streaming_interval(self):
        return self.safe_get_int(self.args.streaming_interval,
                                 self.STREAMING_SECTION,
                                 self.STREAMING_SECTION_INTERVAL,
                                 10)

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

    def __init__(self, ufm_telemetry_host, ufm_telemetry_port, ufm_telemetry_url,
                 streaming_interval,fluentd_host,fluentd_port,fluentd_timeout,fluentd_msg_tag):
        self.ufm_telemetry_host = ufm_telemetry_host
        self.ufm_telemetry_port = ufm_telemetry_port
        self.ufm_telemetry_url = ufm_telemetry_url

        self.streaming_interval = streaming_interval

        self.fluentd_host = fluentd_host
        self.fluentd_port = fluentd_port
        self.fluentd_timeout = fluentd_timeout
        self.fluentd_msg_tag = fluentd_msg_tag

    def _get_metrics(self):
        url = f'http://{self.ufm_telemetry_host}:{self.ufm_telemetry_port}/{self.ufm_telemetry_url}'
        logging.info(f'Send UFM Telemetry Endpoint Request, Method: GET, URL: {url}')
        try:
            response = requests.get(url)
            return response.text
        except Exception as e:
            logging.error(e)
            return response

    def _stream_data_to_fluentd(self, data_to_stream):
        logging.info(f'Streaming to Fluentd IP: {self.fluentd_host} port: {self.fluentd_port} timeout: {self.fluentd_timeout}')
        try:
            fluent_sender = asycsender.FluentSender(UFMTelemetryConstants.PLUGIN_NAME,
                                                    self.fluentd_host,
                                                    self.fluentd_port, timeout=self.fluentd_timeout)

            fluentd_message = {
                "timestamp": datetime.datetime.fromtimestamp(int(time.time())).strftime('%Y-%m-%d %H:%M:%S'),
                "type": "full",
                "metrics": data_to_stream
            }

            fluent_sender.emit(self.fluentd_msg_tag, fluentd_message)
            fluent_sender.close()
            logging.info(f'Finished Streaming to Fluentd Host: {self.fluentd_host} port: {self.fluentd_port}')
        except Exception as e:
            logging.error(e)

    def stream_data(self):
        telemetry_data = self._get_metrics()
        self._stream_data_to_fluentd(telemetry_data)

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

    streaming_interval = config_parser.get_streaming_interval()

    fluentd_host = config_parser.get_fluentd_host()
    fluentd_port = config_parser.get_fluentd_port()
    fluentd_timeout = config_parser.get_fluentd_timeout()
    fluentd_msg_tag = config_parser.get_fluentd_msg_tag(ufm_telemetry_host)

    telemetry_streaming = UFMTelemetryStreaming(ufm_telemetry_host=ufm_telemetry_host,
                                                ufm_telemetry_port= ufm_telemetry_port,
                                                ufm_telemetry_url=ufm_telemetry_url,
                                                streaming_interval=streaming_interval,
                                                fluentd_host=fluentd_host, fluentd_port=fluentd_port,
                                                fluentd_timeout=fluentd_timeout, fluentd_msg_tag=fluentd_msg_tag)

    #streaming_scheduler = StreamingScheduler()
    #streaming_scheduler.start_streaming(telemetry_streaming.stream_data, telemetry_streaming.streaming_interval)

    telemetry_streaming.stream_data()
