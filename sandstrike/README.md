# Avenlis Core Package

This directory contains the core functionality of the Avenlis SandStrike library - a comprehensive Python toolkit for red team testing of Large Language Models (LLMs).

## 🚀 What's New (Latest Updates)

### ✨ Enhanced Web Interface (`server.py`)
- **Modern UI Design**: Beautiful, responsive interface with improved user experience
- **No Authentication Required**: Streamlined access without login barriers
- **Smart Prompt Management**: Advanced prompt overlay with detailed information display
- **Intelligent Title Generation**: Descriptive titles for prompts without IDs

### 🔧 Improved Data Management (`storage.py`)
- **Consolidated Prompt Database**: Single `adversarial_prompts.json` file with comprehensive classification
- **Advanced Attack Classification**: 3 attack techniques, 7 vulnerability categories with subcategories
- **OWASP Top 10 LLM Integration**: Mapping to industry-standard vulnerability frameworks
- **Smart Collections**: Organize prompts by attack type, vulnerability, and severity

### 🎯 Enhanced Red Team Capabilities (`redteam/`)
- **Real-time Testing**: Immediate feedback and result tracking
- **Comprehensive Reporting**: Detailed vulnerability analysis and success rates

## 📁 Directory Structure

```
avenlis/
├── __init__.py              # Package initialization and main exports
├── __main__.py              # CLI entry point (enables `python -m avenlis`)
├── api.py                   # API client for Avenlis services
├── auth.py                  # Authentication and credential management
├── config.py                # Configuration management and environment variables
├── exceptions.py            # Custom exception classes
├── server.py                # Flask web server for modern UI
├── storage.py               # Local data storage and prompt management
├── cli/                     # Command-line interface components
├── redteam/                 # Red team testing framework
└── utils/                   # Utility functions and helpers
```

## 🔧 **Core Components**

### **Web Interface (`server.py`)**
- **Modern Flask Server**: Beautiful, responsive web interface
- **No Authentication**: Start testing immediately without login barriers
- **Smart Prompt Overlays**: Detailed information display
- **Real-time Updates**: See results as they happen
- **Collection Management**: Organize prompts into logical groups

### **Red Team Engine (`redteam/`)**
- **Prompts & Collections**: Comprehensive library of security test prompts
- **Session Management**: Persistent testing sessions with results tracking
- **Target Integration**: Support for Ollama, Anthropic, and custom HTTP endpoints
- **OWASP Integration**: Mapping to industry-standard vulnerability frameworks

### **Storage System (`storage.py`)**
- **Local Data Management**: Load and manage adversarial prompts and collections
- **Prompt Collections**: Organize and manage prompts by attack type and vulnerability
- **Data Classification**: Advanced categorization with attack techniques and vulnerability types

### **Authentication (`auth.py`)**
- **Purpose**: Manages API keys and user authentication (optional for web interface)
- **Features**: 
  - Secure keyring storage
  - Token validation
  - Mock authentication for testing
- **Usage**: `AvenlisAuth()` class provides login/logout functionality

### **Configuration (`config.py`)**
- **Purpose**: Centralized configuration management
- **Features**:
  - Environment variable loading
  - .env file support
  - Default settings
- **Usage**: `AvenlisConfig()` loads settings from various sources

### **API Client (`api.py`)**
- **Purpose**: Client for interacting with Avenlis backend services
- **Features**:
  - HTTP client with retry logic
  - Error handling
  - Rate limiting
- **Usage**: `AvenlisAPI()` for making service calls

## 🚀 Getting Started

### Quick Start with Web Interface
```bash
# Start the web interface
sandstrike ui start

# Your browser will open automatically (default http://localhost:3000; may choose another free port)
# Start testing immediately - no authentication required!
```

### Import the Library
```python
from sandstrike import AvenlisAPI, AvenlisAuth, AvenlisConfig
from sandstrike.redteam import AvenlisRedteam
from sandstrike.server import AvenlisServer
from sandstrike.main_storage import AvenlisStorage
```

### Basic Usage
```python
# Authentication (optional)
auth = AvenlisAuth()
if auth.is_authenticated():
    user = auth.get_current_user()

# Configuration
config = AvenlisConfig()
ollama_url = config.get('AVENLIS_OLLAMA_ENDPOINT')

# Red Team Testing
redteam = AvenlisRedteam()
results = redteam.evaluate_attacks(
    target="ollama://qwen3:1.7b",
    attack_prompts=["prompt-injection", "prompt-probing"]
)

# Storage and Data Management
storage = AvenlisStorage()
prompts = storage.get_all_prompts()
collections = storage.get_collections()
```

## 🌟 Key Features

### **Modern Web Interface**
- **No Authentication Required**: Start testing immediately
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Smart Prompt Overlays**: Detailed prompt information overlays
- **Real-time Updates**: See results as they happen
- **Collection Management**: Organize prompts logically

### **Advanced Data Management**
- **Consolidated Database**: Single source of truth for prompts
- **Intelligent Classification**: Attack techniques and vulnerability categories
- **OWASP Integration**: Industry-standard vulnerability mapping
- **Persistent Storage**: Save test results

### **Comprehensive Red Team Testing**
- **20+ Security Prompts**: Comprehensive security testing
- **Real-time Results**: Immediate feedback and analysis
- **Session Management**: Track and analyze test sessions

## 🔧 Development

### **Running the Web Interface**
```bash
# Development mode
sandstrike ui start

# Production mode
export FLASK_ENV=production
sandstrike ui start
```

### **Testing**
```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_auth.py

# Run with coverage
python -m pytest --cov=avenlis
```

### **Code Structure**
- **Modular Design**: Each component is self-contained
- **Clear Interfaces**: Well-defined APIs between components
- **Error Handling**: Comprehensive exception management
- **Logging**: Detailed logging for debugging and monitoring

## 📊 Data Structure

### **Attack Classification System**
The library now uses a comprehensive classification system:

#### **Attack Techniques**
1. **Prompt Probing**: Extract system information and configuration details
2. **Prompt Injection**: Bypass safety measures and content filters
3. **Text Completion**: Direct generation of harmful content

#### **Vulnerability Categories**
1. **Sensitive Information Disclosure** (LLM02:2025)
2. **System Prompt Leakage** (LLM07:2025)
3. **Biasness** (Gender, Age, Racial)
4. **Firearms and Weapons**
5. **Harassment**
6. **Illegal Criminal Activity**
7. **Misinformation** (LLM09:2025)
8. **Toxicity**
9. **Violence and Self-harm**

### **OWASP Top 10 LLM Integration**
Each prompt is mapped to relevant OWASP LLM vulnerabilities:
- **LLM01:2025**: Prompt Injection
- **LLM02:2025**: Sensitive Information Disclosure
- **LLM07:2025**: System Prompt Leakage
- **LLM09:2025**: Misinformation

## 🔍 Architecture Overview

### **Component Relationships**
```
Web Interface (server.py)
    ↓
Storage Layer (storage.py)
    ↓
Red Team Engine (redteam/)
    ↓
Data Files (JSON)
```

### **Data Flow**
1. **Web Interface**: User interacts with prompts and collections
2. **Storage Layer**: Loads and manages prompt data
3. **Red Team Engine**: Executes attacks against configured targets
4. **Results**: Stored and displayed in real-time

### **Extension Points**
- **Custom Security Prompts**: Add new security test patterns
- **Custom Evaluation Patterns**: Modify vulnerability detection
- **Custom Data Sources**: Integrate with external systems

## 🛠️ Configuration

### **Environment Variables**
```bash
# Avenlis Platform Configuration
AVENLIS_API_URL=https://api.avenlis.com
AVENLIS_API_KEY=your_api_key_here

# Local Testing Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:1.7b

# Web Interface Configuration
WEB_PORT=8080
WEB_HOST=0.0.0.0
```

### **Configuration File**
The library automatically loads configuration from:
1. Environment variables
2. `.env` file in the `avenlis/` directory
3. Default values

## 🚨 Security Considerations

### **Local Data Storage**
- **Privacy**: All data stays on your device
- **No External Calls**: Web interface runs completely locally
- **Secure Storage**: Data stored in local SQLite database

### **Authentication (Optional)**
- **Web Interface**: No authentication required for basic usage
- **CLI Commands**: May require authentication for platform features
- **API Keys**: Stored securely in environment variables

## 📚 Additional Resources

- **[Main README](../README.md)**: Project overview and installation
- **[Documentation](../DOCUMENTATION.md)**: Comprehensive documentation guide
- **[CLI Reference](../CLI_CHEATSHEET.md)**: Command-line interface guide

## 🤝 Contributing

### **Development Setup**
```bash
# Clone the repository
git clone <repository-url>
cd avenlisLibraryTest

# Install in development mode
pip install -e ".[dev]"

# Run tests
python -m pytest
```

### **Code Standards**
- **Python 3.8+**: Modern Python features and syntax
- **Type Hints**: Use type annotations for clarity
- **Docstrings**: Document all public functions and classes
- **Error Handling**: Comprehensive exception management

### **Testing Requirements**
- **Unit Tests**: Test individual components
- **Integration Tests**: Test component interactions
- **Coverage**: Maintain high test coverage
- **Documentation**: Keep docs current with code changes

---

<div align="center">

**Avenlis Core Package** - The heart of AI security testing

[Main README](../README.md) • [Documentation](../DOCUMENTATION.md) • [CLI Reference](../CLI_CHEATSHEET.md)

</div>
