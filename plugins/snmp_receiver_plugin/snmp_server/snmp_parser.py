import re
import sys
import time
import snmp_server.helpers as helpers

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
        helpers.send_external_event(r)