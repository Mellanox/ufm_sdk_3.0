import platform
import os
import logging
from tabulate import tabulate

try:
    from utils.utils import Utils
    from utils.args_parser import ArgsParser
    from utils.config_parser import ConfigParser
    from utils.ufm_rest_client import UfmRestClient, HTTPMethods
    from http import HTTPStatus
    from utils.logger import Logger, LOG_LEVELS
    from scripts.ufm_devices.ufm_devices_action import UfmDevicesAction, ActionConstants
    from utils.exception_handler import ExceptionHandler
except ModuleNotFoundError as e:
    if platform.system() == "Windows":
        print("Error occurred while importing python modules, "
              "Please make sure that you exported your repository to PYTHONPATH by running: "
              f'set PYTHONPATH=%PYTHONPATH%;{os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))}')
    else:
        print("Error occurred while importing python modules, "
              "Please make sure that you exported your repository to PYTHONPATH by running: "
              f'export PYTHONPATH="${{PYTHONPATH}}:{os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))}"')


class TopXErrorMessages(object):
    Invalid_Mode = f"Invalid Topx Mode, please enter one of the following %s"
    Invalid_Member_type = f"Invalid Topx Members Type, please enter one of the following %s"


class UFMAggrTopXConstants:
    UFM_AGGR_TOPX_TITLE = "UFM Aggr TopX"
    UFM_API_AGGR_TOPX = "monitoring/aggr_topx"
    ATTR_OBJECT = "object"
    ATTR_ATTR = "attr"
    ATTR_MODE = "mode"
    ATTR_MEMBERS_TYPE = "members_type"
    ATTR_DATA = "data"
    ATTR_VALUE = "value"
    ATTR_NAME = "name"
    ATTR_DESCRIPTION = "description"

    TOPX_ATTRS_INFO = {
        'bw': {
            'available_modes': ['TxBW', 'RxBW'],
            'available_members_type': ['device', 'port']
        },
        'cong': {
            'available_modes': ['TCBW', 'RCBW'],
            'available_members_type': ['device', 'port']
        },
        'alarms': {
            'available_modes': ['Alarms'],
            'available_members_type': ['device'],
            'default_mode': 'Alarms',
            'default_members_type': 'device'
        }
    }
    args_list = [
        {
            "name": f'--{ATTR_OBJECT}',
            "help": "values are servers or switches. will send to server as GET param",
        },
        {
            "name": f'--{ATTR_ATTR}',
            "help": "values are bw, cong or alarms. will send to server as GET param",
        },
        {
            "name": f'--{ATTR_MODE}',
            "help": "in the response each object(port/device) will have both RxBW and TxBW",
        },
        {
            "name": f'--{ATTR_MEMBERS_TYPE}',
            "help": "in the response the data with have both device and port",
        }
    ]


class UfmAggrTopXConfigParser(ConfigParser):
    config_file = "ufm_aggr_topx.cfg"

    UFM_TOPX_SECTION = "ufm-aggr-topx"
    UFM_TOPX_SECTION_OBJECT = "object"
    UFM_TOPX_SECTION_ATTR = "attr"
    UFM_TOPX_SECTION_MODE = "mode"
    UFM_TOPX_SECTION_MEMBERS_TYPE = "members_type"

    def __init__(self, args):
        super().__init__(args)
        self.args_dict = self.args.__dict__
        self.sdk_config.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), self.config_file))

    def get_object(self):
        return self.get_config_value(self.args_dict.get(UFMAggrTopXConstants.ATTR_OBJECT),
                                     self.UFM_TOPX_SECTION, self.UFM_TOPX_SECTION_OBJECT)

    def get_attr(self):
        return self.get_config_value(self.args_dict.get(UFMAggrTopXConstants.ATTR_ATTR),
                                     self.UFM_TOPX_SECTION, self.UFM_TOPX_SECTION_ATTR)

    def get_mode(self, attr=None):
        value = self.get_config_value(self.args_dict.get(UFMAggrTopXConstants.ATTR_MODE),
                                      self.UFM_TOPX_SECTION, self.UFM_TOPX_SECTION_MODE,
                                      UFMAggrTopXConstants.TOPX_ATTRS_INFO[attr]['default_mode'] if
                                      attr in UFMAggrTopXConstants.TOPX_ATTRS_INFO and 'default_mode' in
                                      UFMAggrTopXConstants.TOPX_ATTRS_INFO[attr]
                                      else None)

        if attr not in UFMAggrTopXConstants.TOPX_ATTRS_INFO or value in UFMAggrTopXConstants.TOPX_ATTRS_INFO[attr][
            'available_modes']:
            return value
        else:
            ExceptionHandler.handel_exception(
                TopXErrorMessages.Invalid_Member_type % UFMAggrTopXConstants.TOPX_ATTRS_INFO[attr][
                    'available_modes'])

    def get_members_type(self, attr):
        value = self.get_config_value(self.args_dict.get(UFMAggrTopXConstants.ATTR_MEMBERS_TYPE),
                                      self.UFM_TOPX_SECTION, self.UFM_TOPX_SECTION_MEMBERS_TYPE,
                                      UFMAggrTopXConstants.TOPX_ATTRS_INFO[attr]['default_members_type'] if
                                      attr in UFMAggrTopXConstants.TOPX_ATTRS_INFO and 'default_members_type' in
                                      UFMAggrTopXConstants.TOPX_ATTRS_INFO[attr]
                                      else None)
        if attr not in UFMAggrTopXConstants.TOPX_ATTRS_INFO or value in UFMAggrTopXConstants.TOPX_ATTRS_INFO[attr][
            'available_members_type']:
            return value
        else:
            ExceptionHandler.handel_exception(
                TopXErrorMessages.Invalid_Member_type % UFMAggrTopXConstants.TOPX_ATTRS_INFO[attr][
                    'available_members_type'])


class UfmAggrTopX:
    def __init__(self, ufm_rest_client, object_type, attr, mode, members_type):
        # init ufm rest client
        self.ufm_rest_client = ufm_rest_client
        self.object_type = object_type
        self.attr = attr
        self.mode = mode
        self.members_type = members_type

    def send_topX_request(self):
        url = f'{UFMAggrTopXConstants.UFM_API_AGGR_TOPX}?{UFMAggrTopXConstants.ATTR_OBJECT}={self.object_type}&{UFMAggrTopXConstants.ATTR_ATTR}={self.attr}'
        response = ufm_rest_client.send_request(url, HTTPMethods.GET)

        if response and response.status_code == HTTPStatus.OK:
            data = response.json()[UFMAggrTopXConstants.ATTR_DATA][self.members_type][self.mode]
            rows = []
            for item in data:
                row = [item[UFMAggrTopXConstants.ATTR_NAME], item[UFMAggrTopXConstants.ATTR_DESCRIPTION],
                       item[UFMAggrTopXConstants.ATTR_VALUE]]
                rows.append(row)
            Logger.log_message(tabulate(rows, headers=['Name', 'Description', 'Value']))

        else:
            Logger.log_message(response.text, LOG_LEVELS.ERROR)


# if run as main module
if __name__ == "__main__":
    try:
        # init app args
        args = ArgsParser.parse_args(UFMAggrTopXConstants.UFM_AGGR_TOPX_TITLE, UFMAggrTopXConstants.args_list)
        args_dict = args.__dict__
        # init app config parser & load config files
        config_parser = UfmAggrTopXConfigParser(args)
        try:
            # ufm aggr topx args
            attr = config_parser.get_attr()
            object_type = config_parser.get_object()
            mode = config_parser.get_mode(attr)
            members_type = config_parser.get_members_type(attr)
            # init logs configs
            logs_file_name = config_parser.get_logs_file_name()
            logs_level = config_parser.get_logs_level()
            max_log_file_size = config_parser.get_log_file_max_size()
            log_file_backup_count = config_parser.get_log_file_backup_count()
            Logger.init_logs_config(logs_file_name, logs_level, max_log_file_size, log_file_backup_count)

        except ValueError as e:
            ExceptionHandler.handel_arg_exception(UFMAggrTopXConstants.UFM_AGGR_TOPX_TITLE,
                                                  UFMAggrTopXConstants.ATTR_OBJECT,
                                                  UFMAggrTopXConstants.ATTR_ATTR,
                                                  UFMAggrTopXConstants.ATTR_MODE,
                                                  UFMAggrTopXConstants.ATTR_MEMBERS_TYPE,
                                                  supported_in_config=True)

        # init ufm rest client
        ufm_rest_client = UfmRestClient(host=config_parser.get_ufm_host(),
                                        client_token=config_parser.get_ufm_access_token(),
                                        username=config_parser.get_ufm_username(),
                                        password=config_parser.get_ufm_password(),
                                        ws_protocol=config_parser.get_ufm_protocol())
        # init UfmAggrTopX
        ufmTopX = UfmAggrTopX(ufm_rest_client, object_type, attr, mode, members_type)
        ufmTopX.send_topX_request()

    except Exception as global_ex:
        logging.error(global_ex)
