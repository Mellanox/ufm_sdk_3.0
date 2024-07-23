#!/bin/bash

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
