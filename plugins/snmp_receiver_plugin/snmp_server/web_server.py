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
# @author: Alexander Tolikin
# @date:   November, 2022
#
import asyncio
from flask import Flask
from flask_restful import Api
import logging
from logging.handlers import RotatingFileHandler
import multiprocessing
import signal
# from twisted.web.wsgi import WSGIResource
# from twisted.internet import reactor
# from twisted.web import server

from resources import Dummy, RegisterSwitch, UnregisterSwitch, AddEvent, RemoveEvent
from helpers import ConfigParser, get_ufm_switches
from trap_receiver import SnmpTrapReceiver

class SNMPWebServer:
    def __init__(self, switch_ip_to_name_and_guid):
        self.port_number = 8780
        self.app = Flask(__name__)
        self.api = Api(self.app)
        self.switch_ip_to_name_and_guid = switch_ip_to_name_and_guid
        self.registered_switches = set()
        self.init_apis()

    def init_apis(self):
        apis = {
            RegisterSwitch: "/register",
            UnregisterSwitch: "/unregister",
            AddEvent: "/add_event",
            RemoveEvent: "/remove_event",
            Dummy: "/dummy"
        }
        for resource, path in apis.items():
            self.api.add_resource(resource, path, resource_class_kwargs={
                'switch_ip_to_name_and_guid': self.switch_ip_to_name_and_guid,
                'registered_switches': self.registered_switches})

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
        logging.basicConfig(handlers=[RotatingFileHandler(ConfigParser.log_file_path,
                                                          maxBytes=ConfigParser.log_file_max_size,
                                                          backupCount=ConfigParser.log_file_backup_count)],
                            level=logging.getLevelName(ConfigParser.log_level),
                            format=ConfigParser.log_format)
        self.switch_ip_to_name_and_guid = get_ufm_switches()
        self.loop = asyncio.get_event_loop()
        self.web_server = SNMPWebServer(self.switch_ip_to_name_and_guid)
        snmp_trap_receiver = SnmpTrapReceiver(self.switch_ip_to_name_and_guid)
        self.snmp_proc = multiprocessing.Process(target=snmp_trap_receiver.run)
        self.snmp_proc.start()

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
