#!/usr/bin/python3

"""
@copyright:
    Copyright (C) 2013-2022 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.

    This software product is a proprietary product of Nvidia Corporation and its affiliates
    (the "Company") and all right, title, and interest in and to the software
    product, including all associated intellectual property rights, are and
    shall remain exclusively with the Company.

    This software product is governed by the End User License Agreement
    provided with the software product.

@author: Nasr Ajaj
@date:   Jul 19, 2022
"""

import os
import platform
from http import HTTPStatus

from utils.job_polling import JobPolling

try:
    from utils.utils import Utils
    from utils.ufm_rest_client import UfmRestClient, HTTPMethods
    from utils.args_parser import ArgsParser
    from utils.config_parser import ConfigParser
    from utils.logger import Logger, LOG_LEVELS
    from utils.exception_handler import ExceptionHandler
except ModuleNotFoundError as e:
    if platform.system() == "Windows":
        print("Error occurred while importing python modules, "
              "Please make sure that you exported your repository to PYTHONPATH by running: "
              f'set PYTHONPATH=%PYTHONPATH%;{os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))}')
    else:
        print("Error occurred while importing python modules, "
              "Please make sure that you exported your repository to PYTHONPATH by running: "
              f'export PYTHONPATH="${{PYTHONPATH}}:{os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))}"')


class UfmValidationTestConstants:

    VALIDATION_TEST_API_URL = 'fabricValidation/tests'
    AVAILABLE_VALIDATION_TESTS = [
        "CheckLids", "CheckLinks", "CheckSubnetManager", "CheckDuplicateNodes", "CheckRouting",
        "CheckDuplicateGuids", "CheckLinkSpeed", "CheckLinkWidth", "CheckPartitionKey", "CheckTemperature",
        "CheckCables", "CheckEffectiveBER", "CheckSymbolBER", "RailOptimizedTopologyValidation",
        "DragonflyTopologyValidation", "SHARPFabricValidation", "TreeTopologyValidation", "SocketDirectModeReporting"
    ]
    API_PARAM_TEST = "test"

    VALIDATION_TEST_OPERATIONS = {
        "run_test": "run_test",
        "get_available_tests": "get_available_tests"
    }

    args_list = [
        {
            "name": f'--{VALIDATION_TEST_OPERATIONS.get("run_test")}',
            "help": "test name to be run"
        },
        {
            "name": f'--{VALIDATION_TEST_OPERATIONS.get("get_available_tests")}',
            "help": "get list of tests which are available to run",
            "no_value": True
        }
    ]


class UfmValidationTestConfigParser(ConfigParser):
    def __init__(self, args):
        super().__init__(args)


class UfmValidationTest:

    @staticmethod
    def run_validation_test(test_name):
        url = f'{UfmValidationTestConstants.VALIDATION_TEST_API_URL}/{test_name}'
        response = ufm_rest_client.send_request(url, HTTPMethods.POST, payload=None)
        if response and response.status_code == HTTPStatus.ACCEPTED:
            job_id = job_polling.extract_job_id(response.text)
            job_polling.start_polling(job_id, print_summary=True)
        return response


if __name__ == "__main__":
    # init app args
    args = ArgsParser.parse_args("UFM Fabric Validation Test", UfmValidationTestConstants.args_list)

    # init app config parser & load config files
    config_parser = UfmValidationTestConfigParser(args)

    # init logs configs
    logs_level = config_parser.get_logs_level()
    logs_file_name = config_parser.get_logs_file_name()
    max_log_file_size = config_parser.get_log_file_max_size()
    log_file_backup_count = config_parser.get_log_file_backup_count()
    Logger.init_logs_config(logs_file_name, logs_level, max_log_file_size, log_file_backup_count)

    # init ufm rest client
    ufm_rest_client = UfmRestClient(host=config_parser.get_ufm_host(),
                                    client_token=config_parser.get_ufm_access_token(), username=config_parser.get_ufm_username(),
                                    password=config_parser.get_ufm_password(), ws_protocol=config_parser.get_ufm_protocol())
    job_polling = JobPolling(ufm_rest_client, "validation test")
    args_dict = args.__dict__
    if args_dict.get(UfmValidationTestConstants.VALIDATION_TEST_OPERATIONS.get("run_test")):
        param_test_name = args_dict.get(UfmValidationTestConstants.VALIDATION_TEST_OPERATIONS.get("run_test"))
        if param_test_name and param_test_name in UfmValidationTestConstants.AVAILABLE_VALIDATION_TESTS:
            UfmValidationTest.run_validation_test(param_test_name)
        else:
            message = f'The test {param_test_name} isn\'t one of the following available tests: {UfmValidationTestConstants.AVAILABLE_VALIDATION_TESTS}'
            Logger.log_message(message, LOG_LEVELS.ERROR)
    elif args_dict.get(UfmValidationTestConstants.VALIDATION_TEST_OPERATIONS.get("get_available_tests")):
        Logger.log_message(UfmValidationTestConstants.AVAILABLE_VALIDATION_TESTS)
    else:
        message = "You must provide one of the following operations: " + \
                  ''.join(['--{0} | '.format(item) for key, item in UfmValidationTestConstants.VALIDATION_TEST_OPERATIONS.items()])

        Logger.log_message(message, LOG_LEVELS.ERROR)