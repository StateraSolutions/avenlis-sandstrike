"""
Authentication module for Avenlis.

This module handles authentication with Avenlis services, including
API key management, token validation, and user session management.
"""

import json
from typing import Any, Dict, Optional

import jwt
import keyring
import requests
import os

from sandstrike.config import AvenlisConfig
from sandstrike.exceptions import AvenlisAuthError, AvenlisError


class AvenlisAuth:
    """
    Handles authentication with Avenlis services.
    
    This class manages API keys, user sessions, and authentication state
    using secure credential storage via keyring.
    """
    
    KEYRING_SERVICE = "avenlis-cli"
    API_KEY_USERNAME = "api-key"
    USER_INFO_USERNAME = "user-info"
    
    def __init__(self, config: Optional[AvenlisConfig] = None) -> None:
        """Initialize the authentication handler."""
        self.config = config or AvenlisConfig()
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": f"avenlis-cli/{self.config.get_version()}"
        })
    
    def login_with_api_key(self, api_key: str) -> Dict[str, Any]:
        """
        Login using an API key.
        
        Args:
            api_key: The API key to authenticate with
            
        Returns:
            Dict containing user information
            
        Raises:
            AvenlisAuthError: If authentication fails
        """
        if not api_key or not api_key.strip():
            raise AvenlisAuthError("API key cannot be empty")
        
        api_key = api_key.strip()
        
        try:
            # Validate API key with the server
            user_info = self._validate_api_key(api_key)
            
            # Store credentials securely
            self._store_api_key(api_key)
            self._store_user_info(user_info)
            
            return user_info
            
        except requests.RequestException as e:
            raise AvenlisAuthError(f"Network error during authentication: {e}")
        except Exception as e:
            raise AvenlisAuthError(f"Authentication failed: {e}")
    
    def logout(self) -> None:
        """
        Logout and clear all stored credentials.
        """
        try:
            # Clear stored credentials
            keyring.delete_password(self.KEYRING_SERVICE, self.API_KEY_USERNAME)
        except keyring.errors.PasswordDeleteError:
            pass  # Already cleared
        
        try:
            keyring.delete_password(self.KEYRING_SERVICE, self.USER_INFO_USERNAME)
        except keyring.errors.PasswordDeleteError:
            pass  # Already cleared
    
    def is_authenticated(self) -> bool:
        """
        Check if the user is currently authenticated.
        
        Returns:
            True if authenticated, False otherwise
        """
        try:
            api_key = self._get_stored_api_key()
            if not api_key:
                return False
            
            # Validate that the stored API key is still valid
            try:
                self._validate_api_key(api_key)
                return True
            except AvenlisAuthError:
                # API key is no longer valid, clear stored credentials
                self.logout()
                return False
            
        except Exception:
            return False
    
    def get_current_user(self) -> Dict[str, Any]:
        """
        Get information about the current authenticated user.
        
        Returns:
            Dict containing user information
            
        Raises:
            AvenlisAuthError: If not authenticated or user info unavailable
        """
        if not self.is_authenticated():
            raise AvenlisAuthError("Not authenticated")
        
        try:
            user_info_json = keyring.get_password(self.KEYRING_SERVICE, self.USER_INFO_USERNAME)
            if not user_info_json:
                raise AvenlisAuthError("User information not found")
            
            return json.loads(user_info_json)
            
        except (json.JSONDecodeError, keyring.errors.KeyringError) as e:
            raise AvenlisAuthError(f"Failed to retrieve user information: {e}")
    
    def get_api_key(self) -> str:
        """
        Get the stored API key.
        
        Returns:
            The API key string
            
        Raises:
            AvenlisAuthError: If no API key is stored
        """
        api_key = self._get_stored_api_key()
        if not api_key:
            raise AvenlisAuthError("No API key found. Please login first.")
        return api_key
    
    def _validate_api_key(self, api_key: str) -> Dict[str, Any]:
        """
        Validate an API key with the Avenlis server.
        
        Args:
            api_key: The API key to validate
            
        Returns:
            Dict containing user information
            
        Raises:
            AvenlisAuthError: If validation fails
        """
        # Check for debug mode first
        if os.getenv("AVENLIS_DEBUG", "").lower() == "true":
            # Return mock user data for development/testing
            return {
                "id": "dev_user_123",
                "email": "dev@avenlis.com",
                "name": "Development User",
                "plan": "Developer",
                "apiKeys": [],
                "lastLogin": "2024-01-01T00:00:00.000Z"
            }
        
        # Production validation - call your actual backend
        try:
            url = f"{self.config.get_api_host()}/api/v1/auth/validate"
            headers = {"Authorization": f"Bearer {api_key}"}
            response = self._session.get(url, headers=headers, timeout=30)
            
            if response.status_code == 401:
                raise AvenlisAuthError("Invalid API key")
            elif response.status_code == 403:
                raise AvenlisAuthError("API key is valid but access denied")
            elif response.status_code == 404:
                raise AvenlisAuthError("Authentication endpoint not found")
            elif response.status_code != 200:
                raise AvenlisAuthError(f"Server error: {response.status_code} - {response.text}")
            
            user_data = response.json()
            
            # Validate that we received the expected user data structure
            if not isinstance(user_data, dict):
                raise AvenlisAuthError("Invalid response format from server")
            
            required_fields = ["id", "email", "name"]
            missing_fields = [field for field in required_fields if field not in user_data]
            
            if missing_fields:
                raise AvenlisAuthError(f"Missing required user fields: {', '.join(missing_fields)}")
            
            # Add the API key to the user info for reference
            user_data["api_key"] = api_key
            
            return user_data
            
        except requests.exceptions.Timeout:
            raise AvenlisAuthError("Request timeout - server is not responding")
        except requests.exceptions.ConnectionError:
            raise AvenlisAuthError("Connection failed - cannot reach the server")
        except requests.exceptions.RequestException as e:
            raise AvenlisAuthError(f"Network error during authentication: {e}")
        except json.JSONDecodeError:
            raise AvenlisAuthError("Invalid JSON response from server")
        except Exception as e:
            raise AvenlisAuthError(f"Unexpected error during authentication: {e}")
    
    def _get_stored_api_key(self) -> Optional[str]:
        """Get the stored API key from keyring."""
        try:
            return keyring.get_password(self.KEYRING_SERVICE, self.API_KEY_USERNAME)
        except keyring.errors.KeyringError:
            return None
    
    def _store_api_key(self, api_key: str) -> None:
        """Store the API key securely in keyring."""
        try:
            keyring.set_password(self.KEYRING_SERVICE, self.API_KEY_USERNAME, api_key)
        except keyring.errors.KeyringError as e:
            raise AvenlisAuthError(f"Failed to store API key: {e}")
    
    def _store_user_info(self, user_info: Dict[str, Any]) -> None:
        """Store user information securely in keyring."""
        try:
            user_info_json = json.dumps(user_info)
            keyring.set_password(self.KEYRING_SERVICE, self.USER_INFO_USERNAME, user_info_json)
        except (keyring.errors.KeyringError, json.JSONEncodeError) as e:
            raise AvenlisAuthError(f"Failed to store user information: {e}")
