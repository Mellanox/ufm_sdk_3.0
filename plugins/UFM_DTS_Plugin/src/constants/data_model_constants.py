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
from enum import Enum


class MESSAGE_TYPES(Enum):
    INVENTORY = 'Inventory'
    NODE = 'Node'
    PACKAGE_INFO = 'PackageInfo'
    RESOURCE_UTIL = 'ResourceUtil'


class MESSAGE_TYPES_HASH(Enum):
    PACKAGE_INFO_HASH = 'PackageInfoHash'
    INVENTORY_HASH = 'InventoryHash'


MESSAGE_TYPES_HASH_MAP = {
    MESSAGE_TYPES.INVENTORY.value: MESSAGE_TYPES_HASH.INVENTORY_HASH.value,
    MESSAGE_TYPES.PACKAGE_INFO.value: MESSAGE_TYPES_HASH.PACKAGE_INFO_HASH.value
}


class DataModelConstants:
    HOST_NAME = 'hostname'
    MESSAGE_TYPE = 'message_type'
    TIMESTAMP = 'timestamp'
    CPU_ARCH = 'cpu_arch'
    CPU_NOS = 'cpu_nos'
    CPU_MODEL = 'cpu_model'
    CPU_MAX_FREQ = 'cpu_max_freq'
    OS_NAME = 'os_name'
    OS_VERSION = 'os_version'
    OS_VERSION_ID = 'os_version_id'
    ASIC_MODEL = 'asic_model'
    ASIC_VENDOR = 'asic_vendor'
    ASIC_SERIAL_NUMBER = 'asic_serial_number'
    MESSAGE = 'message'
    MEMORY_DATA = 'memory_data'
    CPU_DATA = 'cpu_data'
    HASH = 'hash'
    ID = 'id'
