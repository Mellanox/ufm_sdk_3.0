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

from concurrent.futures import ProcessPoolExecutor
import configparser
import os

class Configuration:
    """
    Configuration class
    """
    CONFIG_FILE_NAME = "/config/sysinfo.conf"
    LOG_FILE_NAME = "/log/sysinfo.log"

    ufm_port = 8000
    log_level = "INFO"
    log_file_max_size = 10240000
    log_file_backup_count = 5
    reports_to_save = 10
    amount_of_workers = 10
    executors = None

    @staticmethod
    def load():
        """
        Load configuration from file
        """
        config_file = configparser.ConfigParser()
        if os.path.exists(Configuration.CONFIG_FILE_NAME):
            # pylint: disable=line-too-long
            config_file.read(Configuration.CONFIG_FILE_NAME)
            common_section = config_file['Common']
            Configuration.ufm_port = common_section.getint("ufm_port", fallback=Configuration.ufm_port)
            Configuration.log_level = common_section.get("log_level", fallback=Configuration.log_level)
            Configuration.log_file_max_size = common_section.getint("log_file_max_size", fallback=Configuration.log_file_max_size)
            Configuration.log_file_backup_count = common_section.getint("log_file_backup_count", fallback=Configuration.log_file_backup_count)
            Configuration.reports_to_save = common_section.getint("reports_to_save", fallback=Configuration.reports_to_save)
            Configuration.amount_of_workers = common_section.getint("max_workers", fallback=Configuration.amount_of_workers)
            Configuration.executors = {
                'default': {'type': 'threadpool', 'max_workers': Configuration.amount_of_workers},
                'processpool': ProcessPoolExecutor(max_workers=5)
            }
