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
# @date:   Sep 19, 2022
#

import os
import sys
sys.path.append(os.getcwd())

from utils.config_parser import ConfigParser
from utils.logger import Logger, LOG_LEVELS

class UFMSyslogStreamingConfigParser(ConfigParser):
    # for debugging
    # config_file = "../conf/ufm_syslog_streaming_plugin.cfg"
    # fluent_bit_conf_template_path = "../conf/fluent-bit.conf.template"

    # for production with docker
    config_file = "/config/ufm_syslog_streaming_plugin.cfg"
    fluent_bit_conf_template_path = "/config/fluent-bit.conf.template"

    fluent_bit_conf_file_path = "/etc/fluent-bit/fluent-bit.conf"

    UFM_SYSLOG_ENDPOINT_SECTION = "UFM-syslog-endpoint"
    UFM_SYSLOG_ENDPOINT_SECTION_HOST = "host"
    UFM_SYSLOG_ENDPOINT_SECTION_PORT = "port"

    FLUENT_BIT_ENDPOINT_SECTION = "fluent-bit-endpoint"
    FLUENT_BIT_ENDPOINT_SECTION_ENABLED = "enabled"
    FLUENT_BIT_ENDPOINT_SECTION_SRC_PORT = "source_port"
    FLUENT_BIT_ENDPOINT_SECTION_DEST_HOST = "destination_host"
    FLUENT_BIT_ENDPOINT_SECTION_DEST_PORT = "destination_port"

    SYSLOG_DESTINATION_ENDPOINT_SECTION = "syslog-destination-endpoint"
    SYSLOG_DESTINATION_ENDPOINT_SECTION_ENABLED = "enabled"
    SYSLOG_DESTINATION_ENDPOINT_SECTION_HOST = "host"
    SYSLOG_DESTINATION_ENDPOINT_SECTION_PORT = "port"

    STREAMING_SECTION = "streaming"
    STREAMING_SECTION_ENABLED = "enabled"
    STREAMING_SECTION_MESSAGE_TAG_NAME = "message_tag_name"

    def __init__(self):
        super().__init__(read_sdk_config=False)
        self.sdk_config.read(self.config_file)

    def get_enable_streaming_flag(self):
        return self.safe_get_bool(None,
                                  self.STREAMING_SECTION,
                                  self.STREAMING_SECTION_ENABLED,
                                  False)

    def get_ufm_syslog_host(self):
        return self.get_config_value(None,
                                     self.UFM_SYSLOG_ENDPOINT_SECTION,
                                     self.UFM_SYSLOG_ENDPOINT_SECTION_HOST,
                                     '127.0.0.1')

    def get_ufm_syslog_port(self):
        return self.safe_get_int(None,
                                 self.UFM_SYSLOG_ENDPOINT_SECTION,
                                 self.UFM_SYSLOG_ENDPOINT_SECTION_PORT,
                                 5140)

    def get_enable_fluent_bit_flag(self):
        return self.safe_get_bool(None,
                                  self.FLUENT_BIT_ENDPOINT_SECTION,
                                  self.FLUENT_BIT_ENDPOINT_SECTION_ENABLED,
                                  False)

    def get_message_tag_name(self):
        return self.get_config_value(None,
                                     self.FLUENT_BIT_ENDPOINT_SECTION,
                                     self.STREAMING_SECTION_MESSAGE_TAG_NAME,
                                     'ufm_syslog')

    def get_fluent_bit_src_port(self):
        return self.safe_get_int(None,
                                 self.FLUENT_BIT_ENDPOINT_SECTION,
                                 self.FLUENT_BIT_ENDPOINT_SECTION_SRC_PORT,
                                 24227)

    def get_fluent_bit_destination_host(self):
        return self.get_config_value(None,
                                     self.FLUENT_BIT_ENDPOINT_SECTION,
                                     self.FLUENT_BIT_ENDPOINT_SECTION_DEST_HOST,
                                     '127.0.0.1')

    def get_fluent_bit_destination_port(self):
        return self.safe_get_int(None,
                                 self.FLUENT_BIT_ENDPOINT_SECTION,
                                 self.FLUENT_BIT_ENDPOINT_SECTION_DEST_PORT,
                                 24225)

    def get_enable_sys_log_destination_flag(self):
        return self.safe_get_bool(None,
                                  self.SYSLOG_DESTINATION_ENDPOINT_SECTION,
                                  self.SYSLOG_DESTINATION_ENDPOINT_SECTION_ENABLED,
                                  False)

    def get_sys_log_destination_host(self):
        return self.get_config_value(None,
                                     self.SYSLOG_DESTINATION_ENDPOINT_SECTION,
                                     self.SYSLOG_DESTINATION_ENDPOINT_SECTION_HOST,
                                     '127.0.0.1')

    def get_syslog_destination_port(self):
        return self.safe_get_int(None,
                                 self.SYSLOG_DESTINATION_ENDPOINT_SECTION,
                                 self.SYSLOG_DESTINATION_ENDPOINT_SECTION_PORT,
                                 514)

    def update_fluent_bit_conf_file(self):
        log_file = self.get_logs_file_name()
        log_level = self.get_logs_level()
        src_port = self.get_fluent_bit_src_port()
        dest_ip = self.get_fluent_bit_destination_host()
        dest_port = self.get_fluent_bit_destination_port()
        message_tag_name = self.get_message_tag_name()

        Logger.log_message('Reading fluent-bit configuration template file', LOG_LEVELS.DEBUG)
        template_file = open(self.fluent_bit_conf_template_path, "r")
        template = template_file.read()
        Logger.log_message('Update fluent-bit configuration template values', LOG_LEVELS.DEBUG)
        template = template.replace("log_file", log_file)
        template = template.replace("log_level", log_level.lower())
        template = template.replace("src_port", str(src_port))
        template = template.replace("message_tag_name", message_tag_name)
        template = template.replace("host_ip", dest_ip)
        template = template.replace("host_port", str(dest_port))
        Logger.log_message('Generating fluent-bit configuration file', LOG_LEVELS.DEBUG)
        with open(self.fluent_bit_conf_file_path, 'w') as config:
            config.write(template)
            Logger.log_message('fluent-bit configuration file generated successfully', LOG_LEVELS.DEBUG)
