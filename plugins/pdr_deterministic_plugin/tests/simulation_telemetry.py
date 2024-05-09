#
# Copyright © 2013-2024 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
#

import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from threading import Lock
import copy
import argparse
import random
from os import _exit
from os.path import exists
import requests
from utils.utils import Utils

lock = Lock()

PHY_EFF_ERROR = "phy_effective_errors"
PHY_SYMBOL_ERROR = "phy_symbol_errors"
RCV_PACKETS_COUNTER = "PortRcvPktsExtended"
RCV_ERRORS_COUNTER = "PortRcvErrorsExtended"
LINK_DOWN_COUNTER = "LinkDownedCounterExtended"
RCV_REMOTE_PHY_ERROR_COUNTER = "PortRcvRemotePhysicalErrorsExtended"
TEMP_COUNTER = "CableInfo.Temperature"
FEC_MODE = "fec_mode_active"
BLACK_TTL =  "ExcludePortTimeSeconds"
ENDPOINT_CONFIG = {}

class CsvEndpointHandler(BaseHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()

        path = self.path
        if path not in ENDPOINT_CONFIG:
            self.wfile.write(b'Endpoint not found')
            return

        endpoint = ENDPOINT_CONFIG[path]
        black_ports_simulation(endpoint)

        # Increase iteration counter AFTER black ports simulation
        ENDPOINT_CONFIG["ITERATION_TIME"] += 1

        data = endpoint['data']
        self.wfile.write(data.encode())

DIFFERENT_DEFAULT_VALUES = {
    # because the plugin reads the meta data to know the first temperature and we cannot stream the metadata.
    TEMP_COUNTER:"5",
    RCV_PACKETS_COUNTER:"10000000",
}

# All positive tests
# (iteration, row index, counter name): value
POSITIVE_DATA_TEST = {
    (1,0,PHY_SYMBOL_ERROR): 0, # example, also negative test
    (1,3,RCV_ERRORS_COUNTER): 50,
    # testing packet drop rate criteria
    (2,3,RCV_ERRORS_COUNTER): 500,

    # testing temperature changes
    (3,4,TEMP_COUNTER): 90,
    # testing temperature max difference
    (3,6,TEMP_COUNTER): 25,

    (4,8,RCV_REMOTE_PHY_ERROR_COUNTER): 50,
    # testing packet drop rate criteria from the second counter. because we look on rate
    (5,8,RCV_REMOTE_PHY_ERROR_COUNTER): 500,

    # testing link down
    (4,2,LINK_DOWN_COUNTER): 2,
    (5,2,LINK_DOWN_COUNTER): 3,
    (6,2,LINK_DOWN_COUNTER): 4,

    # testing auto remove port from black list
    (0,9,BLACK_TTL): 60,        # add to blacklist for 60 seconds
    (8,9,LINK_DOWN_COUNTER): 1, # at this moment the port should be already automatically removed from blacklist
    (9,9,LINK_DOWN_COUNTER): 2, # try trigger isolation issue
}

# All negaitive tests
# (iteration, row index, counter name): value
NEGATIVE_DATA_TEST = {
    # testing black list
    (0,5,BLACK_TTL): 0,         # add to blacklist forever
    (1,5,LINK_DOWN_COUNTER): 1,
    (2,5,LINK_DOWN_COUNTER): 2, # try trigger isolation issue (should be ignored)
    (3,5,LINK_DOWN_COUNTER): 3, # try trigger isolation issue (should be ignored)
    (4,5,LINK_DOWN_COUNTER): 4, # try trigger isolation issue (should be ignored)
    (5,5,LINK_DOWN_COUNTER): 5, # try trigger isolation issue (should be ignored)
    (6,5,LINK_DOWN_COUNTER): 6, # try trigger isolation issue (should be ignored)
    (7,5,LINK_DOWN_COUNTER): 7, # try trigger isolation issue (should be ignored)
    (8,5,LINK_DOWN_COUNTER): 8, # try trigger isolation issue (should be ignored)
    (9,5,LINK_DOWN_COUNTER): 9, # try trigger isolation issue (should be ignored)

    # testing ber calculation (should not pass as not all are not equal to 0)
}

def get_max_iteration_index(tests):
   return max([test[0] for test in tests]) if tests else 0

# getting the max tests we test plus 2
MAX_POSITIVE_ITERATION_INDEX = get_max_iteration_index(POSITIVE_DATA_TEST)
MAX_NEGATIVE_ITERATION_INDEX = get_max_iteration_index(NEGATIVE_DATA_TEST)
MAX_ITERATIONS = max(MAX_POSITIVE_ITERATION_INDEX, MAX_NEGATIVE_ITERATION_INDEX) + 2

# return randomize value base on the counter name
def randomize_values(counter_name:str,iteration:int):
    if counter_name == RCV_PACKETS_COUNTER:
        return 1000000 + iteration * 10
    if counter_name == TEMP_COUNTER:
        return round(5 + random.triangular(0,10) + \
            (random.randrange(50) == 0) * 50) ## have high temeprature
    if counter_name == PHY_EFF_ERROR or counter_name == PHY_SYMBOL_ERROR or\
        counter_name == RCV_ERRORS_COUNTER or counter_name == RCV_REMOTE_PHY_ERROR_COUNTER:
        return random.triangular(0,50)
    if counter_name == FEC_MODE:
        return 0

# return value if found on our testing telemetry simulation, else return default value for that telemetry.
def find_value(row_index:int, counter_name:str, iteration:int, default=0):
    if counter_name == RCV_PACKETS_COUNTER:
        return str(1000000 + iteration * 10)
    value = POSITIVE_DATA_TEST.get((iteration, row_index, counter_name), None)
    if value is None:
        value = NEGATIVE_DATA_TEST.get((iteration, row_index, counter_name),
                                       DIFFERENT_DEFAULT_VALUES.get(counter_name, default))

    return value

def start_server(port:str,changes_intervals:int, run_forever:bool):
    server_address = ('', int(port))
    httpd = HTTPServer(server_address, CsvEndpointHandler)
    handler_instance = httpd.RequestHandlerClass

    # Get endpoint config
    endpoint = None
    for path, conf in ENDPOINT_CONFIG.items():
        if conf['endpoint_port'] == port:
            endpoint = conf
            break
    if endpoint is None:
        raise ValueError(f'Endpoint for port {port} not found')
    counters = endpoint['counters']
    rows = endpoint['row']
    # Start the server and update counters every 1 seconds
    t = Thread(target=httpd.serve_forever)
    t.daemon = True
    t.start()
    counters_names = list(counters.keys())
    header = ['timestamp', 'source_id,tag,node_guid,port_guid,port_num'] + counters_names
    endpoint['data'] = ""
    while True:
        # lock.acquire()
        data = []
        timestamp = str(int(time.time() * 1000000))
        for index,row in enumerate(rows):
            str_prefix, counters_objs = row
            row_data = [timestamp, str_prefix]
            for i,counter in enumerate(counters_objs):
                last_val = counter['last_val']
                ## here we set the value for the counters
                if ENDPOINT_CONFIG["ITERATION_TIME"] < MAX_ITERATIONS:
                    counter['last_val'] = find_value(index,counters_names[i],ENDPOINT_CONFIG["ITERATION_TIME"], 0)
                else:
                    counter['last_val'] = randomize_values(counters_names[i],ENDPOINT_CONFIG["ITERATION_TIME"])
                row_data.append(str(last_val))
            data.append(row_data)

        output = [header] + data
        csv_data = '\n'.join([','.join(row) for row in output]) + '\n'
        endpoint['data'] = csv_data
        if not run_forever and ENDPOINT_CONFIG["ITERATION_TIME"] > MAX_ITERATIONS:
            # after all the tests are done, we need to stop the simulator and check the logs
            return
        time.sleep(changes_intervals)

def get_full_port_name(endpoint, index):
    row = endpoint["selected_row"][index];
    items = row[0].split(',')
    return items[3][2:] + '_' + items[4]

def black_ports_simulation(endpoint):
    added_ports = []
    removed_ports = []
    rows = endpoint['row']
    for port_index in range(len(rows)):
        iteration = ENDPOINT_CONFIG["ITERATION_TIME"]
        ttl_seconds = find_value(port_index, BLACK_TTL, iteration, None)
        if ttl_seconds is not None:
            port_name = get_full_port_name(endpoint, port_index)
            if ttl_seconds == -1:
                # Remove from black list
                removed_ports.append(f"\"{port_name}\"")
            else:
                # Add to black list
                if ttl_seconds == 0:
                    # Test optional parameter for infinite TTL
                    added_ports.append(f"[\"{port_name}\"]")
                else:
                    # Test limited TTL value
                    added_ports.append(f"[\"{port_name}\",{ttl_seconds}]")

    if added_ports or removed_ports:
        plugin_port = Utils.get_plugin_port(port_conf_file='/config/pdr_deterministic_httpd_proxy.conf', default_port_value=8977)
        url=f"http://127.0.0.1:{plugin_port}/excluded"
        if added_ports:
            added_ports_str = '[' + ','.join(added_ports) + ']'
            requests.put(url=url, data=added_ports_str, timeout=5)

        if removed_ports:
            removed_ports_str = '[' + ','.join(removed_ports) + ']'
            requests.delete(url=url, data=removed_ports_str, timeout=5)

# create an array of ports in size of ports_num
def create_ports(config:dict,ports_num: int):
    ports_list = []
    ports_names = []
    for _ in range(ports_num):
        port_str = '0x%016x' % random.randrange(16**16)
        # holds the prefix of each simulated csv rows,
        # list of counters structures(will be filled further)
        ports_list.append([f"{port_str},,{port_str},{port_str},1", []])
        ports_names.append(port_str)
    config["Ports_names"] = ports_names
    return ports_list


# create simulate counters base of list of string of the counters
def simulate_counters(supported_counters: list):
    counters = {}
    for counter in supported_counters:
        counters[counter] = {
            'iteration': 0,
            'last_val': 0,
        }
    return counters

def initialize_simulated_counters(endpoint_obj: dict):
    counters = endpoint_obj['counters']
    rows = endpoint_obj['row']
    for row in rows:
        for counter in counters.values():
            counter_obj = copy.deepcopy(counter)
            initial_val = 0
            counter_obj['last_val'] = initial_val
            row[1].append(counter_obj)

def assert_equal(message, left_expr, right_expr, test_name="positive"):
        if left_expr == right_expr:
            print(f"    - {test_name} test name: {message} -- PASS")
        else:
            print(f"    - {test_name} test name: {message} -- FAIL (expected: {right_expr}, actual: {left_expr})")

def validate_simulation_data():
    positive_test_port_indexes = set([x[1] for x in POSITIVE_DATA_TEST])
    negative_test_port_indexes = set([x[1] for x in NEGATIVE_DATA_TEST])
    if not positive_test_port_indexes.isdisjoint(negative_test_port_indexes):
        print("ERROR: same port can't participate in both positive and negative tests")
        return False

    return True

def check_logs(config):
    lines=[]
    location_logs_can_be = ["/log/pdr_deterministic_plugin.log",
                            "/tmp/pdr_deterministic_plugin.log",
                            "/opt/ufm/log/pdr_deterministic_plugin.log",
                            "/opt/ufm/log/plugins/pdr_deterministic/pdr_deterministic_plugin.log"]
    for log_location in location_logs_can_be:
        if exists(log_location):
            with open(log_location,'r') as log_file:
                lines=log_file.readlines()
            break
    if len(lines) == 0:
        print("Could not find log file in " + str(location_logs_can_be))
        return 1        
    # if a you want to add more tests, please add more guids and test on other indeces.
    
    ports_should_be_isoloated_indeces = list(set([x[1] for x in POSITIVE_DATA_TEST]))
    ports_shouldnt_be_isolated_indeces = [0]
    # remove negative tests from the positive ones
    ports_should_be_isoloated_indeces = [port for port in ports_should_be_isoloated_indeces if port not in ports_shouldnt_be_isolated_indeces]

    number_of_tests_approved = len(ports_should_be_isoloated_indeces)
    number_of_negative_tests = len(ports_shouldnt_be_isolated_indeces)
    isolated_message="WARNING: Isolated port: "
    for p in ports_should_be_isoloated_indeces:
        found=False
        port_name = config["Ports_names"][p][2:]
        tested_counter = set([x[2] for x in POSITIVE_DATA_TEST if x[1]==p])
        for line in lines:
            found_port = isolated_message + port_name in line
            if found_port:
                found = True
                number_of_tests_approved -= 1 # it was found
                break
        assert_equal(f"{port_name} which check {tested_counter} changed and in the logs",found,True)
    
    for p in ports_shouldnt_be_isolated_indeces:
        found=False
        port_name = config["Ports_names"][p][2:]
        tested_counter = set([x[2] for x in POSITIVE_DATA_TEST if x[1]==p])
        for line in lines:
            found_port = isolated_message + port_name in line
            if found_port:
                found=True
                number_of_negative_tests -= 1 # it was found, but it shouldnt
                break
        assert_equal(f"{port_name} changed and in the logs",found,False,"negative")
    
    all_pass = number_of_tests_approved == 0 and number_of_negative_tests == len(ports_shouldnt_be_isolated_indeces)
    return 0 if all_pass else 1

# start a server which update the counters every time
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--num_simulated_ports', type=int, default=10,
        help="number of ports to simulate if set to 0 ports will be taken from the UFM REST server")
    parser.add_argument('--url_suffix', type=str, default="/csv/xcset/simulated_telemetry",
        help="endpoint url to simulate, if not set, will be taken from configuration file")
    parser.add_argument('--endpoint_port', type=str, default=9090, help="")
    parser.add_argument('--changes_intervals', type=float, default=0.5,
                         help="interval time that the server to sleep. in seconds")
    parser.add_argument('--run_forever', action='store_true')

    args = parser.parse_args()

    supported_counters = [
            PHY_EFF_ERROR,
            PHY_SYMBOL_ERROR,
            RCV_PACKETS_COUNTER,
            RCV_ERRORS_COUNTER,
            RCV_REMOTE_PHY_ERROR_COUNTER,
            TEMP_COUNTER,
            FEC_MODE,
            LINK_DOWN_COUNTER,
        ]

    config = {}
    config['endpoint_port'] = args.endpoint_port
    config['counters'] = simulate_counters(supported_counters=supported_counters)
    # selected row gives the option to simulate data on part of the ports only.
    # currently all rows are selected for change
    config['selected_row'] = create_ports(config,args.num_simulated_ports)
    ENDPOINT_CONFIG[args.url_suffix] = config
    ENDPOINT_CONFIG["ITERATION_TIME"] = 0

    config['row'] = config['selected_row']
    initialize_simulated_counters(config)

    if not validate_simulation_data():
        return False
    
    port = args.endpoint_port
    url = f'http://0.0.0.0:{port}{args.url_suffix}'
    print(f'---Starting endpoint {url}')
    start_server(port,args.changes_intervals,args.run_forever)
    if not args.run_forever:
        return check_logs(config)

if __name__ == '__main__':
    _exit(main())
