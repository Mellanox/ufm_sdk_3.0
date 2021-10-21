import json

import requests
import logging
import os
import hashlib


def get_hash(file_content):
    sha1 = hashlib.sha1()
    sha1.update(file_content.encode('utf-8'))
    return sha1.hexdigest()


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


def make_request(host_ip, request_type, resource, payload=None, user="admin", password="123456", rest_version="",
                 headers=None):
    if headers is None:
        headers = {}
    request = "https://{}/ufmRest{}/plugin/ndt/{}".format(host_ip, rest_version, resource)
    logging.info("Send UFM API Request, URL:" + request)
    try:
        response = None
        if request_type == "POST":
            response = requests.post(request, verify=False, headers=headers, auth=(user, password), data=payload)
        elif request_type == "GET":
            response = requests.get(request, verify=False, headers=headers, auth=(user, password))
        else:
            logging.error("Request {} is not supported".format(request_type))
            return response
        logging.info("UFM API Request Status [" + str(response.status_code) + "], URL " + request)
        if response.raise_for_status():
            logging.warning(response.raise_for_status())
        return response
    except Exception as e:
        logging.error(e)


def assert_equal(test_name, left_expr, right_expr):
    if left_expr == right_expr:
        print("{}: PASS".format(test_name))
    else:
        print("{}: FAIL (expected: {}, actual: {})".format(test_name, right_expr, left_expr))


def get_json(response):
    if response:
        return response.json()
    else:
        return None


def get_status_code(response):
    if response:
        return response.status_code
    else:
        return None


def no_ndts_test():
    response = make_request("swx-tol", "GET", "list")
    json_response = get_json(response)
    assert_equal("Empty list", json_response, [])


def upload_metadata(ndts_folder):
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
                                   "sha-1": get_hash(data)})
            ndts_list_response.append({"file": ndt,
                                       "file_type": file_type,
                                       "sha-1": get_hash(data)})

    response = make_request("swx-tol", "POST", "upload_metadata", payload=json.dumps(upload_request))
    status_code = get_status_code(response)
    assert_equal("Upload 2 NDTs", status_code, 200)

    response = make_request("swx-tol", "GET", "list")
    json_response = get_json(response)
    assert_equal("Check NDTs list has 2 NDTs", remove_timestamp(json_response), ndts_list_response)


def instant_comparison():
    response = make_request("swx-tol", "POST", "compare")
    status_code = get_status_code(response)
    assert_equal("Instant comparison", status_code, 200)


def check_comparison_report():
    response = make_request("swx-tol", "GET", "reports")
    reports = get_json(response)
    reports_number = 0
    if reports:
        reports_number = len(reports)
    response = make_request("swx-tol", "GET", "reports/{}".format(reports_number))
    report = get_json(response)
    expected_report = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expected_report.json")
    with open(expected_report, "r") as file:
        expected_response = json.load(file)
        assert_equal("Report content", remove_timestamp(report), remove_timestamp(expected_response))


def delete_ndts(ndts_folder):
    delete_request = []
    for ndt in os.listdir(ndts_folder):
        delete_request.append({"file_name": "{}".format(ndt)})
    response = make_request("swx-tol", "POST", "delete", payload=json.dumps(delete_request))
    status_code = get_status_code(response)
    assert_equal("Delete 2 NDTs", status_code, 200)

    response = make_request("swx-tol", "GET", "list")
    json_response = get_json(response)
    assert_equal("Check NDTs list is empty", json_response, [])


def main():
    ndts_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "positive_flow_ndts")

    no_ndts_test()
    upload_metadata(ndts_folder)
    instant_comparison()
    check_comparison_report()
    delete_ndts(ndts_folder)


if __name__ == "__main__":
    logging.basicConfig(filename=os.path.join(os.path.dirname(os.path.abspath(__file__)), "positive.log"),
                        level=logging.ERROR)
    main()
