# ErisPulse 文件

ErisPulse 是一個可擴展的多平台訊息處理框架，支援透過適配器與不同平台互動，提供靈活的模組系統用於功能擴展。

> **第一次使用？** 直接看 [5 分鐘快速入門](docs/zh-TW/quick-start.md) —— 從安裝到執行第一個機器人，一氣呵成。

## 選擇你的路徑

根據你的目標，選擇對應的學習路徑。每條路徑內部按由淺入深排列。

### 一、我要使用機器人

讓機器人跑起來、安裝模組、做設定。

| 進度 | 文件 | 說明 |
|------|------|------|
| **① 入門** | [5 分鐘快速上手](quick-start.md) | 安裝、初始化、運行 —— 唯一的起步入口 |
| App 直裝 | [ErisPulse-App 客戶端](ecosystem/app.md) | 官方全平台客戶端：手機 / 電腦圖形界面直接運行與管理，免終端 |
| ② 深入 | [建立第一個機器人](getting-started/first-bot.md) | 編寫第一個命令處理器 |
| ③ 概念 | [基礎概念](getting-started/basic-concepts.md) | 理解適配器/模組/事件的設計 |
| ④ 實戰 | [常見任務示例](getting-started/common-tasks.md) | 存儲、定時任務、權限控制 |
| 參考 | [設定檔說明](user-guide/configuration.md) · [CLI 命令](user-guide/cli-reference.md) · [部署指南](user-guide/deployment.md) | 按需查閱 |
| 參考 | [平台特性指南](platform-guide/README.md) | 各平台（雲湖/QQ/Telegram…）的差異 |

### 二、我要開發模組 / 適配器

為 ErisPulse 編寫可分發的擴展。

| 類型 | 入門 | 進階 |
|------|------|------|
| **模組開發**（推薦） | [模組開發入門](developer-guide/modules/getting-started.md) | [核心概念](developer-guide/modules/core-concepts.md) · [Event 包裝類](developer-guide/modules/event-wrapper.md) · [最佳實踐](developer-guide/modules/best-practices.md) |
| **適配器開發** | [適配器開發入門](developer-guide/adapters/getting-started.md) | [核心概念](developer-guide/adapters/core-concepts.md) · [SendDSL 詳解](developer-guide/adapters/send-dsl.md) · [事件轉換器](developer-guide/adapters/converter.md) · [最佳實踐](developer-guide/adapters/best-practices.md) |
| **技術標準** | [標準規範總覽](standards/README.md) | 適配器開發必須遵循的 [會話類型](standards/session-types.md) · [事件轉換](standards/event-conversion.md) · [發送方法](standards/send-method-spec.md) · [API 回應](standards/api-response.md) · [請求操作](standards/request-action-spec.md) 規範 |
| **發布** | [發布與模組商店](developer-guide/publishing.md) | 將作品發布到 PyPI 和模組商店 |

### 三、我要深入了解原理

了解框架內部如何運作。

| 文件 | 說明 |
|------|------|
| [架構概覽](architecture.md) | 可視化圖表：核心架構、初始化流程、事件處理、生命週期、模組加載策略（含 `activate_on` 事件驅動懶激活）、本地插件資料夾與模組熱重載架構（支援全部模組來源） |
| [啟動流程與手動控制](advanced/startup.md) | 啟動鏈路拆解、手動驅動各環節、加載失敗診斷 |
| [事件系統](api-reference/event-system.md) | 五大類事件的完整 API |
| [適配器系統](api-reference/adapter-system.md) | 適配器註冊、啟停、API 調用 |
| [核心模組](api-reference/core-modules.md) | Storage / Config / Logger / Router 等基礎能力 |
| [生命週期管理](advanced/lifecycle.md) · [懶加載](advanced/lazy-loading.md) · [路由系統](advanced/router.md) | 內部子系統 |
| [作用域（scope）](advanced/scope.md) | 三維作用域控制：模組可用性 / 事件准入 / 出站動作限制（含方法級細粒度規則、綁定繼承 merge） |
| [歸屬權（owner）系統](advanced/ownership.md) | 資源歸屬與自動回收：owner 上下文、歸屬資源全景、卸載清理序列、設計邊界與模組作者指南 |
| [Conversation 多輪對話](advanced/conversation.md) · [MessageBuilder](advanced/message-builder.md) · [SQL 構建](advanced/sql-builder.md) · [HTTP 客戶端](advanced/http-client.md) · [國際化](advanced/i18n.md) | 進階工具 |

### 四、生態與官方客戶端

官方客戶端 + 按需安裝、即裝即用的生態模組（都不是框架內建功能）。

| 文件 | 說明 |
|------|------|
| [生態總覽](ecosystem/README.md) | 如何安裝生態模組、為什麼這些不是內建功能 |
| [ErisPulse-App](ecosystem/app.md) | 官方全平台客戶端（Android / Windows / Linux / macOS）：原生界面管理多個實例，**手機直接運行**，桌面托盤常駐 |
| [ErisPulse-Dashboard](ecosystem/dashboard.md) | Web 管理面板 + 視窗註冊 API（模組可向側邊欄註冊自定義頁面） |
| [ErisPulse-Takumi](ecosystem/takumi.md) | 圖片渲染（HTML / 節點樹 / SVG / 動畫，內建中英文字型） |

### 五、我要為 ErisPulse 做貢獻

讓框架變得更好

| 文件 | 說明 |
|------|------|
| [為 ErisPulse 做貢獻](contributing/README.md) | 貢獻方式總覽：文件 / i18n / Bug / 模組 / 適配器 |
| [首次貢獻](contributing/first-contribution.md) | 從 fork 到提交 PR |

## 開發方式

ErisPulse 支援兩種開發方式：

- **模組開發（推薦）**：建立獨立的模組套件，透過套件管理工具安裝，便於分發與管理。
- **內嵌式開發**：直接在專案中編寫處理器，適合快速原型。詳見 [快速入門](docs/zh-TW/quick-start.md)。

## 其他

- [文件風格指南](styleguide/docstring.md) — 貢獻文件時的寫作規範
- [為 ErisPulse 貢獻](contributing/README.md) — 參與項目共建的入口
- [AI 輔助開發](ai-support/README.md) — 獲取供 AI 編程助手使用的專案提示詞

## 獲取幫助

- GitHub 倉庫：[https://github.com/ErisPulse/ErisPulse](https://github.com/ErisPulse/ErisPulse)
- 問題回報：提交 Issue
- 技術討論：查看 Discussions

## 相關連結

- [OneBot12 標準](https://12.onebot.dev/)
- [雲湖官方文件](https://www.yhchat.com/document/)
- [Telegram Bot API](https://core.telegram.org/bots/api)