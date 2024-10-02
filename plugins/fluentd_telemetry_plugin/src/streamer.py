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
from typing import List

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
from ufm_sdk_tools.src.xdr_utils import PortType,prepare_port_type_http_telemetry_filter


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
            "name": '--ufm_telemetry_xdr_mode',
            "help": "Telemetry XDR mode flag, "
                    "i.e., if True, the enabled ports types in `xdr_ports_types` "
                    "will be collected from the telemetry and streamed to fluentd"
        },{
            "name": '--ufm_telemetry_xdr_ports_types',
            "help": "Telemetry XDR ports types, "
                    "i.e., List of XDR ports types that should be collected and streamed, "
                    "separated by `;`. For example legacy;aggregated;plane"
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
    UFM_TELEMETRY_ENDPOINT_SECTION_XDR_MODE = "xdr_mode"
    UFM_TELEMETRY_ENDPOINT_SECTION_XDR_PORTS_TYPE = "xdr_ports_types"
    UFM_TELEMETRY_ENDPOINT_SECTION_XDR_PORTS_TYPE_SPLITTER = ";"

    FLUENTD_ENDPOINT_SECTION = "fluentd-endpoint"
    FLUENTD_ENDPOINT_SECTION_HOST = "host"
    FLUENTD_ENDPOINT_SECTION_PORT = "port"
    FLUENTD_ENDPOINT_SECTION_TIMEOUT = "timeout"

    STREAMING_SECTION = "streaming"
    STREAMING_SECTION_COMPRESSED_STREAMING = "compressed_streaming"
    STREAMING_SECTION_C_FLUENT__STREAMER = "c_fluent_streamer"
    STREAMING_SECTION_BULK_STREAMING = "bulk_streaming"
    STREAMING_SECTION_STREAM_ONLY_NEW_SAMPLES = "stream_only_new_samples"
    STREAMING_SECTION_ENABLE_CACHED_STREAM_ON_TELEMETRY_FAIL = "enable_cached_stream_on_telemetry_fail"
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

    def get_ufm_telemetry_xdr_mode_flag(self):
        return self.get_config_value(self.args.ufm_telemetry_xdr_mode,
                                     self.UFM_TELEMETRY_ENDPOINT_SECTION,
                                     self.UFM_TELEMETRY_ENDPOINT_SECTION_XDR_MODE,
                                     "False")

    def get_ufm_telemetry_xdr_ports_types(self):
        return self.get_config_value(self.args.ufm_telemetry_xdr_ports_types,
                                     self.UFM_TELEMETRY_ENDPOINT_SECTION,
                                     self.UFM_TELEMETRY_ENDPOINT_SECTION_XDR_PORTS_TYPE,
                                     "legacy;aggregated;plane")

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

    def get_enable_cached_stream_on_telemetry_fail(self):
        return self.safe_get_bool(None,
                                  self.STREAMING_SECTION,
                                  self.STREAMING_SECTION_ENABLE_CACHED_STREAM_ON_TELEMETRY_FAIL,
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


#pylint: disable=too-many-instance-attributes
class UFMTelemetryStreaming(Singleton):
    """
    UFMTelemetryStreaming class
    to manage/control the streaming
    """

    def __init__(self, conf_parser):

        self.config_parser = conf_parser

        self.last_streamed_data_sample_timestamp = None
        self.normal_port_id_keys = ['node_guid', 'Node_GUID', 'port_guid', 'port_num', 'Port_Number', 'Port']
        self.agg_port_id_keys = ['sys_image_guid', 'aport']
        self.port_type_key = 'port_type'
        self.port_constants_keys = {
            'timestamp': 'timestamp', 'source_id': 'source_id', 'tag': 'tag',
            'node_guid': 'node_guid', 'port_guid': 'port_guid',
            'sys_image_guid': 'sys_image_guid', 'aport': 'aport',
            'port_num': 'port_num', 'node_description': 'node_description',
            'm_label': 'm_label', 'port_label': 'port_label', 'status_message': 'status_message',
            'Port_Number': 'Port_Number', 'Node_GUID': 'Node_GUID', 'Device_ID': 'Device_ID', 'device_id': 'Device_ID',
            'mvcr_sensor_name': 'mvcr_sensor_name', 'mtmp_sensor_name': 'mtmp_sensor_name',
            'switch_serial_number': 'switch_serial_number', 'switch_part_number': 'switch_part_number'
        }
        self.last_streamed_data_sample_per_endpoint = {}

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
    def ufm_telemetry_xdr_mode_flag(self):
        return self.config_parser.get_ufm_telemetry_xdr_mode_flag()

    @property
    def ufm_telemetry_xdr_ports_types(self):
        return self.config_parser.get_ufm_telemetry_xdr_ports_types()

    @property
    def streaming_interval(self):
        return self.config_parser.get_streaming_interval()

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
        endpoints = []
        for i, value in enumerate(hosts):
            _is_xdr_mode = Utils.convert_str_to_type(xdr_mode[i], 'boolean')
            _url = self._append_filters_to_telemetry_url(
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
                    msg_tags[i] if msg_tags[i] else f'{value}:{ports[i]}/{_url}'
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

    def _append_filters_to_telemetry_url(self, url: str, xdr_mode: bool, port_types: List[str]):
        """
        This function constructs and appends filter parameters to the given URL if certain conditions are met.

        Parameters:
            url (str): The base telemetry URL to which filters may be appended.
            xdr_mode (bool): A flag indicating whether extended data record (XDR) mode is enabled.
            port_types (List[str]): list of port type names used to generate filters.

        Returns:
            str: The telemetry URL with appended filter parameters if applicable, or the original URL.
        """
        filters = []
        if xdr_mode:
            filters.append(prepare_port_type_http_telemetry_filter(port_types))
        if filters:
            filters_sign = '&' if '?' in url else '?'
            return f'{url}{filters_sign}{"&".join(filters)}'
        return url

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

    def _get_port_keys_indexes_from_csv_headers(self, headers: List[str]):
        """
        Extracts the indexes of specific port keys from CSV headers.

        This method identifies and returns the indexes of normal (legacy, plane in case of XDR) port ID keys,
        aggregated port ID keys (in case of XDR),
        and the port type key from the provided list of CSV headers.

        Parameters:
        - headers (list of str): A list of strings representing the CSV header row.

        Returns:
        - tuple: A tuple containing three elements:
            - normal_port_id_keys_indexes (list of int): Indices of normal port ID keys found in the headers.
            - aggr_port_id_keys_indexes (list of int): Indices of aggregated port ID keys found in the headers.
            - port_type_key_index (int): Index of the port type key in the headers, or -1 if not found.
        """

        normal_port_id_keys_indexes = []
        aggr_port_id_keys_indexes = []
        port_type_key_index = -1

        normal_port_id_keys_set = set(self.normal_port_id_keys)
        agg_port_id_keys_set = set(self.agg_port_id_keys)

        for i, key in enumerate(headers):
            if key in normal_port_id_keys_set:
                normal_port_id_keys_indexes.append(i)
            if key in agg_port_id_keys_set:
                aggr_port_id_keys_indexes.append(i)
            if key == self.port_type_key and port_type_key_index == -1:
                port_type_key_index = i
        return normal_port_id_keys_indexes, aggr_port_id_keys_indexes, port_type_key_index

    def _get_port_id_from_csv_row(self, port_values, port_indexes):
        """
        Constructs a port ID from a CSV row using specified indexes.

        This method generates a port ID by concatenating values from a list of
        port values at the specified indices. The values are joined together
        using a colon (":") as the separator.

        Parameters:
        - port_values (list of str): A list of strings representing the values from a CSV row.
        - port_indexes (list of int): A list of indexes indicating which values to use for constructing the port ID.

        Returns:
        - str: A string representing the constructed port ID.
        """
        return ":".join([port_values[index] for index in port_indexes])

    def _get_xdr_port_id_from_csv_row(self, port_values,
                                      normal_port_id_keys_indexes,
                                      aggr_port_id_keys_indexes,
                                      port_type_key_index):
        """
        Determines and constructs the XDR port ID from a CSV row.

        This method selects the appropriate set of port ID key indexes based on
        the port type and constructs the XDR port ID by using these indexes to
        extract values from the provided CSV row.

        Parameters:
        - port_values (list of str): A list of strings representing the values from a CSV row.
        - normal_port_id_keys_indexes (list of int): Indexes for normal port ID keys.
        - aggr_port_id_keys_indexes (list of int): Indexes for aggregated port ID keys.
        - port_type_key_index (int): Index of the port type key in the row, or -1 if not present.

        Returns:
        - str: A string representing the constructed XDR port ID.
        """
        port_id_keys_indexes = normal_port_id_keys_indexes
        if port_type_key_index != -1:
            port_type = port_values[port_type_key_index]
            if port_type == PortType.AGGREGATED.value:
                port_id_keys_indexes = aggr_port_id_keys_indexes
        return self._get_port_id_from_csv_row(port_values, port_id_keys_indexes)

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

    def _parse_telemetry_csv_metrics_to_json_with_delta(self, available_headers, rows,
                                                        port_key_generator, port_key_generator_args,
                                                        is_meta_fields_available, endpoint_key):  # pylint: disable=too-many-locals,too-many-branches
        """
        Parses CSV telemetry data into JSON format with delta updates.

        This method processes CSV rows to generate a list of port records. Each record contains
        key-value pairs representing the port's counters.
        Only counters that have changed since the last update are included in the output.

        Parameters:

        - available_headers (dict): Maps available CSV headers to their indices. This is a subset
          of all CSV headers, filtered based on specific criteria.

        - rows (list of str): The CSV data rows as strings. The first row (headers) and the last
          row (empty) are ignored.

        - port_key_generator (function): Function to generate unique keys for each port. These keys
          are crucial for identifying and caching each port's data uniquely across iterations.

        - port_key_generator_args (tuple): Arguments required by the `port_key_generator` function.

        - is_meta_fields_available (bool): If `True`, meta fields (such as aliases or constants)
          are appended to each record.

        - endpoint_key (str): Identifies the endpoint for caching purposes.

        Returns:

        - tuple:
            - A list of dictionaries, where each dictionary represents a port's record with updated
              counter values.
            - `None`: Reserved for future use.

        Example Output:

        [
            {'port_guid': 'port1', 'counterA': value, 'counterB': value, ...},
            {'port_guid': 'port2', 'counterA': value, 'counterB': value, ...},
            ...
        ]

        Process Overview:

        1. Iterate over CSV rows, skipping the header and empty rows.
        2. Use the `port_key_generator` to create a unique key for each port from the row data.
        This key is essential for tracking changes and caching previous data states.
        3. Construct a port record using values from the CSV row and available headers.
        4. Convert values to integers or floats where possible.
        5. Store each port's record in a map per endpoint using the generated port key.
        6. After initial processing, only include counters that have changed in subsequent outputs.
        7. Append configured meta fields to records if applicable.
        """
        output = []

        available_keys_indices = available_headers.keys()

        for row in rows[1:-1]:
            # skip the first row since it contains the headers
            # skip the last row since its empty row
            values = row.split(UFMTelemetryConstants.CSV_ROW_ATTRS_SEPARATOR)
            port_key = port_key_generator(values, *port_key_generator_args)
            # get the last cached port's values
            current_port_values = self.last_streamed_data_sample_per_endpoint.get(endpoint_key,{}).get(port_key, {})
            #######
            is_data_changed = False
            dic = {}
            for i in available_keys_indices:
                value = values[i]
                key = available_headers[i]
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
            self.last_streamed_data_sample_per_endpoint[endpoint_key][port_key] = current_port_values
            if is_data_changed:
                if is_meta_fields_available:
                    dic = self._append_meta_fields_to_dict(dic)
                output.append(dic)
        return output, None

    def _parse_telemetry_csv_metrics_to_json_without_delta(self, available_headers, rows,
                                                           port_key_generator, port_key_generator_args,
                                                           is_meta_fields_available, endpoint_key):
        """
        Parses CSV telemetry data into JSON format with delta updates.

        This method processes CSV rows to generate a list of port records. Each record contains
        key-value pairs representing the port's counters.

        Parameters:

        - available_headers (dict): Maps available CSV headers to their indices. This is a subset
          of all CSV headers, filtered based on specific criteria.

        - rows (list of str): The CSV data rows as strings. The first row (headers) and the last
          row (empty) are ignored.

        - port_key_generator (function): Function to generate unique keys for each port. These keys
          are crucial for identifying and caching each port's data uniquely across iterations.

        - port_key_generator_args (tuple): Arguments required by the `port_key_generator` function.

        - is_meta_fields_available (bool): If `True`, meta fields (such as aliases or constants)
          are appended to each record.

        - endpoint_key (str): Identifies the endpoint for caching purposes.


        Example Output:

        [
            {'port_guid': 'port1', 'counterA': value, 'counterB': value, ...},
            {'port_guid': 'port2', 'counterA': value, 'counterB': value, ...},
            ...
        ]

        Process Overview:

        1. Iterate over CSV rows, skipping the header and empty rows.
        2. Use the `port_key_generator` to create a unique key for each port from the row data.
        This key is essential for tracking changes and caching previous data states.
        3. Construct a port record using values from the CSV row and available headers.
        4. Convert values to integers or floats where possible.
        5. Store each port's record in a map per endpoint using the generated port key.
        6. Append configured meta fields to records if applicable.
        """
        output = []

        available_keys_indices = available_headers.keys()

        for row in rows[1:-1]:
            values = row.split(UFMTelemetryConstants.CSV_ROW_ATTRS_SEPARATOR)
            port_key = port_key_generator(values, *port_key_generator_args)
            port_record = {}
            for i in available_keys_indices:
                value = values[i]
                key = available_headers[i]
                if value:
                    port_record[key] = self._convert_str_to_num(value)
            self.last_streamed_data_sample_per_endpoint[endpoint_key][port_key] = port_record
            if is_meta_fields_available:
                port_record = self._append_meta_fields_to_dict(port_record)
            output.append(port_record)
        return output, None

    def _parse_telemetry_csv_metrics_to_json(self, data, msg_tag, is_xdr_mode):
        """
        Parses telemetry CSV metrics into JSON format.

        This method processes CSV data to convert it into JSON, selecting the
        appropriate parsing strategy based on whether only new samples should be
        streamed. It handles both normal and XDR modes for generating port IDs.

        Parameters:
        - data (str): The CSV data to be parsed.
        - msg_tag (str): A message tag used for identifying the data sample.
        - is_xdr_mode (bool): A flag indicating whether to use XDR mode for port ID generation.

        Returns:
        - tuple: A tuple containing the parsed JSON data and the number of keys (counters).
        """
        rows: List[str] = data.split(UFMTelemetryConstants.CSV_LINE_SEPARATOR)
        keys: List[str] = rows[0].split(UFMTelemetryConstants.CSV_ROW_ATTRS_SEPARATOR)
        modified_keys = self._get_filtered_counters(keys)
        is_meta_fields_available = len(self.meta_fields[0]) or len(self.meta_fields[1])
        normal_port_id_keys_indexes ,aggr_port_id_keys_indexes, port_type_key_index = \
            self._get_port_keys_indexes_from_csv_headers(keys)
        if is_xdr_mode:
            port_key_generator = self._get_xdr_port_id_from_csv_row
            port_key_generator_args = (normal_port_id_keys_indexes, aggr_port_id_keys_indexes, port_type_key_index)
        else:
            port_key_generator = self._get_port_id_from_csv_row
            port_key_generator_args = (normal_port_id_keys_indexes,)

        parser_method = self._parse_telemetry_csv_metrics_to_json_with_delta if self.stream_only_new_samples \
            else self._parse_telemetry_csv_metrics_to_json_without_delta

        parsed_data, new_timestamp = parser_method(modified_keys, rows,
                                                   port_key_generator, port_key_generator_args,
                                                   is_meta_fields_available, msg_tag)

        return parsed_data, new_timestamp, len(keys)

    def _parse_telemetry_prometheus_metrics_to_json(self, data, endpoint_key):  # pylint: disable=too-many-locals,too-many-branches
        elements_dict = {}
        timestamp = current_port_values = None
        num_of_counters = 0
        for family in text_string_to_metric_families(data):
            if len(family.samples):
                timestamp = family.samples[0].timestamp
            for sample in family.samples:
                uid = port_key = ":".join([sample.labels.get(key, '') for key in self.normal_port_id_keys])
                uid += f':{str(sample.timestamp)}'
                current_row = elements_dict.get(uid, {})
                if self.stream_only_new_samples:
                    current_port_values = self.last_streamed_data_sample_per_endpoint.get(endpoint_key,{}).get(port_key, {})

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
                    self.last_streamed_data_sample_per_endpoint[endpoint_key][port_key] = current_port_values

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
        is_xdr_mode = telemetry_endpoint.get(self.config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_XDR_MODE)
        telemetry_data = self._get_metrics(_host, _port, _url, msg_tag)
        try:
            data_to_stream = []
            new_data_timestamp = None
            num_of_counters = data_len = 0
            if telemetry_data:
                if self.last_streamed_data_sample_per_endpoint.get(msg_tag, None) is None:
                    self.last_streamed_data_sample_per_endpoint[msg_tag] = {}
                ufm_telemetry_is_prometheus_format = self._check_data_prometheus_format(telemetry_data)
                logging.info('Start Processing The Received Response From %s', msg_tag)
                start_time = time.time()
                data_to_stream, new_data_timestamp, num_of_counters = \
                    self._parse_telemetry_prometheus_metrics_to_json(telemetry_data, msg_tag) \
                    if ufm_telemetry_is_prometheus_format else \
                    self._parse_telemetry_csv_metrics_to_json(telemetry_data, msg_tag, is_xdr_mode)
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
            elif not telemetry_data:
                logging.error("Failed to get the telemetry data metrics for %s", _url)
            elif self.stream_only_new_samples:
                logging.info('No new samples in endpoint %s, nothing to stream', msg_tag)

        except Exception as ex:  # pylint: disable=broad-except
            logging.error("Exception occurred during parsing telemetry data: %s", str(ex))

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
        self.last_streamed_data_sample_per_endpoint = {}
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
