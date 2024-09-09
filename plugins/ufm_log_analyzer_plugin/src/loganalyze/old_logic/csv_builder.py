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

import csv
import os
from typing import Iterable, List

from log_analyzer.src.loganalyze.old_logic.base_log_parser import (
    LogSubscriber,
    LogAnalysisTypes,
)
from log_analyzer.src.loganalyze.old_logic.constants import Files


class CsvBuilder(LogSubscriber):
    UFM_EVENTS_LOG_HEADER = (
        "timestamp",
        "severity",
        "event_type",
        "object_type",
        "object_id",
        "event",
        "event_details",
    )
    UFM_EVENTS_STATS_HEADER = ("event", "object_id", "count")

    def __init__(self):
        self.ufm_events_log_entries = []
        self.ufm_events_top_talkers = []

    def update(self, analysis_type: LogAnalysisTypes, analysis_record: Iterable):
        if analysis_type == LogAnalysisTypes.UFMEventsLogEntry:
            self.ufm_events_log_entries.append(analysis_record)
        elif analysis_type == LogAnalysisTypes.UFMEventsTopTalkers:
            self.ufm_events_top_talkers.append(analysis_record)

    def _write_csv_file(self, csv_path: str, headers: str, records: List[str]):
        with open(csv_path, "w") as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
            writer.writerow(headers)
            for index, entry in enumerate(records):
                writer.writerow(entry)
                if index % 1000 == 0:
                    print(".", end="")
            print()

    def save(self, out_dir: str):
        csv_path = os.path.join(out_dir, Files.UFM_EVENTS_CSV_FILE)
        print("-I- Generating ufm events file:", csv_path, "...")
        self._write_csv_file(
            csv_path, self.UFM_EVENTS_LOG_HEADER, self.ufm_events_log_entries
        )

        csv_path = os.path.join(out_dir, "ufm_events_stats.csv")
        print("-I- Generating ufm events stats file:", csv_path, "...")
        self._write_csv_file(
            csv_path, self.UFM_EVENTS_STATS_HEADER, self.ufm_events_top_talkers
        )
