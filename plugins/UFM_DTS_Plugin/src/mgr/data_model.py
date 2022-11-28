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


class DataModel(Singleton):
    def __init__(self):
        self.Hosts = {}

    def add_host_if_not_exist(self, host_name):
        if not host_name in self.Hosts:
            self.Hosts[host_name] = {
                "package_info": ""
            }

    def add_package_info(self, host_name, package_info):
        self.add_host_if_not_exist(host_name)
        self.Hosts[host_name]["package_info"] = package_info

    def get_package_info(self, host_name):
        result = {}
        if host_name in self.Hosts:
            if 'package_info' in self.Hosts[host_name]:
                result = self.Hosts[host_name]["package_info"]
        return result

