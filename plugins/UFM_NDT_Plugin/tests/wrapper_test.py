from datetime import datetime, timedelta
import subprocess

HOST_IP = "r-ufm247"
DEFAULT_PASSWORD = "123456"

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


def assert_equal(test_name, output):
    if "response code: 200" in output.decode('utf-8'):
        print("Test {}: PASS".format(test_name))
    else:
        print("Test {}: FAIL (output: {})".format(test_name, output))


def main():
    wrapper_file = "ndt_rest_api.py"
    authentication_cmd = [BASIC, "-u", "admin", "-p", "123456"]

    cmd = ["python3", wrapper_file, HOST_IP, NDTS] + authentication_cmd
    assert_equal(NDTS, subprocess.check_output(cmd))

    ndts_folder = "positive_flow_ndts"
    files = "{}/switch_to_host_topo1.ndt|switch_to_host,{}/switch_to_switch_topo2.ndt|switch_to_switch" \
        .format(ndts_folder, ndts_folder)
    cmd = ["python3", wrapper_file, HOST_IP, UPLOAD_METADATA, "-uf", files] + authentication_cmd
    assert_equal(UPLOAD_METADATA, subprocess.check_output(cmd))

    cmd = ["python3", wrapper_file, HOST_IP, COMPARE] + authentication_cmd
    assert_equal(COMPARE, subprocess.check_output(cmd))

    cmd = ["python3", wrapper_file, HOST_IP, REPORTS] + authentication_cmd
    assert_equal(REPORTS, subprocess.check_output(cmd))

    report_id = "1"
    cmd = ["python3", wrapper_file, HOST_IP, REPORTS, "-id", report_id] + authentication_cmd
    assert_equal(REPORTS + "/{}".format(report_id), subprocess.check_output(cmd))

    start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    end = (datetime.now() + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
    interval = "5"
    cmd = ["python3", wrapper_file, HOST_IP, COMPARE, "-s", start, "-e", end, "-i", interval] + authentication_cmd
    assert_equal("periodic " + COMPARE, subprocess.check_output(cmd))

    cmd = ["python3", wrapper_file, HOST_IP, CANCEL] + authentication_cmd
    assert_equal(CANCEL, subprocess.check_output(cmd))

    files = "switch_to_host_topo1.ndt,switch_to_switch_topo2.ndt"
    cmd = ["python3", wrapper_file, HOST_IP, DELETE, "-df", files] + authentication_cmd
    assert_equal(DELETE, subprocess.check_output(cmd))


if __name__ == "__main__":
    main()
