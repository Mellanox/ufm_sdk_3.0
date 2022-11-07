import re
import sys
import time

# Trap write location:
destination = "/log/snmptrap.log"  # File destination

# Getting Trap
trap = sys.stdin.readlines()  # Read from stdin
trap.pop(0)
result = "" #Declare empty variable
r = "".join(trap)  # Convert LIST to STRING

# Format the time string
time = time.strftime("%H:%M:%S %Y/%m/%d")
time = str(time)

# Matching on IPaddress
source = re.findall('UDP:.\[([\d.+]+)\]' ,r)

# Building the HEADER so that Zabbix understands it
HEADER = ''.join(source)
IP = str(source).strip("[]'")
HEADER = time + " MLNX SWITCH TRAP  " +  str(IP)

# Appending it to the log file for Zabbix to pickup
with open(destination, "a") as file:
    file.write (HEADER + "\n" + r)