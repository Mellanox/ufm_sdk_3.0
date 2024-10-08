#!/bin/bash -x
export SERVER_HOST=$SERVER_HOST
expect << EOF
spawn ssh -o StrictHostKeyChecking=no admin@${SERVER_HOST}
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
send -- "ufm web-client mode https\r"
expect "/(config/) # "
send -- "ufm start\r"
expect "/(config/) # "
sleep 20
send -- "ufm ha takeover\r"
expect "/(config/) # "
sleep 20
send -- "ufm plugin pdr_deterministic remove\r"
expect "/(config/) # "
sleep 10
send -- "ufm plugin pdr_deterministic add tag latest\r"
expect "/(config/) # "
send -- "no ufm plugin pdr_deterministic enable\r"
expect "/(config/) # "
send -- "show ufm plugin\r"
expect "/(config/) # "
send -- "show ufm status\r"
sleep 10
send -- "no ufm plugin pdr_deterministic enable\r"
expect "/(config/) # "
sleep 10
EOF
