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

global logs_file_name
global logs_level
global fluentd_host
global fluentd_port
global ufm_host
global ufm_protocol
global ufm_username
global ufm_password
global args

stored_versioning_api = ''
stored_systems_api = []
stored_ports_api = []
stored_links_api = []


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
        fluent.send(stored_systems_api, PLUGIN_NAME)
        fluent.send(stored_ports_api, PLUGIN_NAME)
        fluent.send(stored_links_api, PLUGIN_NAME)
        logging.info(f'Finished Streaming to Fluentd Host: {fluentd_host} port: {fluentd_port}')
    except Exception as e:
        logging.error(e)


def load_memory_with_jsons():
    global stored_versioning_api
    global stored_systems_api
    global stored_ports_api
    global stored_links_api

    try:
        logging.info(f'Call load_memory_with_jsons')

        if os.path.exists(UFM_API_VERSIONING_RESULT):
            stored_versioning_api = read_json_from_file(UFM_API_VERSIONING_RESULT)

        if os.path.exists(UFM_API_SYSTEMS_RESULT):
            stored_systems_api = read_json_from_file(UFM_API_SYSTEMS_RESULT)

        if os.path.exists(UFM_API_PORTS_RESULT):
            stored_ports_api = read_json_from_file(UFM_API_PORTS_RESULT)

        if os.path.exists(UFM_API_LINKS_RESULT):
            stored_links_api = read_json_from_file(UFM_API_LINKS_RESULT)
    except Exception as e:
        logging.error(e)


def update_ufm_apis():
    global stored_versioning_api
    global stored_systems_api
    global stored_ports_api
    global stored_links_api

    try:
        logging.info(f'Call update_ufm_apis')

        ufm_new_version = send_ufm_request(UFM_API_VERSIONING)

        # check if systems api is changed
        if (stored_versioning_api == '' or ufm_new_version["switches_version"] != stored_versioning_api[
            "switches_version"] or
                ufm_new_version["switches_version"] != stored_versioning_api["switches_version"]):
            stored_systems_api = send_ufm_request(UFM_API_SYSTEMS)
            write_json_to_file(UFM_API_SYSTEMS_RESULT, stored_systems_api)

        # check if ports api is changed
        if stored_versioning_api == '' or ufm_new_version["ports_version"] != stored_versioning_api["ports_version"]:
            stored_ports_api = send_ufm_request(UFM_API_PORTS)
            write_json_to_file(UFM_API_PORTS_RESULT, stored_ports_api)

        # check if links api is changed
        if stored_versioning_api == '' or ufm_new_version["links_version"] != stored_versioning_api["links_version"]:
            stored_links_api = send_ufm_request(UFM_API_LINKS)
            write_json_to_file(UFM_API_LINKS_RESULT, stored_links_api)

        stored_versioning_api = ufm_new_version
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


def get_config_value(section, key):
    return section in CONFIG and key in CONFIG[section]


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
    return parser.parse_args()


def init_logging_config():
    global logs_file_name
    global logs_level
    logging_to_default_stream = False

    if args.logs_file_name:
        logs_file_name = args.logs_file_name
    elif get_config_value('logs-config', 'logs_file_name'):
        logs_file_name = CONFIG['logs-config']['logs_file_name']
    else:
        logging_to_default_stream = True

    if args.logs_level:
        logs_level = args.logs_level
    elif get_config_value('logs-config', 'logs_level'):
        logs_level = CONFIG['logs-config']['logs_level']
    else:
        logging_to_default_stream = True

    if not logging_to_default_stream:
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

    if args.fluentd_host:
        fluentd_host = args.fluentd_host
    elif get_config_value('fluentd-config', 'host'):
        fluentd_host = CONFIG['fluentd-config']['host']
    else:
        raise ValueError("fluentd_host must be provided")

    if args.fluentd_port:
        fluentd_port = int(args.fluentd_port)
    elif get_config_value('fluentd-config', 'port'):
        fluentd_port = int(CONFIG['fluentd-config']['port'])
    else:
        raise ValueError("fluentd_port must be provided")

    if args.ufm_host:
        ufm_host = args.ufm_host
    elif get_config_value('ufm-server-config', 'host'):
        ufm_host = CONFIG['ufm-server-config']['host']
    else:
        raise ValueError("ufm_host must be provided")

    if args.ufm_protocol:
        ufm_protocol = args.ufm_protocol
    elif get_config_value('ufm-server-config', 'ws_protocol'):
        ufm_protocol = CONFIG['ufm-server-config']['ws_protocol']
    else:
        ufm_protocol = 'https'

    if args.ufm_username:
        ufm_username = args.ufm_username
    elif get_config_value('ufm-server-config', 'username'):
        ufm_username = CONFIG['ufm-server-config']['username']
    else:
        raise ValueError("ufm_username must be provided")

    if args.ufm_password:
        ufm_password = args.ufm_password
    elif get_config_value('ufm-server-config', 'password'):
        ufm_password = CONFIG['ufm-server-config']['password']
    else:
        raise ValueError("ufm_password must be provided")


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
