---
name: erispulse-communication
description: "适用于：模块间通信（RPC/定向/广播）、HTTP/WS 客户端、连接管理。覆盖场景：**什麼時候需要閱讀這篇**：需要跨模組呼叫（RPC）、服務契約、定向事件或冷啟動回放時。不需要則跳過，不會影響其他功能的使用。**何時需要閱讀本文**：當需要 WebSocket/SSE 連接池、廣播分組、跨模組推送，或查看連接狀態時。若無此需求則可跳過，不會影響其他功能的使用。**什麼時候需要閱讀這篇**：需要 HTTP / WebSocket / SSE 路由（含連接池廣播）時。不需要則跳過，不會影響其他功能的使用。"
---

# ErisPulse 通信与连接

This skill is auto-built from the ErisPulse documentation.
Repository: https://github.com/ErisPulse/ErisPulse
Source paths are annotated per section; see docs/ in the repository for the latest content.

## 内容大纲

AI 按需读取：只读需要的章节即可，不必全文加载。

- 模块间通信: 56-85 行
- RPC：module.call: 87-114 行
- 服務契約：meta.services: 116-184 行
- 服務目錄：services(): 186-208 行
- 出站審計：誰能呼叫誰: 210-224 行
- 定向事件：lifecycle.emit 的 to 參數: 226-257 行
- 慢載與呼叫: 259-270 行
- 冷啟動回放: 272-303 行
- 事件冪等去重: 305-314 行
- 相關文件: 316-322 行
- 连接管理: 324-344 行
- 概述: 346-372 行
- 查看連接池: 374-398 行
- 廣播與訂閱: 400-463 行
- 跨模組傳遞 / 復用: 465-490 行
- 出站連接（Client 側）: 492-506 行
- 跨執行緒投遞: 508-523 行
- 卸載與清理語意: 525-533 行
- API 一覽: 535-549 行
- 相關文件: 551-556 行
- 路由: 558-567 行
- 概述: 569-584 行
- 抽象類型: 586-598 行
- 裝飾器路由（推薦）: 600-719 行
- 傳統註冊方式: 721-786 行
- WebSocket 生命週期鉤子: 788-810 行
- 路由分組: 812-827 行
- 路由中間件: 829-844 行
- 請求關聯 ID（X-Request-ID）: 846-869 行
- 速率限制: 871-885 行
- CORS 配置: 887-904 行
- 安全標頭: 906-919 行
- 自動文檔: 921-935 行
- 路徑處理: 937-948 行
- 系統路由: 950-969 行
- 主頁入口: 971-1008 行
- 生命週期集成: 1010-1022 行
- 最佳實踐: 1024-1032 行
- 相關文件: 1034-1039 行

## 模块间通信

> 来源: `docs/zh-TW/advanced/module-communication.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-TW/advanced/module-communication.md）

# 模塊間通信

> [!TIP]
> **什麼時候需要閱讀這篇**：需要跨模組呼叫（RPC）、服務契約、定向事件或冷啟動回放時。不需要則跳過，不會影響其他功能的使用。

> **讀完你會知道**：三層通信模型（RPC / 定向事件 / 廣播）的選型口訣、
> `meta.services` 服務契約與服務目錄、出站審計的配置方式、懶喚醒與冷啟動回放。
>
> **本篇不涉及**：生命週期事件系統本身的註冊 / 觸發 / 優先級機制
> （見[生命週期管理](lifecycle.md)）；懶加載的配置與 activate_on 聲明
> （見[懶加載系統](lazy-loading.md)）。

> [!NOTE]
> 本章內容需要 ErisPulse **2.8.0+**。

ErisPulse 的模組之間有**三層通信模型**，依「點對點 → 定向 → 廣播」排列：

| 層 | API | 語義 | 典型場景 |
|---|---|---|---|
| **RPC** | `await sdk.module.call("Chat", "get_history", ...)` | 點對點請求-回應，帶契約 / 審計 / 超時 | 呼叫另一模組的能力（查詢歷史、翻譯、退款） |
| **定向事件** | `await lifecycle.emit("message_received", {...}, to="Chat")` | 僅分發給指定模組註冊的生命週期鉤子 | 上游狀態變化的通知下游（「收到新訊息了」） |
| **廣播** | `await lifecycle.emit("config.updated", {...})` | 全框架可見的生命週期事件 | 配置熱更新、模組上下線 |

{!--< tips >!--}
選型口訣：**要回傳值用 `call`，只通知一個模組的鉤子用 `emit(..., to=...)`，通知所有人用 `emit(...)`**。
{!--< /tips >!--}

## RPC：module.call

```python
result = await sdk.module.call("Chat", "get_history", session_id, n=20)
```

與裸屬性存取 `sdk.module.Chat.get_history(...)`（保持不變）的差異：

| | `module.call()` | 裸屬性存取 |
|---|---|---|
| 目標未註冊 / 未啟用 | 抛 `ModuleNotAvailableError` | 抛 `AttributeError` |
| 慢載入模組 | **自動喚醒**（事件驅動模組走激活鎖） | 異步初始化模組拋 RuntimeError |
| `current_owner` | 歸因到**目標模組**（其內部 wait_reply / 發送 / 日誌正確歸屬） | 保持呼叫方 |
| 超時 | 預設 30 秒（`timeout=` 覆蓋，None 不限時） | 無 |
| scope 審計 | 呼叫方過出站閘口 `actions.<呼叫方>.call` | 無 |
| 契約校驗 | `meta.services` 白名單 | 無 |

### 異常體系

```
ModuleError                      # 模組系統異常基類
└── ModuleCallError              # 跨模組呼叫基類（含 module / method 屬性）
    ├── ModuleNotAvailableError  # 目標未註冊 / 未啟用 / 喚醒失敗
    ├── ServiceNotProvidedError  # 方法不在 services 白名單 / 私有方法 / 不存在
    └── ModuleCallTimeoutError   # 協程方法超時
```

均掛在 `ErisPulseError` 體系下，可 `from ErisPulse.Core import ModuleCallError` 捕獲。

## 服務契約：meta.services

服務方在 `get_meta()` 中宣告所提供的白名單（與 `commands` 欄位對稱）：

```python
from ErisPulse.Core.Bases import BaseModule, ModuleMeta

class ChatModule(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(
            name="聊天",
            services=[
                "get_history",                                       # 簡單形態
                {"name": "translate", "description": "把文本翻譯成指定語言"},  # 帶介紹
            ],
        )

    async def get_history(self, session_id, n=20): ...
    async def translate(self, text, target_lang): ...
    def _internal_helper(self): ...   # 下劃線方法始終禁止被外部呼叫
```

**開發者無感是預設**：

- 未宣告 `services` → 所有**公開**方法天然可被 `module.call()` 呼叫（與裸屬性存取一致），
  無需任何宣告
- 宣告後 → 收緊為白名單，越界呼叫拋 `ServiceNotProvidedError`——用於標記
  "這些方法才是對外承諾"
- 限制的**主控制權在用戶端**：`scope.actions` 配置決定"誰能呼叫誰"（見下文審計），
  模組作者的 `services` 只是服務面宣告，兩層互不替代

**服務介紹**：為每個服務配上人類 / AI 可讀的描述——不需要就什麼都不寫，
介紹自動取**方法 docstring 首行**（框架本就要求 docstring 風格）：

```python
async def translate(self, text, target_lang):
    """把文本翻譯成指定語言"""    # ← 這一行自動成為服務介紹
    ...
```

**參數提示**：呼叫方（尤其是 AI 智能體）需要知道每個參數的含義。不需要就什麼都不寫，
提示自動取方法 docstring 的 **`:param:` 行**：

```python
async def render_card(self, html, width=800, height=0):
    """渲染 HTML 為圖片檔案

    :param html: 要渲染的 HTML 文本          ← 自動成為參數提示
    :param width: 畫布寬度像素，0 為按內容自適應
    :param height: 畫布高度像素，0 為按內容自適應
    """
```

需要精細控制（覆蓋 docstring / 多語言）時用 dict 形態宣告 description 與 parameters
（均支援 i18n 字典；`parameters` 按**參數**與 docstring 合併，單參數內顯式宣告優先，
宣告了簽名中不存在的參數會被過濾）：

```python
services=[
    {"name": "translate", "description": "把文本翻譯成指定語言"},
    {"name": "summarize", "description": {"i18n": "Chat.meta.svc.summarize", "default": "摘要對話"}},
    {
        "name": "render_card",
        "description": "渲染 HTML 為圖片檔案",
        "parameters": {"html": "HTML 文本", "width": "寬度像素，0 為自適應"},
    },
]
```

## 服務目錄：services()

```python
sdk.module.services()
# {'Chat': [{'name': 'get_history', 'signature': '(session_id, n=20)',
#            'description': '把文本翻譯成指定語言',
#            'parameters': {'session_id': '會話 ID', 'n': '返回條數'}}]}

sdk.module.services("Chat")   # 僅查詢指定模組
```

- 僅列出**明確聲明** `meta.services` 的模組（未聲明模組不出現在目錄中）
- 每個服務帶有方法簽名字串（由 `inspect.signature` 提取）、介紹文字與參數提示
- **懶加載模組同樣會進入目錄**（服務發現先於加載發生）——呼叫方可據此決定是否
  `call()` 喚醒目標模組
- 同時進入拓撲：`sdk.module.get_topology()` 的各模組條目帶有 `services` 字段

{!--< tips >!--}
**MCP 化路線**：服務目錄（名稱 + 簽名 + 描述 + 參數提示）即 MCP tool 的形狀——
每個服務天然長成 ``{"name", "description", "parameters"}``。
未來框架可把 ``services()`` 直接暴露為 MCP server 端點，讓 AI 發現並呼叫模組能力；
``scope.actions.call`` 審計天然成為 AI 調用的安全閘口。
{!--< /tips >!--}

## 出站審計：誰能呼叫誰

每次 `module.call()` 都會以**呼叫方模組**的身份過**出站閘口**的審計：

```toml
[ErisPulse.scope.actions.CallerModule.call]
deny = ["Chat.get_history"]        # 禁止 CallerModule 呼叫 Chat 的 get_history
# allow = ["Chat.get_*"]           # 或白名單：僅允許呼叫 Chat 的 get 開頭服務
```

- `name` 格式為 `<目標模組>.<方法名>`，支援精確 / glob / `re:` 正則
- 框架層呼叫（無 owner 上下文，例如啟動腳本）不受審計約束
- 被拒絕的呼叫會拋出 `ModuleCallError`（TRACE 日誌 `core.module.call_denied`）

配置方式詳見 [作用域（scope）](docs/zh-TW/scope.md) 的出站維度。

## 定向事件：lifecycle.emit 的 to 參數

生命週期事件支援定向傳播：`to` 指定目標擁有者（owner）後，事件只分發給以該
owner 身份註冊的鉤子（模組在 `on_load` 內註冊的鉤子自動歸屬本模組），
其它模組與通配符 `*` 處理器不感知。

```python
from ErisPulse.Core.lifecycle import lifecycle

# 投遞方：事件只投給 Chat 模組註冊的鉤子
await lifecycle.emit("message_received", {"text": "hi", "from": "u1"}, to="Chat")

# 訂閱方（Chat 模組內）：註冊同名鉤子，owner 在註冊時自動記錄
@lifecycle.on("message_received")
async def on_message_received(data): ...

@lifecycle.on("message")          # 點式父級前綴同樣生效（按 owner 過濾）
async def on_any(data): ...
```

語義細節：

- 目標 owner 無已註冊鉤子 → 事件**靜默丟棄**（**不發往不存在的地方**），
  可用 `lifecycle.has_handlers("message_received")` 提前探測
- `data` 為 dict 時自動攜帶 `_trace_id`（不覆蓋已有值），與全鏈路追蹤打通
- 廣播與定向共用一套鉤子註冊：`emit(...)` 不帶 `to` 即全框架廣播，
  帶 `to` 則同一事件只對目標模組可見
- `emit_sync` / `submit_event`（相容 API）同樣支援 `to=` 參數

> [!NOTE]
> 定向事件是輕量通知，**不做目標校驗與懶喚醒**；需要目標存在性校驗、
> 契約審計或返回值時，改用 [RPC：module.call](#rpcmodulecall)。

## 慢載與呼叫

`module.call()` 對慢載模組是**透明喚醒**：

- 事件驅動慢載模組（`activate_on` 聲明）→ 走激活鎖 `_activate()`，激活後觸發器 stub 自動註銷
- 普通慢載模組 → 同步初始化或常規載入路徑（冪等）
- 喚醒失敗 → `ModuleNotAvailableError`

也就是說：**呼叫方不需要關心目標模組是否已載入**，也不需要為了喚醒它而等待任何事件。

定向事件（`lifecycle.emit(..., to=...)`）不做慢載喚醒——目標未載入即無鉤子，  
事件靜默丟棄；需要確保傳送到時改用 `module.call()`。

## 冷啟動回放

新裝 / 重啟的模組錯過了一段聊天——`get_load_strategy(replay=...)` 讓框架在模組
就緒後，把會話收件箱裡最近的訊息**回放給該模組自己**：

```python
from ErisPulse.loaders import ModuleLoadStrategy

class MyAIModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(
            lazy_load=False,
            priority=100,
            replay="5m",        # 回放最近 5 分鐘（"1h" / "300" 秒寫法均可）
        )

    async def on_load(self, event):
        @message.on_message()
        async def handle(e):
            if e.get("replayed"):
                # 合成事件：僅補上下文，不要觸發發送等副作用
                ...
```

語義細節：

- 數據來源是[會話收件箱](interaction.md#會話收件箱eventhistory)（`sdk.transcript.recent()`），
  模組加載完成後後台執行，不阻塞啟動
- 合成事件帶 `replayed: True` 標誌、完整的 `platform / detail_type / user_id / alt_message`，
  **只分發給本模組的處理器**——其他模組不受回放影響
- 收件箱未啟用 / 無記錄 / 時長聲明非法（`replay_invalid` 警告）時靜默跳過

## 事件冪等去重

平台 websocket 重新連接後，經常會重複推送同一事件（相同的 `event["id"]`）——分發入口會根據 id 做 LRU 去重（容量 4096），相同 id 的事件只會分發一次。

```toml
[ErisPulse.framework]
event_dedupe = true   # 預設開啟；測試環境固定 id 合成事件可關閉
```

適配器**註冊**（新連接生命週期的起點）時會自動重置去重緩存。

## 相關文件

- [互動對話系統](interaction.md) - wait_reply / 定時器 / 多路等待 / 對話互斥
- [作用域（scope）](scope.md) - 出站維度審計的完整設定
- [歸屬權（owner）系統](ownership.md) - owner 上下文如何貫穿跨模組呼叫
- [懶加載系統](lazy-loading.md) - 懶加載與事件驅動懶激活（activate_on）
- [生命週期管理](lifecycle.md) - 廣播層事件總線的機制

## 连接管理

> 来源: `docs/zh-TW/advanced/connections.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-TW/advanced/connections.md）

# 連接池與廣播

> [!TIP]  
> **何時需要閱讀本文**：當需要 WebSocket/SSE 連接池、廣播分組、跨模組推送，或查看連接狀態時。若無此需求則可跳過，不會影響其他功能的使用。

> **讀完你將了解**：三種連接如何自動登記進註冊表、分組訂閱與廣播 API、  
> 跨模組重用與關閉權的歸屬，以及模組卸載時連接的清理語意。  
>  
> **本文不涉及**：WebSocket / SSE 路由的註冊寫法與連接生命週期鈎子  
> （見[路由管理器](router.md)）；客戶端 HTTP 請求（見[網路客戶端](http-client.md)）。

連接（服務端 WebSocket / SSE / 客戶端出站 WebSocket）在 ErisPulse 中是**框架級一等資源**：  
隨著連接建立自動登記進統一註冊表，支援廣播、業務分組訂閱與跨模組傳遞/重用，  
模組卸載時由框架自動關閉回收——業務不再需自行建立 `_ws_clients` 集合，也不會因忘記清理而造成資源洩漏。

> 本文文件範例均為**根導入**寫法（2.10+ 推薦）：  
> `from ErisPulse import connections, router, client, WebSocketConnection`

## 概述

```python
from ErisPulse import connections, router, WebSocketConnection

# 服務端：連接自動登記，handler 內加入業務分組
@router.ws("MyModule", "/ws")
async def handle(ws: WebSocketConnection):
    ws.join_group("room:1")            # 分組命名完全由業務約定
    async for msg in ws.iter_text():
        ...                             # 斷開時框架自動註銷、清理分組

# 任意位置：向分組廣播（返回成功失敗明細）
result = await connections.broadcast({"type": "notify"}, group="room:1")
if not result.ok:
    ...                                 # result.failed: {連接id: 異常}
```

三種連接統一進入註冊表：

| kind | 來源 | 歸屬 owner | 說明 |
|------|------|-----------|------|
| `server` | `@router.ws(...)` / `register_websocket(...)` | 註冊路由的模組名 | 斷開自動註銷 |
| `sse` | `@router.sse(...)` / `register_sse(...)` | 註冊路由的模組名 | 廣播走 `sse.send()` |
| `client` | `await client.ws_connect(url)` | 當前模組（或顯式 `owner=`） | 關閉/遠端斷開自動註銷；適配器停止時框架統一關閉 |

不想要自動登記時：路由傳 `track=False`，出站連接傳 `track=False`，舊代碼行為完全不變。

## 查看連接池

```python
from ErisPulse import connections

# 查看某模組的連接池（「某模組現在有幾條活連接」）
conns = connections.list(namespace="Dashboard")
for conn in conns:
    print(conn.id, conn.kind, conn.groups, conn.meta)

# 按其它維度過濾（各條件 AND）
connections.list(owner="MyAdapter", kind="client")
connections.list(group="tenant:acme")

# 全局統計（各維度計數）
stats = connections.stats()
# {'total': 5, 'by_kind': {...}, 'by_namespace': {...}, 'by_owner': {...}, 'groups': {...}}

# 歸屬權審計計數（ownership 面門同樣可見）
from ErisPulse import ownership
ownership.counts("Dashboard")   # {'connections': 3, ...}
```

每條連接可讀的身份資訊：`conn.id`（形如 `Dashboard:1a2b3c4d`）、`conn.namespace`、
`conn.owner`、`conn.kind`、`conn.groups`、`conn.meta`（業務自由字典）。

## 廣播與訂閱

### 分組（訂閱模型）

分組是**扁平字串**，命名完全由業務約定（房間 / 租戶 / 主題……），
嵌套層級用命名約定表達（如 `tenant:acme/room:1`），框架不約束格式。

兩個方向都可以操作：

```python
# 方向一：連接端主動加入/退出（handler 內）
@router.ws("Chat", "/ws")
async def handle(ws: WebSocketConnection):
    ws.join_group("room:1")        # 等價 connections.assign(ws.id, "room:1")
    ws.leave_group("room:1")

# 方向二：管理端被動分配（路由端 / 其它模組）
connections.assign(conn_id, "tenant:acme")
connections.dismiss(conn_id, "tenant:acme")   # 不傳分組名 = 退出全部分組
```

連接斷開時自動退出全部分組，無需業務清理。

### 廣播

```python
result = await connections.broadcast(
    data,                       # WS 走 send_json；SSE 走 send（自動 JSON 序列化）
    namespace="Dashboard",      # 按命名空間過濾
    group="room:1",             # 按分組過濾
    kind="sse",                 # 按連接種類過濾
    owner="MyAdapter",          # 按歸屬過濾
    ids={conn_id, ...},         # 明確指定候選集（過濾條件仍生效）
    exclude={conn_id},          # 排除某些連接
    timeout=10.0,               # 單條連接發送超時（非總時長）
    concurrency=64,             # 並發發送上限
    raise_on_error=False,       # True 時有失敗項則拋出首個異常
)
result.total      # 目標連接總數（排除前）
result.sent       # 成功的連接 id 列表
result.failed     # {連接 id: 異常物件}（超時/已斷開/發送失敗）
result.excluded   # 被排除的連接 id
result.ok         # 是否全部傳達
```

過濾條件之間是 **AND**；單條失敗不會影響其它連接；`ids` 中已不存在的連接會計入
`failed`（讓業務知道全貌）。

### 生命週期事件

連接登記/註銷/分組變化會發射標準生命週期事件，Dashboard 等可訂閱做即時呈現：

```python
from ErisPulse import lifecycle

@lifecycle.on("connection.registered")
async def on_registered(data): ...
@lifecycle.on("connection.unregistered")
async def on_unregistered(data): ...
@lifecycle.on("connection.group.joined")
async def on_joined(data): ...
@lifecycle.on("connection.group.left")
async def on_left(data): ...
```

## 跨模組傳遞 / 復用

連接是框架登記的資源，任何模組都可以透過連接 id 拿到它並**復用**——  
不需要自己再建立一條，也不需要知道連接是誰建立的：

```python
from ErisPulse import connections

conn = connections.get("Dashboard:1a2b3c4d")   # 不存在 / 已斷開拋 ConnectionNotFoundError
await conn.send_json({"ping": 1})              # 任何模組都可發送
conn.join_group("someone-elses-room")          # 也可參與分組
```

**歸屬與關閉權**：

- 連接的 `owner`（建立它的模組）獨佔關閉權。非 owner 調用 `close()` 拋  
  `ConnectionPermissionError`（`from ErisPulse import ConnectionPermissionError`）；
- 發送與分組操作對所有模組開放，不需要授權；
- owner 模組卸載 / 适配器停止時，框架**統一關閉並註銷**其名下全部連接  
  （服務器端 + 出站），已拿到的引用再發送會得到失敗結果，監聽  
  `connection.unregistered` 事件可感知；
- 框架內部回收路徑用 `close(force=True)` 繞過校驗。

> 歸因說明：關閉權校驗依賴運行時 owner 上下文（`owner_scope` / 事件分發 /  
> `spawn_background` 等自動攜帶）。上下文不可歸因的呼叫（未歸因的老程式碼）會放行，  
> 保證 0 破壞；新程式碼在 owner 上下文中呼叫即受保護。

## 出站連接（Client 側）

```python
from ErisPulse import client

ws = await client.ws_connect("wss://example.com/ws")
ws.id          # 已登記，可被 connections 查詢/廣播
ws.owner       # 當前模組（owner 上下文不可用時建議顯式傳）

# owner 上下文不可用（如工具線程回調）時顯式指定，卸載才能自動回收：
ws = await client.ws_connect("wss://example.com/ws", owner="MyAdapter")
```

遠端主動斷開、本地 `close()` 都會自動註銷登記；模組卸載時框架關閉其名下
全部出站連接。等舊代碼裸建連接各自管理、忘記清理導致泄漏的日子到此為止。

## 跨執行緒投遞

從子執行緒觸發連線（廣播 / 推送 / 關閉）時，使用框架標準工具投遞回主迴圈，  
**不要手寫 `run_coroutine_threadsafe`**：

```python
from ErisPulse import run_main_loop, spawn_later, spawn_thread

# 子執行緒阻塞取得結果：
run_main_loop(connections.broadcast({"tick": 1}, group="room:1"), timeout=5)

# 後台執行緒 + 延遲任務（owner 歸屬，卸載自動取消）：
def push_tick():
    return connections.broadcast({"tick": 1}, group="room:1")
spawn_later(30, push_tick, owner="MyModule")
```

## 卸載與清理語意

模組卸載 / 适配器停止的歸屬權回收鏈會依序：取消歸屬背景任務與定時器 →  
**關閉並註銷歸屬連接** → 觸發 on_cleanup 鈎子 → 註銷路由/處理器等註冊類資源。  
詳見 [歸屬權（owner）系統](ownership.md)。

> [!WARNING]  
> 從 2.10 開始，模組卸載時會關閉其名下登記的 WS/SSE/出站連接。依賴「卸載後連接仍存活」的  
> 下游組件（如舊版 Dashboard 推送）需知悉——這是杜絕連接泄漏的預期行為。

## API 一覽

| API | 說明 |
|-----|------|
| `connections.get(id)` | 取得連接（跨模組入口），不存在則拋出 `ConnectionNotFoundError` |
| `connections.list(namespace=, owner=, group=, kind=)` | 過濾查詢連接列表 |
| `connections.stats(namespace=, owner=)` | 各維度計數統計 |
| `connections.assign(id, *groups)` / `dismiss(id, *groups)` | 管理端加入/移出分組 |
| `await connections.broadcast(data, ...)` | 廣播，返回 `BroadcastResult` |
| `await connections.close(id, force=False)` | 關閉並註銷（權限驗證） |
| `await connections.close_owner(owner)` | 關閉註銷某 owner 名下全部連接（框架卸載鏈調用） |
| `conn.join_group(*groups)` / `conn.leave_group(*groups)` | 連接端分組 |
| `conn.send_json / send_text / iter_text / ...` | 收發（服務端/客戶端介面一致） |
| `conn.meta` | 業務元數據字典 |
| `conn.close(force=False)` | 關閉（非 owner 拋出 `ConnectionPermissionError`） |

## 相關文件

- **註冊服務端 WS / SSE 路由** → [路由管理器](router.md)
- **建立客戶端出站 WebSocket** → [網路客戶端](network-client.md)
- **模組卸載時連線如何被回收** → [歸屬權（owner）系統](ownership.md)
- **連線相關異常（`ConnectionNotFoundError` / `ConnectionPermissionError`）** → [異常體系與捕獲指南](errors.md)

## 路由

> 来源: `docs/zh-TW/advanced/router.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-TW/advanced/router.md）

# 路由管理器

> [!TIP]
> **什麼時候需要閱讀這篇**：需要 HTTP / WebSocket / SSE 路由（含連接池廣播）時。不需要則跳過，不會影響其他功能的使用。

ErisPulse 路由管理器提供統一的 HTTP 和 WebSocket 路由管理，支援多適配器路由註冊和生命週期管理。底層透過抽象層封裝（目前為 FastAPI + Uvicorn）

## 概述

路由管理器的主要功能：

- **裝飾器路由**：支援 `@http` / `@get` / `@post` / `@put` / `@delete` / `@ws` 裝飾器快速註冊
- **自動注入**：路由處理器無需導入 FastAPI 類型，框架自動注入抽象物件
- **路由分組**：支援帶前綴和版本號的 `RouteGroup`
- **路由中間件**：支援 glob 模式匹配的請求攔截
- **速率限制**：內建滑動視窗限流
- **CORS 支援**：一鍵開啟跨域資源共享
- **安全頭**：自動添加安全回應頭
- **自動文件**：基於 OpenAPI 的互動式文件
- **WebSocket 支援**：完整的 WebSocket 連線管理、自訂認證和生命週期鉤子
- **生命週期整合**：與 ErisPulse 生命週期系統深度整合
- **SSL/TLS 支援**：支援 HTTPS 和 WSS 安全連線
- **主頁入口**：支援模組在根路由 `/` 註冊快速入口按鈕，支援國際化

## 抽象類型

ErisPulse 提供了服務端抽象類型，使模組無需直接依賴 FastAPI：

| 抽象類型 | FastAPI 對應 | 說明 |
|---------|-------------|------|
| `HttpRequest` | `fastapi.Request` | HTTP 請求封裝，介面完全相容 |
| `WebSocketConnection` | `fastapi.WebSocket` | WebSocket 連線封裝，額外提供生命週期鈎子 |
| `WebSocketDisconnect` | `fastapi.WebSocketDisconnect` | WebSocket 斷開異常 |

> `WebSocketConnection` 繼承自 `WebSocketConnectionBase`，與客戶端 WebSocket (`ClientWebSocket`) 共享相同的 send/receive/iter/close 接口。客戶端和服務端 WebSocket 可以使用相同的業務邏輯程式碼。
>
> 透過 `.raw` 屬性可存取底層 FastAPI 原生物件。直接使用 FastAPI 類型的程式碼也完全相容。

## 裝飾器路由（推薦）

### 註冊形態：單參（推薦）與雙參

裝飾器路由支援兩種形態，**推薦單參**——與命令 / 事件觸發器一致，命名空間自動歸屬當前模組：

```python
from ErisPulse import router

# 單參（推薦）：自動歸屬 模組名/hello → 實際路徑 /my_module/hello
@router.get("/hello")
async def hello():
    return {"ok": True}

# 單參 WebSocket：@ws("chat") → /my_module/chat
@router.ws("chat")
async def chat(ws):
    ...

# 雙參：明確指定模組名（規則不變，跨模組/工具程式碼註冊時使用）
@router.get("other_module", "/info")
async def get_info(request):
    return {"method": request.method, "path": str(request.url)}
```

> [!NOTE]
> 單參形態要求在模組/適配器**載入上下文**中註冊（載入期框架已注入歸屬）；
> 在無歸屬上下文處呼叫會拋 `ValueError` 並提示明確傳入模組名。

### HTTP 裝飾器

```python
from ErisPulse import router, HttpRequest

# 也可明確標註抽象類型
@router.post("/data")
async def post_data(request: HttpRequest):
    data = await request.json()
    return {"received": data}

@router.put("/data/{item_id}")
async def update_data(request):
    return {"updated": True}

@router.delete("/data/{item_id}")
async def delete_data(request):
    return {"deleted": True}
```

> **自動注入規則**：當處理器第一個參數名為 `request` 或 `req` 且無 FastAPI 類型註解時，框架自動注入 `HttpRequest`。無參數或非請求參數名的處理器不受影響。

#### 回應返回約定（2.10+）

處理器回傳值支援**元組約定**（推薦寫法，明確控制狀態碼），dict/str/Response 照舊：

```python
@router.post("/login")
async def login(request):
    if not check_token(request):
        # (body, status_code) → 401 JSON
        return {"error": "unauthorized", "message": "token 無效"}, 401
    # (body, status_code, headers) 還可帶回應頭
    return {"user_id": 1}, 200, {"X-Request-Cost": "12ms"}

# 或使用 respond() 幫助函數（message 自動合併進回應體）
from ErisPulse import respond

@router.get("/me")
async def me():
    return respond({"user_id": 1}, status_code=200, message="ok")
```

路徑 / 查詢參數直接用 FastAPI 原生註解即可（`item_id: int`、`page: int = 1`），
中間件見[路由中間件](#路由中間件)一節。

### WebSocket 裝飾器

```python
from ErisPulse import WebSocketConnection, WebSocketDisconnect

# 基本 WebSocket（單參形態）
@router.ws("ws")
async def websocket_handler(ws):
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")

# 帶生命週期鉤子的 WebSocket
@router.ws("/ws/chat")
async def chat(ws: WebSocketConnection):
    @ws.on_disconnect
    async def on_disconnect(ws, reason="unknown"):
        print(f"用戶斷開: {reason}")

    @ws.on_error
    async def on_error(ws, error=""):
        print(f"連接錯誤: {error}")

    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")

# 帶認證的 WebSocket
async def ws_auth(ws: WebSocketConnection) -> bool:
    token = ws.query_params.get("token")
    return token == "secret"

@router.ws("secure_ws", auth_handler=ws_auth)
async def secure_ws_handler(ws):
    while True:
        data = await ws.receive_text()
        await ws.send_text(f"Echo: {data}")
```

> **注意**：WebSocket 處理器和認證處理器也支援自動注入。無需參數註解即可獲得 `WebSocketConnection`。標註 `fastapi.WebSocket` 也可傳入原生物件，但推薦使用抽象類型。

### 連接自動登記（連接池，2.10+）

`@ws` / `@sse` 建立的連接**預設自動登記**進框架連接池（`track=False` 可關閉）：
handler 內 `ws.id` / `ws.join_group(...)` 可用，任意模組可
`connections.list(namespace=...)` 查看本模組連接、向分組廣播。
詳見[連接池與廣播](connections.md)。

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

# 帶限流和文件說明
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

# 帶驗證的註冊（推薦）
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
| `auth_handler` | 驗證函數，回傳 `False` 會自動關閉連接 | `None` |
| `auto_accept` | 是否自動 `accept()` | `True` |

> **建議**：使用 `auth_handler` 進行連接確認，而非關閉 `auto_accept`。僅在你需要完全控制連接流程時才設定 `auto_accept=False`。

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
# 創建帶前綴的路由組
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

從 2.7.0 版本開始，每個 HTTP 請求都會攜帶一個 `X-Request-ID` 關聯 ID，用於日誌 / 鏈路追蹤串聯：

- **生成規則**：優先沿用客戶端傳入的 `X-Request-ID` 請求頭（分佈式追蹤場景）；否則自動生成 UUID
- **回應標頭**：回應會回寫 `X-Request-ID`，方便客戶端將請求與日誌對應
- **生命週期事件**：`server.request` 與 `server.response` 事件資料中新增 `request_id` 欄位

```python
# 在模組中監聽請求事件，依 request_id 串聯請求-回應
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

速率限制格式：`{次數}/{時間視窗}`，例如 `10/minute`、`100/hour`。

## CORS 配置

```python
router.setup_cors(
    allow_origins=["https://example.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

也可透過 `config.toml` 進行配置：

```toml
[router.cors]
allow_origins = ["https://example.com"]
allow_methods = ["GET", "POST"]
allow_headers = ["*"]
```

## 安全標頭

```python
router.setup_security_headers()
```

自動添加 `X-Content-Type-Options`、`X-Frame-Options`、`X-XSS-Protection` 等安全標頭。

也可透過 `config.toml` 進行配置：

```toml
[router.security]
enabled = true
```

## 自動文檔

Router 預設啟用 OpenAPI 互動式文檔：

```python
# 禁用文檔
router.disable_docs()

# 自訂文檔資訊
router.set_docs_info(
    title="My API",
    description="API 文檔",
    version="1.0.0"
)
```

## 路徑處理

路由路徑會自動加上模組名稱作為前綴，以避免衝突：

```python
# 將路徑 "/api" 註冊到模組 "my_module"
# 實際可存取的路徑為 "/my_module/api"
router.register_http_route("my_module", "/api", handler)
```

> [!WARNING]
> 路由路徑（包含模組名前綴）**區分大小寫**。註冊時的模組名稱大小寫會反映在實際路徑上：當模組名稱為 `Test` 時，註冊 `/api` 的實際路徑是 `/Test/api`，若存取 `/test/api` 則會回傳 404。

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

根路由 `/` 顯示 ErisPulse 品牌頁面，自動偵測 Dashboard 的可用性並添加入口按鈕。

## 主頁入口

路由管理器允許外部模組在根路由 `/` 上註冊快捷入口按鈕，方便使用者快速訪問各模組的管理頁面。

### 註冊入口

```python
# 簡單註冊
router.register_home_entry(
    name="我的面板",
    url="/mymodule/admin",
)

# 帶圖標的註冊（SVG）
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
| `name` | `str` / `dict` | 按鈕顯示文本；傳入 `{"i18n": "key", "default": "文本"}` 字典時使用國際化 | 是 |
| `url` | `str` | 按鈕連結地址 | 是 |
| `icon_svg` | `str` | 可選 SVG 圖標標記 | 否 |

### Dashboard 自動註冊

當偵測到 `sdk.Dashboard` 可用時，路由管理器會自動在入口列表首位添加 Dashboard 按鈕，無需手動註冊。

## 生命週期集成

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

1. **優先使用抽象類型**：使用 `HttpRequest` / `WebSocketConnection` 替代 `fastapi.Request` / `fastapi.WebSocket`，避免硬性依賴
2. **利用自動注入**：處理器第一個參數命名為 `request` 或 `req`，無需任何類型註解即可獲得 `HttpRequest`
3. **優先使用單參數形態**：模組加載上下文中優先使用單參數形態（自動歸屬命名空間）；跨模組/工具代碼註冊時顯式傳入模組名
4. **使用路由分組**：對同一模組的多個路由使用 `group()` 進行組織
5. **安全性考量**：為敏感操作實現認證機制和安全頭
6. **合理限流**：對高頻接口設置速率限制
7. **使用生命週期鉤子**：通過 `@ws.on_disconnect` / `@ws.on_error` 處理 WebSocket 異常，避免手動 try/catch

## 相關文件

- [HTTP 客戶端](http-client.md) - 使用內建 HTTP 客戶端發送請求
- [模組開發指南](../developer-guide/modules/getting-started.md) - 了解模組路由註冊
- [最佳實踐](../developer-guide/modules/best-practices.md) - 路由使用建議
