#!/bin/bash
set -eE

PLUGIN_NAME=ports_snapshot
SRC_DIR_PATH=/opt/ufm/ufm_plugin_${PLUGIN_NAME}/${PLUGIN_NAME}_plugin
CONFIG_PATH=/config

mkdir -p "$CONFIG_PATH" /data /log
cp "$SRC_DIR_PATH/conf/${PLUGIN_NAME}_httpd_proxy.conf" $SRC_DIR_PATH/conf/ports_snapshot_ui_conf.json "$CONFIG_PATH"
{
    echo "/opt/ufm/files/log/plugins/${PLUGIN_NAME}:/log"
    echo "/opt/ufm/ufm_plugins_data/${PLUGIN_NAME}:/data"
} > "$CONFIG_PATH/${PLUGIN_NAME}_shared_volumes.conf"

rm -rf /data/ports_snapshot_ui
cp -r "$SRC_DIR_PATH/ui_dist" "/data/ports_snapshot_ui"


required_ufm_version=(6 12 0)
if [ "${1:-}" = "-ufm_version" ]; then
    actual_ufm_version_string=${2:-0.0.0}
    actual_ufm_version=(${actual_ufm_version_string//./ })
    if [ "${actual_ufm_version[0]:-0}" -ge "${required_ufm_version[0]}" ] \
    && [ "${actual_ufm_version[1]:-0}" -ge "${required_ufm_version[1]}" ]; then
        exit 0
    fi
    echo "UFM version $actual_ufm_version_string is older than required ${required_ufm_version[*]}"
    exit 1
fi

exit 0
