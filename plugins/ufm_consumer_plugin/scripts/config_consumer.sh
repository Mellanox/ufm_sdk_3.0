#!/bin/bash

# update gv.cfg file. Set in section [Multisubnet]
# values for multisubnet_enabled = true and 
# multisubnet_role = consumer
. /opt/ufm/scripts/common
#
UpdCfg /opt/ufm/files/conf/gv.cfg Multisubnet multisubnet_enabled true
#
UpdCfg /opt/ufm/files/conf/gv.cfg Multisubnet multisubnet_role consumer

# Set correct port number for REST port (instead 8000)
#port_str=`cat /config/ufm_consumer_httpd_proxy.conf` ; port_value=`echo ${port_str#*=}`
if [ -f /ufm_consumer_plugin.conf ]; then
    config_file="/ufm_consumer_plugin.conf"
else
    config_file="/config/ufm_consumer_plugin.conf"
fi
port_value=`GetCfg $config_file common port_number`
# update in gv.cfg with port to listen 8989
if [ -z $port_value ]; then
    port_value="8989"
fi
UpdCfg /opt/ufm/files/conf/gv.cfg Server rest_port $port_value
UpdCfg /opt/ufm/files/conf/gv.cfg Server osm_traps_listening_port 8088
UpdCfg /opt/ufm/files/conf/gv.cfg UFMAgent default_ufma_port 6366
UpdCfg /opt/ufm/files/conf/gv.cfg Logging syslog_addr /dev/consumer_log
# update apache configuration
ssl_apache_port=`GetCfg $config_file common ssl_apache_port`
apache_port=`GetCfg $config_file common apache_port`
sed -i -e "s/Listen 443/Listen $ssl_apache_port/g" -e "s/Listen 80/Listen $apache_port/g" /etc/apache2/ports.conf
sed -i "s/VirtualHost _default_:443/VirtualHost _default_:$ssl_apache_port/g" /etc/apache2/sites-available/default-ssl.conf
sed -i "s/VirtualHost \*:80/VirtualHost \*:$apache_port/g" /etc/apache2/sites-available/000-default.conf