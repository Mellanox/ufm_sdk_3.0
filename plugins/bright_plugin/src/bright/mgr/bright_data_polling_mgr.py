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
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from mgr.bright_data_mgr import BrightDataMgr, BCMConnectionError, BCMConnectionStatus
from mgr.bright_configurations_mgr import BrightConfigParser
from utils.singleton import Singleton
from utils.logger import Logger, LOG_LEVELS


class BrightDataPollingMgr(Singleton):

    def __init__(self):
        self.bright_data_mgr = BrightDataMgr.getInstance()
        self.conf = BrightConfigParser.getInstance()
        self.scheduler = BackgroundScheduler()
        self.polling_job = None
        self.polling_interval = 60 #seconds

    def start_polling(self):
        Logger.log_message('Start the bright data polling', LOG_LEVELS.DEBUG)
        if not self.polling_job:
            try:
                self.polling_job = self.scheduler.add_job(self.bright_data_mgr.poll_data,
                                                          'interval', seconds=self.polling_interval,
                                                          next_run_time=datetime.now())
                if not self.scheduler.running:
                    self.scheduler.start()
                Logger.log_message('The bright data polling started successfully')
                # this is to trigger the polling function for the first time
                # , don't wait 1 minute to start
                self.bright_data_mgr.poll_data()
            except BCMConnectionError as err:
                self.polling_job = None
                raise err
        return self.polling_job.id

    def stop_polling(self):
        if self.polling_job and self.scheduler.running:
            Logger.log_message('Stopping the bright data polling', LOG_LEVELS.DEBUG)
            self.polling_job.remove()
            self.polling_job = None
            self.bright_data_mgr.disconnect()
            Logger.log_message('The bright data polling stopped successfully')
            return True

    def trigger_polling(self):
        if self.conf.get_bright_enabled() and self.conf.get_bright_host():
            Logger.log_message('Restarting the bright data polling', LOG_LEVELS.DEBUG)
            self.stop_polling()
            self.start_polling()
            return True
        else:
            self.stop_polling()
            self.bright_data_mgr.status = BCMConnectionStatus.Disabled
            return False
