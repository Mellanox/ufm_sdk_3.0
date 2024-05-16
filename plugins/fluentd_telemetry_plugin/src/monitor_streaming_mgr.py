"""
@copyright:
    Copyright (C) Mellanox Technologies Ltd. 2014-2020.  ALL RIGHTS RESERVED.

    This software product is a proprietary product of Mellanox Technologies
    Ltd. (the "Company") and all right, title, and interest in and to the
    software product, including all associated intellectual property rights,
    are and shall remain exclusively with the Company.

    This software product is governed by the End User License Agreement
    provided with the software product.

@author: Anan Al-Aghbar
@date:   Jan 17, 2024
"""
from prometheus_client import Gauge, CollectorRegistry, generate_latest


class MonitorStreamingMgr:
    """
    MonitorStreamingMgr class
    To manage the streaming statistics metrics/attributes
    that will be used to monitor the streaming pipeline
    """

    def __init__(self):

        self.num_of_processed_counters_in_last_msg_key = 'num_of_processed_counters_in_last_msg'
        self.num_of_streamed_ports_in_last_msg_key = 'num_of_streamed_ports_in_last_msg'
        self.streaming_time_seconds_key = 'streaming_time_seconds'
        self.telemetry_expected_response_size_bytes_key = 'telemetry_expected_response_size_bytes'
        self.telemetry_received_response_size_bytes_key = 'telemetry_received_response_size_bytes'
        self.telemetry_response_time_seconds_key = 'telemetry_response_time_seconds'
        self.telemetry_response_process_time_seconds_key = 'telemetry_response_process_time_seconds'

        self.metrics_registry = CollectorRegistry()
        self.metrics = {
            self.num_of_processed_counters_in_last_msg_key: Gauge(self.num_of_processed_counters_in_last_msg_key,
                                                                  'Number of processed counters/attributes in the last streaming interval',
                                                                  ['endpoint'],
                                                                  registry=self.metrics_registry),
            self.num_of_streamed_ports_in_last_msg_key: Gauge(self.num_of_streamed_ports_in_last_msg_key,
                                                              'Number of processed ports in the last streaming interval',
                                                              ['endpoint'],
                                                              registry=self.metrics_registry),
            self.streaming_time_seconds_key: Gauge(self.streaming_time_seconds_key,
                                                   'Time period for last streamed message in seconds',
                                                   ['endpoint'],
                                                   registry=self.metrics_registry),
            self.telemetry_expected_response_size_bytes_key: Gauge(self.telemetry_expected_response_size_bytes_key,
                                                                   'Expected size of the last received telemetry response in bytes',
                                                                   ['endpoint'],
                                                                   registry=self.metrics_registry),
            self.telemetry_received_response_size_bytes_key: Gauge(self.telemetry_received_response_size_bytes_key,
                                                                   'Actual size of the last received telemetry response in bytes',
                                                                   ['endpoint'],
                                                                   registry=self.metrics_registry),
            self.telemetry_response_time_seconds_key: Gauge(self.telemetry_response_time_seconds_key,
                                                            'Response time of the last telemetry request in seconds',
                                                            ['endpoint'],
                                                            registry=self.metrics_registry),
            self.telemetry_response_process_time_seconds_key: Gauge(self.telemetry_response_process_time_seconds_key,
                                                                    'Processing time of the last received telemetry response in seconds',
                                                                    ['endpoint'],
                                                                    registry=self.metrics_registry)
        }

    def update_streaming_metrics(self, endpoint, **kwargs):
        for key, value in kwargs.items():
            metric_obj = self.metrics.get(key)
            if metric_obj:
                metric_obj.labels(endpoint).set(value)

    def get_streaming_metrics_text(self):
        return generate_latest(self.metrics_registry)
