<div align="center">

<img src="https://raw.githubusercontent.com/StateraSolutions/avenlis-sandstrike/main/sandstrike/images/sandstrike_white.png" alt="SandStrike Logo" width="300">

</div>

<div align="center">

![Website](https://img.shields.io/badge/Website-avenlis.staterasolv.com-purple.svg)
[![Join Our Discord](https://img.shields.io/badge/Join%20Our-Discord-5865F2.svg)](https://discord.gg/FzYTgxM5Db)
[![Follow on LinkedIn](https://img.shields.io/badge/Follow%20on-LinkedIn-0077B5.svg)](https://www.linkedin.com/company/statera-solutionss/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-green.svg)](https://www.apache.org/licenses/LICENSE-2.0)
</div>

---

# Avenlis SandStrike

**Avenlis SandStrike** is a comprehensive Python library and CLI tool for AI red team testing and LLM security assessment. Features include comprehensive adversarial prompt library, automated vulnerability detection, persistent session management, and a modern web interface.

## Features

- **🔒 Advanced Red Teaming**: Comprehensive library of adversarial prompts covering multiple attack techniques
- **🔧 Encoding Support**: Coming soon (currently not available)
- **📁 Smart Collections**: Organize and manage adversarial prompts with intelligent categorization
- **🎯 Local LLM Testing**: Full Ollama integration for testing local models
- **🌐 Platform Integration**: Fetch prompts from Avenlis platform
- **📊 Session Management**: Track and analyze test results over time
- **🖥️ Modern Web Interface**: React-based UI with real-time updates, no authentication required
- **⚡ CLI Tools**: Powerful command-line interface for automation and scripting
- **🔍 Intelligent Prompt Analysis**: Automatic classification and OWASP mapping
- **💾 Persistent Data**: Save test results and session data locally (encoding persistence coming soon)
- **📈 SandStrike Copilot Grader**: AI-powered response evaluation using production LLM (Pro users only)

## Installation

### From Source

```bash
git clone https://github.com/StateraSolutions/avenlis-sandstrike.git
cd avenlis-sandstrike
pip install -e .
```

## Quick Start

1. **Install the package**:
```bash
pip install -e .
```

2. **Start the web interface**:
```bash
sandstrike ui start
```

3. **Open your browser** and navigate to `http://localhost:3000`

## Usage

### Web Interface

Start the web interface:
```bash
sandstrike ui start                    # Start on default port
sandstrike ui start --port 3000        # Start on custom port
```

The web interface provides:
- **Dashboard**: Real-time overview of security metrics
- **Sessions**: View and manage testing sessions with detailed analytics
- **Collections**: Organize prompts into logical groups
- **Prompts**: Browse and manage adversarial prompts
- **OWASP LLM & MITRE ATLAS**: Browse industry-standard vulnerability frameworks

### CLI Commands

```bash
# Authentication
sandstrike auth verify

# Prompt Management
sandstrike prompts list
sandstrike prompts create --id ID --technique TECH --category CAT --text TEXT --source local
sandstrike prompts view PROMPT_ID
sandstrike prompts delete PROMPT_ID

# Collections Management
sandstrike collections list
sandstrike collections create --name "Custom Tests" --description "My test suite" --source local
sandstrike collections add-prompt --collection-id ID --collection-source local --prompt-ids prompt1,prompt2 --prompt-source file
sandstrike collections remove-prompt --collection-id ID --collection-source local --prompt-ids prompt1
sandstrike collections delete COLLECTION_ID

# Target Management
sandstrike targets list
sandstrike targets create --id TARGET_ID --name "My Target" --ip "http://localhost:11434" --source local
sandstrike targets view --target-ids TARGET_ID --source local
sandstrike targets delete --target-ids TARGET_ID --source local

# Session Management
sandstrike sessions list
sandstrike sessions show SESSION_ID --detailed

# Reports (Pro users only)
sandstrike reports overview --session-id session_1,session_2
sandstrike reports detailed --source file
sandstrike reports executive --session-id session_1,session_2
sandstrike reports all --session-id session_1,session_2

# Dynamic Variables
sandstrike variables list --source all
sandstrike variables set --category application --name banking_app --value "SecureBank" --source local
sandstrike variables update --category application --name banking_app --value "NewName" --source local

# Database Management
sandstrike database status
sandstrike database local-wipe

# Get help
sandstrike --help
sandstrike [command] --help
```

### Python API

```python
from sandstrike.redteam import AvenlisRedteam, RedteamSession
from sandstrike.config import AvenlisConfig
from sandstrike.main_storage import AvenlisStorage

# Configuration
config = AvenlisConfig()

# Red Team Testing
redteam = AvenlisRedteam()

# Run security tests against Ollama
results = redteam.run_attacks(
    target="ollama://llama3.2:1b@localhost:11434",
    prompt_ids=["prompt_001", "prompt_002"]
)

print(f"Attack success rate: {results['summary']['success_rate']:.1f}%")

# Session management
session = RedteamSession.create("Security Audit", "ollama://llama3.2:1b@localhost:11434")

# Storage and data management
storage = AvenlisStorage(config)
sessions = storage.get_combined_sessions()
prompts = storage.get_combined_prompts()
```


## Configuration

**Targets (including Ollama endpoints/models)** are defined in [`sandstrike/data/targets.yaml`](sandstrike/data/targets.yaml) and can be managed via the CLI/UI, so you don’t need to configure Ollama-related env vars.

For API keys and optional overrides, set environment variables (e.g. in a `.env` file):

```bash
# Avenlis Platform / Pro features
AVENLIS_API_KEY=your_api_key_here

# Custom graders (optional)
OPENAI_API_KEY=your_openai_key_here
GEMINI_API_KEY=your_gemini_key_here
```

Environment variables are used for API keys; other settings use defaults or `sandstrike/data/targets.yaml`.

## Troubleshooting

### Web Interface Not Starting
```bash
sandstrike ui start --port 3000  # Try different port
```

### Import Errors
```bash
pip install -e . --force-reinstall
```

### Database Issues
```bash
sandstrike database status
sandstrike database local-wipe
```

## Getting Help

- **User Guide**: See [`documentation/USER_GUIDE.md`](documentation/USER_GUIDE.md) for detailed usage instructions
- **CLI Reference**: Use `sandstrike --help` for command information
- **CLI Cheat Sheet**: See [`documentation/CLI_CHEATSHEET.md`](documentation/CLI_CHEATSHEET.md) for quick command reference
- **Issues**: Report bugs and feature requests on GitHub
- **Discord**: Join our community for support and discussions

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Avenlis SandStrike** - Empowering AI Security Testing

[Website](https://avenlis.staterasolv.com) • [User Guide](documentation/USER_GUIDE.md) • [CLI Reference](documentation/CLI_CHEATSHEET.md) • [Install Guide](documentation/INSTALL_INSTRUCTIONS.md)

</div>
