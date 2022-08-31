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
@date:   Sep 27, 2021
"""

import logging
from logging.handlers import RotatingFileHandler
from enum import Enum

class LOG_LEVELS(Enum):
    FATAL=0
    ERROR=1
    WARNING=2
    INFO=3
    DEBUG=4

class Logger:

    @staticmethod
    def init_logs_config(logs_file_name, logs_level, log_file_max_size=10 * 1024 * 1024, log_file_backup_count=5):
        logging.basicConfig(handlers=[RotatingFileHandler(logs_file_name,
                                                              maxBytes=log_file_max_size,
                                                              backupCount=log_file_backup_count)],
                            level=logs_level,
                            format='%(asctime)s %(levelname)s %(name)s : %(message)s')

    @staticmethod
    def log_message(message, log_level=LOG_LEVELS.INFO):
        if log_level == LOG_LEVELS.INFO:
            logging.info(message)
        elif log_level == LOG_LEVELS.WARNING:
            logging.warning(message)
        elif log_level == LOG_LEVELS.ERROR:
            logging.error(message)
        elif log_level == LOG_LEVELS.DEBUG:
            logging.debug(message)
        elif log_level == LOG_LEVELS.FATAL:
            logging.fatal(message)
        print(message)

    @staticmethod
    def log_missing_args_message(operation, *argv):
        Logger.log_message(f'The {operation} operation requires at least the following parameters: '+ \
                           ''.join(['--{0} '.format(arg) for arg in argv]),
                           LOG_LEVELS.ERROR)



