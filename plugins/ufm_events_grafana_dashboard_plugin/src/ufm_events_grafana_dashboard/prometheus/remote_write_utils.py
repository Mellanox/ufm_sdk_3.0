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
import requests
import snappy
import calendar

from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from prometheus.prometheus_pb2 import WriteRequest
from utils.logger import Logger, LOG_LEVELS

BASE_LABELS = ['Node_GUID', 'port_guid', 'Port_Number', 'Device_ID', 'node_description']
DEFAULT_TARGET_IP = "localhost"
DEFAULT_TARGET_PORT = "9292"


def dt2ts(dt):
    """Converts a datetime object to UTC timestamp
    naive datetime will be considered UTC.
    """
    return calendar.timegm(dt.utctimetuple())


def send(write_request, target_id=DEFAULT_TARGET_IP, target_port=DEFAULT_TARGET_PORT):
    """
    Send Write Request to Prometheus DB
    """
    uncompressed = write_request.SerializeToString()
    compressed = snappy.compress(uncompressed)
    url = f"http://{target_id}:{target_port}/api/v1/write"
    headers = {
        "Content-Encoding": "snappy",
        "Content-Type": "application/x-protobuf",
        "X-Prometheus-Remote-Write-Version": "0.1.0",
        "User-Agent": "metrics-worker"
    }
    try:
        # pylint: disable=missing-timeout
        response = requests.post(url, headers=headers, data=compressed)
        if response.status_code in [204, 200]:
            return True
        err_msg = f'failed to send metrics to server {target_id}:{target_port}, ' \
                  f'with response info: {response.status_code} {response.text}'
        Logger.log_message(err_msg, LOG_LEVELS.WARNING)
        return False
    # pylint: disable=broad-exception-caught
    except Exception as e:
        Logger.log_message(e, LOG_LEVELS.ERROR)
    return False


def add_metric(write_request, name: str, labels: dict, value: float, timestamp: int = None):
    """
    Add counter/metric to write_request object
    """
    series = write_request.timeseries.add()

    # name label always required
    label = series.labels.add()
    label.name = "__name__"
    label.value = name

    for label_name, label_value in labels.items():
        label = series.labels.add()
        label.name = label_name
        label.value = label_value

    sample = series.samples.add()
    sample.value = value
    sample.timestamp = timestamp or (dt2ts(datetime.utcnow()) * 1000)


def split_metrics_into_chunks(data: list, chunk_size: int):
    """Yield successive chunk_size chunks from data."""
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]


def write_from_list_metrics(metrics_data: list,
                            target_id=DEFAULT_TARGET_IP,
                            target_port=DEFAULT_TARGET_PORT):
    """
    :param metrics_data:
    [{counter_name:{labels:{label:value,..},counter_value:value,timestamp:value}]
    :param target_id:
    :param target_port:
    :return:
    """
    write_request = WriteRequest()
    for data in metrics_data:
        for counter, counter_data in data.items():
            labels = counter_data.get('labels')
            counter_value = counter_data.get('counter_value')
            timestamp = counter_data.get('timestamp')

            add_metric(write_request, counter, labels, counter_value, timestamp)
    # Send to remote write endpoint
    return send(write_request, target_id, target_port)


def write_from_chunk_metrics(metrics_data: list, chunk_index: int,
                             target_id=DEFAULT_TARGET_IP, target_port=DEFAULT_TARGET_PORT):
    debug_msg = f"Start processing metrics chunk [{chunk_index}]"
    Logger.log_message(debug_msg, LOG_LEVELS.DEBUG)
    success = write_from_list_metrics(metrics_data, target_id, target_port)
    if success:
        debug_msg = f"Successfully sent metrics chunk [{chunk_index}]"
        Logger.log_message(debug_msg, LOG_LEVELS.DEBUG)
    else:
        err_msg = f"Failed to send metrics chunk [{chunk_index}]"
        Logger.log_message(err_msg, LOG_LEVELS.WARNING)
    return success


def write_from_list_metrics_in_chunks(metrics_data: list,
                                      target_id=DEFAULT_TARGET_IP, target_port=DEFAULT_TARGET_PORT,
                                      max_chunk_size=10000, max_workers=5):
    """
    Send metrics_data list in chunks to Prometheus DB
    """
    metrics_chunks = list(split_metrics_into_chunks(metrics_data, max_chunk_size))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        write_requests = {
            executor.submit(write_from_chunk_metrics, chunk, i, target_id, target_port):
                i for i, chunk in enumerate(metrics_chunks)
        }
        for request in as_completed(write_requests):
            chunk_index = write_requests[request]
            if not request.result():
                err_msg = f"Metrics Chunk [{chunk_index}] failed to send."
                Logger.log_message(err_msg, LOG_LEVELS.ERROR)
