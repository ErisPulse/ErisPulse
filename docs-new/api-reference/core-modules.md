# 核心模块 API

本文档详细介绍了 ErisPulse 的核心模块 API。

## Storage 模块

### 基本操作

```python
from ErisPulse import sdk

# 设置值
sdk.storage.set("key", "value")

# 获取值
value = sdk.storage.get("key", default_value)

# 删除值
sdk.storage.delete("key")

# 检查键是否存在
exists = sdk.storage.exists("key")
```

### 事务操作

```python
# 使用事务确保数据一致性
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
    # 如果任何操作失败，所有更改都会回滚
```

### 批量操作

```python
# 批量设置
sdk.storage.set_multi({
    "key1": "value1",
    "key2": "value2",
    "key3": "value3"
})

# 批量获取
values = sdk.storage.get_multi(["key1", "key2", "key3"])

# 批量删除
sdk.storage.delete_multi(["key1", "key2", "key3"])
```

## Config 模块

### 读取配置

```python
from ErisPulse import sdk

# 获取配置
config = sdk.config.getConfig("MyModule", {})

# 获取嵌套配置
value = sdk.config.getConfig("MyModule.subkey.value", "default")
```

### 写入配置

```python
# 设置配置
sdk.config.setConfig("MyModule", {"key": "value"})

# 设置嵌套配置
sdk.config.setConfig("MyModule.subkey.value", "new_value")
```

### 配置示例

```python
def _load_config(self):
    config = sdk.config.getConfig("MyModule")
    if not config:
        # 创建默认配置
        default_config = {
            "api_url": "https://api.example.com",
            "timeout": 30,
            "cache_ttl": 3600
        }
        sdk.config.setConfig("MyModule", default_config)
        sdk.config.force_save() # 强制保存配置的这种方式在这里使用是可行的，因为你需要设置默认值到配置文件中，除此之外，不建议使用这种方式强制保存配置
        return default_config
    return config
```

## Logger 模块

### 基本日志

```python
from ErisPulse import sdk

# 不同日志级别
sdk.logger.debug("调试信息")
sdk.logger.info("运行信息")
sdk.logger.warning("警告信息")
sdk.logger.error("错误信息")
sdk.logger.critical("致命错误")
```

### 子日志记录器

```python
# 获取子日志记录器
child_logger = sdk.logger.get_child("MyModule")
child_logger.info("子模块日志")

# 子模块还可以有子模块的日志，这样可以更精确地控制日志输出
child_logger.get_child("utils")
```

### 日志输出

```python
# 设置输出文件
sdk.logger.set_output_file("app.log")

# 保存日志到文件
sdk.logger.save_logs("log.txt")
```

## Adapter 模块

### 获取适配器

```python
from ErisPulse import sdk

# 获取适配器实例
adapter = sdk.adapter.get("platform_name")

# 通过属性访问
adapter = sdk.adapter.platform_name
```

### 适配器事件

```python
# 监听标准事件
@sdk.adapter.on("message")
async def handle_message(event):
    pass

# 监听特定平台的事件
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

## Module 模块

### 获取模块

```python
from ErisPulse import sdk

# 获取模块实例
module = sdk.module.get("ModuleName")

# 通过属性访问
module = sdk.module.ModuleName
module = sdk.ModuleName
```

### 模块管理

```python
# 检查模块是否存在
exists = sdk.module.exists("ModuleName")

# 检查模块是否已加载
is_loaded = sdk.module.is_loaded("ModuleName")

# 检查模块是否启用
is_enabled = sdk.module.is_enabled("ModuleName")

# 启用/禁用模块
sdk.module.enable("ModuleName")
sdk.module.disable("ModuleName")

# 加载模块
await sdk.module.load("ModuleName")

# 卸载模块
await sdk.module.unload("ModuleName")

# 列出已加载的模块
loaded = sdk.module.list_loaded()

# 列出已注册的模块
registered = sdk.module.list_registered()
```

## Lifecycle 模块

### 事件提交

```python
from ErisPulse import sdk

# 提交自定义事件
await sdk.lifecycle.submit_event(
    "custom.event",
    data={"key": "value"},
    source="MyModule",
    msg="自定义事件描述"
)
```

### 事件监听

```python
# 监听特定事件
@sdk.lifecycle.on("module.init")
async def handle_module_init(event_data):
    print(f"模块初始化: {event_data}")

# 监听父级事件
@sdk.lifecycle.on("module")
async def handle_any_module_event(event_data):
    print(f"模块事件: {event_data}")

# 监听所有事件
@sdk.lifecycle.on("*")
async def handle_any_event(event_data):
    print(f"系统事件: {event_data}")
```

### 计时器

```python
# 开始计时
sdk.lifecycle.start_timer("my_operation")

# ... 执行操作 ...

# 获取持续时间
duration = sdk.lifecycle.get_duration("my_operation")

# 停止计时
total_time = sdk.lifecycle.stop_timer("my_operation")
```

## Router 模块

### HTTP 路由

```python
from ErisPulse import sdk
from fastapi import Request

# 注册 HTTP 路由
async def handler(request: Request):
    data = await request.json()
    return {"status": "ok", "data": data}

sdk.router.register_http_route(
    module_name="MyModule",
    path="/api",
    handler=handler,
    methods=["POST"]
)

# 取消路由
sdk.router.unregister_http_route("MyModule", "/api")
```

### WebSocket 路由

```python
from ErisPulse import sdk
from fastapi import WebSocket

# 注册 WebSocket 路由
async def websocket_handler(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")

async def auth_handler(websocket: WebSocket) -> bool:
    token = websocket.query_params.get("token")
    if token == "<PASSWORD>":
        return True
    return False

router.register_websocket(
    module_name="my_module",
    path="/secure_ws",
    handler=websocket_handler,
    auth_handler=auth_handler
)

# 取消路由
sdk.router.unregister_websocket("MyModule", "/ws")
```

### 路由信息

```python
# 获取 FastAPI 应用实例
app = sdk.router.get_app()

# 添加中间件
@app.middleware("http")
async def add_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Custom-Header"] = "value"
    return response
```

## 相关文档

- [事件系统 API](event-system.md) - Event 模块 API
- [适配器系统 API](adapter-system.md) - Adapter 管理 API