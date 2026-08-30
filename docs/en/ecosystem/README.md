# Ecosystem Modules

The ErisPulse framework itself only provides core capabilities (event system, module system, configuration, routing, logging, etc.) and **does not include** "heavyweight" features such as GUI, image rendering, and visualization. These capabilities are provided by **community-maintained third-party modules**, which can be installed on demand.

> [!IMPORTANT]
> Documentation in this directory is divided into two categories with different installation methods:
>
> - **Modules** (e.g., Dashboard / Takumi) use `epsdk install` to install:
>
>   ```bash
>   epsdk install <module_name>
>   ```
>
> - **Standalone Programs** (e.g., ErisPulse-App client) are installed directly by downloading from the corresponding GitHub Releases, without needing `epsdk`.
>

## Recommended Modules and Official Clients

| Item | Type | Purpose | Documentation |
|------|------|--------|---------------|
| [ErisPulse-App](https://github.com/ErisPulse/ErisPulse-App) | Official Client | Official cross-platform client (Android / Windows / Linux / macOS): create/run/manage multiple instances natively with native UI, built-in module store and event builder; **run directly on mobile**, resident desktop tray | [ErisPulse-App Installation and Usage](app.md) |
| [ErisPulse-Dashboard](https://pypi.org/project/ErisPulse-Dashboard/) | Module | Web admin panel: start/stop modules, edit configurations, view logs, monitor events; supports custom windows registration in the sidebar for other modules | [Dashboard Usage and Window Registration](dashboard.md) |
| [ErisPulse-Takumi](https://github.com/ccd2s/ErispulseTakumi) (Author [@ccd2s](https://github.com/ccd2s)) | Module | Image rendering: HTML / Node Tree / Jinja / SVG / Animation, based on [takumi-py](https://github.com/BalconyJH/takumi-py); built-in Chinese and English fonts, ready to use | [Takumi Image Rendering](takumi.md) |

---

## I also want to list my module here?

Welcome to recommend high-quality, widely reusable ErisPulse ecosystem modules. Requirements:

1. Published to [PyPI](https://pypi.org/), and the package name starts with `ErisPulse-`
2. Provide basic README and usage examples
3. Actively maintained, responsive to Issues

Module authors who meet the above conditions can create a new `<ModuleName>.md` document in this directory via PR and append a row to the "Recommended Modules" table.

