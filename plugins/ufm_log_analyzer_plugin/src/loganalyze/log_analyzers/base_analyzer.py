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
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring

import os
import csv
import shutil
import warnings
from datetime import timedelta
from typing import List
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from loganalyze.log_analyzers.constants import DataConstants
import loganalyze.logger as log

pd.set_option("display.max_colwidth", None)
warnings.filterwarnings("ignore")


class BaseImageCreator:
    # Setting the graph time interval to 1 hour
    # This is out side of the constructor since
    # It is defined once for all graphic options
    # Per call/run.

    time_interval = "h"
    _images_type = {"svg", "png"}
    X_POS_FOR_STATS = 0.05
    Y_POS_FOR_STATS = 0.95

    def __init__(self, dest_image_path):
        self._dest_image_path = dest_image_path
        self._images_created = []
        self._funcs_for_analysis = set()

    def _save_data_based_on_timestamp(
        self, data_to_plot, x_label, y_label, title
    ):
        with plt.ion():
            log.LOGGER.debug(f"saving {title}")
            plt.figure(figsize=(12, 6))
            plt.plot(data_to_plot, marker="o", linestyle="-", color="b")
            plt.title(title)
            plt.xlabel(x_label)
            plt.ylabel(y_label)
            plt.grid(True)

            # Set the locator to show ticks every hour and the formatter to
            # include both date and time
            ax = plt.gca()
            ax.xaxis.set_major_locator(mdates.HourLocator())
            ax.xaxis.set_minor_locator(
                mdates.MinuteLocator(interval=15)
            )  # Add minor ticks every 15 minutes
            ax.xaxis.set_major_formatter(
                mdates.DateFormatter("%Y-%m-%d %H:%M")
            )  # Format major ticks to show date and time

            plt.xticks(rotation=45)  # Rotate x-axis labels to make them readable
            plt.tight_layout()
            min_val = np.min(data_to_plot)
            max_val = np.max(data_to_plot)
            median_val = np.median(data_to_plot)
            plt.text(
                self.X_POS_FOR_STATS,
                self.Y_POS_FOR_STATS,
                f"Min: {min_val:.2f}\nMax: {max_val:.2f}\nMedian: {median_val:.2f}",
                transform=ax.transAxes,
                bbox={"facecolor": "white", "alpha": 0.5},
            )


            generic_file_name = f"{title}".replace(" ", "_").replace("/", "_")
            images_created = []
            for img_type in self._images_type:
                cur_img = os.path.join(self._dest_image_path,f"{generic_file_name}.{img_type}")
                log.LOGGER.debug(f"Saving {cur_img}")
                plt.savefig(cur_img, format=img_type)
                images_created.append(cur_img)
            images_list_with_title = [(image, title) for image in images_created]
            self._images_created.extend(images_list_with_title)
            plt.close()

    def _save_pivot_data_in_bars(  # pylint: disable=too-many-arguments
        self, pivoted_data, x_label, y_label, title, legend_title
    ):
        if pivoted_data.empty:
            return
        pivoted_data.plot(kind="bar", figsize=(14, 7))
        # This allows for the image to keep open when we create another one
        with plt.ion():
            log.LOGGER.debug(f"saving {title}")
            plt.title(title)
            plt.xlabel(x_label)
            plt.ylabel(y_label)
            plt.legend(title=legend_title, bbox_to_anchor=(1.05, 1), loc="upper left")
            plt.xticks(rotation=45)
            plt.tight_layout()
            generic_file_name = f"{title}".replace(" ", "_").replace("/", "_")
            images_created = []
            for img_type in self._images_type:
                cur_img = os.path.join(self._dest_image_path,f"{generic_file_name}.{img_type}")
                log.LOGGER.debug(f"Saving {cur_img}")
                plt.savefig(cur_img, format=img_type)
                images_created.append(cur_img)
            images_list_with_title = [(image, title) for image in images_created]
            self._images_created.extend(images_list_with_title)
            plt.close()

    def full_analysis(self):
        """
        Run all the analysis and returns a list of all the graphs created and their title
        """
        for func in self._funcs_for_analysis:
            try:
                func()
            except:
                function_name = func.__name__
                try:
                    class_name = ""
                    if "." in func.__qualname__:
                        class_name = func.__qualname__.split('.')[0]
                    log.LOGGER.debug(f"Error when calling {function_name} {class_name}, skipping")
                except:
                    pass

        return self._images_created if len(self._images_created) > 0 else []


class BaseAnalyzer(BaseImageCreator):
    """
    Analyzer class that gives all the logs the
    ability to print/save images and filter data
    """


    def __init__(
        self,
        logs_csvs: List[str],
        hours: int,
        dest_image_path: str,
        sort_timestamp=True

    ):
        super().__init__(dest_image_path)
        dataframes = [pd.read_csv(ufm_log) for ufm_log in logs_csvs]
        df = pd.concat(dataframes, ignore_index=True)
        if sort_timestamp:
            df[DataConstants.TIMESTAMP] = pd.to_datetime(df[DataConstants.TIMESTAMP])
            max_timestamp = df[DataConstants.TIMESTAMP].max()
            start_time = max_timestamp - timedelta(hours=hours)
            # Filter logs to include only those within the last 'hours' from the max timestamp
            filtered_logs = df[df[DataConstants.TIMESTAMP] >= start_time]
            data_sorted = filtered_logs.sort_values(by=DataConstants.TIMESTAMP)
            data_sorted[DataConstants.AGGREGATIONTIME] = \
                        data_sorted[DataConstants.TIMESTAMP].dt.floor(self.time_interval)
            self._log_data_sorted = data_sorted
        else:
            self._log_data_sorted = df
        self._images_type = {"svg", "png"}

    @staticmethod
    def _remove_empty_lines_from_csv(input_file):
        temp_file = input_file + ".temp"

        with open(input_file, "r", newline="", encoding=DataConstants.UTF8ENCODING) as infile, open(
            temp_file, "w", newline="", encoding=DataConstants.UTF8ENCODING
        ) as outfile:
            reader = csv.reader(infile)
            writer = csv.writer(outfile)

            for row in reader:
                if any(
                    field.strip() for field in row
                ):  # Check if any field in the row is non-empty
                    writer.writerow(row)

        # Replace the original file with the modified file
        shutil.move(temp_file, input_file)

    @staticmethod
    def fix_lines_with_no_timestamp(csvs):
        """
        If a line has no timestamp, we take the last arg data from it and append
        to prev line
        """
        for csv_file in csvs:
            # Create a temporary file to write the modified content
            temp_file = csv_file + ".temp"
            BaseAnalyzer._remove_empty_lines_from_csv(csv_file)
            fixed_lines = 0
            with open(csv_file, "r", newline="", encoding=DataConstants.UTF8ENCODING) \
                as infile, open(
                            temp_file, "w", newline="", encoding=DataConstants.UTF8ENCODING
                                ) as outfile:
                reader = csv.reader(infile)
                writer = csv.writer(outfile)
                current_line = None
                is_first_section = True
                for row in reader:
                    if row[0] != "":  # Lines with date
                        if current_line is not None:
                            writer.writerow(current_line)
                            is_first_section = False
                        current_line = row[:]  # Copy current row to current_line
                    elif is_first_section:  # Still starting, skip them
                        continue
                    elif row[-1].strip():  # Lines with only data
                        if current_line is not None:
                            current_line[-1] += row[
                                -1
                            ]  # Append data to the existing data
                            fixed_lines += 1
                        else:
                            raise ValueError("Unexpected line format before")

                # Write the last processed line
                if current_line is not None:
                    writer.writerow(current_line)

                # Replace the original file with the modified file
            os.replace(temp_file, csv_file)
