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

import argparse
import csv
from datetime import datetime
import requests
import sys

# rest api
GET = "GET"
POST = "POST"

SWITCH_LIST = "switch_list"
UNREGISTER = "unregister"
REGISTER = "register"
TRAP_LIST = "trap_list"

# DEFAULT_PASSWORD="123456"
DEFAULT_PASSWORD="admin"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATETIME_MS_FORMAT = DATETIME_FORMAT + ",%f"

FAILED_TESTS_COUNT = 0
SWITCHES = []

def make_request(request_type, resource, payload=None, user="admin", password=DEFAULT_PASSWORD,
                 rest_version="", headers=None, api="plugin/snmp"):
    if headers is None:
        headers = {}
    if payload is None:
        payload = {}
    request = "https://{}/ufmRest{}/{}/{}".format(HOST_IP, rest_version, api, resource)
    response = None
    if request_type == POST:
        response = requests.post(request, verify=False, headers=headers, auth=(user, password), json=payload)
    elif request_type == GET:
        response = requests.get(request, verify=False, headers=headers, auth=(user, password))
    else:
        print("Request {} is not supported".format(request_type))
    return response, "{} /{}".format(request_type, resource)

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

def unregister_all():
    print("Unregister all switches and check switch list is empty")
    test = "get registered switches"
    response, request_string = make_request(GET, SWITCH_LIST)
    assert_equal(request_string, get_code(response), 200, test)
    global SWITCHES
    SWITCHES = (get_response(response))

    test = "unregister all"
    response, request_string = make_request(POST, UNREGISTER)
    assert_equal(request_string, get_code(response), 200, test)

    test = "empty switch list"
    response, request_string = make_request(GET, SWITCH_LIST)
    assert_equal(request_string, get_code(response), 200, test)
    assert_equal(request_string, get_response(response), [], test)

def register_switch():
    print("Register 1 switch")
    global SWITCHES
    test = "managed switches in the fabric"
    assert_equal(SWITCH_LIST, len(SWITCHES), 1, test)
    try:
        switch = SWITCHES[0]
    except:
        return
    register_request = {
        "switches": [switch]
    }
    test = "register switch"
    response, request_string = make_request(POST, REGISTER, payload=register_request)
    assert_equal(request_string, get_code(response), 200, test)

    test = "switch registered"
    response, request_string = make_request(GET, SWITCH_LIST)
    assert_equal(request_string, get_code(response), 200, test)
    assert_equal(request_string, get_response(response), [switch], test)

def get_trap_list():
    print("Get trap list")
    with open("../snmp_server/traps_policy.csv", "r") as traps_info_file:
        gold = []
        csvreader = csv.reader(traps_info_file)
        for row in csvreader:
            gold.append(row)

    test = "trap list"
    response, request_string = make_request(GET, TRAP_LIST)
    assert_equal(request_string, get_code(response), 200, test)
    assert_equal(request_string, get_response(response), gold, test)

def register_all():
    print("Register all switches to bring initial state")
    test = "register all"
    response, request_string = make_request(POST, REGISTER)
    assert_equal(request_string, get_code(response), 200, test)

    test = "all switches registered"
    response, request_string = make_request(GET, SWITCH_LIST)
    assert_equal(request_string, get_code(response), 200, test)
    global SWTICHES
    assert_equal(request_string, get_response(response), SWITCHES, test)

def send_test_trap():
    print("Send test trap")
    send_trap_request =  {
        "action": "run_cli",
        "identifier": "ip",
        "params": {
            "commandline": ["snmp-server notify send-test"]
        },
        "description": "send test trap",
        "object_ids": SWITCHES,
        "object_type": "System"
    }

    response, request_string = make_request(POST, "actions", send_trap_request, api="")
    assert_equal(request_string, get_code(response), 202, "send test trap")

def trap_in_log():
    print("Check trap in log")
    # TODO: get log name dynamically
    log_path = "/opt/ufm/snmptrap.log"
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
    response, request_string = make_request(GET, "app/events", api="")
    assert_equal(request_string, get_code(response), 200, "get ufm events")
    events = get_response(response)
    gold_result = "Event has been sent successfully"
    result = ""
    for event in events[::-1]:
        if "simulated test trap" in event["description"]:
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

    unregister_all()
    register_switch()
    get_trap_list()
    register_all()
    send_test_trap()
    # trap_in_log()
    trap_in_ufm_events()

    if FAILED_TESTS_COUNT > 0:
        print("\n{} tests failed".format(FAILED_TESTS_COUNT))
        return 1
    else:
        return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='SNMP plugin test')
    parser.add_argument('-ip', '--host', type=str, required=True, help='Host IP address where SNMP plugin is running')
    args = parser.parse_args()
    HOST_IP = args.host
    START_TIME = datetime.now()

    sys.exit(main())
