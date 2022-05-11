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
from http import HTTPStatus

try:
    from utils.utils import Utils
    from utils.ufm_rest_client import UfmRestClient, HTTPMethods
    from utils.args_parser import ArgsParser
    from utils.config_parser import ConfigParser
    from utils.logger import Logger, LOG_LEVELS
except ModuleNotFoundError as e:
    print("Error occurred while importing python modules, "
          "Please make sure that you exported your repository to PYTHONPATH by running: "
          f'export PYTHONPATH="${{PYTHONPATH}}:{os.path.dirname(os.getcwd())}"')


class UfmEventsConstants:

    EVENTS_API_URL = "app/events"
    EVENTS_OPERATIONS = {
        "get_events": "get_events",
        "delete_event": "delete_event"
    }

    args_list = [
        {
            "name": f'--{EVENTS_OPERATIONS.get("get_events")}',
            "help": "Option to get all UFM events",
            "no_value": True
        },
        {
            "name": f'--{EVENTS_OPERATIONS.get("delete_event")}',
            "help": "Option to delete an UFM event"
        },
    ]


class UfmEventsConfigParser(ConfigParser):

    def __init__(self, args):
        super().__init__(args)


class UfmEventsManagement:

    @staticmethod
    def get_events():
        url = UfmEventsConstants.EVENTS_API_URL
        response = ufm_rest_client.send_request(url)
        if response and response.status_code == HTTPStatus.OK:
            Logger.log_message(response.json())
            return response.json()
        else:
            Logger.log_message(response.text, LOG_LEVELS.ERROR)
            return response

    @staticmethod
    def delete_event(event_id):
        url = f'{UfmEventsConstants.EVENTS_API_URL}/{event_id}'
        response = ufm_rest_client.send_request(url,HTTPMethods.DELETE)
        if response and response.status_code == HTTPStatus.OK:
            Logger.log_message(f'The event: {event_id} is removed successfully')
            return True
        else:
            Logger.log_message(f'The event: {event_id} isn`t removed, {response.text}', LOG_LEVELS.ERROR)
            return False


if __name__ == "__main__":
    # init app args
    args = ArgsParser.parse_args("UFM Events Management", UfmEventsConstants.args_list)

    # init app config parser & load config files
    config_parser = UfmEventsConfigParser(args)

    # init logs configs
    logs_file_name = config_parser.get_logs_file_name()
    logs_level = config_parser.get_logs_level()
    Logger.init_logs_config(logs_file_name, logs_level)


    # init ufm rest client
    ufm_rest_client = UfmRestClient(host = config_parser.get_ufm_host(),
                                    client_token=config_parser.get_ufm_access_token(),username = config_parser.get_ufm_username(),
                                    password = config_parser.get_ufm_password(),ws_protocol=config_parser.get_ufm_protocol())
    args_dict = args.__dict__
    if args_dict.get(UfmEventsConstants.EVENTS_OPERATIONS.get("get_events")):
        UfmEventsManagement.get_events()
    elif args_dict.get(UfmEventsConstants.EVENTS_OPERATIONS.get("delete_event")):
        event_id = config_parser.get_config_value(args_dict.get(UfmEventsConstants.EVENTS_OPERATIONS.get("delete_event")),
                                                  None,None)
        UfmEventsManagement.delete_event(event_id)
    else:
        message = "You must provide one of the following operations: "+ \
                  ''.join(['--{0} | '.format(item) for key,item in UfmEventsConstants.EVENTS_OPERATIONS.items()])

        Logger.log_message(message, LOG_LEVELS.ERROR)
