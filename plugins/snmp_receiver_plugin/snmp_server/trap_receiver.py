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
import logging
from pysnmp.entity import engine, config
from pysnmp.carrier.asyncore.dgram import udp
from pysnmp.entity.rfc3413 import ntfrcv
import signal
import threading

from helpers import ConfigParser
import helpers
from plugin_registrator import PluginRegistrator


class SnmpTrapReceiver:
    def __init__(self):
        self.mellanox_oid = "1.3.6.1.4.1.33049"
        self.test_trap_oid = self.mellanox_oid + ".2.1.2.13"

        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        # # register plugin as traps receiver on every switch in the fabric
        # plugin_registrator = PluginRegistrator()
        # self.plugin_registration_thread = threading.Thread(target=plugin_registrator.run)
        # self.plugin_registration_thread.start()

        # Create SNMP engine with autogenernated engineID and pre-bound
        # to socket transport dispatcher
        self.snmpEngine = engine.SnmpEngine()
        self._setup_transport()
        self._setup_snmp_v1_v2c()

    def _setup_transport(self):
        # UDP over IPv4, first listening interface/port
        config.addTransport(self.snmpEngine, udp.domainName + (1,),
                            udp.UdpTransport().openServerMode((ConfigParser.snmp_ip, ConfigParser.snmp_port)))

    # noinspection PyUnusedLocal,PyUnusedLocal
    def trapCallback(self, snmpEngine, stateReference, contextEngineId, contextName,
              varBinds, cbCtx):
        # Get an execution context and use inner SNMP engine data to figure out peer address
        execContext = snmpEngine.observer.getExecutionContext('rfc3412.receiveMessage:request')
        switch_address = '@'.join([str(x) for x in execContext['transportAddress']])

        logging.info('Notification from %s, ContextEngineId "%s", ContextName "%s"' % (switch_address,
                                                                                       contextEngineId.prettyPrint(),
                                                                                       contextName.prettyPrint()))

        description = ""
        for oid_obj, val_obj in varBinds:
            oid = oid_obj.prettyPrint()
            val = val_obj.prettyPrint()
            logging.info('  %s = %s' % (oid, val))
            if val == self.test_trap_oid:
                description = "test trap"
            if self.mellanox_oid in oid:
                description = val

        # send trap as an external event to UFM
        self.send_external_event(f"SNMP trap from {switch_address}: {description}")

    def _setup_snmp_v1_v2c(self):
        # SecurityName <-> CommunityName mapping
        config.addV1System(self.snmpEngine, 'my-area', ConfigParser.community)

        # Register SNMP Application at the SNMP engine
        ntfrcv.NotificationReceiver(self.snmpEngine, self.trapCallback)

        self.snmpEngine.transportDispatcher.jobStarted(1)  # this job would never finish

    def send_external_event(self, description):
        resource = "/app/events/external_event"
        payload = {"event_id": 551, "description": description}
        response = helpers.post_request(resource, json=payload)
        logging.info(f"Post external event status code: {response.status_code},\nresponse: {response.text}")

    def run(self):
        # Run I/O dispatcher which would receive queries and send confirmations
        try:
            self.snmpEngine.transportDispatcher.runDispatcher()
        except:
            self.snmpEngine.transportDispatcher.closeDispatcher()
            raise


if __name__ == "__main__":
    snmp_traps_receiver = SnmpTrapReceiver()
    snmp_traps_receiver.run()