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
    The source port is determined once for each adapter instance and reused across
    its connection pool.
    """
    def __init__(self):
        """
        Initialize the adapter.
        """
        self.source_port = None
        super().__init__()

    @staticmethod
    def _acquire_port():
        """
        Open a new socket and capture the OS given port.
        Socket closes after the port is captured for reuse.
        """
        try:
            # Bind a socket to port 0 to let the OS choose an ephemeral port
            # We'll capture this port and reuse it for all subsequent connections
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('0.0.0.0', 0))
                port = s.getsockname()[1]
            logging.debug('HTTP Client acquired selected port: %d', port)
            return port
        except OSError as e:
            logging.error('Error during HTTP adapter initialization: OS failed to bind port: %s', e)
            raise RuntimeError(
                f'Error during HTTP adapter initialization: OS failed to bind port. Error desc: ({e})'
            ) from e
        except Exception as e:
            logging.error('Error during HTTP adapter initialization: %s', e)
            raise RuntimeError(
                f'Error during HTTP adapter initialization: ({e})'
            ) from e

    def ensure_source_port(self):
        """
        Lazily determine the source port if it hasn't been acquired yet.
        """
        if self.source_port is None:
            self.source_port = self._acquire_port()

    def init_poolmanager(self, *args, **kwargs):
        """
        Overrides original poolmanager function to initialize the connection pool manager with the static source address.
        This is where the static port is actually set for the requests.
        """
        self.ensure_source_port()
        kwargs['source_address'] = ('0.0.0.0', self.source_port)
        return super().init_poolmanager(*args, **kwargs)



class TelemetryHTTPClient:
    """
    HTTP client for telemetry requests that uses a consistent source port
    across all requests throughout the plugin's runtime.
    Port MIGHT change if taken between requests, but this is very rare.
    """

    def __init__(self):
        """
        Construct fields - Initialization occures at first request
        """
        self.session = None
        self.adapter = None
        self.source_port = None
        self.session_creation_attempted = False

    def ensure_session_ready(self):
        try:
            self.session = requests.Session()
            self._mount_adapter()

            logging.info('Telemetry HTTP client initialized successfully and bound to port: %s', self.source_port)
        except Exception: # pylint: disable=broad-exception-caught
            logging.error(
                "Failed to mount HTTP adapter - Falling back to normal requests using requests.get", exc_info=True
            )
            self.session = None
            self.adapter = None
            self.source_port = None
        finally:
            self.session_creation_attempted = True

    def get_telemetry_data(self, url, **kwargs):
        """
        Perform an HTTP GET request using the persistent session.
        If session fails because port is taken, a refresh attempt will be made.
        Falls back to normal requests.get when all fails.

        Args:
            url: The URL to request
            **kwargs: Additional arguments to pass to requests.get()
            
        Returns:
            requests.Response: The response object
        """
        # Initialization takes place at first request for socket binding to occur in background job and not before
        if not self.session_creation_attempted:
            self.ensure_session_ready()

        try:
            logging.debug(
                "Attempting to send request from port: %s", self.source_port
            )
            return self.session.get(url, **kwargs)
        except Exception: # pylint: disable=broad-exception-caught
            logging.warning(
                'Telemetry HTTP request failed, Attempting to acquire a new port and retry The request.'
            )

            try:
                self._refresh_session_port() # Attempting to change port
                return self.session.get(url, **kwargs)
            except Exception: # pylint: disable=broad-exception-caught
                logging.error(
                    'Telemetry HTTP request failed again after port refresh attempt. '
                    'Falling back to a direct requests.get call.',
                    exc_info=True,
                )
                return requests.get(url, **kwargs) # pylint: disable=missing-timeout

    def close(self):
        """
        Close the session and release resources.
        """
        if self.session:
            self.session.close()

    def _mount_adapter(self):
        """
        Mount a SourcePortAdapter on the current session.
        """
        adapter = SourcePortAdapter()
        adapter.ensure_source_port()
        self.session.mount('http://', adapter)
        self.adapter = adapter
        self.source_port = adapter.source_port

    def _refresh_session_port(self):
        """
        Refresh the source port and remount the adapter.
        Used if original port was taken by the OS for a different process.
        """
        try:
            if self.adapter:
                self.adapter.close()
        except Exception: # pylint: disable=broad-exception-caught
            logging.debug('Failed to close existing HTTP adapter before refresh', exc_info=True)

        if self.session:
            self._mount_adapter()
        else:
            self.ensure_session_ready()
