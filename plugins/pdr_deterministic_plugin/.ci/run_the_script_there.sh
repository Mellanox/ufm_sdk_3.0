#!/bin/bash -x
pid=$(ps -fade | grep simulation_telemetry | egrep -v grep | awk '// { print $2 }')
if [[ ! -z $pid ]]; then kill -9 $pid;fi
cp /opt/ufm/conf/plugins/pdr_deterministic/pdr_deterministic.conf /config
docker run --network=host -v /config:/config mellanox/ufm-plugin-pdr_deterministic >/tmp/pdr_deterministic_plugin.log&
python3 /tmp/simulation_telemetry.py
result=$?
docker stop  $(docker ps| grep pdr_ | egrep -v grep | awk '// { print $1 }')
exit $result
