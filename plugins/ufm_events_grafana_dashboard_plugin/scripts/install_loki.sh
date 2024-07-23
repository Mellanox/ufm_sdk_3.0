#!/bin/bash

# Install prerequisites
apt-get update && apt-get install -y wget unzip

# Download and install Loki
wget https://github.com/grafana/loki/releases/download/v3.1.0/loki-linux-amd64.zip
unzip loki-linux-amd64.zip
mv loki-linux-amd64 /usr/local/bin/loki
rm loki-linux-amd64.zip
