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
from aiohttp import web
from http import HTTPStatus
from json import JSONDecodeError
from base_aiohttp_api import BaseAiohttpHandler

ERROR_INCORRECT_INPUT_FORMAT = "Incorrect input format"
EOL = '\n'

class SysInfoPluginAPI:
    '''
    class SysInfoPluginAPI
    '''

    def __init__(self):
        """
        Initialize a new instance of the PDRPluginAPI class.
        """
        self.app = web.Application()
        self.app.router.add_view("/test", TestHandler)


class TestHandler(BaseAiohttpHandler):
    async def get(self):
        # Use self.config here
        return self.web_response("Test handler response\n", HTTPStatus.OK)
