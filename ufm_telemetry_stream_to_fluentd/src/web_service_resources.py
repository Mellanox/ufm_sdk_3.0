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
@date:   Jan 25, 2022
"""

from flask import make_response, request
from flask_restful import Resource

from ufm_telemetry_stream_to_fluentd.src.streamer import UFMTelemetryStreaming
from utils.json_schema_validator import validate_schema

import re

class InvalidConfRequest(Exception):

    def __init__(self, message):
        Exception.__init__(self,message)


class SetStreamingConfigurations(Resource):

    def __init__(self,conf, scheduler):
        self.conf = conf
        self.scheduler = scheduler

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
        validate_schema("ufm_telemetry_stream_to_fluentd/src/schemas/set_conf.schema.json",request.json)
        self._set_new_conf()
        try:
            if self.conf.get_enable_streaming_flag():
                streamer = UFMTelemetryStreaming(config_parser=self.conf)
                self.scheduler.start_streaming(streamer.stream_data,
                                               streamer.streaming_interval)
            else:
                self.scheduler.stop_streaming()

            self.conf.update_config_file(self.conf.config_file)
            return make_response("set configurations has been done successfully")
        except ValueError as ex:
            self.conf.set_item_value(self.conf.STREAMING_SECTION, self.conf.STREAMING_SECTION_ENABLED, False)
            self.conf.update_config_file(self.conf.config_file)
            raise ex

    def get(self):
        conf_dict = {}
        for section in self.conf.get_conf_sections():
            conf_dict[section] = dict(self.conf.get_section_items(section))
        return make_response(conf_dict)
