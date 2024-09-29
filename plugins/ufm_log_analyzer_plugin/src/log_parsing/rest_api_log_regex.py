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


import re
from typing import Match

from log_parsing.base_regex import RegexAndHandlers

REST_API_LOG_REGEX = re.compile(
    #        Date                  NA    Severity
    r"^(?P<date>[\d\-]+ [\d\:\.]+) \w+ (?P<severity>\w+) +(?: client: "
    #       client                           user
    r"(?P<client>None|[\.:\w]+),)?(?: user: (?P<user>[\w]+),)"
    #                url                         method
    r"(?: url: \((?P<url>[^\s\)]+)\)?,)(?: method:? \((?P<method>[\w]+)\),?)?"
    #                        Status code                                duration
    r"(?: status_code: \((?P<status_code>[\d]+)\),?)?(?: duration: (?P<duration>[\d\.]+) seconds)?$"
)

def rest_api_log(match: Match):
    """
    The rest api log line had serval changes in the last releases.
    By using the matching groups here, we do not need to check if
    a filed exists or not. If it does not, it will be None.
    """
    timestamp = match.group("date")
    severity = match.group("severity")
    client_ip = match.group("client")
    user = match.group("user")
    url = match.group("url")
    method = match.group("method")
    status_code = match.group("status_code")
    duration = match.group("duration")
    return (timestamp, severity, client_ip, user, url, method, status_code, duration)

REST_API_LOG_HEADERS = (
    "timestamp",
    "severity",
    "client_ip",
    "user",
    "url",
    "method",
    "status_code",
    "duration"
)

rest_api_log_regex_cls = RegexAndHandlers("rest_api.log", REST_API_LOG_HEADERS)

rest_api_log_regex_cls.add_regex(REST_API_LOG_REGEX, rest_api_log)
