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
        self.bright_nodes = []
        self.djson = {}

    def connect(self):
        try:
            bcm_host = self.conf.get_bright_host()
            bcm_port = self.conf.get_bright_port()
            Logger.log_message(f'Connecting to Bright Cluster Manager on: {bcm_host}:{bcm_port}', LOG_LEVELS.DEBUG)
            settings = Settings(host=bcm_host,
                                port=bcm_port,
                                cert_file=self.conf.cert_file_path,
                                key_file=self.conf.cert_key_file_path,
                                ca_file=self.conf.cacert_file_path)
            if not settings.check_certificate_files():
                self.status = BCMConnectionStatus.Unhealthy
                msg = 'Failed to connect to Bright Cluster Manager: ' \
                      'unable to load the certificates'
                Logger.log_message(msg, LOG_LEVELS.ERROR)
                raise BCMConnectionError(msg)
            else:
                self.bright_cluster = Cluster(settings)
                self.status = BCMConnectionStatus.Healthy
        except BCMConnectionError as ex:
            raise ex
        except Exception as ex:
            self.status = BCMConnectionStatus.Unhealthy
            msg = f'Failed to connect to Bright Cluster Manager: {str(ex)}'
            Logger.log_message(msg, LOG_LEVELS.ERROR)
            raise BCMConnectionError(msg)

    def disconnect(self):
        try:
            if self.bright_cluster:
                Logger.log_message(f'Disconnecting from Bright Cluster Manager on: '
                                   f'{self.bright_cluster.settings.host}:{self.bright_cluster.settings.port}', LOG_LEVELS.DEBUG)
                self.bright_cluster.disconnect()
                self.status = BCMConnectionStatus.Unhealthy
            else:
                msg = 'Failed to disconnect from Bright Cluster Manager: ' \
                      'no available connection'
                Logger.log_message(msg, LOG_LEVELS.ERROR)
                raise BCMConnectionError(msg)
        except BCMConnectionError as ex:
            raise ex
        except Exception as ex:
            msg = f'Failed to disconnect from Bright Cluster Manager: : {str(ex)}'
            Logger.log_message(msg, LOG_LEVELS.ERROR)
            raise BCMConnectionError(msg)

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
        Logger.log_message('Polling bright data', LOG_LEVELS.DEBUG)
        if self.status == BCMConnectionStatus.Healthy:
            nodes = self.get_bright_nodes()
            for node in nodes:
                saved_node = self.djson.get(node.hostname)
                if not saved_node:
                    self.djson[node.hostname] = {
                        "jobs": {}
                    }
            jobs = self.get_bright_jobs()
            for job in jobs:
                for jnode in job.nodes:
                    self.djson[jnode]["jobs"][f'{job.jobID}_{job.submittime}'] = BrightJobResource(job).__dict__
            Utils.write_text_to_file(self.SAVED_DATA_PATH, json.dumps(self.djson))
            Logger.log_message('Polling bright data request completed successfully')
        elif self.status == BCMConnectionStatus.Unhealthy:
            Logger.log_message('Not able to poll bright data, the connection is unhealthy', LOG_LEVELS.WARNING)

    def get_saved_data(self):
        return self.djson
