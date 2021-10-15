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

from twisted.web.wsgi import WSGIResource
from twisted.internet import reactor
from twisted.web import server

from resources import Compare, Ndts, Reports, ReportId, UploadMetadata, Delete


class UFMWebSim:

    def __init__(self):
        self.port_number = 8980
        self.app = Flask(__name__)
        api = Api(self.app)
        log_level = logging.INFO
        ndt_config = configparser.ConfigParser()
        # config_file_name = "/config/ndt.conf"
        config_file_name = "../build/config/ndt.conf"
        if os.path.exists(config_file_name):
            ndt_config.read(config_file_name)
            log_level = ndt_config.get("Common", "debug_level",
                                       fallback=logging.INFO)
        logging.basicConfig(filename="/tmp/ndt.log",
                            level=logging._nameToLevel[log_level])
        # logging.basicConfig(filename="/data/ndt.log",
        #                     level=logging._nameToLevel[log_level])

        apis = {
            Compare: "/plugin/ndt/compare",
            Ndts: "/plugin/ndt/list",
            Reports: "/plugin/ndt/reports",
            Delete: "/plugin/ndt/delete",
            UploadMetadata: "/plugin/ndt/upload_metadata",
            ReportId: "/plugin/ndt/reports/<report_id>",
        }
        for resource, path in apis.items():
            api.add_resource(resource, path)

    async def run(self):
        self.app.run(port=self.port_number, debug=True)
        # resource = WSGIResource(reactor, reactor.getThreadPool(), self.app)
        # reactor.listenTCP(self.port_number, server.Site(resource))
        # reactor.run()

    async def stop(self):
        pass
