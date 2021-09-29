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
@date:   Sep 26, 2021
"""
import configparser


SDK_CONFIG_FILE = '../conf/ufm-sdk.cfg'

SDK_CONFIG_UFM_REMOTE_SECTION = 'ufm-remote-server-config'
SDK_CONFIG_UFM_REMOTE_SECTION_HOST = 'host'
SDK_CONFIG_UFM_REMOTE_SECTION_WS_PROTOCOL = 'ws_protocol'
SDK_CONFIG_UFM_REMOTE_SECTION_USERNAME = 'username'
SDK_CONFIG_UFM_REMOTE_SECTION_PASSWORD = 'password'
SDK_CONFIG_UFM_REMOTE_SECTION_ACCESS_TOKEN = 'access_token'

SDK_CONFIG_LOGS_SECTION = 'logs-config'
SDK_CONFIG_LOGS_SECTION_LOGS_FILE_NAME = "logs_file_name"
SDK_CONFIG_LOGS_SECTION_LOGS_LEVEL = "logs_level"

class ConfigParser(object):

    def __init__(self, args):
        self.sdk_config = configparser.RawConfigParser()
        self.sdk_config.read(SDK_CONFIG_FILE)
        self.args = args

    def get_config_value(self, arg, section, key, default=None):
        if arg:
            return arg
        elif section in self.sdk_config and key in self.sdk_config[section] and len(self.sdk_config[section][key]):
            return self.sdk_config[section][key]
        elif default is not None:
            return default
        else:
            raise ValueError(F'Error to request value : {section}.{key}')

    def safe_get_bool(self, arg, section, option, default=None):
        """
        Get boolean value of option that belong to specified section - if not exist return the default value.
        @param section    section name
        @param option    option name
        @param default    default value
        @return    boolean value (True or False)
        """
        config_value = self.get_config_value(arg, section, option, default)
        if isinstance(config_value, str):
            return config_value.lower() == 'true'
        return config_value

    def get_ufm_host(self):
        return self.get_config_value(self.args.ufm_host,
                                     SDK_CONFIG_UFM_REMOTE_SECTION,
                                     SDK_CONFIG_UFM_REMOTE_SECTION_HOST)

    def get_ufm_username(self):
        return self.get_config_value(self.args.ufm_username,
                                     SDK_CONFIG_UFM_REMOTE_SECTION,
                                     SDK_CONFIG_UFM_REMOTE_SECTION_USERNAME)

    def get_ufm_password(self):
        return self.get_config_value(self.args.ufm_password,
                                     SDK_CONFIG_UFM_REMOTE_SECTION,
                                     SDK_CONFIG_UFM_REMOTE_SECTION_PASSWORD)

    def get_ufm_protocol(self):
        return self.get_config_value(self.args.ufm_protocol,
                                     SDK_CONFIG_UFM_REMOTE_SECTION,
                                     SDK_CONFIG_UFM_REMOTE_SECTION_WS_PROTOCOL)

    def get_ufm_access_token(self):
        return self.get_config_value(self.args.ufm_access_token,
                                     SDK_CONFIG_UFM_REMOTE_SECTION,
                                     SDK_CONFIG_UFM_REMOTE_SECTION_ACCESS_TOKEN)


    def get_logs_file_name(self):
        return self.get_config_value(self.args.logs_file_name,
                                     SDK_CONFIG_LOGS_SECTION,
                                     SDK_CONFIG_LOGS_SECTION_LOGS_FILE_NAME,
                                     'console.log')

    def get_logs_level(self):
        return self.get_config_value(self.args.logs_level,
                                     SDK_CONFIG_LOGS_SECTION,
                                     SDK_CONFIG_LOGS_SECTION_LOGS_LEVEL,
                                     'INFO')
