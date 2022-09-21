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
# @date:   Sep 20, 2022
#
import os
from utils.logger import Logger, LOG_LEVELS

SERVICE_CMD = 'sudo systemctl %s fluent-bit'
SUCCESS_CODE = 0
SERVICE_NOT_INSTALLED = 1024
SERVICE_STOPPED = 768


class FluentBitServiceMgr:

    def __init__(self):
        pass

    @staticmethod
    def get_service_status():
        cmd = SERVICE_CMD % 'status'
        status = os.system(cmd)
        if status == SUCCESS_CODE:
            Logger.log_message('fluent-bit service is running', LOG_LEVELS.DEBUG)
            return True, status
        elif status == SERVICE_NOT_INSTALLED:
            Logger.log_message('fluent-bit service not installed', LOG_LEVELS.ERROR)
            return False, status
        elif status == SERVICE_STOPPED:
            Logger.log_message('fluent-bit service not running', LOG_LEVELS.ERROR)
            return False, status

    @staticmethod
    def stop_service():
        Logger.log_message('stopping the fluent-bit service', LOG_LEVELS.DEBUG)
        cmd = SERVICE_CMD % 'stop'
        result = os.system(cmd)
        if result == SUCCESS_CODE:
            Logger.log_message('fluent-bit service stopped successfully', LOG_LEVELS.DEBUG)
            return True, result
        else:
            Logger.log_message('fluent-bit service not able to be stopped', LOG_LEVELS.ERROR)
            return False, result

    @staticmethod
    def start_service():
        Logger.log_message('starting the fluent-bit service', LOG_LEVELS.DEBUG)
        cmd = SERVICE_CMD % 'start'
        result = os.system(cmd)
        if result == SUCCESS_CODE:
            Logger.log_message('fluent-bit service started successfully')
            return True, result
        else:
            Logger.log_message('fluent-bit service not able to be started', LOG_LEVELS.ERROR)
            return False, result

    @staticmethod
    def restart_service():
        Logger.log_message('restarting the fluent-bit service', LOG_LEVELS.DEBUG)
        cmd = SERVICE_CMD % 'restart'
        result = os.system(cmd)
        if result == SUCCESS_CODE:
            Logger.log_message('fluent-bit service restarted successfully')
            return True, result
        else:
            Logger.log_message('fluent-bit service not able to be restarted', LOG_LEVELS.ERROR)
            return False, result
