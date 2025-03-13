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

mkdir -p /config
cp /opt/ufm/ufm_plugin_tfs/*.conf /config
cp fluentd_telemetry_plugin.cfg /config

if [[ "${READ_ONLY_FS}" == "true" ]]; then
    PLUGIN_DATA_PATH=/opt/ufm/ufm_plugins_data/tfs
    for vol in \
    "${PLUGIN_DATA_PATH}/tmp:/tmp" 
    do
        echo "$vol" >> "/config/tfs_shared_volumes.conf"
    done
fi 

exit 1
