# ErisPulse 核心模块使用指南

## 核心模块
| 名称 | 用途 |
|------|------|
| `sdk` | SDK对象 |
| `storage`/`sdk.storage` | 获取/设置数据库配置 |
| `config`/`sdk.config` | 获取/设置模块配置 |
| `mods`/`sdk.mods` | 模块管理器 |
| `adapter`/`sdk.adapter` | 适配器管理/获取实例 |
| `logger`/`sdk.logger` | 日志记录器 |
| `BaseAdapter`/`sdk.BaseAdapter` | 适配器基类 |
| `Event`/`sdk.Event` | 事件处理模块 |

> 注意: `Event` 模块是 ErisPulse 2.2.0 引入的新模块,发布模块时请注意提醒用户兼容性问题
Event 模块包含以下子模块：

| 子模块 | 用途 |
|-------|------|
| `Event.command` | 命令处理 |
| `Event.message` | 消息事件处理 |
| `Event.notice` | 通知事件处理 |
| `Event.request` | 请求事件处理 |
| `Event.meta` | 元事件处理 |
| `Event.event_manager` | 事件管理器 |
| `Event.exceptions` | 事件异常处理 |

```python
# 直接导入方式
from ErisPulse.Core import storage, mods, logger, adapter, BaseAdapter, Event

# 通过SDK对象方式
from ErisPulse import sdk
sdk.storage  # 等同于直接导入的storage
```

## 模块使用
- 所有模块通过`sdk`对象统一管理
- 每个模块拥有独立命名空间，使用`sdk`进行调用
- 可以在模块间使用 `sdk.<module_name>.<func>` 的方式调用其他模块中的方法

## 适配器使用
- 适配器是ErisPulse的核心，负责与平台进行交互

适配器事件分为两类：
- 标准事件：平台转换为的标准事件，其格式为标准的 OneBot12 事件格式 | 需要判断接收到的消息的 `platform` 字段，来确定消息来自哪个平台
- 原生事件：平台原生事件 通过 sdk.adapter.<Adapter>.on() 监听对应平台的原生事件
适配器标准事件的拓展以及支持的消息发送类型，请参考 [PlatformFeatures.md](docs/PlatformFeatures.md)

建议使用标准事件进行事件的处理，适配器会自动将原生事件转换为标准事件

```python
# 启动适配器
await sdk.adapter.startup("MyAdapter")  # 不指定名称则启动所有适配器
# 另外可以传入列表，例如 sdk.adapter.startup(["Telegram", "Yunhu"])

# 监听 OneBot12 标准事件
@adapter.on("message")
async def on_message(data):
    platform = data.get("platform")
    detail_type = "user" if data.get("detail_type") == "private" else "group"
    detail_id = data.get("user_id") if detail_type == "user" else data.get("group_id")
    Sender = None

    if hasattr(adapter, platform):
        Sender = getattr(adapter, platform).To(detail_type, detail_id)
    
    Sender.Text(data.get("alt_message"))

# 监听平台原生事件
@adapter.Telegram.on("message")
async def on_raw_message(data):
    # Do something ...
```
平台原生事件监听并不建议使用，因为格式不保证与 OneBot12 兼容，另外 OneBot12 的标准事件规定了一个拓展字段 `{{platform}}_raw` 用于传输平台原生数据

## 事件处理模块(Event)
Event 模块提供了一套完整的事件处理机制，支持命令处理、消息处理、通知处理、请求处理和元事件处理等功能。

### 命令处理
```python
from ErisPulse.Core.Event import command

# 基本命令
@command("hello", help="发送问候消息")
async def hello_command(event):
    platform = event["platform"]
    user_id = event["user_id"]
    
    # 发送回复消息
    adapter_instance = getattr(sdk.adapter, platform)
    await adapter_instance.Send.To("user", user_id).Text("Hello World!")

async def send_reply(event: Dict[str, Any], message: Union[str, List[Dict]]) -> Any:
    platform = event.get("platform")
    if not platform:
        logger.warning("事件中缺少 'platform' 字段")
    
    adapter_sender = getattr(adapter, platform, None)
    if not adapter_sender:
        logger.warning(f"适配器 {platform} 未注册")
    
    # 判断消息类型（群聊/频道/私聊）
    if event.get("detail_type") == "group":
        target_type = "group"
        target_id = event.get("group_id")
    elif event.get("detail_type") == "channel":
        target_type = "channel"
        target_id = event.get("channel_id") 
    else:
        target_type = "user"
        target_id = event.get("user_id")
    
    # 发送消息
    adapter_sender.Send.To(target_type, target_id).Text(message)

# 带参数的命令
@command("echo", help="回显消息", usage="/echo <内容>")
async def echo_command(event):
    platform = event["platform"]
    user_id = event["user_id"]

    # 处理command时，我们会自动添加 "command" 字段, 所以他不是一个ob12标准字段
    args = event["command"]["args"]
    
    if not args:
        await send_reply(event, "请提供要回显的内容")
        return
    
    message = " ".join(args)
    adapter_instance = getattr(sdk.adapter, platform)
    await adapter_instance.Send.To("user", user_id).Text(message)

# 带别名的命令
@command(["help", "h"], aliases=["帮助"], help="显示帮助信息")
async def help_command(event):
    platform = event["platform"]
    user_id = event["user_id"]
    help_text = command.help()
    
    adapter_instance = getattr(sdk.adapter, platform)
    await adapter_instance.Send.To("user", user_id).Text(help_text)

# 命令组
@command("admin.reload", group="admin", help="重新加载模块")
async def reload_command(event):
    # 管理员命令逻辑
    pass
```

### 消息处理
```python
from ErisPulse.Core.Event import message

# 处理所有消息
@message.on_message()
async def handle_message(event):
    sdk.logger.info(f"收到消息: {event['alt_message']}")

# 处理私聊消息
@message.on_private_message()
async def handle_private_message(event):
    user_id = event["user_id"]
    sdk.logger.info(f"收到私聊消息，来自用户: {user_id}")

# 处理群聊消息
@message.on_group_message()
async def handle_group_message(event):
    group_id = event["group_id"]
    user_id = event["user_id"]
    sdk.logger.info(f"收到群消息，群: {group_id}，用户: {user_id}")

# 处理@消息
@message.on_at_message()
async def handle_at_message(event):
    user_id = event["user_id"]
    sdk.logger.info(f"收到@消息，来自用户: {user_id}")
```

### 通知处理
```python
from ErisPulse.Core.Event import notice

# 处理好友添加通知
@notice.on_friend_add()
async def handle_friend_add(event):
    user_id = event["user_id"]
    sdk.logger.info(f"新好友添加: {user_id}")
    
    # 发送欢迎消息
    platform = event["platform"]
    adapter_instance = getattr(sdk.adapter, platform)
    await adapter_instance.Send.To("user", user_id).Text("欢迎添加我为好友！")

# 处理群成员增加通知
@notice.on_group_increase()
async def handle_group_increase(event):
    group_id = event["group_id"]
    user_id = event["user_id"]
    sdk.logger.info(f"新成员加入群: {group_id}，用户: {user_id}")

# 处理好友删除通知
@notice.on_friend_remove()
async def handle_friend_remove(event):
    user_id = event["user_id"]
    sdk.logger.info(f"好友删除: {user_id}")

# 处理群成员减少通知
@notice.on_group_decrease()
async def handle_group_decrease(event):
    group_id = event["group_id"]
    user_id = event["user_id"]
    sdk.logger.info(f"群成员减少，群: {group_id}，用户: {user_id}")
```

### 请求处理
```python
from ErisPulse.Core.Event import request

# 处理好友请求
@request.on_friend_request()
async def handle_friend_request(event):
    user_id = event["user_id"]
    sdk.logger.info(f"收到好友请求，来自用户: {user_id}")

# 处理群邀请请求
@request.on_group_request()
async def handle_group_request(event):
    group_id = event["group_id"]
    user_id = event["user_id"]
    sdk.logger.info(f"收到群邀请请求，群: {group_id}，用户: {user_id}")
```

### 元事件处理
```python
from ErisPulse.Core.Event import meta

# 处理连接事件
@meta.on_connect()
async def handle_connect(event):
    platform = event["platform"]
    sdk.logger.info(f"平台 {platform} 连接成功")

# 处理断开连接事件
@meta.on_disconnect()
async def handle_disconnect(event):
    platform = event["platform"]
    sdk.logger.info(f"平台 {platform} 断开连接")

# 处理心跳事件
@meta.on_heartbeat()
async def handle_heartbeat(event):
    platform = event["platform"]
    sdk.logger.debug(f"平台 {platform} 心跳")
```

### 高级功能

#### 优先级控制
```python
# 设置处理器优先级
@message.on_message(priority=10)
async def high_priority_handler(event):
    # 高优先级处理器先执行
    pass

@message.on_message(priority=20)
async def low_priority_handler(event):
    # 低优先级处理器后执行
    pass
```

#### 条件处理器
```python
# 定义条件函数
def keyword_condition(event):
    message_segments = event.get("message", [])
    for segment in message_segments:
        if segment.get("type") == "text":
            text = segment.get("data", {}).get("text", "")
            return "关键词" in text
    return False

# 注册条件处理器
@message.on_message(condition=keyword_condition)
async def keyword_handler(event):
    # 只有消息包含"关键词"时才会执行
    pass
```

#### 中间件
```python
from ErisPulse.Core.Event import command, message, notice, request

# 命令触发中间件
@command.handler.middleware
async def command_middleware(event):
    sdk.logger.info(f"处理命令: {event.get('alt_message')}")
    return event

# 消息触发中间件
@message.handler.middleware
async def message_middleware(event):
    sdk.logger.info(f"处理消息: {event.get('alt_message')}")
    return event

# 其他中间件同理
# ...

```

## 核心模块功能详解

### 1. 日志模块(logger)
```python
logger.set_module_level("MyModule", "DEBUG")  # 设置模块日志级别
logger.save_logs("log.txt")  # 保存日志到文件

# 日志级别
logger.debug("调试信息")
logger.info("运行状态")
logger.warning("警告信息")
logger.error("错误信息")
logger.critical("致命错误")  # 会触发程序崩溃

# 子模块日志记录
# 使用 get_child 方法创建子模块日志记录器，便于更好地组织和识别日志来源
network_logger = logger.get_child("Network")
network_logger.info("网络模块初始化完成")

# 支持多级子模块
http_logger = network_logger.get_child("HTTP")
http_logger.debug("发送HTTP请求")

# 子模块日志记录器使用与主日志记录器相同的配置和功能
# 所有配置操作仍然通过主 logger 对象进行
logger.set_module_level("MyModule", "INFO")  # 影响所有相关子模块
logger.set_output_file("app.log")  # 所有日志都会输出到指定文件
```

### 2. 持久化数据存储(storage)
```python
# 数据库配置操作
storage.set("key", "value")  # 设置配置项
value = storage.get("key", "default")  # 获取配置项
storage.delete("key")  # 删除配置项

# 事务操作
with storage.transaction():
    storage.set('important_key', 'value')
    storage.delete('temp_key')  # 异常时自动回滚

# 批量操作
storage.set_multi({
    "key1": "value1",
    "key2": "value2"
})
storage.delete_multi(["key1", "key2"])
```

### 3. 配置模块(config)
```python
# 模块配置操作（读写config.toml）
module_config = config.getConfig("MyModule")  # 获取模块配置
if module_config is None:
    config.setConfig("MyModule", {"MyKey": "MyValue"})  # 设置默认配置

# 嵌套配置访问
nested_value = config.getConfig("MyModule.subkey.value", "default")
config.setConfig("MyModule.subkey.value", "new_value")
```

### 4. 异常处理模块(exceptions)
```python
# ErisPulse提供了统一的异常处理机制，可以自动捕获和格式化异常信息
# 对于异步代码，可以为特定事件循环设置异常处理器

import asyncio
from ErisPulse.Core import exceptions

# 为当前运行的事件循环设置异常处理器
loop = asyncio.get_running_loop()
exceptions.setup_async_loop(loop)

# 或者不传参数，自动获取当前事件循环 || 但不建议这么做，因为运行主程序时可能使用了其他的异步库
exceptions.setup_async_loop()

# 这样设置后，异步代码中的未捕获异常会被统一处理并格式化输出
```

### 5. 模块管理器(mods)
```python
# 模块状态管理
mods.set_module_status("MyModule", True)  # 启用模块
mods.set_module_status("MyModule", False)  # 禁用模块
is_enabled = mods.get_module_status("MyModule")  # 获取模块状态

# 模块信息管理
mods.set_module("MyModule", {
    "version": "1.0.0",
    "description": "我的模块"
})
module_info = mods.get_module("MyModule")

# 批量操作
mods.set_all_modules({
    "Module1": {"version": "1.0", "status": True},
    "Module2": {"version": "2.0", "status": False}
})
all_modules = mods.get_all_modules()    # 获取所有模块信息
```

## 配置管理

### 1. 命令前缀配置
```toml
[ErisPulse]
[ErisPulse.event]
[ErisPulse.event.command]
prefix = "/"
case_sensitive = true

[ErisPulse.event.message]
ignore_self = true
```

### 2. 框架配置
```toml
[ErisPulse]
[ErisPulse.server]
host = "0.0.0.0"
port = 8000
ssl_certfile = ""
ssl_keyfile = ""

[ErisPulse.logger]
level = "INFO"
log_files = []
memory_limit = 1000
```

更多详细信息请参考[API文档](docs/api/)
