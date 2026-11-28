# 适配器系统 API

> [!TIP]
> **什么时候需要读这篇**：当你需要管理适配器（获取实例、启停、查 Bot 在线状态）、用 Send DSL 发消息、注册中间件，或为适配器接入 Bot 状态上报（meta 事件）时查阅本文。不需要则跳过。

本文档详细介绍了 ErisPulse 适配器系统的 API。

## Adapter 管理器

### 获取适配器

```python
from ErisPulse import sdk

# 通过名称获取适配器
adapter = sdk.adapter.get("platform_name")

# 或者也可以直接通过属性访问
adapter = sdk.adapter.platform_name
```

### 使用适配器事件监听
> 一般情况下，更建议使用`Event`模块进行事件的监听/处理;
>
> 同时`Event`模块提供了强大的包装器，可以为您的模块开发带来更多便利

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
# 以下方法都只展示了传入参数的情况，无参数时代表启动/停止全部已注册适配器
await sdk.adapter.startup(["platform1", "platform2"])
await sdk.adapter.shutdown(["platform1", "platform2"])

# 检查适配器是否正在运行
is_running = sdk.adapter.is_running("platform_name")

# 列出所有正在运行的适配器
running = sdk.adapter.list_running()

# 读取适配器元信息（对齐 module.get_meta，供面板 / 商店等消费）
info = sdk.adapter.get_info("platform_name")   # 注册信息（meta + 类名，json-safe）
meta = sdk.adapter.get_meta("platform_name")   # 介绍元信息（description 支持 i18n 解析）
raw = sdk.adapter.get_meta("platform_name", resolve_i18n=False)  # 透传原始 i18n 字典
```

## 中间件

中间件在事件分发到处理器之前执行，可以对事件数据进行修改、过滤或记录。

### 注册中间件

```python
@sdk.adapter.middleware
async def my_middleware(event):
    sdk.logger.info(f"中间件处理: {event}")
    return event
```

### 中间件执行模型

- **执行顺序**：中间件按注册顺序执行（先注册先执行）
- **数据传递**：每个中间件接收上一个中间件返回的 `event` 数据；如果某个中间件返回 `None`，则忽略该返回值并保留原数据继续传递（同时输出 `warning` 级别日志）
- **修改数据**：中间件可以修改事件数据并返回修改后的字典
- **事件否决**：中间件显式返回 `False` 时否决事件——事件被丢弃，不进入任何处理器、无任何出站副作用；否决时输出 TRACE 日志并触发 `adapter.event.blocked` 生命周期钩子（携带中间件名与完整事件）

```python
@sdk.adapter.middleware
async def add_timestamp(event):
    event["processed_at"] = time.time()
    return event

@sdk.adapter.middleware
async def filter_spam(event):
    if event.get("detail_type") == "private":
        text = event.get("alt_message", "")
        if "垃圾广告" in text:
            return False  # 否决：事件被丢弃，不进入任何处理器
    return event
```

> **注意**：只有显式返回 `False` 才否决事件（返回空字典 / `0` / `""` 等 falsy 值不否决）；
> 返回 `None` 仍然是放行且载荷不变。否决后的事件可通过监听
> `adapter.event.blocked` 钩子进行审计与排查"事件为什么没响应"。

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

> **注意**：`call_api` 是直接调用平台原生 API 的底层方法，各平台的参数和返回值可能不同，请参考对应平台适配器文档。**推荐使用 Send DSL 发送消息**，仅在 Send DSL 不支持的场景（如获取平台特有的数据、调用平台管理接口等）中使用 `call_api`。

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
from ErisPulse import sdk
from ErisPulse.Core import BaseAdapter

class MyAdapter(BaseAdapter):
    def __init__(self):
        super().__init__()
        self.sdk = sdk
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

### meta 事件上报

适配器通过 `meta` 事件上报 Bot 状态，三种 `detail_type`：`connect`（注册上线）、`heartbeat`（心跳保活）、`disconnect`（标记离线）。推荐用 `emit_meta()` 一行发送；即使不发 meta 事件，框架也会从普通事件（message/notice/request）的 `self` 字段自动发现 Bot。

- **meta 事件格式与发送方式**（何时发送、`emit_meta()` 用法、手动构造格式）见 [适配器最佳实践 - Bot 状态管理与 Meta 事件](../developer-guide/adapters/best-practices.md#bot-状态管理与-meta-事件)
- **自动发现机制与框架行为**见 [适配器核心概念 - Bot 状态管理](../developer-guide/adapters/core-concepts.md#bot-状态管理)

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
| `adapter.status.change` | 适配器状态变化 | `{platform, status}`，status 完整取值：`starting` / `started` / `start_failed` / `stopping` / `stopped` / `stop_failed` / `skipped-dependency`（所依赖的适配器未就绪而跳过启动）/ `disabled`（配置禁用） |

```python
# 监听 Bot 上线事件
@sdk.lifecycle.on("adapter.bot.online")
def on_bot_online(event):
    print(f"Bot 上线: {event['data']['platform']}/{event['data']['bot_id']}")

# 监听适配器状态变化
@sdk.lifecycle.on("adapter.status.change")
def on_status_change(event):
    print(f"适配器状态: {event['data']['platform']} -> {event['data']['status']}")
```

> 系统关闭时（`shutdown`），所有 Bot 会自动被标记为 `offline`。

## 相关文档

**继续查 API**：
- [核心模块 API](core-modules.md) - 核心模块 API
- [事件系统 API](event-system.md) - Event 模块 API

**动手写适配器**：
- [适配器开发指南](../developer-guide/adapters/) - 开发平台适配器
- [适配器标准化指南（总纲）](../standards/standardization-guide.md) - 实现新适配器前的标准对照与 Checklist
