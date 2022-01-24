#!/bin/bash -x
cd docker/
tagver=$(cat release_info)
echo $tagver
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
send -- "docker load ufm-plugin-rest-rdma_$tagver.tar.gz\r"
expect "/(config/) # "
send -- "show docker images\r"
sleep 60
EOF