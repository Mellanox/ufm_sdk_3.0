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


class MultisubnetConstants:
    ENABLE_UFM_AS_PROVIDER_API = 'app/ufm_config'
    ADD_PROVIDER_TO_CONSUMER_API = 'providers'

    CONF_CONSUMER_SECTION = "Consumer"
    CONF_UFM_CONSUMER_IP = "ufm_consumer_ip"
    CONF_UFM_CONSUMER_USERNAME = "ufm_consumer_username"
    CONF_UFM_CONSUMER_PASSWORD = "ufm_consumer_password"
    CONF_AUTO_TOKEN_GENERATION = "ufm_auto_token_generation"
    CONF_PROVIDERS_SECTION = "Providers"
    CONF_PROVIDERS_FROM_IP = "ufm_providers_from_ip"
    CONF_PROVIDERS_TO_IP = "ufm_providers_to_ip"
    CONF_UFM_PROVIDER_USERNAME = "ufm_provider_username"
    CONF_UFM_PROVIDER_PASSWORD = "ufm_provider_password"
    CONF_PROVIDERS_TOPOLOGY_PORT = "ufm_provider_topology_port"
    CONF_PROVIDERS_PROXY_PORT = "ufm_provider_proxy_port"
    CONF_PROVIDERS_TELEMETRY_PORT = "ufm_provider_telemetry_port"

    ARGS_LIST = [
        {
            "name": f'--{CONF_UFM_CONSUMER_IP}',
            "help": "IP for the consumer UFM server"
        },
        {
            "name": f'--{CONF_UFM_CONSUMER_USERNAME}',
            "help": "Username for the consumer UFM server"
        },
        {
            "name": f'--{CONF_UFM_CONSUMER_PASSWORD}',
            "help": "Password for the consumer UFM server"
        },
        {
            "name": f'--{CONF_PROVIDERS_FROM_IP}',
            "help": "Starting IP range for the provider UFM servers (inclusive)"
        },
        {
            "name": f'--{CONF_PROVIDERS_TO_IP}',
            "help": "Ending IP range for the provider UFM servers (inclusive)"
        },
        {
            "name": f'--{CONF_AUTO_TOKEN_GENERATION}',
            "help": "If true, a token will be generated in the UFM provider via the provider's credentials"
                    "and use it by the consumer with the communication with this provider"
        },
        {
            "name": f'--{CONF_UFM_PROVIDER_USERNAME}',
            "help": "Username for the providers UFM server"
        },
        {
            "name": f'--{CONF_PROVIDERS_TOPOLOGY_PORT}',
            "help": "Providers topology port (Default is 7120)"
        },
        {
            "name": f'--{CONF_PROVIDERS_PROXY_PORT}',
            "help": "Providers proxy port (Default is 443)"
        },
        {
            "name": f'--{CONF_PROVIDERS_TELEMETRY_PORT}',
            "help": "Providers telemetry endpoint port (Default is 9001)"
        }
    ]