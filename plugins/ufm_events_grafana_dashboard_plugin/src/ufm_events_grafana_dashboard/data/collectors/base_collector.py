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
import json
import httpx

from abc import ABC, abstractmethod
from typing import Any

from mgr.configurations_mgr import UFMEventsGrafanaConfigParser
from utils.logger import Logger, LOG_LEVELS
from data.models.base_model import BaseModel


class BaseCollector(ABC):
    """Base class for a collector that collects data at a given interval"""

    def __init__(self, model: BaseModel, is_enabled: bool, interval: int):
        if not isinstance(interval, int) or interval < 0:
            raise RuntimeError(f"Invalid interval value {interval}. Please use non-negative int values")
        self.model = model
        self.interval = interval
        self.is_enabled = is_enabled

    @abstractmethod
    async def collect(self) -> None:
        """Method that collects data"""
        pass


class HttpCollector(BaseCollector):
    """Base class that collects data from an HTTP URL"""

    def __init__(self, model: BaseModel, is_enabled: bool,
                 interval: int, url: str, jsonify: bool = False):
        super().__init__(model, is_enabled, interval)
        self.url = url
        self.jsonify = jsonify

    async def collect(self):
        """Method that collects data from an HTTP endpoint"""
        try:
            data = await self.do_http_get()
            if self.model:
                self.model.on_data(data)
        except Exception as ex:
            error_msg = f"Failed to collect data from {self.url} : {ex}"
            Logger.log_message(error_msg, LOG_LEVELS.ERROR)

    async def do_http_get(self) -> Any:
        """Method that performs an HTTP GET request"""
        async with httpx.AsyncClient(verify=False) as client:
            try:
                Logger.log_message(f'Requesting URL: {self.url}', LOG_LEVELS.DEBUG)
                response = await client.get(self.url)
                Logger.log_message(f'Requesting URL: {self.url} '
                                   f'completed with status [{str(response.status_code)}]', LOG_LEVELS.DEBUG)
                response.raise_for_status()
                if self.jsonify:
                    return json.loads(response.text)
                return response.text
            except (ConnectionError, httpx.ConnectError) as con_err:
                error_msg = f"Failed to GET from {self.url} : {con_err}"
                Logger.log_message(error_msg, LOG_LEVELS.ERROR)
            except Exception as ex:
                error_msg = f"Failed to GET from {self.url} : {ex}"
                Logger.log_message(error_msg, LOG_LEVELS.ERROR)


class TelemetryHttpCollector(HttpCollector):
    """Class that collects telemetry metrics from a given URL"""

    def __init__(self, model: BaseModel):
        conf = UFMEventsGrafanaConfigParser.getInstance()
        is_enabled = conf.get_telemetry_enabled()
        url = conf.get_telemetry_url()
        interval = conf.get_telemetry_interval()
        super(TelemetryHttpCollector, self).__init__(model=model, url=url,
                                                     interval=interval, is_enabled=is_enabled)
