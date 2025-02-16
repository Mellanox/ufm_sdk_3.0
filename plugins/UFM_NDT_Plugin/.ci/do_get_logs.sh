#!/bin/bash -x
echo "node name : $NODE_NAME"
export WORKSPACE=$WORKSPACE
export SERVER_HOST=$SERVER_HOST
expect << EOF
spawn ssh -4 admin@$SERVER_HOST
expect "Password:*"
send -- "admin\r"
expect "> "
send -- "enable\r"
expect "# "
send -- "config terminal\r"
expect "/(config/) # "
send -- "debug generate dump\r"
expect "/(config/) # "
send -- "file debug-dump upload latest scp://root:3tango@${NODE_NAME}:/$WORKSPACE\r"
expect "/(config/) # "
send -- "file debug-dump delete latest\r"
expect "/(config/) # "
send -- "exit\r"
sleep 10
EOF
echo "End of expect"
cd $WORKSPACE/logs
ls $WORKSPACE/logs/
tar -zxvf $(ls $WORKSPACE/logs/*.tgz)
rm -rf sysdump-ufm-appliance*.tgz
cd sysdump-ufm-appliance*
tar -zxvf ufm-sysdump*
cd ufm-sysdump*/ufm_logs
cp ndt.log $WORKSPACE/logs
cd ../../../
rm -rf sysdump-ufm-appliance*

