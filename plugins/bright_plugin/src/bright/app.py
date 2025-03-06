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

import os
import sys
sys.path.append(os.getcwd())

from utils.utils import Utils
from utils.flask_server import run_api
from utils.flask_server.base_flask_api_app import BaseFlaskAPIApp
from utils.logger import Logger, LOG_LEVELS
from api.conf_api import UFMBrightPluginConfigurationsAPI
from api.bright_api import BrightAPI
from api.ui_files_api import UFMBrightPluginUIFilesAPI
from mgr.bright_configurations_mgr import BrightConfigParser
from mgr.bright_data_polling_mgr import BrightDataPollingMgr


def _init_logs(config_parser):
    # init logs configs
    logs_file_name = config_parser.get_logs_file_name()
    logs_level = config_parser.get_logs_level()
    max_log_file_size = config_parser.get_log_file_max_size()
    log_file_backup_count = config_parser.get_log_file_backup_count()
    Logger.init_logs_config(logs_file_name, logs_level, max_log_file_size, log_file_backup_count)


if __name__ == '__main__':
    try:

        conf = BrightConfigParser()
        _init_logs(conf)

        polling_mgr = BrightDataPollingMgr()
        polling_started = polling_mgr.trigger_polling()
        if not polling_started:
            Logger.log_message('The Bright Cluster Data polling was not started, '
                               'please make sure to enable it and set the needed configurations', LOG_LEVELS.WARNING)
    except ValueError as ve:
        Logger.log_message('The Bright Cluster Data polling was not started, '
                           'please make sure to enable it and set the needed configurations', LOG_LEVELS.WARNING)
    except Exception as ex:
        Logger.log_message(str(ex))
    try:
        plugin_port = Utils.get_plugin_port(
            port_conf_file='/config/bright_httpd_proxy.conf',
            default_port_value=8985)

        routes = {
            "/conf": UFMBrightPluginConfigurationsAPI().application,
            "/data": BrightAPI().application,
            "/files": UFMBrightPluginUIFilesAPI().application
        }

        app = BaseFlaskAPIApp(routes)
        run_api(app=app, port_number=plugin_port)

    except Exception as ex:
        print(f'Failed to run the app due to: {str(ex)}')
