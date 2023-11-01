import sys
from utils.logger import Logger, LOG_LEVELS

class ExceptionHandlerConstants:
    Supported_In_Config_File = 'you can add them to config file'

class ExceptionHandler(object):
    @staticmethod
    def handel_exception(exception_msg , exist=True, log_level = LOG_LEVELS.ERROR):
        Logger.log_message(exception_msg, log_level=log_level)
        if exist:
            sys.exit(1)

    @staticmethod
    def handel_arg_exception(action, *argv, supported_in_config=False, exist=True):
        Logger.log_missing_args_message(action,argv)
        if supported_in_config:
            Logger.log_message(ExceptionHandlerConstants.Supported_In_Config_File)
        if exist:
            sys.exit(1)
