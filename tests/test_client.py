#!/usr/bin/env python3
"""
Unit tests for the client module.
"""

import time
from unittest.mock import Mock, patch, MagicMock
import pytest
import requests

# Add the src directory to the path
import sys
sys.path.insert(0, '/opt/es-keap-database/src')

from keap_export.client import KeapClient
from keap_export.config import Settings


class TestKeapClient:
    """Test the KeapClient class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.cfg = Settings(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="https://example.com/callback",
            base_url="https://api.infusionsoft.com",
            api_key="test_api_key"
        )
        self.client = KeapClient(self.cfg)
    
    def test_init_with_api_key(self):
        """Test client initialization with API key."""
        assert self.client.cfg == self.cfg
        assert self.client.base == "https://api.infusionsoft.com"
        assert self.client.session is not None
    
    def test_init_without_api_key(self):
        """Test client initialization without API key."""
        cfg_no_key = Settings(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="https://example.com/callback",
            base_url="https://api.infusionsoft.com"
        )
        client = KeapClient(cfg_no_key)
        assert client.cfg == cfg_no_key
    
    @patch('keap_export.client.load_token_bundle')
    def test_headers_with_api_key(self, mock_load_tokens):
        """Test headers generation with API key."""
        headers = self.client._headers()
        
        assert "Accept" in headers
        assert headers["Accept"] == "application/json"
        assert "X-Keap-API-Key" in headers
        assert headers["X-Keap-API-Key"] == "test_api_key"
        assert "Authorization" not in headers
    
    @patch('keap_export.client.load_token_bundle')
    def test_headers_without_api_key(self, mock_load_tokens):
        """Test headers generation without API key."""
        cfg_no_key = Settings(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="https://example.com/callback",
            base_url="https://api.infusionsoft.com"
        )
        client = KeapClient(cfg_no_key)
        
        # Mock token bundle
        mock_tb = Mock()
        mock_tb.access_token = "test_access_token"
        mock_tb.is_expired = False
        mock_load_tokens.return_value = mock_tb
        
        headers = client._headers()
        
        assert "Accept" in headers
        assert headers["Accept"] == "application/json"
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test_access_token"
        assert "X-Keap-API-Key" not in headers
    
    @patch('keap_export.client.load_token_bundle')
    def test_headers_with_expired_token(self, mock_load_tokens):
        """Test headers generation with expired token."""
        cfg_no_key = Settings(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="https://example.com/callback",
            base_url="https://api.infusionsoft.com"
        )
        client = KeapClient(cfg_no_key)
        
        # Mock expired token bundle
        mock_tb = Mock()
        mock_tb.access_token = "expired_token"
        mock_tb.is_expired = True
        mock_tb.refresh_token = "refresh_token"
        mock_load_tokens.return_value = mock_tb
        
        with patch('keap_export.client.refresh_tokens') as mock_refresh:
            mock_new_tb = Mock()
            mock_new_tb.access_token = "new_token"
            mock_new_tb.is_expired = False
            mock_refresh.return_value = mock_new_tb
            
            with patch('keap_export.client.save_token_bundle') as mock_save:
                headers = client._headers()
                
                # Verify refresh was called
                mock_refresh.assert_called_once_with(cfg_no_key, "refresh_token")
                mock_save.assert_called_once_with(cfg_no_key, mock_new_tb)
                
                assert headers["Authorization"] == "Bearer new_token"
    
    @patch('keap_export.client.load_token_bundle')
    def test_headers_no_tokens(self, mock_load_tokens):
        """Test headers generation when no tokens are available."""
        cfg_no_key = Settings(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="https://example.com/callback",
            base_url="https://api.infusionsoft.com"
        )
        client = KeapClient(cfg_no_key)
        
        mock_load_tokens.return_value = None
        
        with pytest.raises(RuntimeError, match="No OAuth tokens found"):
            client._headers()
    
    def test_handle_throttle_headers_no_throttle(self):
        """Test throttle handling with no throttle headers."""
        mock_response = Mock()
        mock_response.headers = {}
        
        # Should not raise any exceptions
        self.client._handle_throttle_headers(mock_response)
    
    def test_handle_throttle_headers_critical_throttle(self):
        """Test throttle handling with critical throttle."""
        mock_response = Mock()
        mock_response.headers = {
            'x-keap-product-throttle-available': '5'
        }
        
        with patch('time.sleep') as mock_sleep:
            self.client._handle_throttle_headers(mock_response)
            mock_sleep.assert_called_once_with(5.0)
    
    def test_handle_throttle_headers_low_throttle(self):
        """Test throttle handling with low throttle."""
        mock_response = Mock()
        mock_response.headers = {
            'x-keap-product-throttle-available': '25'
        }
        
        with patch('time.sleep') as mock_sleep:
            self.client._handle_throttle_headers(mock_response)
            mock_sleep.assert_called_once_with(2.0)
    
    def test_handle_throttle_headers_medium_throttle(self):
        """Test throttle handling with medium throttle."""
        mock_response = Mock()
        mock_response.headers = {
            'x-keap-product-throttle-available': '75'
        }
        
        with patch('time.sleep') as mock_sleep:
            self.client._handle_throttle_headers(mock_response)
            mock_sleep.assert_called_once_with(0.5)
    
    def test_handle_throttle_headers_good_throttle(self):
        """Test throttle handling with good throttle level."""
        mock_response = Mock()
        mock_response.headers = {
            'x-keap-product-throttle-available': '500'
        }
        
        with patch('time.sleep') as mock_sleep:
            self.client._handle_throttle_headers(mock_response)
            mock_sleep.assert_not_called()
    
    def test_handle_throttle_headers_multiple_headers(self):
        """Test throttle handling with multiple throttle headers."""
        mock_response = Mock()
        mock_response.headers = {
            'x-keap-product-throttle-available': '100',
            'x-keap-api-throttle-available': '25'
        }
        
        with patch('time.sleep') as mock_sleep:
            self.client._handle_throttle_headers(mock_response)
            # Should use the lowest value (25)
            mock_sleep.assert_called_once_with(2.0)
    
    def test_handle_throttle_headers_invalid_values(self):
        """Test throttle handling with invalid header values."""
        mock_response = Mock()
        mock_response.headers = {
            'x-keap-product-throttle-available': 'invalid',
            'x-keap-api-throttle-available': '50'
        }
        
        with patch('time.sleep') as mock_sleep:
            self.client._handle_throttle_headers(mock_response)
            # Should use the valid value (50)
            mock_sleep.assert_called_once_with(2.0)
    
    @patch('requests.Session.request')
    def test_request_success(self, mock_request):
        """Test successful request."""
        mock_response = Mock()
        mock_response.headers = {'x-keap-product-throttle-available': '1000'}
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        response = self.client.request('GET', '/test')
        
        assert response == mock_response
        mock_request.assert_called_once()
    
    @patch('requests.Session.request')
    def test_request_with_throttle_handling(self, mock_request):
        """Test request with throttle handling."""
        mock_response = Mock()
        mock_response.headers = {'x-keap-product-throttle-available': '10'}
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        with patch.object(self.client, '_handle_throttle_headers') as mock_handle:
            response = self.client.request('GET', '/test')
            
            mock_handle.assert_called_once_with(mock_response)
            assert response == mock_response
    
    @patch('requests.Session.request')
    def test_request_401_with_oauth(self, mock_request):
        """Test request with 401 error and OAuth retry."""
        cfg_no_key = Settings(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="https://example.com/callback",
            base_url="https://api.infusionsoft.com"
        )
        client = KeapClient(cfg_no_key)
        
        # First call returns 401, second call succeeds
        mock_response_401 = Mock()
        mock_response_401.raise_for_status.side_effect = requests.HTTPError("401 Unauthorized")
        
        mock_response_success = Mock()
        mock_response_success.headers = {'x-keap-product-throttle-available': '1000'}
        mock_response_success.raise_for_status.return_value = None
        
        mock_request.side_effect = [mock_response_401, mock_response_success]
        
        with patch('keap_export.client.load_token_bundle') as mock_load:
            mock_tb = Mock()
            mock_tb.refresh_token = "refresh_token"
            mock_load.return_value = mock_tb
            
            with patch('keap_export.client.refresh_tokens') as mock_refresh:
                mock_new_tb = Mock()
                mock_refresh.return_value = mock_new_tb
                
                with patch('keap_export.client.save_token_bundle') as mock_save:
                    response = client.request('GET', '/test')
                    
                    # Should have made two requests
                    assert mock_request.call_count == 2
                    mock_refresh.assert_called_once()
                    mock_save.assert_called_once()
                    assert response == mock_response_success
    
    def test_fetch_all_basic(self):
        """Test basic fetch_all functionality."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'contacts': [
                {'id': 1, 'name': 'Contact 1'},
                {'id': 2, 'name': 'Contact 2'}
            ]
        }
        mock_response.raise_for_status.return_value = None
        
        with patch.object(self.client, 'request', return_value=mock_response) as mock_request:
            items = list(self.client.fetch_all('/contacts', limit=2))
            
            assert len(items) == 2
            assert items[0]['id'] == 1
            assert items[1]['id'] == 2
            mock_request.assert_called_once()
    
    def test_fetch_all_pagination(self):
        """Test fetch_all with pagination."""
        # First page
        mock_response_1 = Mock()
        mock_response_1.json.return_value = {
            'contacts': [
                {'id': 1, 'name': 'Contact 1'},
                {'id': 2, 'name': 'Contact 2'}
            ]
        }
        mock_response_1.raise_for_status.return_value = None
        
        # Second page
        mock_response_2 = Mock()
        mock_response_2.json.return_value = {
            'contacts': [
                {'id': 3, 'name': 'Contact 3'}
            ]
        }
        mock_response_2.raise_for_status.return_value = None
        
        with patch.object(self.client, 'request', side_effect=[mock_response_1, mock_response_2]) as mock_request:
            items = list(self.client.fetch_all('/contacts', limit=2))
            
            assert len(items) == 3
            assert items[0]['id'] == 1
            assert items[1]['id'] == 2
            assert items[2]['id'] == 3
            assert mock_request.call_count == 2
    
    def test_fetch_all_empty_response(self):
        """Test fetch_all with empty response."""
        mock_response = Mock()
        mock_response.json.return_value = {'contacts': []}
        mock_response.raise_for_status.return_value = None
        
        with patch.object(self.client, 'request', return_value=mock_response) as mock_request:
            items = list(self.client.fetch_all('/contacts'))
            
            assert len(items) == 0
            mock_request.assert_called_once()
    
    def test_fetch_all_list_response(self):
        """Test fetch_all with list response."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {'id': 1, 'name': 'Item 1'},
            {'id': 2, 'name': 'Item 2'}
        ]
        mock_response.raise_for_status.return_value = None
        
        with patch.object(self.client, 'request', return_value=mock_response) as mock_request:
            items = list(self.client.fetch_all('/items'))
            
            assert len(items) == 2
            assert items[0]['id'] == 1
            assert items[1]['id'] == 2
            mock_request.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

