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
send -- "docker load ufm-plugin-grpc-streamer_latest-docker.img.gz\r"
expect "/(config/) # "
send -- "show docker images\r"
sleep 60
EOF