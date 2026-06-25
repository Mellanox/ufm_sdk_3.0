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

"""StateMirror sidecar: mirrors UFM runtime state between the pod's emptyDir and
its durable backend -- a ConfigMap (default) or Redis/Valkey (HLD section 5.3).
Ships as the standalone, consumer-agnostic ``ufm-state-mirror`` image.
"""

__version__ = "1.0.0"
