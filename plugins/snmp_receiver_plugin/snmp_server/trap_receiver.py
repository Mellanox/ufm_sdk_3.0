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
import aiohttp
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
from pysnmp.entity import engine, config
from pysnmp.carrier.asyncore.dgram import udp
from pysnmp.entity.rfc3413 import ntfrcv
import threading
import time

from helpers import ConfigParser
import helpers


class SnmpTrapReceiver:
    def __init__(self, switch_ip_to_name={}):
        self.mellanox_oid = "1.3.6.1.4.1.33049"
        self.test_trap_oid = self.mellanox_oid + ".2.1.2.13"

        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # Create SNMP engine with autogenernated engineID and pre-bound
        # to socket transport dispatcher
        self.snmp_engine = engine.SnmpEngine()
        self.ip_to_event_to_count = {}
        self._setup_transport()
        self._setup_snmp_v1_v2c()
        self.switch_ip_to_name = switch_ip_to_name
        self.traps_n = 0
        self.throttle_interval = 10
        self.st_t = 0

    def _setup_transport(self):
        # UDP over IPv4, first listening interface/port
        config.addTransport(self.snmp_engine, udp.domainName + (1,),
                            udp.UdpTransport().openServerMode((ConfigParser.snmp_ip, ConfigParser.snmp_port)))

    def _setup_snmp_v1_v2c(self):
        # SecurityName <-> CommunityName mapping
        config.addV1System(self.snmp_engine, 'my-area', ConfigParser.community)

        # Register SNMP Application at the SNMP engine
        ntfrcv.NotificationReceiver(self.snmp_engine, self.trap_callback)

        self.snmp_engine.transportDispatcher.jobStarted(1)  # this job would never finish

    # noinspection PyUnusedLocal,PyUnusedLocal
    def trap_callback(self, snmpEngine, stateReference, contextEngineId, contextName,
              varBinds, cbCtx):
        self.traps_n += 1
        # Get an execution context and use inner SNMP engine data to figure out peer address
        execContext = snmpEngine.observer.getExecutionContext('rfc3412.receiveMessage:request')
        switch_address = execContext['transportAddress'][0]
        switch_name = self.switch_ip_to_name.get(switch_address, "")
        if not switch_name:
            logging.warning(f"Cannot translate {switch_address} to switch name")
            switch_name = switch_address

        logging.info('Notification from %s' % (switch_name))

        description = ""
        for oid_obj, val_obj in varBinds:
            oid = oid_obj.prettyPrint()
            val = val_obj.prettyPrint()
            logging.debug('  %s = %s' % (oid, val))
            if val == self.test_trap_oid:
                description = "test trap"
            if self.mellanox_oid in oid:
                description = val

        self.ip_to_event_to_count.setdefault(switch_name, {}).setdefault(description, 0)
        self.ip_to_event_to_count[switch_name][description] += 1

        current_t = time.time()
        diff = current_t - self.st_t
        if diff >= self.throttle_interval:
            t = threading.Thread(target=self.throttle_events)
            t.start()
        self.st_t = current_t

    def throttle_events(self):
        s_t = time.time()
        asyncio.run(self.send_events())
        e_t = time.time()
        throughput = self.traps_n / (e_t - s_t)
        logging.warning(f"Throughput is {throughput} traps/second")
        self.traps_n = 0
        self.ip_to_event_to_count = {}

    async def send_events(self):
        async with aiohttp.ClientSession(headers={"X-Remote-User": "ufmsystem"}) as session:
            tasks = []
            for switch_name, event_to_count in self.ip_to_event_to_count.items():
                base_description = f"SNMP traps from {switch_name}: "
                description = ', '.join(f'{event} happened {count} times' for event, count in event_to_count.items())
                tasks.append(asyncio.ensure_future(self.post_external_event(session, base_description + description)))
            # for i in range(1000):
            #     tasks.append(asyncio.ensure_future(self.post_external_event(session, f"SNMP trap #{i} from swithc: event happened!")))
            await asyncio.gather(*tasks)

    async def post_external_event(self, session, description):
        resource = "/app/events/external_event"
        payload = {"event_id": 551, "description": description}
        status_code, text = await helpers.async_post(session, resource, json=payload)
        if not helpers.succeded(status_code):
            logging.error(f"Failed to send external event, status code: {status_code}, response: {text}")
        logging.debug(f"Post external event status code: {status_code}, response: {text}")

    def run(self):
        # Run I/O dispatcher which would receive queries and send confirmations
        try:
            self.snmp_engine.transportDispatcher.runDispatcher()
        except:
            self.snmp_engine.transportDispatcher.closeDispatcher()
            raise

if __name__ == "__main__":
    snmp_trap_receiver = SnmpTrapReceiver()
    snmp_trap_receiver.run()