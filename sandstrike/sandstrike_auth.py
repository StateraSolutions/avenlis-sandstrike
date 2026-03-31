"""
SandStrike Authentication module for API key verification.

This module handles authentication with the Avenlis platform backend to verify
if users are paid subscribers and can access SandStrike features.
"""

import json
import os
import time
from typing import Any, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

import requests
import keyring

from sandstrike.exceptions import AvenlisError


def load_env_file(env_path: str = '.env') -> None:
    """Load environment variables from .env file."""
    try:
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        if key and value:
                            os.environ[key] = value
    except Exception as e:
        print(f"Warning: Could not load .env file: {e}")


# Load .env file when module is imported
load_env_file()


@dataclass
class UserSubscription:
    """User subscription information."""
    user_id: str
    email: str
    first_name: str
    last_name: str
    subscription_plan: str
    subscription_status: str  # active, expired, cancelled, trial
    subscription_expires: Optional[datetime]
    is_paid_user: bool
    features: list
    cached_at: Optional[datetime] = None


class SandStrikeAuth:
    """
    Handles SandStrike authentication with Avenlis platform backend.
    
    This class manages API key verification, subscription status checking,
    and feature access control for paid users.
    """
    
    KEYRING_SERVICE = "sandstrike-auth"
    API_KEY_USERNAME = "avenlis-api-key"
    SUBSCRIPTION_USERNAME = "subscription-info"
    
    # Avenlis platform backend URL
    PLATFORM_BASE_URL = "https://avenlis.staterasolv.com/api"
    
    def __init__(self, config: Optional[Dict] = None) -> None:
        """Initialize the SandStrike authentication handler."""
        self.config = config or {}
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "SandStrike/1.0",
            "Content-Type": "application/json"
        })
        
        # Cache settings
        self.cache_duration = timedelta(hours=1)  # Cache subscription info for 1 hour
        
    def verify_api_key(self, api_key: str = None) -> Tuple[bool, Optional[UserSubscription]]:
        """
        Verify API key with Avenlis platform backend.
        
        Args:
            api_key: The API key to verify (can be None to use environment variable)
            
        Returns:
            Tuple of (is_valid, subscription_info)
        """
        # If no API key provided, try to get from environment
        if not api_key:
            api_key = os.getenv('AVENLIS_API_KEY')
            if not api_key:
                return False, None
        
        if not api_key.strip():
            return False, None
            
        api_key = api_key.strip()
        
        try:
            # Check cache first
            cached_subscription = self._get_cached_subscription(api_key)
            if cached_subscription and self._is_cache_valid(cached_subscription):
                return True, cached_subscription
            
            # Verify with backend
            subscription = self._verify_with_backend(api_key)
            if subscription:
                # Cache the result
                self._cache_subscription(api_key, subscription)
                return True, subscription
            else:
                return False, None
                
        except Exception as e:
            print(f"Error verifying API key: {e}")
            return False, None
    
    def is_paid_user(self, api_key: str = None) -> bool:
        """
        Check if the user has a paid subscription.
        
        Args:
            api_key: The API key to check (optional, uses environment variable if not provided)
            
        Returns:
            True if user has paid subscription, False otherwise
        """
        is_valid, subscription = self.verify_api_key(api_key)
        if not is_valid or not subscription:
            return False
            
        return subscription.is_paid_user and subscription.subscription_status == "active"
    
    def get_user_features(self, api_key: str = None) -> list:
        """
        Get available features for the user.
        
        Args:
            api_key: The API key to check (optional, uses environment variable if not provided)
            
        Returns:
            List of available features
        """
        is_valid, subscription = self.verify_api_key(api_key)
        if not is_valid or not subscription:
            return []
            
        return subscription.features
    
    def store_api_key(self, api_key: str) -> bool:
        """
        Store API key securely for future use.
        
        Args:
            api_key: The API key to store
            
        Returns:
            True if stored successfully, False otherwise
        """
        try:
            # Verify the API key first
            is_valid, subscription = self.verify_api_key(api_key)
            if not is_valid:
                return False
                
            # Store the API key
            keyring.set_password(self.KEYRING_SERVICE, self.API_KEY_USERNAME, api_key)
            
            # Store subscription info
            if subscription:
                self._store_subscription_info(subscription)
                
            return True
            
        except Exception as e:
            print(f"Error storing API key: {e}")
            return False
    
    def get_stored_api_key(self) -> Optional[str]:
        """
        Get the stored API key.
        
        Returns:
            The stored API key or None if not found
        """
        try:
            return keyring.get_password(self.KEYRING_SERVICE, self.API_KEY_USERNAME)
        except Exception:
            return None
    
    def clear_stored_credentials(self) -> None:
        """Clear all stored credentials."""
        try:
            keyring.delete_password(self.KEYRING_SERVICE, self.API_KEY_USERNAME)
            keyring.delete_password(self.KEYRING_SERVICE, self.SUBSCRIPTION_USERNAME)
        except Exception:
            pass  # Ignore errors when clearing
    
    def clear_subscription_cache(self, api_key: str = None) -> None:
        """Clear cached subscription information for a specific API key or all caches."""
        try:
            if api_key:
                # Clear cache for specific API key
                cache_key = f"sub_{hash(api_key)}"
                keyring.delete_password(self.KEYRING_SERVICE, cache_key)
            else:
                # Clear all subscription caches by clearing stored credentials
                # Note: This is a simplified approach. For a more thorough clear,
                # we'd need to track all cache keys, but this is sufficient for most cases
                self.clear_stored_credentials()
        except Exception:
            pass  # Ignore errors when clearing cache
    
    def _verify_with_backend(self, api_key: str) -> Optional[UserSubscription]:
        """
        Verify API key with Avenlis Platform.
        
        Args:
            api_key: The API key to verify
            
        Returns:
            UserSubscription object if valid, None otherwise
        """
        try:
            # Call the Otterback API
            response = self._session.post(
                f"{self.PLATFORM_BASE_URL}/users/validate",
                json={"apiKey": api_key},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Map Otterback simplified response to UserSubscription
                subscription_plan_raw = data.get('subscriptionPlan', 'free')
                subscription_plan = subscription_plan_raw.lower() if isinstance(subscription_plan_raw, str) else ('pro' if subscription_plan_raw else 'free')
                subscription_status = 'active'  # Otterback doesn't have status field, assume active if user exists
                is_paid_user = subscription_plan in ['pro', 'enterprise', 'premium']  # Check if it's a paid plan
                
                # Get available features based on subscription
                features = self._get_features_for_plan(subscription_plan, subscription_status)
                
                return UserSubscription(
                    user_id='',  # Not provided in simplified response
                    email=data.get('email', ''),
                    first_name='',  # Not provided in simplified response
                    last_name='',  # Not provided in simplified response
                    subscription_plan=subscription_plan,
                    subscription_status=subscription_status,
                    subscription_expires=None,  # Otterback doesn't track expiration
                    is_paid_user=is_paid_user,
                    features=features,
                    cached_at=datetime.utcnow()
                )
                
            elif response.status_code == 401:
                print("Invalid API key")
                return None
            else:
                print(f"Otterback API verification failed: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Network error during API verification: {e}")
            return None
        except Exception as e:
            print(f"Error during API verification: {e}")
            return None
    
    def _get_features_for_plan(self, plan: str, status: str = 'active') -> list:
        """
        Get available features for a subscription plan based on the feature comparison table.
        
        Args:
            plan: The subscription plan name
            status: The subscription status
            
        Returns:
            List of available features
        """
        features = {
            'free': [
                'Prompts, Collections, Sessions & Dashboard (UI + CLI)',
                'LLMs for Local & HTTP Endpoints Testing',
                'Response Graders (Basic)',
                'MITRE ATLAS Navigator',
                'OWASP Top 10 LLM Navigator'
            ],
            'pro': [
                'Prompts, Collections, Sessions & Dashboard (UI + CLI)',
                'LLMs for Local & HTTP Endpoints Testing',
                'Response Graders (All + Avenlis Copilot Grader)',
                'MITRE ATLAS Navigator',
                'OWASP Top 10 LLM Navigator',
                'Reports Components (UI + CLI)'
            ],
            'enterprise': [
                'SandStrike Library Package',
                'Prompts, Collections, Sessions & Dashboard (UI + CLI)',
                'LLMs for Local & HTTP Endpoints Testing',
                'Response Graders (All + Avenlis Copilot Grader)',
                'MITRE ATLAS Navigator',
                'OWASP Top 10 LLM Navigator',
                'Reports Components (UI + CLI)',
                'Custom Features & Dashboard',
                'Custom Integrations',
                'Dedicated Support'
            ],
            'premium': [
                'SandStrike Library Package',
                'Prompts, Collections, Sessions & Dashboard (UI + CLI)',
                'LLMs for Local & HTTP Endpoints Testing',
                'Response Graders (All + Avenlis Copilot Grader)',
                'MITRE ATLAS Navigator',
                'OWASP Top 10 LLM Navigator',
                'Reports Components (UI + CLI)',
                'Advanced Analytics',
                'Custom Integrations'
            ]
        }
        
        return features.get(plan.lower(), features['free'])
    
    def _cache_subscription(self, api_key: str, subscription: UserSubscription) -> None:
        """Cache subscription information."""
        try:
            # Create a cache key based on API key hash
            cache_key = f"sub_{hash(api_key)}"
            
            # Serialize subscription data
            cache_data = {
                'user_id': subscription.user_id,
                'email': subscription.email,
                'first_name': subscription.first_name,
                'last_name': subscription.last_name,
                'subscription_plan': subscription.subscription_plan,
                'subscription_status': subscription.subscription_status,
                'subscription_expires': subscription.subscription_expires.isoformat() if subscription.subscription_expires else None,
                'is_paid_user': subscription.is_paid_user,
                'features': subscription.features,
                'cached_at': subscription.cached_at.isoformat() if subscription.cached_at else datetime.utcnow().isoformat()
            }
            
            keyring.set_password(self.KEYRING_SERVICE, cache_key, json.dumps(cache_data))
            
        except Exception:
            pass  # Ignore caching errors
    
    def _get_cached_subscription(self, api_key: str) -> Optional[UserSubscription]:
        """Get cached subscription information."""
        try:
            cache_key = f"sub_{hash(api_key)}"
            cached_data = keyring.get_password(self.KEYRING_SERVICE, cache_key)
            
            if not cached_data:
                return None
                
            data = json.loads(cached_data)
            
            # Reconstruct UserSubscription object
            subscription_expires = None
            if data.get('subscription_expires'):
                subscription_expires = datetime.fromisoformat(data['subscription_expires'])
            
            cached_at = None
            if data.get('cached_at'):
                cached_at = datetime.fromisoformat(data['cached_at'])
            
            return UserSubscription(
                user_id=data['user_id'],
                email=data['email'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                subscription_plan=data['subscription_plan'],
                subscription_status=data['subscription_status'],
                subscription_expires=subscription_expires,
                is_paid_user=data['is_paid_user'],
                features=data['features'],
                cached_at=cached_at
            )
            
        except Exception:
            return None
    
    def _is_cache_valid(self, subscription: UserSubscription) -> bool:
        """Check if cached subscription data is still valid."""
        if not subscription.cached_at:
            return False
        cache_age = datetime.utcnow() - subscription.cached_at
        return cache_age < self.cache_duration
    
    def _store_subscription_info(self, subscription: UserSubscription) -> None:
        """Store subscription information."""
        try:
            data = {
                'user_id': subscription.user_id,
                'email': subscription.email,
                'subscription_plan': subscription.subscription_plan,
                'subscription_status': subscription.subscription_status,
                'is_paid_user': subscription.is_paid_user,
                'cached_at': subscription.cached_at.isoformat() if subscription.cached_at else datetime.utcnow().isoformat()
            }
            
            keyring.set_password(
                self.KEYRING_SERVICE, 
                self.SUBSCRIPTION_USERNAME, 
                json.dumps(data)
            )
            
        except Exception:
            pass  # Ignore storage errors


# Global instance for easy access
_sandstrike_auth = None

def get_sandstrike_auth() -> SandStrikeAuth:
    """Get the global SandStrike authentication instance."""
    global _sandstrike_auth
    if _sandstrike_auth is None:
        _sandstrike_auth = SandStrikeAuth()
    return _sandstrike_auth


def verify_user_subscription(api_key: str = None) -> Tuple[bool, Optional[UserSubscription]]:
    """
    Convenience function to verify user subscription.
    
    Args:
        api_key: The API key to verify (optional, uses environment variable if not provided)
        
    Returns:
        Tuple of (is_valid, subscription_info)
    """
    auth = get_sandstrike_auth()
    return auth.verify_api_key(api_key)


def is_paid_user(api_key: str = None) -> bool:
    """
    Convenience function to check if user is paid.
    
    Args:
        api_key: The API key to check (optional, uses environment variable if not provided)
        
    Returns:
        True if user has paid subscription, False otherwise
    """
    auth = get_sandstrike_auth()
    return auth.is_paid_user(api_key)
