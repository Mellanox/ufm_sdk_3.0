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
import csv
import os
from typing import List
from loganalyze.log_analyzers.constants import DataConstants
from loganalyze.log_analyzers.base_analyzer import BaseAnalyzer
import loganalyze.logger as log


class ConsoleLogAnalyzer(BaseAnalyzer):
    def __init__(
        self, logs_csvs: List[str], hours: int, dest_image_path, sort_timestamp=True
    ):
        self.ufm_versions = self._extract_ufm_version(logs_csvs)
        self.fix_lines_with_no_timestamp(logs_csvs)
        super().__init__(logs_csvs, hours, dest_image_path, sort_timestamp)
        self._log_data_sorted.dropna(subset=["data"], inplace=True)
        self._funcs_for_analysis = {
            self.print_exceptions_per_time_count,
            self.save_ufm_versions,
        }

    @staticmethod
    def _extract_ufm_version(logs_csvs):
        """
        This function gets all the ufm version from the console log.
        It saves then in a set and returns all the unique UFM version
        that were found in the log
        """
        ufm_versions = set()  # List to store ufm_version rows

        for csv_file in logs_csvs:
            temp_file = csv_file + ".temp"

            # Open the input CSV file for reading
            with (
                open(
                    csv_file, mode="r", newline="", encoding=DataConstants.UTF8ENCODING
                ) as infile,
                open(
                    temp_file, mode="w", newline="", encoding=DataConstants.UTF8ENCODING
                ) as outfile,
            ):
                reader = csv.DictReader(infile)
                fieldnames = reader.fieldnames  # Get the header from the CSV
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)

                # Write the header to the new CSV
                writer.writeheader()

                # Iterate through each row in the input CSV
                for row in reader:
                    if row["type"] == "ufm_version":
                        # If the type is 'ufm_version',
                        # save the row and don't write it to the new file
                        ufm_versions.add(row["data"])
                    else:
                        # Write the row to the new CSV file
                        writer.writerow(row)

            # Replace the original file with the new file
            os.replace(temp_file, csv_file)
        return ufm_versions

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
        self._save_data_based_on_timestamp(
            errors_per_hour,
            "Time",
            "Amount of exceptions",
            "Exceptions count",
    )

    def save_ufm_versions(self):
        self._txt_for_pdf.append(
            f"Used ufm version in console log {self.ufm_versions}{os.linesep}"
        )

    def full_analysis(self):
        super().full_analysis()
        self.print_exceptions()
