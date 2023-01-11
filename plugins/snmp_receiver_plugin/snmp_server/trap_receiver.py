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
import csv
import json
import logging
import os
from pysnmp.entity import engine, config
from pysnmp.carrier.asyncore.dgram import udp
from pysnmp.entity.rfc3413 import ntfrcv, context
from pysnmp.smi import builder, view, compiler, rfc1902
from pysnmp import proto
import threading
import time

import helpers
from resources import Switch


class SnmpTrapReceiver:
    def __init__(self, switch_dict={}):
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        self.snmp_engine = engine.SnmpEngine()
        self.switch_dict = switch_dict
        self._setup_transport()
        self._setup_snmp_v1_v2c()
        self.mib_builder = None
        self.mib_view_controller = None
        self._init_mib_controller()
        self.traps_n = 0
        self.st_t = 0
        self.events_at_time = 10
        self.throttling_interval = 10
        self.throttling_thread = None
        self.ip_to_trap_to_count = {}
        self.oid_to_traps_info = {}
        self._init_traps_info()

    def _init_traps_info(self):
        with open(helpers.TRAPS_POLICY_FILE, 'r') as traps_info_file:
            csv_traps_info = csv.DictReader(traps_info_file)
            for row in csv_traps_info:
                self.oid_to_traps_info[row['OID']] = row

    def _setup_transport(self):
        # UDP over IPv4, first listening interface/port
        config.addTransport(self.snmp_engine, udp.domainName + (1,),
                            udp.UdpTransport().openServerMode(
                                (helpers.ConfigParser.snmp_ip,
                                helpers.ConfigParser.snmp_port)))

    def _register_v3_switch(self, engine_id):
        # TODO: change to sha512 and aes-256
        config.addV3User(
            self.snmp_engine,
            helpers.SNMP_USER,
            config.usmHMACSHAAuthProtocol,
            helpers.SNMP_PASSWORD,
            config.usmAesCfb128Protocol,
            helpers.SNMP_PRIV_PASSWORD,
            proto.rfc1902.OctetString(hexValue=engine_id)
        )

    def _setup_snmp_v1_v2c(self):
        # SecurityName <-> CommunityName mapping
        if helpers.ConfigParser.snmp_version == 3:
            for switch_obj in self.switch_dict.values():
                self._register_v3_switch(switch_obj.engine_id)
        else:
            config.addV1System(self.snmp_engine, 'my-area', helpers.ConfigParser.community)

        if helpers.ConfigParser.snmp_mode == "auto":
            switches = list(self.switch_dict.keys())
            status_code, text = helpers.post_provisioning_api(Switch.get_cli(helpers.LOCAL_IP),
                                "Initial registration", switches)
            if not helpers.succeded(status_code):
                logging.error(f"Failed to auto register, status code: {status_code}, response: {text}")
            with open(helpers.SWITCHES_FILE, "w") as file:
                json.dump(switches, file)

        # Register SNMP Application at the SNMP engine
        ntfrcv.NotificationReceiver(self.snmp_engine, self.trap_callback)
        self.snmp_engine.transportDispatcher.jobStarted(1)  # this job would never finish

    def _init_mib_controller(self):
        # Assemble MIB viewer
        snmp_context = context.SnmpContext(self.snmp_engine)
        self.mib_builder = snmp_context.getMibInstrum().getMibBuilder()
        self.mib_builder = builder.MibBuilder()
        mib_dirs = ['../mibs/standard/',
                    '../mibs/private/']
        compiler.addMibCompiler(self.mib_builder, sources=mib_dirs)
        for mib in mib_dirs:
            self.mib_builder.addMibSources(builder.DirMibSource(mib))
        self.mib_view_controller = view.MibViewController(self.mib_builder)
        # Pre-load MIB modules
        # TODO: load all mibs
        self.mib_builder.loadModules('MELLANOX-EFM-MIB')

    # noinspection PyUnusedLocal,PyUnusedLocal
    def trap_callback(self, snmpEngine, stateReference, contextEngineId, contextName, varBinds, cbCtx):
        # TODO: stop listening to the traps that we don't need to
        logging.debug('Trap received')
        self.traps_n += 1
        varBindsResolved = [rfc1902.ObjectType(rfc1902.ObjectIdentity(x[0]), x[1]).resolveWithMib(self.mib_view_controller) for x in varBinds]
        # Get an execution context and use inner SNMP engine data to figure out peer address
        execContext = snmpEngine.observer.getExecutionContext('rfc3412.receiveMessage:request')
        switch_ip = execContext['transportAddress'][0]

        try:
            trap_oid = varBindsResolved[1][1].prettyPrint()
            trap_details = varBindsResolved[2][0].prettyPrint() + " = " + varBindsResolved[2][1].prettyPrint()
        except KeyError as ke:
            logging.info(f'Error while parsing varBindsResolved: {ke}')
            trap_oid = "unknown"
            trap_oid = "failed to decode trap"
        try:
            trap_info = self.oid_to_traps_info[trap_oid]
            severity = trap_info["Severity"]
        except:
            logging.info(f'Failed to decode trap: {trap_oid}')
            return
        trap = helpers.Trap(trap_oid, trap_details, severity)
        logging.debug(f'  {trap_oid}: {trap_details}')

        switch_obj = self.switch_dict.get(switch_ip, None)
        if not switch_obj:
            logging.warning(f'Notification from unknown ip {switch_ip}: {trap_oid}')
        else:
            logging.info(f'Notification from switch {switch_obj.name}: {trap_oid}')
        self.ip_to_trap_to_count.setdefault(switch_ip, {}).setdefault(trap, 0)
        self.ip_to_trap_to_count[switch_ip][trap] += 1

        if not self.throttling_thread:
            # TODO: figure out why it works only whtn the thread started in callbacks context
            self.throttling_thread = threading.Thread(target=self.throttle_events)
            self.throttling_thread.start()

    def throttle_events(self):
        while True:
            if not self.ip_to_trap_to_count:
                continue
            s_t = time.time()
            asyncio.run(self.send_events())
            e_t = time.time()
            throughput = self.traps_n / (e_t - s_t)
            logging.warning(f"Throughput is {throughput} traps/second")
            self.traps_n = 0
            time.sleep(self.throttling_interval)

    async def send_events(self):
        async with aiohttp.ClientSession(headers={"X-Remote-User": "ufmsystem"}) as session:
            tasks = []
            multiple_events = []
            ip_to_trap_to_count_copy = dict(self.ip_to_trap_to_count)
            self.ip_to_trap_to_count = {}
            for switch_ip, trap_to_count in ip_to_trap_to_count_copy.items():
                switch = self.switch_dict.get(switch_ip, helpers.Switch(switch_ip))
                base_description = f"SNMP traps from {switch.name}: "
                description = '; '.join(f"'oid={trap.oid}, {trap.details}', happened {count} times"
                                        for trap, count in trap_to_count.items())
                severity = helpers.Severity()
                for trap in trap_to_count.keys():
                    severity.update_level(trap.severity)
                payload = {"event_id": severity.event_id, "description": base_description + description}
                if switch.guid:
                    payload["object_name"] = switch.guid
                    payload["otype"] = "Switch"
                else:
                    logging.warning(f"Event from unknown switch")
                if helpers.ConfigParser.multiple_events:
                    # TODO: support multiple events correclty
                    payload["event_id"] = helpers.Severity.WARNING_ID
                    # concatenate events into set to improve performance
                    multiple_events.append(payload)
                    if len(multiple_events) >= self.events_at_time:
                        tasks.append(asyncio.ensure_future(self.post_external_event(session, multiple_events)))
                        multiple_events = []
                    # sending rest events
                    tasks.append(asyncio.ensure_future(self.post_external_event(session, multiple_events)))
                else:
                    tasks.append(asyncio.ensure_future(self.post_external_event(session, payload)))
                # clear events dict
            await asyncio.gather(*tasks)

    async def post_external_event(self, session, payload):
        if not payload:
            return
        resource = "/app/events/external_event"
        if helpers.ConfigParser.multiple_events:
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
            self.throttling_thread.join(timeout=self.throttling_interval)
            raise

if __name__ == "__main__":
    snmp_trap_receiver = SnmpTrapReceiver()
    snmp_trap_receiver.run()