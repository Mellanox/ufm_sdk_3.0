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

from loganalyze.log_parsing.base_regex import RegexAndHandlers

###
# This log is only to find general exceptions and errors,
# as each specific log is being analyzed on his own.
###

EXPCT_REGEX = r"expc"
TRACBEBACK_REGEX = r"traceback"

CONSOLE_LOG_EXCEPTION_REGEX = re.compile(
    # Date and time    NA  log level    The rest of the line
    r"^([\d\-]+ [\d\:\.]+) \w+ +(\w+) +(.*(?:traceback|exception).*)",
    re.IGNORECASE,
)

ERROR_LINE_REGEX = re.compile(
    # Does not start with date   The rest
    r"^(?![\d\-]+ [\d\:\.]+ \w+)(.*)$",
)
"""
fetch_telemetry_data() with param: http://0.0.0.0:9001/csv/cset/converted_enterprise, 0
Received bytes: 5369833
Processed counters: 690000
fetch time: 561, parse time: 186

"""

FETCH_TELEMETRY_DATA = re.compile(
    r"^(?:fetch_telemetry_data|Received bytes|Processed counters|fetch time).*$"
)

UFM_STATE_CHANGE = re.compile(r"^.*UFM daemon.*")


def console_log_exception(match: Match):
    timestamp = match.group(1)
    line = match.group(3)
    return (timestamp, "Error", line)


def error_line(match: Match):
    line = match.group(1)
    return (None, None, line)


def do_nothing(match: Match):  # pylint: disable=unused-argument
    return (None, None, None)


CONSOLE_LOG_HEADERS = ("timestamp", "type", "data")

console_log_regex_cls = RegexAndHandlers("console.log", CONSOLE_LOG_HEADERS)
console_log_regex_cls.add_regex(FETCH_TELEMETRY_DATA, do_nothing)
console_log_regex_cls.add_regex(UFM_STATE_CHANGE, do_nothing)
console_log_regex_cls.add_regex(CONSOLE_LOG_EXCEPTION_REGEX, console_log_exception)
console_log_regex_cls.add_regex(ERROR_LINE_REGEX, error_line)
