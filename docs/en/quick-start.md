# Quick Start

> Confused by terminology? Check the [Glossary](terminology.md) for easy-to-understand explanations.

## Install ErisPulse

### One-click Installation Script (Recommended)

The installation script will automatically detect your environment (Docker, Python, uv) and guide you to choose the most suitable installation method.

Windows (PowerShell):
```powershell
irm https://get.erisdev.com/install.ps1 -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1
```

macOS / Linux:
```bash
curl -fsSL https://get.erisdev.com/install.sh | bash
```

The script will guide you through:

- **Docker installation** (Recommended when Docker is detected): Select image source (Docker Hub / GHCR), version channel (Stable / Pre-release), Dashboard management panel configuration, port settings
- **Traditional installation**: Automatically create virtual environment, select ErisPulse version, optionally install Dashboard management panel module

### Using Docker

Docker images come pre-built with the ErisPulse framework and Dashboard management panel.

```bash
# Download docker-compose.yml
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Set Dashboard token and start
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

<details>
<summary>Docker Hub Not Available?</summary>

Use the GitHub Container Registry image by modifying the `image` in `docker-compose.yml`:

```yaml
image: ghcr.io/erispulse/erispulse:latest
```

</details>

After starting, access `http://<host>:8000/Dashboard` and log in with the set token.

### Install using pip

Ensure your Python version is >= 3.10, then use pip to install:

```bash
pip install ErisPulse
```

If you have [uv](https://github.com/astral-sh/uv) installed, you can also use `uv pip install ErisPulse`, which is faster.

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