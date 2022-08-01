import os
import platform
from http import HTTPStatus

from utils.report_polling import ReportPolling

try:
    from utils.utils import Utils
    from utils.ufm_rest_client import UfmRestClient, HTTPMethods
    from utils.args_parser import ArgsParser
    from utils.config_parser import ConfigParser
    from utils.logger import Logger, LOG_LEVELS
except ModuleNotFoundError as e:
    if platform.system() == "Windows":
        print("Error occurred while importing python modules, "
              "Please make sure that you exported your repository to PYTHONPATH by running: "
              f'set PYTHONPATH=%PYTHONPATH%;{os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))}')
    else:
        print("Error occurred while importing python modules, "
              "Please make sure that you exported your repository to PYTHONPATH by running: "
              f'export PYTHONPATH="${{PYTHONPATH}}:{os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))}"')


class UfmHealthConstants:
    UFM_HEALTH_REPORT_API_URL = 'reports/UFM_Health'
    UFM_HEALTH_REPORT_RESULT_PATH = 'report_result/'


class UfmHealthConfigParser(ConfigParser):

    def __init__(self, args):
        super().__init__(args)


class UfmHealthReport:

    @staticmethod
    def run_report(output_path):
        response = ufm_rest_client.send_request(UfmHealthConstants.UFM_HEALTH_REPORT_API_URL, HTTPMethods.POST)
        if response and response.status_code == HTTPStatus.ACCEPTED:
            report_id = response.json()['report_id']
            report_polling = ReportPolling(ufm_rest_client)
            report_polling.start_polling(report_id, output_path)


if __name__ == "__main__":
    # init app args
    args = ArgsParser.parse_args("UFM Health Report", [])

    # init app config parser & load config files
    config_parser = UfmHealthConfigParser(args)

    # init logs configs
    logs_file_name = config_parser.get_logs_file_name()
    logs_level = config_parser.get_logs_level()
    Logger.init_logs_config(logs_file_name, logs_level)

    # init ufm rest client
    ufm_rest_client = UfmRestClient(host=config_parser.get_ufm_host(),
                                    client_token=config_parser.get_ufm_access_token(),
                                    username=config_parser.get_ufm_username(),
                                    password=config_parser.get_ufm_password(),
                                    ws_protocol=config_parser.get_ufm_protocol())

    UfmHealthReport.run_report(UfmHealthConstants.UFM_HEALTH_REPORT_RESULT_PATH)
