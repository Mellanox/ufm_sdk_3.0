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

from http import HTTPStatus
from flask import make_response
from api import InvalidConfRequest
from utils.logger import LOG_LEVELS, Logger
from utils.flask_server.base_flask_api_server import BaseAPIApplication


class InventoryAPI(BaseAPIApplication):
    def __init__(self):
        super(InventoryAPI, self).__init__()

    def _get_error_handlers(self):
        return [
            (InvalidConfRequest,
             lambda e: (str(e), HTTPStatus.BAD_REQUEST))
        ]

    def _get_routes(self):
        return {
            self.get: dict(urls=["/"], methods=["GET"]),
            self.get_firmware: dict(urls=["/firmware"], methods=["GET"]),
            self.get_memory: dict(urls=["/memory"], methods=["GET"]),
            self.get_cpu: dict(urls=["/cpu"], methods=["GET"])

        }

    def get(self):
        try:
            return make_response({
                "timestamp": 1669109706.1853793,
                "hostname": "c-237-153-80-083-bf2",
                "cpu_arch": "aarch64",
                "cpu_nos": "1",
                "cpu_model": "Cortex-A72",
                "cpu_max_freq": "1999 MHz",
                "os_name": "Ubuntu",
                "os_version": "20.04.4 LTS (Focal Fossa)",
                "os_version_id": "20.04",
                "asic_model": "BlueField-2 integrated ConnectX-6 Dx network controller (rev 01)",
                "asic_vendor": "Mellanox Technologies",
                "asic_serial_number": "MT2132X06829"
            })
        except Exception as e:
            Logger.log_message("Error occurred : " + str(e), LOG_LEVELS.ERROR)

    def get_firmware(self):
        try:
            return make_response(
                {
                    "timestamp": 1669109706.1853793,
                    "hostname": "c-237-153-80-083-bf2",
                    "id": "firmware",
                    "class": "memory",
                    "claimed": True,
                    "description": "BIOS",
                    "vendor": "https://www.mellanox.com",
                    "physid": "0",
                    "version": "BlueField:3.9.2-4-gf2113bc",
                    "date": "Jul 25 2022",
                    "units": "bytes",
                    "size": 1048576,
                    "capacity": 4194304,
                    "capabilities": {
                        "pci": "PCI bus",
                        "upgrade": "BIOS EEPROM can be upgraded",
                        "bootselect": "Selectable boot path",
                        "int14serial": "INT14 serial line control",
                        "acpi": "ACPI",
                        "uefi": "UEFI specification is supported"
                    }
                })
        except Exception as e:
            Logger.log_message("Error occurred : " + str(e), LOG_LEVELS.ERROR)

    def get_memory(self):
        try:
            return make_response({
                "timestamp": 1669109706.1853793,
                "hostname": "c-237-153-80-083-bf2",
                "id": "memory",
                "class": "memory",
                "claimed": True,
                "handle": "DMI:000D",
                "description": "System Memory",
                "physid": "d",
                "slot": "System board or motherboard",
                "units": "bytes",
                "size": 17179869184,
                "configuration": {
                    "errordetection": "multi-bit-ecc"
                }
            })
        except Exception as e:
            Logger.log_message("Error occurred : " + str(e), LOG_LEVELS.ERROR)

    def get_cpu(self):
        try:
            return make_response({
                "timestamp": 1669109706.1853793,
                "hostname": "c-237-153-80-083-bf2",
                "id": "cpu",
                "class": "processor",
                "claimed": True,
                "handle": "DMI:0004",
                "description": "CPU",
                "product": "ARMv8 (OPN: MBF2M516A-EEEO)",
                "vendor": "https://www.mellanox.com",
                "physid": "4",
                "businfo": "cpu@0",
                "version": "Mellanox BlueField-2 [A1] A72(D08) r1p0",
                "serial": "Unspecified Serial Number",
                "slot": "Socket 0",
                "units": "Hz",
                "size": 1999000000,
                "capacity": 1999000000,
                "clock": 200000000,
                "configuration": {
                    "cores": "8",
                    "enabledcores": "8"
                },
                "capabilities": {
                    "lm": "64-bit capable"
                }
            })
        except Exception as e:
            Logger.log_message("Error occurred : " + str(e), LOG_LEVELS.ERROR)
