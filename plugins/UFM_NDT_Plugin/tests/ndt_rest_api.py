import argparse
import hashlib
import requests
import re
import os

# resources
NDTS = "list"
UPLOAD_METADATA = "upload_metadata"
COMPARE = "compare"
DELETE = "delete"
CANCEL = "cancel"
REPORTS = "reports"
REPORT_ID_PATTERN = "^reports/\d+$"

# authentication types
BASIC = "basic"
CLIENT = "client"
TOKEN = "token"


def get_rest_version(auth_type):
    if auth_type == BASIC:
        return ""
    elif auth_type == CLIENT:
        return "V2"
    elif auth_type == TOKEN:
        return "V3"


def make_request(host_ip, request, auth_type, user, password, payload, headers):
    request_string = "https://{}/ufmRest{}/plugin/ndt/{}".format(host_ip, get_rest_version(auth_type), request)

    if request in [NDTS, REPORTS] or re.match(REPORT_ID_PATTERN, request):
        if auth_type == BASIC:
            response = requests.get(request_string, verify=False, headers=headers, auth=(user, password))
        else:
            response = requests.get(request_string, verify=False, headers=headers)
    elif request in [UPLOAD_METADATA, COMPARE, DELETE, CANCEL]:
        if auth_type == BASIC:
            response = requests.post(request_string, verify=False, headers=headers, auth=(user, password), json=payload)
        else:
            response = requests.post(request_string, verify=False, headers=headers, json=payload)
    else:
        print("Request /{} is not supported".format(request))
        return None

    print("URL: {}, response code: {}".format(request_string, response.status_code))
    return response


def parse_args():
    parser = argparse.ArgumentParser(description='NDT REST API provider')
    parser.add_argument('host', type=str, help='Host IP address where NDT is running')
    parser.add_argument('request', type=str, help='Request to complete',
                        choices=[NDTS, REPORTS, UPLOAD_METADATA, COMPARE, DELETE, CANCEL])
    parser.add_argument('auth_type', type=str, help='Authentication type', choices=[BASIC, CLIENT, TOKEN])
    parser.add_argument('-u', '--user', type=str)
    parser.add_argument('-p', '--password', type=str)
    parser.add_argument('-t', '--token', type=str)
    parser.add_argument('-d', '--data', type=str, help='Sends the specified data in a POST request')
    parser.add_argument('-df', '--delete_files', type=str, help='String with file names to delete, '
                                                                'format: file1|type1,file2|type2,...,fileN|typeN '
                                                                'where type is switch_to_switch or switch_to_host')
    parser.add_argument('-uf', '--upload_files', type=str, help='String with absolute file paths to upload, '
                                                                'format: file1,file2,...,fileN')
    parser.add_argument('-s', '--start', type=str, help="Periodic comparison start time, "
                                                        "format: '%Y-%m-%d %H:%M:%S'")
    parser.add_argument('-e', '--end', type=str, help="Periodic comparison end time ,"
                                                      "format: '%Y-%m-%d %H:%M:%S'")
    parser.add_argument('-i', '--interval', type=str, help="Periodic comparison interval in minutes")
    parser.add_argument('-id', '--report_id', type=int, help="Specific report to show")
    args = parser.parse_args()
    return args


def get_hash(file_content):
    sha1 = hashlib.sha1()
    sha1.update(file_content.encode('utf-8'))
    return sha1.hexdigest()


def parse_upload_files(files):
    data = []
    for ndt in files.split(","):
        try:
            (file_path, file_type) = ndt.split("|")
        except ValueError:
            return [], "File path format is incorrect"
        try:
            with open(file_path, "r") as file:
                file_content = file.read()
                data.append({"file_name": os.path.basename(file_path),
                             "file": file_content,
                             "file_type": file_type,
                             "sha-1": get_hash(file_content)})
        except FileNotFoundError as fnfe:
            return [], fnfe
    return data, ""


def parse_delete_files(files):
    data = []
    for ndt in files.split(","):
        data.append({"file_name": "{}".format(ndt)})
    return data


def parse_compare(start, end, interval):
    return {
        "run": {
            "startTime": start,
            "endTime": end,
            "interval": interval
        }
    }


def main():
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    args = parse_args()
    headers = {}
    if args.auth_type == BASIC and (args.user is None or args.password is None):
        print("Please provide user and password to authenticate")
        exit(1)
    elif args.auth_type == TOKEN:
        if args.token is None:
            print("Please provide token to authenticate")
            exit(1)
        else:
            headers = {'Authorization': 'Bearer {}'.format(args.token)}

    payload = {}
    if args.request == UPLOAD_METADATA:
        if args.upload_files is None:
            print("Please provide file paths to upload")
            exit(1)
        else:
            payload, error = parse_upload_files(args.upload_files)
            if error:
                print(error)
                exit(1)
    elif args.request == DELETE:
        if args.delete_files is None:
            print("Please provide file names to delete")
            exit(1)
        else:
            payload = parse_delete_files(args.delete_files)
    elif args.request == COMPARE:
        if args.start and args.end and args.interval:
            payload = parse_compare(args.start, args.end, args.interval)
    elif args.request == REPORTS and args.report_id:
            args.request += "/{}".format(args.report_id)

    response = make_request(args.host, args.request, args.auth_type, args.user,
                            args.password, payload, headers)
    if response is not None:
        if response.status_code in [200, 400]:
            print("Response:\n {}".format(response.json()))


if __name__ == "__main__":
    main()
