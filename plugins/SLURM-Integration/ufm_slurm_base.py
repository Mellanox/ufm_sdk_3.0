#!/usr/bin/python
#
# Copyright © 2019-2021 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
#

# Created on January 24, 2021
# Author: Ibrahimbar
# Author: Anas Badaha

import sys
import argparse
import logging
from ufm_slurm_utils import UFM, GeneralUtils, Integration, Constants
from logging.handlers import RotatingFileHandler


class UfmSlurmBase():
    should_fail = 0 #set 0 the script will not fail; 1 the script will fail
    ufm = UFM()
    general_utils = GeneralUtils()
    integration = Integration()

    def init(self):
        self.server = self.general_utils.read_conf_file(Constants.CONF_UFM_IP)
        self.user = self.general_utils.read_conf_file(Constants.CONF_UFM_USER)
        self.password = self.general_utils.read_conf_file(Constants.CONF_UFM_PASSWORD)
        self.partially_alloc = self.general_utils.read_conf_file(Constants.CONF_PARTIALLY_ALLOC)
        self.partially_alloc = self._toBoolean(self.partially_alloc, Constants.CONF_PARTIALLY_ALLOC)
        self.pkey = self.general_utils.read_conf_file(Constants.CONF_PKEY_PARAM)
        self.is_in_debug_mode = self.general_utils.is_debug_mode()

    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("-i", "--job_id", action="store",
                                    dest="job_id", default=None,
                                    help="Job ID")
        parser.add_argument("-s", "--step_id", action="store",
                                    dest="step_id", nargs="?", const="", default=None,
                                    help="Step ID")
        self.args = parser.parse_args(sys.argv[1:])

    def prepare_logger(self, file):
        format_str = "%(asctime)-15s  UFM-SLURM-{0} JobID: {1}    %(levelname)-7s  : %(message)s".format(file,
                                                                                                         self.args.job_id)
        conf_file = self.general_utils.getSlurmConfFile()

        if self.general_utils.isFileExist(conf_file):
            self.log_name = self.general_utils.read_conf_file(Constants.CONF_LOGFILE_NAME)
        else:
            self.log_name = Constants.DEF_LOG_FILE

        logging.basicConfig(format=format_str, level=logging.INFO)
        Rthandler = RotatingFileHandler(self.log_name, maxBytes=10*1024*1024,backupCount=10)
        Rthandler.setLevel(logging.INFO)
        Rthandler.setFormatter(logging.Formatter(format_str))
        logging.getLogger('').addHandler(Rthandler)

    def connect_to_ufm(self):
        try:
            if not self.server:
                logging.error(Constants.UFM_ERR_PARSE_IP)
                sys.exit(self.should_fail)

            logging.info(Constants.LOG_CONNECT_UFM % self.server)
            is_running, msg = self.ufm.IsUfmRunning(self.server, self.session, self.auth_type)

            if is_running:
                logging.info(Constants.LOG_UFM_RUNNING %self.server)
            else:
                logging.error(Constants.LOG_CANNOT_UFM %msg)
                sys.exit(self.should_fail)

        except Exception as exc:
            logging.error(Constants.LOG_ERROR_UFM_CONNECT % str(exc) )
            sys.exit(self.should_fail)

    def set_sharp_reservation(self, job_id, job_nodes, app_resources_limit=-1):
        try:
            logging.info("Allocate Job's node %s to app_id: %s" % (job_nodes, job_id))
            response = self.ufm._set_sharp_reservation(self.server, self.session, self.auth_type, job_id, job_nodes,
                                                       app_resources_limit, self.pkey, self.partially_alloc)
            logging.info("Request Response: %s" % str(response))
        except Exception as exc:
            logging.error("Failed to allocate job's node %s to pkey::: Error==> %s" % (job_nodes, exc))

    def delete_sharp_reservation(self, job_id):
        try:
            logging.info("Delete SHArP allocation with app_id: %s" % job_id)
            response = self.ufm._delete_sharp_reservation(self.server, self.session, self.auth_type, job_id)
            logging.info("Request Response: %s" % str(response))
        except Exception as exc:
            logging.error("Failed to Delete SHArP allocation with app_id %s ::: Error==> %s" % (job_id, exc))

    def _toBoolean(self, arg_val, arg_name, def_val=False):
        if not arg_val:
            arg = def_val
        elif arg_val in set(['True', 'T', 't', 'TRUE', 'true']):
            arg = True
        elif arg_val in set(['False', 'F', 'f', 'FALSE', 'false']):
            arg = False
        else:
            logging.error("Wrong boolean value (%s) detected in parameter: %s" % (arg_val, arg_name))
            sys.exit(self.should_fail)

        return arg
