#
# Copyright © 2013-2023 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
#

import configparser
import os
import logging
from logging.handlers import RotatingFileHandler
from constants import PDRConstants as Constants
from isolation_mgr import IsolationMgr
from ufm_communication_mgr import UFMCommunicator
from api.port_state_api import PortsStateAPI
from twisted.web.wsgi import WSGIResource
from twisted.internet import reactor
from twisted.web import server


def create_logger(file):
    """
    create a logger to put all the data of the server action
    :param file: name of the file
    :return:
    """
    format_str = "%(asctime)-15s UFM-PDR_deterministic-plugin-{0} Machine: {1}     %(levelname)-7s: %(message)s".format(file,'localhost')
    log_name = Constants.LOG_FILE
    if not os.path.exists(log_name):
        os.makedirs('/'.join(log_name.split('/')[:-1]), exist_ok=True)
    logger = logging.getLogger(log_name)

    logging_level = logging.getLevelName(Constants.log_level) \
        if isinstance(Constants.log_level, str) else Constants.log_level

    logging.basicConfig(format=format_str,level=logging_level)
    rotateHandler = RotatingFileHandler(log_name,maxBytes=Constants.log_file_max_size,
                                        backupCount=Constants.log_file_backup_count)
    rotateHandler.setLevel(Constants.log_level)
    rotateHandler.setFormatter(logging.Formatter(format_str))
    logger.addHandler(rotateHandler)
    return logger


def parse_config():
    """
    parse both config file and extract the information for the logger and the server port.
    :return:
    """
    defaults = {Constants.CONF_INTERNAL_PORT: Constants.UFM_HTTP_PORT,
                Constants.T_ISOLATE: 300,
                Constants.MAX_NUM_ISOLATE: 10,
                Constants.D_TMAX: 10,
                Constants.MAX_PDR: 1e-12,
                Constants.MAX_BER: 1e-12,
                Constants.CONFIGURED_BER_CHECK: False,
                Constants.DRY_RUN: False,
                Constants.DEISOLATE_CONSIDER_TIME: 5,
                Constants.AUTOMATIC_DEISOLATE: True,
                }
    pdr_config = configparser.ConfigParser(defaults=defaults)

    if os.path.exists(Constants.CONF_FILE):
        pdr_config.read(Constants.CONF_FILE)
        Constants.log_level = pdr_config.get(Constants.CONF_COMMON,"log_level")
        Constants.log_file_max_size = pdr_config.getint(Constants.CONF_COMMON,"log_file_max_size")
        Constants.log_file_backup_count = pdr_config.getint(Constants.CONF_COMMON,"log_file_backup_count")
    return pdr_config

def run_api(app):
    port_number = 8982
    resource = WSGIResource(reactor, reactor.getThreadPool(), app.application)
    reactor.listenTCP(port_number, server.Site(resource,logPath=None))
    reactor.run()

def main():
    config_parser = parse_config()
    ufm_port = config_parser.getint(Constants.CONF_COMMON, Constants.CONF_INTERNAL_PORT)
    ufm_client = UFMCommunicator("127.0.0.1", ufm_port)
    logger = create_logger(Constants.LOG_FILE)
    
    algo_loop = IsolationMgr(ufm_client, logger)
    app = PortsStateAPI(algo_loop)
    reactor.callInThread(algo_loop.main_flow)
    run_api(app)

    
    #optional second phase
    # rest_server = RESTserver()
    # rest_server.serve()


if __name__ == '__main__':
    main()
