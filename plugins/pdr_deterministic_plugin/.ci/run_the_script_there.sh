#!/bin/bash -x
pid=$(ps -fade | grep simulation_telemetry | egrep -v grep | awk '// { print $2 }')
if [[ ! -z $pid ]]; then kill -9 $pid;fi
cp /opt/ufm/conf/plugins/pdr_deterministic/pdr_deterministic.conf /config
docker run --network=host -v /config:/config mellanox/ufm-plugin-pdr_deterministic >/tmp/pdr_deterministic_plugin.log 2>&1&
sleep 5
container_pid=$(docker ps| grep pdr_ | egrep -v grep | awk '// { print $1 }')
echo $container_pid
docker logs $container_pid >& /tmp/pdr_deterministic_plugin.log&
python3 /tmp/simulation_telemetry.py
result=$?
docker stop $container_pid
exit $result
