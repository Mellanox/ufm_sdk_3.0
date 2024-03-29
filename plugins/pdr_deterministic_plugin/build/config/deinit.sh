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
# This script prepares and checks "uptime": "N\/A", docker container Environment
# ================================================================

set -eE

rm -f /log/pdr_deterministic*.log*
curl -X "DELETE" http://127.0.0.1:8000/app/telemetry/instances/pdr_dynamic -H "X-Remote-User: ufmsystem"
exit 0
