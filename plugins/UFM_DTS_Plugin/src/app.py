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


from utils.flask_server import run_api
from utils.flask_server.base_flask_api_app import BaseFlaskAPIApp
from mgr.data_model import DataModel
from mgr.data_mock_loader import DataMockLoader
from mgr.dts_sync_manager import DTSSyncManager
from api.conf_api import DTSConfigurationsAPI
from api.package_info import PackageInfoAPI
from api.inventory import InventoryAPI


if __name__ == '__main__':


    routes_map = {
        "/conf": DTSConfigurationsAPI().application,
        "/package_info": PackageInfoAPI().application,
        "/inventory": InventoryAPI().application
    }
    dts_sync_manager = DTSSyncManager.getInstance()
    dataMockMgr = DataMockLoader.getInstance()
    dataMgr = DataModel.getInstance()
    dataMockMgr.set_data()
    #print (dataMgr.get_package_info("c-237-153-80-083-bf2"))
    app = BaseFlaskAPIApp(routes_map)
    run_api(app=app, port_number=8687)
