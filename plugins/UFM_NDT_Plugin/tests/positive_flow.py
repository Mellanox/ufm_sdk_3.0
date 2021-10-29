import json
import time

import requests
import logging
import os
import hashlib
from datetime import datetime, timedelta


def get_hash(file_content):
    sha1 = hashlib.sha1()
    sha1.update(file_content.encode('utf-8'))
    return sha1.hexdigest()


HOST_IP = "swx-tol"
DEFAULT_PASSWORD = "123456"
# HOST_IP = "r-ufm235"
# DEFAULT_PASSWORD = "admin"

# rest api
GET = "GET"
POST = "POST"

# resources
NDTS = "list"
UPLOAD_METADATA = "upload_metadata"
COMPARE = "compare"
DELETE = "delete"
CANCEL = "cancel"
REPORTS = "reports"
REPORT_ID = "reports/{}"

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


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


def make_request(request_type, resource, payload=None, user="admin", password=DEFAULT_PASSWORD,
                 rest_version="", headers=None):
    if headers is None:
        headers = {}
    if payload is None:
        payload = {}
    request = "https://{}/ufmRest{}/plugin/ndt/{}".format(HOST_IP, rest_version, resource)
    response = None
    if request_type == POST:
        response = requests.post(request, verify=False, headers=headers, auth=(user, password), data=payload)
    elif request_type == GET:
        response = requests.get(request, verify=False, headers=headers, auth=(user, password))
    else:
        logging.error("Request {} is not supported".format(request_type))
    logging.info("UFM API Request Status [" + str(response.status_code) + "], URL " + request)
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


def no_ndts_test():
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
            upload_request.append({"file_name": ndt,
                                   "file": data,
                                   "file_type": file_type,
                                   "sha-1": "1"})
            ndts_list_response.append({"file": ndt,
                                       "sha-1": get_hash(data),
                                       "file_type": file_type})

    test_name = "not allowed"
    response, request_string = make_request(GET, UPLOAD_METADATA, payload=json.dumps(upload_request))
    assert_equal(request_string, get_code(response), 405, test_name)
    assert_equal(request_string, get_response(response), {'error': 'Method is not allowed'}, test_name)

    test_name = "wrong sha-1"
    good_sha = upload_request[0]["sha-1"]
    file_name = upload_request[0]["file_name"]
    upload_request[0]["sha-1"] = "xyz"
    response, request_string = make_request(POST, UPLOAD_METADATA, payload=json.dumps(upload_request))
    assert_equal(request_string, get_code(response), 400, test_name)
    assert_equal(request_string, get_response(response),
                 {"error": ["Provided sha-1 {} for {} is different from actual one {}"
                 .format("xyz", file_name, good_sha)]}, test_name)

    response, request_string = make_request(GET, NDTS, )
    assert_equal(request_string, get_code(response), 200, test_name)
    assert_equal(request_string, remove_timestamp(get_response(response)), [ndts_list_response[1]], test_name)

    test_name = "update ndts"
    upload_request[0]["sha-1"] = good_sha
    response, request_string = make_request(POST, UPLOAD_METADATA, payload=json.dumps(upload_request))
    assert_equal(request_string, get_code(response), 200, test_name)
    assert_equal(request_string, get_response(response), {}, test_name)

    response, request_string = make_request(GET, NDTS, )
    assert_equal(request_string, get_code(response), 200, test_name)
    assert_equal(request_string, remove_timestamp(get_response(response)), ndts_list_response[::-1], test_name)

    test_name = "incorrect request"
    upload_request = {"asd": "asd"}
    response, request_string = make_request(POST, UPLOAD_METADATA, payload=json.dumps(upload_request))
    assert_equal(request_string, get_code(response), 400, test_name)
    assert_equal(request_string, get_response(response), {"error": ["Request format is incorrect"]}, test_name)

    test_name = "incorrect key"
    upload_request = [{"name_of_the_file": "ndt"}]
    response, request_string = make_request(POST, UPLOAD_METADATA, payload=json.dumps(upload_request))
    assert_equal(request_string, get_code(response), 400, test_name)
    assert_equal(request_string, get_response(response), {"error": ["Incorrect format, no expected key in request: "
                                                                    "'file_name'"]}, test_name)


def instant_comparison():
    print("Simple compare test")
    response, request_string = make_request(POST, COMPARE)
    assert_equal(request_string, get_code(response), 200)
    assert_equal(request_string, get_response(response), {})
    comparison_status_code = get_code(response)

    test_name = "not allowed"
    response, request_string = make_request(GET, COMPARE)
    assert_equal(request_string, get_code(response), 405, test_name)
    assert_equal(request_string, get_response(response), {'error': 'Method is not allowed'}, test_name)

    if comparison_status_code == 200:
        check_comparison_report("Instant")


def check_comparison_report(comparison_type):
    print("{} report content test".format(comparison_type))
    start_test_time = datetime.now()

    test_name = "not allowed"
    response, request_string = make_request(POST, REPORTS)
    assert_equal(request_string, get_code(response), 405, test_name)
    assert_equal(request_string, get_response(response), {'error': 'Method is not allowed'}, test_name)

    response, request_string = make_request(GET, REPORTS)
    assert_equal(request_string, get_code(response), 200)
    reports = get_response(response)
    reports_number = 0
    if reports:
        reports_number = len(reports)

    test_name = "difference"
    response, request_string = make_request(GET, REPORT_ID.format(reports_number))
    assert_equal(request_string, get_code(response), 200, test_name)
    report = get_response(response)
    report_len = 0
    if report:
        # if datetime.strptime(report["timestamp"], DATETIME_FORMAT) < start_test_time:
        #     print("    - no new report was generated, exit -- FAIL")
        #     return
        # else:
        #     print("    - new report was generated, continue -- PASS")
        report_len = len(report["report"]["missing_in_ndt"])
    expected_report = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expected_report.json")
    with open(expected_report, "r") as file:
        expected_response = json.load(file)
        expected_report_len = 0
        if expected_response:
            expected_report_len = len(expected_response["report"]["missing_in_ndt"])
        assert_equal(request_string, str(report_len), str(expected_report_len), test_name)

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


def periodic_comparison():
    print("Periodic comparison")

    datetime_end = datetime_start = datetime.now() + timedelta(seconds=1)

    test_name = "incorrect request"
    payload = {"asd": "asd"}
    response, request_string = make_request(POST, COMPARE, payload=json.dumps(payload))
    assert_equal(request_string, get_code(response), 400, test_name)
    assert_equal(request_string, get_response(response),
                 {'error': "Incorrect format, no expected key in request: 'run'"}, test_name)

    test_name = "incorrect datetime format"
    payload = {
        "run": {
            "startTime": "asd",
            "endTime": "xyz",
            "interval": 10
        }
    }
    response, request_string = make_request(POST, COMPARE, payload=json.dumps(payload))
    assert_equal(request_string, get_code(response), 400, test_name)
    assert_equal(request_string, get_response(response),
                 {'error': "Incorrect timestamp format: time data '{}' does not match format '%Y-%m-%d %H:%M:%S'"
                 .format(payload["run"]["startTime"])},
                 test_name)

    test_name = "too small interval"
    payload = {
        "run": {
            "startTime": datetime_start.strftime("%Y-%m-%d %H:%M:%S"),
            "endTime": datetime_end.strftime("%Y-%m-%d %H:%M:%S"),
            "interval": 1
        }
    }
    response, request_string = make_request(POST, COMPARE, payload=json.dumps(payload))
    assert_equal(request_string, get_code(response), 400, test_name)
    assert_equal(request_string, get_response(response), {'error': 'Minimum interval value is 5 minutes'},
                 test_name)

    good_payload = {
        "run": {
            "startTime": datetime_start.strftime("%Y-%m-%d %H:%M:%S"),
            "endTime": datetime_end.strftime("%Y-%m-%d %H:%M:%S"),
            "interval": 10
        }
    }
    response, request_string = make_request(POST, COMPARE, payload=json.dumps(good_payload))
    assert_equal(request_string, get_code(response), 200)
    assert_equal(request_string, get_response(response), {})
    comparison_status_code = get_code(response)

    # if comparison_status_code == 200:
    #     time.sleep(1)
    #     check_comparison_report("Periodic")

    test_name = "start scheduler twice"
    response, request_string = make_request(POST, COMPARE, payload=json.dumps(good_payload))
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

    test_name = "incorrect request"
    upload_request = {"asd": "asd"}
    response, request_string = make_request(POST, DELETE, payload=json.dumps(upload_request))
    assert_equal(request_string, get_code(response), 400, test_name)
    assert_equal(request_string, get_response(response), {"error": ["Request format is incorrect"]}, test_name)

    test_name = "incorrect key"
    upload_request = [{"name_of_the_file": "ndt"}]
    response, request_string = make_request(POST, DELETE, payload=json.dumps(upload_request))
    assert_equal(request_string, get_code(response), 400, test_name)
    assert_equal(request_string, get_response(response), {"error": ["Incorrect format, no expected key in request: "
                                                                    "'file_name'"]}, test_name)

    test_name = "wrong ndt name"
    wrong_name_request = [delete_request[0], {"file_name": "xyz"}]
    response, request_string = make_request(POST, DELETE, payload=json.dumps(wrong_name_request))
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
                                            payload=json.dumps([{"file_name": delete_request[1]["file_name"]}]))
    assert_equal(request_string, get_code(response), 200)
    assert_equal(request_string, get_response(response), {})

    response, request_string = make_request(GET, NDTS)
    assert_equal(request_string, get_code(response), 200)
    assert_equal(request_string, get_response(response), [])


def main():
    os.environ['PYTHONWARNINGS'] = 'ignore:Unverified HTTPS request'
    ndts_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "positive_flow_ndts")
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # no_ndts_test()
    upload_metadata(ndts_folder)
    # instant_comparison()
    # periodic_comparison()
    # delete_ndts(ndts_folder)


if __name__ == "__main__":
    logging.basicConfig(filename=os.path.join(os.path.dirname(os.path.abspath(__file__)), "positive.log"),
                        level=logging.ERROR)
    main()
