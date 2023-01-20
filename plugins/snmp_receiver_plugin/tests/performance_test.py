#
# Copyright © 2013-2022 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
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
import inspect
import psutil
import requests
import sys
import time

FAILED_TESTS_COUNT = 0
THROUGHPUT_FILE = "/opt/ufm/ufm_plugins_data/snmp/throughput.log"
LINES_TO_CHECK = 300
THROUGHPUT_THRESHOLD = 100
CPU_UTILIZATION_THRESHOLD = 80
TIMES_FAILED_THRESHOLD = 10
REQUEST_TIME_THRESHOLD = 1

def check_throughput():
    function_name = inspect.stack()[0][3]
    with open(THROUGHPUT_FILE, "r") as file:
        content = reversed(file.readlines())
        times_failed = 0
        for i, line in enumerate(content):
            if i > LINES_TO_CHECK:
                break
            words = line.split()
            throughput = words[-2]
            rate_type = words[0]
            if float(throughput) < THROUGHPUT_THRESHOLD:
                times_failed += 1
                print(f"Warning: throughput is low - {throughput}, while threshold is {THROUGHPUT_THRESHOLD}")
        if times_failed > TIMES_FAILED_THRESHOLD:
            print(f"{function_name} -- FAILED, throughput was too low {times_failed} times out of {LINES_TO_CHECK} checks")
            global FAILED_TESTS_COUNT
            FAILED_TESTS_COUNT += 1
        print(f"{function_name} PASSED, failed checks: {times_failed} out of {LINES_TO_CHECK}")

def check_cpu_load():
    function_name = inspect.stack()[0][3]
    times_failed = 0
    tries = 10
    for _ in range(tries):
        cpus_load = psutil.cpu_percent(interval=1, percpu=True)
        for i, cpu_load in enumerate(cpus_load):
            if cpu_load > CPU_UTILIZATION_THRESHOLD:
                times_failed += 1
                print(f"Warning: utilization of {i} cpu is high - {cpu_load}, while threshold is {CPU_UTILIZATION_THRESHOLD}")
    if times_failed > TIMES_FAILED_THRESHOLD:
        print(f"{function_name} -- FAILED, cpu was too high {times_failed} times out of {tries} checks")
        global FAILED_TESTS_COUNT
        FAILED_TESTS_COUNT += 1
    tries = psutil.cpu_count() * tries
    print(f"{function_name} -- PASSED, failed checks: {times_failed} out of {tries}")

def check_systems_api():
    function_name = inspect.stack()[0][3]
    user = "admin"
    password = "123456"
    host = "0.0.0.0"
    resource = "resources/systems"
    request = f"https://{host}/ufmRest/{resource}"
    start_time = time.time()
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    requests.get(request, auth=(user, password), verify=False)
    end_time = time.time()
    duration = end_time - start_time
    print(f"{request} duration is {duration}")
    if duration > REQUEST_TIME_THRESHOLD:
        print(f"{function_name} -- FAILED, {request} duration is {duration}, while the threshold is {REQUEST_TIME_THRESHOLD}")
        global FAILED_TESTS_COUNT
        FAILED_TESTS_COUNT += 1
    print(f"{function_name} -- PASSED, {request} duration is {duration}")

def main():
    check_throughput()
    check_cpu_load()
    check_systems_api()

    if FAILED_TESTS_COUNT > 0:
        print("\n{} tests failed".format(FAILED_TESTS_COUNT))
        return 1
    else:
        return 0

if __name__ == "__main__":
    sys.exit(main())