import sys
from utils.logger import Logger


class ExceptionHandler(object):
    @staticmethod
    def handel_exception(exception_msg , exist=True):
        Logger.log_message(exception_msg)
        if exist:
            sys.exit(1)

    @staticmethod
    def handel_arg_exception(action, *argv, exist=True):
        argv = ('ufm_host','ufm_protocol',)+argv
        Logger.log_missing_args_message(action,argv)
        if exist:
            sys.exit(1)
