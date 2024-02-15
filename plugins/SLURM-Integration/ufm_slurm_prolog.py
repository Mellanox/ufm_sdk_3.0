#!/usr/bin/python
#
# Copyright © 2017-2024 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
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
import time
from ufm_slurm_utils import Constants
import logging
from ufm_slurm_base import UfmSlurmBase


class UfmSlurmProlog(UfmSlurmBase):
    device_list = []
    allocated_ls = []

    def prolog_init(self):
        UfmSlurmBase.init(self)
        try:
            logging.info("Starting JobID: " + self.args.job_id)
            self.create_server_session()
        except Exception as exc:
            logging.error("Error in ufm_slurm_prolog init function: %s" % str(exc))
            sys.exit(self.should_fail)


if __name__ == '__main__':
    try:
        all_time_start = time.time()
        prolog = UfmSlurmProlog()
        prolog.parse_args()
        prolog.prepare_logger(file="Prolog")
        prolog.prolog_init()
        prolog.connect_to_ufm()
        slurm_job_nodelist = prolog.get_job_nodes()
        if prolog.pkey_allocation:
            prolog.add_hosts_to_pkey(slurm_job_nodelist)
        if prolog.sharp_allocation:
            prolog.create_sharp_allocation(prolog.args.job_id, slurm_job_nodelist)
        logging.info("UFM-Slurm-Prolog time: %.1f seconds" % (time.time() - all_time_start))
    except Exception as exc:
        logging.error(
        Constants.LOG_ERR_PROLOG % str(exc))
        sys.exit(prolog.should_fail)
