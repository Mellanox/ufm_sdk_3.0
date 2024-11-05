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

import asyncio
import copy
import json
import socket
import threading
from aiohttp import web
from base_aiohttp_api import BaseAiohttpAPI, BaseAiohttpServer, BaseAiohttpHandler


CALLBACK_SERVER_IP = socket.gethostbyname(socket.gethostname())
CALLBACK_SERVER_PORT = 8995

class Callback(BaseAiohttpHandler):
    """
    Callback aiohttp handler class
    """
    ROUTE = "callback"
    URL = f"http://{CALLBACK_SERVER_IP}:{CALLBACK_SERVER_PORT}/{ROUTE}"

    __response_lock = threading.RLock()
    __response = {}

    async def post(self) -> web.Response:
        """ POST method handler """
        self.logger.info("TEST CALLBACK")
        if self.request.content_type == 'application/json':
            json_data = await self.request.json()
            self.logger.info(json_data)
            # Update callback response file
        else:
            json_data = {}
            self.logger.info(self.request)

        with Callback.__response_lock:
            Callback.__response = json_data

        return self.report_success()

    @staticmethod
    def get_recent_response() -> json:
        """ Return recent callback response """
        with Callback.__response_lock:
            json_data = copy.deepcopy(Callback.__response)
        return json_data

    @staticmethod
    def clear_recent_response() -> None:
        """ Clear recent callback response """
        with Callback.__response_lock:
            Callback.__response = {}


class CallbackServerThread:
    """
    Implements aiohttp callback server that is running in separate thread
    """
    def __init__(self, logger):
        self.logger = logger
        self.server = None
        self.thread = None

    async def stop(self):
        """
        Stop server thread
        """
        if self.server:
            await self.server.stop()
            self.server = None

        if self.thread and self.thread.is_alive():
            self.thread.join()

        self.thread = None

    def start(self):
        """
        Start server thread
        """
        self.thread = threading.Thread(target=self.__start_server)
        self.thread.start()

    def __start_server(self):
        """
        Start server
        """
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            api = BaseAiohttpAPI(self.logger)
            api.add_handler(f"/{Callback.ROUTE}", Callback)

            self.server = BaseAiohttpServer(self.logger)
            self.server.run(api.app, CALLBACK_SERVER_IP, CALLBACK_SERVER_PORT)

        except Exception as e: # pylint: disable=broad-exception-caught
            self.logger.error(f"{e}")
