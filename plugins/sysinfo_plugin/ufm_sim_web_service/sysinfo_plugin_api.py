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

from tzlocal import get_localzone
from apscheduler.schedulers.background import BackgroundScheduler
from base_aiohttp_api import BaseAiohttpAPI
from resources import Version, Help, Config, Queries, Date, Dummy

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
        self.add_handler("/version", Version)
        self.add_handler("/help", Help)
        self.add_handler("/config", Config)
        self.add_handler("/queries", Queries)
        self.add_handler("/dummy", Dummy)
        self.add_handler("/date", Date)

    async def cleanup(self, app): # pylint: disable=unused-argument
        """
        This method runs on cleanup and can be used for releasing resources
        """
        self.scheduler.shutdown()
