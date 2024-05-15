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

#import pytest
from plugins.pdr_deterministic_plugin.ufm_sim_web_service.constants import PDRConstants as Constants
from plugins.pdr_deterministic_plugin.ufm_sim_web_service.exclude_list import ExcludeList
from plugins.pdr_deterministic_plugin.ufm_sim_web_service.isolation_algo import create_logger

def test_get_from_empty_exclude_list():
    """
    Create exclude list and ensure its empty via its method
    """
    logger = create_logger(Constants.LOG_FILE)
    exclude_list = ExcludeList(logger)
    items = exclude_list.items()
    assert not items
