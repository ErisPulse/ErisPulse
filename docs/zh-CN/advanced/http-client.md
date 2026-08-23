# 网络客户端

ErisPulse 提供了统一的网络客户端，聚合了 HTTP 请求、WebSocket 连接和连接池管理。模块和适配器**必须优先使用**此客户端，而非自行导入 `aiohttp` / `httpx` / `requests` 等第三方库。

## 概述

网络客户端的主要功能：

- **统一接口**：提供 `get` / `post` / `put` / `delete` / `patch` / `request` 方法
- **WebSocket 客户端**：通过 `ws_connect` 建立客户端 WebSocket 连接
- **自动日志**：所有请求自动记录日志和统计信息
- **生命周期集成**：每次请求触发 `client.request` 生命周期事件，WS 连接触发 `client.ws.connect` 事件
- **重试支持**：可配置自动重试次数和间隔
- **超时控制**：独立的连接超时和请求超时
- **连接池复用**：基于 aiohttp.ClientSession 的连接池管理
- **异常体系**：aiohttp 异常自动转换为 ErisPulse 异常 (ClientError 体系)

## 快速开始

### HTTP 请求

```python
from ErisPulse.Core import client

# GET 请求
resp = await client.get("https://httpbin.org/get")
data = await resp.json()
print(resp.status)  # 200

# POST 请求
resp = await client.post(
    "https://httpbin.org/post",
    json={"key": "value"},
)
data = await resp.json()
```

### WebSocket 连接

```python
from ErisPulse.Core import client

ws = await client.ws_connect("wss://example.com/ws")

async for text in ws.iter_text():
    await ws.send_text(f"Echo: {text}")
```

## HttpResponse

所有请求方法返回 `HttpResponse` 对象：

```python
from ErisPulse.Core import client

resp = await client.get("https://httpbin.org/get")

resp.status       # int - HTTP 状态码 (如 200, 404)
resp.reason       # str | None - 状态描述 (如 "OK")
resp.headers      # 响应头 (大小写不敏感)
resp.content_type # str | None - Content-Type
resp.url          # 最终 URL (可能因重定向变化)
resp.raw          # 底层原生响应对象 (当前为 aiohttp.ClientResponse)

# 读取响应体
body = await resp.read()       # bytes
text = await resp.text()       # str
data = await resp.json()       # 解析 JSON
text = await resp.text("gbk")  # 指定编码
```

## 请求方法

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

# JSON 请求体
resp = await client.post(
    "https://api.example.com/users",
    json={"name": "Alice", "age": 30},
)

# 表单请求体
resp = await client.post(
    "https://api.example.com/login",
    data={"username": "admin", "password": "123"},
)

# 原始数据
resp = await client.post(
    "https://api.example.com/upload",
    data=b"raw bytes",
    headers={"Content-Type": "application/octet-stream"},
)

# 文件上传 (使用 files 参数, 无需导入 aiohttp)
# 格式: {字段名: 文件对象/bytes/(filename, file)/(filename, file, content_type)}
resp = await client.post(
    "https://api.example.com/upload",
    data={"description": "头像"},            # 可选: 同时携带普通表单字段
    files={
        "file": ("photo.png", open("photo.png", "rb"), "image/png"),
    },
)

# 简化写法: 直接传文件对象
resp = await client.post(
    "https://api.example.com/upload",
    files={"file": open("photo.png", "rb")},
)

# 内存数据直接上传 (无需落盘)
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

## 参数说明

### HTTP 请求参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `url` | `str` | 请求 URL |
| `params` | `dict[str, str]` | 查询参数 (可选) |
| `headers` | `dict[str, str]` | 额外请求头 (可选) |
| `data` | `Any` | 请求体 (表单或原始数据) (可选) |
| `json` | `Any` | JSON 请求体 (可选) |
| `files` | `dict[str, Any]` | 文件上传字段 (可选, 自动构建 multipart/form-data) |
| `timeout` | `float` | 本次请求超时 (秒) (可选, 覆盖默认值) |
| `max_retries` | `int` | 本次最大重试次数 (可选, 覆盖默认值) |

### ws_connect 参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `url` | `str` | WebSocket 服务器 URL |
| `headers` | `dict[str, str]` | 额外请求头 (可选) |
| `heartbeat` | `float` | 心跳间隔秒数 (可选) |

## 超时与重试

```python
from ErisPulse.Core import Client

# 创建带自定义超时的客户端
client = Client(
    timeout=60,           # 请求总超时 60s
    connect_timeout=5,    # 连接超时 5s
    max_retries=3,        # 失败自动重试 3 次
    retry_delay=2,        # 重试间隔 2s
)

# 单次请求覆盖超时
resp = await client.get("https://slow-api.example.com/data", timeout=120)
```

> [!NOTE]
> 客户端类从 2.8.0 起更名为 `Client`（`sdk.client` 属性名不变）；旧名 `HttpClient` 保留为兼容别名，老代码无需修改。

## 自定义默认头

```python
client = Client(
    headers={
        "Authorization": "Bearer token",
        "X-App-Id": "my-app",
    },
    user_agent="MyBot/1.0",
)
```

## 请求统计

```python
from ErisPulse.Core import client

# 查看统计
stats = client.stats
# {"total_requests": 42, "total_errors": 1, "total_bytes_sent": 0, "total_bytes_received": 0}

# 重置统计
client.reset_stats()
```

## 生命周期事件

### HTTP 请求事件

每次请求完成后触发 `client.request` 事件，可用于监控：

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("client.request")
async def on_request(event_data):
    print(f"{event_data['method']} {event_data['url']} -> {event_data['status']} ({event_data['elapsed']}s)")
```

### WebSocket 连接事件

每次 WebSocket 连接建立后触发 `client.ws.connect` 事件：

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("client.ws.connect")
async def on_ws_connect(event_data):
    print(f"WS 连接: {event_data['url']}")
```

## 上下文管理

```python
# 作为上下文管理器，自动关闭会话
async with Client(timeout=30) as client:
    resp = await client.get("https://httpbin.org/get")
    data = await resp.json()
```

## WebSocket 客户端

通过 `client.ws_connect()` 建立 WebSocket 客户端连接，返回 `ClientWebSocket` 对象。客户端和服务端 WebSocket 共享相同的 `WebSocketConnectionBase` 基类，send/receive/iter 接口完全一致。

### 基本用法

```python
from ErisPulse.Core import client

ws = await client.ws_connect("wss://example.com/ws", heartbeat=30)

await ws.send_text("Hello")
await ws.send_bytes(b"\x00\x01\x02")
await ws.send_json({"type": "ping"})
```

### 接收消息

#### 高级方法 (推荐)

自动过滤消息类型，断开时抛出 `WebSocketDisconnect`：

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases.errors import WebSocketDisconnect

ws = await client.ws_connect("wss://example.com/ws")

# 单条接收
text = await ws.receive_text()    # str
data = await ws.receive_bytes()   # bytes
obj = await ws.receive_json()     # dict / list

# 迭代接收 (自动在断开时停止)
async for text in ws.iter_text():
    print(text)

async for data in ws.iter_bytes():
    print(data)

async for obj in ws.iter_json():
    print(obj)
```

#### 低级方法

使用 `receive()` 和 `iter_messages()` 处理原始消息类型，可区分 TEXT / BINARY / CLOSE / ERROR：

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases.websocket import WSMessage

ws = await client.ws_connect("wss://example.com/ws")

# 单条接收原始消息
msg = await ws.receive()
# msg.type  -> WSMessage.TEXT / WSMessage.BINARY / WSMessage.CLOSE / WSMessage.ERROR
# msg.data  -> str | bytes | None

# 迭代原始消息 (CLOSE/ERROR 时自动停止)
async for msg in ws.iter_messages():
    if msg.type == WSMessage.TEXT:
        print(f"文本: {msg.data}")
    elif msg.type == WSMessage.BINARY:
        print(f"二进制: {len(msg.data)} bytes")
```

### WSMessage

`WSMessage` 是统一的 WebSocket 消息类型，不依赖底层库：

| 属性 | 类型 | 说明 |
|------|------|------|
| `type` | `str` | 消息类型: `WSMessage.TEXT` / `WSMessage.BINARY` / `WSMessage.CLOSE` / `WSMessage.ERROR` |
| `data` | `Any` | 消息数据 |

### ClientWebSocket 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `url` | `URL` | 连接 URL |
| `headers` | `Headers` | 响应头 |
| `closed` | `bool` | 连接是否已关闭 |
| `raw` | `object` | 底层原生对象 (aiohttp.ClientWebSocketResponse) |

### 生命周期钩子

与 `服务端 WebSocketConnection` 一致，支持 `on_disconnect` 和 `on_error` 回调：

```python
from ErisPulse.Core import client

ws = await client.ws_connect("wss://example.com/ws")

@ws.on_disconnect
async def handle_disconnect(ws, reason="unknown"):
    print(f"连接断开: {reason}")

@ws.on_error
async def handle_error(ws, error=""):
    print(f"连接错误: {error}")
```

### 关闭连接

```python
await ws.close(code=1000, reason="Normal closure")
```

## 异常体系

ErisPulse 定义了统一的异常层级，通过 `sdk.client` 发起的请求会自动将底层 aiohttp 异常转换为 ErisPulse 异常。

> **向后兼容**：直接使用 `aiohttp.ClientSession` 的旧模块/适配器完全不受影响。异常转换仅在通过 `sdk.client` 发起请求时生效，直接使用 aiohttp 的代码仍然捕获 `aiohttp.ClientError` 等原生异常。两种方式可以共存。

### 异常层级

```
ErisPulseError
├── ClientError                  # 所有 HTTP/WS 客户端请求异常的基类
│   ├── ClientConnectionError    # 连接失败 (DNS 解析失败、连接被拒绝、网络不可达)
│   ├── ClientTimeoutError       # 连接超时或请求超时
│   └── HTTPStatusError          # HTTP 4xx/5xx 状态码错误
└── WebSocketError               # WebSocket 异常基类
    └── WebSocketDisconnect      # WebSocket 连接断开 (客户端和服务端通用)
```

### 异常捕获

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

# HTTP 请求异常处理
try:
    resp = await client.get("https://api.example.com/data")
    data = await resp.json()
except ClientConnectionError:
    print("无法连接到服务器")
except ClientTimeoutError:
    print("请求超时")
except ClientError as e:
    print(f"请求失败: {e}")

# WebSocket 异常处理
try:
    ws = await client.ws_connect("wss://example.com/ws")
    async for text in ws.iter_text():
        await ws.send_text(f"Echo: {text}")
except WebSocketDisconnect as e:
    print(f"连接断开: code={e.code}, reason={e.reason}")
except WebSocketError as e:
    print(f"WebSocket 错误: {e}")
```

### 统一捕获

使用 `ClientError` 统一捕获所有 HTTP/WS 客户端请求异常：

```python
from ErisPulse.Core.Bases.errors import ClientError

try:
    resp = await client.get("https://api.example.com/data")
except ClientError as e:
    print(f"客户端错误: {e}")
```

### HTTPStatusError

当需要在请求后检查状态码并抛出异常时，可手动使用：

```python
from ErisPulse.Core.Bases.errors import HTTPStatusError

resp = await client.get("https://api.example.com/data")
if resp.status >= 400:
    raise HTTPStatusError(resp.status, await resp.text())
```

## 适配器中使用

适配器可使用全局客户端或自行创建客户端实例发送平台 API 请求：

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
            self.logger.error(f"API 调用失败: {e}")
            raise
```

> 也可通过 `from ErisPulse import sdk` 使用 `sdk.client`，效果相同。

## 最佳实践

1. **优先使用全局客户端**：使用 `from ErisPulse.Core import client` 获取全局单例，便于框架统一管理和监控
2. **避免直接导入 aiohttp**：使用 `client` 替代 `aiohttp.ClientSession`，未来更换底层实现无需修改代码。旧代码直接使用 aiohttp 仍可正常工作，两种方式可以共存
3. **使用 ErisPulse 异常体系**：通过 `sdk.client` 请求时捕获 `ClientError` 而非 `aiohttp.ClientError`，确保代码不依赖特定 HTTP 库。直接使用 aiohttp 的旧代码不受影响
4. **合理设置超时**：根据 API 响应速度设置合理的超时时间，避免长时间阻塞
5. **使用重试机制**：对不稳定的 API 启用重试，提高可靠性
6. **监控请求统计**：通过 `sdk.client.stats` 或 `client.request` 生命周期事件监控请求情况
7. **WebSocket 使用高级方法**：优先使用 `iter_text` / `iter_json` 等高级方法，仅在需要区分消息类型时使用 `iter_messages`

## 相关文档

- [路由管理器](router.md) - HTTP/WebSocket 服务端路由（服务端 WebSocketConnection 与客户端共享同一基类）
- [适配器开发指南](../developer-guide/adapters/getting-started.md) - 适配器中使用 HTTP 客户端
- [生命周期管理](lifecycle.md) - 监听请求事件
