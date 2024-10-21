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
from base_aiohttp_api import BaseAiohttpAPI

ERROR_INCORRECT_INPUT_FORMAT = "Incorrect input format"
EOL = '\n'

class SysInfoPluginAPI(BaseAiohttpAPI):
    '''
    class SysInfoPluginAPI
    '''

    def __init__(self):
        """
        Initialize a new instance of the PDRPluginAPI class.
        """
        super().__init__()

        # Define routes using the base class's method
        self.add_route("GET", "/test", self.test)


    async def test(self, request): # pylint: disable=unused-argument
        """
        Return ports from exclude list as comma separated port names
        """
        return self.web_response("Test response\n", HTTPStatus.OK)
