# Installation Reference

> This document is a **complete reference** for installation methods (pip / uv / Docker / troubleshooting).
> If you just want to get started quickly, [5-Minute Quick Start](../quick-start.md) covers the minimal process.

## System Requirements

- Python 3.10 or higher
- pip or uv (recommended)
- Sufficient disk space (at least 100MB)

## Installation Methods

### Method 1: Install with pip

```bash
# Install ErisPulse
pip install ErisPulse

# Upgrade to the latest version
pip install ErisPulse --upgrade
```

### Method 2: Install with uv (Recommended)

uv is a faster Python toolchain, recommended for development environments.

#### Install uv

```bash
# Install uv using pip
pip install uv

# Verify installation
uv --version
```

#### Create a Virtual Environment

```bash
# Create project directory
mkdir my_bot && cd my_bot

# Install Python 3.12
uv python install 3.12

# Create virtual environment
uv venv
```

#### Activate the Virtual Environment

```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

#### Install ErisPulse

```bash
# Install ErisPulse
uv pip install ErisPulse --upgrade
```

## Project Initialization and Module Installation

After installation, the complete workflow for project initialization, module installation, and running is covered in [5-Minute Quick Start](../quick-start.md).

## Verify Installation

### Check Installation

```bash
# Check ErisPulse version
epsdk --version
```

### Run a Test

```bash
# Run the project
epsdk run main.py
```

If you see output similar to the following, the installation was successful:

```
[INFO] Initializing ErisPulse...
[INFO] Adapter loaded: Yunhu
[INFO] Module loaded: MyModule
[INFO] ErisPulse initialization complete
```

## Common Issues

### Installation Failure

1. Check that Python version is >= 3.10 (recommended 3.10 - 3.13)
2. Try using `uv pip install ErisPulse` instead of `pip install`
3. If permission errors occur, try `pip install --user ErisPulse` or use a virtual environment
4. If SSL certificate errors occur in a corporate proxy environment, try `pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org ErisPulse`
5. Ensure network connectivity is normal and the pip source is accessible

### Configuration Errors

1. Check that the `config.toml` syntax is correct (TOML format is sensitive to indentation and quotes)
2. Confirm all required configuration items are filled in
3. Check terminal logs for detailed error messages
4. Use `epsdk init` to regenerate the configuration file

### Module Installation Failure

1. Confirm the module name is spelled correctly (case-sensitive)
2. Check network connectivity
3. Use `epsdk list-remote` to view available module lists
4. Confirm the module is compatible with your current SDK version

### Windows PowerShell Execution Policy

If PowerShell prompts "Cannot load file... because running scripts is disabled on this system":

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Next Steps

- [CLI Command Reference](cli-reference.md) - Learn about all command-line commands
- [Configuration File Guide](configuration.md) - Learn about configuration options in detail