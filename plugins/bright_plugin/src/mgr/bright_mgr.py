"""
@copyright:
    Copyright (C) Nvidia Technologies Ltd. 2014-2022.  ALL RIGHTS RESERVED.

    This software product is a proprietary product of Mellanox Technologies
    Ltd. (the "Company") and all right, title, and interest in and to the
    software product, including all associated intellectual property rights,
    are and shall remain exclusively with the Company.

    This software product is governed by the End User License Agreement
    provided with the software product.

@author: Nasr Ajaj
@date:   May 12, 2022
"""
import os
import sys

sys.path.append(os.getcwd())
import json
import logging

import requests
from utils.config_parser import ConfigParser
from utils.singleton import Singleton


class BrightConstants:
    PLUGIN_NAME = "Bright"
    CERT_DIR = '/config/cert'

    args_list = [
        {
            "name": '--bright_host',
            "help": "Host or IP of Bright endpoint"
        },{
            "name": '--bright_port',
            "help": "Port of Bright endpoint"
        },{
            "name": '--bright_cert_key',
            "help": "Certificate key of Bright endpoint"
        },{
            "name": '--bright_cert_file',
            "help": "Certificate file of Bright endpoint"
        }
    ]


class BrightConfigParser(ConfigParser):
    # for debugging
    # config_file = "../conf/bright_plugin.cfg"

    config_file = "/config/bright_plugin.cfg"  # this path on the docker

    BRIGHT_ENDPOINT_SECTION = "bright-endpoint"
    BRIGHT_ENDPOINT_SECTION_HOST = "host"
    BRIGHT_ENDPOINT_SECTION_PORT = "port"

    META_FIELDS_SECTION = "meta-fields"

    def __init__(self, args):
        super().__init__(args, False)
        self.sdk_config.read(self.config_file)

    def get_bright_host(self):
        return self.get_config_value(self.args.bright_host,
                                     self.BRIGHT_ENDPOINT_SECTION,
                                     self.BRIGHT_ENDPOINT_SECTION_HOST)

    def get_bright_port(self):
        return self.safe_get_int(self.args.bright_port,
                                 self.BRIGHT_ENDPOINT_SECTION,
                                 self.BRIGHT_ENDPOINT_SECTION_PORT,
                                 0)


class BrightMgr(Singleton):

    def __init__(self, config_parser):
        self.config_parser = config_parser
        self.scheme = "https"
        self.BRIGHT_IP = config_parser.get_bright_host()
        self.BRIGHT_PORT = config_parser.get_bright_port()
        self.BRIGHT_DEVICE_JSON_URL = "json?indent=1"
        self.BRIGHT_CERT_FILE = os.path.join(BrightConstants.CERT_DIR, 'admin.pem')
        self.BRIGHT_CERT_KEY = os.path.join(BrightConstants.CERT_DIR, 'admin.key')

    def get_bright_devices(self):
        url = self.BRIGHT_DEVICE_JSON_URL
        url = '%s://%s:%s/%s' % (self.scheme, self.BRIGHT_IP, self.BRIGHT_PORT, url)
        data = {
            "service": "cmdevice",
            "call": "getDevices",
            "minify": True
        }
        post_request = requests.post(url,json=data, cert=(self.BRIGHT_CERT_FILE, self.BRIGHT_CERT_KEY), verify=False)
        if post_request.status_code != 200:
            logging.error("bright server returned status code %s", post_request.status_code)
            return None
        else:
            entities = json.loads(post_request.text)
            bright_devices = list(map(lambda device: device['hostname'], entities))
            return bright_devices

    def get_device_jobs(self, device):
        url = self.BRIGHT_DEVICE_JSON_URL
        url = '%s://%s:%s/%s' % (self.scheme, self.BRIGHT_IP, self.BRIGHT_PORT, url)
        data = {
            "service": "cmjob",
            "call": "getJobs",
            "args": [[], False],
        }
        post_request = requests.post(url, json=data, cert=(self.BRIGHT_CERT_FILE, self.BRIGHT_CERT_KEY), verify=False)
        if post_request.status_code != 200:
            logging.error("Bright server has returned error %s", post_request.text)
            return None
        else:
            jobs = json.loads(post_request.text)['jobs']
            jobs = list(filter(lambda job: (device in job['nodes']), jobs))
            return jobs
