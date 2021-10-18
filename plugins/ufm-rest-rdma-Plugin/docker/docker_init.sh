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
    /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
fi
sleep infinity
