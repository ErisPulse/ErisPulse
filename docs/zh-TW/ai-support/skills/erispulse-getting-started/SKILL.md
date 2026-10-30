---
name: erispulse-getting-started
description: "适用于：第一次接触 ErisPulse，想从零跑起一个机器人并理解核心概念。覆盖场景：[模組開發入門](developer-guide/modules/getting-started.md)。**1. 安裝**（Python >= 3.10）：。機器人已經能跑，想寫出第一個 `/hello` 命令處理器、搞懂 `sdk.run` 與命令裝飾器各自在做什麼。如果還沒裝好 ErisPulse、初始化專案，先完成 [5 分鐘快速開始](../quick-start.md) 的「安裝」「初始化專案」「執行專案」三步；不需要則跳過。一條訊息從使用者發出到機器人回覆，中間經過了哪些元件？配接器和模組各自負責什麼？讀完這篇，撰寫處理器時遇到的設計問題你都能自己回答，而不是只能照抄範例。想讓機器人響應訊息、命令、通知、請求，或要實現等待回覆 / 多輪對話、排查「命令為什麼沒觸發」時讀。只想了解框架設計，看 [基礎概念](basic-concepts.md) 即可；不需要則跳過。想給機器人加某個具體功能時按節查閱——持久化、定時任務、訊息過濾、權限控制、批次傳送，每一節都是可直接複製的完整範例。想系統學事件處理寫法先看 [事件處理入門](event-handling.md)；不需要則跳過。**何時需要閱讀本文**：當 IDE 補全無法顯示適配器的平台特定方法（如雲湖的 `Board`）或模組的自訂方法時，只需執行一條 `epsdk types` 命令生成類型存根即可解決；若不需要則可跳過。"
---

# ErisPulse 快速上手与核心概念

This skill is auto-built from the ErisPulse documentation.
Repository: https://github.com/ErisPulse/ErisPulse
Source paths are annotated per section; see docs/ in the repository for the latest content.

## 内容大纲

AI 按需读取：只读需要的章节即可，不必全文加载。

- 文档总入口与阅读路径: 81-91 行
- 選擇你的路徑: 93-209 行
- 高級特性版本速查表: 211-221 行
- 開發方式: 223-228 行
- 其他: 230-234 行
- 獲取幫助: 236-240 行
- 相關連結: 242-246 行
- 快速开始: 248-254 行
- 60 秒效果：先讓機器人回你一句話: 256-295 行
- 安裝 ErisPulse：三種方式: 297-362 行
- 初始化項目: 364-396 行
- 安裝模塊: 398-418 行
- 運行項目: 420-428 行
- 啟用 IDE 補全（可選）: 430-447 行
- 項目結構: 449-459 行
- 配置文件: 461-498 行
- 第一个机器人: 500-509 行
- 第一步：撰寫第一個命令: 511-558 行
- 第二步：執行機器人: 560-568 行
- 第三步：測試機器人: 570-578 行
- 代碼說明: 580-612 行
- 擴展：添加更多功能: 614-620 行
- 常見問題: 622-658 行
- 基础概念: 660-669 行
- 事件驅動架構: 671-709 行
- 核心元件: 711-833 行
- 事件類型: 835-847 行
- 核心模組說明: 849-951 行
- SendDSL 訊息傳送: 953-998 行
- 懶載入系統: 1000-1021 行
- 事件处理: 1023-1032 行
- 事件類型概覽: 1034-1044 行
- 消息事件處理: 1046-1118 行
- 命令事件處理: 1120-1510 行
- 中間件：分發前改寫或否決: 1512-1534 行
- 命令分發決策鏈：為什麼命令沒觸發: 1536-1542 行
- 作用域過濾：為什麼我的模組沒收到訊息: 1544-1577 行
- 事件覆寫：不改模組程式碼，覆寫任意事件類型的行為: 1579-1642 行
- 鏈路控制：認領與阻斷: 1644-1693 行
- 通知事件處理: 1695-1727 行
- 請求事件處理: 1729-1756 行
- 元事件處理: 1758-1805 行
- 互動式處理: 1807-2035 行
- 事件資料訪問: 2037-2112 行
- 事件處理最佳實踐: 2114-2165 行
- 常见任务: 2167-2174 行
- 內容清單: 2176-2186 行
- 數據持久化: 2188-2245 行
- 定時任務: 2247-2315 行
- 消息過濾: 2317-2356 行
- 多平台適配: 2358-2399 行
- 消息發送進階（重試/超時/批量）: 2401-2454 行
- 權限控制: 2456-2506 行
- 消息統計: 2508-2552 行
- 搜尋功能: 2554-2608 行
- 圖片處理: 2610-2673 行
- IDE 补全: 2675-2685 行
- 核心設計原則: 2687-2693 行
- 基本用法: 2695-2703 行
- 在程式碼中使用: 2705-2717 行
- 工作原理: 2719-2743 行
- 命令選項: 2745-2752 行
- 何時重新產生: 2754-2758 行
- 與 SendDSL 標準方法的關係: 2760-2764 行

## 文档总入口与阅读路径

> 来源: `docs/zh-TW/README.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-TW/README.md）

# ErisPulse 文件

ErisPulse 是事件驅動的模組化非同步機器人框架——業務程式碼只寫一次，透過適配器部署到 QQ、Telegram、Kook、雲湖等多個平台，插件系統、熱重載與完整的開發者工具鏈開箱即用。

> **第一次使用？** 直接看 [5 分鐘快速入門](docs/zh-TW/quick-start.md) —— 從安裝到執行第一個機器人，一氣呵成。

---

## 選擇你的路徑

根據你的目標，選擇對應的學習路徑。每條路徑內部按由淺入深排列。

> [!IMPORTANT]
> **不需要讀完所有文件。** 絕大多數開發者只需按順序讀完 **L1 核心五篇**
> （約 1–2 小時）即可獨立開發 90% 的功能；其餘文件全部是特定場景的按需
> 查閱資料——遇到對應需求再來翻，每篇開頭都標了"什麼時候需要讀這篇"。
>
> **L1 核心五篇**：[模組開發入門](developer-guide/modules/getting-started.md)
> → [基礎概念](getting-started/basic-concepts.md)
> → [Event 包裝類](developer-guide/modules/event-wrapper.md)
> → [配置文件說明](user-guide/configuration.md)
> → [異常捕獲](advanced/errors.md)
>
> 適配器作者另需：[適配器開發入門](developer-guide/adapters/getting-started.md)
> → [事件轉換器](developer-guide/adapters/converter.md)
> → [SendDSL 詳解](developer-guide/adapters/send-dsl.md)

### 一、我要使用機器人

讓機器人跑起來、裝模組、做配置。

| 進度 | 文件 | 說明 |
|------|------|------|
| **① 上手** | [5 分鐘快速開始](quick-start.md) | 安裝、初始化、運行 —— 唯一的起步入口 |
| App 直裝 | [ErisPulse-App 客戶端](ecosystem/app.md) | 官方全平台客戶端：手機 / 電腦圖形界面直接運行與管理，免終端 |
| ② 深入 | [建立第一個機器人](getting-started/first-bot.md) | 編寫第一個命令處理器 |
| ③ 概念 | [基礎概念](getting-started/basic-concepts.md) | 理解適配器/模組/事件的設計 |
| ④ 實戰 | [常見任務示例](getting-started/common-tasks.md) | 存儲、定時任務、權限控制 |
| 參考 | [配置文件說明](user-guide/configuration.md) · [CLI 命令](user-guide/cli-reference.md) · [部署指南](user-guide/deployment.md) | 按需查閱 |
| 參考 | [平台特性指南](platform-guide/README.md) | 各平台（雲湖/QQ/Telegram…）的差異 |
| 選型 | [選型指南](showcase/README.md) | 和 NoneBot2 / AstrBot / LangBot 的對比與遷移 |

### 二、我要開發模組 / 適配器

為 ErisPulse 編寫可分發的擴展。

| 類型 | 入門 | 進階 |
|------|------|------|
| **模組開發**（推薦） | [模組開發入門](developer-guide/modules/getting-started.md) | [核心概念](developer-guide/modules/core-concepts.md) · [Event 包裝類](developer-guide/modules/event-wrapper.md) · [最佳實踐](developer-guide/modules/best-practices.md) |
| **適配器開發** | [適配器開發入門](developer-guide/adapters/getting-started.md) | [核心概念](developer-guide/adapters/core-concepts.md) · [SendDSL 詳解](developer-guide/adapters/send-dsl.md) · [事件轉換器](developer-guide/adapters/converter.md) · [最佳實踐](developer-guide/adapters/best-practices.md) |
| **技術標準** | [標準規範總覽](standards/README.md) | 適配器開發必須遵循的 [會話類型](standards/session-types.md) · [事件轉換](standards/event-conversion.md) · [發送方法](standards/send-method-spec.md) · [API 回應](standards/api-response.md) · [請求操作](standards/request-action-spec.md) 規範 |
| **測試與排查** | [模組測試（ErisPulse-Testing）](developer-guide/testing.md) | 分發決策鏈排查"命令為什麼沒觸發" |
| **發布** | [發布與模組商店](developer-guide/publishing.md) | 將作品發布到 PyPI 和模組商店 |

### 三、我要深入理解原理

了解框架內部如何運作。先看架構與 API 參考，再按下面對照表進入專題。

**架構與 API 參考**

| 文件 | 說明 |
|------|------|
| [架構概覽](architecture.md) | 可視化圖表：核心架構、初始化流程、事件處理、生命週期、模組加載策略（含 `activate_on` 事件驅動懶加載）、本地插件文件夾與模組熱重載架構（支援全部模組來源） |
| [事件系統](api-reference/event-system.md) | 五大類事件的完整 API |
| [適配器系統](api-reference/adapter-system.md) | 適配器註冊、啟停、API 調用 |
| [核心模組](api-reference/core-modules.md) | Storage / Config / Logger / Router 等基礎能力 |

**L2 必讀（寫生產級模組繞不開）**

| 文件 | 說明 |
|------|------|
| [作用域（scope）](advanced/scope.md) | 三維作用域控制：模組可用性 / 事件准入 / 出站動作限制（含方法級細粒度規則、綁定繼承 merge） |
| [歸屬權（owner）系統](advanced/ownership.md) | 資源歸屬與自動回收：owner 上下文、歸屬資源全景、卸載清理序列、設計邊界與模組作者指南 |
| [生命週期管理](advanced/lifecycle.md) | 生命週期事件系統：模組 / 適配器加載、卸載、重載、禁用時各自該做什麼 |
| [互動會話系統](advanced/interaction.md) | wait_reply 全解、會話計時器（remind/escalate）、多路等待（select）、會話互斥租約、收件箱、消息事務、鏈路追蹤 |

**按場景分組（按需查閱）**

| 分組 | 文件 | 不懂首篇會踩的坑 |
|------|------|------|
| 運行啟動 | [啟動流程與手動控制](advanced/startup.md) · [懶加載](advanced/lazy-loading.md) | 不懂啟動鏈路（Finder / Loader / Manager / Router），模組加載失敗時只能對著日誌干瞪眼 |
| 通信連接 | [模組間通信](advanced/module-communication.md) · [連接池與廣播](advanced/connections.md) · [路由系統](advanced/router.md) | 不懂服務契約（`meta.services`）白名單，跨模組 `module.call` 會被 `ServiceNotProvidedError` 拒絕且不知原因 |
| 數據存儲 | [存儲後端](advanced/storage-backends.md) · [SQL 構建](advanced/sql-builder.md) · [HTTP 客戶端](advanced/http-client.md) | 不懂連接失敗冷卻期語義，數據庫抖動時會誤判"框架掛了"（實際是存儲操作快速失敗、冷卻後自動重連） |
| 消息對話 | [Conversation 多輪對話](advanced/conversation.md) · [會話收件箱](advanced/transcript.md) · [MessageBuilder](advanced/message-builder.md) · [國際化](advanced/i18n.md) | 不懂會話互斥租約，兩個模組同時等同一用戶的回覆會互相踢掉 |
| 灰度影子 | [影子模組與灰度轉正](advanced/shadow.md) | 不懂五道隔離閘就提前轉正，影子的出站消息會外溢到真實用戶 |

**概念關係總表**

分不清哪個子系統管什麼時，按這張表對號入座：

| 子系統 | 回答什麼問題 | 一句話口訣 |
|--------|------------|-----------|
| [通信](advanced/module-communication.md)（module-communication） | 模組之間怎麼互相調用、怎麼定向發事件？ | 跨模組走 `module.call`；對方聲明了 `meta.services` 就只能調白名單內的方法 |
| [權限](advanced/scope.md)（scope） | 誰能用這個模組、誰能觸發事件、能執行哪些動作？ | 三道閘——模組綁定、身份准入、出站限制，全部由用戶配置說了算 |
| [歸屬](advanced/ownership.md)（ownership） | 模組卸載後，它開的連接、定時器、訂閱去哪了？ | 誰註冊誰歸屬，卸載即回收，不留懸掛資源 |
| [懶加載與休眠](advanced/lazy-loading.md)（lazy-loading） | 模組什麼時候才真正加載、閒置後去哪？ | `activate_on` 用到才醒，`dormant_after` 閒置歸眠 |
| [互動](advanced/interaction.md)（interaction） | 怎麼等用戶下一條回覆、多輪收集怎麼寫？ | `wait_reply` 等一條、`.got()` 鏈收多輪，租約保證不打架 |
| [影子灰度](advanced/shadow.md)（shadow） | 新版模組怎麼在不影響線上的情況下試運行？ | 影子收副本、出站只記賬，`promote` 由人確認才轉正 |
| [存儲](advanced/storage-backends.md)（storage-backends） | 數據存哪、後端怎麼換？ | 同一套存儲 API，sqlite / mysql / postgres 配置切換 |

### 四、生態與官方客戶端

官方客戶端 + 按需安裝、即裝即用的生態模組（都不是框架內建功能）。

| 文件 | 說明 |
|------|------|------|
| [生態總覽](ecosystem/README.md) | 如何安裝生態模組、為什麼這些不是內建功能 |
| [ErisPulse-QvQChat](ecosystem/qvqchat.md) | 通用智能體模組：工具循環 / MCP / 長期記憶 / 知識庫，聲明服務的模組自動成為 AI 工具 |
| [ErisPulse-ApiMCP](ecosystem/apimcp.md) | 把機器人反向開放為 MCP 工具，讓 Claude 等 AI 客戶端直接操控 |
| [ErisPulse-App](ecosystem/app.md) | 官方全平台客戶端（Android / Windows / Linux / macOS）：原生界面管理多個實例，**手機直接運行**，桌面托盤常駐 |
| [ErisPulse-Dashboard](ecosystem/dashboard.md) | Web 管理面板 + 視窗註冊 API（模組可向側邊欄註冊自定義頁面） |
| [ErisPulse-Cron](ecosystem/cron.md) | 定時任務調度模組：一次性 / 間隔 / Cron 表達式，回調傳參，SQLite 持久化，其他模組可托管定時回調 |
| [ErisPulse-Takumi](ecosystem/takumi.md) | 圖片渲染（HTML / 節點樹 / SVG / 動畫，內置中英文字體） |

### 五、我要為 ErisPulse 貢獻

讓框架更好

| 文件 | 說明 |
|------|------|------|
| [為 ErisPulse 貢獻](contributing/README.md) | 貢獻方式總覽：文件 / i18n / Bug / 模組 / 適配器 |
| [首次貢獻](contributing/first-contribution.md) | 從 fork 到提交 PR |

---
[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | [Русский](README.ru.md)

## 高級特性版本速查表

在進行版本相容性判斷，或接手舊項目時想要知道「這個功能是哪個版本引入的」，可依照此表對號入座（以倉庫根目錄 [CHANGELOG.md](https://github.com/ErisPulse/ErisPulse/blob/main/CHANGELOG.md) 各版本條目為準）。

| 版本 | 引入的功能 |
|------|-----------|
| **2.7** | 生產化基座：OneBot12 標準化基類（`ApiDSL` / `BaseConverter`）、配置熱更新系統化、優雅關閉與 SIGTERM/SIGHUP 信號處理、環境變數配置覆蓋、生命週期回調鉤子、Web 栈懶加載；2.7.1 修補配置寫入可靠性和 GC 分代治理 |
| **2.8** | 權限與通信骨架：作用域三維體系（scope）、交互會話基礎設施（租約 / 檢查點 / 消息事務 / 會話收件箱 transcript）、模組間 RPC 協議化（`module.call` / `meta.services` 服務契約 / 定向事件 emit(to=)）、多後端異步存儲（sqlite / mysql / postgres，連接失敗不阻塞框架）、歸屬權清理、配置註釋保留；2.8.x 後續版本為 CLI 腳手架、子命令等打磨 |
| **2.9** | 「模組開發體驗」主線（EPRFC-2026-001）：宣告式命令參數（`args=` / `options=`）與命令治理（`cooldown=` / `rate_limit=`）、統一依賴注入（`Depends`）、中間件事件否決權、內建 ORM（自動遷移 + 關係映射）、影子模組灰度轉正、分發決策鏈追蹤與排查診斷、正式支援 Python 3.14 |
| **2.10** | 連接一等資源（`connections` 註冊表：廣播 / 業務分組 / 跨模組傳遞複用 / 卸載自動回收）、根導入契約（常用 API 全部可 `from ErisPulse import`）、歸屬權體系補全、收件箱保留策略執行時覆蓋；2.10.2 適配器本地插件目錄（`plugins/`）+ `epsdk create pack` + tomlclass 無損配置寫入 |
| **2.11**（dev） | 「改代碼 → 看效果」開發閉環：熱重載預設全量語義（語法預檢 + 代碼身份核對 + 依賴者級聯重導）、懶加載休眠（`dormant_after`）、適配器代碼級熱重載（`sdk.adapter.reload`）、`.got()` 命令流語法糖、`epsdk stop` / `restart` 運行時控制 |

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

## 快速开始

> 来源: `docs/zh-TW/quick-start.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-TW/quick-start.md）

# 快速入門

> **這是你的第一步。** 在 5 分鐘內從零開始運行一個 ErisPulse 机器人——先看效果，再逐步深入每一步。

## 60 秒效果：先讓機器人回你一句話

**1. 安裝**（Python >= 3.10）：

```bash
pip install ErisPulse
```

**2. 初始化項目**。向導會讓你設定項目名、選擇要接入的平台適配器並完成配置，然後生成 `main.py` 和 `config/config.toml`：

```bash
epsdk init
```

**3. 打開 `main.py`，替換為這 9 行程式碼**：

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("ping", help="測試機器人是否在線")
async def ping_handler(event):
    await event.reply("Pong！機器人運行正常。")

if __name__ == "__main__":
    import asyncio
    asyncio.run(sdk.run(keep_running=True))
```

**4. 運行**：

```bash
epsdk run main.py
```

終端會輸出框架啟動日誌和適配器的連接資訊。這時在你接入的平台裡給機器人發 `/ping`，它會回覆：

> Pong！機器人運行正常。

看到這條回覆，說明框架、適配器、事件處理這條鏈路已經打通。沒跑通？直接翻到文末[遇到問題](#遇到問題)；跑通了，往下看每一步還有哪些選擇。

## 安裝 ErisPulse：三種方式

上面使用的是最直接的 pip。根據您的環境選擇：

### 使用 pip 安裝

確保您的 Python 版本 >= 3.10，然後使用 pip 安裝：

```bash
pip install ErisPulse
```

如果您已安裝 [uv](https://github.com/astral-sh/uv)，也可以使用 `uv pip install ErisPulse`，安裝速度更快。

如果您只想將 `epsdk` 命令行工具安裝到全域、不污染項目環境，推薦使用 `uv tool install`：

```bash
uv tool install ErisPulse
```

安裝後 `epsdk` 全域可用：在項目目錄內運行時會自動感知項目 `.venv`（`epsdk install` 裝進項目環境、`epsdk run` 用項目環境運行），框架本體由工具環境提供。詳見[安裝參考](user-guide/installation.md)。

### 一鍵安裝腳本（新環境推薦）

安裝腳本會自動檢測您的環境（Docker、Python、uv），並引導您選擇最適合的安裝方式，支援多語言（中文/English/日本語/Русский/繁體中文）。

Windows (PowerShell):
```powershell
irm https://get.erisdev.com/install.ps1 -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1
```

macOS / Linux:
```bash
curl -fsSL https://get.erisdev.com/install.sh -o install.sh && chmod +x install.sh && ./install.sh
```

腳本會引導您完成：

- **Docker 安裝**（檢測到 Docker 時推薦）：選擇鏡像源（Docker Hub / GHCR）、版本通道（穩定版 / 預發布版）、Dashboard 管理面板配置、端口設定
- **全域 CLI 安裝（uv tool，推薦）**：將 `epsdk` 安裝為全域命令，無需虛擬環境，uv 自動管理 Python（系統版本過低亦可）；項目目錄內運行時自動感知項目 `.venv`
- **傳統安裝**：自動建立虛擬環境、選擇 ErisPulse 版本、可選安裝 Dashboard 管理面板模組

### 使用 Docker

Docker 鏡像已內建 ErisPulse 框架和 Dashboard 管理面板，支援 `linux/amd64` 和 `linux/arm64` 架構。

```bash
# 下載 docker-compose.yml
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# 設定 Dashboard 令牌並啟動
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

<details>
<summary>Docker Hub 不可用？</summary>

使用 GitHub Container Registry 鏡像，修改 `docker-compose.yml` 中的 image：

```yaml
image: ghcr.io/erispulse/erispulse:latest
```

</details>

啟動後訪問 `http://<host>:8000/Dashboard`，使用設定的令牌登入。

## 初始化項目

### 交互式初始化（推薦）

```bash
epsdk init
```

這將啟動一個交互式向導，引導您完成：
- 項目名稱設置
- 日誌級別配置
- 伺服器配置（主機和端口）
- 適配器選擇和配置
- 項目結構創建

### 快速初始化

```bash
# 指定項目名稱的快速模式
epsdk init -q -n my_bot

# 或者只指定項目名稱
epsdk init -n my_bot
```

### 手動創建項目

如果更喜歡手動創建項目：

```bash
mkdir my_bot && cd my_bot
epsdk init
```

## 安裝模塊

### 通過 CLI 安裝

```bash
epsdk install Yunhu AIChat
```

### 查看可用模塊

```bash
epsdk list-remote
```

### 交互式安裝

不指定包名時進入交互式安裝界面：

```bash
epsdk install
```

## 運行項目

```bash
# 普通運行
epsdk run main.py

# 熱重載模式（開發時推薦）
epsdk run main.py --reload
```

## 啟用 IDE 補全（可選）

ErisPulse 動態發現模塊/適配器，IDE 默认無法補全平台特有方法。  
運行以下命令生成類型存根：

```bash
epsdk types
```

生成後用導入的類型作為變量標註即可獲得精確補全（詳見 [IDE 補全指南](./getting-started/ide-completion.md)）：

```python
from _ep_types import Yunhu
from ErisPulse import sdk

adapter: Yunhu = sdk.adapter.get("yunhu")
await adapter.Send.To("group", "123").Board(...)  # 補全平台特有方法
```

## 項目結構

初始化後的項目結構：

```
my_bot/
├── config/
│   └── config.toml          # 配置文件
└── main.py                  # 入口文件

```

## 配置文件

基本的 `config.toml` 配置：

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000

[ErisPulse.logger]
level = "INFO"

[Yunhu_Adapter]
# 適配器配置
```

### 想做群組機器人（處理訊息、群組管理、通知）

- [事件處理入門](getting-started/event-handling.md) — 訊息、通知、請求事件的寫法
- [常見任務範例](getting-started/common-tasks.md) — 儲存、定時任務、權限控制

### 想寫自己的模組 / 適配器

- [基礎概念](getting-started/basic-concepts.md) — 先理解適配器 / 模組 / 事件 的設計
- [模組開發入門](developer-guide/modules/getting-started.md)
- [適配器開發入門](developer-guide/adapters/getting-started.md)
- [架構概覽](architecture.md) — 可視化架構圖

### 想讓機器人長期運行

- [部署指南](user-guide/deployment.md)
- [設定檔說明](user-guide/configuration.md)

### 遇到問題

- [建立第一個機器人](getting-started/first-bot.md) — 第一個機器人的逐步詳解
- [啟動流程與手動控制](advanced/startup.md) — 模組 / 適配器載入失敗的診斷
- [CLI 命令參考](user-guide/cli-reference.md) — `epsdk` 全部子命令

## 第一个机器人

> 来源: `docs/zh-TW/getting-started/first-bot.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-TW/getting-started/first-bot.md）

# 建立第一個機器人

> [!TIP]
> **什麼時候需要讀這篇**：機器人已經能跑，想寫出第一個 `/hello` 命令處理器、搞懂 `sdk.run` 與命令裝飾器各自在做什麼。如果還沒裝好 ErisPulse、初始化專案，先完成 [5 分鐘快速開始](../quick-start.md) 的「安裝」「初始化專案」「執行專案」三步；不需要則跳過。

跑通快速開始只是第一步——這篇帶你寫出第一個命令處理器，並解釋每一行程式碼在框架裡發生了什麼。

## 第一步：撰寫第一個命令

開啟 `main.py`，撰寫一個簡單的命令處理器：

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("hello", help="發送問候訊息")
async def hello_handler(event):
    """處理 hello 命令"""
    user_name = event.get_user_nickname() or "朋友"
    await event.reply(f"你好，{user_name}！我是 ErisPulse 機器人。")

@command("ping", help="測試機器人是否在線")
async def ping_handler(event):
    """處理 ping 命令"""
    await event.reply("Pong！機器人運行正常。")

async def main():
    """主入口函數"""
    print("正在啟動 ErisPulse...")
    
    # keep_running=True（預設）：框架阻塞維持運行，直到收到關閉訊號（如 Ctrl+C）
    await sdk.run(keep_running=True)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### `keep_running` 參數

`sdk.run(keep_running)` 控制框架是否阻塞維持運行：

- **`keep_running=True`（預設）**：`run()` 會一直阻塞，直到收到關閉訊號（如 Ctrl+C），適合純 bot 應用。
- **`keep_running=False`**：`run()` 初始化完成後立即返回，**框架並不會卸載**——已啟動的適配器/模組仍作為背景任務繼續處理訊息事件，你可以接著執行自己的邏輯，直到事件迴圈結束框架才隨之關閉。例如：

```python
async def main():
    await sdk.run(keep_running=False)   # 初始化後立即返回
    # 框架已在背景運行，這裡可以繼續做別的事
    while True:
        await asyncio.sleep(3600)
        print("每小時檢查一次")
```

> 除了 `run()` 的兩種模式，還有 `init()`/`uninit()` 手動控制生命週期、單獨啟停適配器/路由等更精細的方式，請參閱 [啟動流程與手動控制](../advanced/startup.md)。

## 第二步：執行機器人

```bash
# 普通執行
epsdk run main.py

# 開發模式（支援熱重載）
epsdk run main.py --reload
```

## 第三步：測試機器人

在你的聊天平台中發送命令：

```
/hello
```

你應該會收到機器人的回覆。

## 代碼說明

### 命令裝飾器

```python
@command("hello", help="發送問候訊息")
```

- `hello`：命令名稱，使用者透過 `/hello` 呼叫
- `help`：命令幫助說明，在 `/help` 命令中顯示

### 事件參數

```python
async def hello_handler(event):
```

`event` 參數是一個 Event 物件，包含：
- 消息內容：`event.get_text()`
- 發送者資訊：`event.get_user_id()`、`event.get_user_nickname()`
- 平台資訊：`event.get_platform()`
- 群組資訊：`event.get_group_id()`
- 原始資料：`event.get_raw()`

> 完整的 Event 物件方法請參考 [Event 包裝類詳解](../developer-guide/modules/event-wrapper.md)。

### 發送回覆

```python
await event.reply("回覆內容")
```

`event.reply()` 是一個便捷方法，用於向發送者發送訊息。

## 擴展：添加更多功能

ErisPulse 提供了豐富的事件處理和數據處理能力：

- **消息監聽**：使用 `@message.on_message()` 監聽各類消息 → [事件處理入門](event-handling.md)
- **通知監聽**：使用 `@notice.on_friend_add()` 等監聽系統通知 → [事件處理入門](event-handling.md)
- **數據存儲**：使用 `sdk.storage.get/set` 持久化數據 → [常見任務示例](common-tasks.md)

## 常見問題

### 命令沒有響應？

1. 檢查適配器是否正確配置，確認 `config/config.toml` 中適配器的 `status` 為 `true`
2. 查看終端日誌輸出，確認是否有錯誤資訊（特別是 `ERROR` 級別日誌）
3. 確認命令前綴是否正確（預設是 `/`），可在設定檔中查看 `[ErisPulse.event.command]` 部分
4. 確認命令名稱拼寫正確，注意大小寫敏感性設定

### 如何修改命令前綴？

在 `config.toml` 中添加：

```toml
[ErisPulse.event.command]
prefix = "!"
case_sensitive = false
```

### 如何支援多平台？

ErisPulse 使用 OneBot12 標準統一了不同平台的事件格式，`@command` 和 `@message` 註冊的處理器會自動接收所有平台的事件。透過 `event.get_platform()` 可以區分來源平台：

```python
@command("hello")
async def hello_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        await event.reply("你好！來自雲湖")
    elif platform == "telegram":
        await event.reply("Hello! From Telegram")
    else:
        await event.reply("你好！")
```

> 更多多平台適配技巧請參考 [常見任務範例](common-tasks.md#多平台適配)。

## 基础概念

> 来源: `docs/zh-TW/getting-started/basic-concepts.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-TW/getting-started/basic-concepts.md）

# 基礎概念

> [!NOTE]
> **L1 核心必讀**——文件首頁「L1 核心五篇」中的第 2 篇（模組開發入門 → **基礎概念** → Event 包裝類別 → 設定檔說明 → 例外捕捉）。

一條訊息從使用者發出到機器人回覆，中間經過了哪些元件？配接器和模組各自負責什麼？讀完這篇，撰寫處理器時遇到的設計問題你都能自己回答，而不是只能照抄範例。

## 事件驅動架構

ErisPulse 採用事件驅動架構，所有的互動都透過事件來傳遞和處理。

### 事件流程

```
使用者傳送訊息
      │
      ▼
平台接收
      │
      ▼
配接器接收平台原生事件
      │
      ▼
轉換為 OneBot12 標準事件
      │
      ▼
提交到事件系統
      │
      ▼
分發給已註冊的處理器
      │
      ▼
模組處理事件
      │
      ▼
透過配接器傳送回應
      │
      ▼
平台顯示給使用者
```

### OneBot12 標準

ErisPulse 使用 OneBot12 作為核心事件標準。OneBot12 是一個通用的聊天機器人應用程式介面標準，定義了統一的事件格式。

所有配接器都會將平台特定的事件轉換為 OneBot12 格式，確保程式碼的一致性。

## 核心元件

### 1. SDK 物件

SDK 是所有功能的統一進入點，提供對核心元件的存取。

```python
from ErisPulse import sdk

# 存取核心模組
sdk.storage    # 儲存系統
sdk.config     # 設定系統
sdk.logger     # 日誌系統
sdk.adapter    # 配接器系統
sdk.module     # 模組系統
sdk.router     # 路由系統
sdk.client     # HTTP 用戶端
sdk.lifecycle  # 生命週期系統
```

> [!WARNING]
> **統一從根匯入**：`from ErisPulse.Core import adapter` / `import ErisPulse.Core.adapter`
> 這類寫法綁定到的是**管理器實例**（`AdapterManager` 單例）而非子模組——`ErisPulse.Core`
> 套件的 re-export 會遮蔽同名子模組。撰寫測試、patch 或需要模組物件本身時，請一律使用
> `from ErisPulse import sdk` 根匯入（`sdk.adapter` 即管理器實例）。

### 2. Event 物件

Event 物件封裝了事件資料，提供了便捷的存取方法。

```python
@command("info")
async def info_handler(event):
    # 取得事件資訊
    event_id = event.get_id()
    user_id = event.get_user_id()
    platform = event.get_platform()
    text = event.get_text()
    
    # 傳送回覆
    await event.reply(f"使用者: {user_id}, 平台: {platform}")
```

### 3. 配接器

配接器是 ErisPulse 與外部平台之間的橋樑。

**職責：**
- 接收平台原生事件
- 轉換為 OneBot12 標準格式
- 將標準格式事件傳送到平台

**範例配接器：**
- Yunhu 配接器：與雲湖平台通訊
- Telegram 配接器：與 Telegram Bot API 通訊
- OneBot11 配接器：與 OneBot11 相容的應用程式通訊
- Email 配接器：處理郵件收發

### 4. 模組

模組是功能擴充的基本單位，可以：

- 註冊事件處理器
- 實作業務邏輯
- 呼叫配接器傳送訊息
- 使用核心模組提供的服務

#### 模組發現機制

ErisPulse 透過 Python 的 `importlib.metadata.entry_points` 發現已安裝的模組。模組在 `pyproject.toml` 中宣告進入點：

```toml
[project.entry-points."erispulse.module"]
MyModule = "my_package:Main"
```

SDK 初始化時會掃描所有 `erispulse.module` 群組的進入點，將模組類別註冊到 `ModuleManager`，然後按依賴關係進行拓撲排序後依序初始化。

#### 最小可用模組

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse import sdk

class Main(BaseModule):
    def __init__(self):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("MyModule")

    async def on_load(self, event):
        self.logger.info("模組已載入")

    async def on_unload(self, event):
        self.logger.info("模組已卸載")
```

#### 模組生命週期

- **註冊**：SDK 發現模組類別並註冊到管理器
- **載入**：建立模組實例，呼叫 `on_load(event)`（`event = {"module_name": "MyModule"}`）
- **卸載**：呼叫 `on_unload(event)`，清理資源

#### 載入策略

透過 `get_load_strategy()` 宣告模組的載入行為：

```python
from ErisPulse.loaders import ModuleLoadStrategy

class Main(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(
            lazy_load=True,   # 是否懶載入（預設 True）
            priority=0        # 載入優先級，數值越大越先初始化
        )
```

- **`lazy_load=True`（預設）**：模組在首次被 `sdk.MyModule` 存取時才初始化，減少啟動時間
- **`lazy_load=False`**：SDK 啟動時立即初始化，適合需要監聽生命週期事件或執行定時任務的模組
- **`priority`**：同優先級的模組按註冊順序載入；數值越大越先初始化

> 詳細的懶載入機制說明請參考 [懶載入系統](../advanced/lazy-loading.md)。

## 事件類型

ErisPulse 支援 5 類事件：

| 事件類型 | 裝飾器 | 說明 |
|---------|--------|------|
| 訊息事件 | `@message.on_message()` | 使用者傳送的任何訊息（私聊、群聊） |
| 命令事件 | `@command("name")` | 以命令前綴開頭的訊息（如 `/hello`） |
| 通知事件 | `@notice.on_friend_add()` 等 | 系統通知（好友新增、群成員變化等） |
| 請求事件 | `@request.on_friend_request()` 等 | 使用者請求（好友請求、群邀請） |
| 元事件 | `@meta.on_connect()` 等 | 系統級事件（連線、斷線、心跳） |

> 各事件類型的詳細用法和程式碼範例請參考 [事件處理入門](event-handling.md)。

## 核心模組說明

### Storage（儲存）

基於 SQLite 的鍵值儲存系統，用於持久化資料。

```python
# 設定值
sdk.storage.set("key", "value")

# 取得值
value = sdk.storage.get("key", "default_value")

# 批次操作
sdk.storage.set_multi({
    "key1": "value1",
    "key2": "value2"
})

# 交易
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
```

### Config（設定）

TOML 格式的設定檔管理。

```python
# 取得設定
config = sdk.config.getConfig("MyModule", {})

# 設定組態
sdk.config.setConfig("MyModule", {"key": "value"})

# 讀取巢狀設定
value = sdk.config.getConfig("MyModule.subkey", "default")
```

### Logger（日誌）

模組化日誌系統。

```python
# 記錄日誌
sdk.logger.info("這是一條資訊")
sdk.logger.warning("這是一條警告")
sdk.logger.error("這是一條錯誤")

# 取得子日誌記錄器
child_logger = sdk.logger.get_child("submodule")
child_logger.info("子模組日誌")
```

**屬性存取語法糖**

除了使用 `get_child()` 方法外，你還可以透過**屬性存取**的方式建立子logger，這是一種更簡潔的**語法糖**寫法：

```python
# 透過屬性存取建立子logger
sdk.logger.mymodule.info("模組訊息")

# 支援巢狀存取
sdk.logger.mymodule.database.info("資料庫訊息")
```

### Router（路由）

HTTP 和 WebSocket 路由管理，基於 FastAPI + Uvicorn。支援裝飾器路由、中介軟體、分組、限流、CORS。

```python
from ErisPulse.Core import HttpRequest

@sdk.router.get("MyModule", "/api")
async def handler(request: HttpRequest):
    data = await request.json()
    return {"status": "ok"}
```

> 完整的路由 API（WebSocket、中介軟體、速率限制、CORS 等）請參考 [路由管理器](../advanced/router.md)。

### Client（網路用戶端）

統一的網路用戶端，聚合了 HTTP 請求、WebSocket 連線、連線池管理、自動重試、逾時控制、請求統計和生命週期事件整合。

```python
from ErisPulse.Core import client

# HTTP 請求
resp = await client.get("https://api.example.com/users")
data = await resp.json()

# 帶重試和逾時
resp = await client.get(url, timeout=30, max_retries=3)

# WebSocket 連線
ws = await client.ws_connect("wss://example.com/ws")
async for text in ws.iter_text():
    await ws.send_text(f"Echo: {text}")
```

> 完整的網路用戶端 API 請參考 [網路用戶端](../advanced/http-client.md)。

## SendDSL 訊息傳送

配接器提供鏈式呼叫的訊息傳送介面。

### 基礎傳送

```python
# 取得配接器實例
yunhu = sdk.adapter.get("yunhu")

# 傳送訊息
await yunhu.Send.To("user", "U1001").Text("Hello")

# 指定傳送帳號
await yunhu.Send.Using("bot1").To("group", "G1001").Text("群訊息")
```

### 鏈式修飾

```python
# @使用者
await yunhu.Send.To("group", "G1001").At("U2001").Text("@訊息")

# 回覆訊息
await yunhu.Send.To("group", "G1001").Reply("msg123").Text("回覆")

# @全體
await yunhu.Send.To("group", "G1001").AtAll().Text("公告")
```

### Event 回覆方法

Event 物件提供了便捷的回覆方法：

```python
@command("test")
async def test_handler(event):
    # 簡單文字回覆
    await event.reply("回覆內容")
    
    # 傳送圖片
    await event.reply("http://example.com/image.jpg", method="Image")
    
    # 傳送語音
    await event.reply("http://example.com/voice.mp3", method="Voice")
```

## 懶載入系統

ErisPulse 預設啟用模組懶載入，模組只在首次被存取（如 `sdk.MyModule`）時才初始化，顯著提高啟動速度。

```python
from ErisPulse.loaders import ModuleLoadStrategy

class Main(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(
            lazy_load=True,   # 啟用懶載入（預設）
            priority=0        # 載入優先級，數值越大越先初始化
        )
```

**需要停用懶載入的場景（`lazy_load=False`）：**
- 監聽生命週期事件的模組（如 `core.init.complete`）
- 啟動定時任務或背景服務的模組
- 需要在其他模組載入前完成初始化的模組

> 詳細的懶載入機制和注意事項請參考 [懶載入系統](../advanced/lazy-loading.md)。

## 事件处理

> 来源: `docs/zh-TW/getting-started/event-handling.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-TW/getting-started/event-handling.md）

# 事件處理入門

> [!TIP]
> **什麼時候需要讀這篇**：想讓機器人響應訊息、命令、通知、請求，或要實現等待回覆 / 多輪對話、排查「命令為什麼沒觸發」時讀。只想了解框架設計，看 [基礎概念](basic-concepts.md) 即可；不需要則跳過。

事件處理器就是機器人「聽懂」使用者並作出反應的地方——這篇按五類事件給出可直接複製的寫法，並覆蓋參數解析、權限、節流、多輪互動這些實戰場景。

## 事件類型概覽

ErisPulse 支援以下事件類型：

| 事件類型 | 說明 | 適用場景 |
|---------|------|---------|
| 消息事件 | 使用者發送的任何訊息 | 聊天機器人、內容過濾 |
| 命令事件 | 以命令前綴開頭的訊息 | 命令處理、功能入口 |
| 通知事件 | 系統通知（好友添加、群成員變化等） | 歡迎訊息、狀態通知 |
| 請求事件 | 使用者請求（好友請求、群邀請） | 自動處理請求 |
| 元事件 | 系統級事件（連接、心跳） | 連接監控、狀態檢查 |

## 消息事件處理

> **提示**: 建議在事件處理器中使用 `Event` 類型註解，以獲得 IDE 自動補全和類型檢查支援。

```python
from ErisPulse.Core.Event import Event  # 導入事件類型用於註解
```

### 監聽所有訊息

```python
from ErisPulse.Core.Event import message, Event

@message.on_message()
async def message_handler(event: Event):
    text = event.get_text()
    user_id = event.get_user_id()
    sdk.logger.info(f"收到 {user_id} 的訊息: {text}")
```

### 監聽私人訊息

```python
@message.on_private_message()
async def private_handler(event: Event):
    user_id = event.get_user_id()
    await event.reply(f"你好，{user_id}！這是私人訊息。")
```

### 監聽群聊訊息

```python
@message.on_group_message()
async def group_handler(event: Event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    sdk.logger.info(f"群 {group_id} 中 {user_id} 發送了訊息")
```

### 監聽@訊息

```python
@message.on_at_message()
async def at_handler(event: Event):
    # 獲取被@的使用者列表
    mentions = event.get_mentions()
    await event.reply(f"你@了這些使用者: {mentions}")
```

### 通配符與正規表示式監聽

四個訊息裝飾器（`on_message` / `on_private_message` / `on_group_message` /
`on_at_message`）均支援 `pattern`（glob 通配符）與 `regex`（正規表示式），不匹配的訊息
**不會觸發**處理器：

```python
# glob 通配符：* 任意串、? 單字元、[seq] 字元集
@message.on_message(pattern="簽到*")
async def signin_handler(event: Event):
    await event.reply("簽到成功")

# 正規表示：匹配金額
@message.on_message(regex=r"\d+\s*元")
async def price_handler(event: Event):
    await event.reply(f"收到金額：{event.get_text()}")

# pattern 與 regex 同時給出 → 兩者都須匹配
@message.on_message(pattern="*元", regex=r"\d+\s*元")
async def combined_handler(event: Event):
    pass
```

`wait_reply` 同樣支援這兩個參數（見[等待回覆](../developer-guide/modules/event-wrapper.md#等待回覆功能)）。

## 命令事件處理

### 基本命令

```python
from ErisPulse.Core.Event import command

@command("help", help="顯示幫助訊息")
async def help_handler(event):
    help_text = """
可用命令：
/help - 顯示幫助
/ping - 測試連接
/info - 查看資訊
    """
    await event.reply(help_text)
```

### 命令別名

```python
@command(["help", "h"], aliases=["幫助"], help="顯示幫助訊息")
async def help_handler(event):
    await event.reply("幫助訊息...")
```

使用者可以使用以下任何方式呼叫：
- `/help`
- `/h`
- `/幫助`

### 命令參數

```python
@command("echo", help="回顯訊息")
async def echo_handler(event):
    # 獲取命令參數
    args = event.get_command_args()
    
    if not args:
        await event.reply("請輸入要回顯的訊息")
    else:
        await event.reply(f"你說了: {' '.join(args)}")
```

參數保留使用者輸入的原始大小寫（即使配置為大小寫不敏感，
命令名匹配歸一也不會影響參數內容）。

### 聲明式參數與選項（args= / options=）

手動解析參數需要自己處理類型轉換與錯誤提示。聲明 `args=` / `options=` 後，
框架在權限檢查通過後自動解析命令參數並**按名注入處理器**；使用者輸入錯誤時
自動回覆本地化提示與用法（不會拋異常崩潰），`/help <命令>` 也會自動展示用法：

```python
@command(
    "roll",
    args="<count:int> [sides:int=6]",
    options={"verbose": "-v/--verbose", "label": "--label"},
    help="擲骰子",
)
async def roll_handler(event, count: int, sides: int = 6, verbose: bool = False, label: str = ""):
    total = sum(random.randint(1, sides) for _ in range(count))
    await event.reply(f"擲了 {count} 次 {sides} 面骰，總點數：{total}")
```

`args=` 位置參數語法：`<count:int>` 必填、`[sides:int=6]` 可選（含預設值）。支援類型：

| 類型 | 範例輸入 | 說明 |
|------|---------|------|
| `str` | `hello` | 文本（缺省類型） |
| `int` / `float` | `3` / `0.5` | 數值 |
| `bool` | `是` / `yes` / `はい` / `да` / `true` / `no` / `取消` | 布林值，複用互動確認（`Event.confirm()`）的確認詞表 |
| `literal` | `<mode:literal=fast|slow>` | 限制，僅接受列出的值；可選形式預設取首個 |
| `duration` | `90s`、`1h30m`、`1d` | 時長，按秒折算為 float |
| `rest` | `<text:rest>` | 剩餘全部文本（必須位於最後） |

`options=` 選項為字典式聲明：鍵為處理器參數名，值為旗標形式（多個別名以 `/` 分隔）。
註解為 `bool` 的參數是布林旗標（出現即 `True`）；其餘（缺省按 `str`）是帶值選項，
支援 `--label hello` 與 `--label=hello` 兩種取值，類型跟隨處理器註解。
選項先被識別剔除，剩餘 token 再按 `args=` 解析（`rest` 覆蓋剔除選項後的剩餘文本）。

**行為要點**：

- 權限檢查先於參數解析——無權限使用者不會觸發解析
- 解析失敗（類型不符 / 缺少參數 / 參數過多 / 未知選項）自動回覆本地化錯誤 + 用法，命令仍被認領
- 聲明的參數名必須存在於處理器簽名中，否則註冊期拋 `ValueError`
- 不聲明 `args=` / `options=` 的命令行為完全不變（向後相容）

### 命令治理（cooldown= / rate_limit= / usage_limit= / deprecated=）

手寫冷卻計時、限流視窗、使用配額、廢棄提示可用聲明替代，四者可任意組合。

**冷卻**——時長語法與 `args=` 的 `duration` 類型一致（如 `"30s"`、`"1h30m"`、`"1d"`）：

```python
@command("daily", cooldown="1d", cooldown_key="user", cooldown_reply="今天已簽到")
async def daily_handler(event):
    await event.reply("簽到成功！")
```

**限流**——滑動視窗聲明 `"次數/視窗"`（如 `"5/minute"`、`"10/s"`、`"3/2m"`）：

```python
@command("search", rate_limit="5/minute", rate_limit_key="user")
async def search_handler(event):
    await event.reply("搜尋結果")
```

**配額**——周期內總次數上限（如 `"100/day"`、`"10/hour"`、`"500/30d"`），超限拒絕執行：

```python
@command("translate", usage_limit="100/day", usage_limit_key="user",
         usage_limit_reply="今日翻譯次數已用完")
async def translate_handler(event):
    ...
```

與冷卻/限流不同，配額計數**經儲存持久化**（KV 鍵 `erispulse.usage.<key>`，重啟不丟）：
儲存不可達時自動退化為純記憶體計數並告警（此時配額重啟清零）。計數隨配額周期
切換自動清零，模組卸載時清理。

**廢棄**——呼叫時自動回覆廢棄文案，`deprecated_reject=True` 拒絕執行：

```python
@command("oldcmd", deprecated="請用 /newcmd", deprecated_reject=True)
async def old_handler(event): ...
```

鍵粒度（`cooldown_key=` / `rate_limit_key=`）：`"user"`（預設，同一使用者共享）、
`"session"`（同一會話共享，如同一群）、`"global"`（所有使用者所有會話共享）。

**行為要點**：

- 冷卻 / 限流 / 配額命中預設**靜默丟棄**（對稱於作用域靜默）；聲明 `cooldown_reply=` / `rate_limit_reply=` / `usage_limit_reply=` 後命中即回覆該文案
- 命令命中即認領——治理命中的命令不會漏給低優先級訊息處理器
- 治理判定位於全部權限檢查與參數解析通過、實際執行前：無權限使用者不觸發，參數錯誤不消耗
- 同時聲明冷卻與限流時冷卻先判（冷卻命中不佔限流視窗）；配額在冷卻/限流判定之後
- `deprecated=` 預設回覆文案後**繼續執行**；`deprecated_reject=True` 拒絕執行（`command.executed` 鈎子記 `success=False, error="deprecated"`）
- `/help` 列表與單命令幫助自動顯示廢棄標記與文案
- 冷卻與限流狀態為進程內記憶體，模組卸載時自動清理；跨進程共享 / 重啟持久化不在範圍內（**usage 配額計數除外**——經儲存持久化，見上節）
- 聲明在註冊期校驗（fail-fast）：語法非法、鍵粒度非白名單值、reply 未搭配主聲明均拋 `ValueError`

### 處理器節流（throttle=）與防抖（debounce=）

訊息處理器防刷屏聲明——同鍵事件在間隔內至多處理一條，其餘靜默丟棄：

```python
from ErisPulse import sdk

@sdk.message.on_message(throttle="2s", throttle_key="user")
async def handler(event): ...
```

防抖與節流互補：**視窗內只執行最後一條**，前序待執行任務自動取消（適合
"停止輸入後再處理"的搜尋聯想類場景）：

```python
@sdk.message.on_message(debounce="2s", debounce_key="user")
async def search(event): ...
```

`on_message` / `on_private_message` / `on_group_message` / `on_at_message`
均支援；`throttle_key=` / `debounce_key=` 與命令治理同一套鍵粒度
（user / session / global），時長語法與 `duration` 一致。節流與 `pattern=` /
`regex=` 等既有條件疊加生效（全部滿足才觸發）；間隔內丟棄僅記 TRACE 日誌；
聲明在註冊期校驗；`throttle=` 與 `debounce=` 語義互斥（同時聲明拋 `ValueError`）。

> **防抖不半途掐斷業務**：只有尚未越過等待視窗的待執行任務會被取消；已經
> 越窗、正在執行中的處理器不會被新事件取消（避免停在任意 await 點產生
> 部分副作用）。

### 依賴注入（Depends）

公共依賴（資料庫會話、配置讀取等）可抽為依賴函數，處理器以
`Depends(依賴函數)` 作為參數預設值聲明，框架在呼叫前自動以上下文物件
呼叫依賴函數並按名注入：

```python
from ErisPulse.Core import Depends

async def get_session(event):
    return await sdk.module.call("DB", "get_session")

@command("admin")
async def admin_handler(event, db=Depends(get_session)):
    ...
```

預設開啟**請求級快取**：同一次事件分發內，相同依賴函數只解析一次、所有
注入點共享結果（如 `get_db` 在一次事件中只建一次資料庫會話）；跨請求自動
不複用。可用 `Depends(get_db, use_cache=False)` 關閉單條依賴的快取。

覆蓋全部框架注入點——命令處理器、事件處理器（`message.on_message()` 等）、
生命週期鈎子（`sdk.lifecycle.on`）、SSE 路由處理器。依賴函數的第一個參數
是注入點上下文物件（事件場景為 `Event`，生命週期為事件 `data`，
路由為 `HttpRequest` / `SseEmitter`）；同步與異步依賴函數均可聲明。

**聲明其它模組的服務**（語法糖）：

```python
@command("query")
async def query_handler(event, session=Depends.module("DB", "get_session")):
    ...
```

`Depends.module(模組名, 方法名, *固定參數)` 等價於在依賴函數內呼叫
`sdk.module.call(...)`。模組實例化（`__init__`）不在覆蓋範圍——實例化時無
上下文物件；FastAPI 承載的 HTTP 路由請用 FastAPI 原生 `fastapi.Depends`。

**行為要點**：

- 聲明在註冊期校驗（fail-fast）：依賴不可呼叫、或與 `args=` / `options=` 參數重名時拋 `ValueError`
- 依賴函數拋出的異常與處理器自身異常同口徑處理（命令自動回覆錯誤）
- 不聲明 `Depends` 的處理器零開銷（分發期無任何反射）
- FastAPI 承載的 HTTP 路由請使用 FastAPI 原生 `fastapi.Depends`

### 命令組

```python
@command("admin.reload", group="admin", help="重新載入模組")
async def reload_handler(event):
    await event.reply("模組已重新載入")

@command("admin.stop", group="admin", help="停止機器人")
async def stop_handler(event):
    await event.reply("機器人已停止")
```

`group` 參數僅用於幫助列表歸類；上面示例中的 `admin.reload` 是一個**整體命令名**
（點號只是命名風格，使用者需輸入 `/admin.reload`）。

### 子命令

命令名支援**空格分隔**的多 token 形式，實現 `/admin add`、`/admin user ban` 這樣的子命令：

```python
@command("admin", help="管理命令")
async def admin_handler(event):
    await event.reply("用法：/admin add | /admin remove")

@command("admin add", help="新增管理員")
async def admin_add_handler(event):
    target = event.get_command_args()[0]
    await event.reply(f"已新增 {target}")

@command("admin remove", aliases=["a remove"], help="移除管理員")
async def admin_remove_handler(event):
    await event.reply("已移除")
```

匹配規則（**最長前綴匹配**）：

- `/admin add x` 優先命中 `admin add`，`event.get_command_args()` 返回 `["x"]`（子命令名之後的參數）
- 僅註冊了 `admin` 時，`/admin add x` 命中 `admin`，`get_command_args()` 返回 `["add", "x"]`（歷史行為不變）
- 別名支援多 token 形式（如 `a remove`），也可用單 token 別名（如 `a`）指向子命令
- 父子命令同時註冊時，未註冊的子命令輸入（如 `/admin list x`）回落到父命令

**權限繼承**：子命令未聲明 `permission` 時，自動繼承父鏈上最近聲明了權限的祖先命令——
保護 `/admin` 即自動保護其下全部子命令；子命令自身聲明的權限優先：

```python
def is_admin(event):
    return event.get_user_id() in {"user123"}

@command("admin", permission=is_admin, help="管理命令")
async def admin_handler(event):
    ...

# 無需重複聲明 permission，自動繼承 is_admin
@command("admin add", help="新增管理員")
async def admin_add_handler(event):
    ...
```

注意：`master=True` 與 `hidden` **不會**繼承，需要時請在子命令上單獨聲明；
使用者 ACL（黑白名單）按命令全名匹配，glob 規則如 `"admin*"` 可覆蓋整組子命令。

`/help` 的命令總覽中，子命令會自動掛到可見的父命令下縮進展示
（`admin` → `admin add` 縮進一級，`admin user` → `admin user ban` 縮進兩級）。

### 命令權限與存取控制

命令權限分三層，從上到下逐層判定（**上層拒絕則不再看下層**）：

```python
# ① 命令權限 ACL（使用者側配置）：按命令的使用者黑白名單，拒絕時回覆"權限不足"
# ② master=True —— 僅框架主人可執行（框架自動檢查，拒絕時回覆"權限不足"）
@command("restart", master=True, help="重啟模組")
async def restart_handler(event):
    await event.reply("模組已重啟")

# ③ permission=呼叫函數 —— 命令自身的控制邏輯（回傳 True 才執行）
def is_admin(event):
    return event.get_user_id() in {"user123", "user456"}

@command("panel", permission=is_admin, help="管理面板")
async def panel_handler(event):
    await event.reply("歡迎來到管理面板")
```

**命令使用者 ACL**（`ErisPulse.event.command.acl`）：使用者可為任意命令配置使用者黑白名單，
命令名支援精確與 glob 模式（如 `"roll*"`），拒絕時回覆"權限不足"：

```toml
# config.toml —— 僅允許 123456 執行 restart；666 一律拒絕
[ErisPulse.event.command.acl.restart]
allow = ["onebot11:123456"]
deny = ["onebot11:666"]
```

判定順序：`deny` 命中 → 拒絕；`allow` 非空且未命中 → 拒絕；未配置 ACL 時遵循
`event.command.default_allow`（`false` = 嚴格模式，無 ACL 即拒；`true` 時交給開發者預設
`master=True` / `permission`）。執行時 API（命令名支援 glob）：

```python
from ErisPulse.Core.Event import command

command.allow_user("restart", "onebot11", "123456")   # 允許名單
command.deny_user("restart", "onebot11", "666")       # 拒絕名單
command.remove_acl("restart")                          # 清除黑白名單
command.get_acl("restart")                             # 查詢當前名單
```

> 命令處理器從事件包導入：`from ErisPulse.Core.Event import command`；
> 也可經 SDK 事件包訪問：`sdk.Event.command`（兩者為同一單例）。
> 在模組內通常已隨命令裝飾器導入（`from ErisPulse.Core.Event import command`）。

跨命令 / 跨使用者的**事件級**存取控制（某人 / 某群 / 某 Bot 的訊息收不收）
走作用域**身份維度**（`scope.identity`）；**模組級**可用性（哪些模組能用）
走作用域**模組維度**（`scope.platforms / bots / sessions`）。
詳見[作用域（scope）](../advanced/scope.md)。

> 建議：命令內部需要聯動業務邏輯的用 `master=True` / `permission`；純按使用者 / 群做
> 存取控制的用作用域身份維度；控制模組可用性的用作用域模組維度。

### 命令優先級

```python
# 優先級數值越大，執行越早
@message.on_message(priority=10)
async def high_priority_handler(event):
    await event.reply("高優先級處理器")

@message.on_message(priority=1)
async def low_priority_handler(event):
    await event.reply("低優先級處理器")
```

### 並行事件處理

ErisPulse 事件系統採用**同優先級並行、不同優先級串行**的調度模型：

```
事件到達
    ↓
priority=10 組: [處理器C || 處理器D] 並行 → 合併結果
    ↓ (如未中斷)
priority=0 組: [處理器A || 處理器B] 並行 → 合併結果
    ↓
...
```

- **同優先級並行**：優先級相同的多個處理器會同時執行，提高吞吐量
- **跨級串行**：不同優先級的組按順序執行（數值越大越先執行），確保高優先級處理器先運行
- **Copy-On-Write**：處理器無修改時不建立副本，確保零開銷
- **衝突處理**：同優先級多處理器修改同一欄位時，使用最後修改值並記錄警告日誌
- **中斷機制**：任意處理器呼叫 `event.done()`（預設）或 `event.done(claim=False)` 後，跳過後續低優先級組。認領與阻斷的區別見下文[「鏈路控制：認領與阻斷」](#鏈路控制認領與阻斷)

```python
# 示例：同優先級處理器並行執行
@message.on_message(priority=0)
async def handler_a(event):
    # 處理任務A
    event['result_a'] = process_a()

@message.on_message(priority=0)
async def handler_b(event):
    # 與 handler_a 並行執行
    event['result_b'] = process_b()

# 不同優先級串行執行
@message.on_message(priority=10)
async def handler_c(event):
    # 優先級最高，最先執行
    pass
```

> **併發上限**：所有匹配 handler 的 Task 會**立即建立**，但透過一個信號量限制**同時在途執行數**，預設上限 **64**（`ErisPulse.framework.handler_max_concurrency`，支援熱更新）。超過上限的 Task 在信號量上排隊，等前面的完成後再進。事件洪峰時這就是你的「泄壓閥」。
>
> **慢日誌**：單個處理器耗時超過 **1 秒**時，框架會在日誌打 WARNING（`handler_slow`）。`wait_reply` 的等待時間會從耗時裡剔除，不會因為「等人回覆」誤報慢。

## 中間件：分發前改寫或否決

中間件在事件分發**之前**順序執行，防火牆、限流、事件脫敏等場景的正統實現點：

```python
from ErisPulse.Core import adapter

@adapter.middleware
async def firewall(data):
    if _is_banned(data.get("user_id")):
        return False          # 否決：事件被丟棄，不進入任何處理器，無出站副作用
    data["checked"] = True    # 返回 dict：改寫載體（與歷史行為一致）
    # 返回 None：放行，載體不變（歷史行為）
    return data
```

| 回傳值 | 行為 |
|--------|------|
| `False` | **否決**：事件立即丟棄，不進入任何處理器 |
| `dict` | 改寫事件載體後繼續分發 |
| `None` | 放行，載體不變 |

否決時框架輸出 TRACE 日誌並觸發 `adapter.event.blocked` 生命週期鈎子（攜帶中間件名與完整事件），供審計「事件為什麼沒響應」。

## 命令分發決策鏈：為什麼命令沒觸發

一條命令訊息依次經過：**命令文字判定 → 命令名/別名命中（未命中附拼寫建議）→ 命中即認領 → 作用域 → 使用者 ACL → 主人 → 權限 → 冷卻/限流 → 配額（usage）→ 廢棄（deprecated，notice/rejected）→ 參數解析 → 執行**（中間件可在事件層否決，見上一節）。任何一步不滿足即終止；治理命中（冷卻/限流/配額）預設靜默丟棄，權限類拒絕會回覆使用者，廢棄按聲明回覆或拒絕。

測試中 `ErisPulse-Testing` 的 `dispatch()` 直接回傳這條決策鏈（`DispatchTrace`，`trace.explain()` 輸出逐行因果），生產環境可用 `ErisPulse.Core.Event.start_dispatch_trace()` 采集同樣的記錄。

此外 `ErisPulse.runtime` 提供兩組排查診斷 API：`explain_module(模組名)` 回答"模組為什麼沒加載"（未註冊 / 懶加載 / 配置禁用 / 依賴缺失 / SDK 版本不滿足，逐項給原因），`explain_event(事件)` 回答"事件為什麼沒響應"（適配器未註冊 / 身份拉黑 / 模組會話屏蔽 / 命令未命中）；配 `format_report()` 渲染人類可讀結論。

## 作用域過濾：為什麼我的模組沒收到訊息

事件到達後有兩道**靜默**過濾（都不回覆、不報錯）：

1. **身份維度**（`ErisPulse.scope.identity`）：事件進入分發入口時，按 使用者 > 群 > Bot > 適配器 判定收不收。
   被拒絕的**整個事件**直接丟棄，任何處理器（含命令分發器）都不會觸發。
2. **模組維度**（`ErisPulse.scope`）：事件到達某模組的處理器/命令時，按 會話 > Bot > 平台 判定
   該模組是否可用，**不通過就靜默跳過**。

```toml
# 例1：某群所有訊息不傳播
[ErisPulse.scope.identity.sessions.onebot11."group_123"]
deny = true

# 例2：把 MyModule 屏蔽在某個 Bot
[ErisPulse.scope.bots.onebot11."123456"]
blocked = ["MyModule"]
```

此時該群的訊息到達時，`MyModule` 的命令與事件處理器**都不會被調度**。這不是 bug，是過濾機制——排查「模組沒反應」時優先檢查作用域的身份與模組綁定。

- 過濾日誌只在 **TRACE** 級可見（`core.scope.identity_denied` / `core.scope.denied`），預設 INFO 看不到任何痕跡
- 框架級處理器（如命令分發器 `scope_exempt=True`）不受**模組維度**影響，但受**身份維度**影響（整個事件已丟棄）
- 命令執行前還有第三道：命令使用者 ACL（拒絕時回覆"權限不足"，見上節）
- 第四道是**事件覆寫**（見下節）

> [!NOTE]
> **作用域過濾與事件認領（claim）的關係**：兩道靜默過濾都發生在處理器
> **調度之前**——被過濾跳過的處理器沒有機會執行，自然也不參與
> `event.done()` / `mark_processed()` 的認領狀態。事件是否已被認領，
> 只由**實際執行**的處理器（命令命中認領、回覆命中認領、顯式呼叫）決定；
> 作用域拒絕本身既不認領也不阻斷（靜默跳過，訊息繼續走完剩餘分發鏈）。

> 作用域配置、匹配語法、執行時 API 見 [作用域（scope）](../advanced/scope.md)。

## 事件覆寫：不改模組程式碼，覆寫任意事件類型的行為

> [!NOTE]
> 本特性需要 ErisPulse **2.8.0+**。

事件處理器在註冊時聲明的參數（`pattern` / `regex` / `master` / `hidden` 等）只是**開發者預設**。
統一覆寫系統讓使用者按**事件類型**覆寫任意模組的行為——OneBot12 標準類型
（meta / message / notice / request）與 ErisPulse 擴展類型（command）各自擁有專屬的可覆寫參數：

| 事件類型 | 可覆寫參數 | 作用 |
|---------|-----------|------|
| `message` | `pattern` / `regex` / `detail_types` | 文本觸發條件 + 訊息子類型白名單 |
| `notice` | `detail_types` / `pattern` / `regex` | 通知子類型白名單 + 文本條件 |
| `request` | `detail_types` / `pattern` / `regex` | 請求子類型白名單 + 文本條件 |
| `meta` | `detail_types` | 元事件子類型白名單（connect / heartbeat 等） |
| `command` | `master` / `hidden` / `aliases` / `prefix` / `help` / `usage` | 命令實現參數（使用者優先） |
| `acl`（command 專屬） | `allow` / `deny` | 命令使用者黑白名單（按命令名 glob） |

```toml
# message：覆寫文本觸發條件（與程式內條件 AND）
[ErisPulse.event.overrides.message.ChatModule]
pattern = "閒聊*"

# notice：只響應特定通知子類型
[ErisPulse.event.overrides.notice.MyModule]
detail_types = ["group_increase"]

# command：覆寫實現參數（使用者優先——可收緊或放開開發者預設）
[ErisPulse.event.overrides.command.MyModule.restart]
master = true
hidden = true

# acl：命令使用者黑白名單（跨命令 glob）
[ErisPulse.event.overrides.acl."roll*"]
allow = ["onebot11:u_vip"]

# ACL 兜底（false = 嚴格模式：無 ACL 即拒）
acl_default_allow = true
```

執行時 API（`from ErisPulse.Core.Event import overrides` 或 `sdk.Event.overrides`，
**類型子命名空間**——每類對稱的 `set` / `get` / `delete` 三件套）：

```python
from ErisPulse.Core.Event import overrides

overrides.message.set("ChatModule", pattern="閒聊*")   # message 文本條件
overrides.notice.set("MyModule", detail_types=["group_increase"])
overrides.command.set("MyModule", "restart", master=True)  # 命令參數
overrides.acl.set("roll*", deny=["onebot11:u_bad"])    # 命令使用者黑名單

overrides.message.get("ChatModule")     # {"pattern": "閒聊*"}
overrides.message.delete("ChatModule")  # 恢復開發者預設
```

- 覆寫條件與處理器程式內條件**同時生效**（AND 語義）；`command` 參數與開發者聲明**深合併**（覆寫優先）
- `detail_types`：事件缺 `detail_type` 時放行（不誤殺未知事件）
- `pattern` / `regex`：無文字的事件（connect / heartbeat 等）不受約束，直接放行
- `command` 覆寫鍵 `master` 同步映射儲存鍵 `must_master`；禁用命令統一走 `acl` deny
- **鍵名映射說明**：`overrides.command.set("My", "restart", master=True)` 的參數名
  `master` 僅為配置別名，實際儲存鍵與 `get()` 返回值中的鍵名統一為 **`must_master`**
  （`get()` 回傳 `{"must_master": true}`）——執行時判斷讀取的是儲存鍵，請勿按
  `master` 鍵名讀取
- 配置改了立即生效（熱更新），格式校驗告警（未知參數 / 壞條目忽略）

## 鏈路控制：認領與阻斷

> [!NOTE]
> `event.done()` / `event.mark_processed()` 的 `claim=` / `stop=` 參數本特性需要 ErisPulse **2.7.1+**。

ErisPulse 將「認領」與「阻斷」兩個正交語義解耦，透過 `event.done()` 統一控制，便於在命令處理周圍疊加日誌、審計、權限等觀察層。

**兩個概念的準確定義：**

- **認領（claim）**：標記事件已被本處理器處理（寫入 `_processed`）。命令分發器看到已認領的事件會**跳過去重**——避免同一訊息被多個命令處理器重複處理。典型場景：命令匹配成功後認領，阻止命令分發器再介入。
- **阻斷（stop）**：阻止事件向**更低優先級**處理器傳播（寫入 `_propagation_stopped`）。低優先級處理器將不再看到該事件。典型場景：高優先級處理器已完整處理事件，不希望低優先級再執行。

| `event.done(...)` | 認領 | 阻斷 | 場景 |
|-------------------|------|------|------|
| `event.done()` | ✔ | ✔ | 命令 / 處理器處理完的標準做法 |
| `event.done(stop=False)` | ✔ | ✘ | 僅認領，讓低優先級仍會執行（日誌 / 統計） |
| `event.done(claim=False)` | ✘ | ✔ | 僅阻斷（如防火牆 / 限流），但不做命令去重 |

`event.done(claim=, stop=)` 是 `event.mark_processed(claim=, stop=)` 的別名，二者參數與行為完全等價。

```python
@command("help")
async def help_cmd(event):
    event.done()            # 認領 + 阻斷（命令處理完的標準做法）

@message.on_message(priority=50)
async def observer(event):
    event.done(stop=False)  # 僅認領：低優先級仍會執行（日誌 / 統計）

@message.on_message(priority=100)
async def firewall(event):
    if denied(event):
        event.done(claim=False)  # 僅阻斷：低優先級不執行，但不做去重
```

### 命令與回覆的 block 配置

**命令命中即認領**：訊息一旦匹配到已註冊命令名（含子命令/別名），無論後續作用域或權限判定結果如何，都會被認領並預設阻斷傳播——被權限拒絕的命令再也不會漏給低優先級訊息處理器（消除"命令被拒後 on_message 又響應一次"的雙重響應）。

可透過配置放行阻斷，讓低優先級觀察者（日誌 / 審計 / 權限）也能看到這些訊息：

```toml
[ErisPulse.event.command]
block = false   # 命令訊息繼續流向低優先級處理器（認領不受影響，不會重複消費）

[ErisPulse.event.wait_reply]
block = false   # 被 wait_reply 消費的回覆繼續流向低優先級處理器
```

> 注意：`block` 只控制**阻斷**（stop），不影響**認領**（claim）——命中的命令永遠不會被訊息處理器重複消費；未命中任何命令的訊息照常流向訊息處理器。

## 通知事件處理

### 好友添加

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname() or "新朋友"
    await event.reply(f"歡迎添加我為好友，{nickname}！")
```

### 群成員增加

```python
@notice.on_group_increase()
async def member_increase_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"歡迎新成員 {user_id} 加入群 {group_id}")
```

### 群成員減少

```python
@notice.on_group_decrease()
async def member_decrease_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"成員 {user_id} 離開了群 {group_id}")
```

## 請求事件處理

### 好友請求

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def friend_request_handler(event):
    user_id = event.get_user_id()
    comment = event.get_comment()
    
    sdk.logger.info(f"收到好友請求: {user_id}, 附言: {comment}")
    
    # 可以透過適配器 API 處理請求
    # 具體實作請參考各適配器文件
```

### 群邀請請求

```python
@request.on_group_request()
async def group_request_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"收到群 {group_id} 的邀請，來自 {user_id}")
```

## 元事件處理

### 連接事件

```python
from ErisPulse.Core.Event import meta

@meta.on_connect()
async def connect_handler(event):
    platform = event.get_platform()
    sdk.logger.info(f"{platform} 平台已連接")

@meta.on_disconnect()
async def disconnect_handler(event):
    platform = event.get_platform()
    sdk.logger.warning(f"{platform} 平台已斷開連接")
```

### 心跳事件

```python
@meta.on_heartbeat()
async def heartbeat_handler(event):
    platform = event.get_platform()
    sdk.logger.debug(f"{platform} 心跳檢測")
```

### Bot 狀態查詢

當適配器發送 meta 事件後，框架自動追蹤 Bot 狀態，你可以隨時查詢：

```python
from ErisPulse import sdk

# 檢查某個 Bot 是否在線
if sdk.adapter.is_bot_online("telegram", "123456"):
    telegram = sdk.adapter.get("telegram")
    await telegram.Send.To("user", "123456").Text("Bot 在線")

# 列出當前所有在線 Bot
bots = sdk.adapter.list_bots()
for platform, bot_list in bots.items():
    for bot_id, info in bot_list.items():
        print(f"{platform}/{bot_id}: {info['status']}")

# 獲取完整狀態摘要
summary = sdk.adapter.get_status_summary()
```

## 互動式處理

### 使用 reply 方法發送回覆

`event.reply()` 方法支援多種修飾參數，方便發送帶有 @、回覆等功能的訊息：

```python
# 簡單回覆
await event.reply("你好")

# 發送不同類型的訊息
await event.reply("http://example.com/image.jpg", method="Image")  # 圖片
await event.reply("http://example.com/voice.mp3", method="Voice")  # 語音

# @單個使用者
await event.reply("你好", at_users=["user123"])

# @多個使用者
await event.reply("大家好", at_users=["user1", "user2", "user3"])

# 回覆訊息
await event.reply("回覆內容", reply_to="msg_id")

# @全體成員
await event.reply("公告", at_all=True)

# 組合使用：@使用者 + 回覆訊息
await event.reply("內容", at_users=["user1"], reply_to="msg_id")
```

### 等待使用者回覆

```python
@command("ask", help="詢問使用者")
async def ask_handler(event):
    await event.reply("請輸入你的名字:")
    
    # 等待使用者回覆，超時時間 30 秒
    reply = await event.wait_reply(timeout=30)
    
    if reply:
        name = reply.get_text()
        await event.reply(f"你好，{name}！")
    else:
        await event.reply("等待超時，請重新輸入。")
```

> [!TIP]
> **等待期間命令仍然可用**（2.8.3+）：以命令前綴開頭且命中已註冊命令的
> 訊息（如 `/cancel`）會**執行命令**而非作為回覆內容，等待繼續掛起——
> 使用者可以隨時取消/切換，命令執行完仍可繼續回覆。需要"等待吞掉一切文字"
> 的旧行為時：配置 `ErisPulse.event.wait_reply.cmdpass = true`，或單次
> `wait_reply(cmdpass=True)`。

### 帶驗證的等待回覆

```python
@command("age", help="詢問年齡")
async def age_handler(event):
    def validate_age(event_data):
        """驗證年齡是否有效"""
        try:
            age = int(event_data.get_text())
            return 0 <= age <= 150
        except ValueError:
            return False
    
    await event.reply("請輸入你的年齡 (0-150):")
    
    reply = await event.wait_reply(
        timeout=60,
        validator=validate_age
    )
    
    if reply:
        age = int(reply.get_text())
        await event.reply(f"你的年齡是 {age} 歲")
    else:
        await event.reply("輸入無效或超時")
```

### 帶回調的等待回覆

```python
@command("confirm", help="確認操作")
async def confirm_handler(event):
    async def handle_confirmation(reply_event):
        text = reply_event.get_text().lower()
        
        if text in ["是", "yes", "y"]:
            await event.reply("操作已確認！")
        else:
            await event.reply("操作已取消。")
    
    await event.reply("確認執行此操作嗎？(是/否)")
    
    await event.wait_reply(
        timeout=30,
        callback=handle_confirmation
    )
```

### 確認對話 (confirm)

等待使用者確認或否定，自動識別內建中英文確認詞：

```python
@command("confirm", help="確認操作")
async def confirm_handler(event):
    if await event.confirm("確定要執行此操作嗎？"):
        await event.reply("已確認，執行中...")
    else:
        await event.reply("已取消")

# 自訂確認詞
if await event.confirm("繼續嗎？", yes_words={"go", "繼續"}, no_words={"stop", "停止"}):
    pass
```

### 選擇菜單 (choose)

使用者可回覆選項編號或選項文本：

```python
@command("choose", help="選擇")
async def choose_handler(event):
    choice = await event.choose(
        "請選擇顏色：",
        ["紅色", "綠色", "藍色"]
    )
    
    if choice is not None:
        colors = ["紅色", "綠色", "藍色"]
        await event.reply(f"你選擇了：{colors[choice]}")
    else:
        await event.reply("超時未選擇")
```

**合併模式**：`merge_prompt=True` 時將選項拼入提示訊息，用使用者指定的 `method` 一條訊息發送：

```python
# 用 Markdown 發送合併後的提示 + 選項
choice = await event.choose(
    "## 請選擇顏色\n{options}\n請回覆編號",
    ["紅色", "綠色", "藍色"],
    method="Markdown",
    merge_prompt=True,
)
```

> `{options}` 占位符控制選項插入位置；不寫則追加到 prompt 末尾。
> 可透過 `placeholder` 參數自訂占位符（如 `placeholder="[choices]"`）。
> `options_format="auto"`（預設）根據 method 自動選擇樣式：Markdown→無序列表，Html→有序列表，其他→純文本列表。
> 文本類方法（Text/Markdown/Html 等）預設合併選項到末尾；非文本方法（Image 等）預設拆分為兩條訊息。

### 收集表單 (collect)

多步驟收集使用者輸入：

```python
@command("register", help="註冊")
async def register_handler(event):
    data = await event.collect([
        {"key": "name", "prompt": "請輸入姓名："},
        {"key": "age", "prompt": "請輸入年齡：", 
         "validator": lambda e: e.get_text().isdigit()},
        {"key": "email", "prompt": "請輸入電子信箱："}
    ])
    
    if data:
        await event.reply(f"註冊成功！\n姓名：{data['name']}\n年齡：{data['age']}\n電子信箱：{data['email']}")
    else:
        await event.reply("註冊超時或輸入無效")
```

### 等待任意事件 (wait_for)

等待滿足條件的任意事件，不限於同一使用者：

```python
@command("wait_member", help="等待新成員")
async def wait_member_handler(event):
    await event.reply("等待群成員加入...")
    
    evt = await event.wait_for(
        event_type="notice",
        condition=lambda e: e.get_detail_type() == "group_member_increase",
        timeout=120
    )
    
    if evt:
        await event.reply(f"歡迎新成員：{evt.get_user_id()}")
    else:
        await event.reply("等待超時")
```

### 多輪對話 (conversation)

建立可互動的多輪對話上下文：

```python
@command("survey", help="問卷調查")
async def survey_handler(event):
    conv = event.conversation(timeout=60)
    
    await conv.say("歡迎參與問卷調查！")
    
    while conv.is_active:
        reply = await conv.wait()
        
        if reply is None:
            await conv.say("對話超時，再見！")
            break
        
        text = reply.get_text()
        
        if text == "退出":
            await conv.say("再見！")
            break
        
        await conv.say(f"你說了：{text}，繼續輸入或回覆'退出'結束")
```

### 內建確認詞

ErisPulse 內建了中英文確認詞集合：

- **確認詞** (`CONFIRM_YES_WORDS`): 是、yes、y、確認、確定、好、好的、ok、true、對、嗯、行、同意、沒問題...
- **否定詞** (`CONFIRM_NO_WORDS`): 否、no、n、取消、不、不要、不行、cancel、false、錯、拒絕、不可以...

## 事件資料訪問

### Event 物件常用方法

```python
@command("info")
async def info_handler(event):
    # 基礎資訊
    event_id = event.get_id()
    event_time = event.get_time()
    event_type = event.get_type()
    detail_type = event.get_detail_type()
    
    # 發送者資訊
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    
    # 訊息內容
    message_segments = event.get_message()
    alt_message = event.get_alt_message()
    text = event.get_text()
    
    # 群組資訊
    group_id = event.get_group_id()
    
    # 機器人資訊
    self_id = event.get_self_user_id()
    self_platform = event.get_self_platform()
    
    # 原始資料
    raw_data = event.get_raw()
    raw_type = event.get_raw_type()
    
    # 平台資訊
    platform = event.get_platform()
    
    # 訊息類型判斷
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    is_at = event.is_at_message()
    
    # 命令資訊
    if event.is_command():
        cmd_name = event.get_command_name()
        cmd_args = event.get_command_args()
        cmd_raw = event.get_command_raw()
```

### 平台擴展方法

除了內建方法外，各平台適配器還會註冊平台專有方法，方便你訪問平台特有的資料。

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    platform = event.get_platform()

    # 根據平台呼叫專有方法
    if platform == "telegram":
        chat_type = event.get_chat_type()      # Telegram 專有方法
    elif platform == "email":
        subject = event.get_subject()           # 郵件專有方法
```

如果不確定平台是否註冊了某個方法，可以查詢某個平台註冊了哪些方法：

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("telegram")
# ["get_chat_type", "is_bot_message", ...]
```

> 各平台註冊的專有方法請參閱對應的 [平台文件](../platform-guide/)。

## 事件處理最佳實踐

### 1. 異常處理

```python
@command("process")
async def process_handler(event):
    try:
        # 業務邏輯
        result = await do_some_work()
        await event.reply(f"結果: {result}")
    except ValueError as e:
        # 預期的業務錯誤
        await event.reply(f"參數錯誤: {e}")
    except Exception as e:
        # 未預期的錯誤
        sdk.logger.error(f"處理失敗: {e}")
        await event.reply("處理失敗，請稍後重試")
```

### 2. 日誌記錄

```python
@message.on_message()
async def message_handler(event):
    user_id = event.get_user_id()
    text = event.get_text()
    
    sdk.logger.info(f"處理訊息: {user_id} - {text}")
    
    # 使用模組自己的日誌
    from ErisPulse import sdk
    logger = sdk.logger.get_child("MyHandler")
    logger.debug(f"詳細調試資訊")
```

### 3. 條件處理

```python
@message.on_message(priority=0)
async def conditional_handler(event):
    """條件處理 - 在處理器內部判斷"""
    # 只處理特定使用者的訊息
    if event.get_user_id() in ["bot1", "bot2"]:
        return
    
    # 只處理包含特定關鍵字的訊息
    if "關鍵字" not in event.get_text():
        return
    
    await event.reply("條件滿足，處理訊息")
```

## 常见任务

> 来源: `docs/zh-TW/getting-started/common-tasks.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-TW/getting-started/common-tasks.md）

# 常見任務範例

> [!TIP]
> **什麼時候需要讀這篇**：想給機器人加某個具體功能時按節查閱——持久化、定時任務、訊息過濾、權限控制、批次傳送，每一節都是可直接複製的完整範例。想系統學事件處理寫法先看 [事件處理入門](event-handling.md)；不需要則跳過。

## 內容清單

1. 數據持久化  
2. 定時任務  
3. 消息過濾  
4. 多平台適配  
5. 消息發送進階（重試/超時/批量）  
6. 權限控制  
7. 消息統計  
8. 搜索功能  
9. 圖片處理

## 數據持久化

### 簡單計數器

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("count", help="查看命令呼叫次數")
async def count_handler(event):
    # 獲取計數
    count = sdk.storage.get("command_count", 0)
    
    # 增加計數
    count += 1
    sdk.storage.set("command_count", count)
    
    await event.reply(f"這是第 {count} 次呼叫此命令")
```

### 用戶數據存儲

```python
@command("profile", help="查看個人資料")
async def profile_handler(event):
    user_id = event.get_user_id()
    
    # 獲取用戶數據
    user_data = sdk.storage.get(f"user:{user_id}", {
        "nickname": "",
        "join_date": None,
        "message_count": 0
    })
    
    profile_text = f"""
暱稱: {user_data['nickname']}
加入時間: {user_data['join_date']}
訊息數: {user_data['message_count']}
    """
    
    await event.reply(profile_text.strip())

@command("setnick", help="設定暱稱")
async def setnick_handler(event):
    user_id = event.get_user_id()
    args = event.get_command_args()
    
    if not args:
        await event.reply("請輸入暱稱")
        return
    
    # 更新用戶數據
    user_data = sdk.storage.get(f"user:{user_id}", {})
    user_data["nickname"] = " ".join(args)
    sdk.storage.set(f"user:{user_id}", user_data)
    
    await event.reply(f"暱稱已設定為: {' '.join(args)}")
```

## 定時任務

### 簡單定時器

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command
import asyncio

class TimerModule:
    def __init__(self):
        self.sdk = sdk
        self._tasks = []
    
    async def on_load(self, event):
        """模組載入時啟動定時任務"""
        self._start_timers()
        
        @command("timer", help="定時器管理")
        async def timer_handler(event):
            await event.reply("定時器正在運行中...")
    
    def _start_timers(self):
        """啟動定時任務"""
        # 每 60 秒執行一次
        task = asyncio.create_task(self._every_minute())
        self._tasks.append(task)
        
        # 每天凌晨執行
        task = asyncio.create_task(self._daily_task())
        self._tasks.append(task)
    
    async def _every_minute(self):
        """每分鐘執行的任務"""
        self.sdk.logger.info("每分鐘任務執行")
        # 你的邏輯...
    
    async def _daily_task(self):
        """每天凌晨執行的任務（註：基於 UTC 時間計算，如需本地時間請自行調整）"""
        import time
        
        while True:
            # 計算到凌晨的時間
            now = time.time()
            midnight = now + (86400 - now % 86400)
            
            await asyncio.sleep(midnight - now)
            
            # 執行任務
            self.sdk.logger.info("每日任務執行")
            # 你的邏輯...
```

### 使用生命週期事件

```python
@sdk.lifecycle.on("core.init.complete")
async def init_complete_handler(event_data):
    """SDK 初始化完成後啟動定時任務"""
    import asyncio
    
    async def daily_reminder():
        """每日提醒"""
        await asyncio.sleep(86400)  # 24小時
        sdk.logger.info("執行每日任務")
    
    # 啟動後台任務
    asyncio.create_task(daily_reminder())
```

## 消息過濾

### 關鍵字過濾

```python
from ErisPulse.Core.Event import message

blocked_words = ["垃圾", "廣告", "釣魚"]

@message.on_message()
async def filter_handler(event):
    text = event.get_text()
    
    # 檢查是否包含敏感詞
    for word in blocked_words:
        if word in text:
            sdk.logger.warning(f"攔截敏感訊息: {word}")
            return  # 不處理此訊息
    
    # 正常處理訊息
    await event.reply(f"收到: {text}")
```

### 黑名單過濾

```python
# 從配置或儲存加載黑名單
blacklist = sdk.storage.get("user_blacklist", [])

@message.on_message()
async def blacklist_handler(event):
    user_id = event.get_user_id()
    
    if user_id in blacklist:
        sdk.logger.info(f"黑名單使用者: {user_id}")
        return  # 不處理
    
    # 正常處理
    await event.reply(f"你好，{user_id}")
```

## 多平台適配

### 平台特定回應

```python
@command("help", help="顯示幫助")
async def help_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        await event.reply("雲湖平台幫助...")
    elif platform == "telegram":
        await event.reply("Telegram platform help...")
    elif platform == "onebot11":
        await event.reply("OneBot11 help...")
    else:
        await event.reply("通用幫助資訊")
```

### 平台特性檢測

```python
@command("rich", help="發送富文本訊息")
async def rich_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        # 雲湖支援 HTML
        yunhu = sdk.adapter.get("yunhu")
        await yunhu.Send.To("user", event.get_user_id()).Html(
            "<b>加粗文字</b><i>斜體文字</i>"
        )
    elif platform == "telegram":
        # Telegram 支援 Markdown
        telegram = sdk.adapter.get("telegram")
        await telegram.Send.To("user", event.get_user_id()).Markdown(
            "**加粗文字** *斜體文字*"
        )
    else:
        # 其他平台使用純文字
        await event.reply("加粗文字 斜體文字")
```

## 消息發送進階（重試/超時/批量）

除了簡單的 `event.reply()`，你還可以透過適配器的 Send DSL 實現更複雜的發送場景：失敗自動重試、超時取消、成功後執行邏輯、批量發送多條消息。

> 下面的示例用 `event.get_detail_type()` 和 `event.get_target_id()` 從事件中獲取目標類型和 ID（群聊自動取 group_id，私聊自動取 user_id），避免硬編碼。

### 發送成功後執行邏輯

```python
@command("pay", help="模擬支付")
async def pay_handler(event):
    yunhu = sdk.adapter.get(event.get_platform())
    user_id = event.get_user_id()
    # 發送成功後才扣積分
    await (yunhu.Send.To(event.get_detail_type(), event.get_target_id())
           .Hook(lambda r: sdk.storage.set(f"points:{user_id}", -10))
           .Text("支付成功，已扣除 10 積分"))
```

### 失敗重試 + 超時取消

```python
@command("notice", help="發送重要通知")
async def notice_handler(event):
    adapter_inst = sdk.adapter.get(event.get_platform())
    # 最多重試 3 次，每次超時 10 秒
    task = (adapter_inst.Send.To(event.get_detail_type(), event.get_target_id())
            .Retry(3)
            .Timeout(10)
            .OnError(lambda ctx: sdk.logger.error(f"通知發送失敗: {ctx.error}"))
            .Text("這是一條重要通知"))
    # 不等待，後台發送
```

### 批量發送多條消息

一條鏈路發多條消息，統一執行：

```python
@command("announce", help="發送公告")
async def announce_handler(event):
    adapter_inst = sdk.adapter.get(event.get_platform())
    # 建構多條消息，統一發送（預設並行）
    results = await (adapter_inst.Send.To(event.get_detail_type(), event.get_target_id())
                    .Build()
                    .Text("📋 今日公告")
                    .Image("https://example.com/banner.jpg")
                    .Text("詳細內容見上方圖片")
                    .Retry(2)            # 失敗的條目各自重試
                    .send_all())
    sdk.logger.info(f"批量發送完成，共 {len(results)} 條")
```

> 更完整的規則與批量說明請參考 [平台特性指南](../platform-guide/README.md#發送規則裝飾器)。

## 權限控制

### 管理員檢查

```python
# 配置主人列表
MASTERS = ["user123", "user456"]

def is_master(user_id):
    """檢查是否為框架主人"""
    return user_id in MASTERS

@command("master", help="框架主人命令")
async def master_handler(event):
    user_id = event.get_user_id()
    
    if not is_master(user_id):
        await event.reply("權限不足，此命令僅框架主人可用")
        return
    
    await event.reply("框架主人命令執行成功")

@command("addmaster", help="新增框架主人")
async def addmaster_handler(event):
    if not is_master(event.get_user_id()):
        return
    
    args = event.get("text", "").split()
    if len(args) < 2:
        await event.reply("用法: /addmaster <用戶ID>")
        return
    
    new_master = args[0]
    MASTERS.append(new_master)
    await event.reply(f"已新增框架主人: {new_master}")
```

### 群組權限

```python
@command("groupinfo", help="查看群組資訊")
async def groupinfo_handler(event):
    if not event.is_group_message():
        await event.reply("此命令僅限群聊使用")
        return
    
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"群組 ID: {group_id}, 你的 ID: {user_id}")
```

## 消息統計

### 消息計數

> **注意**：以下示例使用 `sdk.storage.get/set` 進行簡單計數。在高併發場景下，建議使用 `sdk.storage.transaction()` 以保證原子性。

```python
@message.on_message()
async def count_handler(event):
    # 獲取統計
    stats = sdk.storage.get("message_stats", {
        "total": 0,
        "by_user": {},
        "by_day": {}
    })
    
    # 更新統計
    stats["total"] += 1
    
    user_id = event.get_user_id()
    stats["by_user"][user_id] = stats["by_user"].get(user_id, 0) + 1
    
    # 保存
    sdk.storage.set("message_stats", stats)

@command("stats", help="查看消息統計")
async def stats_handler(event):
    stats = sdk.storage.get("message_stats", {
        "total": 0,
        "by_user": {},
        "by_day": {}
    })
    
    top_users = sorted(
        stats["by_user"].items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]
    
    top_text = "\n".join(
        f"{uid}: {count} 條消息" for uid, count in top_users
    )
    
    await event.reply(f"總消息數: {stats['total']}\n\n活躍用戶:\n{top_text}")
```

## 搜尋功能

### 簡單搜尋

> **注意**：以下示例使用記憶體列表儲存訊息歷史，**程式重啟後資料會遺失**。生產環境建議使用 `sdk.storage` 或 SQLite 表進行持久化儲存。

```python
from ErisPulse.Core.Event import command, message

# 儲存訊息歷史
message_history = []

@message.on_message()
async def store_handler(event):
    """儲存訊息用於搜尋"""
    user_id = event.get_user_id()
    text = event.get_text()
    
    message_history.append({
        "user_id": user_id,
        "text": text,
        "time": event.get_time()
    })
    
    # 限制歷史記錄數量
    if len(message_history) > 1000:
        message_history.pop(0)

@command("search", help="搜尋訊息")
async def search_handler(event):
    args = event.get_command_args()
    
    if not args:
        await event.reply("請輸入搜尋關鍵字")
        return
    
    keyword = " ".join(args)
    results = []
    
    # 搜尋歷史記錄
    for msg in message_history:
        if keyword in msg["text"]:
            results.append(msg)
    
    if not results:
        await event.reply("未找到匹配的訊息")
        return
    
    # 顯示結果
    result_text = f"找到 {len(results)} 條匹配訊息:\n\n"
    for i, msg in enumerate(results[:10], 1):  # 最多顯示 10 條
        result_text += f"{i}. {msg['text']}\n"
    
    await event.reply(result_text)
```

## 圖片處理

### 圖片下載和存儲

```python
from ErisPulse.Core import client

@message.on_message()
async def image_handler(event):
    """處理圖片訊息"""
    message_segments = event.get_message()
    
    for segment in message_segments:
        if segment.get("type") == "image":
            file_url = segment.get("data", {}).get("file")
            
            if file_url:
                # 推薦使用 SDK 內建客戶端下載圖片
                resp = await client.get(file_url)
                if resp.status == 200:
                    image_data = await resp.read()
                    
                    # 存儲到檔案
                    filename = f"images/{event.get_time()}.jpg"
                    with open(filename, "wb") as f:
                        f.write(image_data)
                    
                    sdk.logger.info(f"圖片已儲存: {filename}")
                    await event.reply("圖片已儲存")
```

### 圖片識別範例

> **注意**：以下範例使用佔位 API 地址，實際使用時請替換為你自己的圖片識別服務。

```python
from ErisPulse.Core import client

@command("identify", help="識別圖片")
async def identify_handler(event):
    """識別訊息中的圖片"""
    message_segments = event.get_message()
    
    for segment in message_segments:
        if segment.get("type") == "image":
            file_url = segment.get("data", {}).get("file")
            
            # 調用圖片識別 API
            result = await _identify_image(file_url)
            
            await event.reply(f"識別結果: {result}")
            return
    
    await event.reply("未找到圖片")

async def _identify_image(url):
    """調用圖片識別 API（範例）- 使用 SDK 內建客戶端"""
    resp = await client.post(
        "https://api.example.com/identify",
        json={"url": url}
    )
    data = await resp.json()
    return data.get("description", "識別失敗")
```

## IDE 补全

> 来源: `docs/zh-TW/getting-started/ide-completion.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-TW/getting-started/ide-completion.md）

# 類型存根生成（IDE 補全）

> [!TIP]
> **何時需要閱讀本文**：當 IDE 補全無法顯示適配器的平台特定方法（如雲湖的 `Board`）或模組的自訂方法時，只需執行一條 `epsdk types` 命令生成類型存根即可解決；若不需要則可跳過。

ErisPulse 透過 entry-points 動態發現模組/適配器，入口點無法在靜態層面得知使用者類別的具體類型。  
`epsdk types` 命令透過掃描已安裝的模組/適配器，生成一個類型存根檔案，讓使用者可以將這些類型作為變數標註，進而獲得 IDE 補全功能。

## 核心設計原則

存根檔案**只導出類型**，不提供任何執行時實例：

- 所有匯入都在 ``TYPE_CHECKING`` 下，**零執行時開銷、零行為改變**
- 類型名採用 entry-point 名的 PascalCase 形式（如 ``yunhu`` → ``Yunhu``），與傳入 ``sdk.adapter.get()`` / ``sdk.module.get()`` 的名稱對應
- 使用者在程式碼中照常用 ``sdk.module.get(...)`` / ``sdk.adapter.get(...)`` 取得實例，只是用匯入的類型做**變數標註**

## 基本用法

在專案根目錄執行：

```bash
epsdk types
```

會在當前目錄產生 `_ep_types.py`，包含所有已安裝模組/適配器的類型。

## 在程式碼中使用

```python
from _ep_types import MyModule, Yunhu
from ErisPulse import sdk

# 使用導入的類型作為變數標註，即可讓 IDE 自動補全該類的方法
my_mod: MyModule = sdk.module.get("MyModule")
my_mod.hello()                  # ← IDE 自動補全 hello

my_adapter: Yunhu = sdk.adapter.get("yunhu")
await my_adapter.Send.To("group", "123").Board(...)   # ← 自動補全平台特有方法
```

## 工作原理

1. 掃描 `erispulse.adapter` / `erispulse.module` entry-points  
2. 透過子進程在目標 Python 環境中內省，收集每個適配器/模組的實際類資訊（包含模組路徑與限定名）  
3. 產生 `.py` 檔，其中：  
   - 所有 ``from xxx import Yyy as Zzz`` 都在 ``TYPE_CHECKING`` 下  
   - ``Zzz`` 是 entry-point 名的 PascalCase 形式  
4. IDE 讀取 ``TYPE_CHECKING`` 部分提供補全；執行時不執行任何程式碼  

產生的存根範例：

```python
# _ep_types.py（自動產生）
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # 適配器
    from MyAdapter.Core import MyAdapter as MyAdapter
    from YunhuAdapter.Core import YunhuAdapter as Yunhu

    # 模組
    from MyModule.Core import Main as MyModule

    __all__ = ['MyAdapter', 'Yunhu', 'MyModule']
```

## 命令選項

| 選項 | 說明 |
|------|------|
| `-o, --output PATH` | 指定輸出檔案路徑（預設 `./_ep_types.py`） |
| `--force` | 覆蓋已存在的存根檔案 |
| `--adapters-only` | 僅掃描適配器 |
| `--modules-only` | 僅掃描模組 |

## 何時重新產生

- 安裝/解除安裝新的模組或適配器後
- 模組/適配器更新了公開 API 後
- IDE 自動完成失效或類型過期時

## 與 SendDSL 標準方法的關係

`SendDSL` 基類已內建標準發送方法（Text/Image/Voice/Video/File），無論以何種方式取得的 SendDSL 實例都能補全這些方法。  
`types` 命令主要用於補全**平台特有方法**（如雲湖的 `Board`、沙盒的 `Dice`）以及**模組特有方法**。
