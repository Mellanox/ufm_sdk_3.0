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
from flask import make_response, request
from http import HTTPStatus

from utils.flask_server.base_flask_api_server import BaseAPIApplication
from utils.config_parser import InvalidConfRequest
from utils.logger import Logger, LOG_LEVELS
from mgr.events_history_mgr import EventsHistoryMgr


class EventsHistoryApi(BaseAPIApplication):

    def __init__(self):
        super(EventsHistoryApi, self).__init__()
        self.event_mgr = EventsHistoryMgr.getInstance()


    def _get_error_handlers(self):
        return [
            (InvalidConfRequest,
             lambda e: (str(e), HTTPStatus.BAD_REQUEST))
        ]

    def _get_routes(self):
        return {
            self.get_events_history: dict(urls=["/"], methods=["GET"]),
        }

    def get_events_history(self):
        try:
            # TODO implement get events history
            return make_response({})
        except Exception as e:
            Logger.log_message("Error occurred while getting events history: " + str(e),
                               LOG_LEVELS.ERROR)
            raise e


