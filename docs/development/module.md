# ErisPulse 模块开发指南

## 1. 模块结构
一个标准的模块包结构应该是：

```
MyModule/
├── pyproject.toml    # 项目配置
├── README.md         # 项目说明
├── LICENSE           # 许可证文件
└── MyModule/
    ├── __init__.py  # 模块入口
    └── Core.py      # 核心逻辑(只是推荐结构使用Core.py | 只要模块入口使用正确，你可以使用任何你喜欢的文件名)
```

## 2. `pyproject.toml` 文件
模块的配置文件, 包括模块信息、依赖项、模块/适配器入口点等信息

```toml
[project]
name = "ErisPulse-MyModule"     # 模块名称, 建议使用 ErisPulse-<模块名称> 的格式命名
version = "1.0.0"
description = "一个非常哇塞的模块"
readme = "README.md"
requires-python = ">=3.9"
license = { file = "LICENSE" }
authors = [ { name = "yourname", email = "your@mail.com" } ]
dependencies = [
    
]

# 模块主页, 用于在模块管理器中显示模块信息 | 尽量使用仓库地址，以便模块商店显示文档时指定为仓库的 README.md 文件
[project.urls]
"homepage" = "https://github.com/yourname/MyModule"

# 模块入口点，用于指定模块的入口类 当然也可以在一个包中定义多个模块，但并不建议这样做
[project.entry-points]
"erispulse.module" = { "MyModule" = "MyModule:Main" }

```

## 3. `MyModule/__init__.py` 文件

顾名思义,这只是使你的模块变成一个Python包, 你可以在这里导入模块核心逻辑, 当然也可以让他保持空白

示例这里导入了模块核心逻辑

```python
from .Core import Main
```

---

## 4. `MyModule/Core.py` 文件

实现模块主类 `Main`，必须继承 `BaseModule` 基类以获得标准化的生命周期管理功能。

```python
from ErisPulse import sdk
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.Core.Event import command

class Main(BaseModule):
    def __init__(self):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("MyModule")
        self.storage = sdk.storage
        
        self.config = self._get_config()

    @staticmethod
    def should_eager_load():
        # 这适用于懒加载模块, 如果模块需要立即加载, 请返回 True | 比如一些监听器模块/定时器模块等等
        return False
    
    async def on_load(self, event):
        command("一个命令", help="这是一个命令", usage="命令 参数")(self.ACommand)
        self.logger.info("模块已加载")
        
    async def on_unload(self, event):
        command.unregister(self.ACommand)
        self.logger.info("模块已卸载")

    # 从 config.toml 中获取配置, 如果不存在则使用默认值
    def _get_config(self):
        config = self.sdk.config.getConfig("MyModule")
        if not config:
            default_config = {
                "my_config_key": "default_value"
            }
            self.sdk.config.setConfig("MyModule", default_config)
            self.logger.warning("未找到模块配置, 对应模块配置已经创建到config.toml中")
            return default_config
        return config

    async def ACommand(self):
        self.logger.info("命令已执行")

    def print_hello(self):
        self.logger.info("Hello World!")
```

- 所有 SDK 提供的功能都可通过 `sdk` 对象访问。
```python
# 这时候在其它地方可以访问到该模块
from ErisPulse import sdk
sdk.MyModule.print_hello()

# 运行模块主程序（推荐使用CLI命令）
# epsdk run main.py --reload
```

### BaseModule 基类
方法说明
| 方法名 | 说明 | 必须实现 | 参数 | 返回值 |
| --- | --- | --- | --- | --- |
| should_eager_load() | 静态方法，决定模块是否应该立即加载而不是懒加载 | 否 | 无 | bool |
| on_load(event) | 模块加载时调用，用于初始化资源、注册事件处理器等 | 是 | event | bool |
| on_unload(event) | 模块卸载时调用，用于清理资源、注销事件处理器等 | 是 | event | bool |

## 5. Event 事件包装类

ErisPulse 提供了一个功能强大的 Event 包装类，它继承自 `dict`，在保持完全向后兼容的同时，提供了大量便捷的方法来简化事件处理。

### 5.1 核心特性

- **完全兼容字典**：Event 继承自 dict，所有原有的字典访问方式都完全可用
- **便捷方法**：提供大量便捷方法来简化事件处理
- **点式访问**：支持使用点号访问事件字段，如 `event.platform`
- **向后兼容**：所有方法都是可选的，不影响原有的字典访问方式

### 5.2 核心字段方法

```python
from ErisPulse.Core.Event import command

@command("test")
async def test_command(event):
    # 获取核心事件信息
    event_id = event.get_id()              # 事件ID
    event_time = event.get_time()          # 时间戳
    event_type = event.get_type()          # 事件类型 (message/notice/request/meta)
    detail_type = event.get_detail_type()  # 详细类型 (private/group/friend等)
    platform = event.get_platform()        # 平台名称
    
    # 获取机器人信息
    self_platform = event.get_self_platform()    # 机器人平台
    self_user_id = event.get_self_user_id()      # 机器人ID
    self_info = event.get_self_info()            # 机器人完整信息
```

### 5.3 消息事件方法

```python
from ErisPulse.Core.Event import message

@message.on_private_message()
async def private_handler(event):
    # 获取消息内容
    message_segments = event.get_message()    # 消息段数组
    alt_message = event.get_alt_message()      # 消息备用文本
    text = event.get_text()                    # 纯文本内容
    
    # 获取发送者信息
    user_id = event.get_user_id()              # 发送者ID
    nickname = event.get_user_nickname()       # 发送者昵称
    sender_info = event.get_sender()           # 发送者完整信息字典
    
    # 群组信息
    group_id = event.get_group_id()            # 群组ID（仅群聊消息）
```

### 5.4 消息类型判断

```python
from ErisPulse.Core.Event import message

@message.on_group_message()
async def group_handler(event):
    # 判断消息类型
    is_msg = event.is_message()           # 是否为消息事件
    is_private = event.is_private_message()  # 是否为私聊消息
    is_group = event.is_group_message()  # 是否为群聊消息
    
    # @消息相关
    is_at = event.is_at_message()         # 是否为@消息
    has_mention = event.has_mention()     # 是否包含@消息
    mentions = event.get_mentions()       # 获取所有被@的用户ID列表
```

### 5.5 回复功能

Event 提供了统一的 `reply()` 方法，支持多种回复类型：

```python
from ErisPulse.Core.Event import command

@command("reply_test")
async def reply_test(event):
    # 基本文本回复（默认）
    await event.reply("这是一条文本消息")
    
    # 发送图片
    await event.reply("http://example.com/image.jpg", method="Image")
    
    # 发送语音
    await event.reply("http://example.com/voice.mp3", method="Voice")
    
    # 发送视频
    await event.reply("http://example.com/video.mp4", method="Video")
    
    # 发送文件
    await event.reply("http://example.com/file.pdf", method="File")
```

**reply() 方法参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| content | str | 发送内容（文本、URL等，取决于method参数） |
| method | str | 适配器发送方法，默认为 "Text"。可选值：Text, Image, Voice, Video, File 等 |
| **kwargs | dict | 额外参数，具体取决于适配器实现 |

### 5.6 等待回复功能

Event 提供了 `wait_reply()` 方法，可以方便地等待用户回复：

```python
from ErisPulse.Core.Event import command

@command("interactive")
async def interactive_command(event):
    # 发送提示消息
    await event.reply("请输入你的名字:")
    
    # 等待用户回复，超时时间为30秒
    reply = await event.wait_reply(timeout=30)
    
    if reply:
        name = reply.get_text()
        await event.reply(f"你好，{name}！")
    else:
        await event.reply("等待超时，请重试。")

# 带验证函数的例子
@command("age_check")
async def age_check(event):
    def is_valid_age(event_data):
        """验证函数：检查输入是否为有效年龄"""
        text = event_data.get("alt_message", "")
        try:
            age = int(text)
            return 0 <= age <= 150
        except ValueError:
            return False
    
    await event.reply("请输入你的年龄（0-150）:")
    
    # 等待回复并验证
    reply = await event.wait_reply(
        timeout=60,
        validator=is_valid_age
    )
    
    if reply:
        age = int(reply.get_text())
        await event.reply(f"你的年龄是 {age} 岁")
    else:
        await event.reply("输入无效或超时")
```

**wait_reply() 方法参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| prompt | str | 提示消息，如果提供会发送给用户 |
| timeout | float | 等待超时时间（秒），默认60秒 |
| callback | Callable | 回调函数，当收到回复时执行 |
| validator | Callable | 验证函数，用于验证回复是否有效 |

### 5.7 通知事件方法

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    # 通知事件信息
    operator_id = event.get_operator_id()         # 操作者ID
    operator_nickname = event.get_operator_nickname()  # 操作者昵称
    
    # 发送欢迎消息
    await event.reply("欢迎添加我为好友！")

# 群成员事件
@notice.on_group_member_increase()
async def member_increase(event):
    # 群成员增加
    pass

@notice.on_group_member_decrease()
async def member_decrease(event):
    # 群成员减少
    pass

# 好友删除
@notice.on_friend_delete()
async def friend_delete(event):
    # 好友删除
    pass
```

### 5.8 请求事件方法

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def friend_request(event):
    # 获取请求信息
    user_id = event.get_user_id()              # 请求用户ID
    comment = event.get_comment()              # 请求附言
    
    # 可以在这里自动同意或拒绝请求
    await event.reply("已收到你的好友请求")

@request.on_group_request()
async def group_request(event):
    # 群组请求
    group_id = event.get_group_id()
    comment = event.get_comment()
    pass
```

### 5.9 命令信息方法

```python
from ErisPulse.Core.Event import command

@command("cmd_with_args")
async def cmd_with_args(event):
    # 获取命令信息
    cmd_name = event.get_command_name()        # 命令名称
    cmd_args = event.get_command_args()        # 命令参数列表
    cmd_raw = event.get_command_raw()          # 命令原始文本
    cmd_info = event.get_command_info()        # 完整命令信息字典
    
    # 判断是否为命令
    if event.is_command():
        await event.reply(f"执行命令: {cmd_name}")
```

### 5.10 原始数据访问

```python
from ErisPulse.Core.Event import message

@message.on_private_message()
async def raw_data_handler(event):
    # 获取原始事件数据（平台特定的原始数据）
    raw_data = event.get_raw()                 # 原始事件数据
    raw_type = event.get_raw_type()            # 原始事件类型
    
    # 处理原始数据
    if raw_type == "original_event_type":
        pass
```

### 5.11 工具方法

```python
from ErisPulse.Core.Event import command

@command("test_utils")
async def test_utils(event):
    # 转换为字典
    event_dict = event.to_dict()
    
    # 检查是否已处理
    if not event.is_processed():
        # 标记为已处理
        event.mark_processed()
        
    # 点式访问和字典访问都支持
    platform = event.platform                  # 点式访问
    user_id = event["user_id"]                 # 字典访问
    
    await event.reply(f"来自 {platform} 的消息")
```

### 5.12 完整示例

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.Core.Event import command, message, notice

class Main(BaseModule):
    def __init__(self, sdk):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("MyModule")
        self.config = self._load_config()
    
    async def on_load(self, event):
        # 注册命令处理器
        @command("hello", help="发送问候")
        async def hello_command(event):
            # 使用便捷方法
            sender = event.get_sender()
            await event.reply(f"你好，{sender['nickname']}！")
        
        # 注册交互式命令
        @command("greet", help="交互式问候")
        async def greet_command(event):
            await event.reply("请告诉我你的名字:")
            
            reply = await event.wait_reply(timeout=30)
            if reply:
                name = reply.get_text()
                await event.reply(f"很高兴认识你，{name}！")
        
        # 注册消息处理器
        @message.on_group_message()
        async def group_handler(event):
            # 检查@消息
            if event.is_at_message():
                user_id = event.get_user_id()
                # 可以根据需要实现@回复功能，具体取决于适配器支持
        
        # 注册通知处理器
        @notice.on_friend_add()
        async def friend_add_handler(event):
            welcome_msg = self.config.get("welcome_message", "欢迎！")
            await event.reply(welcome_msg)
```

### 5.13 Event 方法速查表

#### 核心方法
- `get_id()` - 获取事件ID
- `get_time()` - 获取时间戳
- `get_type()` - 获取事件类型
- `get_detail_type()` - 获取详细类型
- `get_platform()` - 获取平台名称

#### 机器人信息
- `get_self_platform()` - 获取机器人平台
- `get_self_user_id()` - 获取机器人用户ID
- `get_self_info()` - 获取机器人完整信息

#### 消息方法
- `get_message()` - 获取消息段数组
- `get_text()` - 获取纯文本内容
- `get_user_id()` - 获取发送者ID
- `get_user_nickname()` - 获取发送者昵称
- `get_group_id()` - 获取群组ID
- `get_sender()` - 获取发送者信息字典

#### 类型判断
- `is_message()` - 是否为消息事件
- `is_private_message()` - 是否为私聊消息
- `is_group_message()` - 是否为群聊消息
- `is_at_message()` - 是否为@消息
- `has_mention()` - 是否包含@消息
- `get_mentions()` - 获取被@的用户ID列表

#### 回复功能
- `reply(content, method="Text", **kwargs)` - 通用回复方法

#### 等待回复
- `wait_reply(prompt=None, timeout=60.0, callback=None, validator=None)` - 等待用户回复

#### 命令信息
- `get_command_name()` - 获取命令名称
- `get_command_args()` - 获取命令参数
- `get_command_raw()` - 获取命令原始文本
- `is_command()` - 是否为命令

#### 工具方法
- `to_dict()` - 转换为字典
- `is_processed()` - 是否已处理
- `mark_processed()` - 标记为已处理

## 6. 模块路由注册

从 ErisPulse 2.1.15 版本开始，模块也可以注册自己的 HTTP/WebSocket 路由，用于提供 Web API 或实时通信功能。

### 6.1 HTTP 路由注册

模块可以注册 HTTP 路由来提供 REST API 接口：

```python
from ErisPulse import sdk
from fastapi import Request

class Main(BaseModule):
    def __init__(self):
        super().__init__()
        self.sdk = sdk
        self.logger = sdk.logger.get_child("MyModule")
        self.storage = sdk.storage
        
        # 注册模块路由
        self._register_routes()
        
    def _register_routes(self):
        """注册模块路由"""
        
        # 注册 HTTP GET 路由
        async def get_info():
            return {
                "module": "MyModule", 
                "version": "1.0.0",
                "status": "running"
            }
        
        # 注册 HTTP POST 路由
        async def process_data(request: Request):
            data = await request.json()
            # 处理数据逻辑
            return {"result": "success", "received": data}
        
        # 使用 router 注册路由
        self.sdk.router.register_http_route(
            module_name="MyModule",
            path="/info",
            handler=get_info,
            methods=["GET"]
        )
        
        self.sdk.router.register_http_route(
            module_name="MyModule", 
            path="/process",
            handler=process_data,
            methods=["POST"]
        )
        
        self.logger.info("模块路由注册完成")
```

### 6.2 WebSocket 路由注册

模块也可以注册 WebSocket 路由来实现实时通信功能：

```python
from ErisPulse import sdk
from fastapi import WebSocket, WebSocketDisconnect

class Main(BaseModule):
    def __init__(self):
        super().__init__()
        self.sdk = sdk
        self.logger = sdk.logger.get_child("MyModule")
        self.storage = sdk.storage
        self._connections = set()
        
        # 注册 WebSocket 路由
        self._register_websocket_routes()
        
    def _register_websocket_routes(self):
        """注册 WebSocket 路由"""
        
        async def websocket_handler(websocket: WebSocket):
            """WebSocket 连接处理器"""
            await websocket.accept()
            self._connections.add(websocket)
            self.logger.info(f"新的 WebSocket 连接: {websocket.client}")
            
            try:
                while True:
                    data = await websocket.receive_text()
                    # 处理接收到的消息
                    response = f"收到消息: {data}"
                    await websocket.send_text(response)
                    
                    # 广播给所有连接
                    await self._broadcast(f"广播: {data}")
                    
            except WebSocketDisconnect:
                self.logger.info(f"WebSocket 连接断开: {websocket.client}")
            finally:
                self._connections.discard(websocket)
        
        async def auth_handler(websocket: WebSocket) -> bool:
            """WebSocket 认证处理器（可选）"""
            # 实现认证逻辑
            token = websocket.headers.get("authorization")
            return token == "Bearer valid-token"  # 简单示例
        
        # 注册 WebSocket 路由
        self.sdk.router.register_websocket(
            module_name="MyModule",
            path="/ws",
            handler=websocket_handler,
            auth_handler=auth_handler  # 可选
        )
        
        self.logger.info("WebSocket 路由注册完成")
    
    async def _broadcast(self, message: str):
        """向所有连接广播消息"""
        disconnected = set()
        for connection in self._connections:
            try:
                await connection.send_text(message)
            except:
                disconnected.add(connection)
        
        # 移除断开的连接
        for conn in disconnected:
            self._connections.discard(conn)
```

### 6.3 路由使用说明

注册的路由将自动添加模块名称作为前缀：

- HTTP 路由 `/info` 将可通过 `/MyModule/info` 访问
- WebSocket 路由 `/ws` 将可通过 `/MyModule/ws` 访问

可以通过以下方式访问：
```
GET http://localhost:8000/MyModule/info
POST http://localhost:8000/MyModule/process

WebSocket 连接: ws://localhost:8000/MyModule/ws
```

### 6.4 路由最佳实践

1. **路由命名规范**：
   - 使用清晰、描述性的路径名
   - 遵循 RESTful API 设计原则
   - 避免与其他模块的路由冲突

2. **安全性考虑**：
   - 为敏感操作实现认证机制
   - 对用户输入进行验证和过滤
   - 使用 HTTPS（在生产环境中）

3. **错误处理**：
   - 实现适当的错误处理和响应格式
   - 记录关键操作日志
   - 提供有意义的错误信息

```python
from ErisPulse import sdk
from fastapi import HTTPException

class Main(BaseModule):
    def __init__(self):
        super().__init__()
        self.sdk = sdk
        self.logger = sdk.logger.get_child("MyModule")
        self.storage = sdk.storage
        self._register_routes()
        
    def _register_routes(self):
        async def get_item(item_id: int):
            """获取项目信息"""
            if item_id < 0:
                raise HTTPException(status_code=400, detail="无效的项目ID")
            
            # 模拟数据获取
            item = {"id": item_id, "name": f"Item {item_id}"}
            self.logger.info(f"获取项目: {item}")
            return item
        
        self.sdk.router.register_http_route(
            module_name="MyModule",
            path="/items/{item_id}",
            handler=get_item,
            methods=["GET"]
        )
```

## 7. `LICENSE` 文件
`LICENSE` 文件用于声明模块的版权信息, 示例模块的声明默认为 `MIT` 协议。

---

## 开发建议

### 1. 使用异步编程模型
- **优先使用异步库**：如 `aiohttp`、`asyncpg` 等，避免阻塞主线程。
- **合理使用事件循环**：确保异步函数正确地被 `await` 或调度为任务（`create_task`）。

### 2. 异常处理与日志记录
- **统一异常处理机制**：直接 `raise` 异常，上层会自动捕获并记录日志。
- **详细的日志输出**：在关键路径上打印调试日志，便于问题排查。

### 3. 模块化与解耦设计
- **职责单一原则**：每个模块/类只做一件事，降低耦合度。
- **依赖注入**：通过构造函数传递依赖对象（如 `sdk`），提高可测试性。

### 4. 性能优化
- **避免死循环**：避免无止境的循环导致阻塞或内存泄漏。
- **使用智能缓存**：对频繁查询的数据使用缓存，例如数据库查询结果、配置信息等。

### 5. 安全与隐私
- **敏感数据保护**：避免将密钥、密码等硬编码在代码中，使用sdk的配置模块。
- **输入验证**：对所有用户输入进行校验，防止注入攻击等安全问题。
