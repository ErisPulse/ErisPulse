<div align="center">

[English](README.en.md) | [简体中文](README.md) | [繁體中文](README.zh-TW.md)

</div>

<table>
<tr>
<td width="35%" valign="middle" align="center">
<img src=".github/assets/erispulse_logo_1024.png" width="280" alt="ErisPulse" />
</td>
<td width="65%" valign="middle">

# ErisPulse

**事件驅動的多平台機器人開發框架**

[![PyPI](https://img.shields.io/pypi/v/ErisPulse?style=flat-square)](https://pypi.org/project/ErisPulse/)
[![Python Versions](https://img.shields.io/pypi/pyversions/ErisPulse?style=flat-square)](https://pypi.org/project/ErisPulse/)
[![Docker Pulls](https://img.shields.io/docker/pulls/erispulse/erispulse?style=flat-square&logo=docker&label=pulls)](https://hub.docker.com/r/erispulse/erispulse)
[![Docker Pulls](https://img.shields.io/docker/pulls/wsu2059/erispulse?style=flat-square&logo=docker&label=pulls)](https://hub.docker.com/r/erispulse/erispulse)
[![Docker Version](https://img.shields.io/docker/v/erispulse/erispulse?style=flat-square&logo=docker&label=docker)](https://hub.docker.com/r/erispulse/erispulse)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

</td>
</tr>
</table>

---

## 簡介

ErisPulse 是一個基於 Python 的事件驅動型多平台機器人開發框架。透過統一的 OneBot12 標準介面，您可以一次編寫代碼，同時在雲湖、Telegram、OneBot 等多個平台部署相同功能的機器人。框架提供靈活的模組(`插件`)系統、熱重載支援和完整的開發者工具鏈，適用於從簡單聊天機器人到複雜自動化系統的各種場景。

## 核心特性

- **事件驅動架構** - 基於 OneBot12 標準的清晰事件模型
- **跨平台相容** - 插件模組編寫一次即可在所有平台使用
- **模組化設計** - 靈活的插件系統，易於擴展和整合
- **熱重載支援** - 開發時無需重啟即可重新載入代碼
- **完整工具鏈** - 提供 CLI 工具、套件管理和自動化腳本

## 支援的適配器

歡迎您貢獻適配器！

| 適配器 | 說明 |
|--------|------|
| <img src=".github/assets/adapter_logo/kook.svg" width="20" /> [Kook](https://github.com/shanfishapp/ErisPulse-KookAdapter) | Kook（開黑啦）即時通訊平台 |
| <img src=".github/assets/adapter_logo/matrix.svg" width="20" /> [Matrix](https://github.com/ErisPulse/ErisPulse-MatrixAdapter) | Matrix 去中心化通訊協議 |
| <img src=".github/assets/adapter_logo/onebot.png" width="20" /> [OneBot11](https://github.com/ErisPulse/ErisPulse-OneBot11Adapter) | OneBot v11 通用機器人協議 |
| <img src=".github/assets/adapter_logo/onebot.png" width="20" /> [OneBot12](https://github.com/ErisPulse/ErisPulse-OneBot12Adapter) | OneBot v12 標準協議 |
| <img src=".github/assets/adapter_logo/qqbot.svg" width="20" /> [QQ](https://github.com/ErisPulse/ErisPulse-QQBotAdapter) | QQ 官方機器人平台 |
| <img src=".github/assets/adapter_logo/sandbox.png" width="20" /> [沙箱](https://github.com/ErisPulse/ErisPulse-SandboxAdapter) | 網頁端調試，無需接入真實平台 |
| <img src=".github/assets/adapter_logo/telegram.svg" width="20" /> [Telegram](https://github.com/ErisPulse/ErisPulse-TelegramAdapter) | 全球性即時通訊平台 |
| <img src=".github/assets/adapter_logo/email.svg" width="20" /> [郵件](https://github.com/ErisPulse/ErisPulse-EmailAdapter) | 郵件協議收發適配器 |
| <img src=".github/assets/adapter_logo/yunhu.png" width="20" /> [雲湖](https://github.com/ErisPulse/ErisPulse-YunhuAdapter) | 企業級即時通訊平台（機器人接入） |
| <img src=".github/assets/adapter_logo/yunhu.png" width="20" /> [雲湖用戶](https://github.com/wsu2059q/ErisPulse-YunhuUserAdapter) | 基於雲湖用戶協議的接入適配器 |

查看 [適配器詳情介紹](docs/zh-TW/platform-guide/README.md)

## 快速開始

### 使用 Docker (推薦)

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

### 使用 pip 安裝

```bash
pip install ErisPulse

# 國內鏡像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple ErisPulse

# 使用 uv 安裝
uv pip install ErisPulse
```

![安裝演示](.github/assets/docs/install_pip.gif)

> 如果您的 Python 版本低於 3.10，可以使用一鍵安裝腳本自動配置環境。詳見 [安裝腳本說明](scripts/install/)。

### 初始化項目

```bash
# 互動式初始化
epsdk init

# 快速初始化（指定項目名稱）
epsdk init -q -n my_bot
```

### 創建第一個機器人

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

## 應用場景

- **多平台機器人** - 在多個平台部署相同功能的機器人
- **聊天助手** - 接入 AI 聊天模組，實現娛樂和交互
- **自動化工具** - 消息通知、任務管理、數據收集
- **消息轉發** - 跨平台消息同步和轉發

## 文檔資源

| 簡體中文 | English | 繁體中文 |
|----------------|----------------|----------------|
| [文檔入口](docs/zh-CN/README.md) | [Documentation](docs/en/README.md) | [文檔入口](docs/zh-TW/README.md) |

## 外部資源

| 平台 | 主站點 | 備用站點 |
|------|--------|---------|
| 文檔 | [erisdev.com](https://www.erisdev.com/#docs) | [Cloudflare](https://erispulse.pages.dev/#docs) • [GitHub](https://erispulse.github.io/#docs) • [Netlify](https://erispulse.netlify.app/#docs) |
| 模組市場 | [erisdev.com](https://www.erisdev.com/#market) | [Cloudflare](https://erispulse.pages.dev/#market) • [GitHub](https://erispulse.github.io/#market) • [Netlify](https://erispulse.netlify.app/#market) |

## 貢獻指南

ErisPulse 項目的健全性還需要您的一份力！我們歡迎各種形式的貢獻，包括但不限於：

1. **報告問題**
   在 [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues) 提交 bug 報告

2. **功能請求**
   透過 [社區討論](https://github.com/ErisPulse/ErisPulse/discussions) 提出新想法

3. **代碼貢獻**
   提交 Pull Request 前請閱讀我們的 [代碼風格](docs/zh-CN/styleguide/) 以及 [貢獻指南](CONTRIBUTING.md)

4. **文檔改進**
   幫助完善文檔和示例代碼

[加入社區討論](https://github.com/ErisPulse/ErisPulse/discussions)

---

## 致謝

- 本項目部分代碼基於 [sdkFrame](https://github.com/runoneall/sdkFrame)
- 核心適配器標準化層基於 [OneBot12 規範](https://12.onebot.dev/)
- 感謝所有為開源社區做出貢獻的開發者和作者