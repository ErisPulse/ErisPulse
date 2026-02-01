# ErisPulse 核心模块

ErisPulse 提供了多个核心模块，为开发者提供基础功能支持。

## 0. 核心模块概览

| 名称 | 用途 |
|------|------|
| `sdk` | SDK对象（包含所有核心功能） |
| `storage`/`sdk.storage` | 获取/设置数据库配置 |
| `config`/`sdk.config` | 获取/设置模块配置 |
| `adapter`/`sdk.adapter` | 适配器管理/获取实例 |
| `module`/`sdk.module` | 模块管理器 |
| `logger`/`sdk.logger` | 日志记录器 |
| `BaseAdapter`/`sdk.BaseAdapter` | 适配器基类 |
| `Event`/`sdk.Event` | 事件处理模块 |
| `lifecycle`/`sdk.lifecycle` | 生命周期事件管理器 |
| `router`/`sdk.router` | 路由管理器 |

> 注意: `Event` 模块是 ErisPulse 2.2.0 弹簧的新模块,发布模块时请注意提醒用户兼容性问题

### 模块加载架构

ErisPulse 采用现代化的模块加载架构，将加载逻辑与核心功能分离：

#### 加载器组件

| 组件 | 文件位置 | 用途 |
|------|---------|------|
| `BaseLoader` | `loaders/base_loader.py` | 加载器抽象基类，定义标准接口 |
| `AdapterLoader` | `loaders/adapter_loader.py` | 从 PyPI entry-points 加载适配器 |
| `ModuleLoader` | `loaders/module_loader.py` | 从 PyPI entry-points 加载模块 |
| `ModuleInitializer` | `loaders/initializer.py` | 初始化协调器，统一管理加载流程 |

#### 懒加载机制

ErisPulse 默认启用懒加载模块系统，这意味着模块只有在第一次被访问时才会实际加载和初始化。这样可以显著提升应用启动速度和内存效率。

详细说明请参考：[懒加载模块系统](./lazy-loading.md)

```python
# 全局配置懒加载
[ErisPulse.framework]
enable_lazy_loading = true  # true=启用懒加载(默认)，false=禁用懒加载

# 模块级别控制
class MyModule(BaseModule):
    @staticmethod
    def should_eager_load() -> bool:
        return True  # 返回True表示禁用懒加载
```

#### 加载流程

1. SDK 初始化时，`ModuleInitializer` 协调加载流程
2. 并行调用 `AdapterLoader` 和 `ModuleLoader` 从 PyPI entry-points 加载
3. 按顺序注册适配器和模块
4. 根据配置和模块特性决定是否立即加载或懒加载

### 事件系统子模块

Event 模块包含以下子模块：

| 子模块 | 用途 |
|-------|------|
| `Event.command` | 命令处理 |
| `Event.message` | 消息事件处理 |
| `Event.notice` | 通知事件处理 |
| `Event.request` | 请求事件处理 |
| `Event.meta` | 元事件处理 |
| `Event.exceptions` | 事件异常处理 |

```python
# 直接导入方式
from ErisPulse.Core import (
        storage, config, module_registry,
        adapter, module, logger,
        BaseAdapter, Event, lifecycle
    )

# 通过SDK对象方式
from ErisPulse import sdk
sdk.storage  # 等同于直接导入的storage
```

## 1. 存储系统 (storage)

基于 SQLite 的键值存储系统，支持复杂数据类型的持久化存储。

### 主要功能

- 键值存储：`storage.set(key, value)` / `storage.get(key, default)`
- 事务支持：通过 `storage.transaction()` 上下文管理器
- 数据快照和恢复
- 自动备份机制
- 批量操作：`storage.set_multi(dict)` / `storage.delete_multi(list)`

### 使用示例

```python
from ErisPulse import sdk

# 设置存储项
sdk.storage.set("user.settings", {"theme": "dark", "language": "zh-CN"})

# 获取存储项
settings = sdk.storage.get("user.settings", {})

# 使用事务
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")

# 批量操作
sdk.storage.set_multi({
    "key1": "value1",
    "key2": "value2"
})
sdk.storage.delete_multi(["key1", "key2"])
```

## 2. 配置管理 (config)

TOML 格式配置文件管理器，用于管理模块和适配器配置。

### 主要功能

- 模块配置读取：`config.getConfig(key, default)`
- 配置项设置：`config.setConfig(key, value)`
- 支持嵌套配置结构

### 使用示例

```python
from ErisPulse import sdk

# 获取模块配置
module_config = sdk.config.getConfig("MyModule", {})

# 设置默认配置
if not module_config:
    default_config = {
        "api_url": "https://api.example.com",
        "timeout": 30
    }
    sdk.config.setConfig("MyModule", default_config)

# 嵌套配置访问
nested_value = sdk.config.getConfig("MyModule.subkey.value", "default")
sdk.config.setConfig("MyModule.subkey.value", "new_value")
```

## 3. 日志系统 (logger)

模块化日志系统，支持多级日志和内存存储。

### 主要功能

- 模块级日志级别控制
- 内存日志存储
- 文件日志输出
- 丰富的日志格式
- 子模块日志记录器

### 使用示例

```python
from ErisPulse import sdk

# 记录日志
sdk.logger.info("模块已加载")
sdk.logger.error("发生错误: %s", str(error))

# 设置模块日志级别
sdk.logger.set_module_level("MyModule", "DEBUG")

# 获取子日志记录器
child_logger = sdk.logger.get_child("submodule")
child_logger.info("子模块日志")

# 更多日志级别
sdk.logger.debug("调试信息")
sdk.logger.info("运行状态")
sdk.logger.warning("警告信息")
sdk.logger.error("错误信息")
sdk.logger.critical("致命错误")  # 会触发程序崩溃

# 保存日志到文件
sdk.logger.save_logs("log.txt")
sdk.logger.set_output_file("app.log")
```

## 4. 异常处理 (exceptions)

统一的异常处理机制。

### 主要功能

- 全局异常捕获
- 异步异常处理
- 格式化的错误信息输出

### 使用示例

```python
from ErisPulse import sdk
import asyncio

# 为事件循环设置异常处理器
loop = asyncio.get_running_loop()
sdk.exceptions.setup_async_loop(loop)
```

## 5. 模块管理 (module)

模块管理系统，提供模块的注册、加载和状态管理功能。

### 主要功能

- 模块类注册：`module.register(name, class, info)`
- 模块实例管理：`module.load()` / `module.unload()`
- 模块状态管理：`module.exists()` / `module.is_enabled()` / `module.enable()` / `module.disable()`
- 模块实例获取：`module.get(name)` / `module.list_loaded()` / `module.list_registered()`
- 配置管理：继承自 ManagerBase，提供统一的配置接口

### 使用示例

```python
from ErisPulse import sdk

# 模块注册（通常由加载器自动完成）
from ErisPulse.Core.Bases import BaseModule

class MyModule(BaseModule):
    def on_load(self, data):
        sdk.logger.info("模块已加载")
    
    def on_unload(self, data):
        sdk.logger.info("模块已卸载")

# 手动注册模块类
sdk.module.register("MyModule", MyModule, {"meta": {"version": "1.0.0"}})

# 加载模块
await sdk.module.load("MyModule")

# 获取模块实例
my_module = sdk.module.get("MyModule")

# 通过属性访问获取模块实例
my_module = sdk.module.MyModule

# 检查模块是否已加载
if sdk.module.is_loaded("MyModule"):
    my_module.do_something()

# 检查模块是否存在且启用
if "MyModule" in sdk.module:
    sdk.logger.info("模块可用")

# 列出已注册和已加载的模块
registered = sdk.module.list_registered()
loaded = sdk.module.list_loaded()

# 模块配置管理
sdk.module.enable("MyModule")      # 启用模块
sdk.module.disable("MyModule")     # 禁用模块
sdk.module.is_enabled("MyModule") # 检查是否启用

# 卸载模块
await sdk.module.unload("MyModule")  # 卸载指定模块
await sdk.module.unload()           # 卸载所有模块
```

## 6. 适配器管理 (adapter)

适配器管理系统，提供适配器的注册、启动和状态管理功能。

### 主要功能

- 适配器类注册：`adapter.register(platform, class, info)`
- 适配器实例管理：`adapter.startup()` / `adapter.shutdown()`
- 适配器状态管理：`adapter.exists()` / `adapter.is_enabled()` / `adapter.enable()` / `adapter.disable()`
- 适配器实例获取：`adapter.get(platform)` / `adapter.platforms`
- 配置管理：继承自 ManagerBase，提供统一的配置接口
- 事件处理：`adapter.on()` / `adapter.emit()` / `adapter.middleware()`

### 使用示例

```python
from ErisPulse import sdk
from ErisPulse.Core.Bases import BaseAdapter

class MyPlatformAdapter(BaseAdapter):
    async def start(self):
        sdk.logger.info("适配器已启动")
    
    async def shutdown(self):
        sdk.logger.info("适配器已关闭")

# 注册适配器类
sdk.adapter.register("MyPlatform", MyPlatformAdapter)

# 启动所有适配器
await sdk.adapter.startup()

# 启动指定适配器
await sdk.adapter.startup(["MyPlatform"])

# 获取适配器实例
adapter_instance = sdk.adapter.get("MyPlatform")
adapter_instance = sdk.adapter.MyPlatform

# 发送消息
sdk.adapter.MyPlatform.Send.To("user", "U1001").Text("Hello")

# 监听标准事件（所有平台）
@sdk.adapter.on("message")
async def handler(data):
    sdk.logger.info(f"收到消息: {data}")

# 监听特定平台的标准事件
@sdk.adapter.on("message", platform="MyPlatform")
async def handler(data):
    sdk.logger.info(f"收到 MyPlatform 消息: {data}")

# 监听平台原生事件
@sdk.adapter.on("message", raw=True, platform="MyPlatform")
async def handler(data):
    sdk.logger.info(f"收到 MyPlatform 原生事件: {data}")

# 提交事件
await sdk.adapter.emit({
    "id": "123",
    "time": 1620000000,
    "type": "message",
    "detail_type": "private",
    "message": [{"type": "text", "data": {"text": "Hello"}}],
    "platform": "MyPlatform",
    "myplatform_raw": {...平台原生事件数据...},
    "myplatform_raw_type": "text_message"
})

# 添加中间件
@sdk.adapter.middleware
async def my_middleware(data):
    sdk.logger.info(f"中间件处理: {data}")
    return data

# 获取所有已注册平台
platforms = sdk.adapter.platforms

# 启用/禁用适配器
sdk.adapter.enable("MyPlatform")
sdk.adapter.disable("MyPlatform")

# 关闭所有适配器
await sdk.adapter.shutdown()
```

## 7. 事件处理 (Event)
> 更完整的事件处理示例，请参考 docs/core/event-system.md 文档

事件处理模块，提供了一套完整的事件处理机制。

### 主要功能

- 命令处理
- 消息事件处理
- 通知事件处理
- 请求事件处理
- 元事件处理
- 事件异常处理

### 使用示例

```python
from ErisPulse.Core.Event import message, command, notice, request, meta

# 消息事件处理
@message.on_message()
async def message_handler(event):
    sdk.logger.info(f"收到消息事件: {event}")

# 命令处理
@command(["help", "h"], aliases=["帮助"], help="显示帮助信息")
async def help_handler(event):
    sdk.logger.info(f"收到命令事件: {event}")

# 通知事件处理
@notice.on_group_increase()
async def notice_handler(event):
    sdk.logger.info(f"收到群成员增加事件: {event}")

# 请求事件处理
@request.on_friend_request()
async def request_handler(event):
    sdk.logger.info(f"收到好友请求事件: {event}")

# 元事件处理
@meta.on_connect()
async def connect_handler(event):
    sdk.logger.info(f"平台连接成功: {event['platform']}")
```

## 8. 生命周期管理 (lifecycle)

生命周期管理模块提供了统一的生命周期事件管理和触发机制。所有核心组件和第三方模块都可以通过此模块提交和监听生命周期事件。

### 主要功能

- 生命周期事件注册和监听
- 标准化生命周期事件格式
- 点式结构事件监听（例如 `module.init` 可以被 `module` 监听到）
- 自定义事件支持
- 事件计时器功能

### 事件标准格式

所有生命周期事件都遵循以下标准格式：

```json
{
    "event": "事件名称",
    "timestamp": 1234567890,
    "data": {
        // 事件相关数据
    },
    "source": "事件来源模块",
    "msg": "事件描述"
}
```

### 事件处理机制

#### 点式结构事件
ErisPulse 支持点式结构的事件命名，例如 `module.init`。当触发具体事件时，也会触发其父级事件：
- 触发 `module.init` 事件时，也会触发 `module` 事件
- 触发 `adapter.status.change` 事件时，也会触发 `adapter.status` 和 `adapter` 事件

#### 通配符事件处理器
可以注册 `*` 事件处理器来捕获所有事件。

### 标准生命周期事件

#### 核心初始化事件

| 事件名称 | 触发时机 | 数据结构 |
|---------|---------|---------|
| `core.init.start` | 核心初始化开始时 | `{}` |
| `core.init.complete` | 核心初始化完成时 | `{"duration": "初始化耗时(秒)", "success": true/false}` |

#### 模块生命周期事件

| 事件名称 | 触发时机 | 数据结构 |
|---------|---------|---------|
| `module.load` | 模块加载完成时 | `{"module_name": "模块名", "success": true/false}` |
| `module.init` | 模块初始化完成时 | `{"module_name": "模块名", "success": true/false}` |
| `module.unload` | 模块卸载时 | `{"module_name": "模块名", "success": true/false}` |

#### 适配器生命周期事件

| 事件名称 | 触发时机 | 数据结构 |
|---------|---------|---------|
| `adapter.load` | 适配器加载完成时 | `{"platform": "平台名", "success": true/false}` |
| `adapter.start` | 适配器开始启动时 | `{"platforms": ["平台名列表"]}` |
| `adapter.status.change` | 适配器状态发生变化时 | `{"platform": "平台名", "status": "状态(starting/started/start_failed/stopping/stopped)", "retry_count": 重试次数(可选), "error": "错误信息(可选)"}` |
| `adapter.stop` | 适配器开始关闭时 | `{}` |
| `adapter.stopped` | 适配器关闭完成时 | `{}` |

#### 服务器生命周期事件

| 事件名称 | 触发时机 | 数据结构 |
|---------|---------|---------|
| `server.start` | 服务器启动时 | `{"base_url": "基础url","host": "主机地址", "port": "端口号"}` |
| `server.stop` | 服务器停止时 | `{}` |

### 使用示例

```python
from ErisPulse import sdk

# 监听模块初始化事件
@sdk.lifecycle.on("module.init")
async def module_init_handler(event_data):
    print(f"模块 {event_data['data']['module_name']} 初始化完成")

# 监听适配器状态变化事件
@sdk.lifecycle.on("adapter.status.change")
async def adapter_status_handler(event_data):
    status_data = event_data['data']
    print(f"适配器 {status_data['platform']} 状态变化为: {status_data['status']}")

# 提交自定义生命周期事件
await sdk.lifecycle.submit_event(
    "custom.event",
    data={"custom_field": "custom_value"},
    source="MyModule",
    msg="自定义事件描述"
)

# 使用计时器功能
sdk.lifecycle.start_timer("my_operation")
# ... 执行一些操作 ...
duration = sdk.lifecycle.stop_timer("my_operation")
print(f"操作耗时: {duration} 秒")
```

### 第三方模块集成

生命周期模块是第三方模块也可以使用的核心模块。第三方模块可以通过此模块：

1. 提交自定义生命周期事件
2. 监听标准或自定义生命周期事件
3. 利用计时器功能测量操作耗时

## 模块使用规范

- 所有模块通过 `sdk` 对象统一管理
- 每个模块拥有独立命名空间，使用 `sdk` 进行调用
- 可以在模块间使用 `sdk.<module_name>.<func>` 的方式调用其他模块中的方法
- 生命周期事件可用于模块间通信和状态同步

## 配置管理

### 1. 命令前缀配置
```toml
[ErisPulse]
[ErisPulse.event]
[ErisPulse.event.command]
prefix = "/"
case_sensitive = true
allow_space_prefix = false

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
