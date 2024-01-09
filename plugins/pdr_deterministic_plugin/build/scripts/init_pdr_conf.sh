#!/bin/bash

ufm_dir=/opt/ufm
conf_dir=$ufm_dir/files/conf
ufm_conf=$conf_dir/gv.cfg
ufmd_location=/etc/init.d/ufmd

sed -i 's/high_ber_ports_auto_isolation.*/high_ber_ports_auto_isolation=false/g' $ufm_conf

$ufmd_location model_restart
sleep 2
echo "finished initialize pdr configuration"