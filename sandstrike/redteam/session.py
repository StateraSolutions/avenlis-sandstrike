"""
Red team session management for Avenlis.

This module handles persistent red team testing sessions,
allowing users to save progress, resume tests, and manage results.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from sandstrike.config import AvenlisConfig
from sandstrike.exceptions import AvenlisError
from sandstrike.utils.logging import get_logger

logger = get_logger(__name__)


class RedteamSession:
    """
    Manages a red team testing session.
    
    Sessions allow users to organize and persist their adversarial testing
    campaigns, tracking progress and results over time.
    """
    
    def __init__(
        self,
        id: str,
        name: str,
        target: str,
        created_at: datetime,
        status: str = "active",
        config: Optional[AvenlisConfig] = None
    ):
        """Initialize a red team session."""
        self.id = id
        self.name = name
        self.target = target
        self.created_at = created_at
        self.status = status
        self.config = config or AvenlisConfig()
        
        # Session data
        self.tests = []
        self.results = {}
        self.metadata = {}
        
        # File paths
        self.sessions_dir = Path.home() / ".avenlis" / "redteam" / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.session_file = self.sessions_dir / f"{self.id}.json"
    
    @classmethod
    def create(cls, name: str, target: str, config: Optional[AvenlisConfig] = None) -> 'RedteamSession':
        """
        Create a new red team session.
        
        Args:
            name: Human-readable name for the session
            target: Target LLM endpoint or identifier
            config: Optional configuration
            
        Returns:
            New RedteamSession instance
        """
        session_id = str(uuid.uuid4())
        session = cls(
            id=session_id,
            name=name,
            target=target,
            created_at=datetime.now(),
            config=config
        )
        
        session.save()
        logger.info(f"Created new red team session: {name} ({session_id})")
        
        return session
    
    @classmethod
    def load(cls, session_id: str, config: Optional[AvenlisConfig] = None) -> 'RedteamSession':
        """
        Load an existing red team session.
        
        Args:
            session_id: Session ID to load
            config: Optional configuration
            
        Returns:
            Loaded RedteamSession instance
            
        Raises:
            AvenlisError: If session not found or invalid
        """
        sessions_dir = Path.home() / ".avenlis" / "redteam" / "sessions"
        session_file = sessions_dir / f"{session_id}.json"
        
        if not session_file.exists():
            raise AvenlisError(f"Session {session_id} not found")
        
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            session = cls(
                id=data["id"],
                name=data["name"],
                target=data["target"],
                created_at=datetime.fromisoformat(data["created_at"]),
                status=data.get("status", "active"),
                config=config
            )
            
            session.tests = data.get("tests", [])
            session.results = data.get("results", {})
            session.metadata = data.get("metadata", {})
            
            return session
            
        except (json.JSONDecodeError, KeyError) as e:
            raise AvenlisError(f"Invalid session file: {e}")
    
    @classmethod
    def list_all(cls, config: Optional[AvenlisConfig] = None) -> List['RedteamSession']:
        """
        List all available red team sessions.
        
        Args:
            config: Optional configuration
            
        Returns:
            List of RedteamSession instances
        """
        sessions_dir = Path.home() / ".avenlis" / "redteam" / "sessions"
        sessions = []
        
        if not sessions_dir.exists():
            return sessions
        
        for session_file in sessions_dir.glob("*.json"):
            try:
                session_id = session_file.stem
                session = cls.load(session_id, config)
                sessions.append(session)
            except AvenlisError:
                logger.warning(f"Failed to load session from {session_file}")
                continue
        
        # Sort by creation date (newest first)
        sessions.sort(key=lambda s: s.created_at, reverse=True)
        
        return sessions
    
    def save(self) -> None:
        """Save the session to disk."""
        try:
            data = {
                "id": self.id,
                "name": self.name,
                "target": self.target,
                "created_at": self.created_at.isoformat(),
                "status": self.status,
                "tests": self.tests,
                "results": self.results,
                "metadata": self.metadata
            }
            
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            raise AvenlisError(f"Failed to save session: {e}")
    
    def add_test_result(self, test_result: Dict[str, Any]) -> None:
        """
        Add a test result to the session.
        
        Args:
            test_result: Test result dictionary
        """
        self.tests.append(test_result)
        self.save()
    
    def update_results(self, results: Dict[str, Any]) -> None:
        """
        Update session results summary.
        
        Args:
            results: Results dictionary
        """
        self.results = results
        self.save()
    
    def set_status(self, status: str) -> None:
        """
        Update session status.
        
        Args:
            status: New status (active, completed, paused, failed)
        """
        self.status = status
        self.save()
    
    def export_results(self, output_path: str, format: str = "json") -> None:
        """
        Export session results to a file.
        
        Args:
            output_path: Output file path
            format: Export format (json, csv, html)
        """
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            if format == "json":
                self._export_json(output_file)
            elif format == "csv":
                self._export_csv(output_file)
            elif format == "html":
                self._export_html(output_file)
            else:
                raise AvenlisError(f"Unsupported export format: {format}")
                
            logger.info(f"Session results exported to {output_path}")
            
        except Exception as e:
            raise AvenlisError(f"Failed to export results: {e}")
    
    def _export_json(self, output_file: Path) -> None:
        """Export results as JSON."""
        export_data = {
            "session": {
                "id": self.id,
                "name": self.name,
                "target": self.target,
                "created_at": self.created_at.isoformat(),
                "status": self.status
            },
            "results": self.results,
            "tests": self.tests,
            "metadata": self.metadata,
            "exported_at": datetime.now().isoformat()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    def _export_csv(self, output_file: Path) -> None:
        """Export results as CSV."""
        import csv
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            if not self.tests:
                f.write("No test results available\n")
                return
            
            # Get all possible fields from tests
            fieldnames = set()
            for test in self.tests:
                fieldnames.update(test.keys())
            
            fieldnames = sorted(list(fieldnames))
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            for test in self.tests:
                writer.writerow(test)
    
    def _export_html(self, output_file: Path) -> None:
        """Export results as HTML."""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Avenlis Red Team Results - {self.name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 15px; border-radius: 5px; }}
                .summary {{ margin: 20px 0; }}
                .test-result {{ border: 1px solid #ddd; margin: 10px 0; padding: 10px; border-radius: 5px; }}
                .success {{ background-color: #ffebee; }}
                .failure {{ background-color: #e8f5e8; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Red Team Results: {self.name}</h1>
                <p><strong>Session ID:</strong> {self.id}</p>
                <p><strong>Target:</strong> {self.target}</p>
                <p><strong>Created:</strong> {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Status:</strong> {self.status}</p>
            </div>
            
            <div class="summary">
                <h2>Summary</h2>
                <p><strong>Total Tests:</strong> {len(self.tests)}</p>
                <p><strong>Successful Attacks:</strong> {sum(1 for t in self.tests if t.get('success', False))}</p>
                <p><strong>Failed Attacks:</strong> {sum(1 for t in self.tests if not t.get('success', False))}</p>
            </div>
            
            <div class="tests">
                <h2>Test Results</h2>
        """
        
        for i, test in enumerate(self.tests, 1):
            success_class = "success" if test.get("success", False) else "failure"
            html_content += f"""
                <div class="test-result {success_class}">
                    <h3>Test {i} - {test.get('prompt_name', 'Unknown')}</h3>
                    <p><strong>Success:</strong> {test.get('success', False)}</p>
                    <p><strong>Prompt:</strong> {test.get('prompt', 'N/A')[:200]}...</p>
                    <p><strong>Response:</strong> {test.get('response', 'N/A')[:200]}...</p>
                </div>
            """
        
        html_content += """
            </div>
        </body>
        </html>
        """
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    @property
    def test_count(self) -> int:
        """Get the number of tests in this session."""
        return len(self.tests)
    
    def delete(self) -> None:
        """Delete the session from disk."""
        try:
            if self.session_file.exists():
                self.session_file.unlink()
            logger.info(f"Deleted session {self.id}")
        except Exception as e:
            raise AvenlisError(f"Failed to delete session: {e}")
