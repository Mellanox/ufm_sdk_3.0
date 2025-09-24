from pygnmi.client import gNMIclient
import aiohttp
import asyncio
import threading
import requests
import logging
import time

import helpers

class GNMIEventsReceiver:
    """
    Class for the GNMI events receiver that subscribes to the GNMI events
    by creating sockets for every switch as a separate thread
    and sends the events to the UFM as external events
    """
    # GNMI subscription configuration to get all system events on change
    SUBSCRIBE_CONF = {'subscription': [{'path': 'system-events', 'mode': 'ON_CHANGE'}]}
    TARGET = "nvos"
    def __init__(self, switch_dict=None):
        # disable annoying warning when debugging, in production all requests will be secured
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        # dictionary of switches with their credentials and GUIDs
        self.switch_dict = switch_dict
        self.session = requests.Session()
        self.traps_number = 0
        # throttling interval in which events are send to UFM in seconds
        self.throttling_interval = helpers.ConfigParser.ufm_send_events_interval
        self.high_event_rate = 100
        self.throttling_thread = None
        self.events = []

        def thread_exception_handler(args):
            exc_type = args.exc_type
            exc_value = args.exc_value
            exc_traceback = args.exc_traceback
            thread = args.thread
            
            # Don't handle SystemExit
            if exc_type is SystemExit:
                return
            
            # Try to get IP from thread name or exception
            ip = None
            if hasattr(exc_value, '_state') and hasattr(exc_value._state, 'target'):
                # target is in the format of ip:port
                ip = exc_value._state.target.split(':')[0]
            elif hasattr(thread, 'ip'):
                ip = thread.ip
            elif hasattr(exc_value, 'ip'):
                ip = exc_value.ip

            logging.error("Unhandled exception in thread %s (IP: %s):", thread.name, ip)
            logging.debug("Type: %s", exc_type.__name__)
            logging.debug("Value: %s", exc_value)
            logging.debug("Traceback:", exc_info=(exc_type, exc_value, exc_traceback))
            
            # If this is a switch thread, try to restart it
            if ip and ip in self.switch_dict:
                switch = self.switch_dict.get(ip)
                if switch:
                    logging.info("Attempting to restart thread for switch %s", ip)
                    switch.socket_thread.join(timeout=self.throttling_interval)
                    # try to reconnect 10 times with 60 seconds interval
                    max_retries = 10
                    switch.socket_thread = threading.Thread(target=self.subscribe,
                                                            args=(ip,switch.user,switch.credentials,switch.guid,True))
                    switch.socket_thread.start()

        # Set the exception handler for all threads
        threading.excepthook = thread_exception_handler

    def create_socket_threads(self, switch_dict=None):
        if not switch_dict:
            switch_dict = self.switch_dict
        for ip, switch in switch_dict.items():
            if not switch.socket_thread:
                switch.socket_thread = threading.Thread(target=self.subscribe,
                                                        args=(ip,switch.user,switch.credentials,switch.guid))
                switch.socket_thread.start()

    def run(self):
        self.create_socket_threads()
        if not self.throttling_thread:
            self.throttling_thread = threading.Thread(target=self.throttle_events)
            self.throttling_thread.start()

    def cleanup(self, switch_dict=None):
        if not switch_dict:
            switch_dict = self.switch_dict
        for switch in self.switch_dict.values():
            if switch.socket_thread:
                switch.socket_thread.join(timeout=self.throttling_interval)

    def subscribe(self, ip, user, credentials, guid, reconnect=False):
        retry_count = 0
        max_retries = helpers.ConfigParser.gnmi_reconnect_retries if reconnect else 1
        while retry_count < max_retries:
            try:
                with gNMIclient(target=(ip, helpers.ConfigParser.gnmi_port),
                                        username=user,
                                        password=credentials,
                                        skip_verify=True) as gc:
                    events_stream = gc.subscribe_stream(subscribe=self.SUBSCRIBE_CONF, target=self.TARGET)
                    init = True
                    # this is a blocking loop that will wait for events from the switch.
                    # each time an event is triggered, the loop will execute
                    for event_dict in events_stream:
                        payload = {"object_name": guid, "otype": "Switch"}
                        if init:
                            if reconnect:
                                payload["description"] = f"The connection was reestablished successfully \
                                                           after a disconnect (reboot, power loss, etc.)."
                                payload["event_id"] = helpers.Severity.WARNING_ID
                                self.events.append(payload)
                            # skip initial stream of already happened events
                            init = False
                            continue
                        self.traps_number += 1
                        event_update = event_dict.get("update")
                        if event_update:
                            event_update = event_update.get("update")
                            description = resource = None
                            for event in event_update:
                                path = event.get("path")
                                if path == "state/text":
                                    description = event.get("val")
                                elif path == "state/resource":
                                    resource = event.get("val")
                                elif path == "state/severity":
                                    event_severity = helpers.Severity.LEVEL_TO_EVENT_ID.get(event.get("val"))
                            payload["description"] = f"{resource}: {description}" if resource else description
                            payload["event_id"] = event_severity
                            # append is thread safe
                            self.events.append(payload)
            except Exception as e:
                retry_count += 1
                logging.critical("Failed to create gNMI socket for %s because of wrong credentials or bad connectivity (Attempt %d/%d)", ip, retry_count, max_retries)
                logging.debug("Exception: %s", e)
                if reconnect:
                    logging.info("Waiting 60 seconds before reconnecting...")
                    time.sleep(60)

    def throttle_events(self):
        """
        This function is used to throttle the events that come from switches and to send them to UFM.
        """
        while True:
            if not self.events:
                continue
            logging.info("Got %s traps from switches to be sent to UFM", len(self.events))
            start_time = time.perf_counter()
            asyncio.run(self.send_events())
            end_time = time.perf_counter()
            sending_duration = end_time - start_time
            input_rate = self.traps_number / self.throttling_interval
            output_rate = self.traps_number / sending_duration
            logging.info("Input rate (agents -> plugin) is %s traps/second", input_rate)
            if input_rate > self.high_event_rate:
                logging.warning("Input rate is high, some traps might be dropped")
            logging.info("Output rate (plugin -> UFM) is %s traps/second", output_rate)
            self.traps_number = 0
            time_to_sleep = self.throttling_interval - sending_duration
            if time_to_sleep > 0:
                time.sleep(time_to_sleep)
            else:
                logging.warning("Sending duration is longer than throttling interval, some traps might be dropped")
    
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
            logging.error("Failed to send external event, status code: %s, response: %s", status_code, text)
        logging.debug("Post external event status code: %s, response: %s", status_code, text)
