import argparse
from datetime import datetime
import json
import os
import requests
import socket
import sys

# rest api
GET = "GET"
POST = "POST"

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATETIME_MS_FORMAT = DATETIME_FORMAT + ",%f"

FAILED_TESTS_COUNT = 0


def switch_request(request_type, resource, payload=None):
    if payload is None:
        payload = {}
    request = "https://{}:443/{}".format(HOST_IP, resource)
    response = None
    if request_type == POST:
        response = requests.post(request, verify=False, json=payload)
    elif request_type == GET:
        response = requests.get(request, verify=False)
    else:
        print("Request {} is not supported".format(request_type))
    return response, "{} /{}".format(request_type, resource)


def get_request(resource):
    request = "http://127.0.0.1:8000/{}".format(resource)
    try:
        response = requests.get(request, verify=False, headers={"X-Remote-User": "ufmsystem"})
        return response.status_code, response.json()
    except Exception as e:
        error = f"{request} failed with exception: {e}"
        return 500, {error}


def assert_equal(request, left_expr, right_expr, test_name="positive"):
    if type(right_expr) is int:
        test_type = "code"
    else:
        test_type = "response"
    if left_expr == right_expr:
        print(f"    - test: {test_name} {test_type}, request: {request} -- PASS")
    else:
        global FAILED_TESTS_COUNT
        FAILED_TESTS_COUNT += 1
        print(f"    - test: {test_name} {test_type}, request: {request} -- FAIL (expected: {right_expr}, actual: {left_expr})")


def assert_not_equal(request, left_expr, right_expr, test_name="positive"):
    if type(right_expr) is int:
        test_type = "code"
    else:
        test_type = "response"
    if left_expr != right_expr:
        print(f"    - test: {test_name} {test_type}, request: {request} -- PASS")
    else:
        global FAILED_TESTS_COUNT
        FAILED_TESTS_COUNT += 1
        print(f"    - test: {test_name} {test_type}, request: {request} -- FAIL (expected: {right_expr}, actual: {left_expr})")


def get_response(response):
    if response is not None:
        if response.status_code != 503:
            return response.json()
    else:
        return None


def get_code(response):
    if response is not None:
        return response.status_code
    else:
        return None


def switch_is_up():
    print("Check if switch is up")

    cmd = "show inventory"
    payload = {
        "cmd": cmd
    }
    
    response, request_string = switch_request(POST, "admin/launch?script=json", payload)
    assert_equal(request_string, get_code(response), 200, cmd)
    assert_not_equal(request_string, response.json(), {}, cmd)


def add_trap_host_listener():
    print("Add trap host listener")

    local_hostname = socket.gethostname()
    ip = socket.gethostbyname(local_hostname)
    port = "162"
    version = "v2"
    payload = {
        "params": {
            "ip": ip,
            "port": port,
            "version": version
        }
    }
    response, request_string = switch_request(POST, "setTrapRecipient", payload)
    assert_equal(request_string, get_code(response), 200, f"{ip} {port} {version}")

def send_test_trap():
    print("Send test trap")

    payload = {
        "params": {}
    }
    response, request_string = switch_request(POST, "sendTrap", payload)
    assert_equal(request_string, get_code(response), 200, "testTrap")

def trap_in_log():
    print("Check trap in log")

    # TODO: get log name dynamically
    log_path = "/auto/mtrswgwork/atolikin/ufm_sdk_3.0/plugins/snmp_receiver_plugin/snmp_server/snmptrap.log"
    gold_result = "Trap has been received successfully"
    result = ""
    with open(log_path, "r") as log:
        for line in log.readlines()[::-1]:
            if "test trap" in line:
                date = line.split()[0]
                time = line.split()[1]
                trap_datetime = datetime.strptime(f"{date} {time}", DATETIME_MS_FORMAT)
                if trap_datetime > START_TIME:
                    result = gold_result
                else:
                    result = f"Trap hasn't been received! Last trap time: {trap_datetime}, \
                               test start time: {START_TIME.strftime(DATETIME_MS_FORMAT)}"
                break
    assert_equal("compare timings", result, gold_result, "new trap in log")

def trap_in_ufm_events():
    print("Check trap event in UFM events")

    status_code, json = get_request("app/events")
    gold_result = "Event has been sent successfully"
    result = ""
    for event in json[::-1]:
        if "test trap" in event["description"]:
            event_datetime = datetime.strptime(event["timestamp"], DATETIME_FORMAT)
            if event_datetime > START_TIME:
                result = gold_result
            else:
                result = f"Event hasn't been received! Last event time: {event_datetime}, \
                           test start time: {START_TIME.strftime(DATETIME_MS_FORMAT)}"
            break
    assert_equal("compare timings", result, gold_result, "new trap in log")

def main():
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    switch_is_up()
    add_trap_host_listener()
    send_test_trap()
    trap_in_log()
    trap_in_ufm_events()

    if FAILED_TESTS_COUNT > 0:
        print("\n{} tests failed".format(FAILED_TESTS_COUNT))
        return 1
    else:
        return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='SNMP plugin test')
    parser.add_argument('-ip', '--host', type=str, required=True, help='Simulated switch IP')
    args = parser.parse_args()
    HOST_IP = args.host
    START_TIME = datetime.now()

    sys.exit(main())
