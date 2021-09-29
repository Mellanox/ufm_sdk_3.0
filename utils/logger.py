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


class Logger:

    @staticmethod
    def init_logs_config(logs_file_name, logs_level):
        logging.basicConfig(filename=logs_file_name,
                            level=logs_level,
                            format='%(asctime)s %(levelname)s %(name)s : %(message)s')
