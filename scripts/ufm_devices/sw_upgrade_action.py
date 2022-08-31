import logging
import platform
import os
from enum import Enum

try:
    from utils.utils import Utils
    from utils.args_parser import ArgsParser
    from utils.config_parser import ConfigParser
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


class SwUpgradeActionConstants:
    UFM_API_USER_NAME = "username"
    UFM_API_PASSWORD = "password"
    UFM_API_PATH = "path"
    UFM_API_IMAGE = "image"
    UFM_API_PROTOCOL = "protocol"
    UFM_API_SERVER = "server"
    ACTION = 'sw_upgrade'
    args_list = [
        {
            "name": f'--{ActionConstants.UFM_API_OBJECT_TYPE}',
            "help": "action object type, the default value is System",
        },
        {
            "name": f'--{ActionConstants.UFM_API_IDENTIFIER}',
            "help": "action identifier, the default value is id",
        },
        {
            "name": f'--{ActionConstants.API_OBJECT_IDS}',
            "help": "comma separated GUIDs if this arg was not provided the action will be run on all devices in UFM fabric",
        },
        {
            "name": f'--{ActionConstants.UFM_API_DESCRIPTION}',
            "help": "action description",
        },
        {
            "name": f'--{UFM_API_USER_NAME}',
            "help": "user name",
        },
        {
            "name": f'--{UFM_API_PASSWORD}',
            "help": "password",
        },
        {
            "name": f'--{UFM_API_PATH}',
            "help": "image path",
        },
        {
            "name": f'--{UFM_API_IMAGE}',
            "help": "image",
        },
        {
            "name": f'--{UFM_API_PROTOCOL}',
            "help": "protocol FTP or SCP",
        },
        {
            "name": f'--{UFM_API_SERVER}',
            "help": "IPv4 or IPv6",
        }

    ]


class SWProtocols(Enum):
    scp = "scp"
    ftp = "ftp"


class WrongSWProtocol(Exception):
    pass

class UfmSwUpgradeConfigParser(ConfigParser):
    config_file = "ufm_devices.cfg"

    UFM_SW_UPGRADE_SECTION= "ufm-devices-sw-upgrade"
    UFM_SW_UPGRADE_SECTION_OBJECT_IDS= "object_ids"
    UFM_SW_UPGRADE_SECTION_OBJECT_TYPE= "object_type"
    UFM_SW_UPGRADE_SECTION_ID= "identifier"
    UFM_SW_UPGRADE_SECTION_DESCRIPTION= "description"
    UFM_SW_UPGRADE_SECTION_USER_NAME= "remote_username"
    UFM_SW_UPGRADE_SECTION_PASSWORD= "remote_password"
    UFM_SW_UPGRADE_SECTION_PATH= "remote_path"
    UFM_SW_UPGRADE_SECTION_IMAGE= "image"
    UFM_SW_UPGRADE_SECTION_PROTOCOL= "protocol"
    UFM_SW_UPGRADE_SECTION_SERVER= "remote_server"

    def __init__(self,args):
        super().__init__(args)
        self.args_dict = self.args.__dict__
        self.sdk_config.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), self.config_file))

    def get_object_type(self):
        return self.get_config_value(self.args_dict.get(ActionConstants.UFM_API_OBJECT_TYPE),
                                     self.UFM_SW_UPGRADE_SECTION, self.UFM_SW_UPGRADE_SECTION_OBJECT_TYPE, 'System')
    def get_identifier(self):
        return self.get_config_value(self.args_dict.get(ActionConstants.UFM_API_IDENTIFIER),
                                     self.UFM_SW_UPGRADE_SECTION, self.UFM_SW_UPGRADE_SECTION_ID, 'id')
    def get_object_ids(self):
        return self.get_config_value(self.args_dict.get(ActionConstants.API_OBJECT_IDS),
                                     self.UFM_SW_UPGRADE_SECTION, self.UFM_SW_UPGRADE_SECTION_OBJECT_IDS, '')

    def get_description(self):
        return self.get_config_value(self.args_dict.get(ActionConstants.UFM_API_DESCRIPTION),
                                     self.UFM_SW_UPGRADE_SECTION, self.UFM_SW_UPGRADE_SECTION_DESCRIPTION, '')

    def get_user_name(self):
        return self.get_config_value(self.args_dict.get(SwUpgradeActionConstants.UFM_API_USER_NAME),
                                     self.UFM_SW_UPGRADE_SECTION, self.UFM_SW_UPGRADE_SECTION_USER_NAME)

    def get_password(self):
        return self.get_config_value(self.args_dict.get(SwUpgradeActionConstants.UFM_API_PASSWORD),
                                     self.UFM_SW_UPGRADE_SECTION, self.UFM_SW_UPGRADE_SECTION_PASSWORD)

    def get_path(self):
        return self.get_config_value(self.args_dict.get(SwUpgradeActionConstants.UFM_API_PATH),
                                     self.UFM_SW_UPGRADE_SECTION, self.UFM_SW_UPGRADE_SECTION_PATH)

    def get_image(self):
        return self.get_config_value(self.args_dict.get(SwUpgradeActionConstants.UFM_API_IMAGE),
                                     self.UFM_SW_UPGRADE_SECTION, self.UFM_SW_UPGRADE_SECTION_IMAGE)

    def get_protocol(self):
        sw_protocol =  self.get_config_value(self.args_dict.get(SwUpgradeActionConstants.UFM_API_PROTOCOL),
                                     self.UFM_SW_UPGRADE_SECTION, self.UFM_SW_UPGRADE_SECTION_PROTOCOL)
        if sw_protocol != SWProtocols.ftp.value and sw_protocol != SWProtocols.scp.value:
            raise WrongSWProtocol
        return sw_protocol
    def get_server(self):
        return self.get_config_value(self.args_dict.get(SwUpgradeActionConstants.UFM_API_SERVER),
                                     self.UFM_SW_UPGRADE_SECTION, self.UFM_SW_UPGRADE_SECTION_SERVER)



# if run as main module
if __name__ == "__main__":
    try:
        payload = None
        # init app args
        args = ArgsParser.parse_args("UFM Reboot", SwUpgradeActionConstants.args_list)
        args_dict = args.__dict__

        # init app config parser & load config files
        config_parser = UfmSwUpgradeConfigParser(args)

        # init logs configs
        logs_file_name = config_parser.get_logs_file_name()
        logs_level = config_parser.get_logs_level()
        max_log_file_size = config_parser.get_log_file_max_size()
        log_file_backup_count = config_parser.get_log_file_backup_count()
        Logger.init_logs_config(logs_file_name, logs_level, max_log_file_size, log_file_backup_count)

        # sw upgrade
        try:
            payload={
                ActionConstants.UFM_API_ACTION: SwUpgradeActionConstants.ACTION,
                ActionConstants.UFM_API_OBJECT_TYPE: config_parser.get_object_type(),
                ActionConstants.UFM_API_IDENTIFIER: config_parser.get_identifier(),
                ActionConstants.UFM_API_DESCRIPTION: config_parser.get_description(),
                ActionConstants.UFM_API_PARAMS:{
                    SwUpgradeActionConstants.UFM_API_USER_NAME: config_parser.get_user_name(),
                    SwUpgradeActionConstants.UFM_API_PASSWORD: config_parser.get_password(),
                    SwUpgradeActionConstants.UFM_API_PATH: config_parser.get_path(),
                    SwUpgradeActionConstants.UFM_API_IMAGE: config_parser.get_image(),
                    SwUpgradeActionConstants.UFM_API_PROTOCOL: config_parser.get_protocol(),
                    SwUpgradeActionConstants.UFM_API_SERVER: config_parser.get_server(),
                }
            }
            action = UfmDevicesAction(payload, config_parser.get_object_ids(), host=config_parser.get_ufm_host(),
                                      client_token=config_parser.get_ufm_access_token(),
                                      username=config_parser.get_ufm_username(),
                                      password=config_parser.get_ufm_password(),
                                      ws_protocol=config_parser.get_ufm_protocol())

            # run reboot action
            action.run_action()
        except WrongSWProtocol as e:
            ExceptionHandler.handel_exception("Invalid sw upgrade protocol,please enter a value scp or ftp")
        except ValueError as e:
            ExceptionHandler.handel_arg_exception(SwUpgradeActionConstants.ACTION,
                                            SwUpgradeActionConstants.UFM_API_USER_NAME,
                                            SwUpgradeActionConstants.UFM_API_PASSWORD,
                                            SwUpgradeActionConstants.UFM_API_PATH,
                                            SwUpgradeActionConstants.UFM_API_IMAGE,
                                            SwUpgradeActionConstants.UFM_API_PROTOCOL,
                                            SwUpgradeActionConstants.UFM_API_SERVER,
                                                  supported_in_config=True)



    except Exception as global_ex:
        logging.error(global_ex)