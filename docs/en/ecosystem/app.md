# ErisPulse-App

[ErisPulse-App](https://github.com/ErisPulse/ErisPulse-App) is an **official cross-platform client** maintained directly by ErisDev (releases available for Android / Windows / Linux / macOS),
providing a fully native graphical management interface: create, run, and manage multiple bot instances on your phone or computer,
without the need for a terminal, or a separate Python environment.

> [!IMPORTANT]
> ErisPulse-App is a **standalone installed client application**, not a module installed via `epsdk install`.
> It comes with a built-in Python runtime and ErisPulse SDK, ready to use out of the box—**you can run it directly on your phone**.

## Feature Overview

- **Multi-instance Management**: Create / Start / Stop / Delete multiple instances, automatic port and access token allocation, support for new environments or cloning existing environments
- **Overview Dashboard**: Adapter / Module / Online Bots / Total Events statistics, CPU / Memory usage alerts with color changes
- **Module Store**: Search and tag filtering, one-click Install / Upgrade / Uninstall, specify version installation, pip mirror source and Git package support
- **Event Stream + Event Builder**: Real-time event viewing, visual construction and submission of test events to adapters
- **Monitoring**: Log / Lifecycle / Audit unified view
- **Command Management**: Global settings such as Prefix and Aliases, start/stop and platform allow/deny lists
- **Bot Overview / Config / File Management**: Native interface for direct instance operations
- **Background Persistence**: Android foreground service keep-alive; Windows minimized to system tray, closing the window does not interrupt the instance
- **Dynamic Module Windows**: Registered module pages automatically appear in the sidebar navigation (grouped with Dashboard), click to jump directly



## Supported Platforms

All platform installers can be downloaded from [GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases). Simply select the appropriate package as needed:

| Platform | Package | Description |
|----------|--------|-------------|
| Android | `online-*.apk` / `offline-*.apk` | **Run directly on phone**, no computer required |
| Windows | `windows-x64-setup.exe` / `windows-x64.zip` | Installer / Portable version |
| Linux | `linux-x64.tar.gz` | Extract and run |
| macOS | `macos-arm64.zip` | Apple Silicon (arm64) |

A single Flutter codebase covers all platforms.

---

## Installation (Android / Mobile Direct Run)

Download and install the APK from [GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases). There are two builds available:

| Build | Runtime Image | Use Case |
|------|-----------|---------|
| `erispulse-app-online-*.apk` | Downloaded on first launch | Smaller installer, suitable for good network connectivity |
| `erispulse-app-offline-*.apk` | Packaged into APK | Offline self-contained, no internet required after installation |

The installation steps for both builds are identical:

1. Download and install the APK, and grant notification permission at startup (required to keep background services alive)
2. Click "Run First Initialization" once the initialization banner appears on the home page (includes progress and log view)
3. Create an instance and start it
4. Configure adapters and Model API Keys in the built-in management interface

> The offline package is self-contained — no network is required after installation. If the download is slow or unstable during the first launch, you can switch the download source to a mirror (ghfast / gh-proxy) in the settings page.

### Installation (Desktop: Windows / Linux / macOS)

1. Download the corresponding platform installer from [GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases)
   (Windows `setup.exe` or portable `zip`, Linux `tar.gz`, macOS `zip`)
2. Install and launch
3. On the welcome page, select the ErisPulse SDK version to install (default is the latest) and install it
4. Create an instance and launch it

---

## How It Works

```
┌────────────────────────────────────────────────────┐
│  ErisPulse-App (Flutter)                            │
│                                                    │
│  Native UI ── Dashboard REST / WS API              │
│       │                                            │
│       ├── Android: Foreground Service + proot + Ubuntu rootfs│
│       │        + Python + ErisPulse instance       │
│       └── Desktop: Built-in Python + Direct process management│
└────────────────────────────────────────────────────┘
```

- **Android**: The instance runs inside a foreground service (background isolate) managed `proot` (user-mode chroot). The bot continues to run after the UI closes, with automatic crash recovery.
- **Desktop**: The instance runs as a direct child process of the App; Windows supports minimizing to the system tray for background persistence (closing the window does not interrupt the instance). Upon App restart, management of still-running instances is automatically resumed; upon exit, all instances are stopped uniformly.
- Native UI across all platforms communicates with the instance via the REST / WebSocket API at `127.0.0.1:<port>/Dashboard/*`, sharing the same API as [ErisPulse-Dashboard](docs/en/dashboard.md)

---

## Relationship with SDK

- App comes with a built-in ErisPulse SDK: Android side is bundled in the Ubuntu image, desktop side is installed via PyPI (Welcome page optional versions, default is latest)
- The instance within the App is equivalent to the instance created by the CLI `epsdk`, and the same modules / adapters can be used
- Module developers can register custom pages via [Dashboard View API Registration](dashboard.md):
  The view will automatically appear in the App sidebar navigation (groups are consistent with Dashboard), click to jump to the corresponding page rendering

---



## Related Links

- GitHub repository: [https://github.com/ErisPulse/ErisPulse-App](https://github.com/ErisPulse/ErisPulse-App)
- Download: [GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases)
- Discussions: [Discussions](https://github.com/ErisPulse/ErisPulse-App/discussions)