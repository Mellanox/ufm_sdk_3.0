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
        self.streaming_job = None
        pass

    def start_streaming(self, streaming_func, streaming_interval):

        if not self.streaming_job:
            self.streaming_job = self.scheduler.add_job(streaming_func, 'interval',
                                                        seconds=streaming_interval,
                                                        next_run_time=datetime.now())
            if not self.scheduler.running:
                self.scheduler.start()

        return self.streaming_job.id

    def stop_streaming(self):
        if self.streaming_job and self.scheduler.running:
            self.scheduler.remove_job(self.streaming_job.id)
            self.streaming_job = None
            return True

    def get_streaming_state(self):
        return self.scheduler.state
