import os
from ufm_actions.ufm_action import UfmAction,ActionConstants

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
    # todo help message should contian more detailes
    args_list = [
        {
            "name": f'--{ActionConstants.API_OBJECT_IDS}',
            "help": "comma separated devices GUIDs if",
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
            "help": "path",
        },
        {
            "name": f'--{UFM_API_IMAGE}',
            "help": "image",
        },
        {
            "name": f'--{UFM_API_PROTOCOL}',
            "help": "protocol",
        },
        {
            "name": f'--{UFM_API_SERVER}',
            "help": "server",
        }

    ]


# if run as main module
if __name__ == "__main__":
    try:
        # init app args
        args = ArgsParser.parse_args("UFM Reboot", SwUpgradeActionConstants.args_list)
        args_dict = args.__dict__

        # init app config parser & load config files
        config_parser = ConfigParser(args)

        # sw upgrade
        # todo use constant
        payload={
            "action":'sw_upgrade',
            "object_type": "System",
            "identifier": "id",
            "description": config_parser.get_config_value(args_dict.get(ActionConstants.UFM_API_DESCRIPTION), None, None,''),
            "params":{
                "username": config_parser.get_config_value(args_dict.get(SwUpgradeActionConstants.UFM_API_USER_NAME),
                                                           None, None),
                "password": config_parser.get_config_value(args_dict.get(SwUpgradeActionConstants.UFM_API_PASSWORD),
                                                           None, None),
                "path": config_parser.get_config_value(args_dict.get(SwUpgradeActionConstants.UFM_API_PATH), None, None),
                "image": config_parser.get_config_value(args_dict.get(SwUpgradeActionConstants.UFM_API_IMAGE),
                                                        None, None),
                "protocol": config_parser.get_config_value(args_dict.get(SwUpgradeActionConstants.UFM_API_PROTOCOL),
                                                           None, None),
                "server": config_parser.get_config_value(args_dict.get(SwUpgradeActionConstants.UFM_API_SERVER),
                                                         None, None),
            }
        }
        action = UfmAction(payload,config_parser.get_config_value(args_dict.get(ActionConstants.API_OBJECT_IDS),
                                                                  None, None, ''),
            host=config_parser.get_ufm_host(),client_token=config_parser.get_ufm_access_token(),
            username = config_parser.get_ufm_username(), password = config_parser.get_ufm_password(),
            ws_protocol=config_parser.get_ufm_protocol())

        # run reboot action
        action.run_action()

    except Exception as global_ex:
        print(global_ex)