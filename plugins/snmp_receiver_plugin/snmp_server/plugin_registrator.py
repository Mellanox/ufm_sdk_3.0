import requests
import socket
import time

from helpers import get_ufm_switches, post_request


class PluginRegistrator:
    def __init__(self):
        self.switch_ips = get_ufm_switches()

    def run(self):
        while True:
            new_switch_ips = get_ufm_switches()
            switches_to_register = new_switch_ips - self.switch_ips
            self.switch_ips = new_switch_ips
            credentials = "f_user_id=admin&f_password=admin"
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            for ip in switches_to_register:
                session = requests.Session()
                # authentication
                _ = post_request(session, ip, "https", "/admin/launch?script=rh&template=login&action=login", headers, data=credentials)
                # registration
                local_hostname = socket.gethostname()
                local_ip = socket.gethostbyname(local_hostname)
                payload = {"cmd": f"snmp-server host {local_ip} traps"}
                _ = post_request(session, ip, "https", "/admin/launch?script=json", headers, json=payload)
            time.sleep(60)


if __name__ == "__main__":
    plugin_registrator = PluginRegistrator()
    plugin_registrator.run()