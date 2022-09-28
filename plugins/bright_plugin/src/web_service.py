"""
@copyright:
    Copyright (C) 2013-2022 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.

    This software product is a proprietary product of Nvidia Corporation and its affiliates
    (the "Company") and all right, title, and interest in and to the software
    product, including all associated intellectual property rights, are and
    shall remain exclusively with the Company.

    This software product is governed by the End User License Agreement
    provided with the software product.

@author: Nasr Ajaj
@date:   Sep 11, 2022
"""


from werkzeug.middleware.dispatcher import DispatcherMiddleware

from api.bright_data_api import BrightDataAPI
from api.client_cert_api import ClientCertificateAPI
from api.conf_api import BrightConfigurationsAPI
from utils.base_api import BaseAPIApplication


class BrightAPI(DispatcherMiddleware):

    def __init__(self, config_parser):

        frontend = BaseAPIApplication()
        self.bright_conf = BrightConfigurationsAPI(config_parser)
        self.bright_data_api = BrightDataAPI(config_parser)
        self.bright_cert_api = ClientCertificateAPI()
        super(BrightAPI, self).__init__(
            frontend.application, {
                "/conf": self.bright_conf.application,
                "/bright": self.bright_data_api.application,
                "/cert": self.bright_cert_api.application
            }
        )