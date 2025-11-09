#!/usr/bin/python3

"""
Unit tests for the TelemetryHTTPClient and SourcePortAdapter classes.

Tests verify:
- The same ephemeral source port is maintained across all requests
- Source port consistency across different destination hosts
- Session reuse and adapter mounting

@author: Yotam Ashman
"""

import socket
from unittest.mock import MagicMock, patch
import sys
import os
import pytest

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from telemetry_http_client import SourcePortAdapter, TelemetryHTTPClient


@pytest.fixture(autouse=True)
def reset_source_port():
    SourcePortAdapter._source_port = None
    yield
    SourcePortAdapter._source_port = None


@pytest.fixture
def http_client():
    return TelemetryHTTPClient()

class TestSourcePortAdapter:

    def test_source_port_is_assigned_on_first_init(self):
        adapter = SourcePortAdapter()
        
        # Verify a port was assigned
        assert SourcePortAdapter._source_port is not None
        assert isinstance(SourcePortAdapter._source_port, int)

        EPHEMERAL_PORT_MIN = 1024
        EPHEMERAL_PORT_MAX = 65535
        assert SourcePortAdapter._source_port > EPHEMERAL_PORT_MIN
        assert SourcePortAdapter._source_port <= EPHEMERAL_PORT_MAX

    def test_source_port_remains_consistent(self):
        adapter1 = SourcePortAdapter()
        port1 = SourcePortAdapter._source_port
        
        adapter2 = SourcePortAdapter()
        port2 = SourcePortAdapter._source_port
        
        adapter3 = SourcePortAdapter()
        port3 = SourcePortAdapter._source_port
        
        assert port1 == port2 == port3

    def test_init_poolmanager_sets_source_address(self):
        """Test that init_poolmanager sets the correct source address."""
        adapter = SourcePortAdapter()
        expected_port = SourcePortAdapter._source_port

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
        
        assert SourcePortAdapter._source_port is not None

    def test_adapter_mounted_for_http_and_https(self, http_client):
        # Check that adapters are mounted
        assert 'http://' in http_client.session.adapters
        assert 'https://' in http_client.session.adapters
        
        # Verify it's the custom adapter
        assert isinstance(http_client.session.adapters['http://'], SourcePortAdapter)
        assert isinstance(http_client.session.adapters['https://'], SourcePortAdapter)

    @patch('requests.Session.get')
    def test_get_method_uses_session(self, mock_session_get, http_client):
        test_url = 'http://example.com/metrics'
        test_timeout = 30
        mock_response = MagicMock()
        mock_session_get.return_value = mock_response
        
        response = http_client.get_telemetry_metrics(test_url, timeout=test_timeout)
        
        # Verify session.get was called with correct arguments
        mock_session_get.assert_called_once_with(test_url, timeout=test_timeout)
        assert response == mock_response

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
            assert SourcePortAdapter._source_port == 54321


@pytest.mark.parametrize("num_clients", [1, 3, 5, 10])
def test_port_consistency_with_multiple_clients(num_clients):
    SourcePortAdapter._source_port = None  # Reset
    
    clients = [TelemetryHTTPClient() for _ in range(num_clients)]
    ports = [client.get_source_port() for client in clients]
    
    assert len(set(ports)) == 1, f"Expected all ports to be the same, got {set(ports)}"

    EPHEMERAL_PORT_MIN = 1024
    EPHEMERAL_PORT_MAX = 65535
    assert all(EPHEMERAL_PORT_MIN < port <= EPHEMERAL_PORT_MAX for port in ports)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
