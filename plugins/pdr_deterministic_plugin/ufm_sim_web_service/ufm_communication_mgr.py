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

from constants import PDRConstants as Constants
import requests
import logging
import copy


class UFMCommunicator:

    def __init__(self, host='127.0.0.1', ufm_port=8000):
        #TODO: read from conf
        self.internal_port = ufm_port
        self.ufm_protocol = "http"
        self.headers = {"X-Remote-User": "ufmsystem"}
        #self.suffix = None
        self._host = "{0}:{1}".format(host, self.internal_port)
    
    def get_request(self, uri, headers=None):
        request = self.ufm_protocol + '://' + self._host + uri
        if not headers:
            headers = self.headers
        response = requests.get(request, verify=False, headers=headers)
        logging.info("UFM API Request Status: {}, URL: {}".format(response.status_code, request))
        if response.status_code == 200:
            return response.json()
        else:
            return
    
    def post_request(self, uri, data, post=True, headers=None):
        request = self.ufm_protocol + '://' + self._host + uri
        if not headers:
            headers = self.headers
        if post:
            response = requests.post(url=request, json=data, verify=False, headers=headers)
        else:
            response = requests.put(url=request, json=data, verify=False, headers=headers)
        logging.info("UFM API Request Status: {}, URL: {}".format(response.status_code, request))
        return response

    def get_telemetry(self):
        # returns dictionary port_name: telemetry data ({"counter_name": value})
        telemetry_data = self.get_request(Constants.GET_SESSION_DATA_REST)
        if not telemetry_data:
            return
        else:
            return telemetry_data
    
    def send_event(self, message):
        data = {}
        data["event_id"] = 666
        data["description"] = message
        data["object_name"] = "PDR Plugin Event"
        ret = self.post_request(Constants.POST_EVENT_REST, data)
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
        return self.post_request(Constants.ISOLATION_REST, data, post=False)

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
        return self.post_request(Constants.ISOLATION_REST, data, post=False)


