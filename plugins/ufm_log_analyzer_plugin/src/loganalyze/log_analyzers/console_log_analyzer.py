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
from loganalyze.log_analyzers.constants import DataConstants
from loganalyze.log_analyzers.base_analyzer import BaseAnalyzer
import loganalyze.logger as log


class ConsoleLogAnalyzer(BaseAnalyzer):
    def __init__(
        self, logs_csvs: List[str], hours: int, dest_image_path, sort_timestamp=True
    ):
        self.fix_lines_with_no_timestamp(logs_csvs)
        super().__init__(logs_csvs, hours, dest_image_path, sort_timestamp)
        self._log_data_sorted.dropna(subset=["data"], inplace=True)

    def _get_exceptions(self):
        error_data = self._log_data_sorted[self._log_data_sorted["type"] == "Error"][
            [DataConstants.TIMESTAMP, "data"]
        ]
        return error_data

    def get_all_exceptions_to_print(self):
        error_data = self._get_exceptions()
        if error_data.empty:
            return "No exceptions"
        result_string = " ".join(
            error_data.apply(lambda row: f"{row[0]} {row[1]}\n", axis=1)
        )
        return result_string

    def print_exceptions(self):
        error_data = self._get_exceptions()
        if error_data.empty:
            log.LOGGER.info("No Errors to print")
            return
        log.LOGGER.debug("The following exceptions were found in console log")
        for _, row in error_data.iterrows():
            log.LOGGER.debug(f"Timestamp: {row['timestamp']}: {row['data']}")

    def print_exceptions_per_time_count(self):
        error_data = self._log_data_sorted[self._log_data_sorted["type"] == "Error"]
        errors_per_hour = error_data.groupby(DataConstants.AGGREGATIONTIME).size()
        images_created = self._plot_and_save_data_based_on_timestamp(
            errors_per_hour,
            "Time",
            "Amount of exceptions",
            "Exceptions count",
        )
        return images_created

    def full_analysis(self):
        """
        Returns a list of all the graphs created and their title
        """
        created_images = self.print_exceptions_per_time_count()
        self.print_exceptions()
        return created_images if len(created_images) > 0 else []
