#!/usr/bin/env python3
"""
Unit tests for the auth module.
"""

import json
import time
import tempfile
import os
from unittest.mock import Mock, patch, mock_open
import pytest
import requests

# Add the src directory to the path
import sys
sys.path.insert(0, '/opt/es-keap-database/src')

from keap_export.auth import (
    TokenBundle, 
    build_authorize_url, 
    exchange_code_for_tokens, 
    refresh_tokens, 
    load_token_bundle, 
    save_token_bundle
)
from keap_export.config import Settings


class TestTokenBundle:
    """Test the TokenBundle dataclass."""
    
    def test_token_bundle_creation(self):
        """Test creating a TokenBundle."""
        tb = TokenBundle("access123", "refresh456", time.time() + 3600)
        assert tb.access_token == "access123"
        assert tb.refresh_token == "refresh456"
        assert tb.expires_at > time.time()
    
    def test_is_expired_false(self):
        """Test is_expired returns False for valid token."""
        tb = TokenBundle("access123", "refresh456", time.time() + 3600)
        assert not tb.is_expired
    
    def test_is_expired_true(self):
        """Test is_expired returns True for expired token."""
        tb = TokenBundle("access123", "refresh456", time.time() - 3600)
        assert tb.is_expired
    
    def test_is_expired_near_expiry(self):
        """Test is_expired returns True when within 60 seconds of expiry."""
        tb = TokenBundle("access123", "refresh456", time.time() + 30)
        assert tb.is_expired


class TestBuildAuthorizeUrl:
    """Test the build_authorize_url function."""
    
    def test_build_authorize_url_basic(self):
        """Test building authorize URL with basic parameters."""
        cfg = Settings(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="https://example.com/callback",
            base_url="https://api.infusionsoft.com"
        )
        
        url = build_authorize_url(cfg)
        
        assert "https://accounts.infusionsoft.com/app/oauth/authorize" in url
        assert "client_id=test_client" in url
        assert "redirect_uri=https%3A%2F%2Fexample.com%2Fcallback" in url
        assert "response_type=code" in url
        assert "scope=full" in url
        assert "state=keap_export" in url
    
    def test_build_authorize_url_custom_state(self):
        """Test building authorize URL with custom state."""
        cfg = Settings(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="https://example.com/callback",
            base_url="https://api.infusionsoft.com"
        )
        
        url = build_authorize_url(cfg, state="custom_state")
        
        assert "state=custom_state" in url


class TestExchangeCodeForTokens:
    """Test the exchange_code_for_tokens function."""
    
    @patch('requests.post')
    def test_exchange_code_for_tokens_success(self, mock_post):
        """Test successful token exchange."""
        # Mock the response
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 3600
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        cfg = Settings(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="https://example.com/callback",
            base_url="https://api.infusionsoft.com"
        )
        
        tb = exchange_code_for_tokens(cfg, "auth_code_123")
        
        # Verify the request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://api.infusionsoft.com/token"
        assert call_args[1]["headers"]["Content-Type"] == "application/x-www-form-urlencoded"
        
        # Verify the data sent
        data = call_args[1]["data"]
        assert data["grant_type"] == "authorization_code"
        assert data["code"] == "auth_code_123"
        assert data["redirect_uri"] == "https://example.com/callback"
        assert data["client_id"] == "test_client"
        assert data["client_secret"] == "test_secret"
        
        # Verify the returned TokenBundle
        assert tb.access_token == "new_access_token"
        assert tb.refresh_token == "new_refresh_token"
        assert tb.expires_at > time.time()
    
    @patch('requests.post')
    def test_exchange_code_for_tokens_http_error(self, mock_post):
        """Test token exchange with HTTP error."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("401 Unauthorized")
        mock_post.return_value = mock_response
        
        cfg = Settings(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="https://example.com/callback",
            base_url="https://api.infusionsoft.com"
        )
        
        with pytest.raises(requests.HTTPError):
            exchange_code_for_tokens(cfg, "invalid_code")


class TestRefreshTokens:
    """Test the refresh_tokens function."""
    
    @patch('requests.post')
    def test_refresh_tokens_success(self, mock_post):
        """Test successful token refresh."""
        # Mock the response
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "refreshed_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 3600
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        cfg = Settings(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="https://example.com/callback",
            base_url="https://api.infusionsoft.com"
        )
        
        tb = refresh_tokens(cfg, "old_refresh_token")
        
        # Verify the request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://api.infusionsoft.com/token"
        assert call_args[1]["headers"]["Content-Type"] == "application/x-www-form-urlencoded"
        
        # Verify the data sent
        data = call_args[1]["data"]
        assert data["grant_type"] == "refresh_token"
        assert data["refresh_token"] == "old_refresh_token"
        assert data["client_id"] == "test_client"
        assert data["client_secret"] == "test_secret"
        
        # Verify the returned TokenBundle
        assert tb.access_token == "refreshed_access_token"
        assert tb.refresh_token == "new_refresh_token"
        assert tb.expires_at > time.time()
    
    @patch('requests.post')
    def test_refresh_tokens_http_error(self, mock_post):
        """Test token refresh with HTTP error."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("401 Unauthorized")
        mock_post.return_value = mock_response
        
        cfg = Settings(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="https://example.com/callback",
            base_url="https://api.infusionsoft.com"
        )
        
        with pytest.raises(requests.HTTPError):
            refresh_tokens(cfg, "invalid_refresh_token")


class TestLoadTokenBundle:
    """Test the load_token_bundle function."""
    
    @patch('keap_export.auth.load_tokens')
    def test_load_token_bundle_success(self, mock_load_tokens):
        """Test successful token bundle loading."""
        mock_load_tokens.return_value = {
            "access_token": "loaded_access_token",
            "refresh_token": "loaded_refresh_token",
            "expires_at": time.time() + 3600
        }
        
        cfg = Settings(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="https://example.com/callback",
            base_url="https://api.infusionsoft.com",
            token_file="/tmp/test_tokens.json"
        )
        
        tb = load_token_bundle(cfg)
        
        assert tb is not None
        assert tb.access_token == "loaded_access_token"
        assert tb.refresh_token == "loaded_refresh_token"
        assert tb.expires_at > time.time()
    
    @patch('keap_export.auth.load_tokens')
    def test_load_token_bundle_no_file(self, mock_load_tokens):
        """Test loading when no token file exists."""
        mock_load_tokens.return_value = None
        
        cfg = Settings(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="https://example.com/callback",
            base_url="https://api.infusionsoft.com",
            token_file="/tmp/nonexistent.json"
        )
        
        tb = load_token_bundle(cfg)
        
        assert tb is None


class TestSaveTokenBundle:
    """Test the save_token_bundle function."""
    
    def test_save_token_bundle_success(self):
        """Test successful token bundle saving."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_file = f.name
        
        try:
            cfg = Settings(
                client_id="test_client",
                client_secret="test_secret",
                redirect_uri="https://example.com/callback",
                base_url="https://api.infusionsoft.com",
                token_file=temp_file
            )
            
            tb = TokenBundle("save_access_token", "save_refresh_token", time.time() + 3600)
            save_token_bundle(cfg, tb)
            
            # Verify the file was written correctly
            with open(temp_file, 'r') as f:
                data = json.load(f)
            
            assert data["access_token"] == "save_access_token"
            assert data["refresh_token"] == "save_refresh_token"
            assert data["expires_at"] > time.time()
            
        finally:
            os.unlink(temp_file)
    
    def test_save_token_bundle_file_error(self):
        """Test token bundle saving with file error."""
        cfg = Settings(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="https://example.com/callback",
            base_url="https://api.infusionsoft.com",
            token_file="/nonexistent/path/tokens.json"
        )
        
        tb = TokenBundle("save_access_token", "save_refresh_token", time.time() + 3600)
        
        with pytest.raises(FileNotFoundError):
            save_token_bundle(cfg, tb)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

