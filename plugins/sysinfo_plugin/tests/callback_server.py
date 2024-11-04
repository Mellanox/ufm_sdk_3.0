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
import json
import socket
import threading
from aiohttp import web
from base_aiohttp_api import BaseAiohttpAPI, BaseAiohttpServer, BaseAiohttpHandler


HOSTNAME = socket.gethostname()
CALLBACK_SERVER_IP = socket.gethostbyname(HOSTNAME)
CALLBACK_SERVER_PORT = 8995
CALLBACK_HANDLER = "callback"
CALLBACK_URL = f"http://{CALLBACK_SERVER_IP}:{CALLBACK_SERVER_PORT}/{CALLBACK_HANDLER}"


class Callback(BaseAiohttpHandler):
    """
    Callback aiohttp handler class
    """
    # Shared lock
    __response_lock = threading.RLock()

    # TODO: avoid usage of file  for recent response (Why do we need it at all?)
    CALLBACK_RESPONSE_FILE="/tmp/sysinfo_recent_post.log"

    async def post(self) -> web.Response:
        """ POST method handler """
        self.logger.info("TEST CALLBACK")
        if self.request.content_type == 'application/json':
            json_data = await self.request.json()
            self.logger.info(json_data)
            # Update callback response file
            with Callback.__response_lock:
                with open(Callback.CALLBACK_RESPONSE_FILE, "w", encoding="utf-8") as file:
                    json.dump(json_data, file)
        else:
            self.logger.info(self.request)
        return self.report_success()

    @staticmethod
    def get_recent_response() -> json:
        """ Read recent callback response from the file """
        file_name = Callback.CALLBACK_RESPONSE_FILE
        with Callback.__response_lock:
            with open(file_name, "r", encoding="utf-8") as file:
                # unhandled exception in case some of the files was changed manually
                try:
                    data = json.load(file)
                except json.JSONDecodeError:
                    return {}
        return data


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
            api.add_handler("/{CALLBACK_HANDLER}", Callback)

            self.server = BaseAiohttpServer(self.logger)
            self.server.run(api.app, CALLBACK_SERVER_IP, CALLBACK_SERVER_PORT)

        except Exception as e: # pylint: disable=broad-exception-caught
            self.logger.error(f"{e}")
