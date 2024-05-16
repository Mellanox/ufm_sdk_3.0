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

# pylint: disable=wrong-import-position
import logging
from web_service import UFMTelemetryFluentdStreamingAPI
from streamer import \
    UFMTelemetryStreaming,\
    UFMTelemetryStreamingConfigParser,\
    UFMTelemetryConstants
from streaming_scheduler import StreamingScheduler

# pylint: disable=no-name-in-module,import-error
from utils.flask_server import run_api
from utils.args_parser import ArgsParser
from utils.logger import Logger
from utils.utils import Utils


def _init_logs(config_parser):
    # init logs configs
    default_file_name = 'tfs.log'
    logs_file_name = config_parser.get_logs_file_name(default_file_name=default_file_name)
    logs_level = config_parser.get_logs_level()
    max_log_file_size = config_parser.get_log_file_max_size()
    log_file_backup_count = config_parser.get_log_file_backup_count()
    Logger.init_logs_config(logs_file_name, logs_level, max_log_file_size, log_file_backup_count)


if __name__ == '__main__':

    # init app config parser & load config files
    args = ArgsParser.parse_args("UFM Telemetry Streaming to fluentd", UFMTelemetryConstants.args_list)
    _config_parser = UFMTelemetryStreamingConfigParser(args)

    _init_logs(_config_parser)

    STREAMER = None
    try:
        STREAMER = UFMTelemetryStreaming.getInstance(_config_parser)
        if _config_parser.get_enable_streaming_flag():
            scheduler = StreamingScheduler.getInstance()
            job_id = scheduler.start_streaming()
            logging.info("Streaming has been started successfully")
        else:
            logging.warning("Streaming was not started, need to enable the streaming & set the required configurations")

    except ValueError as ex:
        logging.warning("Streaming was not started, need to enable the streaming & set the required configurations. %s"
                        , str(ex))
    except Exception as ex:  # pylint: disable=broad-except
        logging.error('Streaming was not started due to the following error: %s', str(ex))

    if STREAMER:
        try:
            app = UFMTelemetryFluentdStreamingAPI(_config_parser)
            port = Utils.get_plugin_port('/config/tfs_httpd_proxy.conf', 8981)
            run_api(app=app, port_number=int(port))
        except Exception as ex:  # pylint: disable=broad-except
            logging.error('Streaming server was not started due to the following error: %s', str(ex))
    else:
        logging.error('Streaming server was not started.')
