#!/bin/bash -x
echo -e '\nTEST_MODE=True\n'>>/opt/ufm/files/conf/plugins/pdr_deterministic/pdr_deterministic.conf
sed -i -e 's/DRY_RUN=False/DRY_RUN=True/g' /opt/ufm/files/conf/plugins/pdr_deterministic/pdr_deterministic.conf
sed -i -e 's/T_ISOLATE=300/T_ISOLATE=10/g' /opt/ufm/files/conf/plugins/pdr_deterministic/pdr_deterministic.conf
sed -i -e 's/CONFIGURED_TEMP_CHECK=False/CONFIGURED_TEMP_CHECK=True/g' /opt/ufm/files/conf/plugins/pdr_deterministic/pdr_deterministic.conf
sed -i -e 's/DEISOLATE_CONSIDER_TIME=5/DEISOLATE_CONSIDER_TIME=1/g' /opt/ufm/files/conf/plugins/pdr_deterministic/pdr_deterministic.conf

pid=$(ps -fade | grep /tmp/simulation_telemetry.py | egrep -v grep | awk '// { print $2 }')
if [[ ! -z $pid ]]; then kill -9 $pid;fi
cp /opt/ufm/conf/plugins/pdr_deterministic/pdr_deterministic.conf /config
docker run --network=host -v /config:/config mellanox/ufm-plugin-pdr_deterministic >/tmp/pdr_deterministic_plugin.log 2>&1&
sleep 5
container_pid=$(docker ps| grep pdr_ | egrep -v grep | awk '// { print $1 }')
python3 /tmp/simulation_telemetry.py > /tmp/log_of_simulation.log
result=$?
docker stop $container_pid
exit $result
