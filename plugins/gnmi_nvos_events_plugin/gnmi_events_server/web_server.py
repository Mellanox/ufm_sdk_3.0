#
# Copyright © 2013-2025 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
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
# @date:   March, 2025
#
import asyncio
from flask import Flask
from flask_restful import Api
import signal
import threading
import time
# from twisted.web.wsgi import WSGIResource
# from twisted.internet import reactor
# from twisted.web import server

from resources import Dummy, Version, Date
import helpers
from gnmi_events_receiver import GNMIEventsReceiver

class GNMIEventsWebServer:
    """
    Class for the web server that receives GNMI events from the GNMI events receiver
    """
    def __init__(self, switch_dict):
        self.port_number = helpers.ConfigParser.port
        self.app = Flask(__name__)
        self.api = Api(self.app)
        self.switch_dict = switch_dict
        self.init_apis()

    def init_apis(self):
        apis = {
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


class GNMIEventsWebProc:
    """
    Main class of the GNMI Events web sim daemon,
    that starts the web server and the GNMI events receiver in separate processes
    """
    def __init__(self):
        print("Starting GNMI Events web server", flush=True)
        self.loop = asyncio.get_event_loop()
        self.switch_dict = helpers.get_ufm_switches()
        self.web_server = GNMIEventsWebServer(self.switch_dict)
        self.gnmi_events_receiver = GNMIEventsReceiver(self.switch_dict)
        self.gnmi_events_receiver.run()
        # sleep for 3 minutes before first update - wait for ibdiagnet report to finish
        time.sleep(helpers.ConfigParser.ufm_first_update_interval)
        self.switch_update_thread = threading.Thread(target=self._update_switches)
        self.switch_update_thread.start()

    def _update_switches(self):
        while True:
            updated_switches = helpers.get_ufm_switches(self.switch_dict)
            new_switches = set(updated_switches.items()) - set(self.switch_dict.items())
            old_switches = set(self.switch_dict.items()) - set(updated_switches.items())
            if new_switches:
                self.gnmi_events_receiver.create_socket_threads(dict(new_switches))
            if old_switches:
                self.gnmi_events_receiver.cleanup(dict(old_switches))
            time.sleep(helpers.ConfigParser.ufm_switches_update_interval)

    def start_web_server(self):
        self.loop.run_until_complete(self.web_server.run())

    async def cleanup(self):
        self.gnmi_events_receiver.cleanup()
        await self.web_server.stop()

    def shutdown(self, *_args):
        raise KeyboardInterrupt


if __name__ == "__main__":
    _loop = asyncio.get_event_loop()
    gnmi_events_web_server = GNMIEventsWebProc()
    try:
        signal.signal(signal.SIGTERM, gnmi_events_web_server.shutdown)
        gnmi_events_web_server.start_web_server()
        _loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        print("Stopping GNMI Events web server", flush=True)
        _loop.run_until_complete(gnmi_events_web_server.cleanup())
        _loop.stop()
