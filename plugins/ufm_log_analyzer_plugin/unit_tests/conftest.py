# @copyright:
#     Copyright © 2013-2024 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.

#     This software product is a proprietary product of Nvidia Corporation and its affiliates
#     (the "Company") and all right, title, and interest in and to the
#     software product, including all associated intellectual property rights,
#     are and shall remain exclusively with the Company.

#     This software product is governed by the End User License Agreement
#     provided with the software product.

# @author: Miryam Schwartz
# @date:   Dec 08, 2024

import sys
import os

sys.path.append(os.getcwd() + "/src")   # Add the src directory containing loganalyze
sys.path.append("/".join(os.getcwd().split("/")[:-2]))  # Add the root project directory
