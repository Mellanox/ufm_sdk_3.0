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
send -- "docker load ufm-plugin-pdr_deterministic_latest-docker.img.gz\r"
expect "/(config/) # "
send -- "show docker images\r"
sleep 90
EOF
