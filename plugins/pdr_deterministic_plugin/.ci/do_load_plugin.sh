#!/bin/bash -x
export SERVER_HOST=$SERVER_HOST
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
send -- "docker load ufm-plugin-pdr_deterministic_latest-docker.img.gz\r"
expect "/(config/) # "
send -- "show docker images\r"
sleep 60
EOF
