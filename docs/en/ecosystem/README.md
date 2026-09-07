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
|---------|------|---------|---------------|
| [ErisPulse-App](https://github.com/ErisPulse/ErisPulse-App) | Official Client | Official cross-platform client (Android / Windows / Linux / macOS): native interface to create / run / manage multiple instances, built-in module store and event builder; **runs directly on mobile**, desktop tray icon | [ErisPulse-App Installation and Usage](app.md) |
| [ErisPulse-Dashboard](https://pypi.org/project/ErisPulse-Dashboard/) | Module | Web management panel: module start/stop, configuration editing, log viewing, event monitoring; supports other modules to register custom windows to the sidebar | [Dashboard Usage and Window Registration](dashboard.md) |
| [ErisPulse-Takumi](https://github.com/ccd2s/ErispulseTakumi) (Author [@ccd2s](https://github.com/ccd2s)) | Module | Image rendering: HTML / node tree / Jinja / SVG / animation, based on [takumi-py](https://github.com/BalconyJH/takumi-py); includes Chinese and English fonts, ready to use out of the box | [Takumi Image Rendering](takumi.md) |

---

## Do I want to list my module here too?

We welcome recommendations of high-quality, widely reusable ErisPulse ecosystem modules. Requirements:

1. Published to [PyPI](https://pypi.org/) with a package name starting with `ErisPulse-`
2. Provides a basic README and usage examples
3. Actively maintained, with responses to Issues

Module authors who meet the above conditions can add a new `<module-name>.md` document in this directory via PR and add a line in the "Recommended Modules" section of this table.