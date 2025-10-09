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
from typing import Dict
from constants import DataType, ModelListeners

from data.models.base_model import BaseModel
from data.models.telemetry_metrics_model import TelemetryMetricsModel

from data.listeners.base_listener import BaseListener
from data.listeners.telemetry_prometheus_exporter import TelemetryPrometheusExporter


class DataManager:
    DATA_TYPE_TO_MODEL_CLS = {
        DataType.TELEMETRY: TelemetryMetricsModel
    }

    DATA_LISTENER_TO_CLS = {
        ModelListeners.TELEMETRY_PROMETHEUS_EXPORTER: TelemetryPrometheusExporter
    }

    def __init__(self):
        self.models: Dict[DataType, BaseModel] = self._init_data_models()
        self.listeners: Dict[ModelListeners, BaseListener] = self._init_data_listeners()

    def _init_data_models(self) -> Dict[DataType, BaseModel]:
        models: Dict[DataType, BaseModel] = {}
        for dtype, model_cls in self.DATA_TYPE_TO_MODEL_CLS.items():
            model: BaseModel = model_cls()
            models[dtype] = model
        return models

    def _init_data_listeners(self) -> Dict[ModelListeners, BaseListener]:
        listeners: Dict[ModelListeners, BaseListener] = {}
        for dtype, listener_cls in self.DATA_LISTENER_TO_CLS.items():
            listener: BaseListener = listener_cls(self)
            listeners[dtype] = listener
        return listeners

    def get_model_by_data_type(self, data_type: DataType):
        """
        Returns the Model object for the given DataType
        """
        return self.models.get(data_type)
