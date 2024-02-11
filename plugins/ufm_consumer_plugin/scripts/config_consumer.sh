#!/bin/bash

# update gv.cfg file. Set in section [Multisubnet]
# values for multisubnet_enabled = true and 
# multisubnet_role = consumer
. /opt/ufm/scripts/common

keep_config_file()
{
    conf_file_path=$1
    conf_file_name=$(basename $conf_file_path)
    target_dir=/config
    target_file_path="${target_dir}/${conf_file_name}"

    if [ ! -f ${target_file_path} ]; then
        if [ -f ${conf_file_path} ]; then
            mv ${conf_file_path} ${target_dir}
            ln -s ${target_file_path} ${conf_file_path}
        else
            echo "UFM file ${conf_file_path} not found"
            exit 1
        fi
    else # file exist, but need to check if link exist
        if [ -f ${conf_file_path} ] && [ ! -L ${conf_file_path} ]; then
            # The file is not a symbolic link
            rm -f ${conf_file_path}
            ln -s ${target_file_path} ${conf_file_path}
        fi
    fi
    chown -R ufmapp:ufmapp ${target_file_path} ${conf_file_path}
}

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
sed -i "s/APACHE_PORT/$ssl_apache_port/g" /config/ufm_consumer_ui_conf.json

# keep config file for restart - save all the provider info in gv.cfg
# TODO: sqlite does not work of some reason with db file defined as synbolic link
# need to investigate: 
# 1. If UFM consumer should keep some data in database to be persistent
# 2. If yes - how to manage sqlight to work with db which is link pointing to another file
#for conf_file2keep in /opt/ufm/files/conf/gv.cfg /opt/ufm/files/sqlite/gv.db /opt/ufm/files/conf/ufm_providers_credentials.cfg;
[ ! -f /opt/ufm/files/conf/ufm_providers_credentials.cfg ] &&  echo "[Credentials]" > /opt/ufm/files/conf/ufm_providers_credentials.cfg 
for conf_file2keep in /opt/ufm/files/conf/gv.cfg /opt/ufm/files/conf/ufm_providers_credentials.cfg;
    do
         keep_config_file $conf_file2keep
    done
exit 0
