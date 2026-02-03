import pytest
import tempfile
import os
import sys
from pathlib import Path
from click.testing import CliRunner

@pytest.fixture(scope="function")
def test_db_path():
    """Create a temporary database file for each test."""
    db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_file.close()
    yield db_file.name
    try:    
        os.remove(db_file.name)
    except (PermissionError, FileNotFoundError):
        pass

@pytest.fixture(autouse=True)
def patch_storage(monkeypatch, test_db_path):
    """Patch AvenlisStorage._get_db_path to return test database."""
    from sandstrike.main_storage import AvenlisStorage
    
    # Patch the _get_db_path method to return our test path
    def mock_get_db_path(self):
        return Path(test_db_path)
    
    monkeypatch.setattr(AvenlisStorage, "_get_db_path", mock_get_db_path)
    
    # Force reload of CLI modules to pick up the patch
    import importlib
    modules_to_reload = [
        'sandstrike.cli.commands.sessions',
        'sandstrike.cli.main'
    ]
    
    for module_name in modules_to_reload:
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])

def test_sessions_list():
    """Test listing sessions."""
    # Import AFTER the patch is applied
    from sandstrike.cli.main import cli
    
    runner = CliRunner()
    result = runner.invoke(cli, ["sessions", "list"], catch_exceptions=False)

    print(f"Exit code: {result.exit_code}")
    print(f"Output: {result.output}")
    if result.exception:
        import traceback
        traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)
    
    assert result.exit_code == 0
    assert "Session" in result.output or "no" in result.output.lower()

def test_sessions_list_filter_status():
    """Test listing sessions."""
    # Import AFTER the patch is applied
    from sandstrike.cli.main import cli
    
    runner = CliRunner()
    result = runner.invoke(cli, ["sessions", "list", "--status", "completed"], catch_exceptions=False)

    print(f"Exit code: {result.exit_code}")
    print(f"Output: {result.output}")
    if result.exception:
        import traceback
        traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)
    
    assert result.exit_code == 0
    assert "Test Sessions" in result.output or "no" in result.output.lower()

def test_sessions_list_filter_status_and_source():
    """Test listing sessions."""
    # Import AFTER the patch is applied
    from sandstrike.cli.main import cli
    
    runner = CliRunner()
    result = runner.invoke(cli, ["sessions", "list", "--status", "completed", "--source", "file"], catch_exceptions=False)

    print(f"Exit code: {result.exit_code}")
    print(f"Output: {result.output}")
    if result.exception:
        import traceback
        traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)
    
    assert result.exit_code == 0
    assert "Test Sessions" in result.output or "no" in result.output.lower()

def test_sessions_show():
    """Test displaying 1 session."""
    # Import AFTER the patch is applied
    from sandstrike.cli.main import cli
    
    runner = CliRunner()
    session_id = "scan_session_d573b70f_1764599159"
    result = runner.invoke(cli, ["sessions", "show", session_id], catch_exceptions=False)

    print(f"Exit code: {result.exit_code}")
    print(f"Output: {result.output}")
    if result.exception:
        import traceback
        traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)
    
    assert result.exit_code == 0
    assert "Session Details" in result.output or "no" in result.output.lower()
    assert "ID: " + session_id in result.output

def test_sessions_show_detailed():
    """Test displaying 1 detailed session."""
    # Import AFTER the patch is applied
    from sandstrike.cli.main import cli
    
    runner = CliRunner()
    session_id = "scan_session_d573b70f_1764599159"
    result = runner.invoke(cli, ["sessions", "show", session_id, "--detailed"], catch_exceptions=False)

    print(f"Exit code: {result.exit_code}")
    print(f"Output: {result.output}")
    if result.exception:
        import traceback
        traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)
    
    assert result.exit_code == 0
    assert "Session Details" in result.output or "no" in result.output.lower()
    assert "ID: " + session_id in result.output
    assert "Detailed Prompt and Response Information" in result.output

# def test_sessions_list_empty(test_db_path):
#     """Test listing sessions when database is empty."""
#     # Import AFTER the patch is applied
#     from sandstrike.cli.main import cli
    
#     runner = CliRunner()
#     result = runner.invoke(cli, ["sessions", "list"], catch_exceptions=False)

#     print(f"Exit code: {result.exit_code}")
#     print(f"Output: {result.output}")
#     if result.exception:
#         import traceback
#         traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)
    
#     assert result.exit_code == 0
#     # Fixed typo here
#     assert "session" in result.output.lower() or "no" in result.output.lower()

# def test_sessions_list_with_data(test_db_path):
#     """Test listing sessions with actual data."""
#     from sandstrike.main_storage import AvenlisStorage
#     # Import AFTER the patch is applied
#     from sandstrike.cli.main import cli
    
#     # Create a session directly in the test database
#     storage = AvenlisStorage(db_path=test_db_path)
#     session_id = storage.create_session(
#         name="test_session",
#         target_url="https://example.com",
#         target_model="test-model",
#     )
    
#     # Now list sessions via CLI
#     runner = CliRunner()
#     result = runner.invoke(cli, ["sessions", "list"], catch_exceptions=False)
    
#     print(f"Output: {result.output}")
#     assert result.exit_code == 0
#     assert "test_session" in result.output or "Total" in result.output