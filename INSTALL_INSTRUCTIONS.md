# Installation Instructions

## Uninstalling Old Package

To uninstall the old package, run:

```bash
pip uninstall sandstrike
```

If you installed it in development mode (`pip install -e .`), you may also need to remove it:

```bash
pip uninstall sandstrike -y
```

## Installing SandStrike

### Option 1: Install in Development Mode (Recommended for Development)

If you're developing or modifying the code:

```bash
# Navigate to the project directory
cd /path/to/sandstrikeLibraryTest

# Install in editable/development mode
pip install -e .
```

This will:
- Install the package in editable mode (changes to code are immediately available)
- Create the `sandstrike` CLI command

### Option 2: Install from Source

If you want a regular installation:

```bash
# Navigate to the project directory
cd /path/to/sandstrikeLibraryTest

# Build and install
pip install .
```

### Option 3: Install from Local Wheel

```bash
# Build the package
python -m build

# Install the wheel
pip install dist/avenlis-*.whl
```

## Verify Installation

After installation, verify that the `sandstrike` command is available:

```bash
sandstrike --version
sandstrike --help
```

You should see the SandStrike CLI help menu.

## Troubleshooting

### Command Not Found

If `sandstrike` command is not found after installation:

1. **Check Python environment**: Make sure you're using the correct Python environment
   ```bash
   which python
   which pip
   ```

2. **Check installation location**: Verify the package was installed
   ```bash
   pip show sandstrike
   ```

3. **Reinstall**: Try uninstalling and reinstalling
   ```bash
   pip uninstall sandstrike -y
   pip install -e .
   ```

### Old Command Still Works

If you previously had a different version installed:

```bash
# Force uninstall any old versions
pip uninstall sandstrike -y
pip uninstall avenlis -y

# Check for any remaining references
pip list | grep -i sandstrike
pip list | grep -i avenlis

# Reinstall
pip install -e .
```

### Multiple Python Environments

If you have multiple Python environments (venv, conda, etc.):

1. Activate the correct environment first
2. Then uninstall and reinstall

```bash
# Example with venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

pip uninstall sandstrike -y
pip install -e .
```

## What Changed

- **CLI Command**: `sandstrike`
- **Package Name**: `sandstrike` (for Python imports)
- **All CLI Examples**: Use `sandstrike` command

## Next Steps

After installation, you can start using SandStrike:

```bash
# Verify authentication (requires AVENLIS_API_KEY environment variable)
sandstrike auth verify

# Start the web UI (backend on 8080, frontend on 3000)
sandstrike ui start

# List prompts
sandstrike prompts list

# List sessions
sandstrike sessions list

# List targets
sandstrike targets list

# List collections
sandstrike collections list

# Get help
sandstrike --help
```

## Web UI Setup

The web UI requires Node.js (v16+) for the React frontend:

```bash
# Check Node.js version
node --version

# The first time you run `sandstrike ui start`, it will:
# 1. Install npm dependencies automatically if needed
# 2. Start the Flask backend on port 8080
# 3. Start the React frontend on port 3000
# 4. Open your browser to http://localhost:3000
```

## Environment Variables

Set the following environment variables for full functionality:

```bash
# Required for authenticated features (reports, grading)
export AVENLIS_API_KEY=your_api_key_here

# Optional: Custom Ollama URL (default: http://localhost:11434)
export OLLAMA_BASE_URL=http://localhost:11434
```

On Windows (PowerShell):
```powershell
$env:AVENLIS_API_KEY = "your_api_key_here"
```

