import logging
import sys
import threading
import time
from http import HTTPStatus

import requests

from utils.logger import Logger
from utils.utils import Utils


class ReportsConstants:
    UFM_API_REPORTS = 'reports'


class ReportPolling(object):
    def __init__(self, ufm_rest_client):
        self.ufm_rest_client = ufm_rest_client
        self.action_inprogress = False

    def start_polling(self, report_id, output_file=None):
        try:
            self.action_inprogress = True
            t = self.create_loading_thread()
            report_status = None
            while report_status != HTTPStatus.OK:
                time.sleep(3)
                report_response = self.ufm_rest_client.send_request(f"{ReportsConstants.UFM_API_REPORTS}/{report_id}")
                try:
                    report_response.raise_for_status()
                except requests.exceptions.HTTPError as e:
                    self.action_inprogress = False
                    logging.error(f'Error in report polling: {e}')
                    break
                report_status = report_response.status_code
            self.action_inprogress = False
            # move to new line after to avoid prining load icon and the message in the same line
            print(f" ", end='\n')
            print(report_response.json())
            Logger.log_message(f"Report {report_id}: {report_response.json()}")
            if output_file:
                Utils.write_json_to_file(f'{output_file}Report_{time.strftime("%Y%m%d-%H%M%S")}.json',
                                         report_response.json())

        except Exception as e:
            self.action_inprogress = False
            logging.error(f'Error in report polling: {e}')

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
