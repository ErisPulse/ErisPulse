# `ErisPulse.Core.client` 模块

---

## 模块概述


ErisPulse HTTP/WS 客户端

基于 aiohttp 的统一 HTTP 和 WebSocket 客户端实现，提供完整的请求/响应/WS 抽象。
模块和适配器应优先使用此客户端发送 HTTP 请求和建立 WS 连接，而非自行导入 aiohttp。

底层 aiohttp 异常会在内部捕获并转换为 ErisPulse 异常体系，
确保业务代码不依赖任何特定 HTTP 库。

> **提示**
> 1. 使用 sdk.client 获取全局客户端单例
> 2. 支持 get / post / put / delete / patch / request / ws_connect 等方法
> 3. aiohttp 异常自动转换为 ErisPulse 异常 (ClientError 体系)
> 4. 自动记录请求日志和统计信息

---

## 类列表


### `class HttpResponse(BaseHttpResponse)`

HTTP 响应封装

提供与 aiohttp.ClientResponse 一致的访问接口。
自动读取并缓存响应体，避免重复读取。

> **提示**
> 通过 .raw 属性可访问底层原生响应对象

**示例**:
```python
>>> resp = await sdk.client.get("https://httpbin.org/get")
>>> print(resp.status)
>>> data = await resp.json()
```


#### 方法列表


##### `__init__(response)`

- **response** (`object`): 底层框架 Response 对象

---


##### `status()`

HTTP 状态码

**返回值** (`int`): 状态码 (如 200, 404)

---


##### `reason()`

状态描述

**返回值** (`str`): | None 状态原因短语

---


##### `headers()`

响应头

**返回值** (`object`): 大小写不敏感的响应头映射

---


##### `content_type()`

Content-Type 值

**返回值** (`str`): | None 内容类型

---


##### `charset()`

字符编码

**返回值** (`str`): | None 编码名称

---


##### `url()`

响应 URL (可能因重定向而与请求 URL 不同)

**返回值** (`object`): URL 对象

---


##### `raw()`

底层框架原生 Response 对象

**返回值** (`object`): 原生响应实例 (当前为 aiohttp.ClientResponse)

---


##### `async read()`

读取响应体原始字节 (自动缓存)

**返回值** (`bytes`): 响应体内容

---


### `class ClientWebSocket(BaseClientWebSocket)`

客户端 WebSocket 连接 (基于 aiohttp)

封装 aiohttp.ClientWebSocketResponse，提供统一的 WebSocket 客户端接口。
通过 sdk.client.ws_connect() 获取实例。

> **提示**
> 1. 使用 iter_text/iter_bytes/iter_json 自动过滤消息类型
> 2. 使用 receive/iter_messages 处理原始消息类型 (如 CLOSE/ERROR)
> 3. 通过 .raw 属性可访问底层 aiohttp.ClientWebSocketResponse

**示例**:
```python
>>> ws = await sdk.client.ws_connect("wss://example.com/ws")
>>> async for text in ws.iter_text():
...     await ws.send_text(f"Echo: {text}")
```


#### 方法列表


##### `__init__(ws)`

- **ws** (`aiohttp.ClientWebSocketResponse`): 底层 aiohttp WS 对象

---


##### `closed()`

连接是否已关闭

**返回值** (`bool`): 是否已关闭

---


##### `async send_text(data: str)`

发送文本消息

- **data** (`str`): 文本内容

---


##### `async send_bytes(data: bytes)`

发送二进制消息

- **data** (`bytes`): 二进制内容

---


##### `async send_json(data: Any, mode: str = 'text')`

发送 JSON 消息

- **data** (`Any`): 要序列化的数据
- **mode** (`str`): 发送模式 ("text" 或 "binary") (默认: "text")

---


##### `_convert_ws_msg(msg)`

转换 aiohttp WSMessage 为 ErisPulse WSMessage

> **内部方法**

---


##### `async receive()`

接收原始消息

**返回值** (`WSMessage`): 消息对象

---


##### `async receive_text()`

接收文本消息

**返回值** (`str`): 文本内容
**异常**: `WebSocketDisconnect` - 连接断开时
**异常**: `WebSocketError` - 收到非文本消息时

---


##### `async receive_bytes()`

接收二进制消息

**返回值** (`bytes`): 二进制内容
**异常**: `WebSocketDisconnect` - 连接断开时
**异常**: `WebSocketError` - 收到非二进制消息时

---


##### `async receive_json(mode: str = 'text')`

接收 JSON 消息

- **mode** (`str`): 接收模式 ("text" 或 "binary") (默认: "text")
**返回值** (`Any`): 解析后的 JSON 数据
**异常**: `WebSocketDisconnect` - 连接断开时

---


##### `async close(code: int = 1000, reason: str | None = None)`

关闭 WebSocket 连接

- **code** (`int`): 关闭码 (默认: 1000)
- **reason** (`str`): | None 关闭原因 (可选)

---


### `class HttpClient(BaseHttpClient)`

HTTP/WS 客户端 (基于 aiohttp)

提供统一的异步 HTTP 请求和 WebSocket 连接接口。
自动管理连接池和会话生命周期，底层 aiohttp 异常自动转换为 ErisPulse 异常。

> **提示**
> 1. 通过 sdk.client 获取全局单例，也可自行实例化
> 2. 使用 get/post/put/delete/patch 快捷方法或通用 request 方法
> 3. 使用 ws_connect 建立 WebSocket 连接
> 4. 支持 ErisPulse 异常体系，业务代码不依赖 aiohttp
> 5. 所有请求自动通过 lifecycle 发送事件，可用于监控

**示例**:
```python
>>> resp = await sdk.client.get("https://httpbin.org/get")
>>> data = await resp.json()
>>>
>>> ws = await sdk.client.ws_connect("wss://example.com/ws")
>>> await ws.send_text("Hello")
```


#### 方法列表


##### `__init__()`

- **timeout** (`float`): | None 请求总超时 (秒) (默认: 30)
- **connect_timeout** (`float`): | None 连接超时 (秒) (默认: 10)
- **max_retries** (`int`): 最大重试次数 (默认: 1)
- **retry_delay** (`float`): 重试间隔 (秒) (默认: 1)
- **headers** (`dict[str,`): str] 全局默认请求头 (可选)
- **user_agent** (`str`): User-Agent 字符串 (可选)
- **proxy** (`str`): | None 代理 URL（如 http://127.0.0.1:7890），为 None 时自动检测环境变量

---


##### `_build_session_kwargs(timeout)`

构建 aiohttp.ClientSession 参数，自动注入代理

---


##### `async request(method: str, url: str)`

发送 HTTP 请求

- **method** (`str`): HTTP 方法 (GET, POST, PUT, DELETE, PATCH 等)
- **url** (`str`): 请求 URL
- **params** (`dict[str,`): str] | None 查询参数 (可选)
- **headers** (`dict[str,`): str] | None 额外请求头 (可选)
- **data** (`Any`): 请求体 (表单或原始数据) (可选)
- **json** (`Any`): JSON 请求体 (可选)
- **timeout** (`float`): | None 本次请求超时 (秒) (可选, 覆盖默认值)
- **max_retries** (`int`): | None 本次最大重试次数 (可选, 覆盖默认值)
- **kwargs** (`传递给底层请求的额外参数`): **返回值** (`HttpResponse`): 响应对象

**异常**: `ClientConnectionError` - 连接失败
**异常**: `ClientTimeoutError` - 请求超时
**异常**: `ClientError` - 其他客户端错误

**示例**:
```python
>>> resp = await client.request("GET", "https://httpbin.org/get", params={"q": "test"})
```

---


##### `async ws_connect(url: str)`

建立 WebSocket 连接

- **url** (`str`): WebSocket 服务器 URL
- **headers** (`dict[str,`): str] | None 额外请求头 (可选)
- **heartbeat** (`float`): | None 心跳间隔秒数 (可选)
- **kwargs** (`传递给底层`): ws_connect 的额外参数
**返回值** (`ClientWebSocket`): WebSocket 连接对象

**异常**: `ClientConnectionError` - 连接失败
**异常**: `ClientError` - 其他客户端错误

**示例**:
```python
>>> ws = await sdk.client.ws_connect("wss://example.com/ws", heartbeat=30)
>>> async for text in ws.iter_text():
...     await ws.send_text(f"Echo: {text}")
```

---


##### `async get(url: str)`

发送 GET 请求

- **url** (`str`): 请求 URL
- **params** (`dict[str,`): str] | None 查询参数 (可选)
- **headers** (`dict[str,`): str] | None 额外请求头 (可选)
**返回值** (`HttpResponse`): 响应对象

**示例**:
```python
>>> resp = await client.get("https://httpbin.org/get", params={"q": "test"})
>>> data = await resp.json()
```

---


##### `async post(url: str)`

发送 POST 请求

- **url** (`str`): 请求 URL
- **data** (`Any`): 请求体 (表单或原始数据) (可选)
- **json** (`Any`): JSON 请求体 (可选)
- **headers** (`dict[str,`): str] | None 额外请求头 (可选)
**返回值** (`HttpResponse`): 响应对象

**示例**:
```python
>>> resp = await client.post("https://httpbin.org/post", json={"key": "value"})
```

---


##### `async put(url: str)`

发送 PUT 请求

- **url** (`str`): 请求 URL
- **data** (`Any`): 请求体 (可选)
- **json** (`Any`): JSON 请求体 (可选)
- **headers** (`dict[str,`): str] | None 额外请求头 (可选)
**返回值** (`HttpResponse`): 响应对象

---


##### `async delete(url: str)`

发送 DELETE 请求

- **url** (`str`): 请求 URL
- **headers** (`dict[str,`): str] | None 额外请求头 (可选)
**返回值** (`HttpResponse`): 响应对象

---


##### `async patch(url: str)`

发送 PATCH 请求

- **url** (`str`): 请求 URL
- **data** (`Any`): 请求体 (可选)
- **json** (`Any`): JSON 请求体 (可选)
- **headers** (`dict[str,`): str] | None 额外请求头 (可选)
**返回值** (`HttpResponse`): 响应对象

---


##### `stats()`

请求统计

**返回值** (`dict[str,`): int] 统计数据 (total_requests, total_errors 等)

---


##### `reset_stats()`

重置统计数据

---

