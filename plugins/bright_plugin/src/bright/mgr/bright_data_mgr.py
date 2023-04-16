#
# Copyright © 2013-2022 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
# @author: Anan Al-Aghbar
# @date:   Dec 20, 2022
#
import enum
import json
import datetime
import pytz
import os.path

from pythoncm.cluster import Cluster
from pythoncm.settings import Settings
from pythoncm import entity

from utils.logger import Logger, LOG_LEVELS
from utils.singleton import Singleton
from utils.utils import Utils
from mgr.bright_configurations_mgr import BrightConfigParser
from resources.bright_job_resource import BrightJobResource


class BCMConnectionStatus(enum.Enum):
    Disabled = enum.auto()
    Healthy = enum.auto()
    Unhealthy = enum.auto()


class BCMConnectionError(Exception):

    def __init__(self, message):
        Exception.__init__(self, message)


class BrightDataMgr(Singleton):

    SAVED_DATA_PATH = '/data/historical_bright_data.json'

    def __init__(self):
        self.conf = BrightConfigParser.getInstance()
        self.bright_cluster = None
        self.status = BCMConnectionStatus.Disabled
        self.status_err_msg = ''
        self.bright_nodes = []
        self.djson = Utils.read_json_from_file(self.SAVED_DATA_PATH) \
            if os.path.exists(self.SAVED_DATA_PATH)  \
            else {}
        self.bright_time_format = '%Y-%m-%dT%H:%M:%S'
        self.last_clean_time = None

    def connect(self):
        try:
            # For testing
            # self.last_clean_time = datetime.datetime.now() - datetime.timedelta(days=1)
            self.last_clean_time = datetime.datetime.now()
            bcm_host = self.conf.get_bright_host()
            bcm_port = self.conf.get_bright_port()
            Logger.log_message(f'Connecting to Bright Cluster Manager on: {bcm_host}:{bcm_port}', LOG_LEVELS.DEBUG)
            settings = Settings(host=bcm_host,
                                port=bcm_port,
                                cert_file=self.conf.cert_file_path,
                                key_file=self.conf.cert_key_file_path,
                                ca_file=self.conf.cacert_file_path)
            if not settings.check_certificate_files():
                msg = 'Failed to connect to Bright Cluster Manager: ' \
                      'unable to load the certificates'
                Logger.log_message(msg, LOG_LEVELS.ERROR)
                self.set_status_as_unhealthy(msg)
                raise BCMConnectionError(msg)
            else:
                self.bright_cluster = Cluster(settings)
                self.status = BCMConnectionStatus.Healthy
                self.status_err_msg = ''
                cluster_addr = self.get_bright_cluster_addr()
                if not self.djson.get(cluster_addr):
                    self.djson[cluster_addr] = {
                        "data": {},
                        "settings": {
                            "timezone": self.bright_cluster.get_base_partition().timeZoneSettings.timeZone
                        }
                    }
        except BCMConnectionError as ex:
            raise ex
        except Exception as ex:
            msg = f'Failed to connect to Bright Cluster Manager: {str(ex)}'
            self.set_status_as_unhealthy(msg)
            Logger.log_message(msg, LOG_LEVELS.ERROR)
            raise BCMConnectionError(msg)

    def disconnect(self):
        try:
            if self.bright_cluster:
                msg = f'Disconnecting from Bright Cluster Manager on: '\
                      f'{self.get_bright_cluster_addr()}'
                Logger.log_message(msg, LOG_LEVELS.DEBUG)
                self.bright_cluster.disconnect()
                self.set_status_as_unhealthy(msg)
            else:
                msg = 'Failed to disconnect from Bright Cluster Manager: ' \
                      'no available connection'
                Logger.log_message(msg, LOG_LEVELS.ERROR)
                self.status_err_msg = msg
                raise BCMConnectionError(msg)
        except BCMConnectionError as ex:
            raise ex
        except Exception as ex:
            msg = f'Failed to disconnect from Bright Cluster Manager: : {str(ex)}'
            self.status_err_msg = msg
            Logger.log_message(msg, LOG_LEVELS.ERROR)
            raise BCMConnectionError(msg)

    def get_bright_cluster_addr(self):
        return f'{self.conf.get_bright_host()}:{self.conf.get_bright_port()}'

    def get_bright_cluster_saved_settings(self):
        return self.djson.get(self.get_bright_cluster_addr(), {}).get("settings", {})

    def get_bright_cluster_timezone(self):
        return self.get_bright_cluster_saved_settings().get("timezone")

    def get_bright_cluster_saved_data(self):
        return self.djson.get(self.get_bright_cluster_addr(), {}).get("data", {})

    def get_bright_nodes(self):
        try:
            if self.bright_cluster:
                self.bright_nodes = self.bright_cluster.get_by_type(entity.Node)
                return self.bright_nodes
            else:
                msg = 'Failed to get Bright Cluster Nodes: ' \
                      'no available connection'
                Logger.log_message(msg, LOG_LEVELS.ERROR)
                raise BCMConnectionError(msg)
        except BCMConnectionError as ex:
            raise ex
        except Exception as ex:
            msg = 'Failed to get Bright Cluster Nodes: ' \
                  f'{str(ex)}'
            Logger.log_message(msg, LOG_LEVELS.ERROR)
            raise BCMConnectionError(msg)

    def get_bright_jobs(self):
        try:
            if self.bright_cluster:
                jobs = self.bright_cluster.workload.get_jobs()[1]
                return jobs
            else:
                msg = 'Failed to get Bright Cluster Jobs: ' \
                      'no available connection'
                Logger.log_message(msg, LOG_LEVELS.ERROR)
                raise BCMConnectionError(msg)
        except BCMConnectionError as ex:
            raise ex
        except Exception as ex:
            msg = 'Failed to get Bright Cluster Nodes: ' \
                  f'{str(ex)}'
            Logger.log_message(msg, LOG_LEVELS.ERROR)
            raise BCMConnectionError(msg)

    def poll_data(self):
        if self.status != BCMConnectionStatus.Healthy:
            self.connect()
        self.clean_old_data()
        if self.status == BCMConnectionStatus.Healthy:
            Logger.log_message('Polling bright data', LOG_LEVELS.DEBUG)
            try:
                nodes = self.get_bright_nodes()
                saved_data = self.get_bright_cluster_saved_data()
                for node in nodes:
                    saved_node = saved_data.get(node.hostname)
                    if not saved_node:
                        saved_data[node.hostname] = {
                            "jobs": {}
                        }
                jobs = self.get_bright_jobs()
                for job in jobs:
                    for jnode in job.nodes:
                        saved_data[jnode]["jobs"][f'{job.jobID}_{job.submittime}'] = BrightJobResource(job).__dict__
                Utils.write_text_to_file(self.SAVED_DATA_PATH, json.dumps(self.djson))
                Logger.log_message('Polling bright data request completed successfully')
            except BCMConnectionError as ex:
                self.set_status_as_unhealthy(str(ex))
        elif self.status == BCMConnectionStatus.Unhealthy:
            Logger.log_message('Not able to poll bright data, the connection is unhealthy', LOG_LEVELS.WARNING)

    def get_saved_data(self):
        return self.djson

    def clean_old_data(self):
        current_datetime = datetime.datetime.now()
        data_retention_period, data_retention_timeunit = self.conf.get_bright_data_retention_period()
        data_retention_date = None
        do_retention = False
        if data_retention_timeunit == 'd':
            data_retention_date = datetime.timedelta(days=data_retention_period)
            do_retention = round(
                (current_datetime - self.last_clean_time).total_seconds() / (3600*24)
            ) >= 1 # do retention if the current unit is day & last clean has been done before 1 day
        elif data_retention_timeunit == 'h':
            data_retention_date = datetime.timedelta(hours=data_retention_period)
            do_retention = round(
                (current_datetime - self.last_clean_time).total_seconds() / 3600
            ) >= 1 # do retention if the current unit is h & last clean has been done before 1 hour
        if do_retention:
            Logger.log_message('Clean old history data based on the data retention period', LOG_LEVELS.DEBUG)
            data_retention_date = pytz.timezone(self.get_bright_cluster_timezone()).localize(current_datetime - data_retention_date)
            saved_data = self.get_bright_cluster_saved_data()
            saved_data_list = list(saved_data.items())
            for node, node_data in saved_data_list:
                node_jobs = node_data.get('jobs')
                if node_jobs:
                    node_jobs_list = list(node_jobs.items())
                    for job_key, job in node_jobs_list:
                        job_submit_time = self.get_job_submit_time(job)
                        if job_submit_time < data_retention_date:
                            del node_jobs[job_key]
                    node_jobs_list = list(node_jobs.items())
                    if len(node_jobs_list) == 0:
                        del saved_data[node]
            self.last_clean_time = current_datetime
            Logger.log_message('Clean old history data based on the data retention period completed successfully')

    def convert_bright_time_to_datetime(self, time_str):
        btz = pytz.timezone(self.get_bright_cluster_timezone())
        dt = datetime.datetime.strptime(time_str, self.bright_time_format)
        dt = btz.localize(dt)
        return dt

    def get_job_submit_time(self, job):
        return self.convert_bright_time_to_datetime(job.get('submittime'))

    def set_status_as_unhealthy(self,err_msg=''):
        self.status = BCMConnectionStatus.Unhealthy
        self.status_err_msg = err_msg
