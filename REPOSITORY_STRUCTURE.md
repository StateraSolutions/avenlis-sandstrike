# Repository Structure

```
avenlisLibraryTest/
├── sandstrike/                    # Main Python package
│   ├── __init__.py               # Package initialization (version 1.0.0)
│   ├── __main__.py               # Module entry point
│   ├── api.py                    # API client
│   ├── auth.py                   # Authentication
│   ├── config.py                 # Configuration management
│   ├── server.py                 # Flask backend server
│   ├── main_storage.py           # Main storage interface
│   ├── sandstrike_auth.py        # SandStrike authentication
│   ├── llm_providers.py          # LLM provider integrations
│   ├── exceptions.py             # Custom exceptions
│   │
│   ├── cli/                      # CLI commands
│   │   ├── main.py               # CLI entry point
│   │   └── commands/             # Command modules
│   │       ├── auth.py           # Authentication commands
│   │       ├── prompts.py        # Prompt management
│   │       ├── collections.py    # Collection management
│   │       ├── sessions.py       # Session management
│   │       ├── targets.py        # Target management
│   │       ├── reports.py        # Report generation (Pro)
│   │       ├── variables.py      # Dynamic variables
│   │       ├── database.py       # Database management
│   │       ├── grader.py         # Response grading (Pro)
│   │       └── ui.py             # Web UI launcher
│   │
│   ├── redteam/                  # Red teaming functionality
│   │   ├── core.py               # Core attack modules
│   │   ├── session.py            # Session management
│   │
│   ├── grading/                  # Response grading
│   │   ├── grading_engine.py     # Grading engine
│   │   ├── assertions.py         # Assertion framework
│   │   ├── providers.py          # Grading providers
│   │   └── config.py             # Grading configuration
│   │
│   ├── storage/                  # Data persistence
│   │   ├── database.py           # SQLite database
│   │   ├── yaml_loader.py        # YAML file loader
│   │   └── hybrid_storage.py     # Hybrid storage
│   │

│   │
│   ├── web-ui/                   # React frontend
│   │   ├── src/
│   │   │   ├── pages/            # Page components
│   │   │   │   ├── Dashboard.tsx
│   │   │   │   ├── Scan.tsx
│   │   │   │   ├── Sessions.tsx
│   │   │   │   ├── Collections.tsx
│   │   │   │   ├── Prompts.tsx
│   │   │   │   ├── Targets.tsx
│   │   │   │   ├── Reports.tsx
│   │   │   │   ├── MitreAtlas.tsx
│   │   │   │   └── OwaspLlm.tsx
│   │   │   ├── components/       # Reusable components
│   │   │   └── contexts/         # React contexts
│   │   ├── package.json
│   │   └── vite.config.ts
│   │
│   ├── reports/                  # Generated HTML reports
│   │   └── html_generator.py     # HTML report generator
│   │
│   ├── data/                     # YAML data files
│   │   ├── sessions.json         # Session storage
│   │   ├── collections.yaml      # Collections
│   │   ├── targets.yaml          # Scan targets
│   │   ├── dynamic_variables.yaml
│   │   ├── gradingIntents.yaml
│   │   └── prompts/              # Adversarial prompts
│   │       ├── sample_prompts_primary.yaml
│   │       └── sample_prompts_additional.yaml
│   │
│   ├── info/                     # Security framework documentation
│   │   ├── ATLAS.yaml            # MITRE ATLAS data
│   │   ├── LLM01_PromptInjection.md
│   │   ├── LLM02_SensitiveInformationDisclosure.md
│   │   └── ... (OWASP Top 10 LLM docs)
│   │
│   ├── templates/                # YAML templates
│   │   ├── adversarial_prompts_template.yaml
│   │   ├── collection_template.yaml
│   │   ├── session_config_template.yaml
│   │   └── sessions_template.json
│   │
│   ├── schemas/                  # Data validation schemas
│   │   └── yaml_schemas.py
│   │
│   ├── utils/                    # Utilities
│   │   ├── logging.py
│   │   └── validation.py
│   │
│   └── images/                   # Static images
│       ├── sandstrike_white.png
│       ├── avenlis_icon.png
│       ├── mitre_atlas.png
│       └── owasp_llm.png
│
├── tests/                        # Test suite
│   ├── test_auth.py
│   ├── test_avenlis_main.py
│   ├── collections/
│   ├── prompts/
│   ├── sessions/
│   ├── targets/
│   ├── reports/
│   └── variables/
│
├── avenlis_config.yaml           # Configuration file
├── pyproject.toml                # Project metadata & dependencies
├── requirements.txt              # Dependencies
├── README.md                     # Main documentation
├── USER_GUIDE.md                 # User guide
├── CLI_CHEATSHEET.md             # CLI quick reference
├── CLI_TESTING_GUIDE.md          # CLI testing guide
├── INSTALL_INSTRUCTIONS.md       # Installation guide
├── REPOSITORY_STRUCTURE.md       # This file
├── LICENSE                       # Apache 2.0
└── .gitignore                    # Git ignore rules
```

## Key Directories

| Directory | Purpose |
|-----------|---------|
| `sandstrike/cli/` | CLI commands (prompts, collections, sessions, targets, reports, etc.) |
| `sandstrike/web-ui/` | React frontend for web interface |
| `sandstrike/data/` | YAML/JSON data storage |
| `sandstrike/storage/` | Database and storage abstraction |
| `sandstrike/grading/` | AI-powered response evaluation |
| `sandstrike/redteam/` | Red teaming core functionality |
| `sandstrike/encoding/` | 20+ encoding methods for prompt obfuscation |
| `sandstrike/info/` | OWASP Top 10 LLM and MITRE ATLAS documentation |
| `tests/` | Comprehensive test suite |

## CLI Commands Available

| Command Group | Description |
|---------------|-------------|
| `sandstrike prompts` | Manage adversarial prompts |
| `sandstrike collections` | Manage prompt collections |
| `sandstrike sessions` | View test sessions |
| `sandstrike targets` | Manage scan targets |
| `sandstrike reports` | Generate HTML reports (Pro) |
| `sandstrike variables` | Manage dynamic variables |
| `sandstrike database` | Database management |
| `sandstrike auth` | Authentication |
| `sandstrike ui` | Start web interface |

