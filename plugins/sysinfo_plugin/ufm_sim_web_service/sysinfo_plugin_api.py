#
# Copyright © 2013-2024 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
#

import json
import time
from http import HTTPStatus
from json import JSONDecodeError
from aiohttp import web
from tzlocal import get_localzone
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ProcessPoolExecutor
from base_aiohttp_api import BaseAiohttpHandler, ScheduledAiohttpHandler

class SysInfoPluginAPI:
    """
    Class SysInfoPluginAPI
    """
    def __init__(self, logger):
        """
        Initialize a new instance of the SysInfoPluginAPI class.
        """
        self.logger = logger

        self.scheduler = BackgroundScheduler(timezone=get_localzone())
        self.scheduler.start()

        self.app = web.Application()
        self.app["logger"] = self.logger
        self.app["scheduler"] = self.scheduler
        self.app.router.add_view("/test", TestHandler)

    def cleanup(self):
        """
        Uninitialize instance of the SysInfoPluginAPI class.
        """
        self.scheduler.shutdown()


class TestHandler(ScheduledAiohttpHandler):
    async def get(self):
        # Use self.config here
        return self.web_response("Test handler response\n", HTTPStatus.OK)
