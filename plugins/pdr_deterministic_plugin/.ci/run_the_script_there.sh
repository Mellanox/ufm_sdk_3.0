#!/bin/bash -x
pid=$(ps -fade | grep simulation_telemetry | egrep -v grep | awk '// { print $2 }')
if [[ -z $pid ]]; then kill -9 $pid;fi
python3 /tmp/simulation_telemetry.py
result=$?
exit result
