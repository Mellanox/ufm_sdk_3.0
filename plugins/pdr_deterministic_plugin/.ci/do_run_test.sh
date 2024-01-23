#!/bin/bash -x
export SERVER_HOST=$SERVER_HOST
expect << EOF
spawn ssh root@${SERVER_HOST}
expect "Password:*"
send -- "admin\r"
expect "# "
send -- "sed -i -e 's/TEST_MODE=False/TEST_MODE=True/g' /opt/ufm/files/conf/plugins/pdr_deterministic/pdr_deterministic.conf \r"
expect "# "
send -- "/opt/ufm/scripts/manage_ufm_plugins.sh enable -p pdr_deterministic\r"
expect "# "
send -- "python3 /tmp/simulation_telemetry.py\r"
expect "# "
send -- "echo $?"
EOF