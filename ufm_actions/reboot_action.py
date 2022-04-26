import os
import logging
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



class RebootActionConstants:
    ACTION = "reboot"
    args_list = [
        {
            "name": f'--{ActionConstants.API_OBJECT_IDS}',
            "help": "comma separated devices GUIDs if",
        },
        {
            "name": f'--{ActionConstants.UFM_API_DESCRIPTION}',
            "help": "action description",
        }
    ]

class UfmRebootConfigParser(ConfigParser):

    def __init__(self,args):
        super().__init__(args)
        self.args_dict = self.args.__dict__

    def get_object_ids(self):
        return self.get_config_value(self.args_dict.get(ActionConstants.API_OBJECT_IDS),
                                     None, None, '')

    def get_description(self):
        return self.get_config_value(self.args_dict.get(ActionConstants.UFM_API_DESCRIPTION),
                                     None, None, '')

# if run as main module
if __name__ == "__main__":
    try:
        # init app args
        args = ArgsParser.parse_args("UFM Reboot", RebootActionConstants.args_list)
        args_dict = args.__dict__

        # init app config parser & load config files
        config_parser = UfmRebootConfigParser(args)

        # reboot
        payload={
            ActionConstants.UFM_API_ACTION: RebootActionConstants.ACTION,
            ActionConstants.UFM_API_OBJECT_TYPE: "System",
            ActionConstants.UFM_API_IDENTIFIER: "id",
            ActionConstants.UFM_API_DESCRIPTION: config_parser.get_description(),
        }
        action = UfmAction(payload,config_parser.get_object_ids(),host=config_parser.get_ufm_host(),
                           client_token=config_parser.get_ufm_access_token(),username = config_parser.get_ufm_username(),
                           password = config_parser.get_ufm_password(),ws_protocol=config_parser.get_ufm_protocol())

        # run reboot action
        action.run_action()

    except Exception as global_ex:
        logging.error(global_ex)