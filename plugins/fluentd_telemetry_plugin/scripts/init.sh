#!/bin/bash
# Copyright (C) Mellanox Technologies Ltd. 2001-2021.   ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Mellanox Technologies Ltd.
# (the "Company") and all right, title, and interest in and to the software product,
# including all associated intellectual property rights, are and shall
# remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.

# ================================================================
# This script prepares and checks TFS docker container Environment
# ================================================================

set -eE

# Define readonly variables for the plugin init script
readonly PLUGIN_NAME="tfs"
readonly TFS_PLUGIN_DIR="/opt/ufm/ufm_plugin_${PLUGIN_NAME}"
readonly CONFIG_PATH="/config"
readonly PLUGIN_DATA_PATH="/opt/ufm/ufm_plugins_data/${PLUGIN_NAME}"
readonly SHARED_VOLUMES_PATH="${CONFIG_PATH}/${PLUGIN_NAME}_shared_volumes.conf"

# Create the config folder
mkdir -p "$CONFIG_PATH"

# Copy configuration files to the config folder
cp "$TFS_PLUGIN_DIR"/*.conf $CONFIG_PATH
cp "$TFS_PLUGIN_DIR"/fluentd_telemetry_plugin.cfg $CONFIG_PATH

# If the file system is read-only non root
if [[ "${READ_ONLY_FS}" == "true" ]]; then
    # Generate the shared volumes configuration
    for vol in \
    "${PLUGIN_DATA_PATH}/tmp:/tmp" \
    "${PLUGIN_DATA_PATH}/var/tmp:/var/tmp" 
    do
        echo "$vol" >> "$SHARED_VOLUMES_PATH"
    done
fi 

exit 0
