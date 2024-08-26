#
# Copyright © 2013-2024 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
#
import time

import data.manager as dm
from utils.logger import Logger, LOG_LEVELS
from mgr.configurations_mgr import UFMEventsGrafanaConfigParser
from data.collectors.collectors_mgr import CollectorMgr


def _init_logs(config_parser: UFMEventsGrafanaConfigParser) -> None:
    # init logs configs
    logs_file_name = config_parser.get_logs_file_name()
    logs_level = config_parser.get_logs_level()
    max_log_file_size = config_parser.get_log_file_max_size()
    log_file_backup_count = config_parser.get_log_file_backup_count()
    Logger.init_logs_config(logs_file_name, logs_level, max_log_file_size, log_file_backup_count)


if __name__ == '__main__':

    conf = None
    try:
        conf = UFMEventsGrafanaConfigParser.getInstance()
        _init_logs(conf)
        #######
        data_mgr = dm.DataManager()
        collector_mgr = CollectorMgr(data_manager=data_mgr)
        while True:
            time.sleep(1)
    except ValueError as ve:
        Logger.log_message(f'Error occurred during the plugin initialization process : {str(ve)}',
                           LOG_LEVELS.ERROR)
    except Exception as ex:
        Logger.log_message(f'Error occurred during the plugin initialization process : {str(ex)}',
                           LOG_LEVELS.ERROR)
