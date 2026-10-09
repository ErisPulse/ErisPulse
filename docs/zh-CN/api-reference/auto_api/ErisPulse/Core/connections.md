# `ErisPulse.Core.connections` 模块

---

## 模块概述


ErisPulse 连接注册表（连接池）

把"连接"从模块私有物升级为框架级一等资源：服务端 WS/SSE 连接随路由
自动登记（namespace 维度），客户端出站 WS 连接随 ``client.ws_connect``
自动登记（owner 维度）。支持广播（按命名空间 / 分组 / id 过滤的集合推送）、
业务分组订阅（房间 / 租户 / 主题，命名完全由业务约定）与跨模块连接传递
（共享同一连接对象，关闭权归创建者 owner）。

> **提示**
> 1. 服务端 ``@router.ws(...)`` handler 拿到的连接已自动登记，``ws.id`` 可查
> 2. ``connections.list(namespace=...)`` 查看某模块的连接池；``stats()`` 看全局
> 3. ``connections.broadcast(data, group=...)`` 向分组广播并返回成败明细
> 4. 跨模块 ``connections.get(id)`` 拿连接后可发送 / 分组，但 ``close`` 仅 owner 可调
> 5. 模块卸载时框架自动关闭并注销其名下全部连接（server/client/sse）
> 6. 从子线程调用本模块异步 API 请经 ``ErisPulse.run_main_loop`` 投递

**示例**:

```python
# handler 内加入分组；任意位置向分组广播
@router.ws("MyModule", "/ws")
async def handle(ws: WebSocketConnection):
    ws.join_group("room:1")
    async for msg in ws.iter_text():
        await connections.broadcast({"echo": msg}, group="room:1")
```

---

## 类列表


### `class BroadcastResult`

广播结果

:attribute total: 目标连接总数（排除前，含 id 指定但已不存在的连接）
:attribute sent: 发送成功的连接 id 列表
:attribute failed: 发送失败的 {连接 id: 异常对象}（含超时与已断开）
:attribute excluded: 被 ``exclude`` 参数排除的连接 id 列表


#### 方法列表


##### `ok -> bool`（property）

是否全部送达

**返回值** (`bool`): 无失败项时为 True

---


### `class ConnectionManager`

连接注册表管理器

维护框架级连接集合（服务端 WS / SSE / 客户端出站 WS）与业务分组索引。
连接的登记 / 注销由框架在路由与客户端连接生命周期处自动完成；
业务侧主要使用查询（``list`` / ``stats`` / ``get``）、分组
（``assign`` / ``dismiss``）与广播（``broadcast``）。

> **提示**
> 1. 归属与关闭权：连接 owner 拥有关闭权，其他模块仅可发送与分组
> 2. 分组命名完全由业务约定，连接断开时自动退出全部分组
> 3. 广播永不改变连接归属；跨模块点对点操作请用 ``get``

**示例**:

```python
conns = connections.list(namespace="Dashboard")
result = await connections.broadcast({"type": "notify"}, namespace="Dashboard")
result.ok
True
```


#### 方法列表


##### `register(conn: Any, *, namespace: str = '', owner: str | None = None, kind: str = '', meta: dict[str, Any] | None = None) -> str`

登记连接并分配连接 id

**内部方法**
由 router（服务端 WS/SSE）与 client（出站 WS）在连接建立时自动调用；
owner 缺省时从运行时上下文捕获（current_owner > current_caller）。

- **conn**: 连接对象（需具备 id/owner/kind 等身份混入字段）
- **namespace** (`str`): 服务端路由命名空间（客户端连接留空）
- **owner** (`str`): 归属 owner（模块名 / 平台名），缺省时取当前上下文
- **kind** (`str`): 连接种类（"server" / "client" / "sse"），缺省时读 conn.kind
- **meta** (`dict | None`): 初始业务元数据

**返回值** (`str`): 分配的连接 id

---


##### `unregister(conn: Any) -> bool`

注销连接（不主动关闭底层连接）

连接断开 / 关闭后由框架自动调用；清除全部分组与索引。
幂等：未登记的连接返回 False。

**内部方法**
由 router 断开路径、client 连接关闭与 SseEmitter.close 自动调用。

- **conn**: 连接对象或连接 id

**返回值** (`bool`): 是否实际注销

---


##### `get(connection_id: str) -> Any`

按连接 id 获取连接（跨模块传递 / 复用的入口）

返回连接本体：任何模块都可 ``send_json`` / 分组操作；
``close`` 仅连接 owner 可调（上下文不可归因时放行）。

- **connection_id** (`str`): 连接 id

**返回值**: 连接对象（WebSocketConnection / ClientWebSocket / SseEmitter）

**异常**: `ConnectionNotFoundError` - 连接不存在或已断开注销

---


##### `list(*, namespace: str | None = None, owner: str | None = None, group: str | None = None, kind: str | None = None) -> list[Any]`

查询连接集合（各过滤条件之间为 AND）

- **namespace** (`str | None`): 按服务端命名空间过滤（即"查看某模块连接池"）
- **owner** (`str | None`): 按归属 owner 过滤
- **group** (`str | None`): 按业务分组过滤
- **kind** (`str | None`): 按连接种类过滤（"server" / "client" / "sse"）

**返回值** (`list`): 连接对象快照列表

**示例**:

```python
connections.list(namespace="Dashboard")
```

---


##### `stats(*, namespace: str | None = None, owner: str | None = None) -> dict[str, Any]`

连接池统计（各维度计数）

- **namespace** (`str | None`): 先按命名空间过滤再统计
- **owner** (`str | None`): 先按归属过滤再统计

**返回值** (`dict`): 含 total / by_kind / by_namespace / by_owner / groups

**示例**:

```python
connections.stats()
{'total': 3, 'by_kind': {'server': 2, 'sse': 1}, ...}
```

---


##### `counts() -> dict[str, int]`

**内部方法**
供 ownership.counts() 审计的登记簿计数

---


##### `assign(connection_id: str, *groups: str) -> None`

将连接加入业务分组（管理侧被动分配）

与连接侧 ``conn.join_group(...)`` 等价；分组命名完全由业务约定。
连接断开时自动退出全部分组。

- **connection_id** (`str`): 连接 id
- **groups** (`str`): 一个或多个分组名

**异常**: `ConnectionNotFoundError` - 连接不存在或已断开

---


##### `dismiss(connection_id: str, *groups: str) -> None`

将连接移出业务分组

- **connection_id** (`str`): 连接 id
- **groups** (`str`): 一个或多个分组名；不传则退出全部分组

**异常**: `ConnectionNotFoundError` - 连接不存在或已断开

---


##### `async broadcast(data: Any, *, namespace: str | None = None, owner: str | None = None, group: str | None = None, kind: str | None = None, ids: list[str] | set[str] | tuple[str, ...] | None = None, exclude: list[str] | set[str] | tuple[str, ...] | None = None, timeout: float = DEFAULT_BROADCAST_TIMEOUT_SECS, concurrency: int = DEFAULT_BROADCAST_CONCURRENCY, raise_on_error: bool = False) -> BroadcastResult`

向过滤出的连接集合广播消息

目标集合 = 各过滤条件（namespace / owner / group / kind）的交集；
传入 ``ids`` 时以其为候选基准（过滤条件仍生效），``exclude`` 最后剔除。
每条连接独立计时（``timeout`` 为单条超时而非总时长），单条失败不影响
其他连接；WS 连接走 ``send_json``，SSE 连接走 ``send``。

- **data** (`Any`): 广播数据（SSE 连接上非 str 数据自动 JSON 序列化）
- **namespace** (`str | None`): 按服务端命名空间过滤
- **owner** (`str | None`): 按归属 owner 过滤
- **group** (`str | None`): 按业务分组过滤
- **kind** (`str | None`): 按连接种类过滤
- **ids**: 候选连接 id 集合（缺省为过滤条件命中的全部连接）
- **exclude**: 需要排除的连接 id 集合
- **timeout** (`float`): 单条连接的发送超时秒数 (默认: 10.0)
- **concurrency** (`int`): 最大并发发送数 (默认: 64)
- **raise_on_error** (`bool`): 存在失败项时在全部发送完成后抛出首个异常

**返回值** (`BroadcastResult`): 成败明细

**异常**: `Exception` - raise_on_error=True 且存在失败项时抛出首个错误

**示例**:

```python
result = await connections.broadcast(
    {"type": "kick", "reason": "full"}, group="room:1", exclude={"room:1:ab12cd34"}
)
if not result.ok:
    logger.warning(f"广播部分失败: {result.failed}")
```

---


##### `async close(connection_id: str, *, force: bool = False) -> bool`

关闭并注销指定连接

- **connection_id** (`str`): 连接 id
- **force** (`bool`): 跳过归属权限校验（框架回收路径使用）

**返回值** (`bool`): 连接是否存在（存在则已发起关闭）

**异常**: `ConnectionPermissionError` - 非 owner 关闭且未 force 时

---


##### `async close_owner(owner: str) -> int`

关闭并注销指定 owner 名下的全部连接

模块卸载 / 适配器关闭链由框架自动调用：服务端 WS/SSE 与客户端出站
连接一并回收（server 连接的 owner 即其注册模块名）。

- **owner**: 归属者（模块名 / 平台名）

**返回值** (`int`): 发起关闭的连接数

---


##### `clear(*, kind: str | None = None) -> int`

注销登记（不关闭底层连接）

服务器停止 / 管理器重置时由框架调用：连接随底层服务终止，
仅需清空登记簿防止悬挂条目。

**内部方法**

- **kind** (`str | None`): 仅注销指定种类（如 "server"）；None 清空全部

**返回值** (`int`): 注销的连接数

---

