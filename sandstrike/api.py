"""
API client for Avenlis services.

This module provides a high-level interface for interacting with
Avenlis APIs, handling authentication, requests, and responses.
"""

from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from sandstrike.auth import AvenlisAuth
from sandstrike.config import AvenlisConfig
from sandstrike.exceptions import AvenlisAPIError, AvenlisAuthError, AvenlisNetworkError


class AvenlisAPI:
    """
    High-level API client for Avenlis services.
    
    This class provides methods for interacting with various Avenlis APIs,
    handling authentication, retries, and error handling automatically.
    """
    
    def __init__(self, config: Optional[AvenlisConfig] = None, auth: Optional[AvenlisAuth] = None):
        """
        Initialize the API client.
        
        Args:
            config: Optional configuration instance
            auth: Optional authentication instance
        """
        self.config = config or AvenlisConfig()
        self.auth = auth or AvenlisAuth(self.config)
        
        # Create session with retry strategy
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers
        self.session.headers.update({
            "User-Agent": f"avenlis-python/{self.config.get_version()}",
            "Content-Type": "application/json"
        })
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get headers including authentication.
        
        Returns:
            Dictionary of headers
            
        Raises:
            AvenlisAuthError: If not authenticated
        """
        headers = {}
        
        if self.auth.is_authenticated():
            api_key = self.auth.get_api_key()
            headers["Authorization"] = f"Bearer {api_key}"
        
        return headers
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        require_auth: bool = True
    ) -> Dict[str, Any]:
        """
        Make an authenticated request to the API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters
            require_auth: Whether authentication is required
            
        Returns:
            Response data as dictionary
            
        Raises:
            AvenlisAuthError: If authentication is required but not available
            AvenlisAPIError: If API request fails
            AvenlisNetworkError: If network request fails
        """
        if require_auth and not self.auth.is_authenticated():
            raise AvenlisAuthError("Authentication required for this operation")
        
        url = f"{self.config.get_api_host().rstrip('/')}/{endpoint.lstrip('/')}"
        headers = self._get_headers()
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers,
                timeout=self.config.get_timeout()
            )
            
            # Handle different response status codes
            if response.status_code == 401:
                raise AvenlisAuthError("Authentication failed - please login again")
            elif response.status_code == 403:
                raise AvenlisAuthError("Access forbidden - check your permissions")
            elif response.status_code == 404:
                raise AvenlisAPIError(f"Resource not found: {endpoint}", response.status_code)
            elif response.status_code >= 400:
                error_data = {}
                try:
                    error_data = response.json()
                except ValueError:
                    pass
                
                error_message = error_data.get("message", f"HTTP {response.status_code} error")
                raise AvenlisAPIError(error_message, response.status_code, error_data)
            
            # Parse JSON response
            try:
                return response.json()
            except ValueError:
                return {"status": "success", "data": response.text}
                
        except requests.exceptions.ConnectionError as e:
            raise AvenlisNetworkError(f"Connection error: {e}")
        except requests.exceptions.Timeout as e:
            raise AvenlisNetworkError(f"Request timeout: {e}")
        except requests.exceptions.RequestException as e:
            raise AvenlisNetworkError(f"Network error: {e}")
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, require_auth: bool = True) -> Dict[str, Any]:
        """Make a GET request."""
        return self._make_request("GET", endpoint, params=params, require_auth=require_auth)
    
    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None, require_auth: bool = True) -> Dict[str, Any]:
        """Make a POST request."""
        return self._make_request("POST", endpoint, data=data, require_auth=require_auth)
    
    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None, require_auth: bool = True) -> Dict[str, Any]:
        """Make a PUT request."""
        return self._make_request("PUT", endpoint, data=data, require_auth=require_auth)
    
    def delete(self, endpoint: str, require_auth: bool = True) -> Dict[str, Any]:
        """Make a DELETE request."""
        return self._make_request("DELETE", endpoint, require_auth=require_auth)
    
    # Example API methods (to be implemented based on your backend)
    
    def get_user_profile(self) -> Dict[str, Any]:
        """
        Get the current user's profile.
        
        Returns:
            User profile data
        """
        return self.get("/api/v1/user/profile")
    
    def list_conversations(self) -> Dict[str, Any]:
        """
        List user's conversations.
        
        Returns:
            List of conversations
        """
        return self.get("/api/v1/conversations")
    
    def create_conversation(self, title: str, description: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new conversation.
        
        Args:
            title: Conversation title
            description: Optional description
            
        Returns:
            Created conversation data
        """
        data = {"title": title}
        if description:
            data["description"] = description
            
        return self.post("/api/v1/conversations", data=data)
