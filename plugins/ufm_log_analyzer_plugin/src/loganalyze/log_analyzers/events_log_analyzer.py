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
# pylint: disable=# pylint: disable=missing-function-docstring
# pylint: disable=# pylint: disable=missing-class-docstring
# pylint: disable=# pylint: disable=missing-module-docstring

from typing import List
import pandas as pd
from loganalyze.log_analyzers.constants import DataConstants
from loganalyze.log_analyzers.base_analyzer import BaseAnalyzer
import loganalyze.logger as log


class EventsLogAnalyzer(BaseAnalyzer):
    def __init__(self, logs_csvs: List[str], hours: int, dest_image_path):
        super().__init__(logs_csvs, hours, dest_image_path)
        self._supported_log_levels = ["CRITICAL", "WARNING", "INFO", "MINOR"]
        self._funcs_for_analysis = {self.print_critical_events_per_hour,
                                    self.print_link_up_down_count_per_hour}

    # Function to split "object_id" into "device" and "description"
    def _split_switch_object_id(self, row):
        if "Switch:" in row["object_id"]:
            parts = row["object_id"].split("/")
            return pd.Series([parts[0].strip(), parts[1].strip()])

        return pd.Series([None, None])

    def analyze_events(self):
        grouped = self._log_data_sorted.groupby(["object_id", "event"])
        event_counts_df = grouped.size().reset_index(name="count")
        event_counts_df = event_counts_df.sort_values(
            ["event", "count"], ascending=False
        )
        self._log_data_sorted[["device", "description"]] = self._log_data_sorted.apply(
            self._split_switch_object_id, axis=1
        )
        event_counts = (
            self._log_data_sorted.groupby(["event", "device", "description"])
            .size()
            .reset_index(name="count")
        )
        log.LOGGER.debug(event_counts.head())

    def get_events_by_log_level(self, log_level="CRITICAL"):
        if log_level not in self._supported_log_levels:
            log.LOGGER.error(
                f"Requested log level {log_level} is not valid, "
                f"options are {self._supported_log_levels}"
            )
            return None

        return self._log_data_sorted[self._log_data_sorted["severity"] == log_level]

    def get_events_by_log_level_and_event_types_as_count(self, log_level="CRITICAL"):
        if log_level not in self._supported_log_levels:
            log.LOGGER.error(
                f"Requested log level {log_level} is not valid, "
                f"options are {self._supported_log_levels}"
            )
            return None
        events_by_log_level = self.get_events_by_log_level(log_level)
        return events_by_log_level["event_type"].value_counts()

    def print_critical_events_per_hour(self):
        critical_events = self.get_events_by_log_level("CRITICAL")
        critical_events_grouped_by_time = (
            critical_events.groupby([DataConstants.AGGREGATIONTIME, "event"])\
                .size().reset_index(name="count")
        )

        pivot_critical_events_by_hour = critical_events_grouped_by_time.pivot(
            index=DataConstants.AGGREGATIONTIME, columns="event", values="count"
        ).fillna(0)

        self._save_pivot_data_in_bars(
            pivot_critical_events_by_hour,
            "Time",
            "Events",
            "Aggregated critical events",
            "Events",
        )
        return critical_events_grouped_by_time

    def print_link_up_down_count_per_hour(self):
        links_events = self._log_data_sorted[
            (self._log_data_sorted["event"] == "Link is up")
            |
            (self._log_data_sorted["event"] == "Link went down")
        ]
        grouped_links_events = links_events.groupby([DataConstants.AGGREGATIONTIME, "event"])
        counted_links_events_by_time = grouped_links_events.size().reset_index(
            name="count"
        )

        pivot_links_data = counted_links_events_by_time.pivot(
            index=DataConstants.AGGREGATIONTIME, columns="event", values="count"
        ).fillna(0)
        self._save_pivot_data_in_bars(
            pivot_links_data,
            "Time",
            "Number of Events",
            "Link up/down events",
            "Event"
        )
