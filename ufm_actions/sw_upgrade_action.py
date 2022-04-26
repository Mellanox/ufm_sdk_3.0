import sys
import logging
from ufm_actions.ufm_action import UfmAction, ActionConstants

try:
    from utils.utils import Utils
    from utils.args_parser import ArgsParser
    from utils.config_parser import ConfigParser
    from utils.logger import Logger, LOG_LEVELS
except ModuleNotFoundError as e:
    print("Error occurred while importing python modules, "
          "Please make sure that you exported your repository to PYTHONPATH by running: "
          f'export PYTHONPATH="${{PYTHONPATH}}:{os.path.dirname(os.getcwd())}"')



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
            "name": f'--{ActionConstants.API_OBJECT_IDS}',
            "help": "comma separated devices GUIDs",
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

class UfmSwUpgradeConfigParser(ConfigParser):

    def __init__(self,args):
        super().__init__(args)
        self.args_dict = self.args.__dict__

    def get_object_ids(self):
        return self.get_config_value(self.args_dict.get(ActionConstants.API_OBJECT_IDS),
                                     None, None, '')

    def get_description(self):
        return self.get_config_value(self.args_dict.get(ActionConstants.UFM_API_DESCRIPTION),
                                     None, None, '')

    def get_user_name(self):
        return self.get_config_value(self.args_dict.get(SwUpgradeActionConstants.UFM_API_USER_NAME),
                                     None, None, False)

    def get_password(self):
        return self.get_config_value(self.args_dict.get(SwUpgradeActionConstants.UFM_API_PASSWORD),
                                     None, None)

    def get_path(self):
        return self.get_config_value(self.args_dict.get(SwUpgradeActionConstants.UFM_API_PATH),
                                  None, None)

    def get_image(self):
        return self.get_config_value(self.args_dict.get(SwUpgradeActionConstants.UFM_API_IMAGE),
                                  None, None)

    def get_protocol(self):
        return self.get_config_value(self.args_dict.get(SwUpgradeActionConstants.UFM_API_PROTOCOL),
                                  None, None)
    def get_server(self):
        return self.get_config_value(self.args_dict.get(SwUpgradeActionConstants.UFM_API_SERVER),
                                  None, None)



# if run as main module
if __name__ == "__main__":
    try:
        payload = None
        # init app args
        args = ArgsParser.parse_args("UFM Reboot", SwUpgradeActionConstants.args_list)
        args_dict = args.__dict__

        # init app config parser & load config files
        config_parser = UfmSwUpgradeConfigParser(args)

        # sw upgrade
        try:
            payload={
                ActionConstants.UFM_API_ACTION: SwUpgradeActionConstants.ACTION,
                ActionConstants.UFM_API_OBJECT_TYPE: "System",
                ActionConstants.UFM_API_IDENTIFIER: "id",
                ActionConstants.UFM_API_DESCRIPTION: config_parser.get_description(),
                ActionConstants.UFM_API_PARAMS:{
                    SwUpgradeActionConstants.UFM_API_USER_NAME: config_parser.get_ufm_username(),
                    SwUpgradeActionConstants.UFM_API_PASSWORD: config_parser.get_password(),
                    SwUpgradeActionConstants.UFM_API_PATH: config_parser.get_path(),
                    SwUpgradeActionConstants.UFM_API_IMAGE: config_parser.get_image(),
                    SwUpgradeActionConstants.UFM_API_PROTOCOL: config_parser.get_protocol(),
                    SwUpgradeActionConstants.UFM_API_SERVER: config_parser.get_server(),
                }
            }

        except ValueError as e:
            Logger.log_missing_args_message(SwUpgradeActionConstants.ACTION,
                                            SwUpgradeActionConstants.UFM_API_USER_NAME,
                                            SwUpgradeActionConstants.UFM_API_PASSWORD,
                                            SwUpgradeActionConstants.UFM_API_PATH,
                                            SwUpgradeActionConstants.UFM_API_IMAGE,
                                            SwUpgradeActionConstants.UFM_API_PROTOCOL,
                                            SwUpgradeActionConstants.UFM_API_SERVER)
            sys.exit(1)

        action = UfmAction(payload,config_parser.get_object_ids(),host=config_parser.get_ufm_host(),
                           client_token=config_parser.get_ufm_access_token(),username = config_parser.get_ufm_username(),
                           password = config_parser.get_ufm_password(),ws_protocol=config_parser.get_ufm_protocol())

        # run reboot action
        action.run_action()

    except Exception as global_ex:
        logging.error(global_ex)