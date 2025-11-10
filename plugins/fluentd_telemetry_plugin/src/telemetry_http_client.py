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
    The source port is determined once and shared across all connection pools.
    """
    _source_port = None

    def __init__(self, initialize_port=True):
        """
        Initialize the adapter and determine the static source port if not already set.
        """
        if initialize_port and self._source_port is None:
            self.acquire_port()

        super().__init__()

    @classmethod
    def acquire_port(cls):
        """
        Open a new socket and capture the OS given port.
        Socket closes after the port is captured for reuse.
        """
        try:
            # Bind a socket to port 0 to let the OS choose an ephemeral port
            # We'll capture this port and reuse it for all subsequent connections
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('0.0.0.0', 0))
                cls._source_port = s.getsockname()[1]
            logging.info('HTTP Client port set to: %d', cls._source_port)
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

    @classmethod
    def refresh_port(cls):
        """
        Acquire a new static source port for future connections.
        Used when port was taken for any reason.
        """
        cls.acquire_port()

    def init_poolmanager(self, *args, **kwargs):
        """
        Overrides original poolmanager function to initialize the connection pool manager with the static source address.
        This is where the static port is actually set for the requests.
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
        self._mount_adapter(initialize_port=True)

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
        try:
            return self.session.get(url, **kwargs)
        except requests.exceptions.RequestException as exc:
            if self._is_port_in_use_error(exc):
                current_port = self.get_source_port()
                logging.warning(
                    'Telemetry HTTP request failed because source port %s is already in use. '
                    'Attempting to acquire a new port and retry the request.',
                    current_port,
                )
                self._refresh_session_port()
                try:
                    return self.session.get(url, **kwargs)
                except requests.exceptions.RequestException as retry_exc:
                    logging.warning(
                        'Telemetry HTTP request failed again after refreshing the source port. '
                        'Falling back to a direct requests.get call.',
                        exc_info=True,
                    )
                    try:
                        return requests.get(url, **kwargs) # pylint: disable=missing-timeout
                    except requests.exceptions.RequestException as fallback_exc:
                        raise fallback_exc from retry_exc # Normal requests failed -> propagate exception
            raise

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

    def _mount_adapter(self, initialize_port):
        """
        Mount a SourcePortAdapter on the current session.
        """
        adapter = SourcePortAdapter(initialize_port=initialize_port)
        self.session.mount('http://', adapter)
        self.adapter = adapter

    def _refresh_session_port(self):
        """
        Refresh the source port and remount the adapter.
        """
        try:
            self.adapter.close()
        except Exception: # pylint: disable=broad-exception-caught
            logging.debug('Failed to close existing HTTP adapter before refresh', exc_info=True)

        SourcePortAdapter.refresh_port()
        self._mount_adapter(initialize_port=False) # Port was set manually

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
