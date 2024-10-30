#
# Copyright (C) 2013-2023 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
# author: Elad Gershon
# date:   February 1, 2023
#

import json
import os
from datetime import datetime, timedelta
import logging
from http import HTTPStatus
from typing import Tuple
import requests
from aiohttp import web

import asyncio
import platform, subprocess
from Request_handler.request_handler import RequestHandler
from validators import url
import requests

from configuration import Configuration
from base_aiohttp_api import BaseAiohttpHandler

# pylint: disable=broad-exception-caught

class SysInfoAiohttpHandler(BaseAiohttpHandler):
    """
    Base plugin aiohttp handler class
    """
    config_file_name = "/config/sysinfo.conf"
    periodic_request_file = "/config/periodic_request.json"

    def __init__(self, request):
        """
        Initialize a new instance of the SysInfoAiohttpHandler class.
        """
        super().__init__(request)

        self.scheduler = request.app["scheduler"]
        self.reports_dir = "reports"
        self.queries_list_file = "/log/queries"
        self.sysinfo_config_dir = "/config/sysinfo"

        self.validation_enabled = True
        self.datetime_format = "%Y-%m-%d %H:%M:%S"
        self.expected_keys = set()
        self.optional_keys = set()

        resources_dir = "/opt/ufm/ufm_plugin_sysinfo/ufm_sim_web_service"
        if not os.path.exists(resources_dir):
            resources_dir = os.path.dirname(os.path.abspath(__file__))
        self.version_file = os.path.join(resources_dir, "release.json")
        self.help_file = os.path.join(resources_dir, "help.json")

        self.create_reports_file(self.queries_list_file)

        self.configs = {}
        self.configs['reports_to_save'] = Configuration.reports_to_save
        self.configs['ufm_port'] = Configuration.ufm_port
        self.configs['max_jobs'] = Configuration.max_jobs

    def get_sysinfo_config_path(self, file_name: str) -> str:
        """ Return full configuration file path based on file name """
        return os.path.join(self.sysinfo_config_dir, file_name)

    def get_report_path(self, file_name: str) -> str:
        """ Return full report file path based on file name """
        return os.path.join(self.reports_dir, file_name)

    # def report_success(self) -> tuple((dict,int)):
    #     return {}, self.success

    def check_request_keys(self, json_data:dict) -> web.Response:
        """ Check request keys. """
        try:
            keys_dict = json_data.keys()
        except ValueError:
            return self.text_response("Request format is incorrect", HTTPStatus.BAD_REQUEST)
        extra_keys = keys_dict - self.expected_keys
        if extra_keys:
            extra_keys = extra_keys - self.optional_keys
            if extra_keys:
                return self.text_response(f"Incorrect format, extra keys in request: {extra_keys}", HTTPStatus.BAD_REQUEST)
        missing_keys = self.expected_keys - keys_dict
        if missing_keys:
            return self.text_response(f"Incorrect format, missing keys in request: {missing_keys}", HTTPStatus.BAD_REQUEST)
        return self.text_response(None, HTTPStatus.OK)

    def create_reports_file(self, file_name:str) -> None:
        """ Create reports file if it does not exist """
        if not os.path.exists(file_name):
            self.logger.info("Creating %s", file_name)
            with open(file_name, "w", encoding="utf-8") as file:
                json.dump([], file)

    # @staticmethod
    # def report_error(status_code:int, message:str) -> tuple((dict,int)):
    #     logging.error(message)
    #     return {"error": message}, status_code

    def get_timestamp(self) -> str:
        """ Return timestamp string based in predefined format """
        return str(datetime.now().strftime(self.datetime_format))


class Delete(SysInfoAiohttpHandler):
    """ Delete class handler """
    def __init__(self, request) -> None:
        super().__init__(request)
        self.queries_to_delete = []

    def delete_sysinfo(self, file_name:str) -> web.Response:
        """ Remove report file """
        self.logger.debug(f"Deleting file: {file_name}")
        try:
            os.remove(self.get_report_path(file_name))
            return self.text_response(None, HTTPStatus.OK)
        except FileNotFoundError:
            return self.text_response(f"Cannot remove {file_name}: file not found", HTTPStatus.BAD_REQUEST)

    def parse_request(self, json_data:json, file_name:str, validate_keys:bool=True) -> Tuple[str, web.Response]:
        """ Parse JSON request """
        self.logger.debug(f"Parsing JSON request: {json_data}")
        if validate_keys:
            response = self.check_request_keys(json_data)
            if response.status != HTTPStatus.OK:
                return "", response
        file = json_data[file_name]
        if not file:
            return "", self.text_response("File name is empty", HTTPStatus.BAD_REQUEST)
        return file, self.text_response(None, HTTPStatus.OK)

    def update_queries_list_delete(self, json_data:json, delete_id:int) -> web.Response:
        """ Delete queries from queries list file """
        try:
            error_response = []
            with open(self.queries_list_file, "r", encoding="utf-8") as file:
                # unhandled exception in case sysinfos file was changed manually
                data = json.load(file)
                for sysinfo_dict in json_data:
                    sysinfo_to_delete, response = self.parse_request(sysinfo_dict, "file_name")
                    if response.status != HTTPStatus.OK:
                        error_response.append(response.text)
                        continue
                    for sysinfo_record in list(data):
                        sysinfo_file, response = self.parse_request(sysinfo_record, "file", False)
                        if response.status != HTTPStatus.OK:
                            error_response.append(response.text)
                            continue
                        if sysinfo_to_delete == sysinfo_file:
                            data.remove(sysinfo_record)
                            self.queries_to_delete.append(sysinfo_to_delete)
                            break
                    else:
                        error_response.append(f"Cannot remove {sysinfo_to_delete}: file not found")

            with open(self.queries_list_file, "w", encoding="utf-8") as file:
                json.dump(data, file)

            if not error_response:
                return self.json_response(error_response, HTTPStatus.BAD_REQUEST)

            return self.text_response(None, HTTPStatus.OK)
        
        except Exception as e:
            return self.text_response(f"{e}", HTTPStatus.INTERNAL_SERVER_ERROR)

    async def post(self):
        """ POST method handler """
        delete_id = self.request.match_info["report_id"]
        self.logger.info("POST /plugin/sysinfo/delete/{delete_id}")
        if self.request.content_type == 'application/json':
            json_data = await self.request.json()
            error_status_code = HTTPStatus.OK
            error_response = []
            response = self.update_queries_list_delete(json_data, delete_id)
            if response.status != HTTPStatus.OK:
                error_status_code = response.status
                error_response.extend(response.text)
            for sysinfo_file in self.queries_to_delete:
                response = self.delete_sysinfo(sysinfo_file)
                if response.status != HTTPStatus.OK:
                    error_status_code = response.status
                    error_response.append(response.text)

            if error_status_code == HTTPStatus.OK:
                return self.text_response(None, HTTPStatus.OK)
            else:
                return self.json_response(error_response, error_status_code)
        else:
            return self.text_response("Upload request is empty or invalid", HTTPStatus.BAD_REQUEST)

class QueryRequest(SysInfoAiohttpHandler):
    """ QueryRequest class handler """
    UFM_SWITCHES_URL="http://127.0.0.1:8000/resources/systems?type=switch"

    def __init__(self, request) -> None:
        super().__init__(request)
        self.report_number = 0
        self.timestamp = ""

        self.interval = 0
        self.datetime_start = None
        self.datetime_end = None

        self.retry = 0
        self.callback = ""
        self.ac = None
        self.username = None
        self.password = None

        self.switches = []
        self.sync_set = None
        self.commands = []
        self.is_async = False
        self.auto_respond = {}
        self.ip_to_guid = {}
        self.one_by_one = False
        self.ignore_ufm = False

        self.optional_keys = {'retry','switches','sync_set','periodic_run','ignore_ufm','username','password','is_async','one_by_one'}
        self.expected_keys_first_level = {'callback','commands'}
        self.expected_keys_second_level = {"startTime", "endTime", "interval"}

    def post_commands(self, scope:str="Periodic") -> dict:
        """ Run topology comparison """
        self.logger.info("Run topology comparison")
        if scope == 'Periodic':
            self.parse_config()
        self.timestamp = self.get_timestamp()
        try:
            async_rh = RequestHandler(self.switches,self.commands,self.ac,ip_to_guid=self.ip_to_guid,
                                      auto_respond=self.auto_respond,all_at_once=(self.callback if self.one_by_one else None))
            respond = asyncio.run(async_rh.post_commands())
            respond.update(self.auto_respond)
            return respond
        
        except Exception as e:
            self.logger.error(f"Failed to run topology comparison: {e}")
            return None

    @staticmethod
    def _ping(host:str) -> bool:
        """
        Returns True if host (str) responds to a ping request.
        Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.
        """

        # Option for the number of packets as a function of
        param = '-n' if platform.system().lower()=='windows' else '-c'

        # Building the command. Ex: "ping -c 1 google.com"
        command = ['ping', param, '1', host]

        return subprocess.call(command) == 0

    def check_switches(self) -> None:
        """
        ping all the switches in self.switches.
        if there are not responding removing them from switches and update auto_respond.
        Also check with ufm the guid of them. if it connected to the ufm it will return the guids instead of ips
        """
        self.ip_to_guid=self._get_switches_from_ufm()
        if len(self.switches) == 0 and len(self.ip_to_guid)>0: 
            # empty list of switches with non empty list of ips from ufm
            self.switches=list(self.ip_to_guid.keys())

        for switch in self.switches:
            if not self._ping(switch):
                self.switches.remove(switch)
                self.auto_respond[switch] = "Switch does not respond to ping"
            if len(self.ip_to_guid) > 0 and switch not in self.ip_to_guid:
                self.switches.remove(switch)
                self.auto_respond[switch] = "Switch does not located on the running ufm"
        

    def parse_interval(self,json_data:dict) -> web.Response:
        """
        parse the interval part and check the requested interval for it.
        """
        params = json_data["periodic_run"]
        self.expected_keys = self.expected_keys_second_level
        response = self.check_request_keys(params)
        if response.status != HTTPStatus.OK:
            return response
        start_time = params["startTime"]
        end_time = params["endTime"]
        self.interval = params["interval"]
        try:
            self.interval = int(self.interval)
            if self.interval < 5:
                return self.text_response("Minimal interval value is 5 seconds", HTTPStatus.BAD_REQUEST)
        except ValueError:
            return self.text_response(f"Interval '{self.interval}' is not valid", HTTPStatus.BAD_REQUEST)
        timestamp = datetime.strptime(self.get_timestamp(), self.datetime_format)
        self.datetime_start = datetime.strptime(start_time, self.datetime_format)
        while timestamp > self.datetime_start:
            self.datetime_start += timedelta(seconds=self.interval)
        self.datetime_end = datetime.strptime(end_time, self.datetime_format)
        if self.datetime_end < timestamp:
            self.logger.info(f"End time is: {self.datetime_end.strftime(self.datetime_format)},\
            current time is: {timestamp.strftime(self.datetime_format)}")
            return self.text_response("End time is less than current time", HTTPStatus.BAD_REQUEST)
        return self.text_response(None, HTTPStatus.OK)
            
    def parse_request(self, json_data) -> web.Response:
        """
        parse the request that we got as json_data
        report success if successful to parse all, error and what part elsewise
        """
        self.logger.debug(f"Parsing JSON request: {json_data}")
        try:
            self.expected_keys = self.expected_keys_first_level
            response = self.check_request_keys(json_data)
            if response.status != HTTPStatus.OK:
                return response

            self.__dict__.update((k,v) for k,v in json_data.items() \
             if (k in self.expected_keys or k in self.optional_keys))

            is_url = url(self.callback)
            if not is_url:
                return self.text_response(f"the callback url is not right:{is_url}", HTTPStatus.BAD_REQUEST)

            if self.username and self.password:
                self.ac = (self.username, self.password)
            self.check_switches()

            if "periodic_run" in json_data:
                return self.parse_interval(json_data)

            return self.text_response(None, HTTPStatus.OK)
        except TypeError:
            return self.text_response("Incorrect format, failed to parse timestamp", HTTPStatus.BAD_REQUEST)
        except ValueError as valueerror:
            return self.text_response(f"Incorrect timestamp format: {valueerror}", HTTPStatus.BAD_REQUEST)

    def add_scheduler_jobs(self) -> web.Response:
        """ Add scheduler jobs """
        try:
            request_handler_switches = RequestHandler(self.switches, self.commands,self.ac, ip_to_guid=self.ip_to_guid,
                                        all_at_once=(self.callback if self.one_by_one else None), is_async=self.is_async,
                                        auto_respond=self.auto_respond)
            if self.interval != 0:
                self.scheduler.add_job(func=request_handler_switches.login_to_all,
                                       run_date=self.datetime_start)
                while self.datetime_start <= self.datetime_end:
                    self.scheduler.add_job(func=request_handler_switches.execute_commands_and_save,
                                           run_date=self.datetime_start,args=[self.callback])
                    self.datetime_start += timedelta(seconds=self.interval)
                self.scheduler.add_job(func=request_handler_switches.logout_to_all,
                                       run_date=self.datetime_start)
                return self.text_response(None, HTTPStatus.OK)
            else:
                asyncio.run(request_handler_switches.post_commands())
                return self.save_results(request_handler_switches.latest_respond)
        except Exception as e:
            return self.text_response(f"Periodic comparison failed to start: {e}", HTTPStatus.BAD_REQUEST)

    def _get_switches_from_ufm(self) -> dict:
        if self.ignore_ufm:
            return {}
        respond = requests.get(self.UFM_SWITCHES_URL,headers={"X-Remote-User": "ufmsystem"}, verify=False)
        if respond.status_code == HTTPStatus.OK:
            try:
                as_json = respond.json()
                ip_to_guid = {}
                for switch in as_json:
                    if switch['ip'] != '0.0.0.0':
                        ip_to_guid[switch['ip']] = switch['guid']
                return ip_to_guid

            except (json.JSONDecodeError, ValueError, KeyError):
                return {}
        else:
            print("Couldnt reach ufm:" + respond.reason)
        return {}

    async def post(self):
        """ POST method handler """
        self.logger.info("POST /plugin/sysinfo/query")
        if self.request.content_type == 'application/json':
            json_data = await self.request.json()
            # if len(self.scheduler.get_jobs()) > self.configs["max_jobs"]:
            #     return self.text_response("Too much queries running", HTTPStatus.BAD_REQUEST)
            response = self.parse_request(json_data)
            if response.status == HTTPStatus.OK:
                response = self.add_scheduler_jobs()
            return response
        else:
            return self.text_response("Not receive a json post", HTTPStatus.BAD_REQUEST)

    def save_results(self, results) -> web.Response:
        """ Save results """
        if self.one_by_one:
            return self.text_response(None, HTTPStatus.OK)
        try:
            response = requests.post(self.callback, json=results, verify=False)
            if HTTPStatus.OK <= response.status_code <= HTTPStatus.NON_AUTHORITATIVE_INFORMATION:
                return self.text_response(None, HTTPStatus.OK)
            return self.text_response(response.text, response.status_code)
        except Exception as e:
            return self.text_response(f"Failed to save results: {e}", HTTPStatus.BAD_REQUEST)

class Cancel(SysInfoAiohttpHandler):
    """ Cancel class handler """
    async def post(self):
        """ POST method handler """
        self.logger.info("POST /plugin/sysinfo/cancel")
        try:
            if os.path.exists(self.periodic_request_file):
                os.remove(self.periodic_request_file)

            if len(self.scheduler.get_jobs()):
                self.scheduler.remove_all_jobs()
                return self.text_response(None, HTTPStatus.OK)
            else:
                return self.text_response("Periodic comparison is not running", HTTPStatus.BAD_REQUEST)
        except Exception as e:
            return self.text_response(f"Failed to cancel periodic comparison: {e}", HTTPStatus.BAD_REQUEST)


class QueryId(SysInfoAiohttpHandler):
    """ QueryId class handler """
    async def get(self):
        """ GET method handler """
        query_id = self.request.match_info["query_id"]
        self.logger.info("GET /plugin/sysinfo/queries/{query_id}")
        try:
            query_id = int(query_id)
        except ValueError:
            return self.text_response(f"Report id '{query_id}' is not valid", HTTPStatus.BAD_REQUEST)

        try:
            with open(self.queries_list_file, "r", encoding="utf-8") as file:
                queries_list = json.load(file)
                # pylint: disable=fixme,line-too-long
                # TODO: Do we need to check the list or it is enough to directly look for report file?
                if query_id in queries_list:
                    report_file = os.path.join(self.reports_dir, f"report_{query_id}.json")
                    self.logger.debug(f"Report found: {report_file}")
                    return self.json_file_response(report_file)
                else:
                    return self.text_response(f"Report {query_id} not found", HTTPStatus.BAD_REQUEST)
        except Exception as e:
            return self.text_response(f"{e}", HTTPStatus.INTERNAL_SERVER_ERROR)


class Version(SysInfoAiohttpHandler):
    """ Version class handler """
    async def get(self):
        """ GET method handler """
        self.logger.info("GET /plugin/sysinfo/version")
        return self.json_file_response(self.version_file)


class Help(SysInfoAiohttpHandler):
    """ Help class handler """
    async def get(self):
        """ GET method handler """
        self.logger.info("GET /plugin/sysinfo/help")
        return self.json_file_response(self.help_file)


class Config(SysInfoAiohttpHandler):
    """ Config class handler """
    async def get(self):
        """ GET method handler """
        self.logger.info("GET /plugin/sysinfo/config")
        return self.json_response(self.configs, HTTPStatus.OK)

    async def post(self):
        """ POST method handler """
        self.logger.info("POST /plugin/sysinfo/config")
        if self.request.content_type == 'application/json':
            json_data = await self.request.json()
            with open(self.periodic_request_file, "w", encoding="utf-8") as file:
                json.dump(json_data, file)

            self.optional_keys = self.configs.keys()
            response = self.check_request_keys(json_data)
            if response.status != HTTPStatus.OK:
                return response

            for key in json_data:
                if key in self.configs:
                    self.configs[key] = json_data[key]

            return self.text_response(None, HTTPStatus.OK)
        else:
            return self.text_response("Request format is incorrect", HTTPStatus.BAD_REQUEST)


class Queries(SysInfoAiohttpHandler):
    """ Queries class handler """
    async def get(self):
        """ GET method handler """
        self.logger.info("GET /plugin/sysinfo/queries")
        return self.json_file_response(self.queries_list_file)


class Dummy(SysInfoAiohttpHandler):
    """ Dummy class handler """
    async def get(self):
        """ GET method handler """
        return self.text_response("Dummy 'get' response", HTTPStatus.OK)

    async def post(self):
        """ POST method handler """
        return self.text_response("Dummy 'post' response", HTTPStatus.OK)


class Date(SysInfoAiohttpHandler):
    """ Date class handler """
    async def get(self):
        """ GET method handler """
        self.logger.info("GET /plugin/sysinfo/date")
        return self.json_response({"date": self.get_timestamp()}, HTTPStatus.OK)
