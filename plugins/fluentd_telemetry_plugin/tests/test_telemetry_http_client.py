#!/usr/bin/python3

"""
Unit tests for the TelemetryHTTPClient and SourcePortAdapter classes.

Tests verify:
- The same ephemeral source port is maintained across all requests
- Source port consistency across different destination hosts
- Session reuse and adapter mounting

@author: Yotam Ashman
"""

import errno
import os
import socket
import sys
from unittest.mock import MagicMock, patch

import pytest
import requests

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from telemetry_http_client import SourcePortAdapter, TelemetryHTTPClient


@pytest.fixture
def http_client():
    client = TelemetryHTTPClient()
    client.ensure_session_ready()
    return client

class TestSourcePortAdapter:

    def test_source_port_is_assigned_on_first_init(self):
        adapter = SourcePortAdapter()
        
        # Verify a port was assigned
        assert adapter.source_port is not None
        assert isinstance(adapter.source_port, int)

        EPHEMERAL_PORT_MIN = 1024
        EPHEMERAL_PORT_MAX = 65535
        assert adapter.source_port > EPHEMERAL_PORT_MIN
        assert adapter.source_port <= EPHEMERAL_PORT_MAX

    def test_source_port_unique_per_adapter(self):
        with patch.object(SourcePortAdapter, '_acquire_port', side_effect=[55000, 55001, 55002]):
            adapter1 = SourcePortAdapter()
            adapter2 = SourcePortAdapter()
            adapter3 = SourcePortAdapter()

        assert adapter1.source_port == 55000
        assert adapter2.source_port == 55001
        assert adapter3.source_port == 55002

    def test_init_poolmanager_sets_source_address(self):
        """Test that init_poolmanager sets the correct source address."""
        adapter = SourcePortAdapter()
        expected_port = adapter.source_port

        with patch('requests.adapters.HTTPAdapter.init_poolmanager', return_value=None) as mock_parent:
            adapter.init_poolmanager()
            
            mock_parent.assert_called_once()
            _, call_kwargs = mock_parent.call_args
            assert call_kwargs['source_address'] == ('0.0.0.0', expected_port)
            

class TestTelemetryHTTPClient:

    def test_client_initialization(self, http_client):
        assert http_client.session is not None

        assert http_client.adapter is not None
        assert isinstance(http_client.adapter, SourcePortAdapter)
        
        assert http_client.adapter.source_port is not None

    def test_adapter_mounted_for_http(self, http_client):
        # Check that adapters are mounted
        assert 'http://' in http_client.session.adapters
        
        # Verify it's the custom adapter
        assert isinstance(http_client.session.adapters['http://'], SourcePortAdapter)

    @patch('requests.Session.get')
    def test_get_method_uses_session(self, mock_session_get, http_client):
        test_url = 'http://example.com/metrics'
        test_timeout = 30
        mock_response = MagicMock()
        mock_session_get.return_value = mock_response
        
        response = http_client.get_telemetry_data(test_url, timeout=test_timeout)
        
        # Verify session.get was called with correct arguments
        mock_session_get.assert_called_once_with(test_url, timeout=test_timeout)
        assert response == mock_response

    def test_port_refresh_and_fallback_when_source_port_taken(self):
        """
        This test is meant to cover the rare case where the client has decided on a port to maintain,
        but that port was taken by the OS in between calls (in that time the socket is closed).
        Expected behavior is to attempt port refresh, or fall back to normal requests.get .
        """
        # Setting up the mock environment
        initial_port = 55000
        refreshed_port = 55001

        acquire_side_effect = [initial_port, refreshed_port]
        port_in_use_os_error = OSError(errno.EADDRINUSE, 'Address already in use')
        port_in_use_exception = requests.exceptions.ConnectionError(port_in_use_os_error)
        port_in_use_exception.__cause__ = port_in_use_os_error
        retry_exception = requests.exceptions.Timeout('Timed out')
        fallback_response = MagicMock()

        with patch.object(SourcePortAdapter, '_acquire_port', side_effect=acquire_side_effect) as mock_acquire_port, \
             patch('requests.Session.get') as mock_session_get, \
             patch('requests.get') as mock_requests_get:
            mock_session_get.side_effect = [port_in_use_exception, retry_exception]
            mock_requests_get.return_value = fallback_response

            # Client will first save port 55000
            client = TelemetryHTTPClient()
            client.ensure_session_ready()
            original_adapter = client.adapter

            assert client.source_port == initial_port

            # Request will result in port in use exception
            result = client.get_telemetry_data('http://example.com/metrics', timeout=5)

            # Client is expected to attempt to refresh the port
            assert client.source_port == refreshed_port
            # Since an exception still occurred, client is expected to fall back to normal requests.get
            assert result is fallback_response
            assert mock_acquire_port.call_count == 2
            assert mock_session_get.call_count == 2
            mock_requests_get.assert_called_once_with('http://example.com/metrics', timeout=5)
            assert client.adapter is not original_adapter
            assert client.session.adapters['http://'] is client.adapter

class TestSourcePortAdapterIntegration:

    def test_source_port_binding_mechanism(self):
        """Test the actual mechanism of port assignment via socket binding."""
        with patch('socket.socket') as mock_socket_class:
            # Setup mock socket
            mock_socket = MagicMock()
            mock_socket.__enter__ = MagicMock(return_value=mock_socket)
            mock_socket.__exit__ = MagicMock(return_value=False)
            mock_socket.getsockname.return_value = ('0.0.0.0', 54321)
            mock_socket_class.return_value = mock_socket
            
            adapter = SourcePortAdapter()
            
            # Verify socket was created and bound
            mock_socket_class.assert_called_once_with(socket.AF_INET, socket.SOCK_STREAM)
            mock_socket.bind.assert_called_once_with(('0.0.0.0', 0))
            mock_socket.getsockname.assert_called_once()
            
            # Verify the port was captured
            assert adapter.source_port == 54321

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
