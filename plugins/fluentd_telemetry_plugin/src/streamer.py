#!/usr/bin/python3

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
@date:   Nov 23, 2021
"""
import time
import json
import gzip
import logging
import datetime
import requests

from fluentbit_writer import init_fb_writer
from monitor_streaming_mgr import MonitorStreamingMgr
from plugins.fluentd_telemetry_plugin.src.telemetry_http_client import TelemetryHTTPClient
from telemetry_attributes_manager import TelemetryAttributesManager
from streaming_config_parser import UFMTelemetryStreamingConfigParser
from telemetry_constants import UFMTelemetryConstants
from telemetry_parser import TelemetryParser

# pylint: disable=no-name-in-module,import-error
from utils.utils import Utils
from ufm_sdk_tools.src.utils.singleton import SingletonMeta

class InvalidConfSetting(Exception):
    """InvalidConfSetting Exception class for problem with the configuration file or updating"""

    def __init__(self, message):
        Exception.__init__(self, message)


#pylint: disable=too-many-instance-attributes
class UFMTelemetryStreaming(metaclass=SingletonMeta):
    """
    UFMTelemetryStreaming class
    to manage/control the streaming
    """
    def __init__(self):
        self.initialized = True
        self.config_parser = UFMTelemetryStreamingConfigParser()
        self.last_streamed_data_sample_timestamp = None
        self.last_streamed_data_sample_per_endpoint = {}
        self.streaming_metrics_mgr = MonitorStreamingMgr()
        self._fluent_sender = None
        self.attributes_mngr = TelemetryAttributesManager()
        self.telem_parser = TelemetryParser(self.config_parser, self.streaming_metrics_mgr,
                                            self.last_streamed_data_sample_per_endpoint,
                                            self.attributes_mngr)
        self.init_streaming_attributes()

    def init_streaming_attributes(self):
        self.attributes_mngr.init_streaming_attributes(self.telem_parser,
                                                       self.ufm_telemetry_endpoints, self.config_parser)

    @property
    def ufm_telemetry_host(self):
        return self.config_parser.get_telemetry_host()

    @property
    def ufm_telemetry_port(self):
        return self.config_parser.get_telemetry_port()

    @property
    def ufm_telemetry_url(self):
        return self.config_parser.get_telemetry_url()

    @property
    def ufm_telemetry_xdr_mode_flag(self):
        return self.config_parser.get_ufm_telemetry_xdr_mode_flag()

    @property
    def ufm_telemetry_xdr_ports_types(self):
        return self.config_parser.get_ufm_telemetry_xdr_ports_types()

    @property
    def streaming_interval(self):
        return self.config_parser.get_streaming_interval()

    @property
    def fluentd_msg_tag(self):
        return self.config_parser.get_fluentd_msg_tag()

    @property
    def ufm_telemetry_endpoints(self):
        splitter = ","
        hosts = self.ufm_telemetry_host.split(splitter)
        ports = self.ufm_telemetry_port.split(splitter)
        urls = self.ufm_telemetry_url.split(splitter)
        xdr_mode = self.ufm_telemetry_xdr_mode_flag.split(splitter)
        xdr_ports_types = self.ufm_telemetry_xdr_ports_types.split(splitter)
        intervals = self.streaming_interval.split(splitter)
        msg_tags = self.fluentd_msg_tag.split(splitter)

        bad_settings_name = []
        bad_settings_length = []
        expected_amount = len(hosts)
        for name, array in [("port", ports), ("url", urls), ("interval" ,intervals), ("message_tag_name", msg_tags),\
                             ("xdr_mode", xdr_mode), ("xdr_ports_types", xdr_ports_types)]:
            if len(array)!= expected_amount:
                bad_settings_name.append(name)
                bad_settings_length.append(len(array))

        if len(bad_settings_name)>0:
            raise InvalidConfSetting(f"The following field {bad_settings_name} in the ufm-telemetry-endpoint section are expected"\
                    + f"to contain comma-separated values with a length of {expected_amount}."\
                    + f"However, the provided values have a length of {len(bad_settings_length)}")

        endpoints = []
        for i, value in enumerate(hosts):
            _is_xdr_mode = Utils.convert_str_to_type(xdr_mode[i], 'boolean')
            _url = TelemetryParser.append_filters_to_telemetry_url(
                urls[i],
                _is_xdr_mode,
                xdr_ports_types[i].split(self.config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_XDR_PORTS_TYPE_SPLITTER)
            )
            endpoints.append({
                self.config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_HOST: value,
                self.config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_PORT: ports[i],
                self.config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_URL: _url,
                self.config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_XDR_MODE: _is_xdr_mode,
                self.config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_INTERVAL: intervals[i],
                self.config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_MSG_TAG_NAME:
                    msg_tags[i] if msg_tags[i] else f'{value}:{ports[i]}/{_url}',
                self.telem_parser.HTTP_CLIENT_KEY: TelemetryHTTPClient() # Client per endpoint -> Different port per endpoint
            })
        return endpoints

    @property
    def bulk_streaming_flag(self):
        return self.config_parser.get_bulk_streaming_flag()

    @property
    def c_fluent_streamer_flag(self):
        return self.config_parser.get_c_fluent_streamer_flag()

    @property
    def compressed_streaming_flag(self):
        return self.config_parser.get_compressed_streaming_flag()

    @property
    def stream_only_new_samples(self):
        return self.config_parser.get_stream_only_new_samples_flag()

    @property
    def stream_cached_data_on_telemetry_fail_is_enabled(self):
        return self.config_parser.get_enable_cached_stream_on_telemetry_fail()

    @property
    def fluentd_host(self):
        return self.config_parser.get_fluentd_host()

    @property
    def fluentd_port(self):
        return self.config_parser.get_fluentd_port()

    @property
    def fluentd_timeout(self):
        return self.config_parser.get_fluentd_timeout()

    @property
    def fluent_sender(self):
        _use_c = self.c_fluent_streamer_flag
        if self._fluent_sender and _use_c:
            # in case of C sender, and if the object already initialized
            # no need to init a new sender
            return self._fluent_sender
        host = self.fluentd_host
        port = self.fluentd_port
        timeout = self.fluentd_timeout
        self._fluent_sender = init_fb_writer(host=host,
                                             port=port,
                                             tag_prefix=UFMTelemetryConstants.PLUGIN_NAME,
                                             timeout=timeout,
                                             use_c=_use_c)
        return self._fluent_sender


    def _stream_data_to_fluentd(self, data_to_stream, fluentd_msg_tag=''):
        logging.info('Streaming to Fluentd IP: %s port: %s timeout: %s',
                     self.fluentd_host, self.fluentd_port, self.fluentd_timeout)
        start_time = time.time()
        try:
            fluentd_message = {
                "timestamp": datetime.datetime.fromtimestamp(int(time.time())).strftime('%Y-%m-%d %H:%M:%S'),
                "type": "full",
                "values": data_to_stream
            }

            if self.compressed_streaming_flag:
                plugin_fluent_protocol = 'HTTP'
                _fluentd_host = self.fluentd_host
                _fluentd_host = f'[{_fluentd_host}]' if Utils.is_ipv6_address(_fluentd_host) else _fluentd_host
                compressed = gzip.compress(json.dumps(fluentd_message).encode('utf-8'))

                res = requests.post(
                    url=f'http://{_fluentd_host}:{self.fluentd_port}/'
                        f'{UFMTelemetryConstants.PLUGIN_NAME}.{fluentd_msg_tag}',
                    data=compressed,
                    headers={"Content-Encoding": "gzip", "Content-Type": "application/json"},
                    timeout=self.fluentd_timeout)
                res.raise_for_status()
            else:
                plugin_fluent_protocol = 'FORWARD'
                self.fluent_sender.write(fluentd_msg_tag, fluentd_message)
            end_time = time.time()
            streaming_time = round(end_time-start_time, 6)
            self.streaming_metrics_mgr.update_streaming_metrics(fluentd_msg_tag, **{
                self.streaming_metrics_mgr.streaming_time_seconds_key: streaming_time
            })
            logging.info('Finished Streaming to Fluentd Host: %s port: %s in %.2f Seconds using %s plugin protocol',
                         self.fluentd_host, self.fluentd_port, streaming_time, plugin_fluent_protocol)
        except requests.exceptions.Timeout as ex:
            logging.error('Timeout streaming to Fluentd %s:%s - %s', self.fluentd_host, self.fluentd_port, str(ex))
        except requests.exceptions.ConnectionError as ex:
            logging.error('Failed to connect to Fluentd %s:%s - %s', self.fluentd_host, self.fluentd_port, str(ex))
        except requests.exceptions.RequestException as ex:
            logging.error('HTTP error streaming to Fluentd %s:%s - %s', self.fluentd_host, self.fluentd_port, str(ex))
        except Exception as ex:  # pylint: disable=broad-except
            logging.error('Failed to stream the data due to the error: %s', str(ex))

    def stream_data(self, telemetry_endpoint):  # pylint: disable=too-many-locals
        _host = telemetry_endpoint.get(self.config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_HOST)
        _port = telemetry_endpoint.get(self.config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_PORT)
        _url = telemetry_endpoint.get(self.config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_URL)
        msg_tag = telemetry_endpoint.get(self.config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_MSG_TAG_NAME)
        is_xdr_mode = telemetry_endpoint.get(self.config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_XDR_MODE)
        telemetry_data = self.telem_parser.get_metrics(telemetry_endpoint)
        try:
            data_to_stream = []
            new_data_timestamp = None
            num_of_counters = data_len = 0
            if telemetry_data is not None: # None = Failed, Empty = No new data
                if self.last_streamed_data_sample_per_endpoint.get(msg_tag, None) is None:
                    self.last_streamed_data_sample_per_endpoint[msg_tag] = {}
                logging.info('Start Processing The Received Response From %s', msg_tag)
                start_time = time.time()
                data_to_stream, new_data_timestamp, num_of_counters = \
                    self.telem_parser.parse_telemetry_csv_metrics_to_json(telemetry_data, msg_tag,
                                                                          is_xdr_mode,
                                                                          self.stream_only_new_samples)

                end_time = time.time()
                data_len = len(data_to_stream)
                resp_process_time = round(end_time - start_time, 6)
                self.streaming_metrics_mgr.update_streaming_metrics(msg_tag, **{
                    self.streaming_metrics_mgr.telemetry_response_process_time_seconds_key: resp_process_time
                })
                logging.info('Processing of endpoint %s Completed In: %.2f Seconds. '
                             '(%d) Ports, (%d) Counters Were Handled',
                             msg_tag, resp_process_time, data_len, num_of_counters)
            elif self.stream_cached_data_on_telemetry_fail_is_enabled and \
                    self.last_streamed_data_sample_per_endpoint.get(msg_tag):
                # if the telemetry endpoint currently unavailable, try to get the cached data
                data_to_stream = list(self.last_streamed_data_sample_per_endpoint[msg_tag].values())
                data_len = len(data_to_stream)
                if data_len > 0:
                    warn_msg = f'The telemetry endpoint {msg_tag} unavailable, streaming {data_len} ports from the cached data'
                    logging.warning(warn_msg)
            # Empty data will not be streamed
            if data_len > 0 and \
                    (not new_data_timestamp or
                     (new_data_timestamp and new_data_timestamp != self.last_streamed_data_sample_timestamp)):
                if num_of_counters == 0:
                    num_of_counters = len(data_to_stream[0].keys()) # by default the keys of the first port record
                self.streaming_metrics_mgr.update_streaming_metrics(msg_tag, **{
                    self.streaming_metrics_mgr.num_of_streamed_ports_in_last_msg_key: data_len,
                    self.streaming_metrics_mgr.num_of_processed_counters_in_last_msg_key: num_of_counters
                })
                if self.bulk_streaming_flag:
                    self._stream_data_to_fluentd(data_to_stream, msg_tag)
                else:
                    for row in data_to_stream:
                        self._stream_data_to_fluentd(row, msg_tag)
                self.last_streamed_data_sample_timestamp = new_data_timestamp
            elif telemetry_data is None: # None = Failed, Empty = No new data
                logging.error("Failed to get the telemetry data metrics for %s", _url)
            elif self.stream_only_new_samples:
                logging.info('No new samples in endpoint %s, nothing to stream', msg_tag)

        except Exception as ex:  # pylint: disable=broad-except
            logging.error("Exception occurred during parsing telemetry data: %s", str(ex))

    def clear_cached_streaming_data(self):
        self.last_streamed_data_sample_timestamp = self._fluent_sender = None
        self.last_streamed_data_sample_per_endpoint.clear()
        self.streaming_metrics_mgr = MonitorStreamingMgr()
