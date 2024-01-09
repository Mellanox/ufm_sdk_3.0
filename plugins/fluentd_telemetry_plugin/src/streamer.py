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
import os
import sys
from datetime import time

sys.path.append(os.getcwd())
import json
import gzip
import requests
import logging
import time
import datetime
from requests.exceptions import ConnectionError
from prometheus_client.parser import text_string_to_metric_families
from utils.fluentd.fluent import asyncsender as asycsender
from utils.utils import Utils

from utils.args_parser import ArgsParser
from utils.config_parser import ConfigParser
from utils.logger import Logger, LOG_LEVELS
from utils.singleton import Singleton

class UFMTelemetryConstants:
    PLUGIN_NAME = "UFM_Telemetry_Streaming"

    args_list = [
        {
            "name": '--ufm_telemetry_host',
            "help": "Host or IP of UFM Telemetry endpoint"
        },{
            "name": '--ufm_telemetry_port',
            "help": "Port of UFM Telemetry endpoint"
        },{
            "name": '--ufm_telemetry_url',
            "help": "URL of UFM Telemetry endpoint"
        },{
            "name": '--streaming_interval',
            "help": "Interval for telemetry streaming in seconds"
        },{
            "name": '--bulk_streaming',
            "help": "Bulk streaming flag, i.e. if True all telemetry rows will be streamed in one message; "
                    "otherwise, each row will be streamed in a separated message"
        },{
            "name": '--compressed_streaming',
            "help": "Compressed streaming flag, i.e. if True the streamed data will be sent gzipped json; "
                    "otherwise, will be sent plain text as json"
        },{
            "name": '--enable_streaming',
            "help": "If true, the streaming will be started once the required configurations have been set"
        },{
            "name": '--stream_only_new_samples',
            "help": "If True, the data will be streamed only in case new samples were pulled from the telemetry"
        },{
            "name": '--fluentd_host',
            "help": "Host name or IP of fluentd endpoint"
        },{
            "name": '--fluentd_port',
            "help": "Port of fluentd endpoint"
        },{
            "name": '--fluentd_timeout',
            "help": "Fluentd timeout in seconds"
        },{
            "name": '--fluentd_message_tag_name',
            "help": "Tag name of fluentd endpoint message"
        }
    ]


class UFMTelemetryStreamingConfigParser(ConfigParser):
    # for debugging
    #config_file = "../conf/fluentd_telemetry_plugin.cfg"

    config_file = "/config/fluentd_telemetry_plugin.cfg" # this path on the docker

    UFM_TELEMETRY_ENDPOINT_SECTION = "ufm-telemetry-endpoint"
    UFM_TELEMETRY_ENDPOINT_SECTION_HOST = "host"
    UFM_TELEMETRY_ENDPOINT_SECTION_PORT = "port"
    UFM_TELEMETRY_ENDPOINT_SECTION_URL = "url"
    UFM_TELEMETRY_ENDPOINT_SECTION_INTERVAL = "interval"
    UFM_TELEMETRY_ENDPOINT_SECTION_MSG_TAG_NAME = "message_tag_name"

    FLUENTD_ENDPOINT_SECTION = "fluentd-endpoint"
    FLUENTD_ENDPOINT_SECTION_HOST = "host"
    FLUENTD_ENDPOINT_SECTION_PORT = "port"
    FLUENTD_ENDPOINT_SECTION_TIMEOUT = "timeout"

    STREAMING_SECTION = "streaming"
    STREAMING_SECTION_COMPRESSED_STREAMING = "compressed_streaming"
    STREAMING_SECTION_BULK_STREAMING = "bulk_streaming"
    STREAMING_SECTION_STREAM_ONLY_NEW_SAMPLES = "stream_only_new_samples"
    STREAMING_SECTION_ENABLED = "enabled"

    META_FIELDS_SECTION = "meta-fields"

    def __init__(self, args):
        super().__init__(args, False)
        self.sdk_config.read(self.config_file)

    def get_telemetry_host(self):
        return self.get_config_value(self.args.ufm_telemetry_host,
                                     self.UFM_TELEMETRY_ENDPOINT_SECTION,
                                     self.UFM_TELEMETRY_ENDPOINT_SECTION_HOST)

    def get_telemetry_port(self):
        return self.get_config_value(self.args.ufm_telemetry_port,
                                     self.UFM_TELEMETRY_ENDPOINT_SECTION,
                                     self.UFM_TELEMETRY_ENDPOINT_SECTION_PORT,
                                     '9001')

    def get_telemetry_url(self):
        return self.get_config_value(self.args.ufm_telemetry_url,
                                     self.UFM_TELEMETRY_ENDPOINT_SECTION,
                                     self.UFM_TELEMETRY_ENDPOINT_SECTION_URL,
                                     "csv/metrics")

    def get_streaming_interval(self):
        return self.get_config_value(self.args.streaming_interval,
                                     self.UFM_TELEMETRY_ENDPOINT_SECTION,
                                     self.UFM_TELEMETRY_ENDPOINT_SECTION_INTERVAL,
                                     '10')

    def get_bulk_streaming_flag(self):
        return self.safe_get_bool(self.args.bulk_streaming,
                                  self.STREAMING_SECTION,
                                  self.STREAMING_SECTION_BULK_STREAMING,
                                  True)

    def get_compressed_streaming_flag(self):
        return self.safe_get_bool(self.args.compressed_streaming,
                                  self.STREAMING_SECTION,
                                  self.STREAMING_SECTION_COMPRESSED_STREAMING,
                                  True)

    def get_stream_only_new_samples_flag(self):
        return self.safe_get_bool(self.args.bulk_streaming,
                                  self.STREAMING_SECTION,
                                  self.STREAMING_SECTION_STREAM_ONLY_NEW_SAMPLES,
                                  True)

    def get_enable_streaming_flag(self):
        return self.safe_get_bool(self.args.enable_streaming,
                                  self.STREAMING_SECTION,
                                  self.STREAMING_SECTION_ENABLED,
                                  False)

    def get_fluentd_host(self):
        return self.get_config_value(self.args.fluentd_host,
                                     self.FLUENTD_ENDPOINT_SECTION,
                                     self.FLUENTD_ENDPOINT_SECTION_HOST)

    def get_fluentd_port(self):
        return self.safe_get_int(self.args.fluentd_port,
                                 self.FLUENTD_ENDPOINT_SECTION,
                                 self.FLUENTD_ENDPOINT_SECTION_PORT)

    def get_fluentd_timeout(self):
        return self.safe_get_int(self.args.fluentd_port,
                                 self.FLUENTD_ENDPOINT_SECTION,
                                 self.FLUENTD_ENDPOINT_SECTION_TIMEOUT,
                                 120)

    def get_fluentd_msg_tag(self, default=''):
        return self.get_config_value(self.args.fluentd_host,
                                     self.UFM_TELEMETRY_ENDPOINT_SECTION,
                                     self.UFM_TELEMETRY_ENDPOINT_SECTION_MSG_TAG_NAME,
                                     default)

    def get_meta_fields(self):
        meta_fields_list = self.get_section_items(self.META_FIELDS_SECTION)
        aliases = []
        custom = []
        for meta_field,value in meta_fields_list:
            meta_fields_parts = meta_field.split("_")
            meta_field_type = meta_fields_parts[0]
            meta_field_key = "_".join(meta_fields_parts[1:])
            if meta_field_type == "alias":
                aliases.append({
                    "key": meta_field_key,
                    "value": value
                })
            elif meta_field_type == "add":
                custom.append({
                    "key": meta_field_key,
                    "value": value
                })
            else:
                logging.warning("The meta field type : {} is not from the supported types list [alias, add]".format(meta_field_type))
        return aliases,custom


class UFMTelemetryStreaming(Singleton):

    def __init__(self, config_parser):

        self.config_parser = config_parser

        self.last_streamed_data_sample_timestamp = None
        self.port_id_keys = ['node_guid', 'Node_GUID', 'port_guid', 'port_num', 'Port_Number', 'Port']
        self.port_constants_keys = {
            'timestamp': 'timestamp', 'source_id': 'source_id', 'tag': 'tag', 'node_guid': 'node_guid', 'port_guid': 'port_guid',
            'port_num': 'port_num', 'node_description': 'node_description','m_label': 'm_label', 'port_label': 'port_label', 'status_message': 'status_message',
            'Port_Number': 'Port_Number', 'Node_GUID': 'Node_GUID', 'Device_ID': 'Device_ID', 'device_id': 'Device_ID',
            'mvcr_sensor_name': 'mvcr_sensor_name', 'mtmp_sensor_name': 'mtmp_sensor_name',
            'switch_serial_number': 'switch_serial_number', 'switch_part_number': 'switch_part_number'
        }
        self.last_streamed_data_sample_per_port = {}

        self.TIMESTAMP_CSV_FIELD_KEY = 'timestamp'

        self.streaming_attributes_file = "/config/tfs_streaming_attributes.json"  # this path on the docker
        self.streaming_attributes = {}
        self.init_streaming_attributes()

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
    def streaming_interval(self):
        return self.config_parser.get_streaming_interval()

    @property
    def ufm_telemetry_endpoints(self):
        splitter = ","
        hosts = self.ufm_telemetry_host.split(splitter)
        ports = self.ufm_telemetry_port.split(splitter)
        urls = self.ufm_telemetry_url.split(splitter)
        intervals = self.streaming_interval.split(splitter)
        msg_tags = self.fluentd_msg_tag.split(splitter)
        endpoints = []
        for i in range(len(hosts)):
            endpoints.append({
                self.config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_HOST: hosts[i],
                self.config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_PORT: ports[i],
                self.config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_URL: urls[i],
                self.config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_INTERVAL: intervals[i],
                self.config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_MSG_TAG_NAME: msg_tags[i] if msg_tags[i] else f'{hosts[i]}:{ports[i]}/{urls[i]}',
            })
        return endpoints

    @property
    def bulk_streaming_flag(self):
        return self.config_parser.get_bulk_streaming_flag()

    @property
    def compressed_streaming_flag(self):
        return self.config_parser.get_compressed_streaming_flag()

    @property
    def stream_only_new_samples(self):
        return self.config_parser.get_stream_only_new_samples_flag()

    @property
    def meta_fields(self):
        # aliases_meta_fields, self.custom_meta_fields
        return self.config_parser.get_meta_fields()

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
    def fluentd_msg_tag(self):
        return self.config_parser.get_fluentd_msg_tag()

    def _get_metrics(self, _host, _port, _url):
        _host = f'[{_host}]' if Utils.is_ipv6_address(_host) else _host
        url = f'http://{_host}:{_port}/{_url}'
        logging.info(f'Send UFM Telemetry Endpoint Request, Method: GET, URL: {url}')
        try:
            response = requests.get(url)
            response.raise_for_status()
            logging.info(f'UFM Telemetry Endpoint Response Received Successfully, '
                         f'Response Time: {response.elapsed.total_seconds()} seconds')
            expected_content_size = int(response.headers.get('Content-Length'))
            actual_content_size = len(response.content)
            if expected_content_size > actual_content_size:
                logging.warning(f'The Received UFM Telemetry Endpoint Response Size: {actual_content_size} Bytes'
                                f' Less Than The Expected Size: {expected_content_size} Bytes')
            else:
                logging.info(f'The Received UFM Telemetry Endpoint Response Size: {actual_content_size} Bytes')
            return response.text
        except Exception as e:
            logging.error(e)
            return None

    def _append_meta_fields_to_dict(self, dic):
        keys = dic.keys()
        aliases_meta_fields, custom_meta_fields = self.meta_fields
        for alias in aliases_meta_fields:
            alias_key = alias["key"]
            alias_value = alias["value"]
            value = dic.get(alias_key, None)
            if value is None:
                logging.warning(
                    "The alias : {} does not exist in the telemetry response keys: {}".format(alias_key, str(keys)))
                continue
            dic[alias_value] = value
        for custom_field in custom_meta_fields:
            dic[custom_field["key"]] = custom_field["value"]
        return dic

    def _get_saved_streaming_attributes(self):
        if os.path.exists(self.streaming_attributes_file):
            return Utils.read_json_from_file(self.streaming_attributes_file)
        return {}

    def update_saved_streaming_attributes(self, attributes):
        Utils.write_json_to_file(self.streaming_attributes_file, attributes)

    def _parse_telemetry_csv_metrics_to_json(self, data, line_separator="\n", attrs_separator=","):
        rows = data.split(line_separator)
        keys = rows[0].split(attrs_separator)
        keys_length = len(keys)
        output = []
        sample_timestamp = rows[1].split(attrs_separator)[keys.index(self.TIMESTAMP_CSV_FIELD_KEY)]
        port_id_keys_indices = None
        if self.stream_only_new_samples:
            port_id_keys_indices = []
            for pIDKey in self.port_id_keys:
                port_id_keys_indices += [i for i, x in enumerate(keys) if x == pIDKey]

        for row in rows[1:]:
            if len(row) > 0:
                values = row.split(attrs_separator)
                port_key = current_port_values = None
                if self.stream_only_new_samples:
                    port_key = ":".join([values[index] for index in port_id_keys_indices])
                    current_port_values = self.last_streamed_data_sample_per_port.get(port_key, {})
                dic = {}
                #######
                is_data_changed = False
                for i in range(keys_length):
                    value = self._convert_str_to_num(values[i])
                    key = keys[i]
                    is_constant_value = self.port_constants_keys.get(key)
                    attr_obj = self.streaming_attributes.get(key, None)
                    if attr_obj and attr_obj.get('enabled', False) and len(str(value)):
                        # if the attribute/counter is enabled and
                        # also the value of this counter not empty
                        if is_constant_value is None and \
                                self.stream_only_new_samples and value != current_port_values.get(key):
                            # and the value was changed -> stream it
                            dic[attr_obj.get("name", key)] = value
                            current_port_values[key] = value
                            is_data_changed = True
                        elif not self.stream_only_new_samples or is_constant_value:
                            dic[attr_obj.get("name", key)] = value
                            is_data_changed = not self.stream_only_new_samples
                ########
                if self.stream_only_new_samples:
                    self.last_streamed_data_sample_per_port[port_key] = current_port_values
                if is_data_changed:
                    dic = self._append_meta_fields_to_dict(dic)
                    output.append(dic)
        return output, sample_timestamp

    def _parse_telemetry_prometheus_metrics_to_json(self, data):
        elements_dict = {}
        timestamp = current_port_values = None
        for family in text_string_to_metric_families(data):
            if len(family.samples):
                timestamp = family.samples[0].timestamp
            for sample in family.samples:
                id = port_key = ":".join([sample.labels.get(key, '') for key in self.port_id_keys])
                id += f':{str(sample.timestamp)}'
                current_row = elements_dict.get(id, {})
                if self.stream_only_new_samples:
                    current_port_values = self.last_streamed_data_sample_per_port.get(port_key, {})

                # main sample's counter value
                attr_obj = self.streaming_attributes.get(sample.name, None)
                key = attr_obj.get("name", sample.name)
                is_value_changed = False
                if attr_obj and attr_obj.get('enabled', False):
                    if self.stream_only_new_samples and sample.value != current_port_values.get(key):
                        current_row[key] = sample.value
                        current_port_values[key] = sample.value
                        is_value_changed = True
                    elif not self.stream_only_new_samples:
                        current_row[key] = sample.value
                        is_value_changed = True

                if is_value_changed:
                    # if you add custom attributes here, you should add them to init_streaming_attributes function
                    # current custom attributes timestamp, source_id
                    attr_obj = self.streaming_attributes.get('timestamp', None)
                    if attr_obj and attr_obj.get('enabled', False):
                        current_row[attr_obj.get("name", 'timestamp')] = int(sample.timestamp * 1000)  # to be unified with the csv value
                    for key, value in sample.labels.items():
                        # rename source -> source_id in order to be unified with the csv format key
                        key = key if key != 'source' else 'source_id'
                        attr_obj = self.streaming_attributes.get(key, None)
                        if attr_obj and attr_obj.get('enabled', False) and len(value):
                            current_row[attr_obj.get("name", key)] = value
                    current_row = self._append_meta_fields_to_dict(current_row)
                    elements_dict[id] = current_row
                ####
                if self.stream_only_new_samples:
                    self.last_streamed_data_sample_per_port[port_key] = current_port_values

        return list(elements_dict.values()), timestamp

    def _stream_data_to_fluentd(self, data_to_stream, fluentd_msg_tag=''):
        logging.info(f'Streaming to Fluentd IP: {self.fluentd_host} port: {self.fluentd_port} timeout: {self.fluentd_timeout}')
        st = time.time()
        try:
            fluentd_message = {
                "timestamp": datetime.datetime.fromtimestamp(int(time.time())).strftime('%Y-%m-%d %H:%M:%S'),
                "type": "full",
                "values": data_to_stream
            }

            if self.compressed_streaming_flag:
                compressed = gzip.compress(json.dumps(fluentd_message).encode('utf-8'))
                res = requests.post(
                    url=f'http://{self.fluentd_host}:{self.fluentd_port}/'
                        f'{UFMTelemetryConstants.PLUGIN_NAME}.{fluentd_msg_tag}',
                    data=compressed,
                    headers={"Content-Encoding": "gzip", "Content-Type": "application/json"})
                res.raise_for_status()
            else:
                fluent_sender = asycsender.FluentSender(UFMTelemetryConstants.PLUGIN_NAME,
                                                    self.fluentd_host,
                                                    self.fluentd_port, timeout=self.fluentd_timeout)
                fluent_sender.emit(fluentd_msg_tag, fluentd_message)
                fluent_sender.close()
            et = time.time()
            logging.info(f'Finished Streaming to Fluentd Host: {self.fluentd_host} port: {self.fluentd_port}')
            logging.info(f'Total Streaming Time: {et-st} Seconds')
        except ConnectionError as e:
            logging.error(f'Failed to connect to stream destination due to the error :{str(e)}')
        except Exception as e:
            logging.error(f'Failed to stream the data due to the error: {str(e)}')

    def _check_data_prometheus_format(self, telemetry_data):
        return telemetry_data and telemetry_data.startswith('#')

    def stream_data(self, telemetry_endpoint):
        _host = telemetry_endpoint.get(self.config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_HOST)
        _port = telemetry_endpoint.get(self.config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_PORT)
        _url = telemetry_endpoint.get(self.config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_URL)
        telemetry_data = self._get_metrics(_host, _port, _url)
        if telemetry_data:
            try:
                msg_tag = telemetry_endpoint.get(self.config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_MSG_TAG_NAME)
                ufm_telemetry_is_prometheus_format = self._check_data_prometheus_format(telemetry_data)
                logging.info('Start Processing The Received UFM Telemetry Endpoint Response')
                st = time.time()
                data_to_stream, new_data_timestamp = self._parse_telemetry_prometheus_metrics_to_json(telemetry_data) \
                    if ufm_telemetry_is_prometheus_format else \
                    self._parse_telemetry_csv_metrics_to_json(telemetry_data)
                et = time.time()
                data_len = len(data_to_stream)
                logging.info(f'Total Processing Time of The Received UFM Telemetry Endpoint Response: {(et - st)} Seconds,'
                             f'({data_len}) Ports Were Handled')
                if data_len > 0 and \
                        (not self.stream_only_new_samples or
                         (self.stream_only_new_samples and new_data_timestamp != self.last_streamed_data_sample_timestamp)):
                    if self.bulk_streaming_flag:
                        self._stream_data_to_fluentd(data_to_stream, msg_tag)
                    else:
                        for row in data_to_stream:
                            self._stream_data_to_fluentd(row, msg_tag)
                    self.last_streamed_data_sample_timestamp = new_data_timestamp
                elif self.stream_only_new_samples:
                    logging.info("No new samples, nothing to stream")

            except Exception as e:
                logging.error("Exception occurred during parsing telemetry data: "+ str(e))
        else:
            logging.error("Failed to get the telemetry data metrics")

    def _add_streaming_attribute(self, attribute):
        if self.streaming_attributes.get(attribute, None) is None:
            # if the attribute is new and wasn't set before --> set default values for the new attribute
            self.streaming_attributes[attribute] = {
                'name': attribute,
                'enabled': True
            }

    def init_streaming_attributes(self):
        Logger.log_message('Updating The streaming attributes', LOG_LEVELS.DEBUG)
        # load the saved attributes
        self.streaming_attributes = self._get_saved_streaming_attributes()
        telemetry_endpoints = self.ufm_telemetry_endpoints
        for endpoint in telemetry_endpoints:
            _host = endpoint.get(self.config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_HOST)
            _port = endpoint.get(self.config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_PORT)
            _url = endpoint.get(self.config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_URL)
            telemetry_data = self._get_metrics(_host, _port, _url)
            if telemetry_data:
                ufm_telemetry_is_prometheus_format = self._check_data_prometheus_format(telemetry_data)
                if not ufm_telemetry_is_prometheus_format:
                    # CSV format
                    rows = telemetry_data.split("\n")
                    if len(rows):
                        headers = rows[0].split(",")
                        for attribute in headers:
                            self._add_streaming_attribute(attribute)
                else:
                    # prometheus format
                    for family in text_string_to_metric_families(telemetry_data):
                        # add the counter attribute
                        self._add_streaming_attribute(family.name)
                        for sample in family.samples:
                            # add the labels/metadata attributes
                            for attribute in list(sample.labels.keys()):
                                attribute = attribute if attribute != 'source' else 'source_id'
                                self._add_streaming_attribute(attribute)
                    # custom attribute won't be found in the prometheus format, should be added manually
                    self._add_streaming_attribute('timestamp')
        # update the streaming attributes files
        self.update_saved_streaming_attributes(self.streaming_attributes)
        Logger.log_message('The streaming attributes were updated successfully')

    def clear_cached_streaming_data(self):
        self.last_streamed_data_sample_timestamp = None
        self.last_streamed_data_sample_per_port = {}

    def _convert_str_to_num(self, str_val):
        try:
            return int(str_val)
        except ValueError:
            try:
                return float(str_val)
            except ValueError:
                return str_val

if __name__ == "__main__":
    # init app args
    args = ArgsParser.parse_args("UFM Telemetry Streaming to fluentd", UFMTelemetryConstants.args_list)

    # init app config parser & load config files
    config_parser = UFMTelemetryStreamingConfigParser(args)

    # init logs configs
    logs_file_name = config_parser.get_logs_file_name()
    logs_level = config_parser.get_logs_level()
    max_log_file_size = config_parser.get_log_file_max_size()
    log_file_backup_count = config_parser.get_log_file_backup_count()
    Logger.init_logs_config(logs_file_name, logs_level, max_log_file_size, log_file_backup_count)

    telemetry_streaming = UFMTelemetryStreaming(config_parser)

    #streaming_scheduler = StreamingScheduler.getInstance()
    #streaming_scheduler.start_streaming(telemetry_streaming.stream_data, telemetry_streaming.streaming_interval)

    telemetry_streaming.stream_data()
