#
# Copyright © 2013-2024 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
#

import argparse
import asyncio
from http import HTTPStatus
import json
import sys
import time

import requests
import hashlib
from datetime import datetime, timedelta

from callback_server import Callback, CallbackServerThread
from ufm_web_service import create_logger

def get_hash(file_content):
    sha1 = hashlib.sha1()
    sha1.update(file_content.encode('utf-8'))
    return sha1.hexdigest()

DEFAULT_PASSWORD = "123456"
DEFAULT_USERNAME = "admin"
NOT_ALLOW="not allowed"
FROM_SOURCES=True

# rest api
GET = "GET"
POST = "POST"

# resources
HELP = "help"
VERSION = "version"
QUERY_REQUEST = "query"
DELETE = "delete"
CANCEL = "cancel"
QUERIES = "queries"
QUERYID = "queries/{}"
DATE = "date"

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

FAILED_TESTS_COUNT = 0

def remove_timestamp(response):
    if response:
        if isinstance(response, dict):
            del response["timestamp"]
            return response
        elif isinstance(response, list):
            return [{i: entry[i] for i in entry if i != "timestamp"} for entry in response]
        else:
            return response
    else:
        return response

def make_request(request_type, resource, payload=None, user=DEFAULT_USERNAME, password=DEFAULT_PASSWORD,
                 rest_version="", headers=None):
    if headers is None:
        headers = {}
    if payload is None:
        payload = {}
    if not FROM_SOURCES:
        request = f"https://{HOST_IP}/ufmRest{rest_version}/plugin/sysinfo/{resource}"
        response = None
        if request_type == POST:
            response = requests.post(request, verify=False, headers=headers, auth=(user, password), json=payload)
        elif request_type == GET:
            response = requests.get(request, verify=False, headers=headers, auth=(user, password))
        else:
            print(f"Request {request_type} is not supported")
    else:
        request = f"http://127.0.0.1:8999/{resource}"
        response = None
        if request_type == POST:
            response = requests.post(request, verify=False, headers=headers, json=payload)
        elif request_type == GET:
            response = requests.get(request, verify=False, headers=headers)
        else:
            print(f"Request {request_type} is not supported")
    return response, f"{request_type} /{resource}"


def check_code(request_str, code, expected_code, test_name="positive"):
    test_type = "code"
    if code == expected_code:
        on_check_success(request_str, test_type, test_name)
    else:
        on_check_fail(request_str, code, expected_code, test_type, test_name)


def check_property(request_str, response, property_name, expected_value, test_name="positive"):
    test_type = "response"
    if isinstance(response, dict) and expected_value in response[property_name]:
        on_check_success(request_str, test_type, test_name)
    else:
        on_check_fail(request_str, response, expected_value, test_type, test_name)


def check_length(request_str, response, expected_length, test_name="positive"):
    test_type = "response"
    if isinstance(response, dict) and len(response) == expected_length:
        on_check_success(request_str, test_type, test_name)
    else:
        on_check_fail(request_str, response, f"dictionary of size {expected_length}", test_type, test_name)


def check_commands(request_str, response, switch_index, expected_command_names, test_name="positive"):
    test_type = "response"
    if isinstance(response, dict) and switch_index < len(response):
        commands = list(response.values())[switch_index]
        command_names = list(commands.keys())
        if command_names == expected_command_names:
            on_check_success(request_str, test_type, test_name)
            return
    on_check_fail(request_str, response, f"dictionary of size {expected_command_names}", test_type, test_name)

# def check_equal(request_str, left_expr, right_expr, test_name="positive"):
#     test_type = "response"
#     if left_expr == right_expr:
#         on_check_success(request_str, test_type, test_name)
#     else:
#         on_check_fail(request_str, left_expr, right_expr, test_type, test_name)


def on_check_success(request_str, test_type, test_name):
    print(f"    - test name: {test_name} {test_type}, request: {request_str} -- PASS")


def on_check_fail(request_str, left_expr, right_expr, test_type, test_name):
    global FAILED_TESTS_COUNT # pylint: disable=global-statement
    FAILED_TESTS_COUNT += 1
    print(f"    - test name: {test_name} {test_type}, request: {request_str} -- FAIL (expected: {right_expr}, actual: {left_expr})")


def assert_equal(request, left_expr, right_expr, test_name="positive"):
    if isinstance(right_expr, int):
        test_type = "code"
    else:
        test_type = "response"

    if left_expr == right_expr:
        print(f"    - test name: {test_name} {test_type}, request: {request} -- PASS")
    elif isinstance(right_expr, dict) and right_expr["error"] and right_expr["error"] in left_expr["error"]:
        print(f"    - test name: {test_name} {test_type}, request: {request} -- PASS")
    elif str(right_expr) in str(left_expr):
        print(f"    - test name: {test_name} {test_type}, request: {request} -- PASS")
    else:
        global FAILED_TESTS_COUNT # pylint: disable=global-statement
        FAILED_TESTS_COUNT += 1
        print(f"    - test name: {test_name} {test_type}, request: {request} -- FAIL (expected: {right_expr}, actual: {left_expr})")


def get_response(response):
    if response is not None:
        try:
            json_response = response.json()
            return json_response
        except: # pylint: disable=bare-except
            return response.text
    else:
        return None


def get_code(response):
    if response is not None:
        return response.status_code
    else:
        return None

def help_and_version():
    print("help and version works")

    response, request_string = make_request(GET, HELP)
    check_code(request_string, get_code(response), HTTPStatus.OK)
    check_length(request_string, get_response(response), 8)

    response, request_string = make_request(GET, VERSION)
    check_code(request_string, get_code(response), HTTPStatus.OK)
    check_length(request_string, get_response(response), 1)

    test_name = NOT_ALLOW
    response, request_string = make_request(POST, HELP)
    check_code(request_string, get_code(response), HTTPStatus.METHOD_NOT_ALLOWED, test_name)
    
    response, request_string = make_request(POST, QUERIES)
    check_code(request_string, get_code(response), HTTPStatus.METHOD_NOT_ALLOWED, test_name)


def instant_comparison():
    print("Run comparison test")
    request = {}
    request['callback'] = Callback.URL

    test_name = NOT_ALLOW
    response, request_string = make_request(GET, QUERY_REQUEST, payload=request)
    check_code(request_string, get_code(response), HTTPStatus.METHOD_NOT_ALLOWED, test_name)

    test_name = "incorrect praser information"
    response, request_string = make_request(POST, QUERY_REQUEST, payload=request)
    check_code(request_string, get_code(response), HTTPStatus.BAD_REQUEST, test_name)
    check_property(request_string, get_response(response), "error", "Incorrect format, missing keys in request", test_name)

    request['commands'] = ["show power", "show inventory"]
    request['callback'] = f"notURL/{Callback.ROUTE}"

    test_name = "incorrect URL"
    response, request_string = make_request(POST, QUERY_REQUEST, payload=request)
    check_code(request_string, get_code(response), HTTPStatus.BAD_REQUEST, test_name)
    check_property(request_string, get_response(response), "error", "Incorrect callback url format", test_name)

    test_name = "unreachable switches"
    non_existing_ip = "1.2.3.4"
    request['callback'] = Callback.URL
    request['switches'] = [non_existing_ip]

    response, request_string = make_request(POST, QUERY_REQUEST, payload=request)
    time.sleep(5)
    data_from = Callback.get_recent_response()
    check_code(request_string, get_code(response), HTTPStatus.OK, test_name)
    check_property(request_string, data_from, non_existing_ip, "Switch does not respond to ping", test_name)

    test_name = "unrecognized switches"
    non_switch_ip = "127.0.0.1"
    request['callback'] = Callback.URL
    request['switches'] = [non_switch_ip]

    response, request_string = make_request(POST, QUERY_REQUEST, payload=request)
    time.sleep(5)
    data_from = Callback.get_recent_response()
    check_code(request_string, get_code(response), HTTPStatus.OK, test_name)
    check_property(request_string, data_from, non_switch_ip, "Switch does not located on the running ufm", test_name)

    switch_ip = "10.209.227.189"
    request['switches'] = [switch_ip]

    response, request_string = make_request(POST, QUERY_REQUEST, payload=request)
    time.sleep(5)
    data_from = Callback.get_recent_response()
    check_code(request_string, get_code(response), HTTPStatus.OK, test_name)
    check_commands(request_string, data_from, 0, request['commands'], test_name)


def get_server_datetime():
    response, request_string = make_request(GET, DATE)
    datetime_response = get_response(response)
    datetime_string = datetime_response["date"]
    return datetime.strptime(datetime_string, DATETIME_FORMAT)

def periodic_comparison():
    print("Periodic comparison")

    test_name = "incorrect request"
    request = {}
    request['callback'] = Callback.URL
    request['switches'] = ["10.209.227.189"]
    request['commands'] = ["show power","show inventory"]
    request["periodic_run"] = {}
    response, request_string = make_request(POST, QUERY_REQUEST, payload=request)
    check_code(request_string, get_code(response), HTTPStatus.BAD_REQUEST, test_name)
    check_property(request_string, get_response(response), "error", "Incorrect format, missing keys in request", test_name)

    test_name = "incorrect datetime format"
    request["periodic_run"] = {
        "startTime": "asd",
        "endTime": "xyz",
        "interval": 10
    }
    response, request_string = make_request(POST, QUERY_REQUEST, payload=request)
    check_code(request_string, get_code(response), HTTPStatus.BAD_REQUEST, test_name)
    check_property(request_string, get_response(response), "error", "Incorrect timestamp format: time data 'asd' does not match format", test_name)

    datetime_end = datetime_start = get_server_datetime() + timedelta(seconds=3)
    test_name = "too small interval"
    request = {
        "run": {
            "startTime": datetime_start.strftime(DATETIME_FORMAT),
            "endTime": datetime_end.strftime(DATETIME_FORMAT),
            "interval": 1
        }
    }
    response, request_string = make_request(POST, QUERY_REQUEST, payload=request)
    check_code(request_string, get_code(response), HTTPStatus.BAD_REQUEST, test_name)
    assert_equal(request_string, get_response(response), {'error': 'Minimal interval value is 5 minutes'},
                 test_name)

    test_name = "end time less than start time"
    request = {
        "run": {
            "startTime": datetime_start.strftime(DATETIME_FORMAT),
            "endTime": (datetime_end - timedelta(seconds=10)).strftime(DATETIME_FORMAT),
            "interval": 10
        }
    }
    response, request_string = make_request(POST, QUERY_REQUEST, payload=request)
    check_code(request_string, get_code(response), HTTPStatus.BAD_REQUEST, test_name)
    assert_equal(request_string, get_response(response), {'error': 'End time is less than current time'},
                 test_name)

    datetime_end = datetime_start = get_server_datetime() + timedelta(seconds=5)
    request = {
        "run": {
            "startTime": datetime_start.strftime(DATETIME_FORMAT),
            "endTime": datetime_end.strftime(DATETIME_FORMAT),
            "interval": 10
        }
    }
    response, request_string = make_request(POST, QUERY_REQUEST, payload=request)
    check_code(request_string, get_code(response), HTTPStatus.OK)
    assert_equal(request_string, get_response(response), {})

    if get_code(response) == HTTPStatus.OK:
        time.sleep(5)
        data_from = Callback.get_recent_response()
        check_data(request_string,data_from,request["commands"])

def check_data(requst_string,data,commands):
    test_name="Check Data"
    for switch in data:
        assert_equal(requst_string, len(switch),len(commands) , test_name+ " Amount")
        for command in switch:
            assert_equal(requst_string, commands,switch , test_name+" commands")


async def main():
    """ Main function"""
    logger = create_logger("/log/sysinfo_test.log")

    callback_thread = CallbackServerThread(logger)
    callback_thread.start()

    help_and_version()
    instant_comparison()
    periodic_comparison()

    await callback_thread.stop()

    if FAILED_TESTS_COUNT > 0:
        logger.error(f"\n{FAILED_TESTS_COUNT} tests failed")
        return 1
    else:
        return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Sysinfo plugin test')
    parser.add_argument('-ip', '--host', type=str, required=True, help='Host IP address where Sysinfo plugin is running')
    args = parser.parse_args()
    HOST_IP = args.host

    result = asyncio.run(main())
    sys.exit(result)
