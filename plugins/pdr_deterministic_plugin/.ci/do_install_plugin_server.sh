#!/bin/bash -x
namehost=$(echo $HOSTNAME)
export SERVER_HOST=$SERVER_HOST
export PASSWORD=$PASSWORD
expect << EOF
spawn ssh -o PasswordAuthentication=yes -o KexAlgorithms=+diffie-hellman-group14-sha1 admin@${SERVER_HOST}
expect "*\])?"
send -- "yes\r"
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
