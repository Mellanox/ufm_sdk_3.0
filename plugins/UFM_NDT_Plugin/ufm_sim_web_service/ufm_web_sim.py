"""
@copyright:
    Copyright (C) Mellanox Technologies Ltd. 2021. ALL RIGHTS RESERVED.

    This software product is a proprietary product of Mellanox Technologies
    Ltd. (the "Company") and all right, title, and interest in and to the
    software product, including all associated intellectual property rights,
    are and shall remain exclusively with the Company.

    This software product is governed by the End User License Agreement
    provided with the software product.

@author: Nahum Kilim
@date:   September 20, 2021
"""

import configparser
from flask import Flask
from flask_restful import Api
import logging
import os
from apscheduler.schedulers.background import BackgroundScheduler

from twisted.web.wsgi import WSGIResource
from twisted.internet import reactor
from twisted.web import server

from resources import Compare, Ndts, Reports, ReportId, UploadMetadata, Delete, Cancel


class UFMWebSim:

    def __init__(self):
        self.port_number = 8980
        self.app = Flask(__name__)
        api = Api(self.app)
        log_level = logging.INFO
        ndt_config = configparser.ConfigParser()
        scheduler = BackgroundScheduler()
        # config_file_name = "/config/ndt.conf"
        config_file_name = "../build/config/ndt.conf"
        if os.path.exists(config_file_name):
            ndt_config.read(config_file_name)
            log_level = ndt_config.get("Common", "log_level",
                                       fallback=logging.INFO)
        logging.basicConfig(filename="/tmp/ndt.log",
                            level=logging.getLevelName(log_level))
        # logging.basicConfig(filename="/data/ndt.log",
        #                     level=logging.getLevelName(log_level))

        default_apis = {
            Ndts: "/list",
            Reports: "/reports",
            Delete: "/delete",
            UploadMetadata: "/upload_metadata",
            ReportId: "/reports/<report_id>",
        }
        for resource, path in default_apis.items():
            api.add_resource(resource, path)

        scheduler_apis = {
            Compare: "/compare",
            Cancel: "/cancel",
        }
        for resource, path in scheduler_apis.items():
            api.add_resource(resource, path, resource_class_kwargs={'scheduler': scheduler})

    async def run(self):
        self.app.run(port=self.port_number, debug=True)
        # resource = WSGIResource(reactor, reactor.getThreadPool(), self.app)
        # reactor.listenTCP(self.port_number, server.Site(resource))
        # reactor.run()

    async def stop(self):
        pass
