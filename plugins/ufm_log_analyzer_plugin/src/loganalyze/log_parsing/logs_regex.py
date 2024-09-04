#
# Copyright © 2013-2024 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
#
# pylint: disable=missing-module-docstring

from loganalyze.log_parsing.event_log_regex import event_log_regex_cls
from loganalyze.log_parsing.ufm_health_regex import ufm_health_regex_cls
from loganalyze.log_parsing.ufm_log import ufm_log_regex_cls
from loganalyze.log_parsing.ibdiagnet_log_regex import ibdiagnet_log_regex_cls
from loganalyze.log_parsing.console_log_regex import console_log_regex_cls
from loganalyze.log_parsing.rest_api_log_regex import rest_api_log_regex_cls

logs = [
    event_log_regex_cls,
    ufm_health_regex_cls,
    ufm_log_regex_cls,
    ibdiagnet_log_regex_cls,
    console_log_regex_cls,
    rest_api_log_regex_cls
]

logs_regex_csv_headers_list = []
for log_type in logs:
    logs_regex_csv_headers_list.append(log_type.get_all_info())
