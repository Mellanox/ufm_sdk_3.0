#!/usr/bin/python
#
# Copyright © 2019-2025 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
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
    ufm = UFM()
    general_utils = GeneralUtils()
    integration = Integration()
    should_fail = int(general_utils.get_conf_parameter_value(Constants.CONF_FAIL_SLURM_JOB_UPON_FAILURE_PARAM))

    def init(self):
        self.server = self.general_utils.get_conf_parameter_value(Constants.CONF_UFM_IP)
        self.https_port = self.general_utils.get_conf_parameter_value(Constants.CONF_HTTPS_PORT)
        self.user = self.general_utils.get_conf_parameter_value(Constants.CONF_UFM_USER)
        self.password = self.general_utils.get_conf_parameter_value(Constants.CONF_UFM_PASSWORD)
        self.pkey_allocation = self.general_utils.get_conf_parameter_value(Constants.CONF_PKEY_ALLOCATION)
        self.pkey_allocation = self._toBoolean(self.pkey_allocation, Constants.CONF_PKEY_ALLOCATION, True)
        self.pkey_allocation_mode = self.general_utils.get_conf_parameter_value(Constants.CONF_PKEY_ALLOCATION_MODE)
        if self.pkey_allocation_mode not in [Constants.STATIC_PKEY_ALLOCATION_MODE, Constants.DYNAMIC_PKEY_ALLOCATION_MODE]:
            logging.error(f"pkey_allocation_mode must be one of {Constants.STATIC_PKEY_ALLOCATION_MODE} or {Constants.DYNAMIC_PKEY_ALLOCATION_MODE}, got {self.pkey_allocation_mode}")
            self.pkey_allocation_mode = Constants.STATIC_PKEY_ALLOCATION_MODE
            sys.exit(self.should_fail)
        self.get_pkey_name(self.args.job_id)
        self.ip_over_ib = self.general_utils.get_conf_parameter_value(Constants.CONF_IP_OVER_IB_PARAM)
        if not self.ip_over_ib:
            self.ip_over_ib = True
        self.index0 = self.general_utils.get_conf_parameter_value(Constants.CONF_INDEX0_PARAM)
        if not self.index0:
            self.index0 = False
        if not self.https_port:
            self.https_port = "443"
        self.is_in_debug_mode = self.general_utils.is_debug_mode()

    def get_pkey_name(self, job_id):
        """
        This function is responsible for determining the Pkey name for SLURM job allocation
        based on the configured allocation mode.
        Static Mode: Uses a pre-configured pkey value from the configuration file
        Dynamic Mode: Automatically generates a pkey value by converting the SLURM job ID 
        into a hexadecimal value within a specific range
        Args:
            job_id (int): Slurm job ID (1 → 2,147,483,647)
        """
        if self.pkey_allocation_mode == Constants.STATIC_PKEY_ALLOCATION_MODE:
            self.pkey = self.general_utils.get_conf_parameter_value(Constants.CONF_PKEY_PARAM)
        else: # dynamic pkey allocation mode
            # Convert a Slurm job ID to a hexadecimal string in the range 0x1–0x7ffe.
            # wrap job_id into 1–32766 range
            try:
                wrapped_value = (int(job_id) % (0x7ffe))
                # wrap job_id into 1–32766 range
                wrapped_value = 1 if wrapped_value == 0 else wrapped_value
                self.pkey = hex(wrapped_value)
            except Exception as exc:
                logging.error(f"Failed to get pkey name for job_id: {job_id}, got exception: {exc}")
                sys.exit(self.should_fail)
    
    def create_server_session(self):
        self.auth_type = self.general_utils.get_conf_parameter_value(Constants.AUTH_TYPE)
        if self.auth_type == Constants.BASIC_AUTH:
            user2 = self.general_utils.get_conf_parameter_value(Constants.CONF_UFM_USER)
            password2 = self.general_utils.get_conf_parameter_value(Constants.CONF_UFM_PASSWORD)
            if user2 is None or password2 is None:
                logging.error("For using %s you should set a valid %s %s in ufm_slurm.conf" % (
                    Constants.BASIC_AUTH, Constants.CONF_UFM_USER, Constants.CONF_UFM_PASSWORD))
                sys.exit(self.should_fail)
            self.session = self.ufm.getServerSession(auth_type=self.auth_type, username=user2, password=password2)
        elif self.auth_type == Constants.TOKEN_AUTH:
            token = self.general_utils.get_conf_parameter_value(Constants.CONF_TOKEN)
            if token is None:
                logging.error("For using %s you should set a valid %s in ufm_slurm.conf" % (
                    Constants.TOKEN_AUTH, Constants.CONF_TOKEN))
                sys.exit(self.should_fail)
            self.session = self.ufm.getServerSession(auth_type=self.auth_type, token=token)
        elif self.auth_type == Constants.KERBEROS_AUTH:
            principal_name = self.general_utils.get_conf_parameter_value(Constants.CONF_PRINCIPAL_NAME)
            self.session = self.ufm.getServerSession(auth_type=self.auth_type, principal_name=principal_name)
        else:
            logging.error("auth_type in ufm_slurm.conf file must be one of the following (%s, %s, %s)" % (
                Constants.BASIC_AUTH, Constants.TOKEN_AUTH, Constants.KERBEROS_AUTH))
            sys.exit(self.should_fail)

    def get_job_nodes(self):
        try:
            slurm_job_nodelist = self.integration.getJobNodesName()
            logging.info("SLURM_JOB_NODELIST: {0}".format(slurm_job_nodelist))
            if not slurm_job_nodelist:
                logging.error(Constants.LOG_CANNOT_GET_NODES)
                sys.exit(self.should_fail)
            return slurm_job_nodelist
        except Exception as exc:
            logging.error(Constants.LOG_ERROR_GET_NODES % str(exc))
            sys.exit(self.should_fail)

    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("-i", "--job_id", action="store",
                                    dest="job_id", default=None,
                                    help="Job ID")
        self.args = parser.parse_args(sys.argv[1:])

    def prepare_logger(self, file):
        format_str = "%(asctime)-15s  UFM-SLURM-{0} JobID: {1}    %(levelname)-7s  : %(message)s".format(file,
                                                                                                         self.args.job_id)
        conf_file = self.general_utils.getSlurmConfFile()

        if self.general_utils.isFileExist(conf_file):
            self.log_name = self.general_utils.get_conf_parameter_value(Constants.CONF_LOGFILE_NAME)
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
            is_running, msg = self.ufm.IsUfmRunning(self.server, self.https_port, self.session, self.auth_type)

            if is_running:
                logging.info(Constants.LOG_UFM_RUNNING %self.server)
            else:
                logging.error(Constants.LOG_CANNOT_UFM %msg)
                sys.exit(self.should_fail)

        except Exception as exc:
            logging.error(Constants.LOG_ERROR_UFM_CONNECT % str(exc) )
            sys.exit(self.should_fail)

    def add_hosts_to_pkey(self, job_nodes):
        if not job_nodes or not self.pkey:
            logging.info("Adding hosts to pkey failed, Neither job_nodes or pkey were found!")
            return
        try:
            logging.info("Adding guids of hosts_names (%s) to pkey (%s)" % (job_nodes, self.pkey))
            response = self.ufm._add_hosts_to_pkey(self.server, self.https_port, self.session,
            self.auth_type, job_nodes, self.pkey, self.ip_over_ib, self.index0)
            logging.info("Request Response: %s" % str(response))
        except Exception as exc:
            logging.error("Failed to add guids of hosts_names (%s) to pkey (%s) ::: Error==> %s" % (
                job_nodes, self.pkey, exc))

    def remove_hosts_from_pkey(self, job_nodes):
        if not job_nodes or not self.pkey:
            logging.info("Removing hosts from pkey failed, Neither job_nodes or pkey were found!")
            return
        try:
            logging.info("Removing guids of hosts_names (%s) from pkey (%s)" % (job_nodes, self.pkey))
            response = self.ufm._remove_hosts_from_pkey(self.server, self.https_port, self.session, self.auth_type, job_nodes, self.pkey)
            logging.info("Request Response: %s" % str(response))
        except Exception as exc:
            logging.error("Failed to remove guids of hosts_names (%s) from pkey (%s) ::: Error==> %s" % (
                job_nodes, self.pkey, exc))

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
