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
import configparser
import math
import pandas as pd
import numpy
from exclude_list import ExcludeList

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

class PDRAlgorithm:
    """
    This class is responsible for detection of ports that should be isolated or deisolated based on the telemetry data
    """
    def __init__(self, ufm_client: UFMCommunicator, exclude_list: ExcludeList, logger):
        self.ufm_client = ufm_client
        # {port_name: telemetry_data}
        self.ports_data = dict()
        self.ufm_latest_isolation_state = []

        pdr_config = configparser.ConfigParser()
        pdr_config.read(Constants.CONF_FILE)

        # Take from Conf
        self.interval = pdr_config.getint(Constants.CONF_SAMPLING, Constants.INTERVAL)
        self.tmax = pdr_config.getint(Constants.CONF_METRICS, Constants.TMAX)
        self.d_tmax = pdr_config.getint(Constants.CONF_METRICS, Constants.D_TMAX)
        self.max_pdr = pdr_config.getfloat(Constants.CONF_METRICS, Constants.MAX_PDR)
        self.configured_ber_check = pdr_config.getboolean(Constants.CONF_ISOLATION,Constants.CONFIGURED_BER_CHECK)
        self.deisolate_consider_time = pdr_config.getint(Constants.CONF_ISOLATION,Constants.DEISOLATE_CONSIDER_TIME)
        self.automatic_deisolate = pdr_config.getboolean(Constants.CONF_ISOLATION,Constants.AUTOMATIC_DEISOLATE)
        self.temp_check = pdr_config.getboolean(Constants.CONF_ISOLATION,Constants.CONFIGURED_TEMP_CHECK)
        self.link_down_isolation = pdr_config.getboolean(Constants.CONF_ISOLATION,Constants.LINK_DOWN_ISOLATION)
        self.test_mode = pdr_config.getboolean(Constants.CONF_COMMON,Constants.TEST_MODE, fallback=False)
        # Take from Conf
        self.logger = logger
        self.ber_intervals = Constants.BER_THRESHOLDS_INTERVALS if not self.test_mode else [[0.5 * 60, 3]]
        intervals = [x[0] for x in self.ber_intervals]
        self.min_ber_wait_time = min(intervals)
        self.max_ber_wait_time = max(intervals)
        self.max_ber_threshold = max([x[1] for x in self.ber_intervals])

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

        self.exclude_list = exclude_list

    def calc_max_ber_wait_time(self, min_threshold):
            """
            Calculates the maximum wait time for Bit Error Rate (BER) based on the given minimum threshold.

            Args:
                min_threshold (float): The minimum threshold for BER.

            Returns:
                float: The maximum wait time in seconds.
            """
            # min speed EDR = 32 Gb/s
            min_speed, min_width = 32 * 1024 * 1024 * 1024, 1
            min_port_rate = min_speed * min_width
            min_bits = float(format(float(min_threshold), '.0e').replace('-', ''))
            min_sec_to_wait = min_bits / min_port_rate
            return min_sec_to_wait

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

    def get_rate(self, port_obj, counter_name, new_val, timestamp):
        """
        Calculate the rate of the counter
        """
        counter_delta = 0
        if math.isclose(timestamp, port_obj.last_timestamp):
            # Return last saved value
            counter_delta = port_obj.counters_values.get(counter_name + "_rate", 0)
        else:
            old_val = port_obj.counters_values.get(counter_name)
            if old_val and new_val > old_val:
                counter_delta = (new_val - old_val) / (timestamp - port_obj.last_timestamp)

        if math.isclose(0, counter_delta):
            counter_delta = 0

        return counter_delta

    def get_rate_and_update(self, port_obj, counter_name, new_val, timestamp):
        """
        Calculate the rate of the counter and update the counters_values dictionary with the new value
        """
        # Calculate the rate
        counter_delta = self.get_rate(port_obj, counter_name, new_val, timestamp)
        # Update counters_values
        port_obj.counters_values[counter_name] = new_val
        port_obj.counters_values[counter_name + "_rate"] = counter_delta
        port_obj.counters_values[Constants.LAST_TIMESTAMP] = timestamp
        return counter_delta

    def find_peer_row_for_port(self, port_obj, ports_counters):
        """
        Retrieves peer row for given port
        """
        if not port_obj.peer or port_obj.peer == 'N/A':
            return None
        peer_guid, peer_num = port_obj.peer.split('_')
        # Fix peer guid format for future search
        if ports_counters[Constants.NODE_GUID].iloc[0].startswith('0x') and not peer_guid.startswith('0x'):
            peer_guid = f'0x{peer_guid}'
        #TODO check for a way to save peer row in data structure for performance
        peer_row_list = ports_counters.loc[(ports_counters[Constants.NODE_GUID] == peer_guid) & (ports_counters[Constants.PORT_NUMBER] == int(peer_num))]
        if peer_row_list.empty:
            self.logger.warning(f"Peer port {port_obj.peer} not found in ports data")
            return None
        peer_row = peer_row_list.iloc[0]
        return peer_row

    def calc_error_rate(self, port_obj, row, timestamp):
        """
        Calculate the error rate of the port and update the counters_values
        """
        rcv_error = get_counter(Constants.RCV_ERRORS_COUNTER, row)
        rcv_remote_phy_error = get_counter(Constants.RCV_REMOTE_PHY_ERROR_COUNTER, row)
        errors = rcv_error + rcv_remote_phy_error
        error_rate = self.get_rate_and_update(port_obj, Constants.ERRORS_COUNTER, errors, timestamp)
        return error_rate        

    def check_pdr_issue(self, port_obj, row, timestamp):
        """
        Check if the port passed the PacketDropRate threshold and return an issue
        """
        rcv_pkts = get_counter(Constants.RCV_PACKETS_COUNTER, row)
        rcv_pkt_rate = self.get_rate_and_update(port_obj, Constants.RCV_PACKETS_COUNTER, rcv_pkts, timestamp)
        error_rate = self.calc_error_rate(port_obj, row, timestamp)
        if rcv_pkt_rate and error_rate / rcv_pkt_rate > self.max_pdr:
            self.logger.info(f"Isolation issue ({Constants.ISSUE_PDR}) detected for port {port_obj.port_name}: "
                            f"error rate to packet rate ratio ({error_rate / rcv_pkt_rate}) is greater than MAX_PDR ({self.max_pdr}) "
                            f"for {rcv_pkts} of received packets")
            return Issue(port_obj.port_name, Constants.ISSUE_PDR)
        return None

    def check_temp_issue(self, port_obj, row, timestamp):
        """
        Check if the port passed the temperature threshold and return an issue
        """
        if not self.temp_check:
            return None
        cable_temp = get_counter(Constants.TEMP_COUNTER, row, default=None)
        if cable_temp is not None and not pd.isna(cable_temp):
            if cable_temp in ["NA", "N/A", "", "0C", "0"]:
                return None
            cable_temp = int(cable_temp.split("C")[0]) if type(cable_temp) == str else cable_temp
            old_cable_temp = port_obj.counters_values.get(Constants.TEMP_COUNTER, 0)
            port_obj.counters_values[Constants.TEMP_COUNTER] = cable_temp
            # Check temperature condition
            if cable_temp and (cable_temp > self.tmax):
                self.logger.info(f"Isolation issue ({Constants.ISSUE_OONOC}) detected for port {port_obj.port_name}: "
                                f"cable temperature ({cable_temp}) is higher than TMAX ({self.tmax})")
                return Issue(port_obj.port_name, Constants.ISSUE_OONOC)
            # Check temperature delta condition
            if old_cable_temp is not None and old_cable_temp != 0:
                delta_temp = abs(old_cable_temp - cable_temp)
                if delta_temp > self.d_tmax:
                    self.logger.info(f"Isolation issue ({Constants.ISSUE_OONOC}) detected for port {port_obj.port_name}: "
                                    f"cable temperature changed ({old_cable_temp} -> {cable_temp}): "
                                    f"the delta ({delta_temp}) is greater than D_TMAX ({self.d_tmax})")
                    return Issue(port_obj.port_name, Constants.ISSUE_OONOC)
        return None

    def check_link_down_issue(self, port_obj, row, timestamp, ports_counters):
        """
        Check if the port passed the link down threshold and return an issue
        """
        if not self.link_down_isolation:
            return None
        old_link_downed = port_obj.counters_values.get(Constants.LNK_DOWNED_COUNTER)
        link_downed = get_counter(Constants.LNK_DOWNED_COUNTER, row)
        link_downed_rate = self.get_rate_and_update(port_obj, Constants.LNK_DOWNED_COUNTER, link_downed, timestamp)
        if link_downed_rate > 0:
            # Check if the peer port link downed was raised
            peer_row = self.find_peer_row_for_port(port_obj, ports_counters)
            if peer_row is None:
                return None
            if self.exclude_list.contains(port_obj.peer):
                # The peer is excluded from analysis
                return None
            peer_row_timestamp = get_timestamp_seconds(peer_row)
            peer_link_downed = get_counter(Constants.LNK_DOWNED_COUNTER, peer_row)
            peer_obj = self.ports_data.get(port_obj.peer)
            if self.test_mode:
                peer_obj = port_obj
                # because we use the port obj we need to change the peer link is down.
                # it would have enter here only if there was a change, so the test mode is working
                peer_obj.counters_values[Constants.LNK_DOWNED_COUNTER] = peer_link_downed - 1
            if not peer_obj:
                return None
            peer_link_downed_rate = self.get_rate(peer_obj, Constants.LNK_DOWNED_COUNTER, peer_link_downed, peer_row_timestamp)
            if peer_link_downed_rate > 0:
                self.logger.info(f"Isolation issue ({Constants.ISSUE_LINK_DOWN}) detected for port {port_obj.port_name}: "
                                f"link down counter raised from {old_link_downed} to {link_downed} "
                                f"and its peer ({port_obj.peer}) link down rate is {peer_link_downed_rate}")
                return Issue(port_obj.port_name, Constants.ISSUE_LINK_DOWN)
        return None

    def check_ber_issue(self, port_obj, row, timestamp):
        """
        Check if the port passed the BER threshold and return an issue
        """
        if not self.configured_ber_check:
            return None
        symbol_ber_val = get_counter(Constants.PHY_SYMBOL_ERROR, row, default=None)
        if symbol_ber_val is not None:
            ber_data = {
                Constants.TIMESTAMP : timestamp,
                Constants.SYMBOL_BER : symbol_ber_val, 
            }
            port_obj.ber_tele_data.loc[len(port_obj.ber_tele_data)] = ber_data
            port_obj.last_symbol_ber_timestamp = timestamp
            port_obj.last_symbol_ber_val = symbol_ber_val
            if not port_obj.active_speed or not port_obj.port_width:
                port_obj.active_speed, port_obj.port_width = self.get_port_metadata(port_obj.port_name)
            if not port_obj.port_width:
                self.logger.debug(f"port width for port {port_obj.port_name} is None, can't verify it's BER values")
                return None
            for (interval, threshold) in self.ber_intervals:
                symbol_ber_rate = self.calc_ber_rates(port_obj.port_name, port_obj.active_speed, port_obj.port_width, interval)
                if symbol_ber_rate and symbol_ber_rate > threshold:
                    self.logger.info(f"Isolation issue ({Constants.ISSUE_BER}) detected for port {port_obj.port_name} (speed: {port_obj.active_speed}, width: {port_obj.port_width}): "
                                    f"symbol ber rate ({symbol_ber_rate}) is higher than threshold ({threshold})")
                    return Issue(port_obj.port_name, Constants.ISSUE_BER)
        return None

    def analyze_telemetry_data(self, ports_data, ports_counters):
        """
        Read the next set of ports and check if they have high BER, PDR, temperature or link downed issues
        Receives: detected ports, isolated ports and telemetry data
        Returns: lists of isolation candidates
        """
        self.ports_data = ports_data

        issues = {}
        for _, row in ports_counters.iterrows():
            port_name = f"{row.get(Constants.NODE_GUID, '').split('x')[-1]}_{row.get(Constants.PORT_NUMBER, '')}"
            if self.exclude_list.contains(port_name):
                # The port is excluded from analysis
                continue
            if self.test_mode:
                # Adding the port data upon fetching the first telemetry data
                if not self.ports_data.get(port_name):
                    self.ports_data[port_name] = PortData(port_name=port_name,peer="0x"+port_name)
            port_obj = self.ports_data.get(port_name)
            if not port_obj:
                if get_counter(Constants.RCV_PACKETS_COUNTER,row,0) == 0: # meaning it is down port
                    continue
                self.logger.warning("Port {0} not found in ports data".format(port_name))
                continue
            # Converting from micro seconds to seconds.
            timestamp = get_timestamp_seconds(row)
            #TODO add logs regarding the exact telemetry value leading to the decision
            pdr_issue = self.check_pdr_issue(port_obj, row, timestamp)
            temp_issue = self.check_temp_issue(port_obj, row, timestamp)
            link_downed_issue = self.check_link_down_issue(port_obj, row, timestamp, ports_counters)
            ber_issue = self.check_ber_issue(port_obj, row, timestamp)
            port_obj.last_timestamp = timestamp
            if pdr_issue:
                issues[port_name] = pdr_issue
            elif temp_issue:
                issues[port_name] = temp_issue
            elif link_downed_issue:
                issues[port_name] = link_downed_issue
            elif ber_issue:
                issues[port_name] = ber_issue
            # If out of operating conditions we'll overwrite the cause
            if self.temp_check and self.is_out_of_operating_conf(port_name):
                issues[port_name] = Constants.ISSUE_OONOC
        return list(issues.values())

    def check_deisolation_conditions(self, port_state):
        """
        Check if given port should be deisolated
        Function doesn't perform deisolation itself, just checks deisolation conditions only
        Return True if given port should be deisolated
        """
        state = port_state.get_state()
        cause = port_state.get_cause()
        # EZ: it is a state that say that some maintenance was done to the link 
        #     so need to re-evaluate if to return it to service
        # Deal with ports that with either cause = oonoc or fixed
        if not (self.automatic_deisolate or cause == Constants.ISSUE_OONOC or state == Constants.STATE_TREATED):
            return False
        
        # We don't deisolate those out of NOC
        port_name = port_state.name
        if self.is_out_of_operating_conf(port_name):
            return False

        if datetime.now() < port_state.get_change_time() + timedelta(seconds=self.deisolate_consider_time):
            # Too close to state change
            return False

        # TODO: check if it can be moved into BER issue detection
        port_obj = self.ports_data.get(port_name)
        if port_state.cause == Constants.ISSUE_BER:
            # Check if we are still above the threshold
            symbol_ber_rate = self.calc_ber_rates(port_name, port_obj.active_speed, port_obj.port_width, self.max_ber_wait_time + 1)
            if symbol_ber_rate and symbol_ber_rate > self.max_ber_threshold:
                cause = Constants.ISSUE_BER
                port_state.update(Constants.STATE_ISOLATED, cause)
                return False

        return True

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
