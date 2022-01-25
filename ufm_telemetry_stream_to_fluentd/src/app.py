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
@date:   Jan 25, 2022
"""
import os
import sys
sys.path.append(os.getcwd())

from utils.args_parser import ArgsParser
from utils.logger import Logger

from ufm_telemetry_stream_to_fluentd.src.web_service import UFMTelemetryFluentdStreamingServer
from ufm_telemetry_stream_to_fluentd.src.streamer import \
    UFMTelemetryStreamingConfigParser,\
    UFMTelemetryConstants

def _init_logs(config_parser):
    # init logs configs
    logs_file_name = config_parser.get_logs_file_name()
    logs_level = config_parser.get_logs_level()
    Logger.init_logs_config(logs_file_name, logs_level)

if __name__ == '__main__':

    # init app config parser & load config files
    args = ArgsParser.parse_args("UFM Telemetry Streaming to fluentd", UFMTelemetryConstants.args_list)
    config_parser = UFMTelemetryStreamingConfigParser(args)

    _init_logs(config_parser)

    server = UFMTelemetryFluentdStreamingServer(config_parser)
    server.run()
