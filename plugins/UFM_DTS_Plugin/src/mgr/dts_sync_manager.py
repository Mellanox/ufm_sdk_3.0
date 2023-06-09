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
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from utils.singleton import Singleton
from utils.utils import Logger, LOG_LEVELS
import requests
from constants.data_model_constants import DataModelConstants, MESSAGE_TYPES_HASH_MAP, MESSAGE_TYPES


class DTSConnectionErr(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)


class DTSSyncManager(Singleton):
    def __init__(self, dataMgr):
        self.endpoints = []
        self.dataMgr = dataMgr
        self.scheduler = BackgroundScheduler()
        self.get_endpoints()
        self.start_scheduler(self.sync_with_endpoints, 30)

    def start_scheduler(self, streaming_func, streaming_interval):

        streaming_job = self.scheduler.add_job(streaming_func, 'interval',
                                                    seconds=streaming_interval,
                                                    next_run_time=datetime.now())
        if not self.scheduler.running:
            self.scheduler.start()

        return streaming_job.id
    def get_endpoints(self):
        with open(os.path.join('conf', 'endpoints.json'), 'r') as f:
            self.endpoints = json.load(f)

    def sync_with_endpoints(self):
        for endpoint in self.endpoints:
            self.sync_with_endpoint(endpoint)

    def sync_with_endpoint(self, end_point):
        print(end_point)
        if self.dataMgr.Hosts == {}:  # Hosts is empty that's mean we need to get all data and fill it in the Hosts
            # we need this check to avoid sending requests for each host individually
            print('fill Hosts with data')
            self.update_endpoint_node_info(end_point)
        else:
            for msg_type in MESSAGE_TYPES:
                if msg_type.value in MESSAGE_TYPES_HASH_MAP:  # this message_type use hash for change detection.
                    # each time the data is changed the hash value will be changed too. so here the hash value
                    # will be checked if it is changed before updating the data
                    hash_data = self.get_endpoint_node_info(end_point, MESSAGE_TYPES_HASH_MAP[msg_type.value])
                    for hash_host in hash_data:
                        if not self.compare_hash_data(hash_host, msg_type):
                            print(f'{msg_type.value} need to be update')
                            print(f'update {msg_type.value}')
                            self.update_endpoint_node_info(end_point, msg_type.value)
                            self.update_endpoint_node_info(end_point, MESSAGE_TYPES_HASH_MAP[msg_type.value], hash_data)
                            break  # if there is a change in hash then update all data and break the loop
                else:
                    print(f'update {msg_type.value}')
                    self.update_endpoint_node_info(end_point, msg_type.value)
        print("--------------------------------------")

    def compare_hash_data(self, hash_host, msg_type):
        model_hash_host = self.dataMgr.get_host_data(hash_host[DataModelConstants.HOST_NAME],
                                                     MESSAGE_TYPES_HASH_MAP[msg_type.value])
        if not model_hash_host or model_hash_host == {}:
            return False
        model_host_msg = self.dataMgr.get_host_message(model_hash_host)
        host_msg = self.dataMgr.get_host_message(hash_host)
        if not model_host_msg or not host_msg or model_host_msg[DataModelConstants.HASH] != host_msg[DataModelConstants.HASH]:
            return False
        return True

    def get_endpoint_node_info(self, end_point, message_type=None):
        node_endpoint = f'{end_point}/json/python_dict'
        if message_type:
            node_endpoint = f'{node_endpoint}?message_type={message_type}'
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
        return json.loads(response.text)

    def update_endpoint_node_info(self, end_point, message_type=None, data_list=None):
        if not data_list:
            data_list = self.get_endpoint_node_info(end_point, message_type)
        for data in data_list:
            self.dataMgr.add_host_data(data[DataModelConstants.HOST_NAME], data[DataModelConstants.MESSAGE_TYPE], data)
