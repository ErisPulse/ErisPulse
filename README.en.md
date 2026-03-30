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
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Socket Badge](https://socket.dev/api/badge/pypi/package/ErisPulse/latest)](https://socket.dev/pypi/package/ErisPulse)

</td>
</tr>
</table>

---

## Introduction

ErisPulse is a Python-based event-driven multi-platform bot development framework. With the unified OneBot12 standard interface, you can write code once and deploy bots with identical functionality on multiple platforms such as Yunhu, Telegram, and OneBot. The framework provides a flexible module (plugin) system, hot reload support, and a complete developer toolchain, suitable for various scenarios ranging from simple chatbots to complex automation systems.

## Core Features

- **Event-Driven Architecture** - Clear event model based on OneBot12 standard
- **Cross-Platform Compatibility** - Plugin modules written once work on all platforms
- **Modular Design** - Flexible plugin system, easy to extend and integrate
- **Hot Reload Support** - Reload code without restarting during development
- **Complete Toolchain** - Provides CLI tools, package management, and automation scripts

## Quick Start

### Installation

```bash
pip install ErisPulse

# Domestic mirror
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple ErisPulse

# Install using `uv`
uv install ErisPulse
```

![Installation Demo](.github/assets/docs/install_pip.gif)

> If your Python version is below 3.10, you can use the one-click install script to automatically configure the environment. See [Installation Script Documentation](scripts/install/) for details.

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
    user_name = event.get_user_nickname() or "Friend"
    await event.reply(f"Hello, {user_name}!")

@command("ping", help="Test if bot is online")
async def ping_handler(event):
    await event.reply("Pong! Bot is running normally.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(sdk.run(keep_running=True))
```

</td>
<td width="50%" valign="top">

**Usage Examples**

Send `/hello`

Bot replies: `Hello, {username}!`

---

Send `/ping`

Bot replies: `Pong! Bot is running normally.`

---

**Running Methods**

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

- **Multi-platform Bots** - Deploy bots with identical functionality across multiple platforms
- **Chat Assistants** - Integrate AI chat modules for entertainment and interaction
- **Automation Tools** - Message notifications, task management, data collection
- **Message Forwarding** - Cross-platform message synchronization and forwarding

## Supported Adapters

Contributions to adapters are welcome!

- [Yunhu](https://github.com/ErisPulse/ErisPulse-YunhuAdapter) - Enterprise-grade instant messaging platform (bot account)
- [Yunhu User](https://github.com/wsu2059q/ErisPulse-YunhuUserAdapter) - Adapter based on Yunhu user account
- [Telegram](https://github.com/ErisPulse/ErisPulse-TelegramAdapter) - Global instant messaging software
- [OneBot11](https://github.com/ErisPulse/ErisPulse-OneBot11Adapter) - Universal bot interface standard
- [OneBot12](https://github.com/ErisPulse/ErisPulse-OneBot12Adapter) - OneBot12 standard
- [Email](https://github.com/ErisPulse/ErisPulse-EmailAdapter) - Email sending and receiving processing
- [Sandbox](https://github.com/ErisPulse/ErisPulse-SandboxAdapter) - Web debugging interface, no need to connect to actual platforms
- [Kook](https://github.com/shanfishapp/ErisPulse-KookAdapter) - Instant messaging platform

See [Platform Adapter Details](docs/en/platform-guide/README.md)

## Documentation Resources

| Simplified Chinese | English | Traditional Chinese |
|----------------|----------------|----------------|
| [Documentation Entry](docs/en/README.md) | [Documentation](docs/en/README.md) | [文檔入口](docs/zh-TW/README.md) |

## External Resources

| Platform | Main Site | Mirror Site |
|------|--------|---------|
| Documentation | [erisdev.com](https://www.erisdev.com/#docs) | [Cloudflare](https://erispulse.pages.dev/#docs) • [GitHub](https://erispulse.github.io/#docs) • [Netlify](https://erispulse.netlify.app/#docs) |
| Module Market | [erisdev.com](https://www.erisdev.com/#market) | [Cloudflare](https://erispulse.pages.dev/#market) • [GitHub](https://erispulse.github.io/#market) • [Netlify](https://erispulse.netlify.app/#market) |

## Contributing

The robustness of the ErisPulse project needs your help! We welcome various forms of contributions, including but not limited to:

1. **Report Issues**
   Submit bug reports in [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues)

2. **Feature Requests**
   Submit new ideas via [Community Discussion](https://github.com/ErisPulse/ErisPulse/discussions)

3. **Code Contributions**
   Before submitting a Pull Request, please read our [Code Style](docs/en/styleguide/) and [Contributing Guide](CONTRIBUTING.md)

4. **Documentation Improvements**
   Help improve documentation and example code

[Join Community Discussion](https://github.com/ErisPulse/ErisPulse/discussions)

---

## Acknowledgments

- Some code in this project is based on [sdkFrame](https://github.com/runoneall/sdkFrame)
- The core adapter standardization layer is based on the [OneBot12 Specification](https://12.onebot.dev/)
- Thank you to all developers and authors who have contributed to the open source community