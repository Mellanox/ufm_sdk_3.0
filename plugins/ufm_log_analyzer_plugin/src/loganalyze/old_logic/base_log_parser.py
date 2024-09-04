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
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Iterable, Dict


class LogAnalysisTypes(Enum):
    UFMEventsLogEntry = auto()
    UFMEventsTopTalkers = auto()
    SMEventsLogEntry = auto()
    SMEventsTopTalkers = auto()


class LogSubscriber(ABC):
    @abstractmethod
    def update(self, analysis_type: LogAnalysisTypes, analysis_record: Iterable):
        pass


class BaseLogParser(ABC):
    def __init__(self, file_name):
        self.file_name = file_name
        self.subscribers: Dict[LogAnalysisTypes, LogSubscriber] = {}

    def parse(self):
        lines_counter = 0
        lines_failed = 0
        with open(self.file_name, "r") as fp:
            for line in fp:
                lines_counter += 1
                if not self._parse_line(line):
                    lines_failed += 1
                if lines_counter % 1000 == 0:
                    print(".", end="")
            print()
        print(f"Parsed total {lines_counter} lines, failed {lines_failed} lines")

    @abstractmethod
    def _parse_line(self, line):
        pass

    def subscribe(self, analysis_type: LogAnalysisTypes, subscriber: LogSubscriber):
        self.subscribers.setdefault(analysis_type, []).append(subscriber)

    def notify_sunscribers(self, analysis_type, analysis_record):
        for subscriber in self.subscribers.get(analysis_type, []):
            subscriber.update(analysis_type, analysis_record)
