# 适配器系统 API

本文档详细介绍了 ErisPulse 适配器系统的 API。

## Adapter 管理器

### 获取适配器

```python
from ErisPulse import sdk

# 通过名称获取适配器
adapter = sdk.adapter.get("platform_name")

# 通过属性访问
adapter = sdk.adapter.platform_name
```

### 适配器事件监听

```python
# 监听 OneBot12 标准事件
@sdk.adapter.on("message")
async def handle_message(event):
    pass

# 监听特定平台的标准事件
@sdk.adapter.on("message", platform="yunhu")
async def handle_yunhu_message(event):
    pass

# 监听平台原生事件
@sdk.adapter.on("raw_event", raw=True, platform="yunhu")
async def handle_raw_event(data):
    pass
```

### 适配器管理

```python
# 获取所有平台
platforms = sdk.adapter.platforms

# 检查适配器是否存在
exists = sdk.adapter.exists("platform_name")

# 启用/禁用适配器
sdk.adapter.enable("platform_name")
sdk.adapter.disable("platform_name")

# 启动/关闭适配器
await sdk.adapter.startup(["platform1", "platform2"])
await sdk.adapter.shutdown()
```

## 中间件

### 注册中间件

```python
# 添加中间件
@sdk.adapter.middleware
async def my_middleware(event):
    # 处理事件
    sdk.logger.info(f"中间件处理: {event}")
    return event
```

### 中间件执行顺序

中间件按照注册顺序执行，在事件分发到处理器之前执行。

## Send 消息发送

### 基本发送

```python
# 获取适配器
adapter = sdk.adapter.get("platform")

# 发送文本消息
await adapter.Send.To("user", "123").Text("Hello")

# 发送图片消息
await adapter.Send.To("group", "456").Image("https://example.com/image.jpg")
```

### 指定发送账号

```python
# 使用账户名
await adapter.Send.Using("account1").To("user", "123").Text("Hello")

# 使用账户 ID
await adapter.Send.Using("bot_id").To("user", "123").Text("Hello")
```

### 查询支持的发送方法
> 由于新的标准规范要求使用重写 `__getattr__` 方法来实现兜底发送机制，导致无法使用 `hasattr` 方法来检查方法是否存在，故从 `2.3.5-dev.3` 开始，新增 `list_sends` 方法来查询支持的所有发送方法。

```python
# 列出平台支持的所有发送方法
methods = sdk.adapter.list_sends("onebot11")
# 返回: ["Text", "Image", "Voice", "Markdown", ...]

# 获取某个方法的详细信息
info = sdk.adapter.send_info("onebot11", "Text")
# 返回:
# {
#     "name": "Text",
#     "parameters": [
#         {"name": "text", "type": "str", "default": null, "annotation": "str"}
#     ],
#     "return_type": "Awaitable[Any]",
#     "docstring": "发送文本消息..."
# }
```

### 链式修饰

```python
# @用户
await adapter.Send.To("group", "456").At("789").Text("你好")

# @全体成员
await adapter.Send.To("group", "456").AtAll().Text("大家好")

# 回复消息
await adapter.Send.To("group", "456").Reply("msg_id").Text("回复内容")

# 组合使用
await adapter.Send.To("group", "456").At("789").Reply("msg_id").Text("回复@的消息")
```

## API 调用

### call_api 方法
> 注意，各个平台的 API 调用方式可能不同，请参考对于平台适配器文档
> 并不推荐直接使用 call_api 方法，建议使用 Send 类进行消息发送

```python
# 调用平台 API
result = await adapter.call_api(
    endpoint="/send",
    content="Hello",
    recvId="123",
    recvType="user"
)

# 标准化响应
{
    "status": "ok",
    "retcode": 0,
    "data": {...},
    "message_id": "msg_id",
    "message": "",
    "{platform}_raw": raw_response
}
```

## 适配器基类

### BaseAdapter 方法

```python
from ErisPulse.Core import BaseAdapter

class MyAdapter(BaseAdapter):
    def __init__(self, sdk):
        # 初始化适配器
        pass
    
    async def start(self):
        """启动适配器（必须实现）"""
        pass
    
    async def shutdown(self):
        """关闭适配器（必须实现）"""
        pass
    
    async def call_api(self, endpoint: str, **params):
        """调用平台 API（必须实现）"""
        pass
```

### Send 嵌套类

```python
class MyAdapter(BaseAdapter):
    class Send(BaseAdapter.Send):
        def Text(self, text: str):
            """发送文本消息"""
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

## Bot 状态管理

适配器通过发送 OneBot12 标准的 **`meta` 事件**来告知框架 Bot 的连接状态。系统自动从中提取 Bot 信息进行状态追踪。

### meta 事件类型

适配器应发送以下三种 `meta` 事件：

| `type` | `detail_type` | 说明 | 触发时机 |
|--------|--------------|------|---------|
| `meta` | `connect` | Bot 连接上线 | 适配器与平台建立连接成功后 |
| `meta` | `heartbeat` | Bot 心跳 | 定期发送（建议 30-60 秒） |
| `meta` | `disconnect` | Bot 断开连接 | 检测到连接断开时 |

### self 字段扩展

ErisPulse 在 OneBot12 标准的 `self` 字段上扩展了以下可选字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `self.platform` | string | 平台名称（OB12 标准） |
| `self.user_id` | string | Bot 用户 ID（OB12 标准） |
| `self.user_name` | string | Bot 昵称（ErisPulse 扩展） |
| `self.avatar` | string | Bot 头像 URL（ErisPulse 扩展） |
| `self.account_id` | string | 多账户标识（ErisPulse 扩展） |

### meta 事件格式

#### connect — 连接上线

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

系统处理：注册 Bot，标记为 `online`，触发 `adapter.bot.online` 生命周期事件。

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

系统处理：更新 `last_active` 时间（心跳中也支持更新元信息）。

#### disconnect — 断开连接

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

系统处理：标记 Bot 为 `offline`，触发 `adapter.bot.offline` 生命周期事件。

### 普通事件的自动发现

除了 `meta` 事件外，普通事件（`message`/`notice`/`request`）中的 `self` 字段也会自动发现并注册 Bot、更新活跃时间。这意味着即使适配器不发送 `connect` 事件，框架也能从第一条普通事件中发现 Bot。

### 适配器接入示例

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        # 与平台建立连接...
        connection = await self._connect()
        
        # 连接成功，发送 connect 事件
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
        # 断开连接，发送 disconnect 事件
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

### 查询 Bot 状态

```python
# 获取所有适配器与 Bot 的完整状态（WebUI 友好）
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

# 获取单个 Bot 详情
info = sdk.adapter.get_bot_info("telegram", "123456")

# 检查 Bot 是否在线
if sdk.adapter.is_bot_online("telegram", "123456"):
    print("Bot 在线")
```

### Bot 状态值

| 状态 | 说明 |
|------|------|
| `online` | 在线（持续收到事件或适配器主动标记） |
| `offline` | 离线（适配器主动标记或系统关闭时自动设置） |
| `unknown` | 未知（仅注册但未确认状态） |

### 生命周期事件

| 事件名 | 触发时机 | 数据 |
|--------|---------|------|
| `adapter.bot.online` | 首次自动发现新 Bot | `{platform, bot_id, status}` |

```python
# 监听 Bot 上线事件
@sdk.lifecycle.on("adapter.bot.online")
def on_bot_online(event):
    print(f"Bot 上线: {event['data']['platform']}/{event['data']['bot_id']}")
```

> 系统关闭时（`shutdown`），所有 Bot 会自动被标记为 `offline`。

## 相关文档

- [核心模块 API](core-modules.md) - 核心模块 API
- [事件系统 API](event-system.md) - Event 模块 API
- [适配器开发指南](../developer-guide/adapters/) - 开发平台适配器
