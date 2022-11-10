#!/bin/bash
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
import configparser
import logging
from logging.handlers import RotatingFileHandler
import os
from pysnmp.entity import engine, config
from pysnmp.carrier.asyncore.dgram import udp
from pysnmp.entity.rfc3413 import ntfrcv
import threading

from helpers import send_external_event
from plugin_registrator import PluginRegistrator


class SnmpTrapReceiver:
    def __init__(self):
        self.description = "empty description"
        self.test_trap_oid = "1.3.6.1.4.1.33049.2.1.2.13"

        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        # register plugin as traps receiver on every switch in the fabric
        plugin_registrator = PluginRegistrator()
        self.plugin_registration_thread = threading.Thread(target=plugin_registrator.run)
        self.plugin_registration_thread.start()

        # self.config_file_name = "build/config/snmp.conf"
        self.config_file_name = "/config/snmp.conf"
        self._parse_config()

        # Create SNMP engine with autogenernated engineID and pre-bound
        # to socket transport dispatcher
        self.snmpEngine = engine.SnmpEngine()
        self._setup_transport()
        self._setup_snmp_v1_v2c()

    def _parse_config(self):
        snmp_config = configparser.ConfigParser()
        if os.path.exists(self.config_file_name):
            snmp_config.read(self.config_file_name)
            self.log_file_path = snmp_config.get("Log", "log_file_path")
            self.log_level = snmp_config.get("Log", "log_level")
            self.log_file_max_size = snmp_config.getint("Log", "log_file_max_size")
            self.log_file_backup_count = snmp_config.getint("Log", "log_file_backup_count")

            log_format = '%(asctime)-15s %(levelname)s %(message)s'
            logging.basicConfig(handlers=[RotatingFileHandler(self.log_file_path,
                                                              maxBytes=self.log_file_max_size,
                                                              backupCount=self.log_file_backup_count)],
                                level=logging.getLevelName(self.log_level),
                                format=log_format)

            self.ip = snmp_config.get("Common", "ip")
            self.port = snmp_config.getint("Common", "port")
        else:
            logging.error(f"No config file {self.config_file_name} found!")

    def _setup_transport(self):
        # UDP over IPv4, first listening interface/port
        config.addTransport(self.snmpEngine, udp.domainName + (1,),
                            udp.UdpTransport().openServerMode((self.ip, self.port)))

    # noinspection PyUnusedLocal,PyUnusedLocal
    def trapCallback(self, snmpEngine, stateReference, contextEngineId, contextName,
              varBinds, cbCtx):
        # Get an execution context and use inner SNMP engine data to figure out peer address
        execContext = snmpEngine.observer.getExecutionContext('rfc3412.receiveMessage:request')
        switch_address = '@'.join([str(x) for x in execContext['transportAddress']])

        logging.info('Notification from %s, ContextEngineId "%s", ContextName "%s"' % (switch_address,
                                                                                       contextEngineId.prettyPrint(),
                                                                                       contextName.prettyPrint()))

        for name, val in varBinds:
            logging.info('  %s = %s' % (name.prettyPrint(), val.prettyPrint()))
            if val.prettyPrint() == self.test_trap_oid:
                self.description = "test trap"
        # send trap as an external event to UFM
        send_external_event(f"SNMP trap from {switch_address}: {self.description}")

    def _setup_snmp_v1_v2c(self):
        # SecurityName <-> CommunityName mapping
        config.addV1System(self.snmpEngine, 'my-area', 'public')

        # Register SNMP Application at the SNMP engine
        ntfrcv.NotificationReceiver(self.snmpEngine, self.trapCallback)

        self.snmpEngine.transportDispatcher.jobStarted(1)  # this job would never finish

    def run(self):
        # Run I/O dispatcher which would receive queries and send confirmations
        try:
            self.snmpEngine.transportDispatcher.runDispatcher()
        except:
            self.snmpEngine.transportDispatcher.closeDispatcher()
            self.plugin_registration_thread.join()
            raise


if __name__ == "__main__":
    snmp_traps_receiver = SnmpTrapReceiver()
    snmp_traps_receiver.run()