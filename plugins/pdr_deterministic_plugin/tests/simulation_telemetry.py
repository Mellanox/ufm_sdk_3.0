import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from threading import Lock
import copy
import argparse
import random
from os import listdir
from os.path import isfile, join

lock = Lock()

PHY_RAW_ERROR_LANE0 = "phy_raw_errors_lane0"
PHY_RAW_ERROR_LANE1 = "phy_raw_errors_lane1"
PHY_RAW_ERROR_LANE2 = "phy_raw_errors_lane2"
PHY_RAW_ERROR_LANE3 = "phy_raw_errors_lane3"
PHY_EFF_ERROR = "phy_effective_errors"
PHY_SYMBOL_ERROR = "phy_symbol_errors"
RCV_PACKETS_COUNTER = "PortRcvPktsExtended"
RCV_ERRORS_COUNTER = "PortRcvErrorsExtended"
RCV_REMOTE_PHY_ERROR_COUNTER = "PortRcvRemotePhysicalErrorsExtended"
TEMP_COUNTER = "CableInfo.Temperature"
FEC_MODE = "fec_mode_active"
ENDPOINT_CONFIG = {}

class CsvEndpointHandler(BaseHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def do_GET(self):
        ENDPOINT_CONFIG["ITERATION_TIME"] += 1
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()

        path = self.path
        if path not in ENDPOINT_CONFIG:
            self.wfile.write(b'Endpoint not found')
            return

        endpoint = ENDPOINT_CONFIG[path]
        data = endpoint['data']
        self.wfile.write(data.encode())

DIFFERENT_DEFAULT_VALUES = {
    # because the plugin reads the meta data to know the first temperature and we cannot stream the metadata.
    TEMP_COUNTER:"5",
    RCV_PACKETS_COUNTER:"10000000",
}

ALL_DATA_TEST = {
    # all positive tests
    # iteration, row index, counter name = value
    (1,0,PHY_SYMBOL_ERROR):0, # example
    (1,3,RCV_ERRORS_COUNTER):50,
    # testing packet drop rate criteria
    (2,3,RCV_ERRORS_COUNTER):500,

    # testing temperature changes
    (3,4,TEMP_COUNTER):90,
    # testing temperature max difference
    (3,6,TEMP_COUNTER):25,

    (4,8,RCV_REMOTE_PHY_ERROR_COUNTER):50,
    # testing packet drop rate criteria from the second counter. because we look on rate
    (5,8,RCV_REMOTE_PHY_ERROR_COUNTER):500,
    
    # testing ber calculation
    (3,2,PHY_RAW_ERROR_LANE0):0.001,
    (3,2,PHY_RAW_ERROR_LANE1):0.001,
    (3,2,PHY_RAW_ERROR_LANE2):0.001,
    (3,2,PHY_RAW_ERROR_LANE3):0.001,

    # testing ber calculation rate it is so high because we try to do it instead of 25 minutes, now.
    (4,2,PHY_RAW_ERROR_LANE0):1024**5,
    (4,2,PHY_RAW_ERROR_LANE1):1024**6,
    (4,2,PHY_RAW_ERROR_LANE2):1024**5,
    (4,2,PHY_RAW_ERROR_LANE3):1024**5,
    
    # should not work now, only after 30 (3 iterations) seconds, which is 5 more iterations
    
    (6,2,PHY_RAW_ERROR_LANE0):1024**5,
    (6,2,PHY_RAW_ERROR_LANE1):1024**6,
    (6,2,PHY_RAW_ERROR_LANE2):1024**5,
    (6,2,PHY_RAW_ERROR_LANE3):1024**5,

    # negative tests
    # testing ber calculation ( should not pass as not all are not equal to 0)
    (8,0,PHY_RAW_ERROR_LANE1):0.001,
    (8,0,PHY_RAW_ERROR_LANE2):0.001,
    (8,0,PHY_RAW_ERROR_LANE3):0.001,

    (9,0,PHY_RAW_ERROR_LANE1):1024**6,
    (9,0,PHY_RAW_ERROR_LANE2):1024**6,
    (9,0,PHY_RAW_ERROR_LANE3):1024**6,

}

# getting the max tests we test plus 2
MAX_ITERATIONS = max([x[0] for x in ALL_DATA_TEST]) + 2

# return randomize value base on the counter name
def randomizeValues(counter_name:str,iteration:int):
    if counter_name == RCV_PACKETS_COUNTER:
        return 1000000 + iteration * 10
    if counter_name == TEMP_COUNTER:
        return round(5 + random.triangular(0,10) + \
            (random.randrange(50) == 0) * 50) ## have high temeprature
    if counter_name == PHY_RAW_ERROR_LANE0 or counter_name == PHY_RAW_ERROR_LANE1 or\
        counter_name == PHY_RAW_ERROR_LANE2 or counter_name == PHY_RAW_ERROR_LANE3:
        return random.random()*1000
    if counter_name == PHY_EFF_ERROR or counter_name == PHY_SYMBOL_ERROR or\
        counter_name == RCV_ERRORS_COUNTER or counter_name == RCV_REMOTE_PHY_ERROR_COUNTER:
        return random.triangular(0,50)
    if counter_name == FEC_MODE:
        return 0

# return value if found on our testing telemetry simulation, else return default value for that telemetry.
def findValue(row_index:int, counter_name:str, iteration:int):
    if counter_name == RCV_PACKETS_COUNTER:
        return str(1000000 + iteration * 10)
    return ALL_DATA_TEST.get((iteration,row_index,counter_name),
                             DIFFERENT_DEFAULT_VALUES.get(counter_name,0))
        

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
                    counter['last_val'] = findValue(index,counters_names[i],ENDPOINT_CONFIG["ITERATION_TIME"])
                else:
                    counter['last_val'] = randomizeValues(counters_names[i],ENDPOINT_CONFIG["ITERATION_TIME"])
                row_data.append(str(last_val))
            data.append(row_data)

        output = [header] + data
        csv_data = '\n'.join([','.join(row) for row in output]) + '\n'
        endpoint['data'] = csv_data        
        if not run_forever and ENDPOINT_CONFIG["ITERATION_TIME"] > MAX_ITERATIONS:
            # after all the tests are done, we need to stop the simulator and check the logs
            return
        time.sleep(changes_intervals)


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

def check_logs(config):
    lines=[]
    with open("/log/pdr_deterministic_plugin.log",'r') as log_file:
        lines=log_file.readlines()
    # if a you want to add more tests, please add more guids and test on other indeces.
    ports_should_be_isoloated_indeces = [2,3,4,6,8]
    ports_shouldnt_be_isolated_indeces = [0]

    number_of_tests_approved = len(ports_should_be_isoloated_indeces)
    number_of_negative_tests = len(ports_shouldnt_be_isolated_indeces)
    isolated_message="WARNING: Isolated port: "
    for p in ports_should_be_isoloated_indeces:
        for line in lines:
            if isolated_message + config["Ports_names"][p] in line:
                number_of_tests_approved -= 1 # it was found
                break

    for p in ports_shouldnt_be_isolated_indeces:
        for line in lines:
            if isolated_message + config["Ports_names"][p] in line:
                number_of_negative_tests -= 1 # it was found, but it shouldnt
                break
    
    return number_of_tests_approved == 0 and number_of_negative_tests == len(ports_shouldnt_be_isolated_indeces)

# start a server which update the counters every time
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--num_simulated_ports', type=int, default=10,
        help="number of ports to simulate if set to 0 ports will be taken from the UFM REST server")
    parser.add_argument('--url_suffix', type=str, default="/csv/xcset/simulated_telemetry",
        help="endpoint url to simulate, if not set, will be taken from configuration file")
    parser.add_argument('--endpoint_port', type=str, default=9003, help="")
    parser.add_argument('--changes_intervals', type=float, default=0.5,
                         help="interval time that the server to sleep. in seconds")
    parser.add_argument('--run_forever', action='store_true')

    args = parser.parse_args()

    supported_counters = [
            PHY_RAW_ERROR_LANE0,
            PHY_RAW_ERROR_LANE1,
            PHY_RAW_ERROR_LANE2,
            PHY_RAW_ERROR_LANE3,
            PHY_EFF_ERROR,
            PHY_SYMBOL_ERROR,
            RCV_PACKETS_COUNTER,
            RCV_ERRORS_COUNTER,
            RCV_REMOTE_PHY_ERROR_COUNTER,
            TEMP_COUNTER,
            FEC_MODE
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

    port = args.endpoint_port
    url = f'http://0.0.0.0:{port}{args.url_suffix}'
    print(f'---Starting endpoint {url}')
    start_server(port,args.changes_intervals,args.run_forever)
    if not args.run_forever:
        return check_logs(config)

if __name__ == '__main__':
    main()
