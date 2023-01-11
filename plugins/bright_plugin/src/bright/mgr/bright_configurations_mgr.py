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
# @date:   Dec 15, 2022
#

import re
import os
import site
from utils.config_parser import ConfigParser
from utils.singleton import Singleton


class BrightConfigParser(ConfigParser, Singleton):
    # for debugging
    # config_file = "../../conf/bright_plugin.conf"

    # for production with docker
    config_file = "/config/bright_plugin.conf"

    cert_path = "/config/cert"
    cert_file_path = os.path.join(cert_path, "admin.pem")
    cert_key_file_path = os.path.join(cert_path, "admin.key")
    # /usr/local/lib/python3.9/site-packages
    cacert_file_path = f'{site.getsitepackages()[0]}/pythoncm/etc/cacert.pem'

    BRIGHT_CONFIG_SECTION = "bright-config"
    BRIGHT_CONFIG_SECTION_HOST = "host"
    BRIGHT_CONFIG_SECTION_PORT = "port"
    BRIGHT_CONFIG_SECTION_ENABLED = "enabled"
    BRIGHT_CONFIG_SECTION_STATUS = "status"
    BRIGHT_CONFIG_SECTION_TIMEZONE = "timezone"
    BRIGHT_CONFIG_SECTION_DATA_RETENTION_PERIOD = "data_retention_period"
    BRIGHT_CONFIG_SECTION_CERTIFICATE = "certificate"
    BRIGHT_CONFIG_SECTION_CERTIFICATE_KEY = "certificate_key"

    def __init__(self):
        super(BrightConfigParser, self).__init__(read_sdk_config=False)
        self.sdk_config.read(self.config_file)

    def get_bright_host(self):
        return self.get_config_value(None,
                                     self.BRIGHT_CONFIG_SECTION,
                                     self.BRIGHT_CONFIG_SECTION_HOST)

    def get_bright_port(self):
        return self.safe_get_int(None,
                                 self.BRIGHT_CONFIG_SECTION,
                                 self.BRIGHT_CONFIG_SECTION_PORT,
                                 8081)

    def get_bright_enabled(self):
        return self.safe_get_bool(None,
                                  self.BRIGHT_CONFIG_SECTION,
                                  self.BRIGHT_CONFIG_SECTION_ENABLED,
                                  False)

    def get_bright_data_retention_period(self):
        value = self.get_config_value(None,
                                      self.BRIGHT_CONFIG_SECTION,
                                      self.BRIGHT_CONFIG_SECTION_DATA_RETENTION_PERIOD,
                                      '30d')
        period_list = list(filter(None, re.split(f'(\d+)', value))) # filter to remove empty string
        return int(period_list[0]), period_list[1] # return period,period_unit

    def get_bright_cert(self):
        cert = self.get_config_value(None,
                                     self.BRIGHT_CONFIG_SECTION,
                                     self.BRIGHT_CONFIG_SECTION_CERTIFICATE,
                                     '')

        cert_key = self.get_config_value(None,
                                         self.BRIGHT_CONFIG_SECTION,
                                         self.BRIGHT_CONFIG_SECTION_CERTIFICATE,
                                         '')
        return cert, cert_key
