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
from pathlib import Path


class BaseExtractor:
    def is_exists_get_as_path(self, location) -> Path:
        """
        Checks if location exists and is from the right type
        Returns the location is path object and it's father, else
        returns None
        """
        if isinstance(location, str):
            location = Path(location)
        if location.exists():
            return location
        return None
