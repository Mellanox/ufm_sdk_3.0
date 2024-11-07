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
from pathlib import Path
from abc import abstractmethod
from typing import List, Set


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

    @staticmethod
    def _split_based_on_dir(files:Set[str]):
        single_name_logs = set()
        logs_with_dirs = {}
        for log_name in files:
            dir_name = os.path.dirname(log_name)
            base_name = os.path.basename(log_name)
            if dir_name:
                if dir_name not in logs_with_dirs:
                    logs_with_dirs[dir_name] = set()
                logs_with_dirs[dir_name].add(base_name)
            else:
                single_name_logs.add(base_name)
        return single_name_logs, logs_with_dirs

    @abstractmethod
    def extract_files(self, files_to_extract: List[str],
                      directories_to_extract: List[str],
                      destination: str):
        pass
