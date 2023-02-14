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
# @date:   Jan 26, 2023
#

import re
import os
import site
from utils.config_parser import ConfigParser
from utils.singleton import Singleton


class HelloWorldConfigParser(ConfigParser, Singleton):

    # for debugging
    # config_file = "../../conf/advanced_hello_world_plugin.conf"

    # for production with docker
    config_file = "/config/advanced_hello_world_plugin.conf"

    PLUGIN_CONFIG_SECTION = "plugin-config"
    PLUGIN_CONFIG_SECTION_SOME_CONFIG = "some_config_field"
    PLUGIN_CONFIG_SECTION_SOME_BOOL_CONFIG = "some_bool_config_field"
    PLUGIN_CONFIG_SECTION_SOME_INT_CONFIG = "some_int_config_field"

    def __init__(self):
        super(HelloWorldConfigParser, self).__init__(read_sdk_config=False)
        self.sdk_config.read(self.config_file)

    def get_some_config_field(self):
        return self.get_config_value(None,
                                     self.PLUGIN_CONFIG_SECTION,
                                     self.PLUGIN_CONFIG_SECTION_SOME_CONFIG,
                                     '')

    def get_some_int_config_field(self):
        return self.safe_get_int(None,
                                 self.PLUGIN_CONFIG_SECTION,
                                 self.PLUGIN_CONFIG_SECTION_SOME_INT_CONFIG,
                                 8081)

    def get_some_bool_config_field(self):
        return self.safe_get_bool(None,
                                  self.PLUGIN_CONFIG_SECTION,
                                  self.PLUGIN_CONFIG_SECTION_SOME_BOOL_CONFIG,
                                  True)
