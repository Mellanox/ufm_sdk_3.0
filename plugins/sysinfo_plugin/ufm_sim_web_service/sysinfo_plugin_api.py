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
from tzlocal import get_localzone
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ProcessPoolExecutor
from base_aiohttp_api import BaseAiohttpAPI, BaseAiohttpHandler, ScheduledAiohttpHandler

class SysInfoPluginAPI(BaseAiohttpAPI):
    """
    Class SysInfoPluginAPI
    """
    def __init__(self, logger):
        """
        Initialize a new instance of the SysInfoPluginAPI class.
        """
        # Call the parent class's constructor
        super().__init__(logger)

        # Init scheduler
        self.scheduler = self.app["scheduler"] = BackgroundScheduler(timezone=get_localzone())
        self.scheduler.start()

        # Add handlers
        self.add_handler("/test", TestHandler)

    async def cleanup(self, app): # pylint: disable=unused-argument
        """
        This method runs on cleanup and can be used for releasing resources
        """
        self.scheduler.shutdown()


class TestHandler(ScheduledAiohttpHandler):
    async def get(self):
        # Use self.config here
        return self.web_response("Test handler response\n", HTTPStatus.OK)
