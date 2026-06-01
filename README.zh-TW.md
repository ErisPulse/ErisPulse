<table>
<tr>
<td width="35%" valign="middle" align="center">

<img src=".github/assets/mascot-hero.png" width="320" alt="ErisPulse" />

</td>
<td valign="middle">

[English](README.en.md) | [简体中文](README.md) | **繁體中文**

# ErisPulse

**事件驅動的多平台機器人開發框架**

基於 OneBot12 標準介面，一次編寫，多平台部署。靈活的模組系統、熱重載支援和完整的開發者工具鏈，適用於從簡單聊天機器人到複雜自動化系統的各種場景。

> 支援 Vibe Coding 工作流，讓 AI 直接生成可用模組 — [查看](docs/zh-TW/ai-support/README.md)

[![PyPI](https://img.shields.io/pypi/v/ErisPulse?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/ErisPulse/)
[![Python](https://img.shields.io/badge/Python-3.10+-FFD43B?style=for-the-badge&logo=python&logoColor=blue)](https://pypi.org/project/ErisPulse/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://hub.docker.com/r/erispulse/erispulse)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](https://github.com/ErisPulse/ErisPulse/blob/main/LICENSE)
[![Stars](https://img.shields.io/github/stars/ErisPulse/ErisPulse?style=for-the-badge&logo=github&color=brightgreen)](https://github.com/ErisPulse/ErisPulse)
[![Downloads](https://img.shields.io/pepy/dt/ErisPulse?style=for-the-badge&color=blue)](https://pypi.org/project/ErisPulse/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&style=for-the-badge)](https://github.com/astral-sh/ruff)
[![Socket](https://img.shields.io/badge/Socket-Secure-2ea043?style=for-the-badge&logo=socket&logoColor=white)](https://socket.dev/pypi/package/erispulse)

[![文檔](https://img.shields.io/badge/文檔-erisdev.com-FF6B9D?style=for-the-badge&logo=bookstack&logoColor=white)](https://www.erisdev.com)
[![模組市場](https://img.shields.io/badge/模組市場-erisdev.com-C724B1?style=for-the-badge&logo=webpack&logoColor=white)](https://www.erisdev.com/#market)
[![討論](https://img.shields.io/badge/GitHub-Discussions-181717?style=for-the-badge&logo=github)](https://github.com/ErisPulse/ErisPulse/discussions)

</td>
</tr>
</table>

---

<div align="center">

### 核心特性

</div>

<table>
<tr>
<td width="50%" align="center" valign="top">
<br/>

### ⚡ 事件驅動架構

基於 OneBot12 標準的清晰事件模型，讓訊息處理邏輯更加直觀和高效

</td>
<td width="50%" align="center" valign="top">
<br/>

### 🌐 跨平台相容

模組編寫一次即可在所有平台使用，無需為不同平台重複開發

</td>
</tr>
<tr>
<td width="50%" align="center" valign="top">
<br/>

### 🧩 模組化設計

靈活的模組系統，易於擴展和整合，支援熱插拔模組管理

</td>
<td width="50%" align="center" valign="top">
<br/>

### 🔄 熱重載支援

開發時無需重啟即可重新載入代碼，大幅提升開發迭代效率

</td>
</tr>
</table>

---

### 支援的適配器

<div align="center">
<!-- <img src=".github/assets/adapter-showcase.png" width="520" alt="適配器展示" /> -->

歡迎您貢獻適配器！

| 適配器 | 說明 |
|--------|------|
| <img src=".github/assets/adapter_logo/kook.svg" height="20" alt="Kook" /> [Kook](https://github.com/shanfishapp/ErisPulse-KookAdapter) | Kook（開黑啦）即時通訊平台 |
| <img src=".github/assets/adapter_logo/matrix.svg" height="20" alt="Matrix" /> [Matrix](https://github.com/ErisPulse/ErisPulse-MatrixAdapter) | Matrix 去中心化通訊協議 |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot11](https://github.com/ErisPulse/ErisPulse-OneBot11Adapter) | OneBot v11 通用機器人協議 |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot12](https://github.com/ErisPulse/ErisPulse-OneBot12Adapter) | OneBot v12 標準協議 |
| <img src=".github/assets/adapter_logo/qqbot.svg" height="20" alt="QQ" /> [QQ](https://github.com/ErisPulse/ErisPulse-QQBotAdapter) | QQ 官方機器人平台 |
| <img src=".github/assets/adapter_logo/sandbox.png" height="20" alt="Sandbox" /> [沙箱](https://github.com/ErisPulse/ErisPulse-SandboxAdapter) | 網頁端調試，無需接入真實平台 |
| <img src=".github/assets/adapter_logo/telegram.svg" height="20" alt="Telegram" /> [Telegram](https://github.com/ErisPulse/ErisPulse-TelegramAdapter) | 全球性即時通訊平台 |
| <img src=".github/assets/adapter_logo/email.svg" height="20" alt="Email" /> [郵件](https://github.com/ErisPulse/ErisPulse-EmailAdapter) | 郵件協議收發適配器 |
| <img src=".github/assets/adapter_logo/yunhu.png" height="20" alt="Yunhu" /> [雲湖](https://github.com/ErisPulse/ErisPulse-YunhuAdapter) | 企業級即時通訊平台（機器人接入） |
| [雲湖用戶](https://github.com/wsu2059q/ErisPulse-YunhuUserAdapter) | 基於雲湖用戶協議的接入適配器 |
| [花楓咖啡館](https://github.com/ErisPulse/ErisPulse-Ideaura/) | Allons! \(・ω・) / |

查看 [適配器詳情介紹](docs/zh-TW/platform-guide/README.md)

</div>

---

### 快速開始

#### 一鍵安裝腳本（推薦）

安裝腳本會自動檢測您的環境（Docker、Python、uv），引導選擇最適合的安裝方式，支援多語言（中文/English/日本語/Русский/繁體中文）。

Windows (PowerShell):
```powershell
irm https://get.erisdev.com/install.ps1 -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1
```

macOS / Linux:
```bash
curl -fsSL https://get.erisdev.com/install.sh -o install.sh && chmod +x install.sh && ./install.sh
```

#### 使用 Docker (推薦)

```bash
docker pull erispulse/erispulse:latest
```

<details>
<summary>Docker Hub不可用？</summary>

如果 Docker Hub 無法訪問，可以使用 GitHub Container Registry：

```bash
docker pull ghcr.io/erispulse/erispulse:latest
```

使用 ghcr.io 鏡像時，需要修改 `docker-compose.yml` 中的 image：
```yaml
image: ghcr.io/erispulse/erispulse:latest
```

</details>

<details>
<summary>快速啟動</summary>

```bash
# 下載 docker-compose.yml
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# 設定 Dashboard 登入令牌並啟動
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

> 鏡像內建 ErisPulse 框架和 Dashboard 管理面板，支援 `linux/amd64` 和 `linux/arm64` 架構。

啟動後訪問 `http://<host>:<port>/Dashboard`，使用設定的令牌作為密碼登入 Dashboard 管理面板。

</details>

<details>
<summary>使用預發布版本 (Dev)</summary>

設置 `ERISPULSE_CHANNEL=dev` 即可使用預發布版本：

```bash
# 方式一：使用環境變數（推薦）
ERISPULSE_CHANNEL=dev ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d

# 方式二：建置 dev 鏡像
ERISPULSE_BUILD_TARGET=dev docker compose up -d --build
```

如需啟動時自動更新到最新版本（無論 stable 還是 dev），顯式設置 `ERISPULSE_UPDATE_ON_START=true`：

```bash
ERISPULSE_CHANNEL=dev ERISPULSE_UPDATE_ON_START=true docker compose up -d
```

也可以拉取預建置的 dev 鏡像：

```bash
docker pull erispulse/erispulse:dev
```

</details>

<details>
<summary>Docker 環境變量</summary>

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `ERISPULSE_CHANNEL` | `stable` | 版本通道：`stable`（穩定版）或 `dev`（預發布版） |
| `ERISPULSE_UPDATE_ON_START` | `false` | 容器啟動時是否自動更新到最新版本（需顯式啟用） |
| `ERISPULSE_DASHBOARD_TOKEN` | 空 | Dashboard 登入令牌 |
| `ERISPULSE_PORT` | `8000` | Dashboard 埠對映 |
| `TZ` | `Asia/Shanghai` | 容器時區 |

> 啟用 `ERISPULSE_UPDATE_ON_START=true` 可確保即使鏡像較舊，容器也能在啟動時自動獲取最新版本。

</details>

#### 1Panel 應用商店

透過 [1Panel](https://1panel.cn) 應用商店一鍵