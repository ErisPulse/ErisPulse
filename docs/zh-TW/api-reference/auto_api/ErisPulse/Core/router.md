# `ErisPulse.Core.router` 模块

---

## 模块概述


ErisPulse 路由系统

提供统一的HTTP和WebSocket路由管理，支持多适配器路由注册和生命周期管理。
增强功能: 装饰器路由、路由中间件、自动文档、路由限流、分组/版本管理、CORS/安全头

> **提示**
> 1. 使用 @http / @get / @post / @ws 装饰器快速注册路由
> 2. module_name 为必填第一个参数，决定路径前缀
> 3. 支持 route group 进行版本管理和路由分组
> 4. 支持 CORS 和安全响应头配置化

---

## 类列表


### `class FuncMiddleware`

函数式路由中间件包装

> **内部方法**


### `class RouteGroup`

路由分组

> **提示**
> 通过 sdk.router.group() 创建，支持版本前缀和嵌套分组

**示例**:
```python
>>> api = sdk.router.group("MyModule", "/api", version="1", tags=["API"])
>>> @api.get("/users")
... async def users(request):
...     return {"users": []}
```


#### 方法列表


##### `__init__(module_name: str, prefix: str, version: str = None, tags: list[str] = None, middlewares: list = None, router: 'RouterManager' = None)`

初始化路由分组

:param module_name: str 模块名称 (路径前缀)
:param prefix: str 路由前缀
:param version: str 版本号 (可选, 如 "1")
:param tags: list[str] API 文档标签 (可选)
:param middlewares: list 分组级中间件 (可选)
:param router: RouterManager 路由管理器实例

---


##### `_resolve_path(path: str)`

解析完整路径

> **内部方法**

---


##### `http(path: str, methods: list[str] = None)`

HTTP 路由装饰器

:param path: str 路由路径
:param methods: list[str] HTTP 方法列表 (默认: ["POST"])
:return: Callable 装饰器

---


##### `get(path: str)`

GET 路由装饰器

:param path: str 路由路径
:return: Callable 装饰器

---


##### `post(path: str)`

POST 路由装饰器

:param path: str 路由路径
:return: Callable 装饰器

---


##### `put(path: str)`

PUT 路由装饰器

:param path: str 路由路径
:return: Callable 装饰器

---


##### `delete(path: str)`

DELETE 路由装饰器

:param path: str 路由路径
:return: Callable 装饰器

---


##### `ws(path: str)`

WebSocket 路由装饰器

:param path: str 路由路径
:param auth_handler: Callable 认证函数 (可选)
:param auto_accept: bool 是否自动 accept (默认: True)

---


##### `sse(path: str)`

SSE (Server-Sent Events) 路由装饰器

:param path: str 路由路径

---


##### `group(prefix: str)`

创建嵌套分组

:param prefix: str 子路由前缀
:return: RouteGroup 嵌套分组实例

**示例**:
```python
>>> api = sdk.router.group("MyModule", "/api", version="1")
>>> users = api.group("/users")
>>> @users.get("/")
... async def list_users(request):
...     ...
```

---


### `class RouterManager`

路由管理器

> **提示**
> 核心功能:
> - HTTP/WebSocket 路由注册
> - 路由中间件 (前/后置处理)
> - 自动 OpenAPI 文档 (/docs, /redoc)
> - 路由限流 (rate_limit 参数)
> - 路由分组/版本管理
> - CORS / 安全头配置化


#### 方法列表


##### `__init__()`

初始化路由管理器

> **提示**
> 会自动创建 FastAPI 实例并设置核心路由

---


##### `_normalize_path(prefix: str, path: str)`

标准化路径，确保格式正确

:param prefix: str 路径前缀（如模块名）
:param path: str 路径部分
:return: str 标准化后的完整路径

> **内部方法**

---


##### `_make_http_endpoint(handler: Callable)`

根据处理器签名创建 FastAPI 兼容的 HTTP 端点

自动检测第一个参数的类型注解：
- fastapi.Request → 直接透传（向后兼容）
- HttpRequest / 无注解且名称类似 request → 注入 HttpRequest 包装
- 其他类型 / 非请求参数名 → 不注入

> **内部方法**

---


##### `_make_ws_handler(handler: Callable)`

根据处理器签名创建 WebSocket 处理器包装

- fastapi.WebSocket 注解 → 提取 .raw 透传
- WebSocketConnection / 无注解 → 直接传递 WebSocketConnection

> **内部方法**

---


##### `_make_ws_auth_handler(auth_handler: Callable)`

根据签名创建 WebSocket 认证处理器包装

> **内部方法**

---


##### `_make_sse_endpoint(handler: Callable)`

根据处理器签名创建 SSE 端点包装器

自动检测处理器是否需要 HttpRequest 参数。
为处理器创建 SseEmitter 实例，通过回调桥接 SSE 协议到底层 StreamingResponse。

> **内部方法**

---


##### `_register_sse_endpoint(full_path: str, module_name: str, handler: Callable)`

SSE 路由注册内部实现

> **内部方法**

---


##### `async async _run_ws_hooks(ws_conn: WebSocketConnection, hook_type: str)`

执行 WebSocket 生命周期钩子

> **内部方法**

---


##### `_setup_core_routes()`

设置系统核心路由

> **内部方法**

---


##### `_setup_error_pages()`

设置错误页面和静态资源

> **内部方法** 
注册 web_status/ 包目录的静态文件服务（/status-assets），
并为 GET 请求添加 ErisPulse 主题化错误页面。
POST 等非 GET 请求仍然返回 JSON 格式的错误响应。

---


##### `_restore_routes_from_records()`

将内部记录中已有的路由重新注册到当前 FastAPI 实例

> **内部方法**

---


##### `_ensure_middleware_installed()`

确保 FastAPI 级中间件已安装

> **内部方法**

---


##### `middleware()`

路由中间件装饰器

:param paths: str 路径匹配模式 (支持通配符), 留空则为全局中间件
:return: Callable 装饰器

> **提示**
> 前置中间件签名: (request) -> request | Response
> 后置中间件签名: (request, response) -> response
> 根据函数参数数量自动判断是前置还是后置
> paths 参数为 glob 模式路径匹配，如 "/MyModule/*"，而非 (module_name, pattern)

**示例**:
```python
>>> @sdk.router.middleware()
... async def log_all(request):
...     return request
>>>
>>> @sdk.router.middleware("/MyModule/api/*")
... async def auth_check(request):
...     return request
```

---


##### `add_middleware(before: Callable = None, after: Callable = None)`

添加中间件函数

:param before: Callable 前置中间件 (可选)
:param after: Callable 后置中间件 (可选)
:param paths: str 路径匹配模式, 留空为全局

---


##### `_match_path(pattern: str, path: str)`

通配符路径匹配

:param pattern: str 匹配模式
:param path: str 实际路径
:return: bool 是否匹配

> **内部方法**

---


##### `_http_decorate(full_path: str, module_name: str, methods: list[str] = None)`

HTTP 路由装饰器内部实现

> **内部方法**

---


##### `_ws_decorate(full_path: str, module_name: str)`

WebSocket 路由装饰器内部实现

> **内部方法**

---


##### `http(module_name: str, path: str, methods: list[str] = None)`

HTTP 路由装饰器

:param module_name: str 模块名称 (必填, 作为路径前缀)
:param path: str 路由路径
:param methods: list[str] HTTP 方法列表 (默认: ["POST"])
:param rate_limit: str|dict 限流规则 (可选)
:param summary: str API 摘要 (可选, 用于文档)
:param description: str API 描述 (可选, 用于文档)
:param tags: list[str] API 标签 (可选, 用于文档分组)
:param response_model: type 响应模型 (可选)
:param deprecated: bool 是否废弃 (可选)
:return: Callable 装饰器

**示例**:
```python
>>> @sdk.router.http("MyModule", "/api/data", methods=["GET", "POST"])
... async def handle_data(request):
...     return {"ok": True}
```

---


##### `get(module_name: str, path: str)`

GET 路由装饰器

:param module_name: str 模块名称 (必填)
:param path: str 路由路径
:return: Callable 装饰器

---


##### `post(module_name: str, path: str)`

POST 路由装饰器

:param module_name: str 模块名称 (必填)
:param path: str 路由路径
:return: Callable 装饰器

---


##### `put(module_name: str, path: str)`

PUT 路由装饰器

:param module_name: str 模块名称 (必填)
:param path: str 路由路径
:return: Callable 装饰器

---


##### `delete(module_name: str, path: str)`

DELETE 路由装饰器

:param module_name: str 模块名称 (必填)
:param path: str 路由路径
:return: Callable 装饰器

---


##### `ws(module_name: str, path: str)`

WebSocket 路由装饰器

:param module_name: str 模块名称 (必填)
:param path: str WebSocket 路径
:param auth_handler: Callable 认证函数 (可选)
:param auto_accept: bool 是否自动 accept (默认: True)

> **提示**
> 推荐使用 auth_handler 进行连接确认，而非关闭 auto_accept。
> 仅在需要完全控制连接流程时才设置 auto_accept=False。

**示例**:
```python
>>> @sdk.router.ws("MyModule", "/ws/chat")
... async def chat(websocket):
...     await websocket.send_text("Hello!")
```

---


##### `sse(module_name: str, path: str)`

SSE (Server-Sent Events) 路由装饰器

:param module_name: str 模块名称 (必填)
:param path: str SSE 端点路径
:param summary: str API 摘要 (可选)
:param description: str API 描述 (可选)
:param tags: list[str] API 标签 (可选)

**示例**:
```python
>>> @sdk.router.sse("MyModule", "/events")
... async def event_stream(sse):
...     while True:
...         await sse.send({"msg": "hello"})
...         await asyncio.sleep(1)

>>> @sdk.router.sse("MyModule", "/logs")
... async def log_stream(request, sse):
...     token = request.query_params.get("token")
...     while True:
...         line = await get_next_log(token)
...         await sse.send(line, event="log")
```

---


##### `_sse_decorate(full_path: str, module_name: str)`

SSE 路由装饰器内部实现

> **内部方法**

---


##### `register_http_route(module_name: str, path: str, handler: Callable, methods: list[str] | None = None, rate_limit: str | dict | None = None, summary: str | None = None, description: str | None = None, tags: list[str] | None = None, response_model: type | None = None, deprecated: bool | None = None)`

注册HTTP路由

:param module_name: str 模块名称
:param path: str 路由路径
:param handler: Callable 处理函数
:param methods: list[str] HTTP方法列表(默认["POST"])
:param rate_limit: str|dict|None 限流规则 (可选, 如 "10/minute")
:param summary: str API 摘要 (可选)
:param description: str API 描述 (可选)
:param tags: list[str] API 标签 (可选)
:param response_model: type 响应模型 (可选)
:param deprecated: bool 是否废弃 (可选)

**异常**: `ValueError` - 当路径和方法都已注册时抛出

---


##### `register_webhook()`

兼容性方法：注册HTTP路由（适配器旧接口）

---


##### `unregister_http_route(module_name: str, path: str)`

取消注册HTTP路由

:param module_name: 模块名称
:param path: 路由路径
:return: bool 是否成功取消注册

---


##### `_register_ws_endpoint(full_path: str, module_name: str, handler: Callable[[WebSocket], Awaitable[Any]], auth_handler: Callable[[WebSocket], Awaitable[bool]] | None = None, auto_accept: bool = True)`

WebSocket 路由注册内部实现

> **内部方法**

---


##### `register_websocket(module_name: str, path: str, handler: Callable[[WebSocket], Awaitable[Any]], auth_handler: Callable[[WebSocket], Awaitable[bool]] | None = None, auto_accept: bool = True)`

注册WebSocket路由

:param module_name: str 模块名称
:param path: str WebSocket路径
:param handler: Callable[[WebSocket], Awaitable[Any]] 主处理函数
:param auth_handler: Optional[Callable[[WebSocket], Awaitable[bool]]] 认证函数
:param auto_accept: bool 是否自动调用 websocket.accept()，默认 True

> **提示**
> 推荐使用 auth_handler 进行连接确认，而非关闭 auto_accept。
> auth_handler 在连接建立后执行，返回 False 会自动关闭连接。
> 仅在需要完全控制连接流程时才设置 auto_accept=False。

**异常**: `ValueError` - 当路径已注册时抛出

---


##### `unregister_websocket(module_name: str, path: str)`

取消注册WebSocket路由

:param module_name: 模块名称
:param path: WebSocket路径
:return: bool 是否成功取消注册

---


##### `register_sse(module_name: str, path: str, handler: Callable)`

注册 SSE (Server-Sent Events) 路由

SSE 路由为 HTTP GET 端点，返回 ``text/event-stream`` 流式响应。
处理器接收 ``SseEmitter`` 实例（以及可选的 ``HttpRequest``），
通过 ``sse.send()`` 推送事件，调用 ``sse.close()`` 断开连接。

:param module_name: str 模块名称
:param path: str SSE 端点路径
:param handler: Callable 事件处理器, 签名: ``async def handler(sse)`` 或 ``async def handler(request, sse)``

**异常**: `ValueError` - 当路径已注册时抛出

**示例**:
```python
>>> async def event_stream(sse):
...     for i in range(10):
...         await sse.send({"count": i})
...         await asyncio.sleep(1)
>>> router.register_sse("MyModule", "/events", event_stream)
```

---


##### `unregister_sse(module_name: str, path: str)`

取消注册 SSE 路由

:param module_name: 模块名称
:param path: SSE 路径
:return: bool 是否成功取消注册

---


##### `unregister_all_by_namespace(namespace: str)`

清理指定命名空间下的所有路由

:param namespace: 命名空间（适配器名或模块名）
:return: dict 清理统计 {"http_count": int, "websocket_count": int, "sse_count": int}

---


##### `list_namespaces()`

列出所有已注册的命名空间及其路由

:return: dict {namespace: {"http": [paths], "websocket": [paths], "sse": [paths]}}

**示例**:
```python
>>> router.list_namespaces()
{
    "onebot11": {
        "http": ["/onebot11/webhook", "/onebot11/callback"],
        "websocket": ["/onebot11/ws"],
        "sse": ["/onebot11/events"]
    }
}
```

---


##### `get_module_routes(module_name: str)`

获取指定命名空间的详细路由信息

与 list_namespaces() 不同，此方法返回每个路由的详细信息：
- HTTP 路由包含路径和 HTTP 方法列表
- WebSocket 路由包含路径和是否需要认证
- SSE 路由包含路径和流式标记

:param module_name: 模块/平台名称
:return: {"http": [...], "websocket": [...], "sse": [...]}
   http: [{"path": str, "methods": [str]}]
   websocket: [{"path": str, "auth": bool}]
   sse: [{"path": str, "streaming": true}]

**示例**:
```python
>>> router.get_module_routes("onebot11")
{
    "http": [{"path": "/onebot11/webhook", "methods": ["POST"]}],
    "websocket": [{"path": "/onebot11/ws", "auth": true}],
    "sse": [{"path": "/onebot11/events", "streaming": true}]
}
```

---


##### `get_module_urls(module_name: str)`

获取指定命名空间的完整连接 URL

在 get_module_routes() 的基础上拼接 base_url，生成可直接使用的完整 URL。
HTTP 路由使用 base_url 前缀，WebSocket 路由自动将 http/https 转换为 ws/wss，
SSE 路由使用 base_url 前缀（HTTP）。

:param module_name: 模块/平台名称
:return: {
    "base_url": str,
    "http": [{"path": str, "method": str, "url": str}],
    "websocket": [{"path": str, "url": str}],
    "sse": [{"path": str, "url": str}]
}

**示例**:
```python
>>> # 假设 base_url = "http://localhost:8080"
>>> router.get_module_urls("onebot11")
{
    "base_url": "http://localhost:8080",
    "http": [
        {"path": "/onebot11/webhook", "method": "POST",
         "url": "http://localhost:8080/onebot11/webhook"}
    ],
    "websocket": [
        {"path": "/onebot11/ws",
         "url": "ws://localhost:8080/onebot11/ws"}
    ],
    "sse": [
        {"path": "/onebot11/events",
         "url": "http://localhost:8080/onebot11/events"}
    ]
}
```

---


##### `get_module_urls_matching(prefix: str)`

获取指定前缀的所有命名空间的聚合连接 URL

适配器多账户场景下，路由可能注册为 ``yunhu_bot1``、``yunhu_bot2`` 等命名空间。
此方法按前缀匹配聚合所有相关命名空间的路由信息。

:param prefix: 命名空间前缀（如 "yunhu"）
:return: {
    "base_url": str,
    "http": [{"path": str, "method": str, "url": str, "namespace": str}],
    "websocket": [{"path": str, "url": str, "namespace": str}],
    "sse": [{"path": str, "url": str, "namespace": str}]
}

**示例**:
```python
>>> # 命名空间: yunhu_bot1, yunhu_bot2, onebot11
>>> router.get_module_urls_matching("yunhu")
{
    "base_url": "http://localhost:8080",
    "http": [
        {"path": "/yunhu_bot1/webhook", "method": "POST",
         "url": "http://localhost:8080/yunhu_bot1/webhook",
         "namespace": "yunhu_bot1"},
        {"path": "/yunhu_bot2/webhook", "method": "POST",
         "url": "http://localhost:8080/yunhu_bot2/webhook",
         "namespace": "yunhu_bot2"}
    ],
    "websocket": [],
    "sse": []
}
```

---


##### `group(module_name: str, prefix: str)`

创建路由分组

:param module_name: str 模块名称 (必填)
:param prefix: str 路由前缀
:param version: str 版本号 (可选)
:param tags: list[str] API 标签 (可选)
:param middlewares: list 分组中间件 (可选)
:return: RouteGroup 路由分组实例

**示例**:
```python
>>> api = sdk.router.group("MyModule", "/api", version="1")
>>> @api.get("/users")
... async def users(request):
...     return {"users": []}
```

---


##### `_apply_rate_limit(full_path: str, limit: str | dict)`

为路由应用限流

> **内部方法**

---


##### `_parse_rate_limit(limit: str | dict)`

解析限流规则

:param limit: str|dict 限流规则
:return: tuple[int, int] (max_requests, window_seconds)

> **内部方法**

---


##### `setup_cors(allow_origins: list[str] = None, allow_methods: list[str] = None, allow_headers: list[str] = None, allow_credentials: bool = False, max_age: int = DEFAULT_CORS_MAX_AGE_SECS, expose_headers: list[str] = None)`

配置 CORS

:param allow_origins: list[str] 允许的来源 (默认: ["*"])
:param allow_methods: list[str] 允许的方法 (默认: ["*"])
:param allow_headers: list[str] 允许的头 (默认: ["*"])
:param allow_credentials: bool 允许凭据 (默认: False)
:param max_age: int 预检缓存时间 (默认: 600)
:param expose_headers: list[str] 暴露的响应头 (可选)

**示例**:
```python
>>> sdk.router.setup_cors(
...     allow_origins=["https://example.com"],
...     allow_methods=["GET", "POST"],
... )
```

---


##### `setup_security_headers(headers: dict[str, str] = None)`

配置安全响应头

:param headers: dict[str, str] 自定义安全头 (可选, 会合并默认值)

**示例**:
```python
>>> sdk.router.setup_security_headers({
...     "Strict-Transport-Security": "max-age=31536000",
... })
```

---


##### `disable_docs()`

关闭 API 文档端点（生产环境推荐）

**示例**:
```python
>>> sdk.router.disable_docs()
```

---


##### `set_docs_info(title: str = None, description: str = None)`

更新 API 文档信息

:param title: str 文档标题 (可选)
:param description: str 文档描述 (可选)

---


##### `_apply_config()`

从配置文件自动应用 CORS 和安全头

> **内部方法**

---


##### `get_app()`

获取FastAPI应用实例

:return: FastAPI 应用实例

---


##### `_get_local_ips()`

获取本机局域网IP地址

> **内部方法**

---


##### `async async start(host: str = DEFAULT_SERVER_HOST, port: int = DEFAULT_SERVER_PORT, ssl_certfile: str | None = None, ssl_keyfile: str | None = None)`

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
:return: str 格式化后的URL

---

