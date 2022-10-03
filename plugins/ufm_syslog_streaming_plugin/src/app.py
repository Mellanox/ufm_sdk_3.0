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
# @date:   Sep 19, 2022
#

import os
import sys
sys.path.append(os.getcwd())

from utils.logger import Logger, LOG_LEVELS

from utils.flask_server import run_api
from utils.flask_server.base_flask_api_app import BaseFlaskAPIApp
from mgr.configurations_mgr import UFMSyslogStreamingConfigParser
from mgr.syslog_forwarder_mgr import SyslogForwarder
from api.conf_api import SyslogStreamingConfigurationsAPI



def _init_logs(config_parser):
    # init logs configs
    default_file_name = 'usfs.log'
    logs_file_name = config_parser.get_logs_file_name(default_file_name=default_file_name)
    logs_level = config_parser.get_logs_level()
    max_log_file_size = config_parser.get_log_file_max_size()
    log_file_backup_count = config_parser.get_log_file_backup_count()
    Logger.init_logs_config(logs_file_name, logs_level, max_log_file_size, log_file_backup_count)


if __name__ == '__main__':

    # init app config parser & load config files
    config_parser = UFMSyslogStreamingConfigParser()
    syslog_forwarder = SyslogForwarder(conf=config_parser)
    _init_logs(config_parser)

    try:
        if config_parser.get_enable_streaming_flag():
            syslog_forwarder.start_forwarding()
        else:
            Logger.log_message('The streaming is not enabled, '
                               'please enable it and set the streaming configurations using the REST API: '
                               '[POST] https://<UFM_HOST>/plugin/usfs/conf', LOG_LEVELS.WARNING)

    except ValueError as ve:
        Logger.log_message('The streaming is running without at least one configured destination address, '
                           'Please set the destination configurations using the plugin/usfs/conf API',
                           LOG_LEVELS.WARNING)

    routes_map = {
        "/conf": SyslogStreamingConfigurationsAPI(conf=config_parser,
                                                  syslog_forwarder=syslog_forwarder).application
    }
    app = BaseFlaskAPIApp(routes_map)
    run_api(app=app, port_number=8989)
