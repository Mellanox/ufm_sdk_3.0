"""
Telemetry endpoint data container.
"""
from dataclasses import dataclass
from typing import List

from telemetry_http_client import TelemetryHTTPClient


@dataclass
class TelemetryEndpoint:
    """Representation of a telemetry endpoint definition."""

    host: str
    port: str
    url: str
    interval: str
    message_tag_name: str
    xdr_mode: bool
    xdr_ports_types: List[str]
    http_client: TelemetryHTTPClient

    @property
    def display_name(self) -> str:
        return self.message_tag_name
