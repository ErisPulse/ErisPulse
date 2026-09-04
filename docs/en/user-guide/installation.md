# Installation Reference

> This document is a **complete reference** for installation methods (pip / uv / Docker / troubleshooting).
> If you just want to get started quickly, [5-minute Quick Start](../quick-start.md) covers the minimal setup.

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

uv is a faster Python toolchain, recommended for development environments.

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

#### Activate the virtual environment

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

After installation, the complete workflow for project initialization, module installation, and running is described in [Quick Start in 5 Minutes](../quick-start.md).

### Method 3: Using the ErisPulse-App Client (No Terminal Required)

Don't want to install a Python environment? [ErisPulse-App](../ecosystem/app.md) is the official cross-platform client (Android / Windows / Linux / macOS), which can be **run directly on your phone**. The desktop version supports minimizing to the system tray for background operation. It includes a built-in Python runtime and ErisPulse SDK, eliminating the need for terminal commands or manual configuration:

- Download from [GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases) according to your platform (Android `online`/`offline` APK, Windows `setup.exe`/`zip`, Linux `tar.gz`, macOS `zip`)
- Create and start an instance within the App, managing adapters and modules through the native interface and browsing the module store

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

If you see similar output, the installation is successful:

```
[INFO] Initializing ErisPulse...
[INFO] Adapter loaded: Yunhu
[INFO] Module loaded: MyModule
[INFO] ErisPulse initialization complete
```

## FAQ

### Installation Failed

1. Check if your Python version is >= 3.10 (recommended 3.10 - 3.13)
2. Try using `uv pip install ErisPulse` instead of `pip install`
3. If you encounter permission errors, try `pip install --user ErisPulse` or use a virtual environment
4. If you encounter SSL certificate errors in an enterprise proxy environment, try `pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org ErisPulse`
5. Ensure your network connection is normal and the pip source is accessible

### Configuration Errors

1. Check if the `config.toml` syntax is correct (TOML format is sensitive to indentation and quotes)
2. Ensure all required configuration items are filled in
3. Check terminal logs for detailed error information
4. Use `epsdk init` to regenerate the configuration file

### Module Installation Failed

1. Confirm the module name is spelled correctly (case-sensitive)
2. Check your network connection
3. Use `epsdk list-remote` to view the list of available modules
4. Ensure the module is compatible with your current SDK version

### Windows PowerShell Execution Policy

If PowerShell prompts "Cannot load the file... because running scripts is disabled on this system":

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Debian/Ubuntu Virtual Environment Creation Failed

If the installation script reports "virtual environment creation failed" and the error message includes `ensurepip is not available`, it is because `python3-venv` is not installed by default on Debian/Ubuntu (the `ensurepip` of the system Python is disabled):

```bash
sudo apt install python3.13-venv   # Install the package corresponding to your actual Python version
# Or install the generic meta package:
sudo apt install python3-venv
```

After installation, re-run the installation script. The new version of the installation script will detect this issue and actively prompt to automatically install the corresponding system package; alternatively, you can use uv (`uv venv` does not depend on `ensurepip`).

## Next Steps

- [CLI Command Reference](cli-reference.md) - Learn about all command-line commands
- [Configuration File Guide](configuration.md) - Learn more about configuration options