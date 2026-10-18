# Ecosystem Modules

The ErisPulse framework itself only provides core capabilities (event system, module system, configuration, routing, logging, etc.), and does **not** include "heavyweight" features such as GUI, image rendering, or visualization. These capabilities are provided by **third-party modules** maintained by the community, which can be installed as needed.

> [!IMPORTANT]
> The documentation in this directory is divided into two categories, with different installation methods:
>
> - **Modules** (such as Dashboard / Takumi) are installed using `epsdk install`:
>
>   ```bash
>   epsdk install <module-name>
>   ```
>
> - **Standalone applications** (such as the ErisPulse-App client) are downloaded and installed directly from their corresponding GitHub Releases, without the need for `epsdk`.
>

---

## Recommended Modules and Official Clients

| Project | Type | Purpose | Documentation |
|---------|--------|---------|----------------|
| [ErisPulse-App](https://github.com/ErisPulse/ErisPulse-App) | Official Client | Official cross-platform client (Android / Windows / Linux / macOS): native interface to create / run / manage multiple instances, built-in module store and event builder; **runs directly on mobile**, desktop tray icon | [ErisPulse-App Installation and Usage](app.md) |
| [ErisPulse-Dashboard](https://pypi.org/project/ErisPulse-Dashboard/) | Module | Web management panel: module start/stop, configuration editing, log viewing, event monitoring; supports other modules registering custom sidebars | [Dashboard Usage and Sidebar Registration](dashboard.md) |
| [ErisPulse-Cron](https://github.com/wsu2059q/ErisPulse-Cron) | Module | Scheduled task management: one-time / interval / Cron expressions, callback parameters, SQLite persistence (tasks not lost on restart), supports Dashboard sidebar management | [Cron Scheduled Tasks](cron.md) |
| [ErisPulse-QvQChat](https://github.com/wsu2059q/ErisPulse-QvQChat) | Module | General-purpose agent: tool loops (message sending/receiving / code execution / computer operations / image generation / voice / MCP / sub-agents), built-in Dashboard, streaming conversation and serial tool replay | [QvQChat Agent](qvqchat.md) |
| [ErisPulse-Takumi](https://github.com/ccd2s/ErispulseTakumi) (Author [@ccd2s](https://github.com/ccd2s)) | Module | Image rendering: HTML / node tree / Jinja / SVG / animation, based on [takumi-py](https://github.com/BalconyJH/takumi-py); includes Chinese and English fonts, ready-to-use | [Takumi Image Rendering](takumi.md) |

---

## Do I want to list my module here too?

We welcome recommendations of high-quality, widely reusable ErisPulse ecosystem modules. Requirements:

1. Published to [PyPI](https://pypi.org/) with a package name starting with `ErisPulse-`
2. Provides a basic README and usage examples
3. Actively maintained, with responses to Issues

Module authors who meet the above conditions can add a new `<module-name>.md` document in this directory via PR and add a line in the "Recommended Modules" section of this table.