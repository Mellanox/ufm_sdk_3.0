import requests
import configparser
import json
import logging
import constants
import os
from pyfluent.client import FluentSender

# init app configurations
CONFIG = configparser.RawConfigParser()
CONFIG.read(constants.CONFIG_FILE)

# init app logging
logging.basicConfig(filename=CONFIG['logs-config']['logs_file_name'],
                    level=CONFIG['logs-config']['logs_level'],
                    format='%(asctime)s %(levelname)s %(name)s : %(message)s')

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
        fluend_ip = CONFIG['fluentd-config']['ip']
        fluend_port = int(CONFIG['fluentd-config']['port'])
        logging.info(f'Streaming to Fluentd IP: {fluend_ip} port: {fluend_port}')
        fluent = FluentSender(fluend_ip, fluend_port, 'pyfluent')
        fluent.send(stored_systems_api, constants.PLUGIN_NAME)
        fluent.send(stored_ports_api, constants.PLUGIN_NAME)
        fluent.send(stored_links_api, constants.PLUGIN_NAME)
        logging.info(f'Finished Streaming to Fluentd IP: {fluend_ip} port: {fluend_port}')
    except Exception as e:
        logging.error(e)



def load_memory_with_jsons():
    global stored_versioning_api
    global stored_systems_api
    global stored_ports_api
    global stored_links_api

    try:
        logging.info(f'Call load_memory_with_jsons')

        if os.path.exists(constants.UFM_API_VERSIONING_RESULT):
            stored_versioning_api = read_json_from_file(constants.UFM_API_VERSIONING_RESULT)

        if os.path.exists(constants.UFM_API_SYSTEMS_RESULT):
            stored_systems_api = read_json_from_file(constants.UFM_API_SYSTEMS_RESULT)

        if os.path.exists(constants.UFM_API_PORTS_RESULT):
            stored_ports_api = read_json_from_file(constants.UFM_API_PORTS_RESULT)

        if os.path.exists(constants.UFM_API_LINKS_RESULT):
            stored_links_api = read_json_from_file(constants.UFM_API_LINKS_RESULT)
    except Exception as e:
        logging.error(e)


def update_ufm_apis():
    global stored_versioning_api
    global stored_systems_api
    global stored_ports_api
    global stored_links_api

    try:
        logging.info(f'Call update_ufm_apis')

        ufm_new_version = send_ufm_request(constants.UFM_API_VERSIONING)

        # check if systems api is changed
        if (stored_versioning_api == '' or ufm_new_version["switches_version"] != stored_versioning_api[
            "switches_version"] or
                    ufm_new_version["switches_version"] != stored_versioning_api["switches_version"]):
            stored_systems_api = send_ufm_request(constants.UFM_API_SYSTEMS)
            write_json_to_file(constants.UFM_API_SYSTEMS_RESULT, stored_systems_api)

        # check if ports api is changed
        if stored_versioning_api == '' or ufm_new_version["ports_version"] != stored_versioning_api["ports_version"]:
            stored_ports_api = send_ufm_request(constants.UFM_API_PORTS)
            write_json_to_file(constants.UFM_API_PORTS_RESULT, stored_ports_api)

        # check if links api is changed
        if stored_versioning_api == '' or ufm_new_version["links_version"] != stored_versioning_api["links_version"]:
            stored_links_api = send_ufm_request(constants.UFM_API_LINKS)
            write_json_to_file(constants.UFM_API_LINKS_RESULT, stored_links_api)

        stored_versioning_api = ufm_new_version
    except Exception as e:
        logging.error(e)


def send_ufm_request(url):
    ip = CONFIG['ufm-server-config']['ip']
    username = CONFIG['ufm-server-config']['username']
    password = CONFIG['ufm-server-config']['password']
    ws_protocol = CONFIG['ufm-server-config']['ws_protocol']
    url = ws_protocol + '://' + ip + '/ufmRest/' + url
    headers = {}
    # token auth: to be done
    # if token:
    #    headers = {"Authorization": "Bearer " + token['access_token']}
    try:
        logging.info(f'Send UFM API Request, URL: {url}')
        response = requests.get(url, verify=False, headers=headers, auth=(username, password))
        logging.info("UFM API Request Status [" + str(response.status_code) + "], URL " + url)
        if response.raise_for_status():
            logging.error(response.raise_for_status())
    except Exception as e:
        logging.error(e)
    return response.json()

# if run as main module
if __name__ == "__main__":

    logging.info(f'Start main')
    load_memory_with_jsons()
    update_ufm_apis()
    stream_to_fluentd()
