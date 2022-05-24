import logging
import platform
import time
from http import HTTPStatus
import re
import sys
import threading
import os

try:
    from utils.utils import Utils
    from utils.ufm_rest_client import UfmRestClient, HTTPMethods
    from utils.logger import Logger, LOG_LEVELS
    from utils.job_polling import JobPolling, JobsConstants
except ModuleNotFoundError as e:
    if platform.system() == "Windows":
        print("Error occurred while importing python modules, "
              "Please make sure that you exported your repository to PYTHONPATH by running: "
              f'set PYTHONPATH=%PYTHONPATH%;{os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))}')
    else:
        print("Error occurred while importing python modules, "
              "Please make sure that you exported your repository to PYTHONPATH by running: "
              f'export PYTHONPATH="${{PYTHONPATH}}:{os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))}"')


class ActionConstants:
    UFM_API_SYSTEMS = 'resources/systems'
    UFM_API_ACTIONS = 'actions'
    UFM_API_DESCRIPTION = 'description'
    UFM_API_ACTION = 'action'
    UFM_API_OBJECT_TYPE = "object_type"
    UFM_API_IDENTIFIER = "identifier"
    UFM_API_PARAMS = "params"
    API_GUID = "guid"
    API_OBJECT_IDS = "object_ids"
    API_CAPABILITIES = "capabilities"


class UfmDevicesAction(object):

    def __init__(self,payload,object_ids=None, host=None,client_token=None, username=None, password=None,ws_protocol=None):
        self.action = payload["action"]
        self.object_ids = object_ids
        self.payload = payload
        self.action_inprogress = False
        # init ufm rest client
        self.ufm_rest_client = UfmRestClient(host=host,
                                        client_token=client_token, username=username, password=password,ws_protocol=ws_protocol)
        #init job_polling
        self.job_polling = JobPolling(self.ufm_rest_client, self.action)


    def get_supported_systems(self,systems):
        sys_with_cap = []
        for sys in systems:
            if self.action in sys[ActionConstants.API_CAPABILITIES]:
                sys_with_cap.append(sys[ActionConstants.API_GUID])

        if not sys_with_cap or not len(sys_with_cap):
            raise ValueError(F"systems {self.object_ids} don't support {self.action}")
        if len(systems) != len(sys_with_cap):
            Logger.log_message(F'{self.action} action is supported only on {sys_with_cap}')
        return sys_with_cap

    def send_action_request(self,sys_with_cap):
        self.payload[ActionConstants.API_OBJECT_IDS] = sys_with_cap
        response = self.ufm_rest_client.send_request(ActionConstants.UFM_API_ACTIONS, HTTPMethods.POST,
                                                payload=self.payload)

        if response and response.status_code == HTTPStatus.ACCEPTED:
            Logger.log_message(F"{self.action} action is running on {sys_with_cap}!")
            job_id = self.job_polling.extract_job_id(response.text)
            self.job_polling.start_polling(job_id)
        else:
            Logger.log_message(response.text, LOG_LEVELS.ERROR)


    def run_action(self):
        try:
            url = ActionConstants.UFM_API_SYSTEMS + ('/'+self.object_ids if self.object_ids and len(self.object_ids) else '')
            response = self.ufm_rest_client.send_request(url, HTTPMethods.GET)
            if response and response.status_code == HTTPStatus.OK:
                sys_with_cap = self.get_supported_systems(response.json())
                self.send_action_request(sys_with_cap)
            else:
                Logger.log_message(response.text, LOG_LEVELS.ERROR)

        except Exception as ex:
            Logger.log_message(ex, LOG_LEVELS.ERROR)