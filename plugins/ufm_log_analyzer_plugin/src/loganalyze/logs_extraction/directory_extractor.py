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
import shutil
from typing import List
from loganalyze.logs_extraction.base_extractor import BaseExtractor

class DirectoryExtractor(BaseExtractor):
    def __init__(self, dir_path:Path):
        dir_path = self.is_exists_get_as_path(dir_path)
        if dir_path and dir_path.is_dir():
            self.dir_path = dir_path
        else:
            raise FileNotFoundError(f"Could not use {dir_path}, "
                                    "make sure it exists and is a directory")

    def extract_files(self, files_to_extract: List[str],
                      directories_to_extract: List[str],
                      destination: str):
        if not os.path.exists(destination):
            os.makedirs(destination)

        files_to_extract = set(files_to_extract)
        directories_to_extract = set(directories_to_extract)
        found_files = set()
        not_found_files = set(files_to_extract)
        _, logs_with_dirs = self._split_based_on_dir(files_to_extract)

        for root, _, files in os.walk(self.dir_path):
            for file_name in files:
                full_dir_name = os.path.dirname(file_name)
                last_dir_name = os.path.basename(full_dir_name)
                is_logs_with_dir_flag = last_dir_name in logs_with_dirs and file_name in logs_with_dirs[last_dir_name]
                if file_name in files_to_extract or last_dir_name in directories_to_extract or\
                    is_logs_with_dir_flag:
                    src_file_path = os.path.join(root, file_name)
                    new_file_name = f"{last_dir_name}_{file_name}" if is_logs_with_dir_flag else file_name
                    dest_file_path = os.path.join(destination, new_file_name)
                    shutil.copy2(src_file_path, dest_file_path)
                    found_files.add(dest_file_path)
                    not_found_files.discard(file_name)

        return found_files, not_found_files
