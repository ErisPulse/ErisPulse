<table>
<tr>
<td width="35%" valign="middle" align="center">

<img src=".github/assets/mascot-hero.png" width="320" alt="ErisPulse" />

</td>
<td valign="middle">

[English](README.en.md) | **简体中文** | [繁體中文](README.zh-TW.md)

# ErisPulse

**事件驅動的多平台機器人開發框架**

基於 OneBot12 標準接口，一次編寫，多平台部署。靈活的插件系統、熱重載支援和完整的開發者工具鏈，適用於從簡單聊天機器人到複雜自動化系統的各種場景。

> 支援 Vibe Coding 工作流，讓 AI 直接生成可用模組 — [查看](docs/zh-TW/ai-support/README.md)

[![PyPI](https://img.shields.io/pypi/v/ErisPulse?style=flat-square)](https://pypi.org/project/ErisPulse/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://pypi.org/project/ErisPulse/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)](https://hub.docker.com/r/erispulse/erispulse)
[![License](https://img.shields.io/github/license/ErisPulse/ErisPulse?style=flat-square)](https://github.com/ErisPulse/ErisPulse/blob/main/LICENSE)
[![Stars](https://img.shields.io/github/stars/ErisPulse/ErisPulse?style=flat-square)](https://github.com/ErisPulse/ErisPulse)
[![Downloads](https://img.shields.io/pypi/dm/ErisPulse?style=flat-square)](https://pypi.org/project/ErisPulse/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

[![文檔](https://img.shields.io/badge/文檔-erisdev.com-0a0a0a?style=flat-square)](https://www.erisdev.com)
[![模組市場](https://img.shields.io/badge/模組市場-erisdev.com-0a0a0a?style=flat-square)](https://www.erisdev.com/#market)
[![討論](https://img.shields.io/badge/GitHub-Discussions-0a0a0a?style=flat-square&logo=github)](https://github.com/ErisPulse/ErisPulse/discussions)

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

### 事件驅動架構

基於 OneBot12 標準的清晰事件模型，讓訊息處理邏輯更加直觀和高效

</td>
<td width="50%" align="center" valign="top">
<br/>

### 跨平台相容

模組編寫一次即可在所有平台使用，無需為不同平台重複開發

</td>
</tr>
<tr>
<td width="50%" align="center" valign="top">
<br/>

### 模組化設計

靈活的模組系統，易於擴展和整合，支援熱插拔模組管理

</td>
<td width="50%" align="center" valign="top">
<br/>

### 熱重載支援

開發時無需重啟即可重新載入代碼，大幅提升開發迭代效率

</td>
</tr>
</table>

---

### 支援的適配器

<div align="center">

<table>
<tr>
<td width="35%" valign="middle" align="center">

<img src=".github/assets/adapter-showcase.png" width="320" alt="支援的適配器" />

</td>
<td valign="middle">

歡迎您貢獻適配器！

| 適配器 | 說明 |
|--------|------|
| [Kook](https://github.com/shanfishapp/ErisPulse-KookAdapter) | Kook（開黑啦）即時通訊平台 |
| [Matrix](https://github.com/ErisPulse/ErisPulse-MatrixAdapter) | Matrix 去中心化通訊協議 |
| [OneBot11](https://github.com/ErisPulse/ErisPulse-OneBot11Adapter) | OneBot v11 通用機器人協議 |
| [OneBot12](https://github.com/ErisPulse/ErisPulse-OneBot12Adapter) | OneBot v12 標準協議 |
| [QQ](https://github.com/ErisPulse/ErisPulse-QQBotAdapter) | QQ 官方機器人平台 |
| [沙箱](https://github.com/ErisPulse/ErisPulse-SandboxAdapter) | 網頁端調試，無需接入真實平台 |
| [Telegram](https://github.com/ErisPulse/ErisPulse-TelegramAdapter) | 全球性即時通訊平台 |
| [郵件](https://github.com/ErisPulse/ErisPulse-EmailAdapter) | 郵件協議收發適配器 |
| [雲湖](https://github.com/ErisPulse/ErisPulse-YunhuAdapter) | 企業級即時通訊平台（機器人接入） |
| [雲湖用戶](https://github.com/wsu2059q/ErisPulse-YunhuUserAdapter) | 基於雲湖用戶協議的接入適配器 |
| [花楓咖啡館](https://github.com/ErisPulse/ErisPulse-Ideaura/) | Allons! \(・ω・) / |

查看 [適配器詳情維護文檔](docs/zh-TW/platform-guide/README.md)

</td>
</tr>
</table>

</div>

---

### 快速開始

#### 使用 Docker (推薦)

```bash
docker pull erispulse/erispulse:latest
```

<details>
<summary>Docker Hub 不可用？</summary>

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

# 設置 Dashboard 登入令牌並啟動
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

> 鏡像內建 ErisPulse 框架和 Dashboard 管理面板，支援 `linux/amd64` 和 `linux/arm64` 架構。

啟動後訪問 `http://<host>:<port>/Dashboard`，使用設置的令牌作為密碼登入 Dashboard 管理面板。

</details>

<details>
<summary>使用預發布版本 (Dev)</summary>

設置 `ERISPULSE_CHANNEL=dev` 即可使用預發布版本：

```bash
# 方式一：使用環境變數（推薦）
ERISPULSE_CHANNEL=dev ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d

# 方式二：構建 dev 鏡像
ERISPULSE_BUILD_TARGET=dev docker compose up -d --build
```

如需啟動時自動更新到最新版本（無論 stable 還是 dev），顯式設置 `ERISPULSE_UPDATE_ON_START=true`：

```bash
ERISPULSE_CHANNEL=dev ERISPULSE_UPDATE_ON_START=true docker compose up -d
```

也可以拉取預構建的 dev 鏡像：

```bash
docker pull erispulse/erispulse:dev
```

</details>

<details>
<summary>Docker 環境變數</summary>

| 變量 | 預設值 | 說明 |
|------|--------|------|
| `ERISPULSE_CHANNEL` | `stable` | 版本通道：`stable`（穩定版）或 `dev`（預發布版） |
| `ERISPULSE_UPDATE_ON_START` | `false` | 容器啟動時是否自動更新到最新版本（需顯式啟用） |
| `ERISPULSE_DASHBOARD_TOKEN` | 空 | Dashboard 登入令牌 |
| `ERISPULSE_PORT` | `8000` | Dashboard 埠映射 |
| `TZ` | `Asia/Shanghai` | 容器時區 |

> 啟用 `ERISPULSE_UPDATE_ON_START=true` 可確保即使鏡像較舊，容器也能在啟動時自動獲取最新版本。

</details>

#### 1Panel 應用商店

通過 [1Panel](https://1panel.cn) 應用商店一鍵安裝 ErisPulse，詳見 [ErisPulse-1Panel](https://github.com/ErisPulse/ErisPulse-1Panel)。

```bash
bash <(curl -sL https://get-1panel.erisdev.com/install.sh)
```

#### 使用 pip 安裝

```bash
pip install ErisPulse
```

<img src=".github/assets/docs/install_pip.gif" width="480" alt="安裝演示" />

> 如果您的 Python 版本低於 3.10，可以使用一鍵安裝腳本自動配置環境。詳見 [安裝腳本說明](scripts/install/)。

#### 運行效果

同一段程式碼，多個平台響應：

<table>
<tr>
<td align="center" width="33%">

**Kook**

<img src=".github/assets/demo-kook.png" alt="Kook 演示" />

</td>
<td align="center" width="33%">

**QQ**

<img src=".github/assets/demo-qq.png" alt="QQ 演示" />

</td>
<td align="center" width="33%">

**雲湖**

<img src=".github/assets/demo-yunhu.png" alt="雲湖 演示" />

</td>
</tr>
</table>

#### 初始化項目

```bash
# 互動式初始化
epsdk init

# 快速初始化（指定項目名稱）
epsdk init -q -n my_bot
```

#### 創建第一個機器人

創建 `main.py` 文件：

<table>
<tr>
<td width="50%" valign="top">

**命令處理器**

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("hello", help="發送問候消息")
async def hello_handler(event):
    user_name = event.get_user_nickname() or "朋友"
    await event.reply(f"你好，{user_name}！")

@command("ping", help="測試機器人是否在線")
async def ping_handler(event):
    await event.reply("Pong！機器人運行正常。")

if __name__ == "__main__":
    import asyncio
    asyncio.run(sdk.run(keep_running=True))
```

</td>
<td width="50%" valign="top">

**效果說明**

發送 `/hello`

機器人回覆：`你好，{用戶名}！`

---

發送 `/ping`

機器人回覆：`Pong！機器人運行正常。`

---

**運行方式**

```bash
epsdk run main.py
# 或開發模式
epsdk run main.py --reload
```

</td>
</tr>
</table>

更多詳細說明請參閱：
- [快速開始指南](docs/zh-TW/quick-start.md)
- [入門指南](docs/zh-TW/getting-started/)

---

### 應用場景

<div align="center">

| 多平台機器人 | 聊天助手 | 自動化工具 | 消息轉發 |
|:---:|:---:|:---:|:---:|
| 在多個平台部署<br>相同功能的機器人 | 接入 AI 聊天模組<br>實現娛樂和交互 | 消息通知、任務管理<br>數據收集 | 跨平台消息<br>同步和轉發 |

</div>

---

### 文檔與資源

| 簡體中文 | English | 繁體中文 |
|:---:|:---:|:---:|
| [文檔入口](docs/zh-CN/README.md) | [Documentation](docs/en/README.md) | [文檔入口](docs/zh-TW/README.md) |

| 平台 | 主站點 | 備用站點 |
|------|--------|---------|
| 文檔 | [erisdev.com](https://www.erisdev.com/#docs) | [Cloudflare](https://erispulse.pages.dev/#docs) · [GitHub](https://erispulse.github.io/#docs) · [Netlify](https://erispulse.netlify.app/#docs) |
| 模組市場 | [erisdev.com](https://www.erisdev.com/#market) | [Cloudflare](https://erispulse.pages.dev/#market) · [GitHub](https://erispulse.github.io/#market) · [Netlify](https://erispulse.netlify.app/#market) |

---

### 貢獻指南

ErisPulse 項目的健全性還需要您的一份力！我們歡迎各種形式的貢獻：

1. **報告問題** — 在 [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues) 提交 bug 報告
2. **功能請求** — 通過 [社區討論](https://github.com/ErisPulse/ErisPulse/discussions) 提出新想法
3. **代碼貢獻** — 提交 PR 前請閱讀 [代碼風格](docs/zh-CN/styleguide/) 及 [貢獻指南](CONTRIBUTING.md)
4. **文檔改進** — 幫助完善文檔和示例代碼

[加入社區討論](https://github.com/ErisPulse/ErisPulse/discussions)

---

<div align="center">

### 致謝

<img src=".github/assets/thanks.png" width="200" alt="感謝" />

本項目部分代碼基於 [sdkFrame](https://github.com/runoneall/sdkFrame) · 核心適配器標準化層基於 [OneBot12 規範](https://12.onebot.dev/) · 感謝所有為開源社區做出貢獻的開發者和作者

</div>