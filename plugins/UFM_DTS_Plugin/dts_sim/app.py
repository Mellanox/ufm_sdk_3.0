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

import os
import sys
sys.path.append(os.getcwd())
sys.path.insert(0, os.path.abspath(__file__)[:os.path.abspath(__file__).rfind('ufm_sdk_3.0')] + 'ufm_sdk_3.0')
from utils.flask_server import run_api
from utils.flask_server.base_flask_api_app import BaseFlaskAPIApp
from api.json import JSONAPI


if __name__ == '__main__':

    routes_map = {
        "/json": JSONAPI().application
    }
    app = BaseFlaskAPIApp(routes_map)
    run_api(app=app, port_number=9551)
