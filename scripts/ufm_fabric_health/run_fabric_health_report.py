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


class UfmFabricHealthConstants:
    FABRIC_REPORT_RESULT_PATH = 'report_result/'
    FABRIC_REPORT_API_URL = 'reports/Fabric_Health'
    REPORTS_API_URL = 'reports'

    UFM_FABRIC_SECTION_DUPLICATE_NODES = "duplicate_nodes"
    UFM_FABRIC_SECTION_MAP_GUIDS_DESC = "map_guids_desc"

    UFM_FABRIC_SECTION_CABLES = "cables"
    UFM_FABRIC_SECTION_CABLES_ERRORS_ONLY = "cables_errors_only"

    UFM_FABRIC_SECTION_DUPLICATE_ZERO_AND_LIDS = "duplicate_zero_and_lids"
    UFM_FABRIC_SECTION_NON_OPT_LINKS = "non_opt_links"
    UFM_FABRIC_SECTION_NON_OPT_SPEED_WIDTH = "non_opt_speed_width"
    UFM_FABRIC_SECTION_LINK_SPEED = "link_speed"
    UFM_FABRIC_SECTION_LINK_WIDTH = "link_width"
    UFM_FABRIC_SECTION_EFFECTIVE_BER_CHECK = "effective_ber_check"
    UFM_FABRIC_SECTION_SYMBOL_BER_CHECK = "symbol_ber_check"
    UFM_FABRIC_SECTION_PHY_PORT_GRADE = "phy_port_grade"

    UFM_FABRIC_SECTION_EYE_OPEN = "eye_open"
    UFM_FABRIC_SECTION_MIN_BOUND = "min_bound"
    UFM_FABRIC_SECTION_MAX_BOUND = "max_bound"
    UFM_FABRIC_SECTION_EYE_OPEN_ERRORS_ONLY = "eye_open_errors_only"

    UFM_FABRIC_SECTION_FIRMWARE = "firmware"

    UFM_FABRIC_SECTION_SM_STATE = "sm_state"

    UFM_FABRIC_SECTION_ALARMS = "ufm_alarms"

    args_list = [
        {
            "name": f'--{UFM_FABRIC_SECTION_DUPLICATE_NODES}',
            "help": "Duplicated Node Description"
        },
        {
            "name": f'--{UFM_FABRIC_SECTION_MAP_GUIDS_DESC}',
            "help": "Use Node Guid-Description Mapping"
        },
        {
            "name": f'--{UFM_FABRIC_SECTION_CABLES}',
            "help": "Cable Type Check & Cable Diagnostics"
        },
        {
            "name": f'--{UFM_FABRIC_SECTION_CABLES_ERRORS_ONLY}',
            "help": "Show Cable Errors And Warnings Only"
        },
        {
            "name": f'--{UFM_FABRIC_SECTION_DUPLICATE_ZERO_AND_LIDS}',
            "help": "Duplicate/Zero LIDs Check"
        },
        {
            "name": f'--{UFM_FABRIC_SECTION_NON_OPT_LINKS}',
            "help": "Non-Optimal Links Check"
        },
        {
            "name": f'--{UFM_FABRIC_SECTION_NON_OPT_SPEED_WIDTH}',
            "help": "Non-Optimal Speed And Width"
        },
        {
            "name": f'--{UFM_FABRIC_SECTION_LINK_SPEED}',
            "help": "Link Speed",
        },
        {
            "name": f'--{UFM_FABRIC_SECTION_LINK_WIDTH}',
            "help": "Link Width"
        },
        {
            "name": f'--{UFM_FABRIC_SECTION_EFFECTIVE_BER_CHECK}',
            "help": "Effective Ber Check"
        },
        {
            "name": f'--{UFM_FABRIC_SECTION_SYMBOL_BER_CHECK}',
            "help": "Symbol Ber Check"
        },
        {
            "name": f'--{UFM_FABRIC_SECTION_PHY_PORT_GRADE}',
            "help": "Physical Port Grade"
        },
        {
            "name": f'--{UFM_FABRIC_SECTION_EYE_OPEN}',
            "help": "Eye Open Check"
        },
        {
            "name": f'--{UFM_FABRIC_SECTION_MIN_BOUND}',
            "help": "Minimum Port Bound"
        },
        {
            "name": f'--{UFM_FABRIC_SECTION_MAX_BOUND}',
            "help": "Maximum Port Bound"
        },
        {
            "name": f'--{UFM_FABRIC_SECTION_EYE_OPEN_ERRORS_ONLY}',
            "help": "Show Errors And Warnings Only For Eye Open Check"
        },
        {
            "name": f'--{UFM_FABRIC_SECTION_FIRMWARE}',
            "help": "Firmware Version Check"
        },
        {
            "name": f'--{UFM_FABRIC_SECTION_SM_STATE}',
            "help": "SM Configuration Check"
        },
        {
            "name": f'--{UFM_FABRIC_SECTION_ALARMS}',
            "help": "UFM Alarms"
        }
    ]


class UfmFabricHealthConfigParser(ConfigParser):
    config_file = "fabric_health.cfg"

    UFM_FABRIC_SECTION = "fabric-health"


    def __init__(self, args):
        super().__init__(args)
        self.sdk_config.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), self.config_file))

    def get_duplicate_nodes(self):
        return self.safe_get_bool(self.args.duplicate_nodes,
                                  self.UFM_FABRIC_SECTION,
                                  UfmFabricHealthConstants.UFM_FABRIC_SECTION_DUPLICATE_NODES,
                                  False)

    def get_cables_errors_only(self):
        return self.safe_get_bool(self.args.cables_errors_only,
                                  self.UFM_FABRIC_SECTION,
                                  UfmFabricHealthConstants.UFM_FABRIC_SECTION_CABLES_ERRORS_ONLY,
                                  True)

    def get_cables(self):
        return self.safe_get_bool(self.args.cables,
                                  self.UFM_FABRIC_SECTION,
                                  UfmFabricHealthConstants.UFM_FABRIC_SECTION_CABLES,
                                  True)

    def get_duplicate_zero_and_lids(self):
        return self.safe_get_bool(self.args.duplicate_zero_and_lids,
                                  self.UFM_FABRIC_SECTION,
                                  UfmFabricHealthConstants.UFM_FABRIC_SECTION_DUPLICATE_ZERO_AND_LIDS,
                                  False)

    def get_non_opt_links(self):
        return self.safe_get_bool(self.args.non_opt_links,
                                  self.UFM_FABRIC_SECTION,
                                  UfmFabricHealthConstants.UFM_FABRIC_SECTION_NON_OPT_LINKS,
                                  False)

    def get_non_opt_speed_width(self):
        return self.safe_get_bool(self.args.non_opt_speed_width,
                                  self.UFM_FABRIC_SECTION,
                                  UfmFabricHealthConstants.UFM_FABRIC_SECTION_NON_OPT_SPEED_WIDTH,
                                  False)

    def get_link_speed(self):
        return self.get_config_value(self.args.link_speed,
                                     self.UFM_FABRIC_SECTION,
                                     UfmFabricHealthConstants.UFM_FABRIC_SECTION_LINK_SPEED,
                                     "ALL")

    def get_link_width(self):
        return self.get_config_value(self.args.link_width,
                                     self.UFM_FABRIC_SECTION,
                                     UfmFabricHealthConstants.UFM_FABRIC_SECTION_LINK_WIDTH,
                                     "ALL")

    def get_effective_ber_check(self):
        return self.safe_get_bool(self.args.effective_ber_check,
                                  self.UFM_FABRIC_SECTION,
                                  UfmFabricHealthConstants.UFM_FABRIC_SECTION_EFFECTIVE_BER_CHECK,
                                  False)

    def get_symbol_ber_check(self):
        return self.safe_get_bool(self.args.symbol_ber_check,
                                  self.UFM_FABRIC_SECTION,
                                  UfmFabricHealthConstants.UFM_FABRIC_SECTION_SYMBOL_BER_CHECK,
                                  False)

    def get_phy_port_grade(self):
        return self.safe_get_bool(self.args.phy_port_grade,
                                  self.UFM_FABRIC_SECTION,
                                  UfmFabricHealthConstants.UFM_FABRIC_SECTION_PHY_PORT_GRADE,
                                  False)

    def get_eye_open(self):
        return self.safe_get_bool(self.args.eye_open,
                                  self.UFM_FABRIC_SECTION,
                                  UfmFabricHealthConstants.UFM_FABRIC_SECTION_EYE_OPEN,
                                  False)

    def get_min_bound(self):
        return self.safe_get_int(self.args.min_bound,
                                 self.UFM_FABRIC_SECTION,
                                 UfmFabricHealthConstants.UFM_FABRIC_SECTION_MIN_BOUND,
                                 22)

    def get_max_bound(self):
        return self.safe_get_int(self.args.max_bound,
                                 self.UFM_FABRIC_SECTION,
                                 UfmFabricHealthConstants.UFM_FABRIC_SECTION_MAX_BOUND,
                                 65)

    def get_eye_open_errors_only(self):
        return self.safe_get_bool(self.args.eye_open_errors_only,
                                  self.UFM_FABRIC_SECTION,
                                  UfmFabricHealthConstants.UFM_FABRIC_SECTION_EYE_OPEN_ERRORS_ONLY,
                                  False)

    def get_firmware(self):
        return self.safe_get_bool(self.args.firmware,
                                  self.UFM_FABRIC_SECTION,
                                  UfmFabricHealthConstants.UFM_FABRIC_SECTION_FIRMWARE,
                                  False)

    def get_map_guids_desc(self):
        return self.safe_get_bool(self.args.map_guids_desc,
                                  self.UFM_FABRIC_SECTION,
                                  UfmFabricHealthConstants.UFM_FABRIC_SECTION_MAP_GUIDS_DESC,
                                  False)

    def get_sm_state(self):
        return self.safe_get_bool(self.args.sm_state,
                                  self.UFM_FABRIC_SECTION,
                                  UfmFabricHealthConstants.UFM_FABRIC_SECTION_SM_STATE,
                                  False)

    def get_ufm_alarms(self):
        return self.safe_get_bool(self.args.ufm_alarms,
                                  self.UFM_FABRIC_SECTION,
                                  UfmFabricHealthConstants.UFM_FABRIC_SECTION_ALARMS,
                                  False)


class UfmFabricHealthReport:

        @staticmethod
        def run_report(payload, output_file):
            response = ufm_rest_client.send_request(UfmFabricHealthConstants.FABRIC_REPORT_API_URL, HTTPMethods.POST, payload=payload)
            if response and response.status_code == HTTPStatus.ACCEPTED:
                report_id = response.json()['report_id']
                report_polling = ReportPolling(ufm_rest_client)
                report_polling.start_polling(report_id, output_file)

        @staticmethod
        def prepare_request_data(conf_parser):
            payload = {
                UfmFabricHealthConstants.UFM_FABRIC_SECTION_DUPLICATE_NODES: conf_parser.get_duplicate_nodes(),
                UfmFabricHealthConstants.UFM_FABRIC_SECTION_CABLES: conf_parser.get_cables(),
                UfmFabricHealthConstants.UFM_FABRIC_SECTION_DUPLICATE_ZERO_AND_LIDS: conf_parser.get_duplicate_zero_and_lids(),
                UfmFabricHealthConstants.UFM_FABRIC_SECTION_NON_OPT_LINKS: conf_parser.get_non_opt_links(),
                UfmFabricHealthConstants.UFM_FABRIC_SECTION_NON_OPT_SPEED_WIDTH: conf_parser.get_non_opt_speed_width(),
                UfmFabricHealthConstants.UFM_FABRIC_SECTION_EFFECTIVE_BER_CHECK: conf_parser.get_effective_ber_check(),
                UfmFabricHealthConstants.UFM_FABRIC_SECTION_SYMBOL_BER_CHECK: conf_parser.get_symbol_ber_check(),
                UfmFabricHealthConstants.UFM_FABRIC_SECTION_PHY_PORT_GRADE: conf_parser.get_phy_port_grade(),
                UfmFabricHealthConstants.UFM_FABRIC_SECTION_EYE_OPEN: conf_parser.get_eye_open(),
                UfmFabricHealthConstants.UFM_FABRIC_SECTION_FIRMWARE: conf_parser.get_firmware(),
                UfmFabricHealthConstants.UFM_FABRIC_SECTION_SM_STATE: conf_parser.get_sm_state(),
                UfmFabricHealthConstants.UFM_FABRIC_SECTION_ALARMS: conf_parser.get_ufm_alarms()
            }

            if conf_parser.get_duplicate_nodes():
                payload[UfmFabricHealthConstants.UFM_FABRIC_SECTION_MAP_GUIDS_DESC] = conf_parser.get_map_guids_desc()
            if conf_parser.get_non_opt_speed_width():
                payload[UfmFabricHealthConstants.UFM_FABRIC_SECTION_LINK_SPEED] = conf_parser.get_link_speed()
                payload[UfmFabricHealthConstants.UFM_FABRIC_SECTION_LINK_SPEED] = conf_parser.get_link_width()
            if conf_parser.get_eye_open():
                payload[UfmFabricHealthConstants.UFM_FABRIC_SECTION_MIN_BOUND] = conf_parser.get_min_bound(),
                payload[UfmFabricHealthConstants.UFM_FABRIC_SECTION_MAX_BOUND] = conf_parser.get_max_bound(),
                payload[UfmFabricHealthConstants.UFM_FABRIC_SECTION_EYE_OPEN_ERRORS_ONLY] = conf_parser.get_eye_open_errors_only()
            if conf_parser.get_cables():
                payload[UfmFabricHealthConstants.UFM_FABRIC_SECTION_CABLES_ERRORS_ONLY] = conf_parser.get_cables_errors_only()
            return payload


if __name__ == "__main__":

    # init app args
    args = ArgsParser.parse_args("UFM Fabric Health", UfmFabricHealthConstants.args_list)

    # init app config parser & load config files
    config_parser = UfmFabricHealthConfigParser(args)

    # init logs configs
    logs_file_name = config_parser.get_logs_file_name()
    logs_level = config_parser.get_logs_level()
    max_log_file_size = config_parser.get_log_file_max_size()
    log_file_backup_count = config_parser.get_log_file_backup_count()
    Logger.init_logs_config(logs_file_name, logs_level, max_log_file_size, log_file_backup_count)


    # init ufm rest client
    ufm_rest_client = UfmRestClient(host = config_parser.get_ufm_host(),
                                    client_token=config_parser.get_ufm_access_token(),username = config_parser.get_ufm_username(),
                                    password = config_parser.get_ufm_password(),ws_protocol=config_parser.get_ufm_protocol())

    payload = UfmFabricHealthReport.prepare_request_data(config_parser)

    UfmFabricHealthReport.run_report(payload, UfmFabricHealthConstants.FABRIC_REPORT_RESULT_PATH)


