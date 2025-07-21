#!/usr/bin/python

import json
import requests
import logging
import subprocess
import argparse
from http import HTTPStatus
from urllib.parse import urljoin

HTTP_ERROR = HTTPStatus.INTERNAL_SERVER_ERROR
HOST = "127.0.0.1:8000"
PROTOCOL = "http"
EMPTY_IP = "0.0.0.0"
UFM_IP = "localhost"

def succeded(status_code):
    return status_code in [HTTPStatus.OK, HTTPStatus.ACCEPTED]

def get_request(resource):
    request = urljoin(f"{PROTOCOL}://{HOST}", resource)
    logging.info("GET %s", request)
    try:
        session = requests.Session()
        session.headers = {"X-Remote-User": "ufmsystem"}
        response = session.get(request, verify=False, timeout=10)
        return response.status_code, response.json()
    except Exception as e:
        error = f"{request} failed with exception: {e}"
        return HTTP_ERROR, {"error": error}
    
def put_request(resource, data):
    request = urljoin(f"{PROTOCOL}://{HOST}", resource)
    logging.info("PUT %s", request)
    try:
        session = requests.Session()
        session.headers = {"X-Remote-User": "ufmsystem"}
        response = session.put(request, data=data, verify=False, timeout=10)
        return response.status_code
    except Exception as e:
        logging.error(f"{request} failed with exception: {e}")
        return HTTP_ERROR

def get_ufm_switches():
    resource = "/resources/systems?type=switch"
    status_code, json = get_request(resource)
    if not succeded(status_code):
        logging.error("Failed to get list of UFM switches")
        return {}
    return json

def set_auto_ip(guid):
    resource = f"/resources/systems/{guid}"
    data = {"is_manual_ip": False}
    status_code = put_request(resource, json.dumps(data))
    if not succeded(status_code):
        logging.error("Failed to set auto ip for %s", guid)
        return HTTP_ERROR
    return status_code

def update_system_ip(guid, ip):
    resource = f"/resources/systems/{guid}"
    data = {"ip": ip}
    status_code = put_request(resource, json.dumps(data))
    if not succeded(status_code):
        logging.error("Failed to update system ip for %s", guid)
        return HTTP_ERROR
    return status_code
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Simulate switches with gNMI simulators')
    parser.add_argument('-n', '--num-switches', type=int, default=1,
                      help='Number of switches to simulate (default: 1)')
    args = parser.parse_args()

    switches = get_ufm_switches()
    print(f"All switches are: {len(switches)}")
    i=1
    for sw in switches[:args.num_switches]:
        cmd="""(docker inspect gnmi-simulator-%s|grep IPAddress|tail -n1|awk '{print $NF}'|cut -d'"' -f2)"""%i
        ip = subprocess.check_output(cmd, shell=True)
        ip=ip.decode('utf-8').rstrip()
        logging.info(f"IP is: {ip}")
        status_code = set_auto_ip(sw["guid"])
        status_code = update_system_ip(sw["guid"], ip)
        i=i+1
