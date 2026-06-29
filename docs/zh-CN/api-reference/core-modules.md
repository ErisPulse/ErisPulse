# 核心模块 API

本文档提供 ErisPulse 核心模块的 API 快速参考，包含方法签名和简要说明。详细用法和示例请点击各模块的"完整文档"链接。

## Storage 模块

基于 SQLite 的键值存储系统，支持通用 SQL 链式查询。

### 基本操作

```python
from ErisPulse import sdk

sdk.storage.set("key", "value")
value = sdk.storage.get("key", default_value)
keys = sdk.storage.keys()
sdk.storage.delete("key")
```

### 批量操作

```python
sdk.storage.set_multi({"key1": "val1", "key2": "val2"})
values = sdk.storage.get_multi(["key1", "key2"])
sdk.storage.delete_multi(["key1", "key2"])
```

### 事务操作

```python
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
```

### 属性访问

```python
sdk.storage.my_key          # 等价于 sdk.storage.get("my_key")
sdk.storage.my_key = "val"  # 等价于 sdk.storage.set("my_key", "val")
```

### SQL 链式查询

Storage 模块提供链式调用风格的通用 SQL 查询构建器，支持自定义表的 CRUD 操作。

```python
sdk.storage.CreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
})

sdk.storage.Table("users").Insert({"name": "Alice"}).Execute()
rows = sdk.storage.Table("users").Select("name").Where("id > ?", 0).Execute()
```

> 完整的链式查询 API（Select/Insert/Update/Delete/Where/OrderBy/Limit、AlterTable、事务等）请参考 [SQL 查询构建器](../advanced/sql-builder.md)。

### 存储后端抽象

`StorageManager` 继承自 `BaseStorage` 抽象基类，支持扩展其他存储介质（Redis、MySQL 等）。

```python
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder
```

## Config 模块

TOML 格式的配置文件管理，支持点号分隔的键路径。

### API 概览

| 方法 | 说明 |
|------|------|
| `getConfig(key, default)` | 读取配置，支持点号路径如 `"MyModule.subkey"` |
| `setConfig(key, value, immediate=False)` | 写入配置。`immediate=True` 时立即保存到文件 |
| `force_save()` | 强制将内存中的配置写入文件 |
| `reload()` | 从文件重新加载配置 |

### 示例

```python
config = sdk.config.getConfig("MyModule", {})
value = sdk.config.getConfig("MyModule.timeout", 30)

sdk.config.setConfig("MyModule", {"key": "value"})
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)
```

> `setConfig` 默认采用延迟写入（每 5 秒批量保存），设置 `immediate=True` 可立即持久化到配置文件。配置变更会触发 `config.set` 生命周期事件。

## Logger 模块

模块化日志系统，基于 Rich 输出，支持子日志器和模块级别控制。

### 基本用法

```python
sdk.logger.debug("调试信息")
sdk.logger.info("运行信息")
sdk.logger.warning("警告信息")
sdk.logger.error("错误信息")
sdk.logger.critical("致命错误")
```

### 子日志器

```python
child_logger = sdk.logger.get_child("MyModule")
child_logger.info("子模块日志")

child_logger.get_child("utils")  # 支持嵌套
```

### 日志级别控制

```python
sdk.logger.set_level("DEBUG")                          # 全局级别
sdk.logger.set_module_level("MyModule", "DEBUG")       # 模块级别

# 支持的级别（从低到高）：
# TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL
# TRACE 为最低级别，输出框架内部详细调试信息（事件分发、路由注册等）
sdk.logger.set_level("TRACE")                          # 开启全部日志
```

### 日志订阅（推模式）

供 Dashboard 等模块实时接收结构化日志，支持等级筛选和历史补发。

```python
# 装饰器方式
@sdk.logger.handler("my-handler", min_level="INFO")
def on_log(log_data: dict):
    # log_data = {
    #     "timestamp": "2026-06-29T22:00:00.123456",
    #     "level": "WARNING", "level_num": 30,
    #     "module": "ErisPulse.Core.adapter",
    #     "message": "严格模式：...",
    # }
    pass

# 直接调用方式
sdk.logger.handler("my-handler", min_level="INFO")(on_log)
sdk.logger.remove_handler("my-handler")
```

| 方法 | 说明 |
|------|------|
| `handler(id, *, min_level)(func)` | 装饰器/直接调用两用。`id` 为空时取函数名。注册时自动补发历史日志 |
| `remove_handler(id)` | 移除订阅器 |

### 输出控制

```python
sdk.logger.set_output_file("app.log")
sdk.logger.save_logs("log.txt")
sdk.logger.get_logs("MyModule")
sdk.logger.set_memory_limit(1000)
```

## Adapter 模块

适配器管理器，管理多平台适配器的注册、启动和关闭。

### API 概览

| 方法 | 说明 |
|------|------|
| `get(platform)` | 获取适配器实例 |
| `exists(platform)` | 检查适配器是否已注册 |
| `enable(platform)` / `disable(platform)` | 启用/禁用适配器 |
| `is_enabled(platform)` | 检查是否启用 |
| `startup(platforms)` / `shutdown(platforms)` | 启动/关闭适配器 |
| `is_running(platform)` | 检查适配器是否正在运行 |
| `list_running()` | 列出所有正在运行的适配器 |
| `platforms` | 获取所有平台名称列表 |

### 适配器事件

```python
@sdk.adapter.on("message")
async def handle_message(event):
    pass

@sdk.adapter.on("message", platform="yunhu")
async def handle_yunhu_message(event):
    pass
```

### Bot 状态查询

```python
sdk.adapter.get_bot_info("telegram", "123456")
sdk.adapter.list_bots("telegram")
sdk.adapter.is_bot_online("telegram", "123456")
sdk.adapter.get_status_summary()
```

> 完整的适配器管理 API 请参考 [适配器系统 API](adapter-system.md)。

## Module 模块

模块管理器，管理插件的注册、加载和卸载。

### API 概览

| 方法 | 说明 |
|------|------|
| `get(name)` | 获取模块实例 |
| `exists(name)` | 检查是否已注册 |
| `is_loaded(name)` | 检查是否已加载 |
| `is_enabled(name)` | 检查是否启用 |
| `enable(name)` / `disable(name)` | 启用/禁用模块 |
| `load(name)` / `unload(name)` | 加载/卸载模块 |
| `list_registered()` | 列出已注册模块 |
| `list_loaded()` | 列出已加载模块 |
| `get_info(name)` | 获取模块信息 |
| `get_status_summary()` | 获取模块状态摘要 |

### 属性访问

```python
module = sdk.module.get("ModuleName")
module = sdk.module.ModuleName
module = sdk.ModuleName  # 等价快捷方式
```

## Lifecycle 模块

事件驱动的生命周期管理器，提供事件提交和监听功能。

### API 概览

| 方法 | 说明 |
|------|------|
| `on(event, priority=0)` | 装饰器注册事件处理器，支持点号匹配和通配符 `*` |
| `register(event, handler, priority=0)` | 函数式注册处理器 |
| `unregister(event, handler=None)` | 移除处理器 |
| `emit(event, data)` | 异步触发事件 |
| `emit_sync(event, data)` | 同步触发事件 |
| `submit_event(event_type, msg, data, source)` | 提交标准格式事件（兼容旧版） |
| `start_timer(id)` / `stop_timer(id)` | 性能计时器 |

### 示例

```python
@sdk.lifecycle.on("module.init")
async def handle_module_init(event_data):
    print(f"模块初始化: {event_data}")

@sdk.lifecycle.on("module")
async def handle_any_module_event(event_data):
    print(f"模块事件: {event_data}")

await sdk.lifecycle.emit("custom.event", {"key": "value"})
```

> 完整的标准事件列表和详细用法请参考 [生命周期管理](../advanced/lifecycle.md)。

## Router 模块

HTTP/WebSocket 路由管理器，基于 FastAPI + Uvicorn，支持装饰器路由、中间件、分组、限流、CORS。

> 完整的路由 API 文档（装饰器路由、WebSocket、中间件、速率限制、CORS、安全头等）请参考 [路由管理器](../advanced/router.md)。

### 快速参考

```python
# HTTP 路由
@sdk.router.get("MyModule", "/api")
async def handler(request: HttpRequest):
    return {"status": "ok"}

# WebSocket 路由
@sdk.router.ws("MyModule", "/ws")
async def ws_handler(ws: WebSocketConnection):
    async for text in ws.iter_text():
        await ws.send_text(f"Echo: {text}")

# 路由分组
group = sdk.router.group("MyModule", prefix="/v1")
@group.get("/users")
async def list_users(request: HttpRequest):
    return {"users": []}
```

## HTTP Client 模块

统一 HTTP/WS 客户端，基于 aiohttp，提供请求统计、重试、日志、ErisPulse 异常体系。

> 完整的 HTTP 客户端文档（请求方法、响应对象、WebSocket 客户端、异常体系等）请参考 [HTTP 客户端](../advanced/http-client.md)。

### 快速参考

```python
from ErisPulse.Core import client

# HTTP 请求
resp = await client.get("https://api.example.com/users")
data = await resp.json()

# WebSocket
ws = await client.ws_connect("wss://example.com/ws")
async for text in ws.iter_text():
    await ws.send_text(f"Echo: {text}")
```

## 相关文档

- [事件系统 API](event-system.md) - Event 模块 API
- [适配器系统 API](adapter-system.md) - Adapter 管理 API
- [SQL 查询构建器](../advanced/sql-builder.md) - SQL 链式查询完整文档
- [路由管理器](../advanced/router.md) - 路由管理器完整文档
- [HTTP 客户端](../advanced/http-client.md) - HTTP 客户端完整文档
- [生命周期管理](../advanced/lifecycle.md) - 生命周期完整文档
