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
from utils.singleton import Singleton
from constants.data_model_constants import DataModelConstants, MESSAGE_TYPES, MESSAGE_TYPES_HASH

class DataModel(Singleton):
    def __init__(self):
        self.Hosts = {}

    def add_host_if_not_exist(self, host_name):
        if not host_name in self.Hosts:
            self.Hosts[host_name] = {}
            for msg_type in (list(MESSAGE_TYPES) + list(MESSAGE_TYPES_HASH)):
                self.Hosts[host_name][msg_type.value] = ''

    def add_host_data(self, host_name, message_type, data):
        self.add_host_if_not_exist(host_name)
        self.Hosts[host_name][message_type] = data

    def get_host_data(self, host_name, message_type):
        result = {}
        if host_name in self.Hosts:
            if message_type in self.Hosts[host_name]:
                result = self.Hosts[host_name][message_type]
        return result

    def get_hosts_list(self):
        return list(self.Hosts.keys())

    def get_package_info(self, host_name):
        package_info = []
        if host_name in self.Hosts and MESSAGE_TYPES.PACKAGE_INFO.value in self.Hosts[host_name]:
            # Package info contain more than one item in message that why we couldn't use get_host_message
            package_info = self.Hosts[host_name][MESSAGE_TYPES.PACKAGE_INFO.value][DataModelConstants.MESSAGE]
        return package_info

    def get_host_message(self, host):
        msg = None
        if DataModelConstants.MESSAGE in host and len(host[DataModelConstants.MESSAGE]):
            # all message contain only one item except PackageIngo
            msg = host[DataModelConstants.MESSAGE][0]
        return msg

    def get_inventory_data(self):
        inventory_data = []
        for hostname in self.Hosts:
            if MESSAGE_TYPES.INVENTORY.value in self.Hosts[hostname]:
                inventory = self.Hosts[hostname][MESSAGE_TYPES.INVENTORY.value]
                msg = self.get_host_message(inventory)
                host_data = {
                    DataModelConstants.TIMESTAMP: msg[DataModelConstants.TIMESTAMP],
                    DataModelConstants.HOST_NAME: msg[DataModelConstants.HOST_NAME],
                    DataModelConstants.CPU_ARCH: msg[DataModelConstants.CPU_ARCH],
                    DataModelConstants.CPU_NOS: msg[DataModelConstants.CPU_NOS],
                    DataModelConstants.CPU_MODEL: msg[DataModelConstants.CPU_MODEL],
                    DataModelConstants.CPU_MAX_FREQ: msg[DataModelConstants.CPU_MAX_FREQ],
                    DataModelConstants.OS_NAME: msg[DataModelConstants.OS_NAME],
                    DataModelConstants.OS_VERSION: msg[DataModelConstants.OS_VERSION],
                    DataModelConstants.OS_VERSION_ID: msg[DataModelConstants.OS_VERSION_ID],
                    DataModelConstants.ASIC_MODEL: msg[DataModelConstants.ASIC_MODEL],
                    DataModelConstants.ASIC_VENDOR: msg[DataModelConstants.ASIC_VENDOR],
                    DataModelConstants.ASIC_SERIAL_NUMBER: msg[DataModelConstants.ASIC_SERIAL_NUMBER]
                }
                inventory_data.append(host_data)

        return inventory_data

    def get_memory_data(self, id):
        memory_data = []
        for hostname in self.Hosts:
            if MESSAGE_TYPES.INVENTORY.value in self.Hosts[hostname]:
                inventory_data = self.Hosts[hostname][MESSAGE_TYPES.INVENTORY.value]
                msg = self.get_host_message(inventory_data)
                if DataModelConstants.MEMORY_DATA in msg:
                    data = [x for x in msg[DataModelConstants.MEMORY_DATA] if x[DataModelConstants.ID] == id]
                    memory_data.extend(data)
        return memory_data

    def get_cpu_data(self):
        cpu_data = []
        for hostname in self.Hosts:
            if MESSAGE_TYPES.INVENTORY.value in self.Hosts[hostname]:
                inventory_data = self.Hosts[hostname][MESSAGE_TYPES.INVENTORY.value]
                msg = self.get_host_message(inventory_data)
                if DataModelConstants.CPU_DATA in msg:
                    cpu_data.extend(msg[DataModelConstants.CPU_DATA])
        return cpu_data
