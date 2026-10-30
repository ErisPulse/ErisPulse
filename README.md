<img src=".github/assets/mascot-hero.png" align="right" width="300" alt="ErisPulse" style="margin-left: 24px; margin-bottom: 16px; border-radius: 12px;" />

[**English**](README.md) | 简体中文 | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | [Русский](README.ru.md)

# ErisPulse

**Write once, deploy to QQ / Telegram / Kook / Yunhu / WeChat Official Account / OneBot12 / ... multiple platforms.**

A modular, event-driven, asynchronous robot framework based on the OneBot12 standard interface. Business logic is written once, and adapters handle platform differences; the plugin system, hot reload, and full developer toolchain are ready to use out of the box.

<p>
  <a href="https://pypi.org/project/ErisPulse/"><img src="https://img.shields.io/pypi/v/ErisPulse?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI"></a>
  <a href="https://pypi.org/project/ErisPulse/"><img src="https://img.shields.io/badge/Python-3.10+-FFD43B?style=for-the-badge&logo=python&logoColor=blue" alt="Python"></a>
  <a href="https://github.com/botuniverse/onebot-11"><img src="https://img.shields.io/badge/OneBot-11-black?style=for-the-badge" alt="OneBot 11"></a>
  <a href="https://12.onebot.dev/"><img src="https://img.shields.io/badge/OneBot-12-black?style=for-the-badge" alt="OneBot 12"></a>
  <a href="https://hub.docker.com/r/erispulse/erispulse"><img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"></a>
  <a href="https://github.com/ErisPulse/ErisPulse/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License"></a>
  <a href="https://pepy.tech/project/ErisPulse"><img src="https://img.shields.io/pepy/dt/ErisPulse?style=for-the-badge&color=blue" alt="Downloads"></a>
  <a href="https://github.com/ErisPulse/ErisPulse/stargazers"><img src="https://img.shields.io/github/stars/ErisPulse/ErisPulse?style=for-the-badge&logo=github&color=yellow" alt="Stars"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&style=for-the-badge" alt="Ruff"></a>
  <a href="https://socket.dev/pypi/package/erispulse"><img src="https://img.shields.io/badge/Socket-Secure-2ea043?style=for-the-badge&logo=socket&logoColor=white" alt="Socket"></a>
  <a href="https://www.erisdev.com"><img src="https://img.shields.io/badge/文档-erisdev.com-FF6B9D?style=for-the-badge&logo=bookstack&logoColor=white" alt="Documentation"></a>
  <a href="https://deepwiki.com/ErisPulse/ErisPulse"><img src="https://img.shields.io/badge/DeepWiki-ErisPulse-8A2BE2?style=for-the-badge&logo=readthedocs&logoColor=white" alt="DeepWiki"></a>
  <a href="https://www.erisdev.com/#market"><img src="https://img.shields.io/badge/模块市场-erisdev.com-C724B1?style=for-the-badge&logo=webpack&logoColor=white" alt="Module Market"></a>
  <a href="https://github.com/ErisPulse/ErisPulse/discussions"><img src="https://img.shields.io/badge/GitHub-Discussions-181717?style=for-the-badge&logo=github" alt="Discussions"></a>
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

<img src=".github/assets/icon/icon_event_driven.png.png" width="50" alt="Event-Driven Architecture" />

### Event-Driven Architecture

Based on the unified event model of OneBot12, a single handler adapts to all adapters

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_cross_platform.png.png" width="50" alt="Cross-Platform Compatibility" />

### Cross-Platform Compatibility

15+ platforms including QQ / Telegram / Kook / Yunhu, business code requires no changes

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_modular.png" width="50" alt="Modular Design" />

### Modular Design

Hot-plug plugins without restart, scope controlled by platform / Bot / session

</td>
</tr>
<tr>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_hot_reload.png" width="50" alt="Hot Reload" />

### Hot Reload

Save and apply changes instantly, hot reload is seamless and lightweight

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_ai_assist.png" width="50" alt="AI Assistance" />

### AI Assistance

Describe requirements in natural language, directly generate usable modules

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_lightweight.png" width="50" alt="Simple and Elegant" />

### Simple and Elegant

Chained API: @ user, reply, retry, batch send in one line

</td>
</tr>
</table>

---

## How It Works

ErisPulse uses an adapter layer to abstract platform differences, allowing business code to focus solely on events:

```mermaid
graph LR
    P["15+ Platforms<br/>QQ · Telegram · Kook · Yunhu · WeChat Official Account · Email · Webhook ..."]
    A["Adapter Layer<br/>Native protocols → OneBot12 standard events"]
    Event["Event Bus<br/>Middleware → Distribute command/message/notice/request/meta"]
    M["Business Modules<br/>@command / @message handlers · Your modules"]
    P --> A --> Event --> M
    M -.->|"event.reply() / SendDSL"| Event
```

- **Adapter Layer** converts native protocols from various platforms into OneBot12 standard events, hiding platform differences from business modules
- **Event Bus** executes middleware chains first, then distributes events by type to five handler categories
- **Your code** subscribes to events using decorators and replies using `event.reply()` or SendDSL — replies follow the same path back to the platform

For detailed information on module composition, initialization flow, and lifecycle events, see [Architecture Overview](docs/en/architecture.md).

---

## Quick Start

### One-Click Installation Script (Recommended)

The installation script automatically detects your environment (Docker, Python, uv), guides you through selecting the most suitable installation method, and supports multiple languages (Chinese/English/Japanese/Russian/Traditional Chinese).

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

### Using Docker (Recommended)

```bash
docker pull erispulse/erispulse:latest
```

<details>
<summary>Docker Hub Unavailable?</summary>

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

After starting, access `http://<host>:8000/Dashboard` and log in using the set token to manage the Dashboard panel.

> The image includes the ErisPulse framework and Dashboard management panel, supporting `linux/amd64` and `linux/arm64` architectures.
>
> **Persistence**: Configuration files and installed modules/adapters are persisted to the host via volume mounts, so they won't be lost after container restarts. Framework updates are completed through Dashboard hot reload.

</details>

<details>
<summary>Docker Environment Variables</summary>

| Variable | Default | Description |
|----------|---------|-------------|
| `ERISPULSE_DASHBOARD_TOKEN` | empty | Dashboard login token (automatically written to config after setting) |
| `ERISPULSE_PORT` | `8000` | Dashboard port mapping |
| `ERISPULSE_TAG` | `latest` | Image tag, set to `dev` for pre-release images |
| `CONTAINER_NAME` | `erispulse` | Container name |
| `TZ` | `Asia/Shanghai` | Container timezone |
| `LANG` | `en_US.UTF-8` | System language, automatically detected for startup interface language |
| `ERISPULSE_LANG` | empty | Force startup interface language: `zh` / `zh_TW` / `en` / `ja` / `ru` (overrides `LANG`) |

</details>

### 1Panel App Store

Install ErisPulse via the [1Panel](https://1panel.cn) app store, see [ErisPulse-1Panel](https://github.com/ErisPulse/ErisPulse-1Panel).

```bash
bash <(curl -sL https://get-1panel.erisdev.com/install.sh)
```

ErisPulse is available in the 1Panel third-party app store, and can be installed using the [okxlin/appstore](https://github.com/okxlin/appstore) third-party repository.

### Using pip

```bash
pip install ErisPulse
```

If you want to use `epsdk` as a global command-line tool without entering a virtual environment, we recommend `uv tool install`:

```bash
uv tool install ErisPulse
```

> You can also use the one-click installation script above, which automatically detects the environment and guides configuration (the script menu also provides the "global CLI installation (uv tool)" method).

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
# or in development mode
epsdk run main.py --reload
```

</td>
</tr>
</table>

For more detailed instructions, please refer to:
- [Quick Start Guide](docs/en/quick-start.md)
- [Getting Started Guide](docs/en/getting-started/)

---

## The Same Code. Multiple Platforms.

*Exactly the same command handler. Different platforms. No changes to business logic required.*

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

---

## Chained Send DSL

@ user, reply, retry, timeout, success callback — complex send logic written in a single chain:

```python
yunhu = sdk.adapter.get("yunhu")

# Single send: @user + reply + retry + success callback
await (yunhu.Send.To("group", "123").At("456").Reply("msg_789")
       .Retry(3).Timeout(10)
       .Hook(lambda r: print("Send successful!")).Text("Hello"))

# Batch send: send multiple messages in a single chain
results = await (yunhu.Send.To("user", "123").Build()
                 .Text("Notification 1").Image("pic.jpg").Retry(2).send_all())
```

> Hook / Retry / Timeout / OnProgress / Defer / Build and all other chained methods are documented in [SendDSL Documentation](docs/en/developer-guide/adapters/send-dsl.md).

---

## Multi-Turn Conversation Example

Collect information, validate input, confirm submission — no need to manage conversation state yourself:

```python
from ErisPulse.Core.Event import command

@command("register")
async def register_handler(event):
    conv = event.conversation(timeout=60)
    await conv.say("Welcome to register!")
    data = await conv.collect([
        {"key": "name", "prompt": "Please enter your name"},
        {"key": "age", "prompt": "Please enter your age",
         "validator": lambda e: e.get_text().strip().isdigit(),
         "retry_prompt": "Age must be a number, please re-enter"},
    ])
    if data and await conv.confirm(f"Confirm registration? Name: {data['name']}, Age: {data['age']}"):
        await event.reply(f"Registration successful! Welcome {data['name']}")
```

> Complete capabilities such as option-based questions (choose), branching jumps (branch / goto), and persistence are documented in [Conversation Multi-Turn Dialogue](docs/en/advanced/conversation.md).

---

## Core Modules

A single `sdk` entry point connects all core capabilities:

```mermaid
graph LR
    SDK["sdk unified entry point"] --> Event & Adapter & Module & Router & Storage
    SDK --> Config & Lifecycle & Logger & HttpClient
```

| Module | Description |
|--------|-------------|
| **Event** | Event system, providing five event types: command / message / notice / request / meta + Conversation multi-turn dialogue |
| **Adapter** | Adapter management, BaseAdapter base class for unified event transformation and SendDSL sending, supports 15+ platforms including QQ / Telegram / Kook / Yunhu / WeChat Official Account |
| **Module** | Module management, BaseModule base class + dependency declaration and topological loading |
| **SendDSL** | Chained sending, complex logic such as @/reply/retry/timeout/batch in one line |
| **Router** | HTTP/WebSocket routing system (FastAPI + Uvicorn) |
| **Storage** | Key-value storage based on SQLite + general SQL chained query |
| **Config** | TOML configuration management |
| **Lifecycle** | Lifecycle event hooks (core.init / adapter.* / module.*) |
| **Logger** | Modular logging system, supports sub-loggers |
| **HttpClient** | Unified HTTP/WS client (based on aiohttp), built-in retry and ErisPulse exception system |

For more design details (initialization flow, lifecycle events, module loading strategy), see [Architecture Overview](docs/en/architecture.md).

---

## Scope — Three-Dimensional Permission Control

Without changing any module code, declare "what is effective within what scope" in the configuration:

```toml
[ErisPulse.scope.platforms.onebot11]
modules = ["Chat", "Tool*"]           # ① Module dimension: Only these modules are open on this platform (glob / regex)

[ErisPulse.scope.identity.users.onebot11]
deny = ["u_bad", "spam_*"]            # ② Identity dimension: Event from blacklisted users is directly discarded

[ErisPulse.scope.actions.MyModule]
send = { allow = ["Text"] }           # ③ Outbound dimension: This module can only send text
api = { deny = ["set_*", "leave_*"] } #    and prohibit management APIs
```

```python
# Runtime can also be called, effective immediately (supports dictionary-style read/write via dot notation)
sdk.scope.set_action("MyModule", "api", deny=["set_*"])
```

> See [Scope](docs/en/advanced/scope.md)

---

## Event Override — Without Changing Module Code, Override Behavior of Any Event Type

Change trigger words, add admin restrictions to commands, without modifying module source code, configuration takes effect immediately:

```toml
# Override message handler trigger condition (AND with code-side condition; all types: meta/message/notice/request/command supported)
[ErisPulse.event.overrides.message.ChatModule]
pattern = "闲聊*"

# Override command implementation parameters (master / hidden / aliases / prefix, user priority)
[ErisPulse.event.overrides.command.MyModule.restart]
master = true
```

> See [Event Override](docs/en/getting-started/event-handling.md)

---

## Ecosystem

ErisPulse is not just a framework. Install and start immediately, no need to build wheels from scratch.

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

[Online Demo →](https://dashdemo.erisdev.com/)

</td>
<td align="center" width="25%">

**AI Builder**

Natural language → Usable modules

[Experience Now →](https://builder.erisdev.com)

</td>
<td align="center" width="25%">

**Module Market**

Ready-to-use plugins

[Browse Modules →](https://www.erisdev.com/#market)

</td>
</tr>
<tr>
<td align="center" width="25%">

**Adapters**

15+ platform integrations

</td>
<td align="center" width="25%">

**ErisPulse-App**

Official multi-platform client

Run directly on mobile · Desktop tray always on

[Download & Install →](https://github.com/ErisPulse/ErisPulse-App/releases)

</td>
<td align="center" width="25%">

**Docker**

Multi-architecture support

`erispulse/erispulse`

</td>
<td align="center" width="25%">

**Documentation & CLI**

[erisdev.com](https://www.erisdev.com)

`epsdk` scaffolding tool

</td>
</tr>
</table>

---

## Supported Platforms

We welcome contributions to adapters! Don't know where to start? See [Contribution Guide](docs/en/contributing/README.md).

| Adapter | Description |
|---------|-------------|
| <img src=".github/assets/adapter_logo/kook.svg" height="20" alt="Kook" /> [Kook](https://github.com/shanfishapp/ErisPulse-KookAdapter) | Kook (open party) instant messaging platform |
| <img src=".github/assets/adapter_logo/matrix.svg" height="20" alt="Matrix" /> [Matrix](https://github.com/ErisPulse/ErisPulse-MatrixAdapter) | Matrix decentralized communication protocol |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot11](https://github.com/ErisPulse/ErisPulse-OneBot11Adapter) | OneBot v11 general robot protocol |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot12](https://github.com/ErisPulse/ErisPulse-OneBot12Adapter) | OneBot v12 standard protocol |
| <img src=".github/assets/adapter_logo/qqbot.svg" height="20" alt="QQ" /> [QQ](https://github.com/ErisPulse/ErisPulse-QQBotAdapter) | QQ official robot platform |
| <img src=".github/assets/adapter_logo/sandbox.png" height="20" alt="Sandbox" /> [Sandbox](https://github.com/ErisPulse/ErisPulse-SandboxAdapter) | Web terminal debugging, no need to connect to real platform |
| <img src=".github/assets/adapter_logo/terminal.svg" height="20" alt="Terminal" /> [Terminal](https://github.com/ErisPulse/ErisPulse-TerminalAdapter) | Command-line as chat, zero-config development and debugging |
| <img src=".github/assets/adapter_logo/telegram.svg" height="20" alt="Telegram" /> [Telegram](https://github.com/ErisPulse/ErisPulse-TelegramAdapter) | Global instant messaging platform |
| <img src=".github/assets/adapter_logo/email.svg" height="20" alt="Email" /> [Email](https://github.com/ErisPulse/ErisPulse-EmailAdapter) | Email protocol adapter |
| <img src=".github/assets/adapter_logo/yunhu.png" height="20" alt="Yunhu" /> [Yunhu](https://github.com/ErisPulse/ErisPulse-YunhuAdapter) | Enterprise-level instant messaging platform (robot access) |
| <img src=".github/assets/adapter_logo/yunhu.png" height="20" alt="Yunhu" /> [Yunhu User](https://github.com/wsu2059q/ErisPulse-YunhuUserAdapter) | Access adapter based on Yunhu user protocol |
| [Flower Maple Café](https://github.com/ErisPulse/ErisPulse-Ideaura/) | Allons! \(・ω・) / |
| <img src=".github/assets/adapter_logo/discord.svg" height="20" alt="Discord" /> [Discord](https://github.com/ErisPulse/ErisPulse-DiscordAdapter) | Global community communication platform, supports servers, channels, and private messages |
| <img src=".github/assets/adapter_logo/webhook.svg" height="20" alt="Webhook" /> [Webhook](https://github.com/ErisPulse/ErisPulse-WebhookAdapter) | General HTTP bridge adapter, connects to any system |
| <img src=".github/assets/adapter_logo/wechatmp.svg" height="20" alt="WechatMp" /> [WeChat Official Account](https://github.com/ErisPulse/ErisPulse-WechatMpAdapter) | WeChat official account platform |

See [Adapter Details](docs/en/platform-guide/README.md)

---

## Community

Connect with us:

- Telegram: <https://t.me/ErisPulse>
- QQ Group: <https://qm.qq.com/q/TOwnCmypcy>
- Yunhu Group: <https://yhfx.jwznb.com/share?key=VWJL4fTWXepa&ts=1781889199>

Found the project useful? Consider supporting us on [IfDian](https://ifdian.net/a/YingXinche) to help us continue development!

---

## Star History

If ErisPulse has helped you, please give it a star ⭐ — this is the most direct way to help more developers discover the project.

[![Star History Chart](https://api.star-history.com/svg?repos=ErisPulse/ErisPulse&type=Date)](https://star-history.com/#ErisPulse/ErisPulse&Date)

---

### Contribution Guide

The health of the ErisPulse project still needs your contribution! We welcome all forms of contributions:

1. **Report Issues** — Submit bug reports in [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues)
2. **Feature Requests** — Propose new ideas via [Community Discussions](https://github.com/ErisPulse/ErisPulse/discussions)
3. **Code Contributions** — Please read [Code Style](docs/en/styleguide/) and [Contribution Guide](CONTRIBUTING.md) before submitting PRs
4. **Documentation Improvements** — Help improve documentation and example code

**First-time Contributor?** Start here 👉 [First Contribution Practice](docs/en/contributing/first-contribution.md)

[Join Community Discussions](https://github.com/ErisPulse/ErisPulse/discussions)

---

<div align="center">

### Acknowledgments

<img src=".github/assets/thanks.png" width="200" alt="Thank You" />

This project's code is partially based on [sdkFrame](https://github.com/runoneall/sdkFrame), and its core adapter standardization layer references and benefits from the [OneBot12 Specification](https://12.onebot.dev/).

The early exploration and growth of ErisPulse would not have been possible without the support of the Yunhu developer community. Many ideas, adapters, and practical experiences originated here.

We also thank all developers and project authors who have contributed to ErisPulse, OneBot, and the open-source community.