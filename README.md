<table>
<tr>
<td width="35%" valign="middle" align="center">

<img src=".github/assets/mascot-hero.png" width="320" alt="ErisPulse" />

</td>
<td valign="middle">

>  **English** | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | [Русский](README.ru.md)

> 🎉 **v2.5.0-dev.1 now supports multiple languages!** The framework core and CLI interface now have built-in support for Chinese (Simplified/Traditional), English, Japanese, and Russian, automatically switching based on your system language! 

# ErisPulse

**Event-driven multi-platform robot development framework**

Based on the OneBot12 standard interface, write once, deploy across multiple platforms. A flexible plugin system, hot-reload support, and a complete developer toolchain, suitable for various scenarios from simple chatbots to complex automation systems.

> Supports Vibe Coding workflow, letting AI directly generate usable modules — [View](docs/en/quick-start.md)

[![PyPI](https://img.shields.io/pypi/v/ErisPulse?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/ErisPulse/)
[![Python](https://img.shields.io/badge/Python-3.10+-FFD43B?style=for-the-badge&logo=python&logoColor=blue)](https://pypi.org/project/ErisPulse/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://hub.docker.com/r/erispulse/erispulse)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](https://github.com/ErisPulse/ErisPulse/blob/main/LICENSE)
[![Stars](https://img.shields.io/github/stars/ErisPulse/ErisPulse?style=for-the-badge&logo=github&color=brightgreen)](https://github.com/ErisPulse/ErisPulse)
[![Downloads](https://img.shields.io/pepy/dt/ErisPulse?style=for-the-badge&color=blue)](https://pypi.org/project/ErisPulse/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&style=for-the-badge)](https://github.com/astral-sh/ruff)
[![Socket](https://img.shields.io/badge/Socket-Secure-2ea043?style=for-the-badge&logo=socket&logoColor=white)](https://socket.dev/pypi/package/erispulse)

[![Documentation](https://img.shields.io/badge/Documentation-erisdev.com-FF6B9D?style=for-the-badge&logo=bookstack&logoColor=white)](https://www.erisdev.com)
[![Module Market](https://img.shields.io/badge/Module%20Market-erisdev.com-C724B1?style=for-the-badge&logo=webpack&logoColor=white)](https://www.erisdev.com/#market)
[![Discussion](https://img.shields.io/badge/GitHub-Discussions-181717?style=for-the-badge&logo=github)](https://github.com/ErisPulse/ErisPulse/discussions)

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

### ⚡ Event-driven Architecture

A clear event model based on the OneBot12 standard, making message handling logic more intuitive and efficient

</td>
<td width="50%" align="center" valign="top">
<br/>

### 🌐 Cross-platform Compatibility

Write plugin modules once and use them across all platforms, without repetitive development for different platforms

</td>
</tr>
<tr>
<td width="50%" align="center" valign="top">
<br/>

### 🧩 Modular Design

A flexible plugin system, easy to extend and integrate, supporting hot-swappable module management

</td>
<td width="50%" align="center" valign="top">
<br/>

### 🔄 Hot-reload Support

Reload code without restarting during development, greatly improving development iteration efficiency

</td>
</tr>
</table>

---

### Quick Start

#### One-click Installation Script (Recommended)

The installation script automatically detects your environment (Docker, Python, uv), guides you to choose the most suitable installation method, and supports multiple languages (Chinese/English/Japanese/Russian/Traditional Chinese).

Windows (PowerShell):
```powershell
irm https://get.erisdev.com/install.ps1 -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1
```

macOS / Linux:
```bash
curl -fsSL https://get.erisdev.com/install.sh -o install.sh && chmod +x install.sh && ./install.sh
```

<table>
<tr>
<td align="center" width="50%">

**Docker Installation Demo**

<video src="https://github.com/user-attachments/assets/a367a466-4678-46a9-b101-073a86388ede" controls width="100%"></video>

</td>
<td align="center" width="50%">

**pip Installation Demo**

<video src="https://github.com/user-attachments/assets/a2df4009-dba6-411e-b79d-4454a168d063" controls width="100%"></video>

</td>
</tr>
</table>

#### Using Docker (Recommended)

```bash
docker pull erispulse/erispulse:latest
```

<details>
<summary>Unable to access Docker Hub?</summary>

If Docker Hub is inaccessible, you can use GitHub Container Registry:

```bash
docker pull ghcr.io/erispulse/erispulse:latest
```

When using the ghcr.io image, modify the `docker-compose.yml` file's image:
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

After startup, visit `http://<host>:<port>/Dashboard`, and use the set token as the password to log in to the Dashboard management panel.

</details>

<details>
<summary>Using Pre-release Version (Dev)</summary>

Set `ERISPULSE_CHANNEL=dev` to use the pre-release version:

```bash
# Method 1: Use environment variable (Recommended)
ERISPULSE_CHANNEL=dev ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d

# Method 2: Build dev image
ERISPULSE_BUILD_TARGET=dev docker compose up -d --build
```

To automatically update to the latest version at startup (regardless of stable or dev), explicitly set `ERISPULSE_UPDATE_ON_START=true`:

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

| Variable | Default Value | Description |
|------|--------|------|
| `ERISPULSE_CHANNEL` | `stable` | Version channel: `stable` (stable version) or `dev` (pre-release version) |
| `ERISPULSE_UPDATE_ON_START` | `false` | Whether to automatically update to the latest version when the container starts (must be explicitly enabled) |
| `ERISPULSE_DASHBOARD_TOKEN` | empty | Dashboard login token |
| `ERISPULSE_PORT` | `8000` | Dashboard port mapping |
| `TZ` | `Asia/Shanghai` | Container timezone |

> Setting `ERISPULSE_UPDATE_ON_START=true` ensures that even if the image is outdated, the container will automatically fetch the latest version at startup.

</details>

#### 1Panel App Store

Install ErisPulse one-click via the [1Panel](https://1panel.cn) app store, see [ErisPulse-1Panel](https://github.com/ErisPulse/ErisPulse-1Panel).

```bash
bash <(curl -sL https://get-1panel.erisdev.com/install.sh)
```

#### Using pip Installation

```bash
pip install ErisPulse
```

> You can also use the one-click installation script above, which automatically detects the environment and guides configuration.

#### Running Effect

##### Dashboard:

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Dashboard-FF6B9D?style=for-the-badge&logo=github&logoColor=white)](https://dashdemo.erisdev.com/)

> 💡 Experience the live demo dashboard online: [DashDemo](https://dashdemo.erisdev.com/)

<table>
<tr>
<td width="50%">

<img src=".github/assets/docs/dashboard.png" alt="Dashboard Demo" />

</td>
<td width="50%">

<video src="https://github.com/user-attachments/assets/157191c4-9a84-433c-b311-0c57e3a21151" controls width="100%"></video>

</td>
</tr>
</table>


##### Same code, multiple platform responses:

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

#### Create First Robot

Create `main.py` file:

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

@command("ping", help="Test if the robot is online")
async def ping_handler(event):
    await event.reply("Pong! The robot is running normally.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(sdk.run(keep_running=True))
```

</td>
<td width="50%" valign="top">

**Effect Explanation**

Send `/hello`

Robot replies: `Hello, {username}!`

---

Send `/ping`

Robot replies: `Pong! The robot is running normally.`

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
- [Getting Started Guide](docs/en/getting-started.md)

#### Multi-turn Conversation Example

ErisPulse includes a powerful multi-turn conversation engine, making it easy to implement guided operations, information collection, and other interactive scenarios:

```python
from ErisPulse.Core.Event import command, request

@command("register")
async def register_handler(event):
    conv = event.conversation(timeout=60)
    
    await conv.say("Welcome to register!")
    
    # Multi-step collection of user information, with automatic validation
    data = await conv.collect([
        {"key": "name", "prompt": "Please enter your name"},
        {"key": "age", "prompt": "Please enter your age",
         "validator": lambda e: e.get_text().strip().isdigit(),
         "retry_prompt": "Age must be a number, please re-enter"},
    ])
    
    if data and await conv.confirm(f"Confirm registration? Name: {data['name']}, Age: {data['age']}"):
        # Use SendDSL to actively push notifications
        await sdk.adapter.get(event.get_platform()).Send.To(
            "user", event.get_user_id()
        ).Text(f"Registration successful! Welcome {data['name']}")
        # Or await event.reply("Registration successful!")

# Automatically handle friend requests
@request.on_friend_request()
async def handle_friend_request(event):
    user_name = event.get_user_nickname() or event.get_user_id()
    
    # Approve the request
    result = await event.approve()
    if result.get("status") == "ok":
        await event.reply(f"Friend request approved automatically, welcome {user_name}")
```

<details>
<summary>See more Conversation API (branching/joining/selection/persistence)</summary>

```python
@command("quiz")
async def quiz_handler(event):
    conv = event.conversation(timeout=30)
    
    # Multiple-choice question
    answer = await conv.choose("Who is the creator of Python?", [
        "Guido van Rossum",
        "James Gosling", 
        "Dennis Ritchie",
    ])
    
    if answer == 0:
        await conv.say("Correct!")
    elif answer is None:
        await conv.say("Timed out, try again next time!")
    else:
        await conv.say("Incorrect, the correct answer is Guido van Rossum")

@command("menu")
async def menu_handler(event):
    conv = event.conversation(timeout=60)
    
    # Branching, build complex interaction flow
    @conv.branch("main")
    async def main_menu():
        await conv.say("=== Main Menu ===\n1. Personal Information\n2. Settings\n3. Exit")
        resp = await conv.wait()
        if resp and resp.get_text().strip() == "1":
            await conv.goto("profile")
    
    @conv.branch("profile")
    async def profile():
        await conv.say("Name: Alice\n0. Return")
        resp = await conv.wait()
        if resp and resp.get_text().strip() == "0":
            await conv.goto("main")
    
    await conv.start()
```

See [Conversation Multi-turn Dialogue](docs/en/advanced/conversation.md)

</details>

---

### Supported Adapters

We welcome your contributions to adapters!

| Adapter | Description |
|--------|------|
| <img src=".github/assets/adapter_logo/kook.svg" height="20" alt="Kook" /> [Kook](https://github.com/shanfishapp/ErisPulse-KookAdapter) | Kook (Kahei La) instant messaging platform |
| <img src=".github/assets/adapter_logo/matrix.svg" height="20" alt="Matrix" /> [Matrix](https://github.com/ErisPulse/ErisPulse-MatrixAdapter) | Matrix decentralized communication protocol |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot11](https://github.com/ErisPulse/ErisPulse-OneBot11Adapter) | OneBot v11 general robot protocol |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot12](https://github.com/ErisPulse/ErisPulse-OneBot12Adapter) | OneBot v12 standard protocol |
| <img src=".github/assets/adapter_logo/qqbot.svg" height="20" alt="QQ" /> [QQ](https://github.com/ErisPulse/ErisPulse-QQBotAdapter) | Official QQ robot platform |
| <img src=".github/assets/adapter_logo/sandbox.png" height="20" alt="Sandbox" /> [Sandbox](https://github.com/ErisPulse/ErisPulse-SandboxAdapter) | Web-based debugging, no need to connect to real platforms |
| <img src=".github/assets/adapter_logo/telegram.svg" height="20" alt="Telegram" /> [Telegram](https://github.com/ErisPulse/ErisPulse-TelegramAdapter) | Global instant messaging platform |
| <img src=".github/assets/adapter_logo/email.svg" height="20" alt="Email" /> [Email](https://github.com/ErisPulse/ErisPulse-EmailAdapter) | Email protocol adapter for sending and receiving |
| <img src=".github/assets/adapter_logo/yunhu.png" height="20" alt="Yunhu" /> [Yunhu](https://github.com/ErisPulse/ErisPulse-YunhuAdapter) | Enterprise-level instant messaging platform (robot access) |
| [Yunhu User](https://github.com/wsu2059q/ErisPulse-YunhuUserAdapter) | Access adapter based on the Yunhu user protocol |
| [Flower Maple Cafe](https://github.com/ErisPulse/ErisPulse-Ideaura/) | Allons! \(・ω・) / |
| <img src=".github/assets/adapter_logo/discord.svg" height="20" alt="Discord" /> [Discord](https://github.com/ErisPulse/ErisPulse-DiscordAdapter) | Global community communication platform, supports servers, channels, and private messages |
| <img src=".github/assets/adapter_logo/webhook.svg" height="20" alt="Webhook" /> [Webhook](https://github.com/ErisPulse/ErisPulse-WebhookAdapter) | General HTTP bridge adapter, connects to any system |
| <img src=".github/assets/adapter_logo/wechatmp.png" height="20" alt="WechatMp" /> [WeChat Official Account](https://github.com/ErisPulse/ErisPulse-WechatMpAdapter) | Official WeChat Official Account platform |

See [Adapter Details](docs/en/platform-guide/README.md)

---

### Application Scenarios

<div align="center">

| Multi-platform Robot | Chat Assistant | Automation Tool | Message Forwarding |
|:---:|:---:|:---:|:---:|
| Deploy robots with the same functionality across multiple platforms | Integrate AI chat modules for entertainment and interaction | Message notifications, task management, data collection | Cross-platform message synchronization and forwarding |

</div>

---

### Contribution Guide

The health of the ErisPulse project still needs your contribution! We welcome various forms of contributions:

1. **Report Issues** — Submit bug reports in [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues)
2. **Feature Requests** — Propose new ideas through [Community Discussions](https://github.com/ErisPulse/ErisPulse/discussions)
3. **Code Contributions** — Read [Code Style](docs/en/styleguide/) and [Contribution Guide](CONTRIBUTING.md) before submitting PRs
4. **Documentation Improvements** — Help improve documentation and example code

[Join Community Discussions](https://github.com/ErisPulse/ErisPulse/discussions)

---

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=ErisPulse/ErisPulse&type=Date)](https://star-history.com/#ErisPulse/ErisPulse&Date)

---

<div align="center">

### Acknowledgments

<img src=".github/assets/thanks.png" width="200" alt="Thanks" />

This project is partially based on [sdkFrame](https://github.com/runoneall/sdkFrame) · The core adapter standardization layer is based on the [OneBot12 specification](https://12.onebot.dev/) · Thank you to all developers and authors who have contributed to the open-source community

</div>
