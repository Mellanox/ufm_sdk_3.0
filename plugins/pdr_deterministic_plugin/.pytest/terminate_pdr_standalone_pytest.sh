#!/bin/bash -x

echo "Terminating standalone PDR process"
ps -ef | grep isolation_algo.py | grep -v grep | awk '{print $2}' | xargs kill -9 $1 >/dev/null 2>/dev/null
#sudo pkill -0 isolation_algo.py && pkill -9 -f isolation_algo.py 2>/dev/null
sleep 10
if pgrep -x isolation_algo.py> /dev/null; then
    echo "Failed to kill the process"
    exit 1
fi
