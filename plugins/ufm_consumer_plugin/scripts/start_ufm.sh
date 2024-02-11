#!/bin/bash
# configure consumer UFM
./config_consumer.sh
status=$?
if [ $status -ne 0 ]; then
    echo "Failed to config UFM. UFM consumer plugin will not start."
    exit 1
fi
# start UFM
/etc/init.d/ufmd start
exit 0

