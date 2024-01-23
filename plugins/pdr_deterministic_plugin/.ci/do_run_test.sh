#!/bin/bash -x
export SERVER_HOST=$SERVER_HOST
expect << EOF
spawn ssh admin@${SERVER_HOST}
expect "Password:*"
send -- "admin\r"
expect "> "
send -- "enable\r"
expect "# "
send -- "config terminal\r"
expect "/(config/) # "
send -- "ufm plugin pdr_deterministic enable\r"
expect "/(config/) # "
send -- "_shell"
expect "# "
send -- "python3 /tmp/simulation_telemetry.py\r"
expect "# "
send -- "echo $?"
EOF