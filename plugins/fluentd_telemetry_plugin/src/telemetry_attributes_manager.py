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
import os

# pylint: disable=no-name-in-module,import-error
from utils.utils import Utils
from utils.logger import Logger, LOG_LEVELS

class TelemetryAttributesManager:
    """"
    UFM TelemetryAttributesManager class - to manager streaming attributes
    When we parse the telemetry data, we should update saved/cached attributes (headers) and file (/config/tfs_streaming_attributes.json)
    """

    def __init__(self):
        self.streaming_attributes_file = "/config/tfs_streaming_attributes.json"  # this path on the docker
        self.streaming_attributes = {}

    def _get_saved_streaming_attributes(self):
        attr = {}
        if os.path.exists(self.streaming_attributes_file):
            attr = Utils.read_json_from_file(self.streaming_attributes_file)
        self.streaming_attributes = attr
        return self.streaming_attributes

    def update_saved_streaming_attributes(self):
        Utils.write_json_to_file(self.streaming_attributes_file, self.streaming_attributes)

    def _add_streaming_attribute(self, attribute):
        if self.streaming_attributes.get(attribute, None) is None:
            # if the attribute is new and wasn't set before --> set default values for the new attribute
            self.streaming_attributes[attribute] = {
                'name': attribute,
                'enabled': True
            }

    def get_attr_obj(self, key):
        return self.streaming_attributes.get(key)


    def init_streaming_attributes(self, telemetry_parser, telemetry_endpoints, config_parser):  # pylint: disable=too-many-locals
        Logger.log_message('Updating The streaming attributes', LOG_LEVELS.DEBUG)
        # load the saved attributes
        self._get_saved_streaming_attributes()
        processed_endpoints = {}
        for endpoint in telemetry_endpoints:  # pylint: disable=too-many-nested-blocks
            _host = endpoint.get(config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_HOST)
            _port = endpoint.get(config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_PORT)
            _url = endpoint.get(config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_URL)
            _msg_tag = endpoint.get(config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_MSG_TAG_NAME)
            # the ID of the endpoint is the full URL without filters like the shading,etc...
            endpoint_id = f'{_host}:{_port}:{_url.split("?")[0]}'
            is_processed = processed_endpoints.get(endpoint_id)
            if not is_processed:
                telemetry_data = telemetry_parser.get_metrics(endpoint)
                if telemetry_data:

                    # CSV format
                    rows = telemetry_data.split("\n")
                    if len(rows):
                        headers = rows[0].split(",")
                        for attribute in headers:
                            self._add_streaming_attribute(attribute)

                processed_endpoints[endpoint_id] = True
        # update the streaming attributes files
        self.update_saved_streaming_attributes()
        Logger.log_message('The streaming attributes were updated successfully')
