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

from flask import Flask, request, make_response
from flask_restful import Api
from ufm_telemetry_stream_to_fluentd.src.streaming_scheduler import StreamingScheduler

from ufm_telemetry_stream_to_fluentd.src.web_service_resources import \
    SetStreamingConfigurations, \
    StartStreamingScheduler,StopStreamingScheduler,\
    GetStreamingSchedulerStatus

from utils.args_parser import ArgsParser
from utils.logger import Logger, LOG_LEVELS

class UFMTelemetryFluentdStreamingServer:

    def __init__(self,config_parser):
        self.config_parser = config_parser
        self.streaming_scheduler = StreamingScheduler()

        self.port_number = 8981
        self.app = Flask(__name__)
        self.api = Api(self.app)

        self.api.add_resource(SetStreamingConfigurations, f'/conf',
                              resource_class_kwargs={'conf': config_parser})
        self.api.add_resource(StartStreamingScheduler, f'/start',
                              resource_class_kwargs={'conf': config_parser,'scheduler': self.streaming_scheduler})
        self.api.add_resource(StopStreamingScheduler, f'/stop',
                              resource_class_kwargs={'scheduler': self.streaming_scheduler})
        self.api.add_resource(GetStreamingSchedulerStatus, f'/status',
                              resource_class_kwargs={'scheduler': self.streaming_scheduler})

    def run(self):
        self.app.run(port=self.port_number, debug=True)
