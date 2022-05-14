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
from utils.ufm_rest_client import UfmProtocols, ApiErrorMessages
from utils.exception_handler import  ExceptionHandler

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
        elif section in self.sdk_config and key in self.sdk_config[section] and len(str(self.sdk_config[section][key])):
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

    def safe_get_list(self, arg, section, option, default=None, splitter= ","):
        """
        Get list value of option that belong to specified section - if not exist return the default value.
        @param section    section name
        @param option    option name
        @param default    default value
        @param default    default value
        @param splitter splitter of elements in string
        @return    value (List)
        """
        config_value = self.get_config_value(arg, section, option, default)
        if isinstance(config_value, str):
            return config_value.split(splitter)
        return config_value

    def safe_get_int(self, arg, section, option, default=None):
        """
        Get integer value of option that belong to specified section - if not exist return the default value.
        @param section    section name
        @param option    option name
        @param default    default value
        @param default    default value
        @return    value (integer)
        """
        config_value = self.get_config_value(arg, section, option, default)
        if isinstance(config_value, str):
            return int(config_value)
        return config_value

    def get_ufm_host(self):
        # the exception was handled here to prevent handling it in every script
        try:
            return self.get_config_value(self.args.ufm_host,
                                         SDK_CONFIG_UFM_REMOTE_SECTION,
                                         SDK_CONFIG_UFM_REMOTE_SECTION_HOST)
        except ValueError as e:
            ExceptionHandler.handel_exception(ApiErrorMessages.Missing_UFM_Host)


    def get_ufm_username(self):
        return self.get_config_value(self.args.ufm_username,
                                     SDK_CONFIG_UFM_REMOTE_SECTION,
                                     SDK_CONFIG_UFM_REMOTE_SECTION_USERNAME,
                                     False)

    def get_ufm_password(self):
        return self.get_config_value(self.args.ufm_password,
                                     SDK_CONFIG_UFM_REMOTE_SECTION,
                                     SDK_CONFIG_UFM_REMOTE_SECTION_PASSWORD,
                                     False)

    def get_ufm_protocol(self):
        return self.get_config_value(self.args.ufm_protocol,
                                     SDK_CONFIG_UFM_REMOTE_SECTION,
                                     SDK_CONFIG_UFM_REMOTE_SECTION_WS_PROTOCOL,
                                     UfmProtocols.https.value)

    def get_ufm_access_token(self):
        return self.get_config_value(self.args.ufm_access_token,
                                     SDK_CONFIG_UFM_REMOTE_SECTION,
                                     SDK_CONFIG_UFM_REMOTE_SECTION_ACCESS_TOKEN,
                                     False)


    def get_logs_file_name(self, default_file_name  = 'console.log'):
        return self.get_config_value(self.args.logs_file_name,
                                     SDK_CONFIG_LOGS_SECTION,
                                     SDK_CONFIG_LOGS_SECTION_LOGS_FILE_NAME,
                                     default_file_name)

    def get_logs_level(self):
        return self.get_config_value(self.args.logs_level,
                                     SDK_CONFIG_LOGS_SECTION,
                                     SDK_CONFIG_LOGS_SECTION_LOGS_LEVEL,
                                     'INFO')

    def get_conf_sections(self):
        return self.sdk_config.sections()

    def clear_section_items(self, section):
        # remove the old section with all items
        self.sdk_config.remove_section(section)
        # add new empty section
        self.sdk_config.add_section(section)

    def get_section_items(self, section):
        return self.sdk_config.items(section)

    def set_item_value(self, section, item, value):
        self.sdk_config.set(section, item, value)

    def update_config_file(self, file_path):
        with open(file_path, 'w') as configfile:
            self.sdk_config.write(configfile)
