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
import os
import logging

from flask import Flask
from flask_restful import Api
from logging.handlers import RotatingFileHandler

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ProcessPoolExecutor

from resources import UFMResource, QueryRequest, Queries, QueryId,\
    Delete, Cancel, Version, Help, Dummy


class UFMWebSim:
    
    def __init__(self):
        self.log_level = logging.INFO
        self.log_file_max_size = 10240000
        self.log_file_path = "/log/sysinfo.log"
        self.log_file_backup_count = 5
        self.port_number = 8999
        self.app = Flask(__name__)
        self.api = Api(self.app)

        self.scheduler = BackgroundScheduler(timezone="Asia/Jerusalem")
        self.parse_config()
        self.scheduler.start()
        self.init_apis()

    def parse_config(self):
        config_file = configparser.ConfigParser()
        if os.path.exists(UFMResource.config_file_name):
            config_file.read(UFMResource.config_file_name)
            self.log_level = config_file.get("Common", "log_level")
            self.log_file_max_size = config_file.getint("Common", "log_file_max_size")
            self.log_file_backup_count = config_file.getint("Common", "log_file_backup_count")
            self.amount_of_workers = config_file.getint("Common", "Max_workers")
            executors = {
            'default': {'type': 'threadpool', 'max_workers': self.amount_of_workers},
            'processpool': ProcessPoolExecutor(max_workers=5)
            }
            self.scheduler.configure(executors=executors)

            log_format = '%(asctime)-15s %(levelname)s %(message)s'
            logging.basicConfig(handlers=[RotatingFileHandler(self.log_file_path,
                                                              maxBytes=self.log_file_max_size,
                                                              backupCount=self.log_file_backup_count)],
                                level=logging.getLevelName(self.log_level),
                                format=log_format)
            #logging.getLogger('apscheduler').setLevel(logging.debug)

    def init_apis(self):
        default_apis = {
            Queries: "/queries",
            QueryId: "/queries/<query_id>",
            Delete: "/delete/<report_id>",
            Version: "/version",
            Help: "/help",
            Dummy: "/dummy"
        }
        for resource, path in default_apis.items():
            self.api.add_resource(resource, path)

        self.api.add_resource(Cancel, "/cancel", resource_class_kwargs={'scheduler': self.scheduler})
        self.api.add_resource(QueryRequest, "/query",resource_class_kwargs={'scheduler': self.scheduler})


    async def run(self):
        self.app.run(port=self.port_number, debug=True)
        # resource = WSGIResource(reactor, reactor.getThreadPool(), self.app)
        # reactor.listenTCP(self.port_number, server.Site(resource))
        # reactor.run()

    async def stop(self):
        self.scheduler.shutdown()
