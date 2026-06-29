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
#
from typing import List

from utils.config_parser import ConfigParser
from utils.singleton import Singleton


class UFMEventsGrafanaConfigParser(ConfigParser, Singleton):

    # for debugging
    # CONFIG_FILE = '../../conf/ufm_events_grafana_dashboard_plugin.conf'

    CONFIG_FILE = '/config/ufm_events_grafana_dashboard_plugin.conf'

    TELEMETRY_CONFIG_SECTION = 'telemetry'
    TELEMETRY_CONFIG_URL = 'url'
    TELEMETRY_CONFIG_INTERVAL = 'interval'
    TELEMETRY_CONFIG_ENABLED = 'enabled'
    TELEMETRY_CONFIG_PROMETHEUS_LABELS = 'labels_to_export_to_prometheus'
    TELEMETRY_CONFIG_PROMETHEUS_METRICS = 'metrics_to_export_to_prometheus'
    ############
    PROMETHEUS_CONFIG_SECTION = "prometheus"
    PROMETHEUS_SECTION_IP = "prometheus_ip"
    PROMETHEUS_SECTION_PORT = "prometheus_port"
    PROMETHEUS_REMOTE_WRITE_MAX_CHUNK_SIZE = "prometheus_remote_write_max_chunk_size"

    def __init__(self):
        super().__init__(read_sdk_config=False)
        self.sdk_config.read(self.CONFIG_FILE)

    def get_telemetry_url(self) -> str:
        return self.get_config_value(None,
                                     self.TELEMETRY_CONFIG_SECTION,
                                     self.TELEMETRY_CONFIG_URL,
                                     'http://127.0.0.1:9002/csv/xcset/low_freq_debug')

    def get_telemetry_interval(self) -> int:
        return self.safe_get_int(None,
                                 self.TELEMETRY_CONFIG_SECTION,
                                 self.TELEMETRY_CONFIG_INTERVAL,
                                 300)

    def get_telemetry_enabled(self) -> bool:
        return self.safe_get_bool(None,
                                  self.TELEMETRY_CONFIG_SECTION,
                                  self.TELEMETRY_CONFIG_ENABLED,
                                  True)

    def get_telemetry_labels_to_export_to_prometheus(self) -> List[str]:
        return self.safe_get_list(None,
                                  self.TELEMETRY_CONFIG_SECTION,
                                  self.TELEMETRY_CONFIG_PROMETHEUS_LABELS,
                                  'Node_GUID,port_guid,Port_Number,Device_ID,node_description')

    def get_telemetry_metrics_to_export_to_prometheus(self) -> List[str]:
        return self.safe_get_list(None,
                                  self.TELEMETRY_CONFIG_SECTION,
                                  self.TELEMETRY_CONFIG_PROMETHEUS_METRICS,
                                  'Link_Down')

    #####################################

    def get_prometheus_ip(self) -> str:
        return self.get_config_value(None,
                                     self.PROMETHEUS_CONFIG_SECTION,
                                     self.PROMETHEUS_SECTION_IP, "127.0.0.1")

    def get_prometheus_port(self) -> str:
        return self.get_config_value(None,
                                     self.PROMETHEUS_CONFIG_SECTION,
                                     self.PROMETHEUS_SECTION_PORT, "9292")

    def get_prometheus_request_max_chunk_size(self) -> int:
        return self.safe_get_int(None,
                                 self.PROMETHEUS_CONFIG_SECTION,
                                 self.PROMETHEUS_REMOTE_WRITE_MAX_CHUNK_SIZE, 10000)
