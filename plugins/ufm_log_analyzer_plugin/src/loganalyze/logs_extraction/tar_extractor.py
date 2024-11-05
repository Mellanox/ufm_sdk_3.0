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
# pylint: disable=broad-exception-caught
# pylint: disable=missing-class-docstring
# pylint: disable=missing-module-docstring
from pathlib import Path
from tarfile import TarFile
import tarfile
import os
from typing import List, Set, Tuple

from loganalyze.logs_extraction.base_extractor import BaseExtractor
from loganalyze.utils.common import delete_folders
import loganalyze.logger as log

LOGS_GZ_POSTFIX = ".gz"
GZIP_MAGIC_NUMBER = b"\x1f\x8b"  # Magic number to understand if a file is really a gzip

class DumpFilesExtractor(BaseExtractor):
    def __init__(self, dump_path: Path) -> None:
        dump_path = self.is_exists_get_as_path(dump_path)
        if dump_path and dump_path.is_file():
            self.dump_path = dump_path
            self.directory = dump_path.parent
        else:
            raise FileNotFoundError(f"Could not use {dump_path}, make sure it exists and a tar")
    
    def _get_files_from_tar(
        self, opened_file: TarFile,
        files_to_extract: Set[str],
        directories_to_extract:Set[str],
        destination: str
    ):
        files_went_over = set()
        failed_extract = set()
        folders_to_remove = set()
        single_log_name, logs_with_dirs = self._split_based_on_dir(files_to_extract)
        for member in opened_file:
            base_name = os.path.basename(member.name)
            full_dir_path = os.path.dirname(member.name)
            parent_dir_name = os.path.basename(full_dir_path)
            original_base_name = base_name
            is_logs_with_dir_flag = parent_dir_name in logs_with_dirs and base_name in logs_with_dirs[parent_dir_name]
            if base_name in single_log_name or \
                parent_dir_name in directories_to_extract or \
                is_logs_with_dir_flag:
                try:
                    if is_logs_with_dir_flag:
                        base_name = f"{parent_dir_name}_{base_name}"
                    opened_file.extract(member, path=destination)
                    extracted_file_path = os.path.join(destination, str(member.path))
                    log.LOGGER.debug(f"Extracted {base_name}")
                    os.rename(extracted_file_path, os.path.join(destination, base_name))
                    folder_to_remove = os.path.dirname(extracted_file_path)
                    folders_to_remove.add(folder_to_remove)
                except Exception as e:
                    log.LOGGER.debug(f"Failed to extract {base_name}, {e}")
                    failed_extract.add(base_name)
                finally:
                    files_went_over.add(base_name)
                    if base_name in files_to_extract:
                        files_to_extract.remove(base_name)
                    elif is_logs_with_dir_flag:
                        logs_with_dirs[parent_dir_name].discard(original_base_name)
                        if len(logs_with_dirs[parent_dir_name]) == 0:
                            del logs_with_dirs[parent_dir_name]

        files_extracted = files_went_over.difference(failed_extract)
        # When extracting the files from the tar, they are also taken with their
        # directories from inside the tar, there is no way to only take the file
        # This function will remove all this nested directors
        delete_folders(folders_to_remove, destination)
        files_extracted = {os.path.join(destination, file) for file in files_extracted}
        return files_extracted, failed_extract

    @staticmethod
    def is_gzip_file(file_path: str) -> bool:
        """Check if the file is a gzip-compressed file by reading its magic number."""
        with open(file_path, "rb") as file:
            magic_number = file.read(2)
            return magic_number == GZIP_MAGIC_NUMBER

    @staticmethod
    def is_gzip_file_obj(file_obj) -> bool:
        """Check if the file-like object is a gzip-compressed file."""
        position = file_obj.tell()
        magic_number = file_obj.read(2)
        file_obj.seek(position)  # Reset the stream position
        return magic_number == GZIP_MAGIC_NUMBER

    def extract_files(self, files_to_extract: List[str],
                      directories_to_extract: List[str],
                      destination: str):
        """Since we do not know the type of dump, we search the files in the nested tars"""
        os.makedirs(destination, exist_ok=True)
        files_to_extract = set(files_to_extract)
        directories_to_extract = set(directories_to_extract)
        open_file_mode = "r:gz" if self.is_gzip_file(self.dump_path) else "r:"
        with tarfile.open(self.dump_path, open_file_mode) as outer_tar:
            # Checking if we have a dump from a complex env
            # The first tar that has some of the files, "wins"
            inner_tar_files = [
                name for name in outer_tar.getnames() if name.endswith(".tar.gz")
            ]
            for inner_tar_name in inner_tar_files:
                with outer_tar.extractfile(inner_tar_name) as inner_tar_stream:
                    inner_file_open_mode = (
                        "r:gz" if self.is_gzip_file_obj(inner_tar_stream) else "r:"
                    )
                    with tarfile.open(
                        fileobj=inner_tar_stream, mode=inner_file_open_mode
                    ) as inner_tar:
                        extracted_files, failed_files = self._get_files_from_tar(
                            inner_tar, files_to_extract, directories_to_extract, destination
                        )
                        if len(extracted_files) > 0:
                            return extracted_files, failed_files
            # If we got to this point, we might have a simple tar, try to extract from it
            return self._get_files_from_tar(outer_tar,
                                            files_to_extract,
                                            directories_to_extract,
                                            destination)
