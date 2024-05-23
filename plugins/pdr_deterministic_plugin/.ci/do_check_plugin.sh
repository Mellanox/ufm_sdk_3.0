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
send -- "show ufm status\r"
expect "/(config/) # "
sleep 10
send -- "show ufm plugin\r"
expect "/(config/) # "
sleep 10
EOF
