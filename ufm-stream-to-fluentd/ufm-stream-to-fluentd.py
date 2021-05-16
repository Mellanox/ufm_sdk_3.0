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
import time
import datetime
from pyfluent.client import FluentSender

PLUGIN_NAME = "UFM_API_Streaming"
CONFIG_FILE = 'ufm-stream-to-fluentd.cfg'
FLUENTD_METADATA_FILE = 'fluentd_metadata.json'
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
global fluentd_metadata
global fluentd_host
global fluentd_port
global ufm_host
global ufm_server_name
global ufm_protocol
global ufm_username
global ufm_password
global local_streaming
global internal_ufm_server_port
global args
global streaming_interval
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
    global fluentd_metadata
    try:
        current_time = int(time.time())
        message_id = fluentd_metadata.message_id + 1
        logging.info(f'Streaming to Fluentd IP: {fluentd_host} port: {fluentd_port}')
        fluent = FluentSender(fluentd_host, fluentd_port, ufm_server_name)
        fluentd_message = {
            "id": message_id,
            "timestamp": datetime.datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S'),
            "type": "full"
        }
        if enabled_streaming_systems:
            fluentd_message["systems"] = {
                "systems_list": stored_systems_api
            }
        if enabled_streaming_ports:
            fluentd_message["ports"] = {
                "ports_list": stored_ports_api
            }
        if enabled_streaming_links:
            fluentd_message["links"] = {
                "links_list": stored_links_api
            }
        if enabled_streaming_alarms:
            fluentd_message["alarms"] = {
                "alarms_list": stored_alarms_api
            }
        fluent.send(fluentd_message, PLUGIN_NAME)
        fluentd_metadata.message_id = message_id
        fluentd_metadata.message_timestamp = current_time
        write_json_to_file(FLUENTD_METADATA_FILE, fluentd_metadata.__dict__)
        logging.info(f'Finished Streaming to Fluentd Host: {fluentd_host} port: {fluentd_port}')
    except Exception as e:
        logging.error(e)


def load_fluentd_metadata_json():
    global fluentd_metadata
    logging.info(f'Call load_fluentd_metadata_json')
    if os.path.exists(FLUENTD_METADATA_FILE):
        fluentd_metadata_result = read_json_from_file(FLUENTD_METADATA_FILE)
        fluentd_metadata = FluentdMessageMetadata(fluentd_metadata_result['message_id'],
                                                  fluentd_metadata_result['message_timestamp'])
    else:
        fluentd_metadata = FluentdMessageMetadata()


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
    headers = {}
    # token auth: to be done
    # if token:
    #    headers = {"Authorization": "Bearer " + token['access_token']}
    try:
        logging.info(f'Send UFM API Request, URL: {url}')
        if local_streaming:
            url = 'http://127.0.0.1:' + internal_ufm_server_port + '/' + url
            headers = {"X-Remote-User": ufm_username}
            response = requests.get(url, verify=False, headers=headers)
        else:
            url = ufm_protocol + '://' + ufm_host + '/ufmRest/' + url
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
    parser.add_argument('--ufm_local_streaming', help='Enable/Disable streaming from local ufm server')
    parser.add_argument('--internal_ufm_server_port', help='Port of internal ufm server')
    parser.add_argument('--ufm_host', help='Host name or IP of UFM server')
    parser.add_argument('--ufm_server_name', help='UFM server name')
    parser.add_argument('--ufm_protocol', help='http | https ')
    parser.add_argument('--ufm_username', help='Username of UFM user')
    parser.add_argument('--ufm_password', help='Password of UFM user')
    parser.add_argument('--logs_file_name', help='Logs file name')
    parser.add_argument('--logs_level', help='logs level [ FATAL | ERROR | WARNING | INFO | DEBUG | NOTSET ]')
    parser.add_argument('--streaming_interval', help='Streaming interval in minutes [Default is 5 minutes]')
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
    global local_streaming
    global internal_ufm_server_port
    global ufm_host
    global ufm_server_name
    global ufm_protocol
    global ufm_username
    global ufm_password
    global streaming_interval
    global enabled_streaming_systems
    global enabled_streaming_ports
    global enabled_streaming_links
    global enabled_streaming_alarms
    fluentd_host = get_config_value(args.fluentd_host, 'fluentd-config', 'host', None)
    fluentd_port = int(get_config_value(args.fluentd_port, 'fluentd-config', 'port', None))
    ufm_host = get_config_value(args.ufm_host, 'ufm-remote-server-config', 'host', None)
    ufm_server_name = get_config_value(args.ufm_server_name, 'ufm-remote-server-config', 'server_name', None)
    ufm_protocol = get_config_value(args.ufm_protocol, 'ufm-remote-server-config', 'ws_protocol', None)
    ufm_username = get_config_value(args.ufm_username, 'ufm-remote-server-config', 'username', None)
    ufm_password = get_config_value(args.ufm_password, 'ufm-remote-server-config', 'password', None)
    streaming_interval = int(get_config_value(args.streaming_interval, 'streaming-config', 'interval', 5))
    local_streaming = get_config_value(args.ufm_local_streaming,
                                       'ufm-local-server-config',
                                       'local_streaming',
                                       False) == 'True'
    internal_ufm_server_port = get_config_value(args.internal_ufm_server_port,
                                                'ufm-local-server-config',
                                                'internal_server_port',
                                                None)
	enabled_streaming_systems = get_config_value(args.streaming_systems, 'streaming-config', 'systems', True) == 'True'
    enabled_streaming_ports = get_config_value(args.streaming_ports, 'streaming-config', 'ports', True) == 'True'
    enabled_streaming_links = get_config_value(args.streaming_links, 'streaming-config', 'links', True) == 'True'
    enabled_streaming_alarms = get_config_value(args.streaming_alarms, 'streaming-config', 'alarms', True) == 'True'


class FluentdMessageMetadata:
    def __init__(self, message_id=0, message_timestamp=None):
        self.message_id = message_id
        self.message_timestamp = message_timestamp

    def get_message_id(self):
        return self.message_id

    def set_message_id(self, message_id):
        self.message_id = message_id

    def get_message_timestamp(self):
        return self.message_timestamp

    def set_message_timestamp(self, message_timestamp):
        self.message_timestamp = message_timestamp


def streaming_interval_is_valid():
    if fluentd_metadata and fluentd_metadata.message_timestamp:
        # The timestamp of the last message sent exists => check if it larger than the configurable streaming interval
        time_delta = datetime.datetime.now() - datetime.datetime.fromtimestamp(fluentd_metadata.message_timestamp)
        streaming_interval_in_seconds = streaming_interval * 60
        return time_delta.total_seconds() >= streaming_interval_in_seconds
    return True


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

        load_fluentd_metadata_json()
        if streaming_interval_is_valid():
            load_memory_with_jsons()
            update_ufm_apis()
            stream_to_fluentd()
        else:
            logging.error("Streaming interval isn't completed")

    except Exception as global_ex:
        logging.error(global_ex)
