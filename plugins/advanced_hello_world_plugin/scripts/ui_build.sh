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
# @author: Anan Al-Aghbar
# @date:   Jan 29, 2023
#

#!/bin/bash

set -eE

PLUGIN_NAME=$1

curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash
apt-get update && apt-get install -y nodejs

UI_SRC_PATH=/opt/ufm/ufm_plugin_${PLUGIN_NAME}/${PLUGIN_NAME}_plugin/src/${PLUGIN_NAME}_ui
OUTPUT_PATH=/opt/ufm/ufm_plugin_${PLUGIN_NAME}/${PLUGIN_NAME}_plugin/${PLUGIN_NAME}_ui
cd ${UI_SRC_PATH} ; \
npm install --force; \
node node_modules/@angular/cli/bin/ng build --output-path=${OUTPUT_PATH} ; \
apt-get -y purge nodejs; \
apt-get -y autoremove

rm -rf ${UI_SRC_PATH}

exit 0
