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
send -- "ufm plugin snmp add tag latest\r"
expect "/(config/) # "
send -- "ufm plugin snmp enable\r"
expect "/(config/) # "
send -- "show snmp plugin\r"
expect "/(config/) # "
send -- "no ufm start\r"
expect "/(config/) # "
send -- "ufm mode mgmt"
expect "/(config/) # "
# TOASK: not monitoring, but real mode
send -- "ufm mode mon\r"
expect "/(config/) # "
send -- "ufm start\r"
expect "/(config/) # "
send -- "show ufm status\r"
sleep 10
EOF