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
@date:   Jul 14, 2022
"""

import os
import platform
import time
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


class UfmPortsConstants:

    PORTS_API_URL = 'resources/ports'
    API_PARAM_SHOW_DISABLED = "show_disabled"
    API_PARAM_SYSTEM = "system"
    API_PARAM_ACTIVE = "active"
    PORTS_API_RESULT = 'api_results/ports'

    args_list = [
        {
            "name": f'--{API_PARAM_SYSTEM}',
            "help": "Option to get all ports data related to specific system node"
        },
        {
            "name": f'--{API_PARAM_ACTIVE}',
            "help": "Option to get active ports only"
        },
        {
            "name": f'--{API_PARAM_SHOW_DISABLED}',
            "help": "Option to get disabled ports"
        }
    ]


class UfmPortsConfigParser(ConfigParser):
    def __init__(self, args):
        super().__init__(args)


class UfmPortsManagement:

    @staticmethod
    def get_ports(active, show_disabled, system=None):
        url = f'{UfmPortsConstants.PORTS_API_URL}?{UfmPortsConstants.API_PARAM_ACTIVE}={active}&{UfmPortsConstants.API_PARAM_SHOW_DISABLED}={show_disabled}'
        if system:
            url = f'{url}&{UfmPortsConstants.API_PARAM_SYSTEM}={system}'
        response = ufm_rest_client.send_request(url)
        if response and response.status_code == HTTPStatus.OK:
            Logger.log_message(response.json())
            return response.json()
        return None


if __name__ == "__main__":
    # init app args
    args = ArgsParser.parse_args("UFM Ports Management", UfmPortsConstants.args_list)

    # init app config parser & load config files
    config_parser = UfmPortsConfigParser(args)

    # init logs configs
    logs_level = config_parser.get_logs_level()
    logs_file_name = config_parser.get_logs_file_name()
    max_log_file_size = config_parser.get_log_file_max_size()
    log_file_backup_count = config_parser.get_log_file_backup_count()
    Logger.init_logs_config(logs_file_name, logs_level, max_log_file_size, log_file_backup_count)

    # init ufm rest client
    ufm_rest_client = UfmRestClient(host=config_parser.get_ufm_host(),
                                    client_token=config_parser.get_ufm_access_token(), username=config_parser.get_ufm_username(),
                                    password=config_parser.get_ufm_password(), ws_protocol=config_parser.get_ufm_protocol())
    args_dict = args.__dict__
    param_active = config_parser.safe_get_bool(args_dict.get(UfmPortsConstants.API_PARAM_ACTIVE), None, None, True)
    param_show_disabled = config_parser.safe_get_bool(args_dict.get(UfmPortsConstants.API_PARAM_SHOW_DISABLED), None, None, False)
    system = args_dict.get(UfmPortsConstants.API_PARAM_SYSTEM)
    result = UfmPortsManagement.get_ports(param_active, param_show_disabled, system)
    if result:
        Utils.write_json_to_file(f'{UfmPortsConstants.PORTS_API_RESULT}_{time.strftime("%Y%m%d-%H%M%S")}.json',
                                 result)

