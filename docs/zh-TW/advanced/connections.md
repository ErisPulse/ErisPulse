# 連接池與廣播

連接（服務端 WebSocket / SSE / 客戶端出站 WebSocket）在 ErisPulse 中是**框架級一等資源**：
隨著連接建立自動登記進統一註冊表，支援廣播、業務分組訂閱與跨模組傳遞/複用，
模組卸載時由框架自動關閉回收——業務不再自建 `_ws_clients` 集合，也不會因忘記清理而造成記憶體洩漏。

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