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

## 函数列表


### `_load_web_stack()`

懒加载 FastAPI / Uvicorn / Starlette

> **内部方法**
将 web 栈依赖推迟到路由实际服务时才导入。幂等：重复调用仅做一次实际导入。

---


### `_web_stack_required(fn: Callable[..., Any])`

装饰器：在被装饰方法执行前确保 web 栈已加载

> **内部方法**
自动适配同步与异步方法。

- **fn** (`Callable`): 被装饰的方法
**返回值** (`Callable`): 包装后的方法

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


##### `__init__(module_name: str, prefix: str, version: str | None = None, tags: list[str] | None = None, middlewares: list | None = None, router: RouterManager | None = None)`

初始化路由分组

- **module_name** (`str`): 模块名称 (路径前缀)
- **prefix** (`str`): 路由前缀
- **version** (`str`): 版本号 (可选, 如 "1")
- **tags** (`list[str]`): API 文档标签 (可选)
- **middlewares** (`list`): 分组级中间件 (可选)
- **router** (`RouterManager`): 路由管理器实例

---


##### `_resolve_path(path: str)`

解析完整路径

> **内部方法**

---


##### `http(path: str, methods: list[str] | None = None)`

HTTP 路由装饰器

- **path** (`str`): 路由路径
- **methods** (`list[str]`): HTTP 方法列表 (默认: ["POST"])
**返回值** (`Callable`): 装饰器

---


##### `get(path: str)`

GET 路由装饰器

- **path** (`str`): 路由路径
**返回值** (`Callable`): 装饰器

---


##### `post(path: str)`

POST 路由装饰器

- **path** (`str`): 路由路径
**返回值** (`Callable`): 装饰器

---


##### `put(path: str)`

PUT 路由装饰器

- **path** (`str`): 路由路径
**返回值** (`Callable`): 装饰器

---


##### `delete(path: str)`

DELETE 路由装饰器

- **path** (`str`): 路由路径
**返回值** (`Callable`): 装饰器

---


##### `ws(path: str)`

WebSocket 路由装饰器

- **path** (`str`): 路由路径
- **auth_handler** (`Callable`): 认证函数 (可选)
- **auto_accept** (`bool`): 是否自动 accept (默认: True)

---


##### `sse(path: str)`

SSE (Server-Sent Events) 路由装饰器

- **path** (`str`): 路由路径

---


##### `group(prefix: str)`

创建嵌套分组

- **prefix** (`str`): 子路由前缀
**返回值** (`RouteGroup`): 嵌套分组实例

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
> 首次访问 ``app`` 属性时才创建 FastAPI 实例并注册核心路由。

---


##### `app()`

FastAPI 应用实例（惰性创建，首次访问时加载 web 栈并注册核心路由）

---


##### `_normalize_path(prefix: str, path: str)`

标准化路径，确保格式正确

- **prefix** (`str`): 路径前缀（如模块名）
- **path** (`str`): 路径部分
**返回值** (`str`): 标准化后的完整路径

> **内部方法**

---


##### `_track_owner_namespace(namespace: str)`

> **内部方法**
若当前处于加载上下文（current_owner 已设置），记录命名空间归属，
以便后续按 owner 兜底清理路由。

适配器常以"平台名"作为 owner，却使用更细颗粒度的命名空间
（如 onebot11_default）注册路由。仅靠 unregister_all_by_namespace(平台名)
无法覆盖这些路由，故在此自动建立 owner -> namespace 的映射。

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


##### `_create_sse_route(full_path: str, module_name: str, handler: Callable)`

> **内部方法**
在当前 app 实例上创建 SSE 路由（纯路由创建，不做重复检查、不写记录）

供 ``_register_sse_endpoint``（新注册）与 ``_restore_routes_from_records``（恢复）
共用，确保两条路径的路由创建逻辑完全一致。

---


##### `_register_sse_endpoint(full_path: str, module_name: str, handler: Callable)`

SSE 路由注册内部实现

> **内部方法**
包含重复检查、owner 追踪、记录写入；路由创建委托 :meth:`_create_sse_route`。

---


##### `async _run_ws_hooks(ws_conn: WebSocketConnection, hook_type: str)`

执行 WebSocket 生命周期钩子

> **内部方法**

---


##### `_setup_core_routes()`

设置系统核心路由

> **内部方法**

---


##### `_setup_error_pages()`

设置错误页面

> **内部方法**
为 GET 请求添加 ErisPulse 主题化错误页面。
POST 等非 GET 请求仍然返回 JSON 格式的错误响应。
所有错误码共用同一套 HTML 模板（``render_error_page``），仅注入不同的标题/描述。

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

- **paths** (`str`): 路径匹配模式 (支持通配符), 留空则为全局中间件
**返回值** (`Callable`): 装饰器

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


##### `add_middleware(before: Callable | None = None, after: Callable | None = None)`

添加中间件函数

- **before** (`Callable`): 前置中间件 (可选)
- **after** (`Callable`): 后置中间件 (可选)
- **paths** (`str`): 路径匹配模式, 留空为全局

---


##### `register_home_entry(name: str | dict, url: str, icon_svg: str = '')`

在根路由页面注册一个入口按钮

- **name** (`str`): | dict 按钮显示文本。纯文本直接传入字符串；
              也可传入 i18n 字典格式: {"i18n": "key", "default": "兜底"}
- **url** (`str`): 按钮链接地址
- **icon_svg** (`str`): 可选 SVG 图标标记

**示例**:
```python
>>> # 纯文本
>>> router.register_home_entry(name="Dashboard", url="/Dashboard")
>>>
>>> # i18n 字典格式
>>> router.register_home_entry(
...     name={"i18n": "core.router.entry_dashboard", "default": "Dashboard"},
...     url="/Dashboard",
... )
>>>
>>> # 带 SVG 图标
>>> router.register_home_entry(
...     name="控制台",
...     url="/console",
...     icon_svg='<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M4 17l6-6-6-6"/></svg>',
... )
```

---


##### `_match_path(pattern: str, path: str)`

通配符路径匹配

- **pattern** (`str`): 匹配模式
- **path** (`str`): 实际路径
**返回值** (`bool`): 是否匹配

> **内部方法**

---


##### `_http_decorate(full_path: str, module_name: str, methods: list[str] | None = None)`

HTTP 路由装饰器内部实现

> **内部方法**

---


##### `_ws_decorate(full_path: str, module_name: str)`

WebSocket 路由装饰器内部实现

> **内部方法**

---


##### `http(module_name: str, path: str, methods: list[str] | None = None)`

HTTP 路由装饰器

- **module_name** (`str`): 模块名称 (必填, 作为路径前缀)
- **path** (`str`): 路由路径
- **methods** (`list[str]`): HTTP 方法列表 (默认: ["POST"])
- **rate_limit** (`str|dict`): 限流规则 (可选)
- **summary** (`str`): API 摘要 (可选, 用于文档)
- **description** (`str`): API 描述 (可选, 用于文档)
- **tags** (`list[str]`): API 标签 (可选, 用于文档分组)
- **response_model** (`type`): 响应模型 (可选)
- **deprecated** (`bool`): 是否废弃 (可选)
**返回值** (`Callable`): 装饰器

**示例**:
```python
>>> @sdk.router.http("MyModule", "/api/data", methods=["GET", "POST"])
... async def handle_data(request):
...     return {"ok": True}
```

---


##### `get(module_name: str, path: str)`

GET 路由装饰器

- **module_name** (`str`): 模块名称 (必填)
- **path** (`str`): 路由路径
**返回值** (`Callable`): 装饰器

---


##### `post(module_name: str, path: str)`

POST 路由装饰器

- **module_name** (`str`): 模块名称 (必填)
- **path** (`str`): 路由路径
**返回值** (`Callable`): 装饰器

---


##### `put(module_name: str, path: str)`

PUT 路由装饰器

- **module_name** (`str`): 模块名称 (必填)
- **path** (`str`): 路由路径
**返回值** (`Callable`): 装饰器

---


##### `delete(module_name: str, path: str)`

DELETE 路由装饰器

- **module_name** (`str`): 模块名称 (必填)
- **path** (`str`): 路由路径
**返回值** (`Callable`): 装饰器

---


##### `ws(module_name: str, path: str)`

WebSocket 路由装饰器

- **module_name** (`str`): 模块名称 (必填)
- **path** (`str`): WebSocket 路径
- **auth_handler** (`Callable`): 认证函数 (可选)
- **auto_accept** (`bool`): 是否自动 accept (默认: True)

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

- **module_name** (`str`): 模块名称 (必填)
- **path** (`str`): SSE 端点路径
- **summary** (`str`): API 摘要 (可选)
- **description** (`str`): API 描述 (可选)
- **tags** (`list[str]`): API 标签 (可选)

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

- **module_name** (`str`): 模块名称
- **path** (`str`): 路由路径
- **handler** (`Callable`): 处理函数
- **methods** (`list[str]`): HTTP方法列表(默认["POST"])
- **rate_limit** (`str|dict|None`): 限流规则 (可选, 如 "10/minute")
- **summary** (`str`): API 摘要 (可选)
- **description** (`str`): API 描述 (可选)
- **tags** (`list[str]`): API 标签 (可选)
- **response_model** (`type`): 响应模型 (可选)
- **deprecated** (`bool`): 是否废弃 (可选)

**异常**: `ValueError` - 当路径和方法都已注册时抛出

---


##### `register_webhook()`

兼容性方法：注册HTTP路由（适配器旧接口）

---


##### `unregister_http_route(module_name: str, path: str)`

取消注册HTTP路由

- **module_name** (`模块名称`): - **path**: 路由路径
**返回值** (`bool`): 是否成功取消注册

---


##### `_make_ws_endpoint_fn(full_path: str, module_name: str, wrapped_handler: Callable, wrapped_auth: Callable | None, auto_accept: bool)`

> **内部方法**
构建 WebSocket 端点处理函数（注册与恢复路由共用同一实现）

- **full_path** (`完整路由路径`): - **module_name**: 模块名
- **wrapped_handler** (`已包装的`): WebSocket 处理器
- **wrapped_auth** (`已包装的鉴权处理器（可为`): None）
- **auto_accept** (`是否自动`): accept 连接
**返回值** (`WebSocket`): 端点协程函数

---


##### `_register_ws_endpoint(full_path: str, module_name: str, handler: Callable[[WebSocket], Awaitable[Any]], auth_handler: Callable[[WebSocket], Awaitable[bool]] | None = None, auto_accept: bool = DEFAULT_WS_AUTO_ACCEPT)`

WebSocket 路由注册内部实现

> **内部方法**

---


##### `register_websocket(module_name: str, path: str, handler: Callable[[WebSocket], Awaitable[Any]], auth_handler: Callable[[WebSocket], Awaitable[bool]] | None = None, auto_accept: bool = True)`

注册WebSocket路由

- **module_name** (`str`): 模块名称
- **path** (`str`): WebSocket路径
- **handler** (`Callable[[WebSocket],`): Awaitable[Any]] 主处理函数
- **auth_handler** (`Optional[Callable[[WebSocket],`): Awaitable[bool]]] 认证函数
- **auto_accept** (`bool`): 是否自动调用 websocket.accept()，默认 True

> **提示**
> 推荐使用 auth_handler 进行连接确认，而非关闭 auto_accept。
> auth_handler 在连接建立后执行，返回 False 会自动关闭连接。
> 仅在需要完全控制连接流程时才设置 auto_accept=False。

**异常**: `ValueError` - 当路径已注册时抛出

---


##### `unregister_websocket(module_name: str, path: str)`

取消注册WebSocket路由

- **module_name** (`模块名称`): - **path**: WebSocket路径
**返回值** (`bool`): 是否成功取消注册

---


##### `register_sse(module_name: str, path: str, handler: Callable)`

注册 SSE (Server-Sent Events) 路由

SSE 路由为 HTTP GET 端点，返回 ``text/event-stream`` 流式响应。
处理器接收 ``SseEmitter`` 实例（以及可选的 ``HttpRequest``），
通过 ``sse.send()`` 推送事件，调用 ``sse.close()`` 断开连接。

- **module_name** (`str`): 模块名称
- **path** (`str`): SSE 端点路径
- **handler** (`Callable`): 事件处理器, 签名: ``async def handler(sse)`` 或 ``async def handler(request, sse)``

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

- **module_name** (`模块名称`): - **path**: SSE 路径
**返回值** (`bool`): 是否成功取消注册

---


##### `unregister_all_by_namespace(namespace: str)`

清理指定命名空间下的所有路由

- **namespace** (`命名空间（适配器名或模块名）`): **返回值** (`dict`): 清理统计 {"http_count": int, "websocket_count": int, "sse_count": int}

---


##### `unregister_all_by_owner(owner: str)`

清理指定归属者注册的所有路由

与 :meth:`unregister_all_by_namespace` 不同，本方法基于注册期间
通过 ``current_owner`` 自动追踪的归属关系进行清理，适用于"以平台名
为 owner、却用更细颗粒度命名空间（如 ``onebot11_default``）注册路由"
的适配器热重载场景。

- **owner** (`归属者（适配器平台名或模块名）`): **返回值** (`dict`): 清理统计 {"http_count": int, "websocket_count": int, "sse_count": int}

---


##### `list_namespaces()`

列出所有已注册的命名空间及其路由

**返回值** (`dict`): {namespace: {"http": [paths], "websocket": [paths], "sse": [paths]}}

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

- **module_name** (`模块/平台名称`): **返回值** (`{"http":`): [...], "websocket": [...], "sse": [...]}
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

- **module_name** (`模块/平台名称`): **返回值** (`{`): "base_url": str,
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

- **prefix** (`命名空间前缀（如`): "yunhu"）
**返回值** (`{`): "base_url": str,
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

- **module_name** (`str`): 模块名称 (必填)
- **prefix** (`str`): 路由前缀
- **version** (`str`): 版本号 (可选)
- **tags** (`list[str]`): API 标签 (可选)
- **middlewares** (`list`): 分组中间件 (可选)
**返回值** (`RouteGroup`): 路由分组实例

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

- **limit** (`str|dict`): 限流规则
**返回值** (`tuple[int,`): int] (max_requests, window_seconds)

> **内部方法**

---


##### `setup_cors(allow_origins: list[str] | None = None, allow_methods: list[str] | None = None, allow_headers: list[str] | None = None, allow_credentials: bool = False, max_age: int = DEFAULT_CORS_MAX_AGE_SECS, expose_headers: list[str] | None = None)`

配置 CORS

- **allow_origins** (`list[str]`): 允许的来源 (默认: ["*"])
- **allow_methods** (`list[str]`): 允许的方法 (默认: ["*"])
- **allow_headers** (`list[str]`): 允许的头 (默认: ["*"])
- **allow_credentials** (`bool`): 允许凭据 (默认: False)
- **max_age** (`int`): 预检缓存时间 (默认: 600)
- **expose_headers** (`list[str]`): 暴露的响应头 (可选)

**示例**:
```python
>>> sdk.router.setup_cors(
...     allow_origins=["https://example.com"],
...     allow_methods=["GET", "POST"],
... )
```

---


##### `setup_security_headers(headers: dict[str, str] | None = None)`

配置安全响应头

- **headers** (`dict[str,`): str] 自定义安全头 (可选, 会合并默认值)

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


##### `set_docs_info(title: str | None = None, description: str | None = None)`

更新 API 文档信息

- **title** (`str`): 文档标题 (可选)
- **description** (`str`): 文档描述 (可选)

---


##### `_apply_config()`

从配置文件自动应用 CORS 和安全头

> **内部方法**

---


##### `_on_router_config_changed(_data: dict)`

router 中间件配置变更回调：CORS/安全头需重启进程才能生效

---


##### `get_app()`

获取FastAPI应用实例

**返回值** (`FastAPI`): 应用实例

---


##### `_get_local_ips()`

获取本机局域网IP地址

> **内部方法**

---


##### `async start(host: str = DEFAULT_SERVER_HOST, port: int = DEFAULT_SERVER_PORT, ssl_certfile: str | None = None, ssl_keyfile: str | None = None)`

启动路由服务器

- **host** (`str`): 监听地址(默认"0.0.0.0")
- **port** (`int`): 监听端口(默认8000)
- **ssl_certfile** (`str`): | None SSL证书路径
- **ssl_keyfile** (`str`): | None SSL密钥路径

**异常**: `RuntimeError` - 当服务器已在运行时抛出

.. note::
    端口被占用时不视为致命错误：服务器不启动，但机器人继续运行。

---


##### `_check_port_available(host: str, port: int)`

检测端口是否被占用（有进程正在监听）

使用 ``connect`` 而非 ``bind`` 探测：``bind`` 会因上次进程退出后的
``TIME_WAIT`` 残留而误判端口被占用，导致重启死循环；``connect`` 只在
端口有活跃监听者时才成功，能准确区分"真正占用"与"TIME_WAIT 残留"。

- **host** (`str`): 监听地址
- **port** (`int`): 监听端口

**异常**: `RuntimeError` - 当端口被占用时抛出，携带友好的错误提示

---


##### `_start_rate_limit_cleanup()`

> **内部方法**
启动限流存储的定期清理后台任务

定期扫描 _rate_limit_store，移除窗口已过期的 IP 记录，防止长期运行时无限增长。

---


##### `_stop_rate_limit_cleanup()`

> **内部方法**
停止限流存储定期清理任务

---


##### `_cleanup_expired_rate_limits()`

> **内部方法**
清除过期的限流记录

扫描 _rate_limit_store，移除所有时间戳均已超出限流窗口的条目。

**返回值** (`int`): 被清除的条目数

---


##### `async stop()`

停止服务器并清理所有路由

---


##### `_format_display_url(url: str)`

格式化URL显示

- **url** (`str`): 原始URL
**返回值** (`str`): 格式化后的URL

---

