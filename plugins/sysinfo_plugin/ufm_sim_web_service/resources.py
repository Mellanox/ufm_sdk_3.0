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

import configparser
import json
import os
from datetime import datetime, timedelta
import logging
import requests
from flask_restful import Resource
from flask import request

import asyncio
import platform,subprocess
from Request_handler.request_handler import RequestHandler
from validators import url

class UFMResource(Resource):
    # config_file_name = "../build/config/sysinfo.conf"
    # periodic_request_file = "../build/config/periodic_request.json"
    config_file_name = "/config/sysinfo.conf"
    periodic_request_file = "/config/periodic_request.json"

    def __init__(self) -> None:
        self.response_file = ""
        self.reports_dir = "reports"
        self.queries_list_file = "/log/queries"
        self.sysinfo_config_dir = "/config/sysinfo"
        self.success = 200
        self.configs = {}
   
        self.validation_enabled = True
        self.datetime_format = "%Y-%m-%d %H:%M:%S"
        self.expected_keys = set()
        self.optional_keys = set()
        self.version_file = "release.json"
        self.help_file = "help.json"

        self.queries_list = []
        self.version_file = "/opt/ufm/ufm_plugin_sysinfo/ufm_sim_web_service/release.json"
        self.help_file = "/opt/ufm/ufm_plugin_sysinfo/ufm_sim_web_service/help.json"

        self.create_reports_file(self.queries_list_file)
        self.parse_config()

    def parse_config(self) -> None:
        self.configs['reports_to_save'] = 10
        self.configs['ufm_port'] = 8000
        self.configs['max_jobs'] = 10
        file_config = configparser.ConfigParser()
        if os.path.exists(self.config_file_name):
            file_config.read(self.config_file_name)
            self.configs['reports_to_save'] = file_config.getint("Common", "reports_to_save", fallback=10)
            self.configs['ufm_port'] = file_config.getint("Common", "ufm_port", fallback=8000)
    
   
    def get_sysinfo_config_path(self, file_name: str) -> str:
        return os.path.join(self.sysinfo_config_dir, file_name)

    def get_report_path(self, file_name: str) -> str:
        return os.path.join(self.reports_dir, file_name)

    def get(self) -> tuple((json,int)):
        return self.read_json_file(self.response_file), self.success

    def post(self) -> tuple((dict,int)):
        return self.report_success()

    def report_success(self) -> tuple((dict,int)):
        return {}, self.success

    def check_request_keys(self, json_data:dict) -> tuple((str,int)):
        try:
            keys_dict = json_data.keys()
        except ValueError:
            return "Request format is incorrect", 400
        extra_keys = keys_dict - self.expected_keys
        if extra_keys:
            extra_keys = extra_keys - self.optional_keys
            if extra_keys:
                return f"Incorrect format, extra keys in request: {extra_keys}", 400
        missing_keys = self.expected_keys - keys_dict
        if missing_keys:
            return f"Incorrect format, missing keys in request: {missing_keys}", 400
        return self.report_success()

    @staticmethod
    def read_json_file(file_name:str) -> json:
        with open(file_name, "r", encoding="utf-8") as file:
            # unhandled exception in case some of the files was changed manually
            data = json.load(file)
        return data

    @staticmethod
    def create_reports_file(file_name:str) -> None:
        if not os.path.exists(file_name):
            logging.info("Creating {}".format(file_name))
            with open(file_name, "w") as file:
                json.dump([], file)

    @staticmethod
    def report_error(status_code:int, message:str) -> tuple((dict,int)):
        logging.error(message)
        return {"error": message}, status_code

    def get_timestamp(self) -> str:
        return str(datetime.now().strftime(self.datetime_format))


class Delete(UFMResource):
    def __init__(self) -> None:
        super().__init__()
        self.queries_to_delete = []

    def get(self) -> tuple((str,int)):
        return self.report_error(405, "Method is not allowed")

    def delete_sysinfo(self, file_name:str) -> tuple((str,int)):
        logging.debug("Deleting file: {}".format(file_name))
        try:
            os.remove(self.get_report_path(file_name))
            return self.report_success()
        except FileNotFoundError:
            return f"Cannot remove {file_name}: file not found", 400

    def parse_request(self, json_data:json, file_name:str, validate_keys:bool=True) -> tuple((str,int)):
        logging.debug("Parsing JSON request: {}".format(json_data))
        if validate_keys:
            response, status_code = self.check_request_keys(json_data)
            if status_code != self.success:
                return "", (response, status_code)
        file = json_data[file_name]
        if not file:
            return "", ("File name is empty", 400)
        return file, self.report_success()

    def update_queries_list_delete(self, json_data:json, delete_id:int) -> tuple((str,int)):
        error_response = []
        with open(self.queries_list_file, "r", encoding="utf-8") as file:
            # unhandled exception in case sysinfos file was changed manually
            data = json.load(file)
            for sysinfo_dict in json_data:
                sysinfo_to_delete, (response, status_code) = self.parse_request(sysinfo_dict, "file_name")
                if status_code != self.success:
                    error_response.append(response)
                    continue
                for sysinfo_record in list(data):
                    sysinfo_file, (response, status_code) = self.parse_request(sysinfo_record, "file", False)
                    if status_code != self.success:
                        error_response.append(response)
                        continue
                    if sysinfo_to_delete == sysinfo_file:
                        data.remove(sysinfo_record)
                        self.queries_to_delete.append(sysinfo_to_delete)
                        break
                else:
                    error_response.append(f"Cannot remove {sysinfo_to_delete}: file not found")
        with open(self.queries_list_file, "w") as file:
            json.dump(data, file)
        
        return error_response,400 if error_response else self.report_success()

    def post(self, delete_id:int) -> tuple((dict,int)):
        logging.info("POST /plugin/sysinfo/delete")
        if not request.json:
            return self.report_error(400, "Upload request is empty")
        else:
            error_status_code, error_response = self.success, []
            json_data = request.get_json(force=True)
            response, status_code = self.update_queries_list_delete(json_data, delete_id)
            if status_code != self.success:
                error_status_code = status_code
                error_response.extend(response)
            for sysinfo_file in self.queries_to_delete:
                response, status_code = self.delete_sysinfo(sysinfo_file)
                if status_code != self.success:
                    error_status_code = status_code
                    error_response.append(response)

            if error_status_code == self.success:
                return self.report_success()
            else:
                return self.report_error(error_status_code, error_response)

class QueryRequest(UFMResource):
    def __init__(self, scheduler) -> None:
        super().__init__()
        self.scheduler = scheduler
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

        self.UFM_SWITCHES_URL="http://127.0.0.1:8000/resources/systems?type=switch"

    def get(self) -> tuple((dict,int)):
        return self.report_error(405, "Method is not allowed")

    def post_commands(self, scope:str="Periodic") -> tuple((dict,int)):
        logging.info("Run topology comparison")
        if scope == 'Periodic':
            self.parse_config()
        self.timestamp = self.get_timestamp()
        try:
            async_rh = RequestHandler(self.switches,self.commands,self.ac,ip_to_guid=self.ip_to_guid,
                                      auto_respond=self.auto_respond,all_at_once=(self.callback if self.one_by_one else None))
            respond = asyncio.run(async_rh.post_commands())
            respond.update(self.auto_respond)
            return respond
        
        except Exception as exep:
            return self.report_error(400, exep)

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
            #empty list of switches with non empty list of ips from ufm
            self.switches=list(self.ip_to_guid.keys())


        for switch in self.switches:
            if not self._ping(switch):
                self.switches.remove(switch)
                self.auto_respond[switch] = "Switch does not respond to ping"
            if len(self.ip_to_guid)>0 and switch not in self.ip_to_guid.keys():
                self.switches.remove(switch)
                self.auto_respond[switch] = "Switch does not located on the running ufm"
        

    def parse_interval(self,json_data:dict) -> tuple((dict,int)):
        """
        parse the interval part and check the requested interval for it.
        """
        params = json_data["periodic_run"]
        self.expected_keys = self.expected_keys_second_level
        response, status_code = self.check_request_keys(params)
        if status_code != self.success:
            return self.report_error(status_code, response)
        start_time = params["startTime"]
        end_time = params["endTime"]
        self.interval = params["interval"]
        try:
            self.interval = int(self.interval)
            if self.interval < 5:
                return self.report_error(400, "Minimal interval value is 5 seconds")
        except ValueError:
            return self.report_error(400, f"Interval '{self.interval}' is not valid")
        timestamp = datetime.strptime(self.get_timestamp(), self.datetime_format)
        self.datetime_start = datetime.strptime(start_time, self.datetime_format)
        while timestamp > self.datetime_start:
            self.datetime_start += timedelta(seconds=self.interval)
        self.datetime_end = datetime.strptime(end_time, self.datetime_format)
        if self.datetime_end < timestamp:
            logging.info(f"End time is: {self.datetime_end.strftime(self.datetime_format)},\
            current time is: {timestamp.strftime(self.datetime_format)}")
            return self.report_error(400, "End time is less than current time")
        return self.report_success()
            
    def parse_request(self, json_data) -> tuple((int,str)):
        """
        parse the request that we got as json_data
        report success if successful to parse all, error and what part elsewise
        """
        logging.debug(f"Parsing JSON request: {json_data}")
        try:
            self.expected_keys = self.expected_keys_first_level
            response, status_code = self.check_request_keys(json_data)
            if status_code != self.success:
                return self.report_error(status_code, response)

            self.__dict__.update((k,v) for k,v in json_data.items() \
             if (k in self.expected_keys or k in self.optional_keys))

            is_url=url(self.callback)
            if not is_url:
                return self.report_error(400,f"the callback url is not right:{is_url}")

            if self.username and self.password:
                self.ac = (self.username, self.password)
            self.check_switches()

            if "periodic_run" in json_data:
                response, status_code = self.parse_interval(json_data)
                if status_code != self.success:
                    return self.report_error(status_code, response)
            return self.report_success()
        except TypeError:
            return self.report_error(400, "Incorrect format, failed to parse timestamp")
        except ValueError as valueerror:
            return self.report_error(400, f"Incorrect timestamp format: {valueerror}")

    def add_scheduler_jobs(self) -> tuple((dict,int)):
        
        try:
            request_handler_switches = RequestHandler(self.switches,self.commands,self.ac,ip_to_guid=self.ip_to_guid,
                                        all_at_once=(self.callback if self.one_by_one else None),is_async=self.is_async,
                                        auto_respond=self.auto_respond)
            if self.interval != 0:
                self.scheduler.add_job(func=request_handler_switches.login_to_all,\
                         run_date=self.datetime_start)
                while self.datetime_start <= self.datetime_end:
                    self.scheduler.add_job(func=request_handler_switches.execute_commands_and_save,\
                         run_date=self.datetime_start,args=[self.callback])
                    self.datetime_start += timedelta(seconds=self.interval)
                self.scheduler.add_job(func=request_handler_switches.logout_to_all,\
                         run_date=self.datetime_start)
                return self.report_success()
            else:
                asyncio.run(request_handler_switches.post_commands())
                error,status = self.save_results(request_handler_switches.latest_respond)
                if status == self.success:
                    return self.report_success()
                return self.report_error(status,error)
        except Exception as exep:
            return self.report_error(400, f"Periodic comparison failed to start: {exep}")

    def _get_switches_from_ufm(self) -> dict:
        if self.ignore_ufm:return {}
        respond = requests.get(self.UFM_SWITCHES_URL,headers={"X-Remote-User": "ufmsystem"},verify=False)
        if respond.status_code==200:
            try:
                as_json = respond.json()
                ip_to_guid={}
                for switch in as_json:
                    if switch['ip']!='0.0.0.0':
                        ip_to_guid[switch['ip']]=switch['guid']
                return ip_to_guid

            except (json.JSONDecodeError,ValueError,KeyError):
                return {}
        else:
            print("Couldnt reach ufm:"+respond.reason)
        return {}

    def post(self) -> tuple((dict,int)):
        logging.info("POST /plugin/sysinfo/query")
        if request.json:
            json_data = request.get_json(force=True)
            #if len(self.scheduler.get_jobs()) > self.configs["max_jobs"]:
            #    return self.report_error(400, "Too much queries running")
            response, status_code = self.parse_request(json_data)
            if status_code != self.success:
                return response, status_code
            
            response, status_code = self.add_scheduler_jobs()
            if response != self.success:
                return response,status_code

            return self.report_success()
        else:
            return self.report_error(400, "Not receive a json post")

    def save_results(self,results) -> tuple((dict,int)):
        if self.one_by_one:
            return self.report_success()
        try:
            respond = requests.post(self.callback,json=results,verify=False)
            if 200 <= respond.status_code <= 203:
                return self.report_success()
            return self.report_error(respond.status_code,respond.text)
        except Exception as exception:
            return self.report_error(400, exception)

class Cancel(UFMResource):
    def __init__(self, scheduler) -> None:
        super().__init__()
        self.scheduler = scheduler

    def post(self) -> tuple((str,int)):
        try:
            if os.path.exists(UFMResource.periodic_request_file):
                os.remove(UFMResource.periodic_request_file)
            if len(self.scheduler.get_jobs()):
                self.scheduler.remove_all_jobs()
                return self.report_success()
            else:
                return self.report_error(400, "Periodic comparison is not running")
        except Exception as exep:
            return self.report_error(400, "Failed to cancel periodic comparison: {}".format(exep))

    def get(self) -> tuple((str,int)):
        return self.report_error(405, "Method is not allowed")


class QueryId(UFMResource):
    def __init__(self):
        super().__init__()
        # unhandled exception in case reports file was deleted manually
        with open(self.queries_list_file, "r", encoding="utf-8") as file:
            self.data = json.load(file)

    def post(self, query_id) -> tuple((str,int)):
        return self.report_error(405, "Method is not allowed")

    def get(self, query_id) -> tuple((str,int)):
        logging.info("GET /plugin/sysinfo/reports")
        # unhandled exception in case reports file was changed manually
        try:
            query_id = int(query_id)
        except ValueError:
            return self.report_error(400, f"Report id '{query_id}' is not valid")
        if query_id in self.queries_list:
            self.response_file = \
                os.path.join(self.reports_dir,
                             "report_{}.json".format(query_id))
            logging.debug("Report found: {}".format(self.response_file))
        else:
            return self.report_error(400, f"Report {query_id} not found")

        return super().get()


class Version(UFMResource):
    def __init__(self):
        logging.info("GET /plugin/sysinfo/version")
        super().__init__()
        self.response_file = self.version_file

    def post(self) -> tuple((str,int)):
        return self.report_error(405, "Method is not allowed")


class Help(UFMResource):
    def __init__(self):
        logging.info("GET /plugin/sysinfo/version")
        super().__init__()
        self.response_file = self.help_file

    def post(self) -> tuple((str,int)):
        return self.report_error(405, "Method is not allowed")


class Config(UFMResource):
    def __init__(self):
        logging.info("GET /plugin/sysinfo/config")
        super().__init__()
        self.optional_keys = self.configs.keys()

    def get(self) -> tuple((str,int)):
        logging.info("GET /plugin/sysinfo/config")
        return self.configs, self.success

    def post(self) -> tuple((str,int)):
        if request.json:
            json_data = request.get_json(force=True)
            with open(UFMResource.periodic_request_file, "w") as file:
                json.dump(json_data, file)
            response, status_code = self.check_request_keys(json_data)
            if status_code != self.success:
                return response, status_code
            
            for key in json_data:
                if key in self.configs.keys():
                    self.configs[key] = json_data[key]
            return self.report_success()

class Queries(UFMResource):
    def __init__(self) -> None:
        logging.info("GET /plugin/sysinfo/queries")
        super().__init__()
        self.response_file = self.queries_list_file

    def post(self) -> tuple((str,int)):
        return self.report_error(405, "Method is not allowed")

class Dummy(UFMResource):
    def __init__(self) -> None:
        super().__init__()

    def post(self) -> tuple((str,int)):
        print(datetime.now())
        if request.json:
            print(request.json)
        else: print(request)

class Date(UFMResource):
    def get(self):
        logging.info("GET /plugin/sysinfo/date")
        return {"date": self.get_timestamp()}, self.success

    def post(self):
        return self.report_error(405, "Method is not allowed")

