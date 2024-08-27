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
import traceback
from datetime import datetime
from datetime import timedelta
import time
import http
import configparser
import math
import json
import pandas as pd
import numpy
from exclude_list import ExcludeList
from plugins.pdr_deterministic_plugin.ufm_sim_web_service.pdr_algorithm import PDRAlgorithm

from constants import PDRConstants as Constants
from ufm_communication_mgr import UFMCommunicator
# should actually be persistent and thread safe dictionary pf PortStates

class PortData(object):
    """
    Represents the port data.
    """
    def __init__(self, port_name=None, port_num=None, peer=None, node_type=None, active_speed=None, port_width=None, port_guid=None):
        """
        Initialize a new instance of the PortData class.

        Args:
            port_name (str): The name of the port.
            port_num (int): The number of the port.
            peer (str): The peer of the port.
            node_type (str): The type of the node.
            active_speed (str): The active speed of the port.
            port_width (int): The width of the port.
            port_guid (str): The GUID of the port.
        """
        self.counters_values = {}
        self.node_type = node_type
        self.peer = peer
        self.port_name = port_name
        self.port_num = port_num
        self.last_timestamp = 0.0 # seconds as float
        self.active_speed = active_speed
        self.port_width = port_width
        self.port_guid = port_guid
        self.ber_tele_data = pd.DataFrame(columns=[Constants.TIMESTAMP, Constants.SYMBOL_BER])
        self.last_symbol_ber_timestamp = None
        self.last_symbol_ber_val = None



class PortState(object):
    """
    Represents the state of a port.

    Attributes:
        name (str): The name of the port.
        state (str): The current state of the port (isolated or treated).
        cause (str): The cause of the state change (oonoc, pdr, ber).
        maybe_fixed (bool): Indicates if the port may have been fixed.
        change_time (datetime): The time of the last state change.
    """

    def __init__(self, name):
        """
        Initialize a new instance of the PortState class.

        :param name: The name of the port.
        """
        self.name = name
        self.state = Constants.STATE_NORMAL # isolated | treated
        self.cause = Constants.ISSUE_INIT # oonoc, pdr, ber
        self.maybe_fixed = False
        self.change_time = datetime.now()

    def update(self, state, cause):
        """
        Update the state and cause of the port.

        :param state: The new state of the port.
        :param cause: The cause of the state change.
        """
        self.state = state
        self.cause = cause
        self.change_time = datetime.now()

    def get_cause(self):
        """
        Get the cause of the state change.

        :return: The cause of the state change.
        """
        return self.cause

    def get_state(self):
        """
        Get the current state of the port.

        :return: The current state of the port.
        """
        return self.state

    def get_change_time(self):
        """
        Get the time of the last state change.

        :return: The time of the last state change.
        """
        return self.change_time


class Issue(object):
    """
    Represents an issue that occurred on a specific port.

    Attributes:
        port (int): The port where the issue occurred.
        cause (str): The cause of the issue.
    """

    def __init__(self, port, cause):
        """
        Initialize a new instance of the Issue class.

        :param port: The port where the issue occurred.
        :param cause: The cause of the issue.
        """
        self.cause = cause
        self.port = port

def get_counter(counter_name, row, default=0):
    """
    Get the value of a specific counter from a row of data. If the counter is not present 
    or its value is NaN, return a default value.

    :param counter_name: The name of the counter to get.
    :param row: The row of data from which to get the counter.
    :param default: The default value to return if the counter is not present or its value is NaN.
    :return: The value of the counter, or the default value if the counter is not present
     or its value is NaN.
    """
    try:
        val = row.get(counter_name) if (row.get(counter_name) is not None and not pd.isna(row.get(counter_name))) else default
    except Exception as e:
        return default
    return val

def get_timestamp_seconds(row):
    '''
    Converting from micro seconds to seconds as float
    '''
    return row.get(Constants.TIMESTAMP) / 1000.0 / 1000.0

class IsolationMgr:
    '''
    This class is responsible for managing the isolation of ports based on the telemetry data
    '''

    def __init__(self, ufm_client: UFMCommunicator, logger):
        self.ufm_client = ufm_client
        # {port_name: PortState}
        self.ports_states = dict()
        # {port_name: telemetry_data}
        self.ports_data = dict()
        self.ufm_latest_isolation_state = []

        pdr_config = configparser.ConfigParser()
        pdr_config.read(Constants.CONF_FILE)

        # Take from Conf
        self.interval = pdr_config.getint(Constants.CONF_SAMPLING, Constants.INTERVAL)
        self.max_num_isolate = pdr_config.getint(Constants.CONF_ISOLATION, Constants.MAX_NUM_ISOLATE)
        self.tmax = pdr_config.getint(Constants.CONF_METRICS, Constants.TMAX)
        self.d_tmax = pdr_config.getint(Constants.CONF_METRICS, Constants.D_TMAX)
        self.max_pdr = pdr_config.getfloat(Constants.CONF_METRICS, Constants.MAX_PDR)
        self.configured_ber_check = pdr_config.getboolean(Constants.CONF_ISOLATION,Constants.CONFIGURED_BER_CHECK)
        self.dry_run = pdr_config.getboolean(Constants.CONF_ISOLATION,Constants.DRY_RUN)
        self.do_deisolate = pdr_config.getboolean(Constants.CONF_ISOLATION,Constants.DO_DEISOLATION)
        self.deisolate_consider_time = pdr_config.getint(Constants.CONF_ISOLATION,Constants.DEISOLATE_CONSIDER_TIME)
        self.automatic_deisolate = pdr_config.getboolean(Constants.CONF_ISOLATION,Constants.AUTOMATIC_DEISOLATE)
        self.temp_check = pdr_config.getboolean(Constants.CONF_ISOLATION,Constants.CONFIGURED_TEMP_CHECK)
        self.link_down_isolation = pdr_config.getboolean(Constants.CONF_ISOLATION,Constants.LINK_DOWN_ISOLATION)
        self.switch_hca_isolation = pdr_config.getboolean(Constants.CONF_ISOLATION,Constants.SWITCH_TO_HOST_ISOLATION)
        self.test_mode = pdr_config.getboolean(Constants.CONF_COMMON,Constants.TEST_MODE, fallback=False)
        self.test_iteration = 0
        # Take from Conf
        self.logger = logger
        self.ber_intervals = Constants.BER_THRESHOLDS_INTERVALS if not self.test_mode else [[0.5 * 60, 3]]
        intervals = [x[0] for x in self.ber_intervals]
        self.min_ber_wait_time = min(intervals)
        self.max_ber_wait_time = max(intervals)
        self.max_ber_threshold = max([x[1] for x in self.ber_intervals])

        self.start_time = time.time()
        self.max_time = self.start_time
        self.ber_tele_data = pd.DataFrame(columns=[Constants.TIMESTAMP, Constants.SYMBOL_BER, Constants.PORT_NAME])
        self.speed_types = {
            "FDR": 14,
            "EDR": 25,
            "HDR": 50,
            "NDR": 100,
            }
        self.telemetry_counters = [
            Constants.PHY_SYMBOL_ERROR,
            Constants.RCV_PACKETS_COUNTER,
            Constants.RCV_ERRORS_COUNTER,
            Constants.RCV_REMOTE_PHY_ERROR_COUNTER,
            Constants.TEMP_COUNTER,
            Constants.LNK_DOWNED_COUNTER,
        ]

        self.exclude_list = ExcludeList(self.logger)

    def is_out_of_operating_conf(self, port_name):
        """
        Checks if a port is out of operating configuration based on its temperature.

        Args:
            port_name (str): The name of the port to check.

        Returns:
            bool: True if the port is out of operating configuration, False otherwise.
        """
        port_obj = self.ports_data.get(port_name)
        if not port_obj:
            self.logger.warning(f"Port {port_name} not found in ports data in calculation of oonoc port")
            return
        temp = port_obj.counters_values.get(Constants.TEMP_COUNTER)
        if temp and temp > self.tmax:
            return True
        return False

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
        # if out of operating conditions we ignore the cause
        if self.temp_check and self.is_out_of_operating_conf(port_name):
            cause = Constants.ISSUE_OONOC

        if not self.dry_run:
            ret = self.ufm_client.isolate_port(port_name)
            if not ret or ret.status_code != http.HTTPStatus.OK:
                self.logger.warning("Failed isolating port: %s with cause: %s... status_code= %s", port_name, cause, ret.status_code)
                return
        port_state = self.ports_states.get(port_name)
        if not port_state:
            self.ports_states[port_name] = PortState(port_name)
        self.ports_states[port_name].update(Constants.STATE_ISOLATED, cause)

        log_message = f"Isolated port: {port_name} cause: {cause}. dry_run: {self.dry_run}"
        self.logger.warning(log_message)
        if not self.test_mode:
            self.ufm_client.send_event(log_message, event_id=Constants.EXTERNAL_EVENT_ALERT, external_event_name="Isolating Port")


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
            if self.ports_states.get(port_name):
                self.ports_states.pop(port_name)
            return
        # we dont return those out of NOC
        if self.is_out_of_operating_conf(port_name):
            cause = Constants.ISSUE_OONOC
            self.ports_states[port_name].update(Constants.STATE_ISOLATED, cause)
            return
        # we need some time after the change in state
        elif datetime.now() >= self.ports_states[port_name].get_change_time() + timedelta(seconds=self.deisolate_consider_time):
            port_obj = self.ports_data.get(port_name)
            port_state = self.ports_states.get(port_name)
            if port_state.cause == Constants.ISSUE_BER:
                # check if we are still above the threshold
                symbol_ber_rate = self.calc_ber_rates(port_name, port_obj.active_speed, port_obj.port_width, self.max_ber_wait_time + 1)
                if symbol_ber_rate and symbol_ber_rate > self.max_ber_threshold:
                    cause = Constants.ISSUE_BER
                    self.ports_states[port_name].update(Constants.STATE_ISOLATED, cause)
                    return
        else:
            # too close to state change
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
                self.logger.warning("Failed deisolating port: %s with cause: %s... status_code= %s", port_name, self.ports_states[port_name].cause, ret.status_code)        
                return
        self.ports_states.pop(port_name)
        log_message = f"Deisolated port: {port_name}. dry_run: {self.dry_run}"
        self.logger.warning(log_message)
        if not self.test_mode:
            self.ufm_client.send_event(log_message, event_id=Constants.EXTERNAL_EVENT_NOTICE, external_event_name="Deisolating Port")

    def calc_symbol_ber_rate(self, port_name, port_speed, port_width, col_name, time_delta):
        """
        calculate the symbol BER rate for a given port given the time delta
        """
        try:
            if port_speed != "NDR":
                # BER calculations is only relevant for NDR
                return 0
            port_obj  = self.ports_data.get(port_name)
            ber_data = port_obj.ber_tele_data
            if not port_obj.last_symbol_ber_val or ber_data.empty:
                return 0
            # Calculate the adjusted time delta, rounded up to the nearest sample interval
            adjusted_time_delta = numpy.ceil(time_delta / self.interval) * self.interval

            compare_timestamp = port_obj.last_symbol_ber_timestamp - adjusted_time_delta
            # Find the sample closest to, but not less than, the calculated compare_timestamp
            comparison_df = ber_data[ber_data[Constants.TIMESTAMP] <= compare_timestamp]
            if comparison_df.empty:
                return 0

            comparison_idx = comparison_df[Constants.TIMESTAMP].idxmax()
            comparison_sample = comparison_df.loc[comparison_idx]

            # Calculate the delta of 'symbol_ber'
            delta = port_obj.last_symbol_ber_val - comparison_sample[Constants.SYMBOL_BER]
            actual_speed = self.speed_types.get(port_speed, 100000)
            return delta / ((port_obj.last_symbol_ber_timestamp - comparison_df.loc[comparison_idx][Constants.TIMESTAMP]) * actual_speed * port_width * 1024 * 1024 * 1024)

        except Exception as e:
            self.logger.error(f"Error calculating {col_name}, error: {e}")
            return 0

    def calc_ber_rates(self, port_name, port_speed, port_width, time_delta):
        """
        Calculate the Bit Error Rate (BER) rates for a given port.

        Args:
            port_name (str): The name of the port.
            port_speed (int): The speed of the port in Gbps.
            port_width (int): The width of the port in bits.
            time_delta (float): The time difference for calculating the BER rates.

        Returns:
            float: The symbol rate.

        """
        symbol_rate = self.calc_symbol_ber_rate(port_name, port_speed, port_width, Constants.SYMBOL_BER, time_delta)
        return symbol_rate

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

    def get_port_metadata(self, port_name):
        """
        Retrieves the metadata for a given port.

        Args:
            port_name (str): The name of the port.

        Returns:
            tuple: A tuple containing the port speed and width.

        Raises:
            None
        """
        if self.test_mode:
            # all the switches have the same data for the testing
            return "NDR", 4
        meta_data = self.ufm_client.get_port_metadata(port_name)
        if meta_data and len(meta_data) > 0:
            port_data = meta_data[0]
            port_speed = port_data.get(Constants.ACTIVE_SPEED)
            port_width = port_data.get(Constants.WIDTH)
            if port_width:
                port_width = int(port_width.strip('x'))
            return port_speed, port_width
    
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
        isolated_ports = [port.split('x')[-1] for port in ports.get(Constants.API_ISOLATED_PORTS, [])]
        self.ufm_latest_isolation_state = isolated_ports
        for port in isolated_ports:
            if not self.ports_states.get(port):
                port_state = PortState(port)
                port_state.update(Constants.STATE_ISOLATED, Constants.ISSUE_OONOC)
                self.ports_states[port] = port_state

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
        pdr_alg = PDRAlgorithm(self.ufm_client, self.logger)
        while(True):
            try:
                t_begin = time.time()
                self.exclude_list.refresh()
                self.get_isolation_state()
                if not self.test_mode:
                    self.logger.info("Retrieving telemetry data to determine ports' states")
                else:
                    self.logger.info(f"Retrieving test mode telemetry data to determine ports' states: iteration {self.test_iteration}")
                    self.test_iteration += 1

                issues = None
                try:
                    ports_counters = self.ufm_client.get_telemetry(self.test_mode)
                    if ports_counters is None:
                        self.logger.error("Couldn't retrieve telemetry data")
                    else:
                        issues, deisolate_ports = pdr_alg.apply_algorithm(self.ports_data, self.ports_states, ports_counters)
                except (KeyError,) as e:
                    self.logger.error(f"Failed to read information with error {e}")

                if issues:
                    if len(issues) > self.max_num_isolate:
                        # UFM send external event
                        event_msg = "got too many ports detected as unhealthy: %d, skipping isolation" % len(issues)
                        self.logger.warning(event_msg)
                        if not self.test_mode:
                            self.ufm_client.send_event(event_msg, event_id=Constants.EXTERNAL_EVENT_ALERT, external_event_name="Skipping isolation")

                    # deal with reported new issues
                    else:
                        for issue in issues:
                            port = issue.port
                            cause = issue.cause # ber|pdr|oonoc|link_down
                            self.eval_isolation(port, cause)

                    # deal with ports that with either cause = oonoc or fixed
                    if self.do_deisolate:
                        for port_state in list(self.ports_states.values()):
                            state = port_state.get_state()
                            cause = port_state.get_cause()
                            # EZ: it is a state that say that some maintenance was done to the link 
                            #     so need to re-evaluate if to return it to service
                            if self.automatic_deisolate or cause == Constants.ISSUE_OONOC or state == Constants.STATE_TREATED:
                                self.eval_deisolate(port_state.name)
                    ports_updated = self.update_ports_data()
                    if ports_updated:
                        self.update_telemetry_session()
                t_end = time.time()
            except Exception as e:
                self.logger.warning("Error in main loop")
                self.logger.warning(e)
                traceback_err = traceback.format_exc()
                self.logger.warning(traceback_err)
                t_end = time.time()      
            time.sleep(max(1, self.interval - (t_end - t_begin)))
