#!/bin/bash -x

echo "Terminating standalone PDR process"
ps -ef | grep isolation_algo.py | grep -v grep | awk '{print $2}' | xargs kill -9 $1 >/dev/null 2>/dev/null
sleep 10
if ps aux | grep -q [i]solation_algo.py; then
    echo "Failed to terminate standalone PDR process"
    exit 1
fi
