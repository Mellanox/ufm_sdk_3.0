import logging
import time
from http import HTTPStatus
import sys
import threading
import re
from utils.logger import Logger, LOG_LEVELS


class JobsConstants:
    UFM_API_JOBS="jobs"
    UFM_API_JOBS_PARENT_ID_PARAM="parent_id"

    API_JOB_COMPLETED = "Completed"
    API_JOB_COMPLETED_ERRORS = "Completed With Errors"
    API_JOB_COMPLETED_WARNINGS = "Completed With Warnings"
    API_JOB_RUNNING = "Running"
    API_JOB_STATUS = "Status"
    API_JOB_SUMMARY = "Summary"
    API_JOB_ID = "ID"


class JobPolling(object):
    def __init__(self, ufm_rest_client, operation):
        self.ufm_rest_client = ufm_rest_client
        self.action_inprogress = False
        self.operation = operation

    def start_polling(self, job_id, print_summary=False):
        try:
            self.action_inprogress = True
            t = self.create_loading_thread()
            job_is_completed = False
            job_status = None
            while not job_is_completed:
                time.sleep(3)
                job_response = self.ufm_rest_client.send_request(f"{JobsConstants.UFM_API_JOBS}/{job_id}")
                if job_response.raise_for_status():
                    break
                job_response = job_response.json()
                job_status = job_response[JobsConstants.API_JOB_STATUS]
                job_is_completed = job_status != JobsConstants.API_JOB_RUNNING
            self.action_inprogress = False
            # move to new line after to avoid prining load icon and the message in the same line
            print(f" ", end='\n')
            if job_status == JobsConstants.API_JOB_COMPLETED:
                Logger.log_message(f"{self.operation} completed successfully!")
                if print_summary:
                    self.print_sub_jobs_summary(job_id)

            elif job_status == JobsConstants.API_JOB_COMPLETED_ERRORS or job_status == JobsConstants.API_JOB_COMPLETED_WARNINGS:
                self.print_sub_jobs_summary(job_id)

        except Exception as e:
            self.action_inprogress = False
            logging.error(f'Error in job polling: {e}')

    def create_loading_thread(self):
        t = threading.Thread(target=self.print_loading_message)
        t.daemon = True
        t.start()
        return t

    def print_loading_message(self):
        icon_list = [' | ', ' / ', ' \\ ']
        while self.action_inprogress:
            for icon in icon_list:
                time.sleep(.5)
                print(f"\r{' '}\r", end='')
                print(icon, end='')
                sys.stdout.flush()
            sys.stdout.flush()

    def print_sub_jobs_summary(self, job_id):
        sub_job_response = self.ufm_rest_client.send_request(f'{JobsConstants.UFM_API_JOBS}?{JobsConstants.UFM_API_JOBS_PARENT_ID_PARAM}={job_id}')
        if sub_job_response and sub_job_response.status_code == HTTPStatus.OK:
            for sub_job in sub_job_response.json():
                Logger.log_message(f"{sub_job[JobsConstants.API_JOB_ID]}: {sub_job[JobsConstants.API_JOB_SUMMARY]}",
                                   LOG_LEVELS.ERROR)
        else:
            Logger.log_message(sub_job_response.text, LOG_LEVELS.ERROR)

    def extract_job_id(self, job_url):
        try:
            job_regex_group = re.search(r'\b/jobs/([0-9]*)\b', job_url).groups()
            job_id_list = list(job_regex_group)
            return job_id_list[0]
        except Exception as e:
            logging.error(e)
