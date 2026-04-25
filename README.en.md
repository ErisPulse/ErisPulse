<div align="center">

[English](README.en.md) | [简体中文](README.md) | [繁體中文](README.zh-TW.md)

</div>

<table>
<tr>
<td width="35%" valign="middle" align="center">
<img src=".github/assets/erispulse_logo_1024.png" width="280" alt="ErisPulse" />
</td>
<td width="65%" valign="middle">

# ErisPulse

**An event-driven multi-platform bot development framework**

[![PyPI](https://img.shields.io/pypi/v/ErisPulse?style=flat-square)](https://pypi.org/project/ErisPulse/)
[![Python Versions](https://img.shields.io/pypi/pyversions/ErisPulse?style=flat-square)](https://pypi.org/project/ErisPulse/)
[![Docker Pulls](https://img.shields.io/docker/pulls/erispulse/erispulse?style=flat-square&logo=docker&label=pulls)](https://hub.docker.com/r/erispulse/erispulse)
[![Docker Pulls](https://img.shields.io/docker/pulls/wsu2059/erispulse?style=flat-square&logo=docker&label=pulls)](https://hub.docker.com/r/erispulse/erispulse)
[![Docker Version](https://img.shields.io/docker/v/erispulse/erispulse?style=flat-square&logo=docker&label=docker)](https://hub.docker.com/r/erispulse/erispulse)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

</td>
</tr>
</table>

---

## Introduction

ErisPulse is a Python-based event-driven multi-platform bot development framework. Through the unified OneBot12 standard interface, you can write code once and deploy bots with the same functionality on multiple platforms such as Yunhu, Telegram, and OneBot. The framework provides a flexible module (`plugin`) system, hot reload support, and a complete developer toolchain, suitable for various scenarios from simple chatbots to complex automation systems.

## Core Features

- **Event-Driven Architecture** - A clear event model based on the OneBot12 standard
- **Cross-Platform Compatibility** - Plugin modules written once can be used on all platforms
- **Modular Design** - Flexible plugin system, easy to extend and integrate
- **Hot Reload Support** - Reload code during development without restarting
- **Complete Toolchain** - Provides CLI tools, package management, and automation scripts

## Supported Adapters

Contributions of adapters are welcome!

<table>
<tr>
<td width="20%" align="center"><a href="https://github.com/ErisPulse/ErisPulse-EmailAdapter"><img src=".github/assets/adapter_logo/email.svg" width="36" alt="Email" /><br/><b>Email</b></a></td>
<td width="20%" align="center"><a href="https://github.com/shanfishapp/ErisPulse-KookAdapter"><img src=".github/assets/adapter_logo/kook.svg" width="36" alt="Kook" /><br/><b>Kook</b></a></td>
<td width="20%" align="center"><a href="https://github.com/ErisPulse/ErisPulse-MatrixAdapter"><img src=".github/assets/adapter_logo/matrix.svg" width="36" alt="Matrix" /><br/><b>Matrix</b></a></td>
<td width="20%" align="center"><a href="https://github.com/ErisPulse/ErisPulse-OneBot11Adapter"><img src=".github/assets/adapter_logo/onebot.png" width="36" alt="OneBot11" /><br/><b>OneBot11</b></a></td>
<td width="20%" align="center"><a href="https://github.com/ErisPulse/ErisPulse-OneBot12Adapter"><img src=".github/assets/adapter_logo/onebot.png" width="36" alt="OneBot12" /><br/><b>OneBot12</b></a></td>
</tr>
<tr>
<td width="20%" align="center"><a href="https://github.com/ErisPulse/ErisPulse-QQBotAdapter"><img src=".github/assets/adapter_logo/qqbot.svg" width="36" alt="QQ" /><br/><b>QQ</b></a></td>
<td width="20%" align="center"><a href="https://github.com/ErisPulse/ErisPulse-SandboxAdapter"><img src=".github/assets/adapter_logo/sandbox.png" width="36" alt="Sandbox" /><br/><b>Sandbox</b></a></td>
<td width="20%" align="center"><a href="https://github.com/ErisPulse/ErisPulse-TelegramAdapter"><img src=".github/assets/adapter_logo/telegram.svg" width="36" alt="Telegram" /><br/><b>Telegram</b></a></td>
<td width="20%" align="center"><a href="https://github.com/ErisPulse/ErisPulse-YunhuAdapter"><img src=".github/assets/adapter_logo/yunhu.png" width="36" alt="Yunhu" /><br/><b>Yunhu</b></a></td>
<td width="20%" align="center"><a href="https://github.com/wsu2059q/ErisPulse-YunhuUserAdapter"><img src=".github/assets/adapter_logo/yunhu.png" width="36" alt="YunhuUser" /><br/><b>Yunhu User</b></a></td>
</tr>
</table>

See [Adapter Details](docs/en/platform-guide/README.md)

## Quick Start

### Using Docker (Recommended)

```bash
docker pull erispulse/erispulse:latest
```

<details>
<summary>Quick Start</summary>

```bash
# Download docker-compose.yml
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Set Dashboard login token and start
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

> The image includes ErisPulse framework and Dashboard management panel, supporting `linux/amd64` and `linux/arm64` architectures.

</details>

After starting, visit `http://localhost:8000/Dashboard` and use the set token as the password to log in to the Dashboard management panel.

### Installing with pip

```bash
pip install ErisPulse

# Using domestic mirror
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple ErisPulse

# Install with uv
uv pip install ErisPulse
```

![Installation Demo](.github/assets/docs/install_pip.gif)

> If your Python version is below 3.10, you can use a one-click installation script to automatically configure the environment. See [Installation Script Documentation](scripts/install/).

### Initialize Project

```bash
# Interactive initialization
epsdk init

# Quick initialization (specify project name)
epsdk init -q -n my_bot
```

### Create Your First Bot

Create a `main.py` file:

<table>
<tr>
<td width="50%" valign="top">

**Command Handler**

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("hello", help="Send greeting message")
async def hello_handler(event):
    user_name = event.get_user_nickname() or "friend"
    await event.reply(f"Hello, {user_name}!")

@command("ping", help="Test if the bot is online")
async def ping_handler(event):
    await event.reply("Pong! The bot is running normally.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(sdk.run(keep_running=True))
```

</td>
<td width="50%" valign="top">

**Effect Description**

Send `/hello`

Bot replies: `Hello, {username}!`

---

Send `/ping`

Bot replies: `Pong! The bot is running normally.`

---

**How to Run**

```bash
epsdk run main.py
# Or in development mode
epsdk run main.py --reload
```

</td>
</tr>
</table>

For more detailed instructions, please refer to:
- [Quick Start Guide](docs/en/quick-start.md)
- [Getting Started Guide](docs/en/getting-started/)

## Use Cases

- **Multi-platform Bots** - Deploy bots with the same functionality across multiple platforms
- **Chat Assistants** - Integrate AI chat modules for entertainment and interaction
- **Automation Tools** - Message notifications, task management, data collection
- **Message Forwarding** - Cross-platform message synchronization and forwarding

## Documentation Resources

| 简体中文 | English | 繁體中文 |
|----------------|----------------|----------------|
| [文档入口](docs/zh-CN/README.md) | [Documentation](docs/en/README.md) | [文檔入口](docs/zh-TW/README.md) |

## External Resources

| Platform | Main Site | Alternative Sites |
|------|--------|---------|
| Documentation | [erisdev.com](https://www.erisdev.com/#docs) | [Cloudflare](https://erispulse.pages.dev/#docs) • [GitHub](https://erispulse.github.io/#docs) • [