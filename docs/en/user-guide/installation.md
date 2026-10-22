# Installation Reference

> [!TIP]
> **When to read this**: Read this when you need to choose an installation method (pip / uv / Docker / ErisPulse-App client) or troubleshoot a failed installation. If you just want to get up and running as quickly as possible, the [5-Minute Quick Start](../quick-start.md) already covers the simplest process — skip this page if that's all you need.

## System Requirements

- Python 3.10 – 3.14 (the 3.14t free-threading / no-GIL build is supported experimentally; the framework continuously monitors it via experimental CI smoke tests, without a formal commitment)
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
# Install uv with pip
pip install uv

# Verify installation
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

### Method 3: Install with uv tool (Global CLI, Recommended)

If you only want to use `epsdk` as a global command-line tool, `uv tool install` is the cleanest approach—epsdk runs in an isolated tool environment, without polluting any project environment:

```bash
# Install (epsdk is immediately available, no need to activate any virtual environment)
uv tool install ErisPulse

# Upgrade (or use `epsdk self-update`, which automatically uses this channel)
uv tool upgrade ErisPulse
```

> [!NOTE]
> The epsdk in the tool environment will automatically detect the project’s `.venv` when running within the project directory:
> `epsdk install` will install components into the project environment, and `epsdk run` will use the project environment to run the bot.
> The framework itself remains provided by the tool environment, with no interference between the two.
>
> The one-click installation script (`get.erisdev.com/install.sh` / `install.ps1`) also provides a "Global CLI Installation (uv tool)" option in its menu, which automatically installs uv and guides you through the setup.

## Project Initialization and Module Installation

After installation, the complete workflow for project initialization, module installation, and execution is detailed in [5-Minute Quick Start](../quick-start.md).

### Method 4: Using the ErisPulse-App Client (No Terminal Required)

Don't want to install a Python environment? [ErisPulse-App](../ecosystem/app.md) is the official cross-platform client (Android / Windows / Linux / macOS), allowing you to **run directly on your mobile device**. The desktop version supports minimizing to the system tray for background operation. It includes a built-in Python runtime and ErisPulse SDK, eliminating the need for terminal commands or manual configuration:

- Download the appropriate version from [GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases) based on your platform (Android `online`/`offline` APK, Windows `setup.exe`/`zip`, Linux `tar.gz`, macOS `zip`)
- Create and launch an instance within the App, managing adapters and modules through the native interface and browsing the module store

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

### Installation Failure

1. Check that your Python version is within the supported range (3.10 – 3.14 is supported; 3.14t free-threaded / no-GIL builds are experimentally supported without a formal commitment)
2. Try using `uv pip install ErisPulse` instead of `pip install`
3. If a permission error occurs, try `pip install --user ErisPulse` or use a virtual environment
4. If you encounter SSL certificate errors in a corporate proxy environment, try `pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org ErisPulse`
5. Ensure your network connection is working and the pip index is accessible

### Configuration Errors

1. Check that the `config.toml` syntax is correct (TOML format is sensitive to indentation and quotation marks)
2. Confirm that all required configuration items have been filled in
3. Check the terminal logs for detailed error messages
4. Use `epsdk init` to regenerate the configuration file

### Module Installation Failure

1. Confirm that the module name is spelled correctly (case-sensitive)
2. Check your network connection
3. Use `epsdk list-remote` to view the list of available modules
4. Confirm that the module is compatible with your current SDK version

### Windows PowerShell Execution Policy

If PowerShell shows "cannot be loaded... because running scripts is disabled on this system":

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Debian/Ubuntu Virtual Environment Creation Failure

If the installation script reports "virtual environment creation failed" and the error message contains `ensurepip is not available`, it is because Debian/Ubuntu does not install `python3-venv` by default (the system Python's `ensurepip` is disabled):

```bash
sudo apt install python3.13-venv   # Install the corresponding package for your actual Python version
# Or install the generic metapackage:
sudo apt install python3-venv
```

After installation, simply re-run the installation script. The newer installation script will proactively prompt and attempt to automatically install the corresponding system package when this issue is detected; you can also switch to uv instead (`uv venv` does not depend on `ensurepip`).

## Next Steps

- **To initialize your project and install adapters after installation**: Follow the [5-Minute Quick Start](../quick-start.md) to complete the remaining steps
- **To manage components from the command line in daily use**: Check the [CLI Command Reference](cli-reference.md)
- **To fill in tokens or adjust ports**: See the [Configuration Guide](configuration.md)