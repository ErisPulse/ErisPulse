# Installation Reference

> This document is a **complete reference** for installation methods (pip / uv / Docker / troubleshooting).
> If you just want to get started quickly, [the 5-minute quick start](../quick-start.md) covers the minimal workflow.

## System Requirements

- Python 3.10 or higher
- pip or uv (recommended)
- Sufficient disk space (at least 100MB)

## Installation Methods

### Method 1: Install Using pip

```bash
# Install ErisPulse
pip install ErisPulse

# Upgrade to the latest version
pip install ErisPulse --upgrade
```

### Method 2: Install Using uv (Recommended)

uv is a faster Python toolchain, recommended for development environments.

#### Install uv

```bash
# Install uv using pip
pip install uv

# Verify the installation
uv --version
```

#### Create a Virtual Environment

```bash
# Create a project directory
mkdir my_bot && cd my_bot

# Install Python 3.12
uv python install 3.12

# Create a virtual environment
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

After installation, the complete workflow for project initialization, module installation, and execution is available in the [5-Minute Quick Start](../quick-start.md).

### Method Three: Using the ErisPulse-App Client (No Terminal Required)

Don't want to install a Python environment? [ErisPulse-App](../ecosystem/app.md) is the official cross-platform client (Android / Windows / Linux / macOS), allowing you to **run directly on your phone**. The desktop version supports minimizing to the system tray for background operation. It comes with a built-in Python runtime and ErisPulse SDK, eliminating the need for a terminal or manual configuration:

- Download the appropriate version from [GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases) based on your platform (Android `online`/`offline` APK, Windows `setup.exe`/`zip`, Linux `tar.gz`, macOS `zip`)
- Create and start an instance within the App, and manage adapters and modules through the native interface, or browse the module store

> For complete instructions, see [ErisPulse-App Installation and Usage](../ecosystem/app.md).

## Verification of Installation

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

## FAQ

### Installation Failed

1. Check that your Python version is >= 3.10 (recommended: 3.10 - 3.13)
2. Try using `uv pip install ErisPulse` instead of `pip install`
3. If you get permission errors, try `pip install --user ErisPulse` or use a virtual environment
4. If you encounter SSL certificate errors in enterprise proxy environments, try `pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org ErisPulse`
5. Ensure your network connection is stable and the pip source is accessible

### Configuration Errors

1. Check that the `config.toml` syntax is correct (TOML format is sensitive to indentation and quotes)
2. Confirm all required configuration items have been filled in
3. Check terminal logs for detailed error messages
4. Use `epsdk init` to regenerate the configuration file

### Module Installation Failed

1. Confirm the module name is spelled correctly (case-sensitive)
2. Check your network connection
3. Use `epsdk list-remote` to view available module lists
4. Confirm the module is compatible with your current SDK version

### Windows PowerShell Execution Policy

If PowerShell prompts "Cannot load the file... because running scripts is disabled on this system":

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Debian/Ubuntu Virtual Environment Creation Failed

If the installation script reports "virtual environment creation failed" and the error message includes `ensurepip is not available`, it is because Debian/Ubuntu does not install `python3-venv` by default (the system Python's `ensurepip` is disabled):

```bash
sudo apt install python3.13-venv   # Install the package corresponding to your actual Python version
# Or install the generic meta-package:
sudo apt install python3-venv
```

After installation, re-run the installation script. The new installation script will automatically detect this issue and prompt to install the corresponding system package; alternatively, you can use uv (`uv venv` does not depend on `ensurepip`).

## Next Steps

- [CLI Command Reference](cli-reference.md) - Learn about all command-line commands
- [Configuration File Guide](configuration.md) - Learn more about configuration options