from pygnmi.client import gNMIclient
import aiohttp
import asyncio
import threading
import requests
import logging
import time

import helpers

class GNMIEventsReceiver:
    SUBSCRIBE_CONF = {'subscription': [{'path': 'system-events', 'mode': 'ON_CHANGE'}]}
    TARGET = "nvos"
    def __init__(self, switch_dict={}):
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.switch_dict = switch_dict
        self.session = requests.Session()
        self.traps_number = 0
        self.throttling_interval = 10
        self.high_event_rate = 100
        self.throttling_thread = None
        self.events = []

    def manager(self):
        for ip, switch in self.switch_dict.items():
            if not switch.socket_thread:
                switch.socket_thread = threading.Thread(target=self.subscribe,
                                                        args=(ip,
                                                              switch.user,
                                                              switch.credentials,
                                                              switch.guid))
                switch.socket_thread.start()
        if not self.throttling_thread:
            # TODO: figure out why it works only whtn the thread started in callbacks context
            self.throttling_thread = threading.Thread(target=self.throttle_events)
            self.throttling_thread.start()

    def cleanup(self):
        for switch in self.switch_dict.values():
            if switch.socket_thread:
                switch.socket_thread.join(timeout=self.throttling_interval)

    def subscribe(self, ip, user, credentials, guid):
        try:
            with gNMIclient(target=(ip, helpers.ConfigParser.gnmi_port),
                                    username=user,
                                    password=credentials,
                                    skip_verify=True) as gc:
                events_stream = gc.subscribe_stream(subscribe=self.SUBSCRIBE_CONF, target=self.TARGET)
                init = True
                for event_dict in events_stream:
                    if init:
                        init = False
                        continue
                    # print(json.dumps(event_dict, indent=4))
                    # print("ENTRY END")
                    self.traps_number += 1
                    payload = {"object_name": guid, "otype": "Switch"}
                    event_update = event_dict.get("update")
                    if event_update:
                        event_update = event_update.get("update")
                        description = ""
                        resource = ""
                        for event in event_update:
                            if event.get("path") == "state/text":
                                description = event.get("val")
                            if event.get("path") == "state/resource":
                                resource = event.get("val")
                            if event.get("path") == "state/severity":
                                payload["event_id"] = helpers.Severity.LEVEL_TO_EVENT_ID.get(event.get("val"))
                        payload["description"] = f"{resource}: {description}" if resource else description
                        self.events.append(payload)
        except Exception as e:
            logging.error(f"Failed to create gNMI socket for {ip}: {e}")

    def throttle_events(self):
        while True:
            if not self.events:
                continue
            start_time = time.time()
            asyncio.run(self.send_events())
            end_time = time.time()
            input_rate = self.traps_number / self.throttling_interval
            output_rate = self.traps_number / (end_time - start_time)
            logging.warning(f"Input rate (agents -> plugin) is {input_rate} traps/second")
            if input_rate > self.high_event_rate:
                logging.warning(f"Input rate is high, some traps might be dropped")
            logging.warning(f"Output rate (plugin -> UFM) is {output_rate} traps/second")
            with open(helpers.ConfigParser.throughput_file, "a") as file:
                file.write(f"Input rate (agents -> plugin) is {input_rate} traps/second\n")
                file.write(f"Output rate (plugin -> UFM) is {output_rate} traps/second\n")
            self.traps_number = 0
            time.sleep(self.throttling_interval)

    async def send_events(self):
        async with aiohttp.ClientSession(headers={"X-Remote-User": "ufmsystem"}) as session:
            tasks = []
            events_copy = list(self.events)
            self.events = []
            for payload in events_copy:
                tasks.append(asyncio.ensure_future(self.post_external_event(session, payload)))
            await asyncio.gather(*tasks)

    async def post_external_event(self, session, payload):
        if not payload:
            return
        resource = "/app/events/external_event"
        status_code, text = await helpers.async_post(session, resource, json=payload)
        if not helpers.succeded(status_code):
            logging.error(f"Failed to send external event, status code: {status_code}, response: {text}")
        logging.debug(f"Post external event status code: {status_code}, response: {text}")
