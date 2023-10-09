#!/usr/bin/python
#
# Copyright © 2019-2023 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
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

import sys, time, http
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
        self.user = self.general_utils.get_conf_parameter_value(Constants.CONF_UFM_USER)
        self.password = self.general_utils.get_conf_parameter_value(Constants.CONF_UFM_PASSWORD)
        self.pkey_allocation = self.general_utils.get_conf_parameter_value(Constants.CONF_PKEY_ALLOCATION)
        self.pkey_allocation = self._toBoolean(self.pkey_allocation, Constants.CONF_PKEY_ALLOCATION, True)
        self.pkey = self.general_utils.get_conf_parameter_value(Constants.CONF_PKEY_PARAM)
        self.ip_over_ib = self.general_utils.get_conf_parameter_value(Constants.CONF_IP_OVER_IB_PARAM)
        if not self.ip_over_ib:
            self.ip_over_ib = True
        self.index0 = self.general_utils.get_conf_parameter_value(Constants.CONF_INDEX0_PARAM)
        if not self.index0:
            self.index0 = False
        self.sharp_allocation = self.general_utils.get_conf_parameter_value(Constants.CONF_SHARP_ALLOCATION)
        self.sharp_allocation = self._toBoolean(self.sharp_allocation, Constants.CONF_SHARP_ALLOCATION, False)
        self.partially_alloc = self.general_utils.get_conf_parameter_value(Constants.CONF_PARTIALLY_ALLOC)
        self.partially_alloc = self._toBoolean(self.partially_alloc, Constants.CONF_PARTIALLY_ALLOC, True)
        self.app_resources_limit = self.general_utils.get_conf_parameter_value(Constants.CONF_APP_RESOURCES_LIMIT)
        if self.app_resources_limit and int(self.app_resources_limit) < -1:
            logging.error(
                "app_resources_limit param must be an integer number greater than -1, (got {0}), using default value: - 1".format(
                    self.app_resources_limit))
            self.app_resources_limit = -1
        else:
            self.app_resources_limit = -1
        self.num_of_retries = int(self.general_utils.get_conf_parameter_value(Constants.CONF_NUM_OF_RETRIES))
        self.retry_interval = int(self.general_utils.get_conf_parameter_value(Constants.CONF_RETRY_INTERVAL))
        self.is_in_debug_mode = self.general_utils.is_debug_mode()

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
            is_running, msg = self.ufm.IsUfmRunning(self.server, self.session, self.auth_type)

            if is_running:
                logging.info(Constants.LOG_UFM_RUNNING %self.server)
            else:
                logging.error(Constants.LOG_CANNOT_UFM %msg)
                sys.exit(self.should_fail)

        except Exception as exc:
            logging.error(Constants.LOG_ERROR_UFM_CONNECT % str(exc) )
            sys.exit(self.should_fail)

    def create_sharp_allocation(self, job_id, job_nodes):
        try:
            logging.info("Allocate Job's node guids (%s) to app_id: %s" % (job_nodes, job_id))
            response = self.ufm._create_sharp_allocation(self.server, self.session, self.auth_type, job_id, job_nodes,
                                                       self.pkey, self.app_resources_limit, self.partially_alloc)
            logging.info("Request Response: %s" % str(response))
        except Exception as exc:
            logging.error("Failed to allocate job's node %s to pkey::: Error==> %s" % (job_nodes, exc))

    def delete_sharp_allocation(self, job_id):
        left_retries = self.num_of_retries
        while True:
            try:
                logging.info(f"Attempting to delete sharp reservation with app_id: {job_id}")
                response = self.ufm._delete_sharp_allocation(self.server, self.session, self.auth_type, job_id)
                if response.status_code == http.client.NOT_FOUND:
                    logging.warning(f"Deleting sharp reservation failed, sharp reservation with app_id: "
                                    f"{job_id} is not found!")
                    break
                if response.status_code == http.client.NO_CONTENT:
                    logging.info(f"Deleting sharp reservation with app_id: {job_id} completed successfully.")
                    break
                else:
                    logging.error(f"Deleting sharp reservation with app_id: {job_id} failed! "
                                  f"status_code: {response.status_code}, response: {response.text}")
                    if self.num_of_retries == 0:
                        logging.info(f"Retrying to delete sharp reservation with app_id: {job_id} in "
                                     f"{self.retry_interval} seconds...")
                        time.sleep(self.retry_interval)
                    elif left_retries > 0:
                        logging.info(f"Retrying in {self.retry_interval} seconds... (Retries left: {left_retries})")
                        left_retries -= 1
                        time.sleep(self.retry_interval)
                    else:
                        logging.error(f"No more retries. Giving up after {self.num_of_retries} retries to delete "
                                      f"sharp reservation with app_id: {job_id}")
                        break
            except Exception as exc:
                logging.error(f"Deleting sharp reservation with app_id {job_id} Failed! got exception ==> {exc}")

    def add_hosts_to_pkey(self, job_nodes):
        if not job_nodes or not self.pkey:
            logging.info("Adding hosts to pkey failed, Neither job_nodes or pkey were found!")
            return
        try:
            logging.info("Adding guids of hosts_names (%s) to pkey (%s)" % (job_nodes, self.pkey))
            response = self.ufm._add_hosts_to_pkey(self.server, self.session, self.auth_type, job_nodes, self.pkey,
                                                   self.ip_over_ib, self.index0)
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
            response = self.ufm._remove_hosts_from_pkey(self.server, self.session, self.auth_type, job_nodes, self.pkey)
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
