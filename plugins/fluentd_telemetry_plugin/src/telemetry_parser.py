"""
@copyright:
    Copyright (C) Mellanox Technologies Ltd. 2014-2024.  ALL RIGHTS RESERVED.

    This software product is a proprietary product of Mellanox Technologies
    Ltd. (the "Company") and all right, title, and interest in and to the
    software product, including all associated intellectual property rights,
    are and shall remain exclusively with the Company.

    This software product is governed by the End User License Agreement
    provided with the software product.

@author: Miryam Schwartz
@date:   Nov 13, 2024
"""
import logging
from typing import List
import requests

# pylint: disable=no-name-in-module,import-error
from telemetry_constants import UFMTelemetryConstants
from telemetry_endpoint import TelemetryEndpoint
from ufm_sdk_tools.src.xdr_utils import PortType,prepare_port_type_http_telemetry_filter
from utils.logger import Logger, LOG_LEVELS
from utils.utils import Utils

class TelemetryParser:
    """
    UFM TelemetryParser class - to fetch and parse the telemetry data
    """

    PORT_CONSTANTS_KEYS = {
        'timestamp': 'timestamp', 'source_id': 'source_id', 'tag': 'tag',
        'node_guid': 'node_guid', 'port_guid': 'port_guid',
        'sys_image_guid': 'sys_image_guid', 'aport': 'aport',
        'port_num': 'port_num', 'node_description': 'node_description',
        'm_label': 'm_label', 'port_label': 'port_label', 'status_message': 'status_message',
        'Port_Number': 'Port_Number', 'Node_GUID': 'Node_GUID', 'Device_ID': 'Device_ID', 'device_id': 'Device_ID',
        'mvcr_sensor_name': 'mvcr_sensor_name', 'mtmp_sensor_name': 'mtmp_sensor_name',
        'switch_serial_number': 'switch_serial_number', 'switch_part_number': 'switch_part_number'
        }
    NORMAL_PORT_ID_KEYS = {'node_guid', 'Node_GUID', 'port_guid', 'port_num', 'Port_Number', 'Port'}
    AGG_PORT_ID_KEYS = {'sys_image_guid', 'aport'}
    PORT_TYPE_KEY = 'port_type'
    def __init__(self, conf_parser, monitor_streaming_mgr, _last_streamed_data_sample_per_endpoint, attr_mngr):
        self.config_parser = conf_parser
        self.streaming_metrics_mgr = monitor_streaming_mgr
        self.last_streamed_data_sample_per_endpoint = _last_streamed_data_sample_per_endpoint
        self.meta_fields = self.config_parser.get_meta_fields()
        self.attributes_mngr = attr_mngr

    @staticmethod
    def append_filters_to_telemetry_url(url: str, xdr_mode: bool, port_types: List[str]):
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

    def get_metrics(self, telemetry_endpoint: TelemetryEndpoint):
        _host = telemetry_endpoint.host
        if Utils.is_ipv6_address(_host):
            _host = f'[{_host}]'
        _port = telemetry_endpoint.port
        _url = telemetry_endpoint.url
        msg_tag = telemetry_endpoint.message_tag_name
        url = f'http://{_host}:{_port}/{_url}'

        http_client = telemetry_endpoint.http_client

        try:
            response = http_client.get_telemetry_data(
                url,
                timeout=self.config_parser.get_streaming_telemetry_request_timeout()
            )

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
        except requests.exceptions.Timeout:
            logging.exception("Timeout fetching telemetry from %s", url)
            return None
        except requests.exceptions.ConnectionError:
            logging.exception("Connection error to %s", url)
            return None
        except requests.exceptions.RequestException:
            logging.exception("Request error to %s", url)
            return None
        except Exception:  # pylint: disable=broad-exception-caught
            logging.exception("Unexpected error fetching telemetry from %s", url)
            return None

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
                is_constant_value = TelemetryParser.PORT_CONSTANTS_KEYS.get(key)
                if value:
                    # the value of this counter not empty
                    value = TelemetryParser._convert_str_to_num(value)
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
                    port_record[key] = TelemetryParser._convert_str_to_num(value)
            self.last_streamed_data_sample_per_endpoint[endpoint_key][port_key] = port_record
            if is_meta_fields_available:
                port_record = self._append_meta_fields_to_dict(port_record)
            output.append(port_record)
        return output, None

    def parse_telemetry_csv_metrics_to_json(self, data, msg_tag, is_xdr_mode, stream_only_new_samples_flag):
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
            TelemetryParser._get_port_keys_indexes_from_csv_headers(keys)
        if is_xdr_mode:
            port_key_generator = TelemetryParser._get_xdr_port_id_from_csv_row
            port_key_generator_args = (normal_port_id_keys_indexes, aggr_port_id_keys_indexes, port_type_key_index)
        else:
            port_key_generator = TelemetryParser._get_port_id_from_csv_row
            port_key_generator_args = (normal_port_id_keys_indexes,)

        parser_method = self._parse_telemetry_csv_metrics_to_json_with_delta if stream_only_new_samples_flag \
            else self._parse_telemetry_csv_metrics_to_json_without_delta

        parsed_data, new_timestamp = parser_method(modified_keys, rows,
                                                port_key_generator, port_key_generator_args,
                                                is_meta_fields_available, msg_tag)

        return parsed_data, new_timestamp, len(keys)

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
            attr_obj = self.attributes_mngr.get_attr_obj(key)
            if attr_obj and attr_obj.get('enabled', False):
                modified_keys[i] = attr_obj.get('name', key)
        return modified_keys

    @staticmethod
    def _convert_str_to_num(str_val):
        try:
            return int(str_val)
        except ValueError:
            try:
                return float(str_val)
            except ValueError:
                return str_val

    @staticmethod
    def _get_port_keys_indexes_from_csv_headers(headers: List[str]):
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

        for i, key in enumerate(headers):
            if key in TelemetryParser.NORMAL_PORT_ID_KEYS:
                normal_port_id_keys_indexes.append(i)
            if key in TelemetryParser.AGG_PORT_ID_KEYS:
                aggr_port_id_keys_indexes.append(i)
            if key == TelemetryParser.PORT_TYPE_KEY and port_type_key_index == -1:
                port_type_key_index = i
        return normal_port_id_keys_indexes, aggr_port_id_keys_indexes, port_type_key_index

    @staticmethod
    def _get_xdr_port_id_from_csv_row(port_values,
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
        return TelemetryParser._get_port_id_from_csv_row(port_values, port_id_keys_indexes)

    @staticmethod
    def _get_port_id_from_csv_row(port_values, port_indexes):
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
    