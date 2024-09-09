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

UFM_LOG_BASE = r"^(?P<timestamp>[\d\-]+ [\d\:\.]+) \w+ +(?P<severity>\w+) +{}"

UFM_LOG_HANDLED_TRAPS = re.compile(
    #   date        time    NA    severity
    UFM_LOG_BASE.format(r"UFM handled (\d+) traps$")
)

UFM_LOG_REST_MNGMNT_ERROR = re.compile(
    UFM_LOG_BASE.format(
        r"Rest management error: invalid username\/password \((\w+)\/[\*]+\)$"
    )
)

UFM_LOG_SYSINFO_FAILURE_FOR_SWITCH = re.compile(
    UFM_LOG_BASE.format(
        #                                                   switch    failure reason
        r"Sysinfo cb. Failed to get sysinfo for switch ([\w\d]+): \[(.+)$"
    )
)

UFM_LOG_FABRIC_ANALYSIS = re.compile(
    UFM_LOG_BASE.format(
        #       starting status                             repord-id   completed status
        r"(?P<status>Starting)?\s?Fabric_Analysis report\s(?P<id>\d+)(?:\scompleted)?$"
    )
)

UFM_LOG_UFM_STARTED = re.compile(UFM_LOG_BASE.format(r"UFM Enterprise Server started$"))

UFM_LOG_GRID_LOAD_STATUS = re.compile(
    UFM_LOG_BASE.format(
        #                                           state
        r"Grid Load from DB before discovery (?P<state>started|finished)"
    )
)

UFM_LOG_INIT_IS_DONE = re.compile(
    UFM_LOG_BASE.format(r"Initialization done, UFM server is ready$")
)

UFM_LOG_TELEMETRY_PROCESSING_TIME = re.compile(
    UFM_LOG_BASE.format(
        #                                           processing time
        r"Prometheus Client: Total Processing time = (\d+\.\d+)"
    )
)

UFM_LOG_TELEMETRY_DEVICE_STATS = re.compile(
    UFM_LOG_BASE.format(
        #                                 num devices     devices rate
        r"handled device stats. num_devices=(\d+) rate=(\d+\.\d+) devices\/sec."
        #          num ports     ports rate
        r" num_ports=(\d+) rate=(\d+\.\d+) ports\/sec."
    )
)

UFM_LOG_HEADERS = ("timestamp", "severity", "log_type", "data", "extra_info")


def ufm_log_telemetry_device_stats(match: Match):
    timestamp = match.group(1)
    severity = match.group(2)
    num_devices = match.group(3)
    num_ports = match.group(5)
    return (timestamp, severity, "telemetry_device_stats", num_devices, num_ports)


def ufm_log_telemetry_processing_time(match: Match):
    timestamp = match.group(1)
    severity = match.group(2)
    processing_time = match.group(3)
    return (timestamp, severity, "telemetry_processing_time", processing_time, None)


def ufm_log_init_is_done(match: Match):
    timestamp = match.group(1)
    severity = match.group(2)
    return (timestamp, severity, "ufm_init_done", None, None)


def ufm_log_ufm_grid_load_status(match: Match):
    timestamp = match.group(1)
    severity = match.group(2)
    status = match.group("state")
    return (timestamp, severity, "grid_load_status", status, None)


def ufm_log_fabric_analysis(match: Match):
    timestamp = match.group("timestamp")
    severity = match.group("severity")
    status = match.group("status") or "Completed"
    report_id = match.group("id")
    return (timestamp, severity, "fabric_analysis", status, report_id)


def ufm_log_sysinfo_failure_for_switch(match: Match):
    timestamp = match.group(1)
    severity = match.group(2)
    switch = match.group(3)
    reason = match.group(4)  # not used for now
    return (timestamp, severity, "failed_to_get_sysinfo", switch, reason)


def ufm_log_rest_mngmnt_error(match: Match):
    timestamp = match.group(1)
    severity = match.group(2)
    user = match.group(3)
    return (timestamp, severity, "mngmnt_bad_cookie", user, None)


def ufm_log_ufm_started(match: Match):
    timestamp = match.group(1)
    severity = match.group(2)
    return (timestamp, severity, "ufm_started", None, None)


def ufm_log_trap_handler(match: Match):
    timestamp = match.group(1)
    severity = match.group(2)
    number_of_traps = match.group(3)
    return (timestamp, severity, "trap_handled", number_of_traps, None)


ufm_log_regex_cls = RegexAndHandlers("ufm.log", UFM_LOG_HEADERS)

ufm_log_regex_cls.add_regex(UFM_LOG_HANDLED_TRAPS, ufm_log_trap_handler)
ufm_log_regex_cls.add_regex(UFM_LOG_FABRIC_ANALYSIS, ufm_log_fabric_analysis)
ufm_log_regex_cls.add_regex(UFM_LOG_REST_MNGMNT_ERROR, ufm_log_rest_mngmnt_error)
ufm_log_regex_cls.add_regex(
    UFM_LOG_SYSINFO_FAILURE_FOR_SWITCH, ufm_log_sysinfo_failure_for_switch
)
ufm_log_regex_cls.add_regex(UFM_LOG_GRID_LOAD_STATUS, ufm_log_ufm_grid_load_status)
ufm_log_regex_cls.add_regex(
    UFM_LOG_TELEMETRY_PROCESSING_TIME, ufm_log_telemetry_processing_time
)
ufm_log_regex_cls.add_regex(
    UFM_LOG_TELEMETRY_DEVICE_STATS, ufm_log_telemetry_device_stats
)
ufm_log_regex_cls.add_regex(UFM_LOG_UFM_STARTED, ufm_log_ufm_started)
ufm_log_regex_cls.add_regex(UFM_LOG_INIT_IS_DONE, ufm_log_init_is_done)
