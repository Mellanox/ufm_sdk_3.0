#
# Copyright (C) Mellanox Technologies Ltd. 2021.  ALL RIGHTS RESERVED.
#
# See file LICENSE for terms.

import requests
import configparser
import json
import logging
import os
import argparse
from pyfluent.client import FluentSender

PLUGIN_NAME = "UFM_API_Streaming"
CONFIG_FILE = 'ufm-stream-to-fluentd.cfg'
UFM_API_VERSIONING = 'app/versioning'
UFM_API_VERSIONING_RESULT = 'api_results/versioning.json'
UFM_API_SYSTEMS = 'resources/systems'
UFM_API_SYSTEMS_RESULT = 'api_results/systems.json'
UFM_API_PORTS = 'resources/ports'
UFM_API_PORTS_RESULT = 'api_results/ports.json'
UFM_API_LINKS = 'resources/links'
UFM_API_LINKS_RESULT = 'api_results/links.json'
UFM_API_ALARMS = 'app/alarms'
UFM_API_ALARMS_RESULT = 'api_results/alarms.json'


global logs_file_name
global logs_level
global fluentd_host
global fluentd_port
global ufm_host
global ufm_protocol
global ufm_username
global ufm_password
global args
global enabled_streaming_systems
global enabled_streaming_ports
global enabled_streaming_links
global enabled_streaming_alarms

stored_versioning_api = ''
stored_systems_api = []
stored_ports_api = []
stored_links_api = []
stored_alarms_api = []


def read_json_from_file(path):
    data = ''
    try:
        with open(path) as f:
            data = json.load(f)
        logging.info(f'Finished reading from json file {path}')
    except Exception as e:
        logging.error(e)
    return data


def write_json_to_file(path, json_obj):
    try:
        f = open(path, "w")
        f.write(json.dumps(json_obj))
        f.close()
        logging.info(f'Finished writing to json file {path}')
    except Exception as e:
        logging.error(e)


def stream_to_fluentd():
    try:
        logging.info(f'Streaming to Fluentd IP: {fluentd_host} port: {fluentd_port}')
        fluent = FluentSender(fluentd_host, fluentd_port, 'pyfluent')
        if enabled_streaming_systems:
            fluent.send(stored_systems_api, PLUGIN_NAME)
        if enabled_streaming_ports:
            fluent.send(stored_ports_api, PLUGIN_NAME)
        if enabled_streaming_links:
            fluent.send(stored_links_api, PLUGIN_NAME)
        if enabled_streaming_alarms:
            fluent.send(stored_alarms_api, PLUGIN_NAME)
        logging.info(f'Finished Streaming to Fluentd Host: {fluentd_host} port: {fluentd_port}')
    except Exception as e:
        logging.error(e)


def load_memory_with_jsons():
    global stored_versioning_api
    global stored_systems_api
    global stored_ports_api
    global stored_links_api
    global stored_alarms_api

    try:
        logging.info(f'Call load_memory_with_jsons')

        if os.path.exists(UFM_API_VERSIONING_RESULT):
            stored_versioning_api = read_json_from_file(UFM_API_VERSIONING_RESULT)

        if os.path.exists(UFM_API_SYSTEMS_RESULT) and enabled_streaming_systems:
            stored_systems_api = read_json_from_file(UFM_API_SYSTEMS_RESULT)

        if os.path.exists(UFM_API_PORTS_RESULT) and enabled_streaming_ports:
            stored_ports_api = read_json_from_file(UFM_API_PORTS_RESULT)

        if os.path.exists(UFM_API_LINKS_RESULT) and enabled_streaming_links:
            stored_links_api = read_json_from_file(UFM_API_LINKS_RESULT)

        if os.path.exists(UFM_API_ALARMS_RESULT) and enabled_streaming_alarms:
            stored_alarms_api = read_json_from_file(UFM_API_ALARMS_RESULT)
    except Exception as e:
        logging.error(e)


def update_ufm_apis():
    global stored_versioning_api
    global stored_systems_api
    global stored_ports_api
    global stored_links_api
    global stored_alarms_api

    try:
        logging.info(f'Call update_ufm_apis')

        ufm_new_version = send_ufm_request(UFM_API_VERSIONING)

        # check if systems api is changed
        if enabled_streaming_systems and \
                (stored_versioning_api == '' or
                 ufm_new_version["switches_version"] != stored_versioning_api["switches_version"]):
            stored_systems_api = send_ufm_request(UFM_API_SYSTEMS)
            write_json_to_file(UFM_API_SYSTEMS_RESULT, stored_systems_api)

        # check if ports api is changed
        if enabled_streaming_ports and \
                (stored_versioning_api == '' or
                 ufm_new_version["ports_version"] != stored_versioning_api["ports_version"]):
            stored_ports_api = send_ufm_request(UFM_API_PORTS)
            write_json_to_file(UFM_API_PORTS_RESULT, stored_ports_api)

        # check if links api is changed
        if enabled_streaming_links and \
                (stored_versioning_api == '' or
                 ufm_new_version["links_version"] != stored_versioning_api["links_version"]):
            stored_links_api = send_ufm_request(UFM_API_LINKS)
            write_json_to_file(UFM_API_LINKS_RESULT, stored_links_api)

        # check if alarms api is changed
        if enabled_streaming_alarms and \
                (stored_versioning_api == '' or
                 ufm_new_version["alarms_version"] != stored_versioning_api["alarms_version"]):
            stored_alarms_api = send_ufm_request(UFM_API_ALARMS)
            write_json_to_file(UFM_API_ALARMS_RESULT, stored_alarms_api)

        stored_versioning_api = ufm_new_version
        write_json_to_file(UFM_API_VERSIONING_RESULT, stored_versioning_api)
    except Exception as e:
        logging.error(e)


def send_ufm_request(url):
    url = ufm_protocol + '://' + ufm_host + '/ufmRest/' + url
    headers = {}
    # token auth: to be done
    # if token:
    #    headers = {"Authorization": "Bearer " + token['access_token']}
    try:
        logging.info(f'Send UFM API Request, URL: {url}')
        response = requests.get(url, verify=False, headers=headers, auth=(ufm_username, ufm_password))
        logging.info("UFM API Request Status [" + str(response.status_code) + "], URL " + url)
        if response.raise_for_status():
            logging.error(response.raise_for_status())
    except Exception as e:
        logging.error(e)
    return response.json()


def get_config_value(arg, section, key, default=None):
    if arg:
        return arg
    elif section in CONFIG and key in CONFIG[section]:
        return CONFIG[section][key]
    elif default is not None:
        return default
    else:
        raise ValueError(F'Error to request value : {section}.{key}')


def parse_args():
    parser = argparse.ArgumentParser(description='Streams UFM API to fluentD')
    parser.add_argument('--fluentd_host', help='Host name or IP of fluentd endpoint')
    parser.add_argument('--fluentd_port', help='Port of fluentd endpoint')
    parser.add_argument('--ufm_host', help='Host name or IP of UFM server')
    parser.add_argument('--ufm_protocol', help='http | https ')
    parser.add_argument('--ufm_username', help='Username of UFM user')
    parser.add_argument('--ufm_password', help='Password of UFM user')
    parser.add_argument('--logs_file_name', help='Logs file name')
    parser.add_argument('--logs_level', help='logs level [ FATAL | ERROR | WARNING | INFO | DEBUG | NOTSET ]')
    parser.add_argument('--streaming_systems', help='Enable/Disable streaming systems API [True|False]')
    parser.add_argument('--streaming_ports', help='Enable/Disable streaming ports API [True|False]')
    parser.add_argument('--streaming_alarms', help='Enable/Disable streaming alarms API [True|False]')
    parser.add_argument('--streaming_links', help='Enable/Disable streaming links API [True|False]')
    return parser.parse_args()


def init_logging_config():
    global logs_file_name
    global logs_level
    logs_file_name = get_config_value(args.logs_file_name, 'logs-config', 'logs_file_name', '')
    logs_level = get_config_value(args.logs_level, 'logs-config', 'logs_level', 'INFO')
    logging.basicConfig(filename=logs_file_name,
                        level=logs_level,
                        format='%(asctime)s %(levelname)s %(name)s : %(message)s')


def check_app_params():
    global fluentd_host
    global fluentd_port
    global ufm_host
    global ufm_protocol
    global ufm_username
    global ufm_password
    global enabled_streaming_systems
    global enabled_streaming_ports
    global enabled_streaming_links
    global enabled_streaming_alarms
    fluentd_host = get_config_value(args.fluentd_host, 'fluentd-config', 'host', None)
    fluentd_port = int(get_config_value(args.fluentd_port, 'fluentd-config', 'port', None))
    ufm_host = get_config_value(args.ufm_host, 'ufm-server-config', 'host', None)
    ufm_protocol = get_config_value(args.ufm_protocol, 'ufm-server-config', 'ws_protocol', None)
    ufm_username = get_config_value(args.ufm_username, 'ufm-server-config', 'username', None)
    ufm_password = get_config_value(args.ufm_password, 'ufm-server-config', 'password', None)
    enabled_streaming_systems = get_config_value(args.streaming_systems, 'streaming-config', 'systems', True) == 'True'
    enabled_streaming_ports = get_config_value(args.streaming_ports, 'streaming-config', 'ports', True) == 'True'
    enabled_streaming_links = get_config_value(args.streaming_links, 'streaming-config', 'links', True) == 'True'
    enabled_streaming_alarms = get_config_value(args.streaming_alarms, 'streaming-config', 'alarms', True) == 'True'


# if run as main module
if __name__ == "__main__":
    try:
        # init app args
        args = parse_args()

        # init app configurations
        CONFIG = configparser.RawConfigParser()
        CONFIG.read(CONFIG_FILE)

        # init logging configuration
        init_logging_config()

        # check app parameters
        check_app_params()

        load_memory_with_jsons()
        update_ufm_apis()
        stream_to_fluentd()

    except Exception as global_ex:
        logging.error(global_ex)
