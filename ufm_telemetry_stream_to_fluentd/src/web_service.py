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

from flask import Flask
from flask_restful import Api
from http import HTTPStatus
from twisted.web.wsgi import WSGIResource
from twisted.internet import reactor
from twisted.web import server
from utils.json_schema_validator import SchemaValidationError
from ufm_telemetry_stream_to_fluentd.src.web_service_error_messages import \
    no_running_streaming_instance,\
    streaming_already_running

from ufm_telemetry_stream_to_fluentd.src.streaming_scheduler import \
    StreamingScheduler,\
    NoRunningStreamingInstance,\
    StreamingAlreadyRunning

from ufm_telemetry_stream_to_fluentd.src.web_service_resources import \
    SetStreamingConfigurations, \
    InvalidConfRequest


class UFMTelemetryFluentdStreamingServer:

    def __init__(self,config_parser):
        self.config_parser = config_parser
        self.streaming_scheduler = StreamingScheduler.getInstance()

        self.port_number = 8981
        self.app = Flask(__name__)
        self.api = Api(self.app)

        self.api.add_resource(SetStreamingConfigurations, f'/conf',
                              resource_class_kwargs={'conf': config_parser,'scheduler': self.streaming_scheduler})

        self._addErrorHandlers()

    def _getErrorHandlers(self):
        return [
            (NoRunningStreamingInstance,
             lambda e: (no_running_streaming_instance, HTTPStatus.BAD_REQUEST)),
            (StreamingAlreadyRunning,
             lambda e: (streaming_already_running, HTTPStatus.BAD_REQUEST)),
            (InvalidConfRequest,
             lambda e: (str(e), HTTPStatus.BAD_REQUEST)),
            (SchemaValidationError,
             lambda e: (str(e), HTTPStatus.BAD_REQUEST)),
            (ValueError,
             lambda e: (str(e), HTTPStatus.BAD_REQUEST)),
        ]

    def _addErrorHandlers(self):
        hdlrs = self._getErrorHandlers()
        for code_or_exception, f in hdlrs:
            self.app.register_error_handler(code_or_exception, f)


    def run(self):
        # for debugging
        #self.app.run(port=self.port_number, debug=True)
        resource = WSGIResource(reactor, reactor.getThreadPool(), self.app)
        reactor.listenTCP(self.port_number, server.Site(resource,logPath=None))
        reactor.run()