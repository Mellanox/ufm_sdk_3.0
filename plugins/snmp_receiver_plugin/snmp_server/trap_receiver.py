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
from pysnmp.smi import builder, view, compiler, rfc1902
from pysnmp import proto
import threading
import time

from helpers import ConfigParser
import helpers


class SnmpTrapReceiver:
    def __init__(self, switch_ip_to_name_and_guid={}):
        self.mellanox_oid = "33049"
        self.test_trap_oid = self.mellanox_oid + ".2.1.2.13"

        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # Create SNMP engine with autogenernated engineID and pre-bound
        # to socket transport dispatcher
        self.snmp_engine = engine.SnmpEngine()
        self.ip_to_event_to_count = {}
        self._setup_transport()
        self._setup_snmp_v1_v2c()
        self.mibBuilder = None
        self.mibViewController = None
        self._init_mib_controller()
        self.switch_ip_to_name_and_guid = switch_ip_to_name_and_guid
        self.traps_n = 0
        self.throttle_interval = 10
        self.st_t = 0
        self.events_at_time = 10
        self.event_id = 555 # warning

    def _setup_transport(self):
        # UDP over IPv4, first listening interface/port
        config.addTransport(self.snmp_engine, udp.domainName + (1,),
                            udp.UdpTransport().openServerMode((ConfigParser.snmp_ip, ConfigParser.snmp_port)))

    def _setup_snmp_v1_v2c(self):
        # SecurityName <-> CommunityName mapping
        config.addV1System(self.snmp_engine, 'my-area', ConfigParser.community)
        # config.addV3User(
        #     self.snmp_engine,
        #     "user3",
        #     config.usmHMACMD5AuthProtocol,
        #     "user3password",
        #     config.usmDESPrivProtocol,
        #     "user3encryption",
        #     proto.rfc1902.OctetString(hexValue='8000000004030201')
        # )

        # Register SNMP Application at the SNMP engine
        ntfrcv.NotificationReceiver(self.snmp_engine, self.trap_callback)

        self.snmp_engine.transportDispatcher.jobStarted(1)  # this job would never finish

    def _init_mib_controller(self):
        # Assemble MIB viewer
        self.mibBuilder = builder.MibBuilder()
        compiler.addMibCompiler(self.mibBuilder, sources=[
            'file:///auto/mtrswgwork/atolikin/ufm_sdk_3.0/plugins/snmp_receiver_plugin/mibs/standard',
            'file:///auto/mtrswgwork/atolikin/ufm_sdk_3.0/plugins/snmp_receiver_plugin/mibs/standard'
            ])
        self.mibViewController = view.MibViewController(self.mibBuilder)
        # Pre-load MIB modules
        self.mibBuilder.loadModules()

    # noinspection PyUnusedLocal,PyUnusedLocal
    def trap_callback(self, snmpEngine, stateReference, contextEngineId, contextName,
              varBinds, cbCtx):
        logging.debug('Trap received')
        self.traps_n += 1
        varBindsResolved = [rfc1902.ObjectType(rfc1902.ObjectIdentity(x[0]), x[1]).resolveWithMib(self.mibViewController) for x in varBinds]
        # Get an execution context and use inner SNMP engine data to figure out peer address
        execContext = snmpEngine.observer.getExecutionContext('rfc3412.receiveMessage:request')
        switch_ip = execContext['transportAddress'][0]
        (switch_name, _) = self.switch_ip_to_name_and_guid.get(switch_ip, (switch_ip, ""))

        description = ""
        for oid_obj, val_obj in varBindsResolved:
            oid = oid_obj.prettyPrint()
            val = val_obj.prettyPrint()
            logging.debug('  %s = %s' % (oid, val))
            if self.test_trap_oid in val:
                description = "test trap"
            if self.mellanox_oid in oid:
                description = val

        self.ip_to_event_to_count.setdefault(switch_ip, {}).setdefault(description, 0)
        self.ip_to_event_to_count[switch_ip][description] += 1
        logging.info('Notification from %s: %s' % (switch_name, description))

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
            multiple_events = []
            for switch_ip, event_to_count in self.ip_to_event_to_count.items():
                (switch_name, switch_guid) = self.switch_ip_to_name_and_guid.get(switch_ip, (switch_ip, ""))
                base_description = f"SNMP traps from {switch_name}: "
                description = ', '.join(f"'{event}' happened {count} times" for event, count in event_to_count.items())
                payload = {"event_id": self.event_id, "description": base_description + description}
                if switch_guid:
                    payload["object_name"] = switch_guid
                    payload["otype"] = "Switch"
                else:
                    logging.warning(f"Event from unknown switch")
                if ConfigParser.multiple_events:
                    # concatenate events into set to improve performance
                    multiple_events.append(payload)
                    if len(multiple_events) >= self.events_at_time:
                        tasks.append(asyncio.ensure_future(self.post_external_event(session, multiple_events)))
                        multiple_events = []
                    # sending rest events
                    tasks.append(asyncio.ensure_future(self.post_external_event(session, multiple_events)))
                else:
                    tasks.append(asyncio.ensure_future(self.post_external_event(session, payload)))
            await asyncio.gather(*tasks)

    async def post_external_event(self, session, payload):
        if not payload:
            return
        resource = "/app/events/external_event"
        if ConfigParser.multiple_events:
            resource += "?multiple_events=true"
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