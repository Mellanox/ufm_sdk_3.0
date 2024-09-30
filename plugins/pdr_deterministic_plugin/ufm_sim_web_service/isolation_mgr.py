#
# Copyright © 2013-2023 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
#
from datetime import datetime, timedelta
import traceback
import time
import http
import configparser
import pandas as pd
from exclude_list import ExcludeList
from pdr_algorithm import PortData, IsolatedPort, PDRAlgorithm

from constants import PDRConstants as Constants
from telemetry_collector import TelemetryCollector
from ufm_communication_mgr import UFMCommunicator
from data_store import DataStore

class PortReset:
    """
    Represents the port reset info.
    """
    def __init__(self, port_name):
        """
        Initialize a new instance of the PortReset class.
        """
        self.port_name = port_name
        self.reset_time = datetime.min
        self.reset_count = 0

#pylint: disable=too-many-instance-attributes
class IsolationMgr:
    '''
    This class is responsible for managing the isolation of ports based on the telemetry data
    '''

    def __init__(self, ufm_client: UFMCommunicator, logger):
        self.ufm_client = ufm_client
        # {port_name: IsolatedPort}
        self.isolated_ports = {}
        # {port_name: telemetry_data}
        self.ports_data = {}
        # {port_name: PortReset}
        self.ports_resets = {}
        self.ufm_latest_isolation_state = []

        pdr_config = configparser.ConfigParser()
        pdr_config.read(Constants.CONF_FILE)

        # Take from Conf
        self.interval = pdr_config.getint(Constants.CONF_SAMPLING, Constants.INTERVAL)
        self.max_num_isolate = pdr_config.getint(Constants.CONF_ISOLATION, Constants.MAX_NUM_ISOLATE)
        self.dry_run = pdr_config.getboolean(Constants.CONF_ISOLATION, Constants.DRY_RUN)
        self.do_deisolate = pdr_config.getboolean(Constants.CONF_ISOLATION, Constants.DO_DEISOLATION)
        self.switch_hca_isolation = pdr_config.getboolean(Constants.CONF_ISOLATION, Constants.SWITCH_TO_HOST_ISOLATION)
        self.test_mode = pdr_config.getboolean(Constants.CONF_COMMON, Constants.TEST_MODE, fallback=False)
        self.max_port_reset_num = pdr_config.getint(Constants.CONF_RESET, Constants.MAX_PORT_RESET_NUM, fallback=2)
        self.port_reset_interval = timedelta(seconds=pdr_config.getint(Constants.CONF_RESET,
                                                                       Constants.PORT_RESET_INTERVAL_SECONDS,
                                                                       fallback=7*24*3600)) # default is 1 week in seconds

        self.test_iteration = 0
        self.logger = logger
        self.data_store = DataStore(self.logger)
        self.telemetry_collector = TelemetryCollector(self.test_mode,logger,self.data_store)
        self.exclude_list = ExcludeList(self.logger)
        self.pdr_alg = PDRAlgorithm(self.ufm_client, self.exclude_list, self.logger, pdr_config)

    def eval_isolation(self, port_name, cause):
        """
        Evaluates the isolation of a port based on the given port name and cause.

        Args:
            port_name (str): The name of the port to evaluate isolation for.
            cause (str): The cause of the isolation.

        Returns:
            None
        """
        if self.exclude_list.contains(port_name):
            self.logger.info(f"Skipping isolation of port {port_name}")
            return

        self.logger.info(f"Evaluating isolation of port {port_name} with cause {cause}")
        if port_name in self.ufm_latest_isolation_state:
            self.logger.info("Port is already isolated. skipping...")
            return
        port_obj = self.ports_data.get(port_name)
        if not port_obj:
            self.logger.warning(f"Port {port_name} not found in ports data")
            return
        # TODO: check if we need to check the peer as well
        if port_obj.node_type == Constants.NODE_TYPE_COMPUTER and not self.switch_hca_isolation:
            self.logger.info(f"Port {port_name} is a computer port. skipping...")
            return

        if not self.dry_run:
            # Isolate port
            ret = self.ufm_client.isolate_port(port_name)
            if not ret or ret.status_code != http.HTTPStatus.OK:
                self.logger.warning("Failed isolating port: %s with cause: %s... status_code= %s", port_name, cause, ret.status_code)
                return
            # Reset port
            self.reset_port(port_name, port_obj.port_guid)
        isolated_port = self.isolated_ports.get(port_name)
        if not isolated_port:
            self.isolated_ports[port_name] = IsolatedPort(port_name)
        self.isolated_ports[port_name].update(cause)

        log_message = f"Isolated port: {port_name} cause: {cause}. dry_run: {self.dry_run}"
        self.logger.warning(log_message)
        if not self.test_mode:
            self.ufm_client.send_event(log_message, event_id=Constants.EXTERNAL_EVENT_ALERT, external_event_name="Isolating Port")

    def reset_port(self, port_name, port_guid):
        """
        Reset port if reset limit is not not exceeded
        """
        # Check if reset is allowed
        reset_history = self.ports_resets.get(port_name)
        if reset_history:
            if datetime.now() - reset_history.reset_time > self.port_reset_interval:
                # Passed too much time from last reset: clean reset history and allow resets
                del self.ports_resets[port_name]
            elif reset_history.reset_count >= self.max_port_reset_num:
                # Exceeds reset limit
                self.logger.info("Skipping reset of port: %s... reset limit exceeded", port_name)
                return

        # Perform reset
        ret = self.ufm_client.reset_port(port_name, port_guid)
        if not ret or ret.status_code != http.HTTPStatus.ACCEPTED:
            self.logger.warning("Failed resetting port: %s... status_code= %s", port_name, ret.status_code)
            return

        # Update port resets history
        reset_history = self.ports_resets.get(port_name)
        if not reset_history:
            reset_history = PortReset(port_name)
            self.ports_resets[port_name] = reset_history

        reset_history.reset_count += 1
        reset_history.reset_time = datetime.now()
        self.logger.info("Resetting port: %s... reset_count= %s", port_name, reset_history.reset_count)

    def eval_deisolate(self, port_name):
        """
        Evaluates the deisolation of a port.

        Args:
            port_name (str): The name of the port to evaluate.

        Returns:
            None
        """
        if self.exclude_list.contains(port_name):
            self.logger.info(f"Skipping deisolation of port {port_name}")
            return

        self.logger.info(f"Evaluating deisolation of port {port_name}")
        if not port_name in self.ufm_latest_isolation_state and not self.dry_run:
            if port_name in self.isolated_ports:
                self.isolated_ports.pop(port_name)
            return

        # port is clean now - de-isolate it
        # using UFM "mark as healthy" API - PUT /ufmRestV2/app/unhealthy_ports
            # {
            # "ports": [
            #     "e41d2d0300062380_3"
            # ],
            # "ports_policy": "HEALTHY"
            # }
        if not self.dry_run:
            ret = self.ufm_client.deisolate_port(port_name)
            if not ret or ret.status_code != http.HTTPStatus.OK:
                self.logger.warning("Failed deisolating port: %s with cause: %s... status_code= %s",\
                                     port_name, self.isolated_ports[port_name].cause, ret.status_code)
                return
        self.isolated_ports.pop(port_name)
        log_message = f"Deisolated port: {port_name}. dry_run: {self.dry_run}"
        self.logger.warning(log_message)
        if not self.test_mode:
            self.ufm_client.send_event(log_message, event_id=Constants.EXTERNAL_EVENT_NOTICE, external_event_name="Deisolating Port")

    # called first time to get all the metadata of the telemetry.
    def get_ports_metadata(self):
        """
        Retrieves the metadata for all ports.

        Returns:
            None: If test mode is enabled.
            dict: A dictionary containing the metadata for each port.
        """
        if self.test_mode:
            # we need to skip this check and put the data on the telemetry side.
            return
        meta_data = self.ufm_client.get_ports_metadata()
        if meta_data and len(meta_data) > 0:
            for port in meta_data:
                port_name = port.get(Constants.PORT_NAME)
                if not self.ports_data.get(port_name):
                    self.ports_data[port_name] = PortData(port_name)
                self.update_port_metadata(port_name, port)

    def update_port_metadata(self, port_name, port):
        """
        Update the metadata of a port.

        Args:
            port_name (str): The name of the port.
            port (dict): The port information.

        Returns:
            None
        """
        port_obj = self.ports_data[port_name]
        port_obj.active_speed = port.get(Constants.ACTIVE_SPEED)
        port_obj.port_guid = port.get(Constants.SYSTEM_ID)
        port_obj.peer = port.get(Constants.PEER)
        port_obj.ber_tele_data = pd.DataFrame(columns=[Constants.TIMESTAMP, Constants.SYMBOL_BER])
        if "Computer IB Port" in port.get(Constants.DESCRIPTION):
            port_obj.port_num = 1
            port_obj.node_type = Constants.NODE_TYPE_COMPUTER
        else:
            port_obj.port_num = port.get(Constants.EXTERNAL_NUMBER)
            port_obj.node_type = Constants.NODE_TYPE_OTHER
        port_width = port.get(Constants.WIDTH)
        if port_width:
            port_width = int(port_width.strip('x'))
        port_obj.port_width = port_width


    def update_ports_data(self):
        """
        Updates the ports data by retrieving metadata from the UFM client.

        Returns:
            bool: True if ports data is updated, False otherwise.
        """
        if self.test_mode:
            return False
        meta_data = self.ufm_client.get_ports_metadata()
        ports_updated = False
        if meta_data and len(meta_data) > 0:
            for port in meta_data:
                port_name = port.get(Constants.PORT_NAME)
                if not self.ports_data.get(port_name):
                    self.ports_data[port_name] = {}
                    self.update_port_metadata(port_name, port)
                    ports_updated = True
        return ports_updated

    def get_isolation_state(self):
        """
        Retrieves the isolation state of the ports.

        Returns:
            None: If the test mode is enabled.
            List[str]: A list of isolated ports if available.
        """

        if self.test_mode:
            # I don't want to get to the isolated ports because we simulating everything..
            return
        ports = self.ufm_client.get_isolated_ports()
        if not ports:
            self.ufm_latest_isolation_state = []
        isolated_port_names = [port.split('x')[-1] for port in ports.get(Constants.API_ISOLATED_PORTS, [])]
        self.ufm_latest_isolation_state = isolated_port_names
        for port_name in isolated_port_names:
            if not self.isolated_ports.get(port_name):
                isolated_port = IsolatedPort(port_name)
                isolated_port.update(Constants.ISSUE_OONOC)
                self.isolated_ports[port_name] = isolated_port

    def get_requested_guids(self):
        """
        Get the requested GUIDs and their corresponding ports.

        Returns:
            list: A list of dictionaries, where each dictionary contains the GUID and its associated ports.
        """
        guids = {}
        for port in self.ports_data.values():
            sys_guid = port.port_guid
            if sys_guid in guids:
                guids[sys_guid].append(port.port_num)
            else:
                guids[sys_guid] = [port.port_num]
        requested_guids = [{"guid": sys_guid, "ports": ports} for sys_guid, ports in guids.items()]
        return requested_guids

    #pylint: disable=too-many-branches
    def main_flow(self):
        """
        Executes the main flow of the Isolation Manager.

        This method synchronizes with the telemetry clock, retrieves ports metadata,
        continuously retrieves telemetry data from secondary telemetry to
        determine the states of the ports. skips isolation if too many ports are detected as unhealthy, and evaluates
        isolation and deisolation for reported issues and ports with specific causes.

        Args:
            None

        Returns:
            None
        """
        self.logger.info("Isolation Manager initialized, starting isolation loop")
        self.get_ports_metadata()
        self.logger.info("Retrieved ports metadata")
        #pylint: disable=too-many-nested-blocks
        while True:
            try:
                t_begin = time.time()
                self.exclude_list.refresh()
                self.get_isolation_state()
                self.data_store.clean_old_files()

                issues = None
                # Get telemetry data
                if not self.test_mode:
                    self.logger.info("Retrieving telemetry data to determine ports' states")
                else:
                    self.logger.info(f"Retrieving test mode telemetry data to determine ports' states: iteration {self.test_iteration}")
                    self.test_iteration += 1
                try:
                    ports_counters = self.telemetry_collector.get_telemetry()
                    if ports_counters is None:
                        self.logger.error("Couldn't retrieve telemetry data")
                    else:
                        # Detect ports to be isolated or deisolated
                        self.logger.info("Starting telemetry data analysis")
                        issues = self.pdr_alg.analyze_telemetry_data(self.ports_data, ports_counters)
                except (KeyError, TypeError, ValueError) as exception_error:
                    self.logger.error(f"Failed to read information with error {exception_error}")

                # deal with reported new issues
                for issue in issues or []:
                    # ensure we are not ecxeeding allowed number of isolated ports
                    if len(self.isolated_ports) >= self.max_num_isolate:
                        # UFM send external event and break
                        event_msg = ("Reached muximum allowed number of isolated ports "
                                    f"({len(self.isolated_ports)}), skipping isolation")
                        self.logger.warning(event_msg)
                        if not self.test_mode:
                            self.ufm_client.send_event(event_msg, event_id=Constants.EXTERNAL_EVENT_ALERT,
                                                       external_event_name="Skipping isolation")
                        break

                    # isolate port
                    port = issue.port
                    cause = issue.cause # ber|pdr|oonoc|link_down
                    self.eval_isolation(port, cause)

                # deisolate ports
                if self.do_deisolate:
                    for isolated_port in list(self.isolated_ports.values()):
                        if self.pdr_alg.check_deisolation_conditions(isolated_port):
                            self.eval_deisolate(isolated_port.name)

                self.update_ports_data()
                t_end = time.time()
            #pylint: disable=broad-except
            except Exception as exception:
                self.logger.warning("Error in main loop")
                self.logger.warning(exception)
                traceback_err = traceback.format_exc()
                self.logger.warning(traceback_err)
                t_end = time.time()
            time.sleep(max(1, self.interval - (t_end - t_begin)))
