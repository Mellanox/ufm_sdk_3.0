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

from pythoncm.cluster import Cluster
from pythoncm.settings import Settings
from pythoncm import entity

from utils.logger import Logger, LOG_LEVELS
from utils.singleton import Singleton
from mgr.bright_configurations_mgr import BrightConfigParser


class BCMConnectionError(Exception):

    def __init__(self, message):
        Exception.__init__(self, message)


class BrightDataMgr(Singleton):

    def __init__(self):
        self.conf = BrightConfigParser.getInstance()
        self.bright_cluster = None
        self.bright_nodes = []

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
                msg = 'Failed to connect to Bright Cluster Manager: ' \
                      'unable to load the certificates'
                Logger.log_message(msg, LOG_LEVELS.ERROR)
                raise BCMConnectionError(msg)
            else:
                self.bright_cluster = Cluster(settings)
        except BCMConnectionError as ex:
            raise ex
        except Exception as ex:
            msg = f'Failed to connect to Bright Cluster Manager: {str(ex)}'
            Logger.log_message(msg, LOG_LEVELS.ERROR)
            raise BCMConnectionError(msg)

    def disconnect(self):
        try:
            if self.bright_cluster:
                Logger.log_message(f'Disconnecting from Bright Cluster Manager on: '
                                   f'{self.bright_cluster.settings.host}:{self.bright_cluster.settings.port}', LOG_LEVELS.DEBUG)
                self.bright_cluster.disconnect()
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
