<div align="center">

![Website](https://img.shields.io/badge/Website-avenlis.staterasolv.com-purple.svg)
[![Join Our Telegram](https://img.shields.io/badge/Join%20Our-Telegram-26A5E4.svg)](https://t.me/+09uMofU9Dc8yOTM1)
[![Follow on LinkedIn](https://img.shields.io/badge/Follow%20on-LinkedIn-0077B5.svg)](https://www.linkedin.com/company/statera-solutionss/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-green.svg)](https://www.apache.org/licenses/LICENSE-2.0)
</div>

---

# Avenlis SandStrike

**Avenlis SandStrike** is a comprehensive Python library and CLI tool for AI red team testing and LLM security assessment. Features include comprehensive adversarial prompt library, automated vulnerability detection, persistent session management, and a modern web interface.

## Features

- **🔒 Advanced Red Teaming**: Comprehensive library of adversarial prompts covering multiple attack techniques
- **📁 Smart Collections**: Organize and manage adversarial prompts with intelligent categorization
- **🎯 Local LLM Testing**: Full Ollama integration for testing local models
- **🌐 Platform Integration**: Fetch prompts from Avenlis platform
- **📊 Session Management**: Track and analyze test results over time
- **🖥️ Modern Web Interface**: React-based UI with real-time updates, no authentication required
- **⚡ CLI Tools**: Powerful command-line interface for automation and scripting
- **🔍 Intelligent Prompt Analysis**: Automatic classification and OWASP mapping
- **💾 Persistent Data**: Save test results and session data locally
- **📈 SandStrike Copilot Grader**: AI-powered response evaluation using production LLM (Pro users only)

## Installation

### From PyPI

```bash
pip install sandstrike
```

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

3. **Open your browser**. `sandstrike ui start` will open the UI automatically (default is `http://localhost:3000`, but it may choose another free port if 3000 is taken).

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

### Team collaboration note (file storage + git)

In this repo, `sandstrike/data/` is **gitignored by default** to avoid committing user-generated/runtime data. Seed files (e.g. `targets.yaml`, `collections.yaml`, `dynamic_variables.yaml`) remain tracked so the project works out of the box.

If your team wants to collaborate by versioning file storage outputs in `sandstrike/data/`, remove the `sandstrike/data/*` rules in `.gitignore`.

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

For API keys and optional overrides, set environment variables (e.g. in a `.env` file):

```bash
# Avenlis Platform / Pro features
AVENLIS_API_KEY=your_api_key_here

# Custom graders (optional)
ANTHROPIC_API_KEY=your_anthropic_key_here
ANTHROPIC_MODEL=your_anthropic_model_here
GEMINI_API_KEY=your_gemini_key_here
GEMINI_MODEL=your_gemini_model_here
```

Targets (including Ollama endpoints/models) are managed in the UI/CLI via `sandstrike/data/targets.yaml`, so you generally don’t need Ollama-related env vars.

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

- **User Guide**: See [`USER_GUIDE.md`](USER_GUIDE.md) for detailed usage instructions
- **CLI Reference**: Use `sandstrike --help` for command information
- **CLI Cheat Sheet**: See [`CLI_CHEATSHEET.md`](CLI_CHEATSHEET.md) for quick command reference
- **Issues**: Report bugs and feature requests on GitHub
- **Telegram**: Join our community for support and discussions: [Avenlis Community](https://t.me/+09uMofU9Dc8yOTM1)

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Avenlis SandStrike** - Empowering AI Security Testing

[Website](https://avenlis.staterasolv.com) • [User Guide](USER_GUIDE.md) • [CLI Reference](CLI_CHEATSHEET.md) • [Install Guide](INSTALL_INSTRUCTIONS.md)

</div>
