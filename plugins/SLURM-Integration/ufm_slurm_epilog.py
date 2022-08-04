#!/usr/bin/python
#
# Copyright © 2017-2021 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
#
"""
Created on January 24, 2021

@author: Ibrahimbar
@author: Anas Badaha
@copyright:
        Copyright (C) Mellanox Technologies Ltd. 2001-2021.  ALL RIGHTS RESERVED.

        This software product is a proprietary product of Mellanox Technologies Ltd.
        (the "Company") and all right, title, and interest in and to the software product,
        including all associated intellectual property rights, are and shall
        remain exclusively with the Company.

        This software product is governed by the End User License Agreement
        provided with the software product.
"""
import sys
import logging
from ufm_slurm_utils import Constants
from ufm_slurm_base import UfmSlurmBase


class UfmSlurmEpilog(UfmSlurmBase):

    def epilog_init(self):
        try:
            self.auth_type = self.general_utils.read_conf_file(Constants.AUTH_TYPE)
            if self.auth_type == Constants.BASIC_AUTH:
                user2 = self.general_utils.read_conf_file(Constants.CONF_UFM_USER)
                password2 = self.general_utils.read_conf_file(Constants.CONF_UFM_PASSWORD)
                if user2 is None or password2 is None:
                    logging.error("For using %s you should set a valid %s %s in ufm_slurm.conf" % (
                        Constants.BASIC_AUTH, Constants.CONF_UFM_USER, Constants.CONF_UFM_PASSWORD))
                    sys.exit(self.should_fail)
                self.session = self.ufm.getServerSession(auth_type=self.auth_type, username=user2, password=password2)
            elif self.auth_type == Constants.TOKEN_AUTH:
                token = self.general_utils.read_conf_file(Constants.CONF_TOKEN)
                if token is None:
                    logging.error("For using %s you should set a valid %s in ufm_slurm.conf" % (
                        Constants.TOKEN_AUTH, Constants.CONF_TOKEN))
                    sys.exit(self.should_fail)
                self.session = self.ufm.getServerSession(auth_type=self.auth_type, token=token)
            else:
                logging.error("auth_type in ufm_slurm.conf file must be one of the following (%s, %s)" % (
                    Constants.BASIC_AUTH, Constants.CONF_TOKEN))
                sys.exit(self.should_fail)
        except Exception as exc:
            logging.error("error in epilog init function: %s" % str(exc) )
            sys.exit(self.should_fail)


if __name__ == '__main__':
    try:
        epilog = UfmSlurmEpilog()
        epilog.parse_args()
        epilog.prepare_logger(file="Epilog")
        epilog.init()
        epilog.epilog_init()
        epilog.connect_to_ufm()
        epilog.delete_sharp_reservation(epilog.args.job_id)
    except Exception as exc:
        logging.error(
        Constants.LOG_ERR_EPILOG % str(exc))
        sys.exit(epilog.should_fail)
    finally:
        logging.info("## Done ##")
