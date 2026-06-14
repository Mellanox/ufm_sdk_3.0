#
# Copyright © 2009-2026 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
#

"""StateMirror sidecar: mirrors UFM runtime state between the pod's emptyDir
and Redis (HLD section 5.3). Ships as the ``ufm-state-mirror`` image, pinned to
the UFM version.
"""

__version__ = "0.1.0-poc"
