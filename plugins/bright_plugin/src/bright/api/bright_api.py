#
# Copyright © 2013-2022 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
# @author: Anan Al-Aghbar
# @date:   Dec 26, 2022
#
import datetime
import pytz

from flask import make_response, request
from http import HTTPStatus
from utils.logger import Logger, LOG_LEVELS
from utils.flask_server.base_flask_api_server import BaseAPIApplication, InvalidRequestError
from mgr.bright_data_mgr import BrightDataMgr, BCMConnectionError
from mgr.bright_data_polling_mgr import BrightDataPollingMgr


class BrightAPI(BaseAPIApplication):

    API_PARAM_TIMEZONE = "tz"
    API_PARAM_NODES = "nodes"
    API_PARAM_FROM = "from"
    API_PARAM_TO = "to"

    def __init__(self):
        super(BrightAPI, self).__init__()
        self.bright_data_mgr = BrightDataMgr()
        self.bright_data_polling_mgr = BrightDataPollingMgr()

    def _get_error_handlers(self):
        return [
            (BCMConnectionError,
             lambda e: (str(e), HTTPStatus.BAD_REQUEST))
        ]

    def _get_routes(self):
        return {
            self.get_nodes: dict(urls=["/nodes"], methods=["GET"]),
            self.get_jobs: dict(urls=["/jobs"], methods=["GET"])
        }

    def get_time_req_arg(self, key, def_value=None, tz='UTC'):
        value = self._get_request_arg(key, def_val=def_value)
        if value is None:
            return value
        time = datetime.datetime.now()
        try:
            if value.lower().endswith('min'):
                time = time - datetime.timedelta(minutes=int(value[1:-3]))
            elif value.lower().endswith('h'):
                time = time - datetime.timedelta(hours=int(value[1:-1]))
            else:
                # milliseconds
                milliseconds = int(value) / 1000.0
                time = datetime.datetime.fromtimestamp(milliseconds)
        except Exception as e:
            Logger.log_message(f'Error during parsing time filter in the API: {request.url}, {str(e)}',
                               LOG_LEVELS.ERROR)
            raise InvalidRequestError(f'Unsupported format for time request argument: {key}, {str(e)}')
        # Change the given time from the machine timezone to request timezone
        if tz:
            time = datetime.datetime.fromtimestamp(time.timestamp(), tz=pytz.timezone(tz))
        return time

    def _is_job_within_date(self, job, start_time, end_time, req_timezone):
        job_submit_time = self.bright_data_mgr.get_job_submit_time(job)
        job_submit_time = datetime.datetime.fromtimestamp(job_submit_time.timestamp(), pytz.timezone(req_timezone))
        return start_time <= job_submit_time < end_time

    def get_nodes(self):
        bcm_data = self.bright_data_mgr.get_bright_cluster_saved_data()
        return make_response(list(bcm_data.keys()))

    def get_jobs(self):
        jobs = list([])
        bcm_data = self.bright_data_mgr.get_bright_cluster_saved_data()
        nodes = self._get_request_arg(self.API_PARAM_NODES)
        req_tz = self._get_request_arg(self.API_PARAM_TIMEZONE)
        start_time = self.get_time_req_arg(self.API_PARAM_FROM, tz=req_tz)
        end_time = self.get_time_req_arg(self.API_PARAM_TO, '-0min', req_tz)
        if nodes:
            nodes = nodes.split(",")
            for node in nodes:
                node_jobs = bcm_data.get(node, {}).get('jobs')
                if node_jobs:
                    jobs = jobs + list(node_jobs.values())
        else:
            for node, node_data in bcm_data.items():
                jobs = jobs + list(node_data.get('jobs', {}).values())
        if start_time and end_time:
            jobs = list(filter(lambda job: self._is_job_within_date(job, start_time, end_time, req_tz), jobs))
        return make_response(jobs)
