# ErisPulse-App

[ErisPulse-App](https://github.com/ErisPulse/ErisPulse-App) 是 ErisDev 直接维护的 **官方多端客户端**（Android / Windows / Linux / macOS 均已发布），
提供完全原生的图形化管理界面：在手机或电脑上创建、运行、管理多个机器人实例，
无需终端，也无需单独安装 Python 环境。

> [!IMPORTANT]
> ErisPulse-App 是**独立安装的客户端程序**，不是 `epsdk install` 安装的模块。
> 它内置了 Python 运行时与 ErisPulse SDK，安装即用——**手机上也能直接运行**。

## 功能速览

- **多实例管理**：创建 / 启动 / 停止 / 删除多个实例，端口与访问令牌自动分配，支持全新环境或克隆已有环境
- **概览仪表盘**：适配器 / 模块 / 在线机器人 / 事件总数统计，CPU / 内存占用告警变色
- **模块商店**：搜索与标签筛选、一键安装 / 升级 / 卸载、指定版本安装、pip 镜像源与 Git 包支持
- **事件流 + 事件构建器**：实时事件查看，可视化构造测试事件并提交到适配器
- **监控**：日志 / 生命周期 / 审计三合一视图
- **命令管理**：前缀与别名等全局设置、启停与平台黑白名单
- **机器人总览 / 配置 / 文件管理**：原生界面直接操作实例
- **后台常驻**：Android 前台服务保活；Windows 最小化到系统托盘，关闭窗口不中断实例
- **模块动态视窗**：模块注册的页面自动出现在侧边导航（与 Dashboard 同分组），点击直达

## 支持平台

所有平台的安装包均从 [GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases) 下载，按需选择即可：

| 平台 | 安装包 | 说明 |
|------|--------|------|
| Android | `online-*.apk` / `offline-*.apk` | **手机直接运行**，无需电脑 |
| Windows | `windows-x64-setup.exe` / `windows-x64.zip` | 安装版 / 免安装版 |
| Linux | `linux-x64.tar.gz` | 解压即用 |
| macOS | `macos-arm64.zip` | Apple Silicon（arm64） |

一个 Flutter 代码库覆盖所有平台。

---

## 安装方式（Android / 手机直接运行）

从 [GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases) 下载 APK 安装即可，有两种构建：

| 构建 | 运行时镜像 | 适用场景 |
|------|-----------|---------|
| `erispulse-app-online-*.apk` | 首次启动时下载 | 安装包更小，适合网络良好 |
| `erispulse-app-offline-*.apk` | 已打包进 APK | 离线自包含，安装后无需联网 |

两种构建安装步骤相同：

1. 下载并安装 APK，启动时允许通知权限（用于保持后台服务存活）
2. 首页出现初始化横幅后点击运行首次初始化（含进度与日志视图）
3. 创建一个实例并启动
4. 在 App 内置的管理界面配置适配器与模型 API Key

> 离线包自包含——安装后无需网络。如果首次启动下载慢或不稳定，
> 可在设置页将下载源切换为镜像（ghfast / gh-proxy）。

### 安装方式（桌面端：Windows / Linux / macOS）

1. 从 [GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases) 下载对应平台安装包
   （Windows `setup.exe` 或免安装 `zip`、Linux `tar.gz`、macOS `zip`）
2. 安装并启动
3. 在欢迎页选择要安装的 ErisPulse SDK 版本（默认最新）并安装
4. 创建实例并启动

---

## 工作原理

```
┌────────────────────────────────────────────────────┐
│  ErisPulse-App (Flutter)                            │
│                                                    │
│  原生 UI ── Dashboard REST / WS API                │
│       │                                            │
│       ├── Android：前台服务 + proot + Ubuntu rootfs│
│       │        + Python + ErisPulse 实例           │
│       └── 桌面端：内置 Python + 直接进程管理         │
└────────────────────────────────────────────────────┘
```

- **Android**：实例运行在前台服务（background isolate）托管的 proot（用户态 chroot）
  内，UI 关闭后机器人仍持续运行，崩溃自动重启
- **桌面端**：实例作为 App 的直接子进程运行；Windows 支持最小化到系统托盘后台常驻
  （关闭窗口不中断实例），App 重启后自动恢复对仍在运行实例的管理，退出时统一停止全部实例
- 所有平台的原生 UI 都通过 `127.0.0.1:<port>/Dashboard/*` 的 REST / WebSocket API
  与实例通信，与 [ErisPulse-Dashboard](dashboard.md) 共用同一套 API

---

## 与 SDK 的关系

- App 内置 ErisPulse SDK：Android 端打包在 Ubuntu 镜像中，桌面端从 PyPI 安装
  （欢迎页可选版本，默认最新）
- App 中的实例与命令行 `epsdk` 创建的实例等价，可使用相同的模块 / 适配器
- 模块开发者可通过 [Dashboard 视窗注册 API](dashboard.md) 注册自定义页面：
  视窗会自动出现在 App 侧边导航（分组与 Dashboard 一致），点击跳转对应页面渲染

---

## 相关链接

- GitHub 仓库：[https://github.com/ErisPulse/ErisPulse-App](https://github.com/ErisPulse/ErisPulse-App)
- 下载：[GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases)
- 讨论：[Discussions](https://github.com/ErisPulse/ErisPulse-App/discussions)
