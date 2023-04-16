#!/bin/bash
#
# Copyright © 2013-2023 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
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
cp -f /opt/ufm/snmp_plugin/*.conf /config
cp -f /opt/ufm/snmp_plugin/snmp_server/traps_policy.csv /data
exit 0
