import requests
import socket
import time

from helpers import get_ufm_switches, register_switches


class PluginRegistrator:
    def __init__(self):
        self.switch_ips = set()

    def run(self):
        while True:
            new_switch_ips = get_ufm_switches()
            switches_to_register = new_switch_ips - self.switch_ips
            if switches_to_register:
                self.switch_ips = new_switch_ips
                # TODO: we should log the result
                register_switches(switches_to_register)
            time.sleep(60)


if __name__ == "__main__":
    plugin_registrator = PluginRegistrator()
    plugin_registrator.run()