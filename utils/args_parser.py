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
@date:   Sep 28, 2021
"""
import argparse

sdk_args_list = [
    {
        "name": "--ufm_host",
        "help": "Host name or IP of UFM server"
    },{
        "name": "--ufm_protocol",
        "help": "http | https "
    },{
        "name": "--ufm_username",
        "help": "Username of UFM user"
    },{
        "name": "--ufm_password",
        "help": "Password of UFM user"
    },{
        "name": "--ufm_access_token",
        "help": "Access token of UFM"
    },{
        "name": "--logs_file_name",
        "help": "Logs file name"
    },{
        "name": "--logs_level",
        "help": "logs level [ FATAL | ERROR | WARNING | INFO | DEBUG | NOTSET ]"
    }
]


class ArgsParser(object):

    @staticmethod
    def parse_args(description ,args_list):
        parser = argparse.ArgumentParser(description=description)
        for arg in sdk_args_list+args_list:
            parser.add_argument(arg.get("name"), help=arg.get("help"),
                                action= 'store_true' if arg.get('no_value') else 'store')
        return parser.parse_args()
