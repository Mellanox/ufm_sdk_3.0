#!/usr/bin/python3
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
import ipaddress

try:
    from scripts.ufm_multisubnet.src import MultisubnetConstants
    from scripts.ufm_multisubnet.src.multisubnet_config_parser import MultisubnetConfigParser
    from scripts.ufm_multisubnet.src.consumer_rest_client import MultisubnetConsumer
    from scripts.ufm_multisubnet.src.provider_rest_client import MultisubnetProvider
    from utils.args_parser import ArgsParser
    from utils.logger import Logger, LOG_LEVELS
    from utils.exception_handler import ExceptionHandler
except ModuleNotFoundError as e:
    import platform
    import os
    export_cmd = ''
    if platform.system() == "Windows":
        export_cmd = f'set PYTHONPATH=%PYTHONPATH%;{os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))}"'
    else:
        export_cmd = f'export PYTHONPATH="${{PYTHONPATH}}:{os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))}"'

    print(f"Error occurred while importing python modules, "
          f"Please make sure that you exported your repository to PYTHONPATH by running: {export_cmd}")


def _init_logs(config_parser):
    # init logs configs
    logs_file_name = config_parser.get_logs_file_name()
    logs_level = config_parser.get_logs_level()
    max_log_file_size = config_parser.get_log_file_max_size()
    log_file_backup_count = config_parser.get_log_file_backup_count()
    Logger.init_logs_config(logs_file_name, logs_level, max_log_file_size, log_file_backup_count)


if __name__ == '__main__':
    try:
        ######
        # init app args
        args = ArgsParser.parse_args('Multisubnet Configuration Setup',
                                     MultisubnetConstants.ARGS_LIST)
        config_parser = MultisubnetConfigParser(args)
        _init_logs(config_parser)
        ######
        auto_token_generation = config_parser.get_ufm_auto_token_generation_flag()
        ######
        consumer_client = MultisubnetConsumer(host=config_parser.get_ufm_consumer_ip(),
                                              username=config_parser.get_ufm_consumer_username(),
                                              password=config_parser.get_ufm_consumer_password())
        ######
        from_ip = config_parser.get_ufm_provider_from_ip()
        to_ip = config_parser.get_ufm_provider_to_ip()
        from_ip_addr = ipaddress.ip_address(from_ip)
        to_ip_addr = ipaddress.ip_address(to_ip)
        if from_ip_addr >= to_ip_addr:
            raise Exception('`From` IP providers should be smaller than `To` IP')
        while from_ip_addr <= to_ip_addr:
            try:
                provider_client = MultisubnetProvider(host=str(from_ip_addr),
                                                      username=config_parser.get_ufm_providers_username(),
                                                      password=config_parser.get_ufm_providers_password(),
                                                      topology_port=config_parser.get_ufm_providers_topology_port(),
                                                      proxy_port=config_parser.get_ufm_providers_proxy_port(),
                                                      telemetry_port=config_parser.get_ufm_providers_telemetry_port())
                result = provider_client.set_ufm_as_provider(auto_token_generation=auto_token_generation)
                if result:
                    result = consumer_client.add_provider_request(provider_client)
            except Exception as ex:
                Logger.log_message(f'Failed to configure the IP {str(from_ip_addr)} as Provider '
                                   f'due to the following error: {str(ex)}')
            finally:
                from_ip_addr += 1
    except Exception as ex:
        ExceptionHandler.handel_exception(str(ex))
