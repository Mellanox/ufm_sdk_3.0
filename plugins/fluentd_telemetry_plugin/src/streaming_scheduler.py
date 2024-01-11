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

from streamer import UFMTelemetryStreaming
from utils.singleton import Singleton
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import STATE_RUNNING

from datetime import datetime


class StreamingAlreadyRunning(Exception):
    pass


class NoRunningStreamingInstance(Exception):
    pass


class StreamingScheduler(Singleton):
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.streaming_jobs = None
        pass

    def start_streaming(self, update_attributes=False):
        streamer = UFMTelemetryStreaming.getInstance()
        streamer.clear_cached_streaming_data()
        if update_attributes:
            streamer.init_streaming_attributes()
        if not self.streaming_jobs:
            self.streaming_jobs = []
            for telemetry_endpoint in streamer.ufm_telemetry_endpoints:
                interval = int(telemetry_endpoint[streamer.config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_INTERVAL])
                streaming_job = self.scheduler.add_job(streamer.stream_data, 'interval',
                                                       name=telemetry_endpoint[streamer.config_parser.UFM_TELEMETRY_ENDPOINT_SECTION_MSG_TAG_NAME],
                                                       args=[telemetry_endpoint],
                                                       seconds=interval,
                                                       next_run_time=datetime.now())
                self.streaming_jobs.append(streaming_job)
            if not self.scheduler.running:
                self.scheduler.start()

        return self.streaming_jobs

    def stop_streaming(self):
        if self.streaming_jobs and self.scheduler.running:
            for job in self.streaming_jobs:
                self.scheduler.remove_job(job.id)
            self.streaming_jobs = None
            return True

    def get_streaming_state(self):
        return self.scheduler.state
