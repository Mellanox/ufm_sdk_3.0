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
import time
import json
import gzip
import logging
import datetime
import requests
from requests.exceptions import ConnectionError  # pylint: disable=redefined-builtin
from prometheus_client.parser import text_string_to_metric_families
from fluentbit_writer import init_fb_writer
from monitor_streaming_mgr import MonitorStreamingMgr

# pylint: disable=no-name-in-module,import-error
from utils.utils import Utils
from utils.args_parser import ArgsParser
from utils.config_parser import ConfigParser
from utils.logger import Logger, LOG_LEVELS
from utils.singleton import Singleton


class UFMTelemetryConstants:
    """UFMTelemetryConstants Class"""

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
            "name": '--c_fluent_streamer',
            "help": "C Fluent Streamer flag, i.e. if True the C fluent streamer will be used; "
                    "otherwise, the native python streamer will be used"
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

    CSV_LINE_SEPARATOR = "\n"
    CSV_ROW_ATTRS_SEPARATOR = ","


class UFMTelemetryStreamingConfigParser(ConfigParser):
    """
    UFMTelemetryStreamingConfigParser class to manage
    the TFS configurations
    """

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
    STREAMING_SECTION_C_FLUENT__STREAMER = "c_fluent_streamer"
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

    def get_c_fluent_streamer_flag(self):
        return self.safe_get_bool(self.args.c_fluent_streamer,
                                  self.STREAMING_SECTION,
                                  self.STREAMING_SECTION_C_FLUENT__STREAMER,
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
                logging.warning("The meta field type : %s is not from the supported types list [alias, add]",
                                meta_field_type)
        return aliases, custom


class UFMTelemetryStreaming(Singleton):
    """
    UFMTelemetryStreaming class
    to manage/control the streaming
    """

    def __init__(self, conf_parser):

        self.config_parser = conf_parser

        self.last_streamed_data_sample_timestamp = None
        self.port_id_keys = ['node_guid', 'Node_GUID', 'port_guid', 'port_num', 'Port_Number', 'Port']
        self.port_constants_keys = {
            'timestamp': 'timestamp', 'source_id': 'source_id', 'tag': 'tag',
            'node_guid': 'node_guid', 'port_guid': 'port_guid',
            'port_num': 'port_num', 'node_description': 'node_description',
            'm_label': 'm_label', 'port_label': 'port_label', 'status_message': 'status_message',
            'Port_Number': 'Port_Number', 'Node_GUID': 'Node_GUID', 'Device_ID': 'Device_ID', 'device_id': 'Device_ID',
            'mvcr_sensor_name': 'mvcr_sensor_name', 'mtmp_sensor_name': 'mtmp_sensor_name',
            'switch_serial_number': 'switch_serial_number', 'switch_part_number': 'switch_part_number'
        }
        self.last_streamed_data_sample_per_port = {}

        self.streaming_metrics_mgr = MonitorStreamingMgr()

        self.streaming_attributes_file = "/config/tfs_streaming_attributes.json"  # this path on the docker
        self.streaming_attributes = {}
        self.init_streaming_attributes()

        self._fluent_sender = None
        self.meta_fields = self.config_parser.get_meta_fields()

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
        for i, value in enumerate(hosts):
            endpoints.append({
                self.config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_HOST: value,
                self.config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_PORT: ports[i],
                self.config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_URL: urls[i],
                self.config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_INTERVAL: intervals[i],
                self.config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_MSG_TAG_NAME:
                    msg_tags[i] if msg_tags[i] else f'{value}:{ports[i]}/{urls[i]}'
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

    def _get_metrics(self, _host, _port, _url, msg_tag):
        _host = f'[{_host}]' if Utils.is_ipv6_address(_host) else _host
        url = f'http://{_host}:{_port}/{_url}'
        logging.info('Send UFM Telemetry Endpoint Request, Method: GET, URL: %s', url)
        try:
            response = requests.get(url)  # pylint: disable=missing-timeout
            response.raise_for_status()
            actual_content_size = len(response.content)
            expected_content_size = int(response.headers.get('Content-Length', actual_content_size))
            if expected_content_size > actual_content_size:
                log_msg = (f'Telemetry Response Received Partially from {msg_tag}, The Expected Size is {expected_content_size} Bytes'
                           f' While The Received Size is {actual_content_size} Bytes')
                log_level = LOG_LEVELS.WARNING
            else:
                log_msg = (f'Telemetry Response Received Successfully from {msg_tag},'
                           f'The Received Size is {actual_content_size} Bytes')
                log_level = LOG_LEVELS.INFO
            log_msg += f', Response Time: {response.elapsed.total_seconds()} seconds'
            Logger.log_message(log_msg, log_level)
            self.streaming_metrics_mgr.update_streaming_metrics(msg_tag, **{
                self.streaming_metrics_mgr.telemetry_response_time_seconds_key: response.elapsed.total_seconds(),
                self.streaming_metrics_mgr.telemetry_expected_response_size_bytes_key: expected_content_size,
                self.streaming_metrics_mgr.telemetry_received_response_size_bytes_key: actual_content_size
            })
            return response.text
        except Exception as ex:  # pylint: disable=broad-except
            logging.error(ex)
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
                    "The alias : %s does not exist in the telemetry response keys: %s", alias_key, str(keys))
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

    def _get_filtered_counters(self, counters):
        """
        :desc:
        filters the counters list in order based on the saved streaming_attributes
        it checks if the counter is enabled or disabled to skip it
        and also takes the configured name in case the counter was renamed by the user

        :param: counters: list of counters strings
        :return: {1: 'counter1', 2:'counter2', etc...} , where the key is the index and the value is the saved counter name
        """
        keys_length = len(counters)
        modified_keys = {}
        for i in range(keys_length):
            key = counters[i]
            attr_obj = self.streaming_attributes.get(key)
            if attr_obj and attr_obj.get('enabled', False):
                modified_keys[i] = attr_obj.get('name', key)
        return modified_keys

    def _parse_telemetry_csv_metrics_to_json_with_delta(self, data):  # pylint: disable=too-many-locals
        """
        :desc: parsed the data csv input & convert it to list of ports records
        each record contains key[s]:value[s] for the port's counters
        process operations:
        1. extract the port's ID keys indices from the CSV headers.
        2. filter the headers/counters to include only the enabled counters using _get_filtered_counters method
        3. parse the data CSV, iterate over all rows and construct the port's counters based on the filtered headers/counters
        4. when constructing the port's record, will try to convert the values to int/float if possible
        5. After the first iteration, only the changed counters will be considered and added to the output list (delta only)
        6. if there's a configured/saved meta fields (aliases or constants), they will be appended to the port's record

        :param: data: csv string metrics
        :return: [
        {port_guid: port1, counterA:value, counterB:value...},
        {port_guid: port2, counterA:value, counterB:value}...
        ]
        """
        rows = data.split(UFMTelemetryConstants.CSV_LINE_SEPARATOR)
        keys = rows[0].split(UFMTelemetryConstants.CSV_ROW_ATTRS_SEPARATOR)
        keys_length = len(keys)
        is_meta_fields_available = len(self.meta_fields[0]) or len(self.meta_fields[1])
        output = []

        port_id_keys_indices = []
        for port_id_key in self.port_id_keys:
            port_id_keys_indices += [i for i, x in enumerate(keys) if x == port_id_key]

        modified_keys = self._get_filtered_counters(keys)
        available_keys_indices = modified_keys.keys()

        for row in rows[1:-1]:
            # skip the first row since it contains the headers
            # skip the last row since its empty row
            values = row.split(UFMTelemetryConstants.CSV_ROW_ATTRS_SEPARATOR)

            # prepare the port_key that will be used as an ID in delta
            port_key = ":".join([values[index] for index in port_id_keys_indices])
            # get the last cached port's values
            current_port_values = self.last_streamed_data_sample_per_port.get(port_key, {})
            #######
            is_data_changed = False
            dic = {}
            for i in available_keys_indices:
                value = values[i]
                key = modified_keys[i]
                is_constant_value = self.port_constants_keys.get(key)
                if value:
                    # the value of this counter not empty
                    value = self._convert_str_to_num(value)
                    if is_constant_value is None and value != current_port_values.get(key):
                        # the value was changed -> stream it
                        dic[key] = value
                        current_port_values[key] = value
                        is_data_changed = True
                    elif is_constant_value:
                        dic[key] = value
            ########
            self.last_streamed_data_sample_per_port[port_key] = current_port_values
            if is_data_changed:
                if is_meta_fields_available:
                    dic = self._append_meta_fields_to_dict(dic)
                output.append(dic)
        return output, None, keys_length

    def _parse_telemetry_csv_metrics_to_json_without_delta(self, data):
        """
        :desc: parsed the data csv input & convert it to list of ports records
        each record contains key[s]:value[s] for the port's counters
        process operations:
        1. extract the port's ID keys indices from the CSV headers.
        2. filter the headers/counters to include only the enabled counters using _get_filtered_counters method
        3. parse the data CSV, iterate over all rows and construct the port's counters based on the filtered headers/counters
        4. when constructing the port's record, will try to convert the values to int/float if possible
        5. if there's a configured/saved meta fields (aliases or constants), they will be appended to the port's record

        :param: data: csv string metrics
        :return: [
        {port_guid: port1, counterA:value, counterB:value...},
        {port_guid: port2, counterA:value, counterB:value}...
        ]
        """
        rows = data.split(UFMTelemetryConstants.CSV_LINE_SEPARATOR)
        keys = rows[0].split(UFMTelemetryConstants.CSV_ROW_ATTRS_SEPARATOR)
        keys_length = len(keys)
        output = []

        is_meta_fields_available = len(self.meta_fields[0]) or len(self.meta_fields[1])
        modified_keys = self._get_filtered_counters(keys)
        available_keys_indices = modified_keys.keys()

        for row in rows[1:-1]:
            values = row.split(UFMTelemetryConstants.CSV_ROW_ATTRS_SEPARATOR)
            port_record = {}
            for i in available_keys_indices:
                value = values[i]
                key = modified_keys[i]
                if value:
                    port_record[key] = self._convert_str_to_num(value)
                    if is_meta_fields_available:
                        port_record = self._append_meta_fields_to_dict(port_record)
            output.append(port_record)
        return output, None, keys_length

    def _parse_telemetry_csv_metrics_to_json(self, data):
        if self.stream_only_new_samples:
            return self._parse_telemetry_csv_metrics_to_json_with_delta(data)
        return self._parse_telemetry_csv_metrics_to_json_without_delta(data)

    def _parse_telemetry_prometheus_metrics_to_json(self, data):  # pylint: disable=too-many-locals,too-many-branches
        elements_dict = {}
        timestamp = current_port_values = None
        num_of_counters = 0
        for family in text_string_to_metric_families(data):
            if len(family.samples):
                timestamp = family.samples[0].timestamp
            for sample in family.samples:
                uid = port_key = ":".join([sample.labels.get(key, '') for key in self.port_id_keys])
                uid += f':{str(sample.timestamp)}'
                current_row = elements_dict.get(uid, {})
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
                    current_num_of_counters = len(current_row)
                    num_of_counters = max(num_of_counters, current_num_of_counters)
                    current_row = self._append_meta_fields_to_dict(current_row)
                    elements_dict[uid] = current_row
                ####
                if self.stream_only_new_samples:
                    self.last_streamed_data_sample_per_port[port_key] = current_port_values

        return list(elements_dict.values()), timestamp, num_of_counters

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

                # pylint: disable=missing-timeout
                res = requests.post(
                    url=f'http://{_fluentd_host}:{self.fluentd_port}/'
                        f'{UFMTelemetryConstants.PLUGIN_NAME}.{fluentd_msg_tag}',
                    data=compressed,
                    headers={"Content-Encoding": "gzip", "Content-Type": "application/json"})
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
        except ConnectionError as ex:
            logging.error('Failed to connect to stream destination due to the error : %s', str(ex))
        except Exception as ex:  # pylint: disable=broad-except
            logging.error('Failed to stream the data due to the error: %s', str(ex))

    def _check_data_prometheus_format(self, telemetry_data):
        return telemetry_data and telemetry_data.startswith('#')

    def stream_data(self, telemetry_endpoint):  # pylint: disable=too-many-locals
        _host = telemetry_endpoint.get(self.config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_HOST)
        _port = telemetry_endpoint.get(self.config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_PORT)
        _url = telemetry_endpoint.get(self.config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_URL)
        msg_tag = telemetry_endpoint.get(self.config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_MSG_TAG_NAME)
        telemetry_data = self._get_metrics(_host, _port, _url, msg_tag)
        if telemetry_data:
            try:
                ufm_telemetry_is_prometheus_format = self._check_data_prometheus_format(telemetry_data)
                logging.info('Start Processing The Received Response From %s', msg_tag)
                start_time = time.time()
                data_to_stream, new_data_timestamp, num_of_counters = self._parse_telemetry_prometheus_metrics_to_json(telemetry_data) \
                    if ufm_telemetry_is_prometheus_format else \
                    self._parse_telemetry_csv_metrics_to_json(telemetry_data)
                end_time = time.time()
                data_len = len(data_to_stream)
                resp_process_time = round(end_time - start_time, 6)
                self.streaming_metrics_mgr.update_streaming_metrics(msg_tag, **{
                    self.streaming_metrics_mgr.telemetry_response_process_time_seconds_key: resp_process_time
                })
                if data_len > 0 and \
                        (not new_data_timestamp or
                         (new_data_timestamp and new_data_timestamp != self.last_streamed_data_sample_timestamp)):
                    self.streaming_metrics_mgr.update_streaming_metrics(msg_tag, **{
                        self.streaming_metrics_mgr.num_of_streamed_ports_in_last_msg_key: data_len,
                        self.streaming_metrics_mgr.num_of_processed_counters_in_last_msg_key: num_of_counters
                    })
                    logging.info('Processing of endpoint %s Completed In: %.2f Seconds. '
                                 '(%d) Ports, (%d) Counters Were Handled',
                                 msg_tag, resp_process_time, data_len, num_of_counters)
                    if self.bulk_streaming_flag:
                        self._stream_data_to_fluentd(data_to_stream, msg_tag)
                    else:
                        for row in data_to_stream:
                            self._stream_data_to_fluentd(row, msg_tag)
                    self.last_streamed_data_sample_timestamp = new_data_timestamp
                elif self.stream_only_new_samples:
                    logging.info('No new samples in endpoint %s, nothing to stream', msg_tag)

            except Exception as ex:  # pylint: disable=broad-except
                logging.error("Exception occurred during parsing telemetry data: %s", str(ex))
        else:
            logging.error("Failed to get the telemetry data metrics")

    def _add_streaming_attribute(self, attribute):
        if self.streaming_attributes.get(attribute, None) is None:
            # if the attribute is new and wasn't set before --> set default values for the new attribute
            self.streaming_attributes[attribute] = {
                'name': attribute,
                'enabled': True
            }

    def init_streaming_attributes(self):  # pylint: disable=too-many-locals
        Logger.log_message('Updating The streaming attributes', LOG_LEVELS.DEBUG)
        # load the saved attributes
        self.streaming_attributes = self._get_saved_streaming_attributes()
        telemetry_endpoints = self.ufm_telemetry_endpoints
        processed_endpoints = {}
        for endpoint in telemetry_endpoints:  # pylint: disable=too-many-nested-blocks
            _host = endpoint.get(self.config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_HOST)
            _port = endpoint.get(self.config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_PORT)
            _url = endpoint.get(self.config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_URL)
            _msg_tag = endpoint.get(self.config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_MSG_TAG_NAME)
            # the ID of the endpoint is the full URL without filters like the shading,etc...
            endpoint_id = f'{_host}:{_port}:{_url.split("?")[0]}'
            is_processed = processed_endpoints.get(endpoint_id)
            if not is_processed:
                telemetry_data = self._get_metrics(_host, _port, _url, _msg_tag)
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
                processed_endpoints[endpoint_id] = True
        # update the streaming attributes files
        self.update_saved_streaming_attributes(self.streaming_attributes)
        Logger.log_message('The streaming attributes were updated successfully')

    def clear_cached_streaming_data(self):
        self.last_streamed_data_sample_timestamp = self._fluent_sender = None
        self.last_streamed_data_sample_per_port = {}
        self.streaming_metrics_mgr = MonitorStreamingMgr()

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
    _args = ArgsParser.parse_args("UFM Telemetry Streaming to fluentd", UFMTelemetryConstants.args_list)

    # init app config parser & load config files
    config_parser = UFMTelemetryStreamingConfigParser(_args)

    # init logs configs
    logs_file_name = config_parser.get_logs_file_name()
    logs_level = config_parser.get_logs_level()
    max_log_file_size = config_parser.get_log_file_max_size()
    log_file_backup_count = config_parser.get_log_file_backup_count()
    Logger.init_logs_config(logs_file_name, logs_level, max_log_file_size, log_file_backup_count)

    telemetry_streaming = UFMTelemetryStreaming(config_parser)

    # streaming_scheduler = StreamingScheduler.getInstance()
    # streaming_scheduler.start_streaming(telemetry_streaming.stream_data, telemetry_streaming.streaming_interval)

    # telemetry_streaming.stream_data()
