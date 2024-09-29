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
# pylint: disable=too-many-locals
# pylint: disable=missing-function-docstring
# pylint: disable=useless-parent-delegation
# pylint: disable=missing-class-docstring
# pylint: disable=missing-module-docstring

from typing import List
import pandas as pd
from log_analyzers.constants import DataConstants
from log_analyzers.base_analyzer import BaseAnalyzer
import logger as log


class UFMLogAnalyzer(BaseAnalyzer):
    def __init__(self, logs_csvs: List[str], hours: int, dest_image_path):
        super().__init__(logs_csvs, hours, dest_image_path)
        self._funcs_for_analysis = {self.full_analyze_ufm_loading_time,
                                    self.full_telemetry_processing_time_report,
                                    self.full_analyze_fabric_analysis_time}

    def full_analyze_ufm_loading_time(self):
        ufm_started_logs = self._log_data_sorted[
            self._log_data_sorted["log_type"] == "ufm_started"
        ]
        ufm_init_done_logs = self._log_data_sorted[
            self._log_data_sorted["log_type"] == "ufm_init_done"
        ]

        max_time_window = pd.Timedelta(
            minutes=30
        )  # Set maximum time window for matching

        missing_completed_logs = []
        matched_logs = []

        for _, start_log in ufm_started_logs.iterrows():
            start_time = start_log[DataConstants.TIMESTAMP]
            possible_matches = ufm_init_done_logs[
                ufm_init_done_logs[DataConstants.TIMESTAMP] > start_time
            ]
            if not possible_matches.empty:
                end_time = possible_matches[
                    DataConstants.TIMESTAMP
                ].min()  # Find the earliest 'ufm_init_done' log after 'start_time'
                time_diff = end_time - start_time
                if time_diff <= max_time_window:
                    matched_logs.append(
                        {"timestamp_start": start_time, "timestamp_end": end_time}
                    )
                    ufm_init_done_logs = ufm_init_done_logs[
                        ufm_init_done_logs[DataConstants.TIMESTAMP] > end_time
                    ]  # Remove matched log
                else:
                    missing_completed_logs.append(start_time)
            else:
                missing_completed_logs.append(start_time)

        matched_logs_df = pd.DataFrame(matched_logs)

        if not matched_logs_df.empty:
            matched_logs_df["time_diff"] = (
                matched_logs_df["timestamp_end"] - matched_logs_df["timestamp_start"]
            ).dt.total_seconds()

            # Calculate statistics
            mean_time = matched_logs_df["time_diff"].mean()
            max_time = matched_logs_df["time_diff"].max()
            min_time = matched_logs_df["time_diff"].min()

            max_time_occurrence = matched_logs_df.loc[
                matched_logs_df["time_diff"] == max_time, "timestamp_end"
            ].iloc[0]
            min_time_occurrence = matched_logs_df.loc[
                matched_logs_df["time_diff"] == min_time, "timestamp_end"
            ].iloc[0]

            # Print statistics
            log.LOGGER.debug(f"Mean Time: {mean_time:.2f} seconds")
            log.LOGGER.debug(f"Maximum Time: {max_time:.2f} seconds at {max_time_occurrence}")
            log.LOGGER.debug(f"Minimum Time: {min_time:.2f} seconds at {min_time_occurrence}")

        # Print timestamps with missing 'Completed' logs
        if len(missing_completed_logs) > 0:
            log.LOGGER.debug("\nTimestamps with missing 'Completed' logs:")
            for timestamp_start in missing_completed_logs:
                log.LOGGER.debug(f"timestamp_start: {timestamp_start}")
        # Plot the results with scatter plot
        if not matched_logs_df.empty:
            matched_logs_df.drop(columns=["timestamp_end"], inplace=True)
            matched_logs_df.set_index("timestamp_start", inplace=True)
            self._save_data_based_on_timestamp(
                matched_logs_df,
                DataConstants.TIMESTAMP,
                "Loading time Time (seconds)",
                "UFM loading time",
            )

    def full_analyze_fabric_analysis_time(self):
        # Filter by 'fabric_analysis' log_type and the timestamp range
        fabric_logs = self._log_data_sorted[
            (self._log_data_sorted["log_type"] == "fabric_analysis")
        ]
        fabric_logs.sort_values(by=DataConstants.TIMESTAMP, inplace=True)
        fabric_logs.reset_index(drop=True, inplace=True)  # Reset index after sorting
        merged_logs = pd.DataFrame(
            columns=[
                "timestamp_start",
                "timestamp_end",
                "report_id",
                "original_start_time",
            ]
        )
        reports_with_no_ending = []

        i = 0
        fabric_logs_size = len(fabric_logs)
        to_concat = []
        while i < fabric_logs_size:
            row = fabric_logs.iloc[i]

            if row[DataConstants.DATA] == "Starting":
                report_id = str(
                    int(row["extra_info"])
                )  # This is to fix an issue where some of the reports are with .0
                start_time = row[DataConstants.TIMESTAMP]

                # Find the next log entry for the current start log
                j = i + 1
                while j < fabric_logs_size:
                    next_row = fabric_logs.iloc[j]
                    next_row_report_id = str(int(next_row["extra_info"]))
                    if (
                        next_row[DataConstants.DATA] == "Starting"
                        and next_row_report_id <= report_id
                    ):
                        # If the next row is another start with the same report_id,
                        # treat the current start as having no ending
                        reports_with_no_ending.append((report_id, start_time))
                    elif (
                        next_row[DataConstants.DATA] == "Completed"
                        and next_row_report_id == report_id
                        and next_row[DataConstants.TIMESTAMP] > start_time
                    ):
                        end_time = next_row[DataConstants.TIMESTAMP]
                        new_row = {
                            "timestamp_start": start_time,
                            "timestamp_end": end_time,
                            "report_id": report_id,
                            "original_start_time": start_time,  # Save the original start time
                        }
                        to_concat.append(new_row)
                        break  # Exit the loop for current start log

                    j += 1

                # If no completion found, add to reports_with_no_ending
                if j == fabric_logs_size:
                    reports_with_no_ending.append((report_id, start_time))

            i += 1
        merged_logs = pd.concat(
            [merged_logs] + [pd.DataFrame(to_concat)], ignore_index=True
        )

        # Ensure merged_logs is not empty before further operations
        if not merged_logs.empty:
            # Calculate the time difference in seconds for valid merged logs
            merged_logs["time_diff"] = (
                merged_logs["timestamp_end"] - merged_logs["timestamp_start"]
            ).dt.total_seconds()

            # Statistics
            mean_time = merged_logs["time_diff"].mean()
            max_time = merged_logs["time_diff"].max()
            min_time = merged_logs["time_diff"].min()

            # Use the original_start_time for finding occurrences
            max_time_occurrence = merged_logs.loc[
                merged_logs["time_diff"] == max_time, "original_start_time"
            ].iloc[0]
            min_time_occurrence = merged_logs.loc[
                merged_logs["time_diff"] == min_time, "original_start_time"
            ].iloc[0]

            log.LOGGER.debug(f"Mean Time: {mean_time:.3f} seconds")
            log.LOGGER.debug(
                f"Maximum Time: {max_time:.3f} seconds starting at {max_time_occurrence}"
            )
            log.LOGGER.debug(
                f"Minimum Time: {min_time:.3f} seconds starting at {min_time_occurrence}"
            )

            # Reports with no ending
            if reports_with_no_ending:
                amount = len(reports_with_no_ending)
                log.LOGGER.debug(
                    f"There are {amount} fabric analysis reports that started but did not end"
                )
            # Plotting
            merged_logs.drop(
                columns=["timestamp_end", "report_id", "original_start_time"],
                inplace=True,
            )
            merged_logs.set_index("timestamp_start", inplace=True)
            title = "Fabric analysis run time"
            self._save_data_based_on_timestamp(
                merged_logs, "Time", "Processing Time (s)", title
            )

    def full_telemetry_processing_time_report(self):
        # Further filter to only telemetry processing time logs
        telemetry_logs = self._log_data_sorted[
            self._log_data_sorted["log_type"] == "telemetry_processing_time"
        ]

        # Sort the telemetry logs by timestamp
        telemetry_logs_sorted = telemetry_logs.sort_values(by=DataConstants.TIMESTAMP).copy()

        # Extract the processing time and convert to float
        telemetry_logs_sorted["processing_time"] = (
            telemetry_logs_sorted[DataConstants.DATA].str.extract(r"(\d+(\.\d+)?)")[0].astype(float)
        )

        # Calculate statistics
        mean_time = telemetry_logs_sorted["processing_time"].mean()
        max_time = telemetry_logs_sorted["processing_time"].max()
        min_time = telemetry_logs_sorted["processing_time"].min()

        # Find the occurrences of the max and min processing times
        max_time_row = telemetry_logs_sorted[
            telemetry_logs_sorted["processing_time"] == max_time
        ]
        min_time_row = telemetry_logs_sorted[
            telemetry_logs_sorted["processing_time"] == min_time
        ]

        max_time_occurrence = max_time_row[DataConstants.TIMESTAMP].iloc[0]
        min_time_occurrence = min_time_row[DataConstants.TIMESTAMP].iloc[0]

        # Print the statistics
        log.LOGGER.debug(f"Mean Processing Time: {mean_time}")
        log.LOGGER.debug(f"Maximum Processing Time: {max_time} at {max_time_occurrence}")
        log.LOGGER.debug(f"Minimum Processing Time: {min_time} at {min_time_occurrence}")

        # Set the index to timestamp for resampling, converting to DateTimeIndex
        telemetry_logs_sorted[DataConstants.TIMESTAMP] = pd.to_datetime(
            telemetry_logs_sorted[DataConstants.TIMESTAMP]
        )
        telemetry_logs_sorted.set_index(DataConstants.TIMESTAMP, inplace=True)

        # Resample to minute-wise mean processing time
        minutely_mean_processing_time = (
            telemetry_logs_sorted["processing_time"].resample("min").mean()
        )

        # Drop any NaN values that may have resulted from resampling
        minutely_mean_processing_time.dropna(inplace=True)

        # Plot the data within the filtered time range
        title = "Telemetry processing time"
        self._save_data_based_on_timestamp(
            minutely_mean_processing_time,
            "Time",
            "Processing Time (s)",
            title
        )
