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
from exclude_list import ExcludeListItem


pytest.mark.run(order=0)
def test_exclude_list_rest_api():
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
    test_exclude_list_rest_api()
