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


import glob
import os
import shutil
from typing import Set
import loganalyze.logger as log

def delete_folders(folders: Set[str], until_folder:str):
    """
    Delete all the folders in the folders param, and their parents until reaching the
    until_folder folder
    """
    for folder in folders:
        cur_dir = folder
        while cur_dir != until_folder:
            try:
                shutil.rmtree(cur_dir)
                log.LOGGER.debug(f"Removed {cur_dir}")
            except FileNotFoundError:
                log.LOGGER.debug(f"Error: {cur_dir} does not exist.")
            except PermissionError:
                log.LOGGER.debug(f"Error: Insufficient permissions to delete {cur_dir}.")
            except NotADirectoryError:
                log.LOGGER.debug(f"Error: {cur_dir} is not a directory.")
            except OSError as e:
                log.LOGGER.debug(f"Error: {e.strerror} - {e.filename}")
            except ValueError as e:
                log.LOGGER.debug(f"Error: Invalid parameters passed to rmtree - {e}")
            cur_dir = os.path.dirname(cur_dir)


def delete_files_by_types(folder:str, file_types:set[str]):
    """
    Given a folder and file types, for example svg and png, it will delete all
    files that end with .svg and .png in the given folder.
    """
    
    for file_type in file_types:
        search_pattern = f"*.{file_type}"
        all_files_in_dir_by_type = glob.glob(os.path.join(folder, search_pattern))
        for cur_file in all_files_in_dir_by_type:
            try:
                os.remove(cur_file)
            except Exception as e:
                log.LOGGER.debug(f"Error deleting SVG files: {e}")
