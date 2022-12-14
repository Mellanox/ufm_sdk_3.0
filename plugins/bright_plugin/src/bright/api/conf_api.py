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
# @date:   Dec 14, 2022
#
from flask import make_response
from utils.flask_server.base_flask_api_server import BaseAPIApplication


class UFMBrightPluginConfigurationsAPI(BaseAPIApplication):

    def __init__(self):
        super(UFMBrightPluginConfigurationsAPI, self).__init__()

    def _get_routes(self):
        return {
            self.get_conf: dict(urls=['/'], method=["GET"]),
            self.update_conf: dict(urls=['/'], method=["PUT"])
        }

    def get_conf(self):
        # TBD: implementation to get the current conf values
        return make_response("bright configurations")

    def update_conf(self):
        # TBD: implementation to set the current conf values
        return make_response("bright configurations")