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
# @author: Anan Al-Aghbar
# @date:   Aug 25, 2024
#

CONFIG_FOLDER="/config"

PLUGIN_CONF="$CONFIG_FOLDER/ufm_events_grafana_dashboard_plugin.conf"

ETC_PATH="/var/etc"
SUPERVISORD_PATH="$ETC_PATH/supervisor"
SUPERVISORD_CONF="$SUPERVISORD_PATH/conf.d/supervisord.conf"
PROMETHEUS_DATA_FOLDER="$CONFIG_FOLDER/prometheus/prometheus_db"
PROMETHEUS_CONF_FILE="$CONFIG_FOLDER/prometheus/prometheus-local-config.yaml"
PROMETHEUS_IP="127.0.0.1"
PROMETHEUS_PORT="9292"
PROMETHEUS_DB_DATA_RETENTION_SIZE="500MB"
PROMETHEUS_DB_DATA_RETENTION_TIME="15d"

# Function to read parameters from a configuration file
read_param_from_conf_file() {
  local config_file="$1"
  local param_key="$2"
  local default_value="$3"
  local value=""

  # Check if the config file exists
  if [[ ! -f "$config_file" ]]; then
      echo "$default_value"
  fi

  # Read the value associated with the key
  value=$(sed -n -e "s/^$param_key=\(.*\)/\1/p" "$config_file")

  # Check if the value was found
  if [[ -z "$value" ]]; then
      value="$default_value"
  fi
  echo "$value"
}

modify_prometheus_server_conf_file() {
  local prometheus_port="$1"
  local prometheus_yaml_path="$PROMETHEUS_CONF_FILE"

  echo "Updating the Prometheus port in $prometheus_yaml_path to $prometheus_port"

  sed -i "s|@@PROMETHEUS_PORT@@|$prometheus_port|g" "$prometheus_yaml_path"
}

modify_prometheus_service_in_supervisor() {
    local prometheus_ip="$1"
    local prometheus_port="$2"
    local prometheus_db_data_retention_size="$3"
    local prometheus_db_data_retention_time="$4"
    local prometheus_db_folder="$PROMETHEUS_DATA_FOLDER"
    local prometheus_config_file="$PROMETHEUS_CONF_FILE"
    local supervisor_conf="$SUPERVISORD_CONF"

    sed -i "s|@@prometheus_ip@@|$prometheus_ip|g" "$supervisor_conf"
    sed -i "s|@@prometheus_port@@|$prometheus_port|g" "$supervisor_conf"
    sed -i "s|@@prometheus_db_data_retention_size@@|$prometheus_db_data_retention_size|g" "$supervisor_conf"
    sed -i "s|@@prometheus_db_data_retention_time@@|$prometheus_db_data_retention_time|g" "$supervisor_conf"
    sed -i "s|@@prometheus_db_folder@@|$prometheus_db_folder|g" "$supervisor_conf"
    sed -i "s|@@prometheus_config_file@@|$prometheus_config_file|g" "$supervisor_conf"
}

# Read configuration parameters
PROMETHEUS_IP="$(read_param_from_conf_file "$PLUGIN_CONF" "prometheus_ip" "$PROMETHEUS_IP")"
PROMETHEUS_PORT="$(read_param_from_conf_file "$PLUGIN_CONF" "prometheus_port" "$PROMETHEUS_PORT")"
PROMETHEUS_DB_DATA_RETENTION_SIZE="$(read_param_from_conf_file "$PLUGIN_CONF" "prometheus_db_data_retention_size" "$PROMETHEUS_DB_DATA_RETENTION_SIZE")"
PROMETHEUS_DB_DATA_RETENTION_TIME="$(read_param_from_conf_file "$PLUGIN_CONF" "prometheus_db_data_retention_time" "$PROMETHEUS_DB_DATA_RETENTION_TIME")"


# Update Prometheus server conf in supervisord
modify_prometheus_service_in_supervisor "$PROMETHEUS_IP" "$PROMETHEUS_PORT" "$PROMETHEUS_DB_DATA_RETENTION_SIZE" "$PROMETHEUS_DB_DATA_RETENTION_TIME"

# Update prometheus-local-config.yaml file
modify_prometheus_server_conf_file "$PROMETHEUS_PORT"

echo "Starting supervisord..."
# Start services using supervisord
/usr/bin/supervisord -c "$SUPERVISORD_PATH"/supervisord.conf
