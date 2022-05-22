#!/usr/bin/python3

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
@date:   Oct 5, 2021
"""

import os
import sys
from http import HTTPStatus

try:
    from utils.utils import Utils
    from utils.ufm_rest_client import UfmRestClient, HTTPMethods
    from utils.args_parser import ArgsParser
    from utils.config_parser import ConfigParser
    from utils.logger import Logger, LOG_LEVELS
    from utils.exception_handler import ExceptionHandler
except ModuleNotFoundError as e:
    print("Error occurred while importing python modules, "
          "Please make sure that you exported your repository to PYTHONPATH by running: "
          f'export PYTHONPATH="${{PYTHONPATH}}:{os.path.dirname(os.getcwd())}"')


class UfmLogicalServersConstants:

    ENVS_API_URL = 'resources/environments'
    NETWORKS_API_URL = 'resources/networks'
    FREE_COMPUTES_API_URL = 'resources/systems?computes=free'
    LS_API_URL = 'resources/logical_servers'
    ENV_LS_API_URL = ENVS_API_URL+"/{0}/logical_servers"
    API_NAME = "name"
    API_DESCRIPTION = "description"
    API_PKEY = "pkey"
    API_ENV = "environment"
    API_COMPUTES = "computes"
    API_TOTAL_COMPUTES = "total_computes"
    API_NETWORKS = "networks"



    LS_OPERATIONS = {
        "get_envs": "get_envs",
        "get_env": "get_env",
        "create_env": "create_env",
        "delete_env": "delete_env",
        "get_networks": "get_networks",
        "get_network": "get_network",
        "create_network": "create_network",
        "delete_network": "delete_network",
        "get_logical_servers": "get_logical_servers",
        "create_logical_server": "create_logical_server",
        "delete_logical_server": "delete_logical_server",
        "get_free_hosts": "get_free_hosts",
        "auto_allocate_hosts": "auto_allocate_hosts",
        "allocate_hosts": "allocate_hosts",
        "add_network_interfaces": "add_network_interfaces"
    }

    args_list = [
        {
            "name": f'--{LS_OPERATIONS.get("get_envs")}',
            "help": "Option to get all existing environments",
            "no_value": True
        },
        {
            "name": f'--{LS_OPERATIONS.get("get_env")}',
            "help": "Option to get a specific environment"
        },
        {
            "name": f'--{LS_OPERATIONS.get("create_env")}',
            "help": "Option to create an UFM environment",
            "no_value": True
        },
        {
            "name": f'--{LS_OPERATIONS.get("delete_env")}',
            "help": "Option to delete an UFM environments by it's name"
        },
        {
            "name": f'--{API_NAME}',
            "help": "Option to provide a name for specific element, e.g.:environment, logical server, network"
        },
        {
            "name": f'--{API_DESCRIPTION}',
            "help": "Option to set a description for the created element"
        },
        {
            "name": f'--{LS_OPERATIONS.get("get_networks")}',
            "help": "Option to get all existing networks",
            "no_value": True
        },
        {
            "name": f'--{LS_OPERATIONS.get("get_network")}',
            "help": "Option to get a specific network"
        },
        {
            "name": f'--{LS_OPERATIONS.get("delete_network")}',
            "help": "Option to remove a specific network by it's name"
        },
        {
            "name": f'--{LS_OPERATIONS.get("create_network")}',
            "help": "Option to create a network",
            "no_value": True
        },
        {
            "name": f'--{API_ENV}',
            "help": "Option to provide an environment for the created logical server"
        },
        {
            "name": f'--{API_PKEY}',
            "help": "Option to set a specific Pkey for the created network"
        },
        {
            "name": f'--{LS_OPERATIONS.get("get_logical_servers")}',
            "help": "Option to get all existing logical servers",
            "no_value": True
        },
        {
            "name": f'--{LS_OPERATIONS.get("delete_logical_server")}',
            "help": "Option to remove a specific logical server by it's name",
            "no_value": True
        },
        {
            "name": f'--{LS_OPERATIONS.get("create_logical_server")}',
            "help": "Option to create a logical server",
            "no_value": True
        },
        {
            "name": f'--{LS_OPERATIONS.get("get_free_hosts")}',
            "help": "Option to get all free (unallocated) hosts",
            "no_value": True
        },
        {
            "name": f'--{LS_OPERATIONS.get("auto_allocate_hosts")}',
            "help": "Option to allocate hosts automatically to a logical servers "
                    "by providing the number of hosts to be allocated",
            "no_value": True
        },
        {
            "name": f'--{LS_OPERATIONS.get("allocate_hosts")}',
            "help": "Option to allocate hosts manually to a logical servers "
                    "by providing the GUIDS of hosts to be allocated (comma separated)",
            "no_value": True
        },
        {
            "name": f'--{API_COMPUTES}',
            "help": "Computes GUIDs to be allocated manually to a logical server (comma separated)"
        },
        {
            "name": f'--{API_TOTAL_COMPUTES}',
            "help": "Total number of Computes to be allocated automatically to a logical server"
        },
        {
            "name": f'--{LS_OPERATIONS.get("add_network_interfaces")}',
            "help": "Option to add networks interfaces to a logical server"
                    "by providing existing networks names (comma separated)",
            "no_value": True
        },
        {
            "name": f'--{API_NETWORKS}',
            "help": "Networks names to be added into a logical server (comma separated)"
        }
    ]


class UfmLsConfigParser(ConfigParser):

    def __init__(self,args):
        super().__init__(args)
        self.args_dict = self.args.__dict__

    def get_name(self):
        return self.get_config_value(self.args_dict.get(UfmLogicalServersConstants.API_NAME),
                                     None,None)

    def get_env(self):
        return self.get_config_value(self.args_dict.get(UfmLogicalServersConstants.API_ENV),
                                     None,None)

    def get_description(self):
        return self.get_config_value(self.args_dict.get(UfmLogicalServersConstants.API_DESCRIPTION),
                                     None,None, False)

    def get_pkey(self):
        return self.get_config_value(self.args_dict.get(UfmLogicalServersConstants.API_PKEY),
                                     None,None, False)

    def get_computes(self):
        return self.safe_get_list(self.args_dict.get(UfmLogicalServersConstants.API_COMPUTES),
                                  None,None)

    def get_total_computes(self):
        return self.safe_get_int(self.args_dict.get(UfmLogicalServersConstants.API_TOTAL_COMPUTES),
                                  None,None)

    def get_networks(self):
        return self.safe_get_list(self.args_dict.get(UfmLogicalServersConstants.API_NETWORKS),
                                  None,None)



class UfmLsManagement:

    @staticmethod
    def get_envs(env_name=None):
        url = UfmLogicalServersConstants.ENVS_API_URL
        if env_name:
            url = f'{url}/{env_name}'
        response = ufm_rest_client.send_request(url)
        if response and response.status_code == HTTPStatus.OK:
            Logger.log_message(response.json())
            return
        Logger.log_message(response.text, LOG_LEVELS.ERROR)

    @staticmethod
    def create_env(name, desc):
        url = UfmLogicalServersConstants.ENVS_API_URL
        payload = {
            UfmLogicalServersConstants.API_NAME: name
        }
        if desc:
            payload[UfmLogicalServersConstants.API_DESCRIPTION] = desc
        response = ufm_rest_client.send_request(url, HTTPMethods.POST, payload)
        if response and response.status_code == HTTPStatus.OK:
            Logger.log_message(f'The environment: {name} is created successfully')
            return True
        Logger.log_message(f'The environment: {name} isn`t created, {response.text}',LOG_LEVELS.ERROR)
        return False

    @staticmethod
    def delete_env(name):
        url = f'{UfmLogicalServersConstants.ENVS_API_URL}/{name}'
        response = ufm_rest_client.send_request(url, HTTPMethods.DELETE)
        if response and response.status_code == HTTPStatus.NO_CONTENT:
            Logger.log_message(f'The enviroment: {name} is removed successfully')
            return True
        Logger.log_message(f'The enviroment: {name} isn`t removed, {response.text}', LOG_LEVELS.ERROR)
        return False


    @staticmethod
    def get_networks(network_name=None):
        url = UfmLogicalServersConstants.NETWORKS_API_URL
        if network_name:
            url = f'{url}/{network_name}'
        response = ufm_rest_client.send_request(url)
        if response and response.status_code == HTTPStatus.OK:
            Logger.log_message(response.json())
            return
        Logger.log_message(response.text, LOG_LEVELS.ERROR)

    @staticmethod
    def delete_network(name):
        url = f'{UfmLogicalServersConstants.NETWORKS_API_URL}/{name}'
        response = ufm_rest_client.send_request(url, HTTPMethods.DELETE)
        if response and response.status_code == HTTPStatus.NO_CONTENT:
            Logger.log_message(f'The network: {name} is removed successfully')
            return True
        Logger.log_message(f'The network: {name} isn`t removed, {response.text}', LOG_LEVELS.ERROR)
        return False

    @staticmethod
    def create_network(name, desc=None,
                       pkey=None):
        url = UfmLogicalServersConstants.NETWORKS_API_URL
        payload = {
            UfmLogicalServersConstants.API_NAME: name
        }
        if desc:
            payload[UfmLogicalServersConstants.API_DESCRIPTION] = desc
        if pkey:
            payload[UfmLogicalServersConstants.API_PKEY] = pkey

        response = ufm_rest_client.send_request(url, HTTPMethods.POST, payload)
        if response and response.status_code == HTTPStatus.OK:
            Logger.log_message(f'The network: {name} is created successfully')
            return True
        Logger.log_message(f'The network: {name} isn`t created, {response.text}', LOG_LEVELS.ERROR)

    @staticmethod
    def get_ls():
        url = UfmLogicalServersConstants.LS_API_URL
        response = ufm_rest_client.send_request(url)
        if response and response.status_code == HTTPStatus.OK:
            Logger.log_message(response.json())
            return
        Logger.log_message(response.text, LOG_LEVELS.ERROR)

    @staticmethod
    def delete_ls(env_name, ls_name):
        url = f'{UfmLogicalServersConstants.ENV_LS_API_URL.format(env_name)}/{ls_name}'
        response = ufm_rest_client.send_request(url, HTTPMethods.DELETE)
        if response and response.status_code == HTTPStatus.NO_CONTENT:
            Logger.log_message(f'The logical server: {ls_name} is removed successfully from the environment: {env_name}')
            return True
        Logger.log_message(f'The logical server: {ls_name} isn`t removed, {response.text}', LOG_LEVELS.ERROR)
        return False

    @staticmethod
    def create_ls(env_name, ls_name, desc=None):
        url = UfmLogicalServersConstants.ENV_LS_API_URL.format(env_name, ls_name)
        payload = {
            UfmLogicalServersConstants.API_NAME: ls_name
        }
        if desc:
            payload[UfmLogicalServersConstants.API_DESCRIPTION] = desc

        response = ufm_rest_client.send_request(url, HTTPMethods.POST, payload)
        if response and response.status_code == HTTPStatus.OK:
            Logger.log_message(f'The logical server: {ls_name} is created successfully in the environment: {env_name}')
            return True
        Logger.log_message(f'The logical server: {ls_name} isn`t created, {response.text}', LOG_LEVELS.ERROR)
        return False

    @staticmethod
    def get_free_hosts():
        url = UfmLogicalServersConstants.FREE_COMPUTES_API_URL
        response = ufm_rest_client.send_request(url)
        if response and response.status_code == HTTPStatus.OK:
            response = response.json()
            Logger.log_message(f'The total number of the free hosts is {len(response)}')
            Logger.log_message(response)
            return
        Logger.log_message(response.text, LOG_LEVELS.ERROR)

    @staticmethod
    def auto_allocate_hosts(env_name, ls_name, number_of_hosts):
        url = f'{UfmLogicalServersConstants.ENV_LS_API_URL.format(env_name)}' \
              f'/{ls_name}/auto_assign-computes'
        payload = {
            "total_computes": number_of_hosts
        }
        response = ufm_rest_client.send_request(url, HTTPMethods.PUT, payload)
        if response and response.status_code == HTTPStatus.OK:
            Logger.log_message(f'{number_of_hosts} hosts allocated successfully to the logical server: {ls_name}'
                               f' under the environment: {env_name}')
            Logger.log_message(response.json())
            return True
        Logger.log_message(response.text, LOG_LEVELS.ERROR)

    @staticmethod
    def allocate_hosts(env_name, ls_name, guids_list):
        url = f'{UfmLogicalServersConstants.ENV_LS_API_URL.format(env_name)}' \
              f'/{ls_name}/allocate-computes'
        payload = {
            "computes": guids_list
        }
        response = ufm_rest_client.send_request(url, HTTPMethods.PUT, payload)
        if response and response.status_code == HTTPStatus.OK:
            Logger.log_message(f'{guids_list} allocated successfully to the logical server: {ls_name} '
                               f'under the environment: {env_name}')
            Logger.log_message(response.json())
            return True
        Logger.log_message(response.text, LOG_LEVELS.ERROR)

    @staticmethod
    def add_network_interfaces(env_name, ls_name, networks_list):
        url = f'{UfmLogicalServersConstants.ENV_LS_API_URL.format(env_name)}' \
              f'/{ls_name}/network_interfaces'
        payload = []
        for network in networks_list:
            payload.append({"network": network})
        response = ufm_rest_client.send_request(url, HTTPMethods.POST, payload)
        if response and response.status_code == HTTPStatus.OK:
            Logger.log_message(f'{networks_list} networks interfaces are added successfully '
                               f'to the logical server: {ls_name} '
                               f'under the environment: {env_name}')
            Logger.log_message(response.json())
            return True
        Logger.log_message(response.text, LOG_LEVELS.ERROR)


if __name__ == "__main__":
    # init app args
    args = ArgsParser.parse_args("UFM Logical Servers Management", UfmLogicalServersConstants.args_list)

    # init app config parser & load config files
    config_parser = UfmLsConfigParser(args)

    # init logs configs
    logs_file_name = config_parser.get_logs_file_name()
    logs_level = config_parser.get_logs_level()
    Logger.init_logs_config(logs_file_name, logs_level)

    # init ufm rest client
    ufm_rest_client = UfmRestClient(host = config_parser.get_ufm_host(),
                                    client_token=config_parser.get_ufm_access_token(),username = config_parser.get_ufm_username(),
                                    password = config_parser.get_ufm_password(),ws_protocol=config_parser.get_ufm_protocol())

    if config_parser.args_dict.get(UfmLogicalServersConstants.LS_OPERATIONS.get("get_envs")):
        UfmLsManagement.get_envs()
    elif config_parser.args_dict.get(UfmLogicalServersConstants.LS_OPERATIONS.get("get_env")):
        env_name = config_parser.get_config_value(config_parser.args_dict.get(UfmLogicalServersConstants.LS_OPERATIONS.get("get_env")),
                                                  None,None)
        UfmLsManagement.get_envs(env_name)
    elif config_parser.args_dict.get(UfmLogicalServersConstants.LS_OPERATIONS.get("create_env")):
        try:
            env_name = config_parser.get_name()
        except ValueError as e:
            ExceptionHandler.handel_arg_exception(UfmLogicalServersConstants.LS_OPERATIONS.get("create_env"),
                                                  UfmLogicalServersConstants.API_NAME)
        desc = config_parser.get_description()
        UfmLsManagement.create_env(env_name, desc)
    elif config_parser.args_dict.get(UfmLogicalServersConstants.LS_OPERATIONS.get("delete_env")):
        env_name = config_parser.args_dict.get(UfmLogicalServersConstants.LS_OPERATIONS.get("delete_env"))
        UfmLsManagement.delete_env(env_name)
    elif config_parser.args_dict.get(UfmLogicalServersConstants.LS_OPERATIONS.get("get_networks")):
        UfmLsManagement.get_networks()
    elif config_parser.args_dict.get(UfmLogicalServersConstants.LS_OPERATIONS.get("get_network")):
        network_name = config_parser.get_config_value(config_parser.args_dict.get(
            UfmLogicalServersConstants.LS_OPERATIONS.get("get_network")),None,None)
        UfmLsManagement.get_networks(network_name)
    elif config_parser.args_dict.get(UfmLogicalServersConstants.LS_OPERATIONS.get("delete_network")):
        network_name = config_parser.args_dict.get(UfmLogicalServersConstants.LS_OPERATIONS.get("delete_network"))
        UfmLsManagement.delete_network(network_name)
    elif config_parser.args_dict.get(UfmLogicalServersConstants.LS_OPERATIONS.get("create_network")):
        try:
            name = config_parser.get_name()
        except ValueError as e:
            ExceptionHandler.handel_arg_exception(UfmLogicalServersConstants.LS_OPERATIONS.get("create_network"),
                                            UfmLogicalServersConstants.API_NAME)
        description = config_parser.get_description()
        pkey = config_parser.get_pkey()

        UfmLsManagement.create_network(name=name, desc=description, pkey=pkey)
    elif config_parser.args_dict.get(UfmLogicalServersConstants.LS_OPERATIONS.get("get_logical_servers")):
        UfmLsManagement.get_ls()
    elif config_parser.args_dict.get(UfmLogicalServersConstants.LS_OPERATIONS.get("delete_logical_server")):
        try:
            ls_name = config_parser.get_name()
            env_name = config_parser.get_env()
        except ValueError as e:
            ExceptionHandler.handel_arg_exception(UfmLogicalServersConstants.LS_OPERATIONS.get("delete_logical_server"),
                                            UfmLogicalServersConstants.API_NAME,
                                            UfmLogicalServersConstants.API_ENV)
        UfmLsManagement.delete_ls(env_name, ls_name)
    elif config_parser.args_dict.get(UfmLogicalServersConstants.LS_OPERATIONS.get("create_logical_server")):
        try:
            ls_name = config_parser.get_name()
            env_name = config_parser.get_env()
        except ValueError as e:
            ExceptionHandler.handel_arg_exception(UfmLogicalServersConstants.LS_OPERATIONS.get("create_logical_server"),
                                            UfmLogicalServersConstants.API_NAME,
                                            UfmLogicalServersConstants.API_ENV)
        description = config_parser.get_description()
        UfmLsManagement.create_ls(env_name, ls_name, desc=description)
    elif config_parser.args_dict.get(UfmLogicalServersConstants.LS_OPERATIONS.get("get_free_hosts")):
        UfmLsManagement.get_free_hosts()
    elif config_parser.args_dict.get(UfmLogicalServersConstants.LS_OPERATIONS.get("auto_allocate_hosts")):
        try:
            ls_name = config_parser.get_name()
            env_name = config_parser.get_env()
            total_computes = config_parser.get_total_computes()
        except ValueError as e:
            ExceptionHandler.handel_arg_exception(UfmLogicalServersConstants.LS_OPERATIONS.get("auto_allocate_hosts"),
                                            UfmLogicalServersConstants.API_NAME,
                                            UfmLogicalServersConstants.API_ENV,
                                            UfmLogicalServersConstants.API_TOTAL_COMPUTES)
        UfmLsManagement.auto_allocate_hosts(env_name, ls_name, total_computes)
    elif config_parser.args_dict.get(UfmLogicalServersConstants.LS_OPERATIONS.get("allocate_hosts")):
        try:
            ls_name = config_parser.get_name()
            env_name = config_parser.get_env()
            guids = config_parser.get_computes()
        except ValueError as e:
            ExceptionHandler.handel_arg_exception(UfmLogicalServersConstants.LS_OPERATIONS.get("allocate_hosts"),
                                            UfmLogicalServersConstants.API_NAME,
                                            UfmLogicalServersConstants.API_ENV,
                                            UfmLogicalServersConstants.API_COMPUTES)
        UfmLsManagement.allocate_hosts(env_name, ls_name, guids)
    elif config_parser.args_dict.get(UfmLogicalServersConstants.LS_OPERATIONS.get("add_network_interfaces")):
        try:
            ls_name = config_parser.get_name()
            env_name = config_parser.get_env()
            networks = config_parser.get_networks()
        except ValueError as e:
            ExceptionHandler.handel_arg_exception(UfmLogicalServersConstants.LS_OPERATIONS.get("add_network_interfaces"),
                                            UfmLogicalServersConstants.API_NAME,
                                            UfmLogicalServersConstants.API_ENV,
                                            UfmLogicalServersConstants.API_NETWORKS)
        UfmLsManagement.add_network_interfaces(env_name, ls_name, networks)
    else:
        message = "You must provide one of the following operations: "+ \
                  ''.join(['--{0} | '.format(item) for key,item in UfmLogicalServersConstants.LS_OPERATIONS.items()])
        Logger.log_message(message, LOG_LEVELS.ERROR)
