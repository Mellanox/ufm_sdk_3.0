#
# Copyright © 2013-2023 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
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
import base64
import configparser
from http import HTTPStatus
import logging
from logging.handlers import RotatingFileHandler
import requests
import os
import socket
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from urllib.parse import quote

HTTP_ERROR = HTTPStatus.INTERNAL_SERVER_ERROR
HOST = "127.0.0.1:8000"
PROTOCOL = "http"
EMPTY_IP = "0.0.0.0"
PROVISIONING_TIMEOUT = 20
COMPLETED_WITH_ERRORS = "Completed With Errors"
COMPLETED = "Completed"

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('192.255.255.255', 1))
        local_ip = s.getsockname()[0]
    except:
        local_ip = ''
    finally:
        s.close()
    return local_ip

LOCAL_IP = get_local_ip()

def succeded(status_code):
    return status_code in [HTTPStatus.OK, HTTPStatus.ACCEPTED]

def get_request(resource, debug=False):
    request = PROTOCOL + '://' + HOST + resource
    if debug:
        logging.debug(f"GET {request}")
    else:
        logging.info(f"GET {request}")
    try:
        session = requests.Session()
        session.headers = {"X-Remote-User": "ufmsystem"}
        response = session.get(request, verify=False)
        return response.status_code, response.json()
    except Exception as e:
        error = f"{request} failed with exception: {e}"
        return HTTP_ERROR, {error}

async def async_post(session, resource, json=None):
    request = PROTOCOL + '://' + HOST + resource
    logging.info(f"POST {request}")
    try:
        async with session.post(request, json=json) as resp:
            text = await resp.text()
            return resp.status, text
    except Exception as e:
        error = f"{request} failed with exception: {e}"
        return HTTP_ERROR, error

def get_ufm_switches():
    resource = "/resources/systems?type=switch"
    status_code, json = get_request(resource)
    if not succeded(status_code):
        logging.error(f"Failed to get list of UFM switches")
        return {}
    new_key = RSA.generate(1024)
    public_key = new_key.publickey().export_key()
    public_key = quote(public_key, safe='')
    private_key = new_key.export_key()
    priv_key = RSA.import_key(private_key)
    cipher = PKCS1_OAEP.new(priv_key)
    switch_dict = {}
    for switch in json:
        ip = switch["ip"]
        if not ip == EMPTY_IP:
            guid = switch["guid"]
            resource = f"/resources/systems/{guid}/credentials?credential_types=SSH_Switch&public_key={public_key}"
            status_code, response = get_request(resource)
            if not succeded(status_code):
                logging.error(f"Failed to get switch {ip} credentials")
                continue
            if not response:
                logging.error(f"Switch {ip} credentials are empty, please update them via UFM Web UI")
                continue
            user = response[0]["user"]
            encrypted_credentials = response[0]["credentials"]
            credentials = cipher.decrypt(base64.b64decode(encrypted_credentials)).decode('utf-8')
            switch_dict[ip] = Switch(switch["system_name"], guid, ip, user, credentials)
    logging.debug(f"List of switches in the fabric: {switch_dict.keys()}")
    return switch_dict

class Switch:
    def __init__(self, name="", guid="guid", ip="", user="", credentials=""):
        self.name = name
        self.guid = guid
        self.ip = ip
        self.user = user
        self.credentials = credentials
        self.socket_thread = None

class Severity:
    INFO_ID = 551
    WARNING_ID = 553
    CRITICAL_ID = 554
    INFO_STR = "INFORMATIONAL"
    WARNING_STR = "WARNING"
    MAJOR_STR = "MAJOR"
    CRITICAL_STR = "CRITICAL"
    LEVEL_TO_EVENT_ID = {
        INFO_STR: INFO_ID,
        WARNING_STR: WARNING_ID,
        MAJOR_STR: CRITICAL_ID,
        CRITICAL_STR: CRITICAL_ID,
    }
    def __init__(self, level=INFO_STR):
        self.level = level
        self.event_id = self.LEVEL_TO_EVENT_ID[level]
    def update_level(self, level):
        event_id = self.LEVEL_TO_EVENT_ID[level]
        if event_id > self.event_id:
            self.level = level
            self.event_id = event_id

class ConfigParser:
    config_file = "../build/config/gnmi_events.conf"
    log_file="gnmi_events.log"
    httpd_config_file = "../build/config/gnmi_events_httpd_proxy.conf"
    throughput_file = "throughput.log"
    # config_file = "/config/gnmi_events.conf"
    # log_file="/log/gnmi_events.log"
    # httpd_config_file = "/config/gnmi_events_httpd_proxy.conf"
    # throughput_file = "/data/throughput.log"

    gnmi_events_config = configparser.ConfigParser()
    if not os.path.exists(config_file):
        logging.error(f"No config file {config_file} found!")
        quit()
    gnmi_events_config.read(config_file)
    log_level = gnmi_events_config.get("Log", "log_level")
    log_file_max_size = gnmi_events_config.getint("Log", "log_file_max_size")
    log_file_backup_count = gnmi_events_config.getint("Log", "log_file_backup_count")
    log_format = '%(asctime)-15s %(levelname)s %(message)s'
    logging.basicConfig(handlers=[RotatingFileHandler(log_file,
                                                      maxBytes=log_file_max_size,
                                                      backupCount=log_file_backup_count)],
                        level=logging.getLevelName(log_level),
                        format=log_format)
    logging.getLogger("requests").setLevel(logging.getLevelName(log_level))
    logging.getLogger("werkzeug").setLevel(logging.getLevelName(log_level))

    gnmi_port = gnmi_events_config.getint("GNMI", "gnmi_port", fallback=9339)
    if not gnmi_port:
        logging.error(f"Incorrect value for snmp_port")
        quit()

    ufm_switches_update_interval = gnmi_events_config.getint("UFM", "ufm_switches_update_interval", fallback=60)

    if not os.path.exists(httpd_config_file):
        logging.error(f"No config file {httpd_config_file} found!")
    port = 8750  # Default port
    try:
        with open(httpd_config_file, "r") as file:
            line = file.readline()
            if line and "=" in line:
                port = int(line.split("=")[-1].strip())
    except (ValueError, IOError) as e:
        logging.error(f"Failed to read port from {httpd_config_file}: {e}")