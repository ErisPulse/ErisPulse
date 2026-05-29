<table>
<tr>
<td width="35%" valign="middle" align="center">

<img src=".github/assets/mascot-hero.png" width="320" alt="ErisPulse" />

</td>
<td valign="middle">

[English](README.en.md) | **简体中文** | [繁體中文](README.zh-TW.md)

# ErisPulse

**Event-driven Multi-platform Robot Development Framework**

Based on the OneBot12 standard interface, write once, deploy across multiple platforms. A flexible plugin system with hot reload support and a complete developer toolkit, suitable for various scenarios from simple chatbots to complex automation systems.

> Supports Vibe Coding workflow, enabling AI to directly generate usable modules — [View](docs/en/ai-support/README.md)

[![PyPI](https://img.shields.io/pypi/v/ErisPulse?style=flat-square)](https://pypi.org/project/ErisPulse/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://pypi.org/project/ErisPulse/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)](https://hub.docker.com/r/erispulse/erispulse)
[![License](https://img.shields.io/github/license/ErisPulse/ErisPulse?style=flat-square)](https://github.com/ErisPulse/ErisPulse/blob/main/LICENSE)
[![Stars](https://img.shields.io/github/stars/ErisPulse/ErisPulse?style=flat-square)](https://github.com/ErisPulse/ErisPulse)
[![Downloads](https://img.shields.io/pypi/dm/ErisPulse?style=flat-square)](https://pypi.org/project/ErisPulse/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

[![Docs](https://img.shields.io/badge/Docs-erisdev.com-0a0a0a?style=flat-square)](https://www.erisdev.com)
[![Module Market](https://img.shields.io/badge/Module%20Market-erisdev.com-0a0a0a?style=flat-square)](https://www.erisdev.com/#market)
[![Discussions](https://img.shields.io/badge/GitHub-Discussions-0a0a0a?style=flat-square&logo=github)](https://github.com/ErisPulse/ErisPulse/discussions)

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

### Event-driven Architecture

A clear event model based on the OneBot12 standard, making message processing logic more intuitive and efficient

</td>
<td width="50%" align="center" valign="top">
<br/>

### Cross-platform Compatibility

Write plugin modules once and use them across all platforms without repeated development for different platforms

</td>
</tr>
<tr>
<td width="50%" align="center" valign="top">
<br/>

### Modular Design

A flexible plugin system that is easy to extend and integrate, supporting hot-swappable module management

</td>
<td width="50%" align="center" valign="top">
<br/>

### Hot Reload Support

Reload code without restarting during development, significantly improving development iteration efficiency

</td>
</tr>
</table>

---

### Supported Adapters

<div align="center">

<table>
<tr>
<td width="35%" valign="middle" align="center">

<img src=".github/assets/adapter-showcase.png" width="320" alt="Supported Adapters" />

</td>
<td valign="middle">

We welcome adapter contributions!

| Adapter | Description |
|--------|------|
| [Kook](https://github.com/shanfishapp/ErisPulse-KookAdapter) | Kook (Kaihei La) instant messaging platform |
| [Matrix](https://github.com/ErisPulse/ErisPulse-MatrixAdapter) | Matrix decentralized communication protocol |
| [OneBot11](https://github.com/ErisPulse/ErisPulse-OneBot11Adapter) | OneBot v11 universal robot protocol |
| [OneBot12](https://github.com/ErisPulse/ErisPulse-OneBot12Adapter) | OneBot v12 standard protocol |
| [QQ](https://github.com/ErisPulse/ErisPulse-QQBotAdapter) | QQ official robot platform |
| [Sandbox](https://github.com/ErisPulse/ErisPulse-SandboxAdapter) | Web-based debugging, no need to connect to real platforms |
| [Telegram](https://github.com/ErisPulse/ErisPulse-TelegramAdapter) | Global instant messaging platform |
| [Email](https://github.com/ErisPulse/ErisPulse-EmailAdapter) | Email protocol send/receive adapter |
| [Yunhu](https://github.com/ErisPulse/ErisPulse-YunhuAdapter) | Enterprise instant messaging platform (robot access) |
| [Yunhu User](https://github.com/wsu2059q/ErisPulse-YunhuUserAdapter) | Access adapter based on Yunhu user protocol |
| [Ideaura](https://github.com/ErisPulse/ErisPulse-Ideaura/) | Allons! \(・ω・) / |

See [Adapter Details Maintenance Document](docs/en/platform-guide/README.md)

</td>
</tr>
</table>

</div>

---

### Quick Start

#### Using Docker (Recommended)

```bash
docker pull erispulse/erispulse:latest
```

<details>
<summary>Docker Hub unavailable?</summary>

If Docker Hub cannot be accessed, you can use the GitHub Container Registry:

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

After starting, visit `http://<host>:<port>/Dashboard` and use the set token as the password to login to the Dashboard management panel.

</details>

<details>
<summary>Using Pre-release Version (Dev)</summary>

Set `ERISPULSE_CHANNEL=dev` to use the pre-release version:

```bash
# Method 1: Using environment variables (recommended)
ERISPULSE_CHANNEL=dev ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d

# Method 2: Build dev image
ERISPULSE_BUILD_TARGET=dev docker compose up -d --build
```

To automatically update to the latest version on startup (whether stable or dev), explicitly set `ERISPULSE_UPDATE_ON_START=true`:

```bash
ERISPULSE_CHANNEL=dev ERISPULSE_UPDATE_ON_START=true docker compose up -d
```

You can also pull pre-built dev images:

```bash
docker pull erispulse/erispulse:dev
```

</details>

<details>
<summary>Docker Environment Variables</summary>

| Variable | Default | Description |
|------|--------|------|
| `ERISPULSE_CHANNEL` | `stable` | Version channel: `stable` (stable release) or `dev` (pre-release) |
| `ERISPULSE_UPDATE_ON_START` | `false` | Whether to automatically update to the latest version on container start (needs to be explicitly enabled) |
| `ERISPULSE_DASHBOARD_TOKEN` | Empty | Dashboard login token |
| `ERISPULSE_PORT` | `8000` | Dashboard port mapping |
| `TZ` | `Asia/Shanghai` | Container timezone |

> Enabling `ERISPULSE_UPDATE_ON_START=true` ensures that the container automatically gets the latest version even if the image is outdated.

</details>

#### 1Panel App Store

Install ErisPulse with one click through the [1Panel](https://1panel.cn) app store, see [ErisPulse-1Panel](https://github.com/ErisPulse/ErisPulse-1Panel) for details.

```bash
bash <(curl -sL https://get-1panel.erisdev.com/install.sh)
```

#### Installation with pip

```bash
pip install ErisPulse
```

<img src=".github/assets/docs/install_pip.gif" width="480" alt="Installation demonstration" />

> If your Python version is below 3.10, you can use a one-click installation script to automatically configure the environment. See [Installation Script Instructions](scripts/install/) for details.

#### Running Effect

The same code responding on multiple platforms:

<table>
<tr>
<td align="center" width="33%">

**Kook**

<img src=".github/assets/demo-kook.png" alt="Kook demo" />

</td>
<td align="center" width="33%">

**QQ**

<img src=".github/assets/demo-qq.png" alt="QQ demo" />

</td>
<td align="center" width="33%">

**Yunhu**

<img src=".github/assets/demo-yunhu.png" alt="Yunhu demo" />

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

For more detailed instructions, please refer to:
- [Quick Start Guide](docs/en/quick-start.md)
- [Getting Started Guide](docs/en/getting-started/)

---

### Application Scenarios

<div align="center">

| Multi-platform Bot | Chat Assistant | Automation Tool | Message Forwarding |
|:---:|:---:|:---:|:---:|
| Deploy the same<br>functional bot on multiple platforms | Connect to AI chat modules<br>for entertainment and interaction | Message notifications, task management,<br>data collection | Cross-platform message<br>synchronization and forwarding |

</div>

---

### Documentation and Resources

| 简体中文 | English | 繁體中文 |
|:---:|:---:|:---:|
| [Documentation Entry](docs/zh-CN/README.md) | [Documentation](docs/en/README.md) | [文檔入口](docs/zh-TW/README.md) |

| Platform | Main Site | Backup Sites |
|------|--------|---------|
| Documentation | [erisdev.com](https://www.erisdev.com/#docs) | [Cloudflare](https://erispulse.pages.dev/#docs) · [GitHub](https://erispulse.github.io/#docs) · [Netlify](https://erispulse.netlify.app/#docs) |
| Module Market | [erisdev.com](https://www.erisdev.com/#market) | [Cloudflare](https://erispulse.pages.dev/#market) · [GitHub](https://erispulse.github.io/#market) · [Netlify](https://erispulse.netlify.app/#market) |

---

### Contribution Guidelines

The health of the ErisPulse project also needs your contribution! We welcome all forms of contribution:

1. **Report Issues** — Submit bug reports in [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues)
2. **Feature Requests** — Share new ideas through [Community Discussions](https://github.com/ErisPulse/ErisPulse/discussions)
3. **Code Contributions** — Before submitting PRs, please read the [Code Style Guide](docs/en/styleguide/) and [Contribution Guidelines](CONTRIBUTING.md)
4. **Documentation Improvements** — Help improve documentation and example code

[Join Community Discussions](https://github.com/ErisPulse/ErisPulse/discussions)

---

<div align="center">

### Acknowledgements

<img src=".github/assets/thanks.png" width="200" alt="Thanks" />

Some code in this project is based on [sdkFrame](https://github.com/runoneall/sdkFrame) · The core adapter standardization layer is based on [OneBot12 Specification](https://12.onebot.dev/) · Thanks to all developers and authors who contribute to the open source community

</div>