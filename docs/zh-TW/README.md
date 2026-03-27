# ErisPulse 文檔

ErisPulse 是一個可擴展的多平台訊息處理框架，支援透過適配器與不同平台進行交互，提供彈性的模組系統用於功能擴充。

> 遇到不理解的術語？查看 [術語表](terminology.md) 獲取通俗易懂的解釋。

## 文檔導航

### 快速開始

- [快速開始指南](quick-start.md) - 安裝和執行 ErisPulse 的入門指南

### 新手入門

如果你是第一次使用 ErisPulse，建議按以下順序閱讀：

1. [入門指南總覽](getting-started/README.md)
2. [建立第一個機器人](getting-started/first-bot.md)
3. [基礎概念](getting-started/basic-concepts.md)
4. [事件處理入門](getting-started/event-handling.md)
5. [常見任務範例](getting-started/common-tasks.md)

### 使用者指南

- [安裝和設定](user-guide/installation.md)
- [CLI 命令參考](user-guide/cli-reference.md)
- [設定檔說明](user-guide/configuration.md)

### 開發者指南

#### 模組開發

- [模組開發入門](developer-guide/modules/getting-started.md)
- [模組核心概念](developer-guide/modules/core-concepts.md)
- [Event 包裝類詳解](developer-guide/modules/event-wrapper.md)
- [模組開發最佳實踐](developer-guide/modules/best-practices.md)

#### 適配器開發

- [適配器開發入門](developer-guide/adapters/getting-started.md)
- [適配器核心概念](developer-guide/adapters/core-concepts.md)
- [SendDSL 詳解](developer-guide/adapters/send-dsl.md)
- [適配器開發最佳實踐](developer-guide/adapters/best-practices.md)

#### 擴充開發

- [CLI 擴充開發](developer-guide/extensions/cli-extensions.md)

### 平台特性指南

- [平台特性說明](platform-guide/README.md)
- [雲湖平台特性](platform-guide/yunhu.md)
- [Telegram 平台特性](platform-guide/telegram.md)
- [OneBot11 平台特性](platform-guide/onebot11.md)
- [OneBot12 平台特性](platform-guide/onebot12.md)
- [郵件平台特性](platform-guide/email.md)

### API 參考

- [核心模組 API](api-reference/core-modules.md)
- [事件系統 API](api-reference/event-system.md)
- [適配器系統 API](api-reference/adapter-system.md)

### 技術標準

- [事件轉換標準](standards/event-conversion.md)
- [API 回應標準](standards/api-response.md)
- [傳送方法規範](standards/send-method-spec.md)

### 進階主題

- [懶載入系統](advanced/lazy-loading.md)
- [生命週期管理](advanced/lifecycle.md)
- [路由系統](advanced/router.md)

### AI 輔助開發

- [AI 輔助開發](ai-support/README.md)

### 風格指南

- [文檔風格指南](styleguide/docstring.md)

## 開發方式

ErisPulse 支援兩種開發方式：

### 1. 模組開發（推薦）

建立獨立的模組套件，透過套件管理器安裝使用。這種方式便於散發和管理，適合公開發布的功能。

### 2. 嵌入式開發

直接在專案中嵌入 ErisPulse 代碼，無需建立獨立模組。這種方式適合快速原型開發或專案內部專用功能。

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

# 執行 SDK 並維持運行 | 需要在非同步環境中執行
asyncio.run(sdk.run(keep_running=True))
```

## 獲取幫助

- GitHub 儲存庫：[https://github.com/ErisPulse/ErisPulse](https://github.com/ErisPulse/ErisPulse)
- 問題回饋：提交 Issue
- 技術討論：查看 Discussions

## 相關連結

- [OneBot12 標準](https://12.onebot.dev/)
- [雲湖官方文檔](https://www.yhchat.com/document/)
- [Telegram Bot API](https://core.telegram.org/bots/api)