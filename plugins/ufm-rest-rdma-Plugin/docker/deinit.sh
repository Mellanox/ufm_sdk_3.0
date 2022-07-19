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

# =====================================================================
# This script prepares and checks UFM REST docker/container Environment
# =====================================================================

echo "Running deinit.sh"

set -eE

# removing log file
LOG_FILE=/opt/ufm/files/log/ufm_rest_over_rdma.log
SR_LOG_FILE=/opt/ufm/files/log/ufm_rest_over_rdma_sr_lib.log

log_files_to_remove=( $LOG_FILE $SR_LOG_FILE )

for log_file in ${log_files_to_remove[@]}; do
    if [ -f $log_file ]; then
       rm $log_file
    fi
done
exit 0

