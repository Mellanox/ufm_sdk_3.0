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

from utils.config_parser import ConfigParser
from utils.singleton import Singleton


class EventsHistoryConfigParser(ConfigParser, Singleton):
    """
    This class was designed to manage 'events_history_plugin.conf' file
    """

    # for debugging
    # config_file = "../../conf/events_history_plugin.conf"

    # for production with docker
    config_file = "/config/events_history_plugin.conf"


    def __init__(self):
        super(EventsHistoryConfigParser, self).__init__(read_sdk_config=False)
        self.sdk_config.read(self.config_file)


