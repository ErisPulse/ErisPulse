# 高級主題

本目錄收錄 ErisPulse 框架的進階專題——權限管控、灰度發布、多輪互動、儲存後端等
深度能力，每篇解決一類具體問題。

> [!NOTE]
> 本目錄全部為**按需查閱**的專題文件——請先讀完首頁的 L1 核心五篇，
> 遇到對應需求再來翻。每篇開頭標有「什麼時候需要讀這篇」。

## L2 必讀四篇

撰寫生產級模組時無法繞過的四篇，建議在製作複雜模組前通讀（語氣與文件首頁一致）：

- [作用域（scope）](scope.md) - 三維作用域控制：模組可用性 / 事件准入 / 出站動作限制（含方法級細粒度規則與綁定繼承 merge）
- [歸屬權（owner）系統](ownership.md) - 資源歸屬與自動回收：owner 上下文機制、歸屬資源全景、卸載清理序列與設計邊界
- [生命週期管理](lifecycle.md) - 生命週期事件系統：模組 / 適配器加載、卸載、重載、禁用時各自該做什麼
- [互動會話系統](interaction.md) - wait_reply / 會話定時器 / 多路等待 / 會話互斥租約 / 收件箱 / 消息事務 / 鏈路追蹤

## 按場景分組

與文件首頁「深入理解原理」的分組標準一致，每組首篇標註「不懂會踩什麼坑」。

**執行啟動** —— 不懂啟動鏈路（Finder / Loader / Manager / Router），模組加載失敗時只能對著日誌干瞪眼

- [啟動流程與手動控制](startup.md) - 啟動鏈路拆解（Finder/Loader/Manager/Router）與手動完整啟動
- [懶加載系統](lazy-loading.md) - 懶加載模組系統的工作原理、配置與事件驅動懶激活（activate_on）

**通信連接** —— 不懂服務契約（`meta.services`）白名單，跨模組 `module.call` 會被 `ServiceNotProvidedError` 拒絕且不知原因

- [模組間通信](module-communication.md) - RPC 協議化（module.call）、服務契約與目錄、定向事件、冷啟動回放、事件冪等去重
- [連接池與廣播](connections.md) - 連接註冊表：廣播、分組訂閱、跨模組傳遞與複用、連接池查看
- [路由管理器](router.md) - HTTP 和 WebSocket 路由管理（含單參數註冊、元組回應約定）

**數據存儲** —— 不懂連接失敗冷卻期語義，資料庫抖動時會誤判「框架掛了」（實際是快速失敗、冷卻後自動重連）

- [存儲後端](storage-backends.md) - sqlite / mysql / postgres 異步原生存儲後端的選擇、配置與切換
- [SQL 查詢建構器](sql-builder.md) - 通用 SQL 鏈式查詢建構器及存儲後端抽象
- [HTTP 客戶端](http-client.md) - 統一 HTTP 請求客戶端

**消息對話** —— 不懂會話互斥租約，兩個模組同時等同一用戶的回覆會互相踢掉

- [Conversation 多輪對話](conversation.md) - 多輪對話上下文的交互方法
- [會話收件箱](transcript.md) - 消息自動記錄：保留策略旋鈕、運行時覆蓋 API 與風險/審計
- [MessageBuilder 詳解](message-builder.md) - OneBot12 消息段建構器的雙模式用法
- [國際化 (i18n)](i18n.md) - 多語言支援、翻譯註冊與語言檢測

**灰度影子** —— 不懂五道隔離閘就提前轉正，影子的出站消息會外溢到真實用戶

- [影子模組與灰度轉正](shadow.md) - 模組新版本獨立 owner 並行試運行：出站攔截記帳、行為 diff 對比、promote 轉正與失敗回滾

**異常與規範參考**

- [異常體系與捕獲指南](errors.md) - 框架全部異常類型、發生位置與捕獲建議
- [會話類型系統](../standards/session-types.md) - 會話類型定義、映射與自定義類型註冊

> [!NOTE]
> Dashboard 視窗註冊、Takumi 圖片渲染等 **第三方生態模組** 的文件已遷移至 [生態模組](../ecosystem/README.md) 目錄。

## 適用對象

這些文件適合以下開發者：

- 已經熟悉 ErisPulse 基礎功能的開發者  
- 需要深入理解框架內部機制的開發者  
- 需要優化性能或實現複雜功能的開發者

## 前置知識

閱讀本目錄文件前，建議先了解：

- [基礎概念](../getting-started/basic-concepts.md)  
- [事件處理入門](../getting-started/event-handling.md)  
- [模組開發指南](../developer-guide/modules/)