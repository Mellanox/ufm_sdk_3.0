#!/bin/bash -x
namehost=$(echo $HOSTNAME)
cd docker/
tagver=$(cat release_info)
echo $tagver
env; printenv;
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
send -- "image fetch scp://root:3tango@$namehost/auto/UFM/tmp/${JOB_NAME}/${BUILD_ID}/ufm-plugin-rest-rdma_$tagver.tar.gz\r"
expect "/(config/) # "
sleep 50
EOF