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
import configparser
from http import HTTPStatus
import logging
from logging.handlers import RotatingFileHandler
import requests
import os
import socket
import time

HTTP_ERROR = HTTPStatus.INTERNAL_SERVER_ERROR
HOST = "127.0.0.1:8000"
PROTOCOL = "http"
SESSION = requests.Session()
SESSION.headers = {"X-Remote-User": "ufmsystem"}
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
        response = SESSION.get(request, verify=False)
        return response.status_code, response.json()
    except Exception as e:
        error = f"{request} failed with exception: {e}"
        return HTTP_ERROR, {error}

def post_request(resource, json=None, return_headers=False):
    request = PROTOCOL + '://' + HOST + resource
    try:
        description = json['description']
    except Exception as e:
        description = ""
    logging.info(f"POST {request} {description}")
    try:
        response = SESSION.post(request, verify=False, json=json)
        if return_headers:
            return response.status_code, response.headers
        return response.status_code, response.text
    except Exception as e:
        error = f"{request} failed with exception: {e}"
        return HTTP_ERROR, error

def get_json_api_payload(cli, description, switches):
    return {
        "action": "run_cli",
        "identifier": "ip",
        "params": {
            "commandline": [cli]
        },
        "description": description,
        "object_ids": switches,
        "object_type": "System"
    }

def post_provisioning_api(cli, description, switches, return_headers=False):
    payload = get_json_api_payload(cli, description, switches)
    status_code, text = post_request("/actions", json=payload, return_headers=return_headers)
    return status_code, text

def _extract_job_id(headers):
        # extract job ID from location header
        location = headers.get("Location")
        if not location:
            return None
        job_id = location.split('/')[-1]
        return job_id

def get_provisioning_output(cli, description, switches):
    status_code, headers = post_provisioning_api(cli, description, switches, return_headers=True)
    if not succeded(status_code):
        return status_code, f"Failed to post json api '{cli}' to switches {switches}"
    job_id = _extract_job_id(headers)
    for _ in range(PROVISIONING_TIMEOUT):
        status_code, json = get_request(f"/jobs/{job_id}", debug=True)
        if not succeded(status_code):
            return status_code, f"Failed to get job {job_id} output"
        try:
            status = json["Status"]
            if status in [COMPLETED, COMPLETED_WITH_ERRORS]:
                break
        except KeyError as ke:
            return HTTPStatus.BAD_REQUEST, f"No key {ke} found"
        time.sleep(3)
    else:
        return HTTPStatus.INTERNAL_SERVER_ERROR, f"Failed to complete the job {job_id} in {PROVISIONING_TIMEOUT} seconds"

    result = {}
    status_code, jobs = get_request(f"/jobs?parent_id={job_id}", debug=True)
    if not succeded(status_code):
        return status_code, f"Failed to get childs of {job_id}"
    try:
        for job in jobs:
            guid = job["RelatedObjects"][0]
            status = job["Status"]
            summary = job["Summary"]
            result[guid] = (status, summary)
    except KeyError as ke:
        return HTTPStatus.BAD_REQUEST, f"get_provisioning_output: No key {ke} found"
    return HTTPStatus.OK, result

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

def init_engine_ids(switch_dict, guid_to_ip):
    if ConfigParser.snmp_version == 3:
        cli = "show snmp engineID"
        status_code, guid_to_response = get_provisioning_output(cli, "Requesting engine IDs", list(switch_dict.keys()))
        if not succeded(status_code):
            logging.error(f"Failed to get engine IDs, status_code: {status_code}, error: {guid_to_response}")
            return
        skip_lines = ["", cli, "Events for which traps will be sent:"]
        for guid, (status, engine_id_raw) in guid_to_response.items():
            # e.g.: "show snmp engineID\n\nLocal SNMP engineID: 0x80004f4db1aadcadbc89affa118db\n"
            if status == COMPLETED_WITH_ERRORS:
                logging.error(f"Failed to get engineID for switch {guid}: {engine_id_raw}")
                continue
            engine_id_strs = engine_id_raw.split("\n")
            engine_id_str = list(set(engine_id_strs) - set(skip_lines))
            if len(engine_id_str) != 1:
                logging.error(f"Failed to parse engine ID string {engine_id_raw}")
                continue
            for word in engine_id_str[0].split():
                if word.startswith("0x"):
                    try:
                        switch_obj = switch_dict[guid_to_ip[guid]]
                        switch_obj.engine_id = word[2:]
                    except KeyError as ke:
                        logging.error(f"No key {ke} found in {word}")

def get_ufm_switches(existing_switches=None):
    resource = "/resources/systems?type=switch"
    status_code, json = get_request(resource)
    if not succeded(status_code):
        logging.error(f"Failed to get list of UFM switches")
        return {}
    switch_dict = {}
    guid_to_ip = {}
    for switch in json:
        ip = switch["ip"]
        if not ip == EMPTY_IP:
            switch_dict[ip] = Switch(switch["system_name"], switch["guid"])
            guid_to_ip[switch["guid"]] = ip
    if existing_switches:
        if set(switch_dict.keys()) != set(existing_switches.keys()):
            init_engine_ids(switch_dict, guid_to_ip)
        else:
            return {}
    else:
        init_engine_ids(switch_dict, guid_to_ip)
    logging.debug(f"List of switches in the fabric: {switch_dict.keys()}")
    return switch_dict

class Switch:
    def __init__(self, name="", guid="", engine_id="", event_to_count={}):
        self.name = name
        self.guid = guid
        self.engine_id = engine_id
        self.event_to_count = event_to_count

class Severity:
    INFO_ID = 551
    MINOR_ID = 552
    WARNING_ID = 553
    CRITICAL_ID = 554
    INFO_STR = "Info"
    MINOR_STR = "Minor"
    WARNING_STR = "Warning"
    CRITICAL_STR = "Critical"
    LEVEL_TO_EVENT_ID = {
        INFO_STR: INFO_ID,
        MINOR_STR: MINOR_ID,
        WARNING_STR: WARNING_ID,
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

class Trap:
    def __init__(self, oid="", details="", severity="Info"):
        self.oid = oid
        self.details = details
        self.severity = severity
        self.count = 1
    def __eq__(self, other):
        return self.oid == other.oid
    def __hash__(self):
        return hash(tuple(self.oid))
    def increment_count(self):
        self.count += 1

class ConfigParser:
    # config_file = "../build/config/snmp.conf"
    # log_file="snmptrap.log"
    # throughput_file = "throughput.log"
    # httpd_config_file = "../build/config/snmp_httpd_proxy.conf"
    # switches_file = "registered_switches.json"
    # traps_policy_file = "traps_policy.csv"
    config_file = "/config/snmp.conf"
    log_file="/log/snmptrap.log"
    throughput_file = "/data/throughput.log"
    httpd_config_file = "/config/snmp_httpd_proxy.conf"
    switches_file = "/data/registered_switches.json"
    traps_policy_file = "/data/traps_policy.csv"

    snmp_config = configparser.ConfigParser()
    if not os.path.exists(config_file):
        logging.error(f"No config file {config_file} found!")
        quit()
    snmp_config.read(config_file)
    log_level = snmp_config.get("Log", "log_level")
    log_file_max_size = snmp_config.getint("Log", "log_file_max_size")
    log_file_backup_count = snmp_config.getint("Log", "log_file_backup_count")
    log_format = '%(asctime)-15s %(levelname)s %(message)s'
    logging.basicConfig(handlers=[RotatingFileHandler(log_file,
                                                      maxBytes=log_file_max_size,
                                                      backupCount=log_file_backup_count)],
                        level=logging.getLevelName(log_level),
                        format=log_format)
    logging.getLogger("requests").setLevel(logging.getLevelName(log_level))
    logging.getLogger("werkzeug").setLevel(logging.getLevelName(log_level))

    snmp_port = snmp_config.getint("SNMP", "snmp_port", fallback=162)
    if not snmp_port:
        logging.error(f"Incorrect value for snmp_port")
        quit()
    snmp_community = snmp_config.get("SNMP", "snmp_community", fallback="public")
    if not snmp_community:
        logging.error(f"Incorrect value for snmp_community")
        quit()
    multiple_events = snmp_config.getboolean("SNMP", "multiple_events", fallback=False)
    snmp_version = snmp_config.getint("SNMP", "snmp_version", fallback=3)
    if snmp_version not in [1, 3]:
        logging.error(f"Incorrect value for snmp_version, should be '1' or '3'")
        quit()
    snmp_mode = snmp_config.get("SNMP", "snmp_mode", fallback="auto")
    if snmp_mode not in ["auto", "manual"]:
        logging.error(f"Incorrect value for snmp_mode, should be 'auto' or 'manual'")
        quit()
    snmp_user = snmp_config.get("SNMP", "snmp_user", fallback="")
    if not snmp_user:
        logging.error(f"Incorrect value for snmp_user")
        quit()
    snmp_password = snmp_config.get("SNMP", "snmp_password", fallback="")
    if not snmp_password:
        logging.error(f"Incorrect value for snmp_password")
        quit()
    snmp_priv = snmp_config.get("SNMP", "snmp_priv", fallback="")
    if not snmp_priv:
        logging.error(f"Incorrect value for snmp_priv")
        quit()
    snmp_additional_traps_str = snmp_config.get("SNMP", "snmp_additional_traps", fallback="")
    snmp_additional_traps = snmp_additional_traps_str.split(',')

    ufm_switches_update_interval = snmp_config.getint("UFM", "ufm_switches_update_interval", fallback=60)

    if not os.path.exists(httpd_config_file):
        logging.error(f"No config file {httpd_config_file} found!")
    port=8780
    with open(httpd_config_file, "r") as file:
        line = file.readline()
        port = line.split("=")[-1]