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
from datetime import datetime
import gzip
from itertools import islice
import os
import re
import shutil
from typing import List
from pathlib import Path
import pandas as pd
from utils.netfix.link_flapping import get_link_flapping
from loganalyze.log_analyzers.base_analyzer import BaseImageCreator
import loganalyze.logger as log

FILE_NAME_PATTERN = r"^secondary_(5m|1h|1d|1w)_(\d{14})\.gz$"
TIME_PATTERN = "%Y%m%d%H%M%S"


class LinkFlappingAnalyzer(BaseImageCreator):
    def __init__(self, telemetry_samples_csv: List[str], dest_image_path: str):
        super().__init__(dest_image_path)
        self._telemetry_samples_csv = telemetry_samples_csv
        self._mapped_samples = {"5m": {}, "1h": {}, "1d": {}, "1w": {}}
        self._map_files_by_sampling_rate_and_date()
        self._funcs_for_analysis = {self.plot_link_flapping_last_week}

    def _map_files_by_sampling_rate_and_date(self):
        for sample_file in self._telemetry_samples_csv:
            try:
                file_name = os.path.basename(sample_file)
                match = re.match(FILE_NAME_PATTERN, file_name)
                if match:
                    interval_time = match.group(1)
                    date_time_str = match.group(2)

                    # Convert the date_time string to a datetime object
                    date_time = datetime.strptime(date_time_str, TIME_PATTERN)
                    self._mapped_samples[interval_time][date_time] = sample_file
                else:
                    log.LOGGER.debug(
                        f"File {file_name} cannot be used for links flapping"
                    )
            except FileNotFoundError:
                log.LOGGER.debug(f"File {sample_file} does not exist")
            except re.error:
                log.LOGGER.debug(
                    f"Invalid regular expression pattern {FILE_NAME_PATTERN}"
                )
            except ValueError:
                log.LOGGER.debug(f"Invalid date/time format {date_time_str}")
            except KeyError:
                log.LOGGER.debug(f"Invalid interval time {interval_time}")
        # Sorting the inner dict so the first item would be the last timestamp
        sorted_data = {
            key: sorted(value.items(), key=lambda x: x[0], reverse=True)
            for key, value in self._mapped_samples.items()
        }
        self._mapped_samples = {key: dict(value) for key, value in sorted_data.items()}

    def _ungz_to_csv(self, file_path):
        # Ensure the input file has a .gz extension
        if not file_path.endswith(".gz"):
            return ""

        # Create the output file path by replacing .gz with .csv
        output_file_path = f"{Path(file_path).stem}.csv"

        # Open the .gz file and write its content to a new .csv file
        with gzip.open(file_path, "rb") as f_in:
            with open(output_file_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

        return output_file_path

    def _get_link_flapping_by_gz_files(self, file1_gz, file2_gz):
        link_flapping = get_link_flapping(
            self._ungz_to_csv(file1_gz), self._ungz_to_csv(file2_gz)
        )
        columns_to_keep = ["link_hash_id", "estimated_time"]
        link_flapping = link_flapping.loc[:, columns_to_keep]
        # Drop duplicate columns
        link_flapping = link_flapping.loc[:, ~link_flapping.columns.duplicated()]
        # Reset the index and drop the old index column
        link_flapping = link_flapping.reset_index(drop=True)
        return link_flapping

    def get_link_flapping_last_week(self):
        five_m_samples = self._mapped_samples.get("5m")
        week_samples = self._mapped_samples.get("1w")
        if len(five_m_samples) <= 0 or len(week_samples) <= 0:
            return pd.DataFrame()
        latest_sample_gz = list(islice(five_m_samples.values(), 1))[0]
        older_sample_gz = list(islice(week_samples.values(), 1))[0]
        link_flapping = self._get_link_flapping_by_gz_files(
            older_sample_gz, latest_sample_gz
        )
        data_sorted = link_flapping.sort_values(by="estimated_time").reset_index(
            drop=True
        )
        return data_sorted

    def plot_link_flapping_last_week(self):
        link_flapping = self.get_link_flapping_last_week()
        # Convert "estimated_time" column to datetime object
        link_flapping["estimated_time"] = pd.to_datetime(
            link_flapping["estimated_time"]
        )
        link_flapping["aggregated_by_time"] = link_flapping["estimated_time"].dt.floor(
            self.time_interval
        )

        # Create pivot table with 'aggregated_by_time' as index and count of records as value
        pivot_table = (
            link_flapping.groupby("aggregated_by_time")
            .size()
            .reset_index(name="counts")
        )
        pivot_table["aggregated_by_time"] = pd.to_datetime(
            pivot_table["aggregated_by_time"]
        )

        # Reset index to create a new column for time intervals
        pivot_table = (
            pivot_table.set_index("aggregated_by_time")
            .rename_axis(None)
            .rename(columns={"counts": "Count"})
        )

        # Plot pivot table using _plot_and_save_pivot_data_in_bars method
        self._save_pivot_data_in_bars(
            pivot_table, "Time", "Count", "Link Flapping Count", None
        )

        # Save link_flapping in dataframes_for_pdf
        self._dataframes_for_pdf.extend([("Link Flapping last week", link_flapping)])
