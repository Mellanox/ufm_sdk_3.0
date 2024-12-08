"""
@copyright:
    Copyright © 2013-2024 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.

    This software product is a proprietary product of Nvidia Corporation and its affiliates
    (the "Company") and all right, title, and interest in and to the
    software product, including all associated intellectual property rights,
    are and shall remain exclusively with the Company.

    This software product is governed by the End User License Agreement
    provided with the software product.

@author: Miryam Schwartz
@date:   Dec 08, 2024
"""

import unittest
import sys
import os

sys.path.append(os.getcwd())
sys.path.append("/".join(os.getcwd().split("/")[:-1]))
sys.path.append("/".join(os.getcwd().split("/")[:-1]) + "/src")

from loganalyze.log_analyzers.ibdiagnet_log_analyzer import IBDIAGNETLogAnalyzer


class TestIBDIAGNETLogAnalyzer(unittest.TestCase):
    def setUp(self):
        # Example initialization with dummy arguments
        self.logs_csvs = []
        self.hours = 24
        self.dest_image_path = "/dummy/path"
        self.analyzer = IBDIAGNETLogAnalyzer(self.logs_csvs, self.hours, self.dest_image_path)

    def test_get_fabric_size(self):
        # Mock the _log_data_sorted attribute
        expected_fabric_size = {"switch_count": 10, "link_count": 50}  # Example data
        self.analyzer._log_data_sorted = expected_fabric_size # pylint: disable=protected-access

        # Call the method and check the result
        result = self.analyzer.get_fabric_size()
        self.assertEqual(result, expected_fabric_size)

if __name__ == "__main__":
    unittest.main()
