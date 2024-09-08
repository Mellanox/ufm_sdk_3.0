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
# pylint: disable=missing-class-docstring
# pylint: disable=missing-module-docstring
from typing import List
from loganalyze.log_analyzers.constants import DataConstants
from loganalyze.log_analyzers.base_analyzer import BaseAnalyzer
import loganalyze.logger as log


class UFMHealthAnalyzer(BaseAnalyzer):
    def __init__(self, logs_csvs: List[str], hours: int, dest_image_path):
        self.fix_lines_with_no_timestamp(logs_csvs)
        super().__init__(logs_csvs, hours, dest_image_path)
        self._failed_tests_data = self._log_data_sorted[
            self._log_data_sorted["test_status"] != "succeeded"
        ]

    def top_failed_tests_during_dates(self):
        data = (
            self._failed_tests_data.groupby(["test_class", "test_name", "reason"])
            .size()
            .reset_index(name="count")
            .sort_values(by="count", ascending=False)
            .head()
        )
        log.LOGGER.debug(data)

    def full_analyze_failed_tests(self):
        data = (
            self._log_data_sorted.groupby(["test_name"])
            .size()
            .reset_index(name="count")
            .sort_values(by="count", ascending=False)
        )

        log.LOGGER.debug(data)

    def print_failed_tests_per_hour(self):
        grouped_failed_by_time = (
            self._failed_tests_data.groupby([DataConstants.AGGREGATIONTIME, "test_name"])
            .size()
            .reset_index(name="count")
        )
        # Filter out the AlwaysFailTest test
        grouped_failed_only_relevant_by_time = grouped_failed_by_time[
            grouped_failed_by_time["test_name"] != "AlwaysFailTest"
        ]
        pivot_failed_by_time = grouped_failed_only_relevant_by_time.pivot(
            index=DataConstants.AGGREGATIONTIME, columns="test_name", values="count"
        ).fillna(0)
        graph_images = self._save_pivot_data_in_bars(
            pivot_failed_by_time,
            "Time",
            "Number of failures",
            "UFM Health failed tests",
            "test_name",
        )
        return graph_images

    def full_analysis(self):
        """
        Returns a list of all the graphs created and their title
        """
        created_images = self.print_failed_tests_per_hour()
        return created_images if len(created_images) > 0 else []
