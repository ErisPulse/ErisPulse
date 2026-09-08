# 高級主題

本目錄包含 ErisPulse 框架的高級特性與深入主題。

## 文件列表

- [啟動流程與手動控制](startup.md) - 啟動鏈路拆解（Finder/Loader/Manager/Router）與手動完整啟動
- [懶加載系統](lazy-loading.md) - 懶加載模組系統的工作原理、配置與事件驅動懶激活（activate_on）
- [作用域（scope）](scope.md) - 三維作用域控制：模組可用性 / 事件准入 / 出站動作限制（含方法級細粒度規則與綁定繼承 merge）
- [歸屬權（owner）系統](ownership.md) - 資源歸屬與自動回收：owner 上下文機制、歸屬資源全景、卸載清理序列與設計邊界
- [互動會話系統](interaction.md) - wait_reply / 會話定時器 / 多路等待 / 會話互斥租約 / 收件箱 / 消息事務 / 鏈路追蹤
- [模組間通訊](module-communication.md) - RPC 協定化（module.call）、服務契約與目錄、定向事件、冷啟動回放、事件冪等去重
- [國際化 (i18n)](i18n.md) - 多語言支援、翻譯註冊與語言檢測
- [生命週期管理](lifecycle.md) - 生命週期事件系統的使用方法
- [路由管理器](router.md) - HTTP 和 WebSocket 路由管理
- [HTTP 客戶端](http-client.md) - 統一 HTTP 請求客戶端
- [MessageBuilder 詳解](message-builder.md) - OneBot12 消息段建構器的雙模式用法
- [SQL 查詢建構器](sql-builder.md) - 通用 SQL 串鏈查詢建構器及儲存後端抽象
- [儲存後端](storage-backends.md) - sqlite / mysql / postgres 異步原生儲存後端的選擇、配置與切換
- [會話類型系統](../standards/session-types.md) - 會話類型定義、對應與自訂類型註冊
- [Conversation 多輪對話](conversation.md) - 多輪對話上下文的互動方法

> [!NOTE]
> Dashboard 視窗註冊、Takumi 圖片渲染等 **第三方生態模組** 的文件已遷移至 [生態模組](../ecosystem/README.md) 目錄。

## 適用對象

這些文件適合以下開發者：

- 已經熟悉 ErisPulse 基礎功能的開發者
- 需要深入理解框架內部機制的開發者
- 需要優化性能或實現複雜功能的開發者

## 預備知識

閱讀本目錄文件前，建議先了解：

- [基礎概念](../getting-started/basic-concepts.md)
- [事件處理入門](../getting-started/event-handling.md)
- [模組開發指南](../developer-guide/modules/)