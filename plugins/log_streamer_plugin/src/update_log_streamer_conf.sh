#!/bin/bash
source /opt/ufm/scripts/common
# Function to update log_streamer_conf.ini with syslog settings
update_log_streamer_conf() {
    local syslog_enabled=$1
    local syslog_addr=$2
    local files_to_stream=$3
    local conf_file=$4

    # Check if syslog is enabled
    if [ "$syslog_enabled" != "true" ]; then
        echo "Syslog is not enabled in gv.cfg (syslog = $syslog_enabled)"
        # remove files_to_stream config
        sed -i "s|files_to_stream = .*|files_to_stream = |" "$conf_file"
        # remove remote_syslog_addr config
        sed -i "s|remote_syslog_addr = .*|remote_syslog_addr = |" "$conf_file"
        return 1
    fi

    # Check if syslog_addr is configured
    if [ -z "$syslog_addr" ]; then
        echo "Error: syslog_addr is not configured in gv.cfg"
        return 1
    fi


    # Check if files_to_stream is configured
    if [ -z "$files_to_stream" ]; then
        echo "Error: files_to_stream is not configured in gv.cfg"
        return 1
    fi

    # Update log_streamer_conf.ini with files_to_stream
    sed -i "s|files_to_stream = .*|files_to_stream = $files_to_stream|" "$conf_file"
    # Update log_streamer_conf.ini with syslog settings
    sed -i "s|remote_syslog_addr = .*|remote_syslog_addr = $syslog_addr|" "$conf_file"

    return 0
}

read_config_params() {
    local syslog_enabled=$(GetConfigParam "syslog" "gv.cfg")
    local syslog_addr=$(GetConfigParam "syslog_addr" "gv.cfg")
    local files_to_stream=$(GetConfigParam "files_to_stream" "gv.cfg")
}
config_file="/opt/ufm/files/conf/gv.cfg"
section="Logging"
ini_file=/log_streamer_conf.ini

syslog_enabled=$(GetCfg "$config_file" "$section" "syslog")
syslog_addr=$(GetCfg "$config_file" "$section" "syslog_addr")
files_to_stream=$(GetCfg "$config_file" "$section" "files_to_stream")

update_log_streamer_conf "$syslog_enabled" "$syslog_addr" "$files_to_stream" "$ini_file"
