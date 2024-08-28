#
# Copyright © 2013-2022 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
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
from aiohttp import web

class BaseAiohttpAPI:
    """
    Base class for API implemented with aiohttp
    """
    def __init__(self):
        """
        Initialize a new instance of the BaseAiohttpAPI class.
        """
        self.app = web.Application()

    @property
    def application(self):
        """
        Read-only property for the application instance.
        """
        return self.app

    def add_route(self, method, path, handler):
        """
        Add route to API.
        """
        self.app.router.add_route(method, path, handler)


class BaseAiohttpServer:
    """
    Base class for HTTP server implemented with aiohttp
    """
    def __init__(self, logger):
        """
        Initialize a new instance of the BaseAiohttpAPI class.
        """
        self.logger = logger

    def run(self, app, host, port):
        """
        Run the server on the specified host and port.
        """
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._run_server(app, host, port))

    async def _run_server(self, app, host, port):
        """
        Asynchronously run the server and handle shutdown.
        """
        # Run server
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        self.logger.info(f"Server started at {host}:{port}")

        # Wait for shutdown signal
        shutdown_event = asyncio.Event()
        try:
            await shutdown_event.wait()
        except KeyboardInterrupt:
            self.logger.info(f"Shutting down server {host}:{port}...")
        finally:
            await runner.cleanup()
