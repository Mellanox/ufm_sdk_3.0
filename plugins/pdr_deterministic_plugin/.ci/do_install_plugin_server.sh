#!/bin/bash -x
#namehost="blue-force031"
namehost=$(echo $HOSTNAME)
export SERVER_HOST=$SERVER_HOST
export PASSWORD=$PASSWORD
expect << EOF
spawn ssh -o StrictHostKeyChecking=no admin@${SERVER_HOST}
expect "Password:*"
send -- "admin\r"
expect "> "
send -- "enable\r"
expect "# "
send -- "config terminal\r"
expect "/(config/) # "
send -- "image fetch scp://root:$PASSWORD@$namehost/auto/UFM/tmp/${JOB_NAME}/${BUILD_ID}/ufm-plugin-pdr_deterministic_latest-docker.img.gz\r"
expect "/(config/) # "
sleep 50
EOF
