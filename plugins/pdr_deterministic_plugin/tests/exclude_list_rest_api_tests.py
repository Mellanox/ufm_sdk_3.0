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
import random
import time
import requests


def generate_port_name():
    """
    Generate port name
    """
    port_guid = f'{random.randrange(16**16):016x}'
    port_num = random.randint(10, 99)
    return f'{port_guid}_{port_num}'


def test_exclude_list_rest_api():
    """
    Test exclude list via plugin REST API
    """
    print("\n") # Start tests output from new line

    url = "http://127.0.0.1:8977/excluded"

    excluded_ports = [
        (generate_port_name(), 0),  # Add forever
        (generate_port_name(), 30), # Add for 30 seconds
        (generate_port_name(), 0)   # Add forever
    ]

    # Get (empty) list content
    response = requests.get(url, timeout=5)
    assert response.status_code == http.client.OK
    assert all(char.isspace() for char in response.text)
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

    # Wait until second port TTL is expired
    ttl_seconds = excluded_ports[1][1]
    time.sleep(ttl_seconds + 1)

    # Test auto-remove of second port after TTL is expired
    response = requests.get(url, timeout=5)
    assert response.status_code == http.client.OK
    for (index, pair) in enumerate(excluded_ports):
        port_name = pair[0]
        if index == 1:
            assert port_name not in response.text
        else:
            assert port_name in response.text
    print("    - test: auto-remove of port from exclusion list after TTL is expired -- PASS")

    # Test forced remove of third port
    port_name = excluded_ports[2][0]
    response = requests.delete(url, data=json.dumps([port_name]), timeout=5)
    assert response.status_code == http.client.OK
    assert f'{port_name} removed' in response.text
    print("    - test: forced remove of port from exclusion list -- PASS")

    # Test exclusion list content
    response = requests.get(url, timeout=5)
    for (index, pair) in enumerate(excluded_ports):
        port_name = excluded_ports[index][0]
        if index == 1 or index == 2:
            assert port_name not in response.text
        else:
            assert port_name in response.text
    print("    - test: exclusion list content -- PASS")


if __name__ == '__main__':
    test_exclude_list_rest_api()
