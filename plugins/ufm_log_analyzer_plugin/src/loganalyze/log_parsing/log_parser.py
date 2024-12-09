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
# pylint: disable=missing-module-docstring

import os
import re
from typing import Callable, Tuple, List
import gzip


class LogParser:  # pylint: disable=too-few-public-methods
    """
    Basic class for parsing logs
    """

    def __init__(self, input_log_path: str, lines_regex: List[Tuple[str, Callable]]):
        self._lines_regex_and_fn = lines_regex
        if not os.path.exists(input_log_path):
            raise FileNotFoundError(f"File {input_log_path} does not exists")
        self._input_log_path = input_log_path
        if input_log_path.endswith(".gz"):
            self._parser_func = self._parse_gz_log
        else:
            self._parser_func = self._parse_regular_log
        self._success_parsed = 0
        self._failed_parsed = 0

    def _parse_gz_log(self, callback_fn: Callable[[Tuple], None]):
        with gzip.open(self._input_log_path, "rt") as log_file:
            for line in log_file:
                self._process_line(line, callback_fn)

    def _parse_regular_log(self, callback_fn: Callable[[Tuple], None]):
        with open(self._input_log_path, "r", encoding="utf-8") as log_file:
            for line in log_file:
                self._process_line(line, callback_fn)

    def parse(self, callback_fn: Callable[[Tuple], None]):
        """
        For the given log, parse all the lines
        """
        self._parser_func(callback_fn)

    def _find_first_match(self, line: str):
        for _, regex_and_align_func in enumerate(self._lines_regex_and_fn):
            regex, align_func = regex_and_align_func
            match = re.match(regex, line)
            if match:
                return align_func(match)
        return None

    def _process_line(self, line: str, callback_fn: Callable[[Tuple], None]):
        line_groups = self._find_first_match(line)
        if not line_groups:
            self._failed_parsed += 1
            return
        self._success_parsed += 1
        callback_fn(line_groups)
