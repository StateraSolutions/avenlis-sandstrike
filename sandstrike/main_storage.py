"""
Local storage system for Avenlis.

This module provides SQLite-based local storage for test sessions, results,
and user settings.
"""

import json
import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import Column, DateTime, Integer, String, Text, Boolean, Float, ForeignKey, create_engine, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func

from sandstrike.config import AvenlisConfig
from sandstrike.exceptions import AvenlisError
from sandstrike.utils.logging import get_logger

logger = get_logger(__name__)

Base = declarative_base()


class TestSession(Base):
    """Database model for test sessions."""
    __tablename__ = 'test_sessions'
    
    id = Column(String(255), primary_key=True)  # Use string ID to match JSON structure
    session_name = Column(String(255), nullable=False)  # Session name
    target = Column(String(500), nullable=False)  # Target URL/endpoint
    target_model = Column(String(255), nullable=False)  # Target model name
    grader = Column(String(100), nullable=True)  # Grader used (ollama, anthropic, gemini, avenlis_copilot)
    grading_intent = Column(String(100), nullable=True)  # Grading intent (safety_evaluation, etc.)
    scan_mode = Column(String(50), nullable=True)  # Scan mode (rapid, full)
    status = Column(String(50), default='pending')  # pending, running, completed, failed
    started_at = Column(DateTime, default=func.now())  # When session started
    total_tests = Column(Integer, default=0)  # Total number of tests
    vulnerabilities_found = Column(Integer, default=0)  # Number of vulnerabilities found
    success_rate = Column(Float, default=0.0)  # Success rate percentage
    source = Column(String(50), default='local')  # Source: 'local', 'file', etc.
    results = Column(Text, nullable=True)  # JSON array of test results
    
    # Note: TestResult relationship removed as test_results table was deleted
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_name': self.session_name,
            'name': self.session_name,  # Alias for compatibility
            'target': self.target,
            'target_url': self.target,  # Alias for compatibility
            'target_model': self.target_model,
            'grader': self.grader,
            'grading_intent': self.grading_intent,
            'scan_mode': self.scan_mode,
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'created_at': self.started_at.isoformat() if self.started_at else None,  # Map started_at to created_at
            'date': self.started_at.isoformat() if self.started_at else None,  # Alias for compatibility
            'total_tests': self.total_tests,
            'vulnerabilities_found': self.vulnerabilities_found,
            'success_rate': self.success_rate,
            'source': self.source,
            'results': json.loads(self.results) if self.results else []
        }


# Removed TestResult and UserSetting classes - tables no longer needed
# TestResult table was removed as test results are now stored differently
# UserSetting table was removed as user settings are no longer needed

class Prompt(Base):
    """Master table for all prompts loaded from JSON/YAML files."""
    __tablename__ = 'prompts'
    
    id = Column(String(255), primary_key=True)  # Use string ID to match YAML structure
    attack_technique = Column(String(255), nullable=False)  # e.g., "prompt_injection", "prompt_probing"
    vuln_category = Column(String(255), nullable=False)  # e.g., "system_prompt_leakage", "violence_and_self_harm"
    vuln_subcategory = Column(String(255), nullable=True)  # e.g., "physical_harm", "personal_data"
    prompt = Column(Text, nullable=False)  # The actual prompt text
    severity = Column(String(50), default='medium')  # low, medium, high, critical
    owasp_top10_llm_mapping = Column(Text, nullable=True)  # JSON array of OWASP mappings
    mitreatlasmapping = Column(Text, nullable=True)  # JSON array of MITRE ATLAS mappings
    collection_id = Column(String(255), nullable=True)  # Reference to collection
    
    def to_dict(self):
        return {
            'id': self.id,
            'attack_technique': self.attack_technique,
            'vuln_category': self.vuln_category,
            'vuln_subcategory': self.vuln_subcategory,
            'prompt': self.prompt,
            'severity': self.severity,
            'owasp_top10_llm_mapping': json.loads(self.owasp_top10_llm_mapping) if self.owasp_top10_llm_mapping else [],
            'mitreatlasmapping': json.loads(self.mitreatlasmapping) if self.mitreatlasmapping else [],
            'collection_id': self.collection_id,
            'source': 'local'
        }


class PromptCollection(Base):
    """Database model for prompt collections/projects."""
    __tablename__ = 'prompt_collections'
    
    id = Column(String(255), primary_key=True)  # Use string ID to match YAML structure
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    prompt_ids = Column(Text, nullable=True)  # JSON array of prompt IDs in this collection
    date_updated = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def to_dict(self):
        try:
            prompt_ids_list = json.loads(self.prompt_ids) if self.prompt_ids else []
            return {
                'id': self.id,
                'name': self.name,
                'description': self.description,
                'prompt_ids': prompt_ids_list,
                'prompt_count': len(prompt_ids_list),
                'date_updated': self.date_updated.isoformat() if self.date_updated else None
            }
        except Exception as e:
            # Fallback if JSON parsing fails
            return {
                'id': self.id,
                'name': self.name,
                'description': self.description,
                'prompt_ids': [],
                'prompt_count': 0,
                'date_updated': self.date_updated.isoformat() if self.date_updated else None
            }


# Removed CollectionPrompt class - table no longer needed
# CollectionPrompt table was removed as it was redundant with prompt_collections



# Removed redundant Local* classes - these tables are no longer needed
# The following classes were removed as they correspond to redundant tables:
# - LocalAdversarialPrompt (local_adversarial_prompts)
# - LocalCollection (local_collections)  
# - LocalAttackType (local_attack_types)
# - LocalVulnerabilityCategory (local_vulnerability_categories)
# - LocalSessionConfig (local_session_configs)


class Target(Base):
    """Database model for scan targets."""
    __tablename__ = 'targets'
    
    id = Column(String(255), primary_key=True)  # Use string ID to match YAML structure
    name = Column(String(255), nullable=False)  # Target name
    ip_address = Column(String(255), nullable=False)  # IP address (may include port)
    description = Column(Text, nullable=True)  # Optional description
    target_type = Column(String(50), nullable=True, default='URL')  # Target type: 'Ollama' or 'URL'
    model = Column(String(255), nullable=True)  # Model name (for Ollama targets)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'ip_address': self.ip_address,
            'description': self.description,
            'target_type': self.target_type,
            'model': self.model,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class DynamicVariable(Base):
    """Database model for dynamic variables used in prompt templates."""
    __tablename__ = 'dynamic_variables'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(100), nullable=False)  # e.g., "application", "data", "system"
    name = Column(String(100), nullable=False)  # Variable name within category
    value = Column(Text, nullable=False)  # Variable value
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Unique constraint on category + name combination
    __table_args__ = (
        UniqueConstraint('category', 'name', name='uq_category_name'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'category': self.category,
            'name': self.name,
            'value': self.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class AvenlisStorage:
    """
    Local storage manager for Avenlis.
    
    Provides SQLite-based storage for sessions, results, and settings.
    Tailored for red team testing workflows.
    """
    
    def __init__(self, config: Optional[AvenlisConfig] = None, db_path: Optional[str] = None):
        self.config = config or AvenlisConfig()
        self.db_path = Path(db_path) if db_path else self._get_db_path()
        self.engine = create_engine(f'sqlite:///{self.db_path}', echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Initialize in-memory settings cache (UserSetting table was removed)
        self._settings_cache: Dict[str, Any] = {}
        
        # Initialize database
        self._init_database()
    
    def _get_db_path(self) -> Path:
        """Get the path to the SQLite database file."""
        # Create ~/.avenlis directory if it doesn't exist
        home = Path.home()
        avenlis_dir = home / '.avenlis'
        avenlis_dir.mkdir(exist_ok=True)
        
        db_path = avenlis_dir / 'avenlis.db'
        logger.debug(f"Database path: {db_path}")
        return db_path
    
    def _init_database(self):
        """Initialize the database and create tables."""
        try:
            # Create all tables
            Base.metadata.create_all(self.engine)
            # Run lightweight migrations
            self._migrate_prompt_table_remove_timestamps()
            self._migrate_targets_table_add_target_type()
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise AvenlisError(f"Database initialization failed: {e}")

    def _migrate_prompt_table_remove_timestamps(self):
        """
        Remove created_at/updated_at columns from prompts table if they exist.
        SQLite doesn't support DROP COLUMN directly, so recreate the table.
        """
        try:
            if not self.db_path.exists():
                return

            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(prompts)")
                columns = [row[1] for row in cursor.fetchall()]

                if 'created_at' not in columns and 'updated_at' not in columns:
                    return

                logger.info("Migrating prompts table to remove created_at/updated_at columns")

                cursor.execute("BEGIN")
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS prompts_temp (
                        id TEXT PRIMARY KEY,
                        attack_technique TEXT NOT NULL,
                        vuln_category TEXT NOT NULL,
                        vuln_subcategory TEXT,
                        prompt TEXT NOT NULL,
                        severity TEXT,
                        owasp_top10_llm_mapping TEXT,
                        mitreatlasmapping TEXT,
                        collection_id TEXT
                    )
                """)

                cursor.execute("""
                    INSERT INTO prompts_temp (
                        id, attack_technique, vuln_category, vuln_subcategory,
                        prompt, severity, owasp_top10_llm_mapping, mitreatlasmapping, collection_id
                    )
                    SELECT
                        id, attack_technique, vuln_category, vuln_subcategory,
                        prompt, severity, owasp_top10_llm_mapping, mitreatlasmapping, collection_id
                    FROM prompts
                """)

                cursor.execute("DROP TABLE prompts")
                cursor.execute("ALTER TABLE prompts_temp RENAME TO prompts")
                conn.commit()
                logger.info("Prompts table migration complete")
        except Exception as e:
            logger.error(f"Failed to migrate prompts table: {e}")
    
    def _migrate_targets_table_add_target_type(self):
        """
        Add target_type column to targets table if it doesn't exist.
        """
        try:
            if not self.db_path.exists():
                return

            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(targets)")
                columns = [row[1] for row in cursor.fetchall()]

                if 'target_type' in columns:
                    return

                logger.info("Migrating targets table to add target_type column")

                # SQLite 3.1.3+ supports ALTER TABLE ADD COLUMN
                cursor.execute("""
                    ALTER TABLE targets 
                    ADD COLUMN target_type TEXT
                """)
                
                # Set default value for existing rows
                cursor.execute("""
                    UPDATE targets 
                    SET target_type = 'URL' 
                    WHERE target_type IS NULL
                """)
                
                conn.commit()
                logger.info("Targets table migration complete - added target_type column")
        except Exception as e:
            logger.error(f"Failed to migrate targets table: {e}")
            # If ALTER TABLE fails, try recreating the table
            try:
                logger.info("Attempting to recreate targets table with target_type column")
                with sqlite3.connect(str(self.db_path)) as conn:
                    cursor = conn.cursor()
                    cursor.execute("BEGIN")
                    
                    # Create temp table with new schema
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS targets_temp (
                            id TEXT PRIMARY KEY,
                            name TEXT NOT NULL,
                            ip_address TEXT NOT NULL,
                            description TEXT,
                            target_type TEXT DEFAULT 'URL',
                            model TEXT,
                            created_at TIMESTAMP,
                            updated_at TIMESTAMP
                        )
                    """)
                    
                    # Copy data from old table
                    cursor.execute("""
                        INSERT INTO targets_temp (
                            id, name, ip_address, description, model, created_at, updated_at
                        )
                        SELECT 
                            id, name, ip_address, description, model, created_at, updated_at
                        FROM targets
                    """)
                    
                    # Replace old table
                    cursor.execute("DROP TABLE targets")
                    cursor.execute("ALTER TABLE targets_temp RENAME TO targets")
                    conn.commit()
                    logger.info("Targets table recreated with target_type column")
            except Exception as e2:
                logger.error(f"Failed to recreate targets table: {e2}")
    
    def get_db_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()
    
    # Session management methods
    def create_session(self, name: str, target_url: str, target_model: str, 
                      grader: str = None, grading_intent: str = None, scan_mode: str = None, source: str = 'local') -> str:
        """Create a new test session."""
        try:
            with self.get_db_session() as db:
                # Generate a unique session ID
                import uuid
                session_id = f"session_{uuid.uuid4().hex[:8]}"
                
                session = TestSession(
                    id=session_id,
                    session_name=name,
                    target=target_url,
                    target_model=target_model,
                    grader=grader,
                    grading_intent=grading_intent,
                    scan_mode=scan_mode,
                    source=source,
                    status='pending'
                )
                db.add(session)
                db.commit()
                db.refresh(session)
                logger.info(f"Created session {session.id}: {name}")
                return session.id
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise AvenlisError(f"Failed to create session: {e}")
    
    def get_session_by_id(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a session by ID."""
        try:
            with self.get_db_session() as db:
                session = db.query(TestSession).filter(TestSession.id == session_id).first()
                return session.to_dict() if session else None
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None
    
    def get_all_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all sessions, ordered by creation date (newest first)."""
        try:
            with self.get_db_session() as db:
                sessions = db.query(TestSession)\
                    .order_by(TestSession.started_at.desc())\
                    .limit(limit).all()
                return [session.to_dict() for session in sessions]
        except Exception as e:
            logger.error(f"Failed to get sessions: {e}")
            return []
    
    def update_session(self, session_id: str, **updates) -> bool:
        """Update session data."""
        try:
            with self.get_db_session() as db:
                session = db.query(TestSession).filter(TestSession.id == session_id).first()
                if not session:
                    return False
                
                
                updated_fields = []
                for key, value in updates.items():
                    if hasattr(session, key):
                        old_value = getattr(session, key)
                        setattr(session, key, value)
                        updated_fields.append(f"{key}: '{old_value}' -> '{value}'")
                                
                db.commit()
                logger.debug(f"Updated session {session_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to update session {session_id}: {e}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its results."""
        try:
            with self.get_db_session() as db:
                session = db.query(TestSession).filter(TestSession.id == session_id).first()
                if session:
                    db.delete(session)
                    db.commit()
                    logger.info(f"Deleted session {session_id}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    # Results management methods
    def add_result(self, session_id: str, attack_id: str, attack_name: str,
                   status: str, prompt: str = None,
                   response: str = None, 
                   error_message: str = None, test_group: str = None,
                   grader_verdict: str = None, confidence_score: float = None,
                   prompt_id: str = None, attack_technique: str = None,
                   vuln_category: str = None, severity: str = None,
                   grader_confidence: str = None) -> int:
        """Add a test result to a session."""
        try:
            with self.get_db_session() as db:
                # Get the session
                session = db.query(TestSession).filter(TestSession.id == session_id).first()
                if not session:
                    raise AvenlisError(f"Session {session_id} not found")
                
                # Create result data
                result_data = {
                    'prompt_id': prompt_id or f"result_{int(time.time() * 1000)}",  # Use prompt_id or generate fallback
                    'status': status,
                    'test_group': test_group,
                    'attack_technique': attack_technique or 'Unknown',
                    'vuln_category': vuln_category or 'Unknown',
                    'severity': severity or 'medium'
                }
                
                if prompt:
                    result_data['prompt'] = prompt
                if response:
                    result_data['response'] = response
                if error_message:
                    result_data['error_message'] = error_message
                if grader_verdict:
                    result_data['grader_verdict'] = grader_verdict
                if confidence_score is not None:
                    result_data['confidence_score'] = confidence_score
                if grader_confidence:
                    result_data['grader_confidence'] = grader_confidence
                
                # Get existing results
                existing_results = json.loads(session.results) if session.results else []
                existing_results.append(result_data)
                
                # Update session with new results
                session.results = json.dumps(existing_results)
                db.commit()
                
                logger.info(f"Added result to session {session_id}")
                return result_data['prompt_id']
        except Exception as e:
            logger.error(f"Failed to add result to session {session_id}: {e}")
            raise AvenlisError(f"Failed to add result: {e}")
    
    def get_session_results(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all results for a session."""
        try:
            with self.get_db_session() as db:
                session = db.query(TestSession).filter(TestSession.id == session_id).first()
                if session and session.results:
                    import json
                    return json.loads(session.results)
                return []
        except Exception as e:
            logger.error(f"Failed to get results for session {session_id}: {e}")
            return []
    
    # Settings management methods
    # Note: UserSetting table was removed. These methods are kept for API compatibility
    # but now use a simple in-memory dictionary. For persistent storage, consider using
    # a file-based approach or re-implementing the UserSetting table.
    
    def set_setting(self, key: str, value: Any) -> bool:
        """Set a user setting (in-memory only, not persistent)."""
        try:
            self._settings_cache[key] = value
            return True
        except Exception as e:
            logger.error(f"Failed to set setting {key}: {e}")
            return False
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a user setting (from in-memory cache)."""
        try:
            return self._settings_cache.get(key, default)
        except Exception as e:
            logger.error(f"Failed to get setting {key}: {e}")
            return default
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all user settings (from in-memory cache)."""
        try:
            return self._settings_cache.copy()
        except Exception as e:
            logger.error(f"Failed to get all settings: {e}")
            return {}
    
    # Utility methods
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            with self.get_db_session() as db:
                total_sessions = db.query(TestSession).count()
                # Count results from all sessions
                total_results = 0
                sessions = db.query(TestSession).all()
                for session in sessions:
                    if session.results:
                        import json
                        try:
                            results = json.loads(session.results)
                            total_results += len(results)
                        except:
                            pass
                total_collections = db.query(PromptCollection).count()
                total_prompts = db.query(Prompt).count()
                recent_sessions = db.query(TestSession)\
                    .filter(TestSession.started_at >= datetime.now().replace(day=1))\
                    .count()
                
                return {
                    'database_path': str(self.db_path),
                    'total_sessions': total_sessions,
                    'total_results': total_results,
                    'total_collections': total_collections,
                    'total_prompts': total_prompts,
                    'recent_sessions': recent_sessions,
                    'database_size_mb': self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
                }
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}
    
    def cleanup_old_sessions(self, days_old: int = 30) -> int:
        """Clean up sessions older than specified days."""
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            with self.get_db_session() as db:
                old_sessions = db.query(TestSession)\
                    .filter(TestSession.started_at < cutoff_date).all()
                
                count = len(old_sessions)
                for session in old_sessions:
                    db.delete(session)
                
                db.commit()
                logger.info(f"Cleaned up {count} old sessions")
                return count
        except Exception as e:
            logger.error(f"Failed to cleanup old sessions: {e}")
            return 0
    
    # Prompt Collection Management Methods
    def create_collection(self, name: str, description: str = None, prompt_ids: Optional[List[str]] = None, collection_id: Optional[str] = None) -> str:
        """Create a new prompt collection."""
        try:
            from datetime import datetime
            
            # Generate collection ID if not provided (string format to match YAML structure)
            if not collection_id:
                collection_id = f"collection_{int(datetime.now().timestamp())}"
            # Filter out empty, null, or whitespace-only prompt IDs
            if prompt_ids:
                filtered_prompt_ids = [pid for pid in prompt_ids if pid and str(pid).strip()]
            else:
                filtered_prompt_ids = []
            prompt_ids_json = json.dumps(filtered_prompt_ids)
            
            with self.get_db_session() as db:
                collection = PromptCollection(
                    id=collection_id,
                    name=name,
                    description=description,
                    prompt_ids=prompt_ids_json
                )
                db.add(collection)
                db.commit()
                db.refresh(collection)
                
                logger.info(f"Created collection: {name} (ID: {collection.id}) with {len(filtered_prompt_ids)} prompts")
                return collection.id
        except Exception as e:
            logger.error(f"Failed to create collection {name}: {e}")
            raise AvenlisError(f"Failed to create collection: {e}")
    
    def get_collection(self, collection_id: Union[int, str], include_prompts: bool = True) -> Optional[Dict[str, Any]]:
        """Get a collection by ID (supports both string and int IDs)."""
        try:
            with self.get_db_session() as db:
                # First get the collection without relationships
                collection = db.query(PromptCollection).filter(PromptCollection.id == str(collection_id)).first()
                if not collection:
                    return None
                
                # Convert to dict first
                collection_dict = collection.to_dict()
                
                # If prompts are requested, load them separately to avoid relationship issues
                if include_prompts:
                    try:
                        prompts = self.get_collection_prompts(collection_id)
                        collection_dict['prompts'] = prompts
                    except Exception as prompt_error:
                        logger.warning(f"Failed to load prompts for collection {collection_id}: {prompt_error}")
                        collection_dict['prompts'] = []
                
                return collection_dict
        except Exception as e:
            logger.error(f"Failed to get collection {collection_id}: {e}")
            return None
    
    def get_all_collections(self, include_prompts: bool = False) -> List[Dict[str, Any]]:
        """Get all prompt collections."""
        try:
            with self.get_db_session() as db:
                query = db.query(PromptCollection)
                if include_prompts:
                    query = query.options(relationship(PromptCollection.prompts))
                
                collections = query.order_by(PromptCollection.updated_at.desc()).all()
                return [collection.to_dict() for collection in collections]
        except Exception as e:
            logger.error(f"Failed to get collections: {e}")
            return []
    
    def update_collection(self, collection_id: int, name: str = None, description: str = None, prompt_ids: list = None) -> bool:
        """Update a prompt collection (handles both local and YAML collections)."""
        try:
            # First check if it's a YAML collection
            from sandstrike.storage.yaml_loader import yaml_loader
            yaml_collections = yaml_loader.load_collections()
            yaml_collection = next((c for c in yaml_collections if c.get('id') == collection_id), None)
            
            if yaml_collection:
                # Update YAML collection
                return self.update_yaml_collection(
                    collection_id=collection_id,
                    name=name,
                    description=description,
                    prompt_ids=prompt_ids
                )
            else:
                # Update local collection
                with self.get_db_session() as db:
                    collection = db.query(PromptCollection).filter(PromptCollection.id == collection_id).first()
                    if not collection:
                        return False
                    
                    if name is not None:
                        collection.name = name
                    if description is not None:
                        collection.description = description
                    if prompt_ids is not None:
                        # Filter out empty, null, or whitespace-only prompt IDs
                        filtered_prompt_ids = [pid for pid in prompt_ids if pid and str(pid).strip()]
                        collection.prompt_ids = json.dumps(filtered_prompt_ids)
                    
                    collection.date_updated = func.now()
                    db.commit()
                    
                    logger.info(f"Updated local collection: {collection_id}")
                    return True
        except Exception as e:
            logger.error(f"Failed to update collection {collection_id}: {e}")
            return False
    
    def delete_collection(self, collection_id: Union[int, str]) -> bool:
        """Delete a prompt collection and all its prompts."""
        try:
            with self.get_db_session() as db:
                collection = db.query(PromptCollection).filter(PromptCollection.id == str(collection_id)).first()
                if not collection:
                    return False
                
                db.delete(collection)  # Cascade will delete related prompts
                db.commit()
                
                logger.info(f"Deleted collection: {collection_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to delete collection {collection_id}: {e}")
            return False
    
    def delete_collection_by_name(self, name: str) -> bool:
        """Delete a prompt collection by name."""
        try:
            with self.get_db_session() as db:
                collection = db.query(PromptCollection).filter(PromptCollection.name == name).first()
                if not collection:
                    logger.warning(f"Collection with name '{name}' not found")
                    return False
                
                db.delete(collection)  # Cascade will delete related prompts
                db.commit()
                
                logger.info(f"Deleted collection by name: {name}")
                return True
        except Exception as e:
            logger.error(f"Failed to delete collection by name '{name}': {e}")
            return False
    
    def load_collections_from_json(self, json_file_path: str = None) -> List[Dict[str, Any]]:
        """Load collection templates from JSON file."""
        try:
            if json_file_path is None:
                # Default to the collections.json file in the data directory
                current_dir = Path(__file__).parent
                json_file_path = current_dir / "redteam" / "data" / "collections.json"
            
            json_path = Path(json_file_path)
            if not json_path.exists():
                logger.warning(f"Collections JSON file not found: {json_path}")
                return []
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            collections = data.get('collections', [])
            logger.info(f"Loaded {len(collections)} collection templates from {json_path}")
            return collections
            
        except Exception as e:
            logger.error(f"Failed to load collections from JSON: {e}")
            return []
    
    def create_collection_from_template(self, template: Dict[str, Any]) -> str:
        """Create a collection from a template."""
        try:
            from datetime import datetime
            
            # Generate collection ID (string format to match YAML structure)
            collection_id = f"collection_{int(datetime.now().timestamp())}"
            
            with self.get_db_session() as db:
                # Check if collection already exists
                existing = db.query(PromptCollection).filter(
                    PromptCollection.name == template['name']
                ).first()
                
                if existing:
                    logger.info(f"Collection '{template['name']}' already exists, skipping")
                    return existing.id
                
                collection = PromptCollection(
                    id=collection_id,
                    name=template['name'],
                    description=template.get('description', '')
                )
                
                db.add(collection)
                db.commit()
                db.refresh(collection)
                
                logger.info(f"Created collection from template: {template['name']} (ID: {collection.id})")
                return collection.id
                
        except Exception as e:
            logger.error(f"Failed to create collection from template: {e}")
            raise AvenlisError(f"Failed to create collection from template: {e}")
    
    
    # Prompt Item Management Methods
    def add_prompt_to_collection(self, collection_id: str, prompt_id: str = None, 
                                name: str = None, prompt_text: str = None, 
                                category: str = None, severity: str = 'medium', 
                                expected_behavior: str = 'block',
                                attack_technique: str = None, vuln_category: str = None) -> str:
        """Add a prompt to a collection. If prompt_id is provided, use existing prompt. Otherwise create new prompt."""
        try:
            with self.get_db_session() as db:
                # Verify collection exists
                collection = db.query(PromptCollection).filter(PromptCollection.id == collection_id).first()
                if not collection:
                    raise AvenlisError(f"Collection {collection_id} not found")
                
                # If prompt_id is provided, use existing prompt
                if prompt_id:
                    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
                    if not prompt:
                        raise AvenlisError(f"Prompt {prompt_id} not found")
                    # Update collection_id to link to this collection (for backward compatibility)
                    prompt.collection_id = collection_id
                    
                    # Also update collection's prompt_ids array
                    collection_dict = collection.to_dict()
                    current_prompt_ids = collection_dict.get('prompt_ids', [])
                    if prompt_id not in current_prompt_ids:
                        current_prompt_ids.append(prompt_id)
                        collection.prompt_ids = json.dumps(current_prompt_ids)
                        collection.date_updated = func.now()
                    
                    db.commit()
                    logger.info(f"Added existing prompt {prompt.id} to collection {collection_id}")
                    return prompt.id
                else:
                    # Create new prompt - require essential fields
                    if not prompt_text:
                        raise AvenlisError("prompt_text is required when creating new prompt")
                    if not attack_technique:
                        raise AvenlisError("attack_technique is required when creating new prompt")
                    if not vuln_category:
                        raise AvenlisError("vuln_category is required when creating new prompt")
                    
                    # Generate prompt ID
                    import uuid
                    new_prompt_id = f"prompt_{uuid.uuid4().hex[:8]}"
                    
                    prompt = Prompt(
                        id=new_prompt_id,
                        attack_technique=attack_technique,
                        vuln_category=vuln_category,
                        vuln_subcategory=category,  # Map category to vuln_subcategory
                        prompt=prompt_text,
                        severity=severity,
                        collection_id=collection_id
                    )
                    db.add(prompt)
                    
                    # Also update collection's prompt_ids array
                    collection_dict = collection.to_dict()
                    current_prompt_ids = collection_dict.get('prompt_ids', [])
                    if new_prompt_id not in current_prompt_ids:
                        current_prompt_ids.append(new_prompt_id)
                        collection.prompt_ids = json.dumps(current_prompt_ids)
                        collection.date_updated = func.now()
                    
                    db.commit()
                    db.refresh(prompt)
                    
                    logger.info(f"Added new prompt {prompt.id} to collection {collection_id}")
                    return prompt.id
        except Exception as e:
            logger.error(f"Failed to add prompt to collection {collection_id}: {e}")
            raise AvenlisError(f"Failed to add prompt: {e}")
    
    def get_collection_prompts(self, collection_id: str, category: str = None, 
                              severity: str = None) -> List[Dict[str, Any]]:
        """Get prompts from a collection with optional filtering."""
        try:
            with self.get_db_session() as db:
                # First, get the collection to check if it uses prompt_ids format
                collection = db.query(PromptCollection).filter(PromptCollection.id == collection_id).first()
                
                if collection:
                    collection_dict = collection.to_dict()
                    prompt_ids = collection_dict.get('prompt_ids', [])
                    
                    # If collection has prompt_ids, use those to fetch prompts
                    if prompt_ids and len(prompt_ids) > 0:
                        # Filter out empty/null prompt IDs
                        valid_prompt_ids = [pid for pid in prompt_ids if pid and str(pid).strip()]
                        query = db.query(Prompt).filter(Prompt.id.in_(valid_prompt_ids))
                    else:
                        # Fallback to old format: filter by collection_id field
                        query = db.query(Prompt).filter(Prompt.collection_id == collection_id)
                else:
                    # Collection not found, try old format
                    query = db.query(Prompt).filter(Prompt.collection_id == collection_id)

                if category:
                    query = query.filter(Prompt.vuln_subcategory == category)
                if severity:
                    query = query.filter(Prompt.severity == severity)
                
                prompts = query.order_by(Prompt.created_at.desc()).all()
                
                # Convert to dict and merge with JSON data for rich metadata
                result_prompts = []
                for prompt in prompts:
                    prompt_dict = prompt.to_dict()
                    # Try to find matching prompt in JSON data by prompt text
                    json_prompt = self._find_matching_json_prompt(prompt_dict.get('prompt_text', ''))
                    if json_prompt:
                        # Merge JSON data with database data (JSON takes precedence for metadata)
                        prompt_dict.update({
                            'attack_technique': json_prompt.get('attack_technique', prompt_dict.get('attack_technique')),
                            'vuln_category': json_prompt.get('vuln_category', prompt_dict.get('vuln_category')),
                            'vuln_subcategory': json_prompt.get('vuln_subcategory', prompt_dict.get('vuln_subcategory')),
                            'owasp_top10_llm_mapping': json_prompt.get('owasp_top10_llm_mapping', prompt_dict.get('owasp_top10_llm_mapping', [])),
                            'prompt': json_prompt.get('prompt', prompt_dict.get('prompt_text', '')),
                        })
                    result_prompts.append(prompt_dict)
                
                return result_prompts
        except Exception as e:
            logger.error(f"Failed to get prompts for collection {collection_id}: {e}")
            return []
    
    def _find_matching_json_prompt(self, prompt_text: str) -> Optional[Dict[str, Any]]:
        """Find a matching prompt in JSON data by comparing prompt text."""
        try:
            current_dir = Path(__file__).parent
            data_dir = current_dir / 'redteam' / 'data'
            
            if not data_dir.exists():
                return None
                
            data_files = ['adversarial_prompts.json', 'security_templates.json', 'simple_test.json', 'evaluation_patterns.json']
            
            for file_name in data_files:
                file_path = data_dir / file_name
                if file_path.exists():
                    json_prompts = self._load_json_prompts(str(file_path))
                    for json_prompt in json_prompts:
                        json_text = json_prompt.get('prompt', '')
                        if json_text and json_text.strip() == prompt_text.strip():
                            return json_prompt
            return None
        except Exception as e:
            logger.error(f"Failed to find matching JSON prompt: {e}")
            return None
    
    def update_prompt(self, prompt_id: str, prompt_text: str = None,
                     category: str = None, severity: str = None, 
                     attack_technique: str = None, vuln_category: str = None,
                     vuln_subcategory: str = None) -> bool:
        """Update a prompt in a collection."""
        try:
            with self.get_db_session() as db:
                prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
                if not prompt:
                    return False
                
                if prompt_text is not None:
                    prompt.prompt = prompt_text
                if category is not None:
                    prompt.vuln_subcategory = category
                if vuln_subcategory is not None:
                    prompt.vuln_subcategory = vuln_subcategory
                if severity is not None:
                    prompt.severity = severity
                if attack_technique is not None:
                    prompt.attack_technique = attack_technique
                if vuln_category is not None:
                    prompt.vuln_category = vuln_category
                
                prompt.updated_at = func.now()
                db.commit()
                
                logger.info(f"Updated prompt: {prompt_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to update prompt {prompt_id}: {e}")
            return False
    
    def delete_prompt(self, prompt_id: str) -> bool:
        """Delete a prompt from a collection."""
        try:
            with self.get_db_session() as db:
                prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
                if not prompt:
                    return False
                
                db.delete(prompt)
                db.commit()
                
                logger.info(f"Deleted prompt: {prompt_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to delete prompt {prompt_id}: {e}")
            return False
    
    def search_collections(self, query: str) -> List[Dict[str, Any]]:
        """Search collections by name or description."""
        try:
            with self.get_db_session() as db:
                search_query = db.query(PromptCollection)
                
                # Search in name and description
                if query:
                    search_query = search_query.filter(
                        db.or_(
                            PromptCollection.name.contains(query),
                            PromptCollection.description.contains(query)
                        )
                    )
                
                collections = search_query.order_by(PromptCollection.updated_at.desc()).all()
                return [collection.to_dict() for collection in collections]
        except Exception as e:
            logger.error(f"Failed to search collections: {e}")
            return []

    # Master Prompts Management Methods
    def load_prompts_from_json(self, file_path: str) -> List[Dict[str, Any]]:
        """Load prompts from JSON file into the master prompts table."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            loaded_prompts = []
            with self.get_db_session() as db:
                # Handle different JSON structures
                if isinstance(data, list):
                    # Direct list of prompts
                    for prompt_data in data:
                        if isinstance(prompt_data, dict):
                            prompt = self._create_prompt_from_data(prompt_data, file_path, db)
                            if prompt:
                                loaded_prompts.append(prompt.to_dict())
                elif isinstance(data, dict):
                    # Dict with categories or single prompt
                    if 'prompt' in data:
                        # Single prompt file
                        prompt = self._create_prompt_from_data(data, file_path, db)
                        if prompt:
                            loaded_prompts.append(prompt.to_dict())
                    else:
                        # Dict with categories
                        for category, items in data.items():
                            if isinstance(items, list):
                                for prompt_data in items:
                                    if isinstance(prompt_data, dict):
                                        prompt_data['category'] = prompt_data.get('category', category)
                                        prompt = self._create_prompt_from_data(prompt_data, file_path, db)
                                        if prompt:
                                            loaded_prompts.append(prompt.to_dict())
            
            logger.info(f"Loaded {len(loaded_prompts)} prompts from {file_path}")
            return loaded_prompts
        except Exception as e:
            logger.error(f"Failed to load prompts from {file_path}: {e}")
            return []
            
    def _create_prompt_from_data(self, prompt_data: Dict[str, Any], source_file: str, db: Session) -> Optional[Prompt]:
        """Create a Prompt object from JSON data. Uses auto-generated database IDs, ignores any JSON ID fields."""
        try:
            # Extract prompt text from various possible fields
            prompt_text = prompt_data.get('prompt') or prompt_data.get('prompt_text') or prompt_data.get('text', '')
            if not prompt_text:
                logger.warning(f"Skipping prompt with no text: {prompt_data}")
                return None
            
            # Check if prompt already exists (by text content)
            existing = db.query(Prompt).filter(Prompt.prompt_text == prompt_text).first()
            if existing:
                logger.info(f"Prompt already exists: {prompt_data.get('name', 'Unknown')}")
                return existing
            
            # Extract name - prioritize 'name' field, fallback to 'id' for backwards compatibility
            prompt_name = prompt_data.get('name')
            if not prompt_name:
                # Use 'id' field as name if 'name' not provided (for backwards compatibility)
                prompt_name = prompt_data.get('id', 'Imported Prompt')
                logger.debug(f"Using 'id' field as name: {prompt_name}")
            
            # Create new prompt with auto-generated database ID
            prompt = Prompt(
                name=prompt_name,
                prompt_text=prompt_text,
                category=prompt_data.get('category') or prompt_data.get('vuln_category'),
                severity=prompt_data.get('severity', 'medium'),
                expected_behavior=prompt_data.get('expected_behavior', 'block'),
                source_file=source_file
            )
            
            db.add(prompt)
            db.commit()
            db.refresh(prompt)
            
            logger.debug(f"Created prompt with auto-generated ID {prompt.id}: {prompt.name}")
            return prompt
        except Exception as e:
            logger.error(f"Failed to create prompt from data: {e}")
            return None
    
    def get_all_master_prompts(self, category: str = None, severity: str = None) -> List[Dict[str, Any]]:
        """Get all prompts from the master prompts table."""
        try:
            with self.get_db_session() as db:
                query = db.query(Prompt)
                
                if category:
                    query = query.filter(Prompt.category == category)
                if severity:
                    query = query.filter(Prompt.severity == severity)
                
                prompts = query.order_by(Prompt.created_at.desc()).all()
                return [prompt.to_dict() for prompt in prompts]
        except Exception as e:
            logger.error(f"Failed to get master prompts: {e}")
            return []
    
    def remove_prompt_from_collection(self, collection_id: str, prompt_id: str) -> bool:
        """Remove a prompt from a collection (but keep the prompt in master table)."""
        try:
            with self.get_db_session() as db:
                # Get the collection
                collection = db.query(PromptCollection).filter(PromptCollection.id == collection_id).first()
                if not collection:
                    logger.warning(f"Collection {collection_id} not found")
                    return False
                
                # Update collection's prompt_ids array
                collection_dict = collection.to_dict()
                current_prompt_ids = collection_dict.get('prompt_ids', [])
                if prompt_id in current_prompt_ids:
                    current_prompt_ids.remove(prompt_id)
                    collection.prompt_ids = json.dumps(current_prompt_ids)
                    collection.date_updated = func.now()
                
                # Also remove the relationship by setting collection_id to None (for backward compatibility)
                prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
                if prompt and prompt.collection_id == collection_id:
                    prompt.collection_id = None
                
                db.commit()
                
                logger.info(f"Removed prompt {prompt_id} from collection {collection_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to remove prompt from collection: {e}")
            return False
    
    def create_prompt(self, prompt_data: Union[Dict[str, Any], str], prompt_text: str = None, attack_technique: str = None, 
                     vuln_category: str = None, vuln_subcategory: str = None, severity: str = 'medium', 
                     expected_behavior: str = 'block', source_file: str = None) -> Union[int, str]:
        """Create a new prompt - supports both old API (returns int) and new CLI API (returns str)."""
        try:
            # Handle both old API (individual parameters) and new API (dict)
            if isinstance(prompt_data, dict):
                # New CLI API - create local prompt
                prompt_id = prompt_data.get('id')
                if not prompt_id:
                    from datetime import datetime
                    prompt_id = f"prompt_{int(datetime.now().timestamp())}"
                
                # Extract values from dict, with fallback to function parameters for backwards compatibility
                attack_technique_value = prompt_data.get('attack_technique') or attack_technique
                vuln_category_value = prompt_data.get('vuln_category') or vuln_category
                vuln_subcategory_value = prompt_data.get('vuln_subcategory') or vuln_subcategory
                prompt_text_value = prompt_data.get('prompt') or prompt_data.get('prompt_text') or prompt_text
                severity_value = prompt_data.get('severity') or severity
                
                # Create local prompt in database
                local_prompt_data = {
                    'id': prompt_id,
                    'attack_technique': attack_technique_value,
                    'vuln_category': vuln_category_value,
                    'vuln_subcategory': vuln_subcategory_value,
                    'owasp_top10_llm_mapping': prompt_data.get('owasp_top10_llm_mapping', []),
                    'severity': severity_value,
                    'prompt': prompt_text_value,
                    'collection_id': prompt_data.get('collection_id'),
                    'mitreatlasmapping': prompt_data.get('mitreatlasmapping', [])
                }
                
                result = self.create_local_prompt(local_prompt_data)
                if result:
                    logger.info(f"Created prompt: {prompt_id}")
                    return prompt_id
                else:
                    raise AvenlisError(f"Failed to create prompt: {prompt_id} {vuln_category_value} {vuln_subcategory_value}")
            else:
                # Old API - create in master prompts table
                name = prompt_data  # first parameter is name in old API
                with self.get_db_session() as db:
                    # Check if prompt already exists (by text content)
                    existing = db.query(Prompt).filter(Prompt.prompt_text == prompt_text).first()
                    if existing:
                        logger.info(f"Prompt already exists with ID {existing.id}: {name}")
                        return existing.id
                    
                    # Create new prompt with auto-generated database ID
                    prompt = Prompt(
                        prompt_text=prompt_text,
                        attack_technique=attack_technique,
                        vuln_category=vuln_category,
                        vuln_subcategory=vuln_subcategory,
                        severity=severity,
                        expected_behavior=expected_behavior,
                        source_file=source_file
                    )
                    
                    db.add(prompt)
                    db.commit()
                    db.refresh(prompt)
                    
                    logger.info(f"Created prompt with auto-generated ID {prompt.id}: {name}")
                    return prompt.id
                    
        except Exception as e:
            logger.error(f"Failed to create prompt: {e}")
            raise AvenlisError(f"Failed to create prompt: {e}")
    
    def get_prompt_by_id(self, prompt_id: int) -> Optional[Dict[str, Any]]:
        """Get a prompt by its auto-generated database ID."""
        try:
            with self.get_db_session() as db:
                prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
                if not prompt:
                    return None
                return prompt.to_dict()
        except Exception as e:
            logger.error(f"Failed to get prompt {prompt_id}: {e}")
            return None
    
    # CLI-compatible methods for hybrid storage
    def get_prompt(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """Get a prompt by ID from hybrid storage."""
        try:
            # First try to get from all prompts (includes YAML and local)
            all_prompts = self.get_all_prompts()
            for prompt in all_prompts:
                if str(prompt.get('id')) == str(prompt_id):
                    return prompt
            return None
        except Exception as e:
            logger.error(f"Failed to get prompt {prompt_id}: {e}")
            return None
    
    def get_prompts(self, category: Optional[str] = None, subcategory: Optional[str] = None, technique: Optional[str] = None, 
                   search: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get prompts with filtering from hybrid storage."""
        try:
            all_prompts = self.get_all_prompts()
            
            # Apply filters
            filtered_prompts = all_prompts
            
            if category:
                filtered_prompts = [
                    p for p in filtered_prompts 
                    if (p.get('vuln_category') or '').lower() == category.lower() or 
                       (p.get('category') or '').lower() == category.lower()
                ]
            
            if subcategory:
                filtered_prompts = [
                    p for p in filtered_prompts 
                    if (p.get('vuln_subcategory') or '').lower() == subcategory.lower() or 
                       (p.get('subcategory') or '').lower() == subcategory.lower()
                ]
            
            if technique:
                filtered_prompts = [
                    p for p in filtered_prompts 
                    if p.get('attack_technique', '').lower() == technique.lower()
                ]
            
            if search:
                search_lower = search.lower()
                filtered_prompts = [
                    p for p in filtered_prompts 
                    if search_lower in p.get('prompt', '').lower() or 
                       search_lower in p.get('attack_technique', '').lower() or
                       search_lower in p.get('vuln_category', '').lower()
                ]
            
            if limit:
                filtered_prompts = filtered_prompts[:limit]
            
            return filtered_prompts
            
        except Exception as e:
            logger.error(f"Failed to get prompts: {e}")
            return []
    
    def update_prompt(self, prompt_id: str, prompt_data: Dict[str, Any]) -> bool:
        """Update a prompt in the hybrid storage system (handles both local and YAML prompts)."""
        try:
            # First check if it's a YAML prompt
            from sandstrike.storage.yaml_loader import yaml_loader
            yaml_prompts = yaml_loader.load_prompts()
            yaml_prompt = next((p for p in yaml_prompts if p.get('id') == prompt_id), None)
            
            if yaml_prompt:
                # Update YAML prompt
                return self.update_yaml_prompt(prompt_id=prompt_id, prompt_data=prompt_data)
            
            # Try to update local prompt
            with self.get_db_session() as db:
                local_prompt = db.query(Prompt).filter(
                    Prompt.id == prompt_id
                ).first()
                
                if local_prompt:
                    # Update local prompt
                    if 'attack_technique' in prompt_data:
                        local_prompt.attack_technique = prompt_data['attack_technique']
                    if 'vuln_category' in prompt_data:
                        local_prompt.vuln_category = prompt_data['vuln_category']
                    if 'vuln_subcategory' in prompt_data:
                        local_prompt.vuln_subcategory = prompt_data['vuln_subcategory']
                    if 'severity' in prompt_data:
                        local_prompt.severity = prompt_data['severity']
                    if 'prompt' in prompt_data:
                        local_prompt.prompt = prompt_data['prompt']
                    if 'collection_id' in prompt_data:
                        local_prompt.collection_id = prompt_data['collection_id']
                    if 'owasp_top10_llm_mapping' in prompt_data:
                        local_prompt.owasp_top10_llm_mapping = json.dumps(prompt_data['owasp_top10_llm_mapping'])
                    
                    local_prompt.updated_at = func.now()
                    db.commit()
                    logger.info(f"Updated local prompt: {prompt_id}")
                    return True
                
                # Prompt not found
                logger.warning(f"Prompt {prompt_id} not found in local or YAML storage")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update prompt {prompt_id}: {e}")
            return False
    
    def delete_prompt(self, prompt_id: str) -> bool:
        """Delete a prompt from local storage."""
        try:
            with self.get_db_session() as db:
                local_prompt = db.query(Prompt).filter(
                    Prompt.id == prompt_id
                ).first()
                
                if local_prompt:
                    db.delete(local_prompt)
                    db.commit()
                    logger.info(f"Deleted local prompt: {prompt_id}")
                    return True
                
                logger.warning(f"Prompt {prompt_id} not found in local storage (YAML prompts are read-only)")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete prompt {prompt_id}: {e}")
            return False
    
    # CLI-compatible session methods
    def get_sessions(self, status: Optional[str] = None, target: Optional[str] = None, 
                    limit: int = 50) -> List[Dict[str, Any]]:
        """Get sessions with filtering from hybrid storage."""
        try:
            all_sessions = self.get_combined_sessions()
            
            # Apply filters
            filtered_sessions = all_sessions
            
            if status:
                filtered_sessions = [
                    s for s in filtered_sessions 
                    if s.get('status', '').lower() == status.lower()
                ]
            
            if target:
                filtered_sessions = [
                    s for s in filtered_sessions 
                    if target.lower() in s.get('target_url', '').lower() or
                       target.lower() in s.get('target', '').lower()
                ]
            
            if limit:
                filtered_sessions = filtered_sessions[:limit]
            
            return filtered_sessions
            
        except Exception as e:
            logger.error(f"Failed to get sessions: {e}")
            return []
    
    def get_session(self, session_id: str, include_results: bool = False) -> Optional[Dict[str, Any]]:
        """Get a session by ID from hybrid storage."""
        try:
            session_data = self.get_combined_session(session_id)
            if session_data:
                if include_results:
                    return session_data  # Already includes results
                else:
                    return session_data.get('session')
            return None
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None
    
    def delete_session_by_id(self, session_id: str) -> bool:
        """Delete a session from hybrid storage."""
        try:
            # Try to delete from file storage first
            if self.delete_file_session(session_id):
                return True
            
            # Try to delete from rapid scan database
            try:
                from .storage.database import database
                rapid_manager = database.rapid_scan_manager if hasattr(database, 'rapid_scan_manager') else None
                if rapid_manager and rapid_manager.delete_rapid_scan(session_id):
                    return True
            except Exception as e:
                logger.debug(f"Error checking rapid scan for deletion: {e}")
            
            # Try to delete from local database
            try:
                return super().delete_session(session_id)  # Call parent method
            except Exception:
                pass
            
            logger.warning(f"Session {session_id} not found in any storage")
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    # CLI-compatible collection methods  
    def get_collection(self, collection_id: Union[int, str], include_prompts: bool = True) -> Optional[Dict[str, Any]]:
        """Get a collection by ID from hybrid storage."""
        try:
            if isinstance(collection_id, str):
                # Try combined collections (YAML + local)
                collection_data = self.get_combined_collection(collection_id)
                if collection_data:
                    if include_prompts:
                        return collection_data  # Already includes prompts
                    else:
                        return collection_data.get('collection')
            else:
                # Integer ID - use parent method for database collections
                return super().get_collection(collection_id, include_prompts)
            
            return None
        except Exception as e:
            logger.error(f"Failed to get collection {collection_id}: {e}")
            return None

    def get_all_prompts(self) -> List[Dict[str, Any]]:
        """Get all prompts, combining YAML files, local storage, and JSON fallback."""
        try:
            all_prompts = []
            
            # 1. Load from YAML files (team-shareable)
            from sandstrike.storage.yaml_loader import yaml_loader
            yaml_prompts = yaml_loader.load_adversarial_prompts()
            all_prompts.extend(yaml_prompts)
            
            # 2. Load from local storage (user-specific)
            local_prompts = self.get_all_local_prompts()
            all_prompts.extend(local_prompts)
            
            # 3. Fallback to old JSON files if no YAML/local data found
            if not all_prompts:
                logger.info("No YAML/local prompts found, falling back to JSON files...")
                current_dir = Path(__file__).parent
                data_dir = current_dir / 'redteam' / 'data'
                
                if data_dir.exists():
                    data_files = [
                        'adversarial_prompts.json',
                        'attack_templates.json', 
                        'simple_test.json',
                        'evaluation_patterns.json'
                    ]
                    
                    for file_name in data_files:
                        file_path = data_dir / file_name
                        if file_path.exists():
                            json_prompts = self._load_json_prompts(str(file_path))
                            # Mark JSON prompts with source
                            for prompt in json_prompts:
                                prompt['source'] = 'file'
                                prompt['source_file'] = str(file_path)
                            all_prompts.extend(json_prompts)
            
            return all_prompts
            
        except Exception as e:
            logger.error(f"Failed to get prompts: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []
    
    def _load_json_prompts(self, file_path: str) -> List[Dict[str, Any]]:
        """Load prompts from JSON file without storing in database."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            prompts = []
            if isinstance(data, list):
                # Direct list of prompts
                for i, prompt_data in enumerate(data):
                    if isinstance(prompt_data, dict):
                        # Add auto-generated ID if not present
                        if 'id' not in prompt_data:
                            prompt_data['id'] = i + 1
                        prompts.append(prompt_data)
            elif isinstance(data, dict):
                # Dict with categories or single prompt
                if 'prompt' in data:
                    # Single prompt file
                    if 'id' not in data:
                        data['id'] = 1
                    prompts.append(data)
                else:
                    # Dict with categories
                    id_counter = 1
                    for category, items in data.items():
                        if isinstance(items, list):
                            for prompt_data in items:
                                if isinstance(prompt_data, dict):
                                    prompt_data['category'] = prompt_data.get('category', category)
                                    if 'id' not in prompt_data:
                                        prompt_data['id'] = id_counter
                                        id_counter += 1
                                    prompts.append(prompt_data)
            
            return prompts
        except Exception as e:
            logger.error(f"Failed to load JSON prompts from {file_path}: {e}")
            return []
    
    # New methods for handling local storage with YAML-like structure
    
    def get_all_local_prompts(self) -> List[Dict[str, Any]]:
        """Get all local adversarial prompts."""
        try:
            with self.get_db_session() as db:
                prompts = db.query(Prompt).all()
                return [prompt.to_dict() for prompt in prompts]
        except Exception as e:
            logger.error(f"Failed to get local prompts: {e}")
            return []
    
    def create_local_prompt(self, prompt_data: Dict[str, Any]) -> Optional[str]:
        """Create a local adversarial prompt."""
        try:
            with self.get_db_session() as db:
                prompt = Prompt(
                    id=prompt_data['id'],
                    attack_technique=prompt_data['attack_technique'],
                    vuln_category=prompt_data['vuln_category'],
                    vuln_subcategory=prompt_data.get('vuln_subcategory'),
                    owasp_top10_llm_mapping=json.dumps(prompt_data.get('owasp_top10_llm_mapping', [])),
                    mitreatlasmapping=json.dumps(prompt_data.get('mitreatlasmapping', [])) if prompt_data.get('mitreatlasmapping') else None,
                    severity=prompt_data['severity'],
                    prompt=prompt_data['prompt'],
                    collection_id=prompt_data.get('collection_id')
                )
                db.add(prompt)
                db.commit()
                logger.info(f"Created local prompt: {prompt_data['id']}")
                return prompt_data['id']
        except Exception as e:
            logger.error(f"Failed to create local prompt: {e}")
            return None
    
    def get_all_local_collections(self) -> List[Dict[str, Any]]:
        """Get all local collections."""
        try:
            with self.get_db_session() as db:
                collections = db.query(PromptCollection).all()
                return [collection.to_dict() for collection in collections]
        except Exception as e:
            logger.error(f"Failed to get local collections: {e}")
            return []
    
    def create_yaml_collection(self, name: str, description: str = None, prompt_ids: Optional[List[str]] = None, collection_id: Optional[str] = None) -> str:
        """Create a new collection in collections.yaml file."""
        try:
            from datetime import datetime
            import yaml
            import os
            from pathlib import Path
            
            current_time = datetime.now().isoformat() + 'Z'
            # Generate collection ID if not provided
            if not collection_id:
                collection_id = f"collection_{int(datetime.now().timestamp())}"
            
            # Load existing collections from collections.yaml
            data_dir = Path(__file__).parent / 'data'
            yaml_path = data_dir / 'collections.yaml'
            collections_list = []
            
            if yaml_path.exists():
                with open(yaml_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f) or {}
                    collections_list = data.get('collections', [])
                    if not isinstance(collections_list, list):
                        collections_list = []
            
            # Create new collection matching the exact schema from collections.yaml
            # Order: id, name, description, prompt_ids, date_updated
            # Filter out empty, null, or whitespace-only prompt IDs
            if prompt_ids:
                filtered_prompt_ids = [pid for pid in prompt_ids if pid and str(pid).strip()]
            else:
                filtered_prompt_ids = []
            new_collection = {
                'id': collection_id,
                'name': name,
                'description': description or '',
                'prompt_ids': filtered_prompt_ids,
                'date_updated': current_time
            }
            
            # Add to list
            collections_list.append(new_collection)
            
            # Custom representer to ensure lists always use dash format (block style)
            def represent_list(dumper, data):
                # Always use block style (dashes) for lists, never flow style (square brackets)
                return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=False)
            
            # Custom representer for None values to show as blank dashes
            def represent_none(dumper, data):
                return dumper.represent_scalar('tag:yaml.org,2002:null', '')
            
            # Register the custom representers
            yaml.add_representer(list, represent_list, Dumper=yaml.SafeDumper)
            yaml.add_representer(type(None), represent_none, Dumper=yaml.SafeDumper)
            
            # Save back to YAML with correct structure matching the schema
            with open(yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump({'collections': collections_list}, f, Dumper=yaml.SafeDumper, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
            logger.info(f"Created YAML collection: {collection_id} in collections.yaml")
            return collection_id
            
        except Exception as e:
            logger.error(f"Error creating YAML collection: {e}")
            raise
    
    def update_yaml_collection(self, collection_id: str, name: str = None, 
                              description: str = None, prompt_ids: List[str] = None) -> bool:
        """Update a YAML collection."""
        try:
            from datetime import datetime
            import yaml
            import os
            from pathlib import Path
            
            current_time = datetime.now().isoformat() + 'Z'
            
            # Get the collections YAML file path
            data_dir = Path(__file__).parent / 'data'
            yaml_path = data_dir / 'collections.yaml'
            
            # Load existing collections
            collections = {}
            if yaml_path.exists():
                with open(yaml_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f) or {}
                    collections = data.get('collections', [])
            
            # Find the collection to update
            collection_found = False
            for i, collection in enumerate(collections):
                if collection.get('id') == collection_id:
                    collection_found = True
                    # Update the collection fields
                    if name is not None:
                        collection['name'] = name
                    if description is not None:
                        collection['description'] = description
                    if prompt_ids is not None:
                        # Filter out empty, null, or whitespace-only prompt IDs
                        filtered_prompt_ids = [pid for pid in prompt_ids if pid and str(pid).strip()]
                        collection['prompt_ids'] = filtered_prompt_ids
                    collection['date_updated'] = current_time
                    
                    # Recreate collection in correct field order: id, name, description, prompt_ids, date_updated
                    collections[i] = {
                        'id': collection['id'],
                        'name': collection['name'],
                        'description': collection.get('description', ''),
                        'prompt_ids': collection.get('prompt_ids', []),
                        'date_updated': collection['date_updated']
                    }
                    break
            
            if not collection_found:
                return False
            
            # Custom representer to ensure lists always use dash format (block style)
            def represent_list(dumper, data):
                return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=False)
            
            # Custom representer for None values to show as blank dashes
            def represent_none(dumper, data):
                return dumper.represent_scalar('tag:yaml.org,2002:null', '')
            
            # Register the custom representers
            yaml.add_representer(list, represent_list, Dumper=yaml.SafeDumper)
            yaml.add_representer(type(None), represent_none, Dumper=yaml.SafeDumper)
            
            # Save back to YAML
            with open(yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump({'collections': collections}, f, Dumper=yaml.SafeDumper, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
            logger.info(f"Updated YAML collection: {collection_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating YAML collection: {e}")
            return False
    
    def delete_yaml_collection(self, collection_id: str) -> bool:
        """Delete a collection from collections.yaml file."""
        try:
            import yaml
            from pathlib import Path
            
            # Get the collections YAML file path
            data_dir = Path(__file__).parent / 'data'
            yaml_path = data_dir / 'collections.yaml'
            
            if not yaml_path.exists():
                return False
            
            # Load existing collections
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
                collections = data.get('collections', [])
            
            # Remove the collection
            original_count = len(collections)
            collections = [c for c in collections if c.get('id') != collection_id]
            
            if len(collections) == original_count:
                return False  # Collection not found
            
            # Custom representer to ensure lists always use dash format (block style)
            def represent_list(dumper, data):
                return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=False)
            
            # Custom representer for None values to show as blank dashes
            def represent_none(dumper, data):
                return dumper.represent_scalar('tag:yaml.org,2002:null', '')
            
            # Register the custom representers
            yaml.add_representer(list, represent_list, Dumper=yaml.SafeDumper)
            yaml.add_representer(type(None), represent_none, Dumper=yaml.SafeDumper)
            
            # Save back to YAML
            with open(yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump({'collections': collections}, f, Dumper=yaml.SafeDumper, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
            logger.info(f"Deleted YAML collection: {collection_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting YAML collection: {e}")
            return False
    
    def update_yaml_prompt(self, prompt_id: str, prompt_data: Dict[str, Any]) -> bool:
        """Update a YAML prompt."""
        try:
            from datetime import datetime
            import yaml
            from pathlib import Path
            
            current_time = datetime.now().isoformat() + 'Z'
            
            # Get the prompts YAML file path
            data_dir = Path(__file__).parent / 'data'
            yaml_path = data_dir / 'adversarial_prompts.yaml'
            
            # Load existing prompts
            prompts = {}
            if yaml_path.exists():
                with open(yaml_path, 'r', encoding='utf-8') as f:
                    prompts = yaml.safe_load(f) or {}
            
            # Find and update the prompt
            if prompt_id not in prompts:
                logger.warning(f"Prompt {prompt_id} not found in YAML file")
                return False
            
            # Update the prompt fields
            if 'attack_technique' in prompt_data:
                prompts[prompt_id]['attack_technique'] = prompt_data['attack_technique']
            if 'prompt' in prompt_data:
                prompts[prompt_id]['prompt'] = prompt_data['prompt']
            if 'vuln_category' in prompt_data:
                prompts[prompt_id]['vuln_category'] = prompt_data['vuln_category']
            if 'vuln_subcategory' in prompt_data:
                prompts[prompt_id]['vuln_subcategory'] = prompt_data['vuln_subcategory']
            if 'severity' in prompt_data:
                prompts[prompt_id]['severity'] = prompt_data['severity']
            
            prompts[prompt_id]['date_updated'] = current_time
            
            # Save back to YAML
            with open(yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(prompts, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"Updated YAML prompt: {prompt_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating YAML prompt: {e}")
            return False
    
    def delete_yaml_prompt(self, prompt_id: str, source_file: str = None) -> bool:
        """Delete a prompt from a YAML file."""
        try:
            import yaml
            from pathlib import Path
            
            # Determine which file to modify
            if source_file:
                # Use the source file from the prompt
                data_dir = Path(__file__).parent / 'data'
                yaml_path = data_dir / 'prompts' / source_file
                if not yaml_path.exists():
                    # Try the old location
                    yaml_path = data_dir / source_file
            else:
                # Default to adversarial_prompts.yaml in data directory
                data_dir = Path(__file__).parent / 'data'
                yaml_path = data_dir / 'adversarial_prompts.yaml'
            
            if not yaml_path.exists():
                logger.warning(f"YAML file not found: {yaml_path}")
                return False
            
            # Load existing prompts
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            
            # Handle two possible YAML structures:
            # 1. Dictionary format: {prompt_id: {...}}
            # 2. List format: {prompts: [{id: prompt_id, ...}, ...]}
            
            deleted = False
            original_count = 0
            
            # Try dictionary format first (adversarial_prompts.yaml)
            if prompt_id in data:
                del data[prompt_id]
                deleted = True
            # Try list format (prompts/*.yaml)
            elif 'prompts' in data and isinstance(data['prompts'], list):
                original_count = len(data['prompts'])
                data['prompts'] = [p for p in data['prompts'] if p.get('id') != prompt_id]
                if len(data['prompts']) < original_count:
                    deleted = True
            
            if not deleted:
                logger.warning(f"Prompt {prompt_id} not found in YAML file {yaml_path}")
                return False
            
            # Save back to YAML
            with open(yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
            logger.info(f"Deleted YAML prompt: {prompt_id} from {yaml_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting YAML prompt: {e}")
            return False
    
    def create_yaml_prompt(self, prompt_id: str = None, attack_technique: str = None, 
                          prompt: str = None, vuln_category: str = None, 
                          vuln_subcategory: str = None, severity: str = 'Medium',
                          collection_id: str = None, mitreatlasmapping: List[str] = None,
                          owasp_top10_llm_mapping: List[str] = None,
                          target_file: str = None) -> str:
        """Create a new prompt in YAML file."""
        try:
            from datetime import datetime
            import yaml
            import os
            
            # Generate prompt ID if not provided
            if not prompt_id:
                prompt_id = f"prompt_{int(datetime.now().timestamp())}"
            
            # Determine target file
            data_dir = Path(__file__).parent / 'data'
            if target_file:
                # Use specified target file - prefer prompts subdirectory
                # Check if file exists in prompts directory first
                prompts_path = data_dir / 'prompts' / target_file
                data_path = data_dir / target_file
                if prompts_path.exists():
                    yaml_path = prompts_path
                elif data_path.exists():
                    yaml_path = data_path
                else:
                    # File doesn't exist yet, create in prompts directory
                    yaml_path = prompts_path
            else:
                # Default to adversarial_prompts.yaml in prompts directory
                prompts_path = data_dir / 'prompts' / 'adversarial_prompts.yaml'
                data_path = data_dir / 'adversarial_prompts.yaml'
                if prompts_path.exists():
                    yaml_path = prompts_path
                elif data_path.exists():
                    yaml_path = data_path
                else:
                    # File doesn't exist yet, create in prompts directory
                    yaml_path = prompts_path
            
            # Ensure directory exists
            yaml_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Load existing prompts - structure is {'prompts': [list of prompts]}
            # For new files, start with empty dict that will be initialized with 'prompts' key
            yaml_data = {}
            
            if yaml_path.exists():
                with open(yaml_path, 'r', encoding='utf-8') as f:
                    yaml_data = yaml.safe_load(f) or {}
            
            # Ensure prompts key exists and is a list
            # New files will always start with 'prompts:' as the root key
            if 'prompts' not in yaml_data:
                yaml_data['prompts'] = []
            elif not isinstance(yaml_data['prompts'], list):
                # Convert old dict format to list format
                yaml_data['prompts'] = list(yaml_data['prompts'].values())
            
            # Check if prompt with this ID already exists
            existing_index = None
            for i, p in enumerate(yaml_data['prompts']):
                if isinstance(p, dict) and p.get('id') == prompt_id:
                    existing_index = i
                    break
            
            # Create new prompt object matching the schema
            # Field order: id, attack_technique, vuln_category, vuln_subcategory, owasp mapping, mitre mapping, severity (3rd last), prompt (2nd last), collection_id (last)
            # For empty mappings, use list with 2 None values to create blank - entries in YAML
            owasp_mapping = owasp_top10_llm_mapping if owasp_top10_llm_mapping else [None, None]
            mitre_mapping = mitreatlasmapping if mitreatlasmapping else [None, None]
            
            new_prompt = {
                'id': prompt_id,
                'attack_technique': attack_technique,
                'vuln_category': vuln_category or '',
                'vuln_subcategory': vuln_subcategory or '',
                'owasp_top10_llm_mapping': owasp_mapping,
                'mitreatlasmapping': mitre_mapping,
                'severity': severity.lower() if severity else 'medium',
                'prompt': prompt,
                'collection_id': collection_id or ''
            }
            
            # Update existing or add new
            if existing_index is not None:
                yaml_data['prompts'][existing_index] = new_prompt
            else:
                yaml_data['prompts'].append(new_prompt)
            
            # Custom YAML representers for proper formatting
            def represent_list(dumper, data):
                # Always use block style (dashes) for lists, never flow style (square brackets)
                return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=False)
            
            # Custom representer for None values to show as blank dashes
            def represent_none(dumper, data):
                return dumper.represent_scalar('tag:yaml.org,2002:null', '')
            
            # Register the custom representers
            yaml.add_representer(list, represent_list, Dumper=yaml.SafeDumper)
            yaml.add_representer(type(None), represent_none, Dumper=yaml.SafeDumper)
            
            # Save back to YAML
            with open(yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(yaml_data, f, Dumper=yaml.SafeDumper, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
            logger.info(f"Created YAML prompt: {prompt_id}")
            return prompt_id
            
        except Exception as e:
            logger.error(f"Error creating YAML prompt: {e}")
            raise
    
    def create_local_collection(self, collection_data: Dict[str, Any]) -> Optional[str]:
        """Create a local collection."""
        try:
            from datetime import datetime
            current_time = datetime.now().isoformat() + 'Z'
            
            with self.get_db_session() as db:
                collection = PromptCollection(
                    id=collection_data['id'],
                    name=collection_data['name'],
                    description=collection_data.get('description'),
                    prompt_ids=json.dumps(collection_data.get('prompts', [])),
                    date_updated=collection_data.get('date_updated', current_time)
                )
                db.add(collection)
                db.commit()
                logger.info(f"Created local collection: {collection_data['id']}")
                return collection_data['id']
        except Exception as e:
            logger.error(f"Failed to create local collection: {e}")
            return None
    
    # Note: LocalAttackType, LocalVulnerabilityCategory, and LocalSessionConfig tables were removed.
    # These methods are kept for API compatibility but return empty results.
    # For persistent storage of these entities, consider using YAML files or re-implementing the tables.
    
    def get_all_local_attack_types(self) -> List[Dict[str, Any]]:
        """Get all local attack types (deprecated - table was removed, returns empty list)."""
        logger.warning("get_all_local_attack_types is deprecated - LocalAttackType table was removed")
        return []
    
    def create_local_attack_type(self, attack_data: Dict[str, Any]) -> Optional[str]:
        """Create a local attack type (deprecated - table was removed, returns None)."""
        logger.warning("create_local_attack_type is deprecated - LocalAttackType table was removed")
        return None
    
    def get_all_local_vulnerability_categories(self) -> List[Dict[str, Any]]:
        """Get all local vulnerability categories (deprecated - table was removed, returns empty list)."""
        logger.warning("get_all_local_vulnerability_categories is deprecated - LocalVulnerabilityCategory table was removed")
        return []
    
    def create_local_vulnerability_category(self, category_data: Dict[str, Any]) -> Optional[str]:
        """Create a local vulnerability category (deprecated - table was removed, returns None)."""
        logger.warning("create_local_vulnerability_category is deprecated - LocalVulnerabilityCategory table was removed")
        return None
    
    def get_all_local_session_configs(self) -> List[Dict[str, Any]]:
        """Get all local session configurations (deprecated - table was removed, returns empty list)."""
        logger.warning("get_all_local_session_configs is deprecated - LocalSessionConfig table was removed")
        return []
    
    def create_local_session_config(self, config_data: Dict[str, Any]) -> Optional[str]:
        """Create a local session configuration (deprecated - table was removed, returns None)."""
        logger.warning("create_local_session_config is deprecated - LocalSessionConfig table was removed")
        return None
    
    def get_combined_collections(self) -> List[Dict[str, Any]]:
        """Get collections from both YAML files and local storage."""
        try:
            all_collections = []
            
            # Load from YAML files
            from sandstrike.storage.yaml_loader import yaml_loader
            yaml_collections = yaml_loader.load_collections()
            for collection in yaml_collections:
                collection['source'] = 'file'  # Mark as file collection
                all_collections.append(collection)
            
            # Load from local storage
            local_collections = self.get_all_local_collections()
            for collection in local_collections:
                collection['source'] = 'local'  # Mark as local collection
                all_collections.append(collection)
            
            return all_collections
            
        except Exception as e:
            logger.error(f"Failed to get combined collections: {e}")
            return []
    
    def get_combined_collection(self, collection_id: str) -> Optional[Dict[str, Any]]:
        """Get a collection from both YAML files and local storage by ID."""
        try:
            # First try YAML collections
            from .storage.yaml_loader import YAMLLoader
            yaml_loader = YAMLLoader()
            yaml_collections = yaml_loader.load_collections()
            for collection in yaml_collections:
                if collection.get('id') == collection_id:
                    # Get prompts for this collection
                    prompts = self.get_all_prompts()
                    # Handle new prompt_ids format vs old embedded prompts format
                    if 'prompt_ids' in collection:
                        # New format: filter prompts by the prompt_ids list
                        prompt_ids = collection['prompt_ids']
                        # Filter out blank/empty/null prompt IDs before matching
                        valid_prompt_ids = [pid for pid in prompt_ids if pid and str(pid).strip()]
                        collection_prompts = [p for p in prompts if p.get('id') in valid_prompt_ids]
                        logger.info(f"Collection {collection_id} uses prompt_ids format: {len(collection_prompts)} prompts matched from {len(valid_prompt_ids)} valid IDs (filtered from {len(prompt_ids)} total)")
                    else:
                        # Old format: filter by collection_id field in prompts
                        collection_prompts = [p for p in prompts if p.get('collection_id') == collection_id]
                        logger.info(f"Collection {collection_id} uses collection_id format: {len(collection_prompts)} prompts matched")
                    
                    collection['type'] = 'yaml'  # Mark as YAML collection
                    return {
                        'collection': collection,
                        'prompts': collection_prompts
                    }
            
            # Then try local collections
            local_collections = self.get_all_local_collections()
            for collection in local_collections:
                if collection.get('id') == collection_id:
                    # Get prompts for this collection
                    prompts = self.get_all_prompts()
                    # Handle new prompt_ids format vs old collection_id format
                    if 'prompt_ids' in collection and collection['prompt_ids']:
                        # New format: filter prompts by the prompt_ids list
                        prompt_ids = collection['prompt_ids']
                        # Filter out blank/empty/null prompt IDs before matching
                        valid_prompt_ids = [pid for pid in prompt_ids if pid and str(pid).strip()]
                        collection_prompts = [p for p in prompts if p.get('id') in valid_prompt_ids]
                        logger.info(f"Local collection {collection_id} uses prompt_ids format: {len(collection_prompts)} prompts matched from {len(valid_prompt_ids)} valid IDs (filtered from {len(prompt_ids)} total)")
                    else:
                        # Old format: filter by collection_id field in prompts
                        collection_prompts = [p for p in prompts if p.get('collection_id') == collection_id]
                        logger.info(f"Local collection {collection_id} uses collection_id format: {len(collection_prompts)} prompts matched")
                    collection['type'] = 'local'  # Mark as local collection
                    return {
                        'collection': collection,
                        'prompts': collection_prompts
                    }
            
            # Finally try integer ID for legacy database collections
            try:
                int_id = int(collection_id)
                collection = self.get_collection(int_id)
                if collection:
                    prompts = self.get_collection_prompts(int_id)
                    collection['type'] = 'local'  # Mark as local collection
                    return {
                        'collection': collection,
                        'prompts': prompts or []
                    }
            except (ValueError, TypeError):
                pass  # Not an integer ID
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get combined collection {collection_id}: {e}")
            return None

    def get_grading_intents(self) -> Dict[str, Dict[str, str]]:
        """Get grading intents from YAML file."""
        try:
            from sandstrike.storage.yaml_loader import yaml_loader
            return yaml_loader.load_grading_intents()
        except Exception as e:
            logger.error(f"Failed to get grading intents: {e}")
            return {}

    def get_combined_sessions(self) -> List[Dict[str, Any]]:
        """Get sessions/scan results from both JSON files and local storage."""
        try:
            all_sessions = []
            seen_session_ids = set()
            
            # Load from JSON files first (higher priority)
            from .storage.yaml_loader import YAMLLoader
            json_loader = YAMLLoader()
            json_sessions = json_loader.load_scan_results()
            for session in json_sessions:
                session_id = session.get('id')
                if session_id and session_id not in seen_session_ids:
                    # Normalize field names for JSON sessions
                    normalized_session = session.copy()
                    
                    # Map started_at to created_at for consistency
                    if 'started_at' in normalized_session and 'created_at' not in normalized_session:
                        normalized_session['created_at'] = normalized_session['started_at']
                    
                    # Map session_name to name for consistency
                    if 'session_name' in normalized_session and 'name' not in normalized_session:
                        normalized_session['name'] = normalized_session['session_name']
                    
                    # Map target to target_url for consistency
                    if 'target' in normalized_session and 'target_url' not in normalized_session:
                        normalized_session['target_url'] = normalized_session['target']
                    
                    # Set source to 'file' for JSON sessions
                    normalized_session['source'] = 'file'
                    
                    all_sessions.append(normalized_session)
                    seen_session_ids.add(session_id)
                    logger.debug(f"Added file session: {session_id}")
            
            # Load from rapid scan database

            try:
                from .storage.database import database
                rapid_manager = database.rapid_scan_manager if hasattr(database, 'rapid_scan_manager') else None
                if rapid_manager:
                    rapid_scans = rapid_manager.list_rapid_scans(limit=100)
                    for scan in rapid_scans:
                        session_id = scan.get('id')
                        if session_id and session_id not in seen_session_ids:
                            # Convert rapid scan format to match expected format
                            session_data = {
                                'id': scan['id'],
                                'name': scan['name'],
                                'target': scan['target'],
                                'status': scan['status'],
                                'created_at': scan['created_at'],
                                'updated_at': scan['updated_at'],
                                'duration_seconds': scan.get('duration_seconds'),
                                'total_tests': scan.get('total_prompts', 0),
                                'vulnerabilities_found': scan.get('successful_attacks', 0),
                                'success_rate': (scan.get('successful_attacks', 0) / max(scan.get('total_prompts', 1), 1)) * 100,
                                'source': 'local'
                            }
                            all_sessions.append(session_data)
                            seen_session_ids.add(session_id)
                            logger.debug(f"Added rapid scan session: {session_id}")
            except Exception as e:
                logger.debug(f"Error loading rapid scans: {e}")
                pass
            
            # Load from local storage (skip duplicates)
            local_sessions = self.get_all_sessions()
            for session in local_sessions:
                # Preserve original source; older versions stored full scans in DB with source='file'
                # which should not be shown as an additional "local" session alongside file sessions.
                db_source = session.get('source') or 'local'
                if db_source == 'file':
                    continue
                session['source'] = db_source
                session_id = session.get('id') or str(session.get('name', ''))
                if session_id and session_id not in seen_session_ids:
                    all_sessions.append(session)
                    seen_session_ids.add(session_id)
                    logger.debug(f"Added local session: {session_id}")
                else:
                    logger.debug(f"Skipped duplicate session: {session_id}")
            
            # Sort by creation date (newest first)
            from datetime import datetime
            def get_sort_key(session):
                created_at = session.get('created_at', '')
                if isinstance(created_at, str) and created_at:
                    try:
                        # Parse the datetime and make it timezone-aware
                        dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        return dt.timestamp()
                    except:
                        return 0
                return 0
            
            all_sessions.sort(key=get_sort_key, reverse=True)
            
            return all_sessions
            
        except Exception as e:
            logger.error(f"Failed to get combined sessions: {e}")
            return []
    
    def get_combined_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a session from both file and database sources by ID."""
        try:
            # First try file-based sessions
            from .storage.yaml_loader import YAMLLoader
            yaml_loader = YAMLLoader()
            file_sessions = yaml_loader.load_scan_results()
            for session in file_sessions:
                if session.get('id') == session_id:
                    # Normalize field names for JSON sessions
                    normalized_session = session.copy()
                    
                    # Map started_at to created_at for consistency
                    if 'started_at' in normalized_session and 'created_at' not in normalized_session:
                        normalized_session['created_at'] = normalized_session['started_at']
                    
                    # Map session_name to name for consistency
                    if 'session_name' in normalized_session and 'name' not in normalized_session:
                        normalized_session['name'] = normalized_session['session_name']
                    
                    # Map target to target_url for consistency
                    if 'target' in normalized_session and 'target_url' not in normalized_session:
                        normalized_session['target_url'] = normalized_session['target']
                    
                    # For file sessions, include the results directly
                    return {
                        'session': normalized_session,
                        'results': normalized_session.get('results', [])
                    }
            
            # Then try rapid scan database (string IDs)
            try:
                from .storage.database import database
                rapid_manager = database.rapid_scan_manager if hasattr(database, 'rapid_scan_manager') else None
                if rapid_manager:
                    rapid_scan = rapid_manager.get_rapid_scan(session_id)
                    if rapid_scan:
                        rapid_results = rapid_manager.get_scan_results(session_id)
                        # Convert rapid scan format to match expected format
                        session_data = {
                            'id': rapid_scan['id'],
                            'name': rapid_scan['name'],
                            'target': rapid_scan['target'],
                            'status': rapid_scan['status'],
                            'created_at': rapid_scan['created_at'],
                            'updated_at': rapid_scan['updated_at'],
                            'duration_seconds': rapid_scan.get('duration_seconds'),
                            'total_tests': rapid_scan.get('total_prompts', 0),
                            'vulnerabilities_found': rapid_scan.get('successful_attacks', 0),
                            'success_rate': (rapid_scan.get('successful_attacks', 0) / max(rapid_scan.get('total_prompts', 1), 1)) * 100,
                            'source': 'local'
                        }
                        return {
                            'session': session_data,
                            'results': rapid_results or []
                        }
            except Exception as e:
                logger.debug(f"Error checking rapid scan for {session_id}: {e}")
                pass
            
            # Finally try database sessions (integer IDs)
            try:
                session_data = self.get_session_by_id(session_id)
                if session_data:
                    results = self.get_session_results(session_id)
                    return {
                        'session': session_data,
                        'results': results or []
                    }
            except Exception:
                pass  # Not an integer ID
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get combined session {session_id}: {e}")
            return None

    def delete_file_session(self, session_id: str) -> bool:
        """Delete a session from JSON files by session ID."""
        try:
            from pathlib import Path
            import json
            
            # Look for session JSON files in data directory
            data_dir = Path(__file__).parent / 'data'
            for json_file in data_dir.glob('*sessions*.json'):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Handle different JSON structures
                    sessions_to_process = []
                    if isinstance(data, list):
                        sessions_to_process = data
                        is_direct_list = True
                    elif isinstance(data, dict) and 'scan_results' in data:
                        sessions_to_process = data['scan_results']
                        is_direct_list = False
                    
                    # Find and remove the session
                    original_count = len(sessions_to_process)
                    sessions_to_process[:] = [s for s in sessions_to_process if s.get('id') != session_id]
                    
                    if len(sessions_to_process) < original_count:
                        # Session was found and removed, save the file
                        if is_direct_list:
                            updated_data = sessions_to_process
                        else:
                            data['scan_results'] = sessions_to_process
                            updated_data = data
                        
                        with open(json_file, 'w', encoding='utf-8') as f:
                            json.dump(updated_data, f, indent=2, ensure_ascii=False)
                        
                        logger.info(f"Deleted session {session_id} from {json_file}")
                        return True
                        
                except Exception as e:
                    logger.error(f"Error processing {json_file}: {e}")
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete file session {session_id}: {e}")
            return False

    def cleanup_invalid_sessions(self):
        """Clean up sessions with invalid data like empty names or N/A fields."""
        try:
            with self.get_db_session() as db:
                # Delete sessions with empty or null names
                invalid_sessions = db.query(TestSession).filter(
                    (TestSession.name == '') | 
                    (TestSession.name.is_(None)) |
                    (TestSession.target_url == 'N/A') |
                    (TestSession.target_model == 'N/A')
                ).all()
                
                for session in invalid_sessions:
                    logger.info(f"Deleting invalid session: {session.name} (ID: {session.id})")
                    db.delete(session)
                
                db.commit()
                logger.info(f"Cleaned up {len(invalid_sessions)} invalid sessions")
                
        except Exception as e:
            logger.error(f"Failed to cleanup invalid sessions: {e}")
    
    def wipe_local_data(self):
        """Wipe all local data from the database."""
        try:
            with self.get_db_session() as db:
                db.query(Prompt).delete()
                db.query(PromptCollection).delete()
                db.query(DynamicVariable).delete()
                db.commit()
                logger.info("Wiped all local data from database")
        except Exception as e:
            logger.error(f"Failed to wipe local data: {e}")
            raise
    
    # Dynamic Variables Methods
    def get_dynamic_variables(self) -> Dict[str, Any]:
        """Get all dynamic variables from local storage"""
        try:
            with self.get_db_session() as db:
                variables = db.query(DynamicVariable).all()
                
                result = {'variables': {}}
                for var in variables:
                    category = var.category
                    name = var.name
                    value = var.value
                    
                    if category not in result['variables']:
                        result['variables'][category] = {}
                    result['variables'][category][name] = value
                
                return result
        except Exception as e:
            logger.error(f"Error getting dynamic variables: {e}")
            return {}
    
    def set_dynamic_variable(self, category: str, name: str, value: str, overwrite: bool = True) -> bool:
        """Set a dynamic variable in local storage"""
        try:
            with self.get_db_session() as db:
                # Check if variable exists
                existing = db.query(DynamicVariable).filter(
                    DynamicVariable.category == category,
                    DynamicVariable.name == name
                ).first()
                
                if existing and not overwrite:
                    return False
                
                if existing:
                    # Update existing
                    existing.value = value
                    existing.updated_at = func.now()
                else:
                    # Insert new
                    new_var = DynamicVariable(
                        category=category,
                        name=name,
                        value=value
                    )
                    db.add(new_var)
                
                db.commit()
                return True
        except Exception as e:
            logger.error(f"Error setting dynamic variable: {e}")
            return False
    
    def get_dynamic_variable(self, category: str, name: str) -> Optional[str]:
        """Get a specific dynamic variable"""
        try:
            with self.get_db_session() as db:
                var = db.query(DynamicVariable).filter(
                    DynamicVariable.category == category,
                    DynamicVariable.name == name
                ).first()
                
                return var.value if var else None
        except Exception as e:
            logger.error(f"Error getting dynamic variable: {e}")
            return None
    
    def delete_dynamic_variable(self, category: str, name: str) -> bool:
        """Delete a dynamic variable"""
        try:
            with self.get_db_session() as db:
                var = db.query(DynamicVariable).filter(
                    DynamicVariable.category == category,
                    DynamicVariable.name == name
                ).first()
                
                if var:
                    db.delete(var)
                    db.commit()
                    return True
                return False
        except Exception as e:
            logger.error(f"Error deleting dynamic variable: {e}")
            return False
    
    def clear_dynamic_variables(self) -> bool:
        """Clear all dynamic variables"""
        try:
            with self.get_db_session() as db:
                db.query(DynamicVariable).delete()
                db.commit()
                return True
        except Exception as e:
            logger.error(f"Error clearing dynamic variables: {e}")
            return False
    
    # Target management methods
    
    def create_target(self, target_id: str, name: str, ip_address: str, description: str = None, target_type: str = None, model: str = None) -> str:
        """Create a new target in local database."""
        try:
            with self.get_db_session() as db:
                # Check if target ID already exists
                existing = db.query(Target).filter(Target.id == target_id).first()
                if existing:
                    raise AvenlisError(f"Target with ID '{target_id}' already exists")
                
                target = Target(
                    id=target_id,
                    name=name,
                    ip_address=ip_address,
                    description=description,
                    target_type=target_type or 'URL',
                    model=model
                )
                db.add(target)
                db.commit()
                db.refresh(target)
                
                logger.info(f"Created target: {name} (ID: {target.id})")
                return target.id
        except Exception as e:
            logger.error(f"Failed to create target: {e}")
            raise
    
    def get_target(self, target_id: str) -> Optional[Dict[str, Any]]:
        """Get a target by ID from hybrid storage."""
        try:
            # Try YAML first
            from .storage.yaml_loader import YAMLLoader
            yaml_loader = YAMLLoader()
            yaml_targets = yaml_loader.load_targets()
            for target in yaml_targets:
                if target.get('id') == target_id:
                    target['source'] = 'file'
                    return target
            
            # Try local database
            with self.get_db_session() as db:
                target = db.query(Target).filter(Target.id == target_id).first()
                if target:
                    target_dict = target.to_dict()
                    target_dict['source'] = 'local'
                    return target_dict
            
            return None
        except Exception as e:
            logger.error(f"Failed to get target {target_id}: {e}")
            return None
    
    def get_all_targets(self) -> List[Dict[str, Any]]:
        """Get all targets from local database."""
        try:
            with self.get_db_session() as db:
                targets = db.query(Target).order_by(Target.updated_at.desc()).all()
                result = []
                for target in targets:
                    try:
                        target_dict = target.to_dict()
                        target_dict['source'] = 'local'
                        result.append(target_dict)
                    except Exception as e:
                        logger.error(f"Failed to convert target {target.id} to dict: {e}")
                        continue
                logger.info(f"Retrieved {len(result)} targets from local database")
                return result
        except Exception as e:
            logger.error(f"Failed to get targets from database: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def get_combined_targets(self) -> List[Dict[str, Any]]:
        """Get targets from both YAML files and local storage."""
        try:
            all_targets = []
            
            # Load from YAML files
            from .storage.yaml_loader import YAMLLoader
            yaml_loader = YAMLLoader()
            yaml_targets = yaml_loader.load_targets()
            for target in yaml_targets:
                target_id = target.get('id')
                if target_id:
                    target['source'] = 'file'
                    all_targets.append(target)
            
            # Load from local storage
            local_targets = self.get_all_targets()
            logger.info(f"Found {len(local_targets)} targets from local database")
            for target in local_targets:
                target_id = target.get('id')
                if target_id:
                    # Ensure source is set to 'local'
                    target['source'] = 'local'
                    all_targets.append(target)
            
            return all_targets
        except Exception as e:
            logger.error(f"Failed to get combined targets: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def update_target(self, target_id: str, name: str = None, ip_address: str = None, description: str = None, target_type: str = None, model: str = None) -> bool:
        """Update a target in local database."""
        try:
            with self.get_db_session() as db:
                target = db.query(Target).filter(Target.id == target_id).first()
                if not target:
                    return False
                
                if name is not None:
                    target.name = name
                if ip_address is not None:
                    target.ip_address = ip_address
                if description is not None:
                    target.description = description
                if target_type is not None:
                    target.target_type = target_type
                if model is not None:
                    target.model = model
                
                target.updated_at = func.now()
                db.commit()
                
                logger.info(f"Updated target: {target_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to update target {target_id}: {e}")
            return False
    
    def delete_target(self, target_id: str) -> bool:
        """Delete a target from local database."""
        try:
            with self.get_db_session() as db:
                target = db.query(Target).filter(Target.id == target_id).first()
                if not target:
                    return False
                
                db.delete(target)
                db.commit()
                
                logger.info(f"Deleted target: {target_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to delete target {target_id}: {e}")
            return False
    
    # YAML target methods
    
    def create_yaml_target(self, target_id: str, name: str, ip_address: str, description: str = None, target_type: str = None, model: str = None) -> str:
        """Create a new target in targets.yaml file."""
        try:
            from datetime import datetime
            import yaml
            import os
            from pathlib import Path
            
            current_time = datetime.now().isoformat() + 'Z'
            
            # Get the targets YAML file path
            data_dir = Path(__file__).parent / 'data'
            yaml_path = data_dir / 'targets.yaml'
            
            # Load existing targets
            targets = []
            if yaml_path.exists():
                with open(yaml_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f) or {}
                    targets = data.get('targets', [])
            
            # Check if target ID already exists
            if any(t.get('id') == target_id for t in targets):
                raise AvenlisError(f"Target with ID '{target_id}' already exists")
            
            # Create new target
            new_target = {
                'id': target_id,
                'name': name,
                'ip_address': ip_address,
                'description': description or '',
                'target_type': target_type or 'URL',
                'date_updated': current_time
            }
            
            # Only add model if target_type is Ollama
            if target_type == 'Ollama' and model:
                new_target['model'] = model
            
            targets.append(new_target)
            
            # Save back to YAML
            with open(yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump({'targets': targets}, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
            logger.info(f"Created YAML target: {target_id}")
            return target_id
        except Exception as e:
            logger.error(f"Error creating YAML target: {e}")
            raise
    
    def update_yaml_target(self, target_id: str, name: str = None, ip_address: str = None, description: str = None, target_type: str = None, model: str = None) -> bool:
        """Update a target in targets.yaml file."""
        try:
            from datetime import datetime
            import yaml
            from pathlib import Path
            
            current_time = datetime.now().isoformat() + 'Z'
            
            # Get the targets YAML file path
            data_dir = Path(__file__).parent / 'data'
            yaml_path = data_dir / 'targets.yaml'
            
            # Load existing targets
            targets = []
            if yaml_path.exists():
                with open(yaml_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f) or {}
                    targets = data.get('targets', [])
            
            # Find and update the target
            target_found = False
            for target in targets:
                if target.get('id') == target_id:
                    target_found = True
                    if name is not None:
                        target['name'] = name
                    if ip_address is not None:
                        target['ip_address'] = ip_address
                    if description is not None:
                        target['description'] = description
                    if target_type is not None:
                        target['target_type'] = target_type
                    if target_type == 'Ollama' and model is not None:
                        target['model'] = model
                    elif target_type == 'URL' and 'model' in target:
                        # Remove model field if switching to URL type
                        target.pop('model', None)
                    target['date_updated'] = current_time
                    break
            
            if not target_found:
                return False
            
            # Save back to YAML
            with open(yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump({'targets': targets}, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
            logger.info(f"Updated YAML target: {target_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating YAML target: {e}")
            return False
    
    def delete_yaml_target(self, target_id: str) -> bool:
        """Delete a target from targets.yaml file."""
        try:
            import yaml
            from pathlib import Path
            
            # Get the targets YAML file path
            data_dir = Path(__file__).parent / 'data'
            yaml_path = data_dir / 'targets.yaml'
            
            if not yaml_path.exists():
                return False
            
            # Load existing targets
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
                targets = data.get('targets', [])
            
            # Remove the target
            original_count = len(targets)
            targets = [t for t in targets if t.get('id') != target_id]
            
            if len(targets) == original_count:
                return False  # Target not found
            
            # Save back to YAML
            with open(yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump({'targets': targets}, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
            logger.info(f"Deleted YAML target: {target_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting YAML target: {e}")
            return False

