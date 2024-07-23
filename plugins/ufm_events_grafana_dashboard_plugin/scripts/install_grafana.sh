#!/bin/bash

# Install prerequisites
apt-get update && apt-get install -y wget libfontconfig1 musl || apt --fix-broken install -y

# Download and install Grafana
wget https://dl.grafana.com/oss/release/grafana_11.1.0_amd64.deb
dpkg -i grafana_11.1.0_amd64.deb
rm grafana_11.1.0_amd64.deb
