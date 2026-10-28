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
import time

from typing import Any

from data.models.base_model import BaseModel


class TelemetryMetricsModel(BaseModel):

    def __init__(self):
        super().__init__()
        self.ts = 0
        self.last_metrics_csv: str = ''

    def on_data(self, data: Any):
        if not data:
            return
        with self.lock:
            self.ts = time.time()
            self.last_metrics_csv = data
        self.notify_listeners()
