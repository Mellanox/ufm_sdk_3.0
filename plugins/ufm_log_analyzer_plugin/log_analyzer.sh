#!/bin/bash
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
# author: Samer Deeb
# date:   Mar 02, 2024
#

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
src_dir=$( realpath "${SCRIPT_DIR}/src" )
export PYTHONPATH="${src_dir}:../../" # The ../../ is to be able to use the utils

python3 "${src_dir}/loganalyze/log_analyzer.py" "$@"
