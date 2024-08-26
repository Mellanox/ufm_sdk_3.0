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

import pandas as pd
import time
from io import StringIO

from mgr.configurations_mgr import UFMEventsGrafanaConfigParser
from data.listeners.base_listener import BaseListener
from data.models.telemetry_metrics_model import TelemetryMetricsModel
from constants import DataType, Prometheus
from prometheus.remote_write_utils import write_from_list_metrics_in_chunks


class TelemetryPrometheusExporter(BaseListener):

    def __init__(self, data_manager: 'Type[DataManager]'):
        super().__init__(data_manager, [DataType.TELEMETRY])
        conf: UFMEventsGrafanaConfigParser = UFMEventsGrafanaConfigParser.getInstance()
        self.prometheus_ip = conf.get_prometheus_ip()
        self.prometheus_port = conf.get_prometheus_port()
        self.prometheus_max_chunk_size = conf.get_prometheus_request_max_chunk_size()
        self.telemetry_prometheus_labels = conf.get_telemetry_labels_to_export_to_prometheus()
        self.telemetry_prometheus_metrics = conf.get_telemetry_metrics_to_export_to_prometheus()

    def update_data(self):
        telemetry_model: TelemetryMetricsModel = self.data_manager.get_model_by_data_type(DataType.TELEMETRY)
        with telemetry_model.lock:
            prometheus_labels = self.telemetry_prometheus_labels
            prometheus_metrics = self.telemetry_prometheus_metrics
            data = telemetry_model.last_metrics_csv
            df = pd.read_csv(StringIO(data))
            df.fillna('', inplace=True)
            data_dict = df.to_dict(orient='records')
            metrics = []
            for row in data_dict:
                metrics_dict = {}
                basic_metric = {
                    Prometheus.TIMESTAMP: int(round(row.get('timestamp', time.time() * 1000))),
                    Prometheus.LABELS: {label: str(row.get(label, '')) for label in prometheus_labels}
                }
                for metric in prometheus_metrics:
                    value = row.get(metric, None)
                    if value is not None:
                        metrics_dict[metric] = {
                            **basic_metric,
                            Prometheus.COUNTER_VALUE: value
                        }
                metrics.append(metrics_dict)

            write_from_list_metrics_in_chunks(metrics_data=metrics,
                                              target_id=self.prometheus_ip,
                                              target_port=self.prometheus_port,
                                              max_chunk_size=self.prometheus_max_chunk_size)
