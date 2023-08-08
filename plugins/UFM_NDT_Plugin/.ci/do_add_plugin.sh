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
send -- "ufm start\r"
sleep 59
expect "/(config/) # "
send -- "ufm ha takeover\r"
sleep 60
expect "/(config/) # "
send -- "ufm plugin ndt add tag latest\r"
expect "/(config/) # "
send -- "ufm plugin ndt enable\r"
expect "/(config/) # "
send -- "show ufm plugin\r"
expect "/(config/) # "
send -- "show ufm status\r"
sleep 10
expect "/(config/) # "
exit 0
EOF
