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
# pylint: disable=missing-class-docstring

from typing import List
from loganalyze.log_analyzers.base_analyzer import BaseAnalyzer
import loganalyze.logger as log


class IBDIAGNETLogAnalyzer(BaseAnalyzer):
    def __init__(self, logs_csvs: List[str], hours: int, dest_image_path):
        super().__init__(logs_csvs, hours, dest_image_path, sort_timestamp=False)

    def print_fabric_size(self):
        fabric_info = self.get_fabric_size()
        log.LOGGER.info(fabric_info)

    def get_fabric_size(self):
        return self._log_data_sorted

    def full_analysis(self):
        """
        Returns a list of all the graphs created and their title
        """
        self.print_fabric_size()
        return []
