#!/bin/bash
# Copyright (C) Mellanox Technologies Ltd. 2001-2023.   ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Mellanox Technologies Ltd.
# (the "Company") and all right, title, and interest in and to the software product,
# including all associated intellectual property rights, are and shall
# remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.

# ================================================================
# This script prepares and checks sysinfo docker container Environment
# ================================================================

set -eE

# Updating /config folder
#mv /opt/ufm/ufm_plugin_sysinfo/sysinfo.conf /config
#mv /opt/ufm/ufm_plugin_sysinfo/sysinfo_httpd_proxy.conf /config
#mv /opt/ufm/ufm_plugin_sysinfo/ufm_plugin_sysinfo_httpd.conf /config
cp -f /opt/ufm/ufm_plugin_sysinfo/*.conf /config

echo /opt/ufm/files/log:/log > /config/sysinfo_shared_volumes.conf

exit 0
