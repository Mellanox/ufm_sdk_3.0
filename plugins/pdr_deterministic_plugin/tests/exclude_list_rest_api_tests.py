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

import http
import json
import time
import requests


def test_exclude_list_rest_api():
    """
    Test exclude list via plugin REST API
    """
    print("\n") # Start tests output from new line

    url = "http://127.0.0.1:8977/excluded"

    excluded_ports = [
        ("0123456789aaabbb_1", 0),  # Add forever
        ("9876543210cccddd_2", 30), # Add for 30 seconds
        ("3456789012eeefff_3", 0)   # Add forever
    ]

    # Get (empty) list content
    response = requests.get(url, timeout=5)
    assert response.status_code == http.client.OK
    print("    - test: get exclusion list and ensure it's empty -- PASS")

    # Add ports to excluded list
    response = requests.put(url, data=json.dumps(excluded_ports), timeout=5)
    assert response.status_code == http.client.OK
    for pair in excluded_ports:
        port_name = pair[0]
        assert port_name in response.text
    print("    - test: add ports to exclusion list -- PASS")

    # Test exclusion list content
    response = requests.get(url, timeout=5)
    assert response.status_code == http.client.OK
    for pair in excluded_ports:
        port_name = pair[0]
        assert port_name in response.text
    print("    - test: get added ports from exclusion list -- PASS")

    # Wait until 2nd port TTL is expired
    ttl_seconds = excluded_ports[1][1]
    time.sleep(ttl_seconds + 1)

    # Test auto-remove of second port after TTL is expired
    response = requests.get(url, timeout=5)
    assert response.status_code == http.client.OK
    for (index, pair) in enumerate(excluded_ports):
        port_name = pair[0]
        if (index == 1):
            assert port_name not in response.text
        else:
            assert port_name in response.text
    print("    - test: auto-remove of port from exclusion list after TTL is expired -- PASS")

if __name__ == '__main__':
    test_exclude_list_rest_api()
