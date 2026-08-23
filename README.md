<img src=".github/assets/mascot-hero.png" align="right" width="300" alt="ErisPulse" style="margin-left: 24px; margin-bottom: 16px; border-radius: 12px;" />

**English** | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | [Русский](README.ru.md)

Please directly return the complete translated Markdown content, without any additional text.

Once again, if the document contains a language switch line (with each language name separated by `` | ``), strictly follow the format requirement in point 8 above, and do not write incorrect formats such as ``[**Label**](file)``.

# ErisPulse

**Write once, deploy to QQ / Telegram / Kook / Yunhu / WeChat Official Account / OneBot12 / ... multiple platforms.**

An event-driven multi-platform chatbot development framework.

Based on the OneBot12 standard interface, write once and deploy to multiple platforms; a flexible plugin system, hot reload support, and a complete developer toolchain, suitable for scenarios ranging from simple chatbots to complex automation systems.

<p>
  <a href="https://pypi.org/project/ErisPulse/"><img src="https://img.shields.io/pypi/v/ErisPulse?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI"></a>
  <a href="https://pypi.org/project/ErisPulse/"><img src="https://img.shields.io/badge/Python-3.10+-FFD43B?style=for-the-badge&logo=python&logoColor=blue" alt="Python"></a>
  <a href="https://hub.docker.com/r/erispulse/erispulse"><img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"></a>
  <a href="https://github.com/ErisPulse/ErisPulse/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License"></a>
  <a href="https://github.com/ErisPulse/ErisPulse"><img src="https://img.shields.io/github/stars/ErisPulse/ErisPulse?style=for-the-badge&logo=github&color=brightgreen" alt="Stars"></a>
  <a href="https://pepy.tech/project/ErisPulse"><img src="https://img.shields.io/pepy/dt/ErisPulse?style=for-the-badge&color=blue" alt="Downloads"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&style=for-the-badge" alt="Ruff"></a>
  <a href="https://socket.dev/pypi/package/erispulse"><img src="https://img.shields.io/badge/Socket-Secure-2ea043?style=for-the-badge&logo=socket&logoColor=white" alt="Socket"></a>
  <a href="https://www.erisdev.com"><img src="https://img.shields.io/badge/Documentation-erisdev.com-FF6B9D?style=for-the-badge&logo=bookstack&logoColor=white" alt="Documentation"></a>
  <a href="https://deepwiki.com/ErisPulse/ErisPulse"><img src="https://img.shields.io/badge/DeepWiki-ErisPulse-8A2BE2?style=for-the-badge&logo=readthedocs&logoColor=white" alt="DeepWiki"></a>
  <a href="https://www.erisdev.com/#market"><img src="https://img.shields.io/badge/Module%20Market-erisdev.com-C724B1?style=for-the-badge&logo=webpack&logoColor=white" alt="Module%20Market"></a>
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

<img src=".github/assets/icon/icon_event_driven.png.png" width="50" alt="Event-driven Architecture" />

### Event-driven Architecture

A unified event model based on the OneBot12 standard—no more writing a set of if/elif statements for each platform to check message types, a single handler automatically adapts to all adapters

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_cross_platform.png.png" width="50" alt="Cross-platform Compatibility" />

### Cross-platform Compatibility

The same business code runs on all platforms—write once and serve over 15 platforms including QQ / Telegram / Kook / Yunhu / WeChat Official Account, no need for repeated development

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_modular.png" width="50" alt="Modular Design" />

### Modular Design

A flexible plugin system supports runtime hot-plug—install/uninstall/enable/disable modules without restarting the process, assembling robot capabilities like building blocks

</td>
</tr>
<tr>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_hot_reload.png" width="50" alt="Hot Reload" />

### Hot Reload

Development cycles are shortened from 10 seconds to 0.5 seconds—saving a file takes effect immediately, development and debugging experience is close to that of an interpreted scripting language

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_ai_assist.png" width="50" alt="AI Assistance" />

### AI Assistance

Natural language descriptions of requirements directly generate usable modules—don't know how to write an adapter? Tell the AI which platform you want to integrate, and it will help you write it

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_lightweight.png" width="50" alt="Lightweight" />

### Lightweight

Intuitive chainable API design—complex logic such as @user, reply, retry, batch sending is completed in a single line of code, code is as light and readable as a feather

</td>
</tr>
</table>

---

Please directly return the complete translated Markdown content, without including any other text.

Once again, please note: if the document contains a language switch line (with language names separated by `` | ``), strictly follow the format requirements in item 8 above, and do not write incorrect formats such as ``[**Label**](file)``.

## How It Works

ErisPulse hides platform differences through an adapter layer, allowing business code to focus solely on events:

```mermaid
graph LR
    subgraph Platforms[Platforms]
        QQ["QQ"]
        TG["Telegram"]
        Kook["Kook"]
        YH["Yunhu"]
        WX["WeChat Official Account"]
    end

    subgraph Adapters[Adapter Layer]
        A1["QQ Adapter"]
        A2["Telegram Adapter"]
        A3["Kook Adapter"]
        A4["Yunhu Adapter"]
        A5["WeChat Adapter"]
    end

    Event["Event Bus<br/>Middleware → Dispatch command/message/notice/request/meta"]

    subgraph Modules[Business Modules]
        M1["Command Processor<br/>@command"]
        M2["Message Processor<br/>@message"]
        M3["Your Module"]
    end

    QQ --> A1
    TG --> A2
    Kook --> A3
    YH --> A4
    WX --> A5

    A1 -->|"OB12 Event"| Event
    A2 -->|"OB12 Event"| Event
    A3 -->|"OB12 Event"| Event
    A4 -->|"OB12 Event"| Event
    A5 -->|"OB12 Event"| Event

    Event -->|"Dispatch"| M1
    Event -->|"Dispatch"| M2
    Event -->|"Dispatch"| M3

    M1 -.->|"event.reply()<br/>SendDSL"| Event
    Event -.->|"Send"| A1
```

- The **Adapter Layer** converts native protocols from each platform into OneBot12 standard events, so business modules don't see platform differences.
- The **Event Bus** first executes the middleware chain, then dispatches events to five types of processors based on event type.
- Your code subscribes to events using decorators and replies using `event.reply()` or SendDSL — reply messages flow back along the same path to the platform.

For detailed design information on the complete module composition, initialization process, and lifecycle events, see [Architecture Overview](docs/en/architecture.md).

## Quick Start

### One-Click Installation Script (Recommended)

The installation script will automatically detect your environment (Docker, Python, uv), guide you to choose the most suitable installation method, and support multiple languages (Chinese / English / 日本語 / Русский / 繁體中文).

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
<summary>Unable to access Docker Hub?</summary>

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

After starting, access `http://<host>:8000/Dashboard` and log in to the Dashboard management panel using the set token.

> The image includes the ErisPulse framework and Dashboard management panel, supporting `linux/amd64` and `linux/arm64` architectures.
>
> **Persistence**: Configuration files and installed modules/adapters are persisted to the host machine via volume mounting, so they won't be lost after container restart. Framework updates are completed through hot updates in the Dashboard.

</details>

<details>
<summary>Docker Environment Variables</summary>

| Variable | Default Value | Description |
|----------|---------------|-------------|
| `ERISPULSE_DASHBOARD_TOKEN` | empty | Dashboard login token (automatically written to configuration after setting) |
| `ERISPULSE_PORT` | `8000` | Dashboard port mapping |
| `ERISPULSE_TAG` | `latest` | Image tag, can be set to `dev` to use pre-release images |
| `ERISPULSE_BUILD_TARGET` | `production` | Build target: `production` (stable version) or `dev` (pre-release version) |
| `CONTAINER_NAME` | `erispulse` | Container name |
| `TZ` | `Asia/Shanghai` | Container timezone |
| `LANG` | `en_US.UTF-8` | System language, automatically detects the startup interface language |
| `ERISPULSE_LANG` | empty | Force startup interface language: `zh` / `zh_TW` / `en` / `ja` / `ru` (overrides `LANG`) |

</details>

### 1Panel App Store

Install ErisPulse with one click via the [1Panel](https://1panel.cn) app store. See [ErisPulse-1Panel](https://github.com/ErisPulse/ErisPulse-1Panel).

```bash
bash <(curl -sL https://get-1panel.erisdev.com/install.sh)
```

ErisPulse has been listed in the 1Panel third-party app store and can be installed using the [okxlin/appstore](https://github.com/okxlin/appstore) third-party repository.

### Using pip to Install

```bash
pip install ErisPulse
```

> You can also use the one-click installation script above to automatically detect the environment and guide configuration.

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

## The Same Code. Multiple Platforms.

*Identical command handlers. Different platforms. No changes to business logic required.*

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

docs/en/quick-start.md

## Chained Send DSL

A single chained call completes all sending logic such as @, reply, retry, timeout, and callback:

```python
yunhu = sdk.adapter.get("yunhu")

# Single send: @user + reply + retry + success callback
await (yunhu.Send.To("group", "123")
       .At("456").Reply("msg_789")
       .Retry(3).Timeout(10)
       .Hook(lambda r: print("Send successful!"))
       .Text("Hello"))

# Bulk send: send multiple messages in one chain
results = await (yunhu.Send.To("user", "123")
                .Build()
                .Text("Notification 1")
                .Image("pic.jpg")
                .Retry(2)
                .send_all())
```

> Supports chained methods such as Hook (success callback), Retry (failure retry), Timeout (timeout cancellation), OnProgress (progress monitoring), Defer (delayed sending), and Build (bulk construction), see [SendDSL documentation](docs/en/quick-start.md).

---

Please directly return the complete translated Markdown content without including any other text.

## Multi-turn Dialogue Examples

ErisPulse comes with a powerful multi-turn dialogue engine, making it easy to implement guided operations, information collection, and other interactive scenarios:

```python
from ErisPulse.Core.Event import command, request

@command("register")
async def register_handler(event):
    conv = event.conversation(timeout=60)
    
    await conv.say("Welcome to register!")
    
    # Multi-step user information collection with automatic validation
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
        await event.reply(f"Friend request automatically approved, welcome {user_name}")
```

<details>
<summary>See more Conversation API (branching / selection / persistence)</summary>

```python
@command("quiz")
async def quiz_handler(event):
    conv = event.conversation(timeout=30)
    
    # Multiple choice question
    answer = await conv.choose("Who is the creator of Python?", [
        "Guido van Rossum",
        "James Gosling", 
        "Dennis Ritchie",
    ])
    
    if answer == 0:
        await conv.say("Correct!")
    elif answer is None:
        await conv.say("Time's up, try again next time!")
    else:
        await conv.say("Incorrect, the correct answer is Guido van Rossum")

@command("menu")
async def menu_handler(event):
    conv = event.conversation(timeout=60)
    
    # Branching, build complex interaction flows
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

See more at [Conversation Multi-turn Dialogue](docs/en/advanced/conversation.md)

</details>

## Core Modules

ErisPulse provides a complete multi-platform bot development toolchain, with each core module fulfilling its own responsibilities:

```mermaid
graph TB
    SDK["sdk<br/>Unified Entry"]

    SDK --> Event["Event<br/>Event System"]
    SDK --> AdapterMgr["Adapter<br/>Adapter Management"]
    SDK --> ModuleMgr["Module<br/>Module Management"]
    SDK --> Router["Router<br/>HTTP/WS Routing"]
    SDK --> Storage["Storage<br/>SQLite Storage"]
    SDK --> Config["Config<br/>Configuration Management"]
    SDK --> Lifecycle["Lifecycle<br/>Lifecycle"]
    SDK --> Logger["Logger<br/>Logging System"]
    SDK --> Client["HttpClient<br/>HTTP Client"]
```

| Module | Description |
|--------|-------------|
| **Event** | Event system, providing five types of events: command / message / notice / request / meta + Conversation for multi-turn dialogue |
| **Adapter** | Adapter management, BaseAdapter base class for unified event conversion and SendDSL sending, supports over 15 platforms including QQ / Telegram / Kook / Yunhu / WeChat Official Account |
| **Module** | Module management, BaseModule base class + dependency declaration and topological sorting for loading |
| **SendDSL** | Chainable sending, complex logic such as @/reply/retry/timeout/batch can be completed in one line |
| **Router** | HTTP/WebSocket routing system (FastAPI + Uvicorn) |
| **Storage** | Key-value storage based on SQLite + generic SQL chainable query |
| **Config** | TOML configuration management |
| **Lifecycle** | Lifecycle event hooks (core.init / adapter.* / module.*) |
| **Logger** | Modular logging system, supports sub-loggers |
| **HttpClient** | Unified HTTP/WS client (based on aiohttp), built-in retry and ErisPulse exception system |

For more detailed design (initialization flow, lifecycle events, module loading strategy), see [Architecture Overview](docs/en/architecture.md).

## Ecosystem

ErisPulse is more than just a framework. Get started right away without having to build wheels from scratch.

<table>
<tr>
<td align="center" width="25%">

**Framework**

Core Runtime

Unified Event & Message Model

</td>
<td align="center" width="25%">

**Dashboard**

Visual Management

Plugins · Logs · Configuration

[Live Demo →](https://dashdemo.erisdev.com/)

</td>
<td align="center" width="25%">

**AI Builder**

Natural Language → Usable Modules

[Experience Now →](https://builder.erisdev.com)

</td>
<td align="center" width="25%">

**Module Market**

Ready-to-use Plugins

[Explore Modules →](https://www.erisdev.com/#market)

</td>
</tr>
<tr>
<td align="center" width="25%">

**Adapters**

Access to 15+ Platforms

</td>
<td align="center" width="25%">

**ErisPulse-App**

Official Multi-platform Client

Run directly on mobile · Desktop tray icon

[Download & Install →](https://github.com/ErisPulse/ErisPulse-App/releases)

</td>
<td align="center" width="25%">

**Docker**

Multi-architecture Support

`erispulse/erispulse`

</td>
<td align="center" width="25%">

**Documentation & CLI**

[erisdev.com](https://www.erisdev.com)

`epsdk` Scaffolding Tool

</td>
</tr>
</table>

---

Please directly return the fully translated Markdown content, without any additional text.

## Supported Platforms

Welcome to contribute adapters! Don't know where to start? See [Contributing Guide](docs/en/contributing/README.md).

| Adapter | Description |
|--------|------|
| <img src=".github/assets/adapter_logo/kook.svg" height="20" alt="Kook" /> [Kook](https://github.com/shanfishapp/ErisPulse-KookAdapter) | Kook (Kaihei La) instant messaging platform |
| <img src=".github/assets/adapter_logo/matrix.svg" height="20" alt="Matrix" /> [Matrix](https://github.com/ErisPulse/ErisPulse-MatrixAdapter) | Matrix decentralized communication protocol |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot11](https://github.com/ErisPulse/ErisPulse-OneBot11Adapter) | OneBot v11 universal robot protocol |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot12](https://github.com/ErisPulse/ErisPulse-OneBot12Adapter) | OneBot v12 standard protocol |
| <img src=".github/assets/adapter_logo/qqbot.svg" height="20" alt="QQ" /> [QQ](https://github.com/ErisPulse/ErisPulse-QQBotAdapter) | Official QQ robot platform |
| <img src=".github/assets/adapter_logo/sandbox.png" height="20" alt="Sandbox" /> [Sandbox](https://github.com/ErisPulse/ErisPulse-SandboxAdapter) | Web-based debugging, no real platform integration required |
| <img src=".github/assets/adapter_logo/terminal.svg" height="20" alt="Terminal" /> [Terminal](https://github.com/ErisPulse/ErisPulse-TerminalAdapter) | Command line as chat, zero-configuration development and debugging |
| <img src=".github/assets/adapter_logo/telegram.svg" height="20" alt="Telegram" /> [Telegram](https://github.com/ErisPulse/ErisPulse-TelegramAdapter) | Global instant messaging platform |
| <img src=".github/assets/adapter_logo/email.svg" height="20" alt="Email" /> [Email](https://github.com/ErisPulse/ErisPulse-EmailAdapter) | Email protocol adapter for sending and receiving |
| <img src=".github/assets/adapter_logo/yunhu.png" height="20" alt="Yunhu" /> [Yunhu](https://github.com/ErisPulse/ErisPulse-YunhuAdapter) | Enterprise-grade instant messaging platform (robot integration) |
| <img src=".github/assets/adapter_logo/yunhu.png" height="20" alt="Yunhu" /> [Yunhu User](https://github.com/wsu2059q/ErisPulse-YunhuUserAdapter) | Adapter based on the Yunhu user protocol |
| [HuaFeng Cafe](https://github.com/ErisPulse/ErisPulse-Ideaura/) | Allons! \(・ω・) / |
| <img src=".github/assets/adapter_logo/discord.svg" height="20" alt="Discord" /> [Discord](https://github.com/ErisPulse/ErisPulse-DiscordAdapter) | Global community communication platform, supports servers, channels, and private messages |
| <img src=".github/assets/adapter_logo/webhook.svg" height="20" alt="Webhook" /> [Webhook](https://github.com/ErisPulse/ErisPulse-WebhookAdapter) | Universal HTTP bridge adapter, connects to any system |
| <img src=".github/assets/adapter_logo/wechatmp.svg" height="20" alt="WechatMp" /> [WeChat Official Account](https://github.com/ErisPulse/ErisPulse-WechatMpAdapter) | Official WeChat official account platform |

View [Adapter Details](docs/en/platform-guide/README.md)

## Community

Connect with us:

- Telegram: <https://t.me/ErisPulse>
- QQ Group: <https://qm.qq.com/q/TOwnCmypcy>
- Yunhu Group: <https://yhfx.jwznb.com/share?key=VWJL4fTWXepa&ts=1781889199>

---

### Contribution Guide

The health of the ErisPulse project still needs your contribution! We welcome all forms of contributions:

1. **Report Issues** — Submit bug reports in [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues)
2. **Feature Requests** — Propose new ideas via [Community Discussions](https://github.com/ErisPulse/ErisPulse/discussions)
3. **Code Contributions** — Please read the [Code Style](docs/en/styleguide/) and [Contribution Guide](CONTRIBUTING.md) before submitting PRs
4. **Documentation Improvements** — Help improve documentation and example code

**First-time contributor?** Start here 👉 [First Contribution Guide](docs/en/contributing/first-contribution.md)

[Join the community discussion](https://github.com/ErisPulse/ErisPulse/discussions)

---

<div align="center">

### Acknowledgments

<img src=".github/assets/thanks.png" width="200" alt="Thanks" />

Some code in this project is based on [sdkFrame](https://github.com/runoneall/sdkFrame).

The core adapter standardization layer references and benefits from the [OneBot12 specification](https://12.onebot.dev/).

Special thanks to the Yunhu ecosystem and community.

The early exploration and growth of ErisPulse would not have been possible without the support of the Yunhu developer community. Many ideas, adapters, and practical experiences originated here.

We also thank all developers and project authors who have contributed to ErisPulse, the OneBot ecosystem, and the open-source community.

</div>