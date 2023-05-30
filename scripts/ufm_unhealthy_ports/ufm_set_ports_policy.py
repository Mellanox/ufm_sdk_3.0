#!/usr/bin/python3
#
# Copyright © 2013-2023 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
#
# @author: Anas Badaha
# @date:   May 25, 2023
#

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


class UfmPortsPolicyConstants:

    UNHEATHY_API_URL = "app/unhealthy_ports"
    API_PORTS = "ports"
    API_PORTS_POLICY = "ports_policy"
    API_ACTION = "action"
    UNHEALTHY_PORT_ACTION = "UNHEALTHY"
    HEALTHY_PORT_ACTION = "HEALTHY"

    UNHEALTHY_PORTS_OPERATIONS = {
        "get_unhealthy_ports": "get_unhealthy_ports",
        "set_ports_polict": "set_ports_polict"
    }

    args_list = [
        {
            "name": f'--{UNHEALTHY_PORTS_OPERATIONS.get("set_ports_polict")}',
            "help": "Option to set the ports policy to Healthy/Unhealthy",
            "no_value": True
        },
        {
            "name": f'--{API_PORTS}',
            "help": "The List of ports numbers(comma seprated), Each port number should be a string of"
                    "NodeGUID_PortNumber(Ex 0002c9030060dc20_10) or Keyword 'ALL'"
        },
        {
            "name": f'--{API_PORTS_POLICY}',
            "help": "'HEALTHY' | 'UNHEALTHY'."

        },
        {
            "name": f'--{API_ACTION}',
            "help": "'isolate' | 'no_discover'."
        },
        {
            "name": f'--{UNHEALTHY_PORTS_OPERATIONS.get("get_unhealthy_ports")}',
            "help": "Option to get all ports that are marked as healthy from OpenSM",
            "no_value": True
        }
    ]


class UfmSetPortsPolicyConfigParser(ConfigParser):
    def __init__(self, args):
        super().__init__(args)


class UfmSetPortsPolicyManagement:

    @staticmethod
    def set_ports_polict(ports_numbers_list, ports_policy, action):
        if ports_policy == UfmPortsPolicyConstants.UNHEALTHY_PORT_ACTION:
            payload = {
                UfmPortsPolicyConstants.API_PORTS: ports_numbers_list,
                UfmPortsPolicyConstants.API_PORTS_POLICY: ports_policy,
                UfmPortsPolicyConstants.API_ACTION: action
            }
        else:
            payload = {
                UfmPortsPolicyConstants.API_PORTS: ports_numbers_list,
                UfmPortsPolicyConstants.API_PORTS_POLICY: ports_policy
            }

        response = ufm_rest_client.send_request(UfmPortsPolicyConstants.UNHEATHY_API_URL, HTTPMethods.PUT,
                                                payload=payload)
        if response and response.status_code == HTTPStatus.OK:
            Logger.log_message(f'Mark ports {ports_numbers_list} as {ports_policy} has been completed successfully')
        else:
            Logger.log_message(f'Failed to mark {ports_numbers_list} as {ports_policy}!', LOG_LEVELS.ERROR)
        return response

    @staticmethod
    def get_unhealthy_ports():
        url = UfmPortsPolicyConstants.UNHEATHY_API_URL
        response = ufm_rest_client.send_request(url)
        if response and response.status_code == HTTPStatus.OK:
            Logger.log_message(response.json())
        else:
            Logger.log_message(response, LOG_LEVELS.ERROR)
        return response


if __name__ == "__main__":
    # init app args
    args = ArgsParser.parse_args("UFM Ports Policy Management", UfmPortsPolicyConstants.args_list)

    # init app config parser & load config files
    config_parser = UfmSetPortsPolicyConfigParser(args)

    # init logs configs
    logs_file_name = config_parser.get_logs_file_name()
    logs_level = config_parser.get_logs_level()
    max_log_file_size = config_parser.get_log_file_max_size()
    log_file_backup_count = config_parser.get_log_file_backup_count()
    Logger.init_logs_config(logs_file_name, logs_level, max_log_file_size, log_file_backup_count)


    # init ufm rest client
    ufm_rest_client = UfmRestClient(host = config_parser.get_ufm_host(),
                                    client_token=config_parser.get_ufm_access_token(),username = config_parser.get_ufm_username(),
                                    password = config_parser.get_ufm_password(),ws_protocol=config_parser.get_ufm_protocol())
    args_dict = args.__dict__
    if args_dict.get(UfmPortsPolicyConstants.UNHEALTHY_PORTS_OPERATIONS.get("set_ports_polict")):
        try:
            ports_number_list = config_parser.safe_get_list(args_dict.get(UfmPortsPolicyConstants.API_PORTS),
                                                            None,None)
        except Exception as e:
            ExceptionHandler.handel_arg_exception(UfmPortsPolicyConstants.UNHEALTHY_PORTS_OPERATIONS.get("set_ports_polict"),
                                                  UfmPortsPolicyConstants.API_PORTS)

        ports_policy = config_parser.get_config_value(args_dict.get(UfmPortsPolicyConstants.API_PORTS_POLICY),
                                                      None, None, UfmPortsPolicyConstants.UNHEALTHY_PORT_ACTION)
        action = config_parser.get_config_value(args_dict.get(UfmPortsPolicyConstants.API_ACTION),
                                                None, None, "isolate")

        UfmSetPortsPolicyManagement.set_ports_polict(ports_number_list, ports_policy, action)
    elif args_dict.get(UfmPortsPolicyConstants.UNHEALTHY_PORTS_OPERATIONS.get("get_unhealthy_ports")):
        UfmSetPortsPolicyManagement.get_unhealthy_ports()
    else:
        message = "You must provide one of the following operations: "+ \
                  ''.join(['--{0} | '.format(item) for key,item in UfmPortsPolicyConstants.UNHEALTHY_PORTS_OPERATIONS.items()])
        Logger.log_message(message, LOG_LEVELS.ERROR)
