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
# @author: Alexander Tolikin
# @date:   November, 2022
#
import asyncio
from flask import Flask
from flask_restful import Api
import logging
from logging.handlers import RotatingFileHandler
from multiprocessing import Process, Manager
import threading
import time
# from twisted.web.wsgi import WSGIResource
# from twisted.internet import reactor
# from twisted.web import server

from resources import Dummy, RegisterSwitch, UnregisterSwitch, TrapList, EnableTrap, DisableTrap, SwitchList, Version, Date
import helpers
from trap_receiver import SnmpTrapReceiver

class SNMPWebServer:
    def __init__(self, switch_dict):
        self.port_number = helpers.ConfigParser.port
        self.app = Flask(__name__)
        self.api = Api(self.app)
        self.switch_dict = switch_dict
        self.init_apis()

    def init_apis(self):
        apis = {
            RegisterSwitch: "/register",
            UnregisterSwitch: "/unregister",
            SwitchList: "/switch_list",
            TrapList: "/trap_list",
            EnableTrap: "/enable_trap",
            DisableTrap: "/disable_trap",
            Version: "/version",
            Date: "/date",
            Dummy: "/dummy"
        }
        for resource, path in apis.items():
            self.api.add_resource(resource, path, resource_class_kwargs={
                'switch_dict': self.switch_dict})

    async def run(self):
        self.app.run(port=self.port_number, debug=True, use_reloader=False)
        # resource = WSGIResource(reactor, reactor.getThreadPool(), self.app)
        # reactor.listenTCP(ConfigParser.server_port, server.Site(resource))
        # reactor.run()

    async def stop(self):
        pass


class SNMPWebProc:
    """Main class of the SNMP web sim daemon
    """
    def __init__(self):
        print("Starting SNMP web server", flush=True)
        logging.basicConfig(handlers=[RotatingFileHandler(helpers.ConfigParser.log_file,
                                                          maxBytes=helpers.ConfigParser.log_file_max_size,
                                                          backupCount=helpers.ConfigParser.log_file_backup_count)],
                            level=logging.getLevelName(helpers.ConfigParser.log_level),
                            format=helpers.ConfigParser.log_format)
        self.loop = asyncio.get_event_loop()
        self.manager = Manager()
        switch_dict = helpers.get_ufm_switches()
        self.switch_dict = self.manager.dict(switch_dict)
        self.web_server = SNMPWebServer(self.switch_dict)
        snmp_trap_receiver = SnmpTrapReceiver(self.switch_dict)
        self.snmp_proc = Process(target=snmp_trap_receiver.run)
        self.snmp_proc.start()
        self.switch_update_thread = threading.Thread(target=self._update_switches)
        self.switch_update_thread.start()

    def _update_switches(self):
        while True:
            self.switch_dict.clear()
            self.switch_dict.update(helpers.get_ufm_switches())
            time.sleep(helpers.ConfigParser.ufm_update_switches_interval)

    def start_web_server(self):
        self.loop.run_until_complete(self.web_server.run())

    async def cleanup(self):
        await self.web_server.stop()
        self.snmp_proc.terminate()

    def shutdown(self, *_args):
        raise KeyboardInterrupt


if __name__ == "__main__":
    _loop = asyncio.get_event_loop()
    snmp_web_server = SNMPWebProc()
    try:
        # signal.signal(signal.SIGTERM, snmp_web_server.shutdown)
        snmp_web_server.start_web_server()
        _loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        print("Stopping SNMP web server", flush=True)
        _loop.run_until_complete(snmp_web_server.cleanup())
        _loop.stop()
