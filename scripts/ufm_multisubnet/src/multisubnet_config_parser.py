#!/usr/bin/python3
"""
@copyright:
    Copyright (C) 2013-2023 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.

    This software product is a proprietary product of Nvidia Corporation and its affiliates
    (the "Company") and all right, title, and interest in and to the software
    product, including all associated intellectual property rights, are and
    shall remain exclusively with the Company.

    This software product is governed by the End User License Agreement
    provided with the software product.

@author: anan AlAghbar
@date:   Oct 23, 2023
"""
import os
from utils.config_parser import ConfigParser
from scripts.ufm_multisubnet.src import MultisubnetConstants


class MultisubnetConfigParser(ConfigParser):
    config_file = "../conf/multisubnet.cfg"

    def __init__(self, args):
        super(MultisubnetConfigParser, self).__init__(args, read_sdk_config=False)
        self.args_dict = self.args.__dict__
        abs_conf_path = os.path.normpath(os.path.join(os.path.dirname(__file__), self.config_file))
        self.sdk_config.read(abs_conf_path)


    def get_ufm_consumer_ip(self):
        return self.get_config_value(self.args_dict.get(MultisubnetConstants.CONF_UFM_CONSUMER_IP),
                                     MultisubnetConstants.CONF_CONSUMER_SECTION,
                                     MultisubnetConstants.CONF_UFM_CONSUMER_IP)

    def get_ufm_consumer_username(self):
        return self.get_config_value(self.args_dict.get(MultisubnetConstants.CONF_UFM_CONSUMER_USERNAME),
                                     MultisubnetConstants.CONF_CONSUMER_SECTION,
                                     MultisubnetConstants.CONF_UFM_CONSUMER_USERNAME)

    def get_ufm_consumer_password(self):
        return self.get_config_value(self.args_dict.get(MultisubnetConstants.CONF_UFM_CONSUMER_PASSWORD),
                                     MultisubnetConstants.CONF_CONSUMER_SECTION,
                                     MultisubnetConstants.CONF_UFM_CONSUMER_PASSWORD)

    def get_ufm_provider_from_ip(self):
        return self.get_config_value(self.args_dict.get(MultisubnetConstants.CONF_PROVIDERS_FROM_IP),
                                     MultisubnetConstants.CONF_PROVIDERS_SECTION,
                                     MultisubnetConstants.CONF_PROVIDERS_FROM_IP)

    def get_ufm_provider_to_ip(self):
        return self.get_config_value(self.args_dict.get(MultisubnetConstants.CONF_PROVIDERS_TO_IP),
                                     MultisubnetConstants.CONF_PROVIDERS_SECTION,
                                     MultisubnetConstants.CONF_PROVIDERS_TO_IP)

    def get_ufm_providers_username(self):
        return self.get_config_value(self.args_dict.get(MultisubnetConstants.CONF_UFM_PROVIDER_USERNAME),
                                     MultisubnetConstants.CONF_PROVIDERS_SECTION,
                                     MultisubnetConstants.CONF_UFM_PROVIDER_USERNAME)

    def get_ufm_providers_password(self):
        return self.get_config_value(self.args_dict.get(MultisubnetConstants.CONF_UFM_PROVIDER_PASSWORD),
                                     MultisubnetConstants.CONF_PROVIDERS_SECTION,
                                     MultisubnetConstants.CONF_UFM_PROVIDER_PASSWORD)

    def get_ufm_providers_topology_port(self):
        return self.safe_get_int(self.args_dict.get(MultisubnetConstants.CONF_PROVIDERS_TOPOLOGY_PORT),
                                 MultisubnetConstants.CONF_PROVIDERS_SECTION,
                                 MultisubnetConstants.CONF_PROVIDERS_TOPOLOGY_PORT, 7120)

    def get_ufm_providers_proxy_port(self):
        return self.safe_get_int(self.args_dict.get(MultisubnetConstants.CONF_PROVIDERS_PROXY_PORT),
                                 MultisubnetConstants.CONF_PROVIDERS_SECTION,
                                 MultisubnetConstants.CONF_PROVIDERS_PROXY_PORT, 443)

    def get_ufm_providers_telemetry_port(self):
        return self.safe_get_int(self.args_dict.get(MultisubnetConstants.CONF_PROVIDERS_TELEMETRY_PORT),
                                 MultisubnetConstants.CONF_PROVIDERS_SECTION,
                                 MultisubnetConstants.CONF_PROVIDERS_TELEMETRY_PORT, 9001)

    def get_ufm_auto_token_generation_flag(self):
        return self.safe_get_bool(self.args_dict.get(MultisubnetConstants.CONF_AUTO_TOKEN_GENERATION),
                                  MultisubnetConstants.CONF_PROVIDERS_SECTION,
                                  MultisubnetConstants.CONF_AUTO_TOKEN_GENERATION, True)
