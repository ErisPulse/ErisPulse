# Installation Reference

> This document is the **complete reference** for installation methods (pip / uv / Docker / Troubleshooting).
> If you just want to get started quickly, [5-Minute Quick Start](../quick-start.md) covers the minimal workflow.

## System Requirements

- Python 3.10 or higher
- pip or uv (recommended)
- Sufficient disk space (at least 100MB)

## Installation Methods

### Method 1: Install using pip

```bash
# Install ErisPulse
pip install ErisPulse

# Upgrade to the latest version
pip install ErisPulse --upgrade
```

### Method 2: Install using uv (Recommended)

uv is a faster Python toolchain and is recommended for development environments.

#### Install uv

```bash
# Install uv using pip
pip install uv

# Verify installation
uv --version
```

#### Create a virtual environment

```bash
# Create project directory
mkdir my_bot && cd my_bot

# Install Python 3.12
uv python install 3.12

# Create virtual environment
uv venv
```

#### Activate virtual environment

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

## Project Initialization and Module Installation

After installation, please refer to the [5-Minute Quick Start](../quick-start.md) for the complete workflow of project initialization, module installation, and running.

### Method 3: Using the ErisPulse-App Client (Terminal-Free)

Don't want to set up a Python environment? [ErisPulse-App](../ecosystem/app.md) is the official cross-platform client
(Android / Windows / Linux / macOS) that runs **directly on your phone**; the desktop version supports minimizing to
the system tray for background operation; it includes a built-in Python runtime and ErisPulse SDK, no terminal or manual configuration required:

- Download according to your platform from [GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases)
  (Android `online`/`offline` APK, Windows `setup.exe`/`zip`, Linux `tar.gz`, macOS `zip`)
- Create and start an instance within the App, and manage adapters and modules, as well as browse the module store, via the native interface

> For detailed instructions, see [ErisPulse-App Installation and Usage](../ecosystem/app.md).

Please return the complete translated Markdown content directly, without including any other text.

## Verify Installation

### Check Installation

```bash
# Check ErisPulse version
epsdk --version
```

### Run Tests

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

Please return the complete translated Markdown content directly, without including any other text.

Reminder: If the document contains language switch lines (lines where language names are separated by `` | ``), please strictly follow the format requirements in point 8 above and do not write incorrect formats like ``[**Label**](file)``.

## FAQ

### Installation Failure

1. Check if Python version >= 3.10 (recommended 3.10 - 3.13)
2. Try using `uv pip install ErisPulse` instead of `pip install`
3. If permission error is prompted, try `pip install --user ErisPulse` or use a virtual environment
4. If encountering SSL certificate error in a corporate proxy environment, try `pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org ErisPulse`
5. Ensure network connection is normal and pip source is accessible

### Configuration Errors

1. Check if `config.toml` syntax is correct (TOML format is sensitive to indentation and quotes)
2. Confirm that all required configuration items have been filled
3. View terminal logs for detailed error information
4. Use `epsdk init` to regenerate the configuration file

### Module Installation Failure

1. Confirm the module name spelling is correct (case sensitive)
2. Check network connection
3. Use `epsdk list-remote` to view the list of available modules
4. Confirm the module is compatible with your current SDK version

### Windows PowerShell Execution Policy

If PowerShell prompts "cannot load file... because running scripts is disabled on this system":

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

## Next Steps

- [CLI Command Reference](cli-reference.md) - Learn about all command-line commands
- [Configuration Guide](configuration.md) - Get detailed information about configuration options