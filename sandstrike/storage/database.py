"""
SQLite database support for Avenlis local storage.

This module provides database models and operations for storing rapid scans,
session data, and other local-only information.
"""

import sqlite3
import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from contextlib import contextmanager

from sandstrike.config import config
from sandstrike.exceptions import AvenlisError
from sandstrike.utils.logging import get_logger

logger = get_logger(__name__)


class AvenlisDatabase:
    """SQLite database manager for Avenlis"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path or config.database_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_tables()
    
    @contextmanager
    def get_connection(self):
        """Get database connection with automatic cleanup"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _ensure_tables(self):
        """Create database tables if they don't exist - DISABLED"""
        # DISABLED: This old database system is no longer used
        # The new AvenlisStorage system in main_storage.py handles all database operations
        # This prevents creation of redundant tables that conflict with the cleanup process
        pass


class RapidScanManager:
    """Manager for rapid scan operations"""
    
    def __init__(self, db: Optional[AvenlisDatabase] = None):
        self.db = db or AvenlisDatabase()
    
    def create_rapid_scan(self, name: str, target: str, scan_config: Dict[str, Any]) -> str:
        """Create a new rapid scan"""
        scan_id = str(uuid.uuid4())
        timestamp = int(datetime.now().timestamp())
        
        with self.db.get_connection() as conn:
            conn.execute('''
                INSERT INTO rapid_scans 
                (id, name, target, created_at, updated_at, status, config)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (scan_id, name, target, timestamp, timestamp, 'pending', json.dumps(scan_config)))
        
        logger.info(f"Created rapid scan: {name} ({scan_id})")
        return scan_id
    
    def update_scan_status(self, scan_id: str, status: str, summary: Optional[Dict[str, Any]] = None):
        """Update scan status and summary"""
        timestamp = int(datetime.now().timestamp())
        
        with self.db.get_connection() as conn:
            if summary:
                conn.execute('''
                    UPDATE rapid_scans 
                    SET status = ?, updated_at = ?, summary = ?,
                        total_prompts = ?, successful_attacks = ?, 
                        failed_attacks = ?, error_count = ?
                    WHERE id = ?
                ''', (
                    status, timestamp, json.dumps(summary),
                    summary.get('total_prompts', 0),
                    summary.get('successful_attacks', 0),
                    summary.get('failed_attacks', 0),
                    summary.get('error_count', 0),
                    scan_id
                ))
            else:
                conn.execute('''
                    UPDATE rapid_scans 
                    SET status = ?, updated_at = ? 
                    WHERE id = ?
                ''', (status, timestamp, scan_id))
    
    def add_scan_result(self, scan_id: str, result: Dict[str, Any]) -> str:
        """Add a result to a rapid scan"""
        result_id = str(uuid.uuid4())
        timestamp = int(datetime.now().timestamp())
        
        with self.db.get_connection() as conn:
            conn.execute('''
                INSERT INTO rapid_scan_results
                (id, scan_id, prompt_id, attack_technique, vuln_category, 
                 prompt, response, success, error, latency_ms, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result_id, scan_id,
                result.get('prompt_id'),
                result.get('attack_technique'),
                result.get('vuln_category'),
                result.get('prompt'),
                result.get('response'),
                1 if result.get('success', False) else 0,
                result.get('error'),
                result.get('latency_ms'),
                timestamp,
                json.dumps(result.get('metadata', {}))
            ))
        
        return result_id
    
    def get_rapid_scan(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """Get rapid scan by ID"""
        with self.db.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM rapid_scans WHERE id = ?
            ''', (scan_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return dict(row)
    
    def list_rapid_scans(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List rapid scans with pagination"""
        with self.db.get_connection() as conn:
            cursor = conn.execute('''
                SELECT id, name, target, created_at, updated_at, status,
                       total_prompts, successful_attacks, failed_attacks, error_count
                FROM rapid_scans 
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_scan_results(self, scan_id: str) -> List[Dict[str, Any]]:
        """Get all results for a rapid scan"""
        with self.db.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM rapid_scan_results 
                WHERE scan_id = ?
                ORDER BY created_at ASC
            ''', (scan_id,))
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                if result['metadata']:
                    result['metadata'] = json.loads(result['metadata'])
                results.append(result)
            
            return results
    
    def delete_rapid_scan(self, scan_id: str) -> bool:
        """Delete a rapid scan and all its results"""
        with self.db.get_connection() as conn:
            cursor = conn.execute('DELETE FROM rapid_scans WHERE id = ?', (scan_id,))
            return cursor.rowcount > 0
    
    def get_scan_statistics(self) -> Dict[str, Any]:
        """Get overall rapid scan statistics"""
        with self.db.get_connection() as conn:
            cursor = conn.execute('''
                SELECT 
                    COUNT(*) as total_scans,
                    SUM(total_prompts) as total_prompts,
                    SUM(successful_attacks) as total_successful,
                    SUM(failed_attacks) as total_failed,
                    AVG(duration_seconds) as avg_duration
                FROM rapid_scans
                WHERE status = 'completed'
            ''')
            
            row = cursor.fetchone()
            return dict(row) if row else {}


class CollectionCacheManager:
    """Manager for collections cache"""
    
    def __init__(self, db: Optional[AvenlisDatabase] = None):
        self.db = db or AvenlisDatabase()
    
    def update_collection_cache(self, collection_id: str, name: str, 
                              file_path: str, prompt_count: int,
                              metadata: Optional[Dict[str, Any]] = None):
        """Update collection in cache"""
        timestamp = int(datetime.now().timestamp())
        
        with self.db.get_connection() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO collections_cache
                (id, name, file_path, last_modified, prompt_count, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                collection_id, name, file_path, timestamp, 
                prompt_count, json.dumps(metadata or {})
            ))
    
    def get_cached_collections(self) -> List[Dict[str, Any]]:
        """Get all cached collections"""
        with self.db.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM collections_cache 
                ORDER BY name ASC
            ''')
            
            return [dict(row) for row in cursor.fetchall()]
    
    # Dynamic Variables Methods
    def get_dynamic_variables(self) -> Dict[str, Any]:
        """Get all dynamic variables from local storage"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT category, name, value FROM dynamic_variables
                    ORDER BY category, name
                ''')
                
                variables = {'variables': {}}
                for row in cursor.fetchall():
                    category = row['category']
                    name = row['name']
                    value = row['value']
                    
                    if category not in variables['variables']:
                        variables['variables'][category] = {}
                    variables['variables'][category][name] = value
                
                return variables
        except Exception as e:
            logger.error(f"Error getting dynamic variables: {e}")
            return {}
    
    def set_dynamic_variable(self, category: str, name: str, value: str, overwrite: bool = True) -> bool:
        """Set a dynamic variable in local storage"""
        try:
            with self.db.get_connection() as conn:
                # Check if variable exists
                cursor = conn.execute('''
                    SELECT id FROM dynamic_variables 
                    WHERE category = ? AND name = ?
                ''', (category, name))
                
                existing = cursor.fetchone()
                
                if existing and not overwrite:
                    return False
                
                if existing:
                    # Update existing
                    conn.execute('''
                        UPDATE dynamic_variables 
                        SET value = ?, updated_at = ?
                        WHERE category = ? AND name = ?
                    ''', (value, int(datetime.now().timestamp()), category, name))
                else:
                    # Insert new
                    conn.execute('''
                        INSERT INTO dynamic_variables 
                        (category, name, value, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (category, name, value, int(datetime.now().timestamp()), int(datetime.now().timestamp())))
                
                return True
        except Exception as e:
            logger.error(f"Error setting dynamic variable: {e}")
            return False
    
    def get_dynamic_variable(self, category: str, name: str) -> Optional[str]:
        """Get a specific dynamic variable"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT value FROM dynamic_variables 
                    WHERE category = ? AND name = ?
                ''', (category, name))
                
                row = cursor.fetchone()
                return row['value'] if row else None
        except Exception as e:
            logger.error(f"Error getting dynamic variable: {e}")
            return None
    
    def delete_dynamic_variable(self, category: str, name: str) -> bool:
        """Delete a dynamic variable"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute('''
                    DELETE FROM dynamic_variables 
                    WHERE category = ? AND name = ?
                ''', (category, name))
                
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting dynamic variable: {e}")
            return False
    
    def clear_dynamic_variables(self) -> bool:
        """Clear all dynamic variables"""
        try:
            with self.db.get_connection() as conn:
                conn.execute('DELETE FROM dynamic_variables')
                return True
        except Exception as e:
            logger.error(f"Error clearing dynamic variables: {e}")
            return False


# Global database instance
database = AvenlisDatabase()
