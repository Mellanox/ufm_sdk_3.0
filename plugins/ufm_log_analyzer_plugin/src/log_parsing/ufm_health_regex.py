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
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring

import re
from typing import Match

from log_parsing.base_regex import RegexAndHandlers

UFM_HEALTH_LOG_REGEX = re.compile(
    #       Date                         Severity               Test         Test Class Status
    r"^([\d\-]+ [\d\:\.]+,\d+)\.\d{3} \w+ (\w+) +Test operation (\w+) of the test (\w+) (\w+)\."
    #     N/A      Reason
    r"(?: Reason\:)?(.+)?"
)
UFM_HEALTH_LOG_FAILURE_REASON_REGEX = re.compile(
    #           Does not start with date     Reason
    r"^(?!\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})(.*)$"
)


def ufm_health_failure_line(match: Match):
    """
    This is for the lines that comes after UFMCpuUsageTest failure
    """
    reason = match.group(1)
    return ("", "", "", "", "", reason)


def ufm_health_log(match: Match):
    timestamp = match.group(1)
    timestamp = timestamp.replace(",", ".", 1)
    severity = match.group(2)
    test_name = match.group(3)
    test_class = match.group(4)
    test_status = match.group(5)
    reason = match.group(6)
    if reason:
        reason = reason.replace("but we treated it as success. Reason: ", "")
    return (timestamp, severity, test_name, test_class, test_status, reason)


UFM_HEALTH_HEADERS = (
    "timestamp",
    "severity",
    "test_name",
    "test_class",
    "test_status",
    "reason",
)

ufm_health_regex_cls = RegexAndHandlers("ufmhealth.log", UFM_HEALTH_HEADERS)

ufm_health_regex_cls.add_regex(UFM_HEALTH_LOG_REGEX, ufm_health_log)
ufm_health_regex_cls.add_regex(
    UFM_HEALTH_LOG_FAILURE_REASON_REGEX, ufm_health_failure_line
)
