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

# Update and install prerequisites
apt-get update && apt-get install -y curl gnupg build-essential ruby ruby-dev

# Install Fluentd
gem install fluentd --no-document

# Install Fluentd plugins
fluent-gem install fluent-plugin-script fluent-plugin-grafana-loki

# Clean up development packages
apt-get remove --purge -y ruby-dev build-essential
apt-get autoremove -y
apt-get clean
rm -rf /var/lib/apt/lists/*
