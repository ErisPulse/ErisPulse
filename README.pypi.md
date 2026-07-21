![ErisPulse](https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/.github/assets/mascot-hero.png)

# ErisPulse

**Write once, deploy on multiple platforms.**

An event-driven, multi-platform chatbot development framework based on the OneBot12 standard.

[![PyPI](https://img.shields.io/pypi/v/ErisPulse?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/ErisPulse/)
[![Python](https://img.shields.io/badge/Python-3.10+-FFD43B?style=for-the-badge&logo=python&logoColor=blue)](https://pypi.org/project/ErisPulse/)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](https://github.com/ErisPulse/ErisPulse/blob/main/LICENSE)
[![Docs](https://img.shields.io/badge/docs-erisdev.com-FF6B9D?style=for-the-badge&logo=bookstack&logoColor=white)](https://www.erisdev.com)
[![Stars](https://img.shields.io/github/stars/ErisPulse/ErisPulse?style=for-the-badge&logo=github&color=brightgreen)](https://github.com/ErisPulse/ErisPulse)
[![Downloads](https://img.shields.io/pepy/dt/ErisPulse?style=for-the-badge&color=blue)](https://pepy.tech/project/ErisPulse)
[![Discussions](https://img.shields.io/badge/GitHub-Discussions-181717?style=for-the-badge&logo=github)](https://github.com/ErisPulse/ErisPulse/discussions)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://hub.docker.com/r/erispulse/erispulse)

---

## Overview

ErisPulse is an event-driven, modular async framework for building chatbots that run on **multiple platforms from a single codebase**. It implements the [OneBot12](https://12.onebot.dev/) standard event model, so you write command handlers, conversation flows and message senders once — then deploy them to QQ, Telegram, Discord, Kook, Yunhu, Matrix, Email, WeChat and more without touching business logic.

It ships with a flexible plugin system, hot reload, a visual Dashboard, an AI Builder that turns natural-language prompts into modules, and the `epsdk` CLI scaffolding tool — suitable for everything from a simple chatbot to a complex automation pipeline.

## Key Features

- **Event-driven architecture** — Clear event model based on OneBot12, making message handling intuitive and consistent across platforms.
- **Cross-platform compatibility** — Write handlers once, deploy to 15+ platforms without rewriting business logic.
- **Modular design** — Flexible plugin system with hot-plug module management and per-module configuration.
- **Hot reload** — Iterate on code during development without restarting the bot process.
- **Chainable SendDSL** — Express `@mention`, reply, retry, timeout, progress hook and bulk send as a single fluent chain.
- **Complete toolchain** — `epsdk` CLI, visual Dashboard, AI Builder and Module Market included out of the box.

## Installation

### Option 1 — pip (for library / module developers)

```bash
pip install ErisPulse
```

### Option 2 — Docker (recommended for production)

```bash
docker pull erispulse/erispulse:latest
```

Quick start with `docker-compose.yml`:

```bash
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

The image bundles the ErisPulse framework **and** the Dashboard management panel, supporting `linux/amd64` and `linux/arm64`. After startup, visit `http://<host>:<port>/Dashboard` and log in with the token you set.

<details>
<summary>Docker Hub unavailable? Use GitHub Container Registry</summary>

```bash
docker pull ghcr.io/erispulse/erispulse:latest
```

And update the image in your `docker-compose.yml`:

```yaml
image: ghcr.io/erispulse/erispulse:latest
```

</details>

<details>
<summary>Docker environment variables</summary>

| Variable | Default | Description |
|------|--------|------|
| `ERISPULSE_CHANNEL` | `stable` | Version channel: `stable` or `dev` (pre-release) |
| `ERISPULSE_UPDATE_ON_START` | `false` | Auto-update to the latest version on container start |
| `ERISPULSE_DASHBOARD_TOKEN` | empty | Dashboard login token |
| `ERISPULSE_PORT` | `8000` | Dashboard port mapping |
| `TZ` | `Asia/Shanghai` | Container timezone |

</details>

### Option 3 — One-click install script (auto-detects environment)

The installer detects Docker / Python / uv and guides you through the most suitable setup. Supports Chinese, English, Japanese, Russian and Traditional Chinese.

Windows (PowerShell):

```powershell
irm https://get.erisdev.com/install.ps1 -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1
```

macOS / Linux:

```bash
curl -fsSL https://get.erisdev.com/install.sh -o install.sh && chmod +x install.sh && ./install.sh
```

## Quick Start

Initialize a new project:

```bash
# Interactive initialization
epsdk init

# Quick initialization with a project name
epsdk init -q -n my_bot
```

Create a `main.py` file:

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

Run it:

```bash
epsdk run main.py
# Or in development mode with hot reload
epsdk run main.py --reload
```

Now send `/hello` or `/ping` to the bot on any connected platform — the same handlers work everywhere.

For the full walkthrough (multi-turn conversations, request handlers, adapter configuration), see the [Quick Start guide](https://www.erisdev.com#docs).

## The SendDSL — fluent message sending

Compose the entire send flow — `@mention`, reply, retry, timeout, progress hook and bulk dispatch — as one readable chain:

```python
yunhu = sdk.adapter.get("yunhu")

# Single send: @user + reply + retry + timeout + success callback
await (yunhu.Send.To("group", "123")
       .At("456").Reply("msg_789")
       .Retry(3).Timeout(10)
       .Hook(lambda r: print("Send successful!"))
       .Text("Hello"))

# Bulk send: build multiple messages, then dispatch in one chain
results = await (yunhu.Send.To("user", "123")
                .Build()
                .Text("Notification 1")
                .Image("pic.jpg")
                .Retry(2)
                .send_all())
```

Supported chainable methods include `Hook` (success callback), `Retry` (failure retry), `Timeout` (timeout cancellation), `OnProgress` (progress monitoring), `Defer` (delayed send) and `Build` (batch construction).

> Full reference: [SendDSL documentation](https://www.erisdev.com#docs)

## Supported Platforms

Officially maintained adapters (community contributions welcome):

- [Kook](https://github.com/shanfishapp/ErisPulse-KookAdapter) — instant messaging platform
- [Matrix](https://github.com/ErisPulse/ErisPulse-MatrixAdapter) — decentralized communication protocol
- [OneBot11](https://github.com/ErisPulse/ErisPulse-OneBot11Adapter) — universal OneBot v11 protocol
- [OneBot12](https://github.com/ErisPulse/ErisPulse-OneBot12Adapter) — OneBot v12 standard protocol
- [QQ Bot](https://github.com/ErisPulse/ErisPulse-QQBotAdapter) — official QQ bot platform
- [Telegram](https://github.com/ErisPulse/ErisPulse-TelegramAdapter) — global instant messaging
- [Discord](https://github.com/ErisPulse/ErisPulse-DiscordAdapter) — community communication platform
- [Yunhu](https://github.com/ErisPulse/ErisPulse-YunhuAdapter) / [Yunhu User](https://github.com/wsu2059q/ErisPulse-YunhuUserAdapter) — enterprise IM
- [Email](https://github.com/ErisPulse/ErisPulse-EmailAdapter) — email protocol adapter
- [WeChat Official Account](https://github.com/ErisPulse/ErisPulse-WechatMpAdapter)
- [Webhook](https://github.com/ErisPulse/ErisPulse-WebhookAdapter) — HTTP bridge to any system
- [Sandbox](https://github.com/ErisPulse/ErisPulse-SandboxAdapter) — in-browser debugging, no real platform needed
- [HuaFeng Coffee House](https://github.com/ErisPulse/ErisPulse-Ideaura/)

See the [adapter guide](https://www.erisdev.com#docs) for configuration details.

## Ecosystem

- **Framework** — core runtime with a unified event & message model.
- **Dashboard** — visual management for plugins, logs and configuration. ([live demo](https://dashdemo.erisdev.com/))
- **AI Builder** — natural-language prompts → ready-to-use modules. ([try it](https://www.erisdev.com/#builder))
- **Module Market** — plug-and-play community plugins. ([browse](https://www.erisdev.com/#market))
- **CLI** — `epsdk` scaffolding, project init, run and reload.
- **Docker** — multi-architecture images at `erispulse/erispulse`.

## Documentation & Community

- 📖 **Documentation & API reference:** [erisdev.com](https://www.erisdev.com)
- 💬 **GitHub Discussions:** [ErisPulse/ErisPulse/discussions](https://github.com/ErisPulse/ErisPulse/discussions)
- 📋 **Changelog:** [CHANGELOG.md](https://github.com/ErisPulse/ErisPulse/blob/main/CHANGELOG.md)
- 🤝 **Contributing:** [CONTRIBUTING.md](https://github.com/ErisPulse/ErisPulse/blob/main/CONTRIBUTING.md)
- 🐛 **Bug reports:** [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues)
- 🧠 **DeepWiki:** [deepwiki.com/ErisPulse/ErisPulse](https://deepwiki.com/ErisPulse/ErisPulse)

Chat with us on:

- Telegram: <https://t.me/ErisPulse>
- QQ Group: <https://qm.qq.com/q/TOwnCmypcy>
- Yunhu Group: <https://yhfx.jwznb.com/share?key=VWJL4fTWXepa&ts=1781889199>

---

**Why ErisPulse?** Because platform differences should never be your bottleneck — focus on business logic, and let the framework handle the rest. Write once, deploy everywhere.
