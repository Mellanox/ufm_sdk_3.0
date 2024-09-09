#
# Copyright © 2013-2024 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
#
import logging

LOGGER = None

def setup_logger(name, level=logging.INFO):
    """
    Function to set up a logger that outputs to the console.
    :param name: Name of the logger.
    :param level: Logging level (default is INFO).
    :return: Configured logger instance.
    """
    global LOGGER # pylint: disable=global-statement

    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    LOGGER = logging.getLogger(name)
    LOGGER.setLevel(level)
    LOGGER.addHandler(console_handler)
    return LOGGER
