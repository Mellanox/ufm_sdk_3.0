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
#

set -eE
python3 /opt/ufm/snmp_plugin/snmp_server/unregister_switches.py
LOG_FILE=/log/snmptrap.log
if test -f "$LOG_FILE"; then
    rm "$LOG_FILE"
fi
exit 0
