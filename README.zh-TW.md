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
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Socket Badge](https://socket.dev/api/badge/pypi/package/ErisPulse/latest)](https://socket.dev/pypi/package/ErisPulse)

</td>
</tr>
</table>

---

## 簡介

ErisPulse 是一個基於 Python 的事件驅動型多平台機器人開發框架。通過統一的 OneBot12 標準接口，您可以一次編寫代碼，同時在雲湖、Telegram、OneBot 等多個平台部署相同功能的機器人。框架提供靈活的模組（`插件`）系統、熱重載支持和完整的開發者工具鏈，適用於從簡單聊天機器人到複雜自動化系統的各種場景。

## 核心特性

- **事件驅動架構** - 基於 OneBot12 標準的清晰事件模型
- **跨平台兼容** - 插件模組編寫一次即可在所有平台使用
- **模組化設計** - 靈活的插件系統，易於擴展和集成
- **熱重載支持** - 開發時無需重啟即可重新加載代碼
- **完整工具鏈** - 提供 CLI 工具、包管理和自動化腳本

## 快速開始

### 安裝

```bash
pip install ErisPulse

# 中国大陆鏡像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple ErisPulse

# 使用 `uv` 安裝
uv install ErisPulse
```

![安裝演示](.github/assets/docs/install_pip.gif)

> 如果您的 Python 版本低於 3.10，可以使用一鍵安裝腳本自動配置環境。詳見 [安裝腳本說明](scripts/install/)。

### 初始化項目

```bash
# 交互式初始化
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
- [快速開始指南](docs/quick-start.md)
- [入門指南](docs/getting-started/)

## 應用場景

- **多平台機器人** - 在多個平台部署相同功能的機器人
- **聊天助手** - 接入 AI 聊天模組，實現娛樂和交互
- **自動化工具** - 消息通知、任務管理、數據收集
- **消息轉發** - 跨平台消息同步和轉發

## 支持的適配器

歡迎您貢獻適配器！

- [雲湖](https://github.com/ErisPulse/ErisPulse-YunhuAdapter) - 企業級即時通訊平台（機器人賬戶）
- [雲湖用戶](https://github.com/wsu2059q/ErisPulse-YunhuUserAdapter) - 基於雲湖用戶賬戶的適配器
- [Telegram](https://github.com/ErisPulse/ErisPulse-TelegramAdapter) - 全球性即時通訊軟件
- [OneBot11](https://github.com/ErisPulse/ErisPulse-OneBot11Adapter) - 通用機器人接口標準
- [OneBot12](https://github.com/ErisPulse/ErisPulse-OneBot12Adapter) - OneBot12 標準
- [郵件](https://github.com/ErisPulse/ErisPulse-EmailAdapter) - 郵件收發處理
- [沙箱](https://github.com/ErisPulse/ErisPulse-SandboxAdapter) - 網頁調試界面，無需接入實際平台

查看 [適配器詳情介紹](docs/platform-guide/README.md)

## 文檔語言

<div align="center">

| 🇨🇳🇳 简体中文 | 🇺🇸 English | 🇹🇼 繁體中文 |
|----------------|----------------|----------------|
| [文档入口](docs/zh-CN/README.md) | [Documentation](docs/en/README.md) | [文檔入口](docs/zh-TW/README.md) |

</div>

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
   通過 [社區討論](https://github.com/ErisPulse/ErisPulse/discussions) 提出新想法

3. **代碼貢獻**
   提交 Pull Request 前請閱讀我們的 [代碼風格](docs/styleguide/) 以及 [貢獻指南](CONTRIBUTING.md)

4. **文檔改進**
   幫助完善文檔和示例代碼

[加入社區討論](https://github.com/ErisPulse/ErisPulse/discussions)

---

## 致謝

- 本項目部分代碼基於 [sdkFrame](https://github.com/runoneall/sdkFrame)
- 核心適配器標準化層基於 [OneBot12 規範](https://12.onebot.dev/)
- 感謝所有為開源社區做出貢獻的開發者和作者