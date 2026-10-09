# `ErisPulse.Core.Bases.router` 模块

---

## 模块概述


ErisPulse 路由抽象基类

提供 HTTP 请求和 WebSocket 连接的服务端抽象接口，
使模块和适配器无需直接依赖 FastAPI/Starlette 即可处理网络请求。

当前实现基于 FastAPI/Starlette 封装，接口风格保持 FastAPI 一致，
未来可替换底层后端（如 aiohttp.web）而无需修改业务代码。

> **提示**
> 1. 使用 HttpRequest 替代 fastapi.Request，接口完全兼容
> 2. 使用 WebSocketConnection 替代 fastapi.WebSocket，额外提供生命周期钩子
> 3. 通过 .raw 属性可访问底层原生对象（如需使用框架特有功能）
> 4. 路由注册 API (sdk.router.get/post/ws 等) 无需任何类型注解即可自动注入抽象类型

---

## 函数列表


### `respond(data: Any = None, *, status_code: int = 200, message: str | None = None, headers: dict[str, str] | None = None)`

构造 JSON 响应（HTTP 路由推荐返回方式）

与"元组返回约定"配套的帮助函数：handler 直接返回 ``respond(...)``
或返回 ``(body, status_code)`` 元组均可在 FastAPI 层得到正确响应。
``message`` 会合并进响应体：data 为 dict 时浅拷贝后写入 ``message`` 键，
其余情况构造 ``{"message": ...}``。

- **data** (`Any`): 响应体数据（dict 原样作为响应体；None 且无 message 时为空对象）
- **status_code**: int HTTP 状态码 (默认: 200)
- **message** (`str | None`): 附加的业务消息，写入响应体 ``message`` 键
- **headers** (`dict[str, str] | None`): 额外响应头

**返回值** (`JSONResponse`): 可直接作为 handler 返回值

**示例**:

```python
@router.post("MyModule", "/login")
async def login(request: HttpRequest):
    if not valid(request):
        return respond(message="unauthorized", status_code=401)
    return respond({"user_id": 1}, message="ok")
```

---


## 类列表


### `class HttpRequest`

HTTP 请求抽象封装

完全兼容 starlette.requests.Request 的接口风格。
模块可使用此类替代 fastapi.Request，无需直接依赖 FastAPI。

> **提示**
> 通过 .raw 属性可访问底层框架原生 Request 对象

**示例**:

```python
@sdk.router.get("MyModule", "/api/data")
async def get_data(request: HttpRequest):
    body = await request.json()
    return {"method": request.method, "body": body}
```


#### 方法列表


##### `__init__(request)`

- **request** (`object`): 底层框架 Request 对象

---


##### `method -> str`（property）

HTTP 方法

**返回值**: str HTTP 方法名 (GET, POST, PUT, DELETE 等)

---


##### `url`（property）

完整请求 URL

**返回值**: object URL 对象 (支持 str() 转换)

---


##### `base_url`（property）

基础 URL

**返回值**: object URL 对象

---


##### `headers`（property）

请求头 (大小写不敏感)

**返回值**: object Headers 对象 (支持 .get(key) 和 in 操作符)

---


##### `query_params`（property）

查询参数

**返回值**: object QueryParams 对象 (支持 .get(key) 和 .items())

---


##### `path_params -> dict[str, Any]`（property）

路径参数

**返回值** (`dict[str, Any]`): 路径参数字典

---


##### `cookies -> dict[str, str]`（property）

Cookie 字典

**返回值**: dict[str, str] Cookie 键值对

---


##### `client`（property）

客户端地址

**返回值** (`object | None`): 包含 .host 和 .port 属性的地址对象

---


##### `state`（property）

请求级状态存储

**返回值** (`object`): 状态对象 (支持属性读写)

---


##### `app`（property）

ASGI 应用实例

**返回值** (`object`): 应用实例

---


##### `session -> dict[str, Any]`（property）

会话数据

**返回值** (`dict[str, Any]`): 会话数据 (需要 SessionMiddleware)

**内部方法**

---


##### `auth -> Any`（property）

认证信息

**返回值** (`Any`): 认证数据 (需要 AuthenticationMiddleware)

**内部方法**

---


##### `user -> Any`（property）

用户信息

**返回值** (`Any`): 用户数据 (需要 AuthenticationMiddleware)

**内部方法**

---


##### `raw`（property）

底层框架原生 Request 对象

**返回值** (`object`): 原生请求实例 (当前为 fastapi.Request)

---


##### `async body() -> bytes`

读取请求体原始字节

**返回值** (`bytes`): 请求体内容

---


##### `async json() -> Any`

解析请求体为 JSON

**返回值** (`Any`): 解析后的 JSON 数据

---


##### `async form(**kwargs)`

解析表单数据

- **max_files** (`int`): 最大文件数 (默认: 1000)
- **max_fields** (`int`): 最大字段数 (默认: 1000)

**返回值**: object FormData 对象

---


##### `async stream()`

流式读取请求体

**返回值**: async generator 逐块返回请求体字节

---


##### `async close() -> None`

关闭请求资源

---


##### `async is_disconnected() -> bool`

检查客户端是否已断开连接

**返回值** (`bool`): 是否已断开

---


##### `url_for(name: str, /, **path_params: Any)`

根据路由名反向生成 URL

- **name** (`str`): 路由名称
- **path_params** (`Any`): 路径参数

**返回值**: object URL 对象

---


### `class WebSocketConnection(WebSocketConnectionBase)`

服务端 WebSocket 连接抽象封装

完全兼容 starlette.websockets.WebSocket 的接口风格。
模块可使用此类替代 fastapi.WebSocket，无需直接依赖 FastAPI。

额外提供 on_disconnect / on_error 生命周期钩子，
抽象化断开连接和异常处理，便于未来切换后端。

> **提示**
> 1. 通过 .raw 属性可访问底层框架原生 WebSocket 对象
> 2. 使用 @ws.on_disconnect 和 @ws.on_error 注册生命周期回调
> 3. 所有 send/receive 方法与 fastapi.WebSocket 完全一致

**示例**:

```python
@sdk.router.ws("MyModule", "/ws/chat")
async def chat(ws: WebSocketConnection):
    @ws.on_disconnect
    async def on_close(ws, reason="unknown"):
        print(f"Disconnected: {reason}")
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")
```


#### 方法列表


##### `__init__(websocket, *, connection_id: str = '', namespace: str = '', owner: str = '', kind: str = 'server')`

- **websocket** (`object`): 底层框架 WebSocket 对象 (fastapi.WebSocket)
- **connection_id** (`str`): 连接池分配的连接 id（未登记时为空串）
- **namespace** (`str`): 服务端路由命名空间
- **owner** (`str`): 归属 owner（模块名 / 平台名）
- **kind** (`str`): 连接种类（默认 "server"）

---


##### `base_url`（property）

基础 URL

**返回值**: object URL 对象

---


##### `query_params`（property）

查询参数

**返回值**: object QueryParams 对象

---


##### `path_params -> dict[str, Any]`（property）

路径参数

**返回值** (`dict[str, Any]`): 路径参数字典

---


##### `cookies -> dict[str, str]`（property）

Cookie 字典

**返回值**: dict[str, str] Cookie 键值对

---


##### `client`（property）

客户端地址

**返回值** (`object | None`): 包含 .host 和 .port 属性的地址对象

---


##### `state`（property）

连接级状态存储

**返回值** (`object`): 状态对象

---


##### `app`（property）

ASGI 应用实例

**返回值** (`object`): 应用实例

---


##### `session -> dict[str, Any]`（property）

会话数据

**返回值** (`dict[str, Any]`): 会话数据

---


##### `auth -> Any`（property）

认证信息

**返回值** (`Any`): 认证数据

---


##### `user -> Any`（property）

用户信息

**返回值** (`Any`): 用户数据

---


##### `async accept(subprotocol: str | None = None, headers: Iterable[tuple[bytes, bytes]] | None = None) -> None`

接受 WebSocket 连接

- **subprotocol** (`str | None`): 子协议 (可选)
- **headers**: Iterable[tuple[bytes, bytes]] | None 额外响应头 (可选)

---


##### `async _close(code: int = 1000, reason: str | None = None) -> None`

实际关闭动作（权限校验见基类 close）

- **code** (`int`): 关闭码 (默认: 1000)
- **reason** (`str | None`): 关闭原因 (可选)

---


##### `async receive_text() -> str`

接收文本消息

**返回值** (`str`): 文本内容

---


##### `async receive_bytes() -> bytes`

接收二进制消息

**返回值** (`bytes`): 二进制内容

---


##### `async receive_json(mode: str = 'text') -> Any`

接收 JSON 消息

- **mode** (`str`): 接收模式 ("text" 或 "binary") (默认: "text")

**返回值** (`Any`): 解析后的 JSON 数据

---


##### `async send_text(data: str) -> None`

发送文本消息

- **data** (`str`): 文本内容

---


##### `async send_bytes(data: bytes) -> None`

发送二进制消息

- **data** (`bytes`): 二进制内容

---


##### `async send_json(data: Any, mode: str = 'text') -> None`

发送 JSON 消息

- **data** (`Any`): 要序列化的数据
- **mode** (`str`): 发送模式 ("text" 或 "binary") (默认: "text")

---


##### `async receive()`

低级 ASGI receive

**返回值**: dict ASGI 消息

**内部方法**

---


##### `async send(message) -> None`

低级 ASGI send

- **message**: dict ASGI 消息

**内部方法**

---


### `class SseEmitter(_ConnectionIdentity)`

SSE (Server-Sent Events) 事件发送器 — 服务器无关的 SSE 协议实现

封装 SSE 协议的格式化细节，通过回调函数与服务器层解耦。
无论底层是 FastAPI、aiohttp 还是其他 HTTP 框架，只需提供
``on_send`` 和 ``on_close`` 回调即可使用。

自动生成事件 ID，支持自定义事件类型和重试间隔。
连接经连接池登记后可被广播 / 分组 / 跨模块查看
（kind 为 ``"sse"``，``send`` 即广播的目标方法）。

> **提示**
> 1. 由框架自动创建，模块开发者只需在 handler 中接收 sse 参数
> 2. ``send()`` 方法自动处理 JSON 序列化（非 str 数据转为 JSON）
> 3. 通过 ``request`` 属性可访问客户端请求（query params、headers 等）
> 4. 调用 ``close()`` 优雅关闭连接（默认校验归属权限）

**示例**:

```python
@sdk.router.sse("MyModule", "/events")
async def event_stream(sse: SseEmitter):
    sse.join_group("dashboard")
    while True:
        await sse.send({"msg": "hello"}, event="update")
        await asyncio.sleep(1)
```


#### 方法列表


##### `__init__(on_send, on_close = None, request = None, *, connection_id: str = '', namespace: str = '', owner: str = '')`

- **on_send**: 回调函数，接收格式化后的 SSE 文本并发送到底层传输层
- **on_close**: 可选回调函数，连接关闭时调用
- **request**: 可选，底层 HTTP 请求对象
- **connection_id** (`str`): 连接池分配的连接 id（未登记时为空串）
- **namespace** (`str`): 服务端路由命名空间
- **owner** (`str`): 归属 owner（模块名 / 平台名）

---


##### `request`（property）

底层 HTTP 请求对象

可用于读取查询参数、请求头等客户端信息。
在 FastAPI 环境下为 ``fastapi.Request`` 实例。

**返回值** (`object`): 底层 Request 对象或 None

---


##### `closed -> bool`（property）

连接是否已关闭

**返回值**: bool

---


##### `async send(data = None, event: str | None = None, id: str | None = None, retry: int | None = None) -> None`

发送一个 SSE 事件

根据 SSE 协议自动格式化输出：
- ``event:`` 行（指定事件类型）
- ``id:`` 行（事件 ID，自动生成递增 ID）
- ``retry:`` 行（客户端重连间隔，毫秒）
- ``data:`` 行（事件数据，多行自动拆分）
- 末尾双换行结束一个事件

- **data**: 事件数据。非 str 类型自动 JSON 序列化。为 None 时仅发送事件类型
- **event**: 可选事件类型名
- **id**: 可选事件 ID，不传则自动生成
- **retry**: 可选重试间隔（毫秒）

**异常**: `RuntimeError` - 连接已关闭时抛出

**示例**:

```python
await sse.send({"msg": "hello"})
await sse.send("plain text", event="notice")
await sse.send({"error": "boom"}, event="error", id="err-1")
```

---


##### `async close(*, force: bool = False) -> None`

关闭 SSE 连接（默认校验归属权限）

非 owner 模块关闭他人连接时抛出
:class:`~ErisPulse.Core.Bases.errors.ConnectionPermissionError`；
运行时上下文为空（框架内部路径 / 未归因代码）时放行。
安全方法，可多次调用。第一次调用时触发 ``on_close`` 回调。

- **force** (`bool`): 跳过权限校验（框架内部回收路径使用）

**异常**: `ConnectionPermissionError` - 跨 owner 关闭且未 force 时

---

