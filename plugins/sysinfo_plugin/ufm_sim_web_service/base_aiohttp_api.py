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
import signal
from aiohttp import web

class BaseAiohttpServer:
    """
    Base class for HTTP server implemented with aiohttp
    """
    def __init__(self, logger):
        """
        Initialize a new instance of the BaseAiohttpAPI class.
        """
        self.logger = logger
        self.shutdown_event = asyncio.Event()

    def run(self, app, host, port):
        """
        Run the server on the specified host and port.
        """
        # Register signal handlers
        loop = asyncio.get_event_loop()
        for signame in ["SIGINT", "SIGTERM"]:
            loop.add_signal_handler(getattr(signal, signame), lambda: asyncio.create_task(self.stop()))

        # Run server loop
        loop.run_until_complete(self._run_server(app, host, port))

    async def stop(self):
        """
        Gracefully shut down the server.
        """
        self.shutdown_event.set()

    async def _run_server(self, app, host, port):
        """
        Asynchronously run the server and handle shutdown.
        """
        # Clear shutdown signal
        self.shutdown_event.clear()

        # Run server
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        self.logger.info(f"Server started at {host}:{port}")

        # Wait for shutdown signal
        await self.shutdown_event.wait()
        self.logger.info(f"Shutting down server {host}:{port}")

        # Uninitialize server
        await site.stop()
        await runner.cleanup()

class BaseAiohttpHandler(web.View):
    """
    Base aiohttp handler class
    """
    def __init__(self, request):
        """
        Initialize a new instance of the BaseAiohttpHandler class.
        """
        super().__init__(request)
        self.logger = request.app["logger"]

    @staticmethod
    def web_response(text, status):
        """
        Create response object.
        """
        return web.json_response(text=text, status=status)


class ScheduledAiohttpHandler(BaseAiohttpHandler):
    """
    Base aiohttp handler class with scheduller
    """
    def __init__(self, request):
        """
        Initialize a new instance of the ScheduledAiohttpHandler class.
        """
        super().__init__(request)
        self.scheduler = request.app["scheduler"]
