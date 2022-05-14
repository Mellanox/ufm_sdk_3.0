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
@date:   Oct 3, 2021
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


class UfmPkeysConstants:

    PKEYS_API_URL = "resources/pkeys"
    API_GUIDS = "guids"
    API_PKEY = "pkey"
    API_INDEX0 = "index0"
    API_IP_OVER_IB = "ip_over_ib"
    API_MEMBERSHIP = "membership"
    API_MEMBERSHIPS = "memberships"

    PKEYS_OPERATIONS = {
        "get_pkeys": "get_pkeys",
        "get_pkey": "get_pkey",
        "set_pkey": "set_pkey",
        "delete_pkey": "delete_pkey"
    }

    args_list = [
        {
            "name": f'--{PKEYS_OPERATIONS.get("set_pkey")}',
            "help": "Option to set a Pkey network",
            "no_value": True
        },
        {
            "name": f'--{API_PKEY}',
            "help": "Network Pkey [Hexadecimal string between '0x0'-'0x7fff' exclusive]"
        },
        {
            "name": f'--{API_GUIDS}',
            "help": "The List of port GUIDs(comma seprated), Each GUID is a hexadecimal string with a minimum length of "
                    "16 characters and maximum length of 20 characters,"
                    " e.g.043f720300dd1d3c,0c42a103007aca90,etc... "
        },
        {
            "name": f'--{API_MEMBERSHIPS}',
            "help": "List of “full” or “limited” comma-separated strings. "
                    "It must be the same length as the GUIDs list. "
                    "Each value by an index represents a GUID membership."
                    " e.g. ['full', 'limited', etc...]"
                    "This parameter conflicts with the “membership” parameter. "
                    "You must select either a list of memberships or just one membership for all GUIDs."

        },
        {
            "name": f'--{API_MEMBERSHIP}',
            "help": "'full' | 'limited'. “full”- members with full membership can communicate with all hosts (members)"
                    " within the network/partition"
                    "“limited” - members with limited membership "
                    "cannot communicate with other members with limited membership. "
                    "However, communication is allowed between every other combination of membership types."
                    "[Default = 'full']"
                    "This parameter will be ignored in case the “memberships” parameter has been set"
        },
        {
            "name": f'--{API_INDEX0}',
            "help": "If true, the API will store the PKey at index 0 of the PKey table of the GUID.[Default = False]"
        },
        {
            "name": f'--{API_IP_OVER_IB}',
            "help": "If true, PKey is a member in a multicast group that uses IP over InfiniBand.[Default = True]"
        },
        {
            "name": f'--{PKEYS_OPERATIONS.get("get_pkeys")}',
            "help": "Option to get all existing pkeys data",
            "no_value": True
        },
        {
            "name": f'--{PKEYS_OPERATIONS.get("get_pkey")}',
            "help": "Option to get specific Pkey data"
        },
        {
            "name": f'--{PKEYS_OPERATIONS.get("delete_pkey")}',
            "help": "Option to delete specific Pkey"
        }
    ]



class UfmPkeysConfigParser(ConfigParser):
    def __init__(self, args):
        super().__init__(args)




class UfmPkeysManagement:

    @staticmethod
    def set_pkey(pkey,ports_guids_list,memberships= None,
                    default_membership = "full", index0 = False, ip_over_ib = True):
        payload = {
            UfmPkeysConstants.API_GUIDS:ports_guids_list,
            UfmPkeysConstants.API_PKEY: pkey,
            UfmPkeysConstants.API_INDEX0 : index0,
            UfmPkeysConstants.API_IP_OVER_IB : ip_over_ib
        }

        if memberships and len(memberships) :
            payload[UfmPkeysConstants.API_MEMBERSHIPS] = memberships
        else:
            payload[UfmPkeysConstants.API_MEMBERSHIP] = default_membership

        response = ufm_rest_client.send_request(UfmPkeysConstants.PKEYS_API_URL, HTTPMethods.PUT, payload=payload)
        if response and response.status_code == HTTPStatus.OK:
            Logger.log_message(f'The pkey: {pkey} has been set successfully')
        else:
            Logger.log_message(f'The pkey: {pkey} hasn`t been set', LOG_LEVELS.ERROR)
        return response

    @staticmethod
    def get_pkeys(pkey=None):
        if pkey:
            url = f'{UfmPkeysConstants.PKEYS_API_URL}/{pkey}'
        else:
            url = UfmPkeysConstants.PKEYS_API_URL
        url = f'{url}?guids_data=true'
        response = ufm_rest_client.send_request(url)
        if response and response.status_code == HTTPStatus.OK:
            Logger.log_message(response.json())
        else:
            Logger.log_message(response, LOG_LEVELS.ERROR)
        return response

    @staticmethod
    def delete_pkey(pkey):
        url = f'{UfmPkeysConstants.PKEYS_API_URL}/{pkey}'
        response = ufm_rest_client.send_request(url, HTTPMethods.DELETE)
        if response:
            if response.status_code == HTTPStatus.OK:
                Logger.log_message(f'The Pkey: {pkey} has been removed successfully')
            elif response.status_code == HTTPStatus.NOT_FOUND:
                Logger.log_message(f'The Pkey: {pkey} is not found', LOG_LEVELS.ERROR)
        else:
            Logger.log_message(f'The Pkey: {pkey} hasn`t been removed successfully', LOG_LEVELS.ERROR)
        return response





if __name__ == "__main__":
    # init app args
    args = ArgsParser.parse_args("UFM Pkeys Management", UfmPkeysConstants.args_list)

    # init app config parser & load config files
    config_parser = UfmPkeysConfigParser(args)

    # init logs configs
    logs_file_name = config_parser.get_logs_file_name()
    logs_level = config_parser.get_logs_level()
    Logger.init_logs_config(logs_file_name, logs_level)


    # init ufm rest client
    ufm_rest_client = UfmRestClient(host = config_parser.get_ufm_host(),
                                    client_token=config_parser.get_ufm_access_token(),username = config_parser.get_ufm_username(),
                                    password = config_parser.get_ufm_password(),ws_protocol=config_parser.get_ufm_protocol())
    args_dict = args.__dict__
    if args_dict.get(UfmPkeysConstants.PKEYS_OPERATIONS.get("set_pkey")):
        try:
            pkey = config_parser.get_config_value(args_dict.get(UfmPkeysConstants.API_PKEY),
                                                  None,None)
            guids = config_parser.safe_get_list(args_dict.get(UfmPkeysConstants.API_GUIDS),
                                                   None, None)
        except Exception as e:
            ExceptionHandler.handel_arg_exception(UfmPkeysConstants.PKEYS_OPERATIONS.get("set_pkey"),
                                                  UfmPkeysConstants.API_PKEY,UfmPkeysConstants.API_GUIDS)

        index0 = config_parser.safe_get_bool(args_dict.get(UfmPkeysConstants.API_INDEX0),
                                             None, None, False)
        ip_over_ib = config_parser.safe_get_bool(args_dict.get(UfmPkeysConstants.API_IP_OVER_IB),
                                   None, None, True)
        memberships = config_parser.safe_get_list(args_dict.get(UfmPkeysConstants.API_MEMBERSHIPS),
                                    None, None, [])
        membership = config_parser.get_config_value(args_dict.get(UfmPkeysConstants.API_MEMBERSHIP),
                                   None, None, "full")
        UfmPkeysManagement.set_pkey(pkey, guids, memberships=memberships,
                                       default_membership=membership,index0=bool(index0),
                                       ip_over_ib=bool(ip_over_ib))
    elif args_dict.get(UfmPkeysConstants.PKEYS_OPERATIONS.get("get_pkeys")):
        UfmPkeysManagement.get_pkeys()
    elif args_dict.get(UfmPkeysConstants.PKEYS_OPERATIONS.get("get_pkey")):
        pkey = args_dict.get(UfmPkeysConstants.PKEYS_OPERATIONS.get("get_pkey"))
        UfmPkeysManagement.get_pkeys(pkey)
    elif args_dict.get(UfmPkeysConstants.PKEYS_OPERATIONS.get("delete_pkey")):
        pkey = args_dict.get(UfmPkeysConstants.PKEYS_OPERATIONS.get("delete_pkey"))
        UfmPkeysManagement.delete_pkey(pkey)
    else:
        message = "You must provide one of the following operations: "+ \
                  ''.join(['--{0} | '.format(item) for key,item in UfmPkeysConstants.PKEYS_OPERATIONS.items()])

        Logger.log_message(message, LOG_LEVELS.ERROR)

