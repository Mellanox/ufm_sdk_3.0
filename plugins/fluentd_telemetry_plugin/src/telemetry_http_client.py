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
import errno
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
    def __init__(self, source_port=None):
        """
        Initialize the adapter and determine the static source port if not provided.
        """
        if source_port is None:
            source_port = self.acquire_port()

        self.source_port = source_port
        super().__init__()

    @staticmethod
    def acquire_port():
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
            logging.debug('HTTP Client acquired candidate port: %d', port)
            return port
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

    def init_poolmanager(self, *args, **kwargs):
        """
        Overrides original poolmanager function to initialize the connection pool manager with the static source address.
        This is where the static port is actually set for the requests.
        """
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
        self.initialized = False

    def initialize(self):
        if self.initialized:
            logging.warning('HTTP client initialize method called twice!')
            return

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
            # We set initialized to True regardless so that requests can be made no matter what (using requests if needed)
            self.initialized = True

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
        if not self.initialized:
            self.initialize()

        # If initialization failed - fallback on requests.get
        if not self.session:
            return requests.get(url, **kwargs) # pylint: disable=missing-timeout

        try:
            source_port = self.get_source_port()
            logging.debug(
                "Attempting to send request from port: %s", source_port
            )
            return self.session.get(url, **kwargs)
        except Exception as exc: # pylint: disable=broad-exception-caught
            current_port = self.get_source_port()

            if self._is_port_in_use_error(exc):
                logging.warning(
                    'Telemetry HTTP request failed because source port %s is already in use. '
                    'Attempting to acquire a new port and retry the request.',
                    current_port,
                )
            else:
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

    def get_source_port(self):
        """
        Get the static source port being used by this client instance.
        
        Returns:
            int: The source port number
        """
        return self.source_port

    def close(self):
        """
        Close the session and release resources.
        """
        if self.session:
            self.session.close()

    def _mount_adapter(self, source_port=None):
        """
        Mount a SourcePortAdapter on the current session.
        """
        adapter = SourcePortAdapter(source_port=source_port)
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

        self._mount_adapter()

    @staticmethod
    def _is_port_in_use_error(exc):
        """
        Determine if the provided exception (or its causes) indicates the source
        port is already in use by searching the call stack.
        """
        port_errors = {errno.EADDRINUSE, errno.EADDRNOTAVAIL}
        seen = set()
        current = exc

        while current and id(current) not in seen:
            seen.add(id(current))

            if isinstance(current, OSError) and getattr(current, 'errno', None) in port_errors:
                return True

            message = str(current).lower()
            if 'address already in use' in message or 'port already in use' in message:
                return True

            current = getattr(current, '__cause__', None) or getattr(current, '__context__', None)

        return False
