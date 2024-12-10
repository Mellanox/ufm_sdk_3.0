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
from unittest.mock import MagicMock

from loganalyze.log_analyzers.ibdiagnet_log_analyzer import IBDIAGNETLogAnalyzer


@pytest.fixture
def analyzer(fabric_size_data):
    # Mock the constructor of IBDIAGNETLogAnalyzer
    mock_analyzer = MagicMock(spec=IBDIAGNETLogAnalyzer)

    # Mock the _log_data_sorted attribute
    mock_analyzer._log_data_sorted = fabric_size_data

    # Mock the get_fabric_size method to return the _log_data_sorted attribute
    mock_analyzer.get_fabric_size.return_value = fabric_size_data

    # Return the mocked analyzer instance
    return mock_analyzer

@pytest.fixture
def fabric_size_data():
    # Shared mock data
    return {"switch_count": 10, "link_count": 50}

def test_get_fabric_size(analyzer, fabric_size_data):
    # Call the method and check the result
    result = analyzer.get_fabric_size()
    assert result == fabric_size_data, "get_fabric_size should return _log_data_sorted"