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
import configparser
import pandas as pd
import json
import http
import numpy

from constants import PDRConstants as Constants
from ufm_communication_mgr import UFMCommunicator
# should actually be persistent and thread safe dictionary pf PortStates


class PortData(object):
    def __init__(self, port_name=None, port_num=None, peer=None, node_type=None, active_speed=None, port_width=None, port_guid=None):
        self.counters_values = {}
        self.node_type = node_type
        self.peer = peer
        self.port_name = port_name
        self.port_num = None
        self.last_timestamp = 0
        self.active_speed = active_speed
        self.port_width = port_width
        self.port_guid = None
        self.ber_tele_data = pd.DataFrame(columns=[Constants.TIMESTAMP, Constants.SYMBOL_BER])
        self.last_symbol_ber_timestamp = None
        self.last_symbol_ber_val = None



class PortState(object):
    def __init__(self, name):
        self.name = name
        self.state = Constants.STATE_NORMAL # isolated | treated
        self.cause = Constants.ISSUE_INIT # oonoc, pdr, ber
        self.maybe_fixed = False
        self.change_time = datetime.now()

    def update(self, state, cause):
        self.state = state
        self.cause = cause
        self.change_time = datetime.now()
    
    def get_cause(self):
        return self.cause
    
    def get_state(self):
        return self.state
    
    def get_change_time(self):
        return self.change_time
        
class Issue(object):
    def __init__(self, port, cause):
        self.cause = cause
        self.port = port

def get_counter(counter_name, row, default=0):
    try:
        val = row.get(counter_name) if (row.get(counter_name) is not None and not numpy.isnan(row.get(counter_name))) else default
    except Exception as e:
        return default
    return val

class IsolationMgr:
    
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
        self.t_isolate = pdr_config.getint(Constants.CONF_COMMON, Constants.T_ISOLATE)
        self.max_num_isolate = pdr_config.getint(Constants.CONF_COMMON, Constants.MAX_NUM_ISOLATE)
        self.tmax = pdr_config.getint(Constants.CONF_COMMON, Constants.TMAX)
        self.d_tmax = pdr_config.getint(Constants.CONF_COMMON, Constants.D_TMAX)
        self.max_pdr = pdr_config.getfloat(Constants.CONF_COMMON, Constants.MAX_PDR)
        self.configured_ber_check = pdr_config.getboolean(Constants.CONF_COMMON,Constants.CONFIGURED_BER_CHECK)
        self.dry_run = pdr_config.getboolean(Constants.CONF_COMMON,Constants.DRY_RUN)
        self.do_deisolate = pdr_config.getboolean(Constants.CONF_COMMON,Constants.DO_DEISOLATION)
        self.deisolate_consider_time = pdr_config.getint(Constants.CONF_COMMON,Constants.DEISOLATE_CONSIDER_TIME)
        self.automatic_deisolate = pdr_config.getboolean(Constants.CONF_COMMON,Constants.AUTOMATIC_DEISOLATE)
        self.dynamic_wait_time = pdr_config.getint(Constants.CONF_COMMON,"DYNAMIC_WAIT_TIME")
        self.temp_check = pdr_config.getboolean(Constants.CONF_COMMON,Constants.CONFIGURED_TEMP_CHECK)
        self.no_down_count = pdr_config.getboolean(Constants.CONF_COMMON,Constants.NO_DOWN_COUNT)
        self.access_isolation = pdr_config.getboolean(Constants.CONF_COMMON,Constants.ACCESS_ISOLATION)
        self.test_mode = pdr_config.getboolean(Constants.CONF_COMMON,Constants.TEST_MODE)
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

        # bring telemetry data on disabled ports
        self.dynamic_extra_configuration = {
            "plugin_env_CLX_EXPORT_API_ENABLE_DOWN_PORT_COUNTERS": "1",
            "plugin_env_CLX_EXPORT_API_ENABLE_DOWN_PHY": "1",
            "arg_11": "",
        }
                        
    def calc_max_ber_wait_time(self, min_threshold):
        # min speed EDR = 32 Gb/s
        min_speed, min_width = 32 * 1024 * 1024 * 1024, 1
        min_port_rate = min_speed * min_width
        min_bits = float(format(float(min_threshold), '.0e').replace('-', ''))
        min_sec_to_wait = min_bits / min_port_rate
        return min_sec_to_wait

    def is_out_of_operating_conf(self, port_name):
        port_obj = self.ports_data.get(port_name)
        if not port_obj:
            self.logger.warning(f"Port {port_name} not found in ports data in calculation of oonoc port")
            return
        temp = port_obj.counters_values.get(Constants.TEMP_COUNTER)
        if temp and temp > self.tmax:
            return True
        return False

    def eval_isolation(self, port_name, cause):
        self.logger.info("Evaluating isolation of port {0} with cause {1}".format(port_name, cause))
        if port_name in self.ufm_latest_isolation_state:
            self.logger.info("Port is already isolated. skipping...")
            return
        port_obj = self.ports_data.get(port_name)
        if not port_obj:
            self.logger.warning("Port {0} not found in ports data".format(port_name))
            return
        if port_obj.node_type == Constants.NODE_TYPE_COMPUTER and not self.access_isolation:
            self.logger.info("Port {0} is a computer port. skipping...".format(port_name))
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
            
        self.logger.warning(f"Isolated port: {port_name} cause: {cause}. dry_run: {self.dry_run}")

    def eval_deisolate(self, port_name):
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
        elif datetime.now() >= self.ports_states[port_name].get_change_time() + timedelta(minutes=self.deisolate_consider_time):
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
        self.logger.warning(f"Deisolated port: {port_name}. dry_run: {self.dry_run}")
                
    def get_rate_and_update(self, port_obj, counter_name, new_val, timestamp):

        if timestamp - port_obj.last_timestamp < 1:
            return port_obj.counters_values.get(counter_name + "_rate", 0)
        old_val = port_obj.counters_values.get(counter_name)
        if old_val and new_val > old_val:
            counter_delta = (new_val - old_val) / (timestamp - port_obj.last_timestamp)
        else:
            counter_delta = 0
        port_obj.counters_values[counter_name] = new_val
        port_obj.counters_values[counter_name + "_rate"] = counter_delta
        port_obj.counters_values[Constants.LAST_TIMESTAMP] = timestamp
        return counter_delta
   
    def check_link_down_condition(self, port_obj, port_name, ports_counters):
        if not port_obj.peer or port_obj.peer == 'N/A':
            return None
        peer_guid, peer_num = port_obj.peer.split('_')
        #TODO check for a way to save peer row in data structure for performance
        peer_row = ports_counters.loc[(ports_counters['port_guid'] == peer_guid) & (ports_counters['port_num'] == int(peer_num))]
        if peer_row.empty:
            self.logger.warning("Peer port {0} not found in ports data".format(port_obj.peer))
            return None
        peer_row_timestamp = peer_row.get(Constants.TIMESTAMP)
        peer_link_downed = get_counter(Constants.LNK_DOWNED_COUNTER, peer_row)
        peer_obj = self.ports_data.get(port_obj.peer)
        if not peer_obj:
            return None
        peer_link_downed_rate = self.get_rate_and_update(peer_obj, Constants.LNK_DOWNED_COUNTER, peer_link_downed, peer_row_timestamp)
        if peer_link_downed_rate > 0:
            return Issue(port_name, Constants.ISSUE_LINK_DOWN)
        return None
    
    def read_next_set_of_high_ber_or_pdr_ports(self, endpoint_port):
        issues = {}
        ports_counters = self.ufm_client.get_telemetry(endpoint_port, Constants.PDR_DYNAMIC_NAME,self.test_mode)
        if ports_counters is None:
            # implement health check for the telemetry instance
            self.logger.error("Couldn't retrieve telemetry data")
            return issues
        for index, row in ports_counters.iterrows():
            port_name = f"{row.get('port_guid', '').split('x')[-1]}_{row.get('port_num', '')}"
            if self.test_mode:
                # I want to add them once we get our first telemetry.
                if not self.ports_data.get(port_name):
                    self.ports_data[port_name] = PortData(port_name)
            port_obj = self.ports_data.get(port_name)
            if not port_obj:
                self.logger.warning("Port {0} not found in ports data".format(port_name))
                continue
            # from micro seconds to seconds.
            timestamp = row.get(Constants.TIMESTAMP) / 1000 / 1000
            rcv_error = get_counter(Constants.RCV_ERRORS_COUNTER, row)
            rcv_remote_phy_error = get_counter(Constants.RCV_REMOTE_PHY_ERROR_COUNTER, row)
            errors = rcv_error + rcv_remote_phy_error
            error_rate = self.get_rate_and_update(port_obj, Constants.ERRORS_COUNTER, errors, timestamp)
            rcv_pkts = get_counter(Constants.RCV_PACKETS_COUNTER, row)
            rcv_pkt_rate = self.get_rate_and_update(port_obj, Constants.RCV_PACKETS_COUNTER, rcv_pkts, timestamp)
            cable_temp = get_counter(Constants.TEMP_COUNTER, row, default=None)
            link_downed = get_counter(Constants.LNK_DOWNED_COUNTER, row)
            link_downed_rate = self.get_rate_and_update(port_obj, Constants.LNK_DOWNED_COUNTER, link_downed, timestamp)
            port_obj.last_timestamp = timestamp
            if cable_temp is not None and not numpy.isnan(cable_temp):
                if cable_temp == "NA" or cable_temp == "N/A" or cable_temp == "" or cable_temp == "0C":
                    continue
                cable_temp = int(cable_temp.split("C")[0]) if type(cable_temp) == str else cable_temp
                dT = abs(port_obj.counters_values.get(Constants.TEMP_COUNTER, 0) - cable_temp)
                port_obj.counters_values[Constants.TEMP_COUNTER] = cable_temp
            if rcv_pkt_rate and error_rate / rcv_pkt_rate > self.max_pdr:
                issues[port_name] = Issue(port_name, Constants.ISSUE_PDR)
            elif self.temp_check and cable_temp and (cable_temp > self.tmax or dT > self.d_tmax):
                issues[port_name] = Issue(port_name, Constants.ISSUE_OONOC)
            elif self.no_down_count and link_downed_rate > 0:
                link_downed_issue = self.check_link_down_condition(port_obj, port_name, ports_counters)
                if link_downed_issue:
                    issues[port_name] = link_downed_issue
            if self.configured_ber_check:
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
                        port_obj.active_speed, port_obj.port_width = self.get_port_metadata(port_name)
                    if not port_obj.port_width:
                        self.logger.debug(f"port width for port {port_name} is None, can't verify it's BER values")
                        continue
                    for (interval, threshold) in self.ber_intervals:
                        symbol_ber_rate = self.calc_ber_rates(port_name, port_obj.active_speed, port_obj.port_width, interval)
                        if symbol_ber_rate and symbol_ber_rate > threshold:
                            issued_port = issues.get(port_name)
                            if issued_port:
                                issued_port.cause = Constants.ISSUE_PDR_BER
                            else:
                                issues[port_name] = Issue(port_name, Constants.ISSUE_BER)                    
                            break                        
        return issues

    def calc_single_rate(self, port_name, port_speed, port_width, col_name, time_delta):
        try:
            if port_speed != "NDR":
                # BER calculations is only relevant for NDR
                return 0
            port_obj  = self.ports_data.get(port_name)
            ber_data = port_obj.ber_tele_data
            if not port_obj.last_symbol_ber_val or ber_data.empty:
                return 0
            # Calculate the adjusted time delta, rounded up to the nearest sample interval
            adjusted_time_delta = numpy.ceil(time_delta / self.t_isolate) * self.t_isolate
            
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
        symbol_rate = self.calc_single_rate(port_name, port_speed, port_width, Constants.SYMBOL_BER, time_delta)
        return symbol_rate

    # called first time to get all the metadata of the telemetry.
    def get_ports_metadata(self):
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
        if self.test_mode:
            # all the switches have the same data for the testing
            return "NDR",4
        meta_data = self.ufm_client.get_port_metadata(port_name)
        if meta_data and len(meta_data) > 0:
            port_data = meta_data[0]
            port_speed = port_data.get(Constants.ACTIVE_SPEED)
            port_width = port_data.get(Constants.WIDTH)
            if port_width:
                port_width = int(port_width.strip('x'))
            return port_speed, port_width


    def set_ports_as_treated(self, ports_dict):
        for port, state in ports_dict.items():
            port_state = self.ports_states.get(port)
            if port_state and state == Constants.STATE_TREATED:
                port_state.state = state
    
    def get_isolation_state(self):
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

    def start_telemetry_session(self):
        self.logger.info("Starting telemetry session")
        guids = self.get_requested_guids()
        response = self.ufm_client.start_dynamic_session(Constants.PDR_DYNAMIC_NAME, self.telemetry_counters, self.t_isolate, guids, self.dynamic_extra_configuration)
        if response and response.status_code == http.HTTPStatus.ACCEPTED:
            port = str(int(response.content))
        else:
            self.logger.error(f"Failed to start dynamic session: {response}")
            return False
        return port

    def update_telemetry_session(self):
        self.logger.info("Updating telemetry session")
        guids = self.get_requested_guids()
        response = self.ufm_client.update_dynamic_session(Constants.PDR_DYNAMIC_NAME, self.t_isolate, guids)
        return response

    def get_requested_guids(self):
        guids = {}
        for port in self.ports_data.values():
            sys_guid = port.port_guid
            if sys_guid in guids:
                guids[sys_guid].append(port.port_num)
            else:
                guids[sys_guid] = [port.port_num]
        requested_guids = [{"guid": sys_guid, "ports": ports} for sys_guid, ports in guids.items()]
        return requested_guids

    # this function create dynamic telemetry and returns the port of this telemetry
    def run_telemetry_get_port(self):
        # if we are on test_mode, there is no dynamic telemetry and it will auto go to http://127.0.0.1:9003/csv/xcset/simulated_telemetry (the port is 9003)
        if self.test_mode: return Constants.TEST_MODE_PORT
        try:
            while not self.ufm_client.running_dynamic_session(Constants.PDR_DYNAMIC_NAME):
                self.logger.info("Waiting for dynamic session to start")
                endpoint_port = self.start_telemetry_session()
                time.sleep(self.dynamic_wait_time)
        except Exception as e:
            self.ufm_client.stop_dynamic_session(Constants.PDR_DYNAMIC_NAME)
            time.sleep(self.dynamic_wait_time)
        endpoint_port = self.ufm_client.dynamic_session_get_port(Constants.PDR_DYNAMIC_NAME)
        return endpoint_port

    def main_flow(self):
        # sync to the telemetry clock by blocking read
        self.logger.info("Isolation Manager initialized, starting isolation loop")
        self.get_ports_metadata()    
        self.logger.info("Retrieved ports metadata")
        endpoint_port = self.run_telemetry_get_port()
        self.logger.info("telemetry session started")
        while(True):
            try:
                t_begin = time.time()
                self.get_isolation_state()
                self.logger.info("Retrieving telemetry data to determine ports' states")
                issues = self.read_next_set_of_high_ber_or_pdr_ports(endpoint_port)
                if len(issues) > self.max_num_isolate:
                    # UFM send external event
                    event_msg = "got too many ports detected as unhealthy: %d, skipping isolation" % len(issues)
                    self.logger.warning(event_msg)
                    if not self.test_mode:
                        self.ufm_client.send_event(event_msg)
                
                # deal with reported new issues
                else:
                    for issue in issues.values():
                        port = issue.port
                        cause = issue.cause # ber|pdr|{ber&pdr}

                        self.eval_isolation(port, cause)

                # deal with ports that with either cause = oonoc or fix

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
            time.sleep(max(1, self.t_isolate - (t_end - t_begin)))

# this is a callback for API exposed by this code - second phase
# def work_reportingd(port):
#     PORTS_STATE[port].update(Constants.STATE_TREATED, Constants.ISSUE_INIT)
