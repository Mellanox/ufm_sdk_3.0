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
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring


class RegexAndHandlers:
    def __init__(self, log_name, csv_headers):
        self._regex_and_handler_list = []
        self._log_name = log_name
        self._csv_headers = csv_headers

    def add_regex(self, regex, handler):
        self._regex_and_handler_list.append((regex, handler))

    def get_all_info(self):
        """
        Return a tuple where first is the log name, second is the list of regex and handlers,
        third is the CSV headers
        """
        return (self._log_name, self._regex_and_handler_list, self._csv_headers)
