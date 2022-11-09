import re
import sys
import time
import requests

# Sending it to UFM as an external event
def post_request(host_ip, protocol, resource, headers, data=None, json=None):
    request = protocol + '://' + host_ip + resource
    response = requests.post(request, verify=False, headers=headers, data=data, json=json)
    return response

def external_event(description):
    ufm_host = "127.0.0.1:8000"
    ufm_protocol = "http"
    resource = "/app/events/external_event"
    headers = {"X-Remote-User": "ufmsystem"}
    payload = {"event_id": 551, "description": description}
    _ = post_request(ufm_host, ufm_protocol, resource, headers, payload)

if __name__ == "__main__":    
    # Trap write location:
    destination = "/log/snmptrap.log"  # File destination

    # Getting Trap
    trap = sys.stdin.readlines()  # Read from stdin
    trap.pop(0)
    r = "".join(trap)  # Convert LIST to STRING

    # Format the time string
    time = time.strftime("%H:%M:%S %Y/%m/%d")
    time = str(time)

    # Matching on IPaddress
    source = re.findall('UDP:.\[([\d.+]+)\]' ,r)

    HEADER = ''.join(source)
    IP = str(source).strip("[]'")
    HEADER = time + " MLNX SWITCH TRAP " + IP

    # Writing trap to log and sending event to UFM
    with open(destination, "a") as file:
        file.write (HEADER + "\n" + r)
        external_event(r)