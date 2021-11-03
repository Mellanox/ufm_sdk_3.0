#!/bin/bash

if [ $# -ne 0 ];
then
    first_param=$1
    if [ "$first_param" = "/init.sh" ]; # init process
    then
        $@
        exit 0
    fi
else
    # copy config file into conf directory
    if [ ! -f /opt/ufm/files/conf/ufm_rdma.ini ]; then
        cp /tmp/ufm_rdma.ini /opt/ufm/files/conf/ufm_rdma.ini
    fi
    /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
fi
sleep infinity
