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
# pylint: disable=broad-exception-caught
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
import os
import csv
from typing import List, Tuple
import logger as log

class CsvHandler:
    def __init__(
        self,
        csv_headers: List[str],
        dest_csv_path: str,
        num_of_line_to_keep_in_mem=20000,
    ):
        self._num_of_items_per_row = len(csv_headers)
        self._csv_headers = csv_headers
        self._dest_csv_path = dest_csv_path
        self._lines_to_add_in_csv = []
        self._num_of_line_to_keep_in_mem = num_of_line_to_keep_in_mem
        # Creating the dest CSV
        csv_directory = os.path.dirname(self._dest_csv_path)
        os.makedirs(csv_directory, exist_ok=True)
        # If file exists, delete it and replace with empty one that has only headers
        with open(self._dest_csv_path, "w", newline="", encoding="utf-8") as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(self._csv_headers)

    def add_line(self, line: Tuple):
        if len(line) != self._num_of_items_per_row:
            raise AttributeError(
                f"Wrong number of items passed to add_line, "
                f"got {len(line)} vs {self._num_of_items_per_row}"
            )
        self._lines_to_add_in_csv.append(line)
        if len(self._lines_to_add_in_csv) > self._num_of_line_to_keep_in_mem:
            self.save_file()

    def save_file(self):
        try:
            with open(
                self._dest_csv_path, "a", newline="", encoding="utf-8"
            ) as csv_file:
                csv_writer = csv.writer(csv_file)
                csv_writer.writerows(self._lines_to_add_in_csv)
                self._lines_to_add_in_csv = []
        except Exception as e:
            log.LOGGER.error(f"Error when trying to save to {self._dest_csv_path}, {e}")
