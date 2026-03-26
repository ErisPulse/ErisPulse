<div align="center">

[English](README.en.md) | [简体中文](README.md) | [繁體中文](README.zh-Hant.md)

</div>

<table>
<tr>
<td width="35%" valign="middle" align="center">
<img src=".github/assets/erispulse_logo_1024.png" width="280" alt="ErisPulse" />
</td>
<td width="65%" valign="middle">

# ErisPulse

**Event-Driven Multi-Platform Bot Development Framework**

[![PyPI](https://img.shields.io/pypi/v/ErisPulse?style=flat-square)](https://pypi.org/project/ErisPulse/)
[![Python Versions](https://img.shields.io/pypi/pyversions/ErisPulse?style=flat-square)](https://pypi.org/project/ErisPulse/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Socket Badge](https://socket.dev/api/badge/pypi/package/ErisPulse/latest)](https://socket.dev/pypi/package/ErisPulse)

</td>
</tr>
</table>

---

## Overview

ErisPulse is an event-driven multi-platform bot development framework based on Python. Through the unified OneBot12 standard interface, you can write code once and deploy bots with the same functionality across multiple platforms such as Yunhu, Telegram, and OneBot. The framework provides a flexible module (plugin) system, hot-reload support, and a complete developer toolchain, suitable for scenarios ranging from simple chat bots to complex automation systems.

## Core Features

- **Event-Driven Architecture** - Clear event model based on OneBot12 standard
- **Cross-Platform Compatibility** - Write modules once, use them across all platforms
- **Modular Design** - Flexible plugin system, easy to extend and integrate
- **Hot-Reload Support** - Reload code during development without restarting
- **Complete Toolchain** - CLI tools, package management, and automation scripts

## Quick Start

### Installation

```bash
pip install ErisPulse

# China mirror
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple ErisPulse

# Install with `uv`
uv install ErisPulse
```

![Installation Demo](.github/assets/docs/install_pip.gif)

> If your Python version is below 3.10, you can use the one-click installation script to automatically configure the environment. See [Installation Script Guide](scripts/install/).

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

**Command Handlers**

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

**Run Method**

```bash
epsdk run main.py
# Or development mode
epsdk run main.py --reload
```

</td>
</tr>
</table>

For more details, please see:
- [Quick Start Guide](docs/quick-start.md)
- [Getting Started Guide](docs/getting-started/)

## Use Cases

- **Multi-Platform Bots** - Deploy bots with the same functionality across multiple platforms
- **Chat Assistants** - Integrate AI chat modules for entertainment and interaction
- **Automation Tools** - Message notifications, task management, data collection
- **Message Forwarding** - Cross-platform message synchronization and forwarding

## Supported Adapters

Contributions are welcome!

- [Yunhu](https://github.com/ErisPulse/ErisPulse-YunhuAdapter) - Enterprise instant messaging platform (bot account)
- [Yunhu User](https://github.com/wsu2059q/ErisPulse-YunhuUserAdapter) - Adapter based on Yunhu user account
- [Telegram](https://github.com/ErisPulse/ErisPulse-TelegramAdapter) - Global instant messaging software
- [OneBot11](https://github.com/ErisPulse/ErisPulse-OneBot11Adapter) - Universal bot interface standard
- [OneBot12](https://github.com/ErisPulse/ErisPulse-OneBot12Adapter) - OneBot12 standard
- [Email](https://github.com/ErisPulse/ErisPulse-EmailAdapter) - Email sending and receiving
- [Sandbox](https://github.com/ErisPulse/ErisPulse-SandboxAdapter) - Web debugging interface, no need to connect to actual platforms

See [Adapter Details](docs/platform-guide/README.md)

## Documentation Languages

<div align="center">

| 🇨🇳🇳 简体中文 | 🇺🇸 English | 🇹🇼 繁體中文 |
|----------------|----------------|----------------|
| [文档入口](docs/zh-CN/README.md) | [Documentation](docs/en/README.md) | [文檔入口](docs/zh-TW/README.md) |

</div>

## Other Resources

| Platform | Main Site | Mirror Sites |
|----------|-----------|--------------|
| Documentation | [erisdev.com](https://www.erisdev.com/#docs) | [Cloudflare](https://erispulse.pages.dev/#docs) • [GitHub](https://erispulse.github.io/#docs) • [Netlify](https://erispulse.netlify.app/#docs) |
| Module Market | [erisdev.com](https://www.erisdev.com/#market) | [Cloudflare](https://erispulse.pages.dev/#market) • [GitHub](https://erispulse.github.io/#market) • [Netlify](https://erispulse.netlify.app/#market) |

## Contributing

ErisPulse needs your help to grow! We welcome contributions in various forms, including but not limited to:

1. **Report Issues**
   Submit bug reports at [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues)

2. **Feature Requests**
   Share new ideas through [Community Discussions](https://github.com/ErisPulse/ErisPulse/discussions)

3. **Code Contributions**
   Please read our [Code Style Guide](docs/styleguide/) and [Contributing Guide](CONTRIBUTING.md) before submitting Pull Requests

4. **Documentation Improvements**
   Help improve documentation and example code

[Join Community Discussion](https://github.com/ErisPulse/ErisPulse/discussions)

---

## Acknowledgments

- This project is partially based on [sdkFrame](https://github.com/runoneall/sdkFrame)
- Core adapter standardization layer is based on [OneBot12 Specification](https://12.onebot.dev/)
- Thanks to all developers and authors who contribute to the open source community