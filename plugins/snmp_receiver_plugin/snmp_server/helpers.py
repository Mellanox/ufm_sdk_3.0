#
# Copyright © 2013-2022 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
#
# @author: Alexander Tolikin
# @date:   November, 2022
#
import configparser
from http import HTTPStatus
import logging
import requests
import os

HTTP_ERROR = HTTPStatus.INTERNAL_SERVER_ERROR
HOST = "127.0.0.1:8000"
PROTOCOL = "http"
SESSION = requests.Session()
SESSION.headers = {"X-Remote-User": "ufmsystem"}
EMPTY_IP = "0.0.0.0"

def succeded(status_code):
    return status_code in [HTTPStatus.OK, HTTPStatus.ACCEPTED]

def get_request(resource):
    request = PROTOCOL + '://' + HOST + resource
    logging.info(f"GET {request}")
    try:
        response = SESSION.get(request, verify=False)
        return response.status_code, response.json()
    except Exception as e:
        error = f"{request} failed with exception: {e}"
        logging.error(error)
        return HTTP_ERROR, {error}

def post_request(resource, json=None, return_headers=False):
    request = PROTOCOL + '://' + HOST + resource
    logging.info(f"POST {request}")
    try:
        response = SESSION.post(request, verify=False, json=json)
        if return_headers:
            return response.status_code, response.headers
        return response.status_code, response.text
    except Exception as e:
        error = f"{request} failed with exception: {e}"
        logging.error(error)
        return HTTP_ERROR, error

async def async_post(session, resource, json=None):
    request = PROTOCOL + '://' + HOST + resource
    logging.info(f"POST {request}")
    try:
        async with session.post(request, json=json) as resp:
            text = await resp.text()
            return resp.status, text
    except Exception as e:
        error = f"{request} failed with exception: {e}"
        logging.error(error)
        return HTTP_ERROR, error

def get_ufm_switches():
    resource = "/resources/systems?type=switch"
    status_code, json = get_request(resource)
    if not succeded(status_code):
        return {}
    switch_ips = {}
    for switch in json:
        ip = switch["ip"]
        system_name = switch["system_name"]
        guid = switch["guid"]
        if not ip == EMPTY_IP:
            switch_ips[ip] = (system_name, guid)
    logging.debug(f"List of switches in the fabric: {switch_ips.keys()}")
    return switch_ips

class ConfigParser:
    config_file_name = "../build/config/snmp.conf"
    # config_file_name = "/config/snmp.conf"

    snmp_config = configparser.ConfigParser()
    if not os.path.exists(config_file_name):
        logging.error(f"No config file {config_file_name} found!")
    snmp_config.read(config_file_name)
    log_file_path = snmp_config.get("Log", "log_file_path")
    log_level = snmp_config.get("Log", "log_level")
    log_file_max_size = snmp_config.getint("Log", "log_file_max_size")
    log_file_backup_count = snmp_config.getint("Log", "log_file_backup_count")
    log_format = '%(asctime)-15s %(levelname)s %(message)s'

    snmp_ip = snmp_config.get("SNMP", "snmp_ip")
    snmp_port = snmp_config.getint("SNMP", "snmp_port")
    community = snmp_config.get("SNMP", "community")
    multiple_events = snmp_config.getboolean("SNMP", "multiple_events")