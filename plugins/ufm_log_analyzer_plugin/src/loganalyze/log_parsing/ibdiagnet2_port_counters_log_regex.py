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

from loganalyze.log_parsing.base_regex import RegexAndHandlers

ITERATION_TIME_REGEX = re.compile(
    r"^\[ExportAPI_STATS\] Iteration time"
    r"\: ([\d\.]+) sec \@ \[([\d\-]+ [\d\:\.]+)\]$"
)

TIMEOUT_DUMP_CORE_REGEX = re.compile(r"^timeout: the monitored command dumped core$")

TOTAL_SWITCH_PORTS_REGEX = re.compile(
    r"^.*Total switches\/ports \[(\d+)\/(\d+)\]\, "
    r"CAs\/ports \[(\d+)\/(\d+)\]\, Routers\/ports "
    r"\[(\d+)\/(\d+)\]\s*$"
)

COLLECTX_VERSION_REGEX = re.compile(r"^\[ExportAPI\] Collectx version ([\d\.]+)$")


def iteration_time(match: Match):
    iteration_time_sec = match.group(1)
    timestamp = match.group(2)
    return (
        "iteration_time",
        timestamp,
        iteration_time_sec,
        None,
        None,
        None,
        None,
        None,
    )


def timeout_dump_core(_: Match):
    return ("timeout_dump_core", None, None, None, None, None, None, None)


def total_switch_ports(match: Match):
    total_switches = match.group(1)
    total_switch_ports_count = match.group(2)
    total_cas = match.group(3)
    total_cas_ports = match.group(4)
    total_routers = match.group(5)
    total_routers_ports = match.group(6)
    return (
        "total_devices_ports",
        None,
        total_switches,
        total_switch_ports_count,
        total_cas,
        total_cas_ports,
        total_routers,
        total_routers_ports,
    )


def collectx_version(match: Match):
    collectx_version_str = match.group(1)
    return (
        "collectx_version",
        None,
        collectx_version_str,
        None,
        None,
        None,
        None,
        None,
    )


ibdiagnet2_headers = (
    "type",
    "timestamp",
    "data",
    "extra1",
    "extra2",
    "extra3",
    "extra4",
    "extra5",
)

ibdiagnet2_primary_log_regex_cls = RegexAndHandlers(
    "ufm_logs_ibdiagnet2_port_counters.log", ibdiagnet2_headers
)
ibdiagnet2_secondary_log_regex_cls = RegexAndHandlers(
    "secondary_telemetry_ibdiagnet2_port_counters.log", ibdiagnet2_headers
)

regex_funcs_map = {
    ITERATION_TIME_REGEX: iteration_time,
    TIMEOUT_DUMP_CORE_REGEX: timeout_dump_core,
    TOTAL_SWITCH_PORTS_REGEX: total_switch_ports,
    COLLECTX_VERSION_REGEX: collectx_version,
}

for regex, regex_func in regex_funcs_map.items():
    ibdiagnet2_primary_log_regex_cls.add_regex(regex, regex_func)
    ibdiagnet2_secondary_log_regex_cls.add_regex(regex, regex_func)
