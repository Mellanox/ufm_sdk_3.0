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
# @author: Haitham Jondi
# @date:   Nov 23, 2022
#
import os, json
from utils.singleton import Singleton
from utils.utils import Logger, LOG_LEVELS
import requests


class DTSConnectionErr(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)


class DTSSyncManager(Singleton):
    def __init__(self):
        self.endpoints = []
        with open(os.path.join('conf', 'endpoints.json'), 'r') as f:
            self.endpoints = json.load(f)
        self.sync_with_endpoint(self.endpoints[0])

    def sync_with_endpoint(self, end_point):
        print(end_point)
        self.update_endpoint_node_info(end_point)

    def update_endpoint_node_info(self, end_point):
        node_endpoint = end_point + '/json/python_dict?message_type=Node'
        try:
            Logger.log_message(f'Polling the DTS endpoint node metrics: {node_endpoint}', LOG_LEVELS.DEBUG)
            response = requests.get(node_endpoint)
            Logger.log_message(f'DTS metrics Request Status [ {str(response.status_code)} ]',
                               LOG_LEVELS.DEBUG)
            response.raise_for_status()
        except ConnectionError as ec:
            err_msg = f'Failed to connect to DTS endpoint: {node_endpoint}'
            raise DTSConnectionErr(err_msg)
        except Exception as ex:
            raise ex
        print(response.text)

    def update_endpoint_inventory(self, end_point):
        pass

    def update_endpoint_package_info(self, end_point):
        pass

    def update_endpoint_resource_utilization_info(self, end_point):
        pass
