#!/bin/bash
#
# Copyright (C) 2013-2022 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
#


set -eE

cp /opt/ufm/ufm_plugin_bright/bright_httpd_proxy.conf /config
cp /opt/ufm/ufm_plugin_bright/bright_plugin.cfg /config

touch /config/bright_shared_volumes.conf

echo /opt/ufm/files/log/:/log > /config/bright_shared_volumes.conf

# you need to verify if the dir already exists; then no need to create it
mkdir /opt/ufm/ufm_plugin_bright/bright_certfs

echo /opt/ufm/ufm_plugin_bright/bright_certfs:/opt/ufm/ufm_plugin_bright/bright_certfs

# UFM version test
required_ufm_version=(6 8 0)
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
