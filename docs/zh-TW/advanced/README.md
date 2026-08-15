# 進階主題

本目錄包含 ErisPulse 框架的高級特性和深入主題。

## 文件列表

- [啟動流程與手動控制](docs/zh-TW/startup.md) - 啟動鏈路拆解（Finder/Loader/Manager/Router）與手動完整啟動
- [懶加載系統](docs/zh-TW/lazy-loading.md) - 懶加載模組系統的工作原理和配置
- [模組作用域系統](docs/zh-TW/scope.md) - 模組與適配器 Bot/平台的繫結與隔離
- [國際化 (i18n)](docs/zh-TW/i18n.md) - 多語言支援、翻譯註冊與語言偵測
- [生命週期管理](docs/zh-TW/lifecycle.md) - 生命週期事件系統的使用方法
- [路由管理器](docs/zh-TW/router.md) - HTTP 和 WebSocket 路由管理
- [HTTP 客戶端](docs/zh-TW/http-client.md) - 統一 HTTP 請求客戶端
- [MessageBuilder 詳解](docs/zh-TW/message-builder.md) - OneBot12 訊息段建構器的雙模式用法
- [SQL 查詢建構器](docs/zh-TW/sql-builder.md) - 通用 SQL 鏈式查詢建構器及儲存後端抽象
- [會話類型系統](docs/zh-TW/session-types.md) - 會話類型定義、映射與自訂類型註冊
- [Conversation 多輪對話](docs/zh-TW/conversation.md) - 多輪對話上下文的交互方法

> [!NOTE]
> Dashboard 視窗註冊、Takumi 圖片渲染等 **第三方生態模組** 的文件已遷移至 [生態模組](../ecosystem/README.md) 目錄。

請直接返回翻譯後的完整Markdown內容，不要包含任何其他文字。

## 適用對象

這些文件適合以下開發者：

- 已經熟悉 ErisPulse 基礎功能的開發者
- 需要深入理解框架內部機制的開發者
- 需要優化效能或實現複雜功能的開發者

## 前置知識

閱讀本目錄文件前，建議先了解：

- [基礎概念](../getting-started/basic-concepts.md)
- [事件處理入門](../getting-started/event-handling.md)
- [模組開發指南](../developer-guide/modules/)

請直接返回翻譯後的完整 Markdown 內容，不要包含任何其他文字。

再次提醒：如果文件包含語言切換行（各語言名稱用 `` | `` 分隔的行），務必嚴格遵守上方第 8 條的格式要求，不要寫出 ``[**標籤**](file)`` 這類錯誤格式。