#!/bin/bash -x
export SERVER_HOST=$SERVER_HOST
expect << EOF
spawn ssh root@${SERVER_HOST}
expect "# "
send -- "echo $HOSTNAME"
expect "# "
send -- "python3 /tmp/simulation_telemetry.py\r"
expect "# "
send -- "echo $?"
EOF