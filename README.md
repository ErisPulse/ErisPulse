<img src=".github/assets/mascot-hero.png" align="right" width="300" alt="ErisPulse" style="margin-left: 24px; margin-bottom: 16px; border-radius: 12px;" />

**English** | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | [Русский](README.ru.md)

# ErisPulse

**Write once, deploy on multiple platforms.**

An event-driven multi-platform chatbot development framework.

Based on the OneBot12 standard interface, write once and deploy on multiple platforms. With a flexible plugin system, hot reload support, and a complete developer toolchain, it is suitable for various scenarios from simple chatbots to complex automation systems.

<p>
  <a href="https://pypi.org/project/ErisPulse/"><img src="https://img.shields.io/pypi/v/ErisPulse?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI"></a>
  <a href="https://pypi.org/project/ErisPulse/"><img src="https://img.shields.io/badge/Python-3.10+-FFD43B?style=for-the-badge&logo=python&logoColor=blue" alt="Python"></a>
  <a href="https://hub.docker.com/r/erispulse/erispulse"><img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"></a>
  <a href="https://github.com/ErisPulse/ErisPulse/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License"></a>
  <a href="https://github.com/ErisPulse/ErisPulse"><img src="https://img.shields.io/github/stars/ErisPulse/ErisPulse?style=for-the-badge&logo=github&color=brightgreen" alt="Stars"></a>
  <a href="https://pepy.tech/project/ErisPulse"><img src="https://img.shields.io/pepy/dt/ErisPulse?style=for-the-badge&color=blue" alt="Downloads"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&style=for-the-badge" alt="Ruff"></a>
  <a href="https://socket.dev/pypi/package/erispulse"><img src="https://img.shields.io/badge/Socket-Secure-2ea043?style=for-the-badge&logo=socket&logoColor=white" alt="Socket"></a>
  <a href="https://www.erisdev.com"><img src="https://img.shields.io/badge/文档-erisdev.com-FF6B9D?style=for-the-badge&logo=bookstack&logoColor=white" alt="文档"></a>
  <a href="https://deepwiki.com/ErisPulse/ErisPulse"><img src="https://img.shields.io/badge/DeepWiki-ErisPulse-8A2BE2?style=for-the-badge&logo=readthedocs&logoColor=white" alt="DeepWiki"></a>
  <a href="https://www.erisdev.com/#market"><img src="https://img.shields.io/badge/模块市场-erisdev.com-C724B1?style=for-the-badge&logo=webpack&logoColor=white" alt="模块市场"></a>
  <a href="https://github.com/ErisPulse/ErisPulse/discussions"><img src="https://img.shields.io/badge/GitHub-Discussions-181717?style=for-the-badge&logo=github" alt="讨论"></a>
</p>

<br clear="both">

---

<div align="center">

### Core Features

</div>

<table>
<tr>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_event_driven.png.png" width="50" alt="Event-driven Architecture" />

### Event-driven Architecture

A clear event model based on the OneBot12 standard makes message handling logic more intuitive and efficient

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_cross_platform.png.png" width="50" alt="Cross-platform Compatibility" />

### Cross-platform Compatibility

Write a plugin module once and use it on all platforms, no need to repeat development for different platforms

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_modular.png" width="50" alt="Modular Design" />

### Modular Design

A flexible plugin system, easy to extend and integrate, supports hot-plug module management

</td>
</tr>
<tr>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_hot_reload.png" width="50" alt="Hot Reload" />

### Hot Reload

Reload code without restarting during development

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_ai_assist.png" width="50" alt="AI Assistance" />

### AI Assistance

AI-assisted development allows requirements to be directly translated into usable modules

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_lightweight.png" width="50" alt="Simple and Elegant" />

### Simple and Elegant

Intuitive API design, making code as light and readable as feathers

</td>
</tr>
</table>

### Chainable Send DSL

A single chain call completes all sending logic such as @, reply, retry, timeout, and callback:

```python
yunhu = sdk.adapter.get("yunhu")

# Single send: @user + reply + retry + success callback
await (yunhu.Send.To("group", "123")
       .At("456").Reply("msg_789")
       .Retry(3).Timeout(10)
       .Hook(lambda r: print("Send successful!"))
       .Text("Hello"))

# Batch send: send multiple messages in a single chain
results = await (yunhu.Send.To("user", "123")
                .Build()
                .Text("Notification 1")
                .Image("pic.jpg")
                .Retry(2)
                .send_all())
```

> Supports Hook (success callback), Retry (failure retry), Timeout (timeout cancellation), OnProgress (progress monitoring), Defer (delayed sending), Build (batch construction), and other chainable methods. See [SendDSL documentation](docs/en/developer-guide/adapters/send-dsl.md).

---

## The Same Code. Multiple Platforms.

*Identical command handlers. Different platforms. No business logic changes required.*

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

---

## Ecosystem

ErisPulse is not just a framework. Install and start right away, no need to build from scratch.

<table>
<tr>
<td align="center" width="25%">

**Framework**

Core runtime

Unified event & message model

</td>
<td align="center" width="25%">

**Dashboard**

Visual management

Plugins · Logs · Configuration

[Online demo →](https://dashdemo.erisdev.com/)

</td>
<td align="center" width="25%">

**AI Builder**

Natural language → usable modules

[Experience now →](https://www.erisdev.com/#builder)

</td>
<td align="center" width="25%">

**Module Market**

Ready-to-use plugins

[Explore modules →](https://www.erisdev.com/#market)

</td>
</tr>
<tr>
<td align="center" width="25%">

**Adapters**

Support for 15+ platforms

</td>
<td align="center" width="25%">

**Documentation**

[erisdev.com](https://www.erisdev.com)

</td>
<td align="center" width="25%">

**Docker**

Multi-architecture support

`erispulse/erispulse`

</td>
<td align="center" width="25%">

**CLI**

`epsdk` scaffolding tool

</td>
</tr>
</table>

---

## Project Origin

ErisPulse was not created just to be a framework.

It originated from **Amer** — a project for message interconnection and synchronization between different platforms.

As more platforms were integrated, we began maintaining the asynchronous version of **ryunhusdk2**, gradually abstracting a unified event model and adapter system.

These practices eventually evolved into today's ErisPulse.

Its goal has never changed:

**Let developers focus on business logic, not platform differences.**

---

### Quick Start

#### One-click installation script (recommended)

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

#### Using Docker (recommended)

```bash
docker pull erispulse/erispulse:latest
```

<details>
<summary>Docker Hub unavailable?</summary>

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
<summary>Quick start</summary>

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
<summary>Using pre-release version (Dev)</summary>

Set `ERISPULSE_CHANNEL=dev` to use the pre-release version:

```bash
# Method 1: Use environment variables (recommended)
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

| Variable | Default | Description |
|------|--------|------|
| `ERISPULSE_CHANNEL` | `stable` | Version channel: `stable` (stable) or `dev` (pre-release) |
| `ERISPULSE_UPDATE_ON_START` | `false` | Whether to automatically update to the latest version when the container starts (must be explicitly enabled) |
| `ERISPULSE_DASHBOARD_TOKEN` | empty | Dashboard login token |
| `ERISPULSE_PORT` | `8000` | Dashboard port mapping |
| `TZ` | `Asia/Shanghai` | Container timezone |

> Setting `ERISPULSE_UPDATE_ON_START=true` ensures that even if the image is outdated, the container will automatically fetch the latest version at startup.

</details>

#### 1Panel App Store

Install ErisPulse with one click via the [1Panel](https://1panel.cn) app store, see [ErisPulse-1Panel](https://github.com/ErisPulse/ErisPulse-1Panel).

```bash
bash <(curl -sL https://get-1panel.erisdev.com/install.sh)
```

ErisPulse is available in the 1Panel third-party app store, and can be installed using the [okxlin/appstore](https://github.com/okxlin/appstore) third-party repository.

#### Using pip to install

```bash
pip install ErisPulse
```

> You can also use the one-click installation script above, which automatically detects the environment and guides configuration.

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

@command("hello", help="Send a greeting message")
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

**Effect Explanation**

Send `/hello`

Bot replies: `Hello, {username}!`

---

Send `/ping`

Bot replies: `Pong! The bot is running normally.`

---

**Running Method**

```bash
epsdk run main.py
# Or in development mode
epsdk run main.py --reload
```

</td>
</tr>
</table>

For more detailed instructions, see:
- [Quick Start Guide](docs/en/quick-start.md)
- [Getting Started Guide](docs/en/getting-started/)

#### Multi-turn Conversation Example

ErisPulse has a powerful built-in multi-turn conversation engine, easily enabling guided operations, information collection, and other interactive scenarios:

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
        # Push notification using SendDSL
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
<summary>See more Conversation API (branching / selection / persistence)</summary>

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
    
    # Branching, building complex interaction flow
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

## Supported Platforms

We welcome contributions to adapters!

| Adapter | Description |
|--------|------|
| <img src=".github/assets/adapter_logo/kook.svg" height="20" alt="Kook" /> [Kook](https://github.com/shanfishapp/ErisPulse-KookAdapter) | Kook (Kaihei La) instant messaging platform |
| <img src=".github/assets/adapter_logo/matrix.svg" height="20" alt="Matrix" /> [Matrix](https://github.com/ErisPulse/ErisPulse-MatrixAdapter) | Matrix decentralized communication protocol |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot11](https://github.com/ErisPulse/ErisPulse-OneBot11Adapter) | OneBot v11 generic robot protocol |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot12](https://github.com/ErisPulse/ErisPulse-OneBot12Adapter) | OneBot v12 standard protocol |
| <img src=".github/assets/adapter_logo/qqbot.svg" height="20" alt="QQ" /> [QQ](https://github.com/ErisPulse/ErisPulse-QQBotAdapter) | Official QQ robot platform |
| <img src=".github/assets/adapter_logo/sandbox.png" height="20" alt="Sandbox" /> [Sandbox](https://github.com/ErisPulse/ErisPulse-SandboxAdapter) | Web-based debugging, no real platform integration required |
| <img src=".github/assets/adapter_logo/telegram.svg" height="20" alt="Telegram" /> [Telegram](https://github.com/ErisPulse/ErisPulse-TelegramAdapter) | Global instant messaging platform |
| <img src=".github/assets/adapter_logo/email.svg" height="20" alt="Email" /> [Email](https://github.com/ErisPulse/ErisPulse-EmailAdapter) | Email protocol adapter for sending and receiving |
| <img src=".github/assets/adapter_logo/yunhu.png" height="20" alt="Yunhu" /> [Yunhu](https://github.com/ErisPulse/ErisPulse-YunhuAdapter) | Enterprise-level instant messaging platform (robot integration) |
| <img src=".github/assets/adapter_logo/yunhu.png" height="20" alt="Yunhu" /> [Yunhu User](https://github.com/wsu2059q/ErisPulse-YunhuUserAdapter) | Access adapter based on the Yunhu user protocol |
| [Hua Feng Coffeehouse](https://github.com/ErisPulse/ErisPulse-Ideaura/) | Allons! \(・ω・) / |
| <img src=".github/assets/adapter_logo/discord.svg" height="20" alt="Discord" /> [Discord](https://github.com/ErisPulse/ErisPulse-DiscordAdapter) | Global community communication platform, supports servers, channels, and private messages |
| <img src=".github/assets/adapter_logo/webhook.svg" height="20" alt="Webhook" /> [Webhook](https://github.com/ErisPulse/ErisPulse-WebhookAdapter) | General HTTP bridge adapter, connects to any system |
| <img src=".github/assets/adapter_logo/wechatmp.svg" height="20" alt="WechatMp" /> [WeChat Official Account](https://github.com/ErisPulse/ErisPulse-WechatMpAdapter) | Official WeChat official account platform |

See [Adapter Details](docs/en/platform-guide/README.md)

---

### Use Cases

<div align="center">

| Multi-platform Bot | Chat Assistant | Automation Tool | Message Forwarding |
|:---:|:---:|:---:|:---:|
| Deploy the same functionality bot on multiple platforms | Integrate AI chat module for entertainment and interaction | Message notifications, task management, data collection | Cross-platform message synchronization and forwarding |

</div>

---

## Community

Welcome to join the ErisPulse community and build the ecosystem together with developers.

### Yunhu

Group ID: `635409929`

Join the group chat:

https://yhfx.jwznb.com/share?key=VWJL4fTWXepa&ts=1781889199

### QQ Group

https://qm.qq.com/q/TOwnCmypcy

### Telegram

https://t.me/ErisPulse

---

### Contribution Guide

The health of the ErisPulse project still needs your contribution! We welcome all forms of contributions:

1. **Report Issues** — Submit bug reports on [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues)
2. **Feature Requests** — Propose new ideas via [Community Discussions](https://github.com/ErisPulse/ErisPulse/discussions)
3. **Code Contributions** — Read [Code Style](docs/en/styleguide/) and [Contribution Guide](CONTRIBUTING.md) before submitting PRs
4. **Documentation Improvements** — Help improve documentation and example code

[Join Community Discussions](https://github.com/ErisPulse/ErisPulse/discussions)

---

<div align="center">

### Acknowledgments

<img src=".github/assets/thanks.png" width="200" alt="Thanks" />

Some code in this project is based on [sdkFrame](https://github.com/runoneall/sdkFrame).

The core adapter standardization layer refers to and benefits from the [OneBot12 specification](https://12.onebot.dev/).

Special thanks to the Yunhu ecosystem and community.

ErisPulse's early exploration and growth would not have been possible without the support of the Yunhu developer community. Many ideas, adapters, and practical experiences originated here.

We also thank all developers and project authors who have contributed to ErisPulse, OneBot, and the open-source community.

</div>