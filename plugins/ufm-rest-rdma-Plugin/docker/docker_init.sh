#!/bin/bash

if [ $# -eq 0 ];
then
     /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
fi
tail -f /dev/null