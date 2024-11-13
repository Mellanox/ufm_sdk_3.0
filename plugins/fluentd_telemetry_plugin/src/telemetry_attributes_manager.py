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
from utils.utils import Utils

class TelemetryAttributesManager:
    """"
    UFM TelemetryAttributesManager class - to manager streaming attributes
    When we parse the telemetry data, we should update saved/cached attributes (headers) and file (/config/tfs_streaming_attributes.json)
    """

    def __init__(self):
        self.streaming_attributes_file = "/config/tfs_streaming_attributes.json"  # this path on the docker
        self.streaming_attributes = {}

    def get_saved_streaming_attributes(self):
        attr = {}
        if os.path.exists(self.streaming_attributes_file):
            attr = Utils.read_json_from_file(self.streaming_attributes_file)
        self.streaming_attributes = attr
        return self.streaming_attributes

    def update_saved_streaming_attributes(self):
        Utils.write_json_to_file(self.streaming_attributes_file, self.streaming_attributes)

    def add_streaming_attribute(self, attribute):
        if self.streaming_attributes.get(attribute, None) is None:
            # if the attribute is new and wasn't set before --> set default values for the new attribute
            self.streaming_attributes[attribute] = {
                'name': attribute,
                'enabled': True
            }

    def get_attr_obj(self, key):
        return self.streaming_attributes.get(key)
