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
        self._funcs_for_analysis = {self.plot_critical_events_per_aggregation_time,
                                    self.plot_link_up_down_count_per_aggregation_time,
                                    self.plot_top_n_critical_events_over_time}

    # Function to split "object_id" into "device" and "description"
    def _split_switch_object_id(self, row):
        if "Switch:" in row["object_id"]:
            parts = row["object_id"].split("/")
            return pd.Series([parts[0].strip(), parts[1].strip()])

        return pd.Series([None, None])

    def get_events_by_log_level(self, log_level="CRITICAL"):
        if log_level not in self._supported_log_levels:
            log.LOGGER.error(
                f"Requested log level {log_level} is not valid, "
                f"options are {self._supported_log_levels}"
            )
            return None

        return self._log_data_sorted[self._log_data_sorted["severity"] == log_level]

    def plot_top_n_critical_events_over_time(self, n=10):
        critical_events = self.get_events_by_log_level("CRITICAL")
        total_critical_events = critical_events.groupby("event").size().reset_index(name="count")

        # Get the top n events with the highest count overall
        top_n_events = total_critical_events.nlargest(n, 'count')

        # Group the top 5 events by time interval
        critical_events_grouped_by_time = \
            critical_events[critical_events["event"].isin(top_n_events["event"])]\
            .groupby([DataConstants.AGGREGATIONTIME, "event"])\
            .size().reset_index(name="count")

        pivot_top_n_events_by_hour = critical_events_grouped_by_time.pivot(
            index=DataConstants.AGGREGATIONTIME, columns="event", values="count"
        ).fillna(0)

        self._save_pivot_data_in_bars(
            pivot_top_n_events_by_hour,
            "Time",
            "Events",
            f"Top {n} aggregated critical events over time",
            "Events",
        )

    def get_critical_event_bursts(self, n=5):
        """
        Finds bursts of events by event_type over all time, going minute by minute.
        """
        critical_events = self.get_events_by_log_level("CRITICAL")

        # Round timestamps to the nearest minute
        critical_events['minute'] = critical_events['timestamp'].dt.floor('T')

        # Group by minute and event type, then count the number of events in each group
        event_counts = (critical_events
                        .groupby(['minute', 'event', 'event_type'])
                        .size()
                        .reset_index(name='count'))

        # Filter for bursts where the count exceeds or equals 'n'
        bursts = event_counts[event_counts['count'] >= n]

        # Create a Series with 'minute' as index and 'count' as values
        bursts_series = bursts.set_index('minute')['count']

        # Save the plot using the series
        self._save_data_based_on_timestamp(
            bursts_series,  # Pass the Series instead of separate lists
            "Time",
            "Number of Critical Events in the burst",
            "Critical Event Bursts"
        )

        # Convert the result to a list of dictionaries for returning
        burst_list = bursts.rename(columns={'minute': 'timestamp'}).to_dict(orient='records')

        return burst_list

    def plot_critical_events_per_aggregation_time(self):
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



    def plot_link_up_down_count_per_aggregation_time(self):
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
