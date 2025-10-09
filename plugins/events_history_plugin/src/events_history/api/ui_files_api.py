#
# Copyright © 2013-2023 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
# @author: Abeer Moghrabi
# @date:   Aug 9, 2023
#
from flask import send_from_directory
from utils.flask_server.base_flask_api_server import BaseAPIApplication


class EventsHistoryPluginUIFilesAPI(BaseAPIApplication):
    """
    This class was designed to support retrieving UI files.
    """

    def __init__(self):
        super(EventsHistoryPluginUIFilesAPI, self).__init__()
        self.files_path = "/data/events_history_ui/"

    def _get_routes(self):
        return {
            self.get_file: dict(urls=["/<path:file_name>"], methods=["GET"])
        }

    def get_file(self, file_name):
        return send_from_directory(self.files_path, file_name)

