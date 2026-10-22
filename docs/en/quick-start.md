# Quick Start

> **This is your first step.** Run an ErisPulse robot from scratch in 5 minutes—see the result first, then expand each step.

## 60-Second Demo: Let the Bot Reply to You First

**1. Install** (Python >= 3.10):

```bash
pip install ErisPulse
```

**2. Initialize the project.** The wizard will prompt you to set the project name, select the platform adapter to connect, and complete the configuration, then generate `main.py` and `config/config.toml`:

```bash
epsdk init
```

**3. Open `main.py`, and replace it with these 9 lines of code:**

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("ping", help="Test if the bot is online")
async def ping_handler(event):
    await event.reply("Pong! The bot is running normally.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(sdk.run(keep_running=True))
```

**4. Run**:

```bash
epsdk run main.py
```

The terminal will output framework startup logs and adapter connection information. At this point, send `/ping` to the bot in your connected platform; it will reply:

> Pong! The bot is running normally.

Seeing this reply confirms that the framework, adapter, and event handling chain are all working. If it doesn't work, go directly to the [Troubleshooting section](#troubleshooting) at the end of the document; if it works, continue reading to see what other options are available at each step.

## Install ErisPulse: Three Ways

The above uses the most direct pip method. Choose according to your environment:

### Install with pip

Ensure your Python version is >= 3.10, then install using pip:

```bash
pip install ErisPulse
```

If you have already installed [uv](https://github.com/astral-sh/uv), you can also use `uv pip install ErisPulse` for faster installation.

When you only want to install the `epsdk` command-line tool globally without polluting the project environment, it is recommended to use `uv tool install`:

```bash
uv tool install ErisPulse
```

After installation, `epsdk` will be globally available: when running within a project directory, it will automatically detect the project's `.venv` (installing `epsdk install` into the project environment, and running `epsdk run` using the project environment), while the framework itself is provided by the tool environment. See [Installation Reference](user-guide/installation.md) for details.

### One-Click Installation Script (Recommended for New Environments)

The installation script will automatically detect your environment (Docker, Python, uv), and guide you to select the most suitable installation method, supporting multiple languages (Chinese/English/Japanese/Russian/Traditional Chinese).

Windows (PowerShell):
```powershell
irm https://get.erisdev.com/install.ps1 -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1
```

macOS / Linux:
```bash
curl -fsSL https://get.erisdev.com/install.sh -o install.sh && chmod +x install.sh && ./install.sh
```

The script will guide you through:

- **Docker Installation** (recommended if Docker is detected): Choose image source (Docker Hub / GHCR), version channel (stable / pre-release), Dashboard management panel configuration, and port settings
- **Global CLI Installation (uv tool, recommended)**: Install `epsdk` as a global command, without virtual environments; uv automatically manages Python (even if the system version is too low); when running within a project directory, it automatically detects the project's `.venv`
- **Traditional Installation**: Automatically create a virtual environment, select the ErisPulse version, and optionally install the Dashboard management panel module

### Using Docker

The Docker image comes with the ErisPulse framework and the Dashboard management panel, supporting `linux/amd64` and `linux/arm64` architectures.

```bash
# Download docker-compose.yml
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Set the Dashboard token and start
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

<details>
<summary>Is Docker Hub unavailable?</summary>

Use the GitHub Container Registry image, and modify the `image` in `docker-compose.yml`:

```yaml
image: ghcr.io/erispulse/erispulse:latest
```

</details>

After starting, access `http://<host>:8000/Dashboard` and log in using the set token.

## Initialize Project

### Interactive Initialization (Recommended)

```bash
epsdk init
```

This will start an interactive wizard that guides you through:
- Project name setting
- Log level configuration
- Server configuration (host and port)
- Adapter selection and configuration
- Project structure creation

### Quick Initialization

```bash
# Quick mode with a specified project name
epsdk init -q -n my_bot

# Or just specify the project name
epsdk init -n my_bot
```

### Manual Project Creation

If you prefer to create the project manually:

```bash
mkdir my_bot && cd my_bot
epsdk init
```

## Installing Modules

### Installing via CLI

```bash
epsdk install Yunhu AIChat
```

### Viewing Available Modules

```bash
epsdk list-remote
```

### Interactive Installation

Without specifying a package name, enter the interactive installation interface:

```bash
epsdk install
```

## Running the Project

```bash
# Run normally
epsdk run main.py

# Hot reload mode (recommended for development)
epsdk run main.py --reload
```

## Enable IDE Completion (Optional)

ErisPulse dynamically discovers modules/adapters, and IDEs cannot complete platform-specific methods by default.  
Run the following command to generate type stubs:

```bash
epsdk types
```

After generation, use the imported types as variable annotations to obtain precise completion (see [IDE Completion Guide](./getting-started/ide-completion.md)):

```python
from _ep_types import Yunhu
from ErisPulse import sdk

adapter: Yunhu = sdk.adapter.get("yunhu")
await adapter.Send.To("group", "123").Board(...)  # Completion for platform-specific methods
```

## Project Structure

After initialization, the project structure is as follows:

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

After the bot is running, choose your path based on your goals:

### Want to build a group bot (handle messages, group management, notifications)

- [Event Handling Introduction](getting-started/event-handling.md) — How to write message, notification, and request events
- [Common Tasks Examples](getting-started/common-tasks.md) — Storage, scheduled tasks, permission control

### Want to write your own module / adapter

- [Basic Concepts](getting-started/basic-concepts.md) — First understand the design of adapters / modules / events
- [Module Development Introduction](developer-guide/modules/getting-started.md)
- [Adapter Development Introduction](developer-guide/adapters/getting-started.md)
- [Architecture Overview](architecture.md) — Visual architecture diagram

### Want to keep the bot running long-term

- [Deployment Guide](user-guide/deployment.md)
- [Configuration File Explanation](user-guide/configuration.md)

### Encountered problems

- [Create Your First Bot](getting-started/first-bot.md) — Step-by-step guide to creating your first bot
- [Startup Process and Manual Control](advanced/startup.md) — Diagnosing module / adapter loading failures
- [CLI Command Reference](user-guide/cli-reference.md) — All `epsdk` subcommands