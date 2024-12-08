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

from loganalyze.log_analyzers.ufm_top_analyzer import UFMTopAnalyzer

class TestUFMTopAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = UFMTopAnalyzer()

    def test_add_analyzer(self):
        mock_analyzer_1 = "Analyzer1"
        mock_analyzer_2 = "Analyzer2"

        # Initially, the list should be empty
        self.assertEqual(len(self.analyzer._analyzers), 0) # pylint: disable=protected-access

        # Add first analyzer and check the length
        self.analyzer.add_analyzer(mock_analyzer_1)
        self.assertEqual(len(self.analyzer._analyzers), 1) # pylint: disable=protected-access
        self.assertIn(mock_analyzer_1, self.analyzer._analyzers) # pylint: disable=protected-access

        # Add second analyzer and check the updated length
        self.analyzer.add_analyzer(mock_analyzer_2)
        self.assertEqual(len(self.analyzer._analyzers), 2) # pylint: disable=protected-access
        self.assertIn(mock_analyzer_2, self.analyzer._analyzers) # pylint: disable=protected-access

if __name__ == "__main__":
    unittest.main()
