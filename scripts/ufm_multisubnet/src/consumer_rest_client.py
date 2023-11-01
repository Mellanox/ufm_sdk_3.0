"""
@copyright:
    Copyright (C) 2013-2023 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.

    This software product is a proprietary product of Nvidia Corporation and its affiliates
    (the "Company") and all right, title, and interest in and to the software
    product, including all associated intellectual property rights, are and
    shall remain exclusively with the Company.

    This software product is governed by the End User License Agreement
    provided with the software product.

@author: anan AlAghbar
@date:   Oct 23, 2023
"""
from http import HTTPStatus
from scripts.ufm_multisubnet.src import MultisubnetConstants
from utils.ufm_rest_client import UfmRestClient, HTTPMethods
from utils.logger import Logger, LOG_LEVELS


class MultisubnetConsumer(UfmRestClient):

    def __init__(self, host, username, password):
        super().__init__(host=host, username=username, password=password)

    def add_provider_request(self, provider):
        Logger.log_message(f'Adding the provider: {provider.host} '
                           f'to consumer {self.host}', LOG_LEVELS.DEBUG)
        payload = {
            'ip': provider.host,
            'topology_port': provider.topology_port,
            'proxy_port': provider.proxy_port,
            'telemetry_port': provider.telemetry_port
        }
        if provider.token:
            payload['token'] = provider.token
        else:
            payload['user'] = provider.username
            payload['password'] = provider.password
        response = self.send_request(MultisubnetConstants.ADD_PROVIDER_TO_CONSUMER_API,
                                     HTTPMethods.POST, payload, exit_on_failure=False)
        if response and response.status_code == HTTPStatus.ACCEPTED:
            Logger.log_message(f'Adding the provider: {provider.host} '
                               f'to consumer {self.host} has been completed successfully')
            return True
        Logger.log_message(f'Adding the provider: {provider.host} '
                           f'to consumer {self.host} has been failed', LOG_LEVELS.ERROR)
        return False
