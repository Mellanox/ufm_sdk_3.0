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

from typing import List
import warnings
import pandas as pd
from loganalyze.log_analyzers.base_analyzer import BaseAnalyzer


class Ibdiagnet2PortCountersAnalyzer(BaseAnalyzer):
    def __init__(
        self,
        logs_csvs: List[str],
        hours: int,
        dest_image_path: str,
        sort_timestamp=False,
    ):
        super().__init__(logs_csvs, hours, dest_image_path, sort_timestamp)
        self._iteration_time_data = None
        self._iteration_time_stats = None
        self.text_to_show_in_pdf = ""
        # This will make sure all the extra columns are int
        extra_columns = ["extra1", "extra2", "extra3", "extra4", "extra5"]
        for col in extra_columns:
            self._log_data_sorted[col] = pd.to_numeric(
                self._log_data_sorted[col], errors="coerce"
            ).astype("Int64")
        self._funcs_for_analysis = {
            self.plot_iteration_time_over_time,
            self.save_last_iterations_time_stats,
            self.save_first_last_iteration_timestamp,
            self.save_number_of_switches_and_ports,
            self.save_number_of_core_dumps,
            self.save_collectx_versions,
        }

        # Based on the log path, decided if this is primary or secondary
        if "ufm_logs" in logs_csvs[0]:
            self.telemetry_type = "primary"
        elif "secondary_telemetry" in logs_csvs[0]:
            self.telemetry_type = "secondary"
        else:
            self.telemetry_type = "Unknown_telemetry_type"

        self._first_timestamp_of_logs = None
        self._last_timestamp_of_logs = None

    def save_collectx_versions(self):
        unique_collectx_versions = self._log_data_sorted[
            self._log_data_sorted["type"] == "collectx_version"
        ]["data"].unique()
        self._txt_for_pdf.append(
            f"collectx versions found in {self.telemetry_type} telemetry log \
                {set(unique_collectx_versions)}"
        )

    def save_number_of_switches_and_ports(self):
        """
        Generate summary statistics for 'total_devices_ports' data.
        This function calculates the average, maximum, minimum
        for switches, CAs, routers, and ports.
        """
        filtered_data = self._log_data_sorted[
            self._log_data_sorted["type"] == "total_devices_ports"
        ]

        ports_numbers_columns = ["extra1", "extra3", "extra5"]
        filtered_data["extra135"] = (
            pd.to_numeric(filtered_data[ports_numbers_columns].stack(), errors="coerce")
            .groupby(level=0)
            .sum(min_count=1)
        )

        columns_of_interest = ["data", "extra2", "extra4", "extra135"]
        column_mapping = {
            "data": "# of Switches",
            "extra2": "CAs",
            "extra4": "Routers",
            "extra135": "Ports",
        }

        summary_stats = []

        for col in columns_of_interest:
            numeric_col = pd.to_numeric(filtered_data[col], errors="coerce")
            non_zero_col = numeric_col[numeric_col != 0]

            avg = round(non_zero_col.mean()) if not non_zero_col.empty else 0
            max_val = int(non_zero_col.max()) if not non_zero_col.empty else 0
            min_val = int(non_zero_col.min()) if not non_zero_col.empty else 0
            count = int(non_zero_col.count())

            summary_stats.append(
                {
                    "Category": column_mapping.get(col, col),
                    "Average": avg,
                    "Maximum": max_val,
                    "Minimum": min_val,
                    "Total Rows (Non-Zero)": count,
                }
            )

        summary_df = pd.DataFrame(summary_stats)

        self._dataframes_for_pdf.append(
            (
                f"{self.telemetry_type} telemetry fabric size",
                summary_df,
            )
        )

    def analyze_iteration_time(self, threshold=0.15):
        """
        Analyze rows where 'type' is 'iteration_time'.
        Keep only 'type', 'timestamp', and 'data' columns.
        Calculate statistics for the 'data' column, including timestamps for max and min.
        Also, find gaps of at least 2 minutes with no data and allow filtering by a threshold.

        Parameters:
        - threshold (float): Minimum value to consider for analysis. Default is 0.5 seconds.
        """
        filtered_data = self._log_data_sorted[
            self._log_data_sorted["type"] == "iteration_time"
        ]
        filtered_data = filtered_data[["type", "timestamp", "data"]]
        filtered_data["data"] = pd.to_numeric(filtered_data["data"], errors="coerce")

        if self.telemetry_type == "primary":
            filtered_data = filtered_data[filtered_data["data"] >= threshold]
        filtered_data["timestamp"] = pd.to_datetime(
            filtered_data["timestamp"], errors="coerce"
        )
        filtered_data = filtered_data.dropna(subset=["timestamp"])

        filtered_data = filtered_data.sort_values(by="timestamp").reset_index(drop=True)

        if not filtered_data["data"].empty:
            average = filtered_data["data"].mean()
            max_value = filtered_data["data"].max()
            min_value = filtered_data["data"].min()

            max_timestamp = filtered_data.loc[
                filtered_data["data"] == max_value, "timestamp"
            ].iloc[0]
            min_timestamp = filtered_data.loc[
                filtered_data["data"] == min_value, "timestamp"
            ].iloc[0]
            first_timestamp = filtered_data["timestamp"].iloc[0]
            last_timestamp = filtered_data["timestamp"].iloc[-1]

        else:
            average = max_value = min_value = 0.0
            max_timestamp = min_timestamp = None
            first_timestamp = last_timestamp = None

        stats = {
            "Average": average,
            "Maximum": max_value,
            "Max Timestamp": max_timestamp,
            "Minimum": min_value,
            "Min Timestamp": min_timestamp,
            "Total Rows": filtered_data["data"].count(),
        }
        stats_df = pd.DataFrame([stats])
        self._iteration_time_data = filtered_data
        self._iteration_time_stats = stats_df
        self._first_timestamp_of_logs = first_timestamp
        self._last_timestamp_of_logs = last_timestamp
        return stats_df

    def save_first_last_iteration_timestamp(self):
        if not self._first_timestamp_of_logs or not self._last_timestamp_of_logs:
            self.analyze_iteration_time()
        times = {
            "first": str(self._first_timestamp_of_logs),
            "last": str(self._last_timestamp_of_logs),
        }
        first_last_it = pd.DataFrame([times])
        self._dataframes_for_pdf.append(
            (
                f"{self.telemetry_type} "
                "telemetry iteration first and last timestamps",
                first_last_it,
            )
        )

    def save_last_iterations_time_stats(self):
        self._dataframes_for_pdf.append(
            (
                f"{self.telemetry_type} telemetry iteration time",
                self._iteration_time_stats(),
            )
        )

    def plot_iteration_time_over_time(self):
        if self._iteration_time_data is None:
            self.analyze_iteration_time()

        self._iteration_time_data.set_index("timestamp", inplace=True)

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", ".*Locator attempting to generate.*")
            self._save_data_based_on_timestamp(
                data_to_plot=self._iteration_time_data["data"],
                x_label="Timestamp",
                y_label="Iteration Time (s)",
                title=f"{self.telemetry_type} Iteration Time",
                large_sample=True,
            )

    def save_number_of_core_dumps(self):
        core_dumps = self._log_data_sorted[
            self._log_data_sorted["type"] == "timeout_dump_core"
        ]
        num = {"Amount": len(core_dumps)}
        self._lists_for_pdf.append(
            (
                [num],
                f"{self.telemetry_type} number of core dumps found in the logs",
                ["Amount"],
            )
        )
