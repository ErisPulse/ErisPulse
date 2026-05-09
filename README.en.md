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

**Event-Driven Multi-Platform Robot Development Framework**

[![PyPI](https://img.shields.io/pypi/v/ErisPulse?style=flat-square)](https://pypi.org/project/ErisPulse/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)](https://hub.docker.com/r/erispulse/erispulse)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://pypi.org/project/ErisPulse/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Socket Badge](https://socket.dev/api/badge/pypi/package/ErisPulse/latest)](https://socket.dev/pypi/package/ErisPulse)

</td>
</tr>
</table>

---

## Introduction

ErisPulse is a Python-based event-driven multi-platform robot development framework. Through the unified OneBot12 standard interface, you can write code once and deploy robots with the same functionality across multiple platforms such as Yunhu, Telegram, and OneBot. The framework provides a flexible module (`plugin`) system, hot-reload support, and a complete developer toolchain, suitable for various scenarios from simple chatbots to complex automation systems.

## Core Features

- **Event-Driven Architecture** - Clear event model based on the OneBot12 standard
- **Cross-Platform Compatibility** - Plugin modules written once can be used on all platforms
- **Modular Design** - Flexible plugin system, easy to extend and integrate
- **Hot-Reload Support** - Reload code without restarting during development
- **Complete Toolchain** - Provides CLI tools, package management, and automation scripts

## Supported Adapters

Contributions of adapters are welcome!

| Adapter | Description |
|---------|-------------|
| [Kook](https://github.com/shanfishapp/ErisPulse-KookAdapter) | Kook (Kaihei La) instant messaging platform |
| [Matrix](https://github.com/ErisPulse/ErisPulse-MatrixAdapter) | Matrix decentralized communication protocol |
| [OneBot11](https://github.com/ErisPulse/ErisPulse-OneBot11Adapter) | OneBot v11 general robot protocol |
| [OneBot12](https://github.com/ErisPulse/ErisPulse-OneBot12Adapter) | OneBot v12 standard protocol |
| [QQ](https://github.com/ErisPulse/ErisPulse-QQBotAdapter) | QQ official robot platform |
| [Sandbox](https://github.com/ErisPulse/ErisPulse-SandboxAdapter) | Web-based debugging, no need to connect to a real platform |
| [Telegram](https://github.com/ErisPulse/ErisPulse-TelegramAdapter) | Global instant messaging platform |
| [Email](https://github.com/ErisPulse/ErisPulse-EmailAdapter) | Email protocol send/receive adapter |
| [Yunhu](https://github.com/ErisPulse/ErisPulse-YunhuAdapter) | Enterprise-level instant messaging platform (robot access) |
| [Yunhu User](https://github.com/wsu2059q/ErisPulse-YunhuUserAdapter) | Access adapter based on Yunhu user protocol |
| [Ideaura](https://github.com/ErisPulse/ErisPulse-Ideaura/) | Allons! (・ω・) / |

See [Adapter Details Introduction](docs/en/platform-guide/README.md)

## Quick Start

### Using Docker (Recommended)

```bash
docker pull erispulse/erispulse:latest
```

<details>
<summary>Docker Hub unavailable?</summary>

If Docker Hub cannot be accessed, you can use GitHub Container Registry:

```bash
docker pull ghcr.io/erispulse/erispulse:latest
```

When using ghcr.io images, you need to modify the image in `docker-compose.yml`:
```yaml
image: ghcr.io/erispulse/erispulse:latest
```

</details>

<details>
<summary>Quick Start</summary>

```bash
# Download docker-compose.yml
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Set Dashboard login token and start
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

> The image includes the ErisPulse framework and Dashboard management panel, supporting `linux/amd64` and `linux/arm64` architectures.

After starting, access `http://<host>:<port>/Dashboard` and use the set token as the password to log in to the Dashboard management panel.

</details>

### Installation with pip

```bash
pip install ErisPulse

# Domestic mirror
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple ErisPulse

# Installation using uv
uv pip install ErisPulse
```

![Installation Demo](.github/assets/docs/install_pip.gif)

> If your Python version is below 3.10, you can use the one-click installation script to automatically configure the environment. See [Installation Script Instructions](scripts/install/) for details.

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

**Running Method**

```bash
epsdk run main.py
# Or development mode
epsdk run main.py --reload
```

</td>
</tr>
</table>

For more detailed information, please refer to:
- [Quick Start Guide](docs/en/quick-start.md)
- [Getting Started Guide](docs/en/getting-started/)

## Use Cases

- **Multi-Platform Bots** - Deploy robots with the same functionality on multiple platforms
- **Chat Assistants** - Integrate AI chat modules to achieve entertainment and interaction
- **Automation Tools** - Message notifications, task management, data collection
- **Message Forwarding** - Cross-platform message synchronization and forwarding

## Documentation Resources

| 简体中文 | English | 繁體中文 |
|----------------|----------------|----------------|
| [文档入口](docs/en/README.md) | [Documentation](docs/en/README.md) | [文檔入口](docs/zh-TW/README.md) |

## External Resources

| Platform | Main Site | Backup Sites |
|----------|-----------|--------------|
| Documentation | [erisdev.com](https://www.erisdev.com/#docs) | [Cloudflare](https://erispulse.pages.dev/#docs) • [GitHub](https://erispulse.github.io/#docs) • [Netlify](https://erispulse.netlify.app/#docs) |
| Module Market | [erisdev.com](https://www.erisdev.com/#market) | [Cloudflare](https://erispulse.pages.dev/#market) • [GitHub](https://erispulse.github.io/#market) • [Netlify](https://erispulse.netlify.app/#market) |

## Contribution Guidelines

The ErisPulse project's health needs your contribution! We welcome all forms of contribution, including but not limited to:

1. **Report Issues**
   Submit bug reports in [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues)

2. **Feature Requests**
   Submit new ideas through [Community Discussions](https://github.com/ErisPulse/ErisPulse/discussions)

3. **Code Contributions**
   Before submitting a Pull Request, please read our [Code Style Guide](docs/en/styleguide/) and [Contribution Guidelines](CONTRIBUTING.md)

4. **Documentation Improvements**
   Help improve documentation and example code

[Join Community Discussions](https://github.com/ErisPulse/ErisPulse/discussions)

---

## Acknowledgments

- Some code of this project is based on [sdkFrame](https://github.com/runoneall/sdkFrame)
- The core adapter standardization layer is based on [OneBot12 Specification](https://12.onebot.dev/)
- Thank you to all developers and authors who have contributed to the open source community