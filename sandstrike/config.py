"""
Enhanced configuration management for Avenlis.

This module provides hybrid storage support with YAML/JSON for team sharing
and SQLite for local rapid scans.
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, List, Optional, Union, Literal, Any
from enum import Enum
from pydantic import BaseModel, Field
from dataclasses import dataclass

from sandstrike.exceptions import AvenlisError
from sandstrike.utils.logging import get_logger

logger = get_logger(__name__)

class StorageBackend(str, Enum):
    """Storage backend options"""
    YAML = "yaml"
    JSON = "json"
    DATABASE = "database"
    AUTO = "auto"

class ScanType(str, Enum):
    """Scan type options"""
    RAPID = "rapid"      # Local DB storage
    FULL = "full"        # YAML/JSON storage for sharing

@dataclass
class StorageConfig:
    """Storage configuration settings"""
    default_backend: StorageBackend = StorageBackend.JSON
    enable_database: bool = True
    database_path: Optional[str] = None
    yaml_indent: int = 2
    auto_backup: bool = True
    
class AvenlisConfig:
    """Enhanced Avenlis configuration with hybrid storage support"""
    
    def __init__(self):
        self.base_dir = Path.home() / ".avenlis"
        self.config_dir = self.base_dir / "config"
        self.sessions_dir = self.base_dir / "redteam" / "sessions"
        self.collections_dir = self.base_dir / "collections"
        self.templates_dir = self.base_dir / "templates"
        self.database_path = self.base_dir / "avenlis.db"
        
        # Team-shareable config directories (can be symlinked to project)
        self.shared_dir = self.base_dir / "shared"
        self.shared_collections = self.shared_dir / "collections"
        self.shared_templates = self.shared_dir / "templates"
        
        # Create directories
        for dir_path in [self.config_dir, self.sessions_dir, self.collections_dir, 
                        self.templates_dir, self.shared_dir, self.shared_collections, 
                        self.shared_templates]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        self.storage_config = StorageConfig()
        
        # Initialize Ollama and redteam config defaults
        self.ollama_config = {}
        self.redteam_config = {}
        self.llm_providers = {}
        
        self._load_config()
        self._load_avenlis_config()
    
    def _load_config(self):
        """Load configuration from file"""
        config_file = self.config_dir / "config.yaml"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f) or {}
                
                storage_data = config_data.get('storage', {})
                self.storage_config = StorageConfig(
                    default_backend=StorageBackend(storage_data.get('default_backend', 'json')),
                    enable_database=storage_data.get('enable_database', True),
                    database_path=storage_data.get('database_path'),
                    yaml_indent=storage_data.get('yaml_indent', 2),
                    auto_backup=storage_data.get('auto_backup', True)
                )
            except Exception as e:
                logger.warning(f"Failed to load config: {e}, using defaults")
    
    def save_config(self):
        """Save configuration to file"""
        config_data = {
            'storage': {
                'default_backend': self.storage_config.default_backend.value,
                'enable_database': self.storage_config.enable_database,
                'database_path': self.storage_config.database_path,
                'yaml_indent': self.storage_config.yaml_indent,
                'auto_backup': self.storage_config.auto_backup
            }
        }
        
        config_file = self.config_dir / "config.yaml"
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.safe_dump(config_data, f, default_flow_style=False, 
                              indent=self.storage_config.yaml_indent)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise AvenlisError(f"Configuration save failed: {e}")
    
    def get_storage_path(self, storage_type: str, shared: bool = False) -> Path:
        """Get storage path for different data types"""
        if shared:
            base = self.shared_dir
        else:
            base = self.base_dir
            
        path_map = {
            'sessions': self.sessions_dir,
            'collections': self.shared_collections if shared else self.collections_dir,
            'templates': self.shared_templates if shared else self.templates_dir,
            'config': self.config_dir
        }
        
        return path_map.get(storage_type, base)
    
    def get_version(self) -> str:
        """Get the current version of Avenlis"""
        from sandstrike import __version__
        return __version__
    
    def _load_avenlis_config(self):
        """Load configuration from avenlis_config.yaml in project root or working directory"""
        # Look for config file in current working directory first, then project root
        config_paths = [
            Path.cwd() / "avenlis_config.yaml",
            Path(__file__).parent.parent / "avenlis_config.yaml",
            self.config_dir / "avenlis_config.yaml"
        ]
        
        for config_path in config_paths:
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config_data = yaml.safe_load(f) or {}
                    
                    # Load Ollama configuration
                    self.ollama_config = config_data.get('ollama', {})
                    
                    # Load redteam configuration
                    self.redteam_config = config_data.get('redteam_config', {})
                    
                    # Load LLM providers configuration
                    self.llm_providers = config_data.get('llm_providers', {})
                    
                    # Store redteam targets for easy access
                    self.redteam_targets = config_data.get('redteam', {}).get('targets', [])
                    return
                    
                except Exception as e:
                    logger.warning(f"Failed to load config from {config_path}: {e}")
                    continue
        
        logger.info("No avenlis_config.yaml found, using environment variables as fallback")
    
    def get_ollama_endpoint(self) -> str:
        """Get Ollama endpoint URL"""
        if self.ollama_config:
            return self.ollama_config.get('endpoint', 'http://localhost:11434')
        # Fallback to environment variable
        return os.getenv('AVENLIS_OLLAMA_ENDPOINT', 'http://localhost:11434')
    
    def get_ollama_model(self) -> str:
        """Get default Ollama model"""
        if self.ollama_config:
            return self.ollama_config.get('model', '')
        # Fallback to environment variable
        return os.getenv('AVENLIS_OLLAMA_MODEL', '')
    
    def get_ollama_generate_url(self) -> str:
        """Get Ollama generate API URL"""
        if self.ollama_config and 'api' in self.ollama_config:
            return self.ollama_config['api'].get('generate_endpoint', 
                                               f"{self.get_ollama_endpoint()}/api/generate")
        return f"{self.get_ollama_endpoint()}/api/generate"
    
    def get_default_redteam_target(self) -> Optional[str]:
        """Get default redteam target from configuration"""
        if self.redteam_targets:
            # Return the first target as default
            first_target = self.redteam_targets[0]
            return first_target.get('target', first_target.get('name'))
        
        # Fallback to environment variable
        env_target = os.getenv('AVENLIS_REDTEAM_TARGET')
        if env_target:
            return env_target
        
        # Fallback to constructing from Ollama config
        ollama_endpoint = self.get_ollama_endpoint()
        ollama_model = self.get_ollama_model()
        return f"ollama://{ollama_model}@{ollama_endpoint}"
    
    def get_redteam_targets(self) -> List[Dict[str, Any]]:
        """Get all available redteam targets"""
        return self.redteam_targets or []
    
    def get_redteam_config(self) -> Dict[str, Any]:
        """Get redteam configuration settings"""
        return self.redteam_config or {
            'max_concurrent': 5,
            'retry_count': 3
        }
    
    def get_llm_provider_config(self, provider_name: str) -> Dict[str, Any]:
        """Get configuration for a specific LLM provider"""
        return self.llm_providers.get(provider_name, {})
    
    def get_endpoint_config(self, target_name: str) -> Optional[dict]:
        """Return the endpoint config dictionary for a given target name"""
        if self.redteam_targets:
            for target in self.redteam_targets:
                if target.get("type") == "http" and target.get("target") == target_name:
                    method = target.get("method", "POST").upper()
                    url = target.get("target")
                    
                    # default headers/params/body from config
                    headers = target.get("headers", {})
                    params = target.get("params", {})
                    body = target.get("body", {})

                    return method, url, headers, params, body
        
        return None
    
    def get_file_config(self, target_name: str) -> Optional[dict]:
        """Return the endpoint config dictionary for a given target name"""
        target_name = target_name.removeprefix("file://")
        if self.redteam_targets:
            for target in self.redteam_targets:
                if target.get("type") == "file" and target.get("target") == target_name:
                    path = target.get("target", "").upper()

                    return path
        
        return None


# Global configuration instance
config = AvenlisConfig()
