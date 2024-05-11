#
# Copyright © 2013-2024 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
# @author: Anan Al-Aghbar
# @date:   Jan 10, 2024
#
from api.base_api import BaseAPIApplication
from streamer import UFMTelemetryStreaming
from flask import Response
from prometheus_client import CONTENT_TYPE_LATEST


class StreamingMonitoringStatsAPI(BaseAPIApplication):
    """StreamingMonitoringStatsAPI API class"""

    def __init__(self):
        super(StreamingMonitoringStatsAPI, self).__init__()  # pylint: disable=super-with-arguments
        self.streamer = UFMTelemetryStreaming.getInstance()

    def _get_routes(self):
        return {
            self.get: dict(urls=["/"], methods=["GET"])
        }

    def get(self):
        return Response(
            self.streamer.streaming_metrics_mgr.get_streaming_metrics_text(),
            mimetype=CONTENT_TYPE_LATEST
        )
