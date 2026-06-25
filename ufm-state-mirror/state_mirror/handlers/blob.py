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

"""Blob handler: a single file mirrored as one Redis key (HLD 5.3.2).

Runtime trigger is watchdog's close-write event. The base class already does
read -> hash-compare -> atomic write, so a plain blob needs no extra behavior.
"""

from __future__ import annotations

from state_mirror.handlers.base import BaseHandler


class BlobHandler(BaseHandler):
    pass
