# `ErisPulse.Core.Bases.websocket` 模块

---

## 模块概述


ErisPulse WebSocket 共享基类

定义客户端和服务端 WebSocket 连接的统一抽象接口。
send/receive/iter 方法签名在两端保持一致，具体实现由子类提供。

> **提示**
> 1. 客户端和服务端 WebSocket 共享相同的 send/receive/iter 接口
> 2. iter_text/iter_bytes/iter_json 自动在断开时停止迭代
> 3. 通过 on_disconnect/on_error 注册生命周期回调

---

## 类列表


### `class WSMessage`

WebSocket 消息抽象

统一的 WebSocket 消息类型，不依赖底层库的消息类型。
用于客户端 WebSocket 的低级消息接收。

**示例**:
```python
>>> async for msg in ws.iter_messages():
...     if msg.type == WSMessage.TEXT:
...         print(msg.data)
...     elif msg.type == WSMessage.CLOSE:
...         break
```


#### 方法列表


##### `__init__(type: str, data: Any = None)`

- **type** (`str`): 消息类型 (WSMessage.TEXT / BINARY / CLOSE / ERROR)
- **data** (`Any`): 消息数据

---


### `class WebSocketConnectionBase`

WebSocket 连接共享基类

定义客户端和服务端 WebSocket 连接的统一接口。
send/receive 由子类实现，iter 方法提供基于 receive 的默认实现。

> **提示**
> 1. 通过 .raw 属性可访问底层框架原生对象
> 2. 服务端和客户端共享此基类，接口一致
> 3. 使用 on_disconnect/on_error 注册生命周期回调

**示例**:
```python
>>> # 服务端和客户端共享相同的接口
>>> await ws.send_text("Hello")
>>> async for msg in ws.iter_text():
...     await ws.send_text(f"Echo: {msg}")
```


#### 方法列表


##### `__init__(ws)`

- **ws** (`object`): 底层框架 WebSocket 对象

---


##### `url()`

连接 URL

**返回值** (`object`): URL 对象

---


##### `headers()`

请求头

**返回值** (`object`): Headers 对象

---


##### `raw()`

底层框架原生对象

**返回值** (`object`): 原生 WebSocket 实例

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


##### `async receive_text()`

接收文本消息

**返回值** (`str`): 文本内容
**异常**: `WebSocketDisconnect` - 连接断开时

---


##### `async receive_bytes()`

接收二进制消息

**返回值** (`bytes`): 二进制内容
**异常**: `WebSocketDisconnect` - 连接断开时

---


##### `async receive_json(mode: str = 'text')`

接收 JSON 消息

- **mode** (`str`): 接收模式 ("text" 或 "binary") (默认: "text")
**返回值** (`Any`): 解析后的 JSON 数据
**异常**: `WebSocketDisconnect` - 连接断开时

---


##### `async iter_text()`

迭代文本消息直到断开

**返回值** (`async`): generator 逐条返回文本消息

---


##### `async iter_bytes()`

迭代二进制消息直到断开

**返回值** (`async`): generator 逐条返回二进制消息

---


##### `async iter_json()`

迭代 JSON 消息直到断开

**返回值** (`async`): generator 逐条返回 JSON 数据

---


##### `async close(code: int = 1000, reason: str | None = None)`

关闭 WebSocket 连接

- **code** (`int`): 关闭码 (默认: 1000)
- **reason** (`str`): | None 关闭原因 (可选)

---


##### `on_disconnect(handler: Callable | None = None)`

注册断开连接回调

可作为装饰器或直接调用。

- **handler** (`Callable`): 断开连接时的回调函数，签名: (ws, reason="") -> None

**示例**:
```python
>>> @ws.on_disconnect
... async def handle_disconnect(ws, reason="unknown"):
...     print(f"Disconnected: {reason}")
```

---


##### `on_error(handler: Callable | None = None)`

注册错误回调

- **handler** (`Callable`): 发生错误时的回调函数，签名: (ws, error="") -> None

**示例**:
```python
>>> @ws.on_error
... async def handle_error(ws, error=""):
...     print(f"Error: {error}")
```

---

