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

EVENT_LOG_REGEX = re.compile(
    #  date      time         na       na severity   Site and name      type   objtype objid
    r"^([\d\-]+ [\d\:\.]+) \[\d+\] \[\d+\] (\w+) (?:Site \[[\w-]*\] )?\[(\w+)\] (\w+) \[(.*)\]\: "
    #      event       event_details
    r"((([ \w\/\-]+)((\,|\:|\.)(.*))?)|(.*))$"
)

IBPORT_OBJ_REGEX = re.compile(r"((Computer|Switch).*)\] \[")
COMP_OBJ_REGEX = re.compile(r"(Computer: [\w\-\.]+)")
MODULE_OBJ_REGEX = re.compile(r"(Switch.*)\] \[")
BAD_PKEY_REGEX = re.compile(r"Switch: ([\d\w-]+)")
LINK_OBJ_REGEX = re.compile(r"([a-f0-9]+\_[0-9]+)[\w ]+\: ([a-f0-9]+_[0-9]+)")


def _format_object_id(object_type: str, object_id: str):  # pylint: disable=too-many-branches
    if object_type == "IBPort":
        match = IBPORT_OBJ_REGEX.search(object_id)
        if match:
            object_id = match.group(1)
    elif object_type == "Site":
        object_id = "default"
    elif object_type == "Computer":
        match = COMP_OBJ_REGEX.search(object_id)
        if match:
            object_id = match.group(1)
    elif object_type == "Module":
        match = MODULE_OBJ_REGEX.search(object_id)
        if match:
            object_id = match.group(1)
    elif object_type == "Link":
        match = LINK_OBJ_REGEX.search(object_id)
        if match:
            src = match.group(1)
            dest = match.group(2)
            object_id = f"{src}:{dest}"
    elif object_type == "Switch":
        match = BAD_PKEY_REGEX.search(object_id)
        if match:
            object_id = match.group(1)
    return object_id


def event_log_extractor(match: Match):
    if not match:
        return None
    timestamp = match.group(1)
    severity = match.group(2)
    event_type = match.group(3)
    object_type = match.group(4)
    object_id = _format_object_id(object_type, match.group(5))
    event = match.group(12)
    event_details = ""
    if not event:
        event = match.group(8)
        event_details = match.group(11)
    return (
        timestamp,
        severity,
        event_type,
        object_type,
        object_id,
        event,
        event_details,
    )


EVENT_LOG_HEADERS = (
    "timestamp",
    "severity",
    "event_type",
    "object_type",
    "object_id",
    "event",
    "event_details",
)


event_log_regex_cls = RegexAndHandlers("event.log", EVENT_LOG_HEADERS)
event_log_regex_cls.add_regex(EVENT_LOG_REGEX, event_log_extractor)
