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
# This script prepares and checks grafana-dashboard docker container Environment
# ================================================================

set -eE

SRC_DIR_PATH=/opt/ufm/ufm_plugin_git/grafana_infiniband_telemetry_plugin
CONFIG_PATH=/config

cp $SRC_DIR_PATH/conf/grafana-dashboard_httpd_proxy.conf ${CONFIG_PATH}
cp $SRC_DIR_PATH/conf/grafana_infiniband_telemetry_plugin.cfg ${CONFIG_PATH}

touch ${CONFIG_PATH}/grafana-dashboard_shared_volumes.conf

echo /opt/ufm/files/log/:/log > ${CONFIG_PATH}/grafana-dashboard_shared_volumes.conf

# UFM version test
required_ufm_version=(6 10 0)
echo "Required UFM version: ${required_ufm_version[0]}.${required_ufm_version[1]}.${required_ufm_version[2]}"

if [ "$1" == "-ufm_version" ]; then
    actual_ufm_version_string=$2
    actual_ufm_version=(${actual_ufm_version_string//./ })
    echo "Actual UFM version: ${actual_ufm_version[0]}.${actual_ufm_version[1]}.${actual_ufm_version[2]}"
    if [ ${actual_ufm_version[0]} -ge ${required_ufm_version[0]} ] \
    && [ ${actual_ufm_version[1]} -ge ${required_ufm_version[1]} ] \
    && [ ${actual_ufm_version[2]} -ge ${required_ufm_version[2]} ]; then
        echo "UFM version meets the requirements"
        exit 0
    else
        echo "UFM version is older than required"
        exit 1
    fi
else
    exit 1
fi

exit 1
