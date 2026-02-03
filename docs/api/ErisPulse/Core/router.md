# `ErisPulse.Core.router` 模块

> 最后更新：2026-02-03 22:38:11

---

## 模块概述


ErisPulse 路由系统

提供统一的HTTP和WebSocket路由管理，支持多适配器路由注册和生命周期管理。

> **提示**
> 1. 适配器只需注册路由，无需自行管理服务器
> 2. WebSocket支持自定义认证逻辑

---

## 类列表


### `class RouterManager`

路由管理器

> **提示**
> 核心功能：
> - HTTP/WebSocket路由注册
> - 生命周期管理
> - 统一错误处理


#### 方法列表


##### `__init__()`

初始化路由管理器

> **提示**
> 会自动创建FastAPI实例并设置核心路由

---


##### `_setup_core_routes()`

设置系统核心路由

> **内部方法** 
此方法仅供内部使用

---


##### `register_http_route(module_name: str, path: str, handler: Callable, methods: List[str] = ['POST'])`

注册HTTP路由

:param module_name: str 模块名称
:param path: str 路由路径
:param handler: Callable 处理函数
:param methods: List[str] HTTP方法列表(默认["POST"])

**异常**: `ValueError` - 当路径已注册时抛出

---


##### `register_webhook()`

兼容性方法：注册HTTP路由（适配器旧接口）

---


##### `unregister_http_route(module_name: str, path: str)`

取消注册HTTP路由

:param module_name: 模块名称
:param path: 路由路径

:return: Bool

---


##### `register_websocket(module_name: str, path: str, handler: Callable[[WebSocket], Awaitable[Any]], auth_handler: Optional[Callable[[WebSocket], Awaitable[bool]]] = None)`

注册WebSocket路由

:param module_name: str 模块名称
:param path: str WebSocket路径
:param handler: Callable[[WebSocket], Awaitable[Any]] 主处理函数
:param auth_handler: Optional[Callable[[WebSocket], Awaitable[bool]]] 认证函数

**异常**: `ValueError` - 当路径已注册时抛出

---


##### `get_app()`

获取FastAPI应用实例

:return: FastAPI应用实例

---


##### `async async start(host: str = '0.0.0.0', port: int = 8000, ssl_certfile: Optional[str] = None, ssl_keyfile: Optional[str] = None)`

启动路由服务器

:param host: str 监听地址(默认"0.0.0.0")
:param port: int 监听端口(默认8000)
:param ssl_certfile: Optional[str] SSL证书路径
:param ssl_keyfile: Optional[str] SSL密钥路径

**异常**: `RuntimeError` - 当服务器已在运行时抛出

---


##### `async async stop()`

停止服务器

---


##### `_format_display_url(url: str)`

格式化URL显示，将回环地址转换为更友好的格式

:param url: 原始URL
:return: 格式化后的URL

---

