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
from abc import ABC, abstractmethod
from typing import List

from constants import DataType
from data.models.base_model import BaseModel


class BaseListener(ABC):
    def __init__(self, data_manager: 'Type[DataManager]', data_types: List[DataType]):
        self.data_manager = data_manager
        self.data_types = data_types
        self._subscribe_to_models()

    @abstractmethod
    def update_data(self):
        """
        The implementation for the data logic upon data arrival
        such as storing in database, trigger events, etc...
        """

    def _subscribe_to_models(self):
        for data_type in self.data_types:
            model: BaseModel = self.data_manager.get_model_by_data_type(data_type)
            model.attach(self)
