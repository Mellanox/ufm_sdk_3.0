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


class InvalidConfRequest(Exception):

    def __init__(self, message):
        Exception.__init__(self,message)


class SetStreamingConfigurations(Resource):

    def __init__(self,conf):
        self.conf = conf

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
                    self.conf.set_item_value(section, section_item, value)

            else:
                for section_item, value in section_items.items():
                    if section_item not in dict(self.conf.get_section_items(section)).keys():
                        raise InvalidConfRequest(f'Invalid property: {section_item} in {section}')
                    self.conf.set_item_value(section, section_item, value)
        self.conf.update_config_file(self.conf.config_file)

    def post(self):
        # validate the new conf json
        self._set_new_conf()
        return make_response("set configurations has been done successfully")

    def get(self):
        conf_dict = {}
        for section in self.conf.get_conf_sections():
            conf_dict[section] = dict(self.conf.get_section_items(section))
        return make_response(conf_dict)

class StartStreamingScheduler(Resource):

    def __init__(self, conf, scheduler):
        self.config_parser = conf
        self.scheduler = scheduler
        self.streamer = self._init_telemetry_streamer()

    def _init_telemetry_streamer(self):
        ufm_telemetry_host = self.config_parser.get_telemetry_host()
        ufm_telemetry_port = self.config_parser.get_telemetry_port()
        ufm_telemetry_url = self.config_parser.get_telemetry_url()

        streaming_interval = self.config_parser.get_streaming_interval()
        bulk_streaming_flag = self.config_parser.get_bulk_streaming_flag()

        fluentd_host = self.config_parser.get_fluentd_host()
        fluentd_port = self.config_parser.get_fluentd_port()
        fluentd_timeout = self.config_parser.get_fluentd_timeout()
        fluentd_msg_tag = self.config_parser.get_fluentd_msg_tag(ufm_telemetry_host)
        aliases_meta_fields, custom_meta_fields = self.config_parser.get_meta_fields()

        return UFMTelemetryStreaming(ufm_telemetry_host=ufm_telemetry_host,
                                     ufm_telemetry_port=ufm_telemetry_port,
                                     ufm_telemetry_url=ufm_telemetry_url,
                                     streaming_interval=streaming_interval,bulk_streaming_flag=bulk_streaming_flag,
                                     aliases_meta_fields=aliases_meta_fields,custom_meta_fields=custom_meta_fields,
                                     fluentd_host=fluentd_host, fluentd_port=fluentd_port,
                                     fluentd_timeout=fluentd_timeout, fluentd_msg_tag=fluentd_msg_tag)

    def post(self):
        job_id = self.scheduler.start_streaming(self.streamer.stream_data, self.streamer.streaming_interval)
        return make_response({'job_id': job_id})


class StopStreamingScheduler(Resource):
    def __init__(self, scheduler):
        self.scheduler = scheduler

    def post(self):
        self.scheduler.stop_streaming()
        return make_response("stopped")


class GetStreamingSchedulerStatus(Resource):
    def __init__(self, scheduler):
        self.scheduler = scheduler

    def get(self):
        return make_response(str(self.scheduler.get_streaming_state()))
