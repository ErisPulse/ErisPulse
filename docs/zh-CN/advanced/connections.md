# 连接池与广播

连接（服务端 WebSocket / SSE / 客户端出站 WebSocket）在 ErisPulse 中是**框架级一等资源**：
随连接建立自动登记进统一注册表，支持广播、业务分组订阅与跨模块传递/复用，
模块卸载时由框架自动关闭回收——业务不再自建 `_ws_clients` 集合，也不会因忘记清理而泄漏。

> 本文档示例均为**根导入**写法（2.10+ 推荐）：
> `from ErisPulse import connections, router, client, WebSocketConnection`

## 概述

```python
from ErisPulse import connections, router, WebSocketConnection

# 服务端：连接自动登记，handler 内加入业务分组
@router.ws("MyModule", "/ws")
async def handle(ws: WebSocketConnection):
    ws.join_group("room:1")            # 分组命名完全由业务约定
    async for msg in ws.iter_text():
        ...                             # 断开时框架自动注销、清理分组

# 任意位置：向分组广播（返回成败明细）
result = await connections.broadcast({"type": "notify"}, group="room:1")
if not result.ok:
    ...                                 # result.failed: {连接id: 异常}
```

三种连接统一进入注册表：

| kind | 来源 | 归属 owner | 说明 |
|------|------|-----------|------|
| `server` | `@router.ws(...)` / `register_websocket(...)` | 注册路由的模块名 | 断开自动注销 |
| `sse` | `@router.sse(...)` / `register_sse(...)` | 注册路由的模块名 | 广播走 `sse.send()` |
| `client` | `await client.ws_connect(url)` | 当前模块（或显式 `owner=`） | 关闭/远端断开自动注销；适配器停止时框架统一关闭 |

不想要自动登记时：路由传 `track=False`，出站连接传 `track=False`，老代码行为完全不变。

## 查看连接池

```python
from ErisPulse import connections

# 查看某模块的连接池（"某模块现在有几条活连接"）
conns = connections.list(namespace="Dashboard")
for conn in conns:
    print(conn.id, conn.kind, conn.groups, conn.meta)

# 按其它维度过滤（各条件 AND）
connections.list(owner="MyAdapter", kind="client")
connections.list(group="tenant:acme")

# 全局统计（各维度计数）
stats = connections.stats()
# {'total': 5, 'by_kind': {...}, 'by_namespace': {...}, 'by_owner': {...}, 'groups': {...}}

# 归属权审计计数（ownership 门面同样可见）
from ErisPulse import ownership
ownership.counts("Dashboard")   # {'connections': 3, ...}
```

每条连接可读的身份信息：`conn.id`（形如 `Dashboard:1a2b3c4d`）、`conn.namespace`、
`conn.owner`、`conn.kind`、`conn.groups`、`conn.meta`（业务自由字典）。

## 广播与订阅

### 分组（订阅模型）

分组是**扁平字符串**，命名完全由业务约定（房间 / 租户 / 主题……），
嵌套层级用命名约定表达（如 `tenant:acme/room:1`），框架不约束格式。

两个方向都可以操作：

```python
# 方向一：连接侧主动加入/退出（handler 内）
@router.ws("Chat", "/ws")
async def handle(ws: WebSocketConnection):
    ws.join_group("room:1")        # 等价 connections.assign(ws.id, "room:1")
    ws.leave_group("room:1")

# 方向二：管理侧被动分配（路由侧 / 其它模块）
connections.assign(conn_id, "tenant:acme")
connections.dismiss(conn_id, "tenant:acme")   # 不传分组名 = 退出全部分组
```

连接断开时自动退出全部分组，无需业务清理。

### 广播

```python
result = await connections.broadcast(
    data,                       # WS 走 send_json；SSE 走 send（自动 JSON 序列化）
    namespace="Dashboard",      # 按命名空间过滤
    group="room:1",             # 按分组过滤
    kind="sse",                 # 按连接种类过滤
    owner="MyAdapter",          # 按归属过滤
    ids={conn_id, ...},         # 显式指定候选集（过滤条件仍生效）
    exclude={conn_id},          # 排除某些连接
    timeout=10.0,               # 单条连接发送超时（非总时长）
    concurrency=64,             # 并发发送上限
    raise_on_error=False,       # True 时有失败项则抛出首个异常
)
result.total      # 目标连接总数（排除前）
result.sent       # 成功的连接 id 列表
result.failed     # {连接 id: 异常对象}（超时/已断开/发送失败）
result.excluded   # 被排除的连接 id
result.ok         # 是否全部送达
```

过滤条件之间是 **AND**；单条失败不影响其它连接；`ids` 中已不存在的连接会计入
`failed`（让业务知道全貌）。

### 生命周期事件

连接登记/注销/分组变化会发射标准生命周期事件，Dashboard 等可订阅做实时呈现：

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

## 跨模块传递 / 复用

连接是框架登记的资源，任何模块都可以通过连接 id 拿到它并**复用**——
不需要自己再建一条，也不需要知道连接是谁建的：

```python
from ErisPulse import connections

conn = connections.get("Dashboard:1a2b3c4d")   # 不存在/已断开抛 ConnectionNotFoundError
await conn.send_json({"ping": 1})              # 任何模块都可发送
conn.join_group("someone-elses-room")          # 也可参与分组
```

**归属与关闭权**：

- 连接的 `owner`（创建它的模块）独占关闭权。非 owner 调用 `close()` 抛
  `ConnectionPermissionError`（`from ErisPulse import ConnectionPermissionError`）；
- 发送与分组操作对所有模块开放，不需要授权；
- owner 模块卸载 / 适配器停止时，框架**统一关闭并注销**其名下全部连接
  （服务端 + 出站），已拿到的引用再发送会得到失败结果，监听
  `connection.unregistered` 事件可感知；
- 框架内部回收路径用 `close(force=True)` 绕过校验。

> 归因说明：关闭权校验依赖运行时 owner 上下文（`owner_scope` / 事件分发 /
> `spawn_background` 等自动携带）。上下文不可归因的调用（未归因的老代码）会放行，
> 保证 0 破坏；新代码在 owner 上下文中调用即受保护。

## 出站连接（Client 侧）

```python
from ErisPulse import client

ws = await client.ws_connect("wss://example.com/ws")
ws.id          # 已登记，可被 connections 查询/广播
ws.owner       # 当前模块（owner 上下文不可用时建议显式传）

# owner 上下文不可用（如工具线程回调）时显式指定，卸载才能自动回收：
ws = await client.ws_connect("wss://example.com/ws", owner="MyAdapter")
```

远端主动断开、本地 `close()` 都会自动注销登记；模块卸载时框架关闭其名下
全部出站连接。等旧代码裸建连接各自管理、忘记清理导致泄漏的日子到此为止。

## 跨线程投递

从子线程触达连接（广播 / 推送 / 关闭）时，用框架标准工具投递回主循环，
**不要手写 `run_coroutine_threadsafe`**：

```python
from ErisPulse import run_main_loop, spawn_later, spawn_thread

# 子线程阻塞取结果：
run_main_loop(connections.broadcast({"tick": 1}, group="room:1"), timeout=5)

# 后台线程 + 延迟任务（owner 归属，卸载自动取消）：
def push_tick():
    return connections.broadcast({"tick": 1}, group="room:1")
spawn_later(30, push_tick, owner="MyModule")
```

## 卸载与清理语义

模块卸载 / 适配器停止的归属权回收链会依次：取消归属后台任务与定时器 →
**关闭并注销归属连接** → 触发 on_cleanup 钩子 → 注销路由/处理器等注册类资源。
详见 [归属权（owner）系统](ownership.md)。

> [!WARNING]
> 2.10 起，模块卸载会关闭其名下登记的 WS/SSE/出站连接。依赖"卸载后连接仍存活"的
> 下游组件（如旧版 Dashboard 推送）需知悉——这是杜绝连接泄漏的预期行为。

## API 一览

| API | 说明 |
|-----|------|
| `connections.get(id)` | 取连接（跨模块入口），不存在抛 `ConnectionNotFoundError` |
| `connections.list(namespace=, owner=, group=, kind=)` | 过滤查询连接列表 |
| `connections.stats(namespace=, owner=)` | 各维度计数统计 |
| `connections.assign(id, *groups)` / `dismiss(id, *groups)` | 管理侧加入/移出分组 |
| `await connections.broadcast(data, ...)` | 广播，返回 `BroadcastResult` |
| `await connections.close(id, force=False)` | 关闭并注销（权限校验） |
| `await connections.close_owner(owner)` | 关闭注销某 owner 名下全部连接（框架卸载链调用） |
| `conn.join_group(*groups)` / `conn.leave_group(*groups)` | 连接侧分组 |
| `conn.send_json / send_text / iter_text / ...` | 收发（服务端/客户端接口一致） |
| `conn.meta` | 业务元数据字典 |
| `conn.close(force=False)` | 关闭（非 owner 抛 `ConnectionPermissionError`） |
