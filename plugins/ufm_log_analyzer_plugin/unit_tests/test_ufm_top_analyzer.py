# @copyright:
#     Copyright © 2013-2024 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.

#     This software product is a proprietary product of Nvidia Corporation and its affiliates
#     (the "Company") and all right, title, and interest in and to the
#     software product, including all associated intellectual property rights,
#     are and shall remain exclusively with the Company.

#     This software product is governed by the End User License Agreement
#     provided with the software product.

# @author: Miryam Schwartz
# @date:   Dec 08, 2024

import pytest
import sys
import os

sys.path.append(os.getcwd())
sys.path.append("/".join(os.getcwd().split("/")[:-1]))
sys.path.append("/".join(os.getcwd().split("/")[:-1]) + "/src")

from loganalyze.log_analyzers.ufm_top_analyzer import UFMTopAnalyzer

@pytest.fixture
def analyzer():
    # Fixture to initialize the analyzer object
    return UFMTopAnalyzer()

def test_add_analyzer(analyzer):
    mock_analyzer_1 = "Analyzer1"
    mock_analyzer_2 = "Analyzer2"

    # Initially, the list should be empty
    assert len(analyzer._analyzers) == 0

    # Add first analyzer and check the length
    analyzer.add_analyzer(mock_analyzer_1)
    assert len(analyzer._analyzers) == 1
    assert mock_analyzer_1 in analyzer._analyzers

    # Add second analyzer and check the updated length
    analyzer.add_analyzer(mock_analyzer_2)
    assert len(analyzer._analyzers) == 2
    assert mock_analyzer_2 in analyzer._analyzers
