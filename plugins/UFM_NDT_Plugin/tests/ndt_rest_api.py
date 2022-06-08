import argparse
import hashlib
import requests
import re
import os
import json
import textwrap

# predefined params
BASE_ENVIRON_NAME = "UFM_PLUGIN_NDT_{}"
AUTH_TYPE = os.environ.get(BASE_ENVIRON_NAME.format('AUTH_TYPE'), None)
HOST = os.environ.get(BASE_ENVIRON_NAME.format('HOST'), None)
USER = os.environ.get(BASE_ENVIRON_NAME.format('USER'), None)
PASSWORD = os.environ.get(BASE_ENVIRON_NAME.format('PASSWORD'), None)
PRIVATE_KEY = os.environ.get(BASE_ENVIRON_NAME.format('PRIVATE_KEY'), None)
CLIENT_CERTIFICATE = os.environ.get(BASE_ENVIRON_NAME.format('CLIENT_CERTIFICATE'), None)
AUTHENTICATION_TOKEN = os.environ.get(BASE_ENVIRON_NAME.format('AUTHENTICATION_TOKEN'), None)

# resources
NDTS = "list"
UPLOAD = "upload"
COMPARE = "compare"
DELETE = "delete"
CANCEL = "cancel"
REPORTS = "reports"
REPORT_ID_PATTERN = "^reports/\d+$"
VERSION = "version"
HELP = "help"

# authentication types
BASIC = "basic"
CLIENT = "client_cert"
TOKEN = "token"


def get_rest_version(auth_type):
    if auth_type == BASIC:
        return ""
    elif auth_type == CLIENT:
        return "V2"
    elif auth_type == TOKEN:
        return "V3"


def make_request(host_ip, request, auth_type, auth, payload, headers, cert):
    request_string = "https://{}/ufmRest{}/plugin/ndt/{}".format(host_ip, get_rest_version(auth_type), request)

    verify = True if cert else False
    if request in [NDTS, REPORTS, VERSION, HELP] or re.match(REPORT_ID_PATTERN, request):
        response = requests.get(request_string, verify=verify, headers=headers, auth=auth, cert=cert)
    elif request in [UPLOAD, COMPARE, DELETE, CANCEL]:
        response = requests.post(request_string, verify=verify, headers=headers, auth=auth, cert=cert, json=payload)
    else:
        print("Request /{} is not supported".format(request))
        return None

    print("URL: {}, response code: {}".format(request_string, response.status_code))
    return response


def parse_args():
    parser = argparse.ArgumentParser(description='NDT REST API provider',
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=textwrap.dedent('''\
                                              use following environment variables to set arguments permanently:
                                                  UFM_PLUGIN_NDT_AUTH_TYPE
                                                  UFM_PLUGIN_NDT_HOST
                                                  UFM_PLUGIN_NDT_USER
                                                  UFM_PLUGIN_NDT_PASSWORD
                                                  UFM_PLUGIN_NDT_PRIVATE_KEY
                                                  UFM_PLUGIN_NDT_CLIENT_CERTIFICATE
                                                  UFM_PLUGIN_NDT_AUTHENTICATION_TOKEN
                                                e.g., "export UFM_PLUGIN_NDT_AUTH_TYPE=client_cert"
                                              ''')
    )
    parser.add_argument('request', type=str, help='Request to complete',
                        choices=[NDTS, REPORTS, UPLOAD, COMPARE, DELETE, CANCEL, VERSION, HELP])
    parser.add_argument('-ip', '--host', type=str, help='Host IP address where NDT is running')
    parser.add_argument('-a', '--auth_type', type=str, help='Authentication type', choices=[BASIC, CLIENT, TOKEN])
    parser.add_argument('-u', '--user', type=str)
    parser.add_argument('-p', '--password', type=str)
    parser.add_argument('-t', '--token', type=str)
    parser.add_argument('-d', '--data', type=str, help='Sends the specified data in a POST request')
    parser.add_argument('-df', '--delete_files', type=str, help='String with file names to delete, '
                                                                'format: \"file1,file2,...,fileN\"')
    parser.add_argument('-uf', '--upload_files', type=str, help='String with absolute file paths to upload, '
                                                                'format: \"file1|type1,file2|type2,...,fileN|typeN\" '
                                                                'where type is switch_to_switch or switch_to_host')
    parser.add_argument('-s', '--start', type=str, help="Periodic comparison start time, "
                                                        r"format: '%%Y-%%m-%%d %%H:%%M:%%S'")
    parser.add_argument('-e', '--end', type=str, help="Periodic comparison end time, "
                                                      "format: '%%Y-%%m-%%d %%H:%%M:%%S'")
    parser.add_argument('-i', '--interval', type=str, help="Periodic comparison interval in minutes")
    parser.add_argument('-id', '--report_id', type=int, help="Specific report to show")
    parser.add_argument('-c', '--cert', type=str, help="Client certificate file name")
    parser.add_argument('-k', '--key', type=str, help="Private key file name")
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

    auth_type = args.auth_type if args.auth_type else AUTH_TYPE
    host = args.host if args.host else HOST
    user = args.user if args.user else USER
    password = args.password if args.password else PASSWORD
    private_key = args.key if args.key else PRIVATE_KEY
    client_cert = args.cert if args.cert else CLIENT_CERTIFICATE
    authentication_token = args.token if args.token else AUTHENTICATION_TOKEN
    headers = {}
    auth = None
    cert = None
    if auth_type == BASIC:
        if not user or not password:
            print("Please provide user and password to authenticate")
            exit(1)
        else:
            auth = (user, password)
    elif auth_type == CLIENT:
        if not private_key or not client_cert:
            print("Please provide private key and certificate to authenticate")
            exit(1)
        else:
            cert = (client_cert, private_key)
    elif auth_type == TOKEN:
        if not authentication_token:
            print("Please provide token to authenticate")
            exit(1)
        else:
            headers = {'Authorization': 'Bearer {}'.format(authentication_token)}

    payload = {}
    if args.request == UPLOAD:
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

    response = make_request(host, args.request, auth_type, auth, payload, headers, cert)
    if response is not None:
        if response.status_code in [200, 400, 500]:
            json_formatted_str = json.dumps(response.json(), indent=2)
            print("Response:\n{}".format(json_formatted_str))


if __name__ == "__main__":
    main()
