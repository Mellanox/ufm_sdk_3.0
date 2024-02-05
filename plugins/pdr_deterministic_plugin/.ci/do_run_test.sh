#!/bin/bash -x
export SERVER_HOST=$SERVER_HOST
expect << EOF
spawn ssh root@${SERVER_HOST}
expect "Password:*"
send -- "admin\r"
expect "# "
send -- "sed -i -e 's/TEST_MODE=False/TEST_MODE=True/g' /opt/ufm/files/conf/plugins/pdr_deterministic/pdr_deterministic.conf \r"
expect "# "
send -- "sed -i -e 's/DRY_RUN=False/DRY_RUN=True/g' /opt/ufm/files/conf/plugins/pdr_deterministic/pdr_deterministic.conf \r"
expect "# "
send -- "sed -i -e 's/T_ISOLATE=/T_ISOLATE=10/g' /opt/ufm/files/conf/plugins/pdr_deterministic/pdr_deterministic.conf \r"
expect "# "
send -- "sed -i -e 's/CONFIGURED_TEMP_CHECK=/CONFIGURED_TEMP_CHECK=True/g' /opt/ufm/files/conf/plugins/pdr_deterministic/pdr_deterministic.conf \r"
expect "# "
send -- "sed -i -e 's/DEISOLATE_CONSIDER_TIME=/DEISOLATE_CONSIDER_TIME=True/g' /opt/ufm/files/conf/plugins/pdr_deterministic/pdr_deterministic.conf \r"
expect "# "
send -- "/opt/ufm/scripts/manage_ufm_plugins.sh enable -p pdr_deterministic\r"
expect "# "
spawn python3 /tmp/simulation_telemetry.py
expect "# "
sleep 60
send -- "echo $?"
EOF
