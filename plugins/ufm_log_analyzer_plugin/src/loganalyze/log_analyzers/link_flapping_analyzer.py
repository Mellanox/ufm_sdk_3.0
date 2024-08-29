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
from typing import List
from loganalyze.log_analyzers.base_analyzer import BaseAnalyzer

class LinkFlappingAnalyzer(BaseAnalyzer):
    def __init__(self, csvs: List[str], hours: int, dest_image_path: str, sort_timestamp=True):
        super().__init__(csvs, hours, dest_image_path, sort_timestamp)
    