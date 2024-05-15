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

import os
import tempfile

#import pytest
from constants import PDRConstants as Constants
from exclude_list import ExcludeList
from isolation_algo import create_logger

def test_get_from_empty_exclude_list():
    """
    Create exclude list and ensure its empty via its method
    """
    print("Test 5")

    filename = os.path.basename(Constants.LOG_FILE)
    lod_file = os.path.join(tempfile.gettempdir(), filename)

    logger = create_logger(lod_file)
    exclude_list = ExcludeList(logger)
    items = exclude_list.items()
    assert not items

if __name__ == '__main__':
    test_get_from_empty_exclude_list()
