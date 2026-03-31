# Avenlis Tests

Comprehensive test suite for the Avenlis SandStrike library, ensuring reliability and correctness across all components.

## 📁 Test Structure

```
tests/
├── __init__.py              # Test package initialization
├── test_auth.py             # Authentication system tests
├── test_api.py              # API client tests  
├── test_config.py           # Configuration management tests
├── test_storage.py          # Database storage tests
├── test_redteam*.py         # Red team framework tests
├── test_cli*.py             # CLI command tests
├── test_server.py           # Web server tests
├── test_utils*.py           # Utility function tests
├── fixtures/                # Test data and fixtures
├── mocks/                   # Mock objects and responses
└── integration/             # Integration tests
```

## 🧪 Test Categories

### Unit Tests
Test individual components in isolation:

- **`test_auth.py`**: Authentication, keyring storage, API key validation
- **`test_config.py`**: Configuration loading, environment variables
- **`test_storage.py`**: Database operations, SQLite functionality  
- **`test_redteam_core.py`**: Red team engine functionality
- **`test_attack_modules.py`**: Individual attack module behavior
- **`test_utils.py`**: Utility functions and helpers

### Integration Tests  
Test component interactions:

- **`test_redteam_integration.py`**: End-to-end red team testing
- **`test_cli_integration.py`**: CLI command workflows
- **`test_server_integration.py`**: Web server API functionality

### Mock Tests
Test with simulated external dependencies:

- **`test_cli_*.py`**: CLI commands with mocked services
- **`test_api_mocked.py`**: API client with mock responses

## 🚀 Running Tests

### All Tests
```bash
# Run complete test suite
pytest

# Run with coverage report
pytest --cov=avenlis --cov-report=html

# Run with verbose output
pytest -v
```

### Specific Test Categories
```bash
# Unit tests only
pytest tests/test_*.py

# Integration tests only  
pytest tests/integration/

# CLI tests only
pytest tests/test_cli*.py

# Red team tests only
pytest tests/test_redteam*.py
```

### Specific Test Files
```bash
# Test authentication
pytest tests/test_auth.py -v

# Test with specific markers
pytest -m "not slow" -v

# Test specific function
pytest tests/test_auth.py::test_login_success -v
```

## 🛠️ Test Configuration

### `pytest.ini` Configuration
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers = 
    slow: marks tests as slow
    integration: marks tests as integration tests
    cli: marks tests as CLI tests
    network: marks tests requiring network access
addopts = 
    --strict-markers
    --disable-warnings
    -ra
```

### Test Fixtures (`conftest.py`)
```python
import pytest
import tempfile
from pathlib import Path
from sandstrike.config import AvenlisConfig
from sandstrike.main_storage import AvenlisStorage
from sandstrike.auth import AvenlisAuth

@pytest.fixture
def temp_config():
    """Provide temporary configuration for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = AvenlisConfig()
        config._config_dir = Path(temp_dir)
        yield config

@pytest.fixture  
def mock_storage():
    """Provide mock storage with temporary database."""
    with tempfile.NamedTemporaryFile(suffix='.db') as temp_db:
        storage = AvenlisStorage()
        storage.db_path = temp_db.name
        storage._init_database()
        yield storage

@pytest.fixture
def mock_auth():
    """Provide mock authentication for testing."""
    auth = AvenlisAuth()
    auth._debug_mode = True  # Enable mock authentication
    yield auth
```

## 🧩 Test Examples

### Authentication Tests (`test_auth.py`)
```python
import pytest
from unittest.mock import patch, Mock
from sandstrike.auth import AvenlisAuth
from sandstrike.exceptions import AvenlisAuthError

class TestAvenlisAuth:
    def test_login_success(self, mock_auth):
        """Test successful login with valid API key."""
        result = mock_auth.login_with_api_key("test_api_key_12345")
        
        assert result["id"] == "test_user_123"
        assert result["email"] == "test@avenlis.com"
        assert mock_auth.is_authenticated() is True

    def test_login_invalid_key(self, mock_auth):
        """Test login failure with invalid API key."""
        with pytest.raises(AvenlisAuthError, match="Invalid API key"):
            mock_auth.login_with_api_key("invalid_key")

    @patch('keyring.get_password')
    def test_get_stored_credentials(self, mock_keyring, mock_auth):
        """Test retrieval of stored credentials."""
        mock_keyring.return_value = "stored_api_key"
        
        api_key = mock_auth.get_api_key()
        assert api_key == "stored_api_key"
        mock_keyring.assert_called_once()

    def test_logout_clears_credentials(self, mock_auth):
        """Test that logout clears stored credentials.""" 
        mock_auth.login_with_api_key("test_key")
        assert mock_auth.is_authenticated() is True
        
        mock_auth.logout()
        assert mock_auth.is_authenticated() is False
```

### Red Team Tests (`test_redteam_core.py`)
```python
import pytest
from sandstrike.redteam import AvenlisRedteam
from sandstrike.redteam.attack_modules import AttackModule

class TestAvenlisRedteam:
    def test_evaluate_attacks_success(self):
        """Test successful attack evaluation."""
        redteam = AvenlisRedteam()
        
        results = redteam.evaluate_attacks(
            target="mock://vulnerable",  # Mock target that returns vulnerable responses
            attack_modules=["prompt-injection"],
            severity_filter="medium"
        )
        
        assert "summary" in results
        assert "details" in results
        assert results["summary"]["total_tests"] > 0

    def test_evaluate_attacks_with_filters(self):
        """Test attack evaluation with severity filtering."""
        redteam = AvenlisRedteam()
        
        results = redteam.evaluate_attacks(
            target="mock://secure",
            attack_modules=["all"],
            severity_filter="high"
        )
        
        # Should only include high-severity attacks
        for detail in results["details"]:
            assert detail["severity"] in ["high", "critical"]

    @pytest.mark.slow
    def test_evaluate_attacks_real_target(self):
        """Test against real Ollama instance (if available)."""
        redteam = AvenlisRedteam()
        
        try:
            results = redteam.evaluate_attacks(
                target="ollama://llama2",
                attack_modules=["prompt-injection"],
                timeout=10
            )
            assert results is not None
        except Exception:
            pytest.skip("No Ollama instance available")
```

### CLI Tests (`test_cli_auth.py`)
```python
import pytest
from click.testing import CliRunner
from unittest.mock import patch
from sandstrike.cli.commands.auth import auth_group

class TestAuthCLI:
    def test_login_command(self):
        """Test auth login command."""
        runner = CliRunner()
        
        with patch('avenlis.auth.AvenlisAuth.login_with_api_key') as mock_login:
            mock_login.return_value = {"email": "test@example.com"}
            
            result = runner.invoke(auth_group, ['login'])
            
            assert result.exit_code == 0
            assert "Login successful" in result.output
            mock_login.assert_called_once()

    def test_whoami_not_authenticated(self):
        """Test whoami command when not authenticated."""
        runner = CliRunner()
        
        with patch('avenlis.auth.AvenlisAuth.is_authenticated') as mock_auth:
            mock_auth.return_value = False
            
            result = runner.invoke(auth_group, ['whoami'])
            
            assert result.exit_code == 1
            assert "Not authenticated" in result.output

    def test_logout_command(self):
        """Test auth logout command."""
        runner = CliRunner()
        
        with patch('avenlis.auth.AvenlisAuth.logout') as mock_logout:
            result = runner.invoke(auth_group, ['logout'])
            
            assert result.exit_code == 0
            assert "Logged out" in result.output
            mock_logout.assert_called_once()
```

### Storage Tests (`test_storage.py`)
```python
import pytest
from sandstrike.main_storage import AvenlisStorage

class TestAvenlisStorage:
    def test_create_session(self, mock_storage):
        """Test session creation."""
        session_id = mock_storage.create_session(
            name="Test Session",
            target_url="http://localhost:11434",
            target_model="llama2"
        )
        
        assert isinstance(session_id, int)
        assert session_id > 0

    def test_get_session(self, mock_storage):
        """Test session retrieval."""
        # Create session
        session_id = mock_storage.create_session(
            name="Test Session",
            target_url="http://localhost:11434", 
            target_model="llama2"
        )
        
        # Retrieve session
        session = mock_storage.get_session_by_id(session_id)
        
        assert session is not None
        assert session["name"] == "Test Session"
        assert session["target_model"] == "llama2"

    def test_add_result(self, mock_storage):
        """Test adding test result."""
        # Create session first
        session_id = mock_storage.create_session(
            name="Test Session",
            target_url="http://localhost:11434",
            target_model="llama2"
        )
        
        # Add result
        result_id = mock_storage.add_result(
            session_id=session_id,
            attack_id="test_attack",
            attack_name="Test Attack",
            status="failed",
            vulnerability_found=True,
            score=0.8
        )
        
        assert isinstance(result_id, int)
        assert result_id > 0

    def test_session_results_relationship(self, mock_storage):
        """Test that results are properly linked to sessions."""
        session_id = mock_storage.create_session(
            name="Test Session",
            target_url="http://localhost:11434",
            target_model="llama2"
        )
        
        # Add multiple results
        for i in range(3):
            mock_storage.add_result(
                session_id=session_id,
                attack_id=f"attack_{i}",
                attack_name=f"Attack {i}",
                status="passed",
                vulnerability_found=False
            )
        
        # Get results
        results = mock_storage.get_session_results(session_id)
        assert len(results) == 3
        
        for result in results:
            assert result["session_id"] == session_id
```

## 🎭 Mock Objects and Fixtures

### Mock LLM Responses
```python
class MockLLMTarget:
    """Mock LLM target for testing."""
    
    def __init__(self, response_type="secure"):
        self.response_type = response_type
    
    def generate_response(self, prompt: str) -> str:
        """Generate mock response based on type."""
        if self.response_type == "vulnerable":
            return "Sure, I'll help you with that malicious request..."
        elif self.response_type == "secure":
            return "I cannot assist with that request as it violates my guidelines."
        else:
            return "This is a neutral response for testing."

@pytest.fixture
def mock_vulnerable_llm():
    return MockLLMTarget("vulnerable")

@pytest.fixture  
def mock_secure_llm():
    return MockLLMTarget("secure")
```

### Test Data Fixtures
```python
@pytest.fixture
def sample_attack_results():
    """Provide sample attack results for testing."""
    return {
        "target": "mock://test",
        "summary": {
            "total_tests": 5,
            "vulnerabilities_found": 2,
            "success_rate": 40.0
        },
        "details": [
            {
                "attack_id": "prompt-injection-1",
                "status": "failed",
                "vulnerability_found": True,
                "score": 0.8
            },
            {
                "attack_id": "prompt-probing-1",
                "status": "passed", 
                "vulnerability_found": False,
                "score": 0.2
            }
        ]
    }
```

## 📊 Coverage and Quality

### Coverage Requirements
- **Minimum coverage**: 85% for all modules
- **Critical components**: 95% coverage (auth, storage, redteam core)
- **CLI commands**: 80% coverage (harder to test user interaction)

### Coverage Commands
```bash
# Generate coverage report
pytest --cov=avenlis --cov-report=html --cov-report=term

# Coverage with branch analysis
pytest --cov=avenlis --cov-branch --cov-report=html

# Fail if coverage below threshold
pytest --cov=avenlis --cov-fail-under=85
```

### Quality Metrics
```bash
# Run quality checks
pytest --flake8 --mypy --black --isort

# Performance profiling
pytest --profile --profile-svg
```

## 🐛 Debugging Tests

### Debug Mode
```bash
# Run with debugging
pytest --pdb  # Drop into debugger on failure
pytest --pdb-trace  # Drop into debugger immediately

# Verbose output
pytest -v -s  # Don't capture output

# Show local variables on failure  
pytest --tb=long --showlocals
```

### Logging in Tests
```python
import logging

def test_with_logging(caplog):
    """Test that captures log output."""
    with caplog.at_level(logging.INFO):
        # Code that logs
        logger.info("Test message")
    
    assert "Test message" in caplog.text
```

## 🚀 Performance Testing

### Benchmark Tests
```python
import pytest
import time

@pytest.mark.benchmark
def test_redteam_performance():
    """Benchmark red team attack execution."""
    redteam = AvenlisRedteam()
    
    start_time = time.time()
    results = redteam.evaluate_attacks(
        target="mock://test",
        attack_modules=["prompt-injection", "prompt-probing"]  # Jailbreak coverage coming soon
    )
    duration = time.time() - start_time
    
    assert duration < 5.0  # Should complete within 5 seconds
    assert len(results["details"]) > 0
```

### Memory Testing
```python
import psutil
import os

def test_memory_usage():
    """Test memory usage doesn't exceed limits."""
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    # Run memory-intensive operation
    redteam = AvenlisRedteam()
    redteam.evaluate_attacks("mock://test", ["all"])
    
    final_memory = process.memory_info().rss
    memory_growth = final_memory - initial_memory
    
    # Should not grow by more than 100MB
    assert memory_growth < 100 * 1024 * 1024
```

## 🤝 Contributing Tests

### Test Writing Guidelines

1. **Descriptive names**: `test_login_with_invalid_credentials_raises_auth_error()`
2. **Single responsibility**: Each test should test one specific behavior
3. **Arrange-Act-Assert**: Clear test structure
4. **Mock external dependencies**: Don't rely on external services
5. **Test edge cases**: Empty inputs, null values, boundary conditions

### Test Documentation
```python
def test_complex_scenario(self):
    """
    Test description explaining what scenario is being tested.
    
    This test verifies that when X happens under conditions Y,
    the system behaves correctly by doing Z.
    
    Covers:
    - Edge case A
    - Error condition B  
    - Integration point C
    """
```

### Test Markers
```python
@pytest.mark.slow
def test_long_running_operation():
    """Mark tests that take significant time."""
    pass

@pytest.mark.integration
def test_component_integration():
    """Mark integration tests."""
    pass

@pytest.mark.network
def test_api_endpoint():
    """Mark tests requiring network access.""" 
    pass
```

## 🔧 Continuous Integration

Tests run automatically on:
- **Pull requests**: All tests must pass
- **Merge to main**: Full test suite including integration tests
- **Nightly builds**: Performance and long-running tests

### CI Configuration Example
```yaml
# .github/workflows/tests.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -e .[dev]
      
      - name: Run tests
        run: pytest --cov=avenlis --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v1
```

## 📚 Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [Mock Objects Guide](https://docs.python.org/3/library/unittest.mock.html)
