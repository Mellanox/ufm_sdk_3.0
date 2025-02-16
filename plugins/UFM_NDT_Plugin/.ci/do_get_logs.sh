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
expect -timeout 60 "/(config/) # "
send -- "file debug-dump upload latest scp://root:3tango@${NODE_NAME}:/$WORKSPACE/logs\r"
expect "/(config/) # "
send -- "file debug-dump delete latest\r"
expect "/(config/) # "
send -- "exit\r"
sleep 10
EOF
echo "End of expect"
sudo cd $WORKSPACE/logs
sudo tar -zxvf $(ls $WORKSPACE/logs/*.tgz)
sudo rm -rf sysdump-ufm-appliance*.tgz
sudo cd sysdump-ufm-appliance*
sudo tar -zxvf ufm-sysdump*
sudo cd ufm-sysdump*/ufm_logs
sudo cp ndt.log $WORKSPACE/logs
sudo cd ../../../
sudo rm -rf sysdump-ufm-appliance*

