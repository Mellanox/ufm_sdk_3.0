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
# @author: Anan Al-Aghbar
# @date:   Nov 09, 2022
#
from http import HTTPStatus
from flask import Response
from requests.exceptions import ConnectionError
from utils.flask_server.base_flask_api_server import BaseAPIApplication
from utils.utils import Logger, LOG_LEVELS
import requests
import re


class UFMConnectionErr(Exception):

    def __init__(self, message):
        Exception.__init__(self, message)


class TelemetryConnectionErr(Exception):

    def __init__(self, message):
        Exception.__init__(self, message)


class PortLabelObj:
    def __init__(self, data):
        for attr_name, attr_value in data.items():
            self.__setattr__(attr_name, attr_value or "")


class MetricLabelsGeneratorAPI(BaseAPIApplication):

    def __init__(self, conf):
        super(MetricLabelsGeneratorAPI, self).__init__()
        self.conf = conf
        self.labels_hash = ''
        self.ports_labels_string_map = {}

    def _get_error_handlers(self):
        return [
            (UFMConnectionErr,
             lambda e: (str(e), HTTPStatus.BAD_REQUEST)),
            (TelemetryConnectionErr,
             lambda e: (str(e), HTTPStatus.BAD_REQUEST))
        ]

    def _get_routes(self):
        return {
            self.get: dict(urls=["/enterprise"], methods=["GET"])
        }

    def _get_metrics(self):
        telemetry_endpoint_url = f'http://{self.conf.get_telemetry_host()}:{self.conf.get_telemetry_port()}' \
                                 f'/{self.conf.get_telemetry_url()}'
        try:
            Logger.log_message(f'Polling the UFM telemetry metrics: {telemetry_endpoint_url}', LOG_LEVELS.DEBUG)
            response = requests.get(telemetry_endpoint_url)
            Logger.log_message(f'UFM telemetry metrics Request Status [ {str(response.status_code)} ]', LOG_LEVELS.DEBUG)
            response.raise_for_status()
            return response.text
        except ConnectionError as ec:
            err_msg = f'Failed to connect to UFM Telemetry: {telemetry_endpoint_url}'
            raise TelemetryConnectionErr(err_msg)
        except Exception as ex:
            raise ex

    def _get_ufm_labels(self):
        headers = {
            "X_REMOTE_USER": "admin"
        }
        fabric_snapshot_url = f'http://127.0.0.1:{self.conf.get_ufm_rest_server_port()}' \
                              f'/app/fabric_snapshot?tag=grafana&output=json&levels=true&hash=%s'

        url = fabric_snapshot_url % self.labels_hash
        try:
            Logger.log_message(f'Polling the UFM Labels: {url}', LOG_LEVELS.DEBUG)
            response = requests.get(url=url, headers=headers)
            Logger.log_message(f'UFM Labels Request Status [ {str(response.status_code)} ]', LOG_LEVELS.DEBUG)
            response.raise_for_status()
            return response.json()
        except ConnectionError as ce:
            err_msg = f'Failed to connect to UFM on port: {self.conf.get_ufm_rest_server_port()}'
            raise UFMConnectionErr(err_msg)
        except Exception as ex:
            raise ex


    def _get_port_id(self, port_id, device_type):
        # port_id -> port_guid_port_num
        # in case hosts the port_id should be only the port_guid,
        # because port_num in the telemetry is different from the ufm
        #####
        # in case switches the port_id should be port_guid_port_num,
        # all ports are sharing the same port_guid with different port_num
        return port_id if device_type == "switch" or device_type == 'router' else port_id.split('_')[0]

    def _update_labels(self):
        labels_response = self._get_ufm_labels()
        new_hash = labels_response.get("hash")
        if new_hash != self.labels_hash:
            self.labels_hash = new_hash
            for port in labels_response.get("labels"):
                port_label_obj = PortLabelObj(port)
                status = port_label_obj.status
                if status == "R":
                    # the port is removed from the fabric-> remove it from the map
                    # removed port_label_obj doesn't include the device_type
                    # port_id could be port_label_obj.port_id in case of switches
                    # port_id could be port_label_obj.port_id.split('_')[0] in case of hosts
                    # need to try both options
                    try:
                        del self.ports_labels_string_map[port_label_obj.port_id]
                    except KeyError as ex:
                        del self.ports_labels_string_map[port_label_obj.port_id.split('_')[0]]
                else:
                    port_id = self._get_port_id(port_label_obj.port_id, port_label_obj.device_type)
                    self.ports_labels_string_map[port_id] = \
                        '{device_name="%s",device_type="%s",fabric="compute",hostname="%s",' \
                        'level="%s",node_desc="%s",peer_level="%s",port_id="%s"}' % (
                        port_label_obj.device_name if port_label_obj.device_type == 'switch' else '',
                        port_label_obj.device_type,
                        port_label_obj.device_name if port_label_obj.device_type == 'host' else '',
                        port_label_obj.level,port_label_obj.node_desc,port_label_obj.peer_level,port_label_obj.port_id
                    )

    def get(self):
        try:
            self._update_labels()
            response = self._get_metrics()
            labels_regex = r'\{.*?\}'
            port_guid_regex = r'(?<=port_guid=)"0x([^"]*)"'
            port_num_regex = r'(?<=port_num=)"([^"]*)"'
            lines = []
            for line in response.split("\n"):
                port_guid = re.findall(port_guid_regex, line)
                if len(port_guid) == 1:
                    port_num = re.findall(port_num_regex, line)
                    if len(port_num) == 1:
                        port_guid = port_guid[0]
                        port_num = port_num[0]
                        new_labels_string = self.ports_labels_string_map.get(port_guid)
                        if new_labels_string is None:
                            port_id = f'{port_guid}_{port_num}'
                            new_labels_string = self.ports_labels_string_map.get(port_id)
                        if new_labels_string is not None:
                            line = re.sub(labels_regex, new_labels_string, line)
                            lines.append(line)
                        # else:
                        # the telemetry won't remove the down ports
                        #     Logger.log_message(f'Failed to get labels of the port: {port_guid}', LOG_LEVELS.WARNING)
                else:
                    lines.append(line)
            return Response("\n".join(lines), mimetype="text/plain")
        except Exception as ex:
            Logger.log_message(f'Failed to get UFM telemetry metrics with labels due to: {str(ex)}', LOG_LEVELS.ERROR)
            raise ex
