"""
@copyright:
    Copyright (C) Nvidia Technologies Ltd. 2014-2022.  ALL RIGHTS RESERVED.

    This software product is a proprietary product of Mellanox Technologies
    Ltd. (the "Company") and all right, title, and interest in and to the
    software product, including all associated intellectual property rights,
    are and shall remain exclusively with the Company.

    This software product is governed by the End User License Agreement
    provided with the software product.

@author: Nasr Ajaj
@date:   May 09, 2022
"""

from api.base_api import BaseAPIApplication
from plugins.bright_plugin.bright_mgr import BrightMgr


class BrightDataAPI(BaseAPIApplication):
    """
    Flask RESTful API for Bright integration.
    Create Flask web application that routes URLs to
    task handler API.
    see http://flask.pocoo.org/ for Flask documentation.
    """

    API_PARAM_DEVICES = "device"

    def __init__(self, config_parser):
        self._bright_mgr = BrightMgr.getInstance(config_parser)
        super(BrightDataAPI, self).__init__()

    def _getRoutes(self):
        routes = {
            self.get_device_jobs: dict(urls=["/jobs"], methods=["GET"])
        }

        return routes

    def get_device_jobs(self):
        device = self._getRequestArg(self.API_PARAM_DEVICES)
        jobs = self._bright_mgr.get_device_jobs(device)
        return self.createResp(jobs)
