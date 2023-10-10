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
import json
import os
import logging

from flask import Flask
from flask_restful import Api
from logging.handlers import RotatingFileHandler
from apscheduler.schedulers.background import BackgroundScheduler

from twisted.web.wsgi import WSGIResource
from twisted.internet import reactor
from twisted.web import server

from resources import UIFilesResources ,UFMResource, Compare, Ndts, Reports, ReportId,\
    Upload, Delete, Cancel, Version, Help, Date, Dummy
from merger_resources import MergerUploadNDT, MergerVerifyNDT, MergerDummyTest, \
    MergerVerifyNDTReports, MergerVerifyNDTReportId, MergerDeployNDTConfig, \
    MergerNdts, MergerDeleteNDT, MergerUpdateNDTConfig, MergerLatestDeployedNDT, \
    MergerCreateNDTTopoconfig, MergerUpdDeployNDTConfig, MergerNdtsFile, \
    MergerCableValidationReport, MergerCableValidationEnabled


class UFMNDTWebServer:
    def parse_config(self):
        ndt_config = configparser.ConfigParser()
        if os.path.exists(UFMResource.config_file_name):
            ndt_config.read(UFMResource.config_file_name)
            self.log_level = ndt_config.get("Common", "log_level")
            self.log_file_max_size = ndt_config.getint("Common", "log_file_max_size")
            self.log_file_backup_count = ndt_config.getint("Common", "log_file_backup_count")

            log_format = '%(asctime)-15s %(levelname)s %(message)s'
            logging.basicConfig(handlers=[RotatingFileHandler(self.log_file_path,
                                                              maxBytes=self.log_file_max_size,
                                                              backupCount=self.log_file_backup_count)],
                                level=logging.getLevelName(self.log_level),
                                format=log_format)
            logging.getLogger('apscheduler').setLevel(logging.ERROR)

    def init_apis(self):
        default_apis = {
            UIFilesResources: "/files/<path:file_name>",
            Ndts: "/list",
            Reports: "/reports",
            Delete: "/delete",
            Upload: "/upload",
            ReportId: "/reports/<report_id>",
            # merger specific APIs
            MergerNdts: "/merger_ndts_list",
            MergerNdtsFile: "/merger_ndts_list/<ndt_file_name>",
            MergerUploadNDT: "/merger_upload_ndt",
            MergerVerifyNDT: "/merger_verify_ndt",
            MergerVerifyNDTReports: "/merger_verify_ndt_reports",
            MergerVerifyNDTReportId: "/merger_verify_ndt_reports/<report_id>",
            MergerUpdateNDTConfig: "/merger_update_topoconfig",
            MergerDeployNDTConfig: "/merger_deploy_ndt_config",
            MergerUpdDeployNDTConfig: "/merger_update_deploy_ndt_config",
            MergerDeleteNDT: "/merger_delete_ndt",
            MergerLatestDeployedNDT: "/merger_deployed_ndt",
            MergerCreateNDTTopoconfig: "/merger_create_topoconfig",
            MergerCableValidationReport: "/cable_valigation_report",
            MergerCableValidationEnabled: "/cable_valigation_enabled",
            MergerDummyTest: "/merger_dymmy_test",
            # common
            Version: "/version",
            Help: "/help",
            Date: "/date",
            Dummy: "/dummy"
        }
        for resource, path in default_apis.items():
            self.api.add_resource(resource, path)

        self.api.add_resource(Cancel, "/cancel", resource_class_kwargs={'scheduler': self.scheduler})
        self.api.add_resource(Compare, "/compare", resource_class_kwargs={'scheduler': self.scheduler})

    def restart_periodic_comparison(self):
        if not os.path.exists(UFMResource.periodic_request_file):
            return
        compare = Compare(self.scheduler)
        with open(UFMResource.periodic_request_file, "r") as file:
            compare.parse_request(json.load(file))
        compare.add_scheduler_jobs()

    def __init__(self):
        self.log_level = logging.INFO
        self.log_file_max_size = 10240000
        # self.log_file_path = "/tmp/ndt.log"
        self.log_file_path = "/log/ndt.log"
        self.log_file_backup_count = 5
        self.port_number = 8980
        self.app = Flask(__name__)
        self.api = Api(self.app)

        self.parse_config()
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self.restart_periodic_comparison()
        self.init_apis()

    async def run(self):
        self.app.run(port=self.port_number, debug=True)
        # resource = WSGIResource(reactor, reactor.getThreadPool(), self.app)
        # reactor.listenTCP(self.port_number, server.Site(resource))
        # reactor.run()

    async def stop(self):
        pass
