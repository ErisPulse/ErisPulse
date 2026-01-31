# ErisPulse 最佳实践

本文档提供了 ErisPulse 开发和部署的最佳实践建议。

> **架构更新说明**：本文档已根据 ErisPulse 新架构进行更新，包括：
> - 懒加载模块系统（ErisPulse 2.2.0+）
> - 独立的生命周期事件系统
> - Event 包装类（ErisPulse 2.3.3+）

## 1. 模块开发最佳实践

### 1.1 模块结构设计

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse import sdk
from ErisPulse.Core.Event import command, message, notice

class Main(BaseModule):
    def __init__(self):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("MyModule")
        self.storage = sdk.storage
        self.config = sdk.config
        self.module_config = self._load_config()
        
    @staticmethod
    def should_eager_load():
        """
        控制模块是否立即加载
        
        返回 True 表示禁用懒加载，模块会在 SDK 初始化时立即加载
        返回 False 表示启用懒加载，模块会在首次访问时才加载
        默认值为 False，推荐大多数情况使用懒加载以提升启动速度
        
        适用场景（返回 True）：
        - 监听生命周期事件的模块
        - 定时任务模块
        - 需要在应用启动时就初始化的模块
        """
        return False
    
    async def on_load(self, event):
        """模块加载时调用"""
        # 注册事件处理器（框架会自动管理注销）
        @command("hello", help="发送问候消息")
        async def hello_command(event):
            await event.reply("你好！")
        
        # 注册消息处理器
        @message.on_group_message()
        async def group_handler(event):
            self.logger.info(f"收到群消息: {event.get_alt_message()}")
        
        self.logger.info("模块已加载")
    
    async def on_unload(self, event):
        """模块卸载时调用"""
        # 清理资源
        await self._cleanup_resources()
        self.logger.info("模块已卸载")

    def _load_config(self):
        config = self.config.getConfig("MyModule")
        if not config:
            default_config = self._get_default_config()
            self.config.setConfig("MyModule", default_config)
            return default_config
        return config
        
    def _get_default_config(self):
        return {
            "api_url": "https://api.example.com",
            "timeout": 30,
            "retry_count": 3
        }
    
    async def _cleanup_resources(self):
        """清理资源"""
        # 在这里执行清理逻辑，如关闭连接、释放缓存等
        pass
```

### 1.2 懒加载模块系统

ErisPulse 2.2.0 引入了懒加载模块系统，可以显著提升应用启动速度和内存效率。

#### 配置懒加载

```toml
# config.toml - 全局配置
[ErisPulse.framework]
enable_lazy_loading = true  # true=启用懒加载(默认)，false=禁用懒加载
```

#### 模块级别控制

```python
class MyModule(BaseModule):
    @staticmethod
    def should_eager_load() -> bool:
        # 返回 True 表示禁用懒加载
        # 返回 False 表示启用懒加载
        return True
```

#### 推荐使用懒加载的场景

- ✅ 大多数功能模块（返回 `False`）
- ✅ 命令处理模块
- ✅ 按需加载的扩展功能

#### 推荐禁用懒加载的场景

- ❌ 生命周期事件监听器（返回 `True`）
- ❌ 定时任务模块
- ❌ 需要早期初始化的模块

### 1.3 Event 包装类的使用

> **适用于 ErisPulse 2.3.3 及以上版本**

Event 包装类继承自 `dict`，在保持完全向后兼容的同时，提供了大量便捷方法。

#### 基本使用

```python
from ErisPulse.Core.Event import command, message

@command("info", help="获取用户信息")
async def info_command(event):
    # 获取核心事件信息
    event_id = event.get_id()
    event_time = event.get_time()
    platform = event.get_platform()
    
    # 获取发送者信息
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    
    # 获取消息内容
    text = event.get_text()
    message_segments = event.get_message()
    
    # 判断消息类型
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    
    await event.reply(
        f"用户: {nickname}({user_id}), "
        f"类型: {'私聊' if is_private else '群聊'}, "
        f"平台: {platform}"
    )
```

#### 便捷回复方法

```python
@command("test", help="测试回复方法")
async def test_command(event):
    # 文本回复（默认）
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

#### 等待用户回复

```python
@command("ask", help="询问用户姓名")
async def ask_command(event):
    # 发送提示并等待用户回复
    await event.reply("请输入您的姓名:")
    
    # 等待用户回复，超时时间 30 秒
    reply = await event.wait_reply(timeout=30)
    
    if reply:
        name = reply.get_text()
        await event.reply(f"你好，{name}！")
    else:
        await event.reply("等待超时")

# 带验证的等待回复
@command("age", help="询问用户年龄")
async def age_command(event):
    def validate_age(event_data):
        """验证年龄是否有效"""
        try:
            age = int(event_data.get_text())
            return 0 <= age <= 150
        except ValueError:
            return False
    
    await event.reply("请输入您的年龄（0-150岁）:")
    
    # 等待回复并验证
    reply = await event.wait_reply(timeout=60, validator=validate_age)
    
    if reply:
        age = int(reply.get_text())
        await event.reply(f"您的年龄是 {age} 岁")
```

#### 命令信息获取

```python
@command("cmdinfo", help="获取命令信息")
async def cmdinfo_command(event):
    # 获取命令信息
    cmd_name = event.get_command_name()
    cmd_args = event.get_command_args()
    cmd_raw = event.get_command_raw()
    
    await event.reply(
        f"命令: {cmd_name}\n"
        f"参数: {cmd_args}\n"
        f"原始文本: {cmd_raw}"
    )
```

#### 通知事件处理

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    # 获取通知事件信息
    operator_id = event.get_operator_id()
    operator_nickname = event.get_operator_nickname()
    
    # 自动回复
    await event.reply(f"欢迎添加我为好友，{operator_nickname}！")

@notice.on_group_member_increase()
async def group_increase_handler(event):
    # 群成员增加事件
    user_id = event.get_user_id()
    await event.reply(f"欢迎新成员加入！")
```

### 1.4 生命周期事件监听

> **重要**：生命周期事件已独立到 `sdk.lifecycle` 模块，与普通事件系统分离。

```python
from ErisPulse import sdk

class Main(BaseModule):
    async def on_load(self, event):
        # 监听模块初始化事件
        @sdk.lifecycle.on("module.init")
        async def on_module_init(event_data):
            print(f"模块 {event_data['data']['module_name']} 初始化完成")
        
        # 监听适配器状态变化事件
        @sdk.lifecycle.on("adapter.status.change")
        async def on_adapter_status(event_data):
            status = event_data['data']['status']
            platform = event_data['data']['platform']
            print(f"适配器 {platform} 状态变化为: {status}")
        
        # 监听所有生命周期事件（通配符）
        @sdk.lifecycle.on("*")
        async def on_any_event(event_data):
            print(f"生命周期事件: {event_data['event']}")
```

详细的生命周期事件使用请参考：[lifecycle.md](./lifecycle.md)

### 1.5 异步编程模型

优先使用异步库，避免阻塞主线程：

```python
import aiohttp

class Main(BaseModule):
    async def on_load(self, event):
        # 使用 aiohttp 创建异步 HTTP 会话
        self.session = aiohttp.ClientSession()
    
    async def fetch_data(self, url):
        async with self.session.get(url) as response:
            return await response.json()
    
    async def on_unload(self, event):
        # 关闭会话
        await self.session.close()
```

### 1.6 异常处理

统一异常处理机制，记录详细日志：

```python
import traceback

class Main(BaseModule):
    async def handle_event(self, event):
        try:
            # 业务逻辑
            await self.process_event(event)
        except ValueError as e:
            # 预期的业务错误
            self.logger.warning(f"事件处理警告: {e}")
            await event.reply(f"参数错误: {e}")
        except Exception as e:
            # 未预期的错误
            self.logger.error(f"处理事件时出错: {e}")
            self.logger.debug(f"错误详情: {traceback.format_exc()}")
            raise
```

## 2. 适配器开发最佳实践

### 2.1 连接管理

实现连接重试机制，确保服务稳定性：

```python
import asyncio

class MyAdapter(BaseAdapter):
    async def start(self):
        retry_count = 0
        max_retries = 5
        
        while retry_count < max_retries:
            try:
                await self._connect_to_platform()
                self.logger.info("连接成功")
                break
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    # 指数退避策略
                    wait_time = min(60 * (2 ** retry_count), 600)
                    self.logger.warning(
                        f"连接失败，{wait_time}秒后重试 ({retry_count}/{max_retries}): {e}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error(f"连接失败，已达到最大重试次数")
                    raise
```

### 2.2 事件转换

严格按照 OneBot12 标准进行事件转换，并保留原始数据：

```python
import time
import uuid

class MyPlatformConverter:
    def convert(self, raw_event):
        """将平台原生事件转换为 OneBot12 标准格式"""
        if not isinstance(raw_event, dict):
            return None
        
        onebot_event = {
            "id": self._generate_event_id(raw_event),
            "time": self._convert_timestamp(raw_event.get("timestamp")),
            "type": self._convert_event_type(raw_event.get("type")),
            "detail_type": self._convert_detail_type(raw_event),
            "platform": "myplatform",
            "self": {
                "platform": "myplatform",
                "user_id": str(raw_event.get("bot_id", ""))
            },
            "myplatform_raw": raw_event,          # 保留原始数据（必须）
            "myplatform_raw_type": raw_event.get("type", "")  # 保留原始事件类型（必须）
        }
        return onebot_event
    
    def _generate_event_id(self, raw_event):
        """生成事件 ID"""
        event_id = raw_event.get("event_id")
        if event_id:
            return str(event_id)
        return str(uuid.uuid4())
    
    def _convert_timestamp(self, timestamp):
        """转换时间戳为 10 位秒级时间戳"""
        if not timestamp:
            return int(time.time())
        # 如果是毫秒级时间戳，转换为秒级
        if timestamp > 10**12:
            return int(timestamp / 1000)
        return int(timestamp)
```

### 2.3 SendDSL 使用

适配器支持链式调用风格的消息发送，返回的是 `asyncio.Task` 对象：

```python
# 不等待结果，消息在后台发送
my_adapter = adapter.get("MyPlatform")
task = my_adapter.Send.To("user", "123").Text("Hello")

# 等待结果，获取发送结果
result = await task

# 直接 await
result = await my_adapter.Send.To("user", "123").Text("Hello")

# 指定发送账号（多账户适配器）
await my_adapter.Send.Using("account_id").To("user", "123").Text("Hello")
```

## 3. 配置管理最佳实践

### 3.1 配置结构化

使用结构化配置，便于管理和维护：

```toml
# config.toml
[MyModule]
api_url = "https://api.example.com"
timeout = 30

[MyModule.database]
host = "localhost"
port = 5432
name = "mymodule"

[MyModule.features]
enable_cache = true
cache_ttl = 3600
```

### 3.2 配置验证

对配置进行验证，确保配置正确性：

```python
def _validate_config(self, config):
    required_fields = ["api_url", "timeout"]
    for field in required_fields:
        if field not in config:
            raise ValueError(f"缺少必要配置项: {field}")
    
    if not isinstance(config["timeout"], int) or config["timeout"] <= 0:
        raise ValueError("timeout 配置必须为正整数")
    
    if not config["api_url"].startswith(("http://", "https://")):
        raise ValueError("api_url 必须以 http:// 或 https:// 开头")
```

### 3.3 全局数据库配置

ErisPulse 支持两种数据库模式：

```toml
[ErisPulse.storage]
# 使用全局数据库（包内的 ../data/config.db）
# 默认使用项目数据库（项目目录下的 config/config.db）
use_global_db = false
```

## 4. 存储系统最佳实践

### 4.1 事务使用

在关键操作中使用事务，确保数据一致性：

```python
async def update_user_data(self, user_id, data):
    with self.sdk.storage.transaction():
        self.sdk.storage.set(f"user:{user_id}:profile", data["profile"])
        self.sdk.storage.set(f"user:{user_id}:settings", data["settings"])
        # 如果任何操作失败，所有更改都会回滚
```

### 4.2 批量操作

使用批量操作提高性能：

```python
# 批量设置
self.sdk.storage.set_multi({
    "key1": "value1",
    "key2": "value2",
    "key3": "value3"
})

# 批量获取
values = self.sdk.storage.get_multi(["key1", "key2", "key3"])

# 批量删除
self.sdk.storage.delete_multi(["key1", "key2", "key3"])
```

### 4.3 自动快照

配置自动快照机制，防止数据丢失：

```python
class Main(BaseModule):
    async def on_load(self, event):
        # 每30分钟自动快照
        self.sdk.storage.set_snapshot_interval(1800)
```

## 5. 日志系统最佳实践

### 5.1 日志级别使用

合理使用不同日志级别：

```python
class Main(BaseModule):
    def __init__(self):
        self.logger = sdk.logger.get_child("MyModule")
    
    async def process_event(self, event):
        # DEBUG: 调试信息，生产环境通常关闭
        self.logger.debug(f"开始处理事件: {event.get_id()}")
        
        try:
            result = await self._handle_event(event)
            # INFO: 正常运行信息
            self.logger.info(f"事件处理成功: {event.get_id()}")
            return result
        except ValueError as e:
            # WARNING: 警告信息，不影响主要功能
            self.logger.warning(f"事件处理警告: {e}")
        except Exception as e:
            # ERROR: 错误信息
            self.logger.error(f"事件处理失败: {e}")
            raise
    
    async def _handle_event(self, event):
        # CRITICAL: 严重错误，需要立即处理
        if event.get_text() == "critical":
            self.logger.critical("检测到严重错误！")
```

### 5.2 日志输出配置

配置日志输出到文件，便于问题排查：

```python
class Main(BaseModule):
    async def on_load(self, event):
        # 设置模块日志级别
        self.sdk.logger.set_module_level("MyModule", "DEBUG")
        
        # 设置日志输出文件（可以是单个文件或列表）
        self.sdk.logger.set_output_file([
            "logs/app.log",
            "logs/module.log"
        ])
```

## 6. 性能优化最佳实践

### 6.1 缓存使用

对频繁查询的数据使用缓存：

```python
import asyncio

class Main(BaseModule):
    def __init__(self):
        self._cache = {}
        self._cache_lock = asyncio.Lock()
    
    async def get_user_info(self, user_id):
        async with self._cache_lock:
            if user_id in self._cache:
                # 检查缓存是否过期
                if self._cache[user_id]["expires"] > asyncio.get_event_loop().time():
                    return self._cache[user_id]["data"]
                else:
                    del self._cache[user_id]
        
        # 从数据库获取数据
        user_info = await self._fetch_user_info_from_db(user_id)
        
        # 缓存数据
        async with self._cache_lock:
            self._cache[user_id] = {
                "data": user_info,
                "expires": asyncio.get_event_loop().time() + 3600  # 1小时过期
            }
        
        return user_info
```

### 6.2 资源管理

及时释放资源，避免内存泄漏：

```python
class Main(BaseModule):
    def __init__(self):
        self.resources = []
        self._connections = {}
    
    async def create_resource(self):
        resource = await self._create_new_resource()
        self.resources.append(resource)
        return resource
    
    async def on_unload(self, event):
        # 清理所有资源
        for resource in self.resources:
            await resource.close()
        self.resources.clear()
        
        # 清理所有连接
        for conn in self._connections.values():
            await conn.close()
        self._connections.clear()
```

## 7. 路由注册最佳实践

模块可以注册 HTTP 和 WebSocket 路由，提供 Web API 或实时通信功能。

### 7.1 HTTP 路由注册

```python
from fastapi import Request, HTTPException

class Main(BaseModule):
    async def on_load(self, event):
        # 注册 HTTP 路由
        self.sdk.router.register_http_route(
            module_name="MyModule",
            path="/info",
            handler=self.get_info,
            methods=["GET"]
        )
        
        self.sdk.router.register_http_route(
            module_name="MyModule",
            path="/process",
            handler=self.process_data,
            methods=["POST"]
        )
    
    async def get_info(self):
        """获取模块信息"""
        return {
            "module": "MyModule",
            "version": "1.0.0",
            "status": "running"
        }
    
    async def process_data(self, request: Request):
        """处理数据"""
        data = await request.json()
        
        if "key" not in data:
            raise HTTPException(status_code=400, detail="缺少必要参数: key")
        
        self.logger.info(f"处理数据: {data}")
        
        return {
            "status": "success",
            "received": data
        }
```

### 7.2 WebSocket 路由注册

```python
from fastapi import WebSocket, WebSocketDisconnect

class Main(BaseModule):
    def __init__(self):
        self._connections = set()
    
    async def on_load(self, event):
        # 注册 WebSocket 路由
        self.sdk.router.register_websocket(
            module_name="MyModule",
            path="/ws",
            handler=self.websocket_handler,
            auth_handler=self.auth_handler  # 可选的认证函数
        )
    
    async def auth_handler(self, websocket: WebSocket) -> bool:
        """WebSocket 认证"""
        token = websocket.headers.get("authorization")
        # 实现认证逻辑
        return token == "Bearer valid-token"
    
    async def websocket_handler(self, websocket: WebSocket):
        """WebSocket 连接处理器"""
        await websocket.accept()
        self._connections.add(websocket)
        self.logger.info(f"新的 WebSocket 连接: {websocket.client}")
        
        try:
            while True:
                data = await websocket.receive_text()
                self.logger.info(f"收到消息: {data}")
                
                # 处理消息
                response = self._process_message(data)
                await websocket.send_text(response)
                
                # 广播给所有连接
                await self._broadcast(f"广播: {data}")
                
        except WebSocketDisconnect:
            self.logger.info(f"WebSocket 连接断开: {websocket.client}")
        finally:
            self._connections.discard(websocket)
    
    async def _broadcast(self, message: str):
        """向所有连接广播消息"""
        disconnected = set()
        for connection in self._connections:
            try:
                await connection.send_text(message)
            except:
                disconnected.add(connection)
        
        # 移除断开的连接
        self._connections -= disconnected
    
    async def on_unload(self, event):
        """清理所有 WebSocket 连接"""
        for connection in self._connections:
            try:
                await connection.close()
            except:
                pass
        self._connections.clear()
```

> **注意**：注册的路由会自动添加模块名称作为前缀。例如：
> - HTTP 路由 `/info` 可通过 `/MyModule/info` 访问
> - WebSocket 路由 `/ws` 可通过 `/MyModule/ws` 连接

## 8. 安全最佳实践

### 8.1 敏感数据保护

避免将密钥、密码等硬编码在代码中：

```toml
# config.toml
[MyModule]
api_key = "YOUR_API_KEY_HERE"  # 用户需要替换为实际值
```

```python
# 代码中
class Main(BaseModule):
    def __init__(self):
        config = self.sdk.config.getConfig("MyModule")
        self.api_key = config.get("api_key")
        if not self.api_key or self.api_key == "YOUR_API_KEY_HERE":
            raise ValueError("请在 config.toml 中配置 API 密钥")
```

### 8.2 输入验证

对所有用户输入进行验证，防止注入攻击：

```python
@command("exec", help="执行命令")
async def exec_command(event):
    command = event.get_text().split(maxsplit=1)[1] if len(event.get_text().split(maxsplit=1)) > 1 else ""
    
    # 验证命令
    if not command:
        await event.reply("请提供要执行的命令")
        return
    
    # 白名单验证
    allowed_commands = ["status", "info", "help"]
    if command not in allowed_commands:
        await event.reply(f"不允许的命令: {command}")
        return
    
    # 执行命令
    result = await self._execute_safe_command(command)
    await event.reply(result)
```

## 9. 部署最佳实践

### 9.1 健康检查

实现健康检查接口，便于监控：

```python
import time

class Main(BaseModule):
    async def on_load(self, event):
        self._register_health_check()
    
    def _register_health_check(self):
        self.sdk.router.register_http_route(
            module_name="MyModule",
            path="/health",
            handler=self.health_check,
            methods=["GET"]
        )
    
    async def health_check(self):
        """健康检查接口"""
        return {
            "status": "ok",
            "module": "MyModule",
            "version": "1.0.0",
            "timestamp": int(time.time())
        }
```

### 9.2 优雅关闭

实现优雅关闭机制：

```python
import asyncio

class Main(BaseModule):
    def __init__(self):
        self._running = False
    
    async def on_load(self, event):
        self._running = True
        # 启动后台任务
        asyncio.create_task(self._background_task())
    
    async def on_unload(self, event):
        """优雅关闭"""
        self._running = False
        
        # 等待后台任务完成
        self.logger.info("等待后台任务完成...")
        await asyncio.sleep(2)
        
        # 清理资源
        await self._cleanup_resources()
        self.logger.info("优雅关闭完成")
    
    async def _background_task(self):
        """后台任务"""
        while self._running:
            # 执行周期性任务
            await self._do_periodic_task()
            await asyncio.sleep(60)
```

## 10. 开发工作流建议

### 10.1 热重载开发模式

使用热重载模式进行开发，自动监控文件变化：

```bash
# 启动热重载模式
epsdk run main.py --reload
```

### 10.2 项目初始化

使用官方初始化工具创建项目：

```bash
# 交互式初始化
epsdk init

# 快速初始化
epsdk init -q -n my_bot
```

### 10.3 模块管理

使用 CLI 工具管理模块：

```bash
# 安装模块
epsdk install MyModule

# 列出已安装模块
epsdk list --type=modules

# 升级模块
epsdk upgrade MyModule
```

遵循这些最佳实践可以帮助您开发出高质量、稳定可靠的 ErisPulse 模块和适配器。
