# `ErisPulse/Core/server` 模块

ErisPulse Adapter Server
提供统一的适配器服务入口，支持HTTP和WebSocket路由

> **提示**：
1. 适配器只需注册路由，无需自行管理服务器
2. WebSocket支持自定义认证逻辑
3. 兼容FastAPI 0.68+ 版本

## 类

### `AdapterServer`

适配器服务器管理器

> **提示**：
核心功能：
- HTTP/WebSocket路由注册
- 生命周期管理
- 统一错误处理


#### 方法

##### `__init__`

初始化适配器服务器

> **提示**：
会自动创建FastAPI实例并设置核心路由


##### `register_webhook`

注册HTTP路由

:param adapter_name: str 适配器名称
:param path: str 路由路径(如"/message")
:param handler: Callable 处理函数
:param methods: List[str] HTTP方法列表(默认["POST"])

:raises ValueError: 当路径已注册时抛出

> **提示**：
路径会自动添加适配器前缀，如：/adapter_name/path


##### `register_websocket`

注册WebSocket路由

:param adapter_name: str 适配器名称
:param path: str WebSocket路径(如"/ws")
:param handler: Callable[[WebSocket], Awaitable[Any]] 主处理函数
:param auth_handler: Optional[Callable[[WebSocket], Awaitable[bool]]] 认证函数

:raises ValueError: 当路径已注册时抛出

> **提示**：
认证函数应返回布尔值，False将拒绝连接


##### `get_app`

获取FastAPI应用实例

:return: 
    FastAPI: FastAPI应用实例


##### `start`

启动适配器服务器

:param host: str 监听地址(默认"0.0.0.0")
:param port: int 监听端口(默认8000)
:param ssl_certfile: Optional[str] SSL证书路径
:param ssl_keyfile: Optional[str] SSL密钥路径

:raises RuntimeError: 当服务器已在运行时抛出


##### `stop`

停止服务器

> **提示**：
会等待所有连接正常关闭

