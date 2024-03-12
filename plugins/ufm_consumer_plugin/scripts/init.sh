#!/bin/bash
#
# Copyright (C) 2013-2024 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
# @author: Alex Tabachnik
# @date:   Feb 10, 2024
#
# ================================================================
# This script prepares and checks ufm_consumer docker container Environment
# ================================================================

set -eE
PLUGIN_NAME=ufm_consumer
SRC_DIR_PATH=/opt/ufm/ufm_plugin_${PLUGIN_NAME}/${PLUGIN_NAME}_plugin
CONFIG_PATH=/config

echo /opt/ufm/files/licenses:/opt/ufm/files/licenses > /config/${PLUGIN_NAME}_shared_volumes.conf

cp $SRC_DIR_PATH/conf/${PLUGIN_NAME}_httpd_proxy.conf $SRC_DIR_PATH/conf/${PLUGIN_NAME}_plugin.conf $SRC_DIR_PATH/conf/${PLUGIN_NAME}_ui_conf.json ${CONFIG_PATH}

# UFM version test
required_ufm_version=(6 14 0)
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
