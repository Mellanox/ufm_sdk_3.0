"""
@copyright:
    Copyright (C) 2013-2022 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.

    This software product is a proprietary product of Nvidia Corporation and its affiliates
    (the "Company") and all right, title, and interest in and to the software
    product, including all associated intellectual property rights, are and
    shall remain exclusively with the Company.

    This software product is governed by the End User License Agreement
    provided with the software product.

@author: Nasr Ajaj
@date:   Sep 11, 2022
"""
import platform

from web_service import BrightAPI

try:
    import os
    import sys
    sys.path.append(os.getcwd())

    from mgr.bright_mgr import BrightConfigParser, BrightConstants

    from twisted.web import server
    from utils.args_parser import ArgsParser
    from utils.logger import Logger

    from twisted.web.wsgi import WSGIResource
    from twisted.internet import reactor
except ModuleNotFoundError as e:
    if platform.system() == "Windows":
        print("Error occurred while importing python modules, "
              "Please make sure that you exported your repository to PYTHONPATH by running: "
              f'set PYTHONPATH=%PYTHONPATH%;{os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))}')
    else:
        print("Error occurred while importing python modules, "
              "Please make sure that you exported your repository to PYTHONPATH by running: "
              f'export PYTHONPATH="${{PYTHONPATH}}:{os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))}"')


def _init_logs(config_parser):
    # init logs configs
    default_file_name = 'bright.log'
    logs_file_name = config_parser.get_logs_file_name(default_file_name=default_file_name)
    logs_level = config_parser.get_logs_level()
    max_log_file_size = config_parser.get_log_file_max_size()
    log_file_backup_count = config_parser.get_log_file_backup_count()
    Logger.init_logs_config(logs_file_name, logs_level, max_log_file_size, log_file_backup_count)


def run_api(app):
    port_number = 8983
    # for debugging
    # app.run(port=port_number, debug=True)
    resource = WSGIResource(reactor, reactor.getThreadPool(), app)
    reactor.listenTCP(port_number, server.Site(resource, logPath=None))
    reactor.run()


if __name__ == '__main__':
    # init app config parser & load config files
    args = ArgsParser.parse_args("Bright Computing Integration", BrightConstants.args_list)
    config_parser = BrightConfigParser(args)

    _init_logs(config_parser)

    app = BrightAPI(config_parser)
    run_api(app)
