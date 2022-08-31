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
@date:   Jul 18, 2022
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


class UfmTopNodesConstants:

    TOP_NODES_API_URL = 'telemetry'
    API_PARAM_TYPE = "type"
    API_PARAM_PICKBY = "PickBy"
    API_PARAM_LIMIT = "limit"

    args_list = [
        {
            "name": f'--{API_PARAM_PICKBY}',
            "help": "Option to show monitoring counters data"
        },
        {
            "name": f'--{API_PARAM_LIMIT}',
            "help": "Option to show cable information"
        }
    ]


class UfmTopNodesConfigParser(ConfigParser):
    def __init__(self, args):
        super().__init__(args)


class UfmTopNodesManagement:

    @staticmethod
    def get_top_nodes(counter, limit):
        url = f'{UfmTopNodesConstants.TOP_NODES_API_URL}?{UfmTopNodesConstants.API_PARAM_TYPE}=topX' \
              f'&{UfmTopNodesConstants.API_PARAM_PICKBY}={counter}' \
              f'&{UfmTopNodesConstants.API_PARAM_LIMIT}={limit}'
        response = ufm_rest_client.send_request(url)
        if response and response.status_code == HTTPStatus.OK:
            Logger.log_message(response.json())
        return response


if __name__ == "__main__":
    # init app args
    args = ArgsParser.parse_args("UFM Top Nodes By Counter", UfmTopNodesConstants.args_list)

    # init app config parser & load config files
    config_parser = UfmTopNodesConfigParser(args)

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
    param_pick_by = args_dict.get(UfmTopNodesConstants.API_PARAM_PICKBY)
    param_limit = config_parser.safe_get_int(args_dict.get(UfmTopNodesConstants.API_PARAM_LIMIT), None, None, 5)
    if param_pick_by:
        UfmTopNodesManagement.get_top_nodes(param_pick_by, param_limit)
    else:
        message = f'Please provide valid value for --{UfmTopNodesConstants.API_PARAM_PICKBY}'
        Logger.log_message(message, LOG_LEVELS.ERROR)