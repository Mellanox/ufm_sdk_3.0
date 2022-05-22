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

from utils.utils import Utils

sys.path.append(os.getcwd())

import requests
import logging
import time
import datetime
from utils.fluentd.fluent import asyncsender as asycsender


from utils.args_parser import ArgsParser
from utils.config_parser import ConfigParser
from utils.logger import Logger


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
            "name": '--bulk_streaming',
            "help": "Bulk streaming flag, i.e. if True all telemetry rows will be streamed in one message; "
                    "otherwise, each row will be streamed in a separated message"
        },{
            "name": '--enable_streaming',
            "help": "If true, the streaming will be started once the required configurations have been set"
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
    # for debugging
    #config_file = "../conf/fluentd_telemetry_plugin.cfg"

    config_file = "/config/fluentd_telemetry_plugin.cfg" # this path on the docker

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
    STREAMING_SECTION_BULK_STREAMING = "bulk_streaming"
    STREAMING_SECTION_ENABLED = "enabled"

    META_FIELDS_SECTION = "meta-fields"

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

    def get_bulk_streaming_flag(self):
        return self.safe_get_bool(self.args.bulk_streaming,
                                  self.STREAMING_SECTION,
                                  self.STREAMING_SECTION_BULK_STREAMING,
                                  True)

    def get_enable_streaming_flag(self):
        return self.safe_get_bool(self.args.enable_streaming,
                                  self.STREAMING_SECTION,
                                  self.STREAMING_SECTION_ENABLED,
                                  False)

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

    def get_meta_fields(self):
        meta_fields_list = self.get_section_items(self.META_FIELDS_SECTION)
        aliases = []
        custom = []
        for meta_field,value in meta_fields_list:
            meta_fields_parts = meta_field.split("_")
            meta_field_type = meta_fields_parts[0]
            meta_field_key = "_".join(meta_fields_parts[1:])
            if meta_field_type == "alias":
                aliases.append({
                    "key": meta_field_key,
                    "value": value
                })
            elif meta_field_type == "add":
                custom.append({
                    "key": meta_field_key,
                    "value": value
                })
            else:
                logging.warning("The meta field type : {} is not from the supported types list [alias, add]".format(meta_field_type))
        return aliases,custom


class UFMTelemetryStreaming:

    def __init__(self, config_parser):

        self.config_parser = config_parser

        self.ufm_telemetry_host = self.config_parser.get_telemetry_host()
        self.ufm_telemetry_port = self.config_parser.get_telemetry_port()
        self.ufm_telemetry_url = self.config_parser.get_telemetry_url()

        self.streaming_interval = self.config_parser.get_streaming_interval()
        self.bulk_streaming_flag = self.config_parser.get_bulk_streaming_flag()
        self.aliases_meta_fields , self.custom_meta_fields = self.config_parser.get_meta_fields()

        self.fluentd_host = self.config_parser.get_fluentd_host()
        self.fluentd_port = self.config_parser.get_fluentd_port()
        self.fluentd_timeout = self.config_parser.get_fluentd_timeout()
        self.fluentd_msg_tag = self.config_parser.get_fluentd_msg_tag(self.ufm_telemetry_host)

    def _get_metrics(self):
        _host = f'[{self.ufm_telemetry_host}]' if Utils.is_ipv6_address(self.ufm_telemetry_host) else self.ufm_telemetry_host
        url = f'http://{_host}:{self.ufm_telemetry_port}/{self.ufm_telemetry_url}'
        logging.info(f'Send UFM Telemetry Endpoint Request, Method: GET, URL: {url}')
        try:
            response = requests.get(url)
            return response.text
        except Exception as e:
            logging.error(e)
            return None

    def _parse_telemetry_csv_metrics_to_json(self, data, line_separator = "\n", attrs_sepatator = ","):
        rows = data.split(line_separator)
        keys = rows[0].split(attrs_sepatator)
        output = []
        for row in rows[1:]:
            if len(row) > 0:
                values = row.split(attrs_sepatator)
                dic = {}
                for i in range(len(keys)):
                    dic[keys[i]] = values[i]
                for alias in self.aliases_meta_fields:
                    alias_key = alias["key"]
                    alias_value = alias["value"]
                    value = dic.get(alias_key,None)
                    if value is None:
                        logging.warning("The alias : {} does not exist in the telemetry response keys: {}".format(alias_key, str(keys)))
                        continue
                    dic[alias_value] = value
                for custom_field in self.custom_meta_fields:
                    dic[custom_field["key"]] = custom_field["value"]
                output.append(dic)
        return output

    def _stream_data_to_fluentd(self, data_to_stream):
        logging.info(f'Streaming to Fluentd IP: {self.fluentd_host} port: {self.fluentd_port} timeout: {self.fluentd_timeout}')
        try:
            fluent_sender = asycsender.FluentSender(UFMTelemetryConstants.PLUGIN_NAME,
                                                    self.fluentd_host,
                                                    self.fluentd_port, timeout=self.fluentd_timeout)

            fluentd_message = {
                "timestamp": datetime.datetime.fromtimestamp(int(time.time())).strftime('%Y-%m-%d %H:%M:%S'),
                "type": "full",
                "values": data_to_stream
            }

            fluent_sender.emit(self.fluentd_msg_tag, fluentd_message)
            fluent_sender.close()
            logging.info(f'Finished Streaming to Fluentd Host: {self.fluentd_host} port: {self.fluentd_port}')
        except Exception as e:
            logging.error(e)

    def stream_data(self):
        telemetry_data = self._get_metrics()
        if telemetry_data:
            data_to_stream = self._parse_telemetry_csv_metrics_to_json(telemetry_data)
            if self.bulk_streaming_flag:
                self._stream_data_to_fluentd(data_to_stream)
            else:
                for row in data_to_stream:
                    self._stream_data_to_fluentd(row)
        else:
            logging.error("Failed to get the telemetry data metrics")

if __name__ == "__main__":
    # init app args
    args = ArgsParser.parse_args("UFM Telemetry Streaming to fluentd", UFMTelemetryConstants.args_list)

    # init app config parser & load config files
    config_parser = UFMTelemetryStreamingConfigParser(args)

    # init logs configs
    logs_file_name = config_parser.get_logs_file_name()
    logs_level = config_parser.get_logs_level()
    Logger.init_logs_config(logs_file_name, logs_level)

    telemetry_streaming = UFMTelemetryStreaming(config_parser)

    #streaming_scheduler = StreamingScheduler.getInstance()
    #streaming_scheduler.start_streaming(telemetry_streaming.stream_data, telemetry_streaming.streaming_interval)

    telemetry_streaming.stream_data()
