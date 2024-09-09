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
# author: Samer Deeb
# date:   Mar 02, 2024
#
import re
from collections import Counter

from log_analyzer.src.loganalyze.old_logic.base_log_parser import (
    BaseLogParser,
    LogAnalysisTypes,
)


class UFMEventsLogParser(BaseLogParser):
    EVENT_REGEX = re.compile(
        #  date      time         na       na severity   Site and name      type   objtype objid        event       event_details
        r"^([\d\-]+ [\d\:\.]+) \[\d+\] \[\d+\] (\w+) (?:Site \[[\w-]*\] )?\[(\w+)\] (\w+) \[(.*)\]\: ((([ \w\/\-]+)((\,|\:|\.)(.*))?)|(.*))$"
    )
    IBPORT_OBJ_REGEX = re.compile(r"((Computer|Switch).*)\] \[")
    COMP_OBJ_REGEX = re.compile(r"(Computer: [\w\-\.]+)")
    MODULE_OBJ_REGEX = re.compile(r"(Switch.*)\] \[")
    LINK_OBJ_REGEX = re.compile(r"([a-f0-9]+\_[0-9]+)[\w ]+\: ([a-f0-9]+_[0-9]+)")

    def __init__(self, file_name):
        super().__init__(file_name)
        self.stats = {}

    def _format_object_id(self, object_type: str, object_id: str):
        if object_type == "IBPort":
            match = self.IBPORT_OBJ_REGEX.search(object_id)
            if match:
                object_id = match.group(1)
            else:
                print(f"-W- NO IBPort match for: {object_id}")
        elif object_type == "Site":
            object_id = "default"
        elif object_type == "Computer":
            match = self.COMP_OBJ_REGEX.search(object_id)
            if match:
                object_id = match.group(1)
            else:
                print(f"-W- NO Computer match for: {object_id}")
        elif object_type == "Module":
            match = self.MODULE_OBJ_REGEX.search(object_id)
            if match:
                object_id = match.group(1)
            else:
                print(f"-W- NO Module match for: {object_id}")
        elif object_type == "Link":
            match = self.LINK_OBJ_REGEX.search(object_id)
            if match:
                src = match.group(1)
                dest = match.group(2)
                object_id = f"{src}:{dest}"
            else:
                print(f"-W- NO Link match for: {object_id}")
        return object_id

    def _parse_line(self, line):
        line = line.strip()
        if not line:
            return False
        match = self.EVENT_REGEX.match(line)
        if not match:
            print(f"-W- No match for line: {line}")
            return False
        timestamp = match.group(1)
        severity = match.group(2)
        event_type = match.group(3)
        object_type = match.group(4)
        object_id = self._format_object_id(object_type, match.group(5))
        event = match.group(12)
        event_details = ""
        if not event:
            event = match.group(8)
            event_details = match.group(11)
        else:
            print(f"-W- No event match for: {event}")
        log_entry = (
            timestamp,
            severity,
            event_type,
            object_type,
            object_id,
            event,
            event_details,
        )
        self.notify_sunscribers(LogAnalysisTypes.UFMEventsLogEntry, log_entry)
        self.stats.setdefault(event, Counter())[object_id] += 1
        return True

    def parse(self):
        super().parse()
        for event, ev_counter in self.stats.items():
            sorted_counters = sorted(
                ev_counter.items(), key=lambda x: x[1], reverse=True
            )
            for object_id, count in sorted_counters:
                entry = (event, object_id, count)
                self.notify_sunscribers(LogAnalysisTypes.UFMEventsTopTalkers, entry)
