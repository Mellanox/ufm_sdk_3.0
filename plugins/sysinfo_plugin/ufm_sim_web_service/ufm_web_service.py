"""
@copyright:
    Copyright (C) Mellanox Technologies Ltd. 2021. ALL RIGHTS RESERVED.

    This software product is a proprietary product of Mellanox Technologies
    Ltd. (the "Company") and all right, title, and interest in and to the
    software product, including all associated intellectual property rights,
    are and shall remain exclusively with the Company.

    This software product is governed by the End User License Agreement
    provided with the software product.

@author: Elad Gershon
@date:   January, 2023
"""

import asyncio
import signal

from ufm_web_sim import UFMWebSim


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


if __name__ == "__main__":
    _loop = asyncio.get_event_loop()
    ufm_web_sim = UFMWebSimProc()
    try:
        signal.signal(signal.SIGTERM, ufm_web_sim.shutdown)
        ufm_web_sim.main()
        _loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        print("Stopping Sysinfo web server", flush=True)
        _loop.run_until_complete(ufm_web_sim.cleanup())
        _loop.stop()
