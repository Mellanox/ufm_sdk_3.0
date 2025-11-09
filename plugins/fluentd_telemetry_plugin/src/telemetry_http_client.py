"""
@copyright:
    Copyright (C) Mellanox Technologies Ltd. 2014-2025.  ALL RIGHTS RESERVED.

    This software product is a proprietary product of Mellanox Technologies
    Ltd. (the "Company") and all right, title, and interest in and to the
    software product, including all associated intellectual property rights,
    are and shall remain exclusively with the Company.

    This software product is governed by the End User License Agreement
    provided with the software product.

@author: Yotam Ashman
@date:   Nov 3, 2025
"""
import socket
import logging
import requests
from requests.adapters import HTTPAdapter


class SourcePortAdapter(HTTPAdapter):
    """
    Custom HTTP adapter that binds all connections to a static ephemeral source port.
    The source port is determined once and shared across all connection pools.
    """
    _source_port = None

    def __init__(self, *args, **kwargs):
        """
        Initialize the adapter and determine the static source port if not already set.
        """
        if SourcePortAdapter._source_port is None:
            try:
                # Bind a socket to port 0 to let the OS choose an ephemeral port
                # We'll capture this port and reuse it for all subsequent connections
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('0.0.0.0', 0))
                    SourcePortAdapter._source_port = s.getsockname()[1]
                logging.info('HTTP Client initialized with static source port: %d',
                            SourcePortAdapter._source_port)
            except OSError as e:
                logging.error('Error during HTTP adapter initialization: OS failed to bind port: %s', e)
                raise RuntimeError(
                    f'Error during HTTP adapter initialization: OS failed to bind port: ({e})'
                ) from e
            except Exception as e:
                logging.error('Error during HTTP adapter initialization: %s', e)
                raise RuntimeError(
                    f'Error during HTTP adapter initialization: ({e})'
                ) from e

        super().__init__(*args, **kwargs)

    def init_poolmanager(self, *args, **kwargs):
        """
        Initialize the connection pool manager with the static source address.
        """
        kwargs['source_address'] = ('0.0.0.0', SourcePortAdapter._source_port)
        return super().init_poolmanager(*args, **kwargs)


class TelemetryHTTPClient:
    """
    HTTP client for telemetry requests that uses a consistent source port
    across all requests throughout the plugin's runtime.
    """

    def __init__(self):
        """
        Initialize the HTTP client with a persistent session and custom adapter.
        """
        self.session = requests.Session()
        self.adapter = SourcePortAdapter()

        # Mount the adapter for both HTTP and HTTPS
        self.session.mount('http://', self.adapter)
        self.session.mount('https://', self.adapter)

    def get_telemetry_metrics(self, url, **kwargs):
        """
        Perform an HTTP GET request using the persistent session.

        Args:
            url: The URL to request
            **kwargs: Additional arguments to pass to requests.get()
            
        Returns:
            requests.Response: The response object
        """
        return self.session.get(url, **kwargs)

    def post(self, url, **kwargs):
        """
        Perform an HTTP POST request using the persistent session.
        
        Args:
            url: The URL to request
            **kwargs: Additional arguments to pass to requests.post()
            
        Returns:
            requests.Response: The response object
        """
        return self.session.post(url, **kwargs)

    def get_source_port(self):
        """
        Get the static source port being used by this client.
        
        Returns:
            int: The source port number
        """
        return SourcePortAdapter._source_port # pylint: disable=protected-access

    def close(self):
        """
        Close the session and release resources.
        """
        self.session.close()
