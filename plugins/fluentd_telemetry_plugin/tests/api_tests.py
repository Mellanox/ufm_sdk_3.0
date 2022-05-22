#!/usr/bin/python3

import json
import requests
import time

HOST_IP = "127.0.0.1"

CONF_URL = "conf"
START_URL = "start"
STOP_URL = "stop"
STATUS_URL = "status"

# authentication types
BASIC = "basic"
CLIENT = "client_cert"
TOKEN = "token"

user = "admin"
passowrd = "123456"


def get_rest_version(auth_type):
    if auth_type == BASIC:
        return ""
    elif auth_type == CLIENT:
        return "V2"
    elif auth_type == TOKEN:
        return "V3"


def make_request(url, auth=(user, passowrd), auth_type=BASIC,cert=None, method="GET", headers=None,payload=None):
    request_string = "https://{}/ufmRest{}/plugin/tfs/{}".format(HOST_IP, get_rest_version(auth_type), url)
    verify = True if cert else False
    response = None
    if method == "GET":
        response = requests.get(request_string, verify=verify, headers=headers, auth=auth, cert=cert)
    elif method == "POST":
        response = requests.post(request_string, verify=verify, headers=headers, auth=auth, cert=cert, json=payload)

    if response is not None:
        try:
            formatted_str = json.dumps(response.json(), indent=2)

        except json.JSONDecodeError:
            formatted_str = response.text
        print("ResponseCode:\n {}\nResponse: \n{}".format(response.status_code, formatted_str))

    return response


def get_current_configurations():
    return make_request(CONF_URL)


def set_streaming_configurations():
    payload = {
        "ufm-telemetry-endpoint": {
            "host": "swx-proton03",
            "url": "csv/minimal",
            "port": 9001
        },
        "fluentd-endpoint": {
            "host": "10.209.36.68",
            "port": "24226"
        },
        "streaming": {
            "interval": 10,
            "enabled": True,
            "bulk_streaming": True
        },
        "meta-fields":{
            "alias_node_description": "node_name",
            "alias_node_guid": "AID",
            "add_type":"csv"
        }
    }
    return make_request(CONF_URL, payload=payload, method="POST")

if __name__ == '__main__':
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    print("Getting the current streaming configurations::")
    get_current_configurations()
    print("########")
    print("Set the configurations & start the streaming::")
    set_streaming_configurations()
    print("########")
