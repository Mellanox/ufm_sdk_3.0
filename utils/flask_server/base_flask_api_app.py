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
# @date:   Sep 19, 2022
#

from werkzeug.middleware.dispatcher import DispatcherMiddleware

from utils.flask_server.base_flask_api_server import BaseAPIApplication


class BaseFlaskAPIApp(DispatcherMiddleware):

    def __init__(self, routes_app_map):

        frontend = BaseAPIApplication()
        super(BaseFlaskAPIApp, self).__init__(
            frontend.application, routes_app_map
        )
