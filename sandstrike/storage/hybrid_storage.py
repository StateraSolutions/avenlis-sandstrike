"""
Hybrid storage system for Avenlis.

This module provides a unified interface for storing data in different backends:
- YAML/JSON files for team-shareable configurations
- SQLite database for local rapid scans
- Automatic backend selection based on content type and user preferences
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Literal
from datetime import datetime
from enum import Enum

from sandstrike.config import config, StorageBackend, ScanType
from sandstrike.main_storage import AvenlisStorage
from sandstrike.schemas.yaml_schemas import (
    CollectionSchema, SessionConfigSchema, SessionResultSchema, 
    AdversarialPromptSchema
)
from sandstrike.exceptions import AvenlisError
from sandstrike.utils.logging import get_logger

logger = get_logger(__name__)


class ContentType(str, Enum):
    """Content types for storage operations"""
    COLLECTION = "collection"
    SESSION_CONFIG = "session_config"
    SESSION_RESULT = "session_result"
    ADVERSARIAL_PROMPT = "adversarial_prompt"
    RAPID_SCAN = "rapid_scan"
    DYNAMIC_VARIABLES = "dynamic_variables"


class HybridStorage:
    """Unified storage interface supporting multiple backends"""
    
    def __init__(self):
        self.main_storage = AvenlisStorage()
    
    def save_content(
        self, 
        content_type: ContentType,
        content_id: str,
        data: Dict[str, Any],
        backend: StorageBackend = StorageBackend.AUTO,
        shared: bool = False,
        scan_type: Optional[ScanType] = None
    ) -> str:
        """
        Save content using the appropriate backend
        
        Args:
            content_type: Type of content being saved
            content_id: Unique identifier for the content
            data: Content data to save
            backend: Storage backend to use (AUTO selects automatically)
            shared: Whether to store in shared location for team access
            scan_type: Scan type for automatic backend selection
            
        Returns:
            Path or identifier where content was saved
        """
        # Determine backend automatically if needed
        if backend == StorageBackend.AUTO:
            backend = self._select_backend(content_type, scan_type)
        
        # Route to appropriate storage method
        if backend == StorageBackend.DATABASE:
            return self._save_to_database(content_type, content_id, data)
        elif backend in [StorageBackend.YAML, StorageBackend.JSON]:
            return self._save_to_file(content_type, content_id, data, backend, shared)
        else:
            raise AvenlisError(f"Unsupported storage backend: {backend}")
    
    def load_content(
        self, 
        content_type: ContentType,
        content_id: str,
        backend: StorageBackend = StorageBackend.AUTO,
        shared: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Load content from storage
        
        Args:
            content_type: Type of content to load
            content_id: Content identifier
            backend: Storage backend to check
            shared: Whether to check shared location
            
        Returns:
            Content data or None if not found
        """
        if backend == StorageBackend.DATABASE:
            return self._load_from_database(content_type, content_id)
        elif backend in [StorageBackend.YAML, StorageBackend.JSON]:
            return self._load_from_file(content_type, content_id, backend, shared)
        elif backend == StorageBackend.AUTO:
            # Try database first for rapid scans, then files
            if content_type == ContentType.RAPID_SCAN:
                result = self._load_from_database(content_type, content_id)
                if result:
                    return result
            
            # Try both YAML and JSON files
            for file_backend in [StorageBackend.YAML, StorageBackend.JSON]:
                result = self._load_from_file(content_type, content_id, file_backend, shared)
                if result:
                    return result
        
        return None
    
    def list_content(
        self, 
        content_type: ContentType,
        backend: StorageBackend = StorageBackend.AUTO,
        shared: bool = False,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        List content of a specific type
        
        Args:
            content_type: Type of content to list
            backend: Storage backend to check
            shared: Whether to check shared location
            limit: Maximum number of items to return
            
        Returns:
            List of content items
        """
        if backend == StorageBackend.DATABASE:
            return self._list_from_database(content_type, limit)
        elif backend in [StorageBackend.YAML, StorageBackend.JSON]:
            return self._list_from_files(content_type, backend, shared, limit)
        elif backend == StorageBackend.AUTO:
            # Combine results from multiple backends
            results = []
            
            # Add database results for rapid scans
            if content_type == ContentType.RAPID_SCAN:
                results.extend(self._list_from_database(content_type, limit))
            
            # Add file-based results
            for file_backend in [StorageBackend.YAML, StorageBackend.JSON]:
                results.extend(self._list_from_files(content_type, file_backend, shared, limit))
            
            # Sort by creation date and apply limit
            results.sort(key=lambda x: x.get('created_at', 0), reverse=True)
            return results[:limit] if limit else results
        
        return []
    
    def delete_content(
        self, 
        content_type: ContentType,
        content_id: str,
        backend: StorageBackend = StorageBackend.AUTO
    ) -> bool:
        """Delete content from storage"""
        if backend == StorageBackend.DATABASE:
            return self._delete_from_database(content_type, content_id)
        elif backend in [StorageBackend.YAML, StorageBackend.JSON]:
            return self._delete_from_file(content_type, content_id, backend)
        elif backend == StorageBackend.AUTO:
            # Try all backends
            success = False
            success |= self._delete_from_database(content_type, content_id)
            for file_backend in [StorageBackend.YAML, StorageBackend.JSON]:
                success |= self._delete_from_file(content_type, content_id, file_backend)
            return success
        
        return False
    
    def _select_backend(self, content_type: ContentType, scan_type: Optional[ScanType]) -> StorageBackend:
        """Select appropriate backend based on content type and scan type"""
        
        # Rapid scans always go to database
        if content_type == ContentType.RAPID_SCAN or scan_type == ScanType.RAPID:
            return StorageBackend.DATABASE
        
        # Full scan results go to files for sharing
        if scan_type == ScanType.FULL:
            return config.storage_config.default_backend
        
        # Default based on content type
        content_backend_map = {
            ContentType.COLLECTION: config.storage_config.default_backend,
            ContentType.SESSION_CONFIG: config.storage_config.default_backend,
            ContentType.SESSION_RESULT: config.storage_config.default_backend,
            ContentType.ADVERSARIAL_PROMPT: config.storage_config.default_backend,
        }
        
        return content_backend_map.get(content_type, StorageBackend.JSON)
    
    def _save_to_database(self, content_type: ContentType, content_id: str, data: Dict[str, Any]) -> str:
        """Save content to database"""
        if content_type == ContentType.RAPID_SCAN:
            return self.rapid_scan_manager.create_rapid_scan(
                name=data.get('name', 'Unnamed Scan'),
                target=data.get('target', ''),
                scan_config=data.get('config', {})
            )
        else:
            raise AvenlisError(f"Database storage not supported for {content_type}")
    
    def _load_from_database(self, content_type: ContentType, content_id: str) -> Optional[Dict[str, Any]]:
        """Load content from database"""
        if content_type == ContentType.RAPID_SCAN:
            return self.rapid_scan_manager.get_rapid_scan(content_id)
        return None
    
    def _list_from_database(self, content_type: ContentType, limit: Optional[int]) -> List[Dict[str, Any]]:
        """List content from database"""
        if content_type == ContentType.RAPID_SCAN:
            return self.rapid_scan_manager.list_rapid_scans(limit=limit or 50)
        return []
    
    def _delete_from_database(self, content_type: ContentType, content_id: str) -> bool:
        """Delete content from database"""
        if content_type == ContentType.RAPID_SCAN:
            return self.rapid_scan_manager.delete_rapid_scan(content_id)
        return False
    
    def _save_to_file(
        self, 
        content_type: ContentType, 
        content_id: str, 
        data: Dict[str, Any], 
        backend: StorageBackend,
        shared: bool
    ) -> str:
        """Save content to file"""
        
        # Get storage path
        storage_type = self._content_type_to_storage_type(content_type)
        storage_path = config.get_storage_path(storage_type, shared)
        
        # Determine file extension
        extension = 'yaml' if backend == StorageBackend.YAML else 'json'
        file_path = storage_path / f"{content_id}.{extension}"
        
        try:
            # Validate data against schema if available
            validated_data = self._validate_content(content_type, data)
            
            # Save file
            with open(file_path, 'w', encoding='utf-8') as f:
                if backend == StorageBackend.YAML:
                    yaml.safe_dump(validated_data, f, default_flow_style=False, 
                                  indent=config.storage_config.yaml_indent)
                else:
                    json.dump(validated_data, f, indent=2, ensure_ascii=False, default=str)
            
            # Update collection cache if needed
            if content_type == ContentType.COLLECTION:
                self._update_collection_cache(content_id, data, str(file_path))
            
            logger.info(f"Saved {content_type} to {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to save {content_type} to file: {e}")
            raise AvenlisError(f"File save failed: {e}")
    
    def _load_from_file(
        self, 
        content_type: ContentType, 
        content_id: str, 
        backend: StorageBackend,
        shared: bool
    ) -> Optional[Dict[str, Any]]:
        """Load content from file"""
        
        storage_type = self._content_type_to_storage_type(content_type)
        storage_path = config.get_storage_path(storage_type, shared)
        
        extension = 'yaml' if backend == StorageBackend.YAML else 'json'
        file_path = storage_path / f"{content_id}.{extension}"
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if backend == StorageBackend.YAML:
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to load {content_type} from file: {e}")
            return None
    
    def _list_from_files(
        self, 
        content_type: ContentType, 
        backend: StorageBackend,
        shared: bool, 
        limit: Optional[int]
    ) -> List[Dict[str, Any]]:
        """List content from files"""
        
        storage_type = self._content_type_to_storage_type(content_type)
        storage_path = config.get_storage_path(storage_type, shared)
        
        extension = 'yaml' if backend == StorageBackend.YAML else 'json'
        pattern = f"*.{extension}"
        
        files = list(storage_path.glob(pattern))
        files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        
        if limit:
            files = files[:limit]
        
        results = []
        for file_path in files:
            content_id = file_path.stem
            data = self._load_from_file(content_type, content_id, backend, shared)
            if data:
                data['_file_path'] = str(file_path)
                data['_content_id'] = content_id
                results.append(data)
        
        return results
    
    def _delete_from_file(self, content_type: ContentType, content_id: str, backend: StorageBackend) -> bool:
        """Delete content file"""
        try:
            for shared in [False, True]:
                storage_type = self._content_type_to_storage_type(content_type)
                storage_path = config.get_storage_path(storage_type, shared)
                
                extension = 'yaml' if backend == StorageBackend.YAML else 'json'
                file_path = storage_path / f"{content_id}.{extension}"
                
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"Deleted {content_type} file: {file_path}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete {content_type} file: {e}")
            return False
    
    def _content_type_to_storage_type(self, content_type: ContentType) -> str:
        """Map content type to storage directory type"""
        mapping = {
            ContentType.COLLECTION: 'collections',
            ContentType.SESSION_CONFIG: 'sessions',
            ContentType.SESSION_RESULT: 'sessions',
            ContentType.ADVERSARIAL_PROMPT: 'templates',
        }
        return mapping.get(content_type, 'config')
    
    def _validate_content(self, content_type: ContentType, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate content against schemas"""
        try:
            if content_type == ContentType.COLLECTION:
                schema = CollectionSchema(**data)
                return schema.dict()
            elif content_type == ContentType.SESSION_CONFIG:
                schema = SessionConfigSchema(**data)
                return schema.dict()
            elif content_type == ContentType.SESSION_RESULT:
                schema = SessionResultSchema(**data)
                return schema.dict()
            elif content_type == ContentType.ADVERSARIAL_PROMPT:
                schema = AdversarialPromptSchema(**data)
                return schema.dict()
            else:
                # Return data as-is if no schema available
                return data
        except Exception as e:
            logger.warning(f"Schema validation failed for {content_type}: {e}")
            return data  # Return unvalidated data
    
    def _update_collection_cache(self, collection_id: str, data: Dict[str, Any], file_path: str):
        """Update collection cache in database"""
        prompt_count = len(data.get('prompts', []))
        self.collection_cache.update_collection_cache(
            collection_id=collection_id,
            name=data.get('name', 'Unknown'),
            file_path=file_path,
            prompt_count=prompt_count,
            metadata=data.get('settings', {})
        )
    
    def export_to_yaml(self, content_type: ContentType, content_id: str, output_path: str) -> bool:
        """Export any content to YAML format"""
        data = self.load_content(content_type, content_id)
        if not data:
            return False
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(data, f, default_flow_style=False, 
                              indent=config.storage_config.yaml_indent)
            return True
        except Exception as e:
            logger.error(f"Failed to export to YAML: {e}")
            return False
    
    def import_from_yaml(self, content_type: ContentType, yaml_path: str) -> Optional[str]:
        """Import content from YAML file"""
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            content_id = data.get('id') or Path(yaml_path).stem
            saved_path = self.save_content(
                content_type=content_type,
                content_id=content_id,
                data=data,
                backend=StorageBackend.YAML
            )
            return saved_path
        except Exception as e:
            logger.error(f"Failed to import from YAML: {e}")
            return None
    
    # Dynamic Variables Methods
    def get_dynamic_variables(self, source: str = 'all') -> Dict[str, Any]:
        """Get dynamic variables from storage"""
        try:
            if source == 'all':
                # Try to load from file first, then local
                file_vars = self._load_dynamic_variables_from_file()
                local_vars = self._load_dynamic_variables_from_local()
                
                # Merge variables (local takes precedence)
                merged_vars = file_vars.copy() if file_vars else {}
                if local_vars:
                    if 'variables' not in merged_vars:
                        merged_vars['variables'] = {}
                    for category, vars_dict in local_vars.get('variables', {}).items():
                        if category not in merged_vars['variables']:
                            merged_vars['variables'][category] = {}
                        merged_vars['variables'][category].update(vars_dict)
                
                return merged_vars
            elif source == 'file':
                return self._load_dynamic_variables_from_file()
            elif source == 'local':
                return self._load_dynamic_variables_from_local()
            else:
                return {}
        except Exception as e:
            logger.error(f"Error getting dynamic variables: {e}")
            return {}
    
    def set_dynamic_variable(self, category: str, name: str, value: str, source: str = 'local', overwrite: bool = True) -> bool:
        """Set a dynamic variable value
        
        Args:
            category: Variable category
            name: Variable name
            value: Variable value
            source: 'local' for SQLite database, 'file' for YAML file. Default is 'local'
            overwrite: Whether to overwrite existing variable
        """
        try:
            # Normalize source to lowercase and validate
            source = source.lower() if source else 'local'
            
            if source not in ['local', 'file']:
                logger.error(f"Invalid source '{source}'. Must be 'local' or 'file'")
                return False
            
            logger.debug(f"Setting dynamic variable {category}.{name} with source='{source}'")
            
            if source == 'file':
                logger.debug(f"Calling _save_dynamic_variable_to_file for {category}.{name}")
                return self._save_dynamic_variable_to_file(category, name, value, overwrite)
            elif source == 'local':
                logger.debug(f"Calling _save_dynamic_variable_to_local for {category}.{name}")
                result = self._save_dynamic_variable_to_local(category, name, value, overwrite)
                if not result:
                    logger.error(f"Failed to save variable {category}.{name} to SQLite database")
                return result
            else:
                logger.error(f"Invalid source '{source}'. Must be 'local' or 'file'")
                return False
        except Exception as e:
            logger.error(f"Error setting dynamic variable: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def get_dynamic_variable(self, category: str, name: str, source: str = 'all') -> Optional[str]:
        """Get a specific dynamic variable value"""
        try:
            if source == 'all':
                # Check local first, then file
                local_value = self._get_dynamic_variable_from_local(category, name)
                if local_value:
                    return local_value
                return self._get_dynamic_variable_from_file(category, name)
            elif source == 'file':
                return self._get_dynamic_variable_from_file(category, name)
            elif source == 'local':
                return self._get_dynamic_variable_from_local(category, name)
            else:
                return None
        except Exception as e:
            logger.error(f"Error getting dynamic variable: {e}")
            return None
    
    def delete_dynamic_variable(self, category: str, name: str, source: str = 'local') -> bool:
        """Delete a dynamic variable"""
        try:
            if source == 'file':
                return self._delete_dynamic_variable_from_file(category, name)
            else:  # local
                return self._delete_dynamic_variable_from_local(category, name)
        except Exception as e:
            logger.error(f"Error deleting dynamic variable: {e}")
            return False
    
    def clear_dynamic_variables(self, source: str = 'local') -> bool:
        """Clear all dynamic variables"""
        try:
            if source == 'file':
                return self._clear_dynamic_variables_from_file()
            else:  # local
                return self._clear_dynamic_variables_from_local()
        except Exception as e:
            logger.error(f"Error clearing dynamic variables: {e}")
            return False
    
    def substitute_variables_in_prompt(self, prompt: str, source: str = 'all') -> str:
        """Substitute dynamic variables in a prompt template"""
        try:
            variables = self.get_dynamic_variables(source=source)
            
            if not variables or 'variables' not in variables:
                return prompt
            
            # Find all {variable} patterns
            import re
            pattern = r'\{([^}]+)\}'
            matches = re.findall(pattern, prompt)
            
            substituted_prompt = prompt
            
            for match in matches:
                # Try to find the variable in the variables structure
                value = self._find_variable_value(match, variables)
                if value:
                    substituted_prompt = substituted_prompt.replace(f'{{{match}}}', str(value))
                else:
                    # Use default or keep original
                    defaults = variables.get('substitution_rules', {}).get('defaults', {})
                    if match in defaults:
                        substituted_prompt = substituted_prompt.replace(f'{{{match}}}', str(defaults[match]))
                    else:
                        # Keep original if no default
                        logger.warning(f"No value found for variable: {match}")
            
            return substituted_prompt
        except Exception as e:
            logger.error(f"Error substituting variables in prompt: {e}")
            return prompt
    
    def _load_dynamic_variables_from_file(self) -> Dict[str, Any]:
        """Load dynamic variables from YAML file"""
        try:
            # First try user's custom file
            user_file_path = Path(config.base_dir) / "dynamic_variables.yaml"
            if user_file_path.exists():
                with open(user_file_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            
            # If not found, try the default package file
            package_file_path = Path(__file__).parent.parent / "data" / "dynamic_variables.yaml"
            if package_file_path.exists():
                with open(package_file_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            
            return {}
        except Exception as e:
            logger.error(f"Error loading dynamic variables from file: {e}")
            return {}
    
    def _load_dynamic_variables_from_local(self) -> Dict[str, Any]:
        """Load dynamic variables from local storage (SQLite)"""
        try:
            return self.main_storage.get_dynamic_variables()
        except Exception as e:
            logger.error(f"Error loading dynamic variables from local: {e}")
            return {}
    
    def _save_dynamic_variable_to_file(self, category: str, name: str, value: str, overwrite: bool = True) -> bool:
        """Save dynamic variable to project's data YAML file, preserving comments
        
        WARNING: This method should ONLY be called when source='file'. 
        It should NEVER be called when source='local'.
        """
        try:
            import re
            
            # Save to project's data directory (sandstrike/data/dynamic_variables.yaml)
            package_file_path = Path(__file__).parent.parent / "data" / "dynamic_variables.yaml"
            user_file_path = package_file_path
            
            # Ensure base directory exists (only for file source)
            user_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Read existing file lines to preserve comments
            lines = []
            if user_file_path.exists():
                with open(user_file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            else:
                # New file - create with header comments
                lines = [
                    "# Dynamic Variables Configuration\n",
                    "# This file stores template variable values that can be used in prompts with dynamic fields\n",
                    "# Variables are organized by category for better management\n",
                    "\n",
                    "variables:\n"
                ]
            
            # Parse existing data to check if variable exists
            data = {}
            if user_file_path.exists():
                with open(user_file_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f) or {}
            
            # Check if variable exists and overwrite is False
            if not overwrite and data.get('variables', {}).get(category, {}).get(name) is not None:
                return False
            
            # Find or create the category section
            category_found = False
            category_line_idx = -1
            in_variables_section = False
            variables_indent = 0
            category_indent = 0
            
            # First pass: find the variables section and category
            for i, line in enumerate(lines):
                stripped = line.lstrip()
                
                # Check if we're in variables section
                if stripped.startswith('variables:'):
                    in_variables_section = True
                    variables_indent = len(line) - len(stripped)
                    continue
                
                if not in_variables_section:
                    continue
                
                # Check for category
                current_indent = len(line) - len(stripped)
                if stripped.startswith(f'{category}:') and not stripped.startswith('#'):
                    category_found = True
                    category_indent = current_indent
                    category_line_idx = i
                    break
            
            # If category not found, add it
            if not category_found:
                # Find insertion point after variables: line
                insert_idx = len(lines)
                for i, line in enumerate(lines):
                    if line.strip().startswith('variables:'):
                        # Find the next non-empty, non-comment line or end of file
                        for j in range(i + 1, len(lines)):
                            stripped = lines[j].lstrip()
                            if stripped and not stripped.startswith('#'):
                                insert_idx = j
                                break
                        if insert_idx == len(lines):
                            insert_idx = i + 1
                        break
                
                # Add category with proper indentation
                indent = variables_indent + 2
                category_comments = {
                    'application': '  # Application-related variables',
                    'data': '  # Data-related variables',
                    'system': '  # System-related variables',
                    'context': '  # Additional context variables'
                }
                
                new_lines = lines[:insert_idx]
                if category in category_comments:
                    new_lines.append(category_comments[category] + '\n')
                new_lines.append(' ' * indent + f'{category}:\n')
                new_lines.append(' ' * (indent + 2) + f'{name}: "{value}"\n')
                new_lines.append('\n')  # Add blank line after first variable in new category
                new_lines.extend(lines[insert_idx:])
                lines = new_lines
                category_line_idx = insert_idx + (1 if category in category_comments else 0)
                category_indent = indent
                # Since we just added the variable in a new category, mark it as found and skip the search
                variable_found = True
                variable_line_idx = category_line_idx + 1  # The variable is right after the category line
                variable_indent = category_indent + 2
            else:
                # Category exists, need to find the variable
                variable_found = False
                variable_line_idx = -1
                variable_indent = category_indent + 2
                
                # Look for the variable in the category section
                for i in range(category_line_idx + 1, len(lines)):
                    line = lines[i]
                    stripped = line.lstrip()
                    
                    # Stop if we hit another category or top-level key
                    current_indent = len(line) - len(stripped)
                    if stripped and not stripped.startswith('#') and current_indent <= category_indent:
                        break
                    
                    # Check if this is our variable (match name: pattern)
                    match = re.match(rf'^\s*{re.escape(name)}\s*:', stripped)
                    if match:
                        variable_found = True
                        variable_line_idx = i
                        break
            
            # Update or insert the variable
            if variable_found:
                # Update existing variable line, preserving any inline comment
                line = lines[variable_line_idx]
                comment_match = re.search(r'\s+#.*$', line)
                comment = comment_match.group(0) if comment_match else ''
                
                # Preserve newline
                newline = '\n' if line.endswith('\n') else ''
                lines[variable_line_idx] = ' ' * variable_indent + f'{name}: "{value}"{comment}{newline}'
            else:
                # Insert new variable in the category
                # Find insertion point (after last variable in category or after category line)
                insert_idx = category_line_idx + 1
                last_variable_idx = -1
                
                for i in range(category_line_idx + 1, len(lines)):
                    line = lines[i]
                    stripped = line.lstrip()
                    current_indent = len(line) - len(stripped)
                    
                    # Stop if we hit another category or top-level key (same or less indent than category)
                    # This means we've left the current category
                    if stripped and not stripped.startswith('#') and current_indent <= category_indent:
                        # We've reached the next category
                        # If we found variables, insert after the last one; otherwise insert before this line
                        if last_variable_idx >= 0:
                            insert_idx = last_variable_idx + 1
                        else:
                            insert_idx = i
                        break
                    
                    # If we find a variable in this category (indent matches variable_indent), track it
                    if stripped and not stripped.startswith('#') and ':' in stripped and current_indent == variable_indent:
                        last_variable_idx = i
                        insert_idx = i + 1
                    # Comments and blank lines don't change the insertion point
                
                # If we didn't break (reached end of file), use the last known position
                lines.insert(insert_idx, ' ' * variable_indent + f'{name}: "{value}"\n')
            
            # Write back to file
            with open(user_file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            return True
        except Exception as e:
            logger.error(f"Error saving dynamic variable to file: {e}")
            return False
    
    def _save_dynamic_variable_to_local(self, category: str, name: str, value: str, overwrite: bool = True) -> bool:
        """Save dynamic variable to local storage (SQLite database only - NO YAML files)"""
        try:
            if not self.main_storage:
                logger.error("Main storage not initialized")
                return False
            result = self.main_storage.set_dynamic_variable(category, name, value, overwrite)
            if result:
                logger.debug(f"Successfully saved variable {category}.{name} to SQLite database")
            else:
                logger.warning(f"Failed to save variable {category}.{name} to SQLite database")
            return result
        except Exception as e:
            logger.error(f"Error saving dynamic variable to local: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def _get_dynamic_variable_from_file(self, category: str, name: str) -> Optional[str]:
        """Get dynamic variable from file"""
        try:
            variables = self._load_dynamic_variables_from_file()
            return variables.get('variables', {}).get(category, {}).get(name)
        except Exception as e:
            logger.error(f"Error getting dynamic variable from file: {e}")
            return None
    
    def _get_dynamic_variable_from_local(self, category: str, name: str) -> Optional[str]:
        """Get dynamic variable from local storage"""
        try:
            return self.main_storage.get_dynamic_variable(category, name)
        except Exception as e:
            logger.error(f"Error getting dynamic variable from local: {e}")
            return None
    
    def _delete_dynamic_variable_from_file(self, category: str, name: str) -> bool:
        """Delete dynamic variable from file"""
        try:
            # Use project's data directory file
            file_path = Path(__file__).parent.parent / "data" / "dynamic_variables.yaml"
            existing_data = self._load_dynamic_variables_from_file()
            
            if 'variables' in existing_data and category in existing_data['variables']:
                if name in existing_data['variables'][category]:
                    del existing_data['variables'][category][name]
                    
                    # Save back to file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        yaml.safe_dump(existing_data, f, default_flow_style=False, indent=2)
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error deleting dynamic variable from file: {e}")
            return False
    
    def _delete_dynamic_variable_from_local(self, category: str, name: str) -> bool:
        """Delete dynamic variable from local storage"""
        try:
            return self.main_storage.delete_dynamic_variable(category, name)
        except Exception as e:
            logger.error(f"Error deleting dynamic variable from local: {e}")
            return False
    
    def _clear_dynamic_variables_from_file(self) -> bool:
        """Clear all dynamic variables from file"""
        try:
            # Use project's data directory file
            file_path = Path(__file__).parent.parent / "data" / "dynamic_variables.yaml"
            if file_path.exists():
                file_path.unlink()
            return True
        except Exception as e:
            logger.error(f"Error clearing dynamic variables from file: {e}")
            return False
    
    def _clear_dynamic_variables_from_local(self) -> bool:
        """Clear all dynamic variables from local storage"""
        try:
            return self.main_storage.clear_dynamic_variables()
        except Exception as e:
            logger.error(f"Error clearing dynamic variables from local: {e}")
            return False
    
    def _find_variable_value(self, variable_name: str, variables: Dict[str, Any]) -> Optional[str]:
        """Find variable value in the variables structure"""
        try:
            # Handle nested variables like "application.default_app"
            if '.' in variable_name:
                parts = variable_name.split('.')
                current = variables.get('variables', {})
                for part in parts:
                    if isinstance(current, dict) and part in current:
                        current = current[part]
                    else:
                        return None
                return str(current) if current else None
            else:
                # Search through all categories for the variable
                for category, vars_dict in variables.get('variables', {}).items():
                    if variable_name in vars_dict:
                        return str(vars_dict[variable_name])
                
                # If not found, try to find a 'default' variable in the category
                if variable_name in variables.get('variables', {}):
                    category_vars = variables['variables'][variable_name]
                    if isinstance(category_vars, dict) and 'default' in category_vars:
                        return str(category_vars['default'])
                
                return None
        except Exception as e:
            logger.error(f"Error finding variable value: {e}")
            return None


# Global storage instance
storage = HybridStorage()
