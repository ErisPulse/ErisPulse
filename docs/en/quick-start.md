# Quick Start

> Confused by terminology? Check the [Glossary](terminology.md) for easy-to-understand explanations.

## Install ErisPulse

### Install using pip

Ensure your Python version is >= 3.10, then use pip to install ErisPulse:

```bash
pip install ErisPulse
```

### Install using uv (Recommended)

`uv` is a faster Python toolchain and is recommended. If you are unsure what "toolchain" means, think of it as a more efficient tool for installing and managing Python packages.

#### Install uv

```bash
pip install uv
```

#### Create project and install

```bash
uv python install 3.12              # Install Python 3.12
uv venv                             # Create virtual environment
.venv\Scripts\activate               # Activate environment (Windows)
# source .venv/bin/activate          # Linux/Mac
uv pip install ErisPulse --upgrade  # Install framework
```

## Initialize Project

### Interactive Initialization (Recommended)

```bash
epsdk init
```

This will launch an interactive wizard to guide you through:
- Project name setting
- Log level configuration
- Server configuration (host and port)
- Adapter selection and configuration
- Project structure creation

### Quick Initialization

```bash
# Quick mode with specified project name
epsdk init -q -n my_bot

# Or just specify project name
epsdk init -n my_bot
```

### Manual Project Creation

If you prefer to create the project manually:

```bash
mkdir my_bot && cd my_bot
epsdk init
```

## Install Modules

### Install via CLI

```bash
epsdk install Yunhu AIChat
```

### View Available Modules

```bash
epsdk list-remote
```

### Interactive Installation

Enter the interactive installation interface when no package name is specified:

```bash
epsdk install
```

## Run Project

```bash
# Normal run
epsdk run main.py

# Hot reload mode (recommended for development)
epsdk run main.py --reload
```

## Project Structure

Project structure after initialization:

```
my_bot/
├── config/
│   └── config.toml          # Configuration file
└── main.py                  # Entry file

```

## Configuration File

Basic `config.toml` configuration:

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000

[ErisPulse.logger]
level = "INFO"

[Yunhu_Adapter]
# Adapter configuration
```

## Next Steps

- [Getting Started Overview](getting-started/README.md) - Learn the basic concepts of ErisPulse
- [Create Your First Bot](getting-started/first-bot.md) - Create a simple bot
- [User Guide](user-guide/) - Deep dive into configuration and module management
- [Developer Guide](developer-guide/) - Develop custom modules and adapters