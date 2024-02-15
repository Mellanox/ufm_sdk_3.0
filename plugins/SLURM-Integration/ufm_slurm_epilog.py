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
import logging
from ufm_slurm_utils import Constants
from ufm_slurm_base import UfmSlurmBase


class UfmSlurmEpilog(UfmSlurmBase):

    def epilog_init(self):
        UfmSlurmBase.init(self)
        try:
            self.create_server_session()
        except Exception as exc:
            logging.error("Error in ufm_slurm_epilog init function: %s" % str(exc) )
            sys.exit(self.should_fail)


if __name__ == '__main__':
    try:
        epilog = UfmSlurmEpilog()
        epilog.parse_args()
        epilog.prepare_logger(file="Epilog")
        epilog.epilog_init()
        epilog.connect_to_ufm()
        slurm_job_nodelist = epilog.get_job_nodes()
        if epilog.pkey_allocation:
            epilog.remove_hosts_from_pkey(slurm_job_nodelist)
        if epilog.sharp_allocation:
            epilog.delete_sharp_allocation(epilog.args.job_id)
    except Exception as exc:
        logging.error(
        Constants.LOG_ERR_EPILOG % str(exc))
        sys.exit(epilog.should_fail)
    finally:
        logging.info("## Done ##")
