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

# ====================================================================
# This script prepares and checks  NDT docker/container Environment
# ====================================================================


SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"

LICENSE_FILE=$1

UFM_DIR="${SCRIPT_DIR}/.."

echo "Running init.sh"

#Test UFM version if plugin can run with UFM.
#cmd ./init.sh –ufm_version “6.7.0 build 9”
#cmd ./init.sh -v “6.7.0 build 9”
#/opt/ufm/version/release

#Updating /confiag folder
touch /config/UFM_REST.conf
touch /config/ufm_plugin_UFM_REST_httpd.conf
touch /config/UFM_REST_shared_volumes.conf
touch /config/UFM_REST_cmdline_args.conf

#release_version=$(</opt/ufm/version/release)
release_version="6.7.0 build 9"
echo "Actual Release Build Version: $release_version"

if [ "$1" == "-ufm_version" ]; then
          ufm_version=$2
          echo "Required Release UFM Version Build: $ufm_version"
          if [ "$release_version" == "$ufm_version" ]; then
                echo "Actual and Required Build Versions are same"
                exit 0
          else
                echo "Actual and Required Build Versions are not same"
                exit 1
          fi
else
    exit 1
fi


exit 1
