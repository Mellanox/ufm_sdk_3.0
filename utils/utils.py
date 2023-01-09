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
@date:   Sep 29, 2021
"""
import logging
import json
import ipaddress
import os
import re
from datetime import datetime
from utils.logger import Logger, LOG_LEVELS


class Utils:

    @staticmethod
    def write_json_to_file(path, json_obj):
        try:
            f = open(path, "w")
            f.write(json.dumps(json_obj))
            f.close()
            Logger.log_message(f'Finished writing to json file {path}')
        except Exception as e:
            logging.error(e)

    @staticmethod
    def read_json_from_file(path):
        data = ''
        try:
            with open(path) as f:
                data = json.load(f)
            logging.info(f'Finished reading from json file {path}')
        except Exception as e:
            logging.error(e)
        return data

    @staticmethod
    def write_text_to_file(path, text):
        try:
            if not os.path.exists(os.path.dirname(path)):
                os.makedirs(os.path.dirname(path))
            f = open(path, "w")
            f.write(text)
            f.close()
            Logger.log_message(f'Finished writing to text file {path}', LOG_LEVELS.DEBUG)
        except Exception as e:
            logging.error(e)

    @staticmethod
    def get_timebased_filename():
        dateTimeObj = datetime.now()
        file_name = f'{dateTimeObj.year}_{dateTimeObj.month}_{dateTimeObj.day}_' \
                           f'{dateTimeObj.hour}_{dateTimeObj.minute}_{dateTimeObj.second}'
        return file_name

    @staticmethod
    def is_ipv6_address(ip_address):
        """
        check if IPv6 address and if yes - return True otherwise return False
        @param ip_address:
        """
        try:
            ipaddress.IPv6Address(str(ip_address))
        except:
            return False
        return True

    @staticmethod
    def get_absolute_path(path):
        dirname = os.path.dirname(__file__)
        current_abs_path = os.path.abspath(os.path.join(dirname, os.pardir))
        return os.path.join(current_abs_path, path)


    @staticmethod
    def get_plugin_port(port_conf_file, default_port_value):
        port = default_port_value
        port_regex = re.compile("^port[ =\t]*(?P<web_port>[0-9]{1,5})")
        try:
            with open(port_conf_file, 'r') as f:
                data = f.read()
            match = port_regex.search(data)
            if match:
                port = int(match.group('web_port'))
        except:
            pass
        return port
