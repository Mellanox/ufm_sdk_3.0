import argparse
import json
import subprocess
import sys
import time

import requests
import os
import hashlib
from datetime import datetime, timedelta


def get_hash(file_content):
    sha1 = hashlib.sha1()
    sha1.update(file_content.encode('utf-8'))
    return sha1.hexdigest()

# DEFAULT_PASSWORD = "123456"
DEFAULT_PASSWORD = "admin"

# rest api
GET = "GET"
POST = "POST"

# resources
NDTS = "list"
DATE = "date"
UPLOAD = "upload"
COMPARE = "compare"
DELETE = "delete"
CANCEL = "cancel"
REPORTS = "reports"
REPORT_ID = "reports/{}"

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

FAILED_TESTS_COUNT = 0


def remove_section(response, section):
    if response:
        if isinstance(response, dict):
            del response["section"]
            return response
        elif isinstance(response, list):
            return [{i: entry[i] for i in entry if i != section} for entry in response]
        else:
            return response
    else:
        return response


def make_request(request_type, resource, payload=None, user="admin", password=DEFAULT_PASSWORD,
                 rest_version="", headers=None):
    if headers is None:
        headers = {}
    if payload is None:
        payload = {}
    request = "https://{}/ufmRest{}/plugin/ndt/{}".format(HOST_IP, rest_version, resource)
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
        print("    - test name: {} {}, request: {} -- PASS"
              .format(test_name, test_type, request))
    else:
        global FAILED_TESTS_COUNT
        FAILED_TESTS_COUNT += 1
        print("    - test name: {} {}, request: {} -- FAIL (expected: {}, actual: {})"
              .format(test_name, test_type, request, right_expr, left_expr))


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


def no_ndts():
    print("Empty NDTs folder test")

    response, request_string = make_request(GET, NDTS)
    assert_equal(request_string, get_code(response), 200)
    assert_equal(request_string, get_response(response), [])

    test_name = "not allowed"
    response, request_string = make_request(POST, NDTS)
    assert_equal(request_string, get_code(response), 405, test_name)
    assert_equal(request_string, get_response(response), {'error': 'Method is not allowed'}, test_name)


def upload_metadata(ndts_folder):
    print("Upload 2 NDTs test")
    ndts_list_response = []
    upload_request = []
    switch_to_host_type = "switch_to_host"
    switch_to_switch_type = "switch_to_switch"
    for ndt in os.listdir(ndts_folder):
        with open(os.path.join(ndts_folder, ndt), "r") as file:
            data = file.read().replace('\n', '\r\n')
            file_type = ""
            if switch_to_host_type in ndt:
                file_type = switch_to_host_type
            elif switch_to_switch_type in ndt:
                file_type = switch_to_switch_type
            file_status = "New"
            upload_request.append({"file_name": ndt,
                                   "file": data,
                                   "file_type": file_type,
                                   "sha-1": get_hash(data)})
            ndts_list_response.append({"file": ndt,
                                       "sha-1": get_hash(data),
                                       "file_type": file_type,
                                      'file_status': file_status})

    test_name = "not allowed"
    response, request_string = make_request(GET, UPLOAD, payload=upload_request)
    assert_equal(request_string, get_code(response), 405, test_name)
    assert_equal(request_string, get_response(response), {'error': 'Method is not allowed'}, test_name)

    possible_file_types = ["switch_to_switch", "switch_to_host"]
    test_name = "incorrect file type"
    good_file_type = upload_request[0]["file_type"]
    upload_request[0]["file_type"] = "asd"
    response, request_string = make_request(POST, UPLOAD, payload=upload_request)
    assert_equal(request_string, get_code(response), 400, test_name)
    assert_equal(request_string, get_response(response),
                 {'error': ["Incorrect file type. Possible file types: {}."
                 .format(",".join(possible_file_types))]}, test_name)
    upload_request[0]["file_type"] = good_file_type

    good_file_name = upload_request[0]["file_name"]
    upload_request[0]["file_name"] = ""
    test_name = "empty file name"
    response, request_string = make_request(POST, UPLOAD, payload=upload_request)
    assert_equal(request_string, get_code(response), 400, test_name)
    assert_equal(request_string, get_response(response), {'error': ['File name is empty']}, test_name)
    upload_request[0]["file_name"] = good_file_name

    test_name = "wrong sha-1"
    good_sha = upload_request[0]["sha-1"]
    upload_request[0]["sha-1"] = "xyz"
    response, request_string = make_request(POST, UPLOAD, payload=upload_request)
    assert_equal(request_string, get_code(response), 400, test_name)
    assert_equal(request_string, get_response(response),
                 {"error": ["Provided sha-1 {} for {} is different from actual one {}"
                 .format("xyz", good_file_name, good_sha)]}, test_name)

    response, request_string = make_request(GET, NDTS)
    assert_equal(request_string, get_code(response), 200, test_name)
    response = get_response(response)
    response = remove_section(response, "timestamp")
    response = remove_section(response, "file_capabilities")
    assert_equal(request_string, response, [ndts_list_response[1]], test_name)

    test_name = "update ndts"
    upload_request[0]["sha-1"] = good_sha
    response, request_string = make_request(POST, UPLOAD, payload=upload_request)
    assert_equal(request_string, get_code(response), 200, test_name)
    assert_equal(request_string, get_response(response), {}, test_name)

    response, request_string = make_request(GET, NDTS, )
    assert_equal(request_string, get_code(response), 200, test_name)
    response = get_response(response)
    response = remove_section(response, "timestamp")
    response = remove_section(response, "file_capabilities")
    assert_equal(request_string, response, ndts_list_response[::-1], test_name)

    test_name = "incorrect request"
    upload_request = {"asd": "asd"}
    response, request_string = make_request(POST, UPLOAD, payload=upload_request)
    assert_equal(request_string, get_code(response), 400, test_name)
    assert_equal(request_string, get_response(response), {"error": ["Request format is incorrect"]}, test_name)

    test_name = "incorrect key"
    upload_request = [{"name_of_the_file": "ndt"}]
    response, request_string = make_request(POST, UPLOAD, payload=upload_request)
    assert_equal(request_string, get_code(response), 400, test_name)
    assert_equal(request_string, get_response(response), {"error": ["Incorrect format, extra keys in request: "
                                                                    "{'name_of_the_file'}"]}, test_name)


def get_actual_report_len(report):
    if report:
        return len(report["report"]["miss_wired"]),\
               len(report["report"]["missing_in_ndt"]),\
               len(report["report"]["missing_in_ufm"])
    else:
        return 0, 0, 0


def get_expected_report_len():
    expected_report = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expected_report.json")
    with open(expected_report, "r") as file:
        expected_response = json.load(file)
        if expected_response:
            return len(expected_response["report"]["miss_wired"]),\
                   len(expected_response["report"]["missing_in_ndt"]),\
                   len(expected_response["report"]["missing_in_ufm"])
        else:
            return 0, 0, 0


def check_comparison_report(comparison_type):
    print("{} report content test".format(comparison_type))

    test_name = "not allowed"
    response, request_string = make_request(POST, REPORTS)
    assert_equal(request_string, get_code(response), 405, test_name)
    assert_equal(request_string, get_response(response), {'error': 'Method is not allowed'}, test_name)

    response, request_string = make_request(GET, REPORTS)
    assert_equal(request_string, get_code(response), 200)
    reports = get_response(response)
    if reports:
        if reports[-1]["report_scope"] != comparison_type:
            print("    - no {} new report was generated, exit -- FAIL".format(comparison_type))
            return
        else:
            print("    - new {} report was generated, continue -- PASS".format(comparison_type))
        reports_number = len(reports)
    else:
        print("    - no new report was generated, exit -- FAIL")
        return

    test_name = "difference"
    response, request_string = make_request(GET, REPORT_ID.format(reports_number))
    assert_equal(request_string, get_code(response), 200, test_name)
    report = get_response(response)
    miss_wired_len, missing_in_ndt_len, missing_in_ufm_len = get_actual_report_len(report)
    expected_report = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expected_report.json")
    with open(expected_report, "r") as file:
        expected_response = json.load(file)
        if expected_response:
            expected_miss_wired_len, expected_missing_in_ndt_len, expected_missing_in_ufm_len,\
                = get_expected_report_len()
        assert_equal(request_string, str(missing_in_ndt_len), str(expected_missing_in_ndt_len), test_name + " missing_in_ndt_len")
        assert_equal(request_string, str(missing_in_ufm_len), str(expected_missing_in_ufm_len), test_name + " missing_in_ufm_len")
        assert_equal(request_string, str(miss_wired_len), str(expected_miss_wired_len), test_name + " miss_wired_len")

    test_name = "report doesn't exist"
    response, request_string = make_request(GET, REPORT_ID.format(reports_number + 1))
    assert_equal(request_string, get_code(response), 400, test_name)
    assert_equal(request_string, get_response(response), {'error': 'Report {} not found'.format(reports_number + 1)},
                 test_name)

    test_name = "invalid report id"
    response, request_string = make_request(GET, REPORT_ID.format("x"))
    assert_equal(request_string, get_code(response), 400, test_name)
    assert_equal(request_string, get_response(response), {'error': 'Report id \'{}\' is not valid'.format("x")},
                 test_name)

# TODO: add ssh?
def syslog_message_count(message):
    syslog_proc = subprocess.Popen(["sudo", "cat", "/var/log/messages"],
                                   stdout=subprocess.PIPE)
    grep_proc = subprocess.run(['grep', message], stdin=syslog_proc.stdout,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.splitlines()
    return len(grep_proc)


def check_syslog(miswired_syslog, mufm_syslog, mndt_syslog):
    miswired_diff = syslog_message_count("NDT: actual") - miswired_syslog
    mufm_diff = syslog_message_count("NDT: missing in UFM") - mufm_syslog
    mndt_diff = syslog_message_count("NDT: missing in NDT") - mndt_syslog

    miswired_expected, mndt_expected, mufm_expected = get_expected_report_len()

    if miswired_diff != miswired_expected:
        print("    - test name: miswired syslog -- FAIL (expected: {}, actual: {})".format(miswired_expected, miswired_diff))
    else:
        print("    - test name: miswired syslog -- PASS")
    if mufm_diff != mufm_expected:
        print("    - test name: missing in UFM syslog -- FAIL (expected: {}, actual: {})".format(mufm_expected, mufm_diff))
    else:
        print("    - test name: missing in UFM syslog -- PASS")
    if mndt_diff != mndt_expected:
        print("    - test name: missing in NDT syslog -- FAIL (expected: {}, actual: {})".format(mndt_expected, mndt_diff))
    else:
        print("    - test name: missing in NDT syslog -- PASS")


def instant_comparison():
    print("Simple compare test")

    miswired_syslog = syslog_message_count("NDT: actual")
    mufm_syslog = syslog_message_count("NDT: missing in UFM")
    mndt_syslog = syslog_message_count("NDT: missing in NDT")

    response, request_string = make_request(POST, COMPARE)
    assert_equal(request_string, get_code(response), 200)
    assert_equal(request_string, get_response(response), {})
    comparison_status_code = get_code(response)

    test_name = "not allowed"
    response, request_string = make_request(GET, COMPARE)
    assert_equal(request_string, get_code(response), 405, test_name)
    assert_equal(request_string, get_response(response), {'error': 'Method is not allowed'}, test_name)

    if comparison_status_code == 200:
        check_syslog(miswired_syslog, mufm_syslog, mndt_syslog)
        check_comparison_report("Instant")


def get_server_datetime():
    response, request_string = make_request(GET, DATE)
    datetime_response = get_response(response)
    datetime_string = datetime_response["date"]
    return datetime.strptime(datetime_string, DATETIME_FORMAT)

def periodic_comparison():
    print("Periodic comparison")

    test_name = "incorrect request"
    payload = {"asd": "asd"}
    response, request_string = make_request(POST, COMPARE, payload=payload)
    assert_equal(request_string, get_code(response), 400, test_name)
    assert_equal(request_string, get_response(response),
                 {'error': "Incorrect format, extra keys in request: {'asd'}"}, test_name)

    test_name = "incorrect datetime format"
    payload = {
        "run": {
            "startTime": "asd",
            "endTime": "xyz",
            "interval": 10
        }
    }
    response, request_string = make_request(POST, COMPARE, payload=payload)
    assert_equal(request_string, get_code(response), 400, test_name)
    assert_equal(request_string, get_response(response),
                 {'error': "Incorrect timestamp format: time data '{}' does not match format '{}'"
                 .format(payload["run"]["startTime"], DATETIME_FORMAT)},
                 test_name)

    datetime_end = datetime_start = get_server_datetime() + timedelta(seconds=3)
    test_name = "too small interval"
    payload = {
        "run": {
            "startTime": datetime_start.strftime(DATETIME_FORMAT),
            "endTime": datetime_end.strftime(DATETIME_FORMAT),
            "interval": 1
        }
    }
    response, request_string = make_request(POST, COMPARE, payload=payload)
    assert_equal(request_string, get_code(response), 400, test_name)
    assert_equal(request_string, get_response(response), {'error': 'Minimal interval value is 5 minutes'},
                 test_name)

    test_name = "end time less than start time"
    payload = {
        "run": {
            "startTime": datetime_start.strftime(DATETIME_FORMAT),
            "endTime": (datetime_end - timedelta(seconds=10)).strftime(DATETIME_FORMAT),
            "interval": 5
        }
    }
    response, request_string = make_request(POST, COMPARE, payload=payload)
    assert_equal(request_string, get_code(response), 400, test_name)
    assert_equal(request_string, get_response(response), {'error': 'End time is less than current time'},
                 test_name)

    datetime_end = datetime_start = get_server_datetime() + timedelta(seconds=5)
    good_payload = {
        "run": {
            "startTime": datetime_start.strftime(DATETIME_FORMAT),
            "endTime": datetime_end.strftime(DATETIME_FORMAT),
            "interval": 10
        }
    }
    response, request_string = make_request(POST, COMPARE, payload=good_payload)
    assert_equal(request_string, get_code(response), 200)
    assert_equal(request_string, get_response(response), {})

    if get_code(response) == 200:
        time.sleep(5)
        check_comparison_report("Periodic")

    test_name = "start scheduler twice"
    datetime_end = datetime_start = get_server_datetime() + timedelta(seconds=2)
    datetime_end = datetime_start + timedelta(minutes=10)
    payload = {
        "run": {
            "startTime": datetime_start.strftime(DATETIME_FORMAT),
            "endTime": datetime_end.strftime(DATETIME_FORMAT),
            "interval": 5
        }
    }
    make_request(POST, COMPARE, payload=payload)
    response, request_string = make_request(POST, COMPARE, payload=payload)
    assert_equal(request_string, get_code(response), 400, test_name)
    assert_equal(request_string, get_response(response), {'error': 'Periodic comparison is already running'}, test_name)

    response, request_string = make_request(POST, CANCEL)
    assert_equal(request_string, get_code(response), 200)
    assert_equal(request_string, get_response(response), {})

    test_name = "cancel nothing"
    response, request_string = make_request(POST, CANCEL)
    assert_equal(request_string, get_code(response), 400, test_name)
    assert_equal(request_string, get_response(response), {'error': 'Periodic comparison is not running'}, test_name)


def delete_ndts(ndts_folder):
    print("Delete NDTs test")
    delete_request = []
    for ndt in os.listdir(ndts_folder):
        delete_request.append({"file_name": "{}".format(ndt)})

    test_name = "not allowed"
    response, request_string = make_request(GET, DELETE)
    assert_equal(request_string, get_code(response), 405, test_name)
    assert_equal(request_string, get_response(response), {'error': 'Method is not allowed'}, test_name)

    test_name = "empty file name"
    upload_request = [{"file_name": ""}]
    response, request_string = make_request(POST, DELETE, payload=upload_request)
    assert_equal(request_string, get_code(response), 400, test_name)
    assert_equal(request_string, get_response(response), {'error': ['File name is empty']}, test_name)

    test_name = "incorrect request"
    upload_request = {"asd": "asd"}
    response, request_string = make_request(POST, DELETE, payload=upload_request)
    assert_equal(request_string, get_code(response), 400, test_name)
    assert_equal(request_string, get_response(response), {"error": ["Request format is incorrect"]}, test_name)

    test_name = "incorrect key"
    upload_request = [{"name_of_the_file": "ndt"}]
    response, request_string = make_request(POST, DELETE, payload=upload_request)
    assert_equal(request_string, get_code(response), 400, test_name)
    assert_equal(request_string, get_response(response), {"error": ["Incorrect format, extra keys in request: "
                                                                    "{'name_of_the_file'}"]}, test_name)

    test_name = "wrong ndt name"
    wrong_name_request = [delete_request[0], {"file_name": "xyz"}]
    response, request_string = make_request(POST, DELETE, payload=wrong_name_request)
    assert_equal(request_string, get_code(response), 400, test_name)
    assert_equal(request_string, get_response(response),
                 {"error": ["Cannot remove {}: file not found".format("xyz")]}, test_name)

    response, request_string = make_request(GET, NDTS)
    assert_equal(request_string, get_code(response), 200, test_name)
    ndts_len = 0
    if get_response(response):
        ndts_len = len(get_response(response))
    assert_equal(request_string, str(ndts_len), str(1), test_name)

    response, request_string = make_request(POST, DELETE,
                                            payload=[{"file_name": delete_request[1]["file_name"]}])
    assert_equal(request_string, get_code(response), 200)
    assert_equal(request_string, get_response(response), {})

    response, request_string = make_request(GET, NDTS)
    assert_equal(request_string, get_code(response), 200)
    assert_equal(request_string, get_response(response), [])


def topo_diff(ndts_folder):
    print("Topo diff tests")

    test_name = "no ndts"
    response, request_string = make_request(POST, COMPARE)
    assert_equal(request_string, get_code(response), 400, test_name)
    assert_equal(request_string, get_response(response), {'error': ['No NDTs were uploaded for comparison']}, test_name)

    garbage_ndt = "garbage.ndt"
    upload_request = []
    with open(os.path.join(ndts_folder, garbage_ndt), "r") as file:
        data = file.read()
        upload_request.append({"file_name": garbage_ndt,
                               "file": data,
                               "file_type": "switch_to_switch",
                               "sha-1": get_hash(data)})
    make_request(POST, UPLOAD, payload=upload_request)
    response, request_string = make_request(POST, COMPARE)
    assert_equal(request_string, get_code(response), 400, garbage_ndt)
    assert_equal(request_string, get_response(response),
                 {'error': ['/config/ndts/garbage.ndt is empty or cannot be parsed']}, garbage_ndt)
    make_request(POST, DELETE, payload=[{"file_name": garbage_ndt}])

    incorrect_ports_ndt = "incorrect_ports.ndt"
    upload_request.clear()
    with open(os.path.join(ndts_folder, incorrect_ports_ndt), "r") as file:
        data = file.read()
        upload_request.append({"file_name": incorrect_ports_ndt,
                               "file": data,
                               "file_type": "switch_to_switch",
                               "sha-1": get_hash(data)})
    make_request(POST, UPLOAD, payload=upload_request)
    response, request_string = make_request(POST, COMPARE)
    assert_equal(request_string, get_code(response), 400, incorrect_ports_ndt)
    # patterns = (r"^Port (\d+)$", r"(^Blade \d+_Port \d+/\d+$)", r"(^SAT\d+ ibp.*$)")
    assert_equal(request_string, get_response(response),
                 {'error': ['Failed to parse PortType.SOURCE: abra, in file: incorrect_ports.ndt, line: 0.',
                            'Failed to parse PortType.DESTINATION: cadabra, in file: incorrect_ports.ndt, line: 0.']},
                 incorrect_ports_ndt)
    make_request(POST, DELETE, payload=[{"file_name": incorrect_ports_ndt}])

    incorrect_columns_ndt = "incorrect_columns.ndt"
    upload_request.clear()
    with open(os.path.join(ndts_folder, incorrect_columns_ndt), "r") as file:
        data = file.read()
        upload_request.append({"file_name": incorrect_columns_ndt,
                               "file": data,
                               "file_type": "switch_to_switch",
                               "sha-1": get_hash(data)})
    make_request(POST, UPLOAD, payload=upload_request)
    response, request_string = make_request(POST, COMPARE)
    assert_equal(request_string, get_code(response), 400, incorrect_columns_ndt)
    assert_equal(request_string, get_response(response),
                 {'error': ["No such column: 'StartPort', in line: 0"]}, incorrect_columns_ndt)
    make_request(POST, DELETE, payload=[{"file_name": incorrect_columns_ndt}])


def main():
    ndts_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "positive_flow_ndts")
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    no_ndts()
    upload_metadata(ndts_folder)
    instant_comparison()
    periodic_comparison()
    delete_ndts(ndts_folder)

    ndts_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "negative_flow_ndts")
    topo_diff(ndts_folder)

    if FAILED_TESTS_COUNT > 0:
        print("\n{} tests failed".format(FAILED_TESTS_COUNT))
        return 1
    else:
        return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='NDT plugin test')
    parser.add_argument('-ip', '--host', type=str, required=True, help='Host IP address where NDT plugin is running')
    args = parser.parse_args()
    HOST_IP = args.host

    sys.exit(main())
