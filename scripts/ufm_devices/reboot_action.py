import platform
import os
import logging

try:
    from utils.utils import Utils
    from utils.args_parser import ArgsParser
    from utils.config_parser import ConfigParser
    from utils.logger import Logger, LOG_LEVELS
    from scripts.ufm_devices.ufm_devices_action import UfmDevicesAction, ActionConstants
except ModuleNotFoundError as e:
    if platform.system() == "Windows":
        print("Error occurred while importing python modules, "
              "Please make sure that you exported your repository to PYTHONPATH by running: "
              f'set PYTHONPATH=%PYTHONPATH%;{os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))}')
    else:
        print("Error occurred while importing python modules, "
              "Please make sure that you exported your repository to PYTHONPATH by running: "
              f'export PYTHONPATH="${{PYTHONPATH}}:{os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))}"')


class RebootActionConstants:
    ACTION = "reboot"
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
        }
    ]


class UfmRebootConfigParser(ConfigParser):
    config_file = "ufm_devices.cfg"

    UFM_REBOOT_SECTION = "ufm-devices-reboot"
    UFM_REBOOT_SECTION_OBJECT_IDS = "object_ids"
    UFM_REBOOT_SECTION_OBJECT_TYPE = "object_type"
    UFM_REBOOT_SECTION_ID = "identifier"
    UFM_SW_UPGRADE_SECTION_DESCRIPTION= "description"

    def __init__(self,args):
        super().__init__(args)
        self.args_dict = self.args.__dict__
        self.sdk_config.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), self.config_file))

    def get_object_type(self):
        return self.get_config_value(self.args_dict.get(ActionConstants.UFM_API_OBJECT_TYPE),
                                     self.UFM_REBOOT_SECTION, self.UFM_REBOOT_SECTION_OBJECT_TYPE, 'System')

    def get_identifier(self):
        return self.get_config_value(self.args_dict.get(ActionConstants.UFM_API_IDENTIFIER),
                                     self.UFM_REBOOT_SECTION, self.UFM_REBOOT_SECTION_ID, 'id')

    def get_object_ids(self):
        return self.get_config_value(self.args_dict.get(ActionConstants.API_OBJECT_IDS),
                                     self.UFM_REBOOT_SECTION, self.UFM_REBOOT_SECTION_OBJECT_IDS, '')

    def get_description(self):
        return self.get_config_value(self.args_dict.get(ActionConstants.UFM_API_DESCRIPTION),
                                     self.UFM_REBOOT_SECTION, self.UFM_SW_UPGRADE_SECTION_DESCRIPTION, '')

# if run as main module
if __name__ == "__main__":
    try:
        # init app args
        args = ArgsParser.parse_args("UFM Reboot", RebootActionConstants.args_list)
        args_dict = args.__dict__

        # init app config parser & load config files
        config_parser = UfmRebootConfigParser(args)

        # init logs configs
        logs_file_name = config_parser.get_logs_file_name()
        logs_level = config_parser.get_logs_level()
        max_log_file_size = config_parser.get_log_file_max_size()
        log_file_backup_count = config_parser.get_log_file_backup_count()
        Logger.init_logs_config(logs_file_name, logs_level, max_log_file_size, log_file_backup_count)

        # reboot
        payload={
            ActionConstants.UFM_API_ACTION: RebootActionConstants.ACTION,
            ActionConstants.UFM_API_OBJECT_TYPE: config_parser.get_object_type(),
            ActionConstants.UFM_API_IDENTIFIER: config_parser.get_identifier(),
            ActionConstants.UFM_API_DESCRIPTION: config_parser.get_description(),
        }
        action = UfmDevicesAction(payload,config_parser.get_object_ids(),host=config_parser.get_ufm_host(),
                           client_token=config_parser.get_ufm_access_token(),username = config_parser.get_ufm_username(),
                           password = config_parser.get_ufm_password(),ws_protocol=config_parser.get_ufm_protocol())

        # run reboot action
        action.run_action()

    except Exception as global_ex:
        logging.error(global_ex)