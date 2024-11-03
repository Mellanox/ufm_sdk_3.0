import argparse
from http import HTTPStatus
import json
import subprocess
import sys
import time

import requests
import os
import hashlib
from datetime import datetime, timedelta
import socket

from background_server import LOG_LOCATION,start_server,kill_server

def get_hash(file_content):
    sha1 = hashlib.sha1()
    sha1.update(file_content.encode('utf-8'))
    return sha1.hexdigest()

HOSTNAME = socket.gethostname()
IPAddr = socket.gethostbyname(HOSTNAME)
RECIVER_SERVER_LOCATION = f"http://{IPAddr}:8995/dummy"

DEFAULT_PASSWORD = "123456"
DEFAULT_USERNAME = "admin"
NOT_ALLOW="not allowed"
FROM_SOURCES=True

# rest api
GET = "GET"
POST = "POST"

# resources
HELP = 'help'
VERSION = "version"
QUERY_REQUEST = "query"
DELETE = "delete"
CANCEL = "cancel"
QUERIES = "queries"
QUERYID = "queries/{}"
DATE = "date"

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

FAILED_TESTS_COUNT = 0

def read_json_file() -> json:
    file_name = LOG_LOCATION
    with open(file_name, "r", encoding="utf-8") as file:
        # unhandled exception in case some of the files was changed manually
        try:
            data = json.load(file)
        except json.JSONDecodeError:
            return {}
    return data

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
        request = "http://127.0.0.1:8999/{}".format(resource)
        response = None
        if request_type == POST:
            response = requests.post(request, verify=False, headers=headers, json=payload)
        elif request_type == GET:
            response = requests.get(request, verify=False, headers=headers)
        else:
            print(f"Request {request_type} is not supported")
    return response, f"{request_type} /{resource}"


def assert_equal(request, left_expr, right_expr, test_name="positive"):
    if isinstance(right_expr, int):
        test_type = "code"
    else:
        test_type = "response"

    if left_expr == right_expr:
        print(f"    - test name: {test_name} {test_type}, request: {request} -- PASS")
    elif str(right_expr) in str(left_expr):
        print(f"    - test name: {test_name} {test_type}, request: {request} -- PASS")
    else:
        global FAILED_TESTS_COUNT
        FAILED_TESTS_COUNT += 1
        print(f"    - test name: {test_name} {test_type}, request: {request} -- FAIL (expected: {right_expr}, actual: {left_expr})")


def get_response(response):
    if response is not None:
        #if response.status_code == HTTPStatus.OK:
            json_response = response.json()
            return json_response
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
    assert_equal(request_string, get_code(response), HTTPStatus.OK)
    assert_equal(request_string, len(get_response(response)), 8)

    response, request_string = make_request(GET, VERSION)
    assert_equal(request_string, get_code(response), HTTPStatus.OK)
    assert_equal(request_string, len(get_response(response)), 1)

    test_name = NOT_ALLOW
    response, request_string = make_request(POST, HELP)
    assert_equal(request_string, get_code(response), HTTPStatus.METHOD_NOT_ALLOWED, test_name)
    
    response, request_string = make_request(POST, QUERIES)
    assert_equal(request_string, get_code(response), HTTPStatus.METHOD_NOT_ALLOWED, test_name)



def instant_comparison():
    print("Run comparion test")
    request = {}
    request['callback']=RECIVER_SERVER_LOCATION

    test_name = NOT_ALLOW
    response, request_string = make_request(GET, QUERY_REQUEST, payload=request)
    assert_equal(request_string, get_code(response), HTTPStatus.METHOD_NOT_ALLOWED, test_name)

    test_name = "incorrect praser information"
    response, request_string = make_request(POST, QUERY_REQUEST, payload=request)
    assert_equal(request_string, get_code(response), HTTPStatus.BAD_REQUEST, test_name)
    assert_equal(request_string, get_response(response),
                 {'error': "Incorrect format, missing keys in request: {'commands'}"}, test_name)
    
    request['commands']=["show power","show inventory"]
    request['callback']="notURL/dummy"

    test_name = "incorrect URL"
    response, request_string = make_request(POST, QUERY_REQUEST, payload=request)
    assert_equal(request_string, get_code(response), HTTPStatus.BAD_REQUEST, test_name)
    assert_equal(request_string, get_response(response), {'error': 'the callback url is not right:'}, test_name)
    

    test_name = "unreachable switches"
    request['callback']=RECIVER_SERVER_LOCATION
    request['switches']=["0.0.0.0"]

    response, request_string = make_request(POST, QUERY_REQUEST, payload=request)
    time.sleep(5)
    data_from=read_json_file()
    assert_equal(request_string, get_code(response), HTTPStatus.OK, test_name)
    assert_equal(request_string, data_from[0],{"0.0.0.0":"Switch does not respond to ping"}
                 , test_name)
    
    request['switches']=["10.209.27.19"]

    response, request_string = make_request(POST, QUERY_REQUEST, payload=request)
    time.sleep(5)
    data_from=read_json_file()
    assert_equal(request_string, get_code(response), HTTPStatus.OK, test_name)
    assert_equal(request_string, len(data_from[0]),2 , test_name)


def get_server_datetime():
    response, request_string = make_request(GET, DATE)
    datetime_response = get_response(response)
    datetime_string = datetime_response["date"]
    return datetime.strptime(datetime_string, DATETIME_FORMAT)

def periodic_comparison():
    print("Periodic comparison")

    test_name = "incorrect request"
    request = {}
    request['callback']=RECIVER_SERVER_LOCATION
    request['switches']=["10.209.27.19"]
    request['commands']=["show power","show inventory"]
    request["periodic_run"]=""
    response, request_string = make_request(POST, QUERY_REQUEST, payload=request)
    assert_equal(request_string, get_code(response), HTTPStatus.BAD_REQUEST, test_name)
    assert_equal(request_string, get_response(response),
                 {'error': "Incorrect format, extra keys in request: {'asd'}"}, test_name)

    test_name = "incorrect datetime format"
    request = {
        "periodic_run": {
            "startTime": "asd",
            "endTime": "xyz",
            "interval": 10
        }
    }
    response, request_string = make_request(POST, QUERY_REQUEST, payload=request)
    assert_equal(request_string, get_code(response), HTTPStatus.BAD_REQUEST, test_name)
    assert_equal(request_string, get_response(response),
                 {'error': "Incorrect timestamp format: time data '{}' does not match format '{}'"
                 .format(request["periodic_run"]["startTime"], DATETIME_FORMAT)},
                 test_name)

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
    assert_equal(request_string, get_code(response), HTTPStatus.BAD_REQUEST, test_name)
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
    assert_equal(request_string, get_code(response), HTTPStatus.BAD_REQUEST, test_name)
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
    assert_equal(request_string, get_code(response), HTTPStatus.OK)
    assert_equal(request_string, get_response(response), {})

    if get_code(response) == HTTPStatus.OK:
        time.sleep(5)
        data_from=read_json_file()
        check_data(request_string,data_from,request["commands"])

def check_data(requst_string,data,commands):
    test_name="Check Data"
    for switch in data:
        assert_equal(requst_string, len(switch),len(commands) , test_name+ " Amount")
        for command in switch:
            assert_equal(requst_string, commands,switch , test_name+" commands")


def main():
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    server=start_server()

    help_and_version()
    instant_comparison()
    periodic_comparison()

    kill_server(server)

    if FAILED_TESTS_COUNT > 0:
        print("\n{} tests failed".format(FAILED_TESTS_COUNT))
        return 1
    else:
        return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Sysinfo plugin test')
    parser.add_argument('-ip', '--host', type=str, required=True, help='Host IP address where Sysinfo plugin is running')
    args = parser.parse_args()
    HOST_IP = args.host

    sys.exit(main())
