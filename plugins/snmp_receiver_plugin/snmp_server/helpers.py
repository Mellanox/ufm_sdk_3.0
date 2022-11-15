import requests
import socket
import logging

HOST = "127.0.0.1:8000"
PROTOCOL = "http"
HEADERS = {"X-Remote-User": "ufmsystem"}
EMPTY_IP = "0.0.0.0"

def get_request(resource):
    request = PROTOCOL + '://' + HOST + resource
    logging.info(f"GET {request}")
    try:
        response = requests.get(request, verify=False, headers=HEADERS)
    except Exception as e:
        logging.error(f"{request} failed with exception: {e}")
    return response

def post_request(resource, json=None):
    request = PROTOCOL + '://' + HOST + resource
    logging.info(f"POST {request}")
    try:
        response = requests.post(request, verify=False, headers=HEADERS, json=json)
    except Exception as e:
        logging.error(f"{request} failed with exception: {e}")
    return response

def get_ufm_switches():
    resource = "/resources/systems?type=switch"
    response = get_request(resource)
    switch_ips = set()
    for switch in response.json():
        ip = switch["ip"]
        if not ip == EMPTY_IP:
            switch_ips.add(switch["ip"])
    logging.info(f"List of switches to register plugin on: {switch_ips}")
    return switch_ips

def register_switches(switches):
    resource = "/actions"
    local_hostname = socket.gethostname()
    local_ip = socket.gethostbyname(local_hostname)
    payload = {
        "action": "run_cli",
        "identifier": "ip",
        "params": {
            # TODO: the ip to register should be configurable
            # TODO: need to implement unregistration mechanism
            "commandline": [f"snmp-server host {local_ip} traps"]
        },
        "description": "register plugin as SNMP traps receiver",
        "object_ids": list(switches),
        "object_type": "System"
    }
    response = post_request(resource, json=payload)
    logging.info(f"Registration status code: {response.status_code},\nresponse: {response.text}")

def send_external_event(description):
    resource = "/app/events/external_event"
    # TODO: support severity
    payload = {"event_id": 551, "description": description}
    response = post_request(resource, json=payload)
    logging.info(f"Post external event status code: {response.status_code},\nresponse: {response.text}")