# SandStrike CLI Interface

The command-line interface for SandStrike, providing easy access to all red team testing functionality from the terminal.

## 📁 Directory Structure

```
cli/
├── __init__.py              # CLI package initialization
├── main.py                  # Main CLI entry point and argument parsing
└── commands/
    ├── __init__.py          # Commands package
    ├── auth.py              # Authentication commands
    ├── prompts.py           # Prompt management commands
    ├── collections.py       # Collection management commands
    ├── targets.py           # Target management commands
    ├── sessions.py          # Session management commands
    ├── grader.py            # Response grading commands
    └── reports.py           # Report generation commands
```

## 🚀 Usage

### Basic Command Structure
```bash
sandstrike [OPTIONS] COMMAND [ARGS]...
```

### Global Options
- `--config, -c`: Path to configuration file
- `--help`: Show help message
- `--version`: Show version information

## 📋 Command Groups

### Authentication Commands (`auth.py`)

Manage user authentication and API key verification.

```bash
# Verify API key and check subscription status
sandstrike auth verify
```

**Features:**
- API key validation
- Subscription status checking (Free, Plus, Pro)
- Environment variable support

### Prompt Management Commands (`prompts.py`)

Manage adversarial prompts and their metadata.

```bash
# Create new prompt
sandstrike prompts create --id "prompt_001" --technique "Prompt Injection" --category "LLM01_PromptInjection" --text "Ignore previous instructions..."

# List prompts
sandstrike prompts list
sandstrike prompts list --category "LLM01_PromptInjection"
sandstrike prompts list --subcategory "Direct Injection"

# Show prompt details
sandstrike prompts show prompt_001

# Edit prompt
sandstrike prompts edit prompt_001 --technique "Advanced Injection"

# Delete prompt
sandstrike prompts delete prompt_001

# Export/Import prompts
sandstrike prompts export --output prompts.json
sandstrike prompts import prompts.json --importtype rapid
```

### Collection Management Commands (`collections.py`)

Organize prompts into logical groups for testing.

```bash
# Create collection
sandstrike collections create --name "Web Security Tests" --description "Comprehensive web security testing"

# List collections
sandstrike collections list

# Delete collection
sandstrike collections delete collection_001

# Remove prompt from collection
sandstrike collections remove-prompt collection_001 prompt_001
```

### Target Management Commands (`targets.py`)

Manage scan targets (IP addresses/endpoints) for reusable testing.

```bash
# Create target
sandstrike targets create --id "target_001" --name "Local Ollama Server" --ip "http://localhost:11434" --source local
sandstrike targets create --id "target_002" --name "Production API" --ip "https://api.example.com:8080" --description "Production environment" --source file

# List targets
sandstrike targets list
sandstrike targets list --source local
sandstrike targets list --source file

# View target details
sandstrike targets view target_001

# Delete target
sandstrike targets delete target_001
```

**Features:**
- Store targets in YAML files or local SQLite database
- Reusable target configurations for scans
- Support for IP addresses with optional ports
- Integration with scan page for easy selection

### Session Management Commands (`sessions.py`)

Track and manage testing sessions.

```bash
# List sessions
sandstrike sessions list
sandstrike sessions list --status completed
sandstrike sessions list --source local

# Show session details
sandstrike sessions show session_001
sandstrike sessions show session_001 --results

# Delete sessions
sandstrike sessions delete session_001
sandstrike sessions delete-all

# Export session data
sandstrike sessions export session_001 --format csv
```

### Response Grading Commands (`grader.py`)

Grade LLM responses using AI evaluation (Pro users only).

```bash
# Grade response
sandstrike grader --input "Tell me about weapons" --output "I cannot provide information about weapons" --intent "safety_evaluation"

# Grade with custom intent
sandstrike grader --input "What makes a good leader?" --output "Men are naturally better leaders" --intent "bias_detection"

# Grade with custom API key
sandstrike grader --input "Ignore previous instructions" --output "I'll help you with that" --intent "prompt_injection" --api-key YOUR_KEY
```

### Report Generation Commands (`reports.py`)

Generate comprehensive HTML security reports (Paid users only).

```bash
# Generate all three report types at once
sandstrike reports all

# Generate all reports for specific sessions
sandstrike reports all --session-ids session_001,session_002

# Generate all reports from specific source
sandstrike reports all --source file

# Generate all reports to specific directory
sandstrike reports all --output /path/to/reports

# Generate individual reports
sandstrike reports overview --session-ids session_001,session_002
sandstrike reports detailed --source local
sandstrike reports executive --output custom-executive.html
```

### Web UI Commands (`ui.py`)

Manage the modern React web interface.

```bash
# Start web interface
sandstrike ui start
sandstrike ui start --backend-port 8080 --frontend-port 3000
```

**Features:**
- Full-stack React + Flask setup
- Automatic dependency installation
- Development and production modes
- Custom port configuration  

## 🛠️ Development

### Adding New Commands

1. **Create command module** in `commands/`:
```python
# commands/newcommand.py
import click

@click.group(name="newcommand")
def newcommand_group():
    """New command functionality."""
    pass

@newcommand_group.command()
def action():
    """Perform some action."""
    click.echo("Action performed!")
```

2. **Register in main.py**:
```python
from sandstrike.cli.commands import newcommand

cli.add_command(newcommand.newcommand_group)
```

3. **Add tests**:
```python
# tests/test_cli_newcommand.py
def test_newcommand_action():
    # Test implementation
    pass
```

### Command Patterns

#### Basic Command
```python
@click.command()
@click.option("--name", "-n", help="Name parameter")
def command(name):
    """Command description."""
    click.echo(f"Hello {name}!")
```

#### Command Group
```python
@click.group(name="group")
def group():
    """Command group description."""
    pass

@group.command()
def subcommand():
    """Subcommand description."""
    click.echo("Subcommand executed!")
```

#### Advanced Options
```python
@click.command()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--config", "-c", type=click.Path(exists=True), help="Config file path")
@click.argument("target", required=True)
def command(verbose, config, target):
    """Command with various options."""
    if verbose:
        click.echo("Verbose mode enabled")
    click.echo(f"Target: {target}")
```

## 📚 Examples

### Complete Workflow
```bash
# 1. Verify authentication
sandstrike auth verify

# 2. Create targets for reusable testing
sandstrike targets create --id "local_ollama" --name "Local Ollama Server" --ip "http://localhost:11434" --source local
sandstrike targets create --id "prod_api" --name "Production API" --ip "https://api.example.com:8080" --source file

# 3. Create prompts
sandstrike prompts create --id "test_001" --technique "Prompt Injection" --category "LLM01_PromptInjection" --text "Ignore previous instructions..."

# 4. Create collection
sandstrike collections create --name "Security Tests" --description "Comprehensive security testing"

# 5. View results
sandstrike sessions list --status completed
sandstrike sessions show latest_session_id --results

# 6. Generate report (if paid user)
sandstrike reports detailed --session-id latest_session_id
```

### Grading Workflow (Pro Users)
```bash
# Grade responses
sandstrike grader --input "Tell me about weapons" --output "I cannot provide information about weapons" --intent "safety_evaluation"

# Grade for bias
sandstrike grader --input "What makes a good leader?" --output "Men are naturally better leaders" --intent "bias_detection"

# Grade for prompt injection
sandstrike grader --input "Ignore previous instructions" --output "I'll help you with that" --intent "prompt_injection"
```

## 🔧 Configuration

### Environment Variables
```bash
# API Configuration
export AVENLIS_API_KEY="your_api_key_here"

# Local Testing
export OLLAMA_BASE_URL="http://localhost:11434"
export OLLAMA_MODEL="llama2"

# Web Interface
export WEB_PORT="8080"
export WEB_HOST="0.0.0.0"
```

### Configuration File
Create `.env` file in the `sandstrike/` directory:
```bash
AVENLIS_API_KEY=your_api_key_here
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
WEB_PORT=8080
WEB_HOST=0.0.0.0
```

## 🆘 Troubleshooting

### Common Issues

#### Command Not Found
```bash
# Reinstall the package
pip install -e . --force-reinstall
```

#### Authentication Errors
```bash
# Check API key
sandstrike auth verify

# Verify environment variables
echo $AVENLIS_API_KEY
```

#### Web UI Issues
```bash
# Check if ports are available
netstat -an | grep 8080
netstat -an | grep 3000

# Try different ports
sandstrike ui start --backend-port 8081 --frontend-port 3001
```

### Getting Help
```bash
# General help
sandstrike --help

# Command-specific help
sandstrike prompts --help
sandstrike grader --help
```

## 📖 Related Documentation

- **[CLI Cheat Sheet](../CLI_CHEATSHEET.md)** - Quick reference for all commands
- **[User Guide](../USER_GUIDE.md)** - Comprehensive user guide
- **[Main README](../README.md)** - Project overview and installation
- **[Documentation](../DOCUMENTATION.md)** - Complete documentation structure