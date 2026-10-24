# Ecosystem Modules

The ErisPulse framework itself only provides core capabilities (event system, module system, configuration, routing, logging, etc.), and **does not include** "heavyweight" features such as GUI, image rendering, and visualization. These capabilities are provided by community-maintained **third-party modules**, which can be installed on demand.

> [!IMPORTANT]
> The documentation in this directory is divided into two categories, each with a different installation method:
>
> - **Modules** (such as Dashboard / Takumi) are installed using `epsdk install`:
>
>   ```bash
>   epsdk install <module-name>
>   ```
>
> - **Standalone programs** (such as the ErisPulse-App client) can be downloaded and installed directly from the corresponding GitHub Releases, without the need for `epsdk`.

---

## Recommended Modules

### ErisPulse-Dashboard: An Admin Panel in Your Browser

Your bot runs on a server, and you still need to log into a terminal to start/stop modules, tweak configurations, or check logs? Dashboard brings all of this into the browser: module start/stop, configuration editing, log viewing, and event monitoring; other modules can also register custom windows in the sidebar, keeping all management pages in one place.

```bash
epsdk install Dashboard
```

Docs: [Dashboard Usage and Window Registration](dashboard.md) | Project homepage: [PyPI](https://pypi.org/project/ErisPulse-Dashboard/)

### ErisPulse-Cron: Scheduled Tasks

Need to send daily check-in reminders on schedule, run periodic tasks with Cron expressions, or poll data every few minutes? Cron offers three task types—one-time / interval / Cron expression—with callback parameters and SQLite persistence (tasks survive restarts).

```bash
epsdk install Cron
```

Docs: [Cron Scheduled Tasks](cron.md) | Project homepage: [GitHub](https://github.com/wsu2059q/ErisPulse-Cron)

### ErisPulse-QvQChat: General-Purpose Agent

Want an AI assistant in your group that actually gets things done, instead of one that only replies with keyword matching? QvQChat is a general-purpose agent: its tool loop covers message sending/receiving / code execution / computer operations / image generation / voice / MCP / sub-agents, supports streaming conversations and serialized tool replay, and comes with a built-in Dashboard window.

```bash
epsdk install ErisPulse-QvQChat
```

Docs: [QvQChat Agent](qvqchat.md) | Project homepage: [GitHub](https://github.com/wsu2059q/ErisPulse-QvQChat)

### ErisPulse-Takumi: Image Rendering

For scenarios that require "sending images"—like leaderboards, battle reports, or schedule cards—just write a template, render it into an image, and send it to your group: it supports HTML / node trees / Jinja / SVG / animation (based on [takumi-py](https://github.com/BalconyJH/takumi-py)), comes with built-in Chinese and English fonts, and works right out of the box.

```bash
epsdk install Takumi
```

Docs: [Takumi Image Rendering](takumi.md) | Project homepage: [GitHub](https://github.com/ccd2s/ErispulseTakumi) (Author: [@ccd2s](https://github.com/ccd2s))

## Official Client (Standalone Application)

### ErisPulse-App: Run Bots Directly on Your Phone

No always-on server, but still want to create instances, install modules, and view event streams anytime? ErisPulse-App is the official cross-platform client (Android / Windows / Linux / macOS): a native interface for creating / running / managing multiple bot instances, with a built-in module marketplace and event builder. **Runs directly on your phone**, and stays resident in the desktop tray on desktop.

Installation packages for all platforms can be downloaded from [GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases); no need for `epsdk`.

Documentation: [ErisPulse-App Installation and Usage](app.md)

---

## Want to list your own module here?

We welcome recommendations of high-quality, widely reusable ErisPulse ecosystem modules. Requirements:

1. Published on [PyPI](https://pypi.org/), with a package name starting with `ErisPulse-`
2. Provides a basic README and usage examples
3. Actively maintained, with responses to Issues

Module authors who meet the above criteria can add a `<Module-Name>.md` document in this directory via a PR, and add the corresponding section to the recommendation list above.