"""
@copyright:
    Copyright (C) 2013-2022 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.

    This software product is a proprietary product of Nvidia Corporation and its affiliates
    (the "Company") and all right, title, and interest in and to the software
    product, including all associated intellectual property rights, are and
    shall remain exclusively with the Company.

    This software product is governed by the End User License Agreement
    provided with the software product.

@author: Nasr Ajaj
@date:   Sep 11, 2022
"""

import re
import json
import logging
from flask import make_response, request
from api import InvalidConfRequest
from utils.base_api import BaseAPIApplication
from utils.json_schema_validator import validate_schema
from utils.utils import Utils


class BrightConfigurationsAPI(BaseAPIApplication):

    def __init__(self, conf):
        super(BrightConfigurationsAPI, self).__init__()
        self.conf = conf
        self.conf_schema_path = "bright_plugin/src/schemas/set_conf.schema.json"

    def _get_routes(self):
        return {
            self.get: dict(urls=["/"], methods=["GET"]),
            self.post: dict(urls=["/"], methods=["POST"])
        }

    def _set_new_conf(self):
        new_conf = request.json
        sections = self.conf.get_conf_sections()
        for section,section_items in new_conf.items():
            if section not in sections:
                raise InvalidConfRequest(f'Invalid section: {section}')
            if section == self.conf.META_FIELDS_SECTION:
                #special logic for the meta-fields section because it contains dynamic options
                #current options meta-fields should be overwritten with the new options
                self.conf.clear_section_items(section)
                for section_item, value in section_items.items():
                    if not re.match(r'(alias_|add_).*$', section_item):
                        raise InvalidConfRequest(f'Invalid property: {section_item} in {section}; '
                                                 f'the meta-field key should be with format '
                                                 f'"alias_[[key]]" for aliases or "add_[[key]]" for constants pairs')
                    self.conf.set_item_value(section, section_item, value)

            else:
                for section_item, value in section_items.items():
                    if section_item not in dict(self.conf.get_section_items(section)).keys():
                        raise InvalidConfRequest(f'Invalid property: {section_item} in {section}')
                    self.conf.set_item_value(section, section_item, value)

    def post(self):
        # validate the new conf json
        validate_schema(self.conf_schema_path, request.json)
        self._set_new_conf()
        self.conf.update_config_file(self.conf.config_file)
        return make_response("set configurations has been done successfully")

    def get(self):
        try:
            with open(Utils.get_absolute_path(self.conf_schema_path)) as json_data:
                schema = json.load(json_data)
                properties = schema.get('properties', None)
                if properties is None:
                    raise Exception("Failed to get the configurations schema properties")
                conf_dict = {}
                for section in self.conf.get_conf_sections():
                    section_properties = properties.get(section, None)
                    if section_properties is None:
                        raise Exception("Failed to get the configurations schema for the section: " + section)
                    section_properties = section_properties.get('properties', None)
                    section_items = self.conf.get_section_items(section)
                    if section_properties:
                        conf_dict[section] = {}
                        for item in section_items:
                            item_type = section_properties.get(item[0], None)
                            item_value = item[1]
                            if item_type is None:
                                raise Exception(f"Failed to get the configurations schema for the item {item[0]} "
                                                f"under the section: {section}")
                            item_type = item_type.get('type', None)
                            if isinstance(item_value, str):
                                if item_type == "integer":
                                    item_value = int(item_value)
                                elif item_type == "boolean":
                                    item_value = item_value.lower() == 'true'
                            conf_dict[section][item[0]] = item_value
                    else:
                        conf_dict[section] = dict(section_items)
                return make_response(conf_dict)
        except Exception as e:
            logging.error("Error occurred while getting the current streaming configurations: " + str(e))