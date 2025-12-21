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
