# Getting Started

> **This is your first step.** Get an ErisPulse bot up and running from scratch in 5 minutes.
>
> Confused about terms? Check the [Glossary](terminology.md).

## Installing ErisPulse

### One-Click Install Script (Recommended)

The installation script automatically detects your environment (Docker, Python, uv) and guides you to select the best installation method for you.

Windows (PowerShell):
```powershell
irm https://get.erisdev.com/install.ps1 -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1
```

macOS / Linux:
```bash
curl -fsSL https://get.erisdev.com/install.sh -o install.sh && chmod +x install.sh && ./install.sh
```

The script will guide you through:

- **Docker Installation** (Recommended when Docker is detected): Select image source (Docker Hub / GHCR), version channel (Stable / Prerelease), Dashboard configuration, port settings
- **Traditional Installation**: Automatically create virtual environment, select ErisPulse version, optional Dashboard installation

### Using Docker

The Docker image comes with the ErisPulse framework and Dashboard pre-installed.

```bash
# Download docker-compose.yml
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Set Dashboard token and start
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

<details>
<summary>Docker Hub not available?</summary>

Use the GitHub Container Registry image and modify the `image` in `docker-compose.yml`:

```yaml
image: ghcr.io/erispulse/erispulse:latest
```

</details>

After starting, access `http://<host>:8000/Dashboard` and log in with the set token.

### Using pip

Ensure your Python version is >= 3.10, then install using pip:

```bash
pip install ErisPulse
```

If you have [uv](https://github.com/astral-sh/uv) installed, you can also use `uv pip install ErisPulse` for faster installation.

## Initializing Project

### Interactive Initialization (Recommended)

```bash
epsdk init
```

This launches an interactive wizard to guide you through:
- Project name setup
- Log level configuration
- Server configuration (host and port)
- Adapter selection and configuration
- Project structure creation

### Quick Initialization

```bash
# Quick mode specifying project name
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

## Installing Modules

### Install via CLI

```bash
epsdk install Yunhu AIChat
```

### List Available Modules

```bash
epsdk list-remote
```

### Interactive Installation

Entering the interactive installation interface when package names are not specified:

```bash
epsdk install
```

## Running Project

```bash
# Normal run
epsdk run main.py

# Hot reload mode (recommended for development)
epsdk run main.py --reload
```

## Enabling IDE Completion (Optional)

ErisPulse dynamically discovers modules/adapters, so IDEs cannot autocomplete platform-specific methods by default.
Run the following command to generate type stubs:

```bash
epsdk types
```

After generation, use the imported types as type annotations to get accurate completion (see [IDE Completion Guide](getting-started/ide-completion.md)):

```python
from _ep_types import Yunhu
from ErisPulse import sdk

adapter: Yunhu = sdk.adapter.get("yunhu")
await adapter.Send.To("group", "123").Board(...)  # Autocomplete platform-specific methods
```

## Project Structure

The project structure after initialization:

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

After the bot is running, you can continue as needed:

**Want to understand how the framework works?**
- [Basic Concepts](getting-started/basic-concepts.md) — Design of adapters / modules / events
- [Architecture Overview](architecture.md) — Visual architecture diagrams

**Want to implement more features?**
- [Common Task Examples](getting-started/common-tasks.md) — Storage, scheduled tasks, permission control
- [Introduction to Event Handling](getting-started/event-handling.md) — Messages, notifications, request handling

**Want to develop your own module / adapter?**
- [Introduction to Module Development](developer-guide/modules/getting-started.md)
- [Introduction to Adapter Development](developer-guide/adapters/getting-started.md)

**For reference as needed:**
- [Configuration File Guide](user-guide/configuration.md) · [CLI Reference](user-guide/cli-reference.md) · [Deployment Guide](user-guide/deployment.md)