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


class MultisubnetProvider(UfmRestClient):

    def __init__(self, host, username, password, topology_port, proxy_port, telemetry_port):
        super().__init__(host=host, username=username, password=password)
        self.token = None
        self.topology_port = topology_port
        self.proxy_port = proxy_port
        self.telemetry_port = telemetry_port

    def set_ufm_as_provider(self, auto_token_generation):
        Logger.log_message(f'Setting the UFM: {self.host} as provider', LOG_LEVELS.DEBUG)
        payload = {
            "Multisubnet": {
                "multisubnet_enabled": True,
                "multisubnet_role": 'provider'
            }
        }
        response = self.send_request(MultisubnetConstants.ENABLE_UFM_AS_PROVIDER_API,
                                     HTTPMethods.PUT, payload, exit_on_failure=False)
        if response and response.status_code == HTTPStatus.OK:
            if auto_token_generation:
                self.token = self.generate_token()

            Logger.log_message(f'Setting the UFM: {self.host} as provider has been completed successfully')
            return True
        Logger.log_message(f'Skipping the UFM Provider: {self.host}', LOG_LEVELS.WARNING)
        return False
