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
# @author: Abeer Moghrabi
# @date:   Aug 9, 2023
#

import os
import sys
sys.path.append(os.getcwd())

from utils.utils import Utils
from utils.flask_server import run_api
from utils.flask_server.base_flask_api_app import BaseFlaskAPIApp
from utils.logger import Logger, LOG_LEVELS
from api.ui_files_api import EventsHistoryPluginUIFilesAPI
from api.conf_api import EventsHistoryPluginConfigurationsAPI
from mgr.events_history_configurations_mgr import EventsHistoryConfigParser
from api.events_history_api import EventsHistoryApi

def _init_logs(config_parser):
    # init logs configs
    logs_file_name = config_parser.get_logs_file_name()
    logs_level = config_parser.get_logs_level()
    max_log_file_size = config_parser.get_log_file_max_size()
    log_file_backup_count = config_parser.get_log_file_backup_count()
    Logger.init_logs_config(logs_file_name, logs_level, max_log_file_size, log_file_backup_count)


if __name__ == '__main__':
    try:

        conf = EventsHistoryConfigParser.getInstance()
        _init_logs(conf)

    except ValueError as ve:
        Logger.log_message('Error occurred during the plugin logs initialization:'
                           + str(ve), LOG_LEVELS.ERROR)
    except Exception as ex:
        Logger.log_message(str(ex))
    try:
        plugin_port = Utils.get_plugin_port(
            port_conf_file='/config/events_history_httpd_proxy.conf',
            default_port_value=8686)

        routes = {
            "/conf": EventsHistoryPluginConfigurationsAPI().application,
            "/files": EventsHistoryPluginUIFilesAPI().application,
            "/events-history": EventsHistoryApi().application,
        }

        app = BaseFlaskAPIApp(routes)
        run_api(app=app, port_number=int(plugin_port))

    except Exception as ex:
        print(f'Failed to run the app due to: {str(ex)}')
