# ErisPulse 文件

ErisPulse 是一個可擴展的多平台訊息處理框架，支援透過適配器與不同平台進行互動，提供靈活的模組系統用於功能擴展。

> 遇到不理解的術語？查看 [術語表](docs/zh-TW/terminology.md) 獲取通俗易懂的解釋。

## 文件導航

### 快速入門

- [快速入門指南](docs/zh-TW/quick-start.md) - 安裝和運行 ErisPulse 的入門指南

### 架構概覽

- [架構概覽](docs/zh-TW/architecture.md) - 透過可視化圖表了解 SDK 核心架構、初始化流程、事件處理和生命週期

### 新手入門

如果你是第一次使用 ErisPulse，建議按以下順序閱讀：

1. [入門指南總覽](docs/zh-TW/getting-started/README.md)
2. [建立第一個機器人](docs/zh-TW/getting-started/first-bot.md)
3. [基礎概念](docs/zh-TW/getting-started/basic-concepts.md)
4. [事件處理入門](docs/zh-TW/getting-started/event-handling.md)
5. [常見任務範例](docs/zh-TW/getting-started/common-tasks.md)

### 用戶使用指南

- [安裝和配置](docs/zh-TW/user-guide/installation.md)
- [CLI 命令參考](docs/zh-TW/user-guide/cli-reference.md)
- [配置檔說明](docs/zh-TW/user-guide/configuration.md)
- [部署指南](docs/zh-TW/user-guide/deployment.md)

### 開發者指南

#### 模組開發

- [模組開發入門](docs/zh-TW/developer-guide/modules/getting-started.md)
- [模組核心概念](docs/zh-TW/developer-guide/modules/core-concepts.md)
- [Event 包裝類詳解](docs/zh-TW/developer-guide/modules/event-wrapper.md)
- [模組開發最佳實踐](docs/zh-TW/developer-guide/modules/best-practices.md)

#### 適配器開發

- [適配器開發入門](docs/zh-TW/developer-guide/adapters/getting-started.md)
- [適配器核心概念](docs/zh-TW/developer-guide/adapters/core-concepts.md)
- [SendDSL 詳解](docs/zh-TW/developer-guide/adapters/send-dsl.md)
- [適配器開發最佳實踐](docs/zh-TW/developer-guide/adapters/best-practices.md)

#### 發布

- [發布與模組商店指南](docs/zh-TW/developer-guide/publishing.md) - 將模組、適配器發布到 ErisPulse 模組商店

### 平台特性指南

- [平台特性說明](docs/zh-TW/platform-guide/README.md)
- [雲湖平台特性](docs/zh-TW/platform-guide/yunhu.md)
- [Telegram 平台特性](docs/zh-TW/platform-guide/telegram.md)
- [OneBot11 平台特性](docs/zh-TW/platform-guide/onebot11.md)
- [OneBot12 平台特性](docs/zh-TW/platform-guide/onebot12.md)
- [郵件平台特性](docs/zh-TW/platform-guide/email.md)

### API 參考

- [核心模組 API](docs/zh-TW/api-reference/core-modules.md)
- [事件系統 API](docs/zh-TW/api-reference/event-system.md)
- [適配器系統 API](docs/zh-TW/api-reference/adapter-system.md)

### 技術標準

- [事件轉換標準](docs/zh-TW/standards/event-conversion.md)
- [API 回應標準](docs/zh-TW/standards/api-response.md)
- [發送方法規範](docs/zh-TW/standards/send-method-spec.md)

### 高級主題

- [啟動流程與手動控制](docs/zh-TW/advanced/startup.md) - 啟動鏈路拆解與手動完整啟動
- [懶加載系統](docs/zh-TW/advanced/lazy-loading.md)
- [生命週期管理](docs/zh-TW/advanced/lifecycle.md)
- [路由系統](docs/zh-TW/advanced/router.md)
- [MessageBuilder 詳解](docs/zh-TW/advanced/message-builder.md)
- [會話類型系統](docs/zh-TW/advanced/session-types.md)
- [Conversation 多輪對話](docs/zh-TW/advanced/conversation.md)

### AI 輔助開發

- [AI 輔助開發](docs/zh-TW/ai-support/README.md)

### 風格指南

- [文件風格指南](docs/zh-TW/styleguide/docstring.md)

## 開發方式

ErisPulse 支援兩種開發方式：

### 1. 模組開發（推薦）

建立獨立的模組包，透過套件管理器安裝使用。這方式便於分發和管理，適合公開發布的功能。

### 2. 嵌入式開發

直接在專案中嵌入 ErisPulse 程式碼，無需建立獨立模組。這方式適合快速原型開發或專案內部專用功能。

範例：

```python
# 直接嵌入使用
import asyncio
from ErisPulse import sdk
from ErisPulse.Core.Event import command

# 註冊命令處理器
@command("hello")
async def hello_handler(event):
    await event.reply("你好！")

# 運行 SDK 並且維持運行 | 需要在非同步環境中執行
asyncio.run(sdk.run(keep_running=True))
```

## 獲取幫助

- GitHub 倉庫：[https://github.com/ErisPulse/ErisPulse](https://github.com/ErisPulse/ErisPulse)
- 問題回饋：提交 Issue
- 技術討論：查看 Discussions

## 相關連結

- [OneBot12 標準](https://12.onebot.dev/)
- [雲湖官方文件](https://www.yhchat.com/document/)
- [Telegram Bot API](https://core.telegram.org/bots/api)

[English](README.md) | [简体中文](README.zh-CN.md) | **繁體中文** | [日本語](README.ja.md) | [Русский](README.ru.md)