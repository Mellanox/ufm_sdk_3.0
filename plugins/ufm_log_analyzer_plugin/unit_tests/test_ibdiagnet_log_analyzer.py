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

from loganalyze.log_analyzers.ibdiagnet_log_analyzer import IBDIAGNETLogAnalyzer

# Define a test-specific subclass
class TestIBDIAGNETLogAnalyzer(IBDIAGNETLogAnalyzer):
    def __init__(self, fabric_size_data):
        # Do not call the parent constructor, set up only what's needed for the test
        self._log_data_sorted = fabric_size_data

@pytest.fixture
def fabric_size_data():
    # Shared mock data
    return {"switch_count": 10, "link_count": 50}

@pytest.fixture
def analyzer(fabric_size_data):
    # Return an instance of the test-specific subclass
    return TestIBDIAGNETLogAnalyzer(fabric_size_data)

def test_get_fabric_size(analyzer, fabric_size_data):
    # Call the method and check the result
    result = analyzer.get_fabric_size()
    assert result == fabric_size_data, "get_fabric_size should return _log_data_sorted"
