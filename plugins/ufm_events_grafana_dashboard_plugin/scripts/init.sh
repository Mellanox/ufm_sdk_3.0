#!/bin/bash
#
# Copyright © 2013-2024 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
# @author: Anan Al-Aghbar
# @date:   July 18, 2024
#
set -eE
PLUGIN_NAME=ufm_events_grafana_dashboard
SRC_DIR_PATH=/opt/ufm/ufm_plugin_${PLUGIN_NAME}/${PLUGIN_NAME}_plugin
CONFIG_PATH=/config

cp -r ${SRC_DIR_PATH}/conf/* ${CONFIG_PATH}

# UFM version test
required_ufm_version=${REQUIRED_UFM_VERSION}
# Check if the environment variable is set
if [ -z "${required_ufm_version}" ]; then
  required_ufm_version=6.12.0
fi
required_ufm_version=(${required_ufm_version//./ })
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