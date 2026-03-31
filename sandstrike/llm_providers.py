"""
Avenlis LLM Provider System
Comprehensive support for Cloud APIs, Local Models, and Custom Integrations
"""

import asyncio
import aiohttp
import json
import os
from typing import Dict, List, Optional, Any, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ProviderType(Enum):
    CLOUD_API = "cloud_api"
    LOCAL_MODEL = "local_model"
    CUSTOM_INTEGRATION = "custom_integration"

@dataclass
class LLMResponse:
    """Standardized response from any LLM provider"""
    content: str
    model: str
    provider: str
    tokens_used: Optional[int] = None
    response_time: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@dataclass
class ProviderConfig:
    """Configuration for LLM providers"""
    name: str
    provider_type: ProviderType
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    max_tokens: int = 1000
    temperature: float = 0.7
    timeout: int = 30
    custom_headers: Optional[Dict[str, str]] = None
    custom_params: Optional[Dict[str, Any]] = None

class BaseLLMProvider(ABC):
    """Base class for all LLM providers"""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.session = None
    
    @abstractmethod
    async def generate_response(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response from the LLM"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is healthy and accessible"""
        pass
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

class CloudAPIProvider(BaseLLMProvider):
    """Provider for cloud-based LLM APIs"""
    
    async def generate_response(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response from cloud API"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config.api_key}"
            }
            
            if self.config.custom_headers:
                headers.update(self.config.custom_headers)
            
            payload = {
                "model": self.config.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature)
            }
            
            if self.config.custom_params:
                payload.update(self.config.custom_params)
            
            async with self.session.post(
                f"{self.config.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    response_time = asyncio.get_event_loop().time() - start_time
                    
                    return LLMResponse(
                        content=data["choices"][0]["message"]["content"],
                        model=self.config.model_name,
                        provider=self.config.name,
                        tokens_used=data.get("usage", {}).get("total_tokens"),
                        response_time=response_time,
                        metadata=data
                    )
                else:
                    error_text = await response.text()
                    return LLMResponse(
                        content="",
                        model=self.config.model_name,
                        provider=self.config.name,
                        error=f"API Error {response.status}: {error_text}"
                    )
        
        except Exception as e:
            return LLMResponse(
                content="",
                model=self.config.model_name,
                provider=self.config.name,
                error=f"Request failed: {str(e)}"
            )
    
    async def health_check(self) -> bool:
        """Check if cloud API is accessible"""
        try:
            headers = {"Authorization": f"Bearer {self.config.api_key}"}
            async with self.session.get(
                f"{self.config.base_url}/models",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                return response.status == 200
        except:
            return False

class OllamaProvider(BaseLLMProvider):
    """Provider for Ollama local models"""
    
    async def generate_response(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response from Ollama"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            payload = {
                "model": self.config.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", self.config.temperature),
                    "num_predict": kwargs.get("max_tokens", self.config.max_tokens)
                }
            }
            
            async with self.session.post(
                f"{self.config.base_url}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    response_time = asyncio.get_event_loop().time() - start_time
                    
                    return LLMResponse(
                        content=data["response"],
                        model=self.config.model_name,
                        provider="Ollama",
                        tokens_used=data.get("eval_count"),
                        response_time=response_time,
                        metadata=data
                    )
                else:
                    error_text = await response.text()
                    return LLMResponse(
                        content="",
                        model=self.config.model_name,
                        provider="Ollama",
                        error=f"Ollama Error {response.status}: {error_text}"
                    )
        
        except Exception as e:
            return LLMResponse(
                content="",
                model=self.config.model_name,
                provider="Ollama",
                error=f"Ollama request failed: {str(e)}"
            )
    
    async def health_check(self) -> bool:
        """Check if Ollama is running"""
        try:
            async with self.session.get(
                f"{self.config.base_url}/api/tags",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                return response.status == 200
        except:
            return False

class HuggingFaceProvider(BaseLLMProvider):
    """Provider for HuggingFace models"""
    
    async def generate_response(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response from HuggingFace"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            headers = {"Content-Type": "application/json"}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                    "temperature": kwargs.get("temperature", self.config.temperature),
                    "return_full_text": False
                }
            }
            
            async with self.session.post(
                f"{self.config.base_url}/models/{self.config.model_name}",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    response_time = asyncio.get_event_loop().time() - start_time
                    
                    content = data[0]["generated_text"] if isinstance(data, list) else data.get("generated_text", "")
                    
                    return LLMResponse(
                        content=content,
                        model=self.config.model_name,
                        provider="HuggingFace",
                        response_time=response_time,
                        metadata=data
                    )
                else:
                    error_text = await response.text()
                    return LLMResponse(
                        content="",
                        model=self.config.model_name,
                        provider="HuggingFace",
                        error=f"HuggingFace Error {response.status}: {error_text}"
                    )
        
        except Exception as e:
            return LLMResponse(
                content="",
                model=self.config.model_name,
                provider="HuggingFace",
                error=f"HuggingFace request failed: {str(e)}"
            )
    
    async def health_check(self) -> bool:
        """Check if HuggingFace API is accessible"""
        try:
            headers = {}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            
            async with self.session.get(
                f"{self.config.base_url}/models/{self.config.model_name}",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                return response.status in [200, 404]  # 404 means model exists but not accessible
        except:
            return False

class CustomAPIProvider(BaseLLMProvider):
    """Provider for custom API integrations"""
    
    async def generate_response(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response from custom API"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            headers = {"Content-Type": "application/json"}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            
            if self.config.custom_headers:
                headers.update(self.config.custom_headers)
            
            payload = {
                "prompt": prompt,
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature)
            }
            
            if self.config.custom_params:
                payload.update(self.config.custom_params)
            
            async with self.session.post(
                self.config.base_url,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    response_time = asyncio.get_event_loop().time() - start_time
                    
                    # Extract content based on common response formats
                    content = self._extract_content(data)
                    
                    return LLMResponse(
                        content=content,
                        model=self.config.model_name or "custom",
                        provider=self.config.name,
                        response_time=response_time,
                        metadata=data
                    )
                else:
                    error_text = await response.text()
                    return LLMResponse(
                        content="",
                        model=self.config.model_name or "custom",
                        provider=self.config.name,
                        error=f"Custom API Error {response.status}: {error_text}"
                    )
        
        except Exception as e:
            return LLMResponse(
                content="",
                model=self.config.model_name or "custom",
                provider=self.config.name,
                error=f"Custom API request failed: {str(e)}"
            )
    
    def _extract_content(self, data: Dict[str, Any]) -> str:
        """Extract content from various response formats"""
        # Try common response formats
        for key in ["response", "content", "text", "output", "result", "message"]:
            if key in data:
                if isinstance(data[key], str):
                    return data[key]
                elif isinstance(data[key], dict) and "content" in data[key]:
                    return data[key]["content"]
        
        # If no standard format found, return the whole response as string
        return str(data)
    
    async def health_check(self) -> bool:
        """Check if custom API is accessible"""
        try:
            headers = {}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            
            async with self.session.get(
                self.config.base_url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                return response.status in [200, 404, 405]  # 405 means endpoint exists but method not allowed
        except:
            return False

class LLMProviderFactory:
    """Factory for creating LLM providers"""
    
    @staticmethod
    def create_provider(config: ProviderConfig) -> BaseLLMProvider:
        """Create appropriate provider based on configuration"""
        
        if config.provider_type == ProviderType.CLOUD_API:
            if "ollama" in config.base_url.lower():
                return OllamaProvider(config)
            elif "huggingface" in config.base_url.lower() or "hf.co" in config.base_url.lower():
                return HuggingFaceProvider(config)
            else:
                return CloudAPIProvider(config)
        
        elif config.provider_type == ProviderType.LOCAL_MODEL:
            if "ollama" in config.name.lower():
                return OllamaProvider(config)
            else:
                return CustomAPIProvider(config)
        
        elif config.provider_type == ProviderType.CUSTOM_INTEGRATION:
            return CustomAPIProvider(config)
        
        else:
            raise ValueError(f"Unsupported provider type: {config.provider_type}")

class LLMProviderManager:
    """Manager for multiple LLM providers"""
    
    def __init__(self):
        self.providers: Dict[str, BaseLLMProvider] = {}
        self.configs: Dict[str, ProviderConfig] = {}
    
    def add_provider(self, name: str, config: ProviderConfig):
        """Add a new provider"""
        self.configs[name] = config
        self.providers[name] = LLMProviderFactory.create_provider(config)
    
    async def test_provider(self, name: str) -> bool:
        """Test if a provider is working"""
        if name not in self.providers:
            return False
        
        provider = self.providers[name]
        async with provider:
            return await provider.health_check()
    
    async def generate_response(self, provider_name: str, prompt: str, **kwargs) -> LLMResponse:
        """Generate response using specified provider"""
        if provider_name not in self.providers:
            return LLMResponse(
                content="",
                model="unknown",
                provider=provider_name,
                error=f"Provider '{provider_name}' not found"
            )
        
        provider = self.providers[provider_name]
        async with provider:
            return await provider.generate_response(prompt, **kwargs)
    
    def list_providers(self) -> List[str]:
        """List all available providers"""
        return list(self.providers.keys())
    
    def get_provider_config(self, name: str) -> Optional[ProviderConfig]:
        """Get configuration for a provider"""
        return self.configs.get(name)

# Predefined provider configurations
PREDEFINED_PROVIDERS = {
    "anthropic": ProviderConfig(
        name="Anthropic",
        provider_type=ProviderType.CLOUD_API,
        base_url="https://api.anthropic.com/v1",
        model_name="claude-3-sonnet-20240229"
    ),
    "google": ProviderConfig(
        name="Google AI",
        provider_type=ProviderType.CLOUD_API,
        base_url="https://generativelanguage.googleapis.com/v1beta",
        model_name="gemini-pro"
    ),
    "huggingface": ProviderConfig(
        name="HuggingFace",
        provider_type=ProviderType.CLOUD_API,
        base_url="https://api-inference.huggingface.co",
        model_name="microsoft/DialoGPT-medium"
    ),
    "ollama": ProviderConfig(
        name="Ollama",
        provider_type=ProviderType.LOCAL_MODEL,
        base_url="http://localhost:11434",
        model_name=""
    )
}

