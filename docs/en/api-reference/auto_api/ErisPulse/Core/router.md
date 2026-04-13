# `ErisPulse.Core.router` 模块

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


##### `_normalize_path(prefix: str, path: str)`

标准化路径，确保格式正确

:param prefix: str 路径前缀（如模块名）
:param path: str 路径部分

:return:
    str: 标准化后的完整路径

> **内部方法** 
此方法仅供内部使用

---


##### `_setup_core_routes()`

设置系统核心路由

> **内部方法** 
此方法仅供内部使用

---


##### `register_http_route(module_name: str, path: str, handler: Callable, methods: list[str] = ['POST'])`

注册HTTP路由

:param module_name: str 模块名称
:param path: str 路由路径
:param handler: Callable 处理函数
:param methods: list[str] HTTP方法列表(默认["POST"])

**异常**: `ValueError` - 当路径和方法都已注册时抛出

---


##### `register_webhook()`

兼容性方法：注册HTTP路由（适配器旧接口）

---


##### `unregister_http_route(module_name: str, path: str)`

取消注册HTTP路由

:param module_name: 模块名称
:param path: 路由路径

:return:
    bool: 是否成功取消注册

---


##### `register_websocket(module_name: str, path: str, handler: Callable[[WebSocket], Awaitable[Any]], auth_handler: Callable[[WebSocket], Awaitable[bool]] | None = None, auto_accept: bool = True)`

注册WebSocket路由

:param module_name: str 模块名称
:param path: str WebSocket路径
:param handler: Callable[[WebSocket], Awaitable[Any]] 主处理函数
:param auth_handler: Optional[Callable[[WebSocket], Awaitable[bool]]] 认证函数
:param auto_accept: bool 是否自动调用 websocket.accept()，默认 True

**异常**: `ValueError` - 当路径已注册时抛出

---


##### `unregister_websocket(module_name: str, path: str)`

取消注册WebSocket路由

:param module_name: 模块名称
:param path: WebSocket路径

:return:
    bool: 是否成功取消注册

---


##### `unregister_all_by_namespace(namespace: str)`

清理指定命名空间下的所有路由

:param namespace: 命名空间（适配器名或模块名）
:return: 清理统计 {http_count: int, websocket_count: int}

**示例**:
```python
>>> router.unregister_all_by_namespace("my_adapter")
{"http_count": 3, "websocket_count": 1}
```

---


##### `list_namespaces()`

列出所有已注册的命名空间及其路由

:return: {namespace: {"http": [paths], "websocket": [paths]}}

**示例**:
```python
>>> router.list_namespaces()
{
    "onebot11": {
        "http": ["/onebot11/webhook", "/onebot11/callback"],
        "websocket": ["/onebot11/ws"]
    }
}
```

---


##### `get_app()`

获取FastAPI应用实例

:return:
    FastAPI: FastAPI应用实例

---


##### `_get_local_ips()`

获取本机局域网IP地址

> **内部方法** 
此方法仅供内部使用

---


##### `async async start(host: str = '0.0.0.0', port: int = 8000, ssl_certfile: str | None = None, ssl_keyfile: str | None = None)`

启动路由服务器

:param host: str 监听地址(默认"0.0.0.0")
:param port: int 监听端口(默认8000)
:param ssl_certfile: str | None SSL证书路径
:param ssl_keyfile: str | None SSL密钥路径

**异常**: `RuntimeError` - 当服务器已在运行时抛出

---


##### `async async stop()`

停止服务器并清理所有路由

---


##### `_format_display_url(url: str)`

格式化URL显示

:param url: str 原始URL
:return:
    str: 格式化后的URL

---

