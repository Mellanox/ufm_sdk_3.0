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
send -- "ufm plugin ndt remove\r"
expect "/(config/) # "
send -- "docker remove image mellanox/ufm-plugin-ndt latest\r"
expect "/(config/) # "
send -- "show ufm plugin\r"
expect "/(config/) # "
send "show ufm status\r"
expect "/(config/) # "
send -- "ufm mode mgmt"
expect "/(config/) # "
send -- "no fae ufm sm-simulator enable \r"
expect "/(config/) # "
sleep 20
EOF