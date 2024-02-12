#!/bin/bash -x
export SERVER_HOST=$SERVER_HOST
expect << EOF
spawn ssh root@${SERVER_HOST}
expect "Password:*"
send -- "admin\r"
expect "# "
send -- "echo TEST_MODE=True>>/opt/ufm/files/conf/plugins/pdr_deterministic/pdr_deterministic.conf \r"
expect "# "
send -- "sed -i -e 's/DRY_RUN=False/DRY_RUN=True/g' /opt/ufm/files/conf/plugins/pdr_deterministic/pdr_deterministic.conf \r"
expect "# "
send -- "sed -i -e 's/T_ISOLATE=300/T_ISOLATE=10/g' /opt/ufm/files/conf/plugins/pdr_deterministic/pdr_deterministic.conf \r"
expect "# "
send -- "sed -i -e 's/CONFIGURED_TEMP_CHECK=False/CONFIGURED_TEMP_CHECK=True/g' /opt/ufm/files/conf/plugins/pdr_deterministic/pdr_deterministic.conf \r"
expect "# "
send -- "sed -i -e 's/DEISOLATE_CONSIDER_TIME=5/DEISOLATE_CONSIDER_TIME=1/g' /opt/ufm/files/conf/plugins/pdr_deterministic/pdr_deterministic.conf \r"
expect "# "
EOF
