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

import os
import sys
sys.path.append(os.getcwd())

from utils.utils import Utils
from utils.flask_server import run_api
from utils.flask_server.base_flask_api_app import BaseFlaskAPIApp
from api.conf_api import UFMBrightPluginConfigurationsAPI

if __name__ == '__main__':
    try:
        plugin_port = Utils.get_plugin_port(
            port_conf_file='/config/bright_httpd_proxy.conf',
            default_port_value=8985)

        routes = {
            "/conf": UFMBrightPluginConfigurationsAPI().application
        }

        app = BaseFlaskAPIApp(routes)
        run_api(app=app,port_number= plugin_port)

    except Exception as ex:
        pass
