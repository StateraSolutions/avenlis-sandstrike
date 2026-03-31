"""
Tests for authentication functionality.
"""

import pytest
from unittest.mock import Mock, patch

from sandstrike.auth import AvenlisAuth
from sandstrike.config import AvenlisConfig
from sandstrike.exceptions import AvenlisAuthError


class TestAvenlisAuth:
    """Test cases for AvenlisAuth class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = AvenlisConfig()
        self.auth = AvenlisAuth(self.config)
    
    def test_init(self):
        """Test AvenlisAuth initialization."""
        assert self.auth.config == self.config
        assert self.auth.KEYRING_SERVICE == "avenlis-cli"
    
    def test_login_with_empty_api_key(self):
        """Test login with empty API key raises error."""
        with pytest.raises(AvenlisAuthError, match="API key cannot be empty"):
            self.auth.login_with_api_key("")
    
    def test_login_with_none_api_key(self):
        """Test login with None API key raises error."""
        with pytest.raises(AvenlisAuthError, match="API key cannot be empty"):
            self.auth.login_with_api_key(None)
    
    @patch('sandstrike.auth.keyring.set_password')
    def test_login_with_valid_api_key(self, mock_set_password):
        """Test successful login with valid API key."""
        api_key = "valid-api-key-12345"
        
        # Mock the validation to return user info
        with patch.object(self.auth, '_validate_api_key') as mock_validate:
            mock_validate.return_value = {
                "id": "user_123",
                "email": "test@example.com",
                "organization": "Test Org"
            }
            
            result = self.auth.login_with_api_key(api_key)
            
            # Verify the result
            assert result["email"] == "test@example.com"
            assert result["id"] == "user_123"
            
            # Verify keyring calls
            assert mock_set_password.call_count == 2  # API key + user info
    
    @patch('sandstrike.auth.keyring.get_password')
    def test_is_authenticated_with_stored_key(self, mock_get_password):
        """Test is_authenticated with stored API key."""
        mock_get_password.return_value = "valid-api-key"
        
        with patch.object(self.auth, '_validate_api_key') as mock_validate:
            mock_validate.return_value = {"id": "user_123"}
            
            assert self.auth.is_authenticated() is True
    
    @patch('sandstrike.auth.keyring.get_password')
    def test_is_authenticated_without_stored_key(self, mock_get_password):
        """Test is_authenticated without stored API key."""
        mock_get_password.return_value = None
        
        assert self.auth.is_authenticated() is False
    
    @patch('sandstrike.auth.keyring.delete_password')
    def test_logout(self, mock_delete_password):
        """Test logout functionality."""
        self.auth.logout()
        
        # Verify keyring delete calls
        assert mock_delete_password.call_count == 2  # API key + user info
