#!/bin/bash -x
export SERVER_HOST=$SERVER_HOST
expect << EOF
ssh admin@${SERVER_HOST}
expect "Password:*"
send -- "admin\r"
expect "> "
send -- "enable\r"
expect "# "
send -- "config terminal\r"
expect "/(config/) # "
send -- "ufm plugin pdr_deterministic remove\r"
expect "/(config/) # "
send -- "docker remove image mellanox/ufm-plugin-pdr_deterministic latest\r"
expect "/(config/) # "
send -- "show ufm plugin\r"
expect "/(config/) # "
send "show ufm status\r"
expect "/(config/) # "
send -- "ufm mode mgmt"
sleep 20
EOF