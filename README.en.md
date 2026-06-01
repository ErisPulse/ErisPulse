<table>
<tr>
<td width="35%" valign="middle" align="center">

<img src=".github/assets/mascot-hero.png" width="320" alt="ErisPulse" />

</td>
<td valign="middle">

**English** | [简体中文](README.md) | [繁體中文](README.zh-TW.md)

# ErisPulse

**Event-Driven Multi-Platform Robot Development Framework**

Based on the OneBot12 standard interface, write once and deploy on multiple platforms. Flexible plugin system, hot-reload support, and a complete developer toolchain, suitable for various scenarios from simple chatbots to complex automation systems.

> Supports Vibe Coding workflow that enables AI to directly generate usable modules — [Learn more](docs/en/ai-support/README.md)

[![PyPI](https://img.shields.io/pypi/v/ErisPulse?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/ErisPulse/)
[![Python](https://img.shields.io/badge/Python-3.10+-FFD43B?style=for-the-badge&logo=python&logoColor=blue)](https://pypi.org/project/ErisPulse/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://hub.docker.com/r/erispulse/erispulse)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](https://github.com/ErisPulse/ErisPulse/blob/main/LICENSE)
[![Stars](https://img.shields.io/github/stars/ErisPulse/ErisPulse?style=for-the-badge&logo=github&color=brightgreen)](https://github.com/ErisPulse/ErisPulse)
[![Downloads](https://img.shields.io/pepy/dt/ErisPulse?style=for-the-badge&color=blue)](https://pypi.org/project/ErisPulse/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&style=for-the-badge)](https://github.com/astral-sh/ruff)
[![Socket](https://img.shields.io/badge/Socket-Secure-2ea043?style=for-the-badge&logo=socket&logoColor=white)](https://socket.dev/pypi/package/erispulse)

[![文档](https://img.shields.io/badge/文档-erisdev.com-FF6B9D?style=for-the-badge&logo=bookstack&logoColor=white)](https://www.erisdev.com)
[![模块市场](https://img.shields.io/badge/模块市场-erisdev.com-C724B1?style=for-the-badge&logo=webpack&logoColor=white)](https://www.erisdev.com/#market)
[![讨论](https://img.shields.io/badge/GitHub-Discussions-181717?style=for-the-badge&logo=github)](https://github.com/ErisPulse/ErisPulse/discussions)

</td>
</tr>
</table>

---

<div align="center">

### Core Features

</div>

<table>
<tr>
<td width="50%" align="center" valign="top">
<br/>

### ⚡ Event-Driven Architecture

A clear event model based on the OneBot12 standard makes message processing logic more intuitive and efficient

</td>
<td width="50%" align="center" valign="top">
<br/>

### 🌐 Cross-Platform Compatibility

Plugin modules written once can be used on all platforms, eliminating the need for repeated development for different platforms

</td>
</tr>
<tr>
<td width="50%" align="center" valign="top">
<br/>

### 🧩 Modular Design

Flexible plugin system that is easy to extend and integrate, supporting hot-swappable module management

</td>
<td width="50%" align="center" valign="top">
<br/>

### 🔄 Hot-Reload Support

Reload code without restarting during development, significantly improving development iteration efficiency

</td>
</tr>
</table>

---

### Supported Adapters

<div align="center">
<!-- <img src=".github/assets/adapter-showcase.png" width="520" alt="Supported Adapters" /> -->

Contributions of adapters are welcome!

| Adapter | Description |
|---------|-------------|
| <img src=".github/assets/adapter_logo/kook.svg" height="20" alt="Kook" /> [Kook](https://github.com/shanfishapp/ErisPulse-KookAdapter) | Kook (Kaihei La) instant messaging platform |
| <img src=".github/assets/adapter_logo/matrix.svg" height="20" alt="Matrix" /> [Matrix](https://github.com/ErisPulse/ErisPulse-MatrixAdapter) | Matrix decentralized communication protocol |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot11](https://github.com/ErisPulse/ErisPulse-OneBot11Adapter) | OneBot v11 general robot protocol |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot12](https://github.com/ErisPulse/ErisPulse-OneBot12Adapter) | OneBot v12 standard protocol |
| <img src=".github/assets/adapter_logo/qqbot.svg" height="20" alt="QQ" /> [QQ](https://github.com/ErisPulse/ErisPulse-QQBotAdapter) | QQ official robot platform |
| <img src=".github/assets/adapter_logo/sandbox.png" height="20" alt="Sandbox" /> [Sandbox](https://github.com/ErisPulse/ErisPulse-SandboxAdapter) | Web-based debugging, no need to connect to a real platform |
| <img src=".github/assets/adapter_logo/telegram.svg" height="20" alt="Telegram" /> [Telegram](https://github.com/ErisPulse/ErisPulse-TelegramAdapter) | Global instant messaging platform |
| <img src=".github/assets/adapter_logo/email.svg" height="20" alt="Email" /> [Email](https://github.com/ErisPulse/ErisPulse-EmailAdapter) | Email protocol send/receive adapter |
| <img src=".github/assets/adapter_logo/yunhu.png" height="20" alt="Yunhu" /> [Yunhu](https://github.com/ErisPulse/ErisPulse-YunhuAdapter) | Enterprise-level instant messaging platform (robot access) |
| [Yunhu User](https://github.com/wsu2059q/ErisPulse-YunhuUserAdapter) | Access adapter based on Yunhu user protocol |
| [Ideaura](https://github.com/ErisPulse/ErisPulse-Ideaura/) | Allons! \(・ω・) / |

See [Adapter Details Introduction](docs/en/platform-guide/README.md)

</div>

---

### Quick Start

#### One-Click Installation Script (Recommended)

The installation script automatically detects your environment (Docker, Python, uv), guides you to choose the most suitable installation method, and supports multiple languages (中文/English/日本語/Русский/繁體中文).

Windows (PowerShell):
```powershell
irm https://get.erisdev.com/install.ps1 -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1
```

macOS / Linux:
```bash
curl -fsSL https://get.erisdev.com/install.sh -o install.sh && chmod +x install.sh && ./install.sh
```

#### Using Docker (Recommended)

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

<details>
<summary>Using Pre-release Version (Dev)</summary>

Set `ERISPULSE_CHANNEL=dev` to use the pre-release version:

```bash
# Method 1: Use environment variables (recommended)
ERISPULSE_CHANNEL=dev ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d

# Method 2: Build dev image
ERISPULSE_BUILD_TARGET=dev docker compose up -d --build
```

If you want to automatically update to the latest version on startup (whether stable or dev), explicitly set `ERISPULSE_UPDATE_ON_START=true`:

```bash
ERISPULSE_CHANNEL=dev ERISPULSE_UPDATE_ON_START=true docker compose up -d
```

You can also pull the pre-built dev image:

```bash
docker pull erispulse/erispulse:dev
```

</details>

<details>
<summary>Docker Environment Variables</summary>

| Variable | Default | Description |
|----------|---------|-------------|
| `ERISPULSE_CHANNEL` | `stable` | Version channel: `stable` (stable version) or `dev` (pre-release version) |
| `ERISPULSE_UPDATE_ON_START` | `false` | Whether to automatically update to the latest version on container start (needs to be explicitly enabled) |
| `ERISPULSE_DASHBOARD_TOKEN` | Empty | Dashboard login token |
| `ERISPULSE_PORT` | `8000` | Dashboard port mapping |
| `TZ` | `Asia/Shanghai` | Container timezone |

> Enabling `ERISPULSE_UPDATE_ON_START=true` ensures that even if the image is outdated, the container will automatically get the latest version on startup.

</details>

#### 1Panel App Store

Install ErisPulse with one click via the [1Panel](https://1panel.cn) App Store. See [ErisPulse-1Panel](https://github.com/ErisPulse/ErisPulse-1Panel) for details.

```bash
bash <(curl -sL https://get-1panel.erisdev.com/install.sh)
```

#### Installation with pip

```bash
pip install ErisPulse

# Domestic mirror
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple ErisPulse

# Installation using uv
uv pip install ErisPulse
```

![Installation Demo](.github/assets/docs/install_pip.gif)

> You can also use the one-click installation script mentioned above to automatically detect the environment and guide configuration.

#### Running Effects

##### Dashboard:
> There is a GIF here, but it's too large to include~ Sorry~
> [GIF Demo](.github/assets/docs/dashboard-demo.gif)

<img src=".github/assets/docs/dashboard.png" alt="Dashboard Demo" />

##### Code for one platform, responses on multiple platforms:

<table>
<tr>
<td align="center" width="33%">

**Kook**

<img src=".github/assets/demo-kook.png" alt="Kook Demo" />

</td>
<td align="center" width="33%">

**QQ**

<img src=".github/assets/demo-qq.png" alt="QQ Demo" />

</td>
<td align="center" width="33%">

**Yunhu**

<img src=".github/assets/demo-yunhu.png" alt="Yunhu Demo" />

</td>
</tr>
</table>

#### Initialize Project

```bash
# Interactive initialization
epsdk init

# Quick initialization (specify project name)
epsdk init -q -n my_bot
```

#### Create Your First Bot

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

---

### Use Cases

<div align="center">

| Multi-Platform Bots | Chat Assistants | Automation Tools | Message Forwarding |
|:---:|:---:|:---:|:---:|
| Deploy robots with the same functionality<br>on multiple platforms | Integrate AI chat modules<br>for entertainment and interaction | Message notifications, task management,<br>data collection | Cross-platform message<br>synchronization and forwarding |

</div>

---

### Documentation Resources

| 简体中文 | English | 繁體中文 |
|:---:|:---:|:---:|
| [文档入口](docs/zh-CN/README.md) | [Documentation](docs/en/README.md) | [文檔入口](docs/zh-TW/README.md) |

| Platform | Main Site | Backup Sites |
|----------|-----------|--------------|
| Documentation | [erisdev.com](https://www.erisdev.com/#docs) | [Cloudflare](https://erispulse.pages.dev/#docs) · [GitHub](https://erispulse.github.io/#docs) · [Netlify](https://erispulse.netlify.app/#docs) |
| Module Market | [erisdev.com](https://www.erisdev.com/#market) | [Cloudflare](https://erispulse.pages.dev/#market) · [GitHub](https://erispulse.github.io/#market) · [Netlify](https://erispulse.netlify.app/#market) |

---

### Contribution Guide

The health of the ErisPulse project depends on your contribution! We welcome various forms of contribution:

1. **Report Issues** — Submit bug reports in [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues)
2. **Feature Requests** — Share new ideas through [Community Discussions](https://github.com/ErisPulse/ErisPulse/discussions)
3. **Code Contributions** — Before submitting a PR, please read the [Code Style Guide](docs/en/styleguide/) and [Contribution Guidelines](CONTRIBUTING.md)
4. **Documentation Improvements** — Help improve documentation and example code

[Join Community Discussions](https://github.com/ErisPulse/ErisPulse/discussions)

---

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=ErisPulse/ErisPulse&type=Date)](https://star-history.com/#ErisPulse/ErisPulse&Date)

---

<div align="center">

### Acknowledgments

<img src=".github/assets/thanks.png" width="200" alt="Thanks" />

Some code in this project is based on [sdkFrame](https://github.com/runoneall/sdkFrame) · The core adapter standardization layer is based on [OneBot12 Specification](https://12.onebot.dev/) · Thank you to all developers and authors who contribute to the open source community

</div>