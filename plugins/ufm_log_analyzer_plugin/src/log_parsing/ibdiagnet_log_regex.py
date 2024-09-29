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

import re
from typing import Match

from log_parsing.base_regex import RegexAndHandlers

IBDIAGNET_LOG_TOTAL_NODES = re.compile(
    #                   Num Nodes
    r"^Total Nodes +\: (\d+)$"
)

IBDIAGNET_LOG_IB_DATA = re.compile(
    #                           type                                result number
    r"^IB (Switches|Channel Adapters|Aggregation Nodes|Routers) +\: (\d+)"
)


IBDIAGNET_LOG_HEADERS = ("type", "amount")


def ibdiagnet_log_total_nodes(match: Match):
    num_nodes = match.group(1)
    return ("total_nodes", num_nodes)


def ibdiagnet_log_ib_data(match: Match):
    # This is to make sure we do not write white space to the CSV
    ib_type = f"ib_{match.group(1).replace(' ', '_')}"
    num = match.group(2)
    return (ib_type, num)


ibdiagnet_log_regex_cls = RegexAndHandlers("ibdiagnet2.log", IBDIAGNET_LOG_HEADERS)

ibdiagnet_log_regex_cls.add_regex(IBDIAGNET_LOG_TOTAL_NODES, ibdiagnet_log_total_nodes)
ibdiagnet_log_regex_cls.add_regex(IBDIAGNET_LOG_IB_DATA, ibdiagnet_log_ib_data)
