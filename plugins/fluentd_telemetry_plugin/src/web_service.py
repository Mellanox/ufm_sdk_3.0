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


from werkzeug.middleware.dispatcher import DispatcherMiddleware

from api.conf_api import StreamingConfigurationsAPI
from api.streaming_monitoring_stats_api import StreamingMonitoringStatsAPI
from api.base_api import BaseAPIApplication


class UFMTelemetryFluentdStreamingAPI(DispatcherMiddleware):

    def __init__(self,config_parser):

        frontend = BaseAPIApplication()
        self.streaming_conf = StreamingConfigurationsAPI(config_parser)
        self.streaming_stats = StreamingMonitoringStatsAPI()
        super(UFMTelemetryFluentdStreamingAPI, self).__init__(
            frontend.application, {
                "/conf": self.streaming_conf.application,
                "/metrics": self.streaming_stats.application
            }
        )
