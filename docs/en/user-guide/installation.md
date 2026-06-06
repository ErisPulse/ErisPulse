# Installation and Configuration

This guide introduces how to install ErisPulse and configure your project.

## System Requirements

- Python 3.10 or higher version (recommended 3.10 - 3.13)
- pip or uv (recommended)
- sufficient disk space (at least 100MB)

## Installation Methods

### Method 1: Install via pip

```bash
# Install ErisPulse
pip install ErisPulse

# Upgrade to the latest version
pip install ErisPulse --upgrade
```

### Method 2: Install via uv (Recommended)

uv is a faster Python toolchain, recommended for development environments.

#### Install uv

```bash
# Install uv using pip
pip install uv

# Verify installation
uv --version
```

#### Create Virtual Environment

```bash
# Create project directory
mkdir my_bot && cd my_bot

# Install Python 3.12
uv python install 3.12

# Create virtual environment
uv venv
```

#### Activate Virtual Environment

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

## Project Initialization

### Interactive Initialization

```bash
epsdk init
```

Follow the prompts to complete:
1. Enter project name
2. Select log level
3. Configure server parameters
4. Select adapter
5. Configure adapter parameters

### Quick Initialization

```bash
# Quick mode, skip interactive configuration
epsdk init -q -n my_bot
```

### Configuration Description

A `config/config.toml` file will be generated after initialization:

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000

[ErisPulse.logger]
level = "INFO"

[ErisPulse.framework]
enable_lazy_loading = true

```

## Module Installation

### Install from Remote Repository

```bash
# Install a specific module
epsdk install Yunhu

# Install multiple modules
epsdk install Yunhu Weather
```

### Install from Local

```bash
# Install local module
epsdk install ./my-module
```

### Interactive Installation

```bash
# Enter interactive installation without specifying a package name
epsdk install
```

## Verify Installation

### Check Installation

```bash
# Check ErisPulse version
epsdk --version
```

### Run Tests

```bash
# Run project
epsdk run main.py
```

If you see similar output, the installation is successful:

```
[INFO] Initializing ErisPulse...
[INFO] Adapter loaded: Yunhu
[INFO] Module loaded: MyModule
[INFO] ErisPulse initialization complete
```

## Common Issues

### Installation Failed

1. Check if Python version is >= 3.10 (recommended 3.10 - 3.13)
2. Try using `uv pip install ErisPulse` instead of `pip install`
3. If you encounter permission errors, try `pip install --user ErisPulse` or use a virtual environment
4. If you encounter SSL certificate errors in an enterprise proxy environment, try `pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org ErisPulse`
5. Ensure network connection is normal and pip sources are accessible

### Configuration Errors

1. Check if `config.toml` syntax is correct (TOML format is sensitive to indentation and quotes)
2. Confirm all required configuration items are filled in
3. Check terminal logs for detailed error information
4. Use `epsdk init` to regenerate the configuration file

### Module Installation Failed

1. Confirm if the module name spelling is correct (case sensitive)
2. Check network connection
3. Use `epsdk list-remote` to view the list of available modules
4. Confirm if the module is compatible with your current SDK version

### Windows PowerShell Execution Policy

If PowerShell prompts "Cannot load file... because running scripts is disabled on this system":

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Next Steps

- [CLI Command Reference](cli-reference.md) - Learn all CLI commands
- [Configuration File Explanation](configuration.md) - Learn detailed configuration options