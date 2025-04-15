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
# This script prepares and checks NDT docker container Environment
# ================================================================

set -eE

readonly PLUGIN_DATA_PATH="/opt/ufm/ufm_plugins_data/ndt"
# Updating /config folder

cp --no-preserve=all /opt/ufm/ufm_plugin_ndt/ndt.conf /config
cp --no-preserve=all /opt/ufm/ufm_plugin_ndt/ndt_httpd_proxy.conf /config
cp --no-preserve=all /opt/ufm/ufm_plugin_ndt/ufm_plugin_ndt_httpd.conf /config
cp --no-preserve=all /opt/ufm/ufm_plugin_ndt/ndt_ui_conf.json /config
touch /config/ndt_shared_volumes.conf
touch /config/ndt_cmdline_args.conf

mkdir /config/reports
mkdir /config/merger_reports
mkdir /config/ndts
mkdir /config/merger_ndts
mkdir /config/topoconfig


if [[ "${READ_ONLY_FS}" == "true" ]]; then
    for dir_name in /data/tmp \
                    /data/var/tmp \
                    /data/var/log/supervisor \
                    ;
         do
         mkdir -p "${dir_name}"
    done
    for vol in \
        "${PLUGIN_DATA_PATH}/tmp:/tmp" \
        "${PLUGIN_DATA_PATH}/var/tmp:/var/tmp" \
        "${PLUGIN_DATA_PATH}/data/var/log/supervisor:/var/log/supervisor" \
         ;
         do
            echo "$vol" >> /config/ndt_shared_volumes.conf
         done
fi


# UFM version test
required_ufm_version=(6 7 0)
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
