# API 參考

本目錄包含 ErisPulse 框架的 API 參考文件。

## 文件列表

| 文件 | 說明 |
|------|------|
| [核心模組 API](core-modules.md) | Storage、Config、Logger、Adapter、Module、Lifecycle、Router、HTTP Client 的 API 快速參考 |
| [事件系統 API](event-system.md) | Command、Message、Notice、Request、Meta 事件模組的 API 參考 |
| [適配器系統 API](adapter-system.md) | Adapter 管理器、SendDSL、中間件、Bot 狀態管理的 API 參考 |
| [自動生成 API](auto_api/README.md) | 從原始碼 docstring 自動生成的完整 API 文件 |

> 手動編寫的 API 文件側重於用法範例和快速查閱；自動生成的 API 文件包含完整的類/方法簽名，兩者互補。

## 模組概覽

### 核心模組

| 模組 | 存取路徑 | 說明 |
|------|---------|------|
| `sdk.storage` | `sdk.storage` | 基於 SQLite 的鍵值存儲 + SQL 鏈式查詢 |
| `sdk.config` | `sdk.config` | TOML 格式的設定管理 |
| `sdk.logger` | `sdk.logger` | 模組化日誌系統，支援子日誌器 |
| `sdk.adapter` | `sdk.adapter` | 多平台適配器管理 |
| `sdk.module` | `sdk.module` | 模組註冊、載入、卸載管理 |
| `sdk.lifecycle` | `sdk.lifecycle` | 生命週期事件管理 |
| `sdk.router` | `sdk.router` | HTTP/WebSocket 路由管理 |
| `sdk.client` | `sdk.client` | 統一 HTTP/WS 客戶端 |

### 事件系統

| 模組 | 匯入路徑 | 說明 |
|------|---------|------|
| `command` | `ErisPulse.Core.Event.command` | 命令處理（前綴解析、別名） |
| `message` | `ErisPulse.Core.Event.message` | 訊息事件（私聊、群聊、@訊息） |
| `notice` | `ErisPulse.Core.Event.notice` | 通知事件（好友、群成員變化） |
| `request` | `ErisPulse.Core.Event.request` | 請求事件（好友請求、群邀請） |
| `meta` | `ErisPulse.Core.Event.meta` | 元事件（連線、斷開、心跳） |

### 基類

| 基類 | 匯入路徑 | 說明 |
|------|---------|------|
| `BaseModule` | `ErisPulse.Core.Bases.module.BaseModule` | 模組基類（on_load/on_unload） |
| `BaseAdapter` | `ErisPulse.Core.Bases.adapter.BaseAdapter` | 適配器基類（start/shutdown/call_api） |

## 相關文件

- [核心概念](../getting-started/basic-concepts.md) - 理解框架核心概念
- [模組開發指南](../developer-guide/modules/) - 開發自訂模組
- [適配器開發指南](../developer-guide/adapters/) - 開發平台適配器
- [進階主題](../advanced/) - 路由、HTTP 客戶端、SQL 構建器等深入文件