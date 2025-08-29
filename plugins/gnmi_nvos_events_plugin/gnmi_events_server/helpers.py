#
# Copyright © 2013-2025 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
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
# @date:   March, 2025
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

def get_request(resource):
    request = PROTOCOL + '://' + HOST + resource
    logging.info("GET %s", request)
    try:
        session = requests.Session()
        session.headers = {"X-Remote-User": "ufmsystem"}
        response = session.get(request, verify=False, timeout=10)
        return response.status_code, response.json()
    except Exception as e:
        error = f"{request} failed with exception: {e}"
        return HTTP_ERROR, {"error": error}

async def async_post(session, resource, json=None):
    request = PROTOCOL + '://' + HOST + resource
    logging.info("POST %s", request)
    try:
        async with session.post(request, json=json, timeout=10) as resp:
            text = await resp.text()
            return resp.status, text
    except Exception as e:
        error = f"{request} failed with exception: {e}"
        return HTTP_ERROR, {"error": error}

def generate_key_pair():
    new_key = RSA.generate(1024)
    public_key = new_key.publickey().export_key()
    public_key = quote(public_key, safe='')
    private_key = new_key.export_key()
    priv_key = RSA.import_key(private_key)
    cipher = PKCS1_OAEP.new(priv_key)
    return public_key, cipher

def get_credentials(guid=None):
    guid = guid if guid else "default"
    resource = f"/resources/sites/{guid}/credentials?credential_types=SSH_Switch&public_key={ConfigParser.public_key}"
    logging.info("Get %s credentials %s", guid, resource)
    status_code, response = get_request(resource)
    user = None
    credentials = None
    if not succeded(status_code):
        logging.info("Failed to get %s credentials. Global credentials will be used", guid)
        return user, credentials
    if not response:
        logging.info("Empty %s credentials, please update them via UFM Web UI. Global credentials will be used", guid)
        return user, credentials
    try:
        user = response[0]["user"]
        encrypted_credentials = response[0]["credentials"]
        credentials = ConfigParser.cipher.decrypt(base64.b64decode(encrypted_credentials)).decode('utf-8')
        logging.info("Decrypted %s credentials successfully", guid)
    except Exception as e:
        logging.error("Failed to decrypt %s credentials", guid)
        logging.debug("Exception: %s", e)
    return user, credentials

def get_ufm_switches(existing_switches=None):
    resource = "/resources/systems?type=switch"
    status_code, json = get_request(resource)
    if not succeded(status_code):
        logging.error("Failed to get list of UFM switches")
        return {}
    global_user, global_credentials = get_credentials()
    switch_dict = {}
    for switch in json:
        ip = switch["ip"]
        if not ip == EMPTY_IP:
            guid = switch["guid"]
            system_user, system_credentials = get_credentials(guid)
            user = system_user if system_user else global_user
            credentials = system_credentials if system_credentials else global_credentials
            existing_switch = existing_switches.get(ip) if existing_switches else None
            if existing_switch and existing_switch.user == user and existing_switch.credentials == credentials:
                # do not update the switch since it's already initialized
                switch_dict[ip] = existing_switch
            else:
                switch_dict[ip] = Switch(switch["system_name"], guid, ip, user, credentials)
    logging.info("List of switches in the fabric: %s", list(switch_dict.keys()))
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
    """
    Class for the configuration parser that reads the configuration file and sets the log level and the log file.
    """
    # config_file = "../build/config/gnmi_nvos_events.conf"
    # log_file="gnmi_nvos_events.log"
    # httpd_config_file = "../build/config/gnmi_nvos_events_httpd_proxy.conf"
    config_file = "/config/gnmi_nvos_events.conf"
    log_file="/log/gnmi_nvos_events.log"
    httpd_config_file = "/config/gnmi_nvos_events_httpd_proxy.conf"

    gnmi_events_config = configparser.ConfigParser()
    if not os.path.exists(config_file):
        logging.error("No config file %s found!", config_file)
        quit()
    gnmi_events_config.read(config_file)
    log_level = gnmi_events_config.get("Log", "log_level", fallback="INFO")
    log_file_max_size = gnmi_events_config.getint("Log", "log_file_max_size", fallback=10485760)
    log_file_backup_count = gnmi_events_config.getint("Log", "log_file_backup_count", fallback=5)
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
        logging.error("Incorrect value for snmp_port")
        quit()
    gnmi_reconnect_retries = gnmi_events_config.getint("GNMI", "gnmi_reconnect_retries", fallback=10)

    ufm_switches_update_interval = gnmi_events_config.getint("UFM", "ufm_switches_update_interval", fallback=360)
    ufm_send_events_interval = gnmi_events_config.getint("UFM", "ufm_send_events_interval", fallback=10)
    ufm_first_update_interval = gnmi_events_config.getint("UFM", "ufm_first_update_interval", fallback=180)

    public_key, cipher = generate_key_pair()

    if not os.path.exists(httpd_config_file):
        logging.error("No config file %s found!", httpd_config_file)
    port = 8750  # Default port
    try:
        with open(httpd_config_file, "r") as file:
            line = file.readline()
            if line and "=" in line:
                port = int(line.split("=")[-1].strip())
    except (ValueError, IOError) as e:
        logging.error("Failed to read port from %s: %s", httpd_config_file, e)