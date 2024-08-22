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


# Install prerequisites
apt-get update && apt-get install -y wget libfontconfig1 musl || apt --fix-broken install -y

# Download and install Grafana
wget https://dl.grafana.com/oss/release/grafana_11.1.0_amd64.deb
dpkg -i grafana_11.1.0_amd64.deb
rm grafana_11.1.0_amd64.deb
