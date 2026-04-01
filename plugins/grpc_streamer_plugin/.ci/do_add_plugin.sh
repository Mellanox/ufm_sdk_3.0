#!/bin/bash -x
export SERVER_HOST=$SERVER_HOST
expect << EOF
spawn ssh admin@${SERVER_HOST}
expect "Password:*"
send -- "admin\n"
expect "> "
send -- "enable\n"
expect "# "
send -- "config terminal\n"
expect "/(config/) # "
send -- "show ufm status\n"
expect "/(config/) # "
send -- "ufm start\n"
expect "/(config/) # "
sleep 30
send -- "ufm plugin grpc-streamer remove\n"
expect "/(config/) # "
sleep 20
send -- "ufm plugin grpc-streamer add tag latest\n"
expect "/(config/) # "
send -- "ufm plugin grpc-streamer enable\n"
expect "/(config/) # "
send -- "show ufm plugin\n"
expect "/(config/) # "
send -- "show ufm status\n"
sleep 10
EOF
