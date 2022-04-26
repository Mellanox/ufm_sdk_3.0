import logging
import time
from http import HTTPStatus
import re

try:
    from utils.utils import Utils
    from utils.ufm_rest_client import UfmRestClient, HTTPMethods
    from utils.logger import Logger, LOG_LEVELS
except ModuleNotFoundError as e:
    print("Error occurred while importing python modules, "
          "Please make sure that you exported your repository to PYTHONPATH by running: "
          f'export PYTHONPATH="${{PYTHONPATH}}:{os.path.dirname(os.getcwd())}"')



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
    API_JOB_COMPLETED = "Completed"
    API_JOB_COMPLETED_ERRORS = "Completed With Errors"
    API_JOB_COMPLETED_WARNINGS = "Completed With Warnings"
    API_JOB_RUNNING = "Running"
    API_JOB_STATUS = "Status"
    API_JOB_SUMMARY = "Summary"
    API_JOB_ID = "ID"


class UfmAction(object):

    def __init__(self,payload,object_ids=None, host=None,client_token=None, username=None, password=None,ws_protocol=None):
        self.action = payload["action"]
        self.object_ids = object_ids
        self.payload = payload
        # init ufm rest client
        self.ufm_rest_client = UfmRestClient(host=host,
                                        client_token=client_token, username=username, password=password,ws_protocol=ws_protocol)

    def get_supported_systems(self,systems):
        sys_with_cap = []
        for sys in systems:
            if self.action in sys[ActionConstants.API_CAPABILITIES]:
                sys_with_cap.append(sys[ActionConstants.API_GUID])

        if not sys_with_cap or not len(sys_with_cap):
            raise ValueError(F"systems {self.object_ids} don't support reboot {self.action}")
        if len(systems) != len(sys_with_cap):
            Logger.log_message(F'{self.action} action is supported only on {sys_with_cap}')
        return sys_with_cap

    def send_action_request(self,sys_with_cap):
        self.payload[ActionConstants.API_OBJECT_IDS] = sys_with_cap
        response = self.ufm_rest_client.send_request(ActionConstants.UFM_API_ACTIONS, HTTPMethods.POST,
                                                payload=self.payload)

        if response and response.status_code == HTTPStatus.ACCEPTED:
            Logger.log_message(F"{self.action} action is running on {sys_with_cap}!")
            job_url = re.search(r'\b/jobs/[0-9]*\b', response.text).group(0)
            self.job_polling(job_url)
        else:
            Logger.log_message(response.text, LOG_LEVELS.ERROR)

    def job_polling(self,job_url):
        try:
            job_is_completed = False
            job_status = None
            while not job_is_completed:
                time.sleep(3)
                job_response = self.ufm_rest_client.send_request(job_url)
                if job_response.raise_for_status():
                    break
                job_response = job_response.json()
                job_status = job_response[ActionConstants.API_JOB_STATUS]
                job_is_completed = job_status != ActionConstants.API_JOB_RUNNING
            if job_status == ActionConstants.API_JOB_COMPLETED:
                Logger.log_message(f"{self.action} action completed successfully!")

            elif job_status == ActionConstants.API_JOB_COMPLETED_ERRORS or job_status == ActionConstants.API_JOB_COMPLETED_WARNINGS:
                self.print_sub_jobs_summary(job_url.split('/').pop())

        except Exception as e:
            logging.error(f'Error in job polling: {e}')

    def print_sub_jobs_summary(self, job_id):
        sub_job_response = self.ufm_rest_client.send_request('jobs?parent_id='+job_id)
        if sub_job_response and sub_job_response.status_code == HTTPStatus.OK:
            for sub_job in sub_job_response.json():
                Logger.log_message(f"{sub_job[ActionConstants.API_JOB_ID]}: {sub_job[ActionConstants.API_JOB_SUMMARY]}",
                                   LOG_LEVELS.ERROR)
        else:
            Logger.log_message(sub_job_response.text, LOG_LEVELS.ERROR)

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
            logging.error(ex)