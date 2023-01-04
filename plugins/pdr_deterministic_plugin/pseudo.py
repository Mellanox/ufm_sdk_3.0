from datetime import datetime
import time

# should actually be persistent and thread safe dictionary pf PortStates
PORTS_STATE = dict()
PORTS_DATA = dict()

class PortData(object):
    def __init__(self):
        self.counters_values = {}
        self.change_time = datetime.now()


class PortState(object):
    def __init__(self):
        self.state = "normal" # isolated | treated
        self.cause = "init" # oonoc, pdr, ber
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
    def __init__(self, cause, port):
        self.cause = cause
        self.port = port

def eval_isolation(port, cause):
    if ufm_is_port_isolated(port):
        return

    # if out of operating conditions we ignore the cause
    # Dror - not sure what how does UFM know if a port is OONOC if port is NOC, the UFM doesn't have it in the model?
    # EZ: UFM should perform a query via MAD or some other method (mlx_link?) to get the module temp of the port. 
    if ufm_is_out_of_operating_conf(port):
        cause = "OONOC"
    
    if not dry_run:
        ufm_isolate_port(port)
    PORTS_STATE[port].update("isolated", cause)
    # log and DB
    # using isolation UFM REST API - PUT /ufmRestV2/app/unhealthy_ports
#         {
#            "ports": [
#                "e41d2d0300062380_3"
#              ],
#            "ports_policy": "UNHEALTHY",
#            "action": "isolate"
#          }
    log("isolated port: %s cause: %s", port, cause)

def eval_deisolate(port):
    if not ufm_is_port_isolated(port):
        delete PORTS_STATE[port]
        return

    # we dont return those out of NOC
    if ufm_is_out_of_operating_conf(port):
        cause = "OONOC"
        PORTS_STATE[port].update("isolated", cause)
        return

    # we need some time after the change in state
    # Dror - configurable values
    elif datetime.now() >= PORTS_STATE[port].get_change_time() + 5min:
        if ufm_get_5min_ber(port) > max_ber:
            cause = "ber"
            PORTS_STATE[port].update("isolated", cause)
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
    if not dry_run:
        ufm_deisolate_port(port)
    delete PORTS_STATE[port]
    log("deisolated port: %s", port)
               
def get_rate_and_update(port_data, counter_name, new_val):
    counter_delta = (port_data.counters_values.get(counter_name) - new_val) / Tisolate
    port_data.counters_values[counter_name] = new_val
    return counter_delta

def ufm_blocking_read_next_set_of_high_ber_or_pdr_ports():
    ports_counters = ufm_get_telemetry()
    issues = {}
    for port, counters in ports_counters.items():
        port_data = PORTS_DATA.get(port)
        errors = counters.get("PortRcvErrors") + counters.get("PortRcvRemotePhysicalErrorExt") 
        error_rate = get_rate_and_update(port, "errors", errors)
        rcv_pkts = counters.get("PortRcvPktsExtended")
        rcv_pkt_rate = get_rate_and_update(port, "PortRcvPktsExtended", rcv_pkts)
        cable_temp = counters.get("Temperature")
        dT = abs(port_data.counters_values.get("Temperature") - cable_temp)
        port_data.counters_values["Temperature"] = cable_temp
        if error_rate / rcv_pkt_rate > MAX_PDR or (cable_temp > Tmax and dT > dTmax):
            issues[port] = Issue(port, "pdr")
    if configured_check_ber():
        high_ber_ports = get_high_ber_ports()
        for port in high_ber_ports:
            issued_port = issues.get(port)
            if issued_port:
                issued_port.cause = "ber&pdr"
            else:
                issues[port] = Issue(port, "ber")
        issues.add(high_ber_ports)
    return issues


def main_flow():
    # sync to the telemetry clock by blocking read
    while(True):
        issues = ufm_blocking_read_next_set_of_high_ber_or_pdr_ports()
        if len(issues) > max_ports_batch_size:
            # UFM send external event
            alert("got too many ports detected as unhealthy: %d", len(issues))
        
        # deal with reported new issues
        for issue in issues:
            port = issue.port
            cause = issue.cause # ber|pdr|{ber&pdr}

            eval_isolation(port, cause)

        # deal with ports that with either cause = oonoc or fix
        for port in PORTS_STATE:
            state = PORTS_STATE[port].get_state()
            cause = PORTS_STATE[port].get_cause()
            # Dror - what is a treated state? did you mean isolated?
            # EZ: No it is a state that say that some maintenance was done to the link 
            #     so need to re-evaluate if to return it to service
            if cause == "oonoc" or state == "treated":
                eval_deisolate(port)
        # Dror - what is the default for Tisolate?
        # EZ: Can't we make a blocking call for more ports?
        time.sleep(Tisolate)

# this is a callback for API exposed by this code - second phase
def work_reportingd(port):
    PORTS_STATE[port].update("treated", "init")
