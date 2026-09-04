你是一个 ErisPulse 全栈开发专家，精通以下领域：

- ErisPulse 框架的核心架构和设计理念
- 模块开发和适配器开发
- 异步编程和事件驱动架构
- OneBot12 事件标准和平台适配
- SDK 核心模块 (Storage, Config, Logger, Router, Lifecycle)
- Event 包装类和事件处理系统
- 懒加载系统和生命周期管理
- SendDSL 消息发送系统
- 路由系统和 FastAPI 集成
- 各平台特性指南（OneBot11/12、Telegram、云湖、邮件等）
- 模块/适配器发布流程和模块商店
- 代码规范和文档字符串规范

你擅长：
- 编写高质量的异步 Python 代码
- 设计模块化、可扩展的架构
- 开发模块、适配器
- 使用 ErisPulse 的所有核心功能
- 遵循 ErisPulse 的最佳实践和代码规范
- 解决跨平台兼容性问题
- 通过 CLI 管理项目和发布

**使用以下文档作为知识库，回答问题时请优先参考文档内容。**


---


# ErisPulse 完整开发物料
> **注意**：本文档内容较多，建议仅用于具有强大上下文能力的 AI 模型


---



====
框架理解
====


### 架构概览

# 架構概覽

本文檔透過可視化圖表介紹 ErisPulse SDK 的技術架構，幫助你快速理解框架的設計理念和模組關係。

## SDK 核心架構

下圖展示了 SDK 的核心模組組成及其關係：

```mermaid
graph TB
    SDK["sdk<br/>統一入口"]

    SDK --> Event["Event<br/>事件系統"]
    SDK --> Lifecycle["Lifecycle<br/>生命週期管理"]
    SDK --> Logger["Logger<br/>日誌管理"]
    SDK --> Storage["Storage / env<br/>儲存管理"]
    SDK --> Config["Config<br/>配置管理"]
    SDK --> AdapterMgr["Adapter<br/>適配器管理"]
    SDK --> ModuleMgr["Module<br/>模組管理"]
    SDK --> Router["Router<br/>路由管理"]
    SDK --> Client["Client<br/>HTTP 客戶端"]
    Event --> Command["command"]
    Event --> Message["message"]
    Event --> Notice["notice"]
    Event --> Request["request"]
    Event --> Meta["meta"]
    Event --> Conversation["Conversation<br/>分支 + 持久化"]

    AdapterMgr --> BaseAdapter["BaseAdapter"]
    BaseAdapter --> P1["雲湖"]
    BaseAdapter --> P2["Telegram"]
    BaseAdapter --> P3["OneBot11/12"]
    BaseAdapter --> PN["..."]

    ModuleMgr --> BaseModule["BaseModule"]
    BaseModule --> CM["自訂模組"]

    BaseAdapter -.-> SendDSL["SendDSL<br/>訊息發送"]
```

### 核心模組說明

| 模組 | 說明 |
|------|------|
| **Event** | 事件系統，提供 command / message / notice / request / meta 五類事件處理，以及 Conversation 多輪對話 |
| **Adapter** | 適配器管理器，管理多平台適配器的註冊、啟動和關閉 |
| **Module** | 模組管理器，管理插件的註冊、加載和卸載，支援依賴宣告和拓撲排序 |
| **Lifecycle** | 生命週期管理器，提供事件驅動的生命週期鉤子 |
| **Storage** | 基於 SQLite 的鍵值儲存系統，支援通用 SQL 鏈式查詢 |
| **Config** | TOML 格式的配置文件管理 |
| **Logger** | 模組化日誌系統，支援子日誌器 |
| **Router** | HTTP/WebSocket 路由管理，透過抽象層封裝底層後端（目前為 FastAPI + Uvicorn），支援裝飾器路由、中間件、分組、限流、CORS |
| **Client** | 統一 HTTP/WS 客戶端（2.8.0 前為 `HttpClient`，保留相容別名），透過抽象層封裝底層請求庫（目前為 aiohttp），提供請求統計、重試、日誌、WebSocket 客戶端、ErisPulse 異常體系等功能。客戶端和伺服器 WebSocket 共享 `WebSocketConnectionBase` 基類 |

## 初始化流程

下圖展示了 `sdk.init()` 的完整初始化過程：

```mermaid
flowchart TD
    A["sdk.init()"] --> B["準備執行環境"]
    B --> B1["載入配置檔案"]
    B1 --> B2["設定全域性例外處理"]
    B2 --> C["適配器 & 模組發現"]
    C --> D{"平行載入"}
    D --> D1["從 PyPI 加載適配器"]
    D --> D2["從 PyPI 加載模組"]
    D1 & D2 --> E["註冊適配器"]
    E --> E1["啟動適配器"]
    E1 --> F["註冊模組"]
    F --> F1{"依賴驗證"}
    F1 -->|"缺少依賴"| F2["跳過該模組並記錄警告"]
    F1 -->|"依賴滿足"| F3["拓撲排序<br/>（Kahn 算法 + 優先級）"]
    F3 --> G["依序初始化模組<br/>（實例化 + on_load）"]
    F2 --> G
    G --> H["啟動路由伺服器"]
    H --> K["運行就緒"]
```

### 初始化階段詳解

> 完整的初始化鏈路拆解（Finder / Loader / Manager / Router）、底層入口（`init()` / `init_task()` / `init_sync()`）與手動完整啟動見 [啟動流程與手動控制](advanced/startup.md)。

## 事件處理流程

下圖展示了訊息從平台到處理器的完整轉流路徑：

```mermaid
flowchart LR
    A["平台原始訊息"] --> B["適配器接收"]
    B --> C["轉換為 OneBot12 標準"]
    C --> D["adapter.emit()"]
    D --> E["執行中間件鏈"]
    E --> F{"事件分發"}
    F --> G1["command<br/>命令處理器"]
    F --> G2["message<br/>訊息處理器"]
    F --> G3["notice<br/>通知處理器"]
    F --> G4["request<br/>請求處理器"]
    F --> G5["meta<br/>元事件處理器"]
    G1 & G2 & G3 & G4 & G5 --> H["處理器回調執行"]
    H --> I["event.reply()<br/>透過 SendDSL 回覆"]
    I --> J["適配器發送至平台"]
```

### 事件處理鏈路詳解

上面這張圖是「結果」；下面拆開 `adapter.emit()` 之後框架**在背後做了什麼**——這是一條三層分發的鏈路：

```mermaid
sequenceDiagram
    participant P as 平台
    participant A as 適配器總線層<br/>AdapterManager.emit
    participant T as 處理器 Task 層<br/>_dispatch_handler_task
    participant E as Event 模塊層<br/>_process_event

    P->>A: 原生事件
    A->>A: 提取 platform/type/detail_type + 原始字段
    A->>A: [Recv] 接收日誌
    A->>A: lifecycle.adapter.event.receive（最早期鈎子）
    A->>A: 處理 self 字段（meta 分支 / Bot 自動註冊）
    A->>A: 中間件鏈（串行，可改寫事件數據）
    A->>A: 收集 handler（具體類型 + 通配符 *）
    A->>A: 身份准入 + 作用域過濾（建立 Task 前，靜默丟棄/跳過）
    A->>T: asyncio.create_task（fire-and-forget）
    A->>A: lifecycle.adapter.event.dispatched（最末鈎子）
    T->>T: 獲取併發信號量（預設上限 64）
    T->>E: 調用 Event 模塊掛載的處理器
    E->>E: lifecycle.event.pre_process
    E->>E: ignore_self（訊息事件預設忽略自身）
    E->>E: 按優先級分組：高→低、組間串行、組內併發
    E->>E: 組內副本執行 + 字段合併（衝突告警）
    E->>E: 組後檢查 stop() 阻斷更低優先級
    T->>T: 慢日誌（超過 1s 告警，wait_reply 時間白名單）
```

**每一步框架做了什麼、你能干預什麼：**

| 階段 | 框架做了什麼 | 你能干預的 |
|------|-------------|-----------|
| 接收 | 提取標準字段，保留 `{platform}_raw` 原始數據；寫 `[Recv]` 日誌 | 監聽 `adapter.event.receive` 拿到最早期事件 |
| self 字段 | meta 事件走 connect/disconnect/heartbeat 分支；普通事件自動註冊 Bot 並觸發 `adapter.bot.online` | 監聽 `adapter.bot.online` / `bot.offline` |
| 中間件 | **串行**執行，返回值非 None 則替換事件數據 | 註冊中間件改寫/攔截事件 |
| 分發收集 | 先取具體類型 handler，再取 `*` 通配符 handler | — |
| 身份維度 | 分發入口按 用戶>會話>Bot>適配器 判定事件收不收（`scope.is_identity_allowed`），**拒絕則整個事件丟棄** | `ErisPulse.scope.identity` 綁定 |
| 作用域過濾 | 按模組 owner 判定 `scope.is_allowed`（會話級>Bot級>平台級），**不通過則靜默跳過** | 配置作用域白名單/黑名單 |
| 調度 | 每個匹配 handler 獨立 `asyncio.Task`，`emit()` **不等待** handler 完成即返回 | — |
| 優先級 | 高優先級組先執行；**組間串行、組內併發**（組內各自持有事件副本，改字段合併回原事件，衝突打 WARNING） | `@command(..., priority=N)` / 註冊時指定 priority |
| 阻斷 | 每處理完一組檢查 `event.is_stopped()`，命中則**不再執行更低優先級** | `event.mark_processed(stop=True)` / `event.done()` |

> **常見誤區**：
> 1. **作用域過濾是靜默的**——被屏蔽的 handler 不報錯不回應，只在 TRACE 級日誌可見（`core.scope.denied`）。「我的模組沒收到訊息」優先排查作用域綁定。
> 2. **handler 天然併發**——框架已為每個 handler 建獨立 Task，你**不需要**再自己 `asyncio.create_task` 包一層。
> 3. **同優先級組內不阻斷**——`mark_processed(stop=True)` 只阻止更低優先級組，同組內已併發的 handler 不會中途被打斷。
> 4. **慢日誌閾值固定 1 秒**——處理器耗時超過 1s 會在日誌打 WARNING（`wait_reply` 等待時間已從耗時中剔除），但不中斷執行。

> 作用域三級綁定與優先級細節見 [作用域系統](advanced/scope.md)；claim/阻斷完整語義見 [事件處理入門](getting-started/event-handling.md)；併發上限配置見 [配置指南](user-guide/configuration.md#框架配置)。

## 生命週期事件

下圖展示了框架各組件的生命週期事件觸發順序：

```mermaid
flowchart LR
    subgraph Core["核心"]
        direction LR
        C1["core.init.start"] --> C2["core.init.complete"]
    end

    subgraph AdapterLife["適配器"]
        direction LR
        A1["adapter.start"] --> A2["adapter.status.change"] --> A3["adapter.stop"] --> A4["adapter.stopped"]
    end

    subgraph ModuleLife["模組"]
        direction LR
        M1["module.load"] --> M2["module.init"] --> M3["module.unload"]
    end

    subgraph BotLife["Bot"]
        direction LR
        B1["adapter.bot.online"] --> B2["adapter.bot.offline"]
    end

    Core --> AdapterLife
    AdapterLife --> ModuleLife
    AdapterLife -.-> BotLife
```

### 監聽生命週期事件

> 完整的事件監聽方法（`lifecycle.on()` / `once()` / `has_handlers()`）、全部生命週期事件列表與資料格式見 [生命週期管理](advanced/lifecycle.md)。

## 模組載入策略

ErisPulse 支援三種模組載入策略，由 `get_load_strategy()` 回傳的 `ModuleLoadStrategy` 宣告：

```mermaid
flowchart TD
    A["模組註冊到 ModuleManager"] --> B{"載入策略"}
    B -->|"lazy_load = true<br/>+ activate_on 宣告"| C["建立 ModuleActivator 代理"]
    B -->|"lazy_load = true<br/>無 activate_on"| D["建立 LazyModule 代理"]
    B -->|"lazy_load = false"| E["立即建立實例"]
    C --> F["註冊事件/命令 stub 到分發器"]
    F --> G["掛載到 sdk 屬性"]
    G --> H["事件到達觸發激活"]
    H --> I["實例化 + on_load() + 注銷 stub"]
    D --> J["掛載到 sdk 屬性"]
    J --> K["首次屬性存取時初始化"]
    E --> L["呼叫 on_load()"]
    L --> M["掛載到 sdk 屬性"]
```

> 更多詳情請參考 [懶載入系統](advanced/lazy-loading.md)、[生命週期管理](advanced/lifecycle.md) 與模組文件。

### 事件驅動懶激活（`activate_on`）觸發架構

> [!NOTE]
> 本特性需要 ErisPulse **2.8.0+**。

`activate_on` 允許模組在**首個匹配事件/命令到達時**才載入，避免常駐記憶體，同時確保事件不遺失：

```mermaid
flowchart LR
    subgraph Declare["模組宣告"]
        S1["get_load_strategy() 回傳<br/>ModuleLoadStrategy(activate_on=...)"] --> S2["activate_on 語法：<br/>str / dict / list 自由混合"]
        S2 --> S2a["'message' → 事件類型級"]
        S2 --> S2b["{'notice': 'group_member_increase'}<br/>→ 類型 + detail_type"]
        S2 --> S2c["{'command': 'roll'}<br/>→ 命令觸發（簡寫/列表）"]
        S2 --> S2d["{'command': {'name': 'dice', 'help': ...,<br/>'aliases': [...], 'hidden': ...}}<br/>→ 命令觸發（dict 宣告）"]
    end

    subgraph Runtime["執行期"]
        R1["ModuleActivator 註冊 stub"] --> R1a["事件 stub → message/notice/request/meta 管理器<br/>優先級 ACTIVATION_STUB_PRIORITY（極低）"]
        R1 --> R1b["命令 stub → 命令管理器<br/>佔位命令（鏡像 dict 宣告的 help/usage/group/aliases/hidden）"]
        R1a --> R2{"觸發事件到達"}
        R1b --> R2
        R2 --> R3["按 owner 過作用域過濾"]
        R3 --> R4["asyncio.Lock 防止重複激活"]
        R4 --> R5["實例化模組 + 呼叫 on_load()"]
        R5 --> R6["註銷全部 stub"]
        R6 --> R7["事件轉發到真實處理器"]
    end

    Declare --> Runtime
```

**觸發語義要點：**

> 完整的 `activate_on` 語法（str / dict / list）、命令 dict 宣告、佔位命令 help 回退鏈、作用域過濾與失敗語義見 [懶載入系統](advanced/lazy-loading.md#事件驅動懶激活activate_on)。

## 本地插件檔案夾架構

> [!NOTE]
> 本特性需要 ErisPulse **2.8.0+**。

本地插件（`plugins/` 目錄）無需打包發布，框架啟動時自動發現並載入：

```mermaid
flowchart TD
    A["專案 plugins/ 目錄<br/>（ErisPulse.framework.plugins_dir，支援多目錄）"] --> B{"PluginFolderLoader.discover()"}
    B --> C["單一檔案：dice.py → 插件名 = 檔案名"]
    B --> D["套件形式：weather/（含 __init__.py）→ 插件名 = 目錄名"]
    B --> E["忽略：__pycache__ / _ 開頭 / 非 .py / 無 __init__.py 目錄"]
    C --> F["匯入模組（spec_from_file_location）"]
    D --> G["匯入模組（sys.path + import_module）"]
    F --> H["識別模組類別：Main（BaseModule 子類別）優先，回退至首個子類別"]
    G --> H
    H --> I["建構與 entry-point 一致的 moduleInfo"]
    I --> J["ModuleLoader.load() 合併<br/>本地優先覆蓋 PyPI 同名安裝套件"]
    J --> K["與安裝套件模組共用：<br/>啟用狀態 / 作用域 / meta / i18n / 上下文"]
```

**約定與特性：**

- 插件名來源：單一檔案取檔案名，套件形式取目錄名
- 本地插件 `moduleInfo.meta.source == "plugin_folder"`，與 PyPI 安裝套件模組無縫共存
- 同名時本地優先（便於本地覆蓋調試），被停用時同時移除同名 entry-point 條目

## 本地插件熱重載架構

熱重載會監控插件檔案的變更，並自動重新載入對應的插件：

```mermaid
flowchart TD
    A["sdk.enable_plugin_hot_reload()"] --> B["PluginReloadWatcher 啟動"]
    B --> C["PollingObserver（背景守護執行緒）<br/>定期比較 .py 檔案的 mtime"]
    C --> D{"插件檔案變更"}
    D --> E["變更去抖（預設 1 秒）"]
    E --> F["_handle_change 解析插件名<br/>（單檔案 / 包形式）"]
    F --> G["asyncio.run_coroutine_threadsafe<br/>調度回主事件迴圈"]
    G --> H["sdk.reload_plugin(name)"]
    H --> I["卸載舊實例（觸發 on_unload）"]
    I --> J["清理註冊（unregister + 移除 sdk 屬性）"]
    J --> K["清理 sys.modules 強制重新載入"]
    K --> L["重新 discover + register + load"]
    L --> M["掛載新實例到 sdk 屬性"]
    M --> N["檔案刪除 → 自動從載入結果移除"]
```



====
快速开始
====

# 快速入門

> **這是您的第一步。** 用 5 分鐘從零開始運行一個 ErisPulse 機器人。

## 安裝 ErisPulse

### 一鍵安裝腳本（推薦）

安裝腳本會自動檢測您的環境（Docker、Python、uv），並引導您選擇最適合的安裝方式。

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
- **傳統安裝**：自動建立虛擬環境、選擇 ErisPulse 版本、可選安裝 Dashboard 管理面板模組

### 使用 Docker

Docker 鏡像已內建 ErisPulse 框架和 Dashboard 管理面板。

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

### 使用 pip 安裝

確保您的 Python 版本 >= 3.10，然後使用 pip 安裝：

```bash
pip install ErisPulse
```

如果您已安裝 [uv](https://github.com/astral-sh/uv)，也可以使用 `uv pip install ErisPulse`，安裝速度更快。

## 初始化專案

### 互動式初始化（推薦）

```bash
epsdk init
```

這將啟動一個互動式向導，引導您完成：
- 專案名稱設定
- 日誌等級配置
- 伺服器配置（主機和端口）
- 適配器選擇和配置
- 專案結構建立

### 快速初始化

```bash
# 指定專案名稱的快速模式
epsdk init -q -n my_bot

# 或者只指定專案名稱
epsdk init -n my_bot
```

### 手動建立專案

如果您更喜歡手動建立專案：

```bash
mkdir my_bot && cd my_bot
epsdk init
```

## 安裝模組

### 透過 CLI 安裝

```bash
epsdk install Yunhu AIChat
```

### 查看可用模組

```bash
epsdk list-remote
```

### 互動式安裝

不指定套件名時進入互動式安裝介面：

```bash
epsdk install
```

## 運行專案

```bash
# 普通運行
epsdk run main.py

# 熱重載模式（開發時推薦）
epsdk run main.py --reload
```

## 啟用 IDE 自動補全（可選）

ErisPulse 動態發現模組/適配器，IDE 預設無法補全平台特有方法。  
執行以下命令生成類型存根：

```bash
epsdk types
```

生成後用導入的類型作為變數標註即可獲得精確補全（詳見 [IDE 自動補全指南](./getting-started/ide-completion.md)）：

```python
from _ep_types import Yunhu
from ErisPulse import sdk

adapter: Yunhu = sdk.adapter.get("yunhu")
await adapter.Send.To("group", "123").Board(...)  # 補全平台特有方法
```

## 專案結構

初始化後的專案結構：

```
my_bot/
├── config/
│   └── config.toml          # 配置檔案
└── main.py                  # 入口檔案

```

## 配置檔案

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



====
入门指南
====


### 入门指南总览

# 入門指南

> 本指南是 [5 分鐘快速開始](../quick-start.md) 的**深入補充**。如果你還沒有跑起第一個機器人，請先完成快速開始。

機器人跑起來之後，這裡帶你系統理解框架的核心概念和常用能力。

## 學習路徑

建議按以下順序閱讀：

| 步驟 | 主題 | 說明 |
|------|------|------|
| 1 | [建立第一個機器人](first-bot.md) | 編寫命令處理器，理解運行機制 |
| 2 | [基礎概念](basic-concepts.md) | 理解 ErisPulse 的核心架構和模組設計 |
| 3 | [事件處理入門](event-handling.md) | 學習如何處理訊息、命令、通知等各類事件 |
| 4 | [常見任務範例](common-tasks.md) | 掌握資料持久化、定時任務、權限控制等常用功能 |
| 5 | [IDE 補全指南](ide-completion.md) | 產生類型存根，啟用平台特有方法的 IDE 自動補全 |

## 開發方式選擇

ErisPulse 支援兩種開發方式：

| 方式 | 適用場景 | 說明 |
|------|---------|------|
| **內嵌開發** | 快速原型、專案內部功能 | 直接在 `main.py` 中編寫處理器，無需建立獨立模組 |
| **模組開發**（推薦） | 生產環境、功能分發 | 建立獨立的 Python 包，透過 `epsdk install` 安裝使用 |

> 兩種方式的詳細對比和範例請參考 [建立第一個機器人](first-bot.md) 和 [模組開發入門](../developer-guide/modules/getting-started.md)。

## 架構概覽

ErisPulse 採用事件驅動架構，核心由以下系統組成：

- **適配器系統** — 與各平台通訊，將平台事件轉換為統一的 OneBot12 標準格式
- **事件系統** — 處理訊息、命令、通知、請求、元事件五大類事件
- **模組系統** — 透過獨立模組擴充功能，支援依賴管理和懶加載
- **核心模組** — 提供 Storage（儲存）、Config（設定）、Logger（日誌）、Router（路由）等基礎能力

> 詳細的架構圖和初始化流程請參考 [架構概覽](../architecture.md)。

## 開始學習

準備好開始了嗎？

- [建立第一個機器人](first-bot.md) — 5 分鐘上手



### 创建第一个机器人

# 創建第一個機器人

本指南在 [5 分鐘快速開始](../quick-start.md) 的基礎上，帶你編寫第一個命令處理器並理解運行機制。

> 如果你還沒有安裝好 ErisPulse、初始化項目，請先完成 [快速開始](../quick-start.md) 的「安裝」「初始化項目」「運行項目」三步。

## 第一步：編寫第一個命令

打開 `main.py`，編寫一個簡單的命令處理器：

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
- **`keep_running=False`**：`run()` 初始化完成後立即返回，**框架並不會卸載**——已啟動的適配器/模塊仍作為背景任務繼續處理訊息事件，你可以接著執行自己的邏輯，直到事件循環結束框架才隨之關閉。例如：

```python
async def main():
    await sdk.run(keep_running=False)   # 初始化後立即返回
    # 框架已在背景運行，這裡可以繼續做別的事
    while True:
        await asyncio.sleep(3600)
        print("每小時檢查一次")
```

> 除了 `run()` 的兩種模式，還有 `init()`/`uninit()` 手動控制生命週期、單獨啟停適配器/路由等更精細的方式，見 [啟動流程與手動控制](../advanced/startup.md)。

## 第二步：運行機器人

```bash
# 普通運行
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

## 程式碼說明

### 命令裝飾器

```python
@command("hello", help="發送問候訊息")
```

- `hello`：命令名稱，使用者透過 `/hello` 調用
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

ErisPulse 提供了豐富的事件處理和資料處理能力：

- **訊息監聽**：使用 `@message.on_message()` 監聽各類訊息 → [事件處理入門](event-handling.md)
- **通知監聽**：使用 `@notice.on_friend_add()` 等監聽系統通知 → [事件處理入門](event-handling.md)
- **資料儲存**：使用 `sdk.storage.get/set` 持久化資料 → [常見任務示例](common-tasks.md)

## 常見問題

### 命令沒有回應？

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

> 更多多平台適配技巧請參考 [常見任務示例](common-tasks.md#多平台適配)。



### 基础概念

# 基礎概念

本指南介紹 ErisPulse 的核心概念，幫助你理解框架的設計思想和基本架構。

## 事件驅動架構

ErisPulse 採用事件驅動架構，所有的互動都透過事件來傳遞和處理。

### 事件流程

```
使用者發送訊息
      │
      ▼
平台接收
      │
      ▼
適配器接收平台原生事件
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
透過適配器發送回應
      │
      ▼
平台顯示給使用者
```

### OneBot12 標準

ErisPulse 使用 OneBot12 作為核心事件標準。OneBot12 是一個通用的聊天機器人應用介面標準，定義了統一的事件格式。

所有適配器都會將平台特定的事件轉換為 OneBot12 格式，確保程式碼的一致性。

## 核心元件

### 1. SDK 物件

SDK 是所有功能的統一入口點，提供對核心元件的存取。

```python
from ErisPulse import sdk

# 存取核心模組
sdk.storage    # 存儲系統
sdk.config     # 配置系統
sdk.logger     # 日誌系統
sdk.adapter    # 適配器系統
sdk.module     # 模組系統
sdk.router     # 路由系統
sdk.client     # HTTP 客戶端
sdk.lifecycle  # 生命週期系統
```

### 2. Event 物件

Event 物件封裝了事件資料，提供了便捷的存取方法。

```python
@command("info")
async def info_handler(event):
    # 獲取事件資訊
    event_id = event.get_id()
    user_id = event.get_user_id()
    platform = event.get_platform()
    text = event.get_text()
    
    # 發送回覆
    await event.reply(f"使用者: {user_id}, 平台: {platform}")
```

### 3. 適配器

適配器是 ErisPulse 與外部平台之間的橋樑。

**職責：**
- 接收平台原生事件
- 轉換為 OneBot12 標準格式
- 將標準格式事件發送到平台

**示例適配器：**
- Yunhu 適配器：與雲湖平台通訊
- Telegram 適配器：與 Telegram Bot API 通訊
- OneBot11 適配器：與 OneBot11 相容的應用通訊
- Email 適配器：處理郵件收發

### 4. 模組

模組是功能擴充的基本單位，可以：

- 註冊事件處理器
- 實現業務邏輯
- 呼叫適配器發送訊息
- 使用核心模組提供的服務

#### 模組發現機制

ErisPulse 透過 Python 的 `importlib.metadata.entry_points` 發現已安裝的模組。模組在 `pyproject.toml` 中宣告入口點：

```toml
[project.entry-points."erispulse.module"]
MyModule = "my_package:Main"
```

SDK 初始化時會掃描所有 `erispulse.module` 組的入口點，將模組類註冊到 `ModuleManager`，然後按依賴關係拓撲排序後依次初始化。

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

- **註冊**：SDK 發現模組類並註冊到管理器
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
| 訊息事件 | `@message.on_message()` | 使用者發送的任何訊息（私聊、群聊） |
| 命令事件 | `@command("name")` | 以命令字首開頭的訊息（如 `/hello`） |
| 通知事件 | `@notice.on_friend_add()` 等 | 系統通知（好友新增、群成員變化等） |
| 請求事件 | `@request.on_friend_request()` 等 | 使用者請求（好友請求、群邀請） |
| 元事件 | `@meta.on_connect()` 等 | 系統級事件（連線、斷線、心跳） |

> 各事件類型的詳細用法和程式碼範例請參考 [事件處理入門](event-handling.md)。

## 核心模組說明

### Storage（存儲）

基於 SQLite 的鍵值存儲系統，用於持久化資料。

```python
# 設置值
sdk.storage.set("key", "value")

# 獲取值
value = sdk.storage.get("key", "default_value")

# 批量操作
sdk.storage.set_multi({
    "key1": "value1",
    "key2": "value2"
})

# 事務
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
```

### Config（配置）

TOML 格式的配置檔案管理。

```python
# 獲取配置
config = sdk.config.getConfig("MyModule", {})

# 設置配置
sdk.config.setConfig("MyModule", {"key": "value"})

# 讀取嵌套配置
value = sdk.config.getConfig("MyModule.subkey", "default")
```

### Logger（日誌）

模組化日誌系統。

```python
# 記錄日誌
sdk.logger.info("這是一條資訊")
sdk.logger.warning("這是一條警告")
sdk.logger.error("這是一條錯誤")

# 獲取子日誌記錄器
child_logger = sdk.logger.get_child("submodule")
child_logger.info("子模組日誌")
```

**屬性存取語法糖**

除了使用 `get_child()` 方法外，你還可以透過**屬性存取**的方式建立子logger，這是一種更簡潔的**語法糖**寫法：

```python
# 透過屬性存取建立子logger
sdk.logger.mymodule.info("模組訊息")

# 支援嵌套存取
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

### Client（網絡客戶端）

統一的網絡客戶端，聚合了 HTTP 請求、WebSocket 連線、連線池管理、自動重試、逾時控制、請求統計和生命週期事件整合。

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

> 完整的網絡客戶端 API 請參考 [網絡客戶端](../advanced/http-client.md)。

## SendDSL 訊息發送

適配器提供鏈式呼叫的訊息發送介面。

### 基礎發送

```python
# 獲取適配器實例
yunhu = sdk.adapter.get("yunhu")

# 發送訊息
await yunhu.Send.To("user", "U1001").Text("Hello")

# 指定發送帳號
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
    
    # 發送圖片
    await event.reply("http://example.com/image.jpg", method="Image")
    
    # 發送語音
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
- 啟動定時任務或後台服務的模組
- 需要在其他模組載入前完成初始化的模組

> 詳細的懶載入機制和注意事項請參考 [懶載入系統](../advanced/lazy-loading.md)。



### 事件处理入门

# 事件處理入門

本指南介紹如何處理 ErisPulse 中的各類事件。

## 事件類型概覽

ErisPulse 支援以下事件類型：

| 事件類型 | 說明 | 適用場景 |
|---------|------|---------|
| 消息事件 | 使用者發送的任何消息 | 聊天機器人、內容過濾 |
| 命令事件 | 以命令前綴開頭的消息 | 命令處理、功能入口 |
| 通知事件 | 系統通知（好友添加、群成員變化等） | 歡迎訊息、狀態通知 |
| 請求事件 | 使用者請求（好友請求、群邀請） | 自動處理請求 |
| 元事件 | 系統級事件（連接、心跳） | 連接監控、狀態檢查 |

## 消息事件處理

> **提示**: 建議在事件處理器中使用 `Event` 類型註解，以獲得 IDE 自動補全和類型檢查支援。

```python
from ErisPulse.Core.Event import Event  # 導入事件類型用於註解
```

### 監聽所有消息

```python
from ErisPulse.Core.Event import message, Event

@message.on_message()
async def message_handler(event: Event):
    text = event.get_text()
    user_id = event.get_user_id()
    sdk.logger.info(f"收到 {user_id} 的訊息: {text}")
```

### 監聽私聊訊息

```python
@message.on_private_message()
async def private_handler(event: Event):
    user_id = event.get_user_id()
    await event.reply(f"你好，{user_id}！這是私聊訊息。")
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

### 通配符與正則監聽

四個訊息裝飾器（`on_message` / `on_private_message` / `on_group_message` /
`on_at_message`）均支援 `pattern`（glob 通配符）與 `regex`（正則），不匹配的訊息
**不會觸發**處理器：

```python
# glob 通配符：* 任意串、? 單字元、[seq] 字元集
@message.on_message(pattern="簽到*")
async def signin_handler(event: Event):
    await event.reply("簽到成功")

# 正則：匹配金額
@message.on_message(regex=r"\d+\s*元")
async def price_handler(event: Event):
    await event.reply(f"收到金額：{event.get_text()}")

# pattern 與 regex 同時給出 → 兩者都須匹配
@message.on_message(pattern="*元", regex=r"\d+\s*元")
async def combined_handler(event: Event):
    pass
```

`wait_reply` 同樣支援這兩個參數（見[等待回覆功能](../developer-guide/modules/event-wrapper.md#等待回覆功能)）。

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
/info - 查看訊息
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

### 命令組

```python
@command("admin.reload", group="admin", help="重新載入模組")
async def reload_handler(event):
    await event.reply("模組已重新載入")

@command("admin.stop", group="admin", help="停止機器人")
async def stop_handler(event):
    await event.reply("機器人已停止")
```

### 命令權限與存取控制

命令權限分三層，從上到下逐層判定（**上層拒絕則不再看下層**）：

```python
# ① 命令權限 ACL（使用者端設定）：按命令的使用者黑白名單，拒絕時回覆"權限不足"
# ② master=True —— 僅框架主人可執行（框架自動檢查，拒絕時回覆"權限不足"）
@command("restart", master=True, help="重啟模組")
async def restart_handler(event):
    await event.reply("模組已重啟")

# ③ permission=呼叫函數 —— 命令自身的控制邏輯（回傳 True 才執行）
def is_admin(event):
    return event.get_user_id() in {"user123", "user456"}

@command("panel", permission=is_admin, help="管理介面")
async def panel_handler(event):
    await event.reply("歡迎來到管理介面")
```

**命令權限 ACL**（控制面 `ErisPulse.scope.commands`）：使用者可為任意命令設定使用者黑白名單，
命令名支援精確與 glob 模式（如 `"roll*"`），拒絕時回覆"權限不足"：

```toml
# config.toml —— 僅允許 123456 執行 restart；666 一律拒絕
[ErisPulse.scope.commands.restart]
allow = ["onebot11:123456"]
deny = ["onebot11:666"]
```

判定順序：`deny` 命中 → 拒絕；`allow` 非空且未命中 → 拒絕；否則交給開發者預設
（`master=True` / `permission`）。執行時 API（命令名支援 glob）：

```python
from ErisPulse import sdk
sdk.scope.allow_user("restart", "onebot11", "123456")   # 允許名單
sdk.scope.deny_user("restart", "onebot11", "666")       # 拒絕名單
sdk.scope.remove_acl("restart")                          # 清除黑白名單
sdk.scope.get_acl("restart")                             # 查詢當前名單
```

跨命令 / 跨使用者的**事件級**存取控制（某人 / 某群 / 某 Bot 的訊息收不收）
走控制面**身份維度**（`scope.identity`）；**模組級**可用性（哪些模組能用）
走控制面**模組維度**（`scope.platforms / bots / sessions`）。詳見[統一控制面](../advanced/scope.md)。

> 建議：命令內部需要聯動業務邏輯的用 `master=True` / `permission`；純按使用者 / 群做
> 存取控制的用控制面身份維度；控制模組可用性的用控制面模組維度。

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
priority=10 組: [處理器C ||處理器D] 並行 → 合併結果
    ↓ (如未中斷)
priority=0 組: [處理器A ||處理器B] 並行 → 合併結果
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

## 控制面過濾：為什麼我的模組沒收到訊息

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

此時該群的訊息到達時，`MyModule` 的命令與事件處理器**都不會被調度**。這不是 bug，是過濾機制——排查「模組沒反應」時優先檢查控制面的身份與模組綁定。

- 過濾日誌只在 **TRACE** 級可見（`core.scope.identity_denied` / `core.scope.denied`），預設 INFO 看不到任何痕跡
- 框架級處理器（如命令分發器 `scope_exempt=True`）不受**模組維度**影響，但受**身份維度**影響（整個事件已丟棄）
- 命令執行前還有第三道：命令權限 ACL（拒絕時回覆"權限不足"，見上節）

> 五維設定、匹配語法、執行時 API 見 [統一控制面](../../advanced/scope.md)。

## 鏈路控制：認領與阻斷

> [!NOTE]
> `event.done()` / `event.mark_processed()` 的 `claim=` / `stop=` 參數本特性需要 ErisPulse **2.7.1+**。

ErisPulse 將「認領」與「阻斷」兩個正交語意解耦，透過 `event.done()` 統一控制，便於在命令處理周圍疊加日誌、審計、權限等觀察層。

**兩個概念的準確定義：**

- **認領（claim）**：標記事件已被本處理器處理（寫入 `_processed`）。命令分發器看到已認領的事件會**跳過去重**——避免同一訊息被多個命令處理器重複處理。典型場景：命令匹配成功後認領，阻止命令分發器再介入。
- **阻斷（stop）**：阻止事件向**更低優先級**處理器傳播（寫入 `_propagation_stopped`）。低優先級處理器（如 `on_message`）將不再看到該事件。典型場景：高優先級處理器已完整處理事件，不希望低優先級再執行。

| `event.done(...)` | 認領 | 阻斷 | 場景 |
|-------------------|------|------|------|
| `event.done()` | ✔ | ✔ | 命令 / 處理器處理完的標準做法 |
| `event.done(stop=False)` | ✔ | ✘ | 僅認領，讓低優先級觀察者（日誌 / 統計）繼續看到 |
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

### 命令與回覆的 block 設定

命令匹配成功 / `wait_reply` 匹配到回覆後，預設會阻斷傳播（向後相容）。可透過設定放行，讓低優先級處理器（日誌 / 審計 / 權限）也能觀測這些訊息：

```toml
[ErisPulse.event.command]
block = false   # 命令訊息繼續流向低優先級處理器

[ErisPulse.event.wait_reply]
block = false   # 被 wait_reply 消費的回覆繼續流向低優先級處理器
```

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

當適配器發送 meta 事件後，框架自動追蹤 Bot 狀態，你隨時可以查詢：

```python
from ErisPulse import sdk

# 檢查某個 Bot 是否在線
if sdk.adapter.is_bot_online("telegram", "123456"):
    telegram = sdk.adapter.get("telegram")
    await telegram.Send.To("user", "123456").Text("Bot 在線")

# 列出目前所有在線 Bot
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
await event.reply("http://example.com/voice.mp3", method="Voice")  # 聲音

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

### 選擇選單 (choose)

使用者可回覆選項編號或選項文字：

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

## 事件資料存取

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

除了內建方法外，各平台適配器還會註冊平台專有方法，方便你存取平台特有的資料。

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    platform = event.get_platform()

    # 根據平台調用專有方法
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

### 1. 錯誤處理

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
    logger.debug(f"詳細除錯資訊")
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



### 常见任务示例

# 常見任務範例

本指南提供常見功能的實作範例，幫助您快速實作常用功能。

## 內容列表

1. 資料持久化
2. 定時任務
3. 訊息過濾
4. 多平台適配
5. 訊息傳送進階（重試/逾時/批次）
6. 權限控制
7. 訊息統計
8. 搜尋功能
9. 圖片處理

## 資料持久化

### 簡單計數器

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("count", help="檢視命令呼叫次數")
async def count_handler(event):
    # 取得計數
    count = sdk.storage.get("command_count", 0)
    
    # 增加計數
    count += 1
    sdk.storage.set("command_count", count)
    
    await event.reply(f"這是第 {count} 次呼叫此命令")
```

### 使用者資料儲存

```python
@command("profile", help="檢視個人資料")
async def profile_handler(event):
    user_id = event.get_user_id()
    
    # 取得使用者資料
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
    
    # 更新使用者資料
    user_data = sdk.storage.get(f"user:{user_id}", {})
    user_data["nickname"] = " ".join(args)
    sdk.storage.set(f"user:{user_id}", user_data)
    
    await event.reply(f"暱稱已設定為: {' '.join(args)}")
```

## 定時任務

### 簡單計時器

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
        
        @command("timer", help="計時器管理")
        async def timer_handler(event):
            await event.reply("計時器正在執行中...")
    
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
    
    # 啟動背景任務
    asyncio.create_task(daily_reminder())
```

## 訊息過濾

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
# 從設定或儲存載入黑名單
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
@command("help", help="顯示說明")
async def help_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        await event.reply("雲湖平台說明...")
    elif platform == "telegram":
        await event.reply("Telegram platform help...")
    elif platform == "onebot11":
        await event.reply("OneBot11 help...")
    else:
        await event.reply("通用說明訊息")
```

### 平台特性檢測

```python
@command("rich", help="傳送富文字訊息")
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

## 訊息傳送進階（重試/逾時/批次）

除了簡單的 `event.reply()`，您還可以透過適配器的 Send DSL 實作更複雜的傳送場景：失敗自動重試、逾時取消、成功後執行邏輯、批次傳送多條訊息。

> 下方的範例用 `event.get_detail_type()` 和 `event.get_target_id()` 從事件中取得目標類型和 ID（群聊自動取 group_id，私聊自動取 user_id），避免硬編碼。

### 傳送成功後執行邏輯

```python
@command("pay", help="模擬支付")
async def pay_handler(event):
    yunhu = sdk.adapter.get(event.get_platform())
    user_id = event.get_user_id()
    # 傳送成功後才扣積分
    await (yunhu.Send.To(event.get_detail_type(), event.get_target_id())
           .Hook(lambda r: sdk.storage.set(f"points:{user_id}", -10))
           .Text("支付成功，已扣除 10 積分"))
```

### 失敗重試 + 逾時取消

```python
@command("notice", help="傳送重要通知")
async def notice_handler(event):
    adapter_inst = sdk.adapter.get(event.get_platform())
    # 最多重試 3 次，每次逾時 10 秒
    task = (adapter_inst.Send.To(event.get_detail_type(), event.get_target_id())
            .Retry(3)
            .Timeout(10)
            .OnError(lambda ctx: sdk.logger.error(f"通知傳送失敗: {ctx.error}"))
            .Text("這是一條重要通知"))
    # 不等待，背景傳送
```

### 批次傳送多條訊息

一條鏈路傳送多條訊息，統一執行：

```python
@command("announce", help="傳送公告")
async def announce_handler(event):
    adapter_inst = sdk.adapter.get(event.get_platform())
    # 建構多條訊息，統一傳送（預設並行）
    results = await (adapter_inst.Send.To(event.get_detail_type(), event.get_target_id())
                    .Build()
                    .Text("📋 今日公告")
                    .Image("https://example.com/banner.jpg")
                    .Text("詳細內容見上方圖片")
                    .Retry(2)            # 失敗的項目各自重試
                    .send_all())
    sdk.logger.info(f"批次傳送完成，共 {len(results)} 條")
```

> 更完整的規則與批次說明請參考 [平台特性指南](../platform-guide/README.md#傳送規則裝飾器)。

## 權限控制

### 管理員檢查

```python
# 設定主人列表
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
        await event.reply("用法: /addmaster <使用者ID>")
        return
    
    new_master = args[0]
    MASTERS.append(new_master)
    await event.reply(f"已新增框架主人: {new_master}")
```

### 群組權限

```python
@command("groupinfo", help="檢視群組資訊")
async def groupinfo_handler(event):
    if not event.is_group_message():
        await event.reply("此命令僅限群聊使用")
        return
    
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"群組 ID: {group_id}, 你的 ID: {user_id}")
```

## 訊息統計

### 訊息計數

> **注意**：以下範例使用 `sdk.storage.get/set` 進行簡單計數。在高並發場景下，建議使用 `sdk.storage.transaction()` 保證原子性。

```python
@message.on_message()
async def count_handler(event):
    # 取得統計
    stats = sdk.storage.get("message_stats", {
        "total": 0,
        "by_user": {},
        "by_day": {}
    })
    
    # 更新統計
    stats["total"] += 1
    
    user_id = event.get_user_id()
    stats["by_user"][user_id] = stats["by_user"].get(user_id, 0) + 1
    
    # 儲存
    sdk.storage.set("message_stats", stats)

@command("stats", help="檢視訊息統計")
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
        f"{uid}: {count} 條訊息" for uid, count in top_users
    )
    
    await event.reply(f"總訊息數: {stats['total']}\n\n活躍使用者:\n{top_text}")
```

## 搜尋功能

### 簡單搜尋

> **注意**：以下範例使用記憶體列表儲存訊息歷史，**程式重新啟動後資料會遺失**。生產環境建議使用 `sdk.storage` 或 SQLite 表進行持久化儲存。

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
        await event.reply("未找到符合的訊息")
        return
    
    # 顯示結果
    result_text = f"找到 {len(results)} 條符合訊息:\n\n"
    for i, msg in enumerate(results[:10], 1):  # 最多顯示 10 條
        result_text += f"{i}. {msg['text']}\n"
    
    await event.reply(result_text)
```

## 圖片處理

### 圖片下載和儲存

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
                # 建議使用 SDK 內建用戶端下載圖片
                resp = await client.get(file_url)
                if resp.status == 200:
                    image_data = await resp.read()
                    
                    # 儲存到檔案
                    filename = f"images/{event.get_time()}.jpg"
                    with open(filename, "wb") as f:
                        f.write(image_data)
                    
                    sdk.logger.info(f"圖片已儲存: {filename}")
                    await event.reply("圖片已儲存")
```

### 圖片識別範例

> **注意**：以下範例使用佔位 API 位址，實際使用時請替換為您自己的圖片識別服務。

```python
from ErisPulse.Core import client

@command("identify", help="識別圖片")
async def identify_handler(event):
    """識別訊息中的圖片"""
    message_segments = event.get_message()
    
    for segment in message_segments:
        if segment.get("type") == "image":
            file_url = segment.get("data", {}).get("file")
            
            # 呼叫圖片識別 API
            result = await _identify_image(file_url)
            
            await event.reply(f"識別結果: {result}")
            return
    
    await event.reply("未找到圖片")

async def _identify_image(url):
    """呼叫圖片識別 API（範例）- 使用 SDK 內建用戶端"""
    resp = await client.post(
        "https://api.example.com/identify",
        json={"url": url}
    )
    data = await resp.json()
    return data.get("description", "識別失敗")
```

## 下一個步驟

- [使用者使用指南](../user-guide/) - 了解設定和模組管理
- [開發者指南](../developer-guide/) - 學習開發模組和適配器
- [進階主題](../advanced/) - 深入了解框架特性



### IDE 补全

# 類型存根生成（IDE 自動完成）

ErisPulse 透過 entry-points 動態發現模組/適配器，入口點無法在靜態層面得知使用者類別的具體類型。  
`epsdk types` 命令透過掃描已安裝的模組/適配器，產生一個類型存根檔案，讓使用者可以將這些類型用作變數標註，進而獲得 IDE 自動完成。

## 核心設計原則

存根檔案**僅導出類型**，不提供任何執行時實例：

- 所有匯入都在 ``TYPE_CHECKING`` 下，**零執行時開銷、零行為改變**
- 類型名稱採用 entry-point 名的 PascalCase 形式（如 ``yunhu`` → ``Yunhu``），與傳入 ``sdk.adapter.get()`` / ``sdk.module.get()`` 的名稱對應
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

# 用匯入的類型作為變數標註，即可讓 IDE 自動完成該類的方法
my_mod: MyModule = sdk.module.get("MyModule")
my_mod.hello()                  # ← IDE 自動完成 hello

my_adapter: Yunhu = sdk.adapter.get("yunhu")
await my_adapter.Send.To("group", "123").Board(...)   # ← 自動完成平台特有方法
```

## 工作原理

1. 掃描 `erispulse.adapter` / `erispulse.module` entry-points
2. 透過子程序在目標 Python 環境中內省，收集每個適配器/模組的實際類別資訊（包含模組路徑與限定名）
3. 產生 `.py` 檔案，其中：
   - 所有 ``from xxx import Yyy as Zzz`` 都在 ``TYPE_CHECKING`` 下
   - ``Zzz`` 是 entry-point 名的 PascalCase 形式
4. IDE 讀取 ``TYPE_CHECKING`` 部分提供自動完成；執行時不執行任何程式碼

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

- 安裝/卸載新的模組或適配器後
- 模組/適配器更新了公開 API 後
- IDE 自動完成失效或類型過期時

## 與 SendDSL 標準方法的關係

`SendDSL` 基類已內建標準發送方法（Text/Image/Voice/Video/File），任何方式取得的 SendDSL 實例都能自動完成這些方法。  
`types` 命令主要用於補全**平台特有方法**（如雲湖的 `Board`、沙盒的 `Dice`）和**模組特有方法**。

## 相關文件

- [SendDSL 詳解](../developer-guide/adapters/send-dsl.md) - 標準發送方法說明
- [適配器開發入門](../developer-guide/adapters/getting-started.md) - 建立適配器



====
用户指南
====


### 安装和配置

# 安裝參考

> 本文是安裝方式的**完整參考**（pip / uv / Docker / 故障排除）。
> 如果你只想快速上手，[5 分鐘快速入門](../quick-start.md) 已經涵蓋了最簡流程。

## 系統要求

- Python 3.10 或更高版本
- pip 或 uv（推薦）
- 足夠的磁碟空間（至少 100MB）

## 安裝方式

### 方式一：使用 pip 安裝

```bash
# 安裝 ErisPulse
pip install ErisPulse

# 升級到最新版本
pip install ErisPulse --upgrade
```

### 方式二：使用 uv 安裝（推薦）

uv 是一個更快的 Python 工具鏈，推薦用於開發環境。

#### 安裝 uv

```bash
# 使用 pip 安裝 uv
pip install uv

# 驗證安裝
uv --version
```

#### 建立虛擬環境

```bash
# 建立專案目錄
mkdir my_bot && cd my_bot

# 安裝 Python 3.12
uv python install 3.12

# 建立虛擬環境
uv venv
```

#### 激活虛擬環境

```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

#### 安裝 ErisPulse

```bash
# 安裝 ErisPulse
uv pip install ErisPulse --upgrade
```

## 項目初始化與模組安裝

安裝完成後，項目初始化、模組安裝、運行的完整流程見 [5 分鐘快速開始](../quick-start.md)。

### 方式三：使用 ErisPulse-App 客戶端（免終端）

不想裝 Python 環境？[ErisPulse-App](../ecosystem/app.md) 是官方全平台客戶端
（Android / Windows / Linux / macOS），**手機直接運行**，桌面版支援最小化到
系統托盤後台常駐；內建 Python 運行時與 ErisPulse SDK，無需終端與手動配置：

- 從 [GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases) 按平台選擇下載
  （Android `online`/`offline` APK、Windows `setup.exe`/`zip`、Linux `tar.gz`、macOS `zip`）
- 在 App 內建立並啟動實例，透過原生介面管理適配器與模組、瀏覽模組商店

> 完整說明見 [ErisPulse-App 安裝與使用](../ecosystem/app.md)。

## 驗證安裝

### 檢查安裝

```bash
# 檢查 ErisPulse 版本
epsdk --version
```

### 執行測試

```bash
# 執行項目
epsdk run main.py
```

如果看到類似的輸出，則表示安裝成功：

```
[INFO] 正在初始化 ErisPulse...
[INFO] 適配器已載入: Yunhu
[INFO] 模組已載入: MyModule
[INFO] ErisPulse 初始化完成
```

## 常見問題

### 安裝失敗

1. 檢查 Python 版本是否 >= 3.10（推薦 3.10 - 3.13）
2. 嘗試使用 `uv pip install ErisPulse` 取代 `pip install`
3. 如果提示權限錯誤，嘗試 `pip install --user ErisPulse` 或使用虛擬環境
4. 如果在企業代理環境下遇到 SSL 證書錯誤，嘗試 `pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org ErisPulse`
5. 確保網路連接正常，pip 源可訪問

### 配置錯誤

1. 檢查 `config.toml` 語法是否正確（TOML 格式對縮進和引號敏感）
2. 確認所有必需的配置項都已填寫
3. 查看終端日誌獲取詳細錯誤資訊
4. 使用 `epsdk init` 重新生成配置文件

### 模組安裝失敗

1. 確認模組名稱拼寫正確（大小寫敏感）
2. 檢查網路連接
3. 使用 `epsdk list-remote` 查看可用模組列表
4. 確認模組與你當前 SDK 版本相容

### Windows PowerShell 執行策略

如果 PowerShell 提示「無法載入檔案...因為在此系統上禁止執行腳本」：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Debian/Ubuntu 虛擬環境建立失敗

如果安裝腳本提示「虛擬環境建立失敗」，且錯誤資訊包含 `ensurepip is not available`，是因為 Debian/Ubuntu 預設未安裝 `python3-venv`（系統 Python 的 `ensurepip` 被禁用）：

```bash
sudo apt install python3.13-venv   # 按實際 Python 版本安裝對應套件
# 或安裝通用元套件：
sudo apt install python3-venv
```

安裝後重新執行安裝腳本即可。新版安裝腳本在偵測到該問題時會主動詢問並嘗試自動安裝對應系統套件；也可以改用 uv（`uv venv` 不依賴 `ensurepip`）。



### CLI 命令参考

# CLI 命令參考

ErisPulse 命令行工具（`epsdk`）提供專案管理和套件管理功能。

> **提示**：所有命令均可透過 `epsdk <命令> --help` 查看詳細的參數說明。

---

## 包管理命令

| 命令 | 別名 | 參數 | 說明 |
|------|------|------|------|
| `install` | `i`, `add` | `[package]... [--upgrade/-U] [--pre] [-e PATH] [--user] [--no-deps] [-t DIR] [--index-url URL] [--extra-index-url URL] [--no-cache-dir] [-r FILE] [-c FILE] [--force-reinstall] [--ignore-installed] [--compile/--no-compile] [--prefix DIR] [--src DIR] [--config-settings SETTINGS] [--no-binary FORMAT] [--only-binary FORMAT] [--prefer-binary] [--build-isolation/--no-build-isolation] [--upgrade-strategy {eager,only-if-needed,to-satisfy-only}] [--break-system-packages] [--no-uv]` | 安裝模組/適配器 |
| `uninstall` | `rm`, `remove` | `<package>... [--no-uv]` | 卸載模組/適配器 |
| `upgrade` | `up` | `[package]... [--force/-f] [--pre] [--no-uv]` | 升級指定模組或全部 |
| `self-update` | `su`, `update` | `[version] [--pre] [--force/-f] [--no-uv]` | 更新 SDK 本身 |

## 臨床命令

| 命令 | 別名 | 參數 | 說明 |
|------|------|------|------|
| `doctor` | `diag` | `[--verbose]` | 臨床環境並輸出健康報告 |

### install

安裝 ErisPulse 模組或適配器包。若未指定套件名稱則進入互動式安裝介面。

**別名：** `i`, `add`

**參數：**

| 參數 | 短參數 | 說明 |
|------|--------|------|
| `[package]...` | | 要安裝的套件名稱，可指定多個 |
| `--upgrade` | `-U` | 安裝時升級到最新版本 |
| `--pre` | | 允許安裝預發布版本 |
| `--editable` | `-e` | 以可編輯模式安裝（需指定路徑） |
| `--user` | | 安裝到使用者 site-packages 目錄 |
| `--no-deps` | | 不安裝相依性 |
| `--target` | `-t` | 安裝到指定目錄 |
| `--index-url` | | 指定 PyPI 鏡像源地址 |
| `--extra-index-url` | | 額外 PyPI 鏡像源地址（可多次指定） |
| `--no-cache-dir` | | 禁用快取 |
| `--requirement` | `-r` | 從 requirements 檔案安裝 |
| `--constraint` | `-c` | 從約束檔案安裝 |
| `--force-reinstall` | | 強制重新安裝 |
| `--ignore-installed` | | 忽略已安裝的套件 |
| `--compile` | | 安裝後編譯 .pyc 檔案 |
| `--no-compile` | | 安裝後不編譯 .pyc 檔案 |
| `--prefix` | | 安裝到指定前綴目錄 |
| `--src` | | 可編輯安裝時使用的原始碼目錄 |
| `--config-settings` | | 傳遞給建構後端的設定（可多次指定） |
| `--no-binary` | | 限制不使用二進位套件（格式如 `:all:`） |
| `--only-binary` | | 限制僅使用二進位套件（格式如 `:all:`） |
| `--prefer-binary` | | 优先選擇二進位套件 |
| `--build-isolation` | | 啟用建構隔離 |
| `--no-build-isolation` | | 禁用建構隔離 |
| `--upgrade-strategy` | | 升級策略：`eager`、`only-if-needed`、`to-satisfy-only` |
| `--break-system-packages` | | 允許修改系統包管理器管理的 Python 套件 |
| `--no-uv` | | 使用 pip 代替 uv |

**範例：**

```bash
# 安裝單個模組
epsdk install Weather

# 安裝多個模組
epsdk install Yunhu Weather

# 從鏡像源安裝並升級
epsdk install Weather -U --index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 可編輯模式安裝（開發模式）
epsdk install -e ./my-adapter
```

### uninstall

卸載已安裝的 ErisPulse 模組或適配器套件。若未指定套件名稱則進入互動式卸載介面。

**別名：** `rm`, `remove`

**參數：**

| 參數 | 說明 |
|------|------|
| `<package>...` | 要卸載的套件名稱，可指定多個 |
| `--no-uv` | 使用 pip 代替 uv |

**範例：**

```bash
# 卸載單個模組
epsdk uninstall Weather

# 卸載多個模組
epsdk uninstall Yunhu Weather
```

### upgrade

升級已安裝的 ErisPulse 組件。未指定套件名稱則互動式升級全部。

**別名：** `up`

**參數：**

| 參數 | 短參數 | 說明 |
|------|--------|------|
| `[package]...` | | 要升級的套件名稱，可指定多個 |
| `--force` | `-f` | 強制升級，跳過確認 |
| `--pre` | | 允許升級到預發布版本 |
| `--no-uv` | | 使用 pip 代替 uv |

**範例：**

```bash
# 升級所有套件
epsdk upgrade

# 升級指定套件
epsdk upgrade Weather

# 強制升級（跳過確認）
epsdk upgrade -f
```

### self-update

更新 ErisPulse SDK 本身到最新版本。

**別名：** `su`, `update`

**參數：**

| 參數 | 短參數 | 說明 |
|------|--------|------|
| `[version]` | | 指定要更新的目標版本號 |
| `--pre` | | 允許更新到預發布版本 |
| `--force` | `-f` | 強制更新，跳過確認 |
| `--no-uv` | | 使用 pip 代替 uv |

**範例：**

```bash
# 更新到最新穩定版
epsdk self-update

# 更新到指定版本
epsdk self-update 1.2.3

# 允許預發布版本
epsdk self-update --pre

# 強制更新
epsdk self-update -f
```

---

## 信息查詢命令

| 命令 | 別名 | 參數 | 說明 |
|------|------|------|------|
| `list` | `l`, `ls` | `[--type/-t {modules,adapters,all}] [--outdated/-o]` | 列出已安裝的元件 |
| `list-remote` | `lsr` | `[--type/-t {modules,adapters,all}] [--refresh/-r]` | 列出遠端可用的元件 |

### list

列出已安裝的 ErisPulse 模組和適配器。

**別名：** `l`, `ls`

**參數：**

| 參數 | 短參數 | 說明 |
|------|--------|------|
| `--type` | `-t` | 指定類型：`modules`、`adapters`、`all`（預設） |
| `--outdated` | `-o` | 僅顯示可升級的套件 |

**範例：**

```bash
# 列出所有已安裝的元件
epsdk list

# 只列出模組
epsdk list -t modules

# 只列出適配器
epsdk list -t adapters

# 僅顯示可升級的套件
epsdk list -o
```

### list-remote

列出遠端倉庫中可用的 ErisPulse 模組和適配器。

**別名：** `lsr`

**參數：**

| 參數 | 短參數 | 說明 |
|------|--------|------|
| `--type` | `-t` | 指定類型：`modules`、`adapters`、`all`（預設） |
| `--refresh` | `-r` | 強制刷新遠端套件列表快取 |

**範例：**

```bash
# 列出所有遠端可用元件
epsdk list-remote

# 只列出遠端模組
epsdk list-remote -t modules

# 強制刷新快取後列出
epsdk list-remote -r
```

## 配置命令

| 命令 | 別名 | 參數 | 說明 |
|------|------|------|------|
| `config` | `cfg`, `conf` | `[name] [--list/-l]` | 交互式配置适配器/模組的宣告式配置項 |

### config

交互式填寫適配器/模組的宣告式配置項。向導由適配器/模組宣告的配置類（`ConfigClass` / `AccountConfigClass`）驅動，自动生成表單並校驗，無需手寫 config.toml。

適配器額外支援多賬戶（bot 賬戶）管理：添加/編輯/刪除賬戶，以及啟用/禁用開關。

**別名：** `cfg`, `conf`

**參數：**

| 參數 | 短參數 | 說明 |
|------|--------|------|
| `[name]` | | 目標名稱（適配器平台名或模組名），留空進入交互選擇 |
| `--list` | `-l` | 僅列出所有目標的配置狀態，不進入向導 |

**示例：**

```bash
# 查看所有適配器/模組的配置狀態
epsdk config --list

# 交互選擇目標進行配置
epsdk config

# 直接配置指定適配器
epsdk config yunhu

# 直接配置指定模組
epsdk config MyModule
```

**說明：**

- 配置狀態分為四檔：`已就緒`（校驗通過）、`待完善`（必填項缺失或校驗失敗）、`未配置`（從未生成）、`無配置`（目標未宣告配置類）
- 欄位值帶來源標註：已有配置顯示 `（當前:值）`，未配置時顯示 schema 預設值 `（預設:值）`；直接回車即保留該值
- 密鑰類欄位（宣告 `secret`）輸入時不回顯，回車保留已設置的值
- 交互選擇模式下，單個向導結束後會回到選擇菜單（狀態已刷新），可連續配置多個目標，留空退出
- 全局表單校驗失敗且放棄重新填寫時，本次向導中止且不寫入任何配置（避免產生"已啟用但配置不完整"的半成品狀態）
- 保存後立即寫入 `config/config.toml`，Dashboard 與運行中的 SDK 均可見；運行中的適配器如需應用新賬戶配置，重啟進程即可
- `epsdk install`（交互式安裝）與 `epsdk init` 安裝適配器成功後，若檢測到配置宣告會自動引導進入本向導；命令行直接指定包名安裝時僅列印配置提示

## 運行控制命令

| 命令 | 別名 | 參數 | 說明 |
|------|------|------|------|
| `run` | `r` | `[script] [--reload]` | 運行指定腳本或 SDK |

### run

執行 ErisPulse 項目腳本或直接啟動 SDK。支援熱重載模式。

**別名：** `r`

**參數：**

| 參數 | 說明 |
|------|------|
| `[script]` | 要執行的腳本檔案，不指定則執行 SDK |
| `--reload` | 啟用熱重載模式，監控檔案變更自動重啟 |

**範例：**

```bash
# 直接執行 SDK
epsdk run

# 執行指定腳本檔案
epsdk run main.py

# 熱重載模式執行（檔案變更自動重啟）
epsdk run main.py --reload

# SDK 熱重載模式
epsdk run --reload
```

---

## 項目管理命令

| 命令 | 別名 | 參數 | 說明 |
|------|------|------|------|
| `init` | — | `[--project-name/-n <name>] [--quick/-q] [--force/-f] [--here] [--no-uv]` | 初始化 ErisPulse 項目 |
| `create` | — | `{module,adapter} [--name/-n <name>] [--description/-d <desc>] [--author/-a <name>] [--email/-e <mail>] [--homepage <url>] [--output/-o <dir>] [--force/-f]` | 創建模組/適配器腳手架 |

### init

初始化一個新的 ErisPulse 項目。支援互動式與快速模式。

**參數：**

| 參數 | 短參數 | 說明 |
|------|--------|------|
| `--project-name` | `-n` | 項目名稱 |
| `--quick` | `-q` | 快速模式，跳過互動式向導 |
| `--force` | `-f` | 強制覆蓋現有配置文件 |
| `--here` | | 在當前目錄初始化，不建立子目錄 |
| `--no-uv` | | 使用 pip 代替 uv |

**示例：**

```bash
# 互動式初始化
epsdk init

# 快速初始化
epsdk init -q -n my_bot

# 強制覆蓋已有配置
epsdk init -f

# 在當前目錄初始化
epsdk init --here -n my_bot
```

### create

創建 ErisPulse 模組或適配器的腳手架項目。

**參數：**

| 參數 | 短參數 | 說明 |
|------|--------|------|
| `{module,adapter}` | | 要創建的類型：`module` 或 `adapter` |
| `--name` | `-n` | 項目名稱（PascalCase） |
| `--description` | `-d` | 項目描述 |
| `--author` | `-a` | 作者名稱 |
| `--email` | `-e` | 作者郵箱 |
| `--homepage` | | 項目主頁 URL |
| `--output` | `-o` | 輸出目錄（預設當前目錄） |
| `--force` | `-f` | 強制覆蓋已存在的目錄 |
| `--local` | | 創建本地插件（僅 `module` 可用）：生成 `plugins/<name>/` 包結構，免打包安裝 |

**示例：**

```bash
# 互動式創建（引導選擇類型和填寫資訊）
epsdk create

# 直接創建 Module 項目
epsdk create module -n MyModule

# 創建本地插件（放入項目 plugins/ 目錄，啟動時自動發現，支援熱重載）
epsdk create module -n MyModule --local

# 直接創建 Adapter 項目
epsdk create adapter -n MyAdapter

# 完整參數
epsdk create module -n MyModule -d "模組描述" -a "作者" -e "mail@example.com"

# 指定輸出目錄
epsdk create module -n MyModule -o ./projects

# 強制覆蓋已有目錄
epsdk create module -n MyModule -f
```

## 語言命令

| 命令 | 別名 | 參數 | 說明 |
|------|------|------|------|
| `i18n` | `language`, `lang` | `[lang] [--list/-l]` | 查看或切換 CLI 顯示語言 |

### i18n

查看當前 CLI 語言、列出支援的語言、切換顯示語言。若不指定參數則進入互動式選擇介面。

**別名：** `language`, `lang`

**參數：**

| 參數 | 短參數 | 說明 |
|------|--------|------|
| `[lang]` | | 要切換的語言代碼（如 `zh-CN`、`en`、`ja`、`ru`） |
| `--list` | `-l` | 列出所有支援的語言 |

**示例：**

```bash
# 互動式選擇語言
epsdk i18n

# 切換到英文
epsdk i18n en

# 切換到日文
epsdk i18n ja

# 列出所有支援的語言
epsdk i18n --list
```

---

## 類型存根命令

| 命令 | 別名 | 參數 | 說明 |
|------|------|------|------|
| `types` | `t`, `stub` | `[--output/-o <path>] [--force] [--adapters-only] [--modules-only]` | 生成類型存根文件以啟用 IDE 自動補全 |

### types

掃描已安裝的 ErisPulse 模組和適配器，為它們生成 `.pyi` 類型存根文件，從而在 IDE 中獲得準確的程式碼自動補全與類型檢查支援。

**別名：** `t`, `stub`

**參數：**

| 參數 | 短參數 | 說明 |
|------|--------|------|
| `--output` | `-o` | 輸出路徑（預設為當前目錄下的 `ep-stubs/`） |
| `--force` | | 強制覆蓋已存在的存根文件 |
| `--adapters-only` | | 僅生成適配器的類型存根 |
| `--modules-only` | | 僅生成模組的類型存根 |

> **注意：** `--adapters-only` 與 `--modules-only` 互斥，同時指定時後者生效。

**範例：**

```bash
# 為所有已安裝的模組和適配器生成類型存根
epsdk types

# 僅生成適配器存根
epsdk types --adapters-only

# 輸出到指定目錄
epsdk types -o ./typings

# 強制覆蓋已有檔案
epsdk types --force
```

## 全局參數

以下參數適用於所有命令：

| 參數 | 短參數 | 說明 |
|------|--------|------|
| `--help` | `-h` | 顯示幫助資訊 |
| `--version` | `-V` | 顯示版本資訊 |
| `--verbose` | `-v` | 顯示詳細輸出（可疊加 `-vv`/`-vvv`） |
| `--no-color` | | 禁用彩色輸出（適合 CI / 日誌採集） |
| `--yes` | `-y` | 自動確認所有互動提示（非互動式運行） |

---

## 環境診斷

### doctor

> [!NOTE]  
> 此命令需要 ErisPulse **2.7.0+** 版本。

診斷當前 CLI 運行環境，輸出健康報告。用於排查「為什麼安裝不上 / 連不上」類問題。

| 參數 | 說明 |
|------|------|
| `--verbose` | 顯示詳細診斷資訊 |

**檢查項目**：
- **Python**：解釋器版本與路徑
- **安裝後端**：使用 `uv` 還是 `pip`
- **目標解釋器**：套件實際安裝到的目標 Python 環境
- **配置檔案**：`config/config.toml` 是否存在
- **PyPI 連通性**：能否存取 PyPI（並顯示發現的元件數量）
- **系統代理**：是否偵測到代理

```bash
# 運行環境診斷
epsdk doctor

# 使用別名
epsdk diag
```

## 互動式安裝

執行 `epsdk install` 且不指定套件名稱時，將進入互動式安裝：

```bash
epsdk install
```

互動介面提供：
1. 適配器選擇
2. 模組選擇
3. 自訂安裝

## 常見用法

### 安裝模組

```bash
# 安裝單個模組
epsdk install Weather

# 安裝多個模組
epsdk install Yunhu Weather

# 升級模組
epsdk install Weather -U
```

### 列出組件

```bash
# 列出所有組件
epsdk list

# 只列出適配器
epsdk list -t adapters

# 只列出可升級的組件
epsdk list -o

# 查看遠端可用組件
epsdk list-remote
```

### 卸載組件

```bash
# 卸載單個組件
epsdk uninstall Weather

# 卸載多個組件
epsdk uninstall Yunhu Weather
```

### 配置組件

```bash
# 查看配置狀態
epsdk config --list

# 交互式選擇目標配置
epsdk config

# 配置指定適配器
epsdk config yunhu
```

### 升級組件

```bash
# 升級所有組件
epsdk upgrade

# 升級指定組件
epsdk upgrade Weather

# 強制升級
epsdk upgrade -f
```

### 運行專案

```bash
# 普通運行
epsdk run main.py

# 熱重載模式
epsdk run main.py --reload
```

### 切換語言

```bash
# 交互式選擇語言
epsdk i18n

# 直接切換到英文
epsdk i18n en

# 列出支援的語言
epsdk i18n --list
```

### 產生類型存根

```bash
# 產生所有類型存根
epsdk types

# 僅產生模組類型存根
epsdk types --modules-only
```

### 初始化專案

```bash
# 交互式初始化
epsdk init

# 快速初始化
epsdk init -q -n my_bot
```

### 建立腳手架

```bash
# 交互式建立（引導選擇類型並填寫資訊）
epsdk create

# 直接建立 Module 專案
epsdk create module -n MyModule

# 直接建立 Adapter 專案
epsdk create adapter -n MyAdapter

# 完整參數
epsdk create module -n MyModule -d "模組描述" -a "作者" -e "mail@example.com"

# 強制覆蓋已有目錄
epsdk create module -n MyModule -f
```



### 配置文件说明

# 配置文件說明
> 本文檔將介紹框架的配置文件，如果第三方模組需要配置，請參考模組的文件。

ErisPulse 使用 TOML 格式的配置文件 `config/config.toml` 來管理專案設定。

## 配置文件位置

配置文件位於專案根目錄的 `config/` 資料夾中：

```
project/
├── config/
│   └── config.toml
├── main.py
```

## 配置載入錯誤處理

框架在載入 `config.toml` 時會區分三種錯誤狀態，並提供**可操作的診斷資訊**，而不是靜默回退到預設配置：

| 錯誤狀態 | 觸發條件 | 框架行為 |
|---------|---------|---------|
| 檔案缺失 | `config.toml` 不存在 | 正常首次啟動，靜默使用空配置（不發出警告） |
| TOML 語法錯誤 | 檔案存在但格式非法（例如少了引號、括號未閉合） | 輸出**出錯行號/列號與原因**，並提示已回退預設配置 |
| 權限/其他錯誤 | 無讀取權限、IO 錯誤等 | 輸出**明確原因**，並提示已回退預設配置 |

例如，當你不小心把配置寫成了 `port = 8000`（缺少引號的字串）時，日誌會輸出類似：

```
[ERROR] [Config] 配置文件 config/config.toml 語法錯誤（第 3 行 第 1 列）: ...
[WARNING] [Config] 配置文件讀取失敗。繼續使用上次有效配置運行，本次文件修改未生效——請修復後重新載入或重新啟動
```

這樣你可以在**預設的 INFO 級別**下立刻定位問題，而不會困惑「為什麼我修改的配置沒有生效」。

> **運行中改壞配置檔案？** 如果你在機器人運行期間手動編輯 `config.toml` 引入了語法錯誤，框架在下次寫入（合併配置）時會輸出「配置檔案已損壞（語法錯誤，第 X 行），無法合併寫入——請先修復配置檔案後重新啟動」，而不是令人困惑的「寫入失敗」。待寫入的配置項目會被保留，不會遺失。

## 環境變數覆蓋

框架支援使用環境變數**覆蓋** `ErisPulse.*` 配置項（適合 Docker / 容器化 / CI 部署，無需修改 `config.toml`）。

命名規則：將點分路徑 `ErisPulse.<section>.<key>` 改為全大寫、`.` 替換為 `_`，並加上 `ERISPULSE_` 前綴：

| 配置項 | 環境變數 | 示例值 |
|--------|---------|--------|
| `ErisPulse.server.port` | `ERISPULSE_SERVER_PORT` | `9000` |
| `ErisPulse.server.host` | `ERISPULSE_SERVER_HOST` | `0.0.0.0` |
| `ErisPulse.logger.level` | `ERISPULSE_LOGGER_LEVEL` | `DEBUG` |
| `ErisPulse.framework.strict_mode` | `ERISPULSE_FRAMEWORK_STRICT_MODE` | `false` |

行為說明：
- **優先級最高**：環境變數覆蓋「配置文件」與「預設值」，並按原值類型自動轉換（`bool` / `int` / `float` / 逗號分隔的 `list` / 字串）
- **不持久化**：覆蓋只在執行期間生效，不會寫回 `config.toml`
- **支援熱更新**：執行中修改環境變數後，配合配置監聽的重載即可生效

```bash
# Docker 部署示例：不修改 config.toml，直接覆蓋端口
ERISPULSE_SERVER_PORT=9000 docker compose up -d
```

> 注：`ErisPulse.server.port` 這類框架配置走 `get_server_config()` 等 API 讀取，均受環境變數覆蓋影響。

## 配置熱更新

從 2.7.0 開始，框架對配置熱更新做了**系統化支援**。外部修改 `config.toml` 後（後台 watcher 每 5 秒檢測一次），或程式碼呼叫 `setConfig()` 後，各組件自動響應：

| 組件 | 支援熱更新的設定 | 行為 |
|------|----------------|------|
| **日誌 Logger** | `logger.level` / `log_files` / `log_dir`（含分段參數）/ `memory_limit` / `format` / `exclude_levels` | 自動重新應用（帶變更檢測） |
| **命令系統 CommandHandler** | `event.command.prefix` / `case_sensitive` / `allow_space_prefix` / `must_at_bot` | 下一條訊息即生效 |
| **適配器併發** | `framework.handler_max_concurrency` | 失效快取信號量，按新值重建 |
| **主動 GC** | `framework.proactive_gc_*` | 設定變更即時重啟 GC 任務，支援執行時調整/停用/重新啟用 |
| **主人系統 Master** | `master.users` | 每次 `is_master()` 檢查即時讀取，無需重啟 |
| **模組/適配器設定** | 各自的設定項目 | 觸發 `on_config_update(old, new)` 回呼 |

**需重啟的設定**（無法安全熱切換，變更時會輸出警告「需重啟程序後生效」）：

| 設定 | 原因 |
|------|------|
| `router.cors.*` / `router.security.*` | 中間件在服務啟動時寫入 FastAPI，執行時無法安全熱切換 |
| `storage.use_global_db` | SQLite 檔案句柄已在執行時開啟，切換路徑不安全 |

> **中途編輯儲存出錯？** 若編輯 `config.toml` 時出現瞬間語法錯誤，框架會**保留上次有效設定**並輸出診斷日誌，不會把空設定廣播給各組件（避免 `on_config_update` 收到空值誤回退預設值）。

### 熱更新鏈路內部拆解

「改了設定，各組件怎麼知道的？」——背後是一條檢測 → 重載 → 廣播的鏈路：

```mermaid
flowchart TD
    A["外部編輯 config.toml"] --> B{"誰先發現？"}
    B -->|"後台 watcher 線程<br/>每 5 秒輪詢 mtime"| C["_check_file_change 判定變更"]
    B -->|"程式碼讀取設定時<br/>快取超過 60 秒"| C
    C --> D["_load_config 重新解析 TOML"]
    D --> E{"解析成功？"}
    E -->|"否（語法錯誤）"| F["保留上次有效設定<br/>不廣播，打診斷日誌"]
    E -->|"是"| G["lifecycle.emit config.updated<br/>攜帶 old_config / new_config"]
    G --> H["各組件監聽者響應<br/>（logger / scope / 命令 / GC ...）"]
```

**兩條檢測路徑**（取其一即可，均能兜底）：

| 路徑 | 機制 | 觸發時機 |
|------|------|---------|
| 後台 watcher | daemon 線程 `config-watcher` 每 **5 秒** `wait` 輪詢檔案 `mtime` | 外部改檔案後最多 5 秒內 |
| 慣性檢測 | 任何 `getConfig()` 讀取時，若快取超過 **60 秒**則先查檔案 | 下次讀取設定時 |

> **框架不會誤傷自己**：`setConfig()` 寫盤時會記錄「自身寫入的 mtime」，watcher 對比時把它排除，只把**外部編輯**視為變更。

**兩類設定變更事件：**

| 事件 | 觸發者 | 數據 | 典型場景 |
|------|--------|------|---------|
| `config.set` | 程式碼 / Dashboard 調 `setConfig()` | `{key, old_value, new_value}` | 單鍵寫入（模板生成、狀態記錄、執行時改設定） |
| `config.updated` | 外部編輯後 watcher/慣性檢測捕獲 | `{old_config, new_config, config_file}` | 手動改 `config.toml` |

> `setConfig()` 預設**延遲 5 秒落盤**（合併多次寫入），`immediate=True` 立即寫。watcher 檢測到外部修改後只更新記憶體快取，**不會**把外部變動回寫檔案。

**自動響應方清單**（兩類事件通常會都訂閱，響應內容一致）：

| 組件 | 監聽 | 响應 |
|------|------|------|
| Logger | `config.set` + `config.updated` | 級別/檔案/目錄分段/記憶體上限/格式/屏蔽等級重新應用（帶變更檢測，無變化不動） |
| Scope | `config.updated` | 作用域綁定快取重建 |
| 命令系統 | `config.updated` | 前綴/大小寫/空格前綴/must_at_bot 解析參數刷新，下一條訊息生效 |
| 適配器併發 | `config.set` + `config.updated` | `handler_max_concurrency` 失效重建信號量 |
| 主動 GC | `config.set` + `config.updated` | `proactive_gc_*` 即時重啟 GC 後台任務 |
| 適配器 | 路由到 `on_config_update` | 各適配器 `on_config_update(old, new)` 回呼 |
| 模組 | 路由到 `on_config_update` | 各模組 `on_config_update(old, new)` 回呼 |
| 存儲 | `config.updated` | `use_global_db` 變更**僅警告**（需重啟） |
| 路由 | `config.updated` | `cors.*` / `security.*` 變更**僅警告**（需重啟） |

## 完整配置示例

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000
auto_start = true
ssl_certfile = ""
ssl_keyfile = ""

[ErisPulse.master]
# users 支持兩種寫法（二選一）：
#   全局主人（所有平台生效）：users = ["123456", "789012"]
#   按平台指定主人：users = { yunhu = ["123456"], telegram = ["789012"] }
users = {}

[ErisPulse.logger]
level = "INFO"
format = "rich"
log_files = []
log_dir = ""
log_rotation = "size"
log_max_size_mb = 10
log_backup_count = 5
log_rotation_when = "midnight"
memory_limit = 1000
exclude_levels = []

[ErisPulse.framework]
enable_lazy_loading = true
uninit_timeout = 30
strict_mode = 0

[ErisPulse.framework.strict_mode_exceptions]
modules = []
adapters = []

[ErisPulse.storage]
use_global_db = false

[ErisPulse.event.command]
prefix = "/"
case_sensitive = true
allow_space_prefix = false
must_at_bot = false

[ErisPulse.event.message]
ignore_self = true

[ErisPulse.i18n]
language = "auto"
```

## 伺服器配置

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000
auto_start = true
ssl_certfile = "/path/to/cert.pem"
ssl_keyfile = "/path/to/key.pem"
```

| 配置項 | 類型 | 默認值 | 說明 |
|---------|------|---------|------|
| host | string | 0.0.0.0 | 監聽位址，0.0.0.0 表示所有介面 |
| port | integer | 8000 | 監聽埠號 |
| auto_start | boolean | true | 是否在 `sdk.init()` 時自動啟動路由伺服器。設為 `false` 可跳過路由伺服器啟動（純事件/無 WebUI 場景） |
| ssl_certfile | string | 空 | SSL 證書檔案路徑 |
| ssl_keyfile | string | 空 | SSL 私鑰檔案路徑 |

## 主人系統配置

主人系統用於識別「框架主人」帳號（如 Bot 管理員）。`master.users` 支援兩種寫法：

```toml
[ErisPulse.master]
# 寫法一：全域主人（所有平台生效）
users = ["123456", "789012"]

# 寫法二：按平台指定主人（dict）
# users = { yunhu = ["123456"], telegram = ["789012"] }
```

| 配置項 | 類型 | 預設值 | 說明 |
|---------|------|---------|------|
| users | array / object | 空 | 主人帳號列表。`list` 形式為全域主人（所有平台生效）；`dict` 形式按平台指定（鍵為平台名，值為該平台的主人帳號列表） |

程式碼中透過 `master.is_master(event)` 或 `master.is_master(platform, user_id)` 檢查，每次呼叫即時讀取配置（支援熱更新，無需重啟）：

```python
from ErisPulse.Core import master

if master.is_master(event):
    await event.reply("主人你好")
```

> 身份判定的完整 API（執行時增刪、**自訂身份來源 provider 鏈**）與「使用者優先」的
> 覆蓋語意（使用者可經控制面放寬/收緊 `master=True`），請見
> [統一控制面 · 主人身份與自訂身份來源](../advanced/scope.md#主人身份與自訂身份來源provider)。

## 日誌配置

```toml
[ErisPulse.logger]
level = "INFO"
log_files = []                # 明確的日誌檔案列表（與 log_dir 互斥，優先級更高）
log_dir = ""                  # 日誌目錄（設定後自動分段輪轉）
log_rotation = "size"         # 分段方式: "size" / "date" / "none"
log_max_size_mb = 10          # size 模式單檔案上限（MB）
log_backup_count = 5          # 保留的歷史日誌檔案數
log_rotation_when = "midnight"  # date 模式輪轉週期: S/M/H/D/midnight
memory_limit = 1000
exclude_levels = ["EVENT"]
```

| 配置項 | 類型 | 默認值 | 說明 |
|---------|------|---------|------|
| level | string | INFO | 日誌等級：TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL（TRACE 為最低等級，輸出框架內部詳細除錯資訊） |
| format | string | rich | 日誌輸出格式：`rich`（彩色，預設）、`plain`（純文本無顏色，適合日誌採集/管道重定向）、`json`（JSON 結構化，適合 ELK 等） |
| log_files | array | 空 | 日誌輸出檔案列表（明確路徑，不分段） |
| log_dir | string | 空 | 日誌輸出目錄（自動建立）。設定後寫入目錄內 `erispulse.log` 並按 `log_rotation` 自動分段；與 `log_files` 互斥，`log_files` 優先 |
| log_rotation | string | size | 分段方式：`size`（按大小）/ `date`（按時間）/ `none`（不分段） |
| log_max_size_mb | float | 10 | size 模式單檔案大小上限（MB），超過後輪轉為 `.1`/`.2` 備份 |
| log_backup_count | integer | 5 | 保留的歷史日誌檔案數，超出的最舊備份自動刪除 |
| log_rotation_when | string | midnight | date 模式輪轉週期：`S`/`M`/`H`/`D`/`midnight`（預設每天零點） |
| memory_limit | integer | 1000 | 內存中保存的日誌條數 |
| exclude_levels | array | 空 | 屏蔽指定日誌等級。被屏蔽等級的日誌**完全丟棄**（不寫內存、不推送到 Dashboard 等訂閱器、不列印、不寫檔案）。支援熱更新 |

也可在程式碼中動態切換：

```python
from ErisPulse.Core import logger

# 按大小分段：單檔案 10MB，保留 5 份
logger.set_output_dir("logs", rotation="size", max_size_mb=10, backup_count=5)

# 按時間分段：每天零點輪轉，保留 7 份
logger.set_output_dir("logs", rotation="date", backup_count=7)
```

> [!NOTE]
> `log_dir` 及分段相關配置需要 ErisPulse **2.8.0+**。

> **隱私保護**：訊息收發內容以 **EVENT 等級**（數值 21）記錄。設定 `exclude_levels = ["EVENT"]` 即可讓後台（如 Dashboard 日誌面板）無法看到各群/私聊的訊息內容，同時不影響其它等級日誌。

> [!NOTE]
> `exclude_levels` 本特性需要 ErisPulse **2.8.0+**。

## 框架配置

```toml
[ErisPulse.framework]
enable_lazy_loading = true
uninit_timeout = 30
strict_mode = 0

[ErisPulse.framework.strict_mode_exceptions]
modules = []
adapters = []
```

| 配置項 | 類型 | 默認值 | 說明 |
|---------|------|---------|------|
| enable_lazy_loading | boolean | true | 是否啟用模組懶加載 |
| uninit_timeout | integer | 30 | 優雅關閉的總超時時間（秒），超過後強制終止。0 表示不設超時 |
| strict_mode | integer | 0 | 嚴格模式級別，見下方「嚴格模式」說明 |
| handler_max_concurrency | integer | 64 | 事件處理器最大併發 Task 數，設大提高吞吐但增加記憶體佔用 |
| offline_bot_expiry | integer | 3600 | 離線 Bot 記錄自動過期時間（秒），0 表示不過期 |

### 主動 GC 配置

SDK 初始化完成後啟動主動 GC 後台任務，週期性執行 Python GC 與內部資源回收（離線 Bot 清理等）。全部參數均支援熱更新，變更時即時重啟任務。

| 配置項 | 類型 | 默認值 | 說明 |
|---------|------|---------|------|
| proactive_gc_interval | number | 300 | 回收間隔（秒），支援小數。0 表示禁用主動 GC |
| proactive_gc_generation | integer | 0 | 常規輪次回收分代（0/1/2，钳制到 0..2）。注意 `gc.collect(2)` 等價於全量回收，默认 0 保持輕量；深度回收由 `proactive_gc_full_every` 週期性觸發 |
| proactive_gc_full_every | integer | 20 | 每 N 輪做一次全量回收，0 表示禁用週期性全量。全量回收受 `proactive_gc_memory_growth_mb` 門限約束 |
| proactive_gc_memory_growth_mb | integer | 32 | 全量回收的記憶體增長門限（MB）：對比上次全量後的記憶體基線（優先 tracemalloc，其次 RSS），僅當增長達到此值才執行全量回收。0 表示不設門限 |
| proactive_gc_idle_only | boolean | false | 開啟後，事件洪峰（存在未完成的 pending handler）時本轮跳過 Python GC，避免停頓與訊息處理競爭；內部資源回收不受影響 |
| proactive_gc_gen0_min | integer | 500 | 常規輪次觸發回收的 gen0 垃圾量下限：`gc.get_count()[0]` 低於此值直接跳過（空轉輪次近乎零開銷）。0 表示始終回收 |

> **2.7.1 變更**：默認 `proactive_gc_generation` 由 `2` 調整為 `0`，默認 `proactive_gc_full_every` 由 `0` 調整為 `20`。此前 `generation=2` 意味著每輪都做最重的全量回收；新默認在保持回收覆蓋的同時顯著降低空轉開銷。顯式配置的舊值仍按字面語義生效。

### 嚴格模式

嚴格模式控制模組/適配器在加載階段不合規或失敗時的處理策略。現代模組/適配器都應繼承對應的基類（`BaseModule`/`BaseAdapter`），未繼承基類的組件會影響框架的上下文系統與兜底清理，可能導致資源洩漏。

> **2.5.2 變更**：默認級別從 `1`（跳過）調整為 `0`（寬鬆），以減少新用戶初次使用時遇到的加載問題。未繼承基類的組件將以 WARNING 提示並嘗試加載，而非直接拒絕。如需恢復舊行為，請顯式設定 `strict_mode = 1`。

| 級別 | 名稱 | 行為 |
|------|------|------|
| 0 | 寬鬆（默認） | 違規僅警告，未繼承基類的組件仍會嘗試加載（相容舊組件） |
| 1 | 嚴格-跳過 | 拒絕未繼承基類的組件並跳過，其餘正常啟動 |
| 2 | 嚴格-致命 | 收集所有違規後統一報告並中止整個啟動 |

各級別下，「加載/註冊/初始化階段報錯」這類組件自身崩潰始終會被跳過；區別在於：

- **0 → 1**：唯一行為變化是「未繼承基類」從「仍加載」變為「跳過」。
- **1 → 2**：所有違規（未繼承基類、加載失敗、註冊失敗、初始化失敗等）升級為致命，會在啟動檢查點收集後一次性輸出違規清單並中止。

#### 豁免清單

如果某些組件確實暫時無法遷移（例如依賴的舊模組），可以將其加入豁免清單，被列名的組件即使不合規也會按寬鬆模式對待，繼續加載：

```toml
[ErisPulse.framework.strict_mode_exceptions]
modules = ["SeTu", "SomeLegacyModule"]
adapters = ["OldAdapter"]
```

> 當某個組件被嚴格模式拒絕時，日誌會明確提示如何恢復加載（加入豁免清單或調低級別）。

## 存儲配置

```toml
[ErisPulse.storage]
use_global_db = false
```

| 配置項 | 類型 | 默認值 | 說明 |
|---------|------|---------|------|
| use_global_db | boolean | false | 是否使用全域資料庫（包內）而非專案資料庫。`true` 時所有專案共享 ErisPulse 包內的 SQLite 資料庫；`false`（預設）時每個專案使用 `config/` 目錄下獨立的資料庫 |

## 事件配置

### 命令配置

```toml
[ErisPulse.event.command]
prefix = "/"
case_sensitive = true
allow_space_prefix = false
```

| 配置項目 | 類型 | 預設值 | 說明 |
|---------|------|---------|------|
| prefix | string | / | 命令前綴 |
| case_sensitive | boolean | true | 是否區分大小寫（`/Help` 與 `/help` 是否為不同命令） |
| allow_space_prefix | boolean | false | 是否允許空格作為前綴 |
| must_at_bot | boolean | false | 是否必須@機器人才能觸發命令（私聊不受限制） |

### 消息配置

```toml
[ErisPulse.event.message]
ignore_self = true
```

| 配置項目 | 類型 | 預設值 | 說明 |
|---------|------|---------|------|
| ignore_self | boolean | true | 是否忽略機器人自己的消息 |

## 國際化配置

```toml
[ErisPulse.i18n]
language = "auto"
```

| 配置項 | 類型 | 默認值 | 說明 |
|---------|------|---------|------|
| language | string | auto | 框架內置文本的顯示語言。設為 `auto` 自動檢測系統語言，也可設為具體代碼：`zh-CN`、`zh-TW`、`en`、`ja`、`ru` |

## 模組配置

每個模組可以在配置文件中定義自己的配置：

```toml
[MyModule]
api_url = "https://api.example.com"
timeout = 30
enabled = true
```

在模組中讀取和寫入配置：

```python
from ErisPulse import sdk

# 讀取配置
config = sdk.config.getConfig("MyModule", {})
api_url = config.get("api_url", "https://default.api.com")

# 運行時寫入配置（延遲保存）
sdk.config.setConfig("MyModule.timeout", 60)

# 立即保存到檔案
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)
```

> `setConfig` 預設採用延遲寫入（約每 5 秒批量保存到檔案），設定 `immediate=True` 可立即持久化。配置變更會觸發 `config.set` 生命週期事件。

## 控制面配置（scope）

> [!NOTE]
> 此功能需要 ErisPulse **2.8.0+**。

統一控制面是權限/訪問控制的**唯一**入口，由五維配置樹組成：

| 維度 | 控制什麼 | 配置路徑 |
|------|---------|---------|
| ① 模塊 | 某平台 / Bot / 會話中哪些模塊可用 | `scope.platforms / bots / sessions` |
| ② 身份 | 某用戶 / 群 / Bot / 适配器的事件是否接收 | `scope.identity.*` |
| ③ 命令 | 誰能執行某條命令（命令名支持 glob） | `scope.commands` |
| ④ 處理器 | 某模塊的處理器按文本過濾 | `scope.handlers` |
| ⑤ 覆蓋 | 覆蓋模塊/命令的實現參數 | `scope.overrides` |

```toml
[ErisPulse.scope]
default_allow = true        # 全局兜底（false = 隱式拒絕嚴格模式）
cache_size = 1024           # LRU 缓存大小

# ① 模塊維度（優先級：會話 > Bot > 平台；條目支持精確 / glob / re: 正則）
[ErisPulse.scope.platforms.onebot11]
modules = ["Chat", "Tool*"]
blocked = ["re:^Danger"]

# ② 身份維度（優先級：用戶 > 會話 > Bot > 适配器；每級只寫 allow 或 deny 之一）
[ErisPulse.scope.identity.adapters.onebot11]
deny = true                 # 該平台所有事件在入口丟棄
[ErisPulse.scope.identity.users.onebot11]
allow = ["u_admin"]         # 用戶鍵支持 glob / re: 正則
deny = ["u_bad", "spam_*"]

# ③ 命令維度（用戶標識 "platform:user_id"）
[ErisPulse.scope.commands."roll*"]
allow = ["onebot11:u_vip"]
deny = ["onebot11:u_bad"]

# ④ 處理器/文本維度（與代碼內條件 AND）
[ErisPulse.scope.handlers.MyModule]
pattern = "簽到*"

# ⑤ 實現參數覆蓋（禁用統一走命令 deny，不在這裡）
[ErisPulse.scope.overrides.MyModule.restart]
master = true
hidden = true
```

| 配置項 | 類型 | 說明 |
|---------|------|------|
| `scope.default_allow` | boolean | 全局兜底：未命中規則的放行/拒絕（`true`）。模塊/身份"無規則即拒"；命令"無 ACL 即拒" |
| `scope.cache_size` | integer | LRU 缓存大小（默認 1024） |
| `scope.platforms / bots / sessions` | table | ① 模塊三級綁定：`{modules=[...], blocked=[...]}` |
| `scope.identity.adapters / bots / sessions / users` | table | ② 身份四級綁定：`{allow=true}` / `{deny=true}` |
| `scope.commands.<命令名>` | table | ③ 命令 ACL：`{allow=[...], deny=[...]}` |
| `scope.handlers.<module>` | table | ④ 文本過濾：`{pattern="...", regex="..."}` |
| `scope.overrides.<module>[.<command>]` | table | ⑤ 參數覆蓋：`master` / `hidden` / `aliases` / `prefix` 等 |

> 匹配條目統一語法：精確名 / glob（`*` `?` `[seq]`）/ `re:` 正則，大小寫不敏感。
> 五維詳解與運行時 API（`sdk.scope.bind_module()` / `bind_identity()` / `block_user()` /
> `allow_user()` / `override()` 等）詳見[統一控制面](../advanced/scope.md)。



### 部署指南

# 部署指南

將 ErisPulse 機器人部署到生產環境的最佳實踐。

## Docker 部署（推薦）

ErisPulse 提供官方 Docker 鏡像，內建 ErisPulse 框架和 Dashboard 管理面板，支援 `linux/amd64` 和 `linux/arm64` 架構。

### 快速啟動

```bash
# 拉取鏡像
docker pull erispulse/erispulse:latest

# 下載 docker-compose.yml
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# 設定 Dashboard 登入令牌並啟動
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

啟動後，請訪問 `http://localhost:8000/Dashboard`，使用設定的令牌作為密碼登入。

### 國內鏡像加速

如果 Docker Hub 無法存取，可以使用 GitHub Container Registry 拉取鏡像：

```bash
docker pull ghcr.io/erispulse/erispulse:latest
```

使用 ghcr.io 鏡像時，需要修改 `docker-compose.yml` 中的 image：

```yaml
services:
  erispulse:
    image: ghcr.io/erispulse/erispulse:latest
```

### docker-compose.yml

```yaml
services:
  erispulse:
    image: erispulse/erispulse:latest
    container_name: erispulse
    ports:
      - "${ERISPULSE_PORT:-8000}:8000"
    volumes:
      - ./config:/app/config
    environment:
      - TZ=${TZ:-Asia/Shanghai}
      - ERISPULSE_DASHBOARD_TOKEN=${ERISPULSE_DASHBOARD_TOKEN:-}
    restart: unless-stopped
```

### 環境變數

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `ERISPULSE_PORT` | `8000` | Dashboard 端口映射 |
| `ERISPULSE_DASHBOARD_TOKEN` | 自动生成 | Dashboard 登入令牌（強烈建議設定） |
| `TZ` | `Asia/Shanghai` | 時區 |

### 數據持久化

`./config` 目錄掛載了配置文件和數據庫，包含：

- `config/config.toml` — 配置文件
- `config/config.db` — SQLite 存儲數據庫
- `config/.packages` — Python site-packages 持久化卷，保存框架、適配器和已安裝模塊（首次啟動時由入口點從鏡像內建備份自動初始化，之後的模塊安裝與框架熱更新均寫入此目錄）

## Dashboard 管理面板

ErisPulse Docker 鏡像內建 Dashboard 模組，提供 Web 可視化管理介面。

### 功能概覽

| 功能 | 說明 |
|------|------|
| 儀表板 | 系統概覽、CPU/記憶體監控、運行時長、事件統計 |
| 机器人管理 | 查看各平台机器人在線狀態和資訊 |
| 事件查看 | 實時事件流，支援按類型和平台過濾 |
| 日誌查看 | 按模組和級別過濾的日誌查看器 |
| 模組管理 | 查看、載入、卸載已安裝的模組和適配器 |
| 模組商店 | 瀏覽遠端可用套件並一鍵安裝 |
| 配置編輯 | 在線編輯 `config.toml` |
| 存儲管理 | 瀏覽和編輯 Key-Value 存儲資料 |
| 備份 | 導出/匯入配置和存儲資料 |
| 審計日誌 | 記錄所有管理操作 |

### 透過 Dashboard 安裝模組

Dashboard 集成了模組商店功能，你可以：

1. **從商店安裝**：瀏覽遠端模組列表，選擇需要的模組一鍵安裝
2. **上傳本機包**：直接上傳 `.whl` 或 `.zip` 檔案進行安裝，方便測試個人開發的模組

> **模組開發者的快速測試流程**：使用 Docker 部署後，在 Dashboard 中透過「上傳本機包」功能直接上傳你建構的 `.whl` 檔案進行測試，無需手動操作容器。

## 進程監督與硬重啟

ErisPulse 的硬重啟（`sdk.hard_restart()`）依賴**外部監督者**在進程退出碼為 42 時重新拉起進程——SDK 自己不會拉起新進程。生產環境務必配置監督者，否則硬重啟後進程不會自動恢復：

- Docker：`restart: unless-stopped`（任何退出碼都會重啟，含 42）
- systemd：`Restart=on-failure` + `RestartForceExitStatus=42`
- PM2 / supervisord：將 42 加入可重啟退出碼
- 純 Python 自定義監督者：循環 `Popen` + 檢測 `returncode == 42`

各監督者的完整配置示例與退出碼 42 契約說明見 [啟動流程 → 監督者指南](../advanced/startup.md#監督者指南)。

## 健康檢查

SDK 內建健康檢查端點：

```bash
# 健康檢查
curl http://localhost:8000/health
```

Docker 健康檢查可在 `docker-compose.yml` 中新增：

```yaml
services:
  erispulse:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## 反向代理

如果需要透過 Nginx 等反向代理公開 Dashboard：

```nginx
server {
    listen 80;
    server_name bot.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # WebSocket 支援（Dashboard 實時事件流需要）
    location /Dashboard/ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

SSL 可使用 Let's Encrypt：

```bash
sudo certbot --nginx -d bot.example.com
```

## 手動部署（pip）

如果不使用 Docker，也可以手動部署。

### 生產環境配置

```toml
# config/config.toml

[ErisPulse.server]
host = "0.0.0.0"
port = 8000

[ErisPulse.logger]
level = "INFO"
log_files = ["app.log"]
memory_limit = 5000

[ErisPulse.framework]
enable_lazy_loading = true
```

### systemd (Linux)

建立 `/etc/systemd/system/erispulse-bot.service`：

```ini
[Unit]
Description=ErisPulse Bot
After=network.target

[Service]
Type=simple
User=bot
WorkingDirectory=/opt/erispulse-bot
ExecStart=/opt/erispulse-bot/venv/bin/epsdk run main.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

管理：

```bash
sudo systemctl daemon-reload
sudo systemctl start erispulse-bot
sudo systemctl enable erispulse-bot
sudo journalctl -u erispulse-bot -f
```

### Supervisor

建立 `/etc/supervisor/conf.d/erispulse-bot.conf`：

```ini
[program:erispulse-bot]
command=/opt/erispulse-bot/venv/bin/python -m ErisPulse run main.py
directory=/opt/erispulse-bot
user=bot
autostart=true
autorestart=true
stderr_logfile=/var/log/erispulse-bot/err.log
stdout_logfile=/var/log/erispulse-bot/out.log
```

## 安全建議

1. **設定 Dashboard 令牌**：使用強大的隨機令牌，不要使用預設值
2. **不要將端口暴露到公網**：除非使用反向代理 + SSL，否則將 Dashboard 端口限制在內網
3. **保護資料目錄**：`config/` 目錄包含配置和資料庫，設定適當的檔案權限
4. **定期更新**：使用 `epsdk self-update` 或拉取最新 Docker 鏡像
5. **不要以 root 運行**：手動部署時建立專用使用者
6. **使用 Docker 重啟策略**：`restart: unless-stopped` 確保異常退出後自動重啟

## 多實例部署

執行多個機器人實例時：

1. 每個實例使用獨立的專案目錄和 `docker-compose.yml`
2. 使用不同的端口號：`ERISPULSE_PORT=8001`
3. 使用不同的容器名：`container_name: erispulse-bot2`

## 更新與維護

### Docker 方式

```bash
# 拉取最新鏡像
docker compose pull

# 重啟並使用新鏡像
docker compose up -d
```

### pip 方式

```bash
epsdk self-update
epsdk upgrade
```

### 備份

定期備份 `config/` 目錄：

```bash
# Docker 部署
tar czf erispulse-backup-$(date +%Y%m%d).tar.gz config/

# 或在 Dashboard 中使用「備份」功能導出
```



=====
开发者指南
=====


### 开发者指南总览

# 開發者指南

本指南幫助你開發自訂模組和適配器，以擴展 ErisPulse 的功能。

## 內容列表

### 模組開發

1. [模組開發入門](modules/getting-started.md) - 創建第一個模組
2. [模組核心概念](modules/core-concepts.md) - 模組的核心概念和架構
3. [Event 包裝類詳解](modules/event-wrapper.md) - Event 對象的完整說明
4. [模組最佳實踐](modules/best-practices.md) - 開發高品質模組的建議

### 適配器開發

1. [適配器開發入門](adapters/getting-started.md) - 創建第一個適配器
2. [適配器核心概念](adapters/core-concepts.md) - 適配器的核心概念
3. [SendDSL 詳解](adapters/send-dsl.md) - Send 消息發送 DSL 的完整說明
4. [事件轉換器](adapters/converter.md) - 實現事件轉換器
5. [適配器最佳實踐](adapters/best-practices.md) - 開發高品質適配器的建議

### 發布指南

- [發布與模組商店指南](publishing.md) - 將你的作品發布到 PyPI 和 ErisPulse 模組商店

## 開發準備

在開始開發之前，請確保你：

1. 閱讀了[基礎概念](../getting-started/basic-concepts.md)
2. 熟悉了[事件處理](../getting-started/event-handling.md)
3. 安裝了開發環境（Python >= 3.10）
4. 安裝了 ErisPulse SDK

## 開發類型選擇

根據你的需求選擇合適的開發類型：

| 開發類型 | 適用場景 | 入門指南 |
|---------|---------|---------|
| **模組開發** | 擴展機器人功能、實現業務邏輯、提供命令和訊息處理 | [模組開發入門](modules/getting-started.md) |
| **適配器開發** | 連接新的訊息平台、實現跨平台通信、提供平台特定功能 | [適配器開發入門](adapters/getting-started.md) |

> 如果你想擴展機器人的功能（如新增命令、處理訊息），選擇**模組開發**。如果你需要讓機器人連接到一個新的平台，選擇**適配器開發**。

## 開發工具

### 項目範本

ErisPulse 提供了範例項目作為參考：

- [模組範例](https://github.com/ErisPulse/ErisPulse/tree/main/examples/example-module) - 模組的完整項目結構
- [適配器範例](https://github.com/ErisPulse/ErisPulse/tree/main/examples/example-adapter) - 適配器的完整項目結構

### 開發模式

使用熱重載模式進行開發，程式碼修改後自動重載：

```bash
epsdk run main.py --reload
```

### 調試技巧

在 `config/config.toml` 中啟用 DEBUG 或 TRACE 級別日誌：

```toml
[ErisPulse.logger]
# DEBUG: 輸出模組載入、路由註冊等開發調試資訊
# TRACE: 最低級別，輸出事件分發、儲存寫入、懶加載等框架內部詳細流程
level = "DEBUG"
```

## 發布你的模組

完整的發布流程請參考 [發布與模組商店指南](publishing.md)，包括 PyPI 發布步驟、ErisPulse 模組商店提交流程等。

## 相關文件

- [標準規範](../standards/) - 確保相容性的技術標準
- [平台特性指南](../platform-guide/) - 了解各平台適配器的特性



====
模块开发
====


模块开发
----


### 模块开发入门

# 模組開發入門

本指南帶你從零開始建立一個 ErisPulse 模組。

## 項目結構

一個標準的模組結構：

```
MyModule/
├── pyproject.toml
├── README.md
├── LICENSE
└── MyModule/
    ├── __init__.py
    └── Core.py
```

## pyproject.toml 配置

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
description = "模組功能描述"
readme = "README.md"
requires-python = ">=3.10"
license = { file = "LICENSE" }
authors = [ { name = "yourname", email = "your@mail.com" } ]
dependencies = []

[project.urls]
"homepage" = "https://github.com/yourname/MyModule"

[project.entry-points."erispulse.module"]
"MyModule" = "MyModule:Main"
```

## __init__.py

```python
from .Core import Main
```

## Core.py - 基礎模組

```python
from ErisPulse import sdk
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.Core.Event import command

class Main(BaseModule):
    def __init__(self, sdk):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("MyModule")
        self.storage = sdk.storage
    
    @staticmethod
    def get_load_strategy():
        """返回模組加載策略"""
        from ErisPulse.loaders import ModuleLoadStrategy
        return ModuleLoadStrategy(
            lazy_load=True,
            priority=0,
            depends=[],  # 可選：依賴的其他模組列表
            # 可選：事件驅動懶激活——宣告觸發器，首個匹配事件/命令到達時自動加載
            # activate_on=[{"command": {"name": "hello", "help": "發送問候"}}],
        )
    
    async def on_load(self, event):
        """模組加載時調用"""
        @command("hello", help="發送問候")
        async def hello_command(event):
            name = event.get_user_nickname() or "朋友"
            await event.reply(f"你好，{name}！")
        
        self.logger.info("模組已加載")
    
    async def on_unload(self, event):
        """模組卸載時調用"""
        self.logger.info("模組已卸載")
```

> **配置讀取**：上面的基礎範例未使用配置。需要讀取配置時，推薦宣告嵌套的 `ConfigClass` 並透過 `self.cfg` 即時讀取（見 [模組核心概念](core-concepts.md#宣告式配置推薦)）。手動呼叫 `_load_config()` 的舊寫法已廢棄。

## 測試模組

### 本地測試

```bash
# 在專案目錄安裝模組
epsdk install ./MyModule

# 運行專案
epsdk run main.py --reload
```

### 測試命令

傳送命令測試：

```
/hello
```

## 核心概念

### BaseModule 基類

所有模組必須繼承 `BaseModule`，提供以下方法：

| 方法 | 說明 | 必須 |
|------|------|------|
| `__init__(self, sdk)` | 建構函式（框架傳入 `sdk` 實例） | 否 |
| `get_load_strategy()` | 返回載入策略 | 否 |
| `get_meta()` | 返回模組介紹元資訊（可選） | 否 |
| `on_load(self, event)` | 模組載入時調用 | 是 |
| `on_unload(self, event)` | 模組卸載時調用 | 是 |

### 模組介紹 meta

> [!NOTE]
> 本特性需要 ErisPulse **2.8.0+**。

透過 `get_meta()` 聲明模組的介紹元資訊（這個模組是用來做什麼的、屬於哪一類等）。  
元資訊是模組的**通用介紹資料**，供 help 模組、Dashboard 模組列表、模組商店等各類介面/生態模組消費。

與 `get_load_strategy()` 返回 `ModuleLoadStrategy` 一致，**推薦返回 `ModuleMeta` 配置類實例**（屬性鍵入、IDE 自動補全），也兼容直接返回 dict：

```python
class MyModule(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(
            name="天氣",               # 顯示名（預設註冊名）
            description="查詢城市天氣",  # 模組簡介
            version="1.0.0",
            author="ErisDev",
            group="工具",               # 功能分組
            tags=["天氣", "查詢"],
        )
```

相容寫法（dict）：

```python
class MyModule(BaseModule):
    @staticmethod
    def get_meta() -> dict:
        return {
            "name": "天氣",
            "description": "查詢城市天氣",
            "version": "1.0.0",
            "author": "ErisDev",
            "group": "工具",
            "tags": ["天氣", "查詢"],
        }
```

- `module.get_meta("MyModule")` 讀取已解析的元資訊（類宣告 > 註冊 info，自動補全該模組的指令名）。
- `module.get_commands_overview()` 聚合「模組 meta + 其註冊的指令（別名/分組/幫助）」，按模組組織的指令總覽。
- 指令歸屬模組透過 `cmd_info["owner"]` 取得（註冊時由上下文系統自動注入）。

#### meta 字段的 i18n 支援

元資訊字段值可用純字串，或 i18n 字典 `{"i18n": "key.path", "default": "兜底文本"}`（與設定 `description` 約定一致）。  
翻譯鍵透過 `I18nClass` 聲明註冊，`module.get_meta()` 讀取時自動解析為當前語言文本：

```python
class MyModule(BaseModule):
    class I18nClass(BaseI18n):
        meta_description: I18nKey = I18nKey(
            default="Weather lookup",
            zh_CN="查詢城市天氣",
            en="Weather lookup",
        )

    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(
            name="天氣",
            description={"i18n": "MyModule.meta_description", "default": "Weather lookup"},
        )
```

### SDK 物件

透過 `sdk` 物件存取核心功能：

```python
from ErisPulse import sdk

sdk.storage    # 儲存系統
sdk.config     # 設定系統
sdk.logger     # 日誌系統
sdk.adapter    # 適配器系統
sdk.router     # 路由系統
sdk.lifecycle  # 生命週期系統
```



### 模块核心概念

# 模組核心概念

了解 ErisPulse 模組的核心概念是開發高品質模組的基礎。

## 模組生命週期

### 加載策略

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.loaders import ModuleLoadStrategy

class MyModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        """返回模組加載策略"""
        return ModuleLoadStrategy(
            lazy_load=True,   # 慢加載還是立即加載
            priority=0,       # 加載優先級（數值越大越先加載）
            depends=["OtherModule"]  # 可選：聲明依賴的其他模組
        )
```

> `depends` 聲明的模組如果未註冊，當前模組將被跳過並記錄警告。加載順序由拓撲排序決定，同層級按 `priority` 降序。

> [!NOTE]
> **級聯卸載 / 級聯重載**（ErisPulse **2.8.0+**）：卸載被其它模組依賴的模組時，依賴它的模組會**先被級聯卸載**（日誌說明級聯鏈）；熱重載本地插件時，依賴它的插件同樣**級聯重載**，避免依賴者持有失效實例引用繼續運行。聲明循環依賴會在加載時以 `RuntimeError` 拒絕。

### on_load 方法

模組加載時調用，用於初始化資源和註冊事件處理器：

```python
async def on_load(self, event):
    # 註冊事件處理器
    @command("hello", help="問候命令")
    async def hello_handler(event):
        await event.reply("你好！")
    
    # 使用 SDK 內建 HTTP 客戶端（自動管理連接池，無需手動建立 session）
    # 透過 sdk.client 即可發送請求
```

### on_unload 方法

模組卸載時調用，用於清理資源：

```python
async def on_unload(self, event):
    # 清理自定義資源
    # sdk.client 由框架管理，無需手動關閉
    
    # 取消事件處理器（框架會自動處理）
    self.logger.info("模組已卸載")
```

> 後台任務的建立與清理（`self.spawn()` / 框架兜底取消）詳見 [生命週期管理](../../advanced/lifecycle.md#後台任務歸屬與自動取消)。

### 卸載與徹底卸載（purge）

> [!NOTE]
> 本特性需要 ErisPulse **2.8.0+**。

`unload()` 預設只**取消加載**（卸載實例與資源），但保留註冊存根（模組類與元資訊）——模組仍可被 discover 重新發現、`load()` 重新實例化，無需重新 `register()`。

當需要**徹底卸載**（釋放模組類引用、清理 `sys.modules`，讓插件及其獨佔依賴可被 GC 回收）時，傳入 `purge=True`：

```python
# 只取消加載：保留註冊存根，可隨時重新 load()
await sdk.module.unload("MyModule")

# 彻底卸載：刪除註冊存根 + 清理 sys.modules（插件來源）
await sdk.module.unload("MyModule", purge=True)
```

| 語義 | `unload()` 預設 | `unload(purge=True)` |
|------|-----------------|----------------------|
| 卸載實例與資源（事件/task/路由/lifecycle/i18n） | ✅ | ✅ |
| 保留註冊存根（模組類與元資訊） | ✅ | ❌ 刪除 |
| 清理 `sys.modules`（僅插件資料夾來源） | ❌ | ✅ |
| 模組類可被 GC 回收 | ❌ | ✅ |
| 重新加載 | `load()` 直接可用 | 需先 `register()` + `load()` |

> `purge=True` 時級聯卸載的依賴者同樣被 purge；卸載後框架會 `gc.collect()` 並檢查模組類/實例是否可回收，殘留引用會在日誌中告警（含引用方，DEBUG 級）。

### 生命週期全景

把上面的方法串起來，框架在加載與卸載一個模組時，**在背後為你做的全部事情**：

```mermaid
flowchart TD
    subgraph Load["加載（register → load）"]
        L1["register：登記模組類與元資訊"] --> L2["依賴校驗<br/>缺失則跳過"]
        L2 --> L3["拓撲排序（Kahn + priority）"]
        L3 --> L4["owner 注入 current_owner"]
        L4 --> L5["生成配置範本 + 註冊 i18n 翻譯鍵"]
        L5 --> L6["實例化模組（注入 sdk）"]
        L6 --> L7["呼叫 on_load()"]
        L7 --> L8["掛載到 sdk 屬性 + emit module.load"]
    end

    subgraph Unload["卸載（unload）"]
        U1["呼叫 on_unload()"] --> U2["兜底取消後台任務（self.spawn 歸屬）"]
        U2 --> U3["清理 i18n 翻譯鍵"]
        U3 --> U4["移除路由 / 命令 / 事件處理器（按 owner）"]
        U4 --> U5["清理 lifecycle 鉤子（按 owner）"]
        U5 --> U6["移除 SDK 屬性 + 慢加載代理"]
        U6 --> U7["emit module.unload"]
    end

    Load --> Unload
```

**加載時框架幫你做了什麼**（你只需寫 `on_load`，其餘自動完成）：

| 環節 | 框架自動做的 |
|------|-------------|
| owner 注入 | 實例化期間用 `owner_scope` 包住模組名——你 `on_load` 裡註冊的命令/事件/鉤子/後台任務**自動歸屬本模組**，卸載時按 owner 一鍵清理 |
| 配置範本 | 聲明了 `ConfigClass` 的模組，框架自动生成/填補 `ErisPulse.<ModuleName>` 配置段 |
| i18n 翻譯鍵 | 聲明了 `I18nClass` 的模組，翻譯鍵自動註冊（卸載時自動註銷） |
| 依賴拓撲 | 按 `depends` 聲明排序，確保被依賴模組先加載；循環依賴以 `RuntimeError` 拒絕 |
| SDK 挂載 | 實例化後掛到 `sdk.<ModuleName>`，你才能 `sdk.MyModule.xxx` 訪問 |

**卸載時框架幫你清理的**（對應上面的 U1→U7）：`on_unload` 跑完後再兜底清理——後台任務強制取消（`self.spawn` 建立的，優雅收尾請在 `on_unload` 自行做）、i18n 鍵、路由、命令/事件處理器、lifecycle 鉤子，最後移除 SDK 屬性。`purge=True` 預設額外刪除註冊存根 + 清理 `sys.modules`。

> 這些自動清理就是「你只需寫 `on_load`/`on_unload`，不用手動 unregister」的底氣——框架用 owner 歸屬把「誰註冊的誰清理」做成了一鍵式。

## SDK 物件

### 訪問核心模組

```python
from ErisPulse import sdk

# 透過 sdk 物件存取所有核心模組
sdk.logger.info("日誌")
sdk.storage.set("key", "value")
config = sdk.config.getConfig("MyModule")
```

### 模組間通訊

```python
# 訪問其他模組
other_module = sdk.OtherModule
result = await other_module.some_method()
```

## 適配器發送方法查詢

由於新的標準規範要求使用重寫 `__getattr__` 方法來實現兜底發送機制，導致無法使用 `hasattr` 方法來檢查方法是否存在。從 `2.3.5` 開始，新增了查詢發送方法的功能。

### 列出支援的發送方法

```python
# 列出平台支援的所有發送方法
methods = sdk.adapter.list_sends("onebot11")
# 返回: ["Text", "Image", "Voice", "Markdown", ...]
```

### 獲取方法詳細資訊

```python
# 獲取某個方法的詳細資訊
info = sdk.adapter.send_info("onebot11", "Text")
# 返回:
# {
#     "name": "Text",
#     "parameters": [
#         {"name": "text", "type": "str", "default": null, "annotation": "str"}
#     ],
#     "return_type": "Awaitable[Any]",
#     "docstring": "發送文本訊息..."
# }
```

## 配置管理

### 聲明式配置（推薦）

從 v2.5.2 開始，模組可透過 `ConfigClass` 聲明配置類，與適配器使用同一套配置 Schema 系統。配置透過 `self.cfg` 即時讀取，修改後立即生效：

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.Core.Bases import BaseConfig

@dataclass
class MyModuleConfig(BaseConfig):
    api_key: str = field(
        default="",
        metadata={
            "description": {"i18n": "my_module.api_key", "default": "API 密鑰"},
            "required": True,
            "secret": True,
            "ui": {"widget": "password", "group": "basic", "order": 1},
        },
    )
    timeout: int = field(
        default=30,
        metadata={
            "description": {"i18n": "my_module.timeout", "default": "超時時間（秒）"},
            "ui": {"widget": "number", "group": "advanced", "order": 2},
        },
    )

class MyModule(BaseModule):
    ConfigClass = MyModuleConfig

    def __init__(self, sdk):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("MyModule")

    async def on_load(self, event):
        self.logger.info("模組已載入")

    async def on_unload(self, event):
        pass

    async def do_something(self):
        cfg = self.cfg  # 即時讀取，類型安全
        api_key = cfg.api_key
        timeout = cfg.timeout
```

`BaseConfig` 是通用配置基類，適用於適配器、模組、外部專案等任何場景。配置欄位支援 i18n 多語言描述（詳見 [i18n 文檔](../../advanced/i18n.md#配置欄位多語言)）。

### 聲明式翻譯鍵（v2.7.0+）

從 v2.7.0 開始，模組也可以像宣告 `ConfigClass` 一樣，透過嵌套類 `I18nClass` 集中宣告翻譯鍵。框架會在載入時**自動註冊**所有宣告的翻譯鍵，無需手動呼叫 `i18n.register()`，且註冊時機早於配置模板生成，確保配置描述中引用的 i18n 鍵已可用。

```python
from ErisPulse.Core.Bases import BaseConfig, BaseI18n, I18nKey

class MyModule(BaseModule):
    # 配置類（可選）
    @dataclass
    class ConfigClass(BaseConfig):
        welcome_msg: str = field(
            default="歡迎",
            metadata={
                "description": {"i18n": "mymodule.welcome_msg", "default": "歡迎訊息"},
            },
        )

    # 翻譯鍵集合類（可選）
    class I18nClass(BaseI18n):
        # 屬性名自動拼接為完整鍵路徑：<模組名>.<屬性名>
        welcome_msg: I18nKey = I18nKey(
            default="Welcome Message",   # 語言無關的兜底
            zh_CN="歡迎訊息",
            zh_TW="歡迎訊息",
            en="Welcome Message",
            ja="ウェルカムメッセージ",
            ru="Приветственное сообщение",
        )
        hello: I18nKey = I18nKey(
            default="Hello, {name}!",
            zh_CN="你好，{name}！",
            zh_TW="你好，{name}！",
            en="Hello, {name}!",
            ja="こんにちは、{name}！",
            ru="Привет, {name}!",
        )
```

詳情見 [i18n 推薦寫法](../../advanced/i18n.md#推薦寫法通過-i18nclass-宣告翻譯鍵-v270)。

### 手動讀取配置（已廢棄）

> **已廢棄**：請改用 [聲明式配置](#聲明式配置推薦) + `self.cfg` 即時讀取。

```python
class MyModule(BaseModule):
    def __init__(self, sdk):
        self.sdk = sdk

    def _load_config(self):
        config = self.sdk.config.getConfig("MyModule")
        if not config:
            self.sdk.config.setConfig("MyModule", {"api_key": "", "timeout": 30})
            return {"api_key": "", "timeout": 30}
        return config
```

## 存儲系統

### 基本使用

```python
# 存儲數據
sdk.storage.set("user:123", {"name": "張三"})

# 獲取數據
user = sdk.storage.get("user:123", {})

# 刪除數據
sdk.storage.delete("user:123")
```

### 事務使用

```python
# 使用事務確保數據一致性
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
    # 如果任何操作失敗，所有更改都會回滾
```

## 事件處理

### 事件處理器註冊

```python
from ErisPulse.Core.Event import command, message

# 註冊命令
@command("info", help="獲取資訊")
async def info_handler(event):
    await event.reply("這是資訊")

# 註冊訊息處理器
@message.on_group_message()
async def group_handler(event):
    sdk.logger.info(f"收到群訊息: {event.get_text()}")
```

### 事件處理器生命週期

框架會自動管理事件處理器的註冊與註銷，你只需要在 `on_load` 中註冊即可。

## 慢載機制

### 工作原理

```python
# 模塊首次被存取時才會初始化
result = await sdk.my_module.some_method()
# ↑ 這裡會觸發模塊初始化
```

### 立即載入

對於需要立即初始化的模塊（如監聽器、定時器）：

```python
@staticmethod
def get_load_strategy():
    return ModuleLoadStrategy(
        lazy_load=False,  # 立即載入
        priority=100
    )
```

## 錯誤處理

### 異常捕獲

```python
async def handle_event(self, event):
    try:
        # 業務邏輯
        await self.process_event(event)
    except ValueError as e:
        self.logger.warning(f"參數錯誤: {e}")
        await event.reply(f"參數錯誤: {e}")
    except Exception as e:
        self.logger.error(f"處理失敗: {e}")
        raise
```

### 日誌記錄

```python
# 使用不同的日誌級別
self.logger.debug("除錯資訊")    # 詳細除錯資訊
self.logger.info("運行狀態")      # 正常運行資訊
self.logger.warning("警告資訊")  # 警告資訊
self.logger.error("錯誤資訊")    # 錯誤資訊
self.logger.critical("致命錯誤") # 致命錯誤
```

## 相關文件

- [模組開發入門](getting-started.md) - 建立第一個模組
- [Event 包裝類別](event-wrapper.md) - 事件處理詳解
- [最佳實踐](best-practices.md) - 開發高品質模組



### Event 包装类详解

# Event 包裝類詳解

Event 模組提供了功能強大的 Event 包裝類，簡化事件處理。

請直接返回翻譯後的完整 Markdown 內容，不要包含任何其他文字。

再次提醒：如果文件包含語言切換行（各語言名稱用 `` | `` 分隔的行），請務必嚴格遵守上方第8條的格式要求，不要寫出 ``[**Label**](file)`` 這類錯誤格式。

## 為 event 參數添加類型註解

事件處理器的 `event` 參數是 **Event 包裝類**（dict 子類）。強烈建議為它添加類型註解：

```python
from ErisPulse.Core.Event import Event

@message.on_private_message()
async def handler(event: Event):
    text = event.get_text()   # IDE 自動補全所有便捷方法
    await event.reply(text)   # 拼寫錯誤在靜態檢查時即可發現
```

不加註解時 IDE 無法識別 Event 上的方法（`get_text()` / `reply()` / `wait_reply()` / 平台擴展方法均不提示），只能靠記憶拼寫。

> **注意區分**：事件處理器回調的 `event` 是 **Event 包裝類**（註解為 `Event`）；模組生命週期方法 `on_load` / `on_unload` 的 `event` 是普通 **dict**（註解為 `dict`），二者不要混淆。

[**English**](docs/zh-TW/quick-start.md)

## 核心特性

- **完全相容字典**：Event 繼承自 dict
- **便捷方法**：提供大量便捷方法
- **點式存取**：支援使用點號存取事件欄位
- **向後相容**：所有方法都是可選的

請直接返回翻譯後的完整Markdown內容，不要包含任何其他文字。

再次提醒：如果文件包含語言切換行（各語言名稱用 `` | `` 分隔的行），務必嚴格遵守上方第8條的格式要求，不要寫出 ``[**Label**](file)`` 這類錯誤格式。

## 核心字段方法

```python
from ErisPulse.Core.Event import command

@command("info")
async def info_command(event: Event):
    event_id = event.get_id()
    platform = event.get_platform()
    time = event.get_time()
    print(f"ID: {event_id}, 平台: {platform}, 時間: {time}")
```

[**回到顶部**](#top)

## 消息事件方法

```python
from ErisPulse.Core.Event import message

@message.on_private_message()
async def private_handler(event: Event):
    text = event.get_text()
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    await event.reply(f"你好，{nickname}！")
```

[**快速入門**](docs/zh-TW/quick-start.md) | [**核心概念**](docs/zh-TW/core-concepts.md) | [**事件處理**](docs/zh-TW/event-handling.md) | [**API 參考**](docs/zh-TW/api-reference.md)

## 消息類型判斷

```python
from ErisPulse.Core.Event import message

@message.on_group_message()
async def group_handler(event: Event):
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    is_at = event.is_at_message()
    await event.reply(f"類型: {'私聊' if is_private else '群聊'}")
```

7. **重要：路徑替換規則**
   - 將文件連結中的 `docs/zh-TW/` 替換為 `docs/zh-TW/`
   - 例如：`docs/zh-TW/quick-start.md` 應改為 `docs/zh-TW/quick-start.md`
   - 對於指向非當前語言版本文件的連結（如 `README.xx.md` 形式的連結），保持原樣不要修改
   - 這確保了連結指向正確語言的文件版本

## 回覆功能

```python
from ErisPulse.Core.Event import command

@command("ask")
async def ask_command(event: Event):
    await event.reply("請輸入你的名字:")
    reply = await event.wait_reply(timeout=30)
    if reply:
        name = reply.get_text()
        await event.reply(f"你好，{name}！")

@command("price")
async def price_command(event: Event):
    await event.reply("請輸入金額（如：5元）:")
    # 回覆必須符合正則，否則繼續等待直到超時
    reply = await event.wait_reply(timeout=30, regex=r"\d+\s*元")
    if reply:
        await event.reply(f"收到金額：{reply.get_text()}")
```

## 命令資訊獲取

```python
from ErisPulse.Core.Event import command

@command("cmdinfo")
async def cmdinfo_command(event: Event):
    cmd_name = event.get_command_name()
    cmd_args = event.get_command_args()
    await event.reply(f"命令: {cmd_name}, 參數: {cmd_args}")
```

7. **重要：路徑替換規則**
   - 將文件鏈接中的 `docs/zh-TW/` 替換為 `docs/zh-TW/`
   - 例如：`docs/zh-TW/quick-start.md` 應改為 `docs/zh-TW/quick-start.md`
   - 對於指向非當前語言版本文件的鏈接（如 `README.xx.md` 形式的鏈接），保持原樣不要修改
   - 這確保了鏈接指向正確語言的文件版本

## 通知事件方法

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event: Event):
    await event.reply("歡迎添加我為好友！")
```

請直接返回翻譯後的完整Markdown內容，不要包含任何其他文字。

再次提醒：如果文件包含語言切換行（各語言名稱用 `` | `` 分隔的行），務必嚴格遵守上方第8條的格式要求，不要寫出 ``[**Label**](file)`` 這類錯誤格式。

## 方法速查表

### 核心方法

#### 事件基礎信息
- `get_id()` - 獲取事件ID
- `get_time()` - 獲取事件時間戳（Unix秒級）
- `get_type()` - 獲取事件類型（message/notice/request/meta）
- `get_detail_type()` - 獲取事件詳細類型（private/group/friend等）
- `get_platform()` - 獲取平台名稱

#### 机器人信息
- `get_self_platform()` - 獲取機器人平台名稱
- `get_self_user_id()` - 獲取機器人用戶ID
- `get_self_account_id()` - 獲取機器人賬戶ID（多Bot模式）
- `get_self_info()` - 獲取機器人完整信息字典

#### 會話標識
- `get_target_id()` - 獲取統一目標ID（群聊返回 `group_id`，頻道返回 `channel_id`，私聊返回 `user_id`，按 group → channel → guild → thread → user 顺序取首个非空值）
- `get_session_id()` - 獲取會話唯一標識，格式為 `{platform}:{detail_type}:{target_id}`

### 消息事件方法

#### 消息內容
- `get_message()` - 獲取消息段數組（OneBot12格式）
- `get_alt_message()` - 獲取消息備用文本
- `get_text()` - 獲取純文本內容（`get_alt_message()` 的別名）
- `get_message_text()` - 獲取純文本內容（`get_alt_message()` 的別名）

#### 發送者信息
- `get_user_id()` - 獲取發送者用戶ID
- `get_user_nickname()` - 獲取發送者暱稱
- `get_sender()` - 獲取發送者完整信息字典

#### 群組/頻道信息
- `get_group_id()` - 獲取群組ID（群聊消息）
- `get_channel_id()` - 獲取頻道ID（頻道消息）
- `get_guild_id()` - 獲取伺服器ID（伺服器消息）
- `get_thread_id()` - 獵取話題/子頻道ID（話題消息）

#### @消息相關
- `has_mention()` - 是否包含@機器人
- `get_mentions()` - 獲取所有被@的用戶ID列表

### 消息類型判斷

#### 基礎判斷
- `is_message()` - 是否為消息事件
- `is_private_message()` - 是否為私聊消息
- `is_group_message()` - 是否為群聊消息
- `is_at_message()` - 是否為@消息（`has_mention()` 的別名）

### 通知事件方法

#### 通知操作者
- `get_operator_id()` - 獲取操作者ID
- `get_operator_nickname()` - 獲取操作者暱稱

#### 通知類型判斷
- `is_notice()` - 是否為通知事件
- `is_group_member_increase()` - 群成員增加事件
- `is_group_member_decrease()` - 群成員減少事件
- `is_friend_add()` - 好友添加事件（匹配 `detail_type == "friend_increase"`）
- `is_friend_delete()` - 好友刪除事件（匹配 `detail_type == "friend_decrease"`）

### 請求事件方法

#### 請求信息
- `get_comment()` - 獲取請求附言

#### 請求類型判斷
- `is_request()` - 是否為請求事件
- `is_friend_request()` - 是否為好友請求
- `is_group_request()` - 是否為群組請求

### 回覆功能

#### 基礎回覆
- `reply(content, method="Text", at_sender=False, quote=False, at_users=None, reply_to=None, at_all=False, via=None, **kwargs)` - 通用回覆方法
  - `content`: 發送內容（文本、URL等）
  - `method`: 發送方法，預設 "Text"，可選 "Image"/"Voice"/"Video"/"File" 等
  - `at_sender`: 是否@發送者（自動提取 user_id）
  - `quote`: 是否引用回覆當前消息（自動提取 message_id）
  - `at_users`: @用戶列表，如 `["user1", "user2"]`
  - `reply_to`: 手動指定回覆的消息 ID
  - `at_all`: 是否@全體成員
  - `**kwargs`: 預留參數（如 Mention 方法的 user_id）

- `reply_ob12(message)` - 使用 OneBot12 消息段回覆
  - `message`: OneBot12 消息段列表或字典，可配合 MessageBuilder 構建

#### 平台能力查詢
- `supports(method)` - 檢查當前平台是否支援某發送方法（如 `"Image"`、`"Voice"`），返回 `bool`
- `available_methods()` - 列出當前平台所有可用發送方法，返回方法名列表

#### 轉發功能

> **注意**：轉發功能需要透過適配器的 Send DSL 實現，Event 包裝類本身不提供直接的轉發方法。

```python
# 轉發消息到群組
adapter = sdk.adapter.get(event.get_platform())
target_id = event.get_group_id()  # 或指定其他群組ID
await adapter.Send.To("group", target_id).Text(event.get_text())
```

### 等待回覆功能

- `wait_reply(prompt=None, timeout=60.0, callback=None, validator=None, method="Text", pattern=None, regex=None)` - 等待用戶回覆
  - `prompt`: 提示消息，如果提供會發送給用戶
  - `timeout`: 等待超時時間（秒），預設60秒
  - `callback`: 回調函數，當收到回覆時執行
  - `validator`: 驗證函數，用於驗證回覆是否有效
  - `method`: 發送提示消息的方法，預設 "Text"
  - `pattern`: glob 通配符（`*` / `?` / `[seq]`），回覆文本必須匹配，不匹配則繼續等待
  - `regex`: 正則表達式，回覆文本必須匹配（`pattern` 與 `regex` 二選一），不匹配則繼續等待
  - 返回用戶回覆的 Event 對象，超時返回 None

#### 互動方法

- `confirm(prompt=None, timeout=60.0, yes_words=None, no_words=None, method="Text", hint=False)` - 確認對話
  - 返回 `True`（確認）/ `False`（否認）/ `None`（超時）
  - 內建中英文確認詞自動識別，可自定義詞集
  - `method`: 發送方法，預設 "Text"；支援 "Image"/"Markdown" 等非文本方式發送提示
  - `hint`: 是否在提示末尾自動追加確認詞提示（如 "（是/否）"），預設 False

- `choose(prompt, options, timeout=60.0, method="Text", options_format="auto", merge_prompt=False, placeholder="{options}")` - 選擇菜單
  - `options`: 選項文本列表
  - 返回選項索引（0-based），超時返回 `None`
  - `method`: 發送方法，預設 "Text"；文本類方法 (Text/Markdown/md/Html/h5) 預設合併選項到末尾
  - `options_format`: 選項格式（預設: "auto"，根據 method 自動選擇內建樣式）
    - `"auto"`：Markdown→無序列表（`- 1.選項`），Html→有序列表（`<ol>`），其他→純文本列表
    - `"list"`：每行一個，如 ``1. 選項A\n2. 選項B``
    - `"inline"`：單行展示，如 ``1.A | 2.B``
    - `"md"`：Markdown 無序列表
    - `"html"`：Html 有序列表
    - `callable`：自定義函數，接收 ``list[str]`` 返回 ``str``
  - `merge_prompt`: 是否強制合併為一條消息發送，預設 False
    - `False`（預設）：文本類方法自動合併；非文本方法先發 prompt 再發 Text 選項
    - `True`：無論什麼 method 都合併為一條消息，用用戶指定的 method 發送
  - `placeholder`: 選項插入占位符，預設 `{options}`；prompt 中出現該標記的位置替換為選項文本，設為空字串則始終追加到末尾

- `collect(fields, timeout_per_field=60.0)` - 表單收集
  - `fields`: 字段列表，每項包含 `key`、`prompt`、可選 `validator`、可選 `method`
  - 返回 `{key: value}` 字典，任一字段超時返回 `None`
  - 每個 field 支援 `method` 鍵指定發送方法，例如收集圖片時用 `{"key": "avatar", "prompt": "請發送頭像", "method": "Image"}`
  - 每個 field 可選 `options` 鍵（列表），提供時該字段變為選擇題（自動調用 choose 邏輯）
  - 每個 field 可選 `options_format`、`merge_prompt`、`placeholder` 鍵，控制選項格式、消息合併行為和占位符

- `wait_for(event_type="message", condition=None, timeout=60.0)` - 等待任意事件
  - `condition`: 過濾函數，返回 `True` 時匹配
  - 返回匹配的 Event 對象，超時返回 `None`

- `conversation(timeout=60.0)` - 創建多輪對話上下文
  - 返回 `Conversation` 對象，支援 `say()`/`wait()`/`confirm()`/`choose()`/`collect()`/`stop()`
  - `is_active` 屬性表示對話是否活躍

#### 互動方法示例

**confirm() - 確認對話：**

```python
@command("delete", help="刪除數據")
async def delete_handler(event: Event):
    if await event.confirm("確定要刪除所有數據嗎？"):
        sdk.storage.delete("all_data")
        await event.reply("數據已刪除")
    else:
        await event.reply("已取消")
```

**confirm() - 帶提示詞：**

```python
# hint=True 會在提示末尾追加 "（是/否）"
if await event.confirm("確定繼續？", hint=True):
    await event.reply("已繼續")
# 用戶看到：確定繼續？（是/否）
```

**choose() - 選擇菜單：**

```python
@command("color", help="選擇顏色")
async def color_handler(event: Event):
    choice = await event.choose("請選擇顏色：", ["紅色", "綠色", "藍色"])
    if choice is not None:
        colors = ["紅色", "綠色", "藍色"]
        await event.reply(f"你選擇了：{colors[choice]}")
```

**choose() - 選項格式化與消息合併：**

```python
# inline 格式：選項顯示在同一行
choice = await event.choose("請選擇：", ["A", "B", "C"], options_format="inline")
# 輸出：1.A | 2.B | 3.C

# 自定義格式
choice = await event.choose("請選擇：", ["貓", "狗"],
    options_format=lambda opts: " / ".join(opts))
# 輸出：貓 / 狗

# options_format="auto"（預設）：根據 method 自動選擇內建樣式
# Markdown → 無序列表
choice = await event.choose(
    "## 請選擇", ["貓", "狗"],
    method="Markdown",  # auto 自動識別為 md 列表
)
# 輸出：
# ## 請選擇
# - 1. 貓
# - 2. 狗

# Html → 有序列表
choice = await event.choose(
    "<h2>請選擇</h2>", ["貓", "狗"],
    method="Html", merge_prompt=True,  # auto 自動識別為 html 列表
)
# 輸出：
# <h2>請選擇</h2>
# <ol><li>1. 貓</li><li>2. 狗</li></ol>

# 合併模式 + 占位符
choice = await event.choose(
    "## 請選擇\n{options}\n請回覆編號",
    ["貓", "狗"],
    method="Markdown", merge_prompt=True,
)

# 自定義占位符
choice = await event.choose(
    "請選擇: [choices]",
    ["貓", "狗"],
    placeholder="[choices]",
)
```

**collect() - 表單收集：**

```python
@command("register", help="註冊")
async def register_handler(event: Event):
    data = await event.collect([
        {"key": "name", "prompt": "請輸入姓名："},
        {"key": "age", "prompt": "請輸入年齡：",
         "validator": lambda e: e.get_text().isdigit()},
    ])
    if data:
        await event.reply(f"註冊成功！{data['name']}，{data['age']}歲")
```

**非 Text 方法的 reply：**

```python
await event.reply("http://example.com/img.jpg", method="Image")
await event.reply("http://example.com/audio.mp3", method="Voice")

from ErisPulse.Core.Event import MessageBuilder
segments = MessageBuilder.text("看這張圖：").image("http://example.com/img.jpg").build()
await event.reply_ob12(segments)
```

> 完整的 Conversation 多輪對話用法請參考 [Conversation 多輪對話](../../advanced/conversation.md)。

### 命令信息

#### 命令基礎
- `get_command_name()` - 獲取命令名稱
- `get_command_args()` - 獲取命令參數列表
- `get_command_raw()` - 獲取命令原始文本
- `get_command_info()` - 獲取完整命令信息字典
- `is_command()` - 是否為命令

### 原始數據

- `get_raw()` - 獲取平台原始事件數據
- `get_raw_type()` - 獲取平台原始事件類型

### 平台擴展方法

適配器可以為 Event 包裝類註冊平台專有方法。方法僅在對應平台的 Event 實例上可用，其他平台訪問時拋出 `AttributeError`。

平台方法透過 `Event.__getattribute__` 優先於內置方法生效，因此可以覆寫 `confirm`、`choose`、`collect`、`wait_reply` 等內置互動方法，提供平台特色實現（如按鈕、卡片等）。內置實現作為 `_builtin_*` 函數導出供覆寫方調用。

```python
# 郵件事件 - 只有郵件方法
event = Event({"platform": "email", "email_raw": {"subject": "Hello"}})
event.get_subject()      # ✅ 返回 "Hello"
event.get_chat_type()    # ❌ AttributeError

# Telegram 事件 - 只有 Telegram 方法
event = Event({"platform": "telegram", "telegram_raw": {"chat": {"type": "private"}}})
event.get_chat_type()    # ✅ 返回 "private"
event.get_subject()      # ❌ AttributeError

# 內置方法始終可用
event.get_text()         # ✅ 任何平台
event.reply("hi")        # ✅ 任何平台
```

### 查詢已註冊方法

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("email")
# ["get_subject", "get_from", ...]
```

### `hasattr` 和 `dir` 支援

```python
hasattr(event, "get_subject")   # 僅當 platform="email" 時返回 True
"get_subject" in dir(event)     # 同上
```

### 跨平台擴展（通配符）

`register_event_method` 和 `register_event_mixin` 支援傳 `"*"` 作為平台名，註冊的方法在**所有平台**的 Event 實例上都可用。適合 AI 對話、上下文管理等需要跨平台複用的功能。

```python
from ErisPulse.Core.Event.wrapper import register_event_method

@register_event_method("*")
async def ai_chat(self, prompt: str):
    # self 為 Event 實例，可訪問事件數據和內置方法
    await self.reply(f"AI: {prompt}")
```

註冊後，任何平台的事件處理器都能調用 `event.ai_chat(...)`。

方法解析優先級（從高到低）：平台特定方法 → 通配符方法 → 內置方法 → 字典鍵訪問。

> 適配器開發者註冊擴展方法的方式請參閱 [事件系統 API - 跨平台擴展通配符](../../api-reference/event-system.md#跨平台擴展通配符)。

## 相關文件

- [模組開發入門](getting-started.md) - 建立第一個模組
- [最佳實務](best-practices.md) - 開發高品質模組



### 模块开发最佳实践

# 模組開發最佳實踐

本文檔提供了 ErisPulse 模組開發的最佳實踐建議。

## 模組設計

### 1. 單一職責原則

每個模組應該只負責一個核心功能：

```python
# 好的設計：每個模組只負責一個功能
class WeatherModule(BaseModule):
    """天氣查詢模組"""
    pass

class NewsModule(BaseModule):
    """新聞查詢模組"""
    pass

# 不好的設計：一個模組負責多個不相關的功能
class UtilityModule(BaseModule):
    """包含天氣、新聞、笑話等多個功能"""
    pass
```

### 2. 模組命名規範

```toml
[project]
name = "ErisPulse-ModuleName"  # 使用 ErisPulse- 前綴
```

### 3. 清晰的配置管理

推薦使用宣告式配置（`ConfigClass` + `BaseConfig`），獲得類型安全、自動模板生成、WebUI 表單支援等能力：

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BaseConfig

@dataclass
class MyModuleConfig(BaseConfig):
    api_url: str = field(default="https://api.example.com", metadata={
        "description": {"i18n": "my_module.api_url", "default": "API 位址"},
    })
    timeout: int = field(default=30, metadata={
        "description": {"i18n": "my_module.timeout", "default": "超時時間（秒）"},
    })
    cache_ttl: int = field(default=3600, metadata={
        "description": {"i18n": "my_module.cache_ttl", "default": "緩存存活時間（秒）"},
    })

class MyModule(BaseModule):
    ConfigClass = MyModuleConfig

    async def do_something(self):
        cfg = self.cfg  # 類型安全，即時讀取
        await self._fetch(cfg.api_url, timeout=cfg.timeout)
```

也可以繼續使用手動方式讀寫配置儲存（見[模組核心概念](core-concepts.md#配置管理)）。

### 宣告式翻譯鍵（v2.7.0+）

模組可以透過 `I18nClass` 集中宣告翻譯鍵，框架會自動註冊到 i18n 系統，無需手動呼叫 `i18n.register()`。

```python
from ErisPulse.Core.Bases import BaseI18n, I18nKey

class MyModule(BaseModule):
    class I18nClass(BaseI18n):
        # 帶占位符的業務翻譯鍵
        welcome: I18nKey = I18nKey(
            default="Welcome, {name}!",
            zh_CN="歡迎你，{name}！",
            zh_TW="歡迎你，{name}！",
            en="Welcome, {name}!",
            ja="ようこそ、{name}！",
            ru="Добро пожаловать, {name}!",
        )
        # 配置欄位描述的翻譯
        api_url: I18nKey = I18nKey(
            default="API URL",
            zh_CN="API 位址",
            zh_TW="API 位址",
            en="API URL",
            ja="API URL",
            ru="API URL",
        )
```

詳細用法見 [i18n 文檔](../../advanced/i18n.md#推薦寫法通過-i18nclass-宣告翻譯鍵-v270)。

## 異步編程

### 1. 使用異步庫

```python
# 推薦使用 SDK 內建 HTTP 客戶端（異步，自動日誌和統計）
from ErisPulse.Core import client

class MyModule(BaseModule):
    async def fetch_data(self, url):
        resp = await client.get(url)
        return await resp.json()

# 也可透過 sdk.client 使用（效果相同）
from ErisPulse import sdk

class MyModule(BaseModule):
    async def fetch_data(self, url):
        resp = await sdk.client.get(url)
        return await resp.json()

# 不要使用 aiohttp 直接導入（不利於框架統一管理）
import aiohttp

class MyModule(BaseModule):
    async def fetch_data(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.json()

# 不要使用 requests（同步，會阻塞事件循環）
import requests

class MyModule(BaseModule):
    def fetch_data(self, url):
        return requests.get(url).json()  # 會阻塞事件循環
```

### 2. 正確的異步操作

```python
from ErisPulse.Core.Event import Event  # event: Event 注解可獲得 IDE 補全

async def handle_command(self, event: Event):
    # 需要等待結果的耗時操作：直接 await（生命週期明確）
    result = await self._long_operation()

async def on_load(self, event: dict):
    # 後台任務（輪詢/定時/fire-and-forget）：使用 self.spawn()，
    # 模組卸載時框架在 on_unload 之後兜底取消，避免持有 self 導致泄漏
    self.spawn(self._poll())
```

> [!NOTE]
> 後台任務推薦 `self.spawn()`（ErisPulse **2.8.0+**），而不是 `asyncio.create_task`——後者創建的裸任務不歸屬模組，卸載時不會被自動清理，會持有 `self` 引用導致模組實例無法被回收（熱重載泄漏）。詳見 [生命週期管理](../../advanced/lifecycle.md#後台任務歸屬與自動取消)。

### 3. 資源管理

```python
async def on_load(self, event):
    # SDK 客戶端已自動管理連接池，無需手動創建 session
    pass
    
async def on_unload(self, event):
    # 如需自定義客戶端，記得清理資源
    pass
```

## 事件處理

### 1. 使用 Event 包裝類

```python
# 使用 Event 包裝類的便捷方法
@command("info")
async def info_command(event: Event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    await event.reply(f"你好，{nickname}！")

# 而非直接訪問字典
@command("info")
async def info_command(event: Event):
    user_id = event["user_id"]  # 不夠清晰，容易出錯
```

### 2. 合理使用懶加載

```python
# 低頻命令模塊：聲明 activate_on 觸發器，首個匹配命令到達時自動激活（保持懶加載）
class CommandModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=True, activate_on=[
            {"command": {"name": "dice", "help": "擲一個骰子", "aliases": ["d"]}},
        ])

# 低頻監聽器模塊：聲明事件觸發器，事件到達時自動激活
class ListenerModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=True, activate_on=[
            {"notice": "group_member_increase"},
        ])

# 高頻觸發（每條消息都要處理）或啟動時就必須就緒的模塊：立即加載
class HotListenerModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=False)

# 工具模塊適合懶加載
class UtilityModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=True)
```

> `activate_on` 的完整語法（事件三形式 / 命令簡寫與 dict 聲明 / help 回退鏈）見
> [懶加載模塊系統](../../advanced/lazy-loading.md#事件驅動懶激活activate_on)。

### 3. 事件處理器註冊

```python
async def on_load(self, event):
    # 在 on_load 中註冊事件處理器
    @command("hello")
    async def hello_handler(event: Event):
        await event.reply("你好！")
    
    @message.on_group_message()
    async def group_handler(event: Event):
        self.logger.info("收到群消息")
    
    # 不需要手動註銷，框架會自動處理
```

## 錯誤處理

### 1. 分類異常處理

```python
async def handle_event(self, event: Event):
    try:
        result = await self._process(event)
    except ValueError as e:
        # 預期的業務錯誤
        self.logger.warning(f"業務警告: {e}")
        await event.reply(f"參數錯誤: {e}")
    except aiohttp.ClientError as e:
        # 網絡錯誤（推薦使用 sdk.client + ClientError 替代）
        # 舊代碼直接用 aiohttp 仍可正常工作，但新代碼推薦使用 ErisPulse 異常體系
        self.logger.error(f"網絡錯誤: {e}")
        await event.reply("網絡請求失敗，請稍後重試")
    except Exception as e:
        # 未預期的錯誤
        self.logger.error(f"未知錯誤: {e}", exc_info=True)
        await event.reply("處理失敗，請聯繫管理員")
        raise
```

### 2. 超時處理

```python
# 推薦使用 SDK 內置客戶端（自帶超時和重試）
from ErisPulse.Core import client
from ErisPulse.Core.Bases.errors import ClientTimeoutError

async def fetch_with_timeout(self, url, timeout=30):
    try:
        resp = await client.get(url, timeout=timeout)
        return await resp.json()
    except ClientTimeoutError:
        self.logger.warning(f"請求超時: {url}")
        raise
```

## 儲存系統

### 1. 使用事務

```python
# 使用事務確保資料一致性
async def update_user(self, user_id, data):
    with self.sdk.storage.transaction():
        self.sdk.storage.set(f"user:{user_id}:profile", data["profile"])
        self.sdk.storage.set(f"user:{user_id}:settings", data["settings"])

# ❌ 不使用事務可能導致資料不一致
async def update_user(self, user_id, data):
    self.sdk.storage.set(f"user:{user_id}:profile", data["profile"])
    # 如果這邊出錯，上面的設定無法回滾
    self.sdk.storage.set(f"user:{user_id}:settings", data["settings"])
```

### 2. 批次操作

```python
# 使用批次操作提升效能
def cache_multiple_items(self, items):
    self.sdk.storage.set_multi({
        f"item:{k}": v for k, v in items.items()
    })

# ❌ 多次呼叫效率低
def cache_multiple_items(self, items):
    for k, v in items.items():
        self.sdk.storage.set(f"item:{k}", v)
```

## 日誌記錄

### 1. 合理使用日誌級別

```python
# DEBUG: 詳細的除錯資訊（僅開發時使用）
self.logger.debug(f"輸入參數: {params}")

# INFO: 正常運行資訊
self.logger.info("模組已載入")
self.logger.info(f"處理請求: {request_id}")

# WARNING: 警告資訊，不影響主要功能
self.logger.warning(f"設定項 {key} 未設定，使用預設值")
self.logger.warning("API 回應慢，可能需要優化")

# ERROR: 錯誤資訊
self.logger.error(f"API 請求失敗: {e}")
self.logger.error(f"處理事件失敗: {e}", exc_info=True)

# CRITICAL: 致命錯誤，需要立即處理
self.logger.critical("資料庫連線失敗，機器人無法正常運行")
```

### 2. 結構化日誌

```python
# 使用結構化日誌，便於解析
self.logger.info(f"處理請求: request_id={request_id}, user_id={user_id}, duration={duration}ms")

# ❌ 使用非結構化日誌
self.logger.info(f"處理請求了，來自使用者 {user_id}，用時 {duration} 毫秒")
```

## 性能優化

### 1. 使用快取

```python
class MyModule(BaseModule):
    def __init__(self):
        self._cache = {}
        self._cache_lock = asyncio.Lock()
    
    async def get_data(self, key):
        async with self._cache_lock:
            if key in self._cache:
                return self._cache[key]
            
            # 從資料庫獲取
            data = await self._fetch_from_db(key)
            
            # 快取資料
            self._cache[key] = data
            return data
```

### 2. 避免阻塞操作

```python
# 使用非同步操作
async def process_message(self, event: Event):
    # 非同步處理
    await self._async_process(event)

# ❌ 阻塞操作
async def process_message(self, event: Event):
    # 同步操作，阻塞事件循環
    result = self._sync_process(event)
```

## 安全性

### 1. 敏感數據保護

```python
# 敏感數據儲存在配置中（宣告式 ConfigClass，secret 欄位不會進入日誌/匯出）
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BaseModule, BaseConfig

@dataclass
class MyModuleConfig(BaseConfig):
    api_key: str = field(
        default="",
        metadata={"description": "API 密鑰", "secret": True},
    )

class MyModule(BaseModule):
    ConfigClass = MyModuleConfig

    def check_api_key(self):
        if not self.cfg.api_key or self.cfg.api_key == "YOUR_API_KEY_HERE":
            raise ValueError("請在 config.toml 中配置有效的 API 密鑰")

# ❌ 敏感數據硬編碼
class MyModule(BaseModule):
    API_KEY = "sk-1234567890"  # 不要這樣做！
```

### 2. 輸入驗證

```python
# 驗證使用者輸入
async def process_command(self, event: Event):
    user_input = event.get_text()
    
    # 驗證輸入長度
    if len(user_input) > 1000:
        await event.reply("輸入過長，請重新輸入")
        return
    
    # 驗證輸入格式
    if not re.match(r'^[a-zA-Z0-9]+$', user_input):
        await event.reply("輸入格式不正確")
        return
```

## 測試

### 1. 單元測試

```python
import pytest
from ErisPulse.Core.Bases import BaseModule

class TestMyModule:
    def test_config_defaults(self):
        """測試配置預設值"""
        config = MyModule.ConfigClass()
        assert config.timeout == 30
```

### 2. 集成測試

```python
@pytest.mark.asyncio
async def test_command_handling():
    """測試命令處理"""
    module = MyModule()
    await module.on_load({})
    
    # 模擬命令事件
    event = create_test_command_event("hello")
    await module.handle_command(event)
```

## 部署

### 1. 版本管理

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
```

遵循語義化版本：
- MAJOR.MINOR.PATCH
- 主版本：不相容的 API 變更
- 次版本：向下相容的功能新增
- 修訂號：向下相容的問題修正

### 2. README 頭部

`epsdk create` 產生的 README 已內建 ErisPulse 頭部標識（Logo + 標章行）。兩種推薦模式：

**模式 A — 僅 ErisPulse Logo（預設）：**

```markdown
<div align="center">

<img src="https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/.github/assets/ErisPulseLogo.png" width="180" alt="MyModule" />

# MyModule

**一句話描述**

<p>
  <a href="https://pypi.org/project/ErisPulse-MyModule/"><img src="https://img.shields.io/pypi/v/ErisPulse-MyModule?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI"></a>
  <a href="https://pypi.org/project/ErisPulse-MyModule/"><img src="https://img.shields.io/badge/Python-3.10+-FFD43B?style=for-the-badge&logo=python&logoColor=blue" alt="Python"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License"></a>
  <a href="https://github.com/ErisPulse/ErisPulse"><img src="https://img.shields.io/badge/Powered_by-ErisPulse-FF6B9D?style=for-the-badge&logo=bookstack&logoColor=white" alt="ErisPulse"></a>
</p>

</div>
```

**模式 B — 模塊圖標 × ErisPulse Logo（有自訂圖標時）：**

```markdown
<div align="center">

<img src=".github/assets/MyModuleIcon.svg" width="120" alt="MyModule" />
<span style="font-size:44px;color:#c8c8c8;margin:0 18px;vertical-align:middle;">×</span>
<img src="https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/.github/assets/ErisPulseLogo.png" height="120" alt="ErisPulse" />

# MyModule
（徽章行同上）
</div>
```

可依需求追加 GitHub Stars、Downloads 等徽章。Logo 也可下載到專案本地（`.github/assets/ErisPulseLogo.png`）改為相對路徑引用。

## 相關文件

- [模組開發入門](getting-started.md) - 建立第一個模組  
- [模組核心概念](core-concepts.md) - 理解模組架構  
- [Event 包裝類別](event-wrapper.md) - 事件處理詳解



=====
适配器开发
=====


适配器开发
-----


### 适配器开发入门

# 適配器開發入門

本指南協助您開始開發 ErisPulse 適配器，以連接新的消息平台。

## 适配器簡介

### 什麼是適配器

適配器是 ErisPulse 與各個訊息平台之間的橋樑，負責：

1. **正向轉換**：接收平台事件並轉換為 OneBot12 標準格式（Converter）
2. **反向轉換**：將 OneBot12 消息段轉換為平台 API 調用（`Raw_ob12`）
3. 管理與平台的連接（WebSocket/WebHook）
4. 提供統一的 SendDSL 消息發送介面

### 适配器架构

```mermaid
flowchart LR
    subgraph receive["正向轉換（接收）"]
        direction TB
        P1["平台事件"] --> C1["Converter.convert()"] --> O1["OneBot12 標準事件"] --> S1["事件系統"] --> M1["模組處理"]
    end
    subgraph send["反向轉換（發送）"]
        direction TB
        M2["模組建構訊息"] --> R1["Send.Raw_ob12()"] --> N1["平台原生 API 調用"] --> R2["標準回應格式"]
    end
```

## 目錄結構

標準的適配器包結構：

```
MyAdapter/
├── pyproject.toml          # 項目配置
├── README.md               # 項目說明
├── LICENSE                 # 授權條款
└── MyAdapter/
    ├── __init__.py          # 包入口
    ├── Core.py               # 適配器主類
    └── Converter.py          # 事件轉換器
```

## 快速開始

### 1. 建立項目

```bash
mkdir MyAdapter && cd MyAdapter
```

### 2. 建立 pyproject.toml

```toml
[project]
name = "ErisPulse-MyAdapter"
version = "1.0.0"
description = "MyAdapter平台適配器"
readme = "README.md"
requires-python = ">=3.10"
license = { file = "LICENSE" }
authors = [ { name = "yourname", email = "your@mail.com" } ]

dependencies = [
    "ErisPulse>=2.4.0"  # ErisPulse 已內建 aiohttp，通常無需單獨依賴
]

[project.urls]
"homepage" = "https://github.com/yourname/MyAdapter"

[project.entry-points."erispulse.adapter"]
"MyAdapter" = "MyAdapter:MyAdapter"
```

### 3. 建立適配器主類

框架提供了 `ConfigClass` / `AccountConfigClass` 聲明式配置管理，適配器只需宣告配置類即可自動載入、驗證和產生配置範本。

```python
# MyAdapter/Core.py
from dataclasses import dataclass, field
from ErisPulse.Core import BaseAdapter
from ErisPulse.Core.Bases import BaseConfig

@dataclass
class MyAdapterConfig(BaseConfig):
    """MyAdapter 配置"""
    api_endpoint: str = field(
        default="https://api.example.com",
        metadata={
            "description": {"i18n": "my_adapter.api_endpoint", "default": "API 位址"},
            "required": False,
            "ui": {"widget": "text", "group": "connection", "order": 1},
        },
    )
    token: str = field(
        default="",
        metadata={
            "description": {"i18n": "my_adapter.token", "default": "平台 Token"},
            "required": True,
            "secret": True,
            "ui": {"widget": "password", "group": "basic", "order": 2},
        },
    )

class MyAdapter(BaseAdapter):
    ConfigClass = MyAdapterConfig  # 宣告配置類，框架自動管理
    
    # 不需要覆寫 __init__！框架自動處理：
    # - self.sdk / self.logger 自動設定
    # - self.cfg 實時讀取配置
    # - self.Send / self.Request 自動初始化
    
    def _setup_converter(self):
        from .Converter import MyPlatformConverter
        return MyPlatformConverter()
```

> ⚠️ **關於 `__init__`**：新版本中 `BaseAdapter.__init__(self, sdk=None)` 會自動處理 SDK 引用、日誌初始化和配置載入。大多數適配器**不再需要覆寫 `__init__`**。詳見 [__init__ 注意事項](#init-注意事項)。

> ⚠️ **關於 `super().__init__()`**：`BaseAdapter.__init__()` 負責建立 `Send` 和 `Request` 工廠實例。如果忘記呼叫，所有訊息發送和請求操作都會報 `AttributeError`。詳見 [__init__ 注意事項](#init-注意事項)。

### 4. 實現必需方法

```python
class MyAdapter(BaseAdapter):
    # ... __init__ 代碼 ...
    
    async def start(self):
        """啟動適配器（必須實現）"""
        # 註冊 WebSocket 或 WebHook 路由
        router.register_websocket(
            module_name="myplatform",
            path="/ws",
            handler=self._ws_handler
        )
        self.logger.info("適配器已啟動")
    
    async def shutdown(self):
        """關閉適配器（必須實現）"""
        router.unregister_websocket(
            module_name="myplatform",
            path="/ws"
        )
        # 清理連接和資源
        self.logger.info("適配器已關閉")
    
    async def call_api(self, endpoint: str, **params):
        """呼叫平台 API（必須實現）"""
        raise NotImplementedError("需要實現 call_api")
```

#### 主動發送 Meta 事件

適配器應主動發送 meta 事件，讓框架追蹤 Bot 的線上狀態。使用 `emit_meta()` 一行即可完成：

```python
class MyAdapter(BaseAdapter):
    async def _ws_handler(self, websocket):
        bot_id = self._get_bot_id()

        # Bot 上線
        await self.emit_meta("connect", bot_id, user_name="MyBot")

        try:
            while True:
                data = await websocket.receive_text()
                event = self.convert(data)
                if event:
                    await self.adapter.emit(event)
        except WebSocketDisconnect:
            pass
        finally:
            # Bot 下線
            await self.emit_meta("disconnect", bot_id)
```

> 詳細的 Bot 狀態管理和 Meta 事件說明請參閱 [適配器最佳實踐 - Bot 狀態管理與-meta-事件](best-practices.md#bot-狀態管理與-meta-事件)。

### 5. 實現 Send 類

`At`/`AtAll`/`Reply` 修飾器已由框架 SendDSL 基類內建實現，適配器只需實現 `Raw_ob12` 和具體的發送方法即可。

框架提供兩個關鍵輔助方法：
- `self._apply_modifiers(message)` — 自動合併 At/AtAll/Reply 修飾器到訊息段
- `self.send_context` — 取得發送上下文字典（`target_type`、`target_id`、`account_id`）

```python
import asyncio

class MyAdapter(BaseAdapter):
    # ... 其他代碼 ...

    class Send(BaseAdapter.Send):

        def Raw_ob12(self, message, **kwargs):
            """
            發送 OneBot12 格式訊息（必須實現）

            使用 _apply_modifiers 自動合併修飾器狀態，
            使用 send_context 取得發送上下文。
            """
            async def _do_send():
                segments = self._apply_modifiers(message)
                return await self._adapter.call_api(
                    endpoint="/send_message",
                    message=segments,
                    **self.send_context,
                    **kwargs
                )
            return asyncio.create_task(_do_send())

        # Text/Image/Voice/Video/File 已從 SendDSL 基類繼承，
        # 預設委託給 Raw_ob12，無需重複實現。
        # 如需平台特定邏輯，可覆蓋單個方法：
        # def Text(self, text: str):
        #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

**媒體類發送方法（Image/Video/File）實現要點：**

- 基類的預設實作會將 `file` 參數封裝為 OneBot12 訊息段傳給 `Raw_ob12`，適配器需在 `Raw_ob12` 中處理下載/上傳
- `file` 參數應同時支援 `bytes` 二進位資料和 `str` URL 兩種類型
- 當傳入 URL 時，需先下載檔案再上傳到平台
- 平台通常需要先呼叫上傳接口取得檔案標識，再呼叫發送接口

**`__getattr__` 魔術方法：**

- 實現方法名大小寫不敏感（`Text`、`text`、`TEXT` 都能呼叫）
- 未定義的方法應回傳提示訊息而非報錯

**`Raw_ob12` 方法：**

- 將 OneBot12 標準訊息格式轉換為平台格式發送
- 使用 `self._apply_modifiers(message)` 自動處理 At/AtAll/Reply 修飾器
- 使用 `**self.send_context` 傳遞發送目標資訊和帳號資訊

### 6. 實現轉換器

```python
# MyAdapter/Converter.py
import time
import uuid

class MyPlatformConverter:
    def convert(self, raw_event):
        """將平台原生事件轉換為 OneBot12 標準格式"""
        if not isinstance(raw_event, dict):
            return None
        
        onebot_event = {
            "id": str(raw_event.get("event_id", uuid.uuid4())),
            "time": int(time.time()),
            "type": self._convert_event_type(raw_event.get("type")),
            "detail_type": self._convert_detail_type(raw_event),
            "platform": "myplatform",
            "self": {
                "platform": "myplatform",
                "user_id": str(raw_event.get("bot_id", ""))
            },
            "myplatform_raw": raw_event,
            "myplatform_raw_type": raw_event.get("type", "")
        }
        
        return onebot_event
    
    def _convert_event_type(self, event_type):
        """轉換事件類型"""
        type_map = {
            "message": "message",
            "notice": "notice"
        }
        return type_map.get(event_type, "unknown")
    
    def _convert_detail_type(self, raw_event):
        """轉換詳細類型"""
        return "private"  # 簡化示例
```

### 7. 實現 Request 類（請求操作）

如果你的平台支援好友請求、群邀請等需要 Bot 做出決策的請求，可以實現 `Request` 內部類：

```python
from ErisPulse.Core import BaseAdapter, RequestDSL

class MyAdapter(BaseAdapter):
    # ... Send 和其他代碼 ...

    class Request(RequestDSL):
        """請求操作實現（好友請求、群邀請等）"""

        def accept(self, **kwargs):
            """同意請求"""
            async def _do():
                result = await self._adapter.call_api(
                    endpoint="/set_request",
                    request_id=self._request_id,
                    approve=True,
                    **kwargs,
                )
                return {
                    "status": "ok" if result.get("code") == 0 else "failed",
                    "retcode": result.get("code", 0),
                    "data": None,
                    "message_id": "",
                    "message": result.get("message", ""),
                }
            return self._create_task(_do())

        def reject(self, **kwargs):
            """拒絕請求"""
            async def _do():
                result = await self._adapter.call_api(
                    endpoint="/set_request",
                    request_id=self._request_id,
                    approve=False,
                    **kwargs,
                )
                return {
                    "status": "ok" if result.get("code") == 0 else "failed",
                    "retcode": result.get("code", 0),
                    "data": None,
                    "message_id": "",
                    "message": result.get("message", ""),
                }
            return self._create_task(_do())
```

模組開發者使用方式：

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    # 透過 Event 便捷方法
    await event.approve()
    # 或透過適配器直接操作
    await adapter.myplatform.Request("req_id").accept()
```

> 如果平台不支援請求操作，可以不實現 `Request` 內部類。基類預設回傳 `retcode=10002`（不支援的操作）。詳見 [請求操作規範](../../standards/request-action-spec.md)。

### 8. 建立套件入口

```python
# MyAdapter/__init__.py
from .Core import MyAdapter
```

## 依賴聲明（可選，2.8.0+）

適配器可以聲明對其他適配器或模組的依賴，以實現適配器間的聯動與可選功能：

```python
from typing import ClassVar

class MyAdapter(BaseAdapter):
    # 硬依賴：缺失時跳過啟動（警告 + status=skipped-dependency 事件）
    depends: ClassVar[dict] = {
        "adapters": ["onebot11"],   # 依賴的適配器（按平台名）
        "modules": ["TranslateEngine"],  # 依賴的模組（按註冊名）
    }
    # 軟依賴：缺失不影響啟動；模組加載/卸載時收到回調（可選功能模式）
    optional_modules: ClassVar[list] = ["TranslateEngine"]
```

- **啟動順序**：聲明了模組硬依賴的適配器會**延遲到模組初始化完成後**再啟動
- **軟依賴通知**：`optional_modules`（或模組硬依賴）中的模組被加載時會調用 `on_dependency_ready(module_name)`；被卸載時會調用 `on_dependency_lost(module_name)`（預設為空實作，可覆寫）——覆蓋晚加載與熱重載場景：

```python
async def on_dependency_ready(self, module_name):
    """軟依賴模組就緒：啟用對應可選功能"""
    if module_name == "TranslateEngine":
        self._translate = self.sdk.TranslateEngine

async def on_dependency_lost(self, module_name):
    """軟依賴模組丟失：降級功能"""
    if module_name == "TranslateEngine":
        self._translate = None
```

> [!NOTE]
> 本特性需要 ErisPulse **2.8.0+**。

## `__init__` 注意事項

適配器開發中有三個層面可能涉及 `__init__` 重寫。以下是每個層面的正確做法。

### 1. BaseAdapter 層（大多數情況不需要重寫）

`BaseAdapter.__init__(self, sdk=None)` 負責建立 `Send` / `Request` 工廠實例，並自動完成以下工作：

- 接受 `sdk` 參數並設置 `self.sdk`、`self.logger`
- 如果宣告了 `ConfigClass`，可透過 `self.cfg` 即時讀取全域配置
- 如果宣告了 `AccountConfigClass`，可透過 `self.accounts` 即時讀取多帳號配置

**大多數情況下不需要覆寫 `__init__`**，只需宣告 `ConfigClass` 即可：

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyAdapterConfig  # 宣告後框架自動管理配置
    
    async def start(self):
        cfg = self.cfg  # 類型安全，即時讀取
        ...
```

如果確實需要自定義初始化，調用 `super().__init__(sdk)` 即可：

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyAdapterConfig
    
    def __init__(self, sdk=None):
        super().__init__(sdk)  # 傳入 sdk
        self.converter = self._setup_converter()
        self.convert = self.converter.convert
```

### 2. Send 內部類（大多數情況不需要重寫）

`SendDSL.__init__` 負責鏈式呼叫的狀態傳遞（目標類型、目標 ID、帳號等）。**大多數情況下，你只需要重寫方法**（`Raw_ob12`、`Text` 等），不需要重寫 `__init__`。

如果確實需要（比如初始化平台特有的狀態），**必須透傳所有參數**：

```python
class MyAdapter(BaseAdapter):
    class Send(BaseAdapter.Send):
        # 參數：adapter, target_type, target_id, account_id
        def __init__(self, adapter, target_type=None, target_id=None, account_id=None):
            super().__init__(adapter, target_type, target_id, account_id)  # ← 必須透傳
            self._my_state = None  # 平台特有初始化
```

**為什麼必須透傳？** 鏈式呼叫的每一步都透過 `self.__class__(...)` 創建新實例：

```python
adapter.Send.To("user", "123")               # → Send(adapter, "user", "123", None)
adapter.Send.To("user", "123").Using("bot1")  # → Send(adapter, "user", "123", "bot1")
```

如果 `__init__` 簽名不匹配或沒調 `super()`，鏈式呼叫就會中斷。

### 3. Request 內部類（大多數情況不需要重寫）

與 Send 同理。參數為 `adapter`, `request_id`, `account_id`：

```python
class MyAdapter(BaseAdapter):
    class Request(RequestDSL):
        # 參數：adapter, request_id, account_id
        def __init__(self, adapter, request_id=None, account_id=None):
            super().__init__(adapter, request_id, account_id)  # ← 必須透傳
            self._my_state = None  # 平台特有初始化
```

### 總結

| 層面 | 什麼時候重寫 | 必須做的事 |
|------|------------|-----------|
| **BaseAdapter** | 需要自定義初始化邏輯時 | `super().__init__(sdk)` （傳入 sdk 參數） |
| **Send 內部類** | 需要初始化發送相關狀態時 | `super().__init__(adapter, target_type, target_id, account_id)` |
| **Request 內部類** | 需要初始化請求相關狀態時 | `super().__init__(adapter, request_id, account_id)` |
| 三個層面 | 大多數情況 | **宣告 ConfigClass 即可，不碰 `__init__`** |

### 9. 連接資訊與路由發現

適配器註冊路由後，框架會記錄所有路由資訊。使用者可以透過以下 API 查看適配器的連接地址：

```python
from ErisPulse import sdk

# 獲取適配器完整連接資訊
info = sdk.adapter.get_connection_info("myplatform")
# {
#   "platform": "myplatform",
#   "status": "started",
#   "connection": {
#     "base_url": "http://localhost:8080",
#     "http_routes": [
#       {"path": "/myplatform/webhook", "method": "POST",
#        "url": "http://localhost:8080/myplatform/webhook"}
#     ],
#     "websocket_routes": [
#       {"path": "/myplatform/ws",
#        "url": "ws://localhost:8080/myplatform/ws"}
#     ]
#   }
# }

# 列出所有命名空間（適配器/模組）的路由
namespaces = sdk.router.list_namespaces()
# {"myplatform": {"http": ["/myplatform/webhook"], "websocket": ["/myplatform/ws"]}}

# 獲取命名空間的完整連接 URL
urls = sdk.router.get_module_urls("myplatform")
# {"base_url": "http://localhost:8080", "http": [...], "websocket": [...]}

# 獲取命名空間的詳細路由資訊
routes = sdk.router.get_module_routes("myplatform")
# {"http": [{"path": "/myplatform/webhook", "methods": ["POST"]}],
#  "websocket": [{"path": "/myplatform/ws", "auth": false}]}
```

> **提示**：`get_connection_info()` 返回的資訊適合展示給使用者（如 WebUI），幫助使用者設定平台側的回調地址或 WebSocket 連接地址。路由註冊時的 `module_name` 必須與適配器在 ErisPulse 中註冊的 `platform` 名稱完全一致，否則路由發現將無法正確關聯。

### 10. SSE (Server-Sent Events) 支援

ErisPulse 內建了伺服器無關的 SSE 支援，模組和適配器可以透過 `@sdk.router.sse()` 註冊 SSE 端點。

#### 基本使用

```python
import asyncio
from ErisPulse import sdk

@sdk.router.sse("MyModule", "/events")
async def event_stream(sse):
    """推送 SSE 事件"""
    count = 0
    while not sse.closed:
        await sse.send({"count": count}, event="update")
        count += 1
        await asyncio.sleep(1)
```

#### 使用請求參數

處理器可以宣告 `request` 參數來存取客戶端請求資訊：

```python
@sdk.router.sse("MyModule", "/events")
async def event_stream(request, sse):
    token = request.query_params.get("token")
    if not validate_token(token):
        await sse.close()
        return

    while not sse.closed:
        data = await fetch_data(token)
        await sse.send(data)
        await asyncio.sleep(5)
```

#### SseEmitter API

| 方法 | 說明 |
|------|------|
| `sse.send(data, event=None, id=None, retry=None)` | 發送 SSE 事件。非 str 的 data 自動 JSON 序列化 |
| `sse.close()` | 優雅關閉 SSE 連接（安全呼叫，可多次） |
| `sse.closed` | 連接是否已關閉 |
| `sse.request` | 底層請求物件（可用於讀取 query params、headers） |

#### 在 RouteGroup 中使用

```python
api = sdk.router.group("MyModule", "/api", version="1")

@api.sse("/events")
async def events(sse):
    await sse.send({"msg": "hello"})
```

#### 路由發現

SSE 路由會自動出現在路由發現 API 中：

```python
# list_namespaces 會包含 "sse" 鍵
sdk.router.list_namespaces()
# {"MyModule": {"http": [...], "websocket": [...], "sse": ["/MyModule/events"]}}

# get_module_routes 會標記 streaming: true
sdk.router.get_module_routes("MyModule")
# {"http": [...], "websocket": [...], "sse": [{"path": "/MyModule/events", "streaming": true}]}

# get_module_urls 會產生完整 URL
sdk.router.get_module_urls("MyModule")
# {"sse": [{"path": "/MyModule/events", "url": "http://localhost:8080/MyModule/events"}]}
```

> **伺服器無關設計**：`SseEmitter` 透過回調與底層 HTTP 框架解耦。框架提供了 `register_sse()` 和 `@sse` 裝飾器作為統一的註冊入口，適配器無需直接依賴任何底層 HTTP 框架即可實現 SSE 端點。



### 适配器核心概念

# 適配器核心概念

了解 ErisPulse 適配器的核心概念是開發適配器的基礎。

## 適配器架構

### 組件關係

```
正向轉換（接收方向）                           反向轉換（發送方向）
─────────────────                           ─────────────────
                                             
┌──────────────────┐                        ┌──────────────────┐
│ 平台原生事件     │                        │ 模組建構訊息     │
└────────┬─────────┘                        └────────┬─────────┘
         │                                           │
         ↓                                           ↓
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│                  │   │ 適配器 (MyAdapter) │   │                  │
│  Converter       │   │ ┌──────────────┐ │   │ Send.Raw_ob12()  │
│  (事件轉換器)    │──→│ │              │ │   │ (反向轉換入口)   │
│                  │   │ │              │ │   │                  │
└──────────────────┘   │ └──────────────┘ │   └────────┬─────────┘
                       └──────────────────┘            │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ 平台 API 調用    │
                       │ OneBot12 標準事件 │    └────────┬─────────┘
                       └────────┬─────────┘             │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ 標準回應格式     │
                       │ 事件系統         │    └──────────────────┘
                       └────────┬─────────┘
                                │
                                ↓
                       ┌──────────────────┐
                       │ 模組 (處理事件)  │
                       └──────────────────┘
```

**核心對稱性**：
- **正向轉換**（Converter）：平台原生事件 → OneBot12 標準事件，原始資料保留在 `{platform}_raw`
- **反向轉換**（Raw_ob12）：OneBot12 消息段 → 平台 API 調用，回傳標準回應格式

## AdapterManager 适配器管理器

`AdapterManager` 是 ErisPulse 适配器系統的核心組件，負責管理所有平台適配器的註冊、啟動、關閉和事件分發。

### 核心功能

- **適配器註冊**：註冊和管理多個平台適配器
- **生命週期管理**：控制適配器的啟動和關閉
- **事件分發**：分發 OneBot12 標準事件和平台原生事件
- **配置管理**：管理適配器的啟用/禁用狀態
- **中間件支援**：支援 OneBot12 事件中間件

### 基本使用

```python
from ErisPulse import sdk

# 註冊適配器（通常由 Loader 自動完成）
sdk.adapter.register("myplatform", MyPlatformAdapter)

# 啟動所有適配器
await sdk.adapter.startup()

# 啟動指定適配器
await sdk.adapter.startup(["myplatform"])
# 啟動全部適配器
await sdk.adapter.startup()

# 獲取適配器實例
my_adapter = sdk.adapter.get("myplatform")
# 或透過屬性存取
my_adapter = sdk.adapter.myplatform

# 關閉所有適配器
await sdk.adapter.shutdown()
```

### 啟動和關閉

#### 啟動適配器

```python
# 啟動所有已註冊的適配器
await sdk.adapter.startup()

# 啟動指定平台
await sdk.adapter.startup(["platform1", "platform2"])
```

**啟動流程：**

1. 提交 `adapter.start` 生命週期事件
2. 提交 `adapter.status.change` 事件（starting）
3. 並行啟動各個適配器
4. 如果啟動失敗，自動重試（指數退避策略）
5. 啟動成功後提交 `adapter.status.change` 事件（started）

**重試機制：**

- 前 4 次重試：60秒、10分鐘、30分鐘、60分鐘
- 第 5 次及以後：3 小時固定間隔

#### 關閉適配器

```python
# 關閉所有適配器
await sdk.adapter.shutdown()
```

**關閉流程：**

1. 提交 `adapter.stop` 生命週期事件
2. 呼叫所有適配器的 `shutdown()` 方法
3. 關閉路由伺服器
4. 清空事件處理器
5. 提交 `adapter.stopped` 生命週期事件

### 配置管理

#### 檢查平台狀態

```python
# 檢查平台是否已註冊
exists = sdk.adapter.exists("myplatform")

# 檢查平台是否啟用
enabled = sdk.adapter.is_enabled("myplatform")

# 使用 in 操作符
if "myplatform" in sdk.adapter:
    print("平台存在且已啟用")
```

#### 列出平台

```python
# 列出所有已註冊的平台
platforms = sdk.adapter.list_registered()

# 列出所有平台及其狀態
status_dict = sdk.adapter.list_items()
# 返回: {"platform1": true, "platform2": false, ...}

# 獲取已啟用的平台列表
enabled_platforms = [p for p, enabled in status_dict.items() if enabled]
```

### 事件監聽

#### OneBot12 標準事件

```python
from ErisPulse import sdk

# 監聽所有平台的標準消息事件
@sdk.adapter.on("message")
async def handle_message(data):
    print(f"收到OneBot12消息: {data})

# 監聽特定平台的標準消息事件
@sdk.adapter.on("message", platform="myplatform")
async def handle_platform_message(data):
    print(f"收到 myplatform 消息: {data})

# 監聽所有事件
@sdk.adapter.on("*")
async def handle_any_event(data):
    print(f"收到事件: {data.get('type')})
```

#### 平台原生事件

```python
# 監聽特定平台的原生事件
@sdk.adapter.on("raw_event_type", raw=True, platform="myplatform")
async def handle_raw_event(data):
    print(f"收到原生事件: {data})

# 監聽所有平台的原生事件（通配符）
@sdk.adapter.on("*", raw=True)
async def handle_all_raw_events(data):
    print(f"收到原生事件: {data})
```

#### 事件分發機制

當呼叫 `adapter.emit(event_data)` 時：

1. **中間件處理**：先執行所有 OneBot12 中間件
2. **標準事件分發**：分發到匹配的 OneBot12 事件處理器
3. **原生事件分發**：如果存在原始資料，分發到原生事件處理器

**匹配規則：**

- 精確匹配：`@sdk.adapter.on("message")` 只匹配 `message` 事件
- 通配符：`@sdk.adapter.on("*")` 匹配所有事件
- 平台過濾：`platform="myplatform"` 只分發指定平台的事件

### 中間件

#### 添加中間件

```python
@sdk.adapter.middleware
async def logging_middleware(data):
    """日誌記錄中間件"""
    print(f"處理事件: {data.get('type')}")
    return data  # 必須返回資料

@sdk.adapter.middleware
async def filter_middleware(data):
    """事件過濾中間件"""
    # 過濾不需要的事件
    if data.get("type") == "notice":
        return None  # 返回 None 時中間件鏈會忽略該返回值，保留原資料繼續傳遞
    return data  # 必須返回資料以繼續傳遞
```

#### 中間件執行順序

中間件按照註冊順序執行，後註冊的中間件先執行。

> **注意**：如果中間件返回 `None`（例如忘記 `return data`），框架會忽略該返回值並保留原資料繼續傳遞，同時輸出 warning 級別日誌。這確保了單個中間件的失誤不會導致整個事件鏈中斷。

```python
# 註冊順序
sdk.adapter.middleware(middleware1)  # 最後執行
sdk.adapter.middleware(middleware2)  # 中間執行
sdk.adapter.middleware(middleware3)  # 最先執行

# 執行順序：middleware3 -> middleware2 -> middleware1
```

### 獲取適配器實例

#### get() 方法

```python
adapter = sdk.adapter.get("myplatform")
if adapter:
    await adapter.Send.To("user", "123").Text("Hello")
```

#### 屬性存取

```python
# 透過屬性名存取（不區分大小寫）
adapter = sdk.adapter.myplatform
await adapter.Send.To("user", "123").Text("Hello")
```

## BaseAdapter 基類

### 基本結構

```python
from dataclasses import dataclass, field
from ErisPulse.Core import BaseAdapter
from ErisPulse.Core.Bases import BaseConfig, BotAccountConfig

@dataclass
class MyConfig(BaseConfig):
    """適配器配置（聲明後框架自動管理）"""
    token: str = field(
        default="",
        metadata={
            "description": {"i18n": "my_adapter.token", "default": "Bot Token"},
            "required": True,
            "secret": True,
            "ui": {"widget": "password", "group": "basic", "order": 1},
        },
    )

class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig  # 聲明配置類
    
    # 無需覆寫 __init__，框架自動處理：
    # - self.sdk, self.logger
    # - self.cfg（類型安全的配置實例，即時讀取）
    # - self.Send, self.Request
    
    async def start(self):
        """啟動適配器（必須實現）"""
        cfg = self.cfg  # 自動加載的類型安全配置
        pass
    
    async def shutdown(self):
        """關閉適配器（必須實現）"""
        pass
    
    async def call_api(self, endpoint: str, **params):
        """調用平台 API（必須實現）"""
        pass
```

### 配置管理

框架提供了宣告式配置管理，透過 dataclass 定義配置結構，框架自動處理加載、驗證和範本生成。

#### 單帳號配置

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BaseConfig

@dataclass
class TelegramConfig(BaseConfig):
    token: str = field(default="", metadata={
        "description": {"i18n": "telegram.token", "default": "Bot Token"},
        "required": True,
        "secret": True,
        "ui": {"widget": "password", "group": "basic", "order": 1},
    })
    proxy: str = field(default="", metadata={
        "description": {"i18n": "telegram.proxy", "default": "代理地址"},
        "ui": {"widget": "text", "group": "advanced", "order": 10},
    })

class TelegramAdapter(BaseAdapter):
    ConfigClass = TelegramConfig
    
    async def start(self):
        cfg = self.cfg  # 類型安全，即時讀取
        if not cfg.token:
            raise ValueError("未配置 Token")
        await self._connect(cfg.token, proxy=cfg.proxy)
```

#### 多帳號配置

`BotAccountConfig` 基類提供 `enabled` 和 `name` 欄位。絕大多數適配器能從平台協議或登入回應中自動獲取 bot_id，在事件轉換時注入到帳號配置中。：

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BotAccountConfig

# 大多數適配器：bot_id 運行時自動獲取，無需配置
@dataclass
class MyBotConfig(BotAccountConfig):
    token: str = field(default="", metadata={
        "description": {"i18n": "my_adapter.bot_token", "default": "Token"},
        "required": True,
    })

# 如果登入時無法獲取 bot_id，可讓使用者在配置中填寫
@dataclass
class YunhuBotConfig(BotAccountConfig):
    bot_id: str = field(default="", metadata={
        "description": {"i18n": "yunhu.bot_id", "default": "機器人ID"},
        "required": True,
    })
    token: str = field(default="", metadata={
        "description": {"i18n": "yunhu.token", "default": "Token"},
        "required": True,
    })

class MyAdapter(BaseAdapter):
    AccountConfigClass = MyBotConfig
    
    async def start(self):
        for name, account in self.enabled_accounts.items():
            user_id = await self._login(name, account)
            await self.emit_meta("connect", user_id)
```

#### metadata 約定

欄位 metadata 同時服務於 TOML 註釋生成和 WebUI 表單渲染：

```python
metadata = {
    "description": str | dict,  # 欄位描述（支援 i18n）
    "required": bool,         # 是否必填（驗證 + WebUI 必填標記）
    "secret": bool,           # 是否敏感（WebUI 顯示為 ***，日誌中脫敏）
    "ui": {                   # WebUI 控件配置（舊名 "webui" 仍相容）
        "widget": str,        # 控件類型: "text" | "switch" | "select" | "number" | "password"
        "group": str,         # 分組: "basic" | "advanced" | "connection" 等
        "order": int,         # 排序權重（越小越靠前）
        "options": list,      # select 控件的可選項 [{label, value}]，label 支援 i18n
        "placeholder": str | dict,  # 輸入框佔位符（支援 i18n）
    },
    "extra": dict,            # 額外擴展欄位（透傳到 schema）
}
```

所有使用者可見的文本欄位均支援 i18n，統一採用 `{"i18n": "key", "default": "文本"}` 格式，
純字串則原樣透傳（向後相容）。支援的 i18n 欄位：

| 欄位 | 位置 | 說明 |
|------|------|------|
| `description` | field metadata | 欄位描述 |
| `options[].label` | `ui.options` | select 控件選項標籤 |
| `placeholder` | `ui.placeholder` | 輸入框佔位符 |
| `group_labels` | `_schema_meta` | 分組顯示名（Dashboard 分區標題） |

使用 i18n 時，需提前將翻譯鍵註冊到 i18n 系統（詳見 [i18n 文檔](../../advanced/i18n.md#配置欄位多語言)）。

**description / placeholder / options label** 範例：

```python
token: str = field(
    default="",
    metadata={
        "description": {"i18n": "my_adapter.token", "default": "Bot Token"},
        "ui": {
            "widget": "text",
            "placeholder": {"i18n": "my_adapter.token.ph", "default": "請輸入 Token"},
        },
    },
)
mode: str = field(
    default="a",
    metadata={
        "description": {"i18n": "my_adapter.mode", "default": "模式"},
        "ui": {
            "widget": "select",
            "options": [
                {"label": {"i18n": "my_adapter.mode.a", "default": "選項A"}, "value": "a"},
                {"label": "純字串標籤", "value": "b"},  # 純字串原樣透傳
            ],
        },
    },
)
```

**group_labels** 範例（在配置類定義後宣告）：

```python
MyConfig._schema_meta = {
    "group_labels": {
        "basic": {"i18n": "my_adapter.group.basic", "default": "基本設定"},
        "advanced": {"i18n": "my_adapter.group.advanced", "default": "高級設定"},
    }
}
```

框架的 `resolve_config_schema()` 會根據當前語言自動解析上述所有欄位的 i18n 鍵；
`get_config_schema()` 則原樣透傳 i18n 字典，由前端自行解析。

### 宣告式翻譯鍵（v2.7.0+）

適配器可以像宣告 `ConfigClass` 一樣，透過巢狀類 `I18nClass` 集中宣告翻譯鍵。
框架會在 `__init__` 階段（配置範本生成之前）自動註冊所有宣告的翻譯鍵，
確保配置描述中引用的 i18n 鍵在生成範本時已可用。

```python
from ErisPulse.Core.Bases import BaseAdapter, BaseI18n, I18nKey

class MyAdapter(BaseAdapter):
    class I18nClass(BaseI18n):
        endpoint: I18nKey = I18nKey(
            default="API Endpoint",
            zh_CN="API 地址",
            zh_TW="API 位址",
            en="API Endpoint",
            ja="APIアドレス",
            ru="API адрес",
        )
        token: I18nKey = I18nKey(
            default="Platform Token",
            zh_CN="平台 Token",
            zh_TW="平台權杖",
            en="Platform Token",
            ja="プラットフォームトークン",
            ru="Токен платформы",
        )
```

> ``I18nKey.default`` 是**語言無關的兜底文本**，不會註冊到任何語言。
> 要讓翻譯生效，必須顯式傳入至少一個語言參數。

詳細用法（鍵路徑規則、顯式 key 參數等）見 [i18n 文檔](../../advanced/i18n.md#推薦寫法通過-i18nclass-宣告翻譯鍵-v270)。

### 宣告式事件擴展方法（v2.7.0+）

適配器可以透過 `EventMixin` 集中宣告平台特有的事件擴展方法，框架自動註冊到當前平台。

```python
from ErisPulse.Core import BaseAdapter

class MyAdapter(BaseAdapter):
    class EventMixin:
        def get_chat_name(self):
            """獲取聊天名稱"""
            return self.get("myplatform_raw", {}).get("chat", {}).get("name", "")

        def is_official_message(self):
            """判斷是否為官方消息"""
            raw = self.get("myplatform_raw", {})
            return raw.get("sender", {}).get("is_official", False)
```

註冊後，事件物件直接調用這些方法：

```python
@message.on_group_message()
async def handler(event):
    if event.is_official_message():
        chat_name = event.get_chat_name()
        await event.reply(f"[{chat_name}] 官方消息已收到")
```

> 適配器的事件擴展方法註冊到自身平台（``self._platform``）。
> 模組如需跨平台事件擴展，請使用原有的 ``register_event_mixin()`` API。

#### 帳戶解析

多帳號適配器可使用 `_resolve_account()` 自動解析目標帳戶：

```python
async def call_api(self, endpoint: str, **params):
    account_id = params.pop("account_id", None)
    name, account = self._resolve_account(account_id)
    # name: 帳戶名, account: 配置實例
```

解析策略：帳戶名匹配 → `bot_id` 欄位匹配 → 其他 str 欄位匹配 → 第一個啟用帳戶。

#### 配置熱更新

子類可覆寫 `on_config_update()` 回應配置變更：

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig
    
    def on_config_update(self, old_config, new_config):
        if old_config.token != new_config.token:
            self.logger.info("Token 已更新，將重新連接")
```

### 初始化過程

框架在 `BaseAdapter.__init__(self, sdk=None)` 中自動完成以下工作：

1. **SDK 引用**：設定 `self.sdk`、`self.logger`
2. **Send/Request 工廠**：建立 `self.Send` 和 `self.Request`
3. **配置範本**：如果宣告了 `ConfigClass`，自動產生預設配置範本（首次）
4. **帳戶範本**：如果宣告了 `AccountConfigClass`，自動產生預設帳戶範本（首次）
5. **EventMixin 註冊**：如果宣告了 `EventMixin`，在 `AdapterManager` 注入平台名後自動註冊

配置透過 `self.cfg` / `self.accounts` 即時讀取（每次存取都從配置儲存讀取最新值）。`self.config` 作為 `self.cfg` 的相容別名仍可使用。

大多數適配器無需覆寫 `__init__`。如需自訂初始化：

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig
    
    def __init__(self, sdk=None):
        super().__init__(sdk)  # 傳入 sdk
        self.converter = self._setup_converter()
        self.convert = self.converter.convert
```

## Send 消息發送 DSL

### 繼承關係

```python
class MyAdapter(BaseAdapter):
    class Send(BaseAdapter.Send):
        """Send 嵌套類，繼承自 BaseAdapter.Send"""
        pass
```

### 可用屬性

`Send` 類在呼叫時會自動設置以下屬性：

| 屬性 | 說明 | 設置方式 |
|-----|------|---------|
| `_target_id` | 目標 ID | `To(id)` 或 `To(type, id)` |
| `_target_type` | 目標類型 | `To(type, id)` |
| `_target_to` | 簡化目標 ID | `To(id)` |
| `_account_id` | 發送帳號 ID | `Using(account_id)` |
| `_adapter` | 適配器實例 | 自動設置 |
| `_at_user_ids` | @用戶列表 | `At(user_id)` |
| `_reply_message_id` | 回覆的消息 ID | `Reply(message_id)` |
| `_at_all` | 是否 @全體 | `AtAll()` |

> **推薦**：使用 `self.send_context` 屬性一次性獲取 `target_type`、`target_id`、`account_id`，比直接訪問實例變量更清晰。

### 框架輔助方法

| 方法/屬性 | 說明 |
|-----------|------|
| `self._apply_modifiers(message)` | 將 At/AtAll/Reply 修飾器狀態合併到消息段列表 |
| `self.send_context` | 返回 `{target_type, target_id, account_id}` 字典 |

### 基本方法

適配器只需實現 `Raw_ob12`，標準方法（Text/Image/Voice/Video/File）已從 `SendDSL` 基類繼承並預設委託給它：

```python
class Send(BaseAdapter.Send):
    def Raw_ob12(self, message, **kwargs):
        """必須實現：OneBot12 消息段 → 平台 API"""
        async def _do_send():
            segments = self._apply_modifiers(message)
            return await self._adapter.call_api(
                endpoint="/send_message",
                message=segments,
                **self.send_context,
                **kwargs
            )
        return asyncio.create_task(_do_send())

    # Text/Image/Voice/Video/File 已從基類繼承，自動委託 Raw_ob12，無需重複實現
    # 如需平台特定邏輯，可覆蓋單個方法：
    # def Text(self, text: str):
    #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

### 鏈式修飾方法

```python
class Send(BaseAdapter.Send):

    def __init__(self, adapter, target_type=None, target_id=None, account_id=None):
        super().__init__(adapter, target_type, target_id, account_id)
        self.buttons = []

    def Button(self, content: list) -> 'Send':
        self.buttons.append(content)
        return self
```

## 事件轉換器

### 轉換流程

```
平台原始事件
    ↓
Converter.convert()
    ↓
OneBot12 標準事件
```

### 必需字段

所有轉換後的事件必須包含：

```python
{
    "id": "事件唯一標識",
    "time": 1234567890,           # 10位 Unix 時間戳
    "type": "message/notice/request/meta",
    "detail_type": "事件詳細類型",
    "platform": "平台名稱",
    "self": {
        "platform": "平台名稱",
        "user_id": "機器人ID"     # 必須與 bot_id 一致
    },
    "{platform}_raw": {...},       # 原始數據（必須）
    "{platform}_raw_type": "..."    # 原始類型（必須）
}
```

### 轉換器示例

```python
class MyPlatformConverter:
    def convert(self, raw_event):
        """將平台原生事件轉換為 OneBot12 標準格式"""
        if not isinstance(raw_event, dict):
            return None
        
        # 生成事件 ID
        event_id = raw_event.get("event_id") or str(uuid.uuid4())
        
        # 轉換時間戳
        timestamp = raw_event.get("timestamp")
        if timestamp and timestamp > 10**12:
            timestamp = int(timestamp / 1000)
        else:
            timestamp = int(timestamp) if timestamp else int(time.time())
        
        # 轉換事件類型
        event_type = self._convert_type(raw_event.get("type"))
        detail_type = self._convert_detail_type(raw_event)
        
        # 建構標準事件
        onebot_event = {
            "id": str(event_id),
            "time": timestamp,
            "type": event_type,
            "detail_type": detail_type,
            "platform": "myplatform",
            "self": {
                "platform": "myplatform",
                "user_id": str(raw_event.get("bot_id", ""))
            },
            "myplatform_raw": raw_event,
            "myplatform_raw_type": raw_event.get("type", "")
        }
        
        return onebot_event
```

## 連接管理

### WebSocket 連接

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        """註冊 WebSocket 路由"""
        router.register_websocket(
            module_name="myplatform",
            path="/ws",
            handler=self._ws_handler,
            auth_handler=self._auth_handler
        )
    
    async def _ws_handler(self, websocket):
        """WebSocket 連接處理器"""
        self.connection = websocket
        
        try:
            while True:
                data = await websocket.receive_text()
                onebot_event = self.convert(data)
                if onebot_event:
                    await self.adapter.emit(onebot_event)
        except WebSocketDisconnect:
            self.logger.info("連接已斷開")
        finally:
            self.connection = None
    
    async def _auth_handler(self, websocket) -> bool:
        """WebSocket 認證"""
        token = websocket.query_params.get("token")
        return token == "valid_token"
```

### WebHook 連接

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        """註冊 WebHook 路由"""
        router.register_http_route(
            module_name="myplatform",
            path="/webhook",
            handler=self._webhook_handler,
            methods=["POST"]
        )
    
    async def _webhook_handler(self, request):
        """WebHook 請求處理器"""
        data = await request.json()
        onebot_event = self.convert(data)
        if onebot_event:
            await self.adapter.emit(onebot_event)
        return {"status": "ok"}
```

> **路由資訊查詢**：適配器註冊的路由（HTTP、WebSocket、SSE）可以透過 `sdk.adapter.get_connection_info(platform)` 和 `sdk.router.get_module_urls(module_name)` 查詢完整連接位址（包含 `base_url` + 路徑）。詳見 [適配器開發入門 - 連接資訊與路由發現](docs/zh-TW/getting-started.md#9-連接資訊與路由發現) 和 [SSE 支援](docs/zh-TW/getting-started.md#10-sse-server-sent-events-支援)。

## API 响應標準

框架提供 `make_response()` 和 `make_error()` 方法來構造標準化響應，無需手動構建響應字典。

### 成功響應

```python
async def call_api(self, endpoint: str, **params):
    try:
        raw_response = await self._platform_api_call(endpoint, **params)
        
        return self.make_response(
            data=raw_response.get("data"),
            message_id=raw_response.get("data", {}).get("message_id", ""),
            raw=raw_response,
        )
    except Exception as e:
        return self.make_error(message=str(e), raw=None)
```

### 手動構造響應（舊版方式仍然相容）

```python
async def call_api(self, endpoint: str, **params):
    return {
        "status": "ok",
        "retcode": 0,
        "data": {...},
        "message_id": "msg_id",
        "message": "",
        "myplatform_raw": raw_response
    }
```

## 多賬戶支援

### 聲明式配置（推薦）

使用 `AccountConfigClass` 聲明配置類後，框架自動管理多賬戶加載、驗證和模板生成：

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BotAccountConfig

@dataclass
class MyBotConfig(BotAccountConfig):
    bot_id: str = field(default="", metadata={"description": "Bot ID", "required": True})
    token: str = field(default="", metadata={"description": "Token", "required": True, "secret": True})

class MyAdapter(BaseAdapter):
    AccountConfigClass = MyBotConfig
    
    async def start(self):
        for name, account in self.enabled_accounts.items():
            self.logger.info(f"啟動賬戶 {name}: {account.bot_id}")
            await self._connect(name, account)
    
    async def call_api(self, endpoint: str, **params):
        account_id = params.pop("account_id", None)
        name, account = self._resolve_account(account_id)
        # 使用 account.token, account.bot_id 等字段
```

### 賬戶配置檔案

```toml
[MyAdapter.accounts.account1]
bot_id = "bot_001"
token = "token1"
enabled = true

[MyAdapter.accounts.account2]
bot_id = "bot_002"
token = "token2"
enabled = true
```

### 指定賬戶發送

```python
# 使用 Using 方法指定賬戶
my_adapter = adapter.get("myplatform")

# 透過事件中的 self.user_id（推薦，最通用）
await my_adapter.Send.Using(event["self"]["user_id"]).To("user", "123").Text("Hello")

# 透過賬戶名
await my_adapter.Send.Using("account1").To("user", "123").Text("Hello")
```

### self.user_id 與 Using 的關係

框架的事件回覆機制會自動從事件的 `self` 字段中提取 `account_id`（優先）或 `user_id`，作為 `Using` 參數傳入。適配器開發者需要確保 Converter 中 `self.user_id` 的值與 `_resolve_account()` 能夠正確匹配。

**框架內部行為**：

```python
# 框架提取 bot_id 的邏輯
bot_id = self.get("self", {}).get("account_id", "") or self.get("self", {}).get("user_id", "")

# 僅在 bot_id 非空時調用 Using
if bot_id:
    send_chain = send_chain.Using(bot_id)
```

> **關鍵點**：即使適配器只使用一個 Bot 配置，只要 Converter 正確設置了 `self.user_id`，框架就會將其作為 `Using` 參數傳入。適配器需確保 `self.user_id` 與 `AccountConfigClass` 中的標識字段（如 `bot_id`）一致，使 `_resolve_account()` 能匹配到正確賬戶。如果 `self.user_id` 為空，框架不會調用 `Using`，此時 `call_api` 收到的 `account_id` 為 `None`，`_resolve_account(None)` 返回第一個啟用的賬戶。

## 錯誤處理

### 連接重試

```python
import asyncio

class MyAdapter(BaseAdapter):
    async def start(self):
        retry_count = 0
        max_retries = 5
        
        while retry_count < max_retries:
            try:
                await self._connect_to_platform()
                break
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = min(60 * (2 ** retry_count), 600)
                    self.logger.warning(f"連接失敗，{wait_time}秒後重試")
                    await asyncio.sleep(wait_time)
                else:
                    raise
```

### API 錯誤處理

```python
async def call_api(self, endpoint: str, **params):
    try:
        # 推薦使用 SDK 內建客戶端
        from ErisPulse.Core import client
        from ErisPulse.Core.Bases.errors import ClientError, ClientTimeoutError
        resp = await client.post(
            f"https://api.platform.com/{endpoint}",
            json=params,
            max_retries=2,
        )
        response = await resp.json()
        return self._standardize_response(response)
    except ClientTimeoutError:
        self.logger.error(f"請求超時: {endpoint}")
        return self._error_response("請求超時", 32000)
    except ClientError as e:
        self.logger.error(f"網路錯誤: {e}")
        return self._error_response("網路請求失敗", 33000)
    except Exception as e:
        self.logger.error(f"未知錯誤: {e}")
        return self._error_response(str(e), 34000)
```

> **向後相容**：直接使用 `aiohttp.ClientSession` 的舊適配器程式碼不受影響，仍然可以捕獲 `aiohttp.ClientError`。兩種方式可以共存。建議新程式碼使用 `sdk.client` + ErisPulse 錯誤體系。

## Bot 狀態管理

AdapterManager 內建了 Bot 狀態追蹤系統，自動維護所有已註冊 Bot 的線上狀態、活躍時間和元資訊。

### 自動發現機制

當適配器透過 `adapter.emit()` 發送事件時，框架會自動檢查事件中的 `self` 欄位：

- **meta 事件**：根據 `detail_type` 執行對應操作（connect 註冊/斷開標記離線/heartbeat 更新活躍時間）
- **普通事件**（message/notice/request）：自動發現 Bot 並更新活躍時間

```python
# 所有包含 self 欄位的事件都會觸發自動發現
await self.adapter.emit({
    "type": "message",
    "platform": "myplatform",
    "self": {"platform": "myplatform", "user_id": "bot123"},
    # ...
})
# Bot "bot123" 已自動註冊（如果首次出現）並更新活躍時間
```

### Meta 事件類型

| `detail_type` | 說明 | 框架行為 |
|---|---|---|
| `connect` | Bot 連接 | 註冊 Bot 並觸發 `adapter.bot.online` 生命週期事件 |
| `disconnect` | Bot 斷開 | 標記 Bot 離線並觸發 `adapter.bot.offline` 生命週期事件 |
| `heartbeat` | Bot 心跳 | 更新 Bot 活躍時間和元資訊 |

### 适配器發送 Meta 事件

使用 `emit_meta()` 一行即可發送 meta 事件：

```python
class MyAdapter(BaseAdapter):
    async def _on_bot_connect(self, bot_id: str):
        # 一行發送 connect 事件
        await self.emit_meta("connect", bot_id, user_name="MyBot", nickname="我的機器人")

    async def _on_bot_disconnect(self, bot_id: str):
        await self.emit_meta("disconnect", bot_id)
```

也支援手動構造（舊版方式仍然相容）：

```python
await self.adapter.emit({
    "type": "meta",
    "detail_type": "connect",
    "platform": "myplatform",
    "self": {"platform": "myplatform", "user_id": bot_id}
})
```

### `self` 欄位擴展資訊

`self` 欄位除必需的 `platform` 和 `user_id` 外，還支援以下可選欄位：

| 欄位 | 說明 |
|---|---|
| `user_name` | Bot 用戶名 |
| `nickname` | Bot 昵稱 |
| `avatar` | Bot 頭像 URL |
| `account_id` | 多帳戶標識 |

### Bot 狀態查詢

```python
from ErisPulse import sdk

# 獲取單個 Bot 資訊
info = sdk.adapter.get_bot_info("myplatform", "bot123")
# {"status": "online", "last_active": 1712345678.0, "info": {"nickname": "MyBot"}}

# 列出所有 Bot
all_bots = sdk.adapter.list_bots()

# 列出指定平台的 Bot
platform_bots = sdk.adapter.list_bots("myplatform")

# 檢查 Bot 是否線上
is_online = sdk.adapter.is_bot_online("myplatform", "bot123")

# 獲取完整狀態摘要（適合 WebUI 展示）
summary = sdk.adapter.get_status_summary()
# {"adapters": {"myplatform": {"status": "started", "bots": {...}}}}
```

### 監聽 Bot 生命週期

```python
from ErisPulse import sdk

@sdk.lifecycle.on("adapter.bot.online")
async def on_bot_online(data):
    platform = data.get("platform")
    bot_id = data.get("bot_id")
    sdk.logger.info(f"Bot 上線: {platform}/{bot_id}")

@sdk.lifecycle.on("adapter.bot.offline")
async def on_bot_offline(data):
    platform = data.get("platform")
    bot_id = data.get("bot_id")
    sdk.logger.info(f"Bot 下線: {platform}/{bot_id}")
```

## 相關文件

- [適配器開發入門](getting-started.md) - 建立第一個適配器
- [SendDSL 詳解](send-dsl.md) - 學習訊息傳送
- [適配器最佳實踐](best-practices.md) - 開發高品質適配器



### SendDSL 详解

# SendDSL 详解

SendDSL 是 ErisPulse 适配器提供的鏈式呼叫風格的訊息傳送介面。

## 基本呼叫方式

### 1. 指定類型和ID

```python
await adapter.Send.To("group", "123").Text("Hello")
```

### 2. 僅指定ID

```python
await adapter.Send.To("123").Text("Hello")
```

### 3. 指定發送帳號

```python
await adapter.Send.Using("bot1").Text("Hello")
```

### 4. 組合使用

```python
await adapter.Send.Using("bot1").To("group", "123").Text("Hello")
```

## 方法鏈

```mermaid
flowchart LR
    A["Using / Account<br/>（選發送帳號，可選）"] --> B["To<br/>（選目標類型與 ID）"]
    B --> C["修飾方法<br/>At / Reply / Expire / ForMember 等"]
    C --> D["發送方法<br/>Text / Image / Voice / Raw_ob12"]
    D --> E["返回 asyncio.Task"]
```

## 發送方法

所有發送方法返回 `asyncio.Task` 對象。

### 基本方法（基類內置）

以下標準方法已由 `SendDSL` 基類內置實現，**預設委託給 `Raw_ob12`**，適配器子類無需重複實現即可直接使用，且 IDE 能補全：

| 方法名 | 說明 | 回傳值 |
|--------|------|---------|
| `Text(text: str)` | 發送文字訊息 | `asyncio.Task` |
| `Image(file: bytes \| str)` | 發送圖片 | `asyncio.Task` |
| `Voice(file: bytes \| str)` | 發送語音（OneBot12 `audio` 段） | `asyncio.Task` |
| `Video(file: bytes \| str)` | 發送影片 | `asyncio.Task` |
| `File(file: bytes \| str, filename: str = None)` | 發送檔案 | `asyncio.Task` |

適配器可覆蓋單個標準方法以提供平台特定邏輯：

```python
class Send(SendDSL):
    def Raw_ob12(self, message, **kwargs):
        # 必須實現
        ...

    # 可選：覆蓋 Text 以提供平台特定邏輯
    # def Text(self, text: str):
    #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

### 協議方法

| 方法名 | 說明 | 回傳值 | 是否必須 |
|--------|------|---------|---------|
| `Raw_ob12(message)` | 發送 OneBot12 格式訊息 | `asyncio.Task` | **必須實現** |

> **重要**：`Raw_ob12` 是適配器的核心方法，**必須實現**。它是反向轉換（OneBot12 → 平台）的統一入口。未實現時基類會記錄 error 日誌並回傳標準錯誤回應（`status: "failed"`, `retcode: 10002`）。標準方法（`Text`、`Image` 等）預設委託給 `Raw_ob12`。

### 平台特有方法

適配器可在 `Send` 子類中新增平台特有的發送方法（會被 `event.supports()` / `event.available_methods()` 識別）：

```python
class Send(SendDSL):
    def Raw_ob12(self, message, **kwargs): ...

    # 平台特有方法
    def Sticker(self, sticker_id: str):
        return self.Raw_ob12([{"type": "sticker", "data": {"id": sticker_id}}])
```

## 修飾方法

修飾方法回傳 `self` 以支援鏈式呼叫。

### At 方法

```python
# @單個用戶
await adapter.Send.To("group", "123").At("456").Text("你好")

# @多個用戶
await adapter.Send.To("group", "123").At("456").At("789").Text("你們好")
```

### AtAll 方法

```python
# @全體成員
await adapter.Send.To("group", "123").AtAll().Text("大家好")
```

### Reply 方法

```python
# 回覆訊息
await adapter.Send.To("group", "123").Reply("msg_id").Text("回覆內容")
```

### 組合修飾

```python
await adapter.Send.To("group", "123").At("456").Reply("msg_id").Text("回覆@的訊息")
```

### 平台專有修飾方法

除了內建的 `At`/`AtAll`/`Reply`，適配器可以定義**平台專有的修飾方法**。這類方法**只需回傳 `self`**，無需任何裝飾器——框架會自動識別：

- 回傳 `self`（SendDSL 實例）→ 修飾方法，不觸發發送包裝/生命週期事件，鏈式繼續
- 回傳 `Task`/`Awaitable` → 發送方法

```python
class Send(SendDSL):
    def Raw_ob12(self, message, **kwargs): ...

    # 修飾方法：回傳 self，不發送
    def Expire(self, seconds: int):
        self._expire = seconds
        return self

    def ForMember(self, user_id: str):
        self._member = user_id
        return self

    # 發送方法：回傳 Task，依賴修飾方法設定的狀態
    def Board(self, content: str, **kwargs):
        return self.Raw_ob12([{"type": "board", "data": {"text": content}}])
```

使用：

```python
# 修飾方法可連續鏈式疊加
await adapter.Send.To("group", "big").Expire(3600).ForMember("114").Board("看板內容")
```

## 在 Event 包裝類中使用修飾方法

> [!NOTE]
> `reply(via=)` 與 `event.send_chain()` 本特性需要 ErisPulse **2.7.0+**。

`event.reply()` 預設只暴露 `at_sender`/`at_users`/`at_all`/`quote` 等內建修飾參數。要使用平台專有修飾方法，有兩種方式：

### 方式一：reply() 的 via 參數

適合少量、已知的修飾方法：

```python
await event.reply("看板內容", method="Board",
                  via=[("Expire", 3600), ("ForMember", "114514")])
```

`via` 是一個列表，每個元素可為：

| 形式 | 等價鏈式呼叫 |
|------|-------------|
| `"Name"` | `.Name()` |
| `("Name", arg1, arg2)` | `.Name(arg1, arg2)` |
| `("Name", (arg1,), {kw: val})` | `.Name(arg1, kw=val)` |

### 方式二：event.send_chain()

適合**連續多個修飾方法**或**無內容參數的動作型方法**（如撤回、刪除）。`send_chain()` 回傳已設定好 `To`/`Using` 的發送鏈，可自由追加任意修飾方法和發送方法：

```python
# 平台專有修飾方法 + 看板發送
await event.send_chain().Expire(3600).Board("一小時後過期")

# 連續多個修飾方法
await (event.send_chain()
       .Expire(3600)
       .ForMember("114514")
       .Board("看板內容", content_type="markdown"))

# 內建修飾方法同樣可用
await event.send_chain().At("123").Reply("msg_id").Text("hi")

# 無內容參數的動作型方法
await event.send_chain().DismissBoard()
```

> `send_chain()` 回傳的是完整的 SendDSL 實例，因此**所有鏈式特性都可用**——不僅是修飾方法，還包括發送規則和批量建構：

```python
# 發送規則：重試 + 超時 + 成功回調
await (event.send_chain()
       .Retry(3).Timeout(10)
       .Hook(lambda r: print("發送成功"))
       .Text("可靠發送"))

# 延遲發送 + 平台修飾 + 看板
await event.send_chain().Defer(5).Expire(3600).Board("延遲看板")

# 批量建構模式
results = await (event.send_chain()
                 .Build()
                 .Text("第一句").Image("pic.jpg").Text("第二句")
                 .send_all())
```

## 帳戶管理

### Using 方法

`Using()` 用於指定發送訊息的帳戶。傳入的標識符會透過 `_resolve_account()` 按以下優先級匹配：

1. **帳戶名** — 配置中的鍵名（如 `"default"`、`"bot1"`）
2. **執行時注入的 bot_id** — 從事件轉換時自動注入的標識符
3. **任意 str 字段** — 配置中其他字串字段
4. **兜底** — 第一個啟用的帳戶

```python
# 使用帳戶名
await adapter.Send.Using("account1").To("user", "123").Text("Hello")

# 使用 bot_id（即事件中的 self.user_id）
await adapter.Send.Using("bot_123").To("user", "123").Text("Hello")
```

### Account 方法

`Account` 方法與 `Using` 等價：

```python
await adapter.Send.Account("account1").To("user", "123").Text("Hello")
```

## 異步處理

### 不等待結果

```python
# 訊息在背景發送
task = adapter.Send.To("user", "123").Text("Hello")

# 繼續執行其他操作
# ...
```

### 等待結果

```python
# 直接 await 獲取結果
result = await adapter.Send.To("user", "123").Text("Hello")
print(f"發送結果: {result}")

# 先儲存 Task，稍後等待
task = adapter.Send.To("user", "123").Text("Hello")
# ... 其他操作 ...
result = await task
```

## 發送規則系統

SendDSL 內建了一套發送規則裝飾器，透過鏈式方法附加規則，在最終發送時統一應用。規則涵蓋常見的生產場景：超時控制、失敗重試、成功回調、延遲發送、優先級丟棄、進度監控。

規則方法**回傳 self**（與 At/AtAll/Reply 一樣），必須放在發送方法（Text/Image 等）之前呼叫。規則會隨 `To`/`Using`/`Account` 創建的新實例傳播。

### 規則方法一覽

| 方法 | 說明 |
|--------|------|
| `.Hook(callback)` | 發送成功後執行的回調（可多次呼叫，按順序執行） |
| `.Retry(times=1)` | 失敗自動重試 N 次（含首次共 N+1 次） |
| `.Timeout(seconds)` | 單次發送超時，超時取消當前嘗試（可與 Retry 叠加） |
| `.Defer(seconds=1.0)` | 延遲發送（進程內定時，不持久化） |
| `.Priority(level, drop_if_busy=False)` | 設定優先級；積壓時可丟棄 |
| `.OnProgress(callback)` | 各階段進度回調（傳入 `SendContext`） |
| `.OnError(callback)` | 最終失敗時的錯誤回調（僅觸發一次） |

### 發送成功後執行邏輯（Hook）

```python
# 同步回調
await (adapter.Send.To("user", "123")
       .Hook(lambda r: print(f"發送成功，訊息ID: {r['message_id']}"))
       .Text("你好"))

# 異步回調
async def deduct_points(result):
    await db.update(user_id="123", points=-1)

await adapter.Send.To("user", "123").Hook(deduct_points).Text("扣積分")
```

Hook 僅在發送最終成功（含重試成功）時執行；失敗、超時、取消不觸發。

### 失敗自動重試（Retry）

```python
# 首次失敗後重試 2 次，共 3 次嘗試
result = await adapter.Send.To("user", "123").Retry(2).Text("帶重試")
```

重試觸發條件：發送拋出異常、發送超時、發送回傳 `status == "failed"` 的回應。

### 超時自動取消（Timeout）

```python
# 單次發送超過 10 秒則取消
await adapter.Send.To("user", "123").Timeout(10).Text("帶超時")

# 超時 + 重試：每次嘗試 10 秒，最多 3 次
await adapter.Send.To("user", "123").Timeout(10).Retry(2).Text("超時重試")
```

### 進度監控（OnProgress / OnError）

```python
def on_progress(ctx):
    print(f"階段: {ctx.stage}, 嘗試: {ctx.attempt + 1}/{ctx.max_attempts}, 耗時: {ctx.elapsed:.2f}s")
    if ctx.stage == "failed":
        print(f"  錯誤: {ctx.error!r}")

async def on_error(ctx):
    await notify_admin(f"發送給 {ctx.target_id} 失敗: {ctx.error!r}")

await (adapter.Send.To("user", "123")
       .Retry(3).Timeout(10)
       .OnProgress(on_progress)
       .OnError(on_error)
       .Text("監控"))
```

`SendContext` 包含的欄位：`task_id`、`platform`、`method`、`target_type`、`target_id`、`bot_id`、`stage`、`attempt`、`max_attempts`、`started_at`、`finished_at`、`elapsed`、`error`、`result`、`extra`。

`stage` 可能的值：`pending`、`sending`、`retrying`、`success`、`failed`、`timeout`、`cancelled`、`dropped`。

### 延遲發送（Defer）

```python
# 5 秒後發送
await adapter.Send.To("user", "123").Defer(5).Text("遲到訊息")
```

> 注意：延遲為進程內定時，進程重啟會丟失，不提供持久化。

### 優先級與積壓丟棄（Priority）

```python
# 低優先級訊息，佇列積壓時自動丟棄
result = await (adapter.Send.To("user", "123")
               .Priority(-1, drop_if_busy=True)
               .Text("可放棄的通知"))
# 若被丟棄，result["status"] == "failed"
```

`drop_if_busy` 啟用後，當在途發送任務數超過閾值（預設 64）時直接放棄本次發送。可透過 `.PriorityThreshold(n)` 調整全域閾值。

### 規則組合與背景執行

```python
# 不阻塞主流程，規則照樣生效
task = (adapter.Send.To("user", "123")
        .Hook(lambda r: print("發送成功！"))
        .Retry(3)
        .Timeout(10)
        .OnProgress(on_progress)
        .Text("你好"))

# 繼續執行其他操作
await handle_next_action()
```

### 規則傳播

規則隨 `To`/`Using`/`Account` 創建的新實例傳播，避免鏈式呼叫中規則丟失：

```python
# 規則在 To 之前設定，也會傳播到 To 創建的實例
builder = adapter.Send.Retry(3).Timeout(10)
send = builder.To("user", "123")  # send 仍攜帶 Retry(3) 和 Timeout(10)
await send.Text("hi")
```

多個實例的規則相互獨立（hooks 列表深拷貝）。

## 批量建構模式（Build）

除單發模式外，SendDSL 還支援批量建構模式：一條鏈路中寫多個發送方法，最後統一執行。適用於「一口氣發多條訊息」的場景。

### 進入建構模式

在發送方法之前呼叫 `.Build()`，回傳 `SendBuilder`。此後發送方法（Text/Image 等）不再立即執行，而是累積為發送意圖：

```python
results = await (adapter.Send.To("user", "123")
                 .Build()                    # 進入建構模式
                 .Text("第一句")
                 .Image("pic.jpg")
                 .Text("第二句")
                 .send_all())                 # 統一執行
# results = [Text結果, Image結果, Text結果]
```

`.send_all()` 回傳 `asyncio.Task`，await 後得到結果列表（按意圖順序）。

### 並行與串行

預設**並行**執行（併發發送，總耗時約等於最慢的一條）。需要保證訊息到達順序時呼叫 `.Sequential()`：

```python
# 串行：按順序依次發送
await (adapter.Send.To("group", "456")
       .Build()
       .Sequential()
       .Text("先發這個").Text("再發這個")
       .send_all())

# 並行（預設，可顯式呼叫）
await (adapter.Send.To("group", "456")
       .Build()
       .Parallel()
       .Text("併發1").Text("併發2")
       .send_all())
```

### 失敗繼續與重試

批量執行採用**失敗繼續**策略：某條失敗不會中斷其他條的發送。配合 `.Retry()` 時，失敗的條目會自動重試（重試作用於單條，不是重試整批）：

```python
await (adapter.Send.To("user", "123")
       .Build()
       .Retry(2)                       # 每條各自重試 2 次
       .Text("可能失敗的").Image("也可能失敗的")
       .send_all())
```

### 整批規則與回調

規則統一作用於整批：

| 方法 | 說明 |
|--------|------|
| `.Timeout(seconds)` | 每條發送的單次超時 |
| `.Retry(times)` | 每條發送各自重試（失敗繼續） |
| `.Defer(seconds)` | 延遲整批發送 |
| `.Hook(callback)` | 整批全部成功後觸發，接收 `results` 列表 |
| `.OnError(callback)` | 批次存在失敗時觸發，接收 `BatchContext` |
| `.OnProgress(callback)` | 每條完成時觸發，接收 `BatchContext` |

```python
def on_progress(ctx):
    print(f"進度: {ctx.completed}/{ctx.total}, 成功 {ctx.succeeded}, 失敗 {ctx.failed}")

async def on_error(ctx):
    print(f"批次有 {ctx.failed} 條失敗")

results = await (adapter.Send.To("user", "123")
               .Build()
               .Retry(2).Timeout(10)
               .OnProgress(on_progress)
               .OnError(on_error)
               .Hook(lambda rs: print("整批完成"))
               .Text("a").Text("b").Text("c")
               .send_all())
```

`BatchContext` 包含：`task_id`、`total`、`completed`、`succeeded`、`failed`、`stage`、`results`、`errors`、`elapsed`、`extra`。

`stage` 可能的值：`pending`、`sending`、`success`（全部成功）、`partial`（部分成功）、`failed`（全部失敗）。

### 修飾器與規則的繼承

`.Build()` 之前的 At/AtAll/Reply 修飾器和規則會繼承到整批，作用於每條訊息：

```python
await (adapter.Send.To("group", "456")
       .At("789")                        # 繼承：每條訊息都 @789
       .Build()
       .Retry(2)                         # 繼承 + 追加：每條各自重試
       .Text("@你的通知")
       .Image("公告圖")
       .send_all())
```

進入 Build 後仍可追加修飾器（作用於整批）：

```python
await (adapter.Send.To("group", "456")
       .Build()
       .At("111").At("222")             # 追加 @，作用於整批
       .Text("@多人")
       .send_all())
```

### 背景執行

與單發一樣，`.send_all()` 回傳 Task，可不 await 讓其在背景執行：

```python
task = (adapter.Send.To("user", "123")
        .Build()
        .Hook(lambda rs: print("批量發送完成"))
        .Text("a").Text("b")
        .send_all())

# 不阻塞主流程
await do_something_else()
```

## 命名規範

### PascalCase 命名

所有發送方法使用大駝峰命名法：

```python
# ✅ 正確
def Text(self, text: str):
    pass

def Image(self, file: bytes):
    pass

# ❌ 錯誤
def text(self, text: str):
    pass

def send_image(self, file: bytes):
    pass
```

### 平台特有方法

不推薦添加平台前綴方法：

```python
# ✅ 推薦
def Sticker(self, sticker_id: str):
    pass

# ❌ 不推薦
def TelegramSticker(self, sticker_id: str):
    pass
```

使用 `Raw` 方法替代：

```python
# ✅ 推薦
await adapter.Send.Raw_ob12([{"type": "sticker", ...}])

# ❌ 不推薦
def TelegramSticker(self, ...):
    pass
```

## 發送鏈路內部拆解

一次 `await adapter.Send.To("group", "123").Text("x")` 的背後，框架幫你完成了下面這一串事：

```mermaid
flowchart TD
    A["adapter.Send.To(...).Text(...)"] --> B["To/Using 鏈式方法<br/>每次回傳不可變新實例（順序無關）"]
    B --> C["__getattribute__ 拦截發送方法<br/>包一層規則包裝器"]
    C --> D["呼叫原始方法（如 Text）<br/>內部委託 Raw_ob12"]
    D --> E["Raw_ob12 回傳 asyncio.create_task(...)"]
    E --> F["寫 [Send] 日誌"]
    F --> G["emit message.sending（fire-and-forget）"]
    G --> H{"聲明了發送規則？"}
    H -->|"否"| I["Task done_callback → emit message.sent"]
    H -->|"是"| J["apply_send_rules 包成外層 Task<br/>重試/超時/延遲/優先級"]
    J --> I
    I --> K["await 得到標準回應 dict"]
```

**每一步框架做了什麼：**

| 階段 | 框架做了什麼 |
|------|-------------|
| 鏈式合併 | `To`/`Using`/`Account` 每次呼叫都**新建不可變實例**並繼承已設欄位，因此 `To(...).Using(...)` 與 `Using(...).To(...)` **等價**、順序無關 |
| 方法包裝 | 發送方法（`Text` 等）被 `__getattribute__` 拦截包一層；修飾方法（`To`/`Using`/`At`/`Retry` 等）**不包裝**。嵌套的 `Raw_ob12` 調用靠 `_in_rule_wrap` 標記防重複包裝 |
| Task 建立 | `Raw_ob12` 內部 `asyncio.create_task()` 才是 Task 真正的建立點；`Text()` 只是同步回傳這個 Task，**不阻塞** |
| 發送日誌 | 寫 `[Send] platform/method -> target` 事件日誌（`exclude_levels=["EVENT"]` 可屏蔽） |
| `message.sending` | 發送方法被呼叫時**立即**以 fire-and-forget 觸發（僅當存在監聽者，先 `has_handlers` 短路） |
| `message.sent` | 綁定在 Task 的 `done_callback` 上——**有規則時覆蓋整個重試流程的最終結果**，無規則時即原始 Task 完成 |

### 帳戶解析回退鏈

當適配器內部呼叫 `_resolve_account(account_id)` 時，按以下順序解析到具體帳戶：

1. 單帳戶適配器（無 `AccountConfigClass`）→ 直接回傳
2. 帳戶名精確匹配 `account_id`
3. 各帳戶 `bot_id` 欄位匹配
4. 各帳戶任意 `str` 欄位值匹配（排除 `enabled`/`name`）
5. 兜底第一個啟用的帳戶
6. 全部失敗 → 抛 `ValueError`

> 你傳的 `account_id` 來自：`Using()` 显式指定 > 事件 `self` 欄位（`account_id` 优先于 `user_id`，由 `event.reply()` 自动注入）> 不指定（由适配器兜底第一个启用账户）。

### 發送規則引擎（重試/超時/延遲）

規則在 `Raw_ob12` 回傳 Task **之後**包裝成新的外層 Task，不影響主流程。關鍵事實：

| 規則 | 說明 |
|------|------|
| `Retry(n)` | 總嘗試 `n+1` 次；**失敗後立即重發，無指數退避** |
| `Timeout(s)` | 單次發送超時取消（`asyncio.wait_for`），未耗盡則重試 |
| `Defer(s)` | 發送前延遲 sleep |
| `Priority(level, drop_if_busy)` | 积壓超閾值時直接回傳 `{status:"failed", retcode:10002, message:"dropped_low_priority"}` |
| `Hook(fn)` | 僅最終成功時按序執行 |
| `on_progress` / `on_error` | 各階段 / 最終失敗回調 |

> **注意**：重試是「立即重發」，沒有退避間隔；若平台限流需要退避，請在 `on_error` 回調裡自行 sleep 後再手動重發。規則的成功判定以回傳 dict 的 `status == "ok"` 為準（`retcode == 0`）。

> 標準回應格式與 `retcode` 完整語義見 [API 回應規範](../../standards/api-response.md)。

## 回傳值

### Task 對象

所有發送方法回傳 `asyncio.Task`。適配器只需實現 `Raw_ob12`，標準方法（Text/Image 等）預設委託給它：

```python
import asyncio

def Raw_ob12(self, message, **kwargs):
    async def _do_send():
        segments = self._apply_modifiers(message)
        return await self._adapter.call_api(
            endpoint="/send_message",
            message=segments,
            **self.send_context,
            **kwargs,
        )
    return asyncio.create_task(_do_send())

# Text/Image/Voice/Video/File 已從基類繼承，自動委託給 Raw_ob12
# 如需覆蓋標準方法，回傳 asyncio.Task 即可：
# def Text(self, text: str):
#     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

### 標準化回應

`call_api` 應回傳標準化回應。推薦使用 `make_response()` / `make_error()` 方法：

```python
async def call_api(self, endpoint: str, **params):
    try:
        result = await self._do_api_call(endpoint, **params)
        return self.make_response(
            data=result.get("data"),
            message_id=result.get("message_id", ""),
            raw=result,
        )
    except Exception as e:
        return self.make_error(message=str(e))
```

也支援手動構造（舊版方式仍然相容）：

```python
async def call_api(self, endpoint: str, **params):
    return {
        "status": "ok" or "failed",
        "retcode": 0 or error_code,
        "data": {...},
        "message_id": "msg_id" or "",
        "message": "",
        "{platform}_raw": raw_response
    }
```

## 完整示例

### 基本使用

```python
from ErisPulse.Core import adapter

my_adapter = adapter.get("myplatform")

# 發送文字
await my_adapter.Send.To("user", "123").Text("Hello World!")

# 發送圖片
await my_adapter.Send.To("group", "456").Image("https://example.com/image.jpg")

# 發送檔案
with open("document.pdf", "rb") as f:
    await my_adapter.Send.To("user", "123").File(f.read())
```

### 鏈式呼叫

```python
# @用戶 + 回覆
await my_adapter.Send.To("group", "456").At("789").Reply("msg123").Text("回覆@的訊息")

# @全體 + 多個修飾
await my_adapter.Send.Using("bot1").To("group", "456").AtAll().Text("公告訊息")
```

### 原始訊息與訊息建構

`Raw_ob12` 是反向轉換的核心入口（接收 OB12 訊息段 → 平台 API 調用），`MessageBuilder` 是配合其使用的鏈式訊息段建構工具。

> 完整的 `Raw_ob12` 實現規範、`MessageBuilder` 用法及程式碼示例請參閱：
> - [發送方法規範 §6 反向轉換規範](../../standards/send-method-spec.md#6-反向轉換規範onebot12--平台)
> - [發送方法規範 §11 訊息建構器](../../standards/send-method-spec.md#11-訊息建構器-messagebuilder)

## 相關文件

- [適配器開發入門](getting-started.md) - 建立適配器
- [適配器核心概念](core-concepts.md) - 了解適配器架構
- [適配器最佳實踐](best-practices.md) - 開發高品質適配器
- [發送方法規範](../../standards/send-method-spec.md) - 發送方法完整規範



### 适配器开发最佳实践

# 適配器開發最佳實踐

本文檔提供了 ErisPulse 適配器開發的最佳實踐建議。

## Bot 狀態管理與 Meta 事件

適配器應主動透過 `adapter.emit()` 發送 meta 事件，讓框架自動追蹤 Bot 的連線狀態、上下線和心跳資訊。

### 1. 何時發送 Meta 事件

| 事件 | `detail_type` | 觸發時機 | 框架行為 |
|------|--------------|---------|---------|
| 連接 | `"connect"` | Bot 與平台建立連線時 | 註冊 Bot，觸發 `adapter.bot.online` 生命週期事件 |
| 斷開 | `"disconnect"` | Bot 與平台斷開連線時 | 標記 Bot 離線，觸發 `adapter.bot.offline` 生命週期事件 |
| 心跳 | `"heartbeat"` | 定期發送（建議 30-60 秒） | 更新 Bot 活躍時間和元資訊 |

### 2. 發送 Meta 事件

框架提供 `emit_meta()` 方法，一行即可發送 meta 事件：

```python
class MyAdapter(BaseAdapter):
    async def _ws_handler(self, websocket):
        bot_id = self._get_bot_id()

        # Bot 上線：一行發送 connect 事件
        await self.emit_meta("connect", bot_id, user_name="MyBot", nickname="我的機器人")

        try:
            while True:
                data = await websocket.receive_text()
                event = self.convert(data)
                if event:
                    await self.adapter.emit(event)
        except WebSocketDisconnect:
            pass
        finally:
            # Bot 下線
            await self.emit_meta("disconnect", bot_id)
```

### 3. 心跳事件

適配器應在連線存活期間定期發送心跳事件，更新 Bot 的活躍時間：

```python
class MyAdapter(BaseAdapter):
    async def _heartbeat_loop(self, bot_id: str):
        while self._connected:
            # 向框架發送 meta heartbeat（一行完成）
            await self.emit_meta("heartbeat", bot_id)
            await asyncio.sleep(30)
```

### 4. `self` 字段自動發現

框架的 `adapter.emit()` 會自動處理所有事件（不只是 meta 事件）中的 `self` 字段：

- **一般事件**（message/notice/request）中的 `self` 字段會自動發現並註冊 Bot
- **`self` 字段擴展資訊**：支援 `user_name`、`nickname`、`avatar`、`account_id` 可選欄位

```python
# 轉換器中包含 self 字段即可自動註冊 Bot
onebot_event = {
    "type": "message",
    "detail_type": "private",
    "platform": "myplatform",
    "self": {
        "platform": "myplatform",
        "user_id": "bot123",
        "user_name": "MyBot",
        "nickname": "我的機器人",
    },
    # ... 其他欄位
}
await self.adapter.emit(onebot_event)
# Bot "bot123" 已自動註冊並更新活躍時間
```

### 5. Bot 狀態查詢

框架提供以下查詢方法：

```python
from ErisPulse import sdk

# 獲取 Bot 詳細資訊
info = sdk.adapter.get_bot_info("myplatform", "bot123")
# {"status": "online", "last_active": 1712345678.0, "info": {"nickname": "MyBot"}}

# 列出所有 Bot（按平台分組）
all_bots = sdk.adapter.list_bots()

# 列出指定平台的 Bot
platform_bots = sdk.adapter.list_bots("myplatform")

# 檢查 Bot 是否在線
is_online = sdk.adapter.is_bot_online("myplatform", "bot123")

# 獲取完整狀態摘要（適合 WebUI 展示）
summary = sdk.adapter.get_status_summary()
# {"adapters": {"myplatform": {"status": "started", "bots": {...}}}}
```

## 連線管理

### 1. 實現連線重試

```python
import asyncio

class MyAdapter(BaseAdapter):
    async def start(self):
        retry_count = 0
        max_retries = 5
        
        while retry_count < max_retries:
            try:
                await self._connect_to_platform()
                self.logger.info("連線成功")
                break
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    # 指數退避策略
                    wait_time = min(60 * (2 ** retry_count), 600)
                    self.logger.warning(
                        f"連線失敗，{wait_time}秒後重試 ({retry_count}/{max_retries}): {e}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error("連線失敗，已達到最大重試次數")
                    raise
```

### 2. 連線狀態管理

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        self.connection = None
        self._connected = False
    
    async def _ws_handler(self, websocket: WebSocket):
        self.connection = websocket
        self._connected = True
        self.logger.info("連線已建立")
        
        try:
            while True:
                data = await websocket.receive_text()
                await self._process_event(data)
        except WebSocketDisconnect:
            self.logger.info("連線已斷開")
        finally:
            self.connection = None
            self._connected = False
```

### 3. 心跳保活與 Meta 心跳

適配器的心跳應同時完成兩個任務：向平台發送心跳保活，並向框架發送 meta heartbeat 事件。

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        self.connection = await self._connect_to_platform()
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def _heartbeat_loop(self):
        while self.connection:
            try:
                # 1. 向平台發送心跳保活
                await self.connection.send_json({"type": "ping"})

                # 2. 向框架發送 meta heartbeat（使用 emit_meta 一行完成）
                await self.emit_meta("heartbeat", self._bot_id)

                await asyncio.sleep(30)
            except Exception as e:
                self.logger.error(f"心跳失敗: {e}")
                break
```

### 4. 連線資訊揭露

適配器註冊的路由應對使用者可見，便於使用者設定平台端的回呼位址。推薦在 `start()` 中主動輸出連線資訊：

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        router.register_websocket(
            module_name=self.platform,
            path="/ws",
            handler=self._ws_handler
        )

        if self.sdk:
            info = self.sdk.adapter.get_connection_info(self.platform)
            if info:
                self.logger.info(f"WebSocket 位址: "
                    f"{info.get('connection', {}).get('base_url', '')}"
                    f"{info.get('connection', {}).get('websocket_routes', [])}")
```

使用者可以透過以下 API 查看適配器的所有路由和連線位址：

```python
from ErisPulse import sdk

# 適配器層級的連線資訊（推薦）
info = sdk.adapter.get_connection_info("myplatform")

# 路由管理器層級的查詢
sdk.router.list_namespaces()              # 列出所有命名空間
sdk.router.get_module_routes("myplatform")  # 詳細路由資訊
sdk.router.get_module_urls("myplatform")    # 完整連線 URL
```

> **注意**：路由註冊時的 `module_name` 必須與適配器在 ErisPulse 中註冊的 `platform` 名稱完全一致，否則 `get_connection_info()` 將無法關聯路由。多帳號適配器應為每個帳號註冊子路徑（如 `/account1/webhook`、`/account2/webhook`），而非使用不同的 `module_name`。

## 事件轉換

### 1. 嚴格遵循 OneBot12 標準

```python
class MyPlatformConverter:
    def convert(self, raw_event):
        """轉換事件"""
        onebot_event = {
            "id": str(raw_event.get("event_id", uuid.uuid4())),
            "time": int(time.time()),
            "type": self._convert_type(raw_event.get("type")),
            "detail_type": self._convert_detail_type(raw_event),
            "platform": "myplatform",
            "self": {
                "platform": "myplatform",
                "user_id": str(raw_event.get("bot_id", ""))
            },
            "myplatform_raw": raw_event,  # 保留原始資料（必須）
            "myplatform_raw_type": raw_event.get("type", "")  # 原始類型（必須）
        }
        return onebot_event
```

### 2. 時間戳標準化

```python
def _convert_timestamp(self, timestamp):
    """轉換為 10 位秒級時間戳"""
    if not timestamp:
        return int(time.time())
    
    # 如果是毫秒級時間戳
    if timestamp > 10**12:
        return int(timestamp / 1000)
    
    # 如果是秒級時間戳
    return int(timestamp)
```

### 3. 事件 ID 生成

```python
import uuid

def _generate_event_id(self, raw_event):
    """生成事件 ID"""
    event_id = raw_event.get("event_id")
    if event_id:
        return str(event_id)
    # 如果平台沒有提供 ID，生成 UUID
    return str(uuid.uuid4())
```

## SendDSL 實現

`At`/`AtAll`/`Reply` 修飾器已由框架 SendDSL 基類內建，適配器只需實現 `Raw_ob12` 和具體發送方法。使用 `self._apply_modifiers(message)` 和 `self.send_context` 簡化開發。

### 1. 必須返回 Task 物件

```python
class Send(BaseAdapter.Send):
    def Raw_ob12(self, message, **kwargs):
        """推薦實現：使用框架輔助方法"""
        async def _do_send():
            segments = self._apply_modifiers(message)
            return await self._adapter.call_api(
                endpoint="/send_message",
                message=segments,
                **self.send_context,
                **kwargs
            )
        return asyncio.create_task(_do_send())

    def Text(self, text: str):
        return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

### 2. 鏈式修飾方法返回 self

```python
class Send(BaseAdapter.Send):

    def __init__(self, adapter, target_type=None, target_id=None, account_id=None):
        super().__init__(adapter, target_type, target_id, account_id)
        self.buttons = []

    def Button(self, content: list) -> 'Send':
        self.buttons.append(content)
        return self # 返回 self
```

### 3. 支援平台特有方法

```python
class Send(BaseAdapter.Send):
    def Sticker(self, sticker_id: str):
        """發送貼圖"""
        return asyncio.create_task(
            self._adapter.call_api(
                endpoint="/send_sticker",
                message=[{"type": "sticker", "data": {"id": sticker_id}}],
                **self.send_context
            )
        )
    
    def Card(self, card_data: dict):
        """發送卡片訊息"""
        return asyncio.create_task(
            self._adapter.call_api(
                endpoint="/send_card",
                message=[{"type": "card", "data": card_data}],
                **self.send_context
            )
        )
```

## API 回應

### 1. 標準化回應格式

框架提供 `make_response()` 和 `make_error()` 方法構造標準化回應：

```python
async def call_api(self, endpoint: str, **params):
    try:
        raw_response = await self._platform_api_call(endpoint, **params)
        
        if raw_response.get("success"):
            return self.make_response(
                data=raw_response.get("data"),
                message_id=raw_response.get("data", {}).get("message_id", ""),
                raw=raw_response,
            )
        else:
            return self.make_error(
                retcode=raw_response.get("code", 10001),
                message=raw_response.get("message", ""),
                raw=raw_response,
            )
    except Exception as e:
        return self.make_error(message=str(e))
```

`make_response()` 會自動生成包含 `{platform}_raw` 鍵的回應字典。`make_error()` 預設使用 `retcode=34000`（Platform Error）。

### 2. 錯誤碼規範

遵循 OneBot12 標準錯誤碼：

```python
# 1xxxx - 動作請求錯誤
10001: Bad Request
10002: Unsupported Action
10003: Bad Param

# 2xxxx - 動作處理器錯誤
20001: Bad Handler
20002: Internal Handler Error

# 3xxxx - 動作執行錯誤
31000: Database Error
32000: Filesystem Error
33000: Network Error
34000: Platform Error
35000: Logic Error
```

## 多帳號支援

### 1. 聲明式配置（推薦）

使用 `AccountConfigClass` 聲明配置類後，框架自動管理多帳號載入、驗證和範本生成。`BotAccountConfig` 基類提供 `enabled` 和 `name` 欄位，適配器無需聲明：

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BotAccountConfig

@dataclass
class MyBotConfig(BotAccountConfig):
    token: str = field(default="", metadata={
        "description": {"i18n": "my_adapter.bot_token", "default": "Bot Token"},
        "required": True,
        "secret": True,
    })

class MyAdapter(BaseAdapter):
    AccountConfigClass = MyBotConfig
    
    async def start(self):
        for name, account in self.enabled_accounts.items():
            self.logger.info(f"啟動帳號 {name}")
            await self._connect(name, account.token)
            # bot_id 由框架自動從平台協議/登入回應中獲取並回填
    
    async def call_api(self, endpoint: str, **params):
        account_id = params.pop("account_id", None)
        name, account = self._resolve_account(account_id)
        # name: 帳號名, account: MyBotConfig 實例
```

配置檔案自动生成為：

```toml
[MyAdapter.accounts.default]
token = ""
enabled = true
name = ""
```

### 2. 帳號選擇機制

框架內建 `_resolve_account()` 方法，匹配優先順序：

1. **帳號名** — 配置鍵名精確匹配
2. **`bot_id` 欄位** — 自動獲取的 bot_id（即 `event["self"]["user_id"]`）
3. **任意 str 欄位** — 配置中其他字串欄位
4. **兜底** — 第一個啟用的帳號

```python
# 按帳號名匹配
name, account = self._resolve_account("account1")

# 按 bot_id 匹配（最常用的方式，來自事件）
name, account = self._resolve_account("bot_123")

# 獲取第一個啟用的帳號（傳入 None）
name, account = self._resolve_account(None)
```

## 錯誤處理

### 1. 分類異常處理

使用 `make_error()` 構造標準化錯誤回應。透過 `sdk.client` 請求時捕獲 ErisPulse 異常：

```python
from ErisPulse.Core.Bases.errors import ClientError, ClientTimeoutError

async def call_api(self, endpoint: str, **params):
    try:
        from ErisPulse.Core import client
        resp = await client.post(
            f"https://api.platform.com/{endpoint}",
            json=params,
            max_retries=2,
        )
        response = await resp.json()
        return self.make_response(data=response, raw=response)
    except ClientTimeoutError:
        self.logger.error(f"請求超時: {endpoint}")
        return self.make_error(retcode=32000, message="請求超時")
    except ClientError as e:
        self.logger.error(f"網路錯誤: {e}")
        return self.make_error(retcode=33000, message="網路請求失敗")
    except json.JSONDecodeError:
        self.logger.error("JSON 解析失敗")
        return self.make_error(retcode=10006, message="回應格式錯誤")
    except Exception as e:
        self.logger.error(f"未知錯誤: {e}", exc_info=True)
        return self.make_error(message=str(e))
```

> **向後相容**：直接使用 `aiohttp` 的舊適配器程式碼不受影響，仍可捕獲 `aiohttp.ClientError`。異常轉換僅在透過 `sdk.client` 發起請求時生效。

### 2. 日誌記錄

框架自動為適配器建立子 logger（`sdk.logger.get_child("MyAdapter")`），無需手動初始化：

```python
class MyAdapter(BaseAdapter):
    # ConfigClass = ...  # 聲明配置類後 self.logger 自動可用
    
    async def start(self):
        self.logger.info("適配器啟動中...")
        # ...
        self.logger.info("適配器啟動完成")
    
    async def shutdown(self):
        self.logger.info("適配器關閉中...")
        # ...
        self.logger.info("適配器關閉完成")
```

## 測試

### 1. 單元測試

```python
import pytest
from ErisPulse.Core.Bases import BaseAdapter

class TestMyAdapter:
    def test_converter(self):
        """測試轉換器"""
        converter = MyPlatformConverter()
        raw_event = {"type": "message", "content": "Hello"}
        result = converter.convert(raw_event)
        assert result is not None
        assert result["platform"] == "myplatform"
        assert "myplatform_raw" in result
    
    def test_api_response(self):
        """測試 API 回應格式"""
        adapter = MyAdapter()
        response = adapter.call_api("/test", param="value")
        assert "status" in response
        assert "retcode" in response
```

### 2. 集成測試

```python
@pytest.mark.asyncio
async def test_adapter_start():
    """測試適配器啟動"""
    adapter = MyAdapter()
    await adapter.start()
    assert adapter._connected is True

@pytest.mark.asyncio
async def test_send_message():
    """測試發送訊息"""
    adapter = MyAdapter()
    await adapter.start()
    
    result = await adapter.Send.To("user", "123").Text("Hello")
    assert result is not None
```

## 反向轉換與訊息建構

`Raw_ob12` 是適配器**必須實現**的方法，是反向轉換（OneBot12 → 平台）的統一入口。標準方法（`Text`、`Image` 等）應委託給 `Raw_ob12`，修飾器狀態（`At`/`Reply`/`AtAll`）需在 `Raw_ob12` 內合併為訊息段。

`MessageBuilder` 是配合 `Raw_ob12` 使用的訊息段建構工具，支援鏈式呼叫和快速建構。

> 完整的實現規範、程式碼範例和使用方法請參閱：
> - [發送方法規範 §6 反向轉換規範](../../standards/send-method-spec.md#6-反向轉換規範onebot12--平台)
> - [發送方法規範 §11 訊息建構器](../../standards/send-method-spec.md#11-訊息建構器-messagebuilder)

## 平台事件方法擴充

適配器可以為 Event 包裝類註冊平台專有方法，讓模組開發者能更方便地存取平台特有資料。

### 1. 使用 Mixin 類批量註冊（推薦）

當平台有數個專有方法時，推薦使用 Mixin 類：

```python
# 在適配器的 start() 或模組層級註冊
from ErisPulse.Core.Event import register_event_mixin

class MyPlatformEventMixin:
    def get_chat_name(self):
        """獲取聊天名稱"""
        return self.get("myplatform_raw", {}).get("chat", {}).get("name", "")

    def is_official_message(self):
        """判斷是否為官方訊息"""
        raw = self.get("myplatform_raw", {})
        return raw.get("sender", {}).get("is_official", False)

    def get_message_type(self):
        """獲取平台訊息類型"""
        return self.get("myplatform_raw", {}).get("msg_type", "text")

# 批量註冊
register_event_mixin("myplatform", MyPlatformEventMixin)
```

### 2. 使用裝飾器註冊單個方法

```python
from ErisPulse.Core.Event import register_event_method

@register_event_method("myplatform")
def get_chat_name(self):
    return self.get("myplatform_raw", {}).get("chat", {}).get("name", "")
```

### 3. 適配器關閉時清理

```python
from ErisPulse.Core.Event import unregister_platform_event_methods

class MyAdapter(BaseAdapter):
    async def shutdown(self):
        # 清理平台事件方法註冊
        unregister_platform_event_methods("myplatform")
        # ... 其他清理
```

> 更詳細的註冊和註銷說明請參閱 [事件系統 API - 註冊平台擴充方法](../../api-reference/event-system.md#適配器註冊平台擴充方法)。

## 文件維護

### 1. 維護平台特性文件

在 `docs/zh-TW/platform-guide/` 下建立 `{platform}.md` 文件(其它語言版本會自動產生)：

```markdown
# 平台名稱適配器文件

## 基本資訊
- 對應模組版本: 1.0.0
- 維護者: Your Name

## 支援的訊息發送類型
...

## 特有事件類型
...

## 配置選項
...
```

### 2. 更新版本資訊

發布新版本時，更新文件中的版本資訊：

```toml
[project]
version = "2.0.0"  # 更新版本號
```

## 相關文件

- [適配器開發入門](getting-started.md) - 建立第一個適配器
- [適配器核心概念](core-concepts.md) - 瞭解適配器架構
- [SendDSL 詳解](send-dsl.md) - 學習訊息發送



### 事件转换器

# 事件轉換器實現指南

事件轉換器 (Converter) 是適配器的核心組件之一，負責將平台原生事件轉換為 ErisPulse 統一的 OneBot12 標準事件格式。

## Converter 職責

```
平台原生事件 ──→ Converter.convert() ──→ OneBot12 標準事件
```

Converter 只負責**正向轉換**（接收方向），即將平台的原生事件資料轉換為 OneBot12 標準格式。反向轉換（發送方向）由 `Send.Raw_ob12()` 方法處理。

### 核心原則

1. **無損轉換**：原始資料必須完整保留在 `{platform}_raw` 欄位中
2. **標準相容**：轉換後的事件必須符合 OneBot12 標準格式
3. **平台擴展**：平台特有的資料使用 `{platform}_` 前綴欄位儲存

## BaseConverter 基類（推薦）

從 2.7.0 開始，框架提供 `BaseConverter` 基類（`ErisPulse.Core.Bases`），封裝 OneBot12 事件的**公共欄位建構**與**常用訊息段輔助**，讓轉換器只需聚焦類型映射：

```python
from ErisPulse.Core.Bases import BaseConverter


class MyConverter(BaseConverter):
    def __init__(self):
        super().__init__(platform="myplatform")

    def convert(self, raw_event: dict) -> dict | None:
        if not isinstance(raw_event, dict):
            return None
        event_type = raw_event.get("type", "")
        base = self.build_base_event(raw_event, event_type)  # id/time/platform/self/raw
        if event_type == "message":
            base["type"] = "message"
            base["detail_type"] = "group" if raw_event.get("group_id") else "private"
            base["user_id"] = str(raw_event.get("sender_id", ""))
            base["message"] = [self.text(raw_event.get("content", ""))]
            base["alt_message"] = raw_event.get("content", "")
            return base
        return None
```

`build_base_event()` 已填入的公共欄位：

| 欄位 | 來源 |
|------|------|
| `id` | `raw_event["event_id"]`，缺省自动生成 UUID |
| `time` | `raw_event["timestamp"]`，缺省當前時間 |
| `platform` | 建構時傳入的 `platform` |
| `self` | `{"platform": ..., "user_id": raw_event["bot_id"]}` |
| `{platform}_raw` | 原始事件（滿足"無損轉換"原則） |
| `{platform}_raw_type` | 原始事件類型 |

常用訊息段輔助方法（均為靜態方法，可直接重用）：

```python
converter.text("hi")          # {"type": "text", "data": {"text": "hi"}}
converter.at("123456")        # {"type": "at", "data": {"user_id": "123456"}}
converter.image("file.png")   # {"type": "image", "data": {"file": "file.png"}}
```

> 手動實現時 `build_base_event` 的公共欄位建構是必須重複撰寫的樣板程式碼，使用 `BaseConverter` 可省去這部分，且天然滿足"無損轉換"（原始事件始終進 `{platform}_raw`）。

## convert() 方法

### 方法簽名

```python
def convert(self, raw_event: dict) -> dict:
    """
    將平台原生事件轉換為 OneBot12 標準格式

    :param raw_event: 平台原生事件數據
    :return: OneBot12 標準格式事件字典
    """
    pass
```

### 返回值結構

轉換後的事件字典應包含以下標準字段：

```python
{
    "id": "事件唯一ID",
    "time": 1234567890,           # Unix 時間戳（秒）
    "type": "message",             # 事件類型
    "detail_type": "private",      # 詳細類型
    "platform": "myplatform",      # 平台名稱
    "self": {
        "platform": "myplatform",
        "user_id": "bot_user_id"
    },

    # 消息事件字段
    "user_id": "sender_id",
    "message": [...],              # OneBot12 消息段列表
    "alt_message": "純文字內容",

    # 必須保留原始數據
    "myplatform_raw": { ... },     # 平台原生事件完整數據
    "myplatform_raw_type": "原生事件類型名",
}
```

## 必填字段映射

### 通用字段（所有事件類型）

| OB12 字段 | 類型 | 說明 |
|-----------|------|------|
| `id` | str | 事件唯一標識符 |
| `time` | int | Unix 時間戳（秒） |
| `type` | str | 事件類型：`message` / `notice` / `request` / `meta` |
| `detail_type` | str | 詳細類型：`private` / `group` / `friend` 等 |
| `platform` | str | 平台名稱，與適配器註冊名一致 |
| `self` | dict | 機器人資訊：`{"platform": "...", "user_id": "..."}` |

### 消息事件額外字段

| OB12 字段 | 類型 | 說明 |
|-----------|------|------|
| `user_id` | str | 發送者 ID |
| `message` | list[dict] | OneBot12 消息段列表 |
| `alt_message` | str | 純文字備用內容 |

### 通知事件額外字段

| OB12 字段 | 類型 | 說明 |
|-----------|------|------|
| `user_id` | str | 相關使用者 ID |
| `operator_id` | str | 操作者 ID（如群成員變動） |

## 消息段轉換

OneBot12 標準定義了以下消息段類型：

```python
# 文本
{"type": "text", "data": {"text": "Hello"}}

# 圖片
{"type": "image", "data": {"file": "https://example.com/img.jpg"}}

# 音頻
{"type": "audio", "data": {"file": "https://example.com/audio.mp3"}}

# 視頻
{"type": "video", "data": {"file": "https://example.com/video.mp4"}}

# 文件
{"type": "file", "data": {"file": "https://example.com/doc.pdf"}}

# @提及
{"type": "mention", "data": {"user_id": "123"}}

# @全體
{"type": "mention_all", "data": {}}

# 回覆
{"type": "reply", "data": {"message_id": "msg_123"}}
```

如果平台有不支援的消息段類型，可以省略該段或轉換為最接近的標準類型。

## 平台擴展欄位

平台特有的資料應使用 `{platform}_` 前綴儲存，以避免與標準欄位衝突：

```python
{
    # 標準欄位
    "type": "message",
    "detail_type": "group",
    # ...

    # 平台擴展欄位
    "myplatform_raw": { ... },          # 原始事件資料（必須）
    "myplatform_raw_type": "chat",      # 原始事件類型（必須）

    # 其他平台特有欄位
    "myplatform_group_name": "群組名稱",
    "myplatform_sender_role": "admin",
}
```

> **重要**：`{platform}_raw` 欄位是必須的，ErisPulse 的事件系統和模組可能依賴它來存取平台原始資料。

## 完整範例

以下是一個完整的 Converter 實作範例：

```python
class MyConverter:
    def __init__(self, platform: str):
        self.platform = platform

    def convert(self, raw_event: dict) -> dict:
        event_type = raw_event.get("type", "")

        base_event = {
            "id": raw_event.get("id", ""),
            "time": raw_event.get("timestamp", 0),
            "platform": self.platform,
            "self": {
                "platform": self.platform,
                "user_id": raw_event.get("self_id", ""),
            },
            "myplatform_raw": raw_event,
            "myplatform_raw_type": event_type,
        }

        if event_type == "chat":
            return self._convert_message(raw_event, base_event)
        elif event_type == "notification":
            return self._convert_notice(raw_event, base_event)
        elif event_type == "request":
            return self._convert_request(raw_event, base_event)

        return base_event

    def _convert_message(self, raw: dict, base: dict) -> dict:
        base["type"] = "message"
        base["detail_type"] = "group" if raw.get("group_id") else "private"
        base["user_id"] = raw.get("sender_id", "")
        base["message"] = self._convert_message_segments(raw.get("content", ""))
        base["alt_message"] = raw.get("content", "")

        if raw.get("group_id"):
            base["group_id"] = raw["group_id"]

        return base

    def _convert_message_segments(self, content: str) -> list:
        segments = []
        if content:
            segments.append({"type": "text", "data": {"text": content}})
        return segments

    def _convert_notice(self, raw: dict, base: dict) -> dict:
        base["type"] = "notice"
        notification_type = raw.get("notification_type", "")

        if notification_type == "member_join":
            base["detail_type"] = "group_member_increase"
            base["user_id"] = raw.get("user_id", "")
            base["group_id"] = raw.get("group_id", "")
            base["operator_id"] = raw.get("operator_id", "")
        elif notification_type == "friend_add":
            base["detail_type"] = "friend_increase"
            base["user_id"] = raw.get("user_id", "")

        return base

    def _convert_request(self, raw: dict, base: dict) -> dict:
        base["type"] = "request"
        request_type = raw.get("request_type", "")

        if request_type == "friend":
            base["detail_type"] = "friend"
            base["user_id"] = raw.get("user_id", "")
            base["comment"] = raw.get("message", "")
        elif request_type == "group_invite":
            base["detail_type"] = "group"
            base["group_id"] = raw.get("group_id", "")
            base["user_id"] = raw.get("inviter_id", "")

        return base
```

## 富媒體消息轉換示例

實際平台的消息通常包含圖片、@提及、回覆等富媒體內容。以下是 `_convert_message_segments` 處理多種消息類型的示例：

```python
def _convert_message_segments(self, raw_content: list) -> list:
    """將平台原生消息段列表轉換為 OneBot12 標準消息段"""
    segments = []

    for item in raw_content:
        item_type = item.get("type", "")

        if item_type == "text":
            segments.append({
                "type": "text",
                "data": {"text": item.get("content", "")}
            })

        elif item_type == "image":
            file_url = item.get("url") or item.get("file_id", "")
            segments.append({
                "type": "image",
                "data": {"file": file_url}
            })

        elif item_type == "at":
            segments.append({
                "type": "mention",
                "data": {"user_id": item.get("target_id", "")}
            })

        elif item_type == "reply":
            segments.append({
                "type": "reply",
                "data": {"message_id": item.get("reply_to_id", "")}
            })

        elif item_type == "at_all":
            segments.append({"type": "mention_all", "data": {}})

        else:
            segments.append({
                "type": "text",
                "data": {"text": f"[不支援的消息類型: {item_type}]"}
            })

    return segments
```

## 常見陷阱

### 1. 缺少 `{platform}_raw` 字段

這是常見的錯誤。缺少原始資料字段會導致模組無法存取平台特有的資訊。

```python
base_event["myplatform_raw"] = raw_event        # 必須！
base_event["myplatform_raw_type"] = event_type   # 必須！
```

### 2. 時間戳格式錯誤

OneBot12 標準要求 `time` 欄位為 Unix 秒級時間戳（整數）。如果你的平台回傳毫秒時間戳或 ISO 格式字串，需要轉換：

```python
import time

# 毫秒 → 秒
"time": raw_event.get("timestamp", 0) // 1000

# ISO 字串 → 秒
"time": int(time.mktime(time.strptime(raw_event["created_at"], "%Y-%m-%dT%H:%M:%S")))
```

### 3. 缺少 `self` 欄位

`self` 欄位包含機器人自身資訊，`user_id` 為機器人的帳號 ID。多 Bot 場景下此欄位至關重要：

```python
"self": {
    "platform": self.platform,
    "user_id": raw_event.get("bot_id", ""),   # 機器人自身的 ID
}
```

### 4. detail_type 使用了非標準值

`detail_type` 必須使用 OneBot12 標準定義的值，如 `private`、`group`、`friend_increase`、`group_member_increase` 等。不要使用平台特有的命名。

### 5. 往返一致性

確保 Converter 產生的消息段類型與 Send 端支援的方法對應。例如，如果 Converter 將平台的圖片訊息轉換為 `{"type": "image", ...}`，那麼 Send 端的 `Image()` 方法必須能處理圖片傳送。

## 最佳實踐

1. **始終保留原始資料**：`{platform}_raw` 欄位不能省略
2. **使用標準訊息段**：盡量將平台訊息轉換為 OneBot12 標準訊息段
3. **合理設定 detail_type**：使用標準類型（`private`/`group`/`channel` 等），不要自訂
4. **處理邊界情況**：原始事件可能缺少某些欄位，使用 `.get()` 並提供合理的預設值
5. **效能考量**：`convert()` 在每個事件上被呼叫，避免在其中執行耗時操作

## 相關文件

- [適配器核心概念](core-concepts.md) - 適配器整體架構
- [SendDSL 詳解](send-dsl.md) - 反向轉換（發送方向）
- [事件轉換標準](../../standards/event-conversion.md) - 正式的事件轉換規範
- [會話類型系統](../../standards/session-types.md) - 會話類型映射規則



### 发布与模块商店指南

# 發布與模組商店指南

將你開發的模組或適配器發布到 ErisPulse 模組商店，讓其他使用者可以方便地發現和安裝。

## 模組商店概述

ErisPulse 模組商店是一個集中式的模組註冊表，使用者可以透過 CLI 工具瀏覽、搜尋和安裝社群貢獻的模組、適配器。

### 瀏覽與發現

```bash
# 列出遠端可用的所有套件
epsdk list-remote

# 只查看模組
epsdk list-remote -t modules

# 只查看適配器
epsdk list-remote -t adapters

# 強制刷新遠端套件列表
epsdk list-remote -r
```

你也可以訪問 [ErisPulse 官網](https://www.erisdev.com/#market) 在線瀏覽模組商店。

### 支援的提交類型

| 類型 | 說明 | Entry-point 組 |
|------|------|----------------|
| 模組 | 擴充機器人功能、實現業務邏輯 | `erispulse.module` |
| 適配器 | 連接新的訊息平台 | `erispulse.adapter` |

## 快速發布

整個過程只需要三步：配置專案 → 發布到 PyPI → 提交到模組商店。

### 1. 配置 pyproject.toml

確保專案目錄包含 `pyproject.toml`、`README.md`，並根據類型配置 entry-points：

#### 模組

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
description = "模組功能描述"
requires-python = ">=3.10"
license = { text = "MIT" }
authors = [ { name = "yourname" } ]
dependencies = [
    "ErisPulse>=2.0.0",
]

[project.entry-points."erispulse.module"]
"MyModule" = "MyModule:Main"
```

#### 適配器

```toml
[project]
name = "ErisPulse-MyAdapter"
version = "1.0.0"
description = "適配器功能描述"
requires-python = ">=3.10"

[project.entry-points."erispulse.adapter"]
"myplatform" = "MyAdapter:MyAdapter"
```

> **注意**：套件名建議以 `ErisPulse-` 開頭，便於使用者識別。Entry-point 的鍵名（如 `"MyModule"`）將作為模組在 SDK 中的存取名稱。

### 2. 發布到 PyPI

```bash
# 建構 + 發布（需要 PyPI 帳號）
pip install build twine
python -m build
python -m twine upload dist/*
```

發布成功後驗證安裝：

```bash
pip install ErisPulse-MyModule
```

### 3. 提交到模組商店

前往 [ErisPulse 模組商店](https://www.erisdev.com/#market)，點擊「提交模組」，登入後填寫模組資訊即可。

支援的登入方式：**GitHub**、**Codeberg**、**雲湖**，任選其一即可。

填寫重點：
- 模組名稱、描述、倉庫地址
- 最低 SDK 版本：如果不确定，填寫 [ErisPulse 最新發行版](https://pypi.org/project/ErisPulse/) 版本號即可

提交後立即生效，使用者可透過模組源安裝。模組會被標記為「未驗證」，維護者審核通過後改為「已驗證」。

> **關於驗證狀態**：
> - 「未驗證」僅表示尚未經過官方審核，不代表模組有問題
> - 使用者透過 `epsdk install` 安裝未驗證模組時會收到風險提示，需確認後才可繼續安裝

### 4. 管理已發布的模組

在模組商店點擊「提交模組」並登入後，切換到「我的模組」標籤頁，可以：

- **編輯** — 修改模組描述、倉庫地址、標籤等資訊，版本號會自動從 PyPI 同步
- **刪除** — 從模組商店移除模組（不可撤銷）

> 剛提交的模組可能需要幾分鐘才會顯示在「我的模組」列表中。

## 更新已發布模組

1. 更新 `pyproject.toml` 中的 `version`
2. 重新建構並上傳：`python -m build && python -m twine upload dist/*`
3. 模組商店會自動同步 PyPI 上的最新版本

使用者透過 `epsdk upgrade MyModule` 即可升級。

## 發布前檢查清單

在推送到 PyPI 之前，請逐項確認以下內容：

### 代碼品質

- [ ] 所有公開 API 有型別註解（函數簽名和返回值）
- [ ] 所有公開方法有文件字串（`"""..."""` 格式，包含 `:param` / `:return` / `:raises`）
- [ ] 透過 `ruff check`（無警告）
- [ ] 測試覆蓋率 ≥ 80%
- [ ] 透過 `pytest` 全部用例

### 相容性

- [ ] `pyproject.toml` 宣告了最低 SDK 版本：`dependencies = ["ErisPulse>=x.y.z"]`
- [ ] 測試了 Python 3.10 / 3.11 / 3.12 / 3.13
- [ ] 測試了目標作業系統（Windows / Linux / macOS，如適用）
- [ ] 無循環匯入依賴

### 配置

- [ ] 如果使用宣告式配置（`ConfigClass` + `BaseConfig` / `BotAccountConfig`），配置欄位有 `description`（推薦 i18n 格式）和 `ui` 元數據
- [ ] 如果註冊了 i18n 翻譯鍵，已覆蓋所有 5 種語言（zh-CN / zh-TW / en / ja / ru）
- [ ] 敏感欄位標記了 `secret=True`

### 文件

- [ ] `README.md` 有安裝說明和基本使用範例
- [ ] `README.md` 說明了配置方式（配置檔案範例 + 環境變數）
- [ ] `CHANGELOG.md` 記錄了所有變更
- [ ] 適配器更新了平台特性文件（支援的 Send 類型、事件類型等）

### 發布

- [ ] `pyproject.toml` 版本號已更新
- [ ] 建構透過：`python -m build`
- [ ] 已推送到 PyPI：`python -m twine upload dist/*`
- [ ] 安裝驗證透過：`pip install ErisPulse-xxx && epsdk run`

## 開發模式測試

在正式發布前，可以使用可編輯模式在本地測試：

```bash
epsdk install -e /path/to/MyModule
# 或
pip install -e /path/to/MyModule
```

## 常見問題

### 套件名必須以 `ErisPulse-` 開頭嗎？

不強制，但強烈推薦。這有助於使用者在 PyPI 上識別 ErisPulse 生態的套件。

### 一個套件可以註冊多個模組嗎？

可以。在 `entry-points` 中配置多個鍵值對即可：

```toml
[project.entry-points."erispulse.module"]
"ModuleA" = "MyPackage:ModuleA"
"ModuleB" = "MyPackage:ModuleB"
```

### 審核需要多久時間？

通常在 1-3 個工作日內完成。你可以在模組商店「我的模組」中查看驗證狀態。

## 透過 Docker 映像分發應用

如果你的應用不適合發布到 PyPI（如包含私有依賴、需要預配置環境），可以透過 **GitHub Container Registry (GHCR)** 發布 Docker 映像，讓其他使用者 `docker pull` 一鍵啟動。

### 適用場景

- 你有一個**完整的機器人應用**（模組 + 配置 + 入口腳本），想一鍵分發
- 模組/適配器依賴**私有包**或有特殊安裝流程，不適合 PyPI
- 想提供**開箱即用**的部署方案，降低使用者使用門檻

### 1. 建立 Dockerfile

基於 ErisPulse 官方映像建構，只需新增你的模組即可：

```dockerfile
FROM erispulse/erispulse:latest

LABEL org.opencontainers.image.title="ErisPulse-MyModule" \
      org.opencontainers.image.description="模組描述" \
      org.opencontainers.image.url="https://github.com/yourname/ErisPulse-MyModule" \
      org.opencontainers.image.source="https://github.com/yourname/ErisPulse-MyModule"

COPY pyproject.toml README.md ./
COPY MyModule/ ./MyModule/

RUN uv pip install --system -e .
```

如果模組需要額外的系統依賴（如 SSH 用戶端等），在 `RUN uv pip install` 之後新增：

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*
```

> `erispulse/erispulse:latest` 已包含 ErisPulse、ErisPulse-Dashboard、Python 執行時和 uv，無需重複安裝。

### 2. 建立 GitHub Actions 工作流程

在 `.github/workflows/docker-publish.yml` 中建立：

```yaml
name: 發布 Docker 映像

on:
  workflow_dispatch:
  push:
    branches:
      - main
    tags:
      - "v*"

permissions:
  contents: read
  packages: write

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository_owner }}/my-bot

jobs:
  docker-publish:
    runs-on: ubuntu-latest

    steps:
      - name: 檢出代碼
        uses: actions/checkout@v4

      - name: 設置 QEMU (多架構支援)
        uses: docker/setup-qemu-action@v3

      - name: 設置 Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: 登入 GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: 提取 Docker 元數據
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=raw,value=latest

      - name: 建構並推送 Docker 映像
        uses: docker/build-push-action@v6
        with:
          context: .
          file: ./Dockerfile
          platforms: linux/amd64,linux/arm64
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

> `GITHUB_TOKEN` 由 GitHub Actions 自動提供，無需手動建立金鑰。

### 3. 觸發建構

推送代碼或打 Tag 即可自動建構：

```bash
# 推送到 main 分支觸發
git push origin main

# 或打 Tag 觸發
git tag v1.0.0
git push origin v1.0.0
```

也可在 GitHub 倉庫的 **Actions** 頁面手動觸發。

### 4. 設置映像為公開

GHCR 映像預設為 **private**，需要在 GitHub 設置為 Public 後其他使用者才能免登入拉取：

1. 進入倉庫 → **Packages** → 點擊對應 Package
2. **Package settings** → **Danger Zone** → **Change visibility** → **Public**

### 5. 使用者使用

建構完成後，使用者可以用 `docker run` 一行啟動：

```bash
docker run -d \
  --name my-bot \
  -p 8000:8000 \
  -v $(pwd)/config:/app/config \
  -e TZ=Asia/Shanghai \
  -e ERISPULSE_DASHBOARD_TOKEN=your-token \
  --restart unless-stopped \
  ghcr.io/<your-username>/my-bot:latest
```

或使用 `docker-compose.yml`：

```yaml
services:
  my-bot:
    image: ghcr.io/<your-username>/my-bot:latest
    container_name: my-bot
    ports:
      - "8000:8000"
    volumes:
      - ./config:/app/config
    environment:
      - TZ=Asia/Shanghai
      - ERISPULSE_DASHBOARD_TOKEN=${ERISPULSE_DASHBOARD_TOKEN:-}
    restart: unless-stopped
```

### 同時發布到 Docker Hub

擴充工作流程，在登入步驟前新增 Docker Hub 登入，並在 `images` 中新增 Docker Hub 位址：

```yaml
      - name: 登入 Docker Hub
        uses: docker/login-action@v3
        with:
          registry: docker.io
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: 提取 Docker 元數據
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: |
            docker.io/<your-dockerhub-username>/my-bot
            ghcr.io/${{ github.repository_owner }}/my-bot
```

> 需要在倉庫 **Settings → Secrets** 中新增 `DOCKERHUB_USERNAME` 和 `DOCKERHUB_TOKEN`。

### Docker 映像 vs PyPI 發布

| 特性 | Docker 映像 (GHCR) | PyPI 發布 |
|------|---------------------|-----------|
| 分發方式 | `docker pull` 一鍵執行 | `pip install` + 手動配置 |
| 適用範圍 | 完整應用/解決方案 | 單一模組/適配器 |
| 私有依賴 | 天然支援 | 需要私有 PyPI 源 |
| 模組商店 | 不適用 | 可提交到模組商店 |
| 多架構 | 支援 amd64/arm64 | 與架構無關 |

兩種方式不衝突——你可以同時透過 PyPI 發布模組到模組商店，又透過 GHCR 提供開箱即用的 Docker 映像。



======
API 参考
======


### 核心模块 API

# 核心模組 API

本文檔提供 ErisPulse 核心模組的 API 快速參考，包含方法簽名和簡要說明。詳細用法和範例請點擊各模組的「完整文件」連結。

## Storage 模組

基於 SQLite 的鍵值儲存系統，支援通用 SQL 串接查詢。

### 基本操作

```python
from ErisPulse import sdk

sdk.storage.set("key", "value")
value = sdk.storage.get("key", default_value)
keys = sdk.storage.keys()
sdk.storage.delete("key")
```

### 批次操作

```python
sdk.storage.set_multi({"key1": "val1", "key2": "val2"})
values = sdk.storage.get_multi(["key1", "key2"])
sdk.storage.delete_multi(["key1", "key2"])
```

### 事務操作

```python
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
```

### 屬性存取

```python
sdk.storage.my_key          # 等同於 sdk.storage.get("my_key")
sdk.storage.my_key = "val"  # 等同於 sdk.storage.set("my_key", "val")
```

### SQL 串接查詢

Storage 模組提供串接呼叫風格的通用 SQL 查詢建構器，支援自訂表格的 CRUD 操作。

```python
sdk.storage.CreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
})

sdk.storage.Table("users").Insert({"name": "Alice"}).Execute()
rows = sdk.storage.Table("users").Select("name").Where("id > ?", 0).Execute()
```

> 完整的串接查詢 API（Select/Insert/Update/Delete/Where/OrderBy/Limit、AlterTable、事務等）請參考 [SQL 查詢建構器](../advanced/sql-builder.md)。

### 儲存後端抽象

`StorageManager` 繼承自 `BaseStorage` 抽象基類，支援擴展其他儲存介質（Redis、MySQL 等）。

```python
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder
```

### 異步介面

Storage 和 Config 模組均提供異步方法（前綴 `a`），可在異步處理器中安全呼叫。同步方法繼續保留，無需修改現有程式碼。

```python
# 異步儲存
value = await sdk.storage.aget("key")
await sdk.storage.aset("key", "value")
await sdk.storage.adelete("key")
keys = await sdk.storage.aget_all_keys()
await sdk.storage.aclear()

# 異步批次操作
values = await sdk.storage.aget_multi(["k1", "k2"])
await sdk.storage.aset_multi({"k1": "v1", "k2": "v2"})
await sdk.storage.adelete_multi(["k1", "k2"])

# 異步配置
value = await sdk.config.agetConfig("MyModule.key")
await sdk.config.asetConfig("MyModule.key", "value")
await sdk.config.aforce_save()
await sdk.config.areload()
```

## Config 模組

以 TOML 格式管理配置文件，支援點號分隔的鍵路徑。

### API 概覽

| 方法 | 說明 |
|------|------|
| `getConfig(key, default)` | 讀取配置，支援點號路徑如 `"MyModule.subkey"` |
| `setConfig(key, value, immediate=False)` | 寫入配置。`immediate=True` 時立即儲存到檔案 |
| `force_save()` | 強制將記憶體中的配置寫入檔案 |
| `reload()` | 從檔案重新載入配置 |
| `agetConfig(key, default)` | 異步讀取配置 |
| `asetConfig(key, value, immediate)` | 異步寫入配置 |
| `aforce_save()` | 異步強制儲存 |
| `areload()` | 異步重新載入 |

### 範例

```python
config = sdk.config.getConfig("MyModule", {})
value = sdk.config.getConfig("MyModule.timeout", 30)

sdk.config.setConfig("MyModule", {"key": "value"})
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)
```

> `setConfig` 預設採用延遲寫入（每 5 秒批量儲存），設定 `immediate=True` 可立即持久化到配置檔案。配置變更會觸發 `config.set` 生命週期事件。

## Logger 模組

模組化日誌系統，基於 Rich 輸出，支援子日誌器和模組層級控制。

### 基本用法

```python
sdk.logger.debug("調試資訊")
sdk.logger.info("執行資訊")
sdk.logger.warning("警告資訊")
sdk.logger.error("錯誤資訊")
sdk.logger.critical("致命錯誤")
```

### 子日誌器

```python
child_logger = sdk.logger.get_child("MyModule")
child_logger.info("子模組日誌")

child_logger.get_child("utils")  # 支援嵌套
```

### 日誌層級控制

```python
sdk.logger.set_level("DEBUG")                          # 全域層級
sdk.logger.set_module_level("MyModule", "DEBUG")       # 模組層級

# 支援的層級（由低至高）：
# TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL
# TRACE 為最低層級，輸出框架內部詳細調試資訊（事件分發、路由註冊等）
sdk.logger.set_level("TRACE")                          # 開啟全部日誌
```

### 日誌訂閱（推模式）

供 Dashboard 等模組即時接收結構化日誌，支援層級篩選和歷史補發。

> **顯式訂閱低層級日誌**：訂閱器的 `min_level` 可低於全域日誌層級。此時低層級日誌**僅推送到符合條件的訂閱器**，不會輸出到控制台，也不會寫入記憶體，從而避免污染主日誌流。
>
> ```python
> # 全域為 INFO，仍可單獨訂閱 DEBUG 日誌
> @sdk.logger.handler("debug-tracer", min_level="DEBUG")
> def on_debug(log_data: dict): ...
> ```

```python
# 裝飾器方式
@sdk.logger.handler("my-handler", min_level="INFO")
def on_log(log_data: dict):
    # log_data = {
    #     "timestamp": "2026-06-29T22:00:00.123456",
    #     "level": "WARNING", "level_num": 30,
    #     "module": "ErisPulse.Core.adapter",
    #     "message": "嚴格模式：...",
    # }
    pass

# 直接呼叫方式
sdk.logger.handler("my-handler", min_level="INFO")(on_log)
sdk.logger.remove_handler("my-handler")
```

| 方法 | 說明 |
|------|------|
| `handler(id, *, min_level)(func)` | 裝飾器/直接呼叫兩用。`id` 為空時取函數名。`min_level` 可低於全域層級（低層級日誌僅推送訂閱器，不進控制台/記憶體）。註冊時自動補發歷史日誌 |
| `remove_handler(id)` | 移除訂閱器 |

### 輸出控制

```python
sdk.logger.set_output_file("app.log")
sdk.logger.save_logs("log.txt")
sdk.logger.get_logs("MyModule")
sdk.logger.set_memory_limit(1000)
```

## Adapter 模組

適配器管理器，管理多平台適配器的註冊、啟動和關閉。

### API 概覽

| 方法 | 說明 |
|------|------|
| `get(platform)` | 獲取適配器實例 |
| `exists(platform)` | 檢查適配器是否已註冊 |
| `enable(platform)` / `disable(platform)` | 啟用/禁用適配器 |
| `is_enabled(platform)` | 檢查是否啟用 |
| `startup(platforms)` / `shutdown(platforms)` | 啟動/關閉適配器 |
| `is_running(platform)` | 檢查適配器是否正在運行 |
| `list_running()` | 列出所有正在運行的適配器 |
| `platforms` | 獲取所有平台名稱列表 |

### 適配器事件

```python
@sdk.adapter.on("message")
async def handle_message(event):
    pass

@sdk.adapter.on("message", platform="yunhu")
async def handle_yunhu_message(event):
    pass
```

### Bot 狀態查詢

```python
sdk.adapter.get_bot_info("telegram", "123456")
sdk.adapter.list_bots("telegram")
sdk.adapter.is_bot_online("telegram", "123456")
sdk.adapter.get_status_summary()
```

> 完整的適配器管理 API 請參考 [適配器系統 API](adapter-system.md)。

## Module 模塊

模組管理器，管理插件的註冊、載入和卸載。

### API 概覽

| 方法 | 說明 |
|------|------|
| `get(name)` | 取得模組實例或懶加載代理（已註冊但未載入時返回代理） |
| `exists(name)` | 檢查是否已註冊 |
| `is_loaded(name)` | 檢查是否已載入 |
| `is_enabled(name)` | 檢查是否啟用 |
| `enable(name)` / `disable(name)` | 啟用/停用模組 |
| `load(name)` / `unload(name)` | 載入/卸載模組 |
| `list_registered()` | 列出已註冊模組 |
| `list_loaded()` | 列出已載入模組 |
| `get_info(name)` | 取得模組資訊 |
| `get_status_summary()` | 取得模組狀態摘要 |

### 屬性存取

```python
module = sdk.module.get("ModuleName")
module = sdk.module.ModuleName
module = sdk.ModuleName  # 等價快捷方式
```

## Lifecycle 模塊

事件驅動的生命周期管理器，提供事件提交和監聽功能。

### API 概覽

| 方法 | 說明 |
|------|------|
| `on(event, priority=0)` | 裝飾器註冊事件處理器，支援點號匹配和通配符 `*` |
| `register(event, handler, priority=0)` | 函數式註冊處理器 |
| `unregister(event, handler=None)` | 移除處理器 |
| `emit(event, data)` | 異步觸發事件 |
| `emit_sync(event, data)` | 同步觸發事件 |
| `submit_event(event_type, msg, data, source)` | 提交標準格式事件（相容舊版） |
| `start_timer(id)` / `stop_timer(id)` | 性能計時器 |

### 範例

```python
@sdk.lifecycle.on("module.init")
async def handle_module_init(event_data):
    print(f"模組初始化: {event_data}")

@sdk.lifecycle.on("module")
async def handle_any_module_event(event_data):
    print(f"模組事件: {event_data}")

await sdk.lifecycle.emit("custom.event", {"key": "value"})
```

> 完整的標準事件列表和詳細用法請參考 [生命周期管理](../advanced/lifecycle.md)。

## Router 模組

HTTP/WebSocket 路由管理器，基於 FastAPI + Uvicorn，支援裝飾器路由、中間件、分組、限流、CORS。

> 完整的路由 API 文件（裝飾器路由、WebSocket、中間件、速率限制、CORS、安全標頭等）請參考 [路由管理器](../advanced/router.md)。

### 快速參考

```python
# HTTP 路由
@sdk.router.get("MyModule", "/api")
async def handler(request: HttpRequest):
    return {"status": "ok"}

# WebSocket 路由
@sdk.router.ws("MyModule", "/ws")
async def ws_handler(ws: WebSocketConnection):
    async for text in ws.iter_text():
        await ws.send_text(f"Echo: {text}")

# 路由分組
group = sdk.router.group("MyModule", prefix="/v1")
@group.get("/users")
async def list_users(request: HttpRequest):
    return {"users": []}
```

## HTTP Client 模組

統一網路客戶端，聚合 HTTP 請求、WebSocket 連接、連接池管理、自動重試、請求統計和生命週期事件整合。

> 完整的網路客戶端文件（請求方法、回應物件、WebSocket 客戶端、例外體系等）請參考 [網路客戶端](../advanced/http-client.md)。

### 快速參考

```python
from ErisPulse.Core import client

# HTTP 請求
resp = await client.get("https://api.example.com/users")
data = await resp.json()

# WebSocket
ws = await client.ws_connect("wss://example.com/ws")
async for text in ws.iter_text():
    await ws.send_text(f"Echo: {text}")
```

## SDK 調試

### dump_state()

匯出框架當前運行狀態的快照，用於調試和診斷。

```python
import json
state = sdk.dump_state()
print(json.dumps(state, indent=2, ensure_ascii=False, default=str))
```

返回結構包含以下子系統的狀態：

| 字段 | 說明 |
|------|------|
| `sdk` | SDK 初始化狀態、Python 版本、運行平台、時間戳 |
| `adapters` | 已註冊/已啟動的適配器列表、各平台 Bot 在線狀態 |
| `modules` | 已註冊/已啟用/已禁用/懶加載的模塊列表 |
| `events` | 各類事件處理程序數量（message/notice/request/meta/commands） |
| `router` | 伺服器運行狀態、HTTP/WebSocket 路由數量 |

> 新增於 2.5.2

## 相關文件

- [事件系統 API](event-system.md) - Event 模組 API
- [適配器系統 API](adapter-system.md) - Adapter 管理 API
- [SQL 查詢建構器](../advanced/sql-builder.md) - SQL 鏈式查詢完整文件
- [路由管理器](../advanced/router.md) - 路由管理器完整文件
- [網路用戶端](../advanced/http-client.md) - 網路用戶端完整文件
- [生命週期管理](../advanced/lifecycle.md) - 生命週期完整文件



### 事件系统 API

# 事件系統 API

本文檔詳細介紹了 ErisPulse 事件系統的 API。

事件系統將平台事件按類型分發到五類處理器：

```mermaid
flowchart LR
    A["平台事件<br/>（OneBot12 標準）"] --> B{"事件類型"}
    B --> C["command<br/>命令處理器"]
    B --> D["message<br/>消息處理器"]
    B --> E["notice<br/>通知處理器"]
    B --> F["request<br/>請求處理器"]
    B --> G["meta<br/>元事件處理器"]
    C & D & E & F & G --> H["Event 包裝類<br/>reply / get_text / done 等"]
```

## Command 命令模組

### 註冊命令

```python
from ErisPulse.Core.Event import command

# 基本命令
@command("hello", help="發送問候")
async def hello_handler(event):
    await event.reply("你好！")

# 帶別名的命令
@command(["help", "h"], aliases=["幫助"], help="顯示幫助")
async def help_handler(event):
    pass

# 帶權限的命令
def is_admin(event):
    return event.get("user_id") in admin_ids

@command("admin", permission=is_admin, help="管理員命令")
async def admin_handler(event):
    pass

# 隱藏命令
@command("secret", hidden=True, help="秘密命令")
async def secret_handler(event):
    pass

# 命令組
@command("admin.reload", group="admin", help="重新載入模組")
async def reload_handler(event):
    pass
```

### 命令資訊

所有命令查詢 API 均支援可選的**會話上下文**：傳 `event=`（Event 或 dict）或
顯式 `platform=` / `bot_id=` / `session_id=`（與 event 叠加時顯式參數優先），
即按控制面模組維度過濾當前會話不可用模組的命令（詳見 advanced/scope.md）；
全部為可選關鍵字參數，不傳時保持原有全量行為。

```python
# 獲取命令幫助
help_text = command.help()

# 會話感知幫助：只列出當前會話可用的命令
help_text = command.help(event=event)

# 獲取特定命令（返回合併覆蓋後的生效參數；會話不可用時返回 None）
cmd_info = command.get_command("admin")
cmd_info = command.get_command("admin", event=event)

# 獲取所有命令（會話感知時過濾不可用模組的命令）
all_commands = command.get_commands()
all_commands = command.get_commands(event=event)

# 獲取命令組中的所有命令（支援會話感知過濾）
admin_commands = command.get_group_commands("admin")
admin_commands = command.get_group_commands("admin", event=event)

# 獲取所有可見命令
visible_commands = command.get_visible_commands()

# 會話感知的可見命令（event 或顯式關鍵字任一即可）
visible_commands = command.get_visible_commands(event=event)
visible_commands = command.get_visible_commands(
    platform=event.get("platform"),
    bot_id=event.get_self_account_id(),
    session_id=event.get_session_id(),
)
```

### 等待回覆

```python
# 等待使用者回覆
@command("ask", help="詢問使用者資訊")
async def ask_command(event):
    reply = await command.wait_reply(
        event,
        prompt="請輸入你的名字:",  # 已在上面發送
        timeout=30.0
    )
    
    if reply:
        name = reply.get_text()
        await event.reply(f"你好，{name}！")

# 帶驗證的等待回覆
def validate_age(event_data):
    try:
        age = int(event_data.get_text())
        return 0 <= age <= 150
    except ValueError:
        return False

@command("age", help="詢問使用者年齡")
async def age_command(event):
    await event.reply("請輸入你的年齡:")
    
    reply = await command.wait_reply(
        event,
        timeout=60,
        validator=validate_age
    )
    
    if reply:
        age = int(reply.get_text())
        await event.reply(f"你的年齡是 {age} 歲")

# 帶回調的等待回覆
async def handle_confirmation(reply_event):
    text = reply_event.get_text().lower()
    if text in ["是", "yes", "y"]:
        await event.reply("操作已確認！")
    else:
        await event.reply("操作已取消。")

@command("confirm", help="確認操作")
async def confirm_command(event):
    await command.wait_reply(
        event,
        prompt="請輸入'是'或'否':",
        callback=handle_confirmation
    )
```

## Message 消息模組

### 消息事件

```python
from ErisPulse.Core.Event import message

# 監聽所有消息
@message.on_message()
async def message_handler(event):
    sdk.logger.info(f"收到消息: {event.get_text()}")

# 監聽私聊消息
@message.on_private_message()
async def private_handler(event):
    user_id = event.get_user_id()
    sdk.logger.info(f"私聊來自: {user_id}")

# 監聽群聊消息
@message.on_group_message()
async def group_handler(event):
    group_id = event.get_group_id()
    sdk.logger.info(f"群聊來自: {group_id}")

# 監聽@消息
@message.on_at_message()
async def at_handler(event):
    mentions = event.get_mentions()
    sdk.logger.info(f"被@的使用者: {mentions}")
```

### 條件監聽

```python
# 使用優先級控制執行順序
@message.on_message(priority=10)  # 數值越大優先級越高
async def high_priority_handler(event):
    pass

# 在處理器內部實作條件過濾
@message.on_message()
async def filtered_handler(event):
    if "關鍵詞" not in event.get_text():
        return
    # 處理包含關鍵詞的消息
    pass
```

## Notice 通知模組

### 通知事件

```python
from ErisPulse.Core.Event import notice

# 好友添加
@notice.on_friend_add()
async def friend_add_handler(event):
    user_id = event.get_user_id()
    await event.reply("歡迎添加我為好友！")

# 好友刪除
@notice.on_friend_remove()
async def friend_remove_handler(event):
    user_id = event.get_user_id()
    sdk.logger.info(f"好友刪除: {user_id}")

# 群成員增加
@notice.on_group_increase()
async def member_increase_handler(event):
    user_id = event.get_user_id()
    await event.reply(f"歡迎新成員！")

# 群成員減少
@notice.on_group_decrease()
async def member_decrease_handler(event):
    user_id = event.get_user_id()
    sdk.logger.info(f"群成員離開: {user_id}")
```

## Request 請求模組

### 請求事件

```python
from ErisPulse.Core.Event import request

# 好友請求
@request.on_friend_request()
async def friend_request_handler(event):
    user_id = event.get_user_id()
    comment = event.get_comment()
    sdk.logger.info(f"好友請求: {user_id}, 備註: {comment}")

# 群邀請請求
@request.on_group_request()
async def group_request_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    sdk.logger.info(f"群邀請: {group_id}, 來自: {user_id}")
```

## Meta 元事件模組

### 元事件

```python
from ErisPulse.Core.Event import meta

# 連接事件
@meta.on_connect()
async def connect_handler(event):
    platform = event.get_platform()
    sdk.logger.info(f"平台 {platform} 連接成功")

# 斷開連接事件
@meta.on_disconnect()
async def disconnect_handler(event):
    platform = event.get_platform()
    sdk.logger.info(f"平台 {platform} 斷開連接")

# 心跳事件
@meta.on_heartbeat()
async def heartbeat_handler(event):
    sdk.logger.debug("收到心跳")
```

### Bot 狀態查詢

當適配器發送 meta 事件後，框架會自動追蹤 Bot 狀態。查詢 API 和生命週期事件監聽請參考 [適配器系統 API - Bot 狀態管理](adapter-system.md#bot-狀態管理)。

## Event 包裝類

Event 模組的事件處理器接收一個 Event 包裝類實例，它繼承自 dict 並提供了便捷方法。

### 核心方法

```python
# 獲取事件資訊
event_id = event.get_id()
event_time = event.get_time()
event_type = event.get_type()
detail_type = event.get_detail_type()
platform = event.get_platform()

# 獲取機器人資訊
self_platform = event.get_self_platform()
self_user_id = event.get_self_user_id()
self_info = event.get_self_info()
```

### 會話標識

```python
# 統一目標 ID：群聊返回 group_id，私聊返回 user_id，以此類推
target_id = event.get_target_id()

# 會話唯一標識，格式: {platform}:{detail_type}:{target_id}
session_id = event.get_session_id()
# 示例: "telegram:private:12345"、"qq:group:67890"
```

`get_target_id()` 按以下順序返回首個非空值：`group_id` → `channel_id` → `guild_id` → `thread_id` → `user_id`。適用於上下文管理、狀態儲存等需要統一標識會話的場景。

### 消息方法

```python
# 獲取消息內容
message_segments = event.get_message()
alt_message = event.get_alt_message()
text = event.get_text()

# 獲取發送者資訊
user_id = event.get_user_id()
nickname = event.get_user_nickname()
sender = event.get_sender()

# 獲取群組資訊
group_id = event.get_group_id()

# 判斷消息類型
is_msg = event.is_message()
is_private = event.is_private_message()
is_group = event.is_group_message()

# @消息相關
is_at = event.is_at_message()
has_mention = event.has_mention()
mentions = event.get_mentions()
```

### 命令資訊

```python
# 獲取命令資訊
cmd_name = event.get_command_name()
cmd_args = event.get_command_args()
cmd_raw = event.get_command_raw()

# 判斷是否為命令
is_cmd = event.is_command()
```

### 回覆功能

```python
# 基本回覆
await event.reply("這是一條消息")

# 指定發送方法
await event.reply("http://example.com/image.jpg", method="Image")

# 帶 @使用者 和回覆消息
await event.reply("你好", at_users=["user1"], reply_to="msg_id")

# @全體成員
await event.reply("公告", at_all=True)

# 使用平台專有修飾方法（via 參數）
await event.reply("看板內容", method="Board",
                  via=[("Expire", 3600), ("ForMember", "114514")])

# 獲取發送鏈，自由追加修飾方法和發送方法（適合連續多個修飾 / 動作型方法）
await event.send_chain().Expire(3600).Board("看板內容")
await event.send_chain().DismissBoard()

# 使用 OneBot12 消息段回覆
from ErisPulse.Core.Event import MessageBuilder
msg = MessageBuilder().text("Hello").image("url").build()
await event.reply_ob12(msg)

# 等待回覆
reply = await event.wait_reply(timeout=30)
```

### 平台能力查詢

```python
# 檢查當前平台是否支援某種發送方法
if event.supports("Image"):
    await event.reply(url, method="Image")

# 列出當前平台所有可用發送方法
methods = event.available_methods()
# ["Text", "Image", "Voice", "Video", ...]
```

### 回覆方法

`reply()` 方法支援透過 `method` 參數指定發送類型，以及兩個便捷的布林參數：

```python
# 簡單文本回覆
await event.reply("你好")

# 回覆並@發送者
await event.reply("你好", at_sender=True)

# 回覆並引用當前消息
await event.reply("收到", quote=True)

# 組合使用
await event.reply("收到", at_sender=True, quote=True)

# 發送圖片（使用 method 參數）
if event.supports("Image"):
    await event.reply("http://example.com/img.jpg", method="Image")
else:
    await event.reply("[圖片] http://example.com/img.jpg")
```

**參數說明**：

| 參數 | 類型 | 說明 |
|------|------|------|
| `content` | str | 發送內容 |
| `method` | str | 發送方法，預設 "Text"，可選 "Image"/"Voice"/"Video"/"File" 等 |
| `at_sender` | bool | 是否@發送者（自動提取 user_id） |
| `quote` | bool | 是否引用回覆當前消息（自動提取 message_id） |
| `at_users` | list[str] | @指定使用者列表 |
| `reply_to` | str | 手動指定回覆的消息 ID |
| `at_all` | bool | 是否@全體成員 |

### 互動方法

```python
# confirm — 確認對話（返回 True/False/None）
if await event.confirm("確定要執行此操作嗎？"):
    await event.reply("已確認")

# 使用非 Text 方式發送確認提示
if await event.confirm("http://example.com/image.jpg", method="Image"):
    await event.reply("已確認圖片提示")

# choose — 選擇菜單（返回選項索引或 None）
choice = await event.choose("請選擇顏色：", ["紅色", "綠色", "藍色"])

# options_format="auto"（預設）根據 method 自動選擇樣式：
# Markdown→無序列表（- 1.選項），Html→有序列表（<ol>），其他→純文本列表
# 文本類方法（Markdown/Html 等）預設合併選項到末尾
# merge_prompt=True 可強制任意 method 合併；placeholder 可自訂占位符
choice = await event.choose(
    "## 請選擇\n{options}", ["A", "B"],
    method="Markdown", merge_prompt=True,
)

# collect — 表單收集（返回 {key: value} 字典或 None）
data = await event.collect([
    {"key": "name", "prompt": "請輸入姓名："},
    {"key": "age", "prompt": "請輸入年齡：",
     "validator": lambda e: e.get_text().isdigit()},
    {"key": "avatar", "prompt": "請發送頭像：", "method": "Image"},
])

# wait_for — 等待滿足條件的任意事件
evt = await event.wait_for(event_type="notice", condition=lambda e: ..., timeout=120)

# conversation — 多輪對話上下文
conv = event.conversation(timeout=60)
await conv.say("歡迎！")
```

> 完整的互動方法參數說明和更多示例請參考 [Event 包裝類詳解](../developer-guide/modules/event-wrapper.md) 和 [Conversation 多輪對話](../advanced/conversation.md)。

### 工具方法

```python
# 轉換為字典（過濾以 _ 開頭的內部鍵）
event_dict = event.to_dict()

# 獲取原始資料
raw = event.get_raw()
raw_type = event.get_raw_type()
```

### 鏈路控制

`event.done(claim=, stop=)` 統一控制「認領」與「阻斷」兩個正交語義：

- **認領（claim）**：標記事件已被處理（`_processed`），命令分發器據此跳過去重
- **阻斷（stop）**：阻止向低優先級處理器傳播（`_propagation_stopped`）

```python
# 認領 + 阻斷（預設）
event.done()

# 僅認領，不阻斷（低優先級觀察者仍能看到）
event.done(stop=False)

# 僅阻斷，不認領（如防火牆 / 限流）
event.done(claim=False)

# mark_processed 是主方法，done 是其別名
event.mark_processed()             # 等價 event.done()
event.mark_processed(stop=False)   # 等價 event.done(stop=False)

# 查询狀態
event.is_processed()  # 是否已認領
event.is_stopped()    # 是否已阻斷傳播
```

### 平台擴展方法

適配器可以為 Event 註冊平台專有方法，僅在對應平台的實例上可用。

#### 使用者：使用平台擴展方法

當適配器註冊了平台專有方法後，你可以在事件處理器中直接調用。各平台的方法不同，請參閱對應的 [平台文件](../platform-guide/)。

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    platform = event.get_platform()

    # 根據平台調用專有方法
    if platform == "email":
        subject = event.get_subject()           # 郵件專有
        attachments = event.get_attachments()   # 郵件專有
```

#### 查詢平台已註冊方法

```python
from ErisPulse.Core.Event import get_platform_event_methods

# 查看某平台註冊了哪些方法
methods = get_platform_event_methods("email")
# ["get_subject", "get_from", "get_attachments", ...]

# 動態判斷並調用
for method_name in get_platform_event_methods(event.get_platform()):
    method = getattr(event, method_name)
    print(f"{method_name}: {method()}")
```

#### 平台方法隔離

不同平台註冊的方法互不干擾：

```python
# 郵件事件 - 只有郵件方法
event = Event({"platform": "email", "email_raw": {"subject": "Hello"}})
event.get_subject()      # ✅ "Hello"
event.get_chat_type()    # ❌ AttributeError

# Telegram 事件 - 只有 Telegram 方法
event = Event({"platform": "telegram", "telegram_raw": {"chat": {"type": "private"}}})
event.get_chat_type()    # ✅ "private"
event.get_subject()      # ❌ AttributeError
```

#### `hasattr` / `dir` 支援

```python
hasattr(event, "get_subject")   # 僅當 platform="email" 時返回 True
"get_subject" in dir(event)     # 同上
```

### 適配器：註冊平台擴展方法

適配器可以透過裝飾器為 Event 註冊平台專有方法，方法的第一個參數為 `self`（Event 實例），可以自由訪問事件資料。

#### 單個方法註冊

```python
from ErisPulse.Core.Event import register_event_method

@register_event_method("email")
def get_subject(self):
    """獲取郵件主題"""
    return self.get("email_raw", {}).get("subject", "")

@register_event_method("email")
def get_from(self):
    """獲取發件人"""
    return self.get("email_raw", {}).get("from", {})
```

#### 批量註冊（Mixin 類）

當方法較多時，推薦使用 Mixin 類批量註冊：

```python
from ErisPulse.Core.Event import register_event_mixin

class EmailEventMixin:
    def get_subject(self):
        return self.get("email_raw", {}).get("subject", "")

    def get_from(self):
        return self.get("email_raw", {}).get("from", {})

    def get_attachments(self):
        return self.get("email_raw", {}).get("attachments", [])

# 一次性註冊所有方法
register_event_mixin("email", EmailEventMixin)
```

#### 返回值規範

| 場景 | 返回值 | 使用者使用方式 |
|------|--------|------------|
| 返回資料（文字、字典等） | 直接返回值 | `subject = event.get_subject()` |
| 執行操作（發送消息等） | 返回 `asyncio.Task` | `task = event.do_something()` 可選 `await` |

> **建議**：非資料返回的方法返回 `asyncio.Task`，這樣使用者可以自行決定是否 `await`，即使不 `await` 操作也會執行完成。

```python
@register_event_method("email")
def forward_email(self, to_address: str):
    """轉發郵件 — 返回 Task，使用者可自行決定是否 await"""
    import asyncio
    return asyncio.create_task(
        self._do_forward(to_address)
    )

# 使用者可以 await 等待結果
await event.forward_email("user@example.com")

# 也可以不 await，操作在背景執行
event.forward_email("user@example.com")
```

#### 注銷方法

```python
from ErisPulse.Core.Event import unregister_event_method, unregister_platform_event_methods

# 注銷單個方法
unregister_event_method("email", "get_subject")

# 注銷某平台全部方法（適配器 shutdown 時調用）
unregister_platform_event_methods("email")
```

#### 覆寫內建方法

`register_event_mixin` / `register_event_method` 支援覆寫 Event 內建方法（如 `confirm`、`choose`、`collect`、`wait_reply`、`reply` 等）。註冊的平台方法透過 `Event.__getattribute__` 優先於內建方法生效，因此適配器可以提供平台特色的互動實作。

內建實作為 `_builtin_*` 函數導出，覆寫方可以調用它們作為回退：

```python
from ErisPulse.Core.Event import register_event_mixin, _builtin_choose

class YunhuEventMixin:
    async def choose(self, prompt, options, timeout=60, method="Text"):
        # 云湖平台使用按鈕元件
        buttons = [[{"text": opt} for opt in options]]
        await self.reply(prompt)
        # ...等待按鈕回調或文字回覆...
        # 回退到內建邏輯
        return await _builtin_choose(self, None, options, timeout, "Text")

register_event_mixin("yunhu", YunhuEventMixin)
```

## 跨平台擴展（通配符）

`register_event_method` 和 `register_event_mixin` 支援傳 `"*"` 作為平台名，註冊的方法在**所有平台**的 Event 實例上都可用。適合 AI 對話、上下文管理等需要跨平台複用的功能模組。

### 註冊跨平台方法

```python
from ErisPulse.Core.Event.wrapper import register_event_method

@register_event_method("*")
async def ai_chat(self, prompt: str):
    """self 為 Event 實例，可自由訪問事件資料和內建方法"""
    await self.reply(f"AI: {prompt}")
```

註冊後，所有平台的事件處理器都能調用：

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handler(event):
    await event.ai_chat(event.get_text())
```

### 方法解析優先級

透過屬性存取 Event 方法時，解析順序為：

1. **平台特定方法**（當前平台的覆寫）
2. **通配符方法**（`"*"` 註冊的跨平台方法）
3. **內建方法**（`reply`、`confirm` 等）
4. **字典鍵存取**

> 因此通配符方法可以覆寫內建方法（如 `reply`），但會被同名的平台特定方法進一步覆寫。

## 優先級系統

事件處理器支援優先級，數值越大優先級越高：

```python
# 高優先級處理器先執行
@message.on_message(priority=10)
async def high_priority_handler(event):
    pass

# 低優先級處理器後執行
@message.on_message(priority=0)
async def low_priority_handler(event):
    pass
```

## 相關文件

- [核心模組 API](core-modules.md) - 核心模組 API
- [適配器系統 API](adapter-system.md) - Adapter 管理 API
- [模組開發指南](../developer-guide/modules/) - 開發自訂模組



### 适配器系统 API

# 介面卡系統 API

本文檔詳細介紹 ErisPulse 介面卡系統的 API。

## Adapter 管理器

### 取得介面卡

```python
from ErisPulse import sdk

# 透過名稱取得介面卡
adapter = sdk.adapter.get("platform_name")

# 或者也可以直接透過屬性存取
adapter = sdk.adapter.platform_name
```

### 使用介面卡事件監聽
> 一般情況下，更建議使用`Event`模組進行事件的監聽/處理;
>
> 同時`Event`模組提供了強大的包裝器，可以為您的模組開發帶來更多便利

```python
# 監聽 OneBot12 標準事件
@sdk.adapter.on("message")
async def handle_message(event):
    pass

# 監聽特定平台標準事件
@sdk.adapter.on("message", platform="yunhu")
async def handle_yunhu_message(event):
    pass

# 監聽平台原生事件
@sdk.adapter.on("raw_event", raw=True, platform="yunhu")
async def handle_raw_event(data):
    pass
```

### 介面卡管理

```python
# 取得所有平台
platforms = sdk.adapter.platforms

# 檢查介面卡是否存在
exists = sdk.adapter.exists("platform_name")

# 啟用/停用介面卡
sdk.adapter.enable("platform_name")
sdk.adapter.disable("platform_name")

# 啟動/關閉介面卡
# 以下方法都只展示了傳入參數的情況，無參數時代表啟動/停止全部已註冊介面卡
await sdk.adapter.startup(["platform1", "platform2"])
await sdk.adapter.shutdown(["platform1", "platform2"])

# 檢查介面卡是否正在執行
is_running = sdk.adapter.is_running("platform_name")

# 列出所有正在執行的介面卡
running = sdk.adapter.list_running()
```

## 中間件

中間件在事件分發到處理器之前執行，可以對事件資料進行修改、過濾或記錄。

### 註冊中間件

```python
@sdk.adapter.middleware
async def my_middleware(event):
    sdk.logger.info(f"中間件處理: {event}")
    return event
```

### 中間件執行模型

- **執行順序**：中間件按註冊順序執行（先註冊先執行）
- **資料傳遞**：每個中間件接收上一個中間件傳回的 `event` 資料；如果某個中間件傳回 `None`，則忽略該傳回值並保留原資料繼續傳遞（同時輸出 `warning` 級別日誌）
- **修改資料**：中間件可以修改事件資料並傳回修改後的字典

```python
@sdk.adapter.middleware
async def add_timestamp(event):
    event["processed_at"] = time.time()
    return event

@sdk.adapter.middleware
async def filter_spam(event):
    if event.get("detail_type") == "private":
        text = event.get("alt_message", "")
        if "垃圾廣告" in text:
            return None   # 傳回 None 不會阻止事件傳播，僅忽略此傳回值
    return event
```

> **注意**：中間件目前不支援阻斷事件傳播。如需過濾特定事件，請在事件處理器中透過條件判斷實作。
> 但您可以在Event模組中設定高優先級處理器然後在處理器內使用設定 `event.mark_processed()` 來阻斷低優先級事件處理器

## Send 訊息發送

### 基本發送

```python
# 取得介面卡
adapter = sdk.adapter.get("platform")

# 發送文字訊息
await adapter.Send.To("user", "123").Text("Hello")

# 發送圖片訊息
await adapter.Send.To("group", "456").Image("https://example.com/image.jpg")
```

### 指定發送帳號

```python
# 使用帳號名稱
await adapter.Send.Using("account1").To("user", "123").Text("Hello")

# 使用帳號 ID
await adapter.Send.Using("bot_id").To("user", "123").Text("Hello")
```

### 查詢支援的發送方法

```python
# 列出平台支援的所有發送方法
methods = sdk.adapter.list_sends("onebot11")
# 返回: ["Text", "Image", "Voice", "Markdown", ...]

# 取得某個方法的詳細資訊
info = sdk.adapter.send_info("onebot11", "Text")
# 返回:
# {
#     "name": "Text",
#     "parameters": [
#         {"name": "text", "type": "str", "default": null, "annotation": "str"}
#     ],
#     "return_type": "Awaitable[Any]",
#     "docstring": "發送文字訊息..."
# }
```

### 鏈式修飾

```python
# @用戶
await adapter.Send.To("group", "456").At("789").Text("你好")

# @全體成員
await adapter.Send.To("group", "456").AtAll().Text("大家好")

# 回覆訊息
await adapter.Send.To("group", "456").Reply("msg_id").Text("回覆內容")

# 組合使用
await adapter.Send.To("group", "456").At("789").Reply("msg_id").Text("回覆@的訊息")
```

## API 呼叫

### call_api 方法

> **注意**：`call_api` 是直接呼叫平台原生 API 的底層方法，各平台的參數和傳回值可能不同，請參考對應平台介面卡文件。**推薦使用 Send DSL 發送訊息**，僅在 Send DSL 不支援的場景（如取得平台特有的資料、呼叫平台管理介面等）中使用 `call_api`。

```python
# 呼叫平台 API
result = await adapter.call_api(
    endpoint="/send",
    content="Hello",
    recvId="123",
    recvType="user"
)

# 標準化回應
{
    "status": "ok",
    "retcode": 0,
    "data": {...},
    "message_id": "msg_id",
    "message": "",
    "{platform}_raw": raw_response
}
```

## 介面卡基類

### BaseAdapter 方法

```python
from ErisPulse import sdk
from ErisPulse.Core import BaseAdapter

class MyAdapter(BaseAdapter):
    def __init__(self):
        super().__init__()
        self.sdk = sdk
        # 初始化介面卡
        pass
    
    async def start(self):
        """啟動介面卡（必須實作）"""
        pass
    
    async def shutdown(self):
        """關閉介面卡（必須實作）"""
        pass
    
    async def call_api(self, endpoint: str, **params):
        """呼叫平台 API（必須實作）"""
        pass
```

### Send 嵌套類

```python
class MyAdapter(BaseAdapter):
    class Send(BaseAdapter.Send):
        def Text(self, text: str):
            """發送文字訊息"""
            import asyncio
            return asyncio.create_task(
                self._adapter.call_api(
                    endpoint="/send",
                    content=text,
                    recvId=self._target_id,
                    recvType=self._target_type
                )
            )
```

## Bot 狀態管理

介面卡透過發送 OneBot12 標準的 **`meta` 事件**來告知框架 Bot 的連線狀態。系統自動從中提取 Bot 資訊進行狀態追蹤。

### meta 事件類型

介面卡應發送以下三種 `meta` 事件：

| `type` | `detail_type` | 說明 | 觸發時機 |
|--------|--------------|------|---------|
| `meta` | `connect` | Bot 連線上線 | 介面卡與平台建立連線成功後 |
| `meta` | `heartbeat` | Bot 心跳 | 定期發送（建議 30-60 秒） |
| `meta` | `disconnect` | Bot 斷開連線 | 檢測到連線斷開時 |

### self 欄位擴展

ErisPulse 在 OneBot12 標準的 `self` 欄位上擴展了以下選用欄位：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `self.platform` | string | 平台名稱（OB12 標準） |
| `self.user_id` | string | Bot 用戶 ID（OB12 標準） |
| `self.user_name` | string | Bot 暱稱（ErisPulse 擴展） |
| `self.avatar` | string | Bot 頭像 URL（ErisPulse 擴展） |
| `self.account_id` | string | 多帳號識別（ErisPulse 擴展） |

### meta 事件格式

#### connect — 連線上線

```python
await adapter.emit({
    "id": "unique_id",
    "time": 1712345678,
    "type": "meta",
    "detail_type": "connect",
    "platform": "telegram",
    "self": {
        "platform": "telegram",
        "user_id": "123456",
        "user_name": "MyBot",
        "avatar": "https://example.com/avatar.jpg"
    },
    "telegram_raw": {...},
    "telegram_raw_type": "bot_connected"
})
```

系統處理：註冊 Bot，標記為 `online`，觸發 `adapter.bot.online` 生命週期事件。

#### heartbeat — 心跳

```python
await adapter.emit({
    "id": "unique_id",
    "time": 1712345708,
    "type": "meta",
    "detail_type": "heartbeat",
    "platform": "telegram",
    "self": {
        "platform": "telegram",
        "user_id": "123456"
    }
})
```

系統處理：更新 `last_active` 時間（心跳中也支援更新元資訊）。

#### disconnect — 斷開連線

```python
await adapter.emit({
    "id": "unique_id",
    "time": 1712345738,
    "type": "meta",
    "detail_type": "disconnect",
    "platform": "telegram",
    "self": {
        "platform": "telegram",
        "user_id": "123456"
    }
})
```

系統處理：標記 Bot 為 `offline`，觸發 `adapter.bot.offline` 生命週期事件。

### 一般事件的自動發現

除了 `meta` 事件外，一般事件（`message`/`notice`/`request`）中的 `self` 欄位也會自動發現並註冊 Bot、更新活躍時間。這意味著即使介面卡不發送 `connect` 事件，框架也能從第一條一般事件中發現 Bot。

### 介面卡接入範例

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        # 與平台建立連線...
        connection = await self._connect()
        
        # 連線成功，發送 connect 事件
        await adapter.emit({
            "id": str(uuid4()),
            "time": int(time.time()),
            "type": "meta",
            "detail_type": "connect",
            "platform": "myplatform",
            "self": {
                "platform": "myplatform",
                "user_id": self.bot_id,
                "user_name": self.bot_name,
                "avatar": self.bot_avatar
            },
            "myplatform_raw": raw_data,
            "myplatform_raw_type": "connected"
        })
    
    async def on_disconnect(self):
        # 斷開連線，發送 disconnect 事件
        await adapter.emit({
            "id": str(uuid4()),
            "time": int(time.time()),
            "type": "meta",
            "detail_type": "disconnect",
            "platform": "myplatform",
            "self": {
                "platform": "myplatform",
                "user_id": self.bot_id
            }
        })
```

### 查詢 Bot 狀態

```python
# 取得所有介面卡與 Bot 的完整狀態（WebUI 友好）
summary = sdk.adapter.get_status_summary()
# {
#     "adapters": {
#         "telegram": {
#             "status": "started",
#             "bots": {
#                 "123456": {
#                     "status": "online",
#                     "last_active": 1712345678.0,
#                     "info": {"nickname": "MyBot"}
#                 }
#             }
#         }
#     }
# }

# 列出所有 Bot
all_bots = sdk.adapter.list_bots()

# 列出指定平台的 Bot
tg_bots = sdk.adapter.list_bots("telegram")

# 取得單個 Bot 詳情
info = sdk.adapter.get_bot_info("telegram", "123456")

# 檢查 Bot 是否在線
if sdk.adapter.is_bot_online("telegram", "123456"):
    print("Bot 在線")
```

### Bot 狀態值

| 狀態 | 說明 |
|------|------|
| `online` | 在線（持續收到事件或介面卡主動標記） |
| `offline` | 離線（介面卡主動標記或系統關閉時自動設定） |
| `unknown` | 未知（僅註冊但未確認狀態） |

### 生命週期事件

| 事件名 | 觸發時機 | 資料 |
|--------|---------|------|
| `adapter.bot.online` | 首次自動發現新 Bot | `{platform, bot_id, status}` |
| `adapter.status.change` | 介面卡狀態變化（starting/started/stopping/stopped/stop_failed） | `{platform, status}` |

```python
# 監聽 Bot 上線事件
@sdk.lifecycle.on("adapter.bot.online")
def on_bot_online(event):
    print(f"Bot 上線: {event['data']['platform']}/{event['data']['bot_id']}")

# 監聽介面卡狀態變化
@sdk.lifecycle.on("adapter.status.change")
def on_status_change(event):
    print(f"介面卡狀態: {event['data']['platform']} -> {event['data']['status']}")
```

> 系統關閉時（`shutdown`），所有 Bot 會自動被標記為 `offline`。

## 相關文件

- [核心模組 API](docs/zh-TW/core-modules.md) - 核心模組 API
- [事件系統 API](docs/zh-TW/event-system.md) - Event 模組 API
- [介面卡開發指南](../developer-guide/adapters/) - 開發平台介面卡



====
技术标准
====


### 会话类型标准

# ErisPulse 會話類型標準

本文檔定義了 ErisPulse 支援的會話類型標準，包括接收事件類型和發送目標類型。

## 1. 核心概念

### 1.1 接收類型 && 發送類型

ErisPulse 區分兩種會話類型：

- **接收類型（Receive Type）**：用於接收的事件的 `detail_type` 欄位
- **發送類型（Send Type）**：用於發送訊息時 `Send.To()` 方法的目標類型

### 1.2 類型映射關係

```
接收類型 (detail_type)     發送類型 (Send.To)
─────────────────        ────────────────
private                 →        user
group                   →        group
channel                 →        channel
guild                   →        guild
thread                  →        thread
user                    →        user
```

**關鍵點**：
- `private` 是接收時的類型，發送時必須使用 `user`
- `group`、`channel`、`guild`、`thread` 在接收和發送時類型相同
- 系統會自動進行類型轉換，無需手動處理（代表著你可以直接使用獲得的接收類型進行發送），但實際上，你無需考慮這些，Event 的包裝類的存在，你可以直接使用 event.reply() 方法，而無需考慮類型轉換

## 2. 標準會話類型

### 2.1 OneBot12 標準類型

#### private
- **接收類型**：`private`
- **發送類型**：`user`
- **說明**：一對一私聊訊息
- **ID 欄位**：`user_id`
- **適用平台**：所有支援私聊的平台

#### group
- **接收類型**：`group`
- **發送類型**：`group`
- **說明**：群聊訊息，包括各種形式的群組（如 Telegram supergroup）
- **ID 欄位**：`group_id`
- **適用平台**：所有支援群聊的平台

#### user
- **接收類型**：`user`
- **發送類型**：`user`
- **說明**：使用者類型，某些平台（如 Telegram）將私聊表示為 user 而非 private
- **ID 欄位**：`user_id`
- **適用平台**：Telegram 等平台

### 2.2 ErisPulse 擴展類型

#### channel
- **接收類型**：`channel`
- **發送類型**：`channel`
- **說明**：頻道訊息，支援多個使用者的廣播式訊息
- **ID 欄位**：`channel_id`
- **適用平台**：Discord, Telegram, Line 等

#### guild
- **接收類型**：`guild`
- **發送類型**：`guild`
- **說明**：伺服器/社群訊息，通常用於 Discord Guild 級別的事件
- **ID 欄位**：`guild_id`
- **適用平台**：Discord 等

#### thread
- **接收類型**：`thread`
- **發送類型**：`thread`
- **說明**：話題/子頻道訊息，用於社群中的子討論區
- **ID 欄位**：`thread_id`
- **適用平台**：Discord Threads, Telegram Topics 等

## 3. 平台類型映射

### 3.1 映射原則

適配器負責將平台的原生類型映射到 ErisPulse 標準類型：

```
平台原生類型 → ErisPulse 標準類型 → 發送類型
```

### 3.2 常見平台映射示例

#### Telegram
```
Telegram 類型          ErisPulse 接收類型    發送類型
─────────────────      ────────────────       ───────────
private                private                 user
group                  group                   group
supergroup             group                   group  # 映射到 group
channel                channel                 channel
```

#### Discord
```
Discord 類型          ErisPulse 接收類型    發送類型
─────────────────      ────────────────       ───────────
Direct Message         private                user
Text Channel           channel                channel
Guild                  guild                  guild
Thread                 thread                 thread
```

#### OneBot11
```
OneBot11 類型        ErisPulse 接收類型    發送類型
─────────────────      ────────────────       ───────────
private                private                user
group                  group                  group
discuss                group                  group  # 映射到 group
```

## 4. 自訂類型擴展

### 4.1 註冊自訂類型

適配器可以註冊自訂的會話類型：

```python
from ErisPulse.Core.Event import register_custom_type

# 註冊自訂類型
register_custom_type(
    receive_type="my_custom_type",
    send_type="custom",
    id_field="custom_id",
    platform="MyPlatform"
)
```

### 4.2 使用自訂類型

註冊後，系統會自動處理該類型的轉換和推斷：

```python
# 自動推斷
receive_type = infer_receive_type(event, platform="MyPlatform")
# 返回: "my_custom_type"

# 轉換為發送類型
send_type = convert_to_send_type(receive_type, platform="MyPlatform")
# 返回: "custom"

# 獲取對應 ID
target_id = get_target_id(event, platform="MyPlatform")
# 返回: event["custom_id"]
```

### 4.3 解除註冊自訂類型

```python
from ErisPulse.Core.Event import unregister_custom_type

unregister_custom_type("my_custom_type", platform="MyPlatform")
```

## 5. 自動類型推斷

當事件沒有明確的 `detail_type` 欄位時，系統會根據存在的 ID 欄位自動推斷類型：

> [!NOTE]
> **2.7.0+ 行為變更**：`detail_type` 只有在是**已知會話類型**（標準或自定義）時才直接採用。notice/request 事件的 `detail_type`（如 `group_member_increase`、`friend_increase`）是**語意子類型**而非會話類型，會轉而根據 ID 欄位推斷正確的會話類型。

### 5.1 推斷優先級

```
優先級（從高到低）：
1. group_id     → group
2. channel_id   → channel
3. guild_id     → guild
4. thread_id    → thread
5. user_id      → private
```

### 5.2 使用示例

```python
# 事件只有 group_id
event = {"group_id": "123", "user_id": "456"}
receive_type = infer_receive_type(event)
# 返回: "group"（優先使用 group_id）

# 事件只有 user_id
event = {"user_id": "123"}
receive_type = infer_receive_type(event)
# 返回: "private"

# notice 事件的 detail_type 是語意子類型，2.7.0+ 會從 ID 欄位推斷
event = {"type": "notice", "detail_type": "group_member_increase", "group_id": "123"}
receive_type = infer_receive_type(event)
# 返回: "group"（而非 "group_member_increase"）
```

## 6. API 使用示例

### 6.1 發送訊息

```python
from ErisPulse import adapter

# 發送給使用者
await adapter.myplatform.Send.To("user", "123").Text("Hello")

# 發送給群組
await adapter.myplatform.Send.To("group", "456").Text("Hello")

# 自動轉換 private → user（不推薦，可能會有相容性問題）
await adapter.myplatform.Send.To("private", "789").Text("Hello")
# 內部自動轉換為: Send.To("user", "789") # 直接使用user作為會話類型是更優的選擇
```

### 6.2 事件回覆

```python
from ErisPulse.Core.Event import Event

# Event.reply() 自動處理類型轉換
await event.reply("回覆內容")
# 內部自動使用正確的發送類型
```

### 6.3 命令處理

```python
from ErisPulse.Core.Event import command

@command(name="test")
async def handle_test(event):
    # 系統自動處理會話類型
    # 無需手動判斷 group_id 還是 user_id
    await event.reply("命令執行成功")
```

## 7. 核心 API 參考

### 7.1 類型轉換

```python
from ErisPulse.Core.Event import convert_to_send_type, convert_to_receive_type

# 接收類型 → 發送類型
convert_to_send_type("private")  # → "user"
convert_to_send_type("group")    # → "group"

# 發送類型 → 接收類型
convert_to_receive_type("user")   # → "private"
convert_to_receive_type("group")  # → "group"
```

### 7.2 ID 欄位查詢

```python
from ErisPulse.Core.Event import get_id_field, get_receive_type

get_id_field("group")    # → "group_id"
get_id_field("private")  # → "user_id"

get_receive_type("group_id")  # → "group"
get_receive_type("user_id")   # → "private"
```

### 7.3 一步獲取發送資訊

```python
from ErisPulse.Core.Event import get_send_type_and_target_id

event = {"detail_type": "private", "user_id": "123"}
send_type, target_id = get_send_type_and_target_id(event)
# send_type = "user", target_id = "123"

# 直接用於 Send.To()
await adapter.Send.To(send_type, target_id).Text("Hello")
```

### 7.4 獲取目標 ID

```python
from ErisPulse.Core.Event import get_target_id

event = {"detail_type": "group", "group_id": "456"}
get_target_id(event)  # → "456"
```

## 8. 工具方法

```python
from ErisPulse.Core.Event import (
    is_standard_type,
    is_valid_send_type,
    get_standard_types,
    get_send_types,
    clear_custom_types,
)

is_standard_type("private")     # True
is_standard_type("custom_type") # False

is_valid_send_type("user")      # True
is_valid_send_type("invalid")   # False

get_standard_types()  # {"private", "group", "channel", "guild", "thread", "user"}
get_send_types()      # {"user", "group", "channel", "guild", "thread"}

clear_custom_types()                # 清除所有
clear_custom_types(platform="discord")  # 只清除指定平台的
```

## 9. 最佳實踐

### 7.1 適配器開發者

1. **使用標準映射**：盡可能映射到標準類型，而非創建新類型
2. **正確轉換**：確保接收類型和發送類型的映射關係正確
3. **保留原始數據**：在 `{platform}_raw` 中保留原始事件類型
4. **文件說明**：在適配器文件中說明類型映射關係

### 7.2 模塊開發者

1. **使用工具方法**：使用 `get_send_type_and_target_id()` 等工具方法
2. **避免硬編碼**：不要寫 `if group_id else "private"` 這樣的代碼
3. **考慮所有類型**：代碼要支持所有標準類型，不僅是 private/group
4. **靈活設計**：使用事件包裝器的方法，而非直接訪問字段

### 7.3 類型推斷

- **優先使用 detail_type**：如果有明確字段，不進行推斷
- **合理使用推斷**：只在沒有明確類型時使用
- **注意優先級**：了解推斷優先級，避免意外結果

## 10. 常見問題

### Q1: 為什麼發送時 private 要轉換為 user？

A: 這是 OneBot12 標準的要求。`private` 是接收時的概念，發送時使用 `user` 更符合語義。

### Q2: 如何支援新的會話類型？

A: 透過 `register_custom_type()` 註冊自定義類型，或直接使用標準類型中的 `channel`、`guild` 等。

### Q3: 事件沒有 detail_type 怎麼辦？

A: 系統會根據存在的 ID 欄位自動推斷。優先級為：group > channel > guild > thread > user。

### Q4: 適配器如何映射 Telegram supergroup？

A: 在適配器的轉換邏輯中，將 `supergroup` 映射為標準的 `group` 類型。

### Q5: 郵箱等特殊平台如何處理？

A: 對於不通用或平台特有的類型，使用 `{platform}_raw` 和 `{platform}_raw_type` 保留原始數據，適配器自行處理。

## 11. 相關文件

- [事件轉換標準](event-conversion.md) - 完整的事件轉換規範
- [發送方法規範](send-method-spec.md) - Send 類的方法命名和參數規範
- [適配器開發指南](../developer-guide/adapters/) - 適配器開發完整指南



### 事件转换标准

# 适配器標準化轉換規範

## 1. 核心原則
1. 嚴格相容：所有標準欄位必須完全遵循 OneBot12 規範
2. 明確擴展：平台特有功能必須添加 {platform}_ 前綴（如 yunhu_form）
3. 資料完整：原始事件資料必須保留在 {platform}_raw 欄位中，原始事件類型必須保留在 {platform}_raw_type 欄位中
4. 時間統一：所有時間戳必須轉換為 10 位 Unix 時間戳（秒級）
5. 平台統一：platform 項命名必須與你在 ErisPulse 中註冊的名稱/別稱一致

## 2. 標準欄位要求

### 2.1 必須欄位
| 欄位 | 類型 | 說明 |
|------|------|------|
| id | string | 事件唯一識別符 |
| time | integer | Unix 時間戳（秒級） |
| type | string | 事件類型 |
| detail_type | string | 事件詳細類型（詳見[會話類型標準](session-types.md)） |
| platform | string | 平台名稱 |
| self | object | 機器人自身資訊 |
| self.platform | string | 平台名稱 |
| self.user_id | string | 機器人使用者 ID |

**detail_type 規範**：
- 必須使用 ErisPulse 標準會話類型（詳見 [會話類型標準](session-types.md)）
- 支援的類型：`private`, `group`, `user`, `channel`, `guild`, `thread`
- 适配器負責將平台原生類型映射到標準類型

### 2.2 訊息事件欄位
| 欄位 | 類型 | 說明 |
|------|------|------|
| message | array | 訊息段陣列 |
| alt_message | string | 訊息段備用文字 |
| user_id | string | 使用者 ID |
| user_nickname | string | 使用者暱稱（選填） |

### 2.3 通知事件欄位
| 欄位 | 類型 | 說明 |
|------|------|------|
| user_id | string | 使用者 ID |
| user_nickname | string | 使用者暱稱（選填） |
| operator_id | string | 操作者 ID（選填） |

### 2.4 請求事件欄位
| 欄位 | 類型 | 說明 |
|------|------|------|
| user_id | string | 使用者 ID |
| user_nickname | string | 使用者暱稱（選填） |
| comment | string | 請求附言（選填） |
| request_id | string | 請求識別符（**強烈推薦**，用於同意/拒絕請求操作） |

**`request_id` 欄位說明**：
- `request_id` 是請求事件的唯一操作識別符，用於通過 `HandleRequest` DSL 執行同意/拒絕操作
- 适配器在轉換請求事件時，應將平台原生的請求識別映射到此欄位
- 如果平台本身沒有請求 ID，适配器應生成一個唯一識別（如基於時間戳 + 使用者 ID 的雜湊）
- 當 `request_id` 缺失時，`event.approve()` / `event.reject()` 將拋出 `ValueError`

## 3. 事件格式範例

### 3.1 訊息事件
```json
{
  "id": "1234567890",
  "time": 1752241223,
  "type": "message",
  "detail_type": "group",
  "platform": "yunhu",
  "self": {
    "platform": "yunhu",
    "user_id": "bot_123"
  },
  "message": [
    {
      "type": "text",
      "data": {
        "text": "抽獎 超級大獎"
      }
    }
  ],
  "alt_message": "抽獎 超級大獎",
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "group_id": "group_789",
  "yunhu_raw": {...},
  "yunhu_raw_type": "message.receive.normal",
  "yunhu_command": {
    "name": "抽獎",
    "args": "超級大獎"
  }
}
```

### 3.2 通知事件
```json
{
  "id": "1234567891",
  "time": 1752241224,
  "type": "notice",
  "detail_type": "group_member_increase",
  "platform": "yunhu",
  "self": {
    "platform": "yunhu",
    "user_id": "bot_123"
  },
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "group_id": "group_789",
  "operator_id": "",
  "yunhu_raw": {...},
  "yunhu_raw_type": "bot.followed"
}
```

### 3.3 請求事件
```json
{
  "id": "1234567892",
  "time": 1752241225,
  "type": "request",
  "detail_type": "friend",
  "platform": "onebot11",
  "self": {
    "platform": "onebot11",
    "user_id": "bot_123"
  },
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "comment": "請加好友",
  "request_id": "req_abc123",
  "onebot11_raw": {...},
  "onebot11_raw_type": "request"
}
```

## 4. 訊息段標準

### 4.1 標準訊息段

標準訊息段類型**不添加**平台前綴：

| 類型 | 說明 | data 欄位 |
|------|------|----------|
| `text` | 純文字 | `text: str` |
| `image` | 圖片 | `file: str/bytes`, `url: str` |
| `audio` | 音訊 | `file: str/bytes`, `url: str` |
| `video` | 影片 | `file: str/bytes`, `url: str` |
| `file` | 檔案 | `file: str/bytes`, `url: str`, `filename: str` |
| `mention` | @使用者 | `user_id: str`, `user_name: str` |
| `reply` | 回覆 | `message_id: str` |
| `face` | 表情 | `id: str` |
| `location` | 位置 | `latitude: float`, `longitude: float` |

```json
{
  "type": "text",
  "data": {
    "text": "Hello World"
  }
}
```

### 4.2 平台擴展訊息段

平台特有的訊息段需要添加平台前綴：

```json
// 雲湖 - 表單
{"type": "yunhu_form", "data": {"form_id": "123456", "form_name": "報名表"}}

// Telegram - 貼紙
{"type": "telegram_sticker", "data": {"file_id": "CAACAgIAAxkBAA...", "emoji": "😂"}}
```

**擴展訊息段要求**：
1. **data 內部欄位不加前綴**：`{"type": "yunhu_form", "data": {"form_id": "..."}}` 而非 `{"type": "yunhu_form", "data": {"yunhu_form_id": "..."}}`
2. **提供降級方案**：模組可能不識別擴展訊息段，适配器應在 `alt_message` 中提供文字替代
3. **文件完備**：每個擴展訊息段必須在适配器文件中說明 `type`、`data` 結構和使用場景

## 5. 未知事件處理

對於無法識別的事件類型，應產生警告事件：
```json
{
  "id": "1234567893",
  "time": 1752241223,
  "type": "unknown",
  "platform": "yunhu",
  "yunhu_raw": {...},
  "yunhu_raw_type": "unknown",
  "warning": "Unsupported event type: special_event",
  "alt_message": "This event type is not supported by this system."
}
```

---

## 6. 擴展命名規範

### 6.1 欄位命名

**規則**：`{platform}_{field_name}`

```
平台前綴    欄位名            完整欄位名
────────    ───────          ──────────
yunhu       command           yunhu_command
telegram    sticker_file_id   telegram_sticker_file_id
onebot11    anonymous         onebot11_anonymous
email       subject           email_subject
```

**要求**：
- `platform` 必須與适配器註冊時的平台名完全一致（大小寫敏感）
- `field_name` 使用 `snake_case` 命名
- 禁止使用雙下劃線 `__` 開頭（Python 保留）
- 禁止與標準欄位同名（如 `type`、`time`、`message` 等）

### 6.2 訊息段類型命名

**規則**：`{platform}_{segment_type}`

標準訊息段類型（`text`、`image`、`audio`、`video`、`mention`、`reply` 等）**不得**添加平台前綴。只有平台特有的訊息段類型才需要添加前綴。

### 6.3 原始資料欄位命名

以下欄位名是**保留欄位**，所有适配器必須遵循：

| 保留欄位 | 類型 | 說明 |
|---------|------|------|
| `{platform}_raw` | `any` | 平台原始事件資料的完整副本 |
| `{platform}_raw_type` | `string` | 平台原始事件類型識別 |

**要求**：
- `{platform}_raw` 必須是原始資料的深拷貝，而非引用
- `{platform}_raw_type` 必須是字串，即使平台使用數字類型也要轉換為字串
- 這兩個欄位在所有事件中**必須存在**（無法獲取時為 `null` 和空字串 `""`）

### 6.4 平台特有欄位範例

```json
{
  "yunhu_command": {
    "name": "抽獎",
    "args": "超級大獎"
  },
  "yunhu_form": {
    "form_id": "123456"
  },
  "telegram_sticker": {
    "file_id": "CAACAgIAAxkBAA..."
  }
}
```

### 6.5 嵌套擴展欄位

擴展欄位可以是簡單值，也可以是嵌套物件：

```json
{
  "telegram_chat": {
    "id": 123456,
    "type": "supergroup",
    "title": "My Group"
  },
  "telegram_forward_from": {
    "user_id": "789",
    "user_name": "ForwardUser"
  }
}
```

**嵌套欄位要求**：
- 頂層鍵必須帶平台前綴
- 嵌套內部欄位**不添加**平台前綴
- 嵌套深度建議不超過 3 層

### 6.6 `self` 欄位擴展

`self` 物件的標準必選欄位（`platform`、`user_id`）見 §2.1，以下是 ErisPulse 擴展的可選欄位：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `self.user_name` | `string` | 機器人暱稱 |
| `self.avatar` | `string` | 機器人頭像 URL |
| `self.account_id` | `string` | 多帳號模式下的帳號識別 |

> **Bot 狀態追蹤**：适配器通過發送 `type: "meta"` 事件告知框架 Bot 的連線狀態。支援的 `detail_type`：`connect`（上線）、`heartbeat`（心跳）、`disconnect`（離線）。系統自動從中提取 `self` 欄位的 Bot 元資訊進行狀態追蹤。此外，普通事件中的 `self` 欄位也會自動發現 Bot。詳見 [适配器系統 API - Bot 狀態管理](../api-reference/adapter-system.md)。

---

## 7. 會話類型擴展

ErisPulse 在 OneBot12 標準的 `private`、`group` 基礎上擴展了以下會話類型：

| 類型 | OneBot12 標準 | ErisPulse 擴展 | 說明 |
|------|:-----------:|:------------:|------|
| `private` | ✅ | — | 一對一私聊 |
| `group` | ✅ | — | 群聊 |
| `user` | — | ✅ | 使用者類型（Telegram 等） |
| `channel` | — | ✅ | 頻道（廣播式） |
| `guild` | — | ✅ | 伺服器/社群 |
| `thread` | — | ✅ | 話題/子頻道 |

**适配器自定義類型擴展**：

```python
from ErisPulse.Core.Event.session_type import register_custom_type

# 在适配器啟動時註冊
register_custom_type(
    receive_type="email",      # 接收事件中的 detail_type
    send_type="email",         # 發送時的目標類型
    id_field="email_id",       # 對應的 ID 欄位名
    platform="email"           # 平台識別
)
```

**自定義類型要求**：
- 必須在适配器 `start()` 時註冊，在 `shutdown()` 時註銷
- `receive_type` 不應與標準類型重名
- `id_field` 應遵循 `{目標}_id` 的命名模式

> 完整的會話類型定義和映射關係參見 [會話類型標準](session-types.md)。

---

## 8. 模組開發者指南

### 8.1 訪問擴展欄位

```python
from ErisPulse.Core.Event import message

@message()
async def handle_message(event):
    # 訪問標準欄位
    text = event.get_text()
    user_id = event.get_user_id()

    # 訪問平台擴展欄位 - 方式 1：直接 get
    yunhu_command = event.get("yunhu_command")

    # 訪問平台擴展欄位 - 方式 2：點式訪問（Event 包裝類）
    # event.yunhu_command

    # 訪問原始資料
    raw_data = event.get("yunhu_raw")
    raw_type = event.get_raw_type()

    # 判斷平台
    platform = event.get_platform()
    if platform == "yunhu":
        pass
    elif platform == "telegram":
        pass
```

### 8.2 處理擴展訊息段

```python
@message()
async def handle_message(event):
    message_segments = event.get("message", [])

    for segment in message_segments:
        seg_type = segment.get("type")
        seg_data = segment.get("data", {})

        if seg_type == "text":
            text = seg_data["text"]
        elif seg_type.startswith("yunhu_"):
            if seg_type == "yunhu_form":
                form_id = seg_data["form_id"]
        elif seg_type.startswith("telegram_"):
            if seg_type == "telegram_sticker":
                file_id = seg_data["file_id"]
```

### 8.3 最佳實踐

1. **優先使用標準欄位**：不要假設擴展欄位一定存在
2. **平台判斷**：通過 `event.get_platform()` 判斷平台，而非通過擴展欄位是否存在來推斷
3. **優雅降級**：無法處理擴展訊息段時，使用 `alt_message` 作為兜底
4. **不要硬編碼前綴**：使用 `platform` 變數動態拼接

```python
# ✅ 推薦
platform = event.get_platform()
raw_data = event.get(f"{platform}_raw")

# ❌ 不推薦
raw_data = event.get("yunhu_raw")
```

### 8.4 請求事件處理

模組開發者可以通過 `event.approve()` 和 `event.reject()` 對請求事件進行操作：

```python
from ErisPulse.Core.Event import request

# 好友請求：自動同意
@request.on_friend_request()
async def handle_friend_request(event):
    user_name = event.get_user_nickname() or event.get_user_id()
    comment = event.get_comment()
    
    # 同意請求
    result = await event.approve()
    if result.get("status") == "ok":
        print(f"已同意 {user_name} 的好友請求")
    else:
        print(f"同意好友請求失敗: {result.get('message')}")

# 群邀請：根據條件決定
@request.on_group_request()
async def handle_group_request(event):
    comment = event.get_comment()
    
    # 拒絕請求
    result = await event.reject(comment="暫不加入新群")
```

**通過适配器直接操作**（適用於非事件處理器場景）：

```python
from ErisPulse import adapter

# 通過 request_id 直接操作
await adapter.myplatform.Request("req_abc123").accept()
await adapter.myplatform.Request("req_abc123").reject()

# 指定 Bot 帳號操作
await adapter.myplatform.Request("req_abc123").Using("bot1").accept()

# 附帶備註
await adapter.myplatform.Request("req_abc123").accept(comment="歡迎")
```

---

## 9. notice / request 事件的會話類型推斷

### 9.1 問題背景

notice 事件和 request 事件的 `detail_type` 是**語義子類型**（如 `group_member_increase`、`friend_increase`），不是會話類型（如 `group`、`private`）。

```
type        detail_type                  含義            會話類型
────        ───────────                  ────            ────────
message     group                        群聊訊息         group（detail_type 即會話類型）
message     private                      私聊訊息         private（detail_type 即會話類型）
notice      group_member_increase        群成員增加       group（需從 group_id 推斷）
notice      friend_increase              好友增加         private（需從 user_id 推斷）
request     friend                       好友請求         private（需從 user_id 推斷）
request     group                        群請求           group（detail_type 即會話類型）
```

### 9.2 推斷規則

`infer_receive_type()` 的推斷順序：

1. 如果 `detail_type` 是已知會話類型（`private`/`group`/`channel`/`guild`/`thread`/`user`），直接使用
2. 如果 `detail_type` 是自定義會話類型，直接使用
3. 否則（notice/request 的語義子類型），根據 ID 欄位推斷：
   - 有 `group_id` → `"group"`
   - 有 `channel_id` → `"channel"`
   - 有 `guild_id` → `"guild"`
   - 有 `thread_id` → `"thread"`
   - 有 `user_id` → `"private"`

### 9.3 `event.reply()` 目標推斷

notice/request 事件中 `event.reply()` 的發送目標由會話類型推斷決定：

- 群通知事件（含 `group_id`）→ 回覆到**群**
- 好友通知事件（僅含 `user_id`）→ 回覆到**使用者私聊**

```python
from ErisPulse.Core.Event import notice

@notice.on_group_increase()
async def handle_welcome(event):
    group_id = event.get("group_id")    # "group_789"
    user_id = event.get("user_id")      # "user_456"

    # event.reply() 發送到群（group/group_789）
    await event.reply("歡迎入群！")

    # 如需通知管理員（私聊），顯式指定目標：
    await adapter.Send.To("user", "admin_id").Text(f"新成員 {user_id} 加入了 {group_id}")
```

### 9.4 适配器開發建議

確保 notice/request 事件中包含正確的 ID 欄位：

| detail_type | 必須包含的 ID 欄位 | 推斷的會話類型 |
|-------------|-------------------|---------------|
| `group_member_increase` | `group_id` + `user_id` | `group` |
| `group_member_decrease` | `group_id` + `user_id` | `group` |
| `friend_increase` | `user_id` | `private` |
| `friend_decrease` | `user_id` | `private` |
| `friend`（請求） | `user_id` | `private` |
| `group`（請求） | `group_id` | `group` |

---

## 10. 相關文件

- [各平台特性文件](../platform-guide/README.md) - 你可以訪問此文件來了解各個平台特性以及已知的擴展事件和訊息段等。
- [會話類型標準](session-types.md) - 會話類型定義和映射關係
- [發送方法規範](send-method-spec.md) - Send 類別的方法命名、參數規範及反向轉換要求
- [API 回應標準](api-response.md) - 适配器 API 回應格式標準
- [API 動作標準](api-action-spec.md) - OneBot12 標準 API 動作的統一介面



### API 响应标准

# ErisPulse 适配器標準化回傳規範

## 1. 說明  
為什麼會有這個規範？  

為了確保各平台發送介面返回的統一性與 OneBot12 兼容性，ErisPulse 適配器在 API 回應格式上採用了 OneBot12 定義的消息發送回傳結構標準。  

不過 ErisPulse 的協定有一些特殊性定義：  
- 1. 基礎欄位中，`message_id` 是必需的，但 OneBot12 標準中並無此欄位  
- 2. 回傳內容中需要添加 `{platform_name}_raw` 欄位，用於存放原始回應資料

## 2. 基礎返回結構  
所有動作響應必須包含以下基礎字段：

| 字段名 | 數據類型 | 必選 | 說明 |
|-------|---------|------|------|
| status | string | 是 | 執行狀態，必須是"ok"或"failed" |
| retcode | int64 | 是 | 返回碼，遵循OneBot12返回碼規則 |
| data | any | 是 | 响应数据，成功时包含请求结果，失败时为null |
| message_id | string | 是 | 消息ID，用於標識消息，沒有則為空字串 |
| message | string | 是 | 錯誤信息，成功時為空字串 |
| {platform_name}_raw | any | 否 | 原始響應數據 |

可選字段：
| 字段名 | 數據類型 | 必選 | 說明 |
|-------|---------|------|------|
| echo | string | 否 | 當請求中包含echo字段時，原樣返回 |

## 3. 完整欄位規範

### 3.1 通用欄位

#### 成功回應範例
```json
{
    "status": "ok",
    "retcode": 0,
    "data": {
        "message_id": "1234",
        "time": 1632847927.599013
    },
    "message_id": "1234",
    "message": "",
    "echo": "1234",
    "telegram_raw": {...}
}
```

#### 失敗回應範例
```json
{
    "status": "failed",
    "retcode": 10003,
    "data": null,
    "message_id": "",
    "message": "缺少必要參數: user_id",
    "echo": "1234",
    "telegram_raw": {...}
}
```

### 3.2 回傳碼規範

#### 0 成功（OK）
- 0: 成功（OK）

#### 1xxxx 動作請求錯誤（Request Error）
| 錯誤碼 | 錯誤名 | 說明 |
|-------|-------|------|
| 10001 | Bad Request | 無效的動作請求 |
| 10002 | Unsupported Action | 不支援的動作請求 |
| 10003 | Bad Param | 無效的動作請求參數 |
| 10004 | Unsupported Param | 不支援的動作請求參數 |
| 10005 | Unsupported Segment | 不支援的訊息段類型 |
| 10006 | Bad Segment Data | 無效的訊息段參數 |
| 10007 | Unsupported Segment Data | 不支援的訊息段參數 |
| 10101 | Who Am I | 未指定機器人帳號 |
| 10102 | Unknown Self | 未知的機器人帳號 |

#### 2xxxx 動作處理器錯誤（Handler Error）
| 錯誤碼 | 錯誤名 | 說明 |
|-------|-------|------|
| 20001 | Bad Handler | 動作處理器實作錯誤 |
| 20002 | Internal Handler Error | 動作處理器執行時拋出例外 |

#### 3xxxx 動作執行錯誤（Execution Error）
| 錯誤碼範圍 | 錯誤類型 | 說明 |
|-----------|---------|------|
| 31xxx | Database Error | 資料庫錯誤 |
| 32xxx | Filesystem Error | 檔案系統錯誤 |
| 33xxx | Network Error | 網路錯誤 |
| 34xxx | Platform Error | 機器人平台錯誤 |
| 35xxx | Logic Error | 動作邏輯錯誤 |
| 36xxx | I Am Tired | 實現決定罷工 |

#### 保留錯誤段
- 4xxxx、5xxxx: 保留段，不應使用
- 6xxxx～9xxxx: 其他錯誤段，供實現自訂使用

## 4. 實現要求
1. 所有回應必須包含 status、retcode、data 和 message 欄位
2. 當請求中包含非空 echo 欄位時，回應必須包含相同值的 echo 欄位
3. 回傳碼必須嚴格遵循 OneBot12 規範
4. 錯誤訊息 (message) 應當是人類可讀的描述

## 5. 扩展規範

ErisPulse 在 OneBot12 標準返回結構之上做了以下擴展：

### 5.1 `message_id` 必選字段

OneBot12 標準中 `message_id` 位於 `data` 對象內部且非強制。ErisPulse 將其提升為頂層**必選**字段：

- 無法獲取 `message_id` 時應設為空字串 `""`
- 確保 `message_id` 始終存在，模組無需做 null 檢查

### 5.2 `{platform}_raw` 原始回應字段

回應值中應包含 `{platform}_raw` 字段，存放平台原始回應數據的完整副本：

```json
{
    "status": "ok",
    "retcode": 0,
    "data": {"message_id": "1234", "time": 1632847927},
    "message_id": "1234",
    "message": "",
    "telegram_raw": {
        "ok": true,
        "result": {"message_id": 1234, "date": 1632847927, ...}
    }
}
```

**要求**：
- `{platform}_raw` 必須是原始回應的深拷貝，而非引用
- `platform` 必須與適配器註冊時的平台名完全一致（大小寫敏感）
- 原始回應中的錯誤資訊也應保留，便於除錯

### 5.3 框架擴展回應碼（34xxx 平台錯誤段的低三位自訂）

OneBot12 規範允許實現自訂 `3xxxx` 的低三位。`34xxx` 語意為 **Platform Error**
（機器人平台錯誤，如平台限制導致失敗）。`34xxx` 內部按職責分層使用：

| 低三位段 | 歸屬 | 用途 |
|---------|------|------|
| `340xx` | 適配器實現 | 請求操作族（Request Not Found / Already Handled / Not Supported / Permission Denied，見 request-action-spec §7） |
| `341xx`～`345xx` | 適配器實現 | 平台側權限 / 風控 / 帳號限制等錯誤（實現自定低三位，原始錯誤放 `{platform}_raw`） |
| `346xx` | **ErisPulse 框架（保留）** | 框架自身攔截與通用失敗，適配器/模組請勿占用 |
| `347xx`～`349xx` | 適配器實現 | 其它平台執行錯誤 |

ErisPulse 框架目前使用的 `346xx` 碼：

| 錯誤碼 | 錯誤名 | 說明 |
|-------|-------|------|
| 34600 | SDK Failure | 框架通用失敗（`make_error()` 預設回傳碼） |
| 34601 | Action Denied | 出站動作被控制面禁用（`scope.actions`），呼叫未發起，直接回傳該回應 |

> 職責區分：`34601` 是**框架在呼叫前攔截**（模組根本沒資格發起動作）；
> `34004` / `34xxx` 平台碼是**動作已發出但平台拒絕**（如 Bot 無權限、被風控）。
> 模組判斷權限問題時同時檢查這兩種：先看 `34601`（自己模組被 scope 禁），
> 再看 `34xxx`（平台側限制）。

回應結構為 §2 標準失敗回應：

```json
{
    "status": "failed",
    "retcode": 34601,
    "data": null,
    "message_id": "",
    "message": "action 'send' denied by scope.actions"
}
```

### 5.4 適配器實現檢查清單

- [ ] 包含 `status`, `retcode`, `data`, `message_id`, `message` 字段
- [ ] 回應碼遵循 OneBot12 規範（詳見 §3.2）
- [ ] `message_id` 始終存在（無法獲取時為空字串）
- [ ] `{platform}_raw` 包含平台原始回應數據

## 6. 注意事項
- 對於 3xxxx 錯誤碼，低三位可由實作自行定義
- 避免使用保留錯誤區段 (4xxxx、5xxxx)
- **`34600` / `34601` 為 ErisPulse 框架保留碼**（見 §5.3），適配器/模組應避免使用
- 錯誤訊息應當簡潔明瞭，便於除錯



### 发送方法规范

# ErisPulse 發送方法規範

本文檔定義了 ErisPulse 適配器中 Send 類發送方法的命名規範、參數規範和反向轉換要求。

## 1. 標準方法命名

所有發送方法使用 **大駝峰命名法（PascalCase）**，首字母大寫。

### 1.1 標準發送方法

| 方法名 | 說明 | 參數類型 |
|-------|------|---------|
| `Text` | 發送文字訊息 | `str` |
| `Image` | 發送圖片 | `bytes` \| `str` (URL/路徑) |
| `Voice` | 發送語音 | `bytes` \| `str` (URL/路徑) |
| `Video` | 發送影片 | `bytes` \| `str` (URL/路徑) |
| `File` | 發送檔案 | `bytes` \| `str` (URL/路徑) |
| `At` | @使用者/群組 | `str` (user_id) |
| `Face` | 發送表情 | `str` (emoji) |
| `Reply` | 回覆訊息 | `str` (message_id) |
| `Forward` | 轉發訊息 | `str` (message_id) |
| `Markdown` | 發送 Markdown 訊息 | `str` |
| `HTML` | 發送 HTML 訊息 | `str` |
| `Card` | 發送卡片訊息 | `dict` |

### 1.2 鏈式修飾方法

| 方法名 | 說明 | 參數類型 |
|-------|------|---------|
| `At` | @使用者（可多次呼叫） | `str` (user_id) |
| `AtAll` | @全體成員 | 無 |
| `Reply` | 回覆訊息 | `str` (message_id) |

### 1.3 協議方法

| 方法名 | 說明 | 是否必須 |
|-------|------|---------|
| `Raw_ob12` | 發送 OneBot12 格式訊息段 | 必須 |

**`Raw_ob12` 是必須實作的方法**。這是適配器的核心職責之一：接收 OneBot12 標準訊息段並轉換為平台原生 API 呼叫。`Raw_ob12` 是反向轉換（OneBot12 → 平台）的統一入口，確保模組可以不依賴平台特有的方法，直接使用標準訊息段發送訊息。

**未重寫 `Raw_ob12` 時的行為**：基類預設實作會記錄 **error 級別**日誌並返回標準錯誤回應格式（`status: "failed"`, `retcode: 10002`），提示適配器開發者必須實作此方法。

### 1.4 推薦的擴展命名約定

適配器如需支援發送非 OneBot12 格式的原始資料（如平台特定 JSON、XML 等），推薦使用以下命名約定：

| 推薦方法名 | 說明 |
|-----------|------|
| `Raw_json` | 發送任意 JSON 資料 |
| `Raw_xml` | 發送任意 XML 資料 |

**注意**：這些方法**不是**基類提供的預設方法，也不強制要求實作。它們僅作為命名約定，適配器可依需要自行定義。如果適配器不支援這些格式，則無需定義。

**訊息建構器（MessageBuilder）**：ErisPulse 提供了 `MessageBuilder` 工具類，用於方便地建構 OneBot12 訊息段列表，配合 `Raw_ob12` 使用。詳見 [訊息建構器](#11-訊息建構器-messagebuilder) 章節。

## 2. 參數規範詳解

### 2.1 媒體消息參數規範

媒體消息（`Image`、`Voice`、`Video`、`File`）支援兩種參數類型：

#### 2.1.1 字符串參數（URL 或文件路徑）

**格式：** `str`

**支援類型：**
- **URL**：網路資源位址（如 `https://example.com/image.jpg`）
- **文件路徑**：本機文件路徑（如 `/path/to/file.jpg` 或 `C:\\path\\to\\file.jpg`）

**使用場景：**
- 文件已在網路上，直接發送 URL
- 文件在本機磁碟，發送文件路徑
- 希望適配器自動處理文件上傳

**推薦：** 優先使用 URL，如果 URL 不可用則使用本機文件路徑

**示例：**
```python
# 使用 URL
send.Image("https://example.com/image.jpg")

# 使用本機文件路徑
send.Image("/path/to/local/image.jpg")
send.Image("C:\\path\\to\\local\\image.jpg")
```

#### 2.1.2 二進制數據參數

**格式：** `bytes`

**使用場景：**
- 文件已在記憶體中（如從網路下載、從其他來源讀取）
- 需要處理後再發送（如圖片壓縮、格式轉換）
- 避免重複讀取文件

**注意事項：**
- 大文件上傳可能消耗較多記憶體
- 建議設定合理的文件大小限制

**示例：**
```python
# 從網路讀取後發送
import requests
image_data = requests.get("https://example.com/image.jpg").content
send.Image(image_data)

# 從文件讀取後發送
with open("/path/to/local/image.jpg", "rb") as f:
    image_data = f.read()
send.Image(image_data)
```

#### 2.1.3 參數處理優先級

當適配器接收到媒體消息參數時，應按以下順序處理：

1. **URL 參數**：直接使用 URL 發送（部分平台適配器可能存在 URL 下載後再上傳的操作）
2. **文件路徑**：檢測是否為本機路徑，若是則上傳文件
3. **二進制數據**：直接上傳二進制數據

**適配器實現建議：**
```python
def Image(self, image: Union[bytes, str]):
    if isinstance(image, str):
        # 判斷是 URL 還是本機路徑
        if image.startswith(("http://", "https://")):
            # URL 直接發送
            return self._send_image_by_url(image)
        else:
            # 本機路徑，讀取後上傳
            with open(image, "rb") as f:
                return self._upload_image(f.read())
    elif isinstance(image, bytes):
        # 二進制數據，直接上傳
        return self._upload_image(image)
```

### 2.2 @用戶參數規範

**方法：** `At`（修飾方法）

**參數：** `user_id` (`str`)

**要求：**
- `user_id` 應為字串類型的用戶標識符
- 不同平台的 `user_id` 格式可能不同（數字、UUID、字串等）
- 適配器負責將 `user_id` 轉換為平台特定的格式
- 注意需要把真正的發送方法呼叫放在最後的位置

**示例：**
```python
# 單個 @ 用戶
Send.To("group", "g123").At("123456").Text("你好")

# 多個 @ 用戶（鏈式呼叫）
send.To("group", "g123").At("123456").At("789012").Text("大家好")
```

### 2.3 回覆消息參數規範

**方法：** `Reply`（修飾方法）

**參數：** `message_id` (`str`)

**要求：**
- `message_id` 應為字串類型的消息標識符
- 應為之前收到的消息的 ID
- 某些平台可能不支援回覆功能，適配器應優雅降級

**示例：**
```python
send.To("group", "g123").Reply("msg_123456").Text("收到")
```

## 3. 平台特有方法命名

**不建議**在 Send 類中直接添加平台前綴方法。建議使用通用方法名或 `Raw_{協議}` 方法。

**不建議：**
```python
def YunhuForm(self, form_id: str):  # ❌ 不建議
    pass

def TelegramSticker(self, sticker_id: str):  # ❌ 不建議
    pass
```

**建議：**
```python
def Form(self, form_id: str):  # ✅ 通用方法名
    pass

def Sticker(self, sticker_id: str):  # ✅ 通用方法名
    pass

def Raw_ob12(self, message):  # ✅ 發送 OneBot12 格式
    pass
```

**擴展方法要求**：
- 方法名使用 PascalCase，不加平台前綴
- 必須返回 `asyncio.Task` 對象
- 必須提供完整的類型註解和文件字串
- 參數設計應盡量與標準方法風格一致

## 4. 參數命名規範

| 參數名 | 說明 | 類型 |
|-------|------|------|
| `text` | 文本內容 | `str` |
| `url` / `file` | 檔案 URL 或二進位資料 | `str` / `bytes` |
| `user_id` | 使用者 ID | `str` / `int` |
| `group_id` | 群組 ID | `str` / `int` |
| `message_id` | 消息 ID | `str` |
| `data` | 資料物件（例如卡片資料） | `dict` |

## 5. 返回值規範

- **發送方法**（例如 `Text`, `Image`）：必須返回 `asyncio.Task` 物件
- **修飾方法**（例如 `At`, `Reply`, `AtAll`）：必須返回 `self` 以支援鏈式呼叫

---

## 6. 反轉轉換規範（OneBot12 → 平台）

適配器不僅需要將平台原生事件轉換為 OneBot12 格式（正向轉換），還**必須**提供將 OneBot12 消息段轉換回平台原生 API 調用的能力（反向轉換）。反向轉換的統一入口是 `Raw_ob12` 方法。

### 6.1 轉換模型

```
正向轉換（接收方向）                反向轉換（發送方向）
─────────────────                ─────────────────
平台原生事件                       OneBot12 消息段列表
    │                                  │
    ▼                                  ▼
Converter.convert()               Send.Raw_ob12()
    │                                  │
    ▼                                  ▼
OneBot12 標準事件                  平台原生 API 調用
（含 {platform}_raw）             （返回標準響應格式）
```

**核心對稱性**：正向轉換保留原始數據在 `{platform}_raw` 中，反向轉換接受 OneBot12 標準格式並還原為平台調用。

### 6.2 `Raw_ob12` 實現規範

`Raw_ob12` 接收 OneBot12 標準消息段列表，必須將其轉換為平台原生 API 調用。

**方法簽名**：

```python
def Raw_ob12(self, message_segments: List[Dict]) -> asyncio.Task:
    """
    發送 OneBot12 標準消息段

    :param message_segments: OneBot12 消息段列表
        [
            {"type": "text", "data": {"text": "Hello"}},
            {"type": "image", "data": {"file": "https://..."}},
            {"type": "mention", "data": {"user_id": "123"}},
        ]
    :return: asyncio.Task，await 後返回標準響應格式
    """
```

**實現要求**：

1. **必須處理所有標準消息段類型**：至少支援 `text`、`image`、`audio`、`video`、`file`、`mention`、`reply`
2. **必須處理平台擴展消息段**：對於 `{platform}_xxx` 類型的消息段，轉換為平台對應的原生調用
3. **必須返回標準響應格式**：遵循 [API 響應標準](api-response.md)
4. **不支援的消息段應跳過並記錄警告**，不應拋出異常導致整條消息發送失敗

### 6.3 消息段轉換規則

#### 6.3.1 標準消息段轉換

適配器必須實現以下標準消息段的轉換：

| OneBot12 消息段 | 轉換要求 |
|----------------|---------|
| `text` | 直接使用 `data.text` |
| `image` | 根據 `data.file` 類型處理：URL 直接使用，bytes 上傳，本地路徑讀取後上傳 |
| `audio` | 同 image 處理邏輯 |
| `video` | 同 image 處理邏輯 |
| `file` | 同 image 處理邏輯，注意 `data.filename` |
| `mention` | 轉換為平台的 @用戶 機制（如 Telegram 的 `entities`，雲湖的 `at_uid`） |
| `reply` | 轉換為平台的回覆引用機制 |
| `face` | 轉換為平台的表情發送機制，不支援則跳過 |
| `location` | 轉換為平台的位置發送機制，不支援則跳過 |

#### 6.3.2 平台擴展消息段轉換

對於帶平台前綴的消息段，適配器應識別並轉換：

```python
def _convert_ob12_segments(self, segments: List[Dict]) -> Any:
    """將 OneBot12 消息段轉換為平台原生格式"""
    platform_prefix = f"{self._platform_name}_"
    
    for segment in segments:
        seg_type = segment["type"]
        seg_data = segment["data"]
        
        if seg_type.startswith(platform_prefix):
            # 平台擴展消息段 → 平台原生調用
            self._handle_platform_segment(seg_type, seg_data)
        elif seg_type in self._standard_segment_handlers:
            # 標準消息段 → 平台等價操作
            self._standard_segment_handlers[seg_type](seg_data)
        else:
            # 未知消息段 → 記錄警告並跳過
            logger.warning(f"不支援的消息段類型: {seg_type}")
```

#### 6.3.3 複合消息段處理

一條消息可能包含多個消息段，適配器需要正確處理複合消息：

```python
# 模塊發送包含文本+圖片+@用戶 的消息
await send.Raw_ob12([
    {"type": "mention", "data": {"user_id": "123"}},
    {"type": "text", "data": {"text": "你好"}},
    {"type": "image", "data": {"file": "https://example.com/img.jpg"}}
])
```

**處理策略**：
- **優先合併**：如果平台支援在一條消息中同時包含文本、圖片、@等，應合併發送
- **退而拆分**：如果平台不支援合併，按順序拆分為多條消息發送
- **保持順序**：消息段的發送順序應與列表順序一致

### 6.4 `Raw_ob12` 與標準方法的關係

適配器的標準發送方法（`Text`、`Image` 等）**已由 `SendDSL` 基類內建實現並預設委託給 `Raw_ob12`**，適配器子類無需重複實現：

```python
class Send(SendDSL):
    def Raw_ob12(self, message_segments: List[Dict]) -> asyncio.Task:
        """核心實現：OneBot12 消息段 → 平台 API（必須實現）"""
        return asyncio.create_task(self._send_ob12(message_segments))

    # Text/Image/Voice/Video/File 已從基類繼承，自動委託 Raw_ob12
    # 如需平台特定邏輯，可覆蓋單個方法：
    # def Text(self, text: str) -> asyncio.Task:
    #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

**好處**：
- 轉換邏輯集中在 `Raw_ob12` 一處，減少重複程式碼
- 標準方法和 `Raw_ob12` 行為完全一致
- 模組無論使用 `Text()` 還是 `Raw_ob12()` 都能得到相同結果
- 基類提供類型簽名，IDE 能補全標準方法

### 6.5 實現範例

```python
class YunhuSend(SendDSL):
    """雲湖平台 Send 實現"""
    
    def Raw_ob12(self, message_segments: list) -> asyncio.Task:
        """OneBot12 消息段 → 雲湖 API 調用"""
        return asyncio.create_task(self._do_send(message_segments))
    
    async def _do_send(self, segments: list) -> dict:
        """實際發送邏輯"""
        # 1. 解析修飾器狀態
        at_users = self._at_users or []
        reply_to = self._reply_to
        at_all = self._at_all
        
        # 2. 轉換消息段
        yunhu_elements = []
        for seg in segments:
            seg_type = seg["type"]
            seg_data = seg["data"]
            
            if seg_type == "text":
                yunhu_elements.append({"type": "text", "content": seg_data["text"]})
            elif seg_type == "image":
                yunhu_elements.append({"type": "image", "url": seg_data["file"]})
            elif seg_type == "mention":
                at_users.append(seg_data["user_id"])
            elif seg_type == "reply":
                reply_to = seg_data["message_id"]
            elif seg_type == "yunhu_form":
                # 平台擴展消息段
                yunhu_elements.append({"type": "form", "form_id": seg_data["form_id"]})
            else:
                logger.warning(f"雲湖不支援的消息段: {seg_type}")
        
        # 3. 調用雲湖 API
        response = await self._call_yunhu_api(yunhu_elements, at_users, reply_to, at_all)
        
        # 4. 返回標準響應格式
        return {
            "status": "ok" if response["code"] == 0 else "failed",
            "retcode": response["code"],
            "data": {"message_id": response.get("msg_id", ""), "time": int(time.time())},
            "message_id": response.get("msg_id", ""),
            "message": "",
            "yunhu_raw": response
        }
```

---

## 7. 方法發現

模組開發者可以透過 API 查詢適配器支援的發送方法：

```python
from ErisPulse import adapter

# 列出所有發送方法
methods = adapter.list_sends("myplatform")
# ["Batch", "Form", "Image", "Recall", "Sticker", "Text", ...]

# 查看方法詳情
info = adapter.send_info("myplatform", "Form")
# {
#     "name": "Form",
#     "parameters": [{"name": "form_id", "type": "str", ...}],
#     "return_type": "Awaitable[Any]",
#     "docstring": "發送雲湖表單"
# }
```

---

## 8. 已註冊的發送方法擴展

| 平台 | 方法名 | 說明 |
|------|--------|------|
| onebot12 | `Mention` | @用戶（OneBot12 風格） |
| onebot12 | `Sticker` | 發送貼紙 |
| onebot12 | `Location` | 發送位置 |
| onebot12 | `Recall` | 撤回消息 |
| onebot12 | `Edit` | 編輯消息 |
| onebot12 | `Batch` | 批量發送 |

> **注意**：發送方法不加平台前綴，不同平台的同名方法可以有不同的實現。

## 9. 適配器開發注意事項

關於如何正確重寫 `BaseAdapter`、`Send`、`Request` 的 `__init__`，詳見 [適配器開發入門 - `__init__` 注意事項](../developer-guide/adapters/getting-started.md#init-注意事項)。

## 10. 适配器實現檢查清單

### 發送方法
- [ ] 標準方法（`Text`, `Image` 等）已實現
- [ ] 返回值均為 `asyncio.Task`
- [ ] 修飾方法（`At`, `Reply`, `AtAll`）返回 `self`
- [ ] 平台擴展方法使用 PascalCase，無平台前綴
- [ ] 所有方法有完整的類型註解和文件字串

### 反向轉換
- [ ] `Raw_ob12` **已實現**（必須，不可跳過）
- [ ] `Raw_ob12` 能處理所有標準消息段（`text`, `image`, `audio`, `video`, `file`, `mention`, `reply`）
- [ ] `Raw_ob12` 能處理平台擴展消息段（`{platform}_xxx` 類型）
- [ ] 標準發送方法（`Text`, `Image` 等）內部委託給 `Raw_ob12`，而非獨立實現轉換邏輯
- [ ] 不支援的消息段跳過並記錄警告，不拋出異常
- [ ] 複合消息段正確處理（合併或按序拆分）

## 11. 消息建構器（MessageBuilder）

`MessageBuilder` 是 ErisPulse 提供的消息段建構工具，配合 `Raw_ob12` 使用，簡化 OneBot12 消息段的建構過程。

### 11.1 導入

```python
from ErisPulse.Core import MessageBuilder
# 或
from ErisPulse.Core.Event import MessageBuilder
```

### 11.2 鏈式呼叫建構

```python
# 建構包含文字、圖片、@使用者的消息
segments = (
    MessageBuilder()
    .mention("123456")
    .text("你好，看看這張圖")
    .image("https://example.com/img.jpg")
    .reply("msg_789")
    .build()
)

# 發送
await adapter.Send.To("group", "456").Raw_ob12(segments)
```

### 11.3 快速建構單段

```python
# 快速建構單個消息段（返回 list[dict]，可直接傳給 Raw_ob12）
await adapter.Send.To("user", "123").Raw_ob12(MessageBuilder.text("Hello"))
await adapter.Send.To("group", "456").Raw_ob12(MessageBuilder.image("https://..."))
await adapter.Send.To("group", "456").Raw_ob12(MessageBuilder.mention("123"))
await adapter.Send.To("group", "456").Raw_ob12(MessageBuilder.reply("msg_id"))
await adapter.Send.To("group", "456").Raw_ob12(MessageBuilder.at_all())
```

### 11.4 配合 Event.reply_ob12 使用

```python
from ErisPulse.Core import MessageBuilder

@message()
async def handle(event: Event):
    await event.reply_ob12(
        MessageBuilder()
        .mention(event.get_user_id())
        .text("收到你的消息")
        .build()
    )
```

### 11.5 支援的消息段方法

| 方法 | 說明 | data 字段 |
|------|------|----------|
| `text(text)` | 文字 | `text` |
| `image(file)` | 圖片 | `file` |
| `audio(file)` | 音頻 | `file` |
| `video(file)` | 視頻 | `file` |
| `file(file, filename=None)` | 檔案 | `file`, `filename`(可選) |
| `mention(user_id, user_name=None)` | @使用者 | `user_id`, `user_name`(可選) |
| `at(user_id, user_name=None)` | @使用者（`mention` 的別名） | 同 `mention` |
| `reply(message_id)` | 回覆 | `message_id` |
| `at_all()` | @全體成員 | `{}` |
| `custom(type, data)` | 自定義/平台擴展 | 自定義 |

### 11.6 工具方法

```python
builder = MessageBuilder().text("基礎內容")

# 複製（深拷貝）
msg1 = builder.copy().image("img1").build()
msg2 = builder.copy().image("img2").build()

# 清空
builder.clear().text("新內容").build()

# 判斷是否為空
if builder:
    print(f"包含 {len(builder)} 個消息段")
```

---

## 12. 相關文件

- [事件轉換標準](event-conversion.md) - 完整的事件轉換規範、擴展命名和訊息段標準
- [API 回應標準](api-response.md) - 適配器 API 回應格式標準
- [會話類型標準](session-types.md) - 會話類型定義和映射關係
- [請求操作規範](request-action-spec.md) - 請求事件欄位要求、HandleRequest DSL 及適配器實作要求



### 请求操作规范

# ErisPulse 請求操作規範

本文檔定義了 ErisPulse 適配器中請求事件操作的標準化規範，包括請求事件的欄位要求、Request DSL 的使用方式和適配器實現要求。

## 1. 概述

請求事件（`type: "request"`）是 OneBot12 標準中定義的特殊事件類型，代表需要 Bot 做出決策的請求（如好友請求、群邀請等）。

與消息事件不同，請求事件需要**雙向互動**：
1. **接收**：適配器將平台原生請求轉換為標準請求事件
2. **響應**：模組通過 `Request` DSL 或 `Event.approve()`/`Event.reject()` 執行操作

```
平台原生請求事件
    │
    ▼
Converter.convert()        ← 適配器實現（正向轉換）
    │
    ▼
標準請求事件 (含 request_id)
    │
    ├─→ 模組處理器 @request.on_friend_request()
    │       │
    │       ├─→ event.approve()     ← 同意請求
    │       └─→ event.reject()      ← 拒絕請求
    │               │
    │               ▼
    │       adapter.Request(request_id).accept()
    │               │
    │               ▼
    │       BaseAdapter.Request.accept()  ← 適配器重寫
    │               │
    │               ▼
    │       平台 API 調用
    │
    └─→ 或直接通過適配器操作
            await adapter.Request("req_id").accept()
```

## 2. 請求事件字段要求

### 2.1 標準字段

請求事件除必須包含 OneBot12 標準字段外，還需包含以下字段：

| 字段 | 類型 | 必選 | 說明 |
|------|------|------|------|
| `request_id` | string | **強烈推薦** | 請求標識符，用於同意/拒絕操作 |
| `user_id` | string | 是 | 請求發起者ID |
| `user_nickname` | string | 否 | 請求發起者暱稱 |
| `comment` | string | 否 | 請求附言 |

### 2.2 `request_id` 字段

`request_id` 是請求操作的核心標識符：

- **用途**：標識一個可操作的請求，供 `Request` DSL 使用
- **生成規則**：
  - 優先使用平台原生的請求標識（如 OneBot11 的 `flag` 字段、Telegram 的 `chat_invite_link` 等）
  - 如果平台沒有原生請求ID，適配器應生成一個唯一標識（建議格式：`{platform}_{timestamp}_{user_id}`）
- **唯一性**：在同一平台範圍內應保持唯一
- **缺失行為**：當 `request_id` 缺失時，`event.approve()` / `event.reject()` 將拋出 `ValueError`

### 2.3 請求事件示例

```json
{
  "id": "evt_123456",
  "time": 1752241225,
  "type": "request",
  "detail_type": "friend",
  "platform": "onebot11",
  "self": {
    "platform": "onebot11",
    "user_id": "bot_123"
  },
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "comment": "請加好友",
  "request_id": "flag_abc123",
  "onebot11_raw": {...},
  "onebot11_raw_type": "request"
}
```

## 3. Request DSL

### 3.1 鏈式呼叫

`Request` 提供與 `Send` 風格一致的鏈式呼叫介面：

```python
# 基本用法
await adapter.Request("req_id").accept()
await adapter.Request("req_id").reject()

# 指定 Bot 賬號
await adapter.Request("req_id").Using("bot1").accept()

# 附帶備註（透過 kwargs）
await adapter.Request("req_id").accept(comment="歡迎")
await adapter.Request("req_id").reject(comment="暫不添加")

# 組合使用
await adapter.Request("req_id").Using("bot1").accept(comment="歡迎")
```

### 3.2 方法列表

| 方法 | 說明 | 返回值 |
|------|------|--------|
| `Using(account_id)` | 指定執行操作的 Bot 賬號 | `RequestDSL`（支援鏈式呼叫） |
| `accept(**kwargs)` | 同意請求 | `asyncio.Task`（await 後返回標準回應） |
| `reject(**kwargs)` | 拒絕請求 | `asyncio.Task`（await 後返回標準回應） |

### 3.3 返回值格式

操作返回標準 API 回應格式：

**成功**：
```json
{
    "status": "ok",
    "retcode": 0,
    "data": null,
    "message_id": "",
    "message": ""
}
```

**失敗**：
```json
{
    "status": "failed",
    "retcode": 34001,
    "data": null,
    "message_id": "",
    "message": "請求已過期或不存在"
}
```

**未實現**（適配器未重寫 `accept`/`reject`）：
```json
{
    "status": "failed",
    "retcode": 10002,
    "data": null,
    "message_id": "",
    "message": "平台 MyAdapter 未實現請求操作 (accept)"
}
```

## 4. Event 便捷方法

`Event` 包裝類提供了便捷方法，適合在請求事件處理器中使用：

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    # 檢查請求ID
    request_id = event.get_request_id()
    if not request_id:
        print("警告：請求事件缺少 request_id")
        return
    
    # 同意請求
    result = await event.approve()
    
    # 或拒絕請求
    # result = await event.reject(comment="暫不添加好友")
    
    # 檢查結果
    if result.get("status") == "ok":
        print("操作成功")
    else:
        print(f"操作失敗: {result.get('message')}")
```

### 4.1 Event 方法列表

| 方法 | 說明 | 回傳值 |
|------|------|--------|
| `get_request_id()` | 取得請求ID | `str` |
| `approve(comment=None)` | 同意當前請求事件 | 標準回應格式 |
| `reject(comment=None)` | 拒絕當前請求事件 | 標準回應格式 |

## 5. 适配器實現要求

### 5.1 轉換器要求

適配器的轉換器在轉換請求事件時，**必須**正確設置 `request_id` 欄位：

```python
def convert_request_event(self, raw_event: dict) -> dict:
    """轉換平台原生請求事件"""
    return {
        "id": self._generate_event_id(raw_event),
        "time": int(time.time()),
        "type": "request",
        "detail_type": self._map_request_type(raw_event),  # "friend" 或 "group"
        "platform": self._platform_name,
        "self": {
            "platform": self._platform_name,
            "user_id": str(self._bot_id),
        },
        "user_id": str(raw_event.get("user_id", "")),
        "user_nickname": raw_event.get("nickname", ""),
        "comment": raw_event.get("message", ""),
        "request_id": self._extract_request_id(raw_event),  # ← 關鍵欄位
        f"{self._platform_name}_raw": raw_event,
        f"{self._platform_name}_raw_type": raw_event.get("type", ""),
    }

def _extract_request_id(self, raw_event: dict) -> str:
    """
    從平台原生事件提取請求ID
    
    优先使用平台原生的请求标识，若无则生成唯一ID
    """
    # 优先使用平台原生ID
    if flag := raw_event.get("flag"):
        return str(flag)
    if request_key := raw_event.get("request_key"):
        return str(request_key)
    
    # 兜底：生成唯一ID
    import hashlib
    raw = f"{self._platform_name}_{raw_event.get('user_id')}_{raw_event.get('timestamp')}"
    return hashlib.md5(raw.encode()).hexdigest()
```

### 5.2 Request 內部類實現

適配器在 `Request` 內部類中重寫 `accept` 和 `reject` 即可：

```python
from ErisPulse.Core import BaseAdapter, RequestDSL

class MyAdapter(BaseAdapter):
    
    class Request(RequestDSL):
        """MyPlatform 請求操作實現"""
        
        def accept(self, **kwargs):
            """
            同意請求
            
            :param kwargs: 扩展参数，如 comment="备注"
            :return: asyncio.Task
            """
            async def _do():
                try:
                    result = await self._adapter.call_api(
                        endpoint="/set_request",
                        request_id=self._request_id,
                        approve=True,
                        **kwargs,
                    )
                    return {
                        "status": "ok" if result.get("code") == 0 else "failed",
                        "retcode": result.get("code", 0),
                        "data": None,
                        "message_id": "",
                        "message": result.get("message", ""),
                    }
                except Exception as e:
                    return {
                        "status": "failed",
                        "retcode": 34001,
                        "data": None,
                        "message_id": "",
                        "message": f"請求操作失敗: {e}",
                    }
            
            return self._create_task(_do())
        
        def reject(self, **kwargs):
            """拒絕請求"""
            async def _do():
                try:
                    result = await self._adapter.call_api(
                        endpoint="/set_request",
                        request_id=self._request_id,
                        approve=False,
                        **kwargs,
                    )
                    return {
                        "status": "ok" if result.get("code") == 0 else "failed",
                        "retcode": result.get("code", 0),
                        "data": None,
                        "message_id": "",
                        "message": result.get("message", ""),
                    }
                except Exception as e:
                    return {
                        "status": "failed",
                        "retcode": 34001,
                        "data": None,
                        "message_id": "",
                        "message": f"請求操作失敗: {e}",
                    }
            
            return self._create_task(_do())
```

### 5.3 平台不支援請求操作

如果平台本身不支援好友請求/群邀請操作（如某些平台自動處理請求），適配器可以：

1. **不重寫 `Request` 內部類**：使用基類預設實現，調用 `accept()`/`reject()` 時返回 `retcode=10002`
2. **在轉換時跳過 `request_id`**：不生成 `request_id`，讓 `event.approve()` 抛出 `ValueError`
3. **記錄日誌**：在 `accept`/`reject` 中記錄警告並返回適當錯誤碼

### 5.4 總結：Send 與 Request 並行

適配器有兩個並行的 DSL 內部類，各司其職：

```
BaseAdapter
├── Send(SendDSL)     ← 消息發送
│   ├── Raw_ob12()    ← 必須實現
│   ├── Text()        ← 推薦實現
│   └── Image()       ← 按需實現
│
└── Request(RequestDSL) ← 請求操作
    ├── accept()        ← 按需實現
    └── reject()        ← 按需實現
```

### 5.5 適配器 `__init__` 注意事項

重寫 `Request` 內部類的 `__init__` 時，必須透傳參數並調用 `super().__init__()`，詳見 [適配器開發入門 - `__init__` 注意事項](../developer-guide/adapters/getting-started.md#init-注意事项)（`Request` 同理，參數為 `adapter, request_id, account_id`）。

## 6. 适配器實現檢查清單

### 基礎要求
- [ ] 若重寫了 `__init__`，已調用 `super().__init__()`（確保 Send / Request 工廠初始化）

### 請求事件轉換
- [ ] 請求事件包含 `request_id` 字段（強烈推薦）
- [ ] `detail_type` 正確映射為 `"friend"` 或 `"group"`
- [ ] 保留平台原始數據在 `{platform}_raw` 字段中
- [ ] `request_id` 生成規則有文件說明

### 請求操作
- [ ] `Request` 內部類已實現（如平台支援請求操作）
- [ ] `accept()` 方法已實現
- [ ] `reject()` 方法已實現
- [ ] 操作返回標準 API 回應格式
- [ ] 不支援的操作返回 `retcode=10002`
- [ ] 網路錯誤返回 `retcode=33xxx`（遵循 API 回應標準）

## 7. 錯誤碼擴展

請求操作相關的**適配器實現層**推薦錯誤碼（遵循 [API 响应标准](api-response.md) §3.2，  
落在 `34xxx` 平台錯誤段的低三位自定義）：

| 錯誤碼 | 錯誤名 | 說明 |
|-------|-------|------|
| 34001 | Request Not Found | 請求不存在或已過期 |
| 34002 | Request Already Handled | 請求已被處理 |
| 34003 | Request Not Supported | 平台不支援該類型的請求操作 |
| 34004 | Permission Denied | Bot 無權處理此請求（平台返回） |

> **與框架碼的邊界**：以上 `340xx` 是**平台/適配器**返回的請求處理失敗；  
> ErisPulse 框架在 `scope.actions` 禁用某模組的 request 動作時，**在呼叫適配器之前**  
> 直接返回 `34601`（Action Denied，見 [API 响应标准 §5.3](api-response.md#53-框架擴展返回碼34xxx-平台錯誤段的低三位自定義)），  
> 兩者互不替代：先過 `34601` 框架閘口，再落到平台層 `340xx` 錯誤。

## 8. 相關文件

- [事件轉換標準](event-conversion.md) - 完整的事件轉換規範
- [API 回應標準](api-response.md) - 適配器 API 回應格式標準
- [發送方法規範](send-method-spec.md) - Send 類的方法命名和參數規範
- [會話類型標準](session-types.md) - 會話類型定義和映射關係



### API 动作标准

# ErisPulse API 動作標準

本文檔定義 ErisPulse 適配器中 **OneBot12 標準 API 動作**的統一介面規範，使模組開發者可以面向標準介面編程，由適配器負責映射到平台原生 API。

> **涵蓋範圍**：OneBot12 標準動作中，`ApiDSL` 提供使用者 / 群組 / 頻道（Guild）/
> 消息管理 / 元（Meta）常規介面的強類型方法（`send_message` 由
> `SendDSL.Raw_ob12` 承擔）。檔案資源動作（`upload_file` / `get_file` / 分片）僅作
> 降級透傳保留，見 §3.5 說明。平台擴展動作經 `Api.call("prefix.action", ...)`
> 逃生艙調用。動作參數與回傳結構以 OneBot12 規範（倉庫內 `onebot/specs/interface/`）為準。

## 1. 設計背景

在 ErisPulse 中，訊息段（訊息收發）和事件格式已經完全遵循 OneBot12 標準，但 **API 動作呼叫**（如獲取使用者資訊、獲取群組列表、撤回訊息等）此前未統一——模組開發者必須為每個平台寫不同的 `call_api` 呼叫。

`ApiDSL` 透過提供強類型的標準動作方法，解決這一問題：

```
模組程式碼（跨平台統一）             適配器實作（平台特定）
─────────────────              ──────────────────
adapter.Api.get_user_info("123")  →  適配器 call_api / 覆蓋
adapter.Api.get_group_list()      →  適配器 call_api / 覆蓋
adapter.Api.delete_message("id")  →  適配器 call_api / 覆蓋
```

## 2. 三層 DSL 並行結構

ErisPulse 適配器有三個並行的 DSL 內部類，各司其職：

```
BaseAdapter
├── Send(SendDSL)       ← 訊息發送（Text/Image/Raw_ob12）
├── Request(RequestDSL)  ← 請求操作（accept/reject）
└── Api(ApiDSL)          ← 標準 API 動作（使用者/群組/頻道/訊息管理/檔案/元）★
```

| DSL | 職責 | 方法風格 | 回傳值 |
|-----|------|---------|--------|
| `Send` | 發送訊息 | 串鏈 + `asyncio.Task` | 標準回應 |
| `Request` | 處理請求事件 | `asyncio.Task` | 標準回應 |
| `Api` | 查詢/管理操作 | `async` 方法 | 標準回應 |

## 3. 標準動作列表

### 3.1 使用者相關

| 方法 | OB12 動作 | 參數 | data 回傳 |
|------|----------|------|----------|
| `get_self_info()` | `get_self_info` | 無 | `user_id`, `user_name`, `user_displayname` |
| `get_user_info(user_id)` | `get_user_info` | `user_id: str` | `user_id`, `user_name`, `user_displayname`, `user_remark` |
| `get_friend_list()` | `get_friend_list` | 無 | `list[get_user_info 回應]` |

### 3.2 群組相關

| 方法 | OB12 動作 | 參數 | data 回傳 |
|------|----------|------|----------|
| `get_group_info(group_id)` | `get_group_info` | `group_id: str` | `group_id`, `group_name` |
| `get_group_list()` | `get_group_list` | 無 | `list[get_group_info 回應]` |
| `get_group_member_info(group_id, user_id)` | `get_group_member_info` | `group_id: str`, `user_id: str` | `user_id`, `user_name`, `user_displayname` |
| `get_group_member_list(group_id)` | `get_group_member_list` | `group_id: str` | `list[get_group_member_info 回應]` |
| `set_group_name(group_id, group_name)` | `set_group_name` | `group_id: str`, `group_name: str` | 無 |
| `leave_group(group_id)` | `leave_group` | `group_id: str` | 無 |

### 3.3 訊息管理

| 方法 | OB12 動作 | 參數 | 說明 |
|------|----------|------|------|
| `delete_message(message_id)` | `delete_message` | `message_id: str` | 撤回/刪除訊息 |

> **發送訊息**（`send_message`）由 `SendDSL` 的 `Raw_ob12` 處理，不在 `ApiDSL` 中重複。

### 3.4 頻道（Guild）相關

OneBot12 頻道體系分兩級：**頻道（guild）** 與 **子頻道（channel）**。

| 方法 | OB12 動作 | 參數 | data 回傳 |
|------|----------|------|----------|
| `get_guild_info(guild_id)` | `get_guild_info` | `guild_id: str` | `guild_id`, `guild_name` |
| `get_guild_list()` | `get_guild_list` | 無 | `list[get_guild_info 回應]` |
| `set_guild_name(guild_id, guild_name)` | `set_guild_name` | `guild_id: str`, `guild_name: str` | 無 |
| `get_guild_member_info(guild_id, user_id)` | `get_guild_member_info` | `guild_id: str`, `user_id: str` | `user_id`, `user_name`, `user_displayname` |
| `get_guild_member_list(guild_id)` | `get_guild_member_list` | `guild_id: str` | `list[get_guild_member_info 回應]` |
| `leave_guild(guild_id)` | `leave_guild` | `guild_id: str` | 無 |
| `get_channel_info(guild_id, channel_id)` | `get_channel_info` | `guild_id: str`, `channel_id: str` | `channel_id`, `channel_name` |
| `get_channel_list(guild_id, *, joined_only)` | `get_channel_list` | `guild_id: str`, `joined_only: bool=false` | `list[get_channel_info 回應]` |
| `set_channel_name(guild_id, channel_id, channel_name)` | `set_channel_name` | `guild_id`, `channel_id`, `channel_name` | 無 |
| `get_channel_member_info(guild_id, channel_id, user_id)` | `get_channel_member_info` | `guild_id`, `channel_id`, `user_id` | `user_id`, `user_name`, `user_displayname` |
| `get_channel_member_list(guild_id, channel_id)` | `get_channel_member_list` | `guild_id`, `channel_id` | `list[get_channel_member_info 回應]` |
| `leave_channel(guild_id, channel_id)` | `leave_channel` | `guild_id`, `channel_id` | 無 |

> 頻道體系與群組（group）彼此獨立：Discord / QQ 頻道 / Kook 等平台實作頻道介面，
> 傳統 QQ / 微信實作群組介面，兩者可同時存在或僅其一。

### 3.5 檔案資源操作

> [!WARNING]
> **檔案資源模型（file_id 兩段式）在 ErisPulse 屬"降級可用"**：
> ErisPulse 的檔案收發不走"先上傳拿 file_id 再引用"模型——模組發檔案用
> `SendDSL.File(file, filename)`（URL / 路徑 / 字節**發送時直傳**，見
> [發送方法規範](send-method-spec.md)）。
> 本節 `upload_file` / `get_file` / 分片動作依賴平台特有的 `file_id` 檔案資源
> 能力，**通用性不足**；僅當適配器後端天然具備該能力時才可透傳，框架內建
> 適配器**不實作也不建議實作**，呼叫時通常回傳 `retcode=10002`。
> 模組需要跨平台傳檔案時，請使用 `SendDSL.File`，勿依賴 file_id。
>
> **展望**：`file_id` 資源模型標準化到框架層是未來的方向，當前版本不提供。

整包傳輸（小檔案）：

| 方法 | OB12 動作 | 參數 | data 回傳 |
|------|----------|------|----------|
| `upload_file(*, type, name, ...)` | `upload_file` | `type`, `name`, `url`/`path`/`data`, `headers?`, `sha256?` | `file_id` |
| `get_file(file_id, type)` | `get_file` | `file_id: str`, `type: str` | `name`, `url`/`path`/`data` |

`upload_file` 的 `type` 參數：
- `"url"`：透過 URL 上傳（需提供 `url`）
- `"path"`：透過本地路徑上傳（需提供 `path`）
- `"data"`：透過二進位資料上傳（需提供 `data`）

#### 3.5.1 分片傳輸（大檔案，屬上述降級範圍）

OneBot12 分片動作按 `stage` 區分階段。`ApiDSL` 將同一動作的三/兩階段拆分為獨立方法
（`offset` 為位元組偏移，`data` 在 JSON 中為 Base64）；下表僅為查閱保留，
適配器無需也不應強制實作：

**分片上傳三步**：`prepare` → `transfer`（循環逐片）→ `finish`

| 方法 | 對應 stage | 參數 | data 回傳 |
|------|-----------|------|----------|
| `upload_file_fragmented_prepare(name, total_size)` | `prepare` | `name: str`, `total_size: int` | `file_id`（傳輸期用） |
| `upload_file_fragmented_transfer(file_id, offset, data)` | `transfer` | `file_id`, `offset: int`, `data: bytes` | 無 |
| `upload_file_fragmented_finish(file_id, sha256)` | `finish` | `file_id`, `sha256: str`（整檔案校驗） | `file_id` |

```python
total = os.path.getsize(path)
r = await adapter.Api.upload_file_fragmented_prepare(os.path.basename(path), total)
fid = r["data"]["file_id"]
offset = 0
with open(path, "rb") as f:
    while chunk := f.read(65536):
        await adapter.Api.upload_file_fragmented_transfer(fid, offset, chunk)
        offset += len(chunk)
sha256 = hashlib.sha256(open(path, "rb").read()).hexdigest()
await adapter.Api.upload_file_fragmented_finish(fid, sha256)
```

**分片下載兩步**：`prepare` → `transfer`（循環取片）

| 方法 | 對應 stage | 參數 | data 回傳 |
|------|-----------|------|----------|
| `get_file_fragmented_prepare(file_id)` | `prepare` | `file_id` | `name`, `total_size`, `sha256` |
| `get_file_fragmented_transfer(file_id, offset, size)` | `transfer` | `file_id`, `offset: int`, `size: int` | `data`（本次分片位元組） |

### 3.6 元（Meta）動作

元動作不針對具體帳號，無需 `Using()` 指定 Bot。

| 方法 | OB12 動作 | 參數 | data 回傳 |
|------|----------|------|----------|
| `get_latest_events(limit, timeout)` | `get_latest_events` | `limit: int=0`, `timeout: int=0` | 事件物件陣列（不含元事件） |
| `get_supported_actions()` | `get_supported_actions` | 無 | `list[str]` 支援的動作名 |
| `get_status()` | `get_status` | 無 | `good: bool`, `bots: list[{self, online, ...}]` |
| `get_version()` | `get_version` | 無 | `impl`, `version`, `onebot_version` |

### 3.7 通用擴展動作

| 方法 | 說明 |
|------|------|
| `call(action, **params)` | 平台擴展動作的逃生艙，遵循 OB12 擴展命名規則 `{prefix}.{action}` |

## 4. 使用方式

### 4.1 基本呼叫

```python
from ErisPulse import adapter

# 獲取使用者資訊（跨平台統一）
result = await adapter.myplatform.Api.get_user_info("123456")
if result["status"] == "ok":
    user_name = result["data"]["user_name"]
    print(f"使用者名: {user_name}")

# 獲取群組列表
result = await adapter.myplatform.Api.get_group_list()
groups = result["data"]

# 撤回訊息
await adapter.myplatform.Api.delete_message("msg_123456")
```

### 4.2 指定 Bot 帳號（多帳戶模式）

```python
# 使用指定 Bot 帳號執行操作
info = await adapter.myplatform.Api.Using("bot1").get_self_info()
```

### 4.3 平台擴展動作

```python
# 呼叫平台特有的擴展動作（建議使用 {prefix}.{action} 命名）
result = await adapter.telegram.Api.call(
    "telegram.send_sticker",
    sticker_id="CAACAgIAAxkBAA...",
)
```

### 4.4 在事件處理器中使用

```python
from ErisPulse.Core.Event import message

@message()
async def handle(event):
    # 獲取發送者詳細資訊
    user_id = event.get_user_id()
    platform = event.get_platform()

    result = await getattr(adapter, platform).Api.get_user_info(user_id)
    if result["status"] == "ok":
        user_name = result["data"]["user_name"]
        await event.reply(f"你好，{user_name}！")
```

## 5. 適配器實作

### 5.1 預設行為（零設定）

`ApiDSL` 的預設實作將標準動作名作為 `endpoint` 直接傳遞給 `adapter.call_api()`：

```python
# ApiDSL 預設實作等價於：
async def get_user_info(self, user_id: str) -> dict:
    return await self._adapter.call_api("get_user_info", user_id=user_id, account_id=self._account_id)
```

**適用場景**：當適配器的底層後端自身即遵循 OneBot12 標準動作協議時，
`call_api` 天然支援標準動作名（如直接對接遵循該協議的服務端）。

### 5.2 覆蓋標準方法（映射到平台原生 API）

適配器可覆蓋單個標準方法，將其映射到平台原生 API：

```python
class MyAdapter(BaseAdapter):

    class Api(BaseAdapter.Api):
        """MyPlatform 標準 API 動作實作"""

        async def get_user_info(self, user_id: str) -> dict:
            # 映射到平台原生 API
            raw = await self._adapter._request("GET", f"/users/{user_id}")
            if raw.get("code") != 0:
                return self._adapter.make_error(retcode=34600, message="使用者不存在")

            user = raw["data"]
            return self._adapter.make_response(
                data={
                    "user_id": str(user["id"]),
                    "user_name": user.get("nick", ""),
                    "user_displayname": user.get("display_name", ""),
                    "user_remark": user.get("remark", ""),
                },
                raw=raw,
            )

        async def get_friend_list(self) -> dict:
            raw = await self._adapter._request("GET", "/friends")
            friends = [
                {
                    "user_id": str(u["id"]),
                    "user_name": u.get("nick", ""),
                    "user_displayname": u.get("display_name", ""),
                    "user_remark": u.get("remark", ""),
                }
                for u in raw.get("data", [])
            ]
            return self._adapter.make_response(data=friends, raw=raw)
```

### 5.3 未支援的動作

適配器未覆蓋的標準方法走預設實作（委派給 `call_api`）。如果 `call_api` 也不支援該動作，應回傳標準錯誤回應：

```python
async def call_api(self, endpoint: str, **params):
    if endpoint not in self._supported_endpoints:
        return self.make_error(retcode=10002, message=f"不支援的動作: {endpoint}")
    # ... 平台 API 呼叫
```

模組開發者可透過回傳值的 `retcode` 判斷是否支援：

```python
result = await adapter.myplatform.Api.get_friend_list()
if result["retcode"] == 10002:
    print("該平台不支援獲取好友列表")
```

## 6. 回應格式

所有 `ApiDSL` 方法回傳標準 API 回應格式（詳見 [API 回應標準](api-response.md)）：

```json
{
    "status": "ok",
    "retcode": 0,
    "data": { ... },
    "message_id": "",
    "message": "",
    "myplatform_raw": { ... }
}
```

> **注意**：資訊查詢類動作的 `message_id` 為空字串（僅訊息發送類動作才有 `message_id`）。

## 7. 與 SendDSL / RequestDSL 的關係

| 場景 | 使用 DSL | 示例 |
|------|---------|------|
| 發送訊息 | `Send` | `adapter.Send.To("group", "123").Text("hi")` |
| 同意/拒絕請求 | `Request` | `adapter.Request("req_id").accept()` |
| 獲取使用者/群資訊 | `Api` | `adapter.Api.get_user_info("123")` |
| 撤回訊息 | `Api` | `adapter.Api.delete_message("msg_id")` |
| 退出群 | `Api` | `adapter.Api.leave_group("group_id")` |

## 8. 適配器實作檢查清單

### 標準動作
- [ ] `call_api` 能處理標準動作名（或覆蓋對應 `ApiDSL` 方法）
- [ ] 不支援的動作回傳 `retcode=10002`
- [ ] 回傳值遵循標準 API 回應格式
- [ ] `data` 字段包含 OB12 標準定義的字段
- [ ] 頻道平台需實作 `get_guild_*` / `get_channel_*` / `leave_guild` / `leave_channel`
- [ ] 元動作（`get_status` / `get_version` / `get_supported_actions`）建議實作
- [ ] **檔案收發用 `SendDSL.File`（直傳）**；檔案資源動作（upload_file/get_file/分片）**不強制實作**，僅當後端具備 `file_id` 資源能力時才需透傳

### 擴展動作
- [ ] 平台擴展動作使用 `{prefix}.{action}` 命名
- [ ] 擴展動作的參數和回應仍遵循 OB12 動作請求/回應結構

## 9. 相關文件

- [API 回應標準](api-response.md) - 適配器 API 回應格式標準
- [發送方法規範](send-method-spec.md) - Send 類的方法命名和參數規範
- [請求操作規範](request-action-spec.md) - Request DSL 的使用方式
- [事件轉換標準](event-conversion.md) - 事件格式和訊息段標準



====
高级主题
====


### HTTP 客户端

# 網路用戶端

ErisPulse 提供了統一的網路用戶端，聚合了 HTTP 請求、WebSocket 連接和連接池管理。模組和適配器**必須優先使用**此用戶端，而非自行導入 `aiohttp` / `httpx` / `requests` 等第三方庫。

## 概述

網路客戶端的主要功能：

- **統一介面**：提供 `get` / `post` / `put` / `delete` / `patch` / `request` 方法
- **WebSocket 客戶端**：透過 `ws_connect` 建立客戶端 WebSocket 連接
- **自動日誌**：所有請求自動記錄日誌和統計資訊
- **生命週期整合**：每次請求觸發 `client.request` 生命週期事件，WS 連接觸發 `client.ws.connect` 事件
- **重試支援**：可配置自動重試次數和間隔
- **超時控制**：獨立的連接超時和請求超時
- **連接池複用**：基於 aiohttp.ClientSession 的連接池管理
- **異常體系**：aiohttp 異常自動轉換為 ErisPulse 異常 (ClientError 體系)

## 快速入門

### HTTP 請求

```python
from ErisPulse.Core import client

# GET 請求
resp = await client.get("https://httpbin.org/get")
data = await resp.json()
print(resp.status)  # 200

# POST 請求
resp = await client.post(
    "https://httpbin.org/post",
    json={"key": "value"},
)
data = await resp.json()
```

### WebSocket 連接

```python
from ErisPulse.Core import client

ws = await client.ws_connect("wss://example.com/ws")

async for text in ws.iter_text():
    await ws.send_text(f"Echo: {text}")
```

## HttpResponse

所有請求方法都會返回 `HttpResponse` 物件：

```python
from ErisPulse.Core import client

resp = await client.get("https://httpbin.org/get")

resp.status       # int - HTTP 狀態碼 (例如 200, 404)
resp.reason       # str | None - 狀態描述 (例如 "OK")
resp.headers      # 回應標頭 (大小寫不敏感)
resp.content_type # str | None - Content-Type
resp.url          # 最終 URL (可能因重定向而改變)
resp.raw          # 底層原生回應物件 (目前為 aiohttp.ClientResponse)

# 讀取回應主體
body = await resp.read()       # bytes
text = await resp.text()       # str
data = await resp.json()       # 解析 JSON
text = await resp.text("gbk")  # 指定編碼
```

## 請求方法

### GET

```python
from ErisPulse.Core import client

resp = await client.get(
    "https://api.example.com/users",
    params={"page": "1", "limit": "10"},
    headers={"Authorization": "Bearer token"},
)
```

### POST

```python
from ErisPulse.Core import client

# JSON 請求體
resp = await client.post(
    "https://api.example.com/users",
    json={"name": "Alice", "age": 30},
)

# 表單請求體
resp = await client.post(
    "https://api.example.com/login",
    data={"username": "admin", "password": "123"},
)

# 原始數據
resp = await client.post(
    "https://api.example.com/upload",
    data=b"raw bytes",
    headers={"Content-Type": "application/octet-stream"},
)

# 文件上傳 (使用 files 參數, 無需導入 aiohttp)
# 格式: {字段名: 文件物件/bytes/(檔名, 檔案)/(檔名, 檔案, content_type)}
resp = await client.post(
    "https://api.example.com/upload",
    data={"description": "頭像"},            # 可選: 同時攜帶普通表單欄位
    files={
        "file": ("photo.png", open("photo.png", "rb"), "image/png"),
    },
)

# 簡化寫法: 直接傳文件物件
resp = await client.post(
    "https://api.example.com/upload",
    files={"file": open("photo.png", "rb")},
)

# 內存數據直接上傳 (無需落盤)
import io

resp = await client.post(
    "https://api.example.com/upload",
    files={"file": ("data.txt", io.BytesIO(b"file content"), "text/plain")},
)
```

### PUT / DELETE / PATCH

```python
from ErisPulse.Core import client

resp = await client.put("https://api.example.com/users/1", json={"name": "Bob"})
resp = await client.delete("https://api.example.com/users/1")
resp = await client.patch("https://api.example.com/users/1", json={"age": 31})
```

### 通用 request

```python
from ErisPulse.Core import client

resp = await client.request(
    "OPTIONS",
    "https://api.example.com/resource",
    headers={"Origin": "https://example.com"},
)
```

## 參數說明

### HTTP 請求參數

| 參數 | 類型 | 說明 |
|------|------|------|
| `url` | `str` | 請求 URL |
| `params` | `dict[str, str]` | 查詢參數 (可選) |
| `headers` | `dict[str, str]` | 額外請求頭 (可選) |
| `data` | `Any` | 請求體 (表單或原始資料) (可選) |
| `json` | `Any` | JSON 請求體 (可選) |
| `files` | `dict[str, Any]` | 檔案上傳欄位 (可選, 自動建構 multipart/form-data) |
| `timeout` | `float` | 本次請求超時 (秒) (可選, 覆蓋預設值) |
| `max_retries` | `int` | 本次最大重試次數 (可選, 覆蓋預設值) |

### ws_connect 參數

| 參數 | 類型 | 說明 |
|------|------|------|
| `url` | `str` | WebSocket 伺服器 URL |
| `headers` | `dict[str, str]` | 額外請求頭 (可選) |
| `heartbeat` | `float` | 心跳間隔秒數 (可選) |

## 超時與重試

```python
from ErisPulse.Core import Client

# 創建帶自定義超時的客戶端
client = Client(
    timeout=60,           # 請求總超時 60 秒
    connect_timeout=5,    # 連接超時 5 秒
    max_retries=3,        # 失敗自動重試 3 次
    retry_delay=2,        # 重試間隔 2 秒
)

# 單次請求覆蓋超時
resp = await client.get("https://slow-api.example.com/data", timeout=120)
```

> [!NOTE]
> 客戶端類從 2.8.0 起更名為 `Client`（`sdk.client` 屬性名不變）；舊名 `HttpClient` 保留為相容別名，舊代碼無需修改。

## 自訂預設標頭

```python
client = Client(
    headers={
        "Authorization": "Bearer token",
        "X-App-Id": "my-app",
    },
    user_agent="MyBot/1.0",
)
```

## 請求統計

```python
from ErisPulse.Core import client

# 查看統計
stats = client.stats
# {"total_requests": 42, "total_errors": 1, "total_bytes_sent": 0, "total_bytes_received": 0}

# 重置統計
client.reset_stats()
```

## 生命周期事件

### HTTP 請求事件

每次請求完成後觸發 `client.request` 事件，可用於監控：

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("client.request")
async def on_request(event_data):
    print(f"{event_data['method']} {event_data['url']} -> {event_data['status']} ({event_data['elapsed']}s)")
```

### WebSocket 連接事件

每次 WebSocket 連接建立後觸發 `client.ws.connect` 事件：

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("client.ws.connect")
async def on_ws_connect(event_data):
    print(f"WS 連接: {event_data['url']}")
```

## 上下文管理

```python
# 作為上下文管理器，自動關閉會話
async with Client(timeout=30) as client:
    resp = await client.get("https://httpbin.org/get")
    data = await resp.json()
```

## WebSocket 客戶端

使用 `client.ws_connect()` 建立 WebSocket 客戶端連接，返回 `ClientWebSocket` 物件。客戶端與服務端 WebSocket 共享相同的 `WebSocketConnectionBase` 基類，send/receive/iter 接口完全一致。

### 基本用法

```python
from ErisPulse.Core import client

ws = await client.ws_connect("wss://example.com/ws", heartbeat=30)

await ws.send_text("Hello")
await ws.send_bytes(b"\x00\x01\x02")
await ws.send_json({"type": "ping"})
```

### 接收訊息

#### 高階方法（推薦）

自動過濾訊息類型，斷開時拋出 `WebSocketDisconnect`：

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases.errors import WebSocketDisconnect

ws = await client.ws_connect("wss://example.com/ws")

# 單筆接收
text = await ws.receive_text()    # str
data = await ws.receive_bytes()   # bytes
obj = await ws.receive_json()     # dict / list

# 迭代接收（自動在斷開時停止）
async for text in ws.iter_text():
    print(text)

async for data in ws.iter_bytes():
    print(data)

async for obj in ws.iter_json():
    print(obj)
```

#### 低階方法

使用 `receive()` 和 `iter_messages()` 處理原始訊息類型，可區分 TEXT / BINARY / CLOSE / ERROR：

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases.websocket import WSMessage

ws = await client.ws_connect("wss://example.com/ws")

# 單筆接收原始訊息
msg = await ws.receive()
# msg.type  -> WSMessage.TEXT / WSMessage.BINARY / WSMessage.CLOSE / WSMessage.ERROR
# msg.data  -> str | bytes | None

# 迭代原始訊息（CLOSE/ERROR 時自動停止）
async for msg in ws.iter_messages():
    if msg.type == WSMessage.TEXT:
        print(f"文本: {msg.data}")
    elif msg.type == WSMessage.BINARY:
        print(f"二進制: {len(msg.data)} bytes")
```

### WSMessage

`WSMessage` 是統一的 WebSocket 訊息類型，不依賴底層庫：

| 屬性 | 類型 | 說明 |
|------|------|------|
| `type` | `str` | 訊息類型: `WSMessage.TEXT` / `WSMessage.BINARY` / `WSMessage.CLOSE` / `WSMessage.ERROR` |
| `data` | `Any` | 訊息資料 |

### ClientWebSocket 屬性

| 屬性 | 類型 | 說明 |
|------|------|------|
| `url` | `URL` | 連接 URL |
| `headers` | `Headers` | 回應標頭 |
| `closed` | `bool` | 連接是否已關閉 |
| `raw` | `object` | 底層原生物件 (aiohttp.ClientWebSocketResponse) |

### 生命週期鉤子

與 `服務端 WebSocketConnection` 一致，支援 `on_disconnect` 和 `on_error` 回調：

```python
from ErisPulse.Core import client

ws = await client.ws_connect("wss://example.com/ws")

@ws.on_disconnect
async def handle_disconnect(ws, reason="unknown"):
    print(f"連接斷開: {reason}")

@ws.on_error
async def handle_error(ws, error=""):
    print(f"連接錯誤: {error}")
```

### 關閉連接

```python
await ws.close(code=1000, reason="Normal closure")
```

## 異常體系

ErisPulse 定義了統一的異常層級，透過 `sdk.client` 發起的請求會自動將底層 aiohttp 異常轉換為 ErisPulse 異常。

> **向後兼容**：直接使用 `aiohttp.ClientSession` 的舊模組/適配器完全不受影響。異常轉換僅在透過 `sdk.client` 發起請求時生效，直接使用 aiohttp 的代碼仍然捕獲 `aiohttp.ClientError` 等原生異常。兩種方式可以共存。

### 異常層級

```
ErisPulseError
├── ClientError                  # 所有 HTTP/WS 客戶端請求異常的基類
│   ├── ClientConnectionError    # 連接失敗 (DNS 解析失敗、連接被拒絕、網路不可達)
│   ├── ClientTimeoutError       # 連接超時或請求超時
│   └── HTTPStatusError          # HTTP 4xx/5xx 狀態碼錯誤
└── WebSocketError               # WebSocket 異常基類
    └── WebSocketDisconnect      # WebSocket 連接斷開 (客戶端和服務端通用)
```

### 異常捕獲

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases.errors import (
    ClientError,
    ClientConnectionError,
    ClientTimeoutError,
    HTTPStatusError,
    WebSocketDisconnect,
    WebSocketError,
)

# HTTP 請求異常處理
try:
    resp = await client.get("https://api.example.com/data")
    data = await resp.json()
except ClientConnectionError:
    print("無法連接到伺服器")
except ClientTimeoutError:
    print("請求超時")
except ClientError as e:
    print(f"請求失敗: {e}")

# WebSocket 異常處理
try:
    ws = await client.ws_connect("wss://example.com/ws")
    async for text in ws.iter_text():
        await ws.send_text(f"Echo: {text}")
except WebSocketDisconnect as e:
    print(f"連接斷開: code={e.code}, reason={e.reason}")
except WebSocketError as e:
    print(f"WebSocket 錯誤: {e}")
```

### 統一捕獲

使用 `ClientError` 統一捕獲所有 HTTP/WS 客戶端請求異常：

```python
from ErisPulse.Core.Bases.errors import ClientError

try:
    resp = await client.get("https://api.example.com/data")
except ClientError as e:
    print(f"客戶端錯誤: {e}")
```

### HTTPStatusError

當需要在請求後檢查狀態碼並拋出異常時，可手動使用：

```python
from ErisPulse.Core.Bases.errors import HTTPStatusError

resp = await client.get("https://api.example.com/data")
if resp.status >= 400:
    raise HTTPStatusError(resp.status, await resp.text())
```

## 適配器中使用

適配器可使用全域用戶端或自行建立用戶端實例來發送平台 API 請求：

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases import BaseAdapter
from ErisPulse.Core.Bases.errors import ClientError

class MyAdapter(BaseAdapter):
    async def call_api(self, endpoint, **params):
        try:
            resp = await client.post(
                f"https://api.platform.com/{endpoint}",
                json=params,
                headers={"Authorization": f"Bearer {self.token}"},
            )
            return await resp.json()
        except ClientError as e:
            self.logger.error(f"API 調用失敗: {e}")
            raise
```

> 亦可透過 `from ErisPulse import sdk` 使用 `sdk.client`，效果相同。

## 最佳實踐

1. **優先使用全域客戶端**：使用 `from ErisPulse.Core import client` 獲取全域單例，便於框架統一管理和監控
2. **避免直接導入 aiohttp**：使用 `client` 替代 `aiohttp.ClientSession`，未來更換底層實現無需修改程式碼。舊程式碼直接使用 aiohttp 仍可正常運作，兩種方式可以共存
3. **使用 ErisPulse 異常體系**：透過 `sdk.client` 請求時捕獲 `ClientError` 而非 `aiohttp.ClientError`，確保程式碼不依賴特定 HTTP 庫。直接使用 aiohttp 的舊程式碼不受影響
4. **合理設定超時**：根據 API 回應速度設定合理的超時時間，避免長時間阻塞
5. **使用重試機制**：對不穩定的 API 啟用重試，提高可靠性
6. **監控請求統計**：透過 `sdk.client.stats` 或 `client.request` 生命週期事件監控請求情況
7. **WebSocket 使用高階方法**：優先使用 `iter_text` / `iter_json` 等高階方法，僅在需要區分訊息類型時使用 `iter_messages`

## 相關文件

- [路由管理器](router.md) - HTTP/WebSocket 服務端路由（服務端 WebSocketConnection 與客戶端共享同一基類）
- [適配器開發指南](../developer-guide/adapters/getting-started.md) - 適配器中使用 HTTP 客戶端
- [生命週期管理](lifecycle.md) - 監聽請求事件



### SQL 查询构建器

# SQL 查詢建構器

ErisPulse 的 Storage 模組提供鏈式呼叫風格的通用 SQL 查詢建構器，支援自訂表的建立、查詢、更新和刪除操作。

## 架構設計

```
Bases/storage.py                    Core/storage.py
┌─────────────────────┐             ┌──────────────────────────┐
│  BaseStorage (ABC)  │◄────────────│  StorageManager          │
│  BaseQueryBuilder   │             │  (SQLite concrete impl)  │
│    (ABC)            │             │                          │
└─────────────────────┘             │  SQLiteQueryBuilder      │
                                    │  AlterTableBuilder       │
                                    └──────────────────────────┘
```

- `BaseStorage` / `BaseQueryBuilder` 是抽象基類，定義統一介面，支援未來拓展其他儲存介質（Redis、MySQL 等）
- `StorageManager` 是目前 SQLite 的具體實作，完全向後相容

## 導入

```python
from ErisPulse import sdk
# 或
from ErisPulse.Core import storage

# ABC 基類（用於類型註解或自定義實現）
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder
```

## 表管理

### 建立表格

```python
sdk.storage.CreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
    "age": "INTEGER DEFAULT 0",
    "email": "TEXT"
})
```

### 檢查表格是否存在

```python
if sdk.storage.HasTable("users"):
    print("users 表已存在")
```

### 刪除表格

```python
sdk.storage.DropTable("users")
```

### 修改表格結構

```python
# 新增欄位
sdk.storage.AlterTable("users").AddColumn("email", "TEXT").Execute()

# 重新命名表格
sdk.storage.AlterTable("users").RenameTo("members").Execute()

# 串接多個操作
sdk.storage.AlterTable("users") \
    .AddColumn("phone", "TEXT") \
    .AddColumn("address", "TEXT") \
    .Execute()
```

## 鏈式查詢

### 插入數據

```python
# 單行插入（傳入字典）
sdk.storage.Table("users").Insert({"name": "Alice", "age": 30}).Execute()

# 批量插入（傳入字典列表）
sdk.storage.Table("users").InsertMulti([
    {"name": "Bob", "age": 25},
    {"name": "Charlie", "age": 35},
    {"name": "Dave", "age": 40}
]).Execute()
```

### 查詢數據

> **重要**：`Select()` 返回的是 `list[tuple]`（元組列表），不是字典。你需要按列順序用索引訪問。

```python
# 查詢所有列
rows = sdk.storage.Table("users").Select().Execute()
# rows: [(1, "Alice", 30), (2, "Bob", 25), ...]

# 查詢指定列
rows = sdk.storage.Table("users").Select("name", "age").Execute()
# rows: [("Alice", 30), ("Bob", 25), ...]

# 按索引取值
for row in rows:
    name = row[0]   # "Alice"
    age = row[1]    # 30
```

#### 將元組轉為字典

```python
columns = ["id", "name", "age"]
rows = sdk.storage.Table("users").Select(*columns).Execute()

# 方式一：循環中 zip
for row in rows:
    record = dict(zip(columns, row))
    print(record["name"], record["age"])

# 方式二：一次性轉為字典列表
records = [dict(zip(columns, row)) for row in rows]
```

#### 獲取單條記錄

```python
row = sdk.storage.Table("users").Select("name", "age") \
    .Where("id = ?", 1) \
    .ExecuteOne()

# row 是 tuple 或 None
if row is not None:
    name = row[0]  # "Alice"
    age = row[1]   # 30
```

### 條件過濾

> `Where(condition, *params)` 支持傳入多個參數，對應多個 `?` 佔位符。

```python
# 單條件（一個佔位符，一個參數）
rows = sdk.storage.Table("users").Select("name") \
    .Where("age > ?", 18) \
    .Execute()

# 一個 Where 中使用多個佔位符
rows = sdk.storage.Table("users").Select("name") \
    .Where("age > ? AND age < ?", 20, 40) \
    .Execute()

# 多次調用 Where（AND 連接）
rows = sdk.storage.Table("users").Select("name") \
    .Where("age > ?", 20) \
    .Where("age < ?", 40) \
    .Execute()
```

### 排序、分頁

```python
# 升序
rows = sdk.storage.Table("users").Select("name", "age") \
    .OrderBy("name") \
    .Execute()

# 降序
rows = sdk.storage.Table("users").Select("name") \
    .OrderBy("age", desc=True) \
    .Execute()

# 分頁
rows = sdk.storage.Table("users").Select("name") \
    .OrderBy("id") \
    .Limit(10) \
    .Offset(20) \
    .Execute()
```

### 更新數據

```python
# 條件更新
sdk.storage.Table("users") \
    .Update({"age": 31}) \
    .Where("name = ?", "Alice") \
    .Execute()

# 全量更新
sdk.storage.Table("users") \
    .Update({"status": "active"}) \
    .Execute()
```

### 刪除數據

```python
# 條件刪除
sdk.storage.Table("users") \
    .Delete() \
    .Where("name = ?", "Bob") \
    .Execute()

# 全量刪除
sdk.storage.Table("users").Delete().Execute()
```

### 計數與存在性檢查

```python
# 計數
count = sdk.storage.Table("users").Count()
count = sdk.storage.Table("users").Where("age > ?", 18).Count()

# 存在性檢查
exists = sdk.storage.Table("users").Where("name = ?", "Alice").Exists()
```

## 重複使用查詢條件

使用 `copy()` 深拷貝建構器，重複使用基礎條件：

```python
base = sdk.storage.Table("users").Where("age > ?", 20)

# 使用相同的條件查詢
rows = base.copy().Select("name").OrderBy("name").Limit(5).Execute()

# 使用相同的條件計數
count = base.copy().Count()

# 使用相同的條件檢查是否存在
exists = base.copy().Where("name = ?", "Alice").Exists()
```

## 重設建構器

```python
builder = sdk.storage.Table("users").Select("name").Where("age > ?", 18)
builder.clear()

# 重新建構查詢
builder.Select("name", "age").Where("name = ?", "Alice")
rows = builder.Execute()
```

## 事務中使用

鏈式操作完全支援事務：

```python
# 提交事務
with sdk.storage.transaction():
    sdk.storage.Table("users").Insert({"name": "Eve", "age": 22}).Execute()
    sdk.storage.Table("users").Update({"age": 23}).Where("name = ?", "Eve").Execute()

# 回滾示例
try:
    with sdk.storage.transaction():
        sdk.storage.Table("users").Delete().Where("name = ?", "Alice").Execute()
        raise Exception("force rollback")
except Exception:
    pass
# Alice 的記錄仍然存在
```

## 返回值說明

| 操作 | 返回類型 | 說明 |
|------|---------|------|
| `Select().Execute()` | `list[tuple]` | 元組列表，按欄位順序排列 |
| `Select().ExecuteOne()` | `tuple \| None` | 單條元組或 None |
| `Insert().Execute()` | `int` | 受影響行數 |
| `InsertMulti().Execute()` | `int` | 新增行數 |
| `Update().Execute()` | `int` | 受影響行數 |
| `Delete().Execute()` | `int` | 受影響行數 |
| `Count()` | `int` | 符合條件的行數 |
| `Exists()` | `bool` | 是否存在 |

### 返回值處理範例

```python
# Select 返回元組，按索引取值
rows = sdk.storage.Table("users").Select("name", "age").Execute()
first_name = rows[0][0]  # 第一行第一欄 name
first_age = rows[0][1]   # 第一行第二欄 age

# 推薦：使用欄位名稱列表 + zip 轉為字典，程式碼更易讀
cols = ["name", "age"]
rows = sdk.storage.Table("users").Select(*cols).Execute()
for row in rows:
    d = dict(zip(cols, row))
    print(d["name"], d["age"])

# ExecuteOne 返回單條元組或 None
row = sdk.storage.Table("users").Select("name").Where("id = ?", 1).ExecuteOne()
name = row[0] if row else None

# Insert/Update/Delete 返回受影響行數
affected = sdk.storage.Table("users").Delete().Where("age < ?", 18).Execute()
print(f"刪除 {affected} 條記錄")
```

## 參數化查詢

所有 WHERE 參數使用 `?` 佔位符，參數作為 `Where()` 的後續參數傳入（**不是**元組或列表）：

```python
# 正確 ✓ — 多個參數逐一傳入
sdk.storage.Table("users").Where("age > ? AND name = ?", 18, "Alice").Execute()

# 正確 ✓ — 多次 Where 調用
sdk.storage.Table("users").Where("age > ?", 18).Where("name = ?", "Alice").Execute()

# 錯誤 ✗ — 不要傳入元組
sdk.storage.Table("users").Where("age > ? AND name = ?", (18, "Alice")).Execute()
# 這會把整個元組當成第一個佔位符的值

# 錯誤 ✗ — 存在 SQL 注入風險
sdk.storage.Table("users").Where(f"name = '{user_input}'").Execute()
```

### Where 參數傳遞規則

```python
# Where(condition: str, *params: Any)
# params 是可變參數，逐個傳入即可

# 單個參數
.Where("name = ?", "Alice")

# 多個參數
.Where("age > ? AND age < ?", 18, 60)

# LIKE 查詢
.Where("name LIKE ?", "A%")

# IN 查詢（需要手動構造佔位符）
.Where("name IN (?, ?, ?)", "Alice", "Bob", "Charlie")
```

## 自訂儲存後端

繼承 `BaseStorage` 和 `BaseQueryBuilder` 以實現自訂儲存後端：

```python
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder

class MyQueryBuilder(BaseQueryBuilder):
    def Execute(self):
        # 實現具體執行邏輯
        ...

    def ExecuteOne(self):
        ...

    def Count(self):
        ...

    def Exists(self):
        ...


class MyStorage(BaseStorage):
    def get(self, key, default=None):
        ...

    def set(self, key, value):
        ...

    # 實現其他抽象方法...
    def Table(self, table_name):
        return MyQueryBuilder(self, table_name)
```

## 相關文件

- [核心模組 API](../api-reference/core-modules.md) - Storage 模組完整 API
- [儲存基類 API](../api-reference/auto_api/ErisPulse/Core/Bases/storage.md) - BaseStorage/BaseQueryBuilder 抽象介面
- [訊息建構器](message-builder.md) - MessageBuilder 鏈式呼叫風格參考



### 懶加载系统

# 慢載模組系統

ErisPulse SDK 提供了強大的慢載模組系統，允許模組在實際需要時才進行初始化，從而顯著提升應用啟動速度和記憶體效率。

## 概述

懶加載模組系統是 ErisPulse 的核心特性之一，它透過以下方式運作：

- **延遲初始化**：模組僅在第一次被存取時才會實際載入和初始化
- **透明使用**：對於開發者而言，懶加載模組與一般模組的使用幾乎沒有差異
- **自動依賴管理**：模組依賴會在被使用時自動初始化
- **生命週期支援**：對於繼承自 `BaseModule` 的模組，會自動呼叫生命週期方法

## 工作原理

### LazyModule 類

懶加載系統的核心是 `LazyModule` 類，它是一個包裝器，在第一次存取時才實際初始化模組。

### 初始化過程

當模組首次被存取時，`LazyModule` 會執行以下操作：

1. 獲取模組類的 `__init__` 參數資訊
2. 根據參數決定是否傳入 `sdk` 引用
3. 設定模組的 `moduleInfo` 屬性
4. 對於繼承自 `BaseModule` 的模組，呼叫 `on_load` 方法
5. 觸發 `module.init` 生命週期事件

## 事件驅動懶激活（activate_on）

> [!NOTE]  
> 此特性需要 ErisPulse **2.8.0+**。

`lazy_load=True` 的模組預設只在**首次屬性存取**時載入。若模組註冊了命令/事件處理器，  
傳統做法只能 `lazy_load=False` 立即載入。`activate_on` 提供了第三種選擇：**宣告觸發器，  
首個匹配事件/命令到達時自動激活模組**——既不常駐記憶體，又不遺失觸發入口。

```python
from ErisPulse.loaders import ModuleLoadStrategy

class MyModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(
            lazy_load=True,
            activate_on=[
                # ---- 事件觸發（被動到達，無需使用者感知）----
                "message",                                    # 類型級：任何訊息事件
                {"notice": "group_member_increase"},          # 類型 + 單個 detail_type
                {"message": ["private", "group"]},            # 類型 + 多個 detail_type

                # ---- 命令觸發（主動輸入，佔位命令對 Help 可見）----
                {"command": "roll"},                          # 簡寫：命令名
                {"command": ["roll", "dice"]},                # 命令名列表
                {"command": {                                 # dict 聲明（name 必填）
                    "name": "dice",
                    "help": "擲一個骰子",
                    "usage": "/dice",
                    "group": "娛樂",
                    "aliases": ["d"],
                    "hidden": False,
                }},
            ],
        )
```

### 命令 dict 聲明參數

dict 形式鏡像 `@command()` 裝飾器的使用者級參數，用於在模組載入前就註冊佔位命令：

| 參數 | 類型 | 預設 | 說明 |
|------|------|------|------|
| `name` | `str` | **必填** | 命令名；須與 `on_load` 中 `@command(name)` 一致，否則激活後佔位註銷、命令不存在 |
| `help` | `str` | 回退鏈 | Help 中顯示的介紹；未聲明時按回退鏈取值（見下） |
| `usage` | `str` | 自动生成 | 用法行，預設 `{prefix}{name}` |
| `group` | `str` | `None` | 命令分組 |
| `aliases` | `list[str]` | `[]` | 別名同時註冊，**輸入別名同樣觸發激活** |
| `hidden` | `bool` | `False` | `True` 時佔位命令同樣隱藏（與激活後真實命令的隱藏語義對齊）；知道命令名的使用者輸入仍可觸發 |

**不支援** `priority` / `permission` / `master`：佔位命令的使命只是觸發激活，  
權限檢查由激活後的真實命令執行（佔位階段攔截權限反而會讓「輸入命令激活」失效）。

### 佔位命令 help 回退鏈

模組未載入時 Help 顯示的命令介紹，按以下順序取值（取到即止）：

1. dict 聲明的命令級 `help`（最精確）  
2. 模組 `get_meta()` 的 `description`  
3. 模組 `__description__` 屬性  
4. 包元數據的 `Summary`（PyPI 包簡介）  
5. 通用提示：「此命令來自懶載入模組 X，首次使用將自動載入該模組」

### 觸發語義

- **事件 stub**：以極低優先級（`ACTIVATION_STUB_PRIORITY`）註冊到對應事件管理器，  
  在所有普通處理器之後兜底觸發；激活後將當前事件轉發給模組的真實處理器  
- **命令 stub**：註冊佔位命令；激活後佔位註銷、真實命令接管當次觸發  
- **防重入**：`asyncio.Lock` 保證併發觸發下只激活一次  
- **作用域過濾**：stub 帶模組 owner 身份，模組未對該 Bot / 會話 / 平台啟用時不觸發  
- **失敗語義**：激活失敗不重試，stub 一併註銷  
- **去重**：同名命令以簡寫 + dict 混合聲明時去重（dict 优先）；dict 缺 `name`  
  或事件 `detail_type` 误写 dict 时告警并忽略

> 架構圖與完整語義詳見 [架構概覽](../architecture.md#事件驅動懶激活activate_on觸發架構)。

## 配置懶加載

### 全局配置

在配置文件中啟用/禁用全局懶加載：

```toml
[ErisPulse.framework]
enable_lazy_loading = true  # true=啟用懶加載(預設)，false=禁用懶加載
```

### 模組層級控制

模組可以透過實作 `get_load_strategy()` 靜態方法來控制加載策略：

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.loaders import ModuleLoadStrategy

class MyModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        """返回模組加載策略"""
        return ModuleLoadStrategy(
            lazy_load=False,  # 返回 False 表示立即加載
            priority=100      # 加載優先級，數值越大優先級越高
        )
```

## 使用懶加載模組

### 基本使用

對於開發者來說，懶加載模組與普通模組在使用上幾乎沒有區別：

```python
# 通過 SDK 訪問懶加載模組
from ErisPulse import sdk

# 以下訪問會觸發模組懶加載
result = await sdk.my_module.my_method()
```

### 統一的模組獲取入口

無論是通過 SDK 屬性、模組管理器屬性訪問，還是通過 `module.get()` 查詢，
對於「已註冊但尚未加載」的懶加載模組，都會返回同一個懶加載代理，訪問其屬性才會真正觸發初始化：

```python
# 三種方式拿到的都是懶加載代理（在模組未加載時），行為一致、對使用者透明
sdk.my_module          # 觸發加載的入口
sdk.module.my_module   # 同樣返回懶加載代理
sdk.module.get("my_module")  # 也返回懶加載代理，本身不會觸發加載

# 訪問代理的任意屬性才會真正初始化模組
result = await sdk.my_module.my_method()
```

`module.get()` 是**查詢**介面，本身不觸發加載：
- 模組已加載 → 返回真實實例
- 模組已註冊但未加載 → 返回懶加載代理（訪問屬性才初始化）
- 模組未註冊 → 返回 `None`

如需顯式觸發加載，請使用 `await sdk.load_module("my_module")`。

### 異步初始化

對於需要異步初始化的模組，建議先顯式加載：

```python
# 先顯式加載模組
await sdk.load_module("my_module")

# 然後使用模組
result = await sdk.my_module.my_method()
```

### 同步初始化

對於不需要異步初始化的模組，可以直接訪問：

```python
# 直接訪問會自動同步初始化
result = sdk.my_module.some_sync_method()
```

## 最佳實踐

選擇加載策略時，可參考以下決策流程：

```mermaid
flowchart TD
    A["模組宣告<br/>get_load_strategy()"] --> B{"需要啟動即就緒<br/>或頻繁觸發？"}
    B -->|"是"| C["lazy_load=False<br/>立即加載"]
    B -->|"否"| D{"註冊了命令 / 事件處理器？"}
    D -->|"是"| E["lazy_load=True + activate_on<br/>事件/命令到達時激活"]
    D -->|"否"| F["lazy_load=True<br/>首次屬性存取時加載"]
    C --> G["啟動時呼叫 on_load()"]
    E --> H["註冊 stub → 觸發時實例化"]
    F --> I["LazyModule 代理"]
```

### 推薦使用懶加載的場景（lazy_load=True）

- 被動調用的工具類（如資料查詢模組、格式轉換器等，僅當其他模組調用時才需要）
- 註冊命令/事件處理器但非頻繁使用的模組——配合 `activate_on` 聲明觸發器，首個匹配事件/命令到達時自動激活，無需放棄懶加載

### 推薦禁用懶加載的場景（lazy_load=False）

- 需要在啟動時立即就緒的模組（如為其它模組提供基礎服務的核心模組）
- 頻繁觸發的監聽器（每條訊息都要處理）——`activate_on` 轉發有一次激活開銷，頻繁場景立即加載更直接
- 定時任務模組
- 需要在應用啟動時就初始化的模組

> `priority` 參數控制立即加載模組間的初始化順序，數值越大越先初始化。同優先級的模組按註冊順序加載。

## 注意事項

1. 如果您的模組使用了懶加載，如果其他模組從未在 ErisPulse 內被呼叫過，則您的模組永遠不會被初始化。
2. 如果您的模組中包含了例如監聽 Event 的模組，或其它主動監聽類似模組，有兩種選擇：宣告 `activate_on` 觸發器（保持懶加載，事件到達時自動激活），或宣告需要立即被加載（`lazy_load=False`），否則會影響您模組的正常業務。
3. 我們不建議您禁用懶加載，除非有特殊需求，否則它可能會為您帶來例如依賴管理和生命週期事件等的問題。
4. `activate_on` 的命令 dict 聲明中，`name` 必須與模組 `on_load` 中 `@command()` 註冊的真實命令名一致——否則模組激活後占位命令註銷，宣告與實現不一致的命令將不存在。

## 相關文件

- [模組開發指南](../developer-guide/modules/getting-started.md) - 學習開發模組
- [最佳實踐](../developer-guide/modules/best-practices.md) - 了解更多最佳實踐



### 生命周期管理

# 生命周期管理

ErisPulse 提供統一的鈎子/生命週期系統，用於監控系統各組件的運行狀態，以及實現審計、統計、自定義邏輯等擴展功能。

系統支援三種觸發方式：
- `await lifecycle.emit("event", data)` — 精簡版，傳遞任意數據
- `lifecycle.emit_sync("event", data)` — 同步版（用於非異步上下文）
- `await lifecycle.submit_event("event", ...)` — 兼容舊版，自動建構標準事件格式

## 事件處理機制

### 註冊處理器

```python
from ErisPulse import sdk

# 裝飾器模式
@sdk.lifecycle.on("module.load")
async def on_module_load(data):
    print(f"模組加載: {data}")

# 編程式註冊
sdk.lifecycle.register("module.load", on_module_load, priority=10)

# 取消註冊
sdk.lifecycle.unregister("module.load", on_module_load)

# 按所有者批量取消註冊（模組/適配器卸載時框架自動調用）
removed = sdk.lifecycle.unregister_by_owner("MyModule")
print(f"清理了 {removed} 個生命週期鈎子")
```

### 優先級

處理器支援 `priority` 參數，數值越大越先執行（與模組加載器一致）：

```python
@sdk.lifecycle.on("adapter.event.receive", priority=10)  # 最先執行
async def first_handler(data):
    pass

@sdk.lifecycle.on("adapter.event.receive", priority=0)  # 後執行
async def second_handler(data):
    pass
```

### 點式結構事件

觸發具體事件時，也會觸發其父級事件：
- 觸發 `module.load` 時，也會觸發 `module`
- 觸發 `adapter.event.receive` 時，也會觸發 `adapter.event` 和 `adapter`

### 通配符

註冊 `*` 捕獲所有事件：

```python
@sdk.lifecycle.on("*")
async def on_anything(data):
    print(f"收到事件: {data}")
```

### 一次性註冊（once）

從 2.7.0 起，`lifecycle.once()` 註冊的處理器在**觸發一次後自動註銷**，適合「首次就緒」這類一次性鈎子：

```python
@sdk.lifecycle.once("core.init.complete")
async def on_first_ready(data):
    print("首次就緒，後續不再觸發")
```

- 與 `on()` 同優先級參數語義（`priority` 數值越大越先執行）
- 自動註銷，無需手動 `unregister`
- 同步/異步處理器均支援

### 監聽者查詢（has_handlers）

熱路徑短路場景可先用 `has_handlers()` 判斷是否有監聽者，避免無謂的事件遍歷與任務調度：

```python
if sdk.lifecycle.has_handlers("message.sending"):
    await sdk.lifecycle.emit("message.sending", send_ctx)
```

- 覆蓋**精確事件名、通配符 `*`、父級事件**三種匹配
- 無任何監聽者時返回 `False`，可安全跳過 `emit`

## 鈎子斷點一覽

一條消息從平台進入框架到處理完成的典型生命週期事件時序：

```mermaid
sequenceDiagram
    participant P as 平台
    participant A as 適配器
    participant F as 框架核心
    participant M as 模組處理器

    P->>A: 原生事件到達
    A->>F: adapter.event.receive（最早期）
    F->>F: event.pre_process（處理器執行前）
    F->>M: 分發到處理器（命令/消息/通知等）
    M->>M: command.matched / command.executed
    M->>F: event.reply()
    F->>F: message.sending（發送前）
    F->>A: SendDSL 發送
    A->>P: 發送到平台
    A->>F: message.sent（發送完成）
    F->>F: adapter.event.dispatched（分發完成）
```

框架內建了以下鈎子斷點，使用者可以透過 `@sdk.lifecycle.on()` 監聽任意斷點實現自定義邏輯。

### 核心初始化

| 鈎子名稱 | 觸發時機 | 數據 |
|---------|---------|------|
| `core.init.start` | SDK 初始化開始 | `{}` |
| `core.init.complete` | SDK 初始化完成 | `{"duration": float, "success": bool, "adapters": {"enabled": [str], "disabled": [str]}, "modules": {"enabled": [str], "disabled": [str]}, "error": str(僅失敗時)}` |
| `core.uninit.complete` | SDK 反初始化完成 | `{"duration": float, "success": bool, "adapters_closed": int, "modules_unloaded": int, "module_properties_cleared": int, "module_properties_to_clear": [str], "error": str(僅失敗時)}` |

### 配置變更

| 鈎子名稱 | 觸發時機 | 數據 |
|---------|---------|------|
| `config.set` | 配置項被修改 | `{"key": str, "old_value": Any, "new_value": Any}` |
| `config.updated` | 外部編輯 config.toml 後檢測到整樹變更 | `{"old_config": dict, "new_config": dict, "config_file": str}` |

**範例：配置審計**

```python
@sdk.lifecycle.on("config.set")
def audit_config(data):
    print(f"[審計] {data['key']}: {data['old_value']} -> {data['new_value']}")
```

### 模組生命週期

| 鈎子名稱 | 觸發時機 | 數據 |
|---------|---------|------|
| `module.register` | 模組類註冊到管理器 | `{"module_name": str, "success": bool}` |
| `module.load` | 模組加載完成（實例化成功） | `{"module_name": str, "success": bool}` |
| `module.init` | 模組初始化完畢（含懶加載） | `{"module_name": str, "success": bool}` |
| `module.unload` | 模組卸載 | `{"module_name": str, "success": bool}` |

### 適配器生命週期

| 鈎子名稱 | 觸發時機 | 數據 |
|---------|---------|------|
| `adapter.load` | 適配器註冊完成 | `{"platform": str, "success": bool}` |
| `adapter.start` | 適配器啟動 | `{"platforms": [str]}` |
| `adapter.status.change` | 適配器狀態變化 | `{"platform": str, "status": str, "retry_count": int, "error": str(僅失敗時)}` |
| `adapter.stop` | 適配器關閉 | `{"platforms": [str]}` |
| `adapter.stopped` | 適配器關閉完成 | `{"platforms": [str]}` |
| `adapter.bot.online` | Bot 上線 | `{"platform": str, "bot_id": str, "info": dict, "status": str}` |
| `adapter.bot.offline` | Bot 下線 | `{"platform": str, "bot_id": str, "status": str}` |

### 事件接收與處理

| 鈎子名稱 | 觸發時機 | 數據 |
|---------|---------|------|
| `adapter.event.receive` | 收到外部平台事件（最早期） | `{"platform": str, "event_type": str, "raw_event_type": str}` |
| `adapter.event.dispatched` | 事件分發完成 | `{"platform": str, "event_type": str, "raw_event_type": str, "onebot_handlers_count": int}` |
| `event.pre_process` | 事件處理器開始執行前 | `{"event_type": str, "platform": str, "detail_type": str}` |

**範例：事件統計**

```python
event_counter = {}

@sdk.lifecycle.on("adapter.event.receive")
def count_events(data):
    platform = data["platform"]
    event_counter[platform] = event_counter.get(platform, 0) + 1

@sdk.lifecycle.on("adapter.event.dispatched")
def log_unhandled(data):
    if data["onebot_handlers_count"] == 0:
        print(f"[未處理] {data['platform']}/{data['event_type']}")
```

### 消息發送

| 鈎子名稱 | 觸發時機 | 數據 |
|---------|---------|------|
| `message.sending` | 消息即將發送 | `{"platform": str, "method": str, "detail_type": str, "target_id": str, "bot_id": str}` |
| `message.sent` | 消息發送完成 | `{"platform": str, "method": str, "detail_type": str, "target_id": str, "bot_id": str}` |

**範例：消息發送審計**

```python
@sdk.lifecycle.on("message.sending")
def log_sending(data):
    print(f"[發送] -> {data['platform']}/{data['detail_type']}/{data['target_id']} via {data['method']}")
```

### 命令系統

| 鈎子名稱 | 觸發時機 | 數據 |
|---------|---------|------|
| `command.matched` | 命令被匹配並即將執行 | `{"command": str, "args": list[str], "platform": str, "user_id": str}` |
| `command.executed` | 命令執行完成 | `{"command": str, "args": list[str], "platform": str, "user_id": str, "success": bool, "error": str(僅失敗時)}` |

**範例：命令統計**

```python
@sdk.lifecycle.on("command.matched")
def count_commands(data):
    print(f"[命令] /{data['command']} from {data['user_id']}@{data['platform']}")
```

### HTTP 路由

| 鈎子名稱 | 觸發時機 | 數據 |
|---------|---------|------|
| `server.request` | HTTP 請求接收 | `{"method": str, "path": str, "client_ip": str}` |
| `server.response` | HTTP 回應發送 | `{"method": str, "path": str, "status_code": int, "client_ip": str}` |

**範例：請求日誌**

```python
@sdk.lifecycle.on("server.response")
def log_http(data):
    print(f"[HTTP] {data['method']} {data['path']} -> {data['status_code']}")
```

### WebSocket

| 鈎子名稱 | 觸發時機 | 數據 |
|---------|---------|------|
| `server.start` | 路由伺服器啟動 | `{"base_url": str, "host": str, "port": int}` |
| `server.stop` | 路由伺服器停止 | `{}` |
| `server.websocket.connect` | WebSocket 連接建立 | `{"path": str, "module_name": str, "client_ip": str}` |
| `server.websocket.disconnect` | WebSocket 連接斷開 | `{"path": str, "module_name": str, "reason": str, "error": str(僅異常時)}` |

**範例：WebSocket 連接監控**

```python
@sdk.lifecycle.on("server.websocket.connect")
def on_ws_connect(data):
    print(f"[WS] 連接: {data['path']} from {data['client_ip']}")

@sdk.lifecycle.on("server.websocket.disconnect")
def on_ws_disconnect(data):
    print(f"[WS] 斷開: {data['path']} ({data['reason']})")
```

## 標準事件定義

```python
STANDARD_EVENTS = {
    "core": ["init.start", "init.complete", "uninit.complete"],
    "module": ["load", "init", "unload", "register"],
    "adapter": [
        "load", "start", "status.change", "stop", "stopped",
        "event.receive", "event.dispatched",
        "bot.online", "bot.offline",
    ],
    "server": [
        "start", "stop",
        "request", "response",
        "websocket.connect", "websocket.disconnect",
    ],
    "event": ["pre_process"],
    "message": ["sending", "sent"],
    "command": ["matched", "executed"],
    "config": ["set"],
}
```

## 完整 API 參考

### 註冊與取消

| 方法 | 說明 |
|------|------|
| `@lifecycle.on(event, *, priority=0)` | 裝飾器註冊處理器 |
| `lifecycle.register(event, handler, *, priority=0)` | 編程式註冊 |
| `lifecycle.unregister(event, handler=None)` | 取消註冊（handler=None 時取消該事件全部處理器） |

### 觸發

| 方法 | 說明 |
|------|------|
| `await lifecycle.emit(event, data=None)` | 異步觸發，處理器返回非 None 可修改 data |
| `lifecycle.emit_sync(event, data=None)` | 同步觸發，異步處理器以 create_task 調度 |
| `await lifecycle.submit_event(event_type, *, source, msg, data)` | 兼容舊版，自動建構標準事件格式 |

### 工具

| 方法 | 說明 |
|------|------|
| `lifecycle.start_timer(timer_id)` | 開始計時 |
| `lifecycle.get_duration(timer_id)` | 獲取已持續時間（秒） |
| `lifecycle.stop_timer(timer_id)` | 停止計時並返回持續時間 |
| `lifecycle.list_hooks()` | 列出所有已註冊鈎子及處理器數量 |
| `lifecycle.clear()` | 清除所有處理器和計時器 |

## 模組中使用範例

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse import sdk

class Main(BaseModule):
    async def on_load(self, event):
        # 實現簡單的消息統計
        self.msg_count = 0
        
        @sdk.lifecycle.on("adapter.event.receive")
        async def count(data):
            if data["event_type"] == "message":
                self.msg_count += 1
        
        # 監控所有命令
        @sdk.lifecycle.on("command.matched")
        async def log_cmd(data):
            sdk.logger.info(f"命令執行: /{data['command']} by {data['user_id']}")
        
        # 配置變更審計
        @sdk.lifecycle.on("config.set")
        def audit(data):
            sdk.logger.info(f"配置變更: {data['key']} = {data['new_value']}")
```

## 後台任務歸屬與自動取消

> [!NOTE]
> 本特性需要 ErisPulse **2.8.0+**。

模組創建的 asyncio 後台任務若未在 `on_unload` 中取消，會持有 `self` 引用導致模組實例無法被回收（熱重載後舊實例殘留）。框架提供以下兜底機制：

- **`self.spawn(coro)`**（模組內推薦）：任務自動歸屬模組名，模組卸載時框架在 `on_unload` **之後**兜底取消未結束的任務並記錄警告
- **`spawn_background(coro)`**（`ErisPulse.runtime`）：自動捕獲當前 `owner_scope` 上下文；`cancel_owner_tasks(owner)` 按歸屬取消，`cancel_all_background_tasks()` 供 `sdk.uninit()` 兜底
- **適配器**：關閉時對平台名下的後台任務同樣兜底取消

```python
async def on_load(self, event):
    # 推薦：後台任務用 self.spawn()，卸載時框架自動兜底取消
    self.spawn(self._poll())

async def on_unload(self, event):
    # 精細控制的場景仍建議自行取消並等待收尾
    if self._poll_task:
        self._poll_task.cancel()
        await asyncio.gather(self._poll_task, return_exceptions=True)

async def _poll(self):
    while True:
        await asyncio.sleep(60)
        ...
```

> [!IMPORTANT]
> 框架兜底是**強制 cancel**（`cancel_owner_tasks`），它發生在 `on_unload` 回傳之後。因此需要優雅收尾的任務（flush 缓衝、持久化狀態、關閉連接）**必須**在 `on_unload` 裡自行 `cancel()` + `await` 完成——別指望兜底能保留收尾邏輯。框架只保證「不殘留持有 `self` 的任務」，不保證「優雅」。需要 `await` 結果的任務請直接 `await`，不要丟給後台任務。

## 注意事項

1. **處理器可以是同步或異步**：系統自動辨識並正確呼叫
2. **數據傳遞**：`emit()` 模式下，處理器返回非 None 值會修改傳遞給後續處理器的 data
3. **事件命名規範**：建議使用點式結構命名事件，便於使用父級監聽
4. **錯誤隔離**：單個處理器異常不會影響其他處理器執行
5. **同步觸發限制**：`emit_sync()` 中異步處理器以 fire-and-forget 方式調度，回傳值無法回傳
6. **生命週期清理**：呼叫 `sdk.uninit()` 時，所有已註冊的處理器和計時器會被清理
7. **加載優先性**：如需在框架初始化階段就監聽事件，建議設定高優先級並禁用懶加載

## 相關文件

- [模組開發指南](../developer-guide/modules/getting-started.md) - 了解模組生命週期方法
- [最佳實踐](../developer-guide/modules/best-practices.md) - 生命週期事件使用建議



### 路由系统

# 路由管理器

ErisPulse 路由管理器提供統一的 HTTP 和 WebSocket 路由管理，支援多適配器路由註冊和生命週期管理。底層透過抽象層封裝（目前為 FastAPI + Uvicorn）

## 概述

路由管理器的主要功能：

- **裝飾器路由**：支援 `@http` / `@get` / `@post` / `@put` / `@delete` / `@ws` 裝飾器快捷註冊
- **自動注入**：路由處理器無需匯入 FastAPI 類型，框架自動注入抽象物件
- **路由分組**：支援帶前綴和版本號的 `RouteGroup`
- **路由中間件**：支援 glob 模式匹配的請求攔截
- **速率限制**：內建滑動視窗限流
- **CORS 支援**：一鍵開啟跨域資源共享
- **安全頭**：自動添加安全回應頭
- **自動文件**：基於 OpenAPI 的互動式文件
- **WebSocket 支援**：完整的 WebSocket 連線管理、自訂認證和生命週期鉤子
- **生命週期整合**：與 ErisPulse 生命週期系統深度整合
- **SSL/TLS 支援**：支援 HTTPS 和 WSS 安全連線
- **主頁入口**：支援模組在根路由 `/` 註冊快捷入口按鈕，支援國際化

## 抽象類型

ErisPulse 提供了服務端抽象類型，使模組無需直接依賴 FastAPI：

| 抽象類型 | FastAPI 對應 | 說明 |
|---------|-------------|------|
| `HttpRequest` | `fastapi.Request` | HTTP 請求封裝，介面完全相容 |
| `WebSocketConnection` | `fastapi.WebSocket` | WebSocket 連線封裝，額外提供生命週期鉤子 |
| `WebSocketDisconnect` | `fastapi.WebSocketDisconnect` | WebSocket 斷開異常 |

> `WebSocketConnection` 繼承自 `WebSocketConnectionBase`，與客戶端 WebSocket (`ClientWebSocket`) 共享相同的 send/receive/iter/close 介面。客戶端和服務端 WebSocket 可以使用相同的業務邏輯程式碼。
>
> 透過 `.raw` 屬性可存取底層 FastAPI 原生物件。直接使用 FastAPI 類型的程式碼也完全相容。

## 裝飾器路由（推薦）

### HTTP 裝飾器

```python
from ErisPulse.Core import router
@router.get("my_module", "/info")
async def get_info(request):
    return {"method": request.method, "path": str(request.url)}

# 也可顯式標註抽象類型
from ErisPulse.Core import HttpRequest

@router.post("my_module", "/data")
async def post_data(request: HttpRequest):
    data = await request.json()
    return {"received": data}

@router.put("my_module", "/data/{item_id}")
async def update_data(request):
    return {"updated": True}

@router.delete("my_module", "/data/{item_id}")
async def delete_data(request):
    return {"deleted": True}
```

> **自動注入規則**：當處理器第一個參數名為 `request` 或 `req` 且無 FastAPI 類型註解時，框架自動注入 `HttpRequest`。無參數或非請求參數名的處理器不受影響。

### WebSocket 裝飾器

```python
from ErisPulse.Core import WebSocketConnection, WebSocketDisconnect

# 基本 WebSocket
@router.ws("my_module", "/ws")
async def websocket_handler(ws):
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")

# 帶生命週期鉤子的 WebSocket
@router.ws("my_module", "/ws/chat")
async def chat(ws: WebSocketConnection):
    @ws.on_disconnect
    async def on_disconnect(ws, reason="unknown"):
        print(f"用戶斷開: {reason}")

    @ws.on_error
    async def on_error(ws, error=""):
        print(f"連線錯誤: {error}")

    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")

# 帶認證的 WebSocket
async def ws_auth(ws: WebSocketConnection) -> bool:
    token = ws.query_params.get("token")
    return token == "secret"

@router.ws("my_module", "/secure_ws", auth_handler=ws_auth)
async def secure_ws_handler(ws):
    while True:
        data = await ws.receive_text()
        await ws.send_text(f"Echo: {data}")
```

> **注意**：WebSocket 處理器和認證處理器也支援自動注入。無需參數註解即可獲得 `WebSocketConnection`。標註 `fastapi.WebSocket` 也可傳入原生物件，但推薦使用抽象類型。

## 傳統註冊方式

```python
async def hello_handler(request):
    return {"message": "Hello World"}

# 基本註冊
router.register_http_route(
    module_name="my_module",
    path="/hello",
    handler=hello_handler,
    methods=["GET"],
)

# 帶限流和文件資訊
router.register_http_route(
    module_name="my_module",
    path="/api/data",
    handler=data_handler,
    methods=["POST"],
    rate_limit="10/minute",
    summary="數據介面",
    tags=["API"],
)
```

### WebSocket 註冊

```python
from ErisPulse.Core import WebSocketConnection

async def websocket_handler(ws: WebSocketConnection):
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")

# 基本註冊
router.register_websocket(
    module_name="my_module",
    path="/ws",
    handler=websocket_handler,
)

# 帶認證的註冊（推薦）
async def auth_handler(ws: WebSocketConnection) -> bool:
    token = ws.query_params.get("token")
    return token == "secret"

router.register_websocket(
    module_name="my_module",
    path="/secure_ws",
    handler=websocket_handler,
    auth_handler=auth_handler,
)
```

**參數說明：**

| 參數 | 說明 | 預設值 |
|------|------|--------|
| `module_name` | 模組名稱（必須） | - |
| `path` | WebSocket 路徑 | - |
| `handler` | 處理函數 | - |
| `auth_handler` | 認證函數，回傳 `False` 會自動關閉連線 | `None` |
| `auto_accept` | 是否自動 `accept()` | `True` |

> **推薦**：使用 `auth_handler` 進行連線確認，而非關閉 `auto_accept`。僅在你需要完全控制連線流程時才設定 `auto_accept=False`。

## WebSocket 生命週期鉤子

`WebSocketConnection` 提供了斷開連線和錯誤的回調註冊，無需手動 try/catch：

```python
from ErisPulse.Core import WebSocketConnection

@router.ws("my_module", "/ws")
async def my_ws(ws: WebSocketConnection):
    # 裝飾器方式註冊
    @ws.on_disconnect
    async def on_close(ws, reason="unknown"):
        print(f"斷開原因: {reason}")

    # 也可直接呼叫
    async def on_err(ws, error=""):
        print(f"錯誤: {error}")
    ws.on_error(on_err)

    # 正常業務邏輯
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")
```

## 路由分組

```python
# 建立帶前綴的路由組
group = router.group("my_module", prefix="/v1")

@group.get("/users")
async def list_users(request):
    return {"users": []}

@group.post("/users")
async def create_user(request):
    return {"created": True}

# 實際路徑: /my_module/v1/users
```

## 路由中間件

中間件支援 glob 模式匹配路徑：

```python
@router.middleware("/my_module/*")
async def auth_middleware(request, call_next):
    token = request.headers.get("Authorization")
    if not token:
        return {"error": "Unauthorized"}
    return await call_next(request)

@router.middleware("/my_module/admin/*")
async def admin_middleware(request, call_next):
    return await call_next(request)
```

## 請求關聯 ID（X-Request-ID）

從 2.7.0 起，每個 HTTP 請求都會攜帶一個 `X-Request-ID` 關聯 ID，用於日誌 / 鏈路追蹤串聯：

- **生成規則**：優先沿用客戶端傳入的 `X-Request-ID` 請求頭（分散式追蹤場景）；否則自產生 UUID
- **回應頭**：回應會回寫 `X-Request-ID`，方便客戶端把請求與日誌對應
- **生命週期事件**：`server.request` 與 `server.response` 事件資料中新增 `request_id` 欄位

```python
# 在模組中監聽請求事件，按 request_id 串聯請求-回應
@sdk.lifecycle.on("server.request")
async def on_request(data):
    print(f"[{data['request_id']}] {data['method']} {data['path']}")

@sdk.lifecycle.on("server.response")
async def on_response(data):
    print(f"[{data['request_id']}] -> {data['status_code']}")
```

客戶端可自訂 ID 以便跨服務追蹤：

```bash
curl -H "X-Request-ID: my-trace-id" http://localhost:8080/my_module/health
```

## 速率限制

使用滑動視窗演算法對路由進行限流：

```python
@router.get("my_module", "/limited", rate_limit="10/minute")
async def limited_endpoint(request):
    return {"ok": True}

@router.post("my_module", "/submit", rate_limit="5/minute")
async def submit_data(request):
    return {"submitted": True}
```

速率限制格式：`{次數}/{時間視窗}`，如 `10/minute`、`100/hour`。

## CORS 配置

```python
router.setup_cors(
    allow_origins=["https://example.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

也可透過 `config.toml` 配置：

```toml
[router.cors]
allow_origins = ["https://example.com"]
allow_methods = ["GET", "POST"]
allow_headers = ["*"]
```

## 安全頭

```python
router.setup_security_headers()
```

自動添加 `X-Content-Type-Options`、`X-Frame-Options`、`X-XSS-Protection` 等安全頭。

也可透過 `config.toml` 配置：

```toml
[router.security]
enabled = true
```

## 自動文件

Router 預設啟用 OpenAPI 互動式文件：

```python
# 禁用文件
router.disable_docs()

# 自訂文件資訊
router.set_docs_info(
    title="My API",
    description="API 文件",
    version="1.0.0"
)
```

## 路徑處理

路由路徑會自動添加模組名稱作為前綴，避免衝突：

```python
# 註冊路徑 "/api" 到模組 "my_module"
# 實際存取路徑為 "/my_module/api"
router.register_http_route("my_module", "/api", handler)
```

## 系統路由

路由管理器自動提供以下系統路由：

### 健康檢查

```
GET /health
# 回傳:
{"status": "ok", "service": "ErisPulse Router"}
```

### 根頁面

```
GET /
# 回傳 ErisPulse 品牌頁
```

根路由 `/` 顯示 ErisPulse 品牌頁面，自動檢測 Dashboard 可用性並添加入口按鈕。

## 主頁入口

路由管理器允許外部模組在根路由 `/` 上註冊快捷入口按鈕，方便使用者快速存取各模組的管理頁面。

### 註冊入口

```python
# 簡單註冊
router.register_home_entry(
    name="我的面板",
    url="/mymodule/admin",
)

# 帶圖示的註冊（SVG）
router.register_home_entry(
    name="控制台",
    url="/console",
    icon_svg='<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 17l6-6-6-6"/><path d="M12 19h8"/></svg>',
)

# 支援國際化的註冊（項目 i18n 字典格式）
router.register_home_entry(
    name={"i18n": "mymodule.home.entry", "default": "我的面板"},
    url="/mymodule/admin",
)
```

**參數說明：**

| 參數 | 類型 | 說明 | 必填 |
|------|------|------|------|
| `name` | `str` / `dict` | 按鈕顯示文字；傳入 `{"i18n": "key", "default": "文字"}` 字典時使用國際化 | 是 |
| `url` | `str` | 按鈕連結位址 | 是 |
| `icon_svg` | `str` | 可選 SVG 圖示標記 | 否 |

### Dashboard 自動註冊

當檢測到 `sdk.Dashboard` 可用時，路由管理器自動在入口列表首位添加 Dashboard 按鈕，無需手動註冊。

## 生命週期整合

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("server.start")
async def on_server_start(event):
    print(f"伺服器已啟動: {event['data']['base_url']}")

@lifecycle.on("server.stop")
async def on_server_stop(event):
    print("伺服器正在停止...")
```

## 最佳實踐

1. **優先使用抽象類型**：使用 `HttpRequest` / `WebSocketConnection` 替代 `fastapi.Request` / `fastapi.WebSocket`，避免硬依賴
2. **利用自動注入**：處理器第一個參數命名為 `request` 或 `req`，無需任何類型註解即可獲得 `HttpRequest`
3. **顯式傳入 module_name**：裝飾器第一個參數必須為模組名，不可省略
4. **使用路由分組**：對同一模組的多個路由使用 `group()` 組織
5. **安全性考量**：為敏感操作實作認證機制和安全頭
6. **合理限流**：對高頻介面設定速率限制
7. **使用生命週期鉤子**：透過 `@ws.on_disconnect` / `@ws.on_error` 處理 WebSocket 異常，避免手動 try/catch

## 相關文件

- [HTTP 客戶端](docs/zh-TW/http-client.md) - 使用內建 HTTP 客戶端發送請求
- [模組開發指南](docs/zh-TW/developer-guide/modules/getting-started.md) - 了解模組路由註冊
- [最佳實踐](docs/zh-TW/developer-guide/modules/best-practices.md) - 路由使用建議



### MessageBuilder 详解

# MessageBuilder 詳解

`MessageBuilder` 是 ErisPulse 提供的 OneBot12 標準消息段構建工具，用於構建結構化的消息內容，配合 `Send.Raw_ob12()` 使用。

## 導入方式

`MessageBuilder` 支援以下兩種導入方式（效果相同，推薦使用第一種）：

```python
from ErisPulse.Core.Event import MessageBuilder        # 推薦，透過包導出
from ErisPulse.Core.Event.message_builder import MessageBuilder  # 直接導入模組
```

## 雙模式機制

MessageBuilder 提供兩種使用模式，透過 Python 描述符機制（`__get__`）實現類別級別和實例級別的不同行為：當透過類呼叫方法時，`__get__` 返回靜態方法的執行結果；當透過實例呼叫時，返回 `self` 以支援鏈式呼叫。

### 鏈式呼叫模式（實例）

透過實例化 `MessageBuilder()` 使用，每個方法返回 `self`，支援鏈式呼叫，最後用 `.build()` 獲取消息段列表：

```python
from ErisPulse.Core.Event.message_builder import MessageBuilder

segments = (
    MessageBuilder()
    .text("你好！")
    .image("https://example.com/photo.jpg")
    .build()
)
# [
#     {"type": "text", "data": {"text": "你好！"}},
#     {"type": "image", "data": {"file": "https://example.com/photo.jpg"}}
# ]
```

### 快速構建模式（靜態）

透過類直接呼叫方法，每個方法直接返回消息段列表，適合單段消息：

```python
# 直接返回 list[dict]，無需 .build()
segments = MessageBuilder.text("你好！")
# [{"type": "text", "data": {"text": "你好！"}}]
```

## 消息段類型

| 方法 | 類型 | 數據參數 | 說明 |
|------|------|---------|------|
| `text(text)` | text | `text` | 文本消息 |
| `image(file)` | image | `file` | 圖片消息 |
| `audio(file)` | audio | `file` | 音頻消息 |
| `video(file)` | video | `file` | 視頻消息 |
| `file(file, filename?)` | file | `file`, `filename` | 文件消息 |
| `mention(user_id, user_name?)` | mention | `user_id`, `user_name` | @提及用戶 |
| `at(user_id, user_name?)` | mention | `user_id`, `user_name` | `mention` 的別名 |
| `reply(message_id)` | reply | `message_id` | 回覆消息 |
| `at_all()` | mention_all | - | @全體成員 |
| `custom(type, data)` | 自定義 | 自定義 | 自定義消息段 |

## 配合 Send 使用

構建的消息段列表透過 `Send.Raw_ob12()` 發送：

```python
from ErisPulse import sdk
from ErisPulse.Core.Event.message_builder import MessageBuilder

# 鏈式構建 + 發送
segments = (
    MessageBuilder()
    .mention("user123", "張三")
    .text(" 請查看這張圖片")
    .image("https://example.com/photo.jpg")
    .build()
)
await sdk.adapter.myplatform.Send.To("group", "group456").Raw_ob12(segments)
```

### 配合 Event 回覆

```python
from ErisPulse.Core.Event import command

@command("report")
async def report_handler(event):
    await event.reply_ob12(
        MessageBuilder()
        .text("📊 日報彙總\n")
        .text("今日完成任務: 5\n")
        .text("進行中任務: 3")
        .build()
    )
```

## 工具方法

### copy()

複製當前構建器，用於基於同一基礎內容創建多個消息變體：

```python
base = MessageBuilder().text("基礎內容").mention("admin")

# 基於相同前綴構建不同消息
msg1 = base.copy().text(" 變體A").build()
msg2 = base.copy().text(" 變體B").image("img.jpg").build()
```

### clear()

清空已添加的消息段，複用同一個構建器：

```python
builder = MessageBuilder()

for user_id in ["user1", "user2", "user3"]:
    builder.clear()
    msg = builder.mention(user_id).text(" 你好！").build()
    await adapter.Send.To("user", user_id).Raw_ob12(msg)
```

### len() / bool()

```python
builder = MessageBuilder()
print(bool(builder))   # False

builder.text("Hello")
print(len(builder))    # 1
print(bool(builder))   # True
```

## 自定義消息段

使用 `custom()` 方法添加平台擴展消息段：

```python
# 添加平台特有的消息段
segments = (
    MessageBuilder()
    .text("請填寫表單：")
    .custom("yunhu_form", {"form_id": "12345"})
    .build()
)
```

> 自定義消息段只在對應平台的適配器中有效，其他適配器會忽略不認識的消息段。

## 完整示例

### 多元素消息

```python
segments = (
    MessageBuilder()
    .reply(event.get_id())                    # 回覆原消息
    .mention(event.get_user_id())             # @發送者
    .text(" 這是你的查詢結果：\n")             # 文本
    .image("https://example.com/chart.png")   # 圖片
    .text("\n詳細數據見附件：")
    .file("https://example.com/data.csv", filename="data.csv")
    .build()
)
await event.reply_ob12(segments)
```

### 靜態工廠 + 鏈式混合

```python
# 快速構建單段消息
simple_msg = MessageBuilder.text("簡單文本")

# 鏈式構建複雜消息
complex_msg = (
    MessageBuilder()
    .at_all()
    .text(" 📢 公告：")
    .text("今天下午3點開會")
    .build()
)
```



### Conversation 多轮对话

# Conversation 多輪對話

`Conversation` 類提供了在同一會話中進行多輪互動的便捷方法，適合實現引導式操作、資訊收集、對話式問答等場景。

## 創建對話

透過 `Event` 物件的 `conversation()` 方法建立：

```python
from ErisPulse.Core.Event import command

@command("quiz")
async def quiz_handler(event):
    conv = event.conversation(timeout=30)

    await conv.say("🎮 歡迎參加知識問答！")

    answer = await conv.choose("第一題：Python 的創造者是誰？", [
        "Guido van Rossum",
        "James Gosling",
        "Dennis Ritchie",
    ])

    if answer is None:
        await conv.say("超時了，下次再來吧！")
        return

    if answer == 0:
        await conv.say("正確！")
    else:
        await conv.say("錯誤了，正確答案是 Guido van Rossum")

    conv.stop()
```

## 核心 API

### `say(content, **kwargs)`

發送訊息，並返回 `self` 以支援鏈式呼叫：

```python
await conv.say("第一行").say("第二行").say("第三行")
```

也可以指定發送方法：

```python
await conv.say("https://example.com/image.jpg", method="Image")
```

### `wait(prompt=None, timeout=None)`

等待使用者回覆，並返回 `Event` 物件或 `None`（超時）：

```python
# 簡單等待
resp = await conv.wait()
if resp:
    text = resp.get_text()

# 發送提示後等待
resp = await conv.wait(prompt="請輸入你的名字：")

# 使用自訂超時（覆蓋對話預設超時）
resp = await conv.wait(prompt="請在10秒內回覆：", timeout=10)
```

### `confirm(prompt=None, **kwargs)`

等待使用者確認（是/否），並返回 `True` / `False` / `None`（超時）：

```python
result = await conv.confirm("確定要刪除所有資料嗎？")
if result is True:
    await conv.say("已刪除")
elif result is False:
    await conv.say("已取消")
else:
    await conv.say("超時未回覆")
```

內建識別的確認詞：`是/yes/y/確認/確定/好/ok/true/對/嗯/行/同意/沒問題/可以/當然...`

內建識別的否定詞：`否/no/n/取消/不/不要/不行/cancel/false/錯/不對/別/拒絕...`

### `choose(prompt, options, **kwargs)`

等待使用者從選項中選擇，並返回選項索引（0-based）或 `None`：

```python
choice = await conv.choose("請選擇顏色：", ["紅色", "綠色", "藍色"])
if choice is not None:
    colors = ["紅色", "綠色", "藍色"]
    await conv.say(f"你選擇了 {colors[choice]}")
```

使用者可以透過輸入編號（`1`/`2`/`3`）或選項文字（`紅色`）來選擇。

`options_format="auto"`（預設）會根據 method 自動選擇內建樣式：Markdown→無序列表，Html→有序列表，其他→純文字列表。
也支援 `"list"`、`"inline"`、`"md"`、`"html"` 或自訂函數。

支援 `merge_prompt=True` 合併為一條訊息，以及占位符控制選項插入位置（預設 `{options}`，可透過 `placeholder` 自訂）：

```python
choice = await conv.choose(
    "## 請選擇\n{options}",
    ["選項A", "選項B"],
    method="Markdown",
    merge_prompt=True,
)

# 自訂占位符
choice = await conv.choose(
    "請選擇: [choices]",
    ["選項A", "選項B"],
    placeholder="[choices]",
)
```

### `collect(fields, **kwargs)`

多步驟收集資訊，並返回資料字典或 `None`：

```python
data = await conv.collect([
    {"key": "name", "prompt": "請輸入姓名"},
    {"key": "age", "prompt": "請輸入年齡",
     "validator": lambda e: e.get("alt_message", "").strip().isdigit(),
     "retry_prompt": "年齡必須是數字，請重新輸入"},
    {"key": "city", "prompt": "請輸入城市"},
])

if data:
    await conv.say(f"註冊成功！\n姓名: {data['name']}\n年齡: {data['age']}\n城市: {data['city']}")
else:
    await conv.say("註冊過程中斷")
```

欄位配置：

| 參數 | 說明 | 預設值 |
|------|------|--------|
| `key` | 欄位鍵名（必須） | - |
| `prompt` | 提示訊息 | `"請輸入 {key}"` |
| `validator` | 驗證函數，接收 Event，並回傳 bool | 無 |
| `retry_prompt` | 驗證失敗重試提示 | `"輸入無效，請重新輸入"` |
| `max_retries` | 最大重試次數 | 3 |
| `condition` | 條件函數，接收已收集資料 dict，並回傳 bool | 無 |

**條件欄位**：使用 `condition` 可以實現動態表單，只有條件滿足時才收集該欄位：

```python
data = await conv.collect([
    {"key": "has_car", "prompt": "你有車嗎？（是/否）"},
    {"key": "car_brand", "prompt": "請輸入車型",
     "condition": lambda d: d.get("has_car", "").lower() in ("是", "yes", "y")},
])
```

### `stop()`

手動結束對話，並設定 `is_active` 為 `False`：

```python
conv.stop()
```

### `is_active`

對話是否處於活躍狀態：

```python
if conv.is_active:
    await conv.say("對話還在進行中")
```

## 活躍狀態管理

```mermaid
stateDiagram-v2
    state "活躍" as active
    state "非活躍" as inactive
    [*] --> active: event.conversation()
    active --> active: say / wait / confirm / choose / collect
    active --> inactive: stop()
    active --> inactive: wait() 超時
    active --> inactive: collect() 超時或重試耗盡
    inactive --> [*]
```

對話在以下情況會自動變為非活躍狀態：

1. 調用 `stop()` 方法
2. `wait()` 超時返回 `None`
3. `collect()` 因任何步驟超時或重試耗盡而返回 `None`

非活躍後，所有交互方法（`wait`/`confirm`/`choose`/`collect`）會立即返回 `None`，不會繼續等待使用者輸入。

## 分支與跳轉

### @conv.branch(name) 裝飾器

使用 `branch()` 註冊對話分支，並透過 `goto()` 在分支間跳轉：

```python
@command("menu")
async def menu_handler(event):
    conv = event.conversation(timeout=60)

    @conv.branch("main")
    async def main_menu():
        await conv.say("=== 主菜單 ===\n1. 個人資訊\n2. 設定\n3. 退出")
        resp = await conv.wait()
        if resp is None:
            return
        text = resp.get_text().strip()
        if text == "1":
            await conv.goto("profile")
        elif text == "2":
            await conv.goto("settings")
        elif text == "3":
            await conv.say("再見！")
            conv.stop()

    @conv.branch("profile")
    async def profile():
        await conv.say("=== 個人資訊 ===\n姓名: Alice\n0. 返回")
        resp = await conv.wait()
        if resp and resp.get_text().strip() == "0":
            await conv.goto("main")

    @conv.branch("settings")
    async def settings():
        await conv.say("=== 設定 ===\n1. 通知開關\n0. 返回")
        resp = await conv.wait()
        if resp and resp.get_text().strip() == "0":
            await conv.goto("main")

    await conv.start()  # 從第一個註冊的分支開始
```

### conv.start(name=None)

啟動對話，預設從第一個註冊的分支開始：

```python
await conv.start()          # 從第一個分支開始
await conv.start("settings") # 從指定分支開始
```

## 上下文與持久化

### conv.context

每個對話實例內建 `context` 字典，用於在分支間共享狀態：

```python
@conv.branch("step1")
async def step1():
    conv.context["username"] = resp.get_text().strip()
    await conv.goto("step2")

@conv.branch("step2")
async def step2():
    name = conv.context.get("username", "未知")
    await conv.say(f"你好，{name}！")
```

### save() / resume() / clear_saved()

對話支援持久化，可在超時或中斷後恢復：

```python
# 保存對話狀態
conv_id = conv.save()
# conv_id = "user_123_group_456"  # 基於使用者和群組自動生成

# ... 之後在同一會話中恢復 ...
conv2 = event.conversation()
if conv2.resume():
    await conv2.say("歡迎回來！繼續之前的對話")
else:
    await conv2.say("沒有找到之前的對話")

# 清除保存的對話
conv.clear_saved()
```

## 典型流程模式

### 引導式註冊

```python
@command("register")
async def register_handler(event):
    conv = event.conversation(timeout=60)

    await conv.say("歡迎註冊！")

    data = await conv.collect([
        {"key": "username", "prompt": "請輸入用戶名（3-20個字符）",
         "validator": lambda e: 3 <= len(e.get_text().strip()) <= 20},
        {"key": "email", "prompt": "請輸入電子郵箱地址",
         "validator": lambda e: "@" in e.get_text() and "." in e.get_text(),
         "retry_prompt": "電子郵箱格式不正確，請重新輸入"},
    ])

    if not data:
        await event.reply("註冊已取消")
        return

    confirmed = await conv.confirm(
        f"確認註冊信息？\n用戶名: {data['username']}\n電子郵箱: {data['email']}"
    )

    if confirmed:
        await conv.say("✅ 註冊成功！")
    else:
        await conv.say("❌ 已取消註冊")
```

### 循環對話

```python
@command("chat")
async def chat_handler(event):
    conv = event.conversation(timeout=120)
    await conv.say("進入對話模式，輸入「退出」結束")

    while conv.is_active:
        resp = await conv.wait()
        if resp is None:
            await conv.say("超時，對話結束")
            break

        text = resp.get_text().strip()

        if text == "退出":
            await conv.say("再見！")
            conv.stop()
        elif text == "幫助":
            await conv.say("可用命令：退出、幫助、狀態")
        elif text == "狀態":
            await conv.say("對話活躍中")
        else:
            await conv.say(f"你說的是：{text}")
```

## 相關文件

- [Event 包裝類](../developer-guide/modules/event-wrapper.md) - Event 物件的所有方法
- [事件處理入門](../getting-started/event-handling.md) - 事件處理基礎



### 国际化（i18n）系统

# 國際化 (i18n) 系統

ErisPulse v2.5.0 起內建了完整的國際化支援。框架核心及 CLI 界面均可根據您的系統語言自動切換顯示文字，也支援外部模組註冊自己的翻譯。



## 支援的語言

| 語言 | 代碼 | 說明 |
|------|------|------|
| 簡體中文 | `zh-CN` | 預設語言（框架原生語言） |
| 繁體中文 | `zh-TW` | 繁體中文（香港/澳門/臺灣） |
| English | `en` | 英文（通用回退語言） |
| 日本語 | `ja` | 日文 |
| Русский | `ru` | 俄文 |

## 快速體驗

### 透過環境變數切換

```bash
# Windows PowerShell
$env:ERISPULSE_LANG = "en"
epsdk run

# macOS / Linux
ERISPULSE_LANG=ja epsdk run
```

### 透過設定檔案切換

在 `config/config.toml` 中新增：

```toml
[ErisPulse.i18n]
language = "zh-TW"
```

設為 `"auto"`（預設值）則自動偵測系統語言。

### 在程式碼中手動切換

```python
from ErisPulse import i18n

# 手動設定語言
i18n.set_language("en")
print(i18n.get_language())  # "en"

# 重設為自動偵測
i18n.reset_language()
```

---

## 語言檢測機制

框架按照以下優先級檢測使用者語言：

1. **環境變數 `ERISPULSE_LANG`** — 最高優先級，用於測試和暫時切換
2. **Windows API** — `GetUserDefaultLocaleName`（僅 Windows，不受 Git Bash 等工具覆蓋 `LANG` 的影響）
3. **環境變數** — `LANGUAGE` > `LC_ALL` > `LC_MESSAGES` > `LANG`（Unix/macOS 標準）
4. **系統 Locale** — `locale.getlocale()` / `locale.getdefaultlocale()`
5. **兜底** — en（英文）

### 就近映射原則

當檢測到的語言不是精確匹配時，按就近原則映射到支援的語言：

- `zh-TW`, `zh-HK`, `zh-MO`, `zh-Hant` → **繁體中文**
- 其他所有 `zh-*`（如 `zh-CN`, `zh-SG`）→ **簡體中文**
- `en-US`, `en-GB`, `en-AU` 等 → **英文**
- `ja-JP` → **日文**
- `ru-RU` → **俄文**
- 其他未識別語言 → **簡體中文（兜底）**

---



## 在模組中使用 i18n

您可以為自己的模組註冊翻譯文字，讓您的模組也支援多語言。

### 推薦寫法：透過 I18nClass 宣告翻譯鍵（v2.7.0+）

從 v2.7.0 起，模組/適配器可以像宣告 `ConfigClass` 一樣，透過巢狀類 `I18nClass` 宣告翻譯鍵。框架會在載入時**自動註冊**所有宣告的翻譯鍵，無需手動呼叫 `i18n.register()`。

```python
from dataclasses import dataclass, field

from ErisPulse.Core.Bases import BaseConfig, BaseI18n, BaseModule, I18nKey


class MyModule(BaseModule):
    # 設定類別（選用）
    @dataclass
    class ConfigClass(BaseConfig):
        welcome_msg: str = field(
            default="歡迎",
            metadata={
                # 這裡引用了 i18n 鍵 mymodule.welcome_msg
                "description": {"i18n": "mymodule.welcome_msg", "default": "歡迎訊息"},
            },
        )

    # 翻譯鍵集合類別（選用）
    # 宣告的鍵會被框架自動註冊，優先順序早於 ConfigClass 產生預設設定
    class I18nClass(BaseI18n):
        # 屬性名自動拼接為完整鍵路徑：<模組名>.<屬性名>
        welcome_msg: I18nKey = I18nKey(
            default="Welcome Message",   # 語言無關的兜底，不註冊到任何語言
            zh_CN="歡迎訊息",
            en="Welcome Message",
            ja="ウェルカムメッセージ",
            ru="Приветственное сообщение",
            zh_TW="歡迎訊息",
        )
        # 業務用到的其他翻譯鍵
        hello: I18nKey = I18nKey(
            default="Hello, {name}!",
            zh_CN="你好，{name}！",
            zh_TW="你好，{name}！",
            en="Hello, {name}!",
            ja="こんにちは、{name}！",
            ru="Привет, {name}!",
        )

        # 也可以顯式指定完整鍵路徑（不使用屬性名拼接）
        custom: I18nKey = I18nKey(
            key="mymodule.deep.nested.key",
            default="Default text",
            zh_CN="預設文字",
            zh_TW="預設文本",
            en="Default text",
            ja="デフォルトテキスト",
            ru="Текст по умолчанию",
        )
```

#### 為什麼推薦 I18nClass？

| 場景 | 手動 i18n.register() | I18nClass 宣告式 |
|------|-----------------------|------------------|
| 設定描述引用的 i18n 鍵 | 需手動註冊，且要趕在設定產生前 | 框架自動在設定產生前註冊 |
| 多語言翻譯宣告 | 散落在各個 on_load() 中 | 集中在類別裡，一目了然 |
| 鍵名命名一致性 | 容易拼寫錯誤 | 屬性名作為鍵名後綴，IDE 可補全 |
| 卸載時清理 | 需手動 unregister_domain() | 框架使用統一 domain 註冊 |

#### I18nClass 的鍵路徑規則

- **預設**：使用 ``<模組註冊名>.<屬性名>`` 作為完整鍵路徑
  - 範例：模組名為 ``MyModule``，屬性 ``welcome`` → 鍵路徑 ``MyModule.welcome``
- **顯式**：透過 ``I18nKey(key="...")`` 參數指定任意點分路徑
  - 適合深層巢狀的鍵名（如 ``mymodule.config.basic.token``）

#### 在適配器中使用

適配器同樣支援 `I18nClass`，使用方式完全一致：

```python
from ErisPulse.Core import BaseAdapter
from ErisPulse.Core.Bases import BaseConfig, BaseI18n, I18nKey


class MyAdapter(BaseAdapter):
    @dataclass
    class ConfigClass(BaseConfig):
        endpoint: str = field(
            default="",
            metadata={
                # 設定描述引用了 adapter.MyAdapter.endpoint 鍵
                "description": {"i18n": "MyAdapter.endpoint", "default": "API 位址"},
            },
        )

    class I18nClass(BaseI18n):
        # 集中宣告設定描述引用的鍵與其他業務鍵的多語言譯文
        endpoint: I18nKey = I18nKey(
            default="API Endpoint",
            zh_CN="API 位址",
            zh_TW="API 位址",
            en="API Endpoint",
            ja="APIアドレス",
            ru="API адрес",
        )
```

適配器的 `I18nClass` 會在 `__init__` 階段（即設定範本產生之前）自動註冊，確保設定描述引用的 i18n 鍵已可用。

### 手動註冊自訂翻譯（舊寫法）

如果不使用 `I18nClass`，也可以直接呼叫 `i18n.register()` 註冊翻譯文字。

```python
from ErisPulse import i18n

# 註冊中文翻譯
i18n.register("zh-CN", {
    "my_module.welcome": "歡迎使用我的模組！",
    "my_module.goodbye": "再見！",
    "my_module.hello": "你好，{name}！",
}, domain="my_module")

# 註冊英文翻譯
i18n.register("en", {
    "my_module.welcome": "Welcome to my module!",
    "my_module.goodbye": "Goodbye!",
    "my_module.hello": "Hello, {name}!",
}, domain="my_module")
```

### 使用翻譯

```python
from ErisPulse import i18n

# 簡單翻譯
i18n.t("my_module.welcome")  # 自動使用目前語言

# 帶格式化參數
i18n.t("my_module.hello", name="Alice")

# 指定預設值（翻譯鍵不存在時傳回）
i18n.t("my_module.unknown_key", default="預設文本")
```

### 在模組類別中使用

```python
from dataclasses import dataclass, field
from ErisPulse import i18n
from ErisPulse.Core.Bases import BaseConfig, BaseModule

@dataclass
class MyModuleConfig(BaseConfig):
    welcome_msg: str = field(
        default="歡迎",
        metadata={
            "description": {"i18n": "my_module.welcome_msg", "default": "歡迎訊息"},
            "ui": {"widget": "text", "group": "basic", "order": 1},
        },
    )

class MyModule(BaseModule):
    ConfigClass = MyModuleConfig

    async def on_load(self, event):
        # 即時讀取設定（每次存取都反映最新值）
        self.logger.info(self.cfg.welcome_msg)
        self.logger.info(i18n.t("my_module.welcome"))

    @command("hello")
    async def hello_handler(self, event):
        name = event.get_user_nickname() or "friend"
        await event.reply(i18n.t("my_module.hello", name=name))

    async def on_unload(self, event):
        pass
```

### 卸載翻譯

```python
# 卸載整個域的翻譯
i18n.unregister_domain("my_module")
```

---

請直接傳回翻譯後的完整 Markdown 內容，不要包含任何其他文字。


## 配置欄位多語言

從 v2.5.2 起，配置 Schema 全面支援 i18n。所有用戶可見的文字欄位均可引用 i18n 鍵，WebUI 和其他消費者會自動根據當前語言解析為對應文字。

### 支援的 i18n 欄位

| 欄位 | 位置 | 說明 |
|------|------|------|
| `description` | field metadata | 欄位描述 |
| `options[].label` | `ui.options` | select 控件選項標籤 |
| `placeholder` | `ui.placeholder` | 輸入框佔位符 |
| `group_labels` | `_schema_meta` | 分組顯示名（Dashboard 區域標題） |

統一採用 `{"i18n": "key", "default": "文本"}` 格式，純字串則原樣透傳（向後相容）。

### 宣告 i18n 欄位

所有用戶可見文字欄位都支援 i18n：

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BaseConfig

@dataclass
class MyAdapterConfig(BaseConfig):
    # description i18n
    token: str = field(
        default="",
        metadata={
            "description": {"i18n": "my_adapter.token", "default": "平台 Token"},
            "required": True,
            "secret": True,
            "ui": {
                "widget": "password",
                "group": "basic",
                "order": 1,
                # placeholder i18n
                "placeholder": {"i18n": "my_adapter.token.ph", "default": "請輸入 Token"},
            },
        },
    )
    # options label i18n
    mode: str = field(
        default="a",
        metadata={
            "description": {"i18n": "my_adapter.mode", "default": "運行模式"},
            "ui": {
                "widget": "select",
                "group": "basic",
                "order": 2,
                "options": [
                    {"label": {"i18n": "my_adapter.mode.a", "default": "模式A"}, "value": "a"},
                    {"label": {"i18n": "my_adapter.mode.b", "default": "模式B"}, "value": "b"},
                ],
            },
        },
    )

    # group_labels i18n（分組顯示名）
    _schema_meta = {
        "group_labels": {
            "basic": {"i18n": "my_adapter.group.basic", "default": "基本設定"},
        }
    }
```

`default` 是兜底文本——當翻譯未註冊或查找失敗時顯示。

### secret 脫敏與配置校驗

標記為 `"secret": True` 的欄位會自動獲得**脫敏保護**（2.7.0 起）：

- **範本生成脫敏**：`dataclass_to_toml_with_comments()` 生成配置範本時，secret 欄位的真實值不會寫入檔案（顯示為空佔位），避免敏感資訊落盤
- **通用脫敏工具**：`redact_secret(value)` 將非空值替換為 `***`，空值原樣返回，可用於日誌輸出等場景

```python
from ErisPulse.Core.Bases.config_schema import redact_secret

redact_secret("sk-xxxxxx")  # '***'
redact_secret("")           # ''
```

**配置校驗**（`validate_config()`）除 `required` 非空檢查外，2.7.0 起支援：

| 校驗項 | 元數據 | 示例 |
|--------|--------|------|
| 類型匹配 | 欄位宣告類型 | `int` 欄位傳入字串報錯 |
| 列舉約束 | `ui.options` 或頂層 `options` | 值必須屬於允許選項 |
| 數值範圍 | 頂層 `min` / `max` | `metadata={"min": 1, "max": 65535}` |

```python
from ErisPulse.Core.Bases.config_schema import validate_config

@dataclass
class C(BaseConfig):
    mode: str = field(default="a", metadata={"ui": {"widget": "select", "options": ["a", "b"]}})
    port: int = field(default=80, metadata={"min": 1, "max": 65535})

errors = validate_config(C(mode="x", port=70000))  # 兩條錯誤：列舉 + 範圍
```

### 註冊配置翻譯

配置欄位的 i18n 鍵和普通翻譯鍵一樣，使用 `i18n.register()` 註冊：

```python
from ErisPulse import i18n

# 註冊中文（與 default 一致，也可以不同）
i18n.register("zh-CN", {
    "my_adapter.token": "平台 Token",
}, domain="my_adapter")

# 註冊英文
i18n.register("en", {
    "my_adapter.token": "Platform Token",
}, domain="my_adapter")
```
> **推薦寫法**：使用 `I18nClass` 宣告翻譯鍵，框架會自動註冊（詳見上文「推薦寫法」章節），
> 無需手動呼叫 `i18n.register()` 或 `register_config_i18n()`。

也提供了便捷函數 `register_config_i18n()`，可自動從配置類提取鍵並註冊：

```python
from ErisPulse.Core.Bases.config_schema import register_config_i18n

# 自動提取 description.default 作為 zh-CN 翻譯
register_config_i18n(MyAdapterConfig, "zh-CN")

# 手動提供英文翻譯
register_config_i18n(MyAdapterConfig, "en", {
    "my_adapter.token": "Platform Token",
})
```

### WebUI 如何消費

`get_config_schema()` 返回的 schema 中，i18n 字典會原樣透傳。WebUI 前端可以根據當前語言呼叫 `i18n.t()` 解析。

如果需要服務端直接解析為字串（如返回給不支援 i18n 的前端），使用 `resolve_config_schema()`，它會將 `description`、`options[].label`、`placeholder`、`group_labels` 全部解析為當前語言的文字：

```python
from ErisPulse.Core.Bases.config_schema import resolve_config_schema

# 所有 i18n 欄位已解析為當前語言的字串
schema = resolve_config_schema(MyAdapterConfig)
print(schema["fields"]["token"]["description"])    # "平台 Token" 或 "Platform Token"
print(schema["fields"]["token"]["placeholder"])   # "請輸入 Token" 或 "Enter Token"
print(schema["fields"]["mode"]["options"][0]["label"])  # "模式A" 或 "Mode A"
print(schema["group_labels"]["basic"])             # "基本設定" 或 "Basic"
```

> `BaseConfig`、`BotAccountConfig`、`register_config_i18n()`、`resolve_config_schema()`
> 等類型與工具函數的實際定義位於 `ErisPulse.Core.Bases.config_schema`。
> `ErisPulse.runtime.config_schema` 保留為相容性 shim，
> **推薦從 `ErisPulse.Core.Bases` 統一匯入**（i18n 翻譯鍵相關類型除外，
> 它們位於 `ErisPulse.Core.Bases.i18n_schema`）。


## API 參考

### I18nManager

#### 核心方法

| 方法 | 說明 |
|------|------|
| `t(key, default=None, **kwargs)` | 取得翻譯文字（`gettext()` 是別名） |
| `set_language(lang)` | 手動設定語言 |
| `get_language()` | 取得目前語言 |
| `reset_language()` | 重設為自動偵測（並重新偵測環境） |
| `get_supported_languages()` | 取得所有支援的語言列表 |
| `has_translation(key, lang=None)` | 檢查翻譯鍵是否存在 |
| `register(lang, translations, domain)` | 註冊自訂翻譯 |
| `unregister_domain(domain)` | 解除安裝指定網域的所有翻譯 |
| `reload()` | 重新載入內建翻譯並重新偵測語言 |

#### `t()` 方法詳解

```python
def t(self, key, /, default=None, **kwargs):
```

- `key` — 翻譯鍵（僅位置參數，不與 `**kwargs` 中的 `key=` 衝突）
- `default` — 翻譯不存在時返回的預設值，預設為 `None`（返回鍵名本身）
- `**kwargs` — 格式化參數，用於填入翻譯值中的 `{placeholder}`

範例：

```python
# 翻譯定義: "greeting": "你好，{name}！歡迎來到{place}。"
i18n.t("greeting", name="Alice", place="ErisPulse")
# 返回: "你好，Alice！歡迎來到ErisPulse。"
```

### BaseI18n / I18nKey（宣告式翻譯鍵）

從 v2.7.0 起，`ErisPulse.Core.Bases` 提供了基於類別屬性的翻譯鍵宣告工具（推薦從 `ErisPulse.Core.Bases` 統一匯入）：

> ``I18nKey.default`` 是**語言無關的兜底文字**，不會註冊到任何語言。
> 要讓翻譯生效，必須顯式傳入至少一個語言參數（``zh_CN=`` / ``en=`` / ``ja=`` 等）。
> 這樣各國開發者可以自由使用自己母語填寫 ``default``，框架不做任何假設。

| 名稱 | 說明 |
|------|------|
| `I18nKey(default, *, key=None, zh_CN, zh_TW, en, ja, ru)` | 單個翻譯鍵宣告，`default` 為語言無關的兜底 |
| `BaseI18n` | 翻譯鍵集合基底類別（命名對齊 `BaseConfig`），子類別以類別屬性宣告多個 `I18nKey` |
| `BaseI18n.register(prefix="", domain="app")` | 類別方法：將所有宣告的鍵註冊到 i18n系統 |
| `key` | `I18nKey` 的別名（書寫更簡潔） |

使用範例：

```python
from ErisPulse.Core.Bases import BaseI18n, key

class MyKeys(BaseI18n):
    # 簡潔別名寫法
    hello = key(
        default="Hello",
        zh_CN="你好",
        zh_TW="你好",
        en="Hello",
        ja="こんにちは",
        ru="Привет",
    )
    bye = key(
        default="Bye",
        zh_CN="再見",
        zh_TW="再見",
        en="Bye",
        ja="さようなら",
        ru="До свидания",
    )

# 獨立使用（手動註冊）
MyKeys.register(prefix="myapp.", domain="myapp")
```

### 從 SDK 實例存取

```python
from ErisPulse import sdk

# sdk.i18n 與直接匯入的 i18n 是同一個物件
sdk.i18n.set_language("en")
print(sdk.i18n.t("core.sdk.init.starting"))
```

---

## 執行階段設定

### 使用設定 API 讀取 i18n 設定

```python
from ErisPulse.Core.Bases import I18nConfig
from ErisPulse.runtime import get_i18n_config

config = get_i18n_config()
print(config["language"])  # "auto" 或具體語言代碼

# I18nConfig 是 dataclass，可用於生成設定範本
schema = I18nConfig.__dataclass_fields__
```

### 設定項目說明

在 `config/config.toml` 的 `[ErisPulse.i18n]` 部分：

```toml
[ErisPulse.i18n]
# 顯示語言，可選值:
# - "auto"      — 自動偵測系統語言（預設）
# - "zh-CN"     — 簡體中文
# - "zh-TW"     — 繁體中文
# - "en"        — 英文
# - "ja"        — 日文
# - "ru"        — 俄文
language = "auto"
```

---

## 最佳實踐

### 翻譯鍵命名

建議使用點號分隔的命名空間格式：

```
<模組名>.<類別>.<描述>
```

例如：`my_module.command.hello_desc`、`core.adapter.start_failed`

### 多語言覆蓋

不必一次提供所有語言的翻譯，缺失的語言會自動回退到英文，如果英文也沒有則顯示鍵名本身。

### 動態內容

對於動態生成的內容（如使用者名稱、數量等），使用 `{placeholder}` 格式化：

```python
# 翻譯定義
"user_count": "目前線上使用者：{count} 人"

# 使用
i18n.t("user_count", count=len(users))
```

### 日誌訊息

如果您的模組使用了框架的 Logger，這些訊息也會自動使用目前語言：

```python
self.logger.info(i18n.t("my_module.startup"))
```

---

## 與 CLI i18n 的關係

CLI 擁有**獨立**的國際化模組（`ErisPulse.CLI.i18n`），與框架核心的國際化模組完全解耦。

- **Core i18n** — 框架核心模組使用，外部模組可註冊翻譯
- **CLI i18n** — 命令行介面內部使用，不與 Core 共享翻譯資料

這種設計確保 CLI 的翻譯變更不會影響框架核心的穩定性。



### 统一控制面（scope）

# 統一控制面（scope）

> [!NOTE]  
> 本特性需要 ErisPulse **2.8.0+**。

統一控制面回答六個問題：**哪些模組可用、誰的事件收不收、誰能執行某條命令、  
某模組處理什麼文字、覆蓋哪些實現參數、禁止模組發起哪些出站呼叫**。  
控制權完全交給使用者：在模組 / 適配器 / 命令 / 處理器註冊的**上層**（配置  
`ErisPulse.scope` 或執行時 `sdk.scope`）統一聲明，事件管線在每一級自動讀取並執行。

控制面收斂了原有的多套權限系統，是 2.8.0 權限/訪問控制的**唯一**入口：

| 維度 | 控制什麼 | 拒絕行為 | 配置路徑 |
|------|---------|---------|---------|
| **① 模組** | 哪些模組可用（平台 / Bot / 會話三級） | 靜默忽略（不回覆、不認領） | `scope.platforms / bots / sessions` |
| **② 身份** | 事件收不收（適配器 / Bot / 會話 / 使用者四級） | 入口完全丟棄（靜默） | `scope.identity.*` |
| **③ 命令** | 誰能執行某條命令（命令名支援 glob） | 回覆「權限不足」（顯式） | `scope.commands` |
| **④ 處理器** | 某模組的事件處理器按文字過濾 | 不觸發（靜默） | `scope.handlers` |
| **⑤ 覆蓋** | 覆蓋模組/命令的實現參數（master/hidden/aliases/prefix） | ——（只改參數） | `scope.overrides` |
| **⑥ 出站動作** | 禁止模組發送訊息 / 調用標準 API / 處理請求 | 失敗回應（`retcode=34601`） | `scope.actions` |

{!--< tips >!--}
1. 透過 `from ErisPulse.Core import scope` 導入單例（`sdk.scope` 同物件）
2. `scope.is_allowed(platform, bot_id, module, session_id)` 判斷模組是否可用
3. `scope.is_identity_allowed(platform, bot_id, session_id, user_id)` 判斷事件是否放行
4. `scope.allow_user("roll*", platform, uid)` / `deny_user(...)` 命令 ACL（支援 glob）
5. `scope.override("MyModule", "restart", master=True)` 覆蓋實現參數
6. `scope.set_action("MyModule", "send", False)` 禁止模組回覆/發訊息
7. `scope.get_stats()` 查看過濾統計；`scope.get_topology()` 查看拓撲
{!--< /tips >!--}

## 匹配條目語法（全系統統一）

控制面所有「名字列表」（模組名、身份鍵、命令名）共用同一套匹配語法
（`ErisPulse.Core.text_match`）：

| 語法 | 範例 | 說明 |
|------|------|------|
| 精確名 | `"Chat"` | 全值比較，**大小寫不敏感** |
| glob | `"Tool*"`、`"spam_*"` | `*` 任意串 / `?` 單字符 / `[seq]` 字元集，大小寫不敏感 |
| 正則 | `"re:^Danger.*"` | 以 `re:` 前綴宣告，正則 `search` 匹配，預設大小寫不敏感 |

- 非法正則**靜默降級**為「不匹配」（不拋錯、不崩潰）
- 裝飾器參數（`pattern=` / `regex=`）為固定語義：`pattern` 是 glob、`regex` 是正則源碼
  （不加 `re:` 前綴）；控制面配置裡的正則條目**必須**帶 `re:` 前綴

## 全局兜底：`default_allow`

`default_allow` 是**全域唯一**的兜底開關（預設為 `true`），  
對三個判定維度統一生效：

- **模組維度**：未命中任何綁定 → 由 `default_allow` 決定放行 / 拒絕  
- **身份維度**：未命中任何策略 → 由 `default_allow` 決定放行 / 拒絕  
- **命令維度**：未配置 ACL → 若 `default_allow=true` 則交由開發者預設權限鏈；  
  若為 `false`（嚴格模式）則命令未配置 ACL 即拒絕  

設為 `false` 即開啟「隱式拒絕」嚴格模式：採用白名單式管理，  
**未明確允許者一律拒絕**。

> **例外**：⑥ 出站動作維度**不受** `default_allow` 影響——它是獨立的收緊開關，  
> 預設全允許，僅明確設為 `false` 才會禁止（框架層 owner 為空的呼叫恆定放行）。  
> 這樣嚴格的全域模式不會意外中斷所有模組的消息回覆。

## 配置文件

```toml
[ErisPulse.scope]
default_allow = true        # 全局兜底（false = 隱式拒絕嚴格模式）
cache_size = 1024           # LRU 緩存大小

# ── ① 模組維度（優先級：會話 > Bot > 平台）──
[ErisPulse.scope.platforms.onebot11]
modules = ["Chat", "Tool*"]   # 白名單：精確名 / glob / re: 正則
blocked = ["re:^Danger"]
[ErisPulse.scope.bots.onebot11."123456"]
modules = ["Chat"]
[ErisPulse.scope.sessions.onebot11."789012345"]
modules = ["Chat"]

# ── ② 身份維度（優先級：用戶 > 會話 > Bot > 適配器）──
[ErisPulse.scope.identity.adapters.onebot11]
deny = true                   # 整個適配器的事件全部丟棄
[ErisPulse.scope.identity.bots.onebot11."123456"]
deny = true
[ErisPulse.scope.identity.sessions.onebot11."g_blocked"]
deny = true
[ErisPulse.scope.identity.users.onebot11]
allow = ["u_admin"]           # 用戶鍵支援 glob / re: 正則
deny = ["u_bad", "spam_*"]

# ── ③ 命令維度（命令名支援 glob）──
[ErisPulse.scope.commands."roll*"]
allow = ["onebot11:u_vip"]    # 用戶標識 "platform:user_id"
deny = ["onebot11:u_bad"]

# ── ④ 處理器/文本維度 ──
[ErisPulse.scope.handlers.MyModule]
pattern = "簽到*"             # 與程式碼內 pattern/regex 條件 AND
regex = "re:\\d+\\s*元"

# ── ⑤ 實現參數覆蓋 ──
[ErisPulse.scope.overrides.MyModule.restart]
master = true                 # 僅框架主人可用
hidden = true                 # 幫助中隱藏
aliases = ["rs"]              # 追加別名
prefix = "!"                  # 追加觸發前綴

# ── ⑥ 出站動作維度（預設全允許，顯式禁用才收緊）──
[ErisPulse.scope.actions.MyModule]
send = false                  # 禁止 MyModule 回覆/主動發訊息
api = false                   # 禁止 MyModule 調標準 API（含 call 逃生艙）
request = false               # 禁止 MyModule 處理請求操作 accept/reject
```

## ① 模組維度

回答「在某個上下文裡，哪些模組可用」。預設全部開放；配置綁定後才開始過濾，**模組與適配器無需任何變動**。

```mermaid
flowchart TD
    A["事件到達某模組的處理器/命令"] --> B{"scope.is_allowed<br/>(platform, bot, module, session)"}
    B --> C{"查找生效綁定<br/>會話級 > Bot 級 > 平台級"}
    C -->|"命中"| D["blocked 命中 → 拒絕<br/>modules 非空 → 僅白名單放行<br/>都空 → default_allow"]
    C -->|"未命中"| E["default_allow（預設 true = 放行）"]
    D -->|"拒絕"| Z["靜默忽略<br/>（不回覆、不認領，僅 TRACE 日誌）"]
```

- **解析優先級：會話級 > Bot 級 > 平台級**，高優先級綁定**整體覆蓋**低優先級
- **靜默語義**：被過濾模組的命令與處理器不觸發、不回覆、不認領（防止跨命令誤匹配），僅 TRACE 級日誌可見（`core.scope.denied`）
- **框架級處理器**（`scope_exempt=True` 或 owner 為空）不受影響；模組名為空（框架層資源）始終放行
- **會話感知幫助與命令查詢**：命令查詢 API（`command.help` / `get_command` / `get_commands` / `get_group_commands` / `get_visible_commands`，以及 `module.get_commands_overview`）均支援可選 `event=` 或顯式 `platform=` / `bot_id=` / `session_id=` 關鍵字——當前會話不可用模組的命令不再出現在結果中（`get_command` 返回 None、單命令幫助按「未註冊」處理，與靜默語義一致）；不傳上下文則保持全量行為。命令查詢返回的 help / hidden 等欄位為合併覆蓋後的生效值（使用者優先）

## ② 身份維度（事件准入）

回答「誰的事件收不收」。被拒絕的事件在**分發入口完全丟棄**——  
不進入中間件與任何處理器（含框架級），僅 TRACE 級日誌可見（`core.scope.identity_denied`）。

- **解析優先級：用戶 > 會話 > Bot > 適配器**，取最具體的已配置策略；deny 优先於 allow
- 每級綁定是二元策略：`{ allow = true }` 或 `{ deny = true }`
- 用戶鍵支援 glob / 正則（如 `"spam_*"` 拉黑一批垃圾用戶）
- 典型用法——上級 deny、個人 allow 做「例外放行」：

```toml
[ErisPulse.scope.identity.adapters.onebot11]
deny = true
[ErisPulse.scope.identity.users.onebot11]
allow = ["u_admin"]   # 即使適配器級拒絕，u_admin 的事件仍然放行
```

## ③ 命令維度（命令 ACL）

回答「誰能執行某條命令」。判定順序：**deny 命中 → 拒絕；allow 白名單非空且未命中 → 拒絕；均未配置 → 遵循 `default_allow`**（`true` 交給開發者預設權限鏈）。  
被拒絕的命令會顯式回覆「權限不足」。

- 命令名支援 glob：`"roll*"` 一條規則覆蓋 `roll`、`roll_dice` 等一組命令
- 精確鍵優先於 glob 鍵（`commands.roll` 命中時不再查 `commands."roll*"`）
- 使用者標識格式 `"platform:user_id"`（與框架主人系統一致）
- 該維度**只是使用者端的額外閘門**，與命令的 `master` / `permission` 參數串聯：  
  ACL 通過後仍走開發者聲明的預設權限鏈（該預設鏈可用 ⑤ 覆蓋調整）

## ④ 處理器/文字維度

依模組過濾「處理什麼文字」：為某模組設定 `pattern` / `regex` 後，  
該模組的所有事件處理器僅在文字命中時觸發（與程式碼內條件 AND，需同時滿足）。  
適合在不修改模組程式碼的情況下縮小其觸發範圍。

```toml
[ErisPulse.scope.handlers.ChatModule]
pattern = "閒聊*"     # ChatModule 的處理器僅回應以「閒聊」開頭的消息
```

## ⑤ 實現參數覆蓋

在模組/命令註冊的**上層**覆蓋實現參數，不修改模組代碼：

```toml
[ErisPulse.scope.overrides.MyModule.restart]
master = true      # 覆蓋為僅框架主人（也可設 false 放開開發者的主人限制）
hidden = true      # 幫助列表中隱藏
aliases = ["rs"]   # 生效別名
```

> 覆蓋遵循**使用者優先**：開發者宣告的 `master` / `hidden` 等只是預設值，
> 使用者在此顯式配置後即以使用者配置為準（可收緊也可放開）。
> 覆蓋只改**實現參數**（master / hidden / aliases / prefix / help / usage 等），
> 命令執行判定與幫助渲染共用同一合併結果：`hidden` 覆蓋即時改變幫助列表可見性，
> `help` / `usage` 覆蓋即時改變 `/help` 展示。
> **禁用一條命令不在這裡**——統一走命令維度 deny（`scope.commands` 或
> `scope.deny_user()`），避免兩套"禁用"語義打架。

## ⑥ 出站動作維度（禁止模組發起出站呼叫）

限制模組**發起的出站動作**：訊息發送 / 標準 API 動作 / 請求操作。  
三類動作對應底層 DSL：`Event.reply` 與 `Send`（send）、`Api` / `call_api`（api）、  
`Request` 的 accept/reject（request）。模組在事件 handler 執行期間發起的出站呼叫  
攜帶模組 owner，由本維度統一判定。

```toml
[ErisPulse.scope.actions.MyModule]
send = false      # 禁止 MyModule 回覆/主動發訊息
api = false       # 禁止 MyModule 調用標準 API 動作（含 call 逃生艙）
request = false   # 禁止 MyModule 對請求事件執行 accept/reject
```

判定語義：**預設全允許**——未配置、或 owner 為空（框架層內部呼叫）均放行；  
僅當使用者顯式設為 `false` 才拒絕，被拒呼叫不發起任何網路請求，直接返回  
標準失敗回應（`retcode = 34601`，見 [api-response §5.3](../standards/api-response.md#53-框架擴展返回碼34xxx-平台錯誤段的低三位自定義)）。三個動作互相獨立，可只禁其一。

```python
# 運行時 API
sdk.scope.set_action("MyModule", "send", False)   # 禁發訊息
sdk.scope.is_action_allowed("MyModule", "send")   # False
sdk.scope.unset_action("MyModule", "send")        # 恢復允許
sdk.scope.get_action_rules("MyModule")            # {"send": False, "api": True, "request": True}
```

## 運行時 API

### 模組維度

```python
from ErisPulse import sdk

# 判斷
sdk.scope.is_allowed("onebot11", "123456", "Chat")
sdk.scope.is_allowed("onebot11", "123456", "Chat", "789012345")
sdk.scope.is_allowed("onebot11", "123456", None)      # 框架層資源 -> True

# 綁定 / 解綁
sdk.scope.bind_module("onebot11", "123456", modules=["Chat", "Tool*"])
sdk.scope.bind_module("onebot11", blocked=["Danger"])             # 平台級
sdk.scope.bind_module("onebot11", "123456", "789012345", modules=["Chat"])  # 會話級
sdk.scope.bind_module("onebot11", "123456", modules=["Music"], merge=True)  # 合併
sdk.scope.bind_module("onebot11", "123456", modules=["Chat"], persist=False)  # 僅運行時
sdk.scope.unbind_module("onebot11", "123456")

# 查詢
sdk.scope.get("onebot11", "123456")   # {"modules": ["Chat"], "blocked": []}
```

### 身份維度

```python
# 判斷事件是否放行
sdk.scope.is_identity_allowed("onebot11", "123456", "group_9", "u1")

# 綁定策略（層級由參數決定：user > session > bot > adapter）
sdk.scope.bind_identity("onebot11", user_id="u_bad", deny=True)
sdk.scope.bind_identity("onebot11", user_id="spam_*", deny=True)   # glob
sdk.scope.bind_identity("onebot11", "123456", "group_9", allow=True)
sdk.scope.unbind_identity("onebot11", user_id="u_bad")

# 用戶黑名單便捷 API
sdk.scope.block_user("onebot11", "u_bad")
sdk.scope.is_user_blocked("onebot11", "u_bad")
sdk.scope.get_blocked_users()        # {"onebot11": ["u_bad"]}
sdk.scope.unblock_user("onebot11", "u_bad")
```

### 命令維度

```python
sdk.scope.is_command_allowed("roll", "onebot11", "u1")
sdk.scope.allow_user("roll*", "onebot11", "u_vip")   # 命令名支援 glob
sdk.scope.deny_user("roll*", "onebot11", "u_bad")
sdk.scope.get_acl("roll*")
sdk.scope.remove_acl("roll*")

# 也可透過命令系統門面（等價委託）
from ErisPulse.Core.Event import command
command.allow_user("restart", "onebot11", "123456")
```

### 處理器與覆蓋維度

```python
sdk.scope.bind_handler("MyModule", pattern="簽到*", regex=r"\d+號")
sdk.scope.unbind_handler("MyModule")

sdk.scope.override("MyModule", "restart", master=True, hidden=True)
sdk.scope.get_override("MyModule", "restart")
sdk.scope.remove_override("MyModule", "restart")
```

### 通用

```python
sdk.scope.list_bindings()   # 全量綁定
sdk.scope.get_topology()    # 拓撲（供 Dashboard）
sdk.scope.get_stats()
# {"module_calls": .., "module_filtered": .., "identity_checks": .., "identity_denied": ..,
#  "command_checks": .., "command_denied": .., "action_checks": .., "action_denied": ..,
#  "cache_hits": .., "cache_misses": ..}
sdk.scope.reset_stats()
sdk.scope.clear()           # 清空全部綁定（僅記憶體生效）
```

## 主人身份與自定義身份來源（provider）

主人系統回答「誰是框架主人」：命令的 `master=True` 參數與業務層的
`master.is_master()` 共用同一套身份判定，判定鏈為
**配置主人 → 運行時記錄 → provider 鏈**。

主人配置（`ErisPulse.master.users`，支援全域 list 與按平台 dict）見
[配置文件](../user-guide/configuration.md#主人系統配置)；本節聚焦身份判定 API 與擴展點。

### 判定與運行時增刪

```python
from ErisPulse.Core import master

master.is_master(event)                      # 從事件判定
master.is_master("yunhu", "123")             # 明確判定
master.add("yunhu", "123")                   # 運行時新增（預設持久化；persist=False 僅內存）
master.remove("yunhu", "123")                # 移除（預設持久化）
master.list()                                # 匯總：{"global": [...], "<platform>": [...]}
```

### 自定義身份來源（provider）

除了配置外，還可以註冊自定義身份來源：`fn(platform, user_id) -> bool`，
內建身份來源（配置 + 運行時記錄）未命中時依序嘗試，任一 provider 放行即認定為主人。
適合對接適配器管理員介面、資料庫角色等外部身份體系。

註冊入口 `master.provider` 支援裝飾器 / 函數式兩種寫法，
註銷統一透過被註冊函數上的 `fn.unregister()`：

```python
from ErisPulse.Core import master

# 寫法一：裝飾器（常駐身份來源，推薦）
@master.provider
def admin_provider(platform, user_id):
    return user_id in {"999"}     # 自訂判定邏輯

master.is_master("yunhu", "999")   # True
admin_provider.unregister()        # 不再需要時註銷

# 寫法二：函數式（模組載入期註冊 / 卸載期註銷）
fn = master.provider(admin_provider)
fn.unregister()
```

> provider 異常會被捕捉並跳過，不阻斷身份判定鏈。
> 綁定執行個體方法無法掛載 `unregister`，需要註冊/註銷配對的場景請使用**模組級函數**。

### 用戶優先：主人生效範圍由用戶最終決定

命令的 `master=True` 只是**開發者預設**：用戶可在控制面
`ErisPulse.scope.overrides.<module>.<cmd>.master = true/false`
覆蓋收緊或放寬（見上文 ⑤ 實現參數覆蓋，用戶顯式設定即生效）。

## 緩存與熱更新

- `is_allowed` / `is_identity_allowed` 的結果帶有 **LRU 緩存**（`scope.cache_size` 可調），  
  `bind_*` / `unbind_*` / 配置熱更新（`config.updated` / `config.set`）會自動失效
- 所有維度的配置修改**立即生效**，無需重啟
- 控制面是「逐事件」判斷，不跨事件記憶：配置變了，下一個事件即按新規則

## 常見問題與注意事項

### 1. 配置層級與覆蓋

- 模塊維度：會話級 > Bot 級 > 平台級，**整體覆蓋**。想「平台允許 Chat，Bot 再加 Music」，
  必須在 Bot 級同時列出兩者
- 身份維度：使用者 > 會話 > Bot > 適配器，取**最具體**的已配置策略（可做例外放行）
- 命令維度：精確命令名優先於 glob 鍵

### 2. 優先使用控制面而不是修改模組代碼

模組聲明的是「開發者預設」（`master=True`、`permission=...`、`pattern=...`）；
控制面聲明的是「使用者最終決定」。實現參數覆蓋遵循**使用者優先**：
使用者顯式配置的 `master = true/false` 直接生效（可收緊可放寬）。
開發者未設的限制使用者可自行收緊；禁用/放行類控制走命令 deny / 身份 allow。

### 3. 模組/命令沒有反應

先懷疑控制面而不是模組本身：

```python
from ErisPulse import sdk

print(sdk.scope.is_allowed(event.get_platform(), bot_id, "MyModule", session_id))
print(sdk.scope.is_identity_allowed(event.get_platform(), bot_id, session_id, user_id))
print(sdk.scope.get_stats())   # module_filtered / identity_denied > 0 代表被靜默過濾
```

被過濾是**靜默**的（模組維度與身份維度不回應，避免暴露規則），但統計會累計；
命令維度被 ACL 拒絕會顯式回應「權限不足」。

### 4. 會話標識跨平台隔離

`(platform, session_id)` 組合才是唯一標識。`scope.sessions.onebot11."789"`
只作用於 onebot11，不影響 telegram 上同為 `789` 的會話。身份維度的使用者鍵同理。

## 拓撲樹 API

`ModuleManager.get_topology()` 與 `AdapterManager.get_topology()` 提供模組/適配器歸屬關係資料，  
`sdk.get_topology()` 一鍵聚合（含控制面 `scope` 五維）：

```python
from ErisPulse import sdk

topology = sdk.get_topology()
# {
#   "modules": {                                   # 模組 → 擁有的資源
#     "Chat": {
#       "loaded": True, "enabled": True,
#       "commands": ["chat", "translate"],
#       "handlers": {"message": 2, "notice": 1},
#       "routes": {"http": ["/Chat/api"], "ws": [], "sse": []},
#       "lifecycle_hooks": 3,
#     }
#   },
#   "adapters": {                                  # 適配器 → Bot → 作用域
#     "onebot11": {
#       "status": "started", "enabled": True,
#       "bots": {"123456": {"status": "online", "scope": {...}}},
#       "scope": {"modules": [...], "blocked": [...]},
#     }
#   },
#   "scope": {                                     # 統一控制面（五維）
#     "platforms": {...}, "bots": {...}, "sessions": {...},
#     "identity": {"adapters": {...}, "bots": {...}, "sessions": {...}, "users": {...}},
#     "commands": {...}, "handlers": {...}, "overrides": {...},
#   },
# }
```

- 模組拓撲聚合了該模組註冊的命令、事件處理器、HTTP/WS/SSE 路由與生命週期鉤子，便於繪製模組資源樹。  
- 適配器拓撲聚合了各適配器狀態、下屬 Bot 狀態及平台級/Bot 級作用域綁定。



### 启动流程与手动控制

# 啟動流程與手動控制

ErisPulse 的 `await sdk.run()` / `await sdk.init()` 把一整條啟動鏈路封裝成了「一行程式碼」。但當你需要完全自訂啟動流程（例如部分載入、動態註冊、熱插拔、注入自訂載入策略）時，就需要了解這條鏈路內部到底發生了什麼、以及如何手動驅動每一步。

本文把啟動鏈路拆解成獨立的環節，說明各自的職責、呼叫順序，並給出手動完整啟動的範例。

> 本文假設你已經跑過 [第一個機器人](../getting-started/first-bot.md)，了解 `sdk.run(keep_running=True/False)` 兩種模式。本文聚焦於 `init()` **內部**的鏈路拆解，以及 `init()`/`init_task()`/`init_sync()` 等更底層的入口。

## SDK 頂層入口一覽

除了 `run()` 的兩種 `keep_running` 模式，SDK 還提供幾個更底層的初始化入口，區別在於**異步性、回傳值、以及是否包裝例外**：

| 入口 | 異步性 | 回傳值 | 例外處理 | 適用場景 |
|------|--------|--------|----------|----------|
| `await sdk.run(True)` | async，阻塞維持 | `None`（關閉時自動 `uninit`） | 模組/適配器錯誤被攔截，不拖垮程序 | 純 bot 應用 |
| `await sdk.run(False)` | async，不阻塞 | `None`（不自動卸載） | 同上 | 初始化後執行自訂邏輯 |
| `await sdk.init()` | async，需 await | `bool` | 內部捕獲元件例外，失敗回傳 `False` | 手動控制生命週期（配 `uninit()`） |
| `sdk.init_task()` | async，回傳 Task 不阻塞 | `asyncio.Task` | 同 `init()` | 並發執行別的初始化、或事件迴圈尚未運行 |
| `sdk.init_sync()` | **同步**，阻塞目前執行緒 | `bool` | 同 `init()` | 命令列腳本、無事件迴圈的同步入口 |

> **常見誤區**：`await sdk.init()` **不等於** `await sdk.run(keep_running=False)`。兩點不同：① `init()` 回傳 `bool`（失敗時回傳 `False`），`run()` 回傳 `None`；② `init()` 只做初始化、**不自動卸載**，`run()` 在事件迴圈結束時自動 `uninit()`。因此需要手動配對卸載或自訂生命週期時，用 `init()` + `uninit()`。

## 啟動鏈路總覽

`sdk.init()`（確實是其內部的 `Initializer.init()`）按以下順序拉起整個框架：

```mermaid
flowchart TD
    A[0. 準備環境<br/>配置載入 / 例外處理] --> B
    B[1. 並行發現與載入<br/>AdapterLoader.load / ModuleLoader.load<br/>內部呼叫 Finder.find_all] --> C
    C[2. 註冊適配器<br/>AdapterLoader.register_to_manager] --> D
    D[3. 啟動適配器<br/>adapter.startup] --> E
    E[4. 註冊模組<br/>ModuleLoader.register_to_manager] --> F
    F[5. 初始化模組<br/>ModuleLoader.initialize_modules<br/>實例化並掛載到 sdk] --> G
    G[6. 啟動路由伺服器<br/>router.start]
```

對應的核心元件：

| 層 | 元件 | 職責 |
|----|------|------|
| 發現 | `AdapterFinder` / `ModuleFinder` | 從已安裝套件的 entry-points 中**發現**適配器/模組 |
| 載入 | `AdapterLoader` / `ModuleLoader` | 發現 + 導入 + 讀取元資料 + 判斷啟用/禁用，回傳物件清單 |
| 註冊 | `*Loader.register_to_manager` | 把物件登記到對應管理器 |
| 管理 | `sdk.adapter` / `sdk.module` | 維護適配器/模組實例，提供啟停介面 |
| 初始化 | `ModuleLoader.initialize_modules` | 建立模組實例並掛載到 `sdk`（處理相依性拓撲排序） |
| 路由 | `sdk.router` | HTTP / WebSocket 伺服器 |

> **重要**：`Finder` 和 `Loader` 是兩層。`Loader` 內部**已經持有**一個 `Finder`（`AdapterLoader` 自帶 `AdapterFinder`，`ModuleLoader` 自帶 `ModuleFinder`）。大多數場景你只需要用 `Loader`，只有需要「只列出不導入」時才會單獨用 `Finder`。

## 各環節詳解

### 1. 發現層：Finder

Finder 只負責「找到有哪些套件提供了適配器/模組」，不導入、不實例化。

```python
from ErisPulse.finders import AdapterFinder, ModuleFinder

adapter_finder = AdapterFinder()
module_finder = ModuleFinder()

# 查找所有已安裝的適配器/模組 entry-points
adapter_entries = adapter_finder.find_all()    # list[EntryPoint]
module_entries = module_finder.find_all()      # list[EntryPoint]

# 按名稱查找單個
entry = module_finder.find_by_name("MyModule")  # EntryPoint | None
```

每個 `EntryPoint` 可以 `.load()` 得到對應的類，但通常不用你手動調——Loader 會做。

### 2. 載入層：Loader

Loader 在 Finder 之上做了「導入 + 讀元資料 + 判斷啟用/禁用」。

```python
from ErisPulse.loaders import AdapterLoader, ModuleLoader
from ErisPulse import sdk

adapter_loader = AdapterLoader()
module_loader = ModuleLoader()

# load() 內部：呼叫 finder.find_all() → 逐個處理 entry-point → 回傳三元組
adapter_objs, enabled_adapters, disabled_adapters = await adapter_loader.load(sdk.adapter)
module_objs, enabled_modules, disabled_modules = await module_loader.load(sdk.module)
```

`load()` 回傳的三元組：

| 回傳值 | 含義 |
|--------|------|
| `objs` (`dict`) | 名稱 → 對象（適配器類 / 模組包裝物件） |
| `enabled` (`list[str]`) | 被啟用的名稱（設定中未禁用） |
| `disabled` (`list[str]`) | 被禁用的名稱 |

#### 載入失敗時的診斷資訊

當某個模組/適配器在載入或初始化階段拋出例外時，框架會跳過該元件並繼續載入其他元件，同時輸出**使用者程式碼幀摘要**，讓你在預設 INFO 級別下即可定位出錯位置，無需手動重開 DEBUG：

```
[ERROR] [ModuleLoader] 從 entry-point 載入模組 MyModule 失敗，已跳過: 'NoneType' object has no attribute 'platform'
  → MyModule/Core.py:42 in on_load
      adapter = sdk.platform
  → AttributeError: 'NoneType' object has no attribute 'platform'
  → 提示: 將日誌級別提高到 DEBUG 可查看完整堆疊；檢查模組 MyModule 的實作程式碼
```

診斷資訊透過 `ErisPulse.runtime.diagnostics` 模組產生，會自動過濾掉框架內部幀，只保留你的程式碼幀。如需在自訂載入邏輯中重用：

```python
from ErisPulse.runtime import log_diagnostic

try:
    risky_init()
except Exception as e:
    log_diagnostic(e)  # 自動提取使用者程式碼幀並寫入 ERROR 日誌
```

該模組還提供 `extract_user_frame()`（回傳結構化幀資訊）和 `format_diagnostic_block()`（回傳多行文字）兩個底層函數。

### 3. 註冊層：register_to_manager

把 Loader 產出的物件登記到管理器，讓 `sdk.adapter` / `sdk.module` 能識別它們。

```python
# 註冊適配器（回傳 bool，表示是否全部成功）
await adapter_loader.register_to_manager(enabled_adapters, adapter_objs, sdk.adapter)

# 註冊模組
await module_loader.register_to_manager(enabled_modules, module_objs, sdk.module)
```

註冊後，適配器已登記到適配器管理器、模組已登記到模組管理器，但**都還未啟動/實例化**。

### 4. 啟動適配器

```python
# 啟動所有已註冊的適配器
await sdk.adapter.startup()
# 或指定平台
await sdk.adapter.startup("yunhu")
await sdk.adapter.startup(["yunhu", "telegram"])
```

> 註冊 ≠ 啟動。`register_to_manager` 只是登記；`startup` 才會呼叫適配器的 `start()`，建立與平台的連接。

### 5. 初始化模組

模組比適配器多一步——需要**實例化**並掛載到 `sdk` 上（這樣你才能 `sdk.MyModule.xxx` 呼叫）。這一步還處理模組間的相依宣告與拓撲排序。

```python
success = await module_loader.initialize_modules(
    enabled_modules, module_objs, sdk.module, sdk
)
```

實例化成功後，模組會出現在 `sdk.<ModuleName>` 上。

### 6. 啟動路由伺服器

```python
await sdk.router.start(
    host="0.0.0.0",
    port=8000,
    ssl_certfile=None,
    ssl_keyfile=None,
)
```

路由伺服器負責接收適配器的 Webhook / WebSocket 回呼。不啟動它，server 模式的適配器無法收訊息。

## 完整手動啟動範例

下面這段程式碼**等於** `await sdk.init()` 的核心流程，但每一步都暴露在你手裡，可以在任意環節插入自訂邏輯：

```python
import asyncio
from ErisPulse import sdk
from ErisPulse.loaders import AdapterLoader, ModuleLoader

async def manual_startup():
    # 0. 準備環境（載入設定、註冊全域例外處理）
    #    _prepare_environment 是 init() 內部的前置步驟；手動流程也需先呼叫，
    #    否則 Loader 讀不到設定，會把所有適配器/模組誤判為禁用。
    if not await sdk._prepare_environment():
        print("環境準備失敗")
        return False

    # 1. 建立載入器（內部各自持有 Finder）
    adapter_loader = AdapterLoader()
    module_loader = ModuleLoader()

    # 2. 並行發現與載入（與 init() 內部一致用 gather）
    (adapter_objs, enabled_adapters, disabled_adapters), \
    (module_objs, enabled_modules, disabled_modules) = await asyncio.gather(
        adapter_loader.load(sdk.adapter),
        module_loader.load(sdk.module),
    )

    # 3. 註冊適配器
    await adapter_loader.register_to_manager(
        enabled_adapters, adapter_objs, sdk.adapter
    )

    # 4. 啟動適配器
    if enabled_adapters:
        await sdk.adapter.startup()

    # 5. 註冊模組
    await module_loader.register_to_manager(
        enabled_modules, module_objs, sdk.module
    )

    # 6. 初始化模組（實例化 + 掛載到 sdk）
    if enabled_modules:
        await module_loader.initialize_modules(
            enabled_modules, module_objs, sdk.module, sdk
        )

    # 7. 啟動路由伺服器
    await sdk.router.start(host="0.0.0.0", port=8000)

    print("手動啟動完成")
    return True

async def main():
    ok = await manual_startup()
    if ok:
        # 阻塞維持運行（手動流程不會自動阻塞）
        await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
```

### 何時該手動啟動？

大多數情況下**不需要**手動啟動，`await sdk.run()` 已經把上面這些都做好了。手動啟動僅在這些場景才有價值：

- **部分載入**：只載入指定的適配器/模組，跳過其他
- **動態註冊**：執行時根據條件註冊新的適配器/模組
- **自訂順序**：需要打亂預設的載入順序（如先啟動某模組再啟動適配器）
- **注入策略**：對 Loader 注入自訂的嚴格模式管理器、載入策略等
- **除錯/診斷**：在某個環節失敗時，手動驅動以定位問題

## 運行時細粒度控制

即使用了 `sdk.run()` 完成啟動，你仍然可以在執行時單獨控制各子系統，而不必重新啟動整個 SDK：

### 適配器熱啟停

```python
# 熱重啟某個適配器（修復連接，不受其他平台影響）
await sdk.adapter.shutdown("yunhu")
await sdk.adapter.startup("yunhu")

# 執行中拉起一個新平台
await sdk.adapter.startup("telegram")

# 臨時下線某平台
await sdk.adapter.shutdown("telegram")
```

> `adapter.startup()` 要求適配器**已被註冊**到管理器。註冊發生在 `init()`/`run()` 內部，所以這是啟動**之後**的細粒度控制。

### 路由伺服器

```python
# 臨時下線 webhook 伺服器
await sdk.router.stop()

# 重新啟動（例如換了端口）
await sdk.router.start(host="0.0.0.0", port=9000)
```

### 模組按需載入

```python
# 手動載入一個（可能是懶載入的）模組
await sdk.load_module("MyModule")
```

## 優雅關閉

從 2.7.0 起，`sdk.shutdown()` 提供**程序化優雅關閉**：設定關閉事件，讓正在 `await sdk.run(keep_running=True)` 掛起的主迴圈回傳，進而觸發 `uninit()` 完成資源清理。

```python
# 在任意協程中呼叫，觸發優雅退出（run() 掛起回傳並自動 uninit）
sdk.shutdown()
```

典型用途：

```python
async def shutdown_after_idle():
    await asyncio.sleep(3600)
    sdk.shutdown()  # 空閒 1 小時後優雅退出
```

**訊號處理**：`run()` 內部會註冊 `SIGTERM` / `SIGHUP` 處理器，將系統訊號轉為優雅關閉——容器編排（Docker `docker stop`）或 `systemd` 停止服務時，進程會走完 `uninit()` 清理而非被強殺。

- Windows 不支援 `loop.add_signal_handler`，訊號處理器會自動跳過（仍可用 `sdk.shutdown()` 或 Ctrl+C 觸發關閉）
- 反覆呼叫 `sdk.shutdown()` 是安全的（事件已設定後再次呼叫為無操作）

## 卸載流程

啟動的反向操作是 `await sdk.uninit()`，它按相反順序清理：

1. 關閉所有適配器（`adapter.shutdown()`）
2. 卸載所有模組
3. 清理所有事件處理器
4. 清理管理器與 SDK 上的模組屬性

手動啟動場景下，記得在退出前呼叫 `uninit()` 保證優雅關閉：

```python
try:
    await asyncio.Event().wait()   # 維持運行
finally:
    await sdk.uninit()
```

## 重啟

SDK 提供兩種重啟方式，都不需要你自己先卸載——框架會自行處理：

| 方式 | 呼叫 | 行為 | 適用場景 |
|------|------|------|----------|
| 熱重啟 | `await sdk.restart()` | 同一進程內 `uninit()` 後重新 `init()`，重新載入適配器/模組 | 重新載入設定、熱更新模組 |
| 硬重啟 | `await sdk.hard_restart()` | `uninit()` 後以**退出碼 42** 退出進程，由外部監督者拉起全新進程 | 怀疑有記憶體/資源洩漏、需要徹底乾淨重啟 |

```python
# 熱重啟：同進程內重新載入（最常用）
await sdk.restart()

# 硬重啟：退出進程，交由外部監督者重啟（見下方「監督者指南」）
await sdk.hard_restart()
```

> **兩點注意**：
> 1. 這兩個方法都用背景任務執行重啟，**立即回傳 `True` 表示「重啟任務已調度」**，而非「重啟已完成」。實際重啟在背景進行，避免中斷目前事件鏈路。
> 2. `hard_restart()` 的原理是：卸載並刷盤設定後，以**退出碼 42**（`HARD_RESTART_EXIT_CODE`）退出進程——**它自身不拉起新進程**，必須由外部監督者檢測到退出碼 42 後重新啟動。若直接 `python main.py` 運行且無任何監督者，進程以碼 42 退出後就結束了，**不會自動重啟**（框架會打警告提示）。

### 什麼時候該用硬重啟？

硬重啟不只是「更徹底的重啟」，它在以下場景比熱重啟更合適、甚至更高效：

- **二進位函式庫（C 扩展）副作用**：熱重啟在同一進程內進行，無法釋放 C 扩展、打開的檔案描述符、執行緒等進程級資源；硬重啟換一個全新進程，這些副作用隨之徹底清零。
- **資源洩漏排查**：懷疑存在記憶體或句柄洩漏時，硬重啟能拿到一個乾淨的環境。
- **對效能敏感的頻繁重啟**：硬重啟省去了同進程內卸載→重新載入的開銷，實際比熱重啟更高效。

> Dashboard 管理面板裡的「框架重啟」功能，底層呼叫的就是 `hard_restart()`。

### 退出碼 42 契約

硬重啟是跨進程協作：**SDK 負責退出（碼 42），監督者負責拉起**。

| 角色 | 行為 |
|------|------|
| SDK（被硬重啟時） | `uninit()` → 刷盤設定 → `os._exit(42)` |
| 監督者 | 檢測到子進程退出碼為 42 → 重新啟動同一命令 |

> `sdk.is_supervised()` 可查詢目前進程是否由監督者啟動（檢測環境變數 `ERISPULSE_SUPERVISED`）。CLI `run` 命令啟動子進程時會自動注入該標記；systemd / Docker 等外部監督者不會注入，`is_supervised()` 回傳 `False`，此時硬重啟後框架會打「未檢測到監督者」警告。

### 監督者指南

選擇適合你的監督者，讓硬重啟真正生效：

#### 1. CLI run 命令（開發/簡單部署，推薦）

`epsdk run main.py` 內建監督迴圈：檢測子進程退出碼，42 時立即重啟；其它異常退出碼按指數退避自動重試；`Ctrl+C` 會先優雅終止子進程（碼 0 視為正常退出，不再拉起）。

```bash
epsdk run main.py
```

#### 2. systemd（Linux 伺服器）

`RestartForceExitStatus=42` 讓退出碼 42 也觸發重啟（預設 `on-failure` 只對非零碼生效）：

```ini
[Service]
ExecStart=/usr/bin/python3 /opt/mybot/main.py
Restart=on-failure
RestartForceExitStatus=42
RestartSec=2
User=mybot
```

#### 3. Docker / docker-compose

容器內 PID 1 是應用進程，退出碼 42 後容器退出——用 `restart` 策略讓它自動重啟：

```yaml
services:
  bot:
    build: .
    restart: unless-stopped   # 任何退出（含 42）都重啟
```

#### 4. PM2（Node 生態維運）

```bash
pm2 start main.py --name mybot --interpreter python3
# 42 被視為退出碼，PM2 預設重啟；設定 restart_delay 防抖
pm2 set mybot.restart_delay 2000
```

#### 5. supervisord

```ini
[program:mybot]
command=python3 /opt/mybot/main.py
autorestart=true
exitcodes=0,2,42    # 42 也視為"正常退出需重啟"
```

#### 6. 純 Python 自訂監督者

```python
import subprocess, sys, time

while True:
    p = subprocess.Popen([sys.executable, "main.py"])
    code = p.wait()
    if code == 42:          # 硬重啟請求
        time.sleep(0.5)
        continue
    if code == 0:           # 正常退出
        break
    time.sleep(3)           # 異常退出，退避重試
```

> **無監督者時的行為**：直接 `python main.py` 運行，呼叫 `hard_restart()` 後進程以碼 42 退出、不會重啟。此時應接入上述任一監督者。

## 相關文件

- [建立第一個機器人](../getting-started/first-bot.md) - `keep_running` 兩種基礎模式入門
- [生命週期管理](lifecycle.md) - 監聽 `core.init.start` / `core.init.complete` 等啟動事件
- [懶載入系統](lazy-loading.md) - 模組懶載入機制與 `load_module`



====
生态模块
====


### ErisPulse-App 安装与使用

# ErisPulse-App

[ErisPulse-App](https://github.com/ErisPulse/ErisPulse-App) 是由 ErisDev 直接維護的 **官方多端用戶端**（Android / Windows / Linux / macOS 均已發布），
提供完全原生的圖形化管理介面：在手機或電腦上建立、執行、管理多個機器人實例，
無需終端機，也無需單獨安裝 Python 環境。

> [!IMPORTANT]
> ErisPulse-App 是**獨立安裝的用戶端程式**，不是 `epsdk install` 安裝的模組。
> 它內建了 Python 執行時環境與 ErisPulse SDK，安裝即用——**手機上也能直接執行**。



## 功能速覽

- **多實例管理**：建立 / 啟動 / 停止 / 刪除多個實例，連接埠與存取權杖自動分配，支援全新環境或克隆既有環境
- **概覽儀表板**：適配器 / 模組 / 在線機器人 / 事件總數統計，CPU / 記憶體佔用告警變色
- **模組商店**：搜尋與標籤篩選、一鍵安裝 / 升級 / 解除安裝、指定版本安裝、pip 映像源與 Git 套件支援
- **事件流 + 事件構建器**：即時事件查看，視覺化建構測試事件並提交至適配器
- **監控**：日誌 / 生命週期 / 審計三合一檢視
- **指令管理**：前置字串與別名等全域設定、啟停與平台黑白名單
- **機器人總覽 / 設定 / 檔案管理**：原生介面直接操作實例
- **背景常駐**：Android 前台服務保活；Windows 最小化至系統匣，關閉視窗不中斷實例
- **模組動態視窗**：模組註冊的頁面自動出現在側邊導覽（與 Dashboard 同分組），點擊直接導向


## 支援平台

所有平台的安裝程式均可從 [GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases) 下載，按需選擇即可：

| 平台 | 安裝程式 | 說明 |
|------|--------|------|
| Android | `online-*.apk` / `offline-*.apk` | **手機直接執行**，無需電腦 |
| Windows | `windows-x64-setup.exe` / `windows-x64.zip` | 安裝版 / 免安裝版 |
| Linux | `linux-x64.tar.gz` | 解壓即用 |
| macOS | `macos-arm64.zip` | Apple Silicon（arm64） |

一個 Flutter 程式庫涵蓋所有平台。

## 安裝方式（Android / 手機直接執行）

從 [GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases) 下載 APK 安裝即可，有兩種建構：

| 建構 | 執行時映像 | 適用場景 |
|------|-----------|---------|
| `erispulse-app-online-*.apk` | 首次啟動時下載 | 安裝檔更小，適合網路良好 |
| `erispulse-app-offline-*.apk` | 已打包進 APK | 離線自包含，安裝後無需上網 |

兩種建構安裝步驟相同：

1. 下載並安裝 APK，啟動時允許通知權限（用於保持後台服務存活）
2. 首頁出現初始化橫幅後點擊執行首次初始化（含進度與日誌檢視）
3. 建立一個實例並啟動
4. 在 App 內建的管理介面設定配接器與模型 API Key

> 離線包自包含——安裝後無需網路。如果首次啟動下載慢或不穩定，
> 可在設定頁將下載來源切換為映像（ghfast / gh-proxy）。

### 安裝方式（桌面端：Windows / Linux / macOS）

1. 從 [GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases) 下載對應平台安裝包
   （Windows `setup.exe` 或免安裝 `zip`、Linux `tar.gz`、macOS `zip`）
2. 安裝並啟動
3. 在歡迎頁選擇要安裝的 ErisPulse SDK 版本（預設最新）並安裝
4. 建立實例並啟動

---

## 運作原理

```
┌────────────────────────────────────────────────────┐
│  ErisPulse-App (Flutter)                            │
│                                                    │
│  原生 UI ── Dashboard REST / WS API                │
│       │                                            │
│       ├── Android：前台服務 + proot + Ubuntu rootfs│
│       │        + Python + ErisPulse 實例           │
│       └── 桌面端：內建 Python + 直接進程管理         │
└────────────────────────────────────────────────────┘
```

- **Android**：實例運行在前台服務（background isolate）托管的 proot（使用者態 chroot）內，UI 關閉後機器人仍持續運行，崩潰自動重啟
- **桌面端**：實例作為 App 的直接子進程運行；Windows 支援最小化到系統匣背景常駐（關閉視窗不中斷實例），App 重啟後自動恢復對仍在運行實例的管理，退出時統一停止全部實例
- 所有平台的原生 UI 都透過 `127.0.0.1:<port>/Dashboard/*` 的 REST / WebSocket API 與實例通訊，與 [ErisPulse-Dashboard](dashboard.md) 共用同一套 API

---

## 與 SDK 的關係

- App 內建 ErisPulse SDK：Android 端打包在 Ubuntu 映像中，桌面端從 PyPI 安裝
  （歡迎頁可選版本，預設最新）
- App 中的執行個體與命令列 `epsdk` 建立的執行個體等價，可使用相同的模組 / 適配器
- 模組開發者可透過 [儀表板視窗註冊 API](docs/zh-TW/dashboard.md) 註冊自訂頁面：
  視窗會自動出現在 App 側邊導航（分組與儀表板一致），點擊跳轉對應頁面渲染

---

請直接傳回翻譯後的完整 Markdown 內容，不要包含任何其他文字。



### Dashboard 使用与视窗注册

# ErisPulse-Dashboard

[ErisPulse-Dashboard](https://pypi.org/project/ErisPulse-Dashboard/) 是 ErisDev 直接維護的 **Web 管理面板模組**，為 ErisPulse 提供視覺化的執行階段管理介面：模組啟停、設定編輯、日誌查看、事件流監控等。

> [!IMPORTANT]
> Dashboard **不是** ErisPulse 框架的內建功能，需要單獨安裝：
>
> ```bash
> epsdk install Dashboard
> ```

Dashboard 還支援其他 ErisPulse 模組將自訂的管理頁面註冊到側邊欄。註冊後，使用者可以直接在 Dashboard 中切換到該模組的專屬視窗頁面，無需額外開發獨立的前端介面。

> [!NOTE]
> 視窗註冊是**選用功能**。
>
> - 如果 Dashboard 模組**未安裝**或**未載入**，呼叫 `sdk.Dashboard.register_view()` 會拋出異常
> - 請務必使用 `try/except` 包裹註冊程式碼，確保模組本身的其他功能不受影響
> - 建議在註冊前檢查 Dashboard 是否可用：`hasattr(sdk, 'Dashboard') and sdk.Dashboard`

---

## 運作原理

```
模組 on_load()
  → 呼叫 sdk.Dashboard.register_view(...)
  → Dashboard 後端儲存視窗資訊
  → WebSocket 通知前端
  → 前端動態建立側邊欄導覽項目 + 頁面容器
  → 使用者點擊即可查看模組視窗
```

---

## 註冊 API

```python
sdk.Dashboard.register_view(
    id="MyModule",                    # 必填，唯一識別
    title="我的模組",                  # 中文名稱
    title_en="My Module",             # 英文名稱
    icon_svg='<svg>...</svg>',        # 側邊欄圖示 SVG
    html_content='<div>...</div>',     # 頁面 HTML 內容
    js_content='function xxx() {}',    # 頁面 JavaScript 邏輯
    css_content='.my-style {}',        # 選用自訂 CSS
    iframe_url='',                     # iframe 模式 URL（與 html_content 二選一）
    loader="loadMyModuleView",         # 切換到該頁面時呼叫的 JS 函數名
    group="group_extensions",          # 側邊欄分組
    group_title="",                    # 自訂分組中文名稱
    group_title_en="",                 # 自訂分組英文名稱
)
```

### 參數說明

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `id` | `str` | 是 | 視窗唯一識別，建議使用模組名稱 |
| `title` | `str` | 否 | 中文顯示名稱，預設使用 `id` |
| `title_en` | `str` | 否 | 英文顯示名稱，預設使用 `title` |
| `icon_svg` | `str` | 否 | 側邊欄圖示的完整 SVG 字串 |
| `html_content` | `str` | 否* | 註入模式的頁面 HTML 內容 |
| `js_content` | `str` | 否 | 頁面 JavaScript 程式碼 |
| `css_content` | `str` | 否 | 頁面自訂 CSS 樣式 |
| `iframe_url` | `str` | 否* | iframe 模式的 URL，設定後忽略 `html_content` |
| `loader` | `str` | 否 | 頁面啟動時自動呼叫的 JS 函數名 |
| `group` | `str` | 否 | 側邊欄分組識別，預設 `group_extensions` |
| `group_title` | `str` | 否 | 自訂分組的中文標題 |
| `group_title_en` | `str` | 否 | 自訂分組的英文標題 |

> *`html_content` 和 `iframe_url` 至少提供一個，否則頁面為空白。

---

## 兩種註入模式

### 模式一：HTML/JS 註入（推薦）

直接提供 HTML、JS、CSS 字串，Dashboard 會將內容註入到頁面中。該模式與 Dashboard 樣式完全一致，推薦使用 Dashboard 提供的 CSS 類別名稱。

```python
sdk.Dashboard.register_view(
    id="HelloPage",
    title="你好頁面", title_en="Hello",
    icon_svg='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/></svg>',
    html_content='<h1 class="page-title">Hello World</h1><div class="card"><div class="card-body">這是一個範例頁面</div></div>',
    group="group_tools",
)
```

> 完整的氣象模組範例（包含 API 路由、JS 互動等）請見下方 [完整模組範例](#完整模組範例)。

### 模式二：iframe 嵌入

模組提供自己的 HTML 頁面 URL（需自行註冊路由），Dashboard 以 iframe 方式嵌入。適合需要完全獨立 UI 或複雜互動的場景。

```python
sdk.Dashboard.register_view(
    id="MyVisualizer",
    title="資料視覺化", title_en="Data Visualizer",
    iframe_url="/MyVisualizer/view",
    group="group_tools",
)
```

> iframe 模式會自動在 URL 後附加 `token` 參數用於認證。

---

## 側邊欄分組

模組可指定視窗所在的側邊欄分組。Dashboard 內建以下分組：

| 分組識別 | 中文名 | 位置 |
|---------|--------|------|
| `group_overview` | 概覽 | 第1組 |
| `group_events` | 事件 | 第2組 |
| `group_extensions` | 擴充 | 第3組（預設） |
| `group_system` | 系統 | 第4組 |
| `group_tools` | 工具 | 第5組 |

指定內建分組名稱，模組視窗會附加到該分組末尾：

```python
group="group_tools"  # 附加到"工具"分組
```

也可以使用自訂分組名稱（不以 `group_` 開頭），Dashboard 會自動建立新分組：

```python
group="my_group",
group_title="我的分組",
group_title_en="My Group",
```

---

## 常用 CSS 類別名稱

模組視窗使用 HTML 註入模式時，可直接使用 Dashboard 已有的 CSS 類別名稱來保持視覺一致性：

| 類別名 | 用途 |
|------|------|
| `page-title` | 頁面標題，如 `<h1 class="page-title">標題</h1>` |
| `card` | 卡片容器 |
| `card-header` | 卡片標題列 |
| `card-body` | 卡片內容區域 |
| `grid-2` | 雙欄網格佈局 |
| `grid-3` | 三欄網格佈局 |
| `btn` | 基礎按鈕 |
| `btn-primary` | 主按鈕（藍色） |
| `btn-secondary` | 次要按鈕 |
| `btn-icon` | 圖示按鈕 |
| `btn-danger` | 危險操作按鈕 |

Dashboard 使用 CSS 變數控制主題色，您可以在模組視窗中直接引用：

| CSS 變數 | 用途 |
|----------|------|
| `var(--bg-p)` | 主背景色 |
| `var(--bg-s)` | 次背景色 |
| `var(--bg-t)` | 三級背景色（卡片等） |
| `var(--tx-p)` | 主文字色 |
| `var(--tx-s)` | 次文字色 |
| `var(--tx-t)` | 輔助文字色 |
| `var(--bd)` | 邊框色 |
| `var(--accent)` | 強調色 |
| `var(--ok-c)` | 成功色 |
| `var(--er-c)` | 錯誤色 |

這些變數會根據 Dashboard 的亮色/暗色主題自動切換，模組無需額外處理。

---

## 認證與 API 呼叫

在模組視窗的 JS 中呼叫模組自己的 API 時，需要攜帶 Dashboard 的 Token 進行認證：

```javascript
var token = localStorage.getItem('__ep_tk__');
var resp = await fetch('/YourModule/api/data', {
    headers: { 'Authorization': 'Bearer ' + token }
});
var data = await resp.json();
```

模組的 API 端點可以自行決定是否驗證 Token。如果需要驗證，可以從請求標頭中提取：

```python
async def _api_data(self, request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return {"error": "Unauthorized"}, 401
    return {"data": "hello"}
```

---

## 完整模組範例

以下是一個完整的氣象模組範例，展示如何註冊視窗、提供 API 資料、以及在卸載時清理資源：

```python
from ErisPulse import sdk
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.Core.Event import command


class Main(BaseModule):
    def __init__(self):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("Weather")
        self.config = self._load_config()

    @staticmethod
    def get_load_strategy():
        from ErisPulse.loaders import ModuleLoadStrategy
        return ModuleLoadStrategy(lazy_load=False, priority=50)

    async def on_load(self, event):
        self._register_routes()
        self._register_dashboard_view()
        self.logger.info("氣象模組已載入")

    async def on_unload(self, event):
        self._unregister_routes()
        if hasattr(self.sdk, 'Dashboard') and self.sdk.Dashboard:
            self.sdk.Dashboard.unregister_view("Weather")
        self.logger.info("氣象模組已卸載")

    def _load_config(self):
        config = self.sdk.config.getConfig("Weather")
        if not config:
            default = {"city": "北京", "api_key": ""}
            self.sdk.config.setConfig("Weather", default)
            return default
        return config

    def _register_routes(self):
        r = self.sdk.router
        r.register_http_route("Weather", "/api/current",
                              handler=self._api_current, methods=["GET"])

    def _unregister_routes(self):
        r = self.sdk.router
        try:
            r.unregister_http_route("Weather", "/api/current")
        except Exception:
            pass

    async def _api_current(self, request):
        return {
            "city": self.config.get("city", "北京"),
            "temp": 25,
            "humidity": 60,
        }

    def _register_dashboard_view(self):
        try:
            dashboard = self.sdk.Dashboard
            dashboard.register_view(
                id="Weather",
                title="天氣", title_en="Weather",
                icon_svg='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>',
                html_content='''
                    <h1 class="page-title">天氣查詢</h1>
                    <p style="color:var(--tx-s);margin-bottom:16px">查看目前天氣資訊</p>
                    <div class="grid-2">
                        <div class="card">
                            <div class="card-header">目前天氣</div>
                            <div class="card-body">
                                <div id="weather-info" style="font-size:14px;color:var(--tx-s)">點擊重新整理載入</div>
                            </div>
                        </div>
                        <div class="card">
                            <div class="card-header">操作</div>
                            <div class="card-body">
                                <button class="btn btn-primary" onclick="refreshWeather()">重新整理</button>
                            </div>
                        </div>
                    </div>
                ''',
                js_content='''
                    async function loadWeatherView() { await refreshWeather(); }
                    async function refreshWeather() {
                        var el = document.getElementById('weather-info');
                        if (!el) return;
                        el.textContent = '載入中...';
                        try {
                            var resp = await fetch('/Weather/api/current', {
                                headers: { 'Authorization': 'Bearer ' + localStorage.getItem('__ep_tk__') }
                            });
                            var data = await resp.json();
                            el.innerHTML = '<p>城市: ' + (data.city || '--') + '</p>' +
                                           '<p>溫度: ' + (data.temp || '--') + '°C</p>' +
                                           '<p>濕度: ' + (data.humidity || '--') + '%</p>';
                        } catch (e) {
                            el.textContent = '載入失敗: ' + e.message;
                        }
                    }
                ''',
                loader="loadWeatherView",
                group="group_tools",
            )
        except Exception as e:
            self.logger.warning(f"註冊 Dashboard 視窗失敗: {e}")
```

---

## 登出視窗

模組卸載時應呼叫 `unregister_view()` 清理已註冊的視窗：

```python
async def on_unload(self, event):
    if hasattr(self.sdk, 'Dashboard') and self.sdk.Dashboard:
        self.sdk.Dashboard.unregister_view("Weather")
```

登出後 Dashboard 前端會透過 WebSocket 即時移除側邊欄導覽項目和頁面內容，無需使用者重新整理。

---

## 注意事項

1. **載入順序** — Dashboard 的載入優先級為 `99999`（高優先級），您的模組優先級應低於此值（如 `50`），確保 Dashboard 先載入完成
2. **防禦性程式設計** — 註冊視窗時使用 `try/except` 包裹，因為 Dashboard 模組可能未安裝或未載入
3. **資源清理** — 在 `on_unload` 中呼叫 `unregister_view()` 移除已註冊的視窗
4. **ID 唯一性** — `id` 參數在整個 Dashboard 中必須唯一，建議直接使用模組名稱
5. **SVG 圖示** — `icon_svg` 應為完整的 `<svg>` 標籤，建議尺寸使用 `viewBox="0 0 24 24"`，使用 `stroke="currentColor"` 繼承 Dashboard 主題色
6. **JS 函數命名** — `js_content` 中的函數名應具有唯一性（如 `loadWeatherView`），避免與其他模組衝突
7. **動態更新** — 模組註冊/登出視窗後，Dashboard 前端會透過 WebSocket 即時更新側邊欄，無需重新整理頁面



### Takumi 图片渲染

# ErisPulse-Takumi

[ErisPulse-Takumi](https://pypi.org/project/ErisPulse-Takumi/) 是由 ccd2s 維護的 **第三方圖片渲染模組**，基於 [takumi-py](https://github.com/BalconyJH/takumi-py)，讓 Bot 能夠將 HTML、節點樹、Jinja 模板、SVG、動畫渲染為圖片。模組 **內建中英文字體**（Noto Sans SC / Roboto / Source Code Pro），無需額外配置。

> [!IMPORTANT]
> Takumi **不是** ErisPulse 框架的內建功能，需要單獨安裝：
>
> ```bash
> epsdk install Takumi
> ```

適用場景：

- 將資料/統計渲染為卡片圖片
- 將 Markdown / 長文字渲染為排版穩定的圖片，規避平台樣式差異
- 產生 SVG / 動畫，實現動態視覺效果
- 中英混排圖文（內建字體開箱即用）

---

## 安裝與啟用

```bash
epsdk install Takumi
```

安裝後模組會自動載入，在設定中確認啟用：

```toml
[Takumi]
enabled = true
```

---

## 快速上手

模組自動載入後，透過模組管理器取得，或使用 `sdk` 快捷方式：

```python
from ErisPulse import sdk

takumi = sdk.module.get("Takumi")
# 等價寫法：takumi = sdk.Takumi
```

### 渲染 HTML

```python
png = takumi.render_html(
    """
    <div class="card">
      <h1>你好，ErisPulse</h1>
      <p>由 Takumi 渲染</p>
    </div>
    """,
    stylesheets=["""
    .card {
      width: 800px;
      padding: 48px;
      color: white;
      background: #111827;
      font-family: "Noto Sans SC";
    }
    """],
    width=800,
    height=None,   # 按內容自動撐高
    lang="zh-CN",
)
```

### 渲染節點樹

```python
png = takumi.render_node(
    {
        "type": "text",
        "text": "中文和 English 都可直接渲染",
        "style": {"fontSize": 48, "color": "#111827"},
    },
    width=800,
    height=None,
    lang="zh-CN",
)
```

`png` 是 `bytes`，可透過 `event.reply(png, method="Image")` 傳送（詳見 [發送渲染結果](zh-TW/send-render-result)）。

---

## 渲染 API

`sdk.Takumi` 代理了底層 `takumi_py.Renderer` 的所有能力：所有渲染、測量、SVG、動畫、模板方法都可直接在 `sdk.Takumi` 上呼叫。對於這些方法，模組會在呼叫時**自動注入內建字體回退堆疊**（`takumi.families`），無需手動傳遞 `font_families`；若顯式傳入則尊重呼叫方設定。

### 方法總覽

| 類別 | 方法 | 返回 | 說明 |
|------|------|------|------|
| 靜態渲染 | `render_html(html, ...)` | `bytes` | 渲染 HTML 字串 |
| | `render_node(node, ...)` | `bytes` | 渲染節點樹（dict） |
| | `render_template(name, ctx, ...)` | `bytes` | 渲染 Jinja 模板 |
| | `render_compiled(node, ...)` | `bytes` | 渲染預編譯節點 |
| SVG 輸出 | `render_svg_html(html, ...)` | `str` | 輸出 SVG（HTML 輸入） |
| | `render_svg_node(node, ...)` | `str` | 輸出 SVG（節點樹輸入） |
| | `render_svg_template(name, ctx, ...)` | `str` | 輸出 SVG（模板輸入） |
| | `render_svg_compiled(node, ...)` | `str` | 輸出 SVG（預編譯輸入） |
| 動畫 | `render_animation(scenes, ...)` | `bytes` | 編碼多幀動畫 |
| | `render_sequence_at_time(scenes, time_ms, ...)` | `bytes` | 取序列某一時刻幀 |
| 測量 | `measure_node(node, ...)` | `dict` | 測量節點樹佈局 |
| | `measure_html(html, ...)` | `dict` | 測量 HTML 佈局 |
| | `measure_compiled(node, ...)` | `dict` | 測量預編譯節點 |
| 編譯 | `compile_node(node)` | `CompiledNode` | 編譯節點樹 |
| | `compile_html(html, ...)` | `CompiledNode` | 編譯 HTML |
| 字體 | `register_font(font)` | `list[str]` | 註冊自訂字體，返回 family 列表 |
| | `register_fonts(fonts)` | `list[str]` | 批量註冊 |

> `CompiledNode` 暴露 `resource_urls()` 方法，可預先發現待載入的 HTTP(S) 圖片參考，便於提前準備資源。

### 通用參數

以下參數適用於靜態渲染與 SVG 方法（動畫方法另有 `fps` 等，見對應範例）：

| 參數 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| `stylesheets` | `list[str]` | `None` | 文件級 CSS 字串列表；內聯 `style` 仍隨 HTML 一起解析 |
| `width` | `int \| None` | `1200` | 視口寬度（像素）；`None` 按佈局推斷 |
| `height` | `int \| None` | `630` | 畫布高度（像素）；`None` 按內容自動撐高（見 [視口與輸出格式](#視口與輸出格式)） |
| `lang` | `str \| None` | `None` | BCP-47 語言標籤（如 `zh-CN`），影響文字整形與換行 |
| `font_families` | `list[str]` | 自動注入 | 字體回退堆疊；便捷方法預設注入內建字體 |
| `format` | `str` | `"png"` | 輸出格式（見 [視口與輸出格式](#視口與輸出格式)） |
| `device_pixel_ratio` | `float` | `1.0` | 設備像素比，控制輸出解析度 |
| `time_ms` | `int` | `0` | 動畫取樣時刻（毫秒） |
| `dithering` | `str` | `"none"` | 抖動演算法：`none` / `ordered-bayer` / `floyd-steinberg` |
| `quality` | `int \| None` | `None` | 有損編碼品質 |
| `lossless` | `bool \| None` | `None` | 是否無損編碼 |
| `images` | `list` | `None` | 本次渲染的圖片資源（`ImageResource` 或 `(src, bytes)` 元組） |
| `keyframes` | `Mapping` | `None` | 結構化關鍵幀，無需寫入 `@keyframes` |
| `options` | `RenderOptions` | — | 以 `RenderOptions(...)` 聚合傳參，欄位與上表一致 |

完整欄位定義見 `takumi_py.RenderOptions`。

### 節點樹範例

```python
png = takumi.render_node(
    {
        "type": "container",
        "style": {"padding": "32px", "backgroundColor": "#111827"},
        "children": [
            {"type": "text", "text": "標題", "style": {"fontSize": 32, "color": "white"}},
            {"type": "text", "text": "正文", "style": {"fontSize": 18, "color": "#9ca3af"}},
        ],
    },
    width=800,
    height=None,
    lang="zh-CN",
)
```

### Jinja 模板範例

```python
png = takumi.render_template(
    "card.html.jinja",
    {"title": "Takumi", "subtitle": "Jinja to image"},
    stylesheets=["""
    .card {
      width: 800px;
      padding: 48px;
      color: white;
      background: #111827;
    }
    """],
    width=800,
    height=None,
    lang="zh-CN",
)
```

> 可透過 `filters={...}` 注入自訂 Jinja 過濾器，或 `environment=...` 傳入完整 `jinja2.Environment`。模板目錄與環境設定詳見 [takumi-py 模板文件](https://github.com/BalconyJH/takumi-py/blob/main/docs/zh-TW/guides/templates.md)。

### SVG 輸出範例

```python
svg = takumi.render_svg_html(
    '<div class="card">Hello</div>',
    stylesheets=[".card { width: 800px; color: black; }"],
    width=800,
    height=None,
)
```

### 動畫範例

```python
from takumi_py import AnimationScene

webp = takumi.render_animation(
    [
        AnimationScene(
            {"type": "container", "style": {"width": "100%", "height": "100%", "backgroundColor": "black"}},
            duration_ms=100,
        ),
        AnimationScene(
            {"type": "container", "style": {"width": "100%", "height": "100%", "backgroundColor": "white"}},
            duration_ms=100,
        ),
    ],
    width=64,
    height=64,
    fps=20,
    format="webp",
)
```

> 每幀由 `AnimationScene(node, duration_ms=...)` 構成，`duration_ms` 必須為正數。

---

## 視埠與輸出格式

### 輸出格式

| 場景 | `format` 取值 |
|------|---------------|
| 靜態圖片 | `png`（預設） / `jpeg` / `jpg` / `webp` / `ico` / `raw` |
| 動畫 | `webp`（預設） / `apng` / `gif` |

`format="raw"` 返回行主序 RGBA 位元組串流，用於自訂像素級處理。

### 關於 width 與 height

`width` 與 `height` 的角色不對稱：

- `width` 是**視埠寬度**，文字與佈局按它換行、回流。**應固定**為具體數值（如 `800`），否則畫布會按內容自然寬度拉伸、文字不換行，尺寸不可控。
- `height` 是**畫布高度**，隨內容增長。`height` 預設值為 `630`；傳入 `height=None` 時，Takumi 會**根據內容自動撐高畫布**（auto viewport）。

> [!TIP]
> **推薦組合：固定 `width` + `height=None`。** 僅當需要固定尺寸畫布或裁切效果時，才傳入具體的 `height`。

> [!NOTE]
> `width` / `height` 任一在技術上都可傳 `None` 讓其按佈局推斷（如節點自身已宣告尺寸時）；兩者都給定時，輸出尺寸為確定值。

---

## 字體

### 內建字體

| 字體 | family | 類別 |
|------|--------|------|
| Noto Sans SC | `Noto Sans SC` | sans-serif |
| Roboto | `Roboto` | sans-serif |
| Roboto Italic | `Roboto` | sans-serif（italic） |
| Source Code Pro | `Source Code Pro` | monospace |
| Source Code Pro Italic | `Source Code Pro` | monospace（italic） |

模組屬性：

| 屬性 | 說明 |
|------|------|
| `takumi.fonts` | 內建字型檔案名稱清單 |
| `takumi.families` | 已註冊的字型 family 清單 |

### 自動注入

`sdk.Takumi` 上的全部渲染、測量、SVG、動畫、模板方法會自動注入 `takumi.families` 作為字型回退堆疊。若直接呼叫 `takumi.renderer`（原生實例）或透過 `create_renderer()` 建立的獨立實例，則需手動傳 `font_families=takumi.families`。

### 自訂字體

```python
from takumi_py import FontResource

families = takumi.renderer.register_font(
    FontResource(
        font_bytes,
        name="MyFont",
        weight=400,
        style="normal",
        generic_family="sans-serif",
    )
)
```

`register_font` 回傳已註冊的 family 名稱清單，可在後續渲染時作為 `font_families` 傳入。

---

## 渲染器執行個體

### 原生 Renderer

`takumi.renderer` 是原始的 `takumi_py.Renderer` 執行個體。直接呼叫時需手動傳 `font_families`：

```python
png = takumi.renderer.render_html(
    "<div>你好</div>",
    font_families=takumi.families,
    lang="zh-CN",
)
```

### 獨立 Renderer

需要隔離字型 / 圖片 / 資源快取時（長生命週期程式、多租戶情境），可建立獨立的 `Renderer`，內建字型會自動註冊：

```python
renderer = takumi.create_renderer(cache_max_bytes=64 * 1024 * 1024)

png = renderer.render_html(
    "<div>獨立 Renderer</div>",
    font_families=takumi.families,
    width=800,
    height=None,
    lang="zh-CN",
)
```

`create_renderer()` 接受 `takumi_py.Renderer` 的建構參數：

| 參數 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| `load_default_fonts` | `bool` | `False` | 是否載入 takumi-py 自帶字型（內建字型始終載入） |
| `fonts` | `list[FontResource]` | `None` | 額外註冊的自訂字型 |
| `cache_max_bytes` | `int \| None` | `None` | 資源快取上限（位元組）；`0` 禁用 |
| `persistent_images` | `list` | `None` | 持久化圖片資源 |

> 獨立執行個體不經過模組代理，因此若要保留統一的內建字型回退堆疊，需顯式傳入 `font_families=takumi.families`。若顯式傳入 `font_families`，模組會尊重呼叫方設定，不再注入預設回退堆疊；`RenderOptions(font_families=...)` 同樣有效。

---

## 傳送渲染結果

渲染得到的圖片為 `bytes`，可透過事件回覆直接傳送：

```python
from ErisPulse import sdk

takumi = sdk.Takumi
png = takumi.render_html("<div>hello</div>", lang="zh-TW")

# 方式一：以 Image 方法回覆
await event.reply(png, method="Image")

# 方式二：透過 OneBot12 訊息段回覆
from ErisPulse.Core.Event import MessageBuilder
await event.reply_ob12(
    MessageBuilder().image(png).build()
)
```

> 不同平台對圖片的封裝由適配器統一處理。詳見 [MessageBuilder 詳解](../advanced/message-builder.md) 與 [傳送方法規範](../standards/send-method-spec.md)。

## 設定

```toml
[Takumi]
enabled = true
```

---



======
平台特性指南
======


### 平台特性总览

# ErisPulse PlatformFeatures 文檔

> 基線協議：[OneBot12](https://12.onebot.dev/) 
> 
> 本文檔為**平台特定功能指南**，包含：
> - 各適配器支援的Send方法鏈式呼叫示例
> - 平台特有的事件/訊息格式說明
> 
> 通用使用方法請參考：
> - [基礎概念](../getting-started/basic-concepts.md)
> - [事件轉換標準](../standards/event-conversion.md)  
> - [API回應規範](../standards/api-response.md)

---

## 平台特定功能

此部分由各適配器開發者維護，用於說明該適配器與 OneBot12 標準的差異和擴展功能。請參考以下各平台的詳細文件：

- [維護說明](maintain-notes.md)

- [雲湖平台特性](yunhu.md)
- [雲湖用戶平台特性](yunhu_user.md)
- [Telegram平台特性](telegram.md)
- [OneBot11平台特性](onebot11.md)
- [OneBot12平台特性](onebot12.md)
- [郵件平台特性](email.md)
- [Kook(開黑啦)平台特性](kook.md)
- [Matrix平台特性](matrix.md)
- [QQ官方機器人平台特性](qqbot.md)
- [花楓咖啡館](ideaura.md)
- [Discord](discord.md)
- [Webhook協議橋](webhook.md)
- [微信公眾號](wechatmp.md)

> 此外還有 `sandbox` 適配器，但此適配器無需維護平台特性文件

---

## 通用介面

### Send 鏈式呼叫
所有適配器都支援以下標準呼叫方式：

> **注意：** 文件中的 `{AdapterName}` 需替換為實際適配器名稱（如 `yunhu`、`telegram`、`onebot11`、`email` 等）。

1. 指定類型和ID: `To(type,id).Func()`
   ```python
   # 獲取適配器實例
   my_adapter = adapter.get("{AdapterName}")
   
   # 發送訊息
   await my_adapter.Send.To("user", "U1001").Text("Hello")
   
   # 例如：
   yunhu = adapter.get("yunhu")
   await yunhu.Send.To("user", "U1001").Text("Hello")
   ```
2. 僅指定ID: `To(id).Func()`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.To("U1001").Text("Hello")
   
   # 例如：
   telegram = adapter.get("telegram")
   await telegram.Send.To("U1001").Text("Hello")
   ```
3. 指定發送帳號: `Using(account_id)`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.Using("bot1").To("U1001").Text("Hello")
   
   # 例如：
   onebot11 = adapter.get("onebot11")
   await onebot11.Send.Using("bot1").To("U1001").Text("Hello")
   ```
4. 直接呼叫: `Func()`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.Text("廣播訊息")
   
   # 例如：
   email = adapter.get("email")
   await email.Send.Text("廣播訊息")
   ```

#### 異步發送與結果處理

Send DSL 的方法返回 `asyncio.Task` 物件，這意味著您可以選擇是否立即等待結果：

```python
# 獲取適配器實例
my_adapter = adapter.get("{AdapterName}")

# 不等待結果，訊息在背景發送
task = my_adapter.Send.To("user", "123").Text("Hello")

# 如果需要獲取發送結果，稍後可以等待
result = await task
```

#### 發送規則裝飾器

在實際開發中，經常需要：發送成功後才執行後續邏輯、失敗自動重試、超時取消、發送進度監控等。Send DSL 內建了一套發送規則裝飾器，透過鏈式方法附加規則：

| 方法 | 說明 |
|--------|------|
| `.Hook(callback)` | 發送成功後執行的回調（可多次呼叫） |
| `.Retry(times=1)` | 失敗自動重試 N 次（含首次共 N+1 次） |
| `.Timeout(seconds)` | 單次發送超時，超時取消（可與 Retry 叠加） |
| `.Defer(seconds)` | 延遲發送（進程內定時，不持久化） |
| `.OnProgress(callback)` | 各階段進度回調，傳入 SendContext |
| `.OnError(callback)` | 最終失敗時的錯誤回調（僅觸發一次） |

```python
yunhu = adapter.get("yunhu")

# 發送成功後才扣積分
await (yunhu.Send.To("user", "123")
       .Hook(lambda r: deduct_points("123"))
       .Text("消費成功"))

# 失敗重試 + 超時取消 + 進度監控
def on_progress(ctx):
    print(f"階段: {ctx.stage}, 嘗試: {ctx.attempt + 1}/{ctx.max_attempts}")

task = (yunhu.Send.To("user", "123")
        .Retry(3)              # 最多重試 3 次
        .Timeout(10)           # 每次超時 10 秒
        .OnProgress(on_progress)
        .OnError(lambda ctx: notify_admin(ctx.error))
        .Text("重要通知"))
```

規則方法返回 `self`，必須放在發送方法（Text/Image 等）之前呼叫。`SendContext` 包含 `stage`（pending/sending/retrying/success/failed/timeout）、`attempt`、`elapsed`、`error`、`result` 等字段，便於監控。

#### 批量建構模式（Build）

一條鏈路中建構多個發送方法，最後統一執行。適用於「一口氣發多條訊息」的場景：

```python
yunhu = adapter.get("yunhu")

# 建構多條訊息，統一發送
results = await (yunhu.Send.To("user", "123")
                .Build()                     # 進入建構模式
                .Text("通知一")
                .Image("pic.jpg")
                .Text("通知二")
                .send_all())                 # 統一執行
# results = [Text結果, Image結果, Text結果]
```

`.send_all()` 默認**並行**執行（併發發送，效率高）。需要保證訊息到達順序時呼叫 `.Sequential()` 串行執行：

```python
# 串行執行（保證順序）+ 失敗重試
await (yunhu.Send.To("group", "456")
       .Build()
       .Sequential()                # 按順序依次發送
       .Retry(2)                     # 失敗的條目各自重試
       .Text("第一條").Text("第二條")
       .send_all())
```

批量執行採用**失敗繼續**策略：某條失敗不會中斷其他條，失敗的條目自動重試。批量也支援整批的 `Hook`（全部成功後觸發）、`OnError`（有失敗時觸發）、`OnProgress`（進度回調）。

> 更詳細的規則與批量建構說明請參考 [SendDSL 詳解](../developer-guide/adapters/send-dsl.md)。

### 事件監聽
有三種事件監聽方式：

1. 平台原生事件監聽：
   ```python
   from ErisPulse.Core import adapter, logger
   
   @adapter.on("event_type", raw=True, platform="{AdapterName}")
   async def handler(data):
       logger.info(f"收到{AdapterName}原生事件: {data}")
   ```

2. OneBot12標準事件監聽：
   ```python
   from ErisPulse.Core import adapter, logger

   # 監聽OneBot12標準事件
   @adapter.on("event_type")
   async def handler(data):
       logger.info(f"收到標準事件: {data}")

   # 監聽特定平台的標準事件
   @adapter.on("event_type", platform="{AdapterName}")
   async def handler(data):
       logger.info(f"收到{AdapterName}標準事件: {data}")
   ```

3. Event模組監聽：
    `Event`的事件基於 `adapter.on()` 函數，因此`Event`提供的事件格式是一個OneBot12標準事件

    ```python
    from ErisPulse.Core.Event import message, notice, request, command

    message.on_message()(message_handler)
    notice.on_notice()(notice_handler)
    request.on_request()(request_handler)
    command("hello", help="發送問候訊息", usage="hello")(command_handler)

    async def message_handler(event):
        logger.info(f"收到訊息: {event}")
    async def notice_handler(event):
        logger.info(f"收到通知: {event}")
    async def request_handler(event):
        logger.info(f"收到請求: {event}")
    async def command_handler(event):
        logger.info(f"收到命令: {event}")
    ```

其中，最推薦的是使用 `Event` 模組進行事件處理，因為 `Event` 模組提供了豐富的事件類型，以及豐富的事件處理方法。

---

## 標準格式
為方便參考，這裡給出了簡單的事件格式，如果需要詳細資訊，請參考上方的連結。

> **注意：** 以下格式為基礎 OneBot12 標準格式，各適配器可能在此基礎上有擴展欄位。具體請參考各適配器的特定功能說明。

### 標準事件格式
所有適配器必須實現的事件轉換格式：
```json
{
  "id": "event_123",
  "time": 1752241220,
  "type": "message",
  "detail_type": "group",
  "platform": "example_platform",
  "self": {"platform": "example_platform", "user_id": "bot_123"},
  "message_id": "msg_abc",
  "message": [
    {"type": "text", "data": {"text": "你好"}}
  ],
  "alt_message": "你好",
  "user_id": "user_456",
  "user_nickname": "ExampleUser",
  "group_id": "group_789"
}
```

### 標準回應格式
#### 訊息發送成功
```json
{
  "status": "ok",
  "retcode": 0,
  "data": {
    "message_id": "1234",
    "time": 1632847927.599013
  },
  "message_id": "1234",
  "message": "",
  "echo": "1234",
  "{platform}_raw": {...}
}
```

#### 訊息發送失敗
```json
{
  "status": "failed",
  "retcode": 10003,
  "data": null,
  "message_id": "",
  "message": "缺少必要參數",
  "echo": "1234",
  "{platform}_raw": {...}
}
```

---

## 參考連結
ErisPulse 項目：
- [主庫](https://github.com/ErisPulse/ErisPulse/)
- [Yunhu 適配器庫](https://github.com/ErisPulse/ErisPulse-YunhuAdapter)
- [Telegram 適配器庫](https://github.com/ErisPulse/ErisPulse-TelegramAdapter)
- [OneBot 適配器庫](https://github.com/ErisPulse/ErisPulse-OneBotAdapter)

相關官方文件：
- [OneBot V11 協議文件](https://github.com/botuniverse/onebot-11)
- [Telegram Bot API 官方文件](https://core.telegram.org/bots/api)
- [雲湖官方文件](https://www.yhchat.com/document/1-3)

## 參與貢獻

我們歡迎更多開發者參與編寫和維護適配器文件！請按照以下步驟提交貢獻：
1. Fork [ErisPuls](https://github.com/ErisPulse/ErisPulse) 倉庫。
2. 在 `docs/platform-features/` 目錄下建立一個 Markdown 檔案，並命名格式為 `<平台名稱>.md`。
3. 在本 `README.md` 檔案中新增對您貢獻的適配器的連結以及相關官方文件。
4. 提交 Pull Request。

感謝您的支持！



### OneBot11 适配

# OneBot11 平台特性文件

OneBot11Adapter 是基於 OneBot V11 協議建構的適配器。

---
docs/zh-TW/quick-start.md

## 文件資訊

- 對應模組版本: 4.0.0
- 維護者: ErisPulse

## 基本資訊

- 平台簡介：OneBot 是一個聊天機器人應用介面標準
- 適配器名稱：OneBotAdapter
- 支援的協定/API版本：OneBot V11
- 多帳號支援：預設多帳號架構，支援同時設定和執行多個 OneBot 帳號
- 配置鍵名：`OneBotAdapter`

## 支援的消息發送類型

所有發送方法均透過鏈式語法實現，例如：

```python
from ErisPulse.Core import adapter
onebot = adapter.get("onebot11")

# 使用預設帳戶發送
await onebot.Send.To("group", group_id).Text("Hello World!")

# 指定特定帳戶發送
await onebot.Send.Using("main").To("group", group_id).Text("來自主帳戶的消息")

# 鏈式修飾：@使用者 + 回覆
await onebot.Send.To("group", group_id).At(123456).Reply(msg_id).Text("回覆訊息")

# @全體成員
await onebot.Send.To("group", group_id).AtAll().Text("公告訊息")
```

### 基礎發送方法

- `.Text(text: str)`：發送純文字訊息。
- `.Image(file: Union[str, bytes], filename: str = "image.png")`：發送圖片（支援 URL、Base64 或 bytes）。
- `.Voice(file: Union[str, bytes], filename: str = "voice.amr")`：發送語音訊息。
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")`：發送影片訊息。
- `.Face(id: Union[str, int])`：發送 QQ 表情。
- `.File(file: Union[str, bytes], filename: str = "file.dat")`：發送檔案（自動判斷類型）。
- `.Raw_ob12(message: List[Dict], **kwargs)`：發送 OneBot12 格式訊息（自動轉換為 OB11）。
- `.Recall(message_id: Union[str, int])`：撤回訊息。

### 群操作方法

以下方法需透過 `To("group", group_id)` 指定目標群，使用群上下文執行操作：

- `.Kick(user_id, reject_add_request=False)`：踢出群成員。
- `.Ban(user_id, duration=1800)`：禁言群成員（秒），0 表示解禁。
- `.WholeBan(enable=True)`：開啟/關閉全體禁言。
- `.SetAdmin(user_id, enable=True)`：設定/取消群管理員。
- `.SetCard(user_id, card="")`：設定群名片。
- `.SetGroupName(name)`：修改群名稱。
- `.Leave(is_dismiss=False)`：退群（群主可解散）。
- `.SetTitle(user_id, title="")`：設定群頭銜。
- `.SetPortrait(file)`：設定群頭像。

### 查詢方法

- `.GetMsg(message_id)`：獲取訊息內容。
- `.GetForwardMsg(id)`：獲取合併轉發訊息。
- `.GetLoginInfo()`：獲取目前登入號資訊。
- `.GetFriendList()`：獲取好友列表。
- `.GetGroupInfo()`：獲取群資訊（需 `To("group", group_id)`）。
- `.GetGroupList()`：獲取群列表。
- `.GetGroupMemberInfo(user_id)`：獲取群成員資訊（需 `To("group", group_id)`）。
- `.GetGroupMemberList()`：獲取群成員列表（需 `To("group", group_id)`）。

### 好友操作方法

- `.Like(user_id, times=1)`：發送好友讚（最多 10 次）。

### 鏈式修飾方法（可組合使用）

鏈式修飾方法返回 `self`，支援鏈式呼叫，必須在最終發送方法前呼叫：

- `.At(user_id: Union[str, int], name: str = None)`：@指定使用者（可多次呼叫）。
- `.AtAll()`：@全體成員。
- `.Reply(message_id: Union[str, int])`：回覆指定訊息。

### 鏈式呼叫示例

```python
# 基礎發送
await onebot.Send.To("group", 123456).Text("Hello")

# @單個使用者
await onebot.Send.To("group", 123456).At(789012).Text("你好")

# @多個使用者
await onebot.Send.To("group", 123456).At(111).At(222).At(333).Text("大家好")

# 發送 OneBot12 格式訊息
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await onebot.Send.To("group", 123456).Raw_ob12(ob12_msg)

# 點讚
await onebot.Send.Like(123456, times=10)

# 禁言群成員
await onebot.Send.To("group", 123456).Ban(789012, duration=3600)

# 解禁
await onebot.Send.To("group", 123456).Ban(789012, duration=0)

# 踢人
await onebot.Send.To("group", 123456).Kick(789012)

# 設定群管理員
await onebot.Send.To("group", 123456).SetAdmin(789012)

# 修改群名
await onebot.Send.To("group", 123456).SetGroupName("新群名")

# 獲取群資訊
result = await onebot.Send.To("group", 123456).GetGroupInfo()

# 指定帳戶操作
await onebot.Send.Using("main").To("group", 123456).Ban(789012)
```

### 不支援的類型處理

如果呼叫未定義的發送方法，適配器會回傳文字提示：
```python
# 呼叫不存在的方法
await onebot.Send.To("group", 123456).SomeUnsupportedMethod(arg1, arg2)
# 實際發送: "[不支援的發送類型] 方法名: SomeUnsupportedMethod, 參數: [...]"
```

## 請求操作（Request DSL）

適配器提供請求操作 DSL，用於處理好友請求和群請求（加群/邀請）的同意/拒絕操作。

### Event 快捷方法

請求事件支援 `event.approve()` 和 `event.reject()` 快捷方法，內部自動呼叫 Request DSL：

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    comment = event.get("comment", "")

    if comment == "passphrase":
        await event.approve()
    else:
        await event.reject()

@request.on_group_request()
async def handle_group_request(event):
    group_id = event.get("group_id")
    await event.approve()
```

### 手動呼叫 Request DSL

```python
# 同意請求
await onebot.Request("flag_string").accept()

# 拒絕請求
await onebot.Request("flag_string").reject()

# 指定帳號操作
await onebot.Request("flag_string").Using("main").accept()
```

### 完整範例

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    comment = event.get("comment", "")

    # 方式一：使用 Event 快捷方法
    if comment == "passphrase":
        await event.approve()
    else:
        await event.reject()

    # 方式二：使用 Request DSL
    flag = event.get("flag")
    if comment == "passphrase":
        await onebot.Request(flag).accept()
    else:
        await onebot.Request(flag).reject()
```

### 請求操作回傳值

```python
{
    "status": "ok",
    "retcode": 0,
    "data": {...},
    "message_id": "",
    "message": ""
}
```

## 事件類型映射

### 標準 OB12 映射

| OB11 原始類型 | 轉換後 detail_type | 說明 |
|--------------|-------------------|------|
| message_type: private | `private` | 私聊消息 |
| message_type: group | `group` | 群聊消息 |
| request_type: friend | `friend` | 好友請求 |
| request_type: group | `group` | 群請求 |
| meta_event_type: heartbeat | `heartbeat` | 心跳 |
| notice_type: group_upload | `group_file_upload` | 群文件上傳 |
| notice_type: group_admin | `group_admin_change` | 群管理員變動 |
| notice_type: group_increase | `group_member_increase` | 群成員增加 |
| notice_type: group_decrease | `group_member_decrease` | 群成員減少 |
| notice_type: group_ban | `group_ban` | 群禁言 |
| notice_type: friend_add | `friend_increase` | 好友添加 |
| notice_type: friend_delete | `friend_decrease` | 好友刪除 |
| notice_type: group_recall / friend_recall | `message_recall` | 消息撤回 |

### 平台特有事件（onebot11_ 前綴）

| OB11 原始類型 | 轉換後 detail_type | 說明 |
|--------------|-------------------|------|
| meta_event_type: lifecycle | `onebot11_lifecycle` | OneBot 實現生命週期 |
| notify + sub_type: honor | `onebot11_honor` | 群榮譽變更 |
| notify + sub_type: poke | `onebot11_poke` | 戳一戳 |
| notify + sub_type: lucky_king | `onebot11_lucky_king` | 群紅包運氣王 |
| CQ 碼未知類型 | 消息段 `onebot11_{type}` | 未識別的 CQ 碼 |

### 事件示例

```python
// 好友請求
{
  "type": "request",
  "detail_type": "friend",
  "user_id": "789012",
  "comment": "請加好友",
  "request_id": "flag_abc123",
  "flag": "flag_abc123"
}

// 心跳
{
  "type": "meta_event",
  "detail_type": "heartbeat",
  "interval": 5000,
  "status": {...}
}

// 生命週期（平台特有）
{
  "type": "meta_event",
  "detail_type": "onebot11_lifecycle",
  "sub_type": "enable"
}

// 戳一戳（平台特有）
{
  "type": "notice",
  "detail_type": "onebot11_poke",
  "group_id": "123456",
  "user_id": "789012",
  "target_id": "345678"
}

// 群紅包運氣王（平台特有）
{
  "type": "notice",
  "detail_type": "onebot11_lucky_king",
  "group_id": "123456",
  "user_id": "789012",
  "target_id": "345678"
}

// 榮譽變更（平台特有）
{
  "type": "notice",
  "detail_type": "onebot11_honor",
  "group_id": "123456",
  "user_id": "789012",
  "honor_type": "talkative"
}

// CQ 碼擴展消息段
{
  "type": "message",
  "message": [
    {"type": "onebot11_shake", "data": {}}
  ]
}
```

### 擴展字段說明

- 所有特有字段均以 `onebot11_` 前綴標識
- 保留原始事件數據在 `onebot11_raw` 字段
- 保留原始事件類型在 `onebot11_raw_type` 字段
- 消息內容中的 CQ 碼會轉換為相應的消息段（標準類型無前綴，未知類型加 `onebot11_` 前綴）
- 回覆消息會添加 `reply` 類型的消息段
- @消息會添加 `mention` 類型的消息段

## 事件擴展方法

OneBot11 适配器為事件物件註冊了以下平台專有方法，可在事件處理器中直接呼叫：

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    raw_self_id = event.get_raw_self_id()
    sender_info = event.get_sender_info()
    sender_role = event.get_sender_role()
```

### 方法列表

| 方法 | 回傳類型 | 說明 |
|------|----------|------|
| `get_raw_event()` | `dict` | 取得 OneBot11 完整原始事件資料 |
| `get_raw_self_id()` | `str` | 取得原始 self_id（Bot 的 QQ 號） |
| `get_sender_info()` | `dict` | 取得完整的發送者資訊（包含 nickname、role、level 等） |
| `get_sender_role()` | `str` | 取得發送者在群內的角色（owner/admin/member） |
| `get_sender_level()` | `int` | 取得發送者等級 |
| `get_sender_title()` | `str` | 取得發送者群頭銜 |
| `is_system_message()` | `bool` | 判斷是否為系統訊息（sub_type == "system"） |

### 使用範例

```python
from ErisPulse.Core.Event import message, command

@message.on_group_message()
async def handle_group(event):
    role = event.get_sender_role()
    if role == "admin" or role == "owner":
        await event.reply("管理員好！")

    title = event.get_sender_title()
    if title:
        await event.reply(f"你的頭銜是: {title}")

@command("whoami")
async def whoami(event):
    info = event.get_sender_info()
    nickname = info.get("nickname", "未知")
    level = event.get_sender_level()
    await event.reply(f"暱稱: {nickname}, 等級: {level}")
```

## 配置選項

OneBot11 适配器采用多账户架构，每个账户独立配置。配置键名为 `OneBotAdapter`。

### 账户配置字段

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `bot_id` | `str` | 是 | `""` | 机器人 QQ 号，用於標識帳戶 |
| `mode` | `str` | 否 | `"server"` | 運行模式：`"server"`（被動監聽）或 `"client"`（主動連接） |
| `url` | `str` | 否 | `"ws://127.0.0.1:3001"` | Client 模式的 WebSocket 地址 |
| `token` | `str` | 否 | `""` | 認證 Token（Client 模式連接 Token / Server 模式驗證 Token） |
| `server_path` | `str` | 否 | `"/"` | Server 模式的 WebSocket 路徑 |
| `enabled` | `bool` | 否 | `true` | 是否啟用該帳戶 |
| `name` | `str` | 否 | `""` | 帳戶備註名稱 |

### 內建預設值

- 重連間隔：30秒
- API調用超時：30秒

### 配置示例

```toml
[OneBotAdapter.accounts.main]
bot_id = "123456789"
mode = "server"
server_path = "/onebot-main"
token = "main_token"
enabled = true

[OneBotAdapter.accounts.backup]
bot_id = "987654321"
mode = "client"
url = "ws://127.0.0.1:3002"
token = "backup_token"
enabled = true

[OneBotAdapter.accounts.test]
bot_id = "111222333"
mode = "client"
url = "ws://127.0.0.1:3003"
enabled = false
```

### 預設配置

如果未配置任何帳戶，适配器會自動創建：
```toml
[OneBotAdapter.accounts.default]
bot_id = ""
mode = "server"
server_path = "/"
enabled = true
```

## 發送方法返回值

所有發送方法均返回一個 Task 對象，可以直接 await 獲取發送結果。返回結果遵循 ErisPulse 适配器标准化返回规范：

```python
{
    "status": "ok",
    "retcode": 0,
    "data": {...},
    "message_id": "123456",
    "message": "",
    "onebot11_raw": {...}
}
```

### 多账户發送語法

```python
# 賬戶選擇方法
await onebot.Send.Using("main").To("group", 123456).Text("主账户消息")
await onebot.Send.Using("backup").To("group", 123456).Image("http://example.com/image.jpg")

# 通過 bot_id 選擇賬戶
await onebot.Send.Using("123456789").To("group", 123456).Text("通過QQ號選擇")

# API調用方式
await onebot.call_api("send_msg", account_id="main", group_id=123456, message="Hello")
```

### 賬戶解析優先級

`call_api` 和 `Using()` 中 `account_id` 參數的解析優先級：
1. 精確匹配賬戶名稱
2. 匹配 `bot_id` 字段
3. 匹配賬戶的任意 `str` 類型字段
4. 回退到第一個已啟用的賬戶

## 異步處理機制

OneBot11 適配器採用異步非阻塞設計，確保：
1. 消息發送不會阻塞事件處理循環
2. 多個併發發送操作可以同時進行
3. API 回應能夠即時處理
4. WebSocket 連接保持活躍狀態
5. 多帳號併發處理，每個帳號獨立運行

## 錯誤處理

適配器提供完善的錯誤處理機制：
1. 網路連接異常自動重連（支援每個帳戶獨立重連，間隔30秒）
2. API 呼叫超時處理（固定30秒超時）
3. 連接失敗時自動按間隔重試

## 事件處理增強

多帳戶模式下，所有事件都會自動添加帳戶資訊：
```python
{
    "type": "message",
    "detail_type": "private",
    "self": {"user_id": "123456789", "platform": "onebot11"},
    "platform": "onebot11",
    // ... 其他事件欄位
}
```

適配器會自動維護 `self_id → account_name` 映射，`event.reply()` 無需手動指定帳戶即可正確路由到來源帳戶。

## 管理介面

```python
# 獲取所有帳號資訊
accounts = onebot.accounts

# 檢查帳號連線狀態
connection_status = {
    account_id: connection is not None and not connection.closed
    for account_id, connection in onebot.connections.items()
}

# 動態啟用/停用帳號（需要重啟適配器）
onebot.accounts["test"].enabled = False
```

## self_id 自動映射

適配器會自動建立 OneBot `self_id`（QQ號）到 `account_name` 的映射關係，用於事件回傳路由：

```python
# 适配器内部自动完成
# 當收到事件時，self.user_id 字段填充為 bot_id
# 适配器自动记录: self_id("123456789") → account_name("main")

# 因此 event.reply() 可以自動找到正確的帳戶發送消息
@message.on_message()
async def handler(event):
    await event.reply("自動路由到正確的帳戶")
```



### OneBot12 适配

# OneBot12 平台特性文件

OneBot12Adapter 是基於 OneBot V12 協議建構的適配器，作為 ErisPulse 框架的基線協議適配器。

---

## 文件資訊

- 對應模組版本: 4.0.0
- 維護者: ErisPulse
- 協議版本: OneBot V12

## 基本資訊

- 平台簡介：OneBot V12 是一個通用的聊天機器人應用介面標準，是 ErisPulse 框架的基線協議
- 適配器名稱：OneBot12Adapter
- 支援的協議/API版本：OneBot V12
- 多帳戶支援：完全多帳戶架構，支援同時配置和執行多個 OneBot12 帳戶

## 支援的訊息傳送類型

所有傳送方法均透過鏈式語法實現，例如：

```python
from ErisPulse.Core import adapter
onebot12 = adapter.get("onebot12")

# 使用預設帳戶傳送
await onebot12.Send.To("group", group_id).Text("Hello World!")

# 指定特定帳戶傳送
await onebot12.Send.To("group", group_id).Account("main").Text("來自主帳戶的訊息")
```

### 大小寫不敏感呼叫

所有傳送方法和鏈式修飾方法均支援大小寫不敏感呼叫，適配器會自動映射到正確的標準方法名：

```python
# 以下所有呼叫方式等價
await onebot12.Send.To("user", 123).Text("hello")
await onebot12.Send.To("user", 123).text("hello")
await onebot12.Send.To("user", 123).TEXT("hello")

# 鏈式修飾方法同樣支援
await onebot12.Send.To("group", 123).At(456).Text("hello")
await onebot12.Send.To("group", 123).at(456).TEXT("hello")
await onebot12.Send.To("group", 123).AT(456).text("hello")
```

### 不支援的方法呼叫

當呼叫不存在的方法時，適配器會返回友善的文本提示，而不是拋出異常：

```python
# 呼叫不支援的方法
result = await onebot12.Send.To("user", 123).UnsupportedMethod("test")

# 返回的結果是傳送的文本訊息
# 消息內容: [不支援的傳送類型] 方法名: UnsupportedMethod, 參數: [args[0]: 'test']
```

### 基礎訊息類型

- `.Text(text: str)`：傳送純文字訊息
- `.Image(file: Union[str, bytes], filename: str = "image.png")`：傳送圖片訊息（支援 URL、Base64 或 bytes）
- `.Audio(file: Union[str, bytes], filename: str = "audio.ogg")`：傳送音訊訊息
- `.Voice(file: Union[str, bytes], filename: str = "voice.ogg")`：傳送語音訊息（Audio 的別名，相容 OneBot11）
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")`：傳送視訊訊息

### 鏈式修飾方法（返回 self 支援鏈式呼叫）

- `.At(user_id: Union[str, int])`：@使用者（可多次呼叫）
- `.AtAll()`：@全體成員
- `.Reply(message_id: Union[str, int])`：回覆訊息

### 原始訊息傳送

- `.Raw_ob12(message: Union[Dict, List[Dict]], **kwargs)`：傳送 OneBot12 原始格式訊息（符合命名規範）

### 其他訊息類型

- `.Sticker(file_id: str)`：傳送表情包/貼紙
- `.Location(latitude: float, longitude: float, title: str = "", content: str = "")`：傳送位置

### 管理功能

- `.Recall(message_id: Union[str, int])`：撤回訊息
- `.Edit(message_id: Union[str, int], content: Union[str, List[Dict]])`：編輯訊息
- `.Raw(message_segments: List[Dict])`：傳送原生 OneBot12 訊息段
- `.Batch(target_ids: List[str], message: Union[str, List[Dict]], target_type: str = "user")`：批量傳送訊息

## OneBot12 標準事件

OneBot12 適配器完全遵循 OneBot12 標準，事件格式無需轉換，直接提交至框架。

### 新增特性：原始事件類型欄位

符合 `standards/event-conversion.md` 規範，所有事件都會保留原始事件類型欄位 `onebot12_raw_type`：

```python
{
    "id": "event-id",
    "type": "message",              # 事件類型
    "onebot12_raw_type": "message", # 原始事件類型（與 type 相同）
    "detail_type": "private",
    "self": {"user_id": "bot-id"},
    "user_id": "user-id",
    "message": [{"type": "text", "data": {"text": "Hello"}}],
    "alt_message": "Hello",
    "time": 1234567890
}
```

### 訊息事件 (Message Events)

```python
# 私聊訊息
{
    "id": "event-id",
    "type": "message",
    "onebot12_raw_type": "message",
    "detail_type": "private",
    "self": {"user_id": "bot-id"},
    "user_id": "user-id",
    "message": [{"type": "text", "data": {"text": "Hello"}}],
    "alt_message": "Hello",
    "time": 1234567890
}

# 群聊訊息
{
    "id": "event-id",
    "type": "message",
    "onebot12_raw_type": "message",
    "detail_type": "group",
    "self": {"user_id": "bot-id"},
    "user_id": "user-id",
    "group_id": "group-id",
    "message": [{"type": "text", "data": {"text": "Hello group"}}],
    "alt_message": "Hello group",
    "time": 1234567890
}
```

### 通知事件 (Notice Events)

```python
# 群成員增加
{
    "id": "event-id",
    "type": "notice",
    "onebot12_raw_type": "notice",
    "detail_type": "group_member_increase",
    "self": {"user_id": "bot-id"},
    "group_id": "group-id",
    "user_id": "user-id",
    "operator_id": "operator-id",
    "sub_type": "approve",
    "time": 1234567890
}

# 群成員減少
{
    "id": "event-id",
    "type": "notice",
    "onebot12_raw_type": "notice",
    "detail_type": "group_member_decrease",
    "self": {"user_id": "bot-id"},
    "group_id": "group-id",
    "user_id": "user-id",
    "operator_id": "operator-id",
    "sub_type": "leave",
    "time": 1234567890
}
```

### 請求事件 (Request Events)

```python
# 好友請求
{
    "id": "event-id",
    "type": "request",
    "onebot12_raw_type": "request",
    "detail_type": "friend",
    "self": {"user_id": "bot-id"},
    "user_id": "user-id",
    "comment": "申請訊息",
    "flag": "request-flag",
    "time": 1234567890
}

# 群邀請請求
{
    "id": "event-id",
    "type": "request",
    "onebot12_raw_type": "request",
    "detail_type": "group",
    "self": {"user_id": "bot-id"},
    "group_id": "group-id",
    "user_id": "user-id",
    "comment": "申請訊息",
    "flag": "request-flag",
    "sub_type": "invite",
    "time": 1234567890
}
```

### 元事件 (Meta Events)

```python
# 生命週期事件
{
    "id": "event-id",
    "type": "meta_event",
    "onebot12_raw_type": "meta_event",
    "detail_type": "lifecycle",
    "self": {"user_id": "bot-id"},
    "sub_type": "enable",
    "time": 1234567890
}

# 心跳事件
{
    "id": "event-id",
    "type": "meta_event",
    "onebot12_raw_type": "meta_event",
    "detail_type": "heartbeat",
    "self": {"user_id": "bot-id"},
    "interval": 5000,
    "status": {"online": true},
    "time": 1234567890
}
```

## 配置選項

### 帳戶配置

每個帳戶獨立配置以下選項：

- `mode`: 該帳戶的執行模式 ("server" 或 "client")
- `server_path`: Server 模式下的 WebSocket 路徑
- `server_token`: Server 模式下的認證 Token（選用）
- `client_url`: Client 模式下要連線的 WebSocket 位址
- `client_token`: Client 模式下的認證 Token（選用）
- `enabled`: 是否啟用該帳戶
- `platform`: 平台識別，預設為 "onebot12"
- `implementation`: 實現識別，如 "go-cqhttp"（選用）

### 配置範例

```toml
[OneBotv12_Adapter.accounts.main]
mode = "server"
server_path = "/onebot12-main"
server_token = "main_token"
enabled = true
platform = "onebot12"
implementation = "go-cqhttp"

[OneBotv12_Adapter.accounts.backup]
mode = "client"
client_url = "ws://127.0.0.1:3002"
client_token = "backup_token"
enabled = true
platform = "onebot12"
implementation = "shinonome"

[OneBotv12_Adapter.accounts.test]
mode = "client"
client_url = "ws://127.0.0.1:3003"
enabled = false
```

### 預設配置

如果未配置任何帳戶，適配器會自動建立：

```toml
[OneBotv12_Adapter.accounts.default]
mode = "server"
server_path = "/onebot12"
enabled = true
platform = "onebot12"
```

## 傳送方法傳回值

### 訊息傳送方法
所有訊息傳送方法（如 `.Text()`, `.Image()`, `.Raw_ob12()` 等）均傳回一個 `asyncio.Task` 物件，可以直接 await 獲取傳送結果：

```python
task = await onebot12.Send.To("group", 123456).Text("Hello")
```

### 鏈式修飾方法
所有鏈式修飾方法（如 `.At()`, `.AtAll()`, `.Reply()`）均傳回 `self`，支援鏈式呼叫：

```python
# 組合使用多個修飾方法
await onebot12.Send.To("group", 123456).Reply("msg123").At(789).At(790).Text("文本")
```

## API 回應標準

適配器遵循 ErisPulse 標準化回應規範（`standards/api-response.md`）：

```python
# 成功回應
{
    "status": "ok",              // 必須：執行狀態
    "retcode": 0,                // 必須：回傳碼（0 表示成功）
    "data": {                     // 必須：回應資料
        "message_id": "123456",
        "time": 1632847927.599013
    },
    "message_id": "123456",       // 必須：訊息 ID（無則為空字串）
    "message": "",                // 必須：錯誤訊息（成功時為空）
    "echo": "1234",               // 可選：原樣回傳請求中的 echo
    "onebot12_raw": {...}        // 可選：原始回應資料
}

# 失敗回應
{
    "status": "failed",           // 必須：執行狀態
    "retcode": 10003,            // 必須：回傳碼（非 0 表示失敗）
    "data": None,                // 必須：失敗時為 null
    "message_id": "",            // 必須：失敗時為空字串
    "message": "缺少必要參數",    // 必須：錯誤描述
    "echo": "1234",              // 可選：原樣回傳請求中的 echo
    "onebot12_raw": {...}        // 可選：原始回應資料
}
```

### 錯誤碼規範

遵循 OneBot12 標準錯誤碼：

- **0**: 成功
- **1xxxx**: 動作請求錯誤
- **2xxxx**: 動作處理器錯誤
- **3xxxx**: 動作執行錯誤（33001 為網路超時）

### 多帳戶傳送語法

```python
# 帳戶選擇方法
await onebot12.Send.Using("main").To("group", 123456).Text("主帳戶訊息")
await onebot12.Send.Using("backup").To("group", 123456).Image("http://example.com/image.jpg")

# API 呼叫方式
await onebot12.call_api("send_message", account_id="main", 
    detail_type="group", group_id=123456, 
    content=[{"type": "text", "data": {"text": "Hello"}}])
```

## 非同步處理機制

OneBot12 適配器採用非同步非阻塞設計：

1. 訊息傳送不會阻斷事件處理迴圈
2. 多個並發傳送操作可以同時進行
3. API 回應能夠及時處理
4. WebSocket 連線保持活躍狀態
5. 多帳戶並發處理，每個帳戶獨立執行

## 錯誤處理

適配器提供完善的錯誤處理機制：

1. 網路連線異常自動重連（支援每個帳戶獨立重連，間隔 30 秒）
2. API 呼叫逾時處理（固定 30 秒逾時）
3. 訊息傳送失敗自動重試（最多 3 次重試）
4. 不支援的方法呼叫會返回友善的文本提示

## 事件處理增強

多帳戶模式下，所有事件都會自動新增帳戶資訊：

```python
{
    "type": "message",
    "onebot12_raw_type": "message",  // 原始事件類型
    "detail_type": "private",
    "self": {"user_id": "123456"},  // 發送事件的帳戶 ID（標準欄位）
    "platform": "onebot12",
    // ... 其他事件欄位
}
```

## 管理介面

```python
# 獲取所有帳戶資訊
accounts = onebot12.accounts

# 檢查帳戶連線狀態
connection_status = {
    account_id: connection is not None and not connection.closed
    for account_id, connection in onebot12.connections.items()
}

# 動態啟用/禁用帳戶（需要重啟適配器）
onebot12.accounts["test"].enabled = False
```

## OneBot12 標準特性

### 訊息段標準

OneBot12 使用標準化的訊息段格式：

```python
# 文字訊息段
{"type": "text", "data": {"text": "Hello"}}

# 圖片訊息段
{"type": "image", "data": {"file_id": "image-id"}}

# 提及訊息段
{"type": "mention", "data": {"user_id": "user-id", "user_name": "Username"}}

# 回覆訊息段
{"type": "reply", "data": {"message_id": "msg-id"}}
```

### API 標準

遵循 OneBot12 標準 API 規範：

- `send_message`: 傳送訊息
- `delete_message`: 撤回訊息
- `edit_message`: 編輯訊息
- `get_message`: 獲取訊息
- `get_self_info`: 獲取自身資訊
- `get_user_info`: 獲取使用者資訊
- `get_group_info`: 獲取群組資訊

## 最佳實踐

1. **配置管理**: 建議使用多帳戶配置，將不同用途的機器人分開管理
2. **錯誤處理**: 始終檢查 API 呼叫的回傳狀態
3. **訊息傳送**: 使用合適的訊息類型，避免傳送不支援的訊息
4. **連線監控**: 定期檢查連線狀態，確保服務可用性
5. **效能優化**: 批量傳送時使用 Batch 方法，減少網路開銷
6. **方法呼叫**: 推薦使用標準的大駝峰命名（如 `.Text()`），但也支援小寫形式以相容不同程式設計風格 (這種方式可能會不相容舊版本)



### Telegram 适配

﻿# Telegram 平台特性文件

TelegramAdapter 是基於 Telegram Bot API 建構的適配器，支援多種訊息類型與事件處理。

---

## 文件資訊

- 對應模組版本: 4.1.1
- 維護者: ErisPulse

## 基本資訊

- 平台簡介：Telegram 是一個跨平台的即時通訊軟體
- 適配器名稱：TelegramAdapter
- 支援的協定/API 版本：Telegram Bot API
- 會話類型映射：`private` → 發送時用 `user`，`group`/`supergroup` → `group`，`channel` → `channel`

## 支援的訊息發送類型

所有發送方法均透過鏈式語法實現，例如：
```python
from ErisPulse.Core import adapter
telegram = adapter.get("telegram")

await telegram.Send.To("user", user_id).Text("Hello World!")
```

### 基本發送方法

| 方法 | 說明 | 參數 |
|------|------|------|
| `.Text(text)` | 發送純文字訊息 | `text: str` |
| `.Face(emoji)` | 發送表情骰子 | `emoji: str`（如 🎲 🎯 🏀） |
| `.Markdown(text, content_type)` | 發送 Markdown 格式訊息 | `content_type` 預設 `"MarkdownV2"` |
| `.HTML(text)` | 發送 HTML 格式訊息 | `text: str` |
| `.Sticker(file)` | 發送貼紙 | `file: str (file_id/URL) \| bytes` |
| `.Location(lat, lng)` | 發送位置 | `latitude: float, longitude: float` |
| `.Venue(lat, lng, title, addr)` | 發送地點 | 含標題和地址 |
| `.Contact(phone, first, last)` | 發送聯絡人 | 含電話號碼和姓名 |

### 媒體發送方法

所有媒體方法支援 `bytes`（上傳）與 `str`（file_id / URL）兩種輸入：

| 方法 | 說明 |
|------|------|
| `.Image(file, caption, content_type)` | 發送圖片 |
| `.Video(file, caption, content_type)` | 發送影片 |
| `.Voice(file, caption)` | 發送語音 |
| `.Audio(file, caption, content_type)` | 發送音訊 |
| `.File(file, caption)` | 發送檔案 |
| `.Document(file, caption, content_type)` | File 的別名 |

### 訊息管理方法

| 方法 | 說明 |
|------|------|
| `.Edit(message_id, text, content_type)` | 編輯已有訊息 |
| `.Recall(message_id)` | 刪除指定訊息 |
| `.Forward(from_chat_id, message_id)` | 轉發訊息（保留來源） |
| `.CopyMessage(from_chat_id, message_id)` | 複製訊息（不帶來源） |
| `.AnswerCallback(callback_query_id, text, show_alert)` | 應答回調查詢 |

### 原始訊息發送

- `.Raw_ob12(message: List[Dict])`：發送 OneBot12 標準格式訊息
- `.Raw_json(json_str: str)`：發送原始 JSON 格式訊息

### 鏈式修飾方法

| 方法 | 說明 |
|------|------|
| `.At(user_id)` | @指定用戶（透過 Telegram entities 實現，可多次調用） |
| `.AtAll()` | @全體成員（發送 `@All` 文本） |
| `.Reply(message_id)` | 回覆指定訊息 |
| `.Keyboard(inline_keyboard)` | 設置內聯鍵盤（`list[list[dict]]`） |
| `.ProtectContent(protect)` | 保護內容（防止轉發和保存） |
| `.Silent(silent)` | 靜默發送（不通知用戶） |

### 發送範例

```python
# 基本文本發送
await telegram.Send.To("user", user_id).Text("Hello World!")

# 帶內聯鍵盤的訊息
from ErisPulse import sdk
telegram = sdk.adapter.get("telegram")
keyboard = [
    [{"text": "按鈕1", "callback_data": "btn1"}, {"text": "按鈕2", "callback_data": "btn2"}],
    [{"text": "訪問官網", "url": "https://example.com"}],
]
await telegram.Send.To("group", group_id).Keyboard(keyboard).Text("請選擇：")

# 媒體發送（URL 方式）
await telegram.Send.To("group", group_id).Image("https://example.com/image.jpg", caption="圖片")

# @用戶
await telegram.Send.To("group", group_id).At("6117725680").Text("你好！")

# 回覆 + 保護內容
await telegram.Send.To("group", group_id).Reply("12345").ProtectContent().Text("機密訊息")

# 靜默發送
await telegram.Send.To("group", group_id).Silent().Text("靜默通知")

# 應答回調查詢
await telegram.Send.AnswerCallback(callback_query_id, text="已處理", show_alert=False)

# OneBot12 組合訊息
ob12_message = [
    {"type": "text", "data": {"text": "複雜訊息："}},
    {"type": "mention", "data": {"user_id": "6117725680", "user_name": "使用者名稱"}},
    {"type": "reply", "data": {"message_id": "12345"}},
    {"type": "image", "data": {"file": "https://http.cat/200"}}
]
await telegram.Send.To("group", group_id).Raw_ob12(ob12_message)

# 發送貼紙
await telegram.Send.To("user", user_id).Sticker("CAACAgIAAxkBAA...")  # file_id

# 發送位置
await telegram.Send.To("user", user_id).Location(39.9042, 116.4074)
```

## 特有事件類型

Telegram 事件轉換遵循 OneBot12 標準，同時透過 `telegram_` 前綴提供平台擴展。

### 訊息事件 detail_type 映射

| Telegram chat.type | OneBot12 detail_type | 發送目標類型 |
|---|---|---|
| `private` | `private` | `user` |
| `group` | `group` | `group` |
| `supergroup` | `group` | `group` |
| `channel` | `channel` | `channel` |

### 特有事件類型

| detail_type | 說明 |
|---|---|
| `telegram_callback_query` | 回調查詢（內聯鍵盤按鈕點擊） |
| `telegram_inline_query` | 內聯查詢 |
| `telegram_chosen_inline_result` | 選擇的內聯結果 |
| `telegram_poll` | 投票事件 |
| `telegram_poll_answer` | 投票答案 |
| `telegram_my_chat_member` | Bot 自身成員狀態變更 |
| `telegram_chat_member` | 聊天成員變更 |
| `telegram_chat_join_request` | 加入聊天請求 |
| `telegram_shipping_query` | 運費查詢 |
| `telegram_pre_checkout_query` | 預付款查詢 |

### 標準訊息段類型

轉換後的訊息段使用 OneBot12 標準格式：

| 訊息段類型 | 說明 | data 字段 |
|---|---|---|
| `text` | 純文字（不含 @使用者名） | `text` |
| `mention` | @使用者（標準 OB12） | `user_id`, `user_name` |
| `reply` | 回覆引用 | `message_id`, `user_id` |
| `image` | 圖片 | `file_id`, `url` |
| `video` | 影片 | `file_id`, `url`, `duration`, `width`, `height` |
| `voice` | 語音 | `file_id`, `url`, `duration` |
| `audio` | 音訊 | `file_id`, `url`, `duration`, `title`, `performer` |
| `file` | 檔案 | `file_id`, `url`, `file_name`, `file_size`, `mime_type` |
| `location` | 位置 | `latitude`, `longitude`, 可選 `title`, `address` |

### 平台擴展訊息段

以 `telegram_` 前綴標識的擴展訊息段：

| 訊息段類型 | 說明 | data 字段 |
|---|---|---|
| `telegram_sticker` | 貼紙 | `file_id`, `emoji`, `sticker_type`, `url` |
| `telegram_animation` | GIF 動畫 | `file_id`, `url`, `duration`, `caption` |
| `telegram_contact` | 聯絡人 | `phone_number`, `first_name`, `last_name`, `user_id` |
| `telegram_inline_keyboard` | 內聯鍵盤 | `inline_keyboard` |

### 事件範例

#### 群聊訊息（含 @提及）
```python
{
  "type": "message",
  "detail_type": "group",
  "platform": "telegram",
  "user_id": "6117725680",
  "user_nickname": "WSu2059",
  "group_id": "-1002850921906",
  "message_id": "172",
  "message": [
    {"type": "text", "data": {"text": "/it.echo "}},
    {"type": "mention", "data": {"user_id": "", "user_name": "@nm123_91178"}}
  ],
  "alt_message": "/it.echo @nm123_91178",
  "telegram_chat": {
    "id": -1002850921906,
    "title": "ErisPulse",
    "username": "erispulse",
    "type": "supergroup"
  }
}
```

#### 回調查詢事件
```python
{
  "type": "notice",
  "detail_type": "telegram_callback_query",
  "user_id": "123456",
  "user_nickname": "YingXinche",
  "telegram_callback_id": "cb_123",
  "telegram_callback_data": "callback_data",
  "message_id": "msg_456"
}
```

#### 內聯查詢事件
```python
{
  "type": "request",
  "detail_type": "telegram_inline_query",
  "user_id": "789012",
  "user_nickname": "YingXinche",
  "telegram_query_id": "iq_789",
  "telegram_query_text": "search_text",
  "telegram_query_offset": "0"
}
```

#### 帶內聯鍵盤的訊息
```python
{
  "type": "message",
  "detail_type": "group",
  "message": [
    {"type": "text", "data": {"text": "請選擇："}},
    {
      "type": "telegram_inline_keyboard",
      "data": {
        "inline_keyboard": [
          [{"text": "按鈕1", "callback_data": "btn1"}],
          [{"text": "訪問", "url": "https://example.com"}]
        ]
      }
    }
  ]
}
```

## Event Mixin 擴展方法

適配器註冊了以下平台專有方法，僅在 `platform == "telegram"` 時可用：

### 訊息相關

| 方法 | 回傳類型 | 說明 |
|------|----------|------|
| `is_bot_message()` | `bool` | 判斷訊息是否來自機器人 |
| `is_edited_message()` | `bool` | 判斷是否為編輯過的訊息 |
| `is_topic_message()` | `bool` | 判斷是否為主題/Topic 訊息 |
| `get_update_id()` | `int` | 獲取 Telegram update ID |
| `get_chat_title()` | `str` | 獲取聊天標題 |
| `get_chat_username()` | `str` | 獲取聊天使用者名 |
| `get_forward_from()` | `dict` | 獲取轉發來源資訊 |
| `get_topic_id()` | `str` | 獲取主題 ID |

### 回調查詢相關

| 方法 | 回傳類型 | 說明 |
|------|----------|------|
| `get_callback_data()` | `str` | 獲取回調查詢的 callback_data |
| `get_callback_id()` | `str` | 獲取回調查詢 ID（用於應答） |

### 訊息段資料提取

| 方法 | 回傳類型 | 說明 |
|------|----------|------|
| `get_inline_keyboard()` | `list` | 獲取消息中的內聯鍵盤 |
| `get_sticker_info()` | `dict` | 獲取貼紙資訊 |
| `get_contact_info()` | `dict` | 獲取聯絡人資訊 |
| `get_location()` | `dict` | 獲取位置資訊 |

### 使用範例

```python
from ErisPulse.Core.Event import message, notice

@message.on_message()
async def handle_message(event):
    if event.get("platform") != "telegram":
        return

    # 訊息屬性
    if event.is_bot_message():
        return  # 忽略機器人訊息

    if event.is_edited_message():
        print("這是編輯過的訊息")

    # 聊天資訊
    title = event.get_chat_title()
    username = event.get_chat_username()

    # 轉發來源
    forward = event.get_forward_from()

    # 訊息段資料
    sticker = event.get_sticker_info()
    contact = event.get_contact_info()
    location = event.get_location()
    keyboard = event.get_inline_keyboard()

    # 主題
    if event.is_topic_message():
        topic_id = event.get_topic_id()

@notice.on_notice()
async def handle_notice(event):
    if event.get("platform") != "telegram":
        return

    if event.get("detail_type") == "telegram_callback_query":
        callback_data = event.get_callback_data()
        callback_id = event.get_callback_id()

        # 應答回調查詢
        telegram = sdk.adapter.get("telegram")
        await telegram.Send.AnswerCallback(callback_id, text="已點擊")

        # 回覆訊息
        await event.reply(f"你點擊了：{callback_data}")
```

## 擴展欄位說明

- 所有特有欄位均以 `telegram_` 前綴標識
- 保留原始資料在 `telegram_raw` 欄位
- 保留原始事件類型在 `telegram_raw_type` 欄位
- 頻道訊息使用 `detail_type="channel"`
- 私聊訊息使用 `detail_type="private"`（發送時需轉換為 `user`）
- 主題訊息包含 `thread_id` 欄位
- `@` 提及使用標準 `mention` 訊息段類型（`type: "mention"`），文本中不含 @使用者名

## 配置選項

Telegram 適配器支援多帳號配置：

### 配置範例
```toml
[Telegram_Adapter.accounts.default]
token = "YOUR_BOT_TOKEN"
enabled = true

[Telegram_Adapter.accounts.bot2]
token = "ANOTHER_BOT_TOKEN"
enabled = true
```

### 運行模式

Telegram 適配器僅支援 **Polling（輪詢）** 模式，Webhook 模式已移除。

### 代理配置

如需透過代理連線 Telegram API，請使用系統級代理（環境變數 `ALL_PROXY` / `HTTPS_PROXY`）。

### 舊版配置遷移

舊版單 token 配置會自動相容：
```toml
# 舊版格式（仍可使用，但建議遷移）
[Telegram_Adapter]
token = "YOUR_BOT_TOKEN"
```

建議遷移到新格式：
```toml
[Telegram_Adapter.accounts.default]
token = "YOUR_BOT_TOKEN"
enabled = true
```



### 云湖适配

# 雲湖平台特性文件

YunhuAdapter 是基於雲湖協議建構的適配器，整合了所有雲湖功能模組，提供統一的事件處理和訊息操作介面。

---

## 文件資訊

- 對應模組版本: 4.3.0
- 維護者: ErisPulse

## 基本資訊

- 平台簡介：雲湖（Yunhu）是一個企業級即時通訊平台
- 適配器名稱：YunhuAdapter
- 多帳戶支援：支援透過 bot_id 識別並設定多個雲湖機器人帳戶
- 鏈式修飾支援：支援 `.Reply()` 等鏈式修飾方法
- OneBot12 兼容：支援發送 OneBot12 格式訊息

## 支援的消息傳送類型

所有傳送方法均透過鏈式語法實現，例如：
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("user", user_id).Text("Hello World!")
```

支援的傳送類型包括：
- `.Text(text: str)`：傳送純文字訊息。
- `.Html(html: str)`：傳送HTML格式訊息。
- `.Markdown(markdown: str)`：傳送Markdown格式訊息。
- `.A2UI(text: str)`：傳送A2UI格式訊息。
- `.Image(file: bytes, stream: bool = False, filename: str = None)`：傳送圖片訊息，支援流式上傳和自訂檔名。
- `.Video(file: bytes, stream: bool = False, filename: str = None)`：傳送影片訊息，支援流式上傳和自訂檔名。
- `.File(file: bytes, stream: bool = False, filename: str = None)`：傳送檔案訊息，支援流式上傳和自訂檔名。
- `.Batch(target_ids: List[str], message: str, content_type: str = "text", **kwargs)`：批量傳送訊息。
- `.Edit(msg_id: str, text: str, content_type: str = "text", buttons: List = None)`：編輯已有訊息。
- `.Recall(msg_id: str)`：撤回訊息。
- `.Board(content: str, content_type: str = "text")`：發布公告看板。作用域由 `To()` 推斷（指定目標=本地看板，未指定=全局看板）。鏈式修飾：`.Expire(duration)` 相對過期（秒）、`.ExpireAt(timestamp)` 絕對過期（秒級時間戳）、`.ForMember(member_id)` 群成員看板；**內容為空時自動轉為撤銷看板**。仍兼容舊式 `Board("local", "公告")` 显式 scope 寫法。
- `.DismissBoard()`：撤銷公告看板。作用域同樣由 `To()` 推斷，支援 `.ForMember(member_id)`；仍兼容舊式 `DismissBoard("local")` 寫法。
- `.Stream(content_type: str, content_generator: AsyncGenerator, **kwargs)`：傳送流式訊息。

### 群組管理方法

所有群組管理方法需要透過鏈式語法指定群組，例如：
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("group", group_id).Kick(user_id)
```

- `.Kick(user_id: str)`：移除群組成員。機器人需要`允許移除群組成員`權限。
- `.Ban(user_id: str, duration: int = 600)`：用戶禁言。`duration`為禁言時長（秒），0為解禁，-1為永久禁言。機器人需要`允許禁言用戶`權限。
- `.CreateTag(tag: str, color: str = None, desc: str = None, sort: int = None)`：建立群組標籤。`color`格式為#RRGGBB，`sort`越小越靠前。機器人需要`允許控制標籤組`權限。
- `.EditTag(tag: str, new_tag: str = None, color: str = None, desc: str = None, sort: int = None)`：修改群組標籤。各參數可選，不傳則不修改。機器人需要`允許控制標籤組`權限。
- `.DeleteTag(tag: str)`：刪除群組標籤。機器人需要`允許控制標籤組`權限。
- `.GetTagList()`：獲取群組標籤列表。回傳包含`list`陣列的回應資料。
- `.AddUserTag(user_id: str, tag: str)`：給用戶添加標籤。機器人需要`允許控制標籤組`權限。
- `.RemoveUserTag(user_id: str, tag: str)`：給用戶移除標籤。機器人需要`允許控制標籤組`權限。
- `.SetMsgTypeLimit(types: str)`：控制群組內訊息類型。`types`為訊息類型名稱，多個用逗號分隔（如`"text,image,video"`），空字串表示不限制。機器人需要`允許修改群組資訊`權限。

### 訊息查詢方法

獲取指定會話（用戶/群）的歷史訊息列表，需要透過鏈式語法指定目標，例如：
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

result = await yunhu.Send.To("group", group_id).GetMessages(before=10)
```

- `.GetMessages(message_id: str = None, before: int = None, after: int = None)`：獲取會話歷史訊息。回傳包含`list`陣列和`total`總數的回應資料。
  - `message_id`：訊息ID（可選）。不填時配合`before`回傳最近的N條訊息。
  - `before`：回傳指定訊息ID前N條。
  - `after`：回傳指定訊息ID後N條。
  - > **注意：** `before` 和 `after` 至少需指定一個且大於0，否則伺服器不會回傳任何訊息。

Board 作用域由 `To()` 自動推斷：
- 指定 `To(target_type, target_id)` → 本地看板（指定用戶/群組）
- 未指定 `To()` → 全局看板

```python
# 本地看板（60 秒後相對過期）
await yunhu.Send.To("group", group_id).Expire(60).Board("公告", content_type="markdown")

# 群成員看板（僅指定成員可見）
await yunhu.Send.To("group", group_id).ForMember(user_id).Board("僅你可見")

# 絕對時間戳過期
await yunhu.Send.To("group", group_id).ExpireAt(1785208268).Board("指定時間過期")

# 全局看板
await yunhu.Send.Board("全局公告")

# 清空本地看板（內容為空 → 自動撤銷）
await yunhu.Send.To("group", group_id).Board("")
```

### 按鈕參數說明

`buttons` 參數是一個嵌套列表，表示按鈕的佈局和功能。每個按鈕物件包含以下欄位：

| 欄位         | 類型   | 是否必填 | 說明                                                                 |
|--------------|--------|----------|----------------------------------------------------------------------|
| `text`       | string | 是       | 按鈕上的文字                                                         |
| `actionType` | int    | 是       | 動作類型：<br>`1`: 跳轉 URL<br>`2`: 複製<br>`3`: 點擊回報            |
| `url`        | string | 否       | 當 `actionType=1` 時使用，表示跳轉的目標 URL                         |
| `value`      | string | 否       | 當 `actionType=2` 時，該值會複製到剪貼簿<br>當 `actionType=3` 時，該值會發送給訂閱端 |

範例：
```python
buttons = [
    [
        {"text": "複製", "actionType": 2, "value": "xxxx"},
        {"text": "點擊跳轉", "actionType": 1, "url": "http://www.baidu.com"},
        {"text": "回報事件", "actionType": 3, "value": "xxxxx"}
    ]
]
await yunhu.Send.To("user", user_id).Buttons(buttons).Text("帶按鈕的訊息")
```
> **注意：**
> - 只有用戶點擊了**按鈕回報事件**的按鈕才會收到推送，**複製**和**跳轉URL**均無法收到推送。

### 鏈式修飾方法（可組合使用）

鏈式修飾方法回傳 `self`，支援鏈式呼叫，必須在最終傳送方法前呼叫：

- `.Reply(message_id: str)`：回覆指定訊息。
- `.At(user_id: str)`：@指定用戶。
- `.AtAll()`：@所有人。
- `.Buttons(buttons: List)`：添加按鈕。

### 鏈式呼叫範例

```python
# 基礎傳送
await yunhu.Send.To("user", user_id).Text("Hello")

# 回覆訊息
await yunhu.Send.To("group", group_id).Reply(msg_id).Text("回覆訊息")

# 回覆 + 按鈕
await yunhu.Send.To("group", group_id).Reply(msg_id).Buttons(buttons).Text("帶回覆和按鈕的訊息")
```

### 群組管理範例

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# 移除群組成員
await yunhu.Send.To("group", group_id).Kick(user_id)

# 用戶禁言（10分鐘）
await yunhu.Send.To("group", group_id).Ban(user_id, duration=600)

# 解除禁言
await yunhu.Send.To("group", group_id).Ban(user_id, duration=0)

# 永久禁言
await yunhu.Send.To("group", group_id).Ban(user_id, duration=-1)

# 建立群組標籤
await yunhu.Send.To("group", group_id).CreateTag("VIP用戶", color="#FF5733", desc="VIP會員")

# 修改群組標籤
await yunhu.Send.To("group", group_id).EditTag("VIP用戶", new_tag="SVIP用戶", color="#33C4FF")

# 刪除群組標籤
await yunhu.Send.To("group", group_id).DeleteTag("VIP用戶")

# 獲取群組標籤列表
result = await yunhu.Send.To("group", group_id).GetTagList()

# 給用戶添加標籤
await yunhu.Send.To("group", group_id).AddUserTag(user_id, "VIP用戶")

# 移除用戶標籤
await yunhu.Send.To("group", group_id).RemoveUserTag(user_id, "VIP用戶")

# 設定訊息類型限制
await yunhu.Send.To("group", group_id).SetMsgTypeLimit("text,image,video")

# 取消訊息類型限制
await yunhu.Send.To("group", group_id).SetMsgTypeLimit("")
```

### 訊息查詢範例

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# 獲取群組最近10條訊息（共回傳10條）
result = await yunhu.Send.To("group", group_id).GetMessages(before=10)

# 獲取群組中指定訊息ID前10條（共回傳11條）
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10)

# 獲取群組中指定訊息ID前后各10條（共回傳21條）
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10, after=10)

# 獲取用戶會話歷史訊息
result = await yunhu.Send.To("user", user_id).GetMessages(message_id="msg_xxx", before=10)
```

### OneBot12訊息支援

適配器支援傳送 OneBot12 格式的訊息，便於跨平台訊息相容：

- `.Raw_ob12(message: List[Dict], **kwargs)`：傳送 OneBot12 格式訊息。

```python
# 發送 OneBot12 格式訊息
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu.Send.To("user", user_id).Raw_ob12(ob12_msg)

# 配合鏈式修飾
ob12_msg = [{"type": "text", "data": {"text": "回覆訊息"}}]
await yunhu.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)
```

## 標準 API 動作（ApiDSL）

> [!NOTE]  
> 本特性需要 ErisPulse **2.7.0+** 且 YunhuAdapter **4.3.0+**。

除了 `Send` 鏈式發送，適配器還提供 `Api` 內部類，暴露 OneBot12 標準 API 動作與雲湖平台擴展動作。所有方法返回標準響應格式。

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# 信息查詢（透過公開 Web API，無需鑑權）
result = await yunhu.Api.get_self_info()              # 機器人自身資訊
result = await yunhu.Api.get_user_info("7058262")     # 任意使用者資訊
result = await yunhu.Api.get_group_info("635409929")  # 群資訊

# 檔案操作
result = await yunhu.Api.upload_file(type="path", name="a.png", path="./a.png")
result = await yunhu.Api.get_file("https://chat-file.jwznb.com/xxx")

# 撤回訊息（需額外提供 chat_id + chat_type）
await yunhu.Api.delete_message("msg_id", chat_id="123", chat_type="group")

# 多帳號：指定 Bot 帳號
info = await yunhu.Api.Using("bot1").get_self_info()
```

### 支援的標準動作

| 方法 | 說明 | 資料來源 |
|------|------|---------|
| `get_self_info()` | 機器人自身資訊 | 公開 Web API（bot-info） |
| `get_user_info(user_id)` | 使用者資訊（任意使用者可查） | 公開 Web API（user/homepage） |
| `get_group_info(group_id)` | 群資訊 | 公開 Web API（group-info） |
| `upload_file(*, type, name, ...)` | 上傳檔案（自動判定 image/video/file） | Bot 開放 API |
| `get_file(file_id)` | 獲取檔案（file_id 即 URL） | — |
| `delete_message(message_id, *, chat_id, chat_type)` | 撤回訊息 | Bot 開放 API（/bot/recall） |

> **注意**：`get_self_info` / `get_user_info` / `get_group_info` 透過**非官方公開 Web API**（chat-web-go.jwzhd.com）實現，這些介面無需鑑權但非官方文件、可能隨平台更新變動；失敗時返回標準錯誤響應。

### 不支援的標準動作

以下標準動作雲湖無對應 API，呼叫時返回 `retcode=10002`（不支援的操作）：
- `get_friend_list`（Bot 開放 API 的"機器人使用者列表"尚在待上線狀態）
- `get_group_list` / `get_group_member_info` / `get_group_member_list`
- `set_group_name` / `leave_group`

### 平台擴展動作

透過 `Api.call("yunhu.xxx", **params)` 呼叫雲湖特有動作（參數採用 OB12 風格命名，適配器自動翻譯為雲湖欄位）：

| 擴展動作 | 說明 | 等價 Send 方法 |
|---------|------|---------------|
| `yunhu.recall` | 撤回訊息（msg_id, chat_id, chat_type） | `Send.To(...).Recall(msg_id)` |
| `yunhu.kick` | 移除群成員（group_id, user_id） | `Send.To("group", g).Kick(uid)` |
| `yunhu.ban` | 禁言（group_id, user_id, duration） | `Send.To("group", g).Ban(uid, duration)` |
| `yunhu.unban` | 解除禁言（group_id, user_id） | `Send.To("group", g).Ban(uid, duration=0)` |
| `yunhu.tag.create/edit/delete/list` | 群標籤 CRUD（group_id, ...） | `Send.To("group", g).CreateTag(...)` 等 |
| `yunhu.tag.relate` / `yunhu.tag.relate_cancel` | 給使用者添加/移除標籤 | `Send.To("group", g).AddUserTag(...)` 等 |
| `yunhu.set_member_title` / `yunhu.unset_member_title` | **成員頭銜語義別名**（標籤≈頭銜，內部映射到 tag.relate） | — |
| `yunhu.msg_type_limit` | 群訊息類型限制（group_id, type） | `Send.To("group", g).SetMsgTypeLimit(...)` |
| `yunhu.get_messages` | 獲取歷史訊息（chat_id, chat_type, message_id?, before?, after?） | `Send.To(...).GetMessages(...)` |
| `yunhu.bot_info` | 公開 bot-info 查詢（bot_id） | — |
| `yunhu.user_homepage` | 公開使用者主頁查詢（user_id） | — |

```python
# 平台擴展示例
await yunhu.Api.call("yunhu.kick", group_id="123", user_id="456")
await yunhu.Api.call("yunhu.set_member_title", group_id="123", user_id="456", title="VIP")
result = await yunhu.Api.call("yunhu.get_messages", chat_id="123", chat_type="group", before=10)
```

> **標籤與頭銜**：雲湖的"標籤"語義等同 OneBot12 群成員 `title`。`yunhu.set_member_title` 是 `yunhu.tag.relate` 的原生語義別名，二者內部映射到同一端點。群訊息事件中發送者角色由 `senderUserLevel` 映射到標準 `role` 欄位（owner/admin/member）。

## 發送方法返回值

所有發送方法均返回一個 Task 對象，可以直接 await 獲取發送結果。返回結果遵循 ErisPulse 适配器标准化返回规范：

```python
{
    "status": "ok",           // 執行狀態
    "retcode": 0,             // 返回碼
    "data": {...},            // 回應資料
    "self": {...},            // 自身資訊（包含 bot_id）
    "message_id": "123456",   // 消息ID
    "message": "",            // 錯誤資訊
    "yunhu_raw": {...}        // 原始回應資料
}
```

## 特有事件類型

需要 `platform=="yunhu"` 檢測再使用本平台特性

### 核心差異點

1. 特有事件類型：
    - 表單（如表單指令）：yunhu_form
    - 表情包/貼紙訊息段：yunhu_expression
    - 按鈕點擊：yunhu_button_click
    - A2UI按鈕點擊：yunhu_a2ui_button
    - 機器人設定：yunhu_bot_setting
    - 快捷選單：yunhu_shortcut_menu
2. 標準欄位擴展（4.3.0+）：
    - 訊息事件新增標準 `role` 欄位（由雲湖 `senderUserLevel` 映射為 `owner`/`admin`/`member`）
    - 新增 `user_avatar` 欄位（發送者頭像 URL）
3. 擴展欄位：
    - 所有特有欄位均以 `yunhu_` 前綴標識
    - 保留原始資料在 `yunhu_raw` 欄位
    - 私聊中 `self.user_id` 表示機器人 ID

### 特殊欄位示例

```python
# 表單命令
{
  "type": "message",
  "detail_type": "private",
  "yunhu_command": {
    "name": "表單指令名",
    "id": "指令ID",
    "form": {
      "字段ID1": {
        "id": "字段ID1",
        "type": "input/textarea/select/radio/checkbox/switch",
        "label": "字段標籤",
        "value": "字段值"
      }
    }
  }
}

# 按鈕事件
{
  "type": "notice",
  "detail_type": "yunhu_button_click",
  "user_id": "點擊按鈕的用戶ID",
  "user_nickname": "用戶暱稱",
  "message_id": "訊息ID",
  "yunhu_button": {
    "id": "按鈕ID（可能為空）",
    "value": "按鈕值"
  }
}

# A2UI按鈕事件
{
  "type": "notice",
  "detail_type": "yunhu_a2ui_button",
  "user_id": "操作用戶ID",
  "user_nickname": "用戶暱稱",
  "message_id": "訊息ID",
  "yunhu_a2ui": {
    "recv_id": "接收者ID",
    "recv_type": "接收者類型",
    "action_name": "操作名稱",
    "source_component_id": "來源組件ID",
    "form_context": {},
    "interaction_json": "互動資料JSON字串"
  }
}

### 按鈕點擊事件處理示例

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_yunhu_notice(event):
    """處理雲湖通知事件

    使用通用的 on_notice() 裝飾器來處理所有通知事件，
    然後透過 detail_type 區分不同類型的通知
    event.reply() 會自動透過雲湖平台回覆
    """

# 檢查是否是按鈕點擊事件
    if event.get("detail_type") == "yunhu_button_click":
        user_id = event.get_user_id()
        user_nickname = event.get_user_nickname()
        button_value = event.get("yunhu_button", {}).get("value", "")

        print(f"用戶 {user_nickname}({user_id}) 點擊了按鈕: {button_value}")

# 使用 event.reply() 自動回覆（會根據平台自動選擇正確的發送方式）
        if button_value == "confirm":
            await event.reply("你點擊了確認按鈕！")
        elif button_value == "cancel":
            await event.reply("操作已取消")
        else:
            await event.reply(f"收到你的選擇: {button_value}")

# 處理快捷選單事件
    elif event.get("detail_type") == "yunhu_shortcut_menu":
        menu_id = event.get("yunhu_menu", {}).get("id", "")
        await event.reply(f"觸發了快捷選單: {menu_id}")

# 處理機器人設定變更
    elif event.get("detail_type") == "yunhu_bot_setting":
        settings = event.get("yunhu_setting", {})
        await event.reply(f"設定已更新: {settings}")

# 處理A2UI按鈕事件
    elif event.get("detail_type") == "yunhu_a2ui_button":
        a2ui = event.get("yunhu_a2ui", {})
        action_name = a2ui.get("action_name", "")
        form_context = a2ui.get("form_context", {})
        await event.reply(f"A2UI操作: {action_name}, 表單數據: {form_context}")
```

### 使用鏈式呼叫傳送帶按鈕訊息

```python
from ErisPulse import sdk

yunhu = sdk.adapter.get("yunhu")

buttons = [
    [
        {"text": "確認", "actionType": 3, "value": "confirm"},
        {"text": "取消", "actionType": 3, "value": "cancel"},
        {"text": "檢視詳細", "actionType": 1, "url": "http://example.com/detail"}
    ]
]

# 發送帶按鈕的消息到群組  
await yunhu.Send.To("group", "123456").Buttons(buttons).Text("請確認以下操作")

# 發送帶按鈕的消息到用戶私聊  
await yunhu.Send.To("user", "789").Buttons(buttons).Text("請選擇你的偏好設置")  

### 發送A2UI消息  

```python  
from ErisPulse import sdk  

yunhu = sdk.adapter.get("yunhu")  
```

# 發送 A2UI 消息  
await yunhu.Send.To("user", user_id).A2UI("A2UI 交互卡片內容")  

```
# 機器人設置  
{
  "type": "notice",
  "detail_type": "yunhu_bot_setting",
  "group_id": "群組 ID（可能為空）",
  "user_nickname": "用戶暱稱",
  "yunhu_setting": {
    "設置項 ID": {
      "id": "設置項 ID",
      "type": "input/radio/checkbox/select/switch",
      "value": "設置值"
    }
  }
}

# 快捷菜單  
{
  "type": "notice",
  "detail_type": "yunhu_shortcut_menu",
  "user_id": "觸發菜單的用戶 ID",
  "user_nickname": "用戶暱稱",
  "group_id": "群組 ID（如果是群聊）",
  "yunhu_menu": {
    "id": "菜單 ID",
    "type": "菜單類型(整數)",
    "action": "菜單動作(整數)"
  }
}
```

## Event Mixin 扩展方法

適配器註冊了以下平台專有方法，僅在 `platform == "yunhu"` 時可用：

| 方法 | 返回類型 | 說明 |
|------|----------|------|
| `get_raw_event()` | `dict` | 獲取雲湖原始事件數據（`yunhu_raw`） |
| `get_sender_level()` | `str` | 發送者雲湖原生級別（owner/administrator/member/unknown） |
| `get_sender_role()` | `str` | 發送者 OneBot12 標準 role（owner/admin/member） |
| `get_sender_title()` | `str` | 發送者頭銜（標準 `title` 字段訪問器，預留） |
| `get_sender_avatar()` | `str` | 發送者頭像 URL |
| `get_command()` | `dict` | 指令數據（僅指令消息事件，`yunhu_command`） |
| `get_button_value()` | `str` | 按鈕點擊事件的 value（`yunhu_button.value`） |
| `get_a2ui_action()` | `str` | A2UI 按鈕事件的 actionName |
| `get_a2ui_form_context()` | `dict` | A2UI 按鈕事件的表單上下文 |
| `get_menu_id()` | `str` | 快捷菜單事件 ID（`yunhu_menu.id`） |
| `get_setting()` | `dict` | 機器人設定事件的設定數據（`yunhu_setting`） |
| `is_command_message()` | `bool` | 是否為指令消息 |
| `is_button_click()` | `bool` | 是否為按鈕點擊事件 |
| `is_a2ui_button()` | `bool` | 是否為 A2UI 按鈕事件 |

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_yunhu_notice(event):
    if event.get("platform") != "yunhu":
        return

    if event.is_button_click():
        value = event.get_button_value()
        await event.reply(f"你點擊了按鈕: {value}")

    if event.get("detail_type") == "yunhu_shortcut_menu":
        menu_id = event.get_menu_id()
```

## 扩展字段說明

- 所有特有字段均以 `yunhu_` 前綴標識，避免與標準字段衝突
- 保留原始數據在 `yunhu_raw` 字段，便於訪問雲湖平台的完整原始數據
- `self.user_id` 表示機器人ID（從配置中的bot_id獲取）
- 表單指令通過 `yunhu_command` 字段提供結構化數據
- 按鈕點擊事件通過 `yunhu_button` 字段提供按鈕相關資訊
- A2UI按鈕事件通過 `yunhu_a2ui` 字段提供A2UI互動相關資訊
- 機器人設置變更通過 `yunhu_setting` 字段提供設置項數據
- 快捷菜單操作通過 `yunhu_menu` 字段提供菜單相關資訊
- 表情包/貼紙消息通過 `yunhu_expression` 消息段提供貼紙數據（sticker_id、貼紙包ID、圖片尺寸等）

### 表情包/貼紙消息段 (yunhu_expression)

當用戶發送表情包或貼紙時，消息段類型為 `yunhu_expression`：

```json
{
  "type": "yunhu_expression",
  "data": {
    "sticker_id": "35154",
    "sticker_pack_id": "1670",
    "expression_id": "0",
    "image_name": "sticker/fabb9077f2ba302402ea871cab3686ad7a3fc52c.gif",
    "width": 500,
    "height": 500
  }
}
```

| 字段 | 類型 | 說明 |
|------|------|------|
| `sticker_id` | string | 貼紙唯一標識 |
| `sticker_pack_id` | string | 貼紙包ID |
| `expression_id` | string | 表情ID |
| `image_name` | string | 表情圖片文件路徑 |
| `width` | int | 圖片寬度（可選） |
| `height` | int | 圖片高度（可選） |

使用示例：
```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event.get_platform() == "yunhu":
        for segment in event.get("message", []):
            if segment.get("type") == "yunhu_expression":
                data = segment["data"]
                print(f"收到表情包: sticker_id={data['sticker_id']}, 包ID={data['sticker_pack_id']}")
```

## 多Bot配置

### 配置說明

雲湖適配器支援同時配置和運行多個雲湖機器人帳戶。

```toml
# config.toml
[Yunhu_Adapter.accounts.bot1]
token = "your_bot1_token"  # 機器人token（必填）
mode = "ws"  # 接收模式（可選，預設為"ws"，可選值："ws"、"webhook"）
webhook_path = "/webhook/bot1"  # Webhook路徑（可選，預設為"/webhook"）
enabled = true  # 是否啟用（可選，預設為true）

[Yunhu_Adapter.accounts.bot2]
token = "your_bot2_token"  # 第二個機器人的token
webhook_path = "/webhook/bot2"  # 獨立的webhook路徑
enabled = true
```

**配置項說明：**
- `token`：雲湖平台提供的API token（必填）
- `mode`：接收模式（可選，預設為 `"ws"`，可選值 `"ws"`、`"webhook"`）
- `webhook_path`：接收雲湖事件的HTTP路徑（可選，預設為"/webhook"，僅 webhook 模式使用）
- `enabled`：是否啟用該帳戶（可選，預設為true）

**重要提示：**
1. 雲湖平台的機器人ID在**運行時自動檢測**，無需在配置中指定
2. webhook 模式下每個bot都應該有獨立的`webhook_path`，以便接收各自的webhook事件
3. 在雲湖平台配置webhook時，請為每個bot配置對應的URL，例如：
   - Bot1: `https://your-domain.com/webhook/bot1`
   - Bot2: `https://your-domain.com/webhook/bot2`

### 使用Send DSL指定Bot

可以透過`Using()`方法指定使用哪個bot發送訊息。該方法支援兩種參數：
- **帳戶名**：配置中的 bot 名稱（如 `bot1`, `bot2`）
- **bot_id**：配置中的 `bot_id` 值

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# 使用帳戶名發送訊息
await yunhu.Send.Using("bot1").To("user", "user123").Text("Hello from bot1!")

# 使用 bot_id 發送訊息（自動匹配對應帳戶）
await yunhu.Send.Using("30535459").To("group", "group456").Text("Hello from bot!")

# 不指定時使用第一個啟用的bot
await yunhu.Send.To("user", "user123").Text("Hello from default bot!")
```

> **提示：** 使用 `bot_id` 時，系統會自動查找配置中匹配的帳戶。這在處理事件回覆時特別有用，可以直接使用 `event["self"]["user_id"]` 來回覆同一帳戶。

### 事件中的Bot標識

接收到的事件會自動包含對應的`bot_id`資訊：

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu":
        # 獲取觸發事件的機器人ID
        bot_id = event["self"]["user_id"]
        print(f"訊息來自Bot: {bot_id}")
        
        # 使用相同bot回覆訊息
        yunhu = adapter.get("yunhu")
        await yunhu.Send.Using(bot_id).To(
            event["detail_type"],
            event["user_id"] if event["detail_type"] == "private" else event["group_id"]
        ).Text("回覆訊息")
```

### 日誌資訊

適配器會在日誌中自動包含 `bot_id` 資訊，便於除錯和追蹤：

```
[INFO] [yunhu] [bot:30535459] 收到來自使用者 user123 的私聊訊息
[INFO] [yunhu] [bot:12345678] 訊息發送成功，message_id: abc123
```

### 管理介面

```python
# 獲取所有帳戶資訊
bots = yunhu.bots

# 檢查帳戶是否啟用
bot_status = {
    bot_name: bot_config.enabled
    for bot_name, bot_config in yunhu.bots.items()
}

# 動態啟用/禁用帳戶（需要重啟適配器）
yunhu.bots["bot1"].enabled = False
```

### 舊配置相容

舊版 `[Yunhu_Adapter.bots.*]` 配置（含 `bot_id` 字段）會自動遷移至 `accounts` 格式（`bot_id` 已改為運行時自動檢測，配置中的值會被忽略）；建議儘快遷移至新格式。



### 邮件适配

# 郵件平台特性文件

EmailAdapter 是基於 SMTP/IMAP 協議的郵件適配器，支援郵件發送、接收和處理。

---

## 文件資訊

- 對應模組版本: 4.1.0
- 維護者: ErisPulse

## 基本資訊

- 平台簡介：透過標準 SMTP/IMAP 協議收發郵件的通用適配器
- 適配器名稱：EmailAdapter
- 多帳戶支援：支援同時配置多個郵箱帳戶
- 連接方式：IMAP 長輪詢接收 + SMTP 發送
- 認證方式：郵箱地址 + 密碼/授權碼
- OneBot12 兼容：支援發送 OneBot12 格式訊息

## 配置說明

### 全局配置（EmailAdapter）

| 配置項 | 類型 | 默認值 | 說明 |
|--------|------|--------|------|
| `imap_server` | str | `imap.example.com` | 默認 IMAP 伺服器地址 |
| `imap_port` | int | `993` | 默認 IMAP 端口 |
| `smtp_server` | str | `smtp.example.com` | 默認 SMTP 伺服器地址 |
| `smtp_port` | int | `465` | 默認 SMTP 端口 |
| `ssl` | bool | `true` | 是否默認啟用 SSL |
| `timeout` | int | `30` | 默認連接超時（秒） |
| `poll_interval` | int | `60` | IMAP 輪詢間隔（秒） |
| `max_retries` | int | `3` | 連接失敗最大重試次數 |

### 帳戶配置（EmailAdapter.accounts）

每個帳戶對應一個獨立郵箱。帳戶級配置優先於全局配置。

```toml
[EmailAdapter.accounts.default]
email = "user@example.com"
password = "your-password-or-auth-code"
imap_server = "imap.example.com"    # 可選，留空使用全局默認
imap_port = 993                      # 可選
smtp_server = "smtp.example.com"    # 可選
smtp_port = 465                      # 可選
ssl = true                           # 可選
timeout = 30                         # 可選
enabled = true

[EmailAdapter.accounts.backup]
email = "backup@example.com"
password = "another-password"
enabled = true
```

## 支援的消息發送類型

所有發送方法均透過鏈式語法實現：

```python
from ErisPulse.Core import adapter
mail = adapter.get("email")

# 簡單純文字郵件
await mail.Send.To("private", "to@example.com").Subject("測試").Text("內容")

# 帶附件的 HTML 郵件
await mail.Send.To("private", "to@example.com") \
    .Subject("HTML郵件") \
    .Cc(["cc1@example.com", "cc2@example.com"]) \
    .Attachment("report.pdf") \
    .Html("<h1>HTML內容</h1>")

# 使用 Raw_ob12 發送標準 OB12 消息
await mail.Send.To("private", "to@example.com").Raw_ob12([
    {"type": "text", "data": {"text": "郵件正文"}},
    {"type": "file", "data": {"file": "/path/to/attachment.pdf"}},
])

# 指定發送帳戶（多帳戶）
await mail.Send.Using("default").To("private", "to@example.com").Text("內容")
```

> 注意：使用鏈式語法時，參數方法（Subject / Cc / Attachment 等）必須在發送方法（Text / Html / Raw_ob12）之前調用。

### 基礎發送方法

| 方法 | 說明 |
|------|------|
| `.Text(text: str)` | 發送純文字郵件 |
| `.Html(html: str)` | 發送 HTML 格式郵件 |
| `.Raw_ob12(message, **kwargs)` | 發送 OneBot12 格式消息 |

### 鏈式修飾方法（返回 self，可組合使用）

| 方法 | 說明 |
|------|------|
| `.Subject(subject: str)` | 設定郵件主題 |
| `.Cc(emails: Union[str, List[str]])` | 設定抄送地址 |
| `.Bcc(emails: Union[str, List[str]])` | 設定密送地址 |
| `.ReplyTo(email: str)` | 設定回覆地址 |
| `.Attachment(file, filename: str = None)` | 添加附件 |

### OB12 消息段反向轉換（Raw_ob12）

| OB12 消息段 | 轉換為郵件內容 |
|------------|--------------|
| `text` | 純文字正文 |
| `image` | 圖片附件 |
| `video` | 影片附件 |
| `file` | 檔案附件 |
| `audio` | 音訊附件 |
| `markdown` | 轉為 HTML 正文 |

## 特有事件類型

### 核心差異點

1. 郵件事件均為 `message` 類型，`detail_type` 固定為 `private`
2. `user_id` 為發件人**純郵箱地址**，`user_nickname` 為發件人顯示名
3. `message` 消息段為標準 OB12 格式（text 段 + file 段）
4. 郵件主題透過 `email_subject` 擴展欄位獲取
5. 完整原始資料保留在 `email_raw` 欄位中

### 新郵件事件（email_new）

```json
{
  "id": "<message-id@example.com>",
  "time": 1751990446,
  "type": "message",
  "detail_type": "private",
  "platform": "email",
  "self": {
    "platform": "email",
    "user_id": "bot@example.com"
  },
  "message": [
    {
      "type": "text",
      "data": {
        "text": "郵件正文內容"
      }
    }
  ],
  "alt_message": "郵件主題",
  "user_id": "sender@example.com",
  "user_nickname": "Saber"
}
```

### 帶附件的郵件

```json
{
  "message": [
    {
      "type": "text",
      "data": {
        "text": "請查收附件"
      }
    },
    {
      "type": "file",
      "data": {
        "file_id": "document.pdf",
        "file_name": "document.pdf",
        "size": 102400
      }
    }
  ]
}
```

### 回覆郵件事件（email_reply）

當郵件包含 `References` 或 `In-Reply-To` 頭時，`email_raw_type` 為 `email_reply`：

```json
{
  "email_raw_type": "email_reply",
  "email_raw": {
    "references": "<original-msg-id@example.com>",
    "in_reply_to": "<original-msg-id@example.com>"
  }
}
```

## 扩展字段說明

| 欄位 | 類型 | 說明 |
|------|------|------|
| `email_raw` | dict | 完整原始郵件數據（subject/from/to/date/cc/bcc/text_content/html_content/attachments 等） |
| `email_raw_type` | str | 原始事件類型：`email_new`（新郵件）或 `email_reply`（回覆郵件） |
| `email_subject` | str | 郵件主題（便捷存取） |
| `email_from` | str | 寄件人純郵箱地址（便捷存取） |
| `attachments` | list | 附件數據列表（含二進位 `data` 欄位，向後相容） |

## 標準事件範例

### 完整郵件事件

```json
{
  "id": "<abc123@example.com>",
  "time": 1751990446,
  "type": "message",
  "detail_type": "private",
  "platform": "email",
  "self": {
    "platform": "email",
    "user_id": "bot@example.com"
  },
  "message": [
    {
      "type": "text",
      "data": {
        "text": "請查收附件"
      }
    },
    {
      "type": "file",
      "data": {
        "file_id": "document.pdf",
        "file_name": "document.pdf",
        "size": 102400
      }
    }
  ],
  "alt_message": "會議通知",
  "user_id": "sender@example.com",
  "user_nickname": "Sender",
  "email_subject": "會議通知",
  "email_from": "sender@example.com",
  "email_raw": {
    "subject": "會議通知",
    "from": "\"Sender\" <sender@example.com>",
    "to": "<bot@example.com>",
    "date": "Wed, 9 Jul 2026 02:00:46 +0800",
    "message_id": "<abc123@example.com>",
    "references": "",
    "in_reply_to": "",
    "cc": "",
    "bcc": "",
    "text_content": "請查收附件",
    "html_content": "<p>請查收附件</p>",
    "attachments": ["document.pdf"]
  },
  "email_raw_type": "email_new",
  "attachments": [
    {
      "filename": "document.pdf",
      "content_type": "application/pdf",
      "size": 102400,
      "data": "..."
    }
  ]
}
```

## 發送方法返回值

```json
{
  "status": "ok",
  "retcode": 0,
  "data": {
    "message_id": "<sent-msg-id@example.com>",
    "time": 1751990446
  },
  "message_id": "<sent-msg-id@example.com>",
  "message": "",
  "email_raw": {
    "success": true,
    "message": "Email sent successfully"
  }
}
```

## 事件處理示例

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_email(event):
    if event.get("platform") != "email":
        return
    # 發件人純郵箱地址
    sender = event["user_id"]              # sender@example.com
    
    # 發件人顯示名
    nickname = event.get("user_nickname")  # Sender
    
    # 郵件主題
    subject = event.get("email_subject")   # 會議通知
    
    # 純文字正文（第一個 text 段）
    text = event.get_text()
    
    # 完整原始數據
    raw = event.get("email_raw", {})
    html = raw.get("html_content", "")
    
    # 處理附件
    for seg in event.get("message", []):
        if seg["type"] == "file":
            filename = seg["data"]["file_name"]
            size = seg["data"]["size"]
    
    # 回覆郵件
    await event.reply(f"已收到：{subject}")
```



### Kook 适配

# Kook 平台特性文件

KookAdapter 是基於 Kook（開黑啦）Bot WebSocket 協議建構的適配器，整合了 Kook 所有功能模組，提供統一的事件處理和訊息操作介面。

---

## 文件資訊

- 對應模組版本: 0.1.0
- 維護者: ShanFish

## 基本資訊

- 平台簡介：Kook（原開黑啦）是一款支援文字、語音、視訊通訊的社群平台，提供完整的 Bot 開發介面
- 适配器名称：KookAdapter
- 多賬戶支援：支援同時配置多個 Kook 機器人
- 連接方式：WebSocket 長連接（通過 Kook 網關）
- 認證方式：基於 Bot Token 進行身份認證
- 鏈式修飾支援：支援 `.Reply()`、`.At()`、`.AtAll()` 等鏈式修飾方法
- OneBot12 兼容：支援發送 OneBot12 格式訊息

## 配置說明

KookAdapter 支援多帳戶配置，每個帳戶對應一個獨立的 Kook 机器人工。

```toml
# config.toml
# 帳戶1
[KookAdapter.accounts.default]
token = "YOUR_BOT_TOKEN"     # Kook Bot Token（必填，格式: Bot xxx/xxx）
bot_id = ""                   # Bot 用戶ID（可選，不填則從 token 中解析）
compress = true               # 是否啟用 WebSocket 壓縮（可選，預設為 true）
enabled = true                # 是否啟用（可選，預設為true）

# 帳戶2
[KookAdapter.accounts.bot2]
token = "ANOTHER_BOT_TOKEN"
bot_id = ""
enabled = true
```

> 兼容舊配置：若檢測到舊的單帳戶 `[KookAdapter]` 配置（含 token），會自動遷移為 `accounts.default`。

**配置項說明（每個帳戶）：**
- `token`：Kook Bot 的 Token（必填），從 [Kook開發者中心](https://developer.kookapp.cn) 獲取，格式為 `Bot xxx/xxx`
- `bot_id`：Bot 的用戶ID（可選），如果不填寫，適配器會嘗試從 token 中自動解析。建議手動填寫以確保準確性
- `compress`：是否啟用 WebSocket 數據壓縮（可選，預設為 `true`），啟用後使用 zlib 解壓數據
- `enabled`：是否啟用該帳戶（可選，預設為true）

**API環境：**
- Kook API 基礎地址：`https://www.kookapp.cn/api/v3`
- WebSocket 網關透過 API 動態獲取：`POST /gateway/index`

## 支援的消息傳送類型

所有傳送方法均透過鏈式語法實現，例如：
```python
from ErisPulse.Core import adapter
kook = adapter.get("kook")

await kook.Send.To("group", channel_id).Text("Hello World!")
```

支援的傳送類型包括：
- `.Text(text: str)`：傳送純文字訊息。
- `.Image(file: bytes | str)`：傳送圖片訊息，支援檔案路徑、URL、二進位資料。
- `.Video(file: bytes | str)`：傳送影片訊息，支援檔案路徑、URL、二進位資料。
- `.File(file: bytes | str, filename: str = None)`：傳送檔案訊息，支援檔案路徑、URL、二進位資料。
- `.Voice(file: bytes | str)`：傳送語音訊息，支援檔案路徑、URL、二進位資料。
- `.Markdown(text: str)`：傳送KMarkdown格式訊息。
- `.Card(card_data: dict)`：傳送卡片訊息（CardMessage）。
- `.Raw_ob12(message: List[Dict], **kwargs)`：傳送 OneBot12 格式訊息。

### 鏈式修飾方法（可組合使用）

鏈式修飾方法返回 `self`，支援鏈式呼叫，必須在最終傳送方法前呼叫：

- `.Reply(message_id: str)`：回覆（引用）指定訊息。
- `.At(user_id: str)`：@指定使用者，可多次呼叫以@多個使用者。
- `.AtAll()`：@所有人。

### 鏈式呼叫範例

```python
# 基礎傳送
await kook.Send.To("group", channel_id).Text("Hello")

# 回覆訊息
await kook.Send.To("group", channel_id).Reply(msg_id).Text("回覆訊息")

# @使用者
await kook.Send.To("group", channel_id).At("user_id").Text("你好")

# @多個使用者
await kook.Send.To("group", channel_id).At("user1").At("user2").Text("多使用者@")

# @全體
await kook.Send.To("group", channel_id).AtAll().Text("公告")

# 組合使用
await kook.Send.To("group", channel_id).Reply(msg_id).At("user_id").Text("複合訊息")
```

### OneBot12訊息支援

適配器支援傳送 OneBot12 格式的訊息，便於跨平台訊息相容：

```python
# 傳送 OneBot12 格式訊息
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await kook.Send.To("group", channel_id).Raw_ob12(ob12_msg)

# 配合鏈式修飾
ob12_msg = [{"type": "text", "data": {"text": "回覆訊息"}}]
await kook.Send.To("group", channel_id).Reply(msg_id).Raw_ob12(ob12_msg)

# 在 Raw_ob12 中使用 mention 和 reply 消息段
ob12_msg = [
    {"type": "text", "data": {"text": "Hello "}},
    {"type": "mention", "data": {"user_id": "user_id"}},
    {"type": "reply", "data": {"message_id": "msg_id"}}
]
await kook.Send.To("group", channel_id).Raw_ob12(ob12_msg)
```

### 額外操作方法

除了傳送訊息外，Kook 適配器還支援以下操作：

```python
# 編輯訊息（僅支援 KMarkdown type=9 和 CardMessage type=10）
await kook.Send.To("group", channel_id).Edit(msg_id, "**更新後的內容**")

# 撤回訊息
await kook.Send.To("group", channel_id).Recall(msg_id)

# 上傳檔案（取得檔案URL）
result = await kook.Send.Upload("C:/path/to/file.jpg")
file_url = result["data"]["url"]
```

## 發送方法返回值

所有發送方法均返回一個 Task 對象，可以直接 await 獲取發送結果。返回結果遵循 ErisPulse 适配器标准化返回规范：

```python
{
    "status": "ok",           // 執行狀態: "ok" 或 "failed"
    "retcode": 0,             // 返回碼（Kook API 的 code）
    "data": {...},            // 响应数据
    "message_id": "xxx",      // 消息ID
    "message": "",            // 錯誤信息
    "kook_raw": {...}         // 原始響應數據
}
```

### 錯誤碼說明

| retcode | 說明 |
|---------|------|
| 0 | 成功 |
| 40100 | Token 無效或未提供 |
| 40101 | Token 過期 |
| 40102 | Token 與 Bot 不匹配 |
| 40103 | 缺少權限 |
| 40000 | 參數錯誤 |
| 40400 | 目標不存在 |
| 40300 | 無權限操作 |
| 50000 | 伺服器內部錯誤 |
| -1 | 适配器內部錯誤 |

## 特有事件類型

需要 `platform=="kook"` 檢測再使用本平台特性

### 核心差異點

1. **頻道系統**：Kook 使用伺服器（Guild）和頻道（Channel）兩層結構，頻道是訊息的基本發送目標
2. **訊息類型**：Kook 支援文本(1)、圖片(2)、影片(3)、檔案(4)、語音(8)、KMarkdown(9)、卡片訊息(10)等多種訊息類型
3. **私信系統**：Kook 區分頻道訊息和私信訊息，使用不同的 API 端點
4. **訊息序號**：Kook WebSocket 使用 `sn` 序號保證訊息有序性，支援訊息暫存和亂序重排
5. **訊息編輯與撤回**：支援編輯已發送的訊息（僅 KMarkdown 和 CardMessage）和撤回訊息

### 擴展欄位

- 所有特有欄位均以 `kook_` 前綴標識
- 保留原始資料在 `kook_raw` 欄位
- `kook_raw_type` 標識原始 Kook 訊息類型編號（如 `1` 為文本、`255` 為通知事件）

### 特殊欄位範例

```python
# 頻道文本訊息
{
  "type": "message",
  "detail_type": "group",
  "user_id": "用戶ID",
  "group_id": "頻道ID",
  "channel_id": "頻道ID",
  "message_id": "訊息ID",
  "kook_raw": {...},
  "kook_raw_type": "1",
  "message": [
    {"type": "text", "data": {"text": "Hello"}}
  ],
  "alt_message": "Hello"
}

# 帶圖片的訊息
{
  "type": "message",
  "detail_type": "group",
  "user_id": "用戶ID",
  "group_id": "頻道ID",
  "channel_id": "頻道ID",
  "message_id": "訊息ID",
  "kook_raw": {...},
  "kook_raw_type": "2",
  "message": [
    {"type": "image", "data": {"file": "圖片URL", "url": "圖片URL"}}
  ],
  "alt_message": "圖片內容"
}

# KMarkdown訊息
{
  "type": "message",
  "detail_type": "group",
  "user_id": "用戶ID",
  "group_id": "頻道ID",
  "message_id": "訊息ID",
  "kook_raw": {...},
  "kook_raw_type": "9",
  "message": [
    {"type": "text", "data": {"text": "解析後的純文本"}}
  ]
}

# 卡片訊息
{
  "type": "message",
  "detail_type": "group",
  "user_id": "用戶ID",
  "group_id": "頻道ID",
  "message_id": "訊息ID",
  "kook_raw": {...},
  "kook_raw_type": "10",
  "message": [
    {"type": "json", "data": {"data": "卡片JSON內容"}}
  ]
}

# 私聊訊息
{
  "type": "message",
  "detail_type": "private",
  "user_id": "用戶ID",
  "message_id": "訊息ID",
  "kook_raw": {...},
  "kook_raw_type": "1",
  "message": [
    {"type": "text", "data": {"text": "私聊內容"}}
  ]
}
```

### 訊息段類型

Kook 的訊息類型根據 `type` 欄位自動轉換為對應訊息段：

| Kook type | 轉換類型 | 說明 |
|---|---|---|
| 1 | `text` | 文本訊息 |
| 2 | `image` | 圖片訊息 |
| 3 | `video` | 影片訊息 |
| 4 | `file` | 檔案訊息 |
| 8 | `record` | 語音訊息 |
| 9 | `text` | KMarkdown訊息（提取純文本內容） |
| 10 | `json` | 卡片訊息（原始JSON） |

訊息段結構範例：
```json
{
  "type": "image",
  "data": {
    "file": "圖片URL",
    "url": "圖片URL"
  }
}
```

### Mention訊息段

當訊息中包含@資訊時，會在訊息段前插入 `mention` 訊息段：

```json
{
  "type": "mention",
  "data": {
    "user_id": "被@用戶ID"
  }
}
```

### mention_all訊息段

當訊息為@全體時，會插入 `mention_all` 訊息段：

```json
{
  "type": "mention_all",
  "data": {}
}
```

## WebSocket 連接

### 連接流程

1. 使用 Bot Token 調用 `POST /gateway/index` 以獲取 WebSocket 網關地址
2. 連接到 WebSocket 網關
3. 收到 HELLO（s=1）信令，驗證連接狀態
4. 開始心跳循環（PING，s=2，每 30 秒一次）
5. 接收消息事件（s=0），使用 sn 序號以確保有序性
6. 收到心跳響應 PONG（s=3）

### 信令類型

| 信令 | s 值 | 說明 |
|------|-----|------|
| HELLO | 1 | 伺服器歡迎信令，連接成功後收到 |
| PING | 2 | 客戶端心跳，每 30 秒發送一次，攜帶當前 sn |
| PONG | 3 | 心跳響應 |
| RESUME | 4 | 恢復連接信令，攜帶 sn 以恢復會話 |
| RECONNECT | 5 | 伺服器要求重連，需要重新獲取網關 |
| RESUME_ACK | 6 | RESUME 成功響應 |

### 斷線重連

- 連接異常斷開後，適配器自動重試連接
- 如果之前有 `sn > 0`，會首先嘗試 RESUME（s=4）以恢復連接
- RESUME 失敗後，重置 sn 和訊息佇列，重新進行全新連接（HELLO 流程）
- 收到 RECONNECT（s=5）信令時，清除狀態並重新連接

### 消息序號機制

Kook WebSocket 使用 `sn`（遞增序號）以確保訊息有序性：

- 每收到一條訊息事件（s=0），sn 會遞增
- 如果收到的訊息 sn 不連續，則進入暫存模式
- 暫存區中的訊息按 sn 排序，等待缺失訊息到達後按序處理
- 暫存區清空後自動退出暫存模式

## 使用示例

### 處理頻道訊息

```python
from ErisPulse.Core.Event import message
from ErisPulse import sdk

kook = sdk.adapter.get("kook")

@message.on_message()
async def handle_group_msg(event):
    if event.get("platform") != "kook":
        return
    if event.get("detail_type") != "group":
        return

    text = event.get_text()
    channel_id = event.get("group_id")

    if text == "hello":
        await kook.Send.To("group", channel_id).Text("Hello!")
```

### 處理私聊訊息

```python
@message.on_message()
async def handle_private_msg(event):
    if event.get("platform") != "kook":
        return
    if event.get("detail_type") != "private":
        return

    text = event.get_text()
    user_id = event.get("user_id")

    await kook.Send.To("user", user_id).Text(f"你說了: {text}")
```

### 處理通知事件（表情回應等）

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_notice(event):
    if event.get("platform") != "kook":
        return

    sub_type = event.get("sub_type")

    if sub_type == "added_reaction":
        emoji = event.get("emoji", {})
        user_id = event.get("user_id")
        msg_id = event.get("message_id")
        print(f"用戶 {user_id} 對訊息 {msg_id} 添加了表情回應")

    elif sub_type == "deleted_reaction":
        emoji = event.get("emoji", {})
        user_id = event.get("user_id")
        msg_id = event.get("message_id")
        print(f"用戶 {user_id} 移除了訊息 {msg_id} 的表情回應")
```

### 發送媒體訊息

```python
# 發送圖片（URL）
await kook.Send.To("group", channel_id).Image("https://example.com/image.png")

# 發送圖片（二進位）
with open("image.png", "rb") as f:
    image_bytes = f.read()
await kook.Send.To("group", channel_id).Image(image_bytes)

# 發送影片
await kook.Send.To("group", channel_id).Video("https://example.com/video.mp4")

# 發送檔案
await kook.Send.To("group", channel_id).File("https://example.com/file.pdf", filename="document.pdf")

# 發送語音
await kook.Send.To("group", channel_id).Voice("https://example.com/voice.mp3")
```

### 發送KMarkdown和卡片訊息

```python
# KMarkdown
await kook.Send.To("group", channel_id).Markdown("**粗體** *斜體* [連結](https://example.com)")

# 卡片訊息
card = {
    "type": "card",
    "theme": "primary",
    "size": "lg",
    "modules": [
        {"type": "header", "text": {"type": "plain-text", "content": "標題"}},
        {"type": "section", "text": {"type": "kmarkdown", "content": "內容"}}
    ]
}
await kook.Send.To("group", channel_id).Card(card)
```

### 訊息編輯與撤回

```python
# 發送訊息
result = await kook.Send.To("group", channel_id).Markdown("**原始內容**")
msg_id = result["data"]["msg_id"]

# 編輯訊息（僅支援 KMarkdown 和 CardMessage）
await kook.Send.To("group", channel_id).Edit(msg_id, "**更新後的內容**")

# 撤回訊息
await kook.Send.To("group", channel_id).Recall(msg_id)
```

### 處理私訊訊息的編輯和刪除通知

```python
@notice.on_notice()
async def handle_private_notice(event):
    if event.get("platform") != "kook":
        return

    sub_type = event.get("sub_type")

    if sub_type == "updated_private_message":
        msg_id = event.get("message_id")
        content = event.get("content")
        print(f"私訊訊息已更新: {msg_id}, 新內容: {content}")

    elif sub_type == "deleted_private_message":
        msg_id = event.get("message_id")
        print(f"私訊訊息已刪除: {msg_id}")
```



### Matrix 适配

# Matrix平台特性文件

MatrixAdapter 是基於 [Matrix協議](https://spec.matrix.org/) 建構的適配器，整合了Matrix協議的所有核心功能模組，提供統一的事件處理和訊息操作介面。

---

## 文件資訊

- 對應模組版本: 4.1.0
- 維護者: ErisPulse

## 基本資訊

- 平台簡介：Matrix 是一個開放的去中心化通信協議，支援私聊、群組等多種場景
- 適配器名稱：MatrixAdapter
- 多帳戶支援：支援同時設定多個 Matrix 帳戶
- 連接方式：Long Polling（透過 Matrix Sync API `/sync`）
- 認證方式：基於 access_token 或 user_id + password 登錄獲取 token
- 鏈式修飾支援：支援 `.Reply()`、`.At()`、`.AtAll()` 等鏈式修飾方法
- OneBot12相容：支援發送 OneBot12 格式訊息

## 設定說明

MatrixAdapter 支援多帳戶設定，每個帳戶獨立設定 homeserver 和認證資訊。

```toml
# config.toml
# 帳戶1
[Matrix_Adapter.accounts.default]
homeserver = "https://matrix.org"          # Matrix伺服器位址（必填）
access_token = "YOUR_ACCESS_TOKEN"          # 訪問令牌（與 user_id+password 二選一）
user_id = ""                                # Matrix用戶ID（如 @bot:matrix.org）
password = ""                               # Matrix用戶密碼
auto_accept_invites = true                  # 是否自動接受房間邀請（可選，預設為true）
enabled = true                              # 是否啟用（可選，預設為true）

# 帳戶2
[Matrix_Adapter.accounts.bot2]
homeserver = "https://matrix.example.com"
access_token = "ANOTHER_TOKEN"
enabled = true
```

> 兼容舊設定：若檢測到舊的單帳戶 `[Matrix_Adapter]` 設定（含 access_token），會自動遷移為 `accounts.default`。

**設定項說明（每個帳戶）：**
- `homeserver`：Matrix伺服器位址（必填），預設為 `https://matrix.org`
- `access_token`：訪問令牌，可從Matrix用戶端獲取。如果已有 token，直接填寫即可
- `user_id`：Matrix用戶ID（如 `@bot:matrix.org`），與 `password` 配合使用進行登入
- `password`：Matrix用戶密碼，用於自動登入獲取 access_token
- `auto_accept_invites`：是否自動接受房間邀請，預設為 `true`
- `enabled`：是否啟用該帳戶（可選，預設為true）

**認證方式：**
- 方式一（推薦）：直接提供 `access_token`
- 方式二：提供 `user_id` 和 `password`，適配器會自動呼叫登入介面獲取 token

## 支援的訊息發送類型

所有發送方法均透過鏈式語法實現，例如：
```python
from ErisPulse.Core import adapter
matrix = adapter.get("matrix")

await matrix.Send.To("group", room_id).Text("Hello World!")
```

支援的發送類型包括：
- `.Text(text: str)`：發送純文字訊息。
- `.Image(file: bytes | str)`：發送圖片訊息，支援檔案路徑、URL、MXC URI、二進位數據。
- `.Voice(file: bytes | str)`：發送語音訊息，支援檔案路徑、URL、MXC URI、二進位數據。
- `.Video(file: bytes | str)`：發送影片訊息，支援檔案路徑、URL、MXC URI、二進位數據。
- `.File(file: bytes | str, filename: str = "")`：發送檔案訊息，支援檔案路徑、URL、MXC URI、二進位數據。
- `.Notice(text: str)`：發送通知訊息（Matrix的 m.notice 類型）。
- `.Html(html: str, fallback: str = "")`：發送HTML格式訊息，支援富文字內容。
- `.Raw_ob12(message: List[Dict], **kwargs)`：發送 OneBot12 格式訊息。

### 鏈式修飾方法（可組合使用）

鏈式修飾方法返回 `self`，支援鏈式呼叫，必須在最終發送方法前呼叫：

- `.Reply(message_id: str)`：回覆指定訊息（透過 Matrix `m.in_reply_to` 關係）。
- `.At(user_id: str)`：@指定用戶（透過 Matrix `m.mentions` 欄位實現）。
- `.AtAll()`：@房間內所有人（透過 Matrix `@room` 提及實現）。

### 鏈式呼叫範例

```python
# 基礎發送
await matrix.Send.To("user", dm_room_id).Text("Hello")

# 回覆訊息
await matrix.Send.To("group", room_id).Reply("$event_id").Text("回覆訊息")

# @用戶
await matrix.Send.To("group", room_id).At("@user:matrix.org").Text("你好")

# @所有人
await matrix.Send.To("group", room_id).AtAll().Text("公告通知")

# 組合使用：回覆 + @
await matrix.Send.To("group", room_id).Reply("$event_id").At("@user:matrix.org").Text("複合訊息")

# 發送HTML訊息
await matrix.Send.To("group", room_id).Html("<h1>標題</h1><p>內容</p>", fallback="標題\n內容")

# 發送通知訊息
await matrix.Send.To("group", room_id).Notice("系統通知")
```

### OneBot12訊息支援

適配器支援發送 OneBot12 格式訊息，便於跨平台訊息相容：

```python
# 發送 OneBot12 格式訊息
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await matrix.Send.To("user", dm_room_id).Raw_ob12(ob12_msg)

# 配合鏈式修飾
ob12_msg = [{"type": "text", "data": {"text": "回覆訊息"}}]
await matrix.Send.To("group", room_id).Reply("$event_id").Raw_ob12(ob12_msg)

# 複雜訊息
ob12_msg = [
    {"type": "text", "data": {"text": "看這張圖片："}},
    {"type": "image", "data": {"file": "https://example.com/image.png"}},
    {"type": "text", "data": {"text": "不錯吧？"}}
]
await matrix.Send.To("group", room_id).Raw_ob12(ob12_msg)
```

## 發送方法回傳值

所有發送方法均回傳一個 Task 物件，可以直接 await 獲取發送結果。回傳結果遵循 ErisPulse 適配器標準化回傳規範：

```python
{
    "status": "ok",           // 執行狀態: "ok" 或 "failed"
    "retcode": 0,             // 回傳碼
    "data": {...},            // 回應數據
    "message_id": "$event_id", // Matrix事件ID
    "message": "",            // 錯誤訊息
    "matrix_raw": {...}       // 原始回應數據
}
```

### 錯誤碼說明

| retcode | 說明 |
|---------|------|
| 0 | 成功 |
| 32000 | 請求超時或媒體上傳失敗 |
| 33000 | API呼叫異常 |
| 34000 | API回傳了意外格式或業務錯誤 |

## 特有事件類型

需要 `platform=="matrix"` 檢測再使用本平台特性

### 核心差異點

1. **去中心化架構**：Matrix 是一個去中心化的通信協議，用戶ID格式為 `@user:server.domain`，房間ID格式為 `!room_id:server.domain`
2. **房間概念**：Matrix 不區分群聊和私聊，所有會話都是"房間"。適配器透過 DM（Direct Message）帳戶數據自動識別私聊房間
3. **Long Polling 同步**：使用 `/sync` API 進行長輪詢獲取新事件，而非 WebSocket
4. **MXC URI**：媒體檔案透過 `mxc://server.domain/media_id` 格式引用
5. **HTML 富文字**：支援透過 `formatted_body` 發送 HTML 格式訊息
6. **表情回應**：支援訊息層級的表情回應（Reaction），區別於傳統的回覆訊息
7. **訊息編輯**：支援透過 `m.replace` 關係編輯已發送的訊息
8. **訊息撤回**：支援透過 `m.room.redaction` 撤回/刪除訊息

### 擴展欄位

- 所有特有欄位均以 `matrix_` 前綴標示
- 保留原始數據在 `matrix_raw` 欄位
- `matrix_raw_type` 標示原始Matrix事件類型（如 `m.room.message`、`m.room.member`）

### 特殊欄位範例

```python
# 群組訊息
{
  "type": "message",
  "detail_type": "group",
  "user_id": "@user:matrix.org",
  "group_id": "!room_id:matrix.org",
  "matrix_room_id": "!room_id:matrix.org"
}

# 私聊訊息
{
  "type": "message",
  "detail_type": "private",
  "user_id": "@user:matrix.org",
  "matrix_room_id": "!dm_room_id:matrix.org"
}

# 表情回應
{
  "type": "notice",
  "detail_type": "matrix_reaction",
  "matrix_reaction_event_id": "$reacted_msg_id",
  "matrix_reaction_key": "👍"
}

# 訊息撤回
{
  "type": "notice",
  "detail_type": "matrix_redaction",
  "matrix_redacted_event_id": "$deleted_msg_id"
}

# 訊息編輯
{
  "type": "message",
  "detail_type": "group",
  "matrix_edit": true,
  "matrix_original_event_id": "$original_event_id"
}

# 線程訊息
{
  "type": "message",
  "detail_type": "group",
  "thread_id": "$thread_root_id"
}
```

### 訊息段類型

Matrix訊息根據 `msgtype` 自動轉換為對應的訊息段：

| msgtype | 轉換類型 | 說明 |
|---|---|---|
| m.text | `text` | 文字訊息 |
| m.notice | `text` | 通知訊息 |
| m.emote | `text` | 動作訊息 |
| m.image | `image` | 圖片訊息 |
| m.audio | `voice` | 音頻訊息 |
| m.video | `video` | 視頻訊息 |
| m.file | `file` | 檔案訊息 |
| m.location | `location` | 位置訊息 |

訊息段結構範例：

```json
// 文字訊息（帶HTML）
{
  "type": "text",
  "data": {
    "text": "純文字內容",
    "html": "<b>HTML內容</b>"
  }
}

// 圖片訊息
{
  "type": "image",
  "data": {
    "url": "mxc://matrix.org/abc123",
    "filename": "photo.png",
    "matrix_mxc": "mxc://matrix.org/abc123",
    "info": {
      "mimetype": "image/png",
      "w": 800,
      "h": 600,
      "size": 123456
    }
  }
}

// 位置訊息
{
  "type": "location",
  "data": {
    "latitude": 0.0,
    "longitude": 0.0,
    "matrix_geo_uri": "geo:39.9,116.4",
    "text": "北京市"
  }
}
```

### Event Mixin 方法

MatrixAdapter 註冊了以下事件混入方法，可在事件處理中直接呼叫：

| 方法 | 回傳類型 | 說明 |
|------|----------|------|
| `get_room_id()` | `str` | 獲取房間ID |
| `get_matrix_event_type()` | `str` | 獲取原始Matrix事件類型 |
| `get_matrix_sender()` | `str` | 獲取原始發送者ID |
| `get_reaction_key()` | `str` | 獲取回應表情 |
| `is_edited()` | `bool` | 判斷訊息是否為編輯訊息 |
| `is_notice()` | `bool` | 判斷訊息是否為 m.notice 類型 |

```python
@message.on_message()
async def handle_message(event):
    if event.get("platform") != "matrix":
        return

    room_id = event.get_room_id()
    event_type = event.get_matrix_event_type()
    sender = event.get_matrix_sender()
    is_edited = event.is_edited()
    is_notice = event.is_notice()
```

## Sync API 連接

### 同步流程

1. 使用 access_token 或 user_id + password 進行認證
2. 呼叫 `/_matrix/client/v3/account/whoami` 獲取 bot_user_id
3. 發出 connect 元事件
4. 執行初始同步（`/_matrix/client/v3/sync?timeout=0`）獲取 `next_batch` token
5. 發現 DM 房間（`/_matrix/client/v3/user/{user_id}/account_data/m.direct`）
6. 開始 Long Polling 同步迴圈（`/_matrix/client/v3/sync?since={next_batch}&timeout=30000`）
7. 處理每次同步回傳的新事件並轉換發出

### 心跳機制

- 適配器每 30 秒發出一次 `heartbeat` 元事件
- 連接成功時發出 `connect` 元事件
- 關閉時發出 `disconnect` 元事件

### 房間邀請

- 收到房間邀請（`invite` 狀態的房間）時，如果 `auto_accept_invites` 設定為 `true`（預設），適配器會自動加入房間
- 加入房間呼叫 `/_matrix/client/v3/join/{room_id}` 介面

## 使用範例

### 處理群組訊息

```python
from ErisPulse.Core.Event import message
from ErisPulse import sdk

matrix = sdk.adapter.get("matrix")

@message.on_message()
async def handle_group_msg(event):
    if event.get("platform") != "matrix":
        return
    if event.get("detail_type") != "group":
        return

    text = event.get_text()
    room_id = event.get("group_id")

    if text == "hello":
        await matrix.Send.To("group", room_id).Reply(
            event.get("message_id")
        ).Text("Hello!")
```

### 處理表情回應

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_reaction(event):
    if event.get("platform") != "matrix":
        return

    if event.get("detail_type") == "matrix_reaction":
        reaction_key = event.get("matrix_reaction_key")
        reacted_event_id = event.get("matrix_reaction_event_id")
        room_id = event.get_room_id()
        # 處理表情回應...
```

### 發送媒體訊息

```python
# 發送圖片（URL）
await matrix.Send.To("group", room_id).Image("https://example.com/image.png")

# 發送圖片（MXC URI）
await matrix.Send.To("group", room_id).Image("mxc://matrix.org/abc123")

# 發送圖片（二進位數據）
with open("image.png", "rb") as f:
    image_bytes = f.read()
await matrix.Send.To("group", room_id).Image(image_bytes)

# 發送圖片（本地檔案路徑）
await matrix.Send.To("group", room_id).Image("/path/to/image.png")

# 發送檔案（帶檔案名）
await matrix.Send.To("group", room_id).File("/path/to/document.pdf", filename="文件.pdf")
```

### 處理訊息編輯

```python
@message.on_message()
async def handle_edited_message(event):
    if event.get("platform") != "matrix":
        return

    if event.is_edited():
        original_id = event.get("matrix_original_event_id")
        # 處理編輯訊息...
```

### 監聽成員變更

```python
@notice.on_notice()
async def handle_member_change(event):
    if event.get("platform") != "matrix":
        return

    detail_type = event.get("detail_type")

    if detail_type == "group_member_increase":
        user_id = event.get("user_id")
        nickname = event.get("user_nickname")
        print(f"用戶 {nickname} ({user_id}) 加入了房間")

    elif detail_type == "group_member_decrease":
        user_id = event.get("user_id")
        operator_id = event.get("operator_id")
        print(f"用戶 {user_id} 被移除，操作者: {operator_id}")
```



### QQBot 适配

# QQBot平台特性文件

QQBotAdapter 是基於 QQBot（QQ 機器人文件）協議所建構的適配器，整合了 QQBot 所有功能模組，提供統一的事件處理與訊息操作介面。

---

## 文件資訊

- 對應模組版本: 1.0.0
- 維護者: ErisPulse

## 基本資訊

- 平台簡介：QQBot 是 QQ 官方提供的機器人的開發接口，支援群聊、私聊、頻道等多種場景
- 適配器名稱：QQBotAdapter
- 連接方式：WebSocket 長連接（透過 QQBot 網關）
- 認證方式：基於 appId + clientSecret 獲取 access_token
- 鏈式修飾支援：支援 `.Reply()`、`.At()`、`.AtAll()`、`.Keyboard()` 等鏈式修飾方法
- OneBot12 兼容：支援發送 OneBot12 格式訊息

## 配置說明

```toml
# config.toml
[QQBot_Adapter]
appid = "YOUR_APPID"          # QQ機器人應用ID（必填）
secret = "YOUR_CLIENT_SECRET"  # QQ機器人客戶端密鑰（必填）
sandbox = false                 # 是否使用沙盒環境（可選，預設為false）
intents = [1, 30, 25]          # 訂閱的事件 intents 位（可選）
gateway_url = "wss://api.sgroup.qq.com/websocket/"  # 自訂網關地址（可選）
```

**配置項說明：**
- `appid`：QQ機器人的應用ID（必填），從QQ開放平台獲取
- `secret`：QQ機器人的客戶端密鑰（必填），從QQ開放平台獲取
- `sandbox`：是否使用沙盒環境，沙盒環境API地址為 `https://sandbox.api.sgroup.qq.com`
- `intents`：事件訂閱 intents 列表，每個值會被左移位後按位或運算
  - `1`：頻道相關事件
  - `25`：頻道訊息事件
  - `30`：群@訊息事件
- `gateway_url`：WebSocket 網關地址，預設為 `wss://api.sgroup.qq.com/websocket/`

**API環境：**
- 正式環境：`https://api.sgroup.qq.com`
- 沙盒環境：`https://sandbox.api.sgroup.qq.com`

## 支援的消息發送類型

所有發送方法均透過鏈式語法實現，例如：
```python
from ErisPulse.Core import adapter
qqbot = adapter.get("qqbot")

await qqbot.Send.To("user", user_openid).Text("Hello World!")
```

支援的發送類型包括：
- `.Text(text: str)`：發送純文字訊息。
- `.Image(file: bytes | str)`：發送圖片訊息，支援檔案路徑、URL、二進位元資料。
- `.Markdown(content: str)`：發送Markdown格式訊息。
- `.Ark(template_id: int, kv: list)`：發送Ark模板訊息。
- `.Embed(embed_data: dict)`：發送Embed訊息。
- `.Raw_ob12(message: List[Dict], **kwargs)`：發送 OneBot12 格式訊息。

### 鏈式修飾方法（可組合使用）

鏈式修飾方法返回 `self`，支援鏈式呼叫，必須在最終發送方法前呼叫：

- `.Reply(message_id: str)`：回覆指定訊息。
- `.At(user_id: str)`：@指定使用者（以 `<@user_id>` 格式插入內容）。
- `.AtAll()`：@所有人（插入 `@所有人` 文字）。
- `.Keyboard(keyboard: dict)`：新增鍵盤按鈕。

### 鏈式呼叫示例

```python
# 基礎發送
await qqbot.Send.To("user", user_openid).Text("Hello")

# 回覆訊息
await qqbot.Send.To("group", group_openid).Reply(msg_id).Text("回覆訊息")

# 回覆 + 按鈕
await qqbot.Send.To("group", group_openid).Reply(msg_id).Keyboard(keyboard).Text("帶回覆和鍵盤的訊息")

# @使用者
await qqbot.Send.To("group", group_openid).At("member_openid").Text("你好")

# 組合使用
await qqbot.Send.To("group", group_openid).Reply(msg_id).At("member_openid").Keyboard(keyboard).Text("複合訊息")
```

### OneBot12訊息支援

適配器支援發送 OneBot12 格式的訊息，便於跨平台訊息相容：

```python
# 發送 OneBot12 格式訊息
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await qqbot.Send.To("user", user_openid).Raw_ob12(ob12_msg)

# 配合鏈式修飾
ob12_msg = [{"type": "text", "data": {"text": "回覆訊息"}}]
await qqbot.Send.To("group", group_openid).Reply(msg_id).Raw_ob12(ob12_msg)
```

## 發送方法返回值

所有發送方法均返回一個 Task 對象，可以直接 await 獲取發送結果。返回結果遵循 ErisPulse 适配器标准化返回规范：

```python
{
    "status": "ok",           // 執行狀態: "ok" 或 "failed"
    "retcode": 0,             // 返回碼
    "data": {...},            // 响應數據
    "message_id": "123456",   // 消息ID
    "message": "",            // 錯誤信息
    "qqbot_raw": {...}        // 原始響應數據
}
```

### 錯誤碼說明

| retcode | 說明 |
|---------|------|
| 0 | 成功 |
| 10003 | 無法確定發送目標 |
| 32000 | 請求超時 |
| 33000 | API調用異常 |
| 34000 | API返回了意外格式或業務錯誤 |

## 特有事件類型

需要 `platform=="qqbot"` 檢測再使用本平台特性

### 核心差異點

1. **openid體系**：QQBot 使用 openid 而非 QQ號，使用者和群的標識均為 openid 字串
2. **群消息必須@**：群內消息僅在使用者 @ 機器人時才會收到（`GROUP_AT_MESSAGE_CREATE`）
3. **頻道系統**：QQBot 支援頻道（Guild）和子頻道（Channel）的消息和事件
4. **消息審核**：發送的消息可能需要經過審核，透過 `qqbot_audit_pass`/`qqbot_audit_reject` 事件通知結果
5. **被動回覆**：群消息和私聊消息支援被動回覆機制，需要在發送時攜帶 `msg_id`

### 擴展欄位

- 所有特有欄位均以 `qqbot_` 前綴標識
- 保留原始資料在 `qqbot_raw` 欄位
- `qqbot_raw_type` 標識原始QQBot事件類型（如 `C2C_MESSAGE_CREATE`）
- 附件資料透過 `qqbot_attachment` 欄位保存原始附件資訊

### 特殊欄位示例

```python
# 群@消息
{
  "type": "message",
  "detail_type": "group",
  "user_id": "MEMBER_OPENID",
  "group_id": "GROUP_OPENID",
  "qqbot_group_openid": "GROUP_OPENID",
  "qqbot_member_openid": "MEMBER_OPENID",
  "qqbot_event_id": "訊息事件ID",
  "qqbot_reply_token": "回覆token"
}

# 私聊消息
{
  "type": "message",
  "detail_type": "private",
  "user_id": "USER_OPENID",
  "qqbot_openid": "USER_OPENID",
  "qqbot_event_id": "訊息事件ID",
  "qqbot_reply_token": "回覆token"
}

# 互動事件
{
  "type": "notice",
  "detail_type": "qqbot_interaction",
  "qqbot_interaction_id": "互動ID",
  "qqbot_interaction_type": "互動類型",
  "qqbot_interaction_data": {
    "...": "互動資料"
  }
}

# 消息審核
{
  "type": "notice",
  "detail_type": "qqbot_audit_pass",
  "qqbot_audit_id": "審核ID",
  "qqbot_message_id": "訊息ID"
}

# 消息刪除
{
  "type": "notice",
  "detail_type": "qqbot_message_delete",
  "message_id": "被刪除的訊息ID",
  "operator_id": "操作者ID"
}

# 表情回應
{
  "type": "notice",
  "detail_type": "qqbot_reaction_add",
  "qqbot_raw": {
    "...": "原始資料"
  }
}
```

### 頻道消息段

頻道消息支援 `mentions` 欄位，轉換後以 `mention` 消息段表示：

```json
{
  "type": "mention",
  "data": {
    "user_id": "被@使用者ID",
    "user_name": "被@使用者暱稱"
  }
}
```

### 附件消息段

QQBot 的附件根據 `content_type` 自動轉換為對應消息段：

| content_type 前綴 | 轉換類型 | 說明 |
|---|---|---|
| `image` | `image` | 圖片訊息 |
| `video` | `video` | 影片訊息 |
| `audio` | `voice` | 語音訊息 |
| 其他 | `file` | 檔案訊息 |

附件訊息段結構：
```json
{
  "type": "image",
  "data": {
    "url": "附件URL",
    "qqbot_attachment": {
      "content_type": "image/png",
      "url": "原始附件URL"
    }
  }
}
```

## WebSocket 連接

### 連接流程

1. 使用 appId + clientSecret 獲取 access_token
2. 連接到 WebSocket 網關
3. 收到 OP_HELLO（op=10）訊息，獲取心跳間隔
4. 發送 OP_IDENTIFY（op=2）進行身份驗證
5. 收到 READY 事件，獲取 session_id 和 bot_id
6. 開始心跳循環（OP_HEARTBEAT，op=1）
7. 接收事件分發（OP_DISPATCH，op=0）

### 斷線重連

- 支援自動重連，最大重連次數為50次
- 重連等待時間採用指數退避演算法：`min(5 * 2^min(count, 6), 300)` 秒
- 支援會話恢復（OP_RESUME，op=6），使用 session_id + seq 恢復
- 收到 OP_RECONNECT（op=7）或 OP_INVALID_SESSION（op=9）時自動觸發重連

### Token刷新

- access_token 有效期通常為7200秒
- 适配器自動每 7080 秒（7200-120）刷新一次 token
- 刷新接口：`POST https://bots.qq.com/app/getAppAccessToken`

## 事件訂閱（Intents）

intents 值透過位元運算組合：

```python
intents = [1, 30, 25]
value = 0
for intent in intents:
    value |= (1 << intent)
```

常用的 intent 位：
| intent 值 | 說明 |
|----------|------|
| 1 | 頻道相關事件（GUILD_CREATE 等） |
| 25 | 頻道訊息事件（AT_MESSAGE_CREATE 等） |
| 30 | 群組 @ 訊息事件（GROUP_AT_MESSAGE_CREATE 等） |

## 使用示例

### 處理群消息

```python
from ErisPulse.Core.Event import message
from ErisPulse import sdk

qqbot = sdk.adapter.get("qqbot")

@message.on_message()
async def handle_group_msg(event):
    if event.get("platform") != "qqbot":
        return
    if event.get("detail_type") != "group":
        return

    text = event.get_text()
    group_id = event.get("group_id")

    if text == "hello":
        await qqbot.Send.To("group", group_id).Reply(
            event.get("message_id")
        ).Text("Hello!")
```

### 處理互動事件

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_interaction(event):
    if event.get("platform") != "qqbot":
        return

    if event.get("detail_type") == "qqbot_interaction":
        interaction_id = event.get("qqbot_interaction_id", "")
        interaction_data = event.get("qqbot_interaction_data", {})
        # 處理互動...
```

### 發送媒體訊息

```python
# 發送圖片（URL）
await qqbot.Send.To("group", group_openid).Image("https://example.com/image.png")

# 發送圖片（二進位）
with open("image.png", "rb") as f:
    image_bytes = f.read()
await qqbot.Send.To("user", user_openid).Image(image_bytes)
```

### 監聽訊息審核結果

```python
@notice.on_notice()
async def handle_audit(event):
    if event.get("platform") != "qqbot":
        return

    detail_type = event.get("detail_type")

    if detail_type == "qqbot_audit_pass":
        msg_id = event.get("qqbot_message_id")
        print(f"訊息審核通過: {msg_id}")

    elif detail_type == "qqbot_audit_reject":
        reason = event.get("qqbot_audit_reject_reason", "")
        print(f"訊息審核拒絕: {reason}")
```



### 云湖用户端适配

# 雲湖用戶平台特性文件

YunhuUserAdapter 是基於雲湖用戶帳戶協議構建的適配器，透過用戶郵箱帳戶登入，使用 WebSocket 接收事件，提供統一的事件處理和消息操作介面。

---

## 文件資訊

- 對應模組版本: 1.4.0
- 維護者: wsu2059

## 基本資訊

- 平台簡介：雲湖（Yunhu）是一個企業級即時通訊平台，本適配器透過**用戶帳戶**（而非機器人帳戶）與之交互
- 適配器名稱：YunhuUserAdapter
- 多帳戶支援：支援透過帳戶名識別並配置多個用戶帳戶
- 連式修飾支援：支援 `.Reply()` 等連式修飾方法
- OneBot12相容：支援發送 OneBot12 格式消息
- 通信方式：透過郵箱登入獲取 token，使用 WebSocket 接收事件，HTTP + Protobuf 協議發送消息
- 會話類型：支援私聊（user）、群聊（group）、機器人會話（bot）

## 支援的消息發送類型

所有發送方法均透過連式語法實現，例如：
```python
from ErisPulse.Core import adapter
yunhu_user = adapter.get("yunhu_user")

await yunhu_user.Send.To("user", user_id).Text("Hello World!")
```

支援的發送類型包括：
- `.Text(text: str, buttons: Optional[List] = None)`：發送純文本消息。
- `.Html(html: str, buttons: Optional[List] = None)`：發送HTML格式消息。
- `.Markdown(markdown: str, buttons: Optional[List] = None)`：發送Markdown格式消息。
- `.Image(file: Union[str, bytes], buttons: Optional[List] = None)`：發送圖片消息，支援URL、本地路徑或二進制數據。
- `.Video(file: Union[str, bytes], buttons: Optional[List] = None)`：發送視頻消息，支援URL、本地路徑或二進制數據。
- `.Audio(file: Union[str, bytes], buttons: Optional[List] = None)`：發送語音消息，支援URL、本地路徑或二進制數據，自動檢測音頻時長。
- `.Voice(file: Union[str, bytes], buttons: Optional[List] = None)`：`.Audio()` 的別名。
- `.File(file: Union[str, bytes], file_name: Optional[str] = None, buttons: Optional[List] = None)`：發送文件消息，支援URL、本地路徑或二進制數據。
- `.Face(file: Union[str, bytes], buttons: Optional[List] = None)`：發送表情/貼紙消息，支援貼紙ID、貼紙URL或二進位圖片數據。
- `.A2ui(a2ui_data: Union[str, Dict, List], buttons: Optional[List] = None)`：發送A2UI消息（消息類型14），A2UI JSON 數據會填入 text 字段發送。
- `.Edit(msg_id: str, text: str, content_type: str = "text")`：編輯已有消息。
- `.Recall(msg_id: str)`：撤回消息。
- `.Raw_ob12(message: Union[List, Dict])`：發送 OneBot12 格式消息。

### 媒體文件處理

所有媒體類型（圖片、視頻、音頻、文件）支援以下輸入方式：
- **URL**：`"https://example.com/image.jpg"` — 自動下載後上傳
- **本地路徑**：`"/path/to/file.jpg"` — 自動讀取後上傳
- **二進制數據**：`open("file.jpg", "rb").read()` — 直接上傳

媒體文件會自動上傳到七牛雲存儲，支援以下特性：
- 自動透過 `filetype` 庫檢測文件類型和 MIME
- 自動計算文件大小
- 音頻文件自動檢測時長（支援 MP3、MP4/M4A 格式）

### 按鈕參數說明

`buttons` 參數是一個嵌套列表，表示按鈕的佈局和功能。每個按鈕物件包含以下字段：

| 字段         | 類型   | 是否必填 | 說明                                                                 |
|--------------|--------|----------|----------------------------------------------------------------------|
| `text`       | string | 是       | 按鈕上的文字                                                         |
| `actionType` | int    | 是       | 動作類型：<br>`1`: 跳轉 URL<br>`2`: 複製<br>`3`: 點擊匯報            |
| `url`        | string | 否       | 當 `actionType=1` 時使用，表示跳轉的目標 URL                         |
| `value`      | string | 否       | 當 `actionType=2` 時，該值會複製到剪貼板<br>當 `actionType=3` 時，該值會發送給訂閱端 |

示例：
```python
buttons = [
    [
        {"text": "複製", "actionType": 2, "value": "xxxx"},
        {"text": "點擊跳轉", "actionType": 1, "url": "http://www.baidu.com"},
        {"text": "匯報事件", "actionType": 3, "value": "xxxxx"}
    ]
]
await yunhu_user.Send.To("user", user_id).Buttons(buttons).Text("帶按鈕的消息")
```

### 連式修飾方法（可組合使用）

連式修飾方法返回 `self`，支援連式調用，必須在最終發送方法前調用：

- `.Reply(message_id: str)`：回覆指定消息。
- `.At(user_id: str)`：@指定用戶（文本形式 @user_id）。
- `.AtAll()`：@所有人（偽@全體，發送 @all 文本）。
- `.Buttons(buttons: List)`：添加按鈕。

> **注意：** 因為用戶帳戶較為特殊，即便不是管理員也可以 @全體，但這裡的 `AtAll()` 只會發送一個艾特全體的文本，是一個偽@全體。

### 連式調用示例

```python
# 基礎發送
await yunhu_user.Send.To("user", user_id).Text("Hello")

# 回覆消息
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Text("回覆消息")

# 回覆 + 按鈕
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Buttons(buttons).Text("帶回覆和按鈕的消息")

# 指定帳戶 + 回覆 + 按鈕
await yunhu_user.Send.Using("default").To("group", group_id).Reply(msg_id).Buttons(buttons).Text("完整連式調用")
```

### OneBot12消息支援

適配器支援發送 OneBot12 格式的消息，便於跨平台消息相容：

- `.Raw_ob12(message: List[Dict], **kwargs)`：發送 OneBot12 格式消息。

```python
# 發送 OneBot12 格式消息
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu_user.Send.To("user", user_id).Raw_ob12(ob12_msg)

# 配合連式修飾
ob12_msg = [{"type": "text", "data": {"text": "回覆消息"}}]
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)
```

Raw_ob12 支援自動將混合消息段分組處理：
- `text`、`mention` 類型可合併為一組發送
- `image`、`video`、`audio`、`file`、`face`、`markdown`、`html`、`a2ui` 等類型各自獨立成組
- `reply` 類型可附加到任何組

## 發送方法返回值

所有發送方法均返回一個 Task 物件，可以直接 await 獲取發送結果。返回結果遵循 ErisPulse 適配器標準化返回規範：

```python
{
    "status": "ok",           // 執行狀態
    "retcode": 0,             // 返回碼
    "data": {...},            // 響應數據
    "message_id": "123456",   // 消息ID
    "message": "",            // 錯誤信息
    "yunhu_user_raw": {...}   // 原始響應數據
}
```

## 特有事件類型

需要 `platform == "yunhu_user"` 檢測再使用本平台特性

### 核心差異點

1. 特有事件類型：
    - 超級文件分享：`yunhu_user_file_send`
    - 機器人公告看板：`yunhu_user_bot_board`
    - 消息編輯通知：`message_edit`
    - 消息刪除通知：`message_delete`（撤回）
2. 特有消息段類型：
    - 表單消息段：`yunhu_user_form`
    - 文章消息段：`yunhu_user_post`
    - 貼紙消息段：`yunhu_user_sticker`
    - 按鈕消息段：`yunhu_user_button`
    - A2UI 消息段：`a2ui`
3. 擴展字段：
    - 所有特有字段均以 `yunhu_user_` 前綴標識
    - 保留原始數據在 `yunhu_user_raw` 字段
    - 原始事件類型記錄在 `yunhu_user_raw_type` 字段
    - 私聊中 `self.user_id` 表示當前登錄用戶ID

### 支援的原始事件類型

| 原始事件類型 | OneBot12 類型 | 說明 |
|-------------|--------------|------|
| `push_message` | `message` | 推送消息（私聊、群聊、Bot 會話） |
| `edit_message` | `notice` (`message_edit`) | 消息編輯事件 |
| `file_send_message` | `notice` (`yunhu_user_file_send`) | 超級文件分享事件 |
| `bot_board_message` | `notice` (`yunhu_user_bot_board`) | 機器人公告看板事件 |

> 其他事件類型（如 `heartbeat_ack`、`draft_input`、`stream_message` 等）會被忽略。

### OneBot12 支援的 detail_type

| OneBot12 detail_type | 雲湖 chat_type | 說明 |
|---------------------|---------------|------|
| `private` | 1 | 私聊消息 |
| `group` | 2 | 群聊消息 |
| `bot` | 3 | 機器人會話 |

### 消息事件示例

```python
{
    "id": "event_id",
    "time": 1234567890,
    "type": "message",
    "detail_type": "group",
    "platform": "yunhu_user",
    "self": {
        "platform": "yunhu_user",
        "user_id": "your_user_id"
    },
    "message": [
        {"type": "text", "data": {"text": "消息內容"}}
    ],
    "alt_message": "消息內容",
    "user_id": "sender_user_id",
    "user_nickname": "發送者暱稱",
    "group_id": "group_id",
    "message_id": "msg_id",
    "yunhu_user_raw": {...},
    "yunhu_user_raw_type": "push_message"
}
```

### 消息編輯通知示例

```python
{
    "type": "notice",
    "detail_type": "message_edit",
    "platform": "yunhu_user",
    "self": {
        "platform": "yunhu_user",
        "user_id": "your_user_id"
    },
    "message_id": "msg_id",
    "user_id": "sender_user_id",
    "user_nickname": "發送者暱稱",
    "edit_time": 1234567890,
    "group_id": "group_id",
    "yunhu_user_raw": {...},
    "yunhu_user_raw_type": "edit_message"
}
```

### 超級文件分享事件示例

```python
{
    "type": "notice",
    "detail_type": "yunhu_user_file_send",
    "platform": "yunhu_user",
    "self": {
        "platform": "yunhu_user",
        "user_id": "your_user_id"
    },
    "user_id": "send_user_id",
    "user_nickname": "",
    "yunhu_user_file_send": {
        "send_user_id": "發送者ID",
        "user_id": "接收用戶ID",
        "send_type": "發送類型",
        "data": "文件數據"
    },
    "yunhu_user_raw": {...},
    "yunhu_user_raw_type": "file_send_message"
}
```

### 機器人公告看板事件示例

```python
{
    "type": "notice",
    "detail_type": "yunhu_user_bot_board",
    "platform": "yunhu_user",
    "self": {
        "platform": "yunhu_user",
        "user_id": "your_user_id"
    },
    "bot_id": "bot_id",
    "bot_name": "機器人名稱",
    "yunhu_user_bot_board": {
        "bot_id": "bot_id",
        "chat_id": "chat_id",
        "chat_type": 1,
        "content": "公告內容",
        "content_type": 1,
        "last_update_time": 1234567890
    },
    "yunhu_user_raw": {...},
    "yunhu_user_raw_type": "bot_board_message"
}
```

### 事件處理示例

```python
from ErisPulse.Core.Event import message, notice

@message.on_message()
async def handle_yunhu_user_message(event):
    """處理雲湖用戶消息"""
    if event.get("platform") != "yunhu_user":
        return
    
    user_id = event.get("user_id", "")
    user_nickname = event.get("user_nickname", "")
    alt_message = event.get("alt_message", "")
    
    print(f"用戶 {user_nickname}({user_id}): {alt_message}")
    
    # 檢查消息段中的特有類型
    for segment in event.get("message", []):
        seg_type = segment.get("type", "")
        
        if seg_type == "yunhu_user_form":
            form_data = segment["data"]["form"]
            print(f"收到表單消息: {form_data}")
        
        elif seg_type == "yunhu_user_post":
            post_data = segment["data"]
            print(f"收到文章消息: {post_data.get('post_title', '')}")
        
        elif seg_type == "yunhu_user_sticker":
            sticker_url = segment["data"]["file_id"]
            print(f"收到貼紙消息: {sticker_url}")
        
        elif seg_type == "yunhu_user_button":
            buttons = segment["data"]["buttons"]
            print(f"消息包含按鈕: {buttons}")
        
        elif seg_type == "a2ui":
            a2ui_data = segment["data"]["a2ui"]
            print(f"收到A2UI消息: {a2ui_data}")
    
    # 使用 event.reply() 自動回覆
    await event.reply(f"Echo: {alt_message}")

@notice.on_notice()
async def handle_yunhu_user_notice(event):
    """處理雲湖用戶通知事件"""
    if event.get("platform") != "yunhu_user":
        return
    
    detail_type = event.get("detail_type", "")
    
    if detail_type == "message_edit":
        message_id = event.get("message_id", "")
        user_nickname = event.get("user_nickname", "")
        edit_time = event.get("edit_time", 0)
        print(f"用戶 {user_nickname} 編輯了消息 {message_id}")
    
    elif detail_type == "yunhu_user_file_send":
        file_data = event.get("yunhu_user_file_send", {})
        print(f"收到超級文件分享: {file_data}")
    
    elif detail_type == "yunhu_user_bot_board":
        board_data = event.get("yunhu_user_bot_board", {})
        bot_name = event.get("bot_name", "")
        print(f"機器人 {bot_name} 發布了公告: {board_data.get('content', '')}")
```

## 擴展字段說明

- 所有特有字段均以 `yunhu_user_` 前綴標識，避免與標準字段衝突
- 保留原始數據在 `yunhu_user_raw` 字段，便於訪問雲湖平台的完整原始數據
- 原始事件類型記錄在 `yunhu_user_raw_type` 字段（如 `push_message`、`edit_message` 等）
- `self.user_id` 表示當前登錄用戶ID（從登錄響應中獲取）
- 超級文件分享透過 `yunhu_user_file_send` 字段提供文件分享數據
- 機器人公告看板透過 `yunhu_user_bot_board` 字段提供公告數據

### 特有消息段類型

#### 表單消息段 (yunhu_user_form)

當 content_type 為 5 時，消息段類型為 `yunhu_user_form`：

```json
{
    "type": "yunhu_user_form",
    "data": {
        "form": "表單數據"
    }
}
```

#### 文章消息段 (yunhu_user_post)

當 content_type 為 6 時，消息段類型為 `yunhu_user_post`：

```json
{
    "type": "yunhu_user_post",
    "data": {
        "post_id": "文章ID",
        "post_title": "文章標題",
        "post_content": "文章內容"
    }
}
```

| 字段 | 類型 | 說明 |
|------|------|------|
| `post_id` | string | 文章唯一標識 |
| `post_title` | string | 文章標題 |
| `post_content` | string | 文章內容 |

#### 貼紙消息段 (yunhu_user_sticker)

當 content_type 為 7 時，消息段類型為 `yunhu_user_sticker`：

```json
{
    "type": "yunhu_user_sticker",
    "data": {
        "file_id": "貼紙圖片URL"
    }
}
```

| 字段 | 類型 | 說明 |
|------|------|------|
| `file_id` | string | 貼紙圖片URL |

#### 按鈕消息段 (yunhu_user_button)

消息中包含按鈕時，會附加 `yunhu_user_button` 消息段：

```json
{
    "type": "yunhu_user_button",
    "data": {
        "buttons": [[{"text": "按鈕文字", "actionType": 3, "value": "值"}]]
    }
}
```

#### A2UI 消息段 (a2ui)

當 content_type 為 14 時，消息段類型為 `a2ui`：

```json
{
    "type": "a2ui",
    "data": {
        "a2ui": "A2UI JSON數據"
    }
}
```

---

## 多帳戶配置

### 配置說明

YunhuUserAdapter 支援同時配置和運行多個用戶帳戶。

```toml
# config.toml
[YunhuUserAdapter]
ws_reconnect_interval = 30  # WebSocket重連間隔（秒）
ws_timeout = 70             # WebSocket超時時間（秒）

[YunhuUserAdapter.accounts.default]
email = "user1@example.com"  # 用戶郵箱（必填）
password = "password1"       # 用戶密碼（必填）
platform = "windows"         # 登錄平台（可選，默認windows）
device_id = ""               # 設備ID（可選，不填自動生成）
enabled = true               # 是否啟用（可選，默認為true）

[YunhuUserAdapter.accounts.account2]
email = "user2@example.com"
password = "password2"
platform = "android"
device_id = "fixed_device_id_2"
enabled = true
```

**配置項說明：**
- `email`：用戶郵箱（必填），用於登錄雲湖平台
- `password`：用戶密碼（必填）
- `platform`：登錄平台標識（可選，默認為 `windows`），可選值：`windows`、`macos`、`linux`、`ios`、`android`
- `device_id`：設備ID（可選，不填自動生成），建議填寫固定值以保持會話一致性
- `enabled`：是否啟用該帳戶（可選，默認為 `true`）

**適配器級別配置：**
- `ws_reconnect_interval`：WebSocket 重連間隔（秒，默認 30）
- `ws_timeout`：WebSocket 超時時間（秒，默認 70）

**重要提示：**
1. 適配器使用郵箱登錄方式獲取 token，登錄後透過 WebSocket 接收事件
2. WebSocket 連接斷開後會自動重連，最多重試 3 次
3. 建議為每個帳戶設置固定的 `device_id`，以保持會話一致性
4. 未修改的模板帳戶（默認郵箱和密碼）會被自動跳過

### 使用Send DSL指定帳戶

可以透過 `Using()` 方法指定使用哪個帳戶發送消息。該方法支援兩種參數：
- **帳戶名**：配置中的帳戶名稱（如 `default`、`account2`）
- **user_id**：登錄後獲取的用戶 ID

```python
from ErisPulse.Core import adapter
yunhu_user = adapter.get("yunhu_user")

# 使用帳戶名發送消息
await yunhu_user.Send.Using("default").To("user", "user123").Text("Hello from account1!")

# 使用 user_id 發送消息（自動匹配對應帳戶）
await yunhu_user.Send.Using("user_id_here").To("group", "group456").Text("Hello from user!")

# 不指定時使用第一個啟用的帳戶
await yunhu_user.Send.To("user", "user123").Text("Hello from default account!")
```

> **提示：** 使用 `user_id` 時，系統會自動查找配置中匹配的帳戶。這在處理事件回覆時特別有用，可以直接使用 `event["self"]["user_id"]` 來回覆同一帳戶。

### 事件中的帳戶標識

接收到的事件會自動包含對應的用戶ID資訊：

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu_user":
        # 獲取當前登錄用戶ID
        my_user_id = event["self"]["user_id"]
        print(f"消息來自帳戶: {my_user_id}")
        
        # 使用相同帳戶回覆消息
        yunhu_user = adapter.get("yunhu_user")
        await yunhu_user.Send.Using(my_user_id).To(
            event["detail_type"],
            event["user_id"] if event["detail_type"] == "private" else event["group_id"]
        ).Text("回覆消息")
```

### 日誌信息

適配器會在日誌中自動包含帳戶資訊，便於調試和追蹤：

```
[INFO] 帳戶 default (user1@example.com) 登錄成功，用戶ID: 12345678
[INFO] 帳戶 default WebSocket 監聽任務已啟動
[INFO] 帳戶 account2 (user2@example.com) 登錄成功，用戶ID: 87654321
```

### 管理介面

```python
# 獲取所有帳戶資訊
accounts = yunhu_user.accounts
# 返回格式: {"default": {"name": "default", "email": "...", "token": "...", "user_id": "...", ...}, ...}

# 檢查帳戶是否啟用
for account_name, account_config in yunhu_user._account_configs.items():
    print(f"{account_name}: enabled={account_config.enabled}")

# 透過帳戶名獲取 HTTP 客戶端
http_client = yunhu_user._get_http_client("default")

# 透過 user_id 查找帳戶
account_name = yunhu_user._get_account_by_user_id("12345678")
```

## API 調用

適配器提供 `call_api` 方法，支援直接調用平台 API：

```python
# 發送消息
result = await yunhu_user.call_api("/send", 
    target_type="group", 
    target_id="group_id",
    account_id="default",
    message={"text": "Hello", "msg_type": 1}
)

# 編輯消息
result = await yunhu_user.call_api("/edit",
    target_type="group",
    target_id="group_id",
    msg_id="msg_id",
    text="新內容",
    content_type="text"
)

# 撤回消息
result = await yunhu_user.call_api("/recall",
    target_type="group",
    target_id="group_id",
    msg_id="msg_id"
)

# 批量撤回消息
result = await yunhu_user.call_api("/recall_batch",
    target_type="group",
    target_id="group_id",
    msg_id_list=["msg_id_1", "msg_id_2"]
)

# 獲取消息列表
result = await yunhu_user.call_api("/list",
    chat_id="group_id",
    chat_type=2,
    msg_count=10,
    msg_id=""
)

# 獲取消息編輯記錄
result = await yunhu_user.call_api("/list_edit_record",
    msg_id="msg_id",
    size=10,
    page=1
)

# 按鈕事件報告
result = await yunhu_user.call_api("/button_report",
    chat_id="group_id",
    chat_type=2,
    msg_id="msg_id",
    user_id="user_id",
    button_value="button_value"
)
```

**支援的 API 端點：**

| 端點 | 說明 |
|------|------|
| `/send` | 發送消息 |
| `/edit` | 編輯消息 |
| `/recall` | 撤回消息 |
| `/recall_batch` | 批量撤回消息 |
| `/list` | 獲取消息列表 |
| `/list_by_seq` | 通過序列獲取消息 |
| `/list_by_mid_seq` | 通過消息ID和序列獲取消息 |
| `/list_edit_record` | 獲取消息編輯記錄 |
| `/button_report` | 按鈕事件報告 |



### 平台文档维护说明

# 文檔維護說明

本文件由各適配器開發者維護，用於說明該適配器與 OneBot12 標準的差異和擴展功能。請適配器開發者在發布新版本時同步更新此文件。

## 更新要求

1. 準確描述平台特有的傳送方法和參數
2. 詳細說明與 OneBot12 標準的差異點
3. 提供清晰的程式碼範例和參數說明
4. 保持文件格式統一，便於用戶查閱
5. 及時更新版本資訊和維護者聯絡方式

## 文件結構規範

### 1. 基本資訊部分
每個平台特性文件應包含以下基本資訊：
```markdown
# 平台名稱適配器文件

適配器名稱：[適配器類名]
平台簡介：[平台簡要介紹]
支援的協定/API版本：[具體協定或API版本]
維護者：[維護者姓名/團隊]
對應模組版本: [版本號]
```

### 2. 支援的訊息傳送類型
詳細列出所有支援的傳送方法及其參數：
```markdown
## 支援的訊息傳送類型

所有傳送方法均透過鏈式語法實現，例如：
[程式碼範例]

支援的傳送類型包括：
- 方法1：說明
- 方法2：說明
- ...

### 參數說明
| 參數 | 類型 | 說明 |
|------|------|------|
| 參數名 | 類型 | 說明 |
```

### 3. 特有事件類型
詳細描述平台特有的事件類型及格式：
```markdown
## 特有事件類型

[平台名稱]事件轉換到OneBot12協定，其中標準欄位完全遵守OneBot12協定，但存在以下差異：

### 核心差異點
1. 特有事件類型：
   - 事件類型1：說明
   - 事件類型2：說明
2. 擴展欄位：
   - 欄位說明

### 特殊欄位範例
[JSON範例]
```

### 4. 擴展欄位說明
```markdown
## 擴展欄位說明

- 所有特有欄位均以 `[platform]_` 前綴識別
- 保留原始資料在 `[platform]_raw` 欄位
- [其他特殊欄位說明]
```

### 5. 配置選項（如適用）
```markdown
## 配置選項

[平台名稱] 適配器支援以下配置選項：

### 基本配置
- 配置項1：說明
- 配置項2：說明

### 特殊配置
- 特殊配置項1：說明
```

## 內容編寫規範

### 程式碼範例規範
1. 所有程式碼範例必須是可執行的完整範例
2. 使用標準導入方式：
```python
from ErisPulse.Core import adapter
[適配器實例] = adapter.get("[適配器名稱]")
```
3. 提供多種使用場景的範例

### 文件格式規範
1. 使用標準 Markdown 語法
2. 標題層級清晰，最多使用 4 級標題
3. 表格使用標準 Markdown 表格格式
4. 程式碼區塊使用適當的語言標識

### 版本更新說明
每次更新文件時，應在文件頂部更新版本資訊：
```markdown
## 文件資訊

- 對應模組版本：[新版本號]
- 維護者：[維護者資訊]
- 最後更新：[日期]
```

## 質量檢查清單

在提交文件更新前，請檢查以下內容：

- [ ] 文件結構符合規範要求
- [ ] 所有程式碼範例可以正常執行
- [ ] 參數說明完整準確
- [ ] 事件格式範例符合實際輸出
- [ ] 連結和引用正確無誤
- [ ] 語法和拼寫無錯誤
- [ ] 版本資訊已更新
- [ ] 維護者資訊準確

## 參考文檔

編寫時請參考以下文檔以確保一致性：
- [OneBot12 標準文檔](https://12.onebot.dev/)
- [ErisPulse 核心概念](../getting-started/basic-concepts.md)
- [事件轉換標準](../standards/event-conversion.md)
- [API 回應規範](../standards/api-response.md)
- [其他平台適配器文檔](./)

## 貢獻流程

1. Fork [ErisPulse](https://github.com/ErisPulse/ErisPulse) 儲存庫
2. 在 `docs/platform-features/` 目錄下修改對應的平台文件
3. 確保文件符合上述規範要求
4. 提交 Pull Request 並詳細說明修改內容

如有疑問，請聯絡相關適配器維護者或在專案 Issues 中提問。



### 花枫咖啡馆适配

# 花楓咖啡館（RockyChat）平台特性文件

IdeauraAdapter 是基於花楓咖啡館（RockyChat）平台 API 建構的適配器，整合了所有平台功能模組，提供統一的事件處理與訊息操作介面。

---
docs/zh-TW/quick-start.md

## 文件資訊

- 對應模組: ErisPulse-Ideaura
- 對應模組版本: 4.0.1
- 維護者: ErisPulse

## 基本資訊

- 平台簡介：花楓咖啡館（RockyChat）是一個即時通訊平台
- 適配器名稱：IdeauraAdapter
- 多帳號支援：支援透過 Bot Token 配置多個帳號
- 鏈式修飾支援：支援 `.At()`、`.AtAll()`、`.Reply()`、`.Command()` 等鏈式修飾方法
- OneBot12 兼容：支援發送 OneBot12 格式訊息

## 支援的消息傳送類型

所有傳送方法均透過串接語法實作，例如：
```python
from ErisPulse.Core import adapter
ideaura = adapter.get("ideaura")

await ideaura.Send.To("group", "chatroom").Text("Hello World!")
```

支援的傳送類型包括：
- `.Text(text: str)`：傳送純文字訊息。
- `.Image(file, filename: str = None)`：傳送圖片訊息，支援 bytes/URL/本機路徑。
- `.Video(file, filename: str = None)`：傳送影片訊息，支援 bytes/URL/本機路徑。
- `.File(file, filename: str = None)`：傳送檔案訊息，支援 bytes/URL/本機路徑。
- `.Voice(file, filename: str = None)`：傳送語音訊息（以檔案形式傳送）。
- `.Face(face_id: str)`：傳送表情（以純文字形式傳送 emoji）。
- `.Markdown(text: str)`：傳送 Markdown 格式訊息。
- `.Html(html: str)`：傳送 HTML 格式訊息。
- `.Edit(message_id: str, text: str, content_type: str = "text")`：編輯已有訊息。
- `.Recall(message_id: str)`：撤回訊息。

### 串接修飾方法（可組合使用）

串接修飾方法會返回 `self`，支援串接呼叫，必須在最終傳送方法前呼叫：

- `.At(user_id: str, name: str = None)`：@指定用戶。
- `.AtAll()`：@所有人。
- `.Reply(message_id: str)`：回覆指定訊息。
- `.Command(command_id: str)`：觸發 Bot 指令，配合傳送方法使用（將訊息作為指定指令傳送）。

### 串接呼叫範例

```python
# 基礎傳送
await ideaura.Send.To("user", user_id).Text("Hello")

# 觸發 Bot 指令
await ideaura.Send.To("group", "chatroom").Command("550e8400-e29b-41d4-a716-446655440000").Text("/weather 北京")

# @用戶
await ideaura.Send.To("group", "chatroom").At("456").Text("@李四 你好")

# @多人
await ideaura.Send.To("group", "chatroom").At("456").At("789").Text("@多人")

# 回覆訊息
await ideaura.Send.To("group", "chatroom").Reply(msg_id).Text("回覆訊息")

# 回覆 + @
await ideaura.Send.To("group", "chatroom").Reply(msg_id).At("456").Text("回覆並@")
```

### 發送到不同目標

```python
# 發送到聊天室
await ideaura.Send.To("group", "chatroom").Text("聊天室訊息")

# 發送到話題
await ideaura.Send.To("group", "topic_id").Text("話題訊息")

# 發送私聊訊息
await ideaura.Send.To("user", "user_id").Text("私聊訊息")
```

### OneBot12 訊息支援

適配器支援傳送 OneBot12 格式的訊息，便於跨平台訊息相容：

- `.Raw_ob12(message: List[Dict], **kwargs)`：傳送 OneBot12 格式訊息。

```python
# 發送 OneBot12 格式訊息
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await ideaura.Send.To("user", user_id).Raw_ob12(ob12_msg)

# 配合串接修飾
ob12_msg = [{"type": "text", "data": {"text": "回覆訊息"}}]
await ideaura.Send.To("group", "chatroom").Reply(msg_id).Raw_ob12(ob12_msg)
```

## 發送方法返回值

所有發送方法均返回一個 Task 對象，可以直接 await 獲取發送結果。返回結果遵循 ErisPulse 适配器标准化返回规范：

```python
{
    "status": "ok",           // 執行狀態
    "retcode": 0,             // 返回碼
    "data": {...},            // 响應數據
    "self": {...},            // 自身信息（包含 user_id）
    "message_id": "123456",  // 消息ID
    "message": "",            // 錯誤信息
    "ideaura_raw": {...}      // 原始響應數據
}
```

## 特有事件類型

需要 `platform=="ideaura"` 檢測再使用本平台特性

### 核心差異點

1. 特有事件類型：
    - 消息編輯：ideaura_message_edit
    - 消息撤回：ideaura_message_recall
    - 消息轉發：ideaura_message_forward
    - 消息已讀：ideaura_message_read
    - 好友被拒：ideaura_friend_rejected
    - 好友上線：ideaura_friend_online
    - 好友下線：ideaura_friend_offline
    - 用戶狀態變更：ideaura_user_status_change
    - 轉發消息段：ideaura_forwarded
    - 編輯標記段：ideaura_edited
    - Markdown消息段：ideaura_markdown
    - HTML消息段：ideaura_html
    - Bot指令消息段：ideaura_command
2. 擴展字段：
    - 所有特有字段均以 `ideaura_` 前綴標識
    - 保留原始數據在 `ideaura_raw` 字段
    - `self.user_id` 表示當前帳戶的用戶ID

### 消息編輯事件

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_edit",
  "platform": "ideaura",
  "message_id": "消息ID",
  "user_id": "編輯者ID",
  "ideaura_new_content": "編輯後的內容",
  "ideaura_updated_message": { ... },
  "ideaura_source_type": "chatroom/topic/private"
}
```

### 消息撤回事件

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_recall",
  "platform": "ideaura",
  "message_id": "被撤回的消息ID",
  "user_id": "撤回者ID",
  "group_id": "chatroom",
  "ideaura_source_type": "chatroom",
  "ideaura_recall_time": "撤回時間",
  "ideaura_is_self": false
}
```

### 消息轉發事件

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_forward",
  "platform": "ideaura",
  "message_id": "原始消息ID",
  "user_id": "轉發者ID",
  "ideaura_forward_to": "目標話題ID",
  "ideaura_original_message_id": "原始消息ID",
  "ideaura_forwarded_message_id": "轉發後的新消息ID"
}
```

### 消息已讀事件

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_read",
  "platform": "ideaura",
  "message_id": "消息ID",
  "ideaura_reader_id": "已讀者ID",
  "ideaura_reader_name": "已讀者暱稱"
}
```

### 好友上線事件

```python
{
  "type": "notice",
  "detail_type": "ideaura_friend_online",
  "platform": "ideaura",
  "user_id": "好友ID",
  "user_nickname": "好友暱稱",
  "ideaura_friend_avatar": "頭像URL",
  "ideaura_presence_status": "online"
}
```

### 好友下線事件

```python
{
  "type": "notice",
  "detail_type": "ideaura_friend_offline",
  "platform": "ideaura",
  "user_id": "好友ID",
  "ideaura_presence_status": "offline"
}
```

### 用戶狀態變更事件

```python
{
  "type": "notice",
  "detail_type": "ideaura_user_status_change",
  "platform": "ideaura",
  "user_id": "用戶ID",
  "ideaura_status": "新狀態",
  "ideaura_previous_status": "舊狀態"
}
```

### 好友請求事件

```python
{
  "type": "request",
  "detail_type": "friend",
  "platform": "ideaura",
  "user_id": "請求者ID",
  "user_nickname": "請求者暱稱",
  "ideaura_request_id": "請求ID",
  "ideaura_message": "驗證消息"
}
```

### 好友被拒事件

```python
{
  "type": "notice",
  "detail_type": "ideaura_friend_rejected",
  "platform": "ideaura",
  "user_id": "拒絕者ID",
  "user_nickname": "拒絕者暱稱",
  "ideaura_request_id": "請求ID",
  "ideaura_requester_id": "請求發起者ID",
  "ideaura_requester_name": "請求發起者暱稱"
}
```

### 轉發消息段 (ideaura_forwarded)

當收到轉發消息時，消息段類型為 `ideaura_forwarded`：

```json
{
  "type": "ideaura_forwarded",
  "data": {
    "forward_source_id": "1001",
    "original_message_id": "1001"
  }
}
```

| 字段 | 類型 | 說明 |
|------|------|------|
| `forward_source_id` | string | 轉發源消息ID |
| `original_message_id` | string | 原始消息ID |

### Bot 指令消息段 (ideaura_command)

當用戶觸發 Bot 指令時，消息段類型為 `ideaura_command`：

```json
{
  "type": "ideaura_command",
  "data": {
    "command_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

| 字段 | 類型 | 說明 |
|------|------|------|
| `command_id` | string | 指令 UUID |

### 事件處理示例

```python
from ErisPulse.Core.Event import notice, message

@message.on_message()
async def handle_message(event):
    if event.get_platform() == "ideaura":
        # 處理消息事件
        for segment in event.get("message", []):
            if segment.get("type") == "ideaura_forwarded":
                data = segment["data"]
                print(f"轉發消息，源ID: {data['forward_source_id']}")

@notice.on_notice()
async def handle_notice(event):
    if event.get_platform() != "ideaura":
        return

    detail_type = event.get("detail_type")

    if detail_type == "ideaura_message_edit":
        new_content = event.get("ideaura_new_content", "")
        print(f"消息被編輯: {new_content}")

    elif detail_type == "ideaura_message_recall":
        message_id = event.get("message_id")
        print(f"消息被撤回: {message_id}")

    elif detail_type == "ideaura_friend_online":
        friend_name = event.get_user_nickname()
        print(f"好友上線: {friend_name}")

    elif detail_type == "ideaura_user_status_change":
        status = event.get("ideaura_status")
        print(f"用戶狀態變更: {status}")
```

## Event Mixin 擴展方法

適配器註冊了以下平台專有方法，僅在 `platform == "ideaura"` 時可用：

| 方法 | 返回類型 | 說明 |
|------|----------|------|
| `get_source_type()` | `str` | 消息來源類型（`chatroom`/`topic`/`private`） |
| `get_sender_name()` | `str` | 發送者暱稱 |
| `get_sender_avatar()` | `str` | 發送者頭像 URL |
| `is_sender_bot()` | `bool` | 發送者是否為機器人 |
| `is_receiver_bot()` | `bool` | 接收者是否為機器人 |
| `get_command_id()` | `str` | 觸發的 Bot 指令 ID（若有，`ideaura_command_id`） |
| `get_command()` | `str` | `get_command_id()` 的別名 |
| `get_topic_name()` | `str` | 話題名稱 |
| `get_message_type()` | `str` | 消息類型（normal/edited/forwarded/quoted） |
| `get_message_subtype()` | `str` | 消息子類型（text/image/video/file/markdown/html） |
| `is_self_message()` | `bool` | 是否為自己發送的消息 |

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event.get_platform() != "ideaura":
        return

    # 獲取觸發的 Bot 指令 ID（若有）
    cmd_id = event.get_command_id()
    if cmd_id:
        print(f"收到指令: {cmd_id}")
```

---

## 多帳戶配置

### 配置說明

IdeauraAdapter 支援同時配置和運行多個帳戶，使用 **Bot Token** 進行認證。

> [!WARNING]
> 從 4.0.1 開始**移除電郵密碼登入**，僅支援 Bot Token。Bot Token 需前往 [MSCPO 開放平台](https://open.mscpo.com/rockychat/bots) 取得（以 `bot-token-` 開頭）。

```toml
# config.toml
# 帳戶1
[IdeauraAdapter.accounts.default]
token = "bot-token-xxxxxx1"      # 機器人 API Token（必填）
enabled = true                   # 是否啟用（可選，預設為true）

# 帳戶2
[IdeauraAdapter.accounts.bot2]
token = "bot-token-xxxxxx2"
enabled = true

# 可選：自訂伺服器地址
[IdeauraAdapter]
base_url = "https://api.mscpo.com/api/rockychat"
ws_url = "wss://api-cofe.allons-y.uk:3009/mqtt"
heartbeat_interval = 30
```

**配置項說明：**
- `token`：機器人 API Token（必填，以 `bot-token-` 開頭）
- `enabled`：是否啟用該帳戶（可選，預設為true）

**全域配置項：**
- `base_url`：API 伺服器地址（可選，預設為 `https://api.mscpo.com/api/rockychat`）
- `ws_url`：WebSocket 伺服器地址（可選，預設為花楓咖啡館官方地址）
- `heartbeat_interval`：心跳間隔秒數（可選，預設30秒）

### 使用 Send DSL 指定帳戶

可以透過 `Using()` 方法指定使用哪個帳戶發送訊息：

```python
from ErisPulse.Core import adapter
ideaura = adapter.get("ideaura")

# 使用帳戶名發送訊息
await ideaura.Send.Using("default").To("user", "user123").Text("Hello from account 1!")

# 使用 user_id 發送訊息（自動匹配對應帳戶）
await ideaura.Send.Using("456").To("group", "chatroom").Text("Hello from account 2!")

# 不指定時使用第一個啟用的帳戶
await ideaura.Send.To("user", "user123").Text("Hello from default account!")
```

### 事件中的帳戶標識

接收到的事件會自動包含對應的帳戶資訊：

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "ideaura":
        account_id = event["self"]["user_id"]
        print(f"訊息來自帳戶: {account_id}")
```

## 擴展欄位說明

- 所有特有欄位均以 `ideaura_` 前綴標識，避免與標準欄位衝突
- 保留原始數據在 `ideaura_raw` 欄位，便於訪問平台的完整原始數據
- `self.user_id` 表示當前登入帳戶的用戶ID
- `ideaura_source_type`：消息來源類型（`chatroom`/`topic`/`private`）
- `ideaura_sender_name`：發送者暱稱
- `ideaura_sender_avatar`：發送者頭像URL
- `ideaura_sender_is_bot`：發送者是否為機器人
- `ideaura_is_self`：是否為自己發送的消息（自消息已被過濾）
- `ideaura_topic_name`：話題名稱
- `ideaura_message_type`：消息類型（normal/edited/forwarded/quoted）
- `ideaura_message_subtype`：消息子類型（text/image/video/file/markdown/html）

### 文件處理特性

- 文件大小限制：10MB（下載和本地讀取均有限制）
- 自動文件類型檢測：通過文件頭魔術字節檢測實際類型
- 智能文件名解析：對 `.bin`/`.dat`/`.tmp` 等無意義擴展名自動修正
- 支持 bytes、URL、本地路徑三種文件輸入方式
- URL 文件自動下載並上傳到伺服器

### 支援的文件類型

透過魔術字節自動檢測：

| 類型 | 擴展名 |
|------|--------|
| 圖片 | png, jpg, gif, webp |
| 視頻 | mp4, avi, flv |
| 音頻 | mp3, wav, ogg |
| 文件 | pdf, docx |

## 注意事項

1. API 伺服器預設位址為 `https://api.mscpo.com/api/rockychat`（可透過 `base_url` 自訂）；WebSocket 位址 `wss://api-cofe.allons-y.uk:3009/mqtt` 為平台固定位址，不隨適配器名稱變更
2. 適配器使用 WebSocket 長連接接收事件，支援自動重連（固定 5 秒延遲）
3. 自身發送的消息（`isSelf: true`）會被自動過濾，不會產生事件
4. @全體（`AtAll()`）需要管理員權限
5. 檔案上傳大小限制為 10MB
6. 音訊檔案作為 `file` 子類型發送（平台不區分獨立音訊類型）
7. 表情（`Face()`）以純文字形式發送 emoji
8. 程式退出時請呼叫 `shutdown()` 確保資源釋放



### Discord 适配

# Discord 平台特性文件

DiscordAdapter 是基於 Discord Gateway (WebSocket) 和 REST API v10 協議所建構的適配器，整合了 Discord Bot 的核心功能，提供統一的事件處理和訊息操作介面。

---

## 文件資訊

- 對應模組版本: 4.1.0
- 維護者: ErisPulse
- Discord API 版本: v10

## 基本資訊

- 平台簡介：Discord 是一款廣受歡迎的社群通訊平台，支援伺服器、頻道、私訊等多種對話形式，提供完善的 Bot 開發介面
- 適配器名稱：DiscordAdapter
- 多帳號支援：支援同時設定多個 Discord 機器人
- 連接方式：Gateway WebSocket（接收事件）+ REST API（傳送訊息/呼叫介面）
- 認證方式：Bot Token（HTTP 標頭 `Authorization: Bot {token}`，Gateway IDENTIFY payload 攜帶 token）
- 鏈式修飾支援：支援 `.Reply()`、`.At()`、`.AtAll()` 等鏈式修飾方法
- OneBot12 兼容：支援傳送 OneBot12 格式訊息

## 配置說明

DiscordAdapter 支援多帳戶設定，每個帳戶對應一個獨立的 Discord Bot。

```toml
# config.toml

# 帳戶1
[DiscordAdapter.accounts.default]
token = "YOUR_BOT_TOKEN"       # Discord Bot Token（必填）
intents = 33281                 # Gateway Intents（可選，默认 33281）
enabled = true                  # 是否啟用（可選，默认 true）

# 帳戶2
[DiscordAdapter.accounts.bot2]
token = "ANOTHER_BOT_TOKEN"
intents = 33281
enabled = true
```

**設定項說明（每個帳戶）：**

- `token`：Discord Bot Token（必填），從 [Discord Developer Portal](https://discord.com/developers/applications) 獲取
- `intents`：Gateway Intents 位遮罩（可選，默认 `33281`），決定 Bot 訂閱的事件類型
- `bot_id`：Bot 的使用者 ID（可選，執行時從 READY 事件自動獲取，無需手動填寫）
- `enabled`：是否啟用該帳戶（可選，默认 `true`）

### Gateway Intents

Intents 使用位遮罩，計算方式為各 Intent 值按位或（`|`）：

| Intent | 位 | 值 | 說明 | Privileged |
|-------|------|------|------|------|
| GUILDS | `1 << 0` | 1 | 伺服器建立/刪除/更新、頻道、角色變更 | 否 |
| GUILD_MEMBERS | `1 << 1` | 2 | 成員加入/離開/更新 | 是 |
| GUILD_MESSAGES | `1 << 9` | 512 | 伺服器訊息收發 | 否 |
| MESSAGE_CONTENT | `1 << 15` | 32768 | 訊息內容（無此 Intent 時 content 為空） | 是 |

預設值 `33281` = `GUILDS(1) | GUILD_MESSAGES(512) | MESSAGE_CONTENT(32768)`。

> **注意**：Privileged Intents 需在 Discord Developer Portal → Bot → Privileged Gateway Intents 中開啟。如果 Bot 在超過 100 個伺服器中，還需透過 Discord 審核。

**API 環境：**
- Discord REST API 基本位址：`https://discord.com/api/v10`
- Gateway WebSocket 位址：透過 `GET /gateway/bot` 動態獲取，通常為 `wss://gateway.discord.gg/?v=10&encoding=json`

## 支援的消息傳送類型

所有傳送方法均透過鏈式語法實現，例如：
```python
from ErisPulse.Core import adapter
discord = adapter.get("discord")

await discord.Send.To("group", channel_id).Text("Hello World!")
```

支援的傳送類型包括：
- `.Text(text: str)`：傳送純文字訊息。
- `.Embed(embed: dict | list)`：傳送 Embed 嵌入訊息，支援單個或多個 Embed。
- `.Image(file: bytes | str, filename: str = "image.png")`：傳送圖片，支援二進位資料或 URL。
- `.File(file: bytes | str, filename: str = None)`：傳送檔案，支援二進位資料或 URL。
- `.Reply(content: str, message_id: str)`：回覆指定訊息（便捷終端方法）。
- `.Raw_ob12(message: List[Dict], **kwargs)`：傳送 OneBot12 格式訊息。
- `.Raw_json(json_str: str)`：傳送任意 Discord API 請求 JSON。

### 鏈式修飾方法（可組合使用）

鏈式修飾方法返回 `self`，支援鏈式呼叫，必須在最終傳送方法前呼叫：

- `.Reply(message_id: str)`：回覆（引用）指定訊息，設定 `message_reference`。
- `.At(user_id: str)`：@指定使用者，轉換為 `<@user_id>`，可多次呼叫。
- `.AtAll()`：@所有人，轉換為 `@everyone`。

### 鏈式呼叫範例

```python
# 基礎傳送
await discord.Send.To("group", channel_id).Text("Hello")

# 回覆訊息
await discord.Send.To("group", channel_id).Reply(msg_id).Text("回覆訊息")

# 便捷回覆（一步到位）
await discord.Send.To("group", channel_id).Reply("回覆內容", msg_id)

# @使用者
await discord.Send.To("group", channel_id).At("user_id").Text("你好")

# @多個使用者
await discord.Send.To("group", channel_id).At("user1").At("user2").Text("多使用者@")

# @全體
await discord.Send.To("group", channel_id).AtAll().Text("公告")

# 組合使用
await discord.Send.To("group", channel_id).Reply(msg_id).At("user_id").Text("複合訊息")

# Embed 嵌入訊息
embed = {
    "title": "通知",
    "description": "這是一條嵌入訊息",
    "color": 5814783,
    "fields": [{"name": "字段", "value": "值", "inline": True}],
}
await discord.Send.To("group", channel_id).Embed(embed)

# 發送圖片
await discord.Send.To("group", channel_id).Image("https://example.com/image.png")
```

### 私訊傳送

私訊傳送時，適配器會自動建立 DM 頻道：

```python
# 發送私訊
await discord.Send.To("user", user_id).Text("私訊內容")
await discord.Send.To("user", user_id).Embed(embed)
```

### 訊息操作

```python
# 撤回訊息
await discord.Send.To("group", channel_id).Recall(msg_id)

# OneBot12 格式
ob12_msg = [
    {"type": "text", "data": {"text": "Hello "}},
    {"type": "mention", "data": {"user_id": "user_id"}},
]
await discord.Send.To("group", channel_id).Raw_ob12(ob12_msg)
```

## 發送方法返回值

所有發送方法均返回一個 Task 對象，可以直接 await 獲取發送結果。返回結果遵循 ErisPulse 适配器标准化返回规范：

```python
{
    "status": "ok",           // 執行狀態: "ok" 或 "failed"
    "retcode": 0,             // 返回碼（0 為成功）
    "data": {...},            // Discord API 原始響應
    "message_id": "xxx",      // 消息ID（發送消息時）
    "message": "",            // 錯誤信息
    "discord_raw": {...}      // 原始響應數據
}
```

### 錯誤碼說明

| retcode | 說明 |
|---------|------|
| 0 | 成功 |
| 33001 | 網路錯誤（連接失敗、超時等） |
| 34000 | Discord API 返回錯誤（權限不足、參數錯誤等） |

## 特有事件類型

需要 `platform == "discord"` 檢測再使用本平台特性。

### 核心差異點

1. **伺服器/頻道系統**：Discord 使用伺服器（Guild）和頻道（Channel）兩層結構，頻道是訊息的基本發送目標
2. **Gateway 事件**：所有事件透過 WebSocket Gateway 接收，使用 Opcode + Dispatch 機制
3. **Intents 訂閱**：透過位掩碼訂閱事件類型，`MESSAGE_CONTENT` 需 Privileged 權限
4. **訊息段類型**：支援文字、圖片、檔案、影片、音訊、Embed、Sticker 等訊息段
5. **Mention 格式**：Discord 使用 `<@user_id>` 格式表示使用者提及

### 擴展欄位

所有特有欄位均以 `discord_` 前綴標識：
- `discord_raw`：原始 Discord 事件資料
- `discord_raw_type`：原始事件類型名（如 `MESSAGE_CREATE`）
- `discord_guild_id`：伺服器 ID
- `discord_channel_id`：頻道 ID

### detail_type 映射

| Discord 場景 | detail_type | 說明 |
|---|---|---|
| 頻道訊息 | `channel` | ErisPulse 擴展類型 |
| 私信（DM） | `private` | OneBot12 標準類型 |

### 事件類型映射

| Discord 事件 | OneBot12 type | detail_type | 說明 |
|---|---|---|---|
| MESSAGE_CREATE | message | channel/private | 訊息建立 |
| MESSAGE_UPDATE | message | channel/private | 訊息編輯 |
| MESSAGE_DELETE | notice | group_message_delete / private_message_delete | 訊息刪除 |
| GUILD_MEMBER_ADD | notice | group_member_increase | 成員加入 |
| GUILD_MEMBER_REMOVE | notice | group_member_decrease | 成員離開 |
| GUILD_MEMBER_UPDATE | notice | group_member_update | 成員資訊更新 |
| GUILD_ROLE_CREATE | notice | group_role_create | 角色建立 |
| GUILD_ROLE_DELETE | notice | group_role_delete | 角色刪除 |
| CHANNEL_CREATE | notice | channel_create | 頻道建立 |
| CHANNEL_DELETE | notice | channel_delete | 頻道刪除 |
| INTERACTION_CREATE | request | interaction | 互動（按鈕、命令等） |

### 特殊欄位範例

```python
# 頻道文字訊息
{
  "type": "message",
  "detail_type": "channel",
  "user_id": "發送者ID",
  "user_nickname": "使用者名稱",
  "group_id": "頻道ID",
  "message_id": "訊息ID",
  "discord_raw": {...},
  "discord_raw_type": "MESSAGE_CREATE",
  "discord_guild_id": "伺服器ID",
  "discord_channel_id": "頻道ID",
  "message": [
    {"type": "text", "data": {"text": "Hello"}}
  ],
  "alt_message": "Hello"
}

# 私訊
{
  "type": "message",
  "detail_type": "private",
  "user_id": "發送者ID",
  "user_nickname": "使用者名稱",
  "message_id": "訊息ID",
  "discord_raw": {...},
  "discord_raw_type": "MESSAGE_CREATE",
  "discord_channel_id": "DM頻道ID",
  "message": [
    {"type": "text", "data": {"text": "私訊內容"}}
  ],
  "alt_message": "私訊內容"
}

# 帶 Embed 的訊息
{
  "type": "message",
  "detail_type": "channel",
  "message": [
    {"type": "discord_embed", "data": {"embed": {...}}}
  ],
  "alt_message": "[嵌入訊息]"
}

# 帶附件的訊息
{
  "type": "message",
  "detail_type": "channel",
  "message": [
    {"type": "text", "data": {"text": "看這張圖"}},
    {"type": "image", "data": {"file": "圖片URL", "url": "圖片URL", "file_name": "image.png"}}
  ],
  "alt_message": "看這張圖[圖片]"
}
```

### 訊息段類型

Discord 訊息內容根據 `content`、`attachments`、`embeds` 欄位自動轉換為對應訊息段：

| 來源 | 轉換類型 | 說明 |
|---|---|---|
| content 文字 | `text` | 純文字內容 |
| content `<@id>` | `mention` | 使用者提及 |
| content `<@&id>` | `discord_role_mention` | 角色提及 |
| content `<#id>` | `discord_channel_mention` | 頻道提及 |
| attachments (image/*) | `image` | 圖片附件 |
| attachments (video/*) | `video` | 影片附件 |
| attachments (audio/*) | `audio` | 音訊附件 |
| attachments (其他) | `file` | 檔案附件 |
| embeds | `discord_embed` | 嵌入訊息 |
| sticker_items | `discord_sticker` | 貼紙 |

### discord_embed 訊息段

```json
{
  "type": "discord_embed",
  "data": {
    "embed": {
      "title": "標題",
      "description": "描述",
      "color": 12345,
      "fields": [...],
      "image": {"url": "..."},
      "thumbnail": {"url": "..."},
      "footer": {"text": "..."}
    }
  }
}
```

## 網關連接

### 連接流程

1. 呼叫 `GET /gateway/bot` 以取得 WebSocket 網關 URL
2. 連接到 `wss://gateway.discord.gg/?v=10&encoding=json`
3. 收到 opcode 10 HELLO：包含 `heartbeat_interval`
4. 發送 opcode 2 IDENTIFY：攜帶 token、intents、properties
5. 開始心跳循環：依照 `heartbeat_interval` 定時發送 opcode 1 Heartbeat
6. 收到 opcode 0 Dispatch：事件分發（`t`=事件名, `s`=序號, `d`=資料）
7. 收到 opcode 11 Heartbeat ACK：心跳確認

### Opcode 說明

| Opcode | 名稱 | 方向 | 說明 |
|--------|------|------|------|
| 0 | Dispatch | 接收 | 事件分發（含 `t`、`s`、`d` 欄位） |
| 1 | Heartbeat | 發送/接收 | 心跳（攜帶最後 seq） |
| 2 | Identify | 發送 | 身份驗證 |
| 6 | Resume | 發送 | 恢復會話 |
| 7 | Reconnect | 接收 | 伺服器要求重連 |
| 9 | Invalid Session | 接收 | 無效會話 |
| 10 | Hello | 接收 | 連接握手（含 heartbeat_interval） |
| 11 | Heartbeat ACK | 接收 | 心跳確認 |

### 斷線重連與 RESUME

- 連接斷開後，適配器自動重試連接
- 如果之前有 `session_id`，優先嘗試 RESUME（opcode 6）恢復會話
- RESUME 攜帶 `token`、`session_id`、最後 `seq`，恢復後補發遺漏事件
- 收到 opcode 7（Reconnect）時，保持會話狀態並重連
- 收到 opcode 9（Invalid Session）且 `d=false` 時，清除會話並重新 IDENTIFY

### 心跳機制

- 收到 HELLO 後，等待 `heartbeat_interval * random()` 毫秒發送首次心跳
- 此後每隔 `heartbeat_interval` 毫秒發送一次心跳
- 心跳攜帶最後的 `seq` 值（opcode 1，`d: seq`）
- 若發送心跳後 `heartbeat_interval` 內未收到 ACK（opcode 11），視為連接異常並重連

## 使用示例

### 處理頻道訊息

```python
from ErisPulse.Core.Event import message
from ErisPulse import sdk

discord = sdk.adapter.get("discord")

@message.on_message()
async def handle_group_msg(event):
    if event.get("platform") != "discord":
        return

    text = event.get_text()
    channel_id = event.get("group_id")

    if text == "hello":
        await discord.Send.To("group", channel_id).Text("Hello!")
```

### 處理私訊

```python
@message.on_message()
async def handle_private_msg(event):
    if event.get("platform") != "discord":
        return
    if not event.is_dm():
        return

    text = event.get_text()
    user_id = event.get("user_id")

    await discord.Send.To("user", user_id).Text(f"你說了: {text}")
```

### 發送 Embed 訊息

```python
embed = {
    "title": "伺服器公告",
    "description": "歡迎使用 ErisPulse Discord 适配器",
    "color": 3447003,
    "fields": [
        {"name": "版本", "value": "4.0.0", "inline": True},
        {"name": "框架", "value": "ErisPulse", "inline": True},
    ],
    "footer": {"text": "Powered by ErisPulse"},
    "timestamp": "2025-01-01T00:00:00.000Z",
}
await discord.Send.To("group", channel_id).Embed(embed)
```

### 使用 Discord 特有方法

```python
@message.on_message()
async def handle(event):
    if event.get("platform") != "discord":
        return

    channel_id = event.get_channel_id()
    guild_id = event.get_guild_id()
    is_dm = event.is_dm()
    embeds = event.get_embeds()
    attachments = event.get_attachments()

    if embeds:
        await discord.Send.To("group", channel_id).Text(
            f"收到 {len(embeds)} 個 Embed"
        )
```

### 處理互動事件

```python
from ErisPulse.Core.Event import request

@request.on_request()
async def handle_interaction(event):
    if event.get("platform") != "discord":
        return

    interaction = event.get_interaction_data()
    if interaction.get("type") == 3:  # MESSAGE_COMPONENT
        await event.reply("按鈕已點擊！")
```



### Webhook 适配

# 平台特性說明 — Webhook 通用橋接適配器

本文檔詳細說明 Webhook 适配器的雙向橋接協議、欄位映射與實現特性。

## 總覽

Webhook 适配器是一個**協議級橋接器**，不綁定任何特定平台。它透過 HTTP 收發訊息，使任何能發起 HTTP 請求的系統都能接入 ErisPulse。

```
入站方向                                出站方向
────────                                ────────
外部系統                                ErisPulse 模組
   │                                       │
   │ POST JSON                             │ Send.Text(...)
   ▼                                       ▼
┌──────────────────────────────────────────────────┐
│              WebhookAdapter                       │
│  ┌──────────────────┐   ┌──────────────────┐    │
│  │ 入站路由          │   │ 出站轉發          │    │
│  │ GET  (健康檢查)   │   │ client.post()    │    │
│  │ POST (接收事件)   │   │ → outgoing_url   │    │
│  └────────┬─────────┘   └────────▲─────────┘    │
│           │                      │               │
│           ▼                      │               │
│  ┌──────────────────┐   ┌──────────────────┐    │
│  │ WebhookConverter │   │ Send 類          │    │
│  │ JSON → OneBot12  │   │ 消息段 → JSON    │    │
│  └────────┬─────────┘   └────────▲─────────┘    │
└───────────┼──────────────────────┼───────────────┘
            ▼                      │
     adapter.emit(event)    call_api("send_message")
            │                      │
            ▼                      │
       ErisPulse 事件系統 ◄────────┘
```

## 多帳戶模型

每個帳戶是一個獨立的橋接配置，互不干擾：

| 帳戶 | bot_id | callback_path | outgoing_url | secret |
|------|--------|---------------|--------------|--------|
| `default` | `webhook_bot` | `/webhook/default` | `https://a.com/recv` | `key1` |
| `discord` | `discord_bot` | `/webhook/discord` | `https://b.com/send` | `key2` |

每個帳戶啟動時獨立註冊路由、獨立 emit connect。

## 入站協議

### 1. 健康檢查（GET）

- **路徑**：`{callback_path}`
- **方法**：`GET`
- **鑑權**：無
- **回應**：

```json
{"status": "ok", "account": "default"}
```

### 2. 接收事件（POST）

- **路徑**：`{callback_path}`
- **方法**：`POST`
- **Content-Type**：`application/json`
- **鑑權**（配置 secret 時）：Header `X-Webhook-Secret` 或 Query `?secret=`

#### 請求 Body

```json
{
  "user_id": "u123",
  "user_nickname": "使用者名稱",
  "group_id": "群組ID（僅群組會話）",
  "detail_type": "private",
  "message": [
    {"type": "text", "data": {"text": "訊息內容"}}
  ],
  "raw": {}
}
```

| 欄位 | 必填 | 說明 |
|------|------|------|
| `user_id` | 是 | 發送者 ID |
| `user_nickname` | 否 | 發送者暱稱 |
| `group_id` | 否 | 群組/頻道 ID（群組會話時提供） |
| `detail_type` | 否 | 會話類型（`private`/`group`），預設用帳戶預設值 |
| `message` | 是 | OneBot12 消息段陣列 |
| `raw` | 否 | 原始資料，原樣存入 `webhook_raw` |

#### 回應

```json
{"status": "ok"}
```

錯誤回應帶 HTTP 狀態碼：

| 狀態碼 | 含義 |
|--------|------|
| 400 | 無效 JSON / body 非物件 |
| 401 | 鑑權失敗 |
| 404 | 未知帳戶 |
| 500 | 事件分發失敗 |

### 3. 欄位映射（入站 JSON → OneBot12 事件）

| 入站 JSON | OneBot12 事件欄位 | 說明 |
|-----------|-------------------|------|
| — | `id` | 自動產生 |
| — | `time` | 當前 Unix 時間戳（秒） |
| — | `type` | 固定 `message` |
| `detail_type` | `detail_type` | 預設用帳戶預設值 |
| — | `platform` | 固定 `webhook` |
| — | `self.platform` | 固定 `webhook` |
| — | `self.user_id` | 帳戶 `bot_id` |
| `user_id` | `user_id` | 傳遞 |
| `user_nickname` | `user_nickname` | 傳遞（可選） |
| `group_id` | `group_id` | 傳遞（可選） |
| `message` | `message` | 傳遞 |
| 完整 body | `webhook_raw` | 原始請求 |
| 帳戶名 | `webhook_account` | 產生事件的帳戶名 |
| `type` 或 `message` | `webhook_raw_type` | 原始事件類型 |

## 出站協議

### 1. 發送訊息

當模組調用 `Send.To(...).Text(...)` 等方法時，適配器向 `outgoing_url` 發起 POST：

- **方法**：`POST`
- **Content-Type**：`application/json`
- **鑑權 Header**（配置 secret 時）：`X-Webhook-Secret: {secret}`

#### 請求 Body

```json
{
  "target_type": "private",
  "target_id": "target_user_id",
  "account": "default",
  "message": [
    {"type": "text", "data": {"text": "訊息內容"}}
  ],
  "timestamp": 1700000000
}
```

| 欄位 | 說明 |
|------|------|
| `target_type` | 目標類型（來自 `Send.To(type, id)`），預設用帳戶預設值 |
| `target_id` | 目標 ID（來自 `Send.To`） |
| `account` | 發送帳戶名 |
| `message` | OneBot12 消息段陣列 |
| `timestamp` | 發送時間戳（秒） |

### 2. 回應標準化

適配器把出站目標返回的回應標準化為 ErisPulse 標準回應格式：

```json
{
  "status": "ok",
  "retcode": 0,
  "data": {"message_id": "...", ...},
  "message_id": "...",
  "message": "",
  "webhook_raw": {}
}
```

從目標回應 JSON 的 `message_id` 欄位提取訊息 ID。若目標未返回 `message_id`，則為空字串。

請求失敗時返回錯誤回應（`status: "failed"`, `retcode: 33001`）。

## Send 方法

| 方法 | 說明 |
|------|------|
| `Text(text)` | 發送文字，封裝為 `[{"type":"text","data":{"text":text}}]` |
| `Image(file)` | 發送圖片，封裝為 `[{"type":"image","data":{"file":file}}]` |
| `Raw_ob12(message)` | 發送 OneBot12 原始消息段 |
| `Json(data)` | 原始 JSON 傳遞，封裝為 `[{"type":"json","data":{"raw":data}}]` |

`At` / `AtAll` / `Reply` 修飾器由框架基類提供，透過 `_apply_modifiers` 合併到消息段。

## 事件擴展方法（WebhookEventMixin）

| 方法 | 說明 |
|------|------|
| `get_raw_data()` | 取得原始請求 body（`webhook_raw`） |
| `get_detail_type()` | 取得會話類型 |
| `get_webhook_account()` | 取得產生該事件的帳戶名 |

## 特性矩陣

| 特性 | 支援情況 |
|------|----------|
| 多帳戶 | ✅ 每個帳戶獨立橋接 |
| 入站鑑權 | ✅ Header / Query 雙模式 |
| 健康檢查 | ✅ GET 返回狀態 |
| 出站鑑權 | ✅ Header 攜帶 secret |
| OneBot12 標準事件 | ✅ 完整標準欄位 |
| Meta 事件 | ✅ connect / disconnect |
| 路由發現 | ✅ 注冊到 `webhook` 命名空間 |
| WebSocket | ❌ 僅 HTTP |
| 媒體上傳 | ❌ 透過 URL 傳遞，不代傳二進位 |

## 注意事項

1. **單向出站**：若 `outgoing_url` 留空，該帳戶僅作入站接收，發送操作會返回錯誤
2. **密鑰安全**：`secret` 在配置中以密文儲存（metadata secret），傳輸建議使用 HTTPS
3. **路徑唯一**：多個帳戶的 `callback_path` 必須互不相同，避免路由衝突
4. **冪等性**：適配器不保證入站事件去重，外部系統應自行處理重試
5. **超時**：出站請求使用 ErisPulse 內建 `client`，繼承全域超時配置



### 微信公众号适配

# 微信公眾號 (WechatMp) 適配器 - 平台特性文件



## 基本資訊
- 模組名稱: `ErisPulse-WechatMpAdapter`
- 平台標識: `mp`（別名: `wechat_mp`）
- 模組版本: 4.1.0
- 維護者: ErisPulse
- 依賴: `cryptography`


## 支援的消息傳送類型

| 方法 | 說明 | 微信 API |
|------|------|---------|
| `Text(text)` | 發送文字 | 客服消息 `message/custom/send` |
| `Image(file)` | 發送圖片（自動上傳獲取 media_id） | 客服消息 + `media/upload` |
| `Voice(file)` | 發送語音（自動上傳獲取 media_id） | 客服消息 + `media/upload` |
| `Video(file, title, description)` | 發送影片（自動上傳獲取 media_id） | 客服消息 + `media/upload` |
| `Music(url, title, description, ...)` | 發送音樂 | 客服消息 |
| `News(articles)` | 發送圖文消息 | 客服消息 |
| `Template(template_id, data, url)` | 發送模板消息 | `message/template/send` |
| `Menu(head_content, list, tail_content)` | 發送選單消息 | 客服消息 `msgmenu` |
| `Raw_ob12(message)` | 發送 OneBot12 標準消息段 | - |

### 媒體文件說明
- 支援三種參數類型：
  - `str` URL（以 `http://` / `https://` 開頭）：自動下載後上傳
  - `str` 本地檔案路徑：自動讀取後上傳
  - `bytes` 二進位資料：直接上傳
  - `str` media_id：以 `media:` 前綴可直接重用已上傳的 media_id
- 上傳後獲得臨時素材 `media_id`，有效期 3 天

### 重要限制
- 客服消息只能在用戶與公眾號互動後 **48 小時內** 主動發送
- 超過 48 小時需使用模板消息（需用戶授權場景）
- 未認證服務號（`verified=false`）無法主動發送，只能被動回覆（見上方「認證服務號與被動回覆」）

## 事件類型

### 消息事件 (message)
所有使用者訊息均為 `detail_type: private`（公眾號 1v1 場景）。

| 微信 MsgType | 消息段類型 | 說明 |
|-------------|-----------|------|
| `text` | `text` | 文字訊息 |
| `image` | `image` | 圖片訊息 |
| `voice` | `voice` | 語音訊息（含語音辨識結果） |
| `video` | `video` | 影片訊息 |
| `shortvideo` | `video` | 小影片（標記 `mp_shortvideo`） |
| `location` | `location` | 地理位置訊息 |
| `link` | `text` | 鏈接訊息（轉為文字） |

### 通知事件 (notice)
事件透過 `mp_event` 欄位區分具體類型。

| 微信 Event | `mp_event` | 說明 |
|-----------|-----------|------|
| `subscribe` | `subscribe` | 關注公眾號 |
| `unsubscribe` | `unsubscribe` | 取消關注 |
| `SCAN` | `scan` | 掃描帶參數二維碼 |
| `LOCATION` | `location_report` | 上報地理位置 |
| `CLICK` | `menu_click` | 自訂選單點擊 |
| `VIEW` | `menu_view` | 選單跳轉連結 |
| `TEMPLATESENDJOBFINISH` | `template_send_finish` | 模板訊息發送結果 |
| `MASSSENDJOBFINISH` | `mass_send_finish` | 群發訊息發送結果 |

## 平台擴展欄位

事件物件中的微信特有欄位（`mp_` 前綴）：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `mp_raw` | str | 原始 XML 數據 |
| `mp_raw_type` | str | 原始消息/事件類型 |
| `mp_msg_id` | str | 微信消息 ID |
| `mp_event` | str | 事件類型（僅事件通知） |
| `mp_event_key` | str | 事件 Key（選單點擊/掃描等） |
| `mp_to_user` | str | 接收方微信號（公眾號原始 ID） |
| `mp_from_user` | str | 發送方 OpenID |
| `mp_data` | dict | 解析後的 XML 字典數據 |


## 事件擴展方法

透過 `register_event_mixin("mp", ...)` 註冊後，在事件物件上可直接呼叫：

| 方法 | 返回值 | 說明 |
|------|--------|------|
| `get_openid()` | str | 發送者 OpenID |
| `get_msg_type()` | str | 微信原始消息類型 |
| `get_event()` | str | 事件類型（僅事件通知） |
| `get_content()` | str | 消息純文字內容 |
| `get_raw_xml()` | str | 原始 XML 數據 |



## 配置選項

### 多帳號配置

每個帳號對應一個公眾號：

```toml
[WechatMpAdapter.accounts.main]
appid = "wx1234567890abcdef"
appsecret = "your_app_secret_here"
token = "your_callback_token"
encoding_aes_key = ""                    # 安全模式/兼容模式才需要（43位）
callback_path = "/mp/main"               # 回調路徑
verified = true                          # 是否為認證服務號（影響主動發送能力）
enable = true

[WechatMpAdapter.accounts.secondary]
appid = "wx0987654321fedcba"
appsecret = "another_app_secret"
token = "another_callback_token"
callback_path = "/mp/secondary"
enable = true
```

### 配置字段說明

| 字段 | 必填 | 說明 |
|------|------|------|
| `appid` | 是 | 公眾號 AppID |
| `appsecret` | 是 | 公眾號 AppSecret（secret） |
| `token` | 否 | 回調驗證 Token（建議填寫以啟用簽名驗證） |
| `encoding_aes_key` | 否 | 消息加解密密鑰（43位，安全模式必需） |
| `callback_path` | 否 | 回調路徑模板，預設 `/mp/{account}`，`{account}` 會被帳號名替換 |
| `verified` | 否 | 是否為**認證服務號**，預設 `true`（見下方說明） |
| `enable` | 否 | 是否啟用，預設 true |

### 認證服務號與被動回覆（verified）

- `verified = true`（預設，認證服務號）：可隨時使用**客服消息**主動推送（48 小時視窗內）與模板消息
- `verified = false`（未認證訂閱號）：
  - 客服消息 / 模板消息**只能在 webhook 被動回覆上下文中發送**（收到用戶消息後 15 秒內、一次回覆）——適配器會自動將發送截獲為被動回覆
  - 主動推送（如定時任務）返回 `retcode=34003` 錯誤

## 加密模式說明

微信公眾號提供三種訊息加解密模式：

| 模式 | 說明 | encoding_aes_key | 驗證欄位 |
|------|------|-----------------|---------|
| 明文模式 | XML 明文傳輸 | 不需要 | `signature` |
| 兼容模式 | 明文+密文同時存在 | 可選 | `signature` / `msg_signature` |
| 安全模式 | 全部加密 | 必需 | `msg_signature` |

本適配器自動處理：
- 明文模式：驗證 `signature`，直接解析 XML
- 安全/兼容模式：檢測 `Encrypt` 欄位，驗證 `msg_signature`，使用 AES-256-CBC 解密
- 解密依賴 `cryptography` 庫（已宣告在 dependencies 中）


## 回調路由

適配器為每個已啟用帳戶註冊兩個路由（GET + POST）：

- **GET**：微信伺服器接入驗證，驗證簽名後返回 `echostr`
- **POST**：接收使用者訊息和事件，驗證簽名→解密（如需）→轉換→emit

實際訪問路徑會自動添加模組前綴，例如註冊路徑 `/mp/main`，
實際訪問路徑為 `/mp_{account}_verify/mp/main` 和 `/mp_{account}_message/mp/main`。

## API 回應

所有 `call_api` 調用返回標準化響應：

- 成功：`status: "ok"`, `retcode: 0`
- 失敗：`status: "failed"`, `retcode: 34000+errcode`
- 始終包含 `mp_raw`（原始響應）、`message_id`

[**返回頂部**](docs/zh-TW/quick-start.md)



====
代码规范
====


### 文档字符串规范

# ErisPulse 註解風格規範

在建立 EP 核心方法時，必須新增方法註解，註解格式如下：

## 模組層級文件註解

每個模組檔案開頭應包含模組文件註解：
```python
"""
[模組名稱]
[模組功能描述]

{!--< tips >!--}
重要使用說明或注意事項
{!--< /tips >!--}
"""
```

## 方法註解

### 基本格式
```python
def func(param1: type1, param2: type2) -> return_type:
    """
    [功能描述]
    
    :param param1: [類型1] [參數描述1]
    :param param2: [類型2] [參數描述2]
    :return: [返回類型] [返回描述]
    """
    pass
```

### 完整格式（適用於複雜方法）
```python
def complex_func(param1: type1, param2: type2 = None) -> Tuple[type1, type2]:
    """
    [功能詳細描述]
    [可包含多行描述]
    
    :param param1: [類型1] [參數描述1]
    :param param2: [類型2] [可選參數描述2] (預設: None)
    
    :return: 
        type1: [返回參數1描述]
        type2: [返回參數2描述]
    
    :raises ErrorType: [錯誤描述]
    """
    pass
```

## 特殊標籤（用於 API 文件生成）

當方法註解包含以下內容時，將在 API 文件建置時產生對應效果：

| 標籤格式 | 作用 | 範例 |
|---------|------|------|
| `{!--< internal-use >!--}` | 標記為內部使用，不生成文件 | `{!--< internal-use >!--}` |
| `{!--< ignore >!--}` | 忽略此方法，不生成文件 | `{!--< ignore >!--}` |
| `{!--< deprecated >!--}` | 標記為已棄用方法 | `{!--< deprecated >!--} 請使用new_func()取代` |
| `{!--< experimental >!--}` | 標記為實驗性功能 | `{!--< experimental >!--} 可能不穩定` |
| `{!--< tips >!--}...{!--< /tips >!--}` | 多行提示內容 | `{!--< tips >!--}\n重要提示內容\n{!--< /tips >!--}` |
| `{!--< tips >!--}` | 單行提示內容 | `{!--< tips >!--} 注意: 此方法需要先初始化` |

## 最佳建議

1. **類型標註**：使用 Python 類型標註語法
   ```python
   def func(param: int) -> str:
   ```

2. **參數說明**：對可選參數註明預設值
   ```python
   :param timeout: [int] 超時時間(秒) (預設: 30)
   ```

3. **回傳值**：多回傳值使用 `Tuple` 或明確說明
   ```python
   :return: 
       str: 狀態資訊
       int: 狀態碼
   ```

4. **異常說明**：使用 `:raises:` 標註可能拋出的異常
   ```python
   :raises ValueError: 當參數無效時拋出
   ```

5. **內部方法**：非公開 API 應新增 `{!--< internal-use >!--}` 標籤

6. **已棄用方法**：標記已棄用方法並提供替代方案
   ```python
   {!--< deprecated >!--} 請使用new_method()取代 | 2025-07-09

