#
# Copyright © 2013-2023 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
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
import logging
from logging.handlers import RotatingFileHandler
import os
from configuration import Configuration
from ufm_web_sim import UFMWebSim
from base_aiohttp_api import BaseAiohttpServer
from sysinfo_plugin_api import SysInfoPluginAPI

class UFMWebSimProc:
    """Main class of the UFM web sim daemon
    """

    def __init__(self):
        print("Starting Sysinfo web server", flush=True)
        self.web_server = UFMWebSim()

    def _start_web_server(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.web_server.run())

    def main(self):
        self._start_web_server()

    async def cleanup(self):
        await self.web_server.stop()

    def shutdown(self, *_args):
        raise KeyboardInterrupt


def create_logger():
    """
    Create a logger for plugin actions
    """
    log_file = Configuration.LOG_FILE_NAME
    if not os.path.exists(log_file):
        os.makedirs('/'.join(log_file.split('/')[:-1]), exist_ok=True)

    logger = logging.getLogger(log_file)
    format_str = f"%(asctime)-15s ufm-sysinfo-plugin-{log_file} Machine: localhost     %(levelname)-7s: %(message)s"
    logging.basicConfig(format=format_str, level=Configuration.log_level)
    rotate_handler = RotatingFileHandler(log_file,maxBytes=Configuration.log_file_max_size,
                                         backupCount=Configuration.log_file_backup_count)
    rotate_handler.setLevel(Configuration.log_level)
    rotate_handler.setFormatter(logging.Formatter(format_str))
    logger.addHandler(rotate_handler)
    return logger


def main():
    """
    Plugin main function
    """
    try:
        host = "127.0.0.1"
        port = 8999

        Configuration.load()
        logger = create_logger()
        api = SysInfoPluginAPI(logger)

        server = BaseAiohttpServer(logger)
        server.run(api, host, port)
    
    except Exception as e: # pylint: disable=broad-exception-caught
        logger.error(f"{str(e)}")


if __name__ == "__main__":
    main()

#    _loop = asyncio.get_event_loop()
#    ufm_web_sim = UFMWebSimProc()
#    try:
#        signal.signal(signal.SIGTERM, ufm_web_sim.shutdown)
#        ufm_web_sim.main()
#        _loop.run_forever()
#    except KeyboardInterrupt:
#        pass
#    finally:
#        print("Stopping Sysinfo web server", flush=True)
#        _loop.run_until_complete(ufm_web_sim.cleanup())
#        _loop.stop()
