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
#
import asyncio
import datetime
import threading
from typing import Dict
from apscheduler.job import Job
from apscheduler.schedulers.background import BackgroundScheduler


from constants import DataType
from data.collectors.base_collector import BaseCollector,\
    TelemetryHttpCollector
from data.manager import DataManager


class CollectorMgr:
    """Class that manages data collection"""

    DATA_TYPE_TO_COLLECTOR = {
        DataType.TELEMETRY: TelemetryHttpCollector
    }

    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self.scheduler = BackgroundScheduler()
        self.collectors: Dict[DataType, BaseCollector] = self._init_collectors()
        self.jobs: Dict[DataType, Job] = {}
        thread = threading.Thread(target=self.scheduler_jobs)
        thread.start()

    def _init_collectors(self) -> Dict[DataType, BaseCollector]:
        """Method that init the collectors objects"""
        self.collectors = {}
        for data_type, collector_cls in self.DATA_TYPE_TO_COLLECTOR.items():
            model = self.data_manager.get_model_by_data_type(data_type)
            self.collectors[data_type] = collector_cls(model=model)
        return self.collectors

    def scheduler_jobs(self):
        jobs = {}
        for collector_type, collector in self.collectors.items():
            if collector.is_enabled:
                job = self.scheduler.add_job(self.do_collection, args=(collector,),
                                             name=collector_type.name,
                                             trigger='interval', seconds=collector.interval,
                                             next_run_time=datetime.datetime.now())
                jobs[collector_type] = job
        if not self.scheduler.running:
            self.scheduler.start()
        self.jobs = jobs

    def stop_job(self, data_type: DataType):
        job = self.jobs.get(data_type)
        if job and self.scheduler.running:
            self.scheduler.remove_job(job.id)

    def do_collection(self, collector: BaseCollector):
        """Method that performs data collection"""
        asyncio.run(collector.collect())
