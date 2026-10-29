<img src=".github/assets/mascot-hero.png" align="right" width="300" alt="ErisPulse" style="margin-left: 24px; margin-bottom: 16px; border-radius: 12px;" />

**English** | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | [Русский](README.ru.md)

# ErisPulse

**Write once, deploy to QQ / Telegram / Kook / Yunhu / WeChat Official Account / OneBot12 / ... multiple platforms.**

An asynchronous, event-driven, modular robot framework based on the OneBot12 standard interface. Business code is written once, and adapters handle platform-specific differences; the plugin system, hot reload, and complete developer toolchain are ready to use out of the box.

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

A unified event model based on OneBot12, a single handler adapts to all adapters

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_cross_platform.png.png" width="50" alt="Cross-Platform Compatibility" />

### Cross-Platform Compatibility

Support for 15+ platforms including QQ / Telegram / Kook / Yunhu, business code requires zero changes

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_modular.png" width="50" alt="Modular Design" />

### Modular Design

Hot-pluggable plugins without restart, scopes controlled by platform / Bot / session

</td>
</tr>
<tr>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_hot_reload.png" width="50" alt="Hot Reload" />

### Hot Reload

Save and apply changes instantly, hot reload is lightweight and seamless

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_ai_assist.png" width="50" alt="AI Assistance" />

### AI Assistance

Describe requirements in natural language, directly generate usable modules

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_lightweight.png" width="50" alt="Clean and Elegant" />

### Clean and Elegant

Chained API: @ user, reply, retry, batch send, all in one line

</td>
</tr>
</table>

---

## How It Works

ErisPulse hides platform differences through its adapter layer, allowing business code to focus solely on events:

```mermaid
graph LR
    P["15+ Platforms<br/>QQ · Telegram · Kook · Yunhu · WeChat Official Account · Email · Webhook ..."]
    A["Adapter Layer<br/>Native Protocol → OneBot12 Standard Event"]
    Event["Event Bus<br/>Middleware → Distribute command/message/notice/request/meta"]
    M["Business Module<br/>@command / @message Handlers · Your Module"]
    P --> A --> Event --> M
    M -.->|"event.reply() / SendDSL"| Event
```

- The **Adapter Layer** converts native protocols from each platform into OneBot12 standard events, so business modules are unaware of platform differences.
- The **Event Bus** executes a chain of middleware first, then distributes events to five types of handlers based on event type.
- Your code subscribes to events using decorators and replies via `event.reply()` or SendDSL — replies follow the same path back to the platform.

For detailed information on the complete module composition, initialization process, lifecycle events, and other design aspects, see [Architecture Overview](docs/en/architecture.md).

## Quick Start

### One-Click Installation Script (Recommended)

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

When using the ghcr.io image, you need to modify the `docker-compose.yml` file's image:
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

After starting, access `http://<host>:8000/Dashboard` and log in using the set token in the Dashboard management panel.

> The image includes the ErisPulse framework and Dashboard management panel, supporting `linux/amd64` and `linux/arm64` architectures.
>
> **Persistence**: Configuration files and installed modules/adapters are persisted to the host machine via volume mounting, so they won't be lost after container restart. Framework updates are completed through Dashboard hot updates.

</details>

<details>
<summary>Docker Environment Variables</summary>

| Variable | Default | Description |
|------|--------|------|
| `ERISPULSE_DASHBOARD_TOKEN` | Empty | Dashboard login token (automatically written to configuration after setting) |
| `ERISPULSE_PORT` | `8000` | Dashboard port mapping |
| `ERISPULSE_TAG` | `latest` | Image tag, can be set to `dev` to use pre-release images |
| `CONTAINER_NAME` | `erispulse` | Container name |
| `TZ` | `Asia/Shanghai` | Container timezone |
| `LANG` | `en_US.UTF-8` | System language, automatically detects the startup interface language |
| `ERISPULSE_LANG` | Empty | Force startup interface language: `zh` / `zh_TW` / `en` / `ja` / `ru` (overrides `LANG`) |

</details>

### 1Panel App Store

Install ErisPulse via the [1Panel](https://1panel.cn) app store, see [ErisPulse-1Panel](https://github.com/ErisPulse/ErisPulse-1Panel).

```bash
bash <(curl -sL https://get-1panel.erisdev.com/install.sh)
```

ErisPulse is listed in the 1Panel third-party app store and can be installed using the [okxlin/appstore](https://github.com/okxlin/appstore) third-party repository.

### Using pip to Install

```bash
pip install ErisPulse
```

If you want to use `epsdk` as a global command-line tool without entering a virtual environment, it is recommended to use `uv tool install`:

```bash
uv tool install ErisPulse
```

> You can also use the one-click installation script above, which automatically detects the environment and guides the configuration (the script menu also provides the "Global CLI Installation (uv tool)" option).

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
# or in development mode
epsdk run main.py --reload
```

</td>
</tr>
</table>

For more detailed instructions, see:
- [Quick Start Guide](docs/en/quick-start.md)
- [Getting Started Guide](docs/en/getting-started/)

---

## Same Code, Multiple Platforms.

*Identical command handlers. Different platforms. No changes to business logic required.*

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

## Chained Sending DSL

@ User, Reply, Retry, Timeout, Success Callback — complex sending logic, all written in a single chain:

```python
yunhu = sdk.adapter.get("yunhu")

# Single send: @user + reply + retry + success callback
await (yunhu.Send.To("group", "123").At("456").Reply("msg_789")
       .Retry(3).Timeout(10)
       .Hook(lambda r: print("Send successful!")).Text("Hello"))

# Batch: send multiple messages in one chain
results = await (yunhu.Send.To("user", "123").Build()
                 .Text("Notification 1").Image("pic.jpg").Retry(2).send_all())
```

> All chained methods such as Hook / Retry / Timeout / OnProgress / Defer / Build are documented in [SendDSL Documentation](docs/en/developer-guide/adapters/send-dsl.md).

---

## Multi-turn Conversation Examples

Collect information, validate input, and confirm submission—all without managing conversation state yourself:

```python
from ErisPulse.Core.Event import command

@command("register")
async def register_handler(event):
    conv = event.conversation(timeout=60)
    await conv.say("Welcome to registration!")
    data = await conv.collect([
        {"key": "name", "prompt": "Please enter your name"},
        {"key": "age", "prompt": "Please enter your age",
         "validator": lambda e: e.get_text().strip().isdigit(),
         "retry_prompt": "Age must be a number, please re-enter"},
    ])
    if data and await conv.confirm(f"Confirm registration? Name: {data['name']}, Age: {data['age']}"):
        await event.reply(f"Registration successful! Welcome {data['name']}")
```

> For full capabilities such as option-based questions (choose), branching jumps (branch / goto), persistence, see [Conversation Multi-turn Conversations](docs/en/advanced/conversation.md).

---

## Core Modules

A unified SDK entry point, connecting all core capabilities:

```mermaid
graph LR
    SDK["sdk unified entry"] --> Event & Adapter & Module & Router & Storage
    SDK --> Config & Lifecycle & Logger & HttpClient
```

| Module | Description |
|--------|-------------|
| **Event** | Event system, providing five types of events: command / message / notice / request / meta, plus Conversation for multi-turn dialogue |
| **Adapter** | Adapter management, BaseAdapter base class for unified event conversion and SendDSL sending, supporting over 15 platforms including QQ / Telegram / Kook / Yunhu / WeChat Official Account |
| **Module** | Module management, BaseModule base class + dependency declaration and topological sorting for loading |
| **SendDSL** | Chainable sending, complex logic such as @/reply/retry/timeout/batch completed in one line |
| **Router** | HTTP/WebSocket routing system (FastAPI + Uvicorn) |
| **Storage** | Key-value storage based on SQLite + generic SQL chainable query |
| **Config** | TOML configuration management |
| **Lifecycle** | Lifecycle event hooks (core.init / adapter.* / module.*) |
| **Logger** | Modular logging system, supporting sub-loggers |
| **HttpClient** | Unified HTTP/WS client (based on aiohttp), built-in retry and ErisPulse exception system |

For more details on design (initialization flow, lifecycle events, module loading strategy), see [Architecture Overview](docs/en/architecture.md).

## Scope — Three-Dimensional Permission Control

Without changing any module code, declare "what scope is effective" in the configuration:

```toml
[ErisPulse.scope.platforms.onebot11]
modules = ["Chat", "Tool*"]           # ① Module dimension: only these modules are open on this platform (glob / regex)

[ErisPulse.scope.identity.users.onebot11]
deny = ["u_bad", "spam_*"]            # ② Identity dimension: events from blacklisted users are directly discarded

[ErisPulse.scope.actions.MyModule]
send = { allow = ["Text"] }           # ③ Outbound dimension: this module only allows sending text
api = { deny = ["set_*", "leave_*"] } #    and prohibits management APIs
```

```python
# Runtime can also be called, immediately effective (supports dot-separated path dictionary read/write)
sdk.scope.set_action("MyModule", "api", deny=["set_*"])
```

> See [Scope](docs/en/advanced/scope.md)

---

## Event Overriding – Override Behavior of Any Event Type Without Modifying Module Code

Change trigger words, add admin restrictions to commands, and make configurations take effect without modifying module source code:

```toml
# Override message handler trigger conditions (AND with conditions in code; supports all types: meta/message/notice/request/command)
[ErisPulse.event.overrides.message.ChatModule]
pattern = "闲聊*"  # "闲聊*" means "chat*"

# Override command implementation parameters (master / hidden / aliases / prefix, etc.; user preference takes precedence)
[ErisPulse.event.overrides.command.MyModule.restart]
master = true
```

> See [Event Overriding](docs/en/getting-started/event-handling.md) for more details.

---

## Ecosystem

ErisPulse is not just a framework. Install and start right away, no need to build wheels from scratch.

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

Natural language → usable module

[Experience Now →](https://builder.erisdev.com)

</td>
<td align="center" width="25%">

**Module Market**

Plug-and-play plugins

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

Run directly on mobile · Desktop tray icon

[Download and Install →](https://github.com/ErisPulse/ErisPulse-App/releases)

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

We welcome contributions to adapters! Not sure where to start? See [Contribution Guide](docs/en/contributing/README.md).

| Adapter | Description |
|--------|------|
| <img src=".github/assets/adapter_logo/kook.svg" height="20" alt="Kook" /> [Kook](https://github.com/shanfishapp/ErisPulse-KookAdapter) | Kook (Open Black) instant messaging platform |
| <img src=".github/assets/adapter_logo/matrix.svg" height="20" alt="Matrix" /> [Matrix](https://github.com/ErisPulse/ErisPulse-MatrixAdapter) | Matrix decentralized communication protocol |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot11](https://github.com/ErisPulse/ErisPulse-OneBot11Adapter) | OneBot v11 general robot protocol |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot12](https://github.com/ErisPulse/ErisPulse-OneBot12Adapter) | OneBot v12 standard protocol |
| <img src=".github/assets/adapter_logo/qqbot.svg" height="20" alt="QQ" /> [QQ](https://github.com/ErisPulse/ErisPulse-QQBotAdapter) | QQ official robot platform |
| <img src=".github/assets/adapter_logo/sandbox.png" height="20" alt="Sandbox" /> [Sandbox](https://github.com/ErisPulse/ErisPulse-SandboxAdapter) | Web terminal debugging, no need to integrate real platforms |
| <img src=".github/assets/adapter_logo/terminal.svg" height="20" alt="Terminal" /> [Terminal](https://github.com/ErisPulse/ErisPulse-TerminalAdapter) | Command line as chat, zero configuration development and debugging |
| <img src=".github/assets/adapter_logo/telegram.svg" height="20" alt="Telegram" /> [Telegram](https://github.com/ErisPulse/ErisPulse-TelegramAdapter) | Global instant messaging platform |
| <img src=".github/assets/adapter_logo/email.svg" height="20" alt="Email" /> [Email](https://github.com/ErisPulse/ErisPulse-EmailAdapter) | Email protocol adapter |
| <img src=".github/assets/adapter_logo/yunhu.png" height="20" alt="Yunhu" /> [Yunhu](https://github.com/ErisPulse/ErisPulse-YunhuAdapter) | Enterprise-level instant messaging platform (robot integration) |
| <img src=".github/assets/adapter_logo/yunhu.png" height="20" alt="Yunhu" /> [Yunhu User](https://github.com/wsu2059q/ErisPulse-YunhuUserAdapter) | Adapter based on Yunhu user protocol |
| [Flower Maple Cafe](https://github.com/ErisPulse/ErisPulse-Ideaura/) | Allons! \(・ω・) / |
| <img src=".github/assets/adapter_logo/discord.svg" height="20" alt="Discord" /> [Discord](https://github.com/ErisPulse/ErisPulse-DiscordAdapter) | Global community communication platform, supports servers, channels, and private messages |
| <img src=".github/assets/adapter_logo/webhook.svg" height="20" alt="Webhook" /> [Webhook](https://github.com/ErisPulse/ErisPulse-WebhookAdapter) | General HTTP bridge adapter, connects to any system |
| <img src=".github/assets/adapter_logo/wechatmp.svg" height="20" alt="WechatMp" /> [WeChat Official Account](https://github.com/ErisPulse/ErisPulse-WechatMpAdapter) | Official WeChat platform |

See [Adapter Details](docs/en/platform-guide/README.md)

---

## Community

Connect with us:

- Telegram: <https://t.me/ErisPulse>
- QQ Group: <https://qm.qq.com/q/TOwnCmypcy>
- Yunhu Group: <https://yhfx.jwznb.com/share?key=VWJL4fTWXepa&ts=1781889199>

Found the project useful? Consider supporting us for continued development on [Ifdian](https://ifdian.net/a/YingXinche)!

---
**English** | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | [Русский](README.ru.md)

## Star History

If ErisPulse helped you, feel free to give it a star ⭐—it’s the most direct way to help more developers discover the project.

[![Star History Chart](https://api.star-history.com/svg?repos=ErisPulse/ErisPulse&type=Date)](https://star-history.com/#ErisPulse/ErisPulse&Date)

---

### Contribution Guide

The health and growth of the ErisPulse project still need your help! We welcome contributions in all forms:

1. **Report Issues** — Submit bug reports on [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues)
2. **Feature Requests** — Share new ideas via [Community Discussions](https://github.com/ErisPulse/ErisPulse/discussions)
3. **Code Contributions** — Before submitting a PR, please read the [Code Style Guide](docs/en/styleguide/) and [Contribution Guide](CONTRIBUTING.md)
4. **Documentation Improvements** — Help improve documentation and example code

**First-time contributor?** Start here 👉 [First Contribution Guide](docs/en/contributing/first-contribution.md)

[Join the community discussion](https://github.com/ErisPulse/ErisPulse/discussions)

---

<div align="center">

### Acknowledgments

<img src=".github/assets/thanks.png" width="200" alt="Thanks" />

Some code in this project is based on [sdkFrame](https://github.com/runoneall/sdkFrame), and the core adapter standardization layer draws reference and benefits from the [OneBot12 specification](https://12.onebot.dev/).

The early exploration and growth of ErisPulse would not have been possible without the support of the Yunhu developer community, where many ideas, adapters, and practical experiences originated.

We also thank all developers and project authors who have contributed to ErisPulse, the OneBot ecosystem, and the open-source community.

</div>