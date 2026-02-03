"""
YAML file loader for Avenlis data files.

This module provides utilities to load adversarial prompts, collections,
attack types, and session configurations from YAML files.
"""

import yaml
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from sandstrike.config import AvenlisConfig
from sandstrike.exceptions import AvenlisError
from sandstrike.utils.logging import get_logger

logger = get_logger(__name__)


class YAMLLoader:
    """Loader for YAML-based data files"""
    
    def __init__(self, data_dir: Optional[Path] = None):
        self.config = AvenlisConfig()
        
        # Use provided data directory or default to avenlis/data
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            # Default to the new avenlis/data directory
            current_dir = Path(__file__).parent.parent
            self.data_dir = current_dir / 'data'
    
    def load_adversarial_prompts(self) -> List[Dict[str, Any]]:
        """Load adversarial prompts from all YAML files in the prompts folder"""
        prompts_dir = self.data_dir / 'prompts'
        
        if not prompts_dir.exists():
            logger.warning(f"prompts directory not found: {prompts_dir}")
            return []
            
        all_prompts = []
        
        # Load all YAML files in the prompts directory
        for yaml_file in prompts_dir.glob('*.yaml'):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                if not data or 'prompts' not in data:
                    logger.warning(f"Invalid prompts YAML structure in {yaml_file}")
                    continue
                
                prompts = data['prompts']
                if not isinstance(prompts, list):
                    logger.warning(f"prompts should be a list in {yaml_file}")
                    continue
                
                # Add source file information to each prompt
                for prompt in prompts:
                    prompt['source'] = 'file'
                    prompt['source_file'] = yaml_file.name
                    prompt['last_modified'] = self._get_file_modified_time(yaml_file)
                
                all_prompts.extend(prompts)
                
            except Exception as e:
                logger.error(f"Error loading prompts from {yaml_file}: {e}")
                continue
        
        return all_prompts
    
    def save_prompt_to_file(self, prompt_data: Dict[str, Any], filename: str = None) -> bool:
        """Save a prompt to a specific YAML file in the prompts directory"""
        prompts_dir = self.data_dir / 'prompts'
        prompts_dir.mkdir(exist_ok=True)
        
        # Use provided filename or default to adversarial_prompts.yaml
        if not filename:
            filename = 'adversarial_prompts.yaml'
        
        yaml_file = prompts_dir / filename
        
        try:
            # Load existing prompts from the file
            existing_prompts = []
            if yaml_file.exists():
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f) or {}
                    existing_prompts = data.get('prompts', [])
            
            # Add the new prompt
            existing_prompts.append(prompt_data)
            
            # Save back to file
            data = {'prompts': existing_prompts}
            with open(yaml_file, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
            logger.info(f"Saved prompt to {yaml_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving prompt to {yaml_file}: {e}")
            return False
    
    def get_available_prompt_files(self) -> List[str]:
        """Get list of available prompt files in the prompts directory"""
        prompts_dir = self.data_dir / 'prompts'
        
        if not prompts_dir.exists():
            return []
        
        return [f.name for f in prompts_dir.glob('*.yaml')]
    
    def load_collections(self) -> List[Dict[str, Any]]:
        """Load collections from YAML files"""
        collections = []
        
        # Load main collection file
        collection_file = self.data_dir / 'collections.yaml'
        if collection_file.exists():
            try:
                with open(collection_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                if data and 'collections' in data:
                    # Handle collections root key structure (array format)
                    collections_list = data['collections']
                    if isinstance(collections_list, list):
                        # Array format: collections: [collection1, collection2, ...]
                        for collection_data in collections_list:
                            collection_data['source'] = 'file'
                            collection_data['source_file'] = str(collection_file)
                            collection_data['last_modified'] = self._get_file_modified_time(collection_file)
                            
                            # Count prompts
                            prompt_count = 0
                            if 'prompts' in collection_data:
                                prompt_count = len(collection_data['prompts'])
                            elif 'prompt_ids' in collection_data:
                                prompt_count = len(collection_data['prompt_ids'])
                            collection_data['prompt_count'] = prompt_count
                            
                            # Ensure date fields exist
                            from datetime import datetime
                            current_time = datetime.now().isoformat() + 'Z'
                            if 'date_created' not in collection_data:
                                collection_data['date_created'] = current_time
                            
                            collections.append(collection_data)
                    elif isinstance(collections_list, dict):
                        # Object format: collections: {id1: collection1, id2: collection2, ...}
                        for collection_id, collection_data in collections_list.items():
                            collection_data['id'] = collection_id
                            collection_data['source'] = 'file'
                            collection_data['source_file'] = str(collection_file)
                            collection_data['last_modified'] = self._get_file_modified_time(collection_file)
                            
                            # Count prompts
                            prompt_count = 0
                            if 'prompts' in collection_data:
                                prompt_count = len(collection_data['prompts'])
                            elif 'prompt_ids' in collection_data:
                                prompt_count = len(collection_data['prompt_ids'])
                            collection_data['prompt_count'] = prompt_count
                            
                            # Ensure date fields exist
                            from datetime import datetime
                            current_time = datetime.now().isoformat() + 'Z'
                            if 'date_created' not in collection_data:
                                collection_data['date_created'] = current_time
                            
                            collections.append(collection_data)
                else:
                    # Handle flat structure (single collection at root level)
                    collection = self._load_single_collection(collection_file)
                    if collection:
                        collections.append(collection)
            except Exception as e:
                logger.error(f"Failed to load collections from {collection_file}: {e}")
        
        # Look for additional collection files
        for yaml_file in self.data_dir.glob('*_collection.yaml'):
            collection = self._load_single_collection(yaml_file)
            if collection:
                collections.append(collection)
        
        return collections
    
    def _load_single_collection(self, yaml_file: Path) -> Optional[Dict[str, Any]]:
        """Load a single collection from YAML file"""
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data:
                logger.warning(f"Empty collection YAML file: {yaml_file}")
                return None
            
            # Add source information
            data['source'] = 'file'
            data['source_file'] = str(yaml_file)
            data['last_modified'] = self._get_file_modified_time(yaml_file)
            
            # Count prompts - handle both old 'prompts' format and new 'prompt_ids' format
            prompt_count = 0
            if 'prompts' in data:
                # Old format with embedded prompts
                prompt_count = len(data['prompts'])
            elif 'prompt_ids' in data:
                # New format with prompt IDs only - filter out blank/empty/null entries
                prompt_ids = data['prompt_ids']
                # Filter out blank, empty, None, or whitespace-only prompt IDs
                valid_prompt_ids = [pid for pid in prompt_ids if pid and str(pid).strip()]
                prompt_count = len(valid_prompt_ids)
            
            data['prompt_count'] = prompt_count
            
            # Ensure date fields exist with defaults if not specified
            from datetime import datetime
            current_time = datetime.now().isoformat() + 'Z'
            if 'date_created' not in data:
                data['date_created'] = current_time
            if 'date_updated' not in data:
                data['date_updated'] = current_time
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to load collection from {yaml_file}: {e}")
            return None
    
    def load_session_config(self, config_file: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Load session configuration from YAML file"""
        if config_file:
            yaml_file = Path(config_file)
        else:
            yaml_file = self.data_dir / 'session_config.yaml'
        
        if not yaml_file.exists():
            logger.warning(f"Session config YAML file not found: {yaml_file}")
            return None
            
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data:
                logger.warning(f"Empty session config YAML file: {yaml_file}")
                return None
            
            # Add source information
            data['source'] = 'file'
            data['source_file'] = str(yaml_file)
            data['last_modified'] = self._get_file_modified_time(yaml_file)
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to load session config from {yaml_file}: {e}")
            return None
    
    def load_scan_results(self) -> List[Dict[str, Any]]:
        """Load scan results from JSON files"""
        scan_results = []
        
        # Look for scan result and session JSON files
        patterns = ['*scan_results*.json', 'sessions*.json', '*sessions*.json']
        json_files = []
        for pattern in patterns:
            json_files.extend(self.data_dir.glob(pattern))
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Handle different JSON structures
                results_to_process = []
                
                if isinstance(data, list):
                    # Direct array of scan results
                    results_to_process = data
                elif isinstance(data, dict):
                    if 'scan_results' in data and isinstance(data['scan_results'], list):
                        # Nested structure: {"scan_results": [...]}
                        results_to_process = data['scan_results']
                    else:
                        # Single scan result object
                        results_to_process = [data]
                
                # Process each result
                for result in results_to_process:
                    if isinstance(result, dict):
                        result['source'] = 'file'
                        result['source_file'] = str(json_file)
                        result['last_modified'] = self._get_file_modified_time(json_file)
                        
                        # Ensure consistent field names for sessions table
                        if 'session_name' not in result and 'name' in result:
                            result['session_name'] = result['name']
                        
                        # Map session fields to expected format
                        if 'session_name' in result:
                            result['name'] = result['session_name']
                        if 'target' in result:
                            result['target_url'] = result['target']
                        # Use started_at as date if created_at is not available, otherwise use started_at
                        if 'started_at' in result:
                            result['date'] = result['started_at']
                        elif 'created_at' in result:
                            result['date'] = result['created_at']
                        
                        # Duration calculation removed - only track started_at
                        result['duration_seconds'] = 0
                        
                        # Calculate counts from results array instead of using static fields
                        results_array = result.get('results', [])
                        if results_array:
                            total_tests = len(results_array)
                            passed_count = len([r for r in results_array if r.get('status') == 'passed'])
                            failed_count = len([r for r in results_array if r.get('status') == 'failed'])
                            error_count = len([r for r in results_array if r.get('status') == 'error'])
                            
                            result['total_tests'] = total_tests
                            result['vulnerabilities_found'] = failed_count  # Failed tests = vulnerabilities
                            result['success_rate'] = (passed_count / total_tests * 100) if total_tests > 0 else 0
                        else:
                            result['total_tests'] = 0
                            result['vulnerabilities_found'] = 0
                            result['success_rate'] = 0
                        
                        # Extract model name from metadata if not at top level
                        if 'target_model' not in result and 'metadata' in result:
                            metadata = result.get('metadata', {})
                            if 'model_name' in metadata:
                                result['target_model'] = metadata['model_name']
                        
                        # Only add results that have valid names
                        if result.get('name') and result.get('session_name') and result['name'] != 'N/A':
                            scan_results.append(result)
                    
            except Exception as e:
                logger.error(f"Failed to load scan results from {json_file}: {e}")
        
        return scan_results
    
    def load_targets(self) -> List[Dict[str, Any]]:
        """Load targets from targets.yaml file"""
        targets = []
        
        # Load main targets file
        targets_file = self.data_dir / 'targets.yaml'
        if targets_file.exists():
            try:
                with open(targets_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                if data and 'targets' in data:
                    targets_list = data['targets']
                    if isinstance(targets_list, list):
                        # Array format: targets: [target1, target2, ...]
                        for target_data in targets_list:
                            target_data['source'] = 'file'
                            target_data['source_file'] = str(targets_file)
                            target_data['last_modified'] = self._get_file_modified_time(targets_file)
                            
                            # Ensure date fields exist
                            from datetime import datetime
                            current_time = datetime.now().isoformat() + 'Z'
                            if 'date_updated' not in target_data:
                                target_data['date_updated'] = current_time
                            
                            targets.append(target_data)
            except Exception as e:
                logger.error(f"Failed to load targets from {targets_file}: {e}")
        
        return targets
    
    def _get_file_modified_time(self, file_path: Path) -> int:
        """Get file modification time as timestamp"""
        try:
            return int(file_path.stat().st_mtime)
        except Exception:
            return int(datetime.now().timestamp())
    
    def list_available_files(self) -> Dict[str, List[str]]:
        """List all available YAML files by category"""
        files = {
            'prompts': [],
            'collections': [],
            'attack_types': [],
            'session_configs': []
        }
        
        if not self.data_dir.exists():
            return files
        
        for yaml_file in self.data_dir.glob('*.yaml'):
            name = yaml_file.name
            if 'adversarial_prompts' in name:
                files['prompts'].append(str(yaml_file))
            elif 'collection' in name:
                files['collections'].append(str(yaml_file))
            elif 'attack_types' in name or 'vulnerabilities' in name:
                files['attack_types'].append(str(yaml_file))
            elif 'session' in name:
                files['session_configs'].append(str(yaml_file))
        
        return files
    
    def save_scan_result(self, session_data: Dict[str, Any]) -> bool:
        """Save a scan result to sessions.json file"""
        try:
            sessions_file = self.data_dir / 'sessions.json'
            
            # Load existing sessions
            existing_sessions = []
            if sessions_file.exists():
                with open(sessions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    existing_sessions = data.get('scan_results', [])
            
            # Add new session
            existing_sessions.append(session_data)
            
            # Save back to file
            with open(sessions_file, 'w', encoding='utf-8') as f:
                json.dump({'scan_results': existing_sessions}, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved scan result to {sessions_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save scan result: {e}")
            return False
    
    def load_grading_intents(self) -> Dict[str, Dict[str, str]]:
        """Load grading intents from YAML file"""
        try:
            intents_file = self.data_dir / 'gradingIntents.yaml'
            if not intents_file.exists():
                logger.warning(f"Grading intents file not found: {intents_file}")
                return {}
            
            with open(intents_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data or 'grading_intents' not in data:
                logger.warning("No grading intents found in YAML file")
                return {}
            
            return data['grading_intents']
            
        except Exception as e:
            logger.error(f"Failed to load grading intents: {e}")
            return {}


# Global YAML loader instance
yaml_loader = YAMLLoader()
