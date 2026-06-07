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

## 类列表


### `class HttpRequest`

HTTP 请求抽象封装

完全兼容 starlette.requests.Request 的接口风格。
模块可使用此类替代 fastapi.Request，无需直接依赖 FastAPI。

> **提示**
> 通过 .raw 属性可访问底层框架原生 Request 对象

**示例**:
```python
>>> @sdk.router.get("MyModule", "/api/data")
... async def get_data(request: HttpRequest):
...     body = await request.json()
...     return {"method": request.method, "body": body}
```


#### 方法列表


##### `__init__(request)`

:param request: object 底层框架 Request 对象

---


##### `method()`

HTTP 方法

:return: str HTTP 方法名 (GET, POST, PUT, DELETE 等)

---


##### `url()`

完整请求 URL

:return: object URL 对象 (支持 str() 转换)

---


##### `base_url()`

基础 URL

:return: object URL 对象

---


##### `headers()`

请求头 (大小写不敏感)

:return: object Headers 对象 (支持 .get(key) 和 in 操作符)

---


##### `query_params()`

查询参数

:return: object QueryParams 对象 (支持 .get(key) 和 .items())

---


##### `path_params()`

路径参数

:return: dict[str, Any] 路径参数字典

---


##### `cookies()`

Cookie 字典

:return: dict[str, str] Cookie 键值对

---


##### `client()`

客户端地址

:return: object | None 包含 .host 和 .port 属性的地址对象

---


##### `state()`

请求级状态存储

:return: object 状态对象 (支持属性读写)

---


##### `app()`

ASGI 应用实例

:return: object 应用实例

---


##### `session()`

会话数据

:return: dict[str, Any] 会话数据 (需要 SessionMiddleware)

> **内部方法**

---


##### `auth()`

认证信息

:return: Any 认证数据 (需要 AuthenticationMiddleware)

> **内部方法**

---


##### `user()`

用户信息

:return: Any 用户数据 (需要 AuthenticationMiddleware)

> **内部方法**

---


##### `raw()`

底层框架原生 Request 对象

:return: object 原生请求实例 (当前为 fastapi.Request)

---


##### `async async body()`

读取请求体原始字节

:return: bytes 请求体内容

---


##### `async async json()`

解析请求体为 JSON

:return: Any 解析后的 JSON 数据

---


##### `async async form()`

解析表单数据

:param max_files: int 最大文件数 (默认: 1000)
:param max_fields: int 最大字段数 (默认: 1000)
:return: object FormData 对象

---


##### `async async stream()`

流式读取请求体

:return: async generator 逐块返回请求体字节

---


##### `async async close()`

关闭请求资源

---


##### `async async is_disconnected()`

检查客户端是否已断开连接

:return: bool 是否已断开

---


##### `url_for()`

根据路由名反向生成 URL

:param name: str 路由名称
:param path_params: Any 路径参数
:return: object URL 对象

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
>>> @sdk.router.ws("MyModule", "/ws/chat")
... async def chat(ws: WebSocketConnection):
...     @ws.on_disconnect
...     async def on_close(ws, reason="unknown"):
...         print(f"Disconnected: {reason}")
...     async for msg in ws.iter_text():
...         await ws.send_text(f"Echo: {msg}")
```


#### 方法列表


##### `__init__(websocket)`

:param websocket: object 底层框架 WebSocket 对象 (fastapi.WebSocket)

---


##### `base_url()`

基础 URL

:return: object URL 对象

---


##### `query_params()`

查询参数

:return: object QueryParams 对象

---


##### `path_params()`

路径参数

:return: dict[str, Any] 路径参数字典

---


##### `cookies()`

Cookie 字典

:return: dict[str, str] Cookie 键值对

---


##### `client()`

客户端地址

:return: object | None 包含 .host 和 .port 属性的地址对象

---


##### `state()`

连接级状态存储

:return: object 状态对象

---


##### `app()`

ASGI 应用实例

:return: object 应用实例

---


##### `session()`

会话数据

:return: dict[str, Any] 会话数据

---


##### `auth()`

认证信息

:return: Any 认证数据

---


##### `user()`

用户信息

:return: Any 用户数据

---


##### `async async accept(subprotocol: str | None = None, headers: Iterable[tuple[bytes, bytes]] | None = None)`

接受 WebSocket 连接

:param subprotocol: str | None 子协议 (可选)
:param headers: Iterable[tuple[bytes, bytes]] | None 额外响应头 (可选)

---


##### `async async close(code: int = 1000, reason: str | None = None)`

关闭 WebSocket 连接

:param code: int 关闭码 (默认: 1000)
:param reason: str | None 关闭原因 (可选)

---


##### `async async receive_text()`

接收文本消息

:return: str 文本内容

---


##### `async async receive_bytes()`

接收二进制消息

:return: bytes 二进制内容

---


##### `async async receive_json(mode: str = 'text')`

接收 JSON 消息

:param mode: str 接收模式 ("text" 或 "binary") (默认: "text")
:return: Any 解析后的 JSON 数据

---


##### `async async send_text(data: str)`

发送文本消息

:param data: str 文本内容

---


##### `async async send_bytes(data: bytes)`

发送二进制消息

:param data: bytes 二进制内容

---


##### `async async send_json(data: Any, mode: str = 'text')`

发送 JSON 消息

:param data: Any 要序列化的数据
:param mode: str 发送模式 ("text" 或 "binary") (默认: "text")

---


##### `async async receive()`

低级 ASGI receive

:return: dict ASGI 消息

> **内部方法**

---


##### `async async send(message)`

低级 ASGI send

:param message: dict ASGI 消息

> **内部方法**

---


### `class SseEmitter`

SSE (Server-Sent Events) 事件发送器 — 服务器无关的 SSE 协议实现

封装 SSE 协议的格式化细节，通过回调函数与服务器层解耦。
无论底层是 FastAPI、aiohttp 还是其他 HTTP 框架，只需提供
``on_send`` 和 ``on_close`` 回调即可使用。

自动生成事件 ID，支持自定义事件类型和重试间隔。

> **提示**
> 1. 由框架自动创建，模块开发者只需在 handler 中接收 sse 参数
> 2. ``send()`` 方法自动处理 JSON 序列化（非 str 数据转为 JSON）
> 3. 通过 ``request`` 属性可访问客户端请求（query params、headers 等）
> 4. 调用 ``close()`` 优雅关闭连接

**示例**:
```python
>>> @sdk.router.sse("MyModule", "/events")
... async def event_stream(sse: SseEmitter):
...     while True:
...         await sse.send({"msg": "hello"}, event="update")
...         await asyncio.sleep(1)
```


#### 方法列表


##### `__init__(on_send, on_close = None, request = None)`

:param on_send: 回调函数，接收格式化后的 SSE 文本并发送到底层传输层
:param on_close: 可选回调函数，连接关闭时调用
:param request: 可选，底层 HTTP 请求对象

---


##### `request()`

底层 HTTP 请求对象

可用于读取查询参数、请求头等客户端信息。
在 FastAPI 环境下为 ``fastapi.Request`` 实例。

:return: object 底层 Request 对象或 None

---


##### `closed()`

连接是否已关闭

:return: bool

---


##### `async async send(data = None, event: str | None = None, id: str | None = None, retry: int | None = None)`

发送一个 SSE 事件

根据 SSE 协议自动格式化输出：
- ``event:`` 行（指定事件类型）
- ``id:`` 行（事件 ID，自动生成递增 ID）
- ``retry:`` 行（客户端重连间隔，毫秒）
- ``data:`` 行（事件数据，多行自动拆分）
- 末尾双换行结束一个事件

:param data: 事件数据。非 str 类型自动 JSON 序列化。为 None 时仅发送事件类型
:param event: 可选事件类型名
:param id: 可选事件 ID，不传则自动生成
:param retry: 可选重试间隔（毫秒）

**异常**: `RuntimeError` - 连接已关闭时抛出

**示例**:
```python
>>> await sse.send({"msg": "hello"})
>>> await sse.send("plain text", event="notice")
>>> await sse.send({"error": "boom"}, event="error", id="err-1")
```

---


##### `async async close()`

关闭 SSE 连接

安全方法，可多次调用。第一次调用时触发 ``on_close`` 回调。

---

