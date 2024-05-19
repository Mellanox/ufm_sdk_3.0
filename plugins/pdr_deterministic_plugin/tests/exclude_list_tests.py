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
import os
import tempfile
import time
import pytest
import requests
from constants import PDRConstants as Constants
from exclude_list import ExcludeList, ExcludeListItem
from isolation_algo import create_logger

# Temp 4

def get_logger():
    """
    Return logger associated with log file in temporary directory
    """
    log_name = os.path.basename(Constants.LOG_FILE)
    log_path = os.path.join(tempfile.gettempdir(), log_name)
    return create_logger(log_path)

pytest.mark.run(order=0)
def test_exclude_list_class_methods():
    """
    Test exclude list class methods by direct calls
    """
    excluded_ports = [
        ExcludeListItem("0123456789aaabbb_1", 0),  # Add forever
        ExcludeListItem("9876543210cccddd_2", 30), # Add for 30 seconds
        ExcludeListItem("3456789012eeefff_3", 0)   # Add forever
    ]

    # Create exclude list and ensure it's empty
    exclude_list = ExcludeList(get_logger())
    items = exclude_list.items()
    assert not items

    # Add ports to excluded list
    for port in excluded_ports:
        exclude_list.add(port.port_name, port.ttl_seconds)

    # Test excluded list size
    items = exclude_list.items()
    assert items and len(items) == len(excluded_ports)

    # Test 'contains' method
    for port in excluded_ports:
        assert exclude_list.contains(port.port_name)

    # Test excluded list content
    for (index, item) in enumerate(items):
        assert item.port_name == excluded_ports[index].port_name
        assert item.ttl_seconds == excluded_ports[index].ttl_seconds

    # Test auto-remove of second port after TTL is expired
    auto_remove_port = excluded_ports[1]
    time.sleep(auto_remove_port.ttl_seconds + 1)
    assert not exclude_list.contains(auto_remove_port.port_name)

    # Test excluded list size
    items = exclude_list.items()
    assert items and len(items) == (len(excluded_ports) - 1)

    # Test excluded list content
    for port in excluded_ports:
        if port.port_name != auto_remove_port.port_name:
            assert exclude_list.contains(port.port_name)

    # Test forced remove of third port
    remove_port = excluded_ports[2]
    exclude_list.remove(port.port_name)
    assert not exclude_list.contains(remove_port.port_name)

    # Test excluded list size
    items = exclude_list.items()
    assert items and len(items) == (len(excluded_ports) - 2)

    # Test excluded list content
    for port in excluded_ports:
        if port.port_name != remove_port.port_name and port.port_name != auto_remove_port.port_name:
            assert exclude_list.contains(port.port_name)

#pytest.mark.run(order=1)
def no_test_exclude_list_rest_api():
    """
    Test exclude list inside plugin via REST API
    """
    url = "http://127.0.0.1:8977/excluded"

    excluded_ports = [
        ExcludeListItem("0123456789aaabbb_1", 0),  # Add forever
        ExcludeListItem("9876543210cccddd_2", 30), # Add for 30 seconds
        ExcludeListItem("3456789012eeefff_3", 0)   # Add forever
    ]

    # Prepare data for PUT HTTP request
    data = []
    for port in excluded_ports:
        data.append([port.port_name, port.ttl_seconds])

    # Add ports to excluded list
    response = requests.put(url, data=json.dumps(data), headers={'Content-Type': 'application/json'}, timeout=5, auth = None, verify = False)
    assert response.status_code == http.client.OK

if __name__ == '__main__':
    test_exclude_list_class_methods()
    #no_test_exclude_list_rest_api()
