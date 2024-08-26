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
import threading
from abc import ABC, abstractmethod
from typing import Set, Any


class Notifier:

    def __init__(self, listeners: Set['Type[BaseListener]'] = None):
        self.listeners: Set['Type[BaseListener]'] = listeners
        if self.listeners is None:
            self.listeners = set()

    def attach(self, listener):
        if listener not in self.listeners:
            self.listeners.add(listener)

    def notify_listeners(self):
        for listener in self.listeners:
            listener.update_data()


class BaseModel(Notifier, ABC):
    """
    BaseModel is base class for all data model types
    """
    def __init__(self):
        super().__init__()
        self.lock = threading.Lock()
        self.ts = 0

    @abstractmethod
    def on_data(self, data: Any):
        """
        called by designated data collector
        """

    def get_ts_milliseconds(self) -> int:
        """Get the timestamp in milliseconds"""
        return int(round(self.ts * 1000))
