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

"""Atomic-blob handler (HLD 5.3.2).

For writers that use the write-tmp-then-rename pattern (e.g. OpenSM): the
rename surfaces to watchdog as a move event, and the file is already complete
when we read it. Behavior is identical to a blob today; the distinct class
documents the writer contract and leaves room for move-specific tuning.
"""

from __future__ import annotations

from state_mirror.handlers.blob import BlobHandler


class AtomicBlobHandler(BlobHandler):
    pass
