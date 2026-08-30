# 進階主題

本目錄包含 ErisPulse 框架的高級特性和深入主題。

## 文件列表

- [啟動流程與手動控制](startup.md) - 啟動鏈路拆解（Finder/Loader/Manager/Router）與手動完整啟動
- [懶加載系統](lazy-loading.md) - 懶加載模組系統的工作原理、設定與事件驅動懶激活（activate_on）
- [模組作用域系統](scope.md) - 模組與適配器 Bot/平台的綁定與隔離
- [國際化 (i18n)](i18n.md) - 多語言支援、翻譯註冊與語言檢測
- [生命週期管理](lifecycle.md) - 生命週期事件系統的使用方法
- [路由管理器](router.md) - HTTP 和 WebSocket 路由管理
- [HTTP 客戶端](http-client.md) - 統一 HTTP 請求客戶端
- [MessageBuilder 詳解](message-builder.md) - OneBot12 消息段建構器的雙模式用法
- [SQL 查詢建構器](sql-builder.md) - 通用 SQL 串接查詢建構器及儲存後端抽象
- [會話類型系統](../standards/session-types.md) - 會話類型定義、映射與自訂類型註冊
- [Conversation 多輪對話](conversation.md) - 多輪對話上下文的互動方法

> [!NOTE]
> Dashboard 視窗註冊、Takumi 圖片渲染等 **第三方生態模組** 的文件已遷移至 [生態模組](../ecosystem/README.md) 目錄。

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

