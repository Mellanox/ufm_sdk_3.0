#
# Copyright © 2013-2023 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
#

import logging
import http
from constants import PDRConstants as Constants
import requests

class UFMCommunicator:
    """
    communicate with the UFM, send actions to the UFM, see that ports isolated.
    """

    def __init__(self, host='127.0.0.1', ufm_port=8000):
        #TODO: read from conf
        self.internal_port = ufm_port
        self.ufm_protocol = "http"
        self.headers = {"X-Remote-User": "ufmsystem"}
        #self.suffix = None
        self._host = f"{host}:{self.internal_port}"

    def get_request(self, uri, headers=None):
        request = self.ufm_protocol + '://' + self._host + uri
        if not headers:
            headers = self.headers
        try:
            response = requests.get(request, verify=False, headers=headers,timeout=Constants.TIMEOUT)
            logging.info("UFM API Request Status: %s, URL: %s",response.status_code, request)
            if response.status_code == http.client.OK:
                return response.json()
        except ConnectionRefusedError as connection_error:
            logging.error("failed to get data from %s with error %s",request,connection_error)
        return None

    def send_request(self, uri, data, method=Constants.POST_METHOD, headers=None):
        request = self.ufm_protocol + '://' + self._host + uri
        if not headers:
            headers = self.headers
        if method == Constants.POST_METHOD:
            response = requests.post(url=request, json=data, verify=False, headers=headers,timeout=Constants.TIMEOUT)
        elif method == Constants.PUT_METHOD:
            response = requests.put(url=request, json=data, verify=False, headers=headers,timeout=Constants.TIMEOUT)
        elif method == Constants.DELETE_METHOD:
            response = requests.delete(url=request, verify=False, headers=headers,timeout=Constants.TIMEOUT)
        else:
            return None
        logging.info("UFM API Request Status: %s, URL: %s",response.status_code, request)
        return response

    def send_event(self, message, event_id=Constants.EXTERNAL_EVENT_NOTICE,
                    external_event_name="PDR Plugin Event", external_event_type="PDR Plugin Event"):
        data = {
            "event_id": event_id,
            "description": message,
            "external_event_name": external_event_name,
            "external_event_type": external_event_type,
            "external_event_source": "PDR Plugin"

        }
        ret = self.send_request(Constants.POST_EVENT_REST, data)
        if ret:
            return True
        return False

    def get_isolated_ports(self):
        # GET /resources/isolated_ports
        # NOT IMPLEMENTED
        return self.get_request(Constants.GET_ISOLATED_PORTS)

    def isolate_port(self, port_name):
         # using isolation UFM REST API - PUT /ufmRestV2/app/unhealthy_ports
        data = {
            "ports": [port_name],
            "ports_policy": "UNHEALTHY",
            "action": "isolate"
            }
        return self.send_request(Constants.ISOLATION_REST, data, method=Constants.PUT_METHOD)

    def deisolate_port(self, port_name):
        # PUT
        # {
        # "ports": [
        #     "e41d2d0300062380_3"
        # ],
        # "ports_policy": "HEALTHY"
        # }
        data = {
            "ports": [port_name],
            "ports_policy": "HEALTHY",
            }
        return self.send_request(Constants.ISOLATION_REST, data, method=Constants.PUT_METHOD)

    def get_ports_metadata(self):
        return self.get_request(Constants.GET_ACTIVE_PORTS_REST)

    def get_port_metadata(self, port_name):
        return self.get_request(f"{Constants.GET_PORTS_REST}/ {port_name}")

    def reset_port(self, port_name, port_guid):
        """ 
        Reset port
        """
        # using isolation UFM REST API - POST /ufmRestV2/actions
        data = {
            "params": { "port_id": port_name },
            "action": "reset",
            "object_ids": [ port_guid ],
            "object_type": "System",
            "description": "",
            "identifier": "id"
        }
        return self.send_request(Constants.POST_ACTIONS_REST, data, method=Constants.POST_METHOD)
