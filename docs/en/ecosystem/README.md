# Ecosystem Modules

The ErisPulse framework itself only provides core capabilities (event system, module system, configuration, routing, logging, etc.) and **does not include built-in** GUI, image rendering, visualization, and other "heavyweight" features. These capabilities are provided by **third-party modules** maintained by the community, which can be installed on demand.

> [!IMPORTANT]
> All modules described in the documents in this directory **need to be installed separately** and are not included in the ErisPulse framework:
>
> ```bash
> epsdk install <module_name>
> ```
>

---

## Recommended Modules

| Module | Purpose | Docs |
|--------|---------|------|
| [ErisPulse-Dashboard](https://pypi.org/project/ErisPulse-Dashboard/) | Web management panel: module start/stop, configuration editing, log viewing, event monitoring; supports other modules registering custom views to the sidebar | [Dashboard Usage and View Registration](dashboard.md) |
| [ErisPulse-Takumi](https://github.com/ccd2s/ErispulseTakumi) (Author [@ccd2s](https://github.com/ccd2s)) | Image rendering: HTML / node tree / Jinja / SVG / animation, based on [takumi-py](https://github.com/BalconyJH/takumi-py); built-in Chinese and English fonts, ready to use out of the box | [Takumi Image Rendering](takumi.md) |

---

## I want to list my module here too?

You are welcome to recommend high-quality, widely reusable ErisPulse ecosystem modules. Requirements:

1. Published to [PyPI](https://pypi.org/) and package name starts with `ErisPulse-`
2. Provides basic README and usage examples
3. Actively maintained with responses to Issues

Module authors meeting the above conditions can add a `<module_name>.md` document under this directory via a PR and append a row to the "Recommended Modules" table.