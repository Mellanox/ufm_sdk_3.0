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
import http
import pandas as pd
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
        if response.status_code == http.client.OK:
            return response.json()
        else:
            return
    
    def send_request(self, uri, data, method=Constants.POST_METHOD, headers=None):
        request = self.ufm_protocol + '://' + self._host + uri
        if not headers:
            headers = self.headers
        if method == Constants.POST_METHOD:
            response = requests.post(url=request, json=data, verify=False, headers=headers)
        elif method == Constants.PUT_METHOD:
            response = requests.put(url=request, json=data, verify=False, headers=headers)
        elif method == Constants.DELETE_METHOD:
            response = requests.delete(url=request, verify=False, headers=headers)
        logging.info("UFM API Request Status: {}, URL: {}".format(response.status_code, request))
        return response

    def get_telemetry(self, port, instance_name,test_mode):
        if test_mode:
            url = f"http://127.0.0.1:9090/csv/xcset/simulated_telemetry"
        else:
            url = f"http://127.0.0.1:{port}/csv/xcset/{instance_name}"
        try:
            telemetry_data = pd.read_csv(url)
        except Exception as e:
            logging.error(f"Failed to get telemetry data from UFM, fetched url={url}. Error: {e}")
            telemetry_data = None
        return telemetry_data
    
    def send_event(self, message, event_id=Constants.EXTERNAL_EVENT_NOTICE, external_event_name="PDR Plugin Event", external_event_type="PDR Plugin Event"):
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
        return self.get_request("%s/%s" % (Constants.GET_PORTS_REST, port_name))

    def start_dynamic_session(self, instance_name, counters, sample_rate, guids, extra_configuration=None):
        data = {
            "counters": counters,
            "sample_rate": sample_rate,
            "requested_guids": guids,
            }
        if extra_configuration:
            data["configuration"] = extra_configuration
        return self.send_request(Constants.DYNAMIC_SESSION_REST % instance_name, data, method=Constants.POST_METHOD)

    def update_dynamic_session(self, instance_name, sample_rate, guids):
        data = {
            "sample_rate": sample_rate,
            "requested_guids": guids
            }
        return self.send_request(Constants.DYNAMIC_SESSION_REST % instance_name, data, method=Constants.PUT_METHOD)

    def running_dynamic_session(self, instance_name):
        response = self.get_request(Constants.STATUS_DYNAMIC_SESSION_REST)
        if response:
            instance_status = response.get(instance_name)
            if instance_status and instance_status.get("status") == "running":
                return True
        return False

    def stop_dynamic_session(self, instance_name):
        data = {}
        return self.send_request(Constants.DYNAMIC_SESSION_REST % instance_name, data, method=Constants.DELETE_METHOD)

    def dynamic_session_get_port(self, instance_name):
        data = self.get_request(Constants.DYNAMIC_SESSION_REST % instance_name)
        if data:
            return data.get("endpoint_port")
