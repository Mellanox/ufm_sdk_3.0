#!/usr/bin/python3

"""
@copyright:
    Copyright (C) 2013-2022 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.

    This software product is a proprietary product of Nvidia Corporation and its affiliates
    (the "Company") and all right, title, and interest in and to the software
    product, including all associated intellectual property rights, are and
    shall remain exclusively with the Company.

    This software product is governed by the End User License Agreement
    provided with the software product.

@author: Nasr Ajaj
@date:   Jul 17, 2022
"""

import os
import platform
from http import HTTPStatus

try:
    from utils.utils import Utils
    from utils.ufm_rest_client import UfmRestClient, HTTPMethods
    from utils.args_parser import ArgsParser
    from utils.config_parser import ConfigParser
    from utils.logger import Logger, LOG_LEVELS
    from utils.exception_handler import ExceptionHandler
except ModuleNotFoundError as e:
    if platform.system() == "Windows":
        print("Error occurred while importing python modules, "
              "Please make sure that you exported your repository to PYTHONPATH by running: "
              f'set PYTHONPATH=%PYTHONPATH%;{os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))}')
    else:
        print("Error occurred while importing python modules, "
              "Please make sure that you exported your repository to PYTHONPATH by running: "
              f'export PYTHONPATH="${{PYTHONPATH}}:{os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))}"')


class UfmLinksConstants:

    LINKS_API_URL = 'resources/links'
    API_PARAM_CABLE_INFO = "cable_info"
    API_PARAM_MONITORING_COUNTERS_INFO = "monitoring_counters_info"
    API_PARAM_SYSTEM = "system"

    args_list = [
        {
            "name": f'--{API_PARAM_SYSTEM}',
            "help": "Option to get all links data related to specific system node"
        },
        {
            "name": f'--{API_PARAM_MONITORING_COUNTERS_INFO}',
            "help": "Option to show monitoring counters data"
        },
        {
            "name": f'--{API_PARAM_CABLE_INFO}',
            "help": "Option to show cable information"
        }
    ]


class UfmLinksConfigParser(ConfigParser):
    def __init__(self, args):
        super().__init__(args)


class UfmLinksManagement:

    @staticmethod
    def get_links(show_cable_info, show_counters_info, system=None):
        url = f'{UfmLinksConstants.LINKS_API_URL}?{UfmLinksConstants.API_PARAM_CABLE_INFO}={show_cable_info}' \
              f'&{UfmLinksConstants.API_PARAM_MONITORING_COUNTERS_INFO}={show_counters_info}'
        if system:
            url = f'{url}&{UfmLinksConstants.API_PARAM_SYSTEM}={system}'
        response = ufm_rest_client.send_request(url)
        if response and response.status_code == HTTPStatus.OK:
            Logger.log_message(response.json())
        else:
            Logger.log_message(response, LOG_LEVELS.ERROR)
        return response


if __name__ == "__main__":
    # init app args
    args = ArgsParser.parse_args("UFM Links Management", UfmLinksConstants.args_list)

    # init app config parser & load config files
    config_parser = UfmLinksConfigParser(args)

    # init logs configs
    logs_level = config_parser.get_logs_level()
    logs_file_name = config_parser.get_logs_file_name()
    Logger.init_logs_config(logs_file_name, logs_level)

    # init ufm rest client
    ufm_rest_client = UfmRestClient(host=config_parser.get_ufm_host(),
                                    client_token=config_parser.get_ufm_access_token(), username=config_parser.get_ufm_username(),
                                    password=config_parser.get_ufm_password(), ws_protocol=config_parser.get_ufm_protocol())
    args_dict = args.__dict__
    param_show_cable_info = config_parser.safe_get_bool(args_dict.get(UfmLinksConstants.API_PARAM_CABLE_INFO), None, None, True)
    param_show_counters_info = config_parser.safe_get_bool(args_dict.get(UfmLinksConstants.API_PARAM_MONITORING_COUNTERS_INFO), None, None, False)
    if args_dict.get(UfmLinksConstants.API_PARAM_SYSTEM):
        system = args_dict.get(UfmLinksConstants.API_PARAM_SYSTEM)
        UfmLinksManagement.get_links(param_show_cable_info, param_show_counters_info, system)
    else:
        UfmLinksManagement.get_links(param_show_cable_info, param_show_counters_info)