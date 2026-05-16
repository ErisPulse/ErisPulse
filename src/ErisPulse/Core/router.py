"""
ErisPulse 路由系统

提供统一的HTTP和WebSocket路由管理，支持多适配器路由注册和生命周期管理。
增强功能: 装饰器路由、路由中间件、自动文档、路由限流、分组/版本管理、CORS/安全头

{!--< tips >!--}
1. 使用 @http / @get / @post / @ws 装饰器快速注册路由
2. module_name 为必填第一个参数，决定路径前缀
3. 支持 route group 进行版本管理和路由分组
4. 支持 CORS 和安全响应头配置化
{!--< /tips >!--}
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response
from fastapi.routing import APIRoute
from typing import Any, TypeAlias
from collections.abc import Callable, Awaitable
from collections import defaultdict
from .logger import logger
from .lifecycle import lifecycle
import asyncio
import functools
import inspect
import socket
import ipaddress
import sys
import time
import importlib.metadata
from datetime import datetime, timezone
import uvicorn

ERISPULSE_VERSION = "UnknownVersion"

try:
    ERISPULSE_VERSION = importlib.metadata.version("ErisPulse")
except importlib.metadata.PackageNotFoundError:
    pass

HTTPHandler: TypeAlias = Callable
WebSocketHandler: TypeAlias = Callable[[WebSocket], Awaitable[Any]]
RoutePath: TypeAlias = str


class FuncMiddleware:
    """
    函数式路由中间件包装

    {!--< internal-use >!--}
    {!--< /internal-use >!--}
    """

    def __init__(self, before: Callable = None, after: Callable = None):
        self._before = before
        self._after = after


class RouteGroup:
    """
    路由分组

    {!--< tips >!--}
    通过 sdk.router.group() 创建，支持版本前缀和嵌套分组
    {!--< /tips >!--}

    :example:
    >>> api = sdk.router.group("MyModule", "/api", version="1", tags=["API"])
    >>> @api.get("/users")
    ... async def users(request):
    ...     return {"users": []}
    """

    def __init__(self, module_name: str, prefix: str,
                 version: str = None, tags: list[str] = None,
                 middlewares: list = None, router: "RouterManager" = None):
        """
        初始化路由分组

        :param module_name: str 模块名称 (路径前缀)
        :param prefix: str 路由前缀
        :param version: str 版本号 (可选, 如 "1")
        :param tags: list[str] API 文档标签 (可选)
        :param middlewares: list 分组级中间件 (可选)
        :param router: RouterManager 路由管理器实例
        """
        self._module_name = module_name
        self._prefix = prefix
        self._version = version
        self._tags = tags or []
        self._middlewares = middlewares or []
        self._router = router

    def _resolve_path(self, path: str) -> str:
        """
        解析完整路径

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        parts = []
        if self._version:
            parts.append(f"v{self._version}")
        p = self._prefix.strip("/")
        if p:
            parts.append(p)
        sub = path.strip("/")
        if sub:
            parts.append(sub)
        return self._router._normalize_path(self._module_name, "/" + "/".join(parts))

    def http(self, path: str, methods: list[str] = None, **kwargs):
        """
        HTTP 路由装饰器

        :param path: str 路由路径
        :param methods: list[str] HTTP 方法列表 (默认: ["POST"])
        :return: Callable 装饰器
        """
        resolved = self._resolve_path(path)
        kw = dict(kwargs)
        if self._tags and "tags" not in kw:
            kw["tags"] = self._tags
        if self._middlewares and "middlewares" not in kw:
            kw["middlewares"] = self._middlewares
        return self._router._http_decorate(resolved, self._module_name, methods, **kw)

    def get(self, path: str, **kwargs):
        """
        GET 路由装饰器

        :param path: str 路由路径
        :return: Callable 装饰器
        """
        return self.http(path, methods=["GET"], **kwargs)

    def post(self, path: str, **kwargs):
        """
        POST 路由装饰器

        :param path: str 路由路径
        :return: Callable 装饰器
        """
        return self.http(path, methods=["POST"], **kwargs)

    def put(self, path: str, **kwargs):
        """
        PUT 路由装饰器

        :param path: str 路由路径
        :return: Callable 装饰器
        """
        return self.http(path, methods=["PUT"], **kwargs)

    def delete(self, path: str, **kwargs):
        """
        DELETE 路由装饰器

        :param path: str 路由路径
        :return: Callable 装饰器
        """
        return self.http(path, methods=["DELETE"], **kwargs)

    def ws(self, path: str, **kwargs):
        """
        WebSocket 路由装饰器

        :param path: str 路由路径
        :param auth_handler: Callable 认证函数 (可选)
        :param auto_accept: bool 是否自动 accept (默认: True)
        """
        resolved = self._resolve_path(path)
        return self._router._ws_decorate(resolved, self._module_name, **kwargs)

    def group(self, prefix: str, **kwargs) -> "RouteGroup":
        """
        创建嵌套分组

        :param prefix: str 子路由前缀
        :return: RouteGroup 嵌套分组实例

        :example:
        >>> api = sdk.router.group("MyModule", "/api", version="1")
        >>> users = api.group("/users")
        >>> @users.get("/")
        ... async def list_users(request):
        ...     ...
        """
        new_prefix = f"{self._prefix.rstrip('/')}/{prefix.strip('/')}"
        return RouteGroup(
            self._module_name, new_prefix,
            version=kwargs.pop("version", self._version),
            tags=kwargs.pop("tags", self._tags),
            middlewares=kwargs.pop("middlewares", self._middlewares),
            router=self._router,
        )


class RouterManager:
    """
    路由管理器

    {!--< tips >!--}
    核心功能:
    - HTTP/WebSocket 路由注册
    - 路由中间件 (前/后置处理)
    - 自动 OpenAPI 文档 (/docs, /redoc)
    - 路由限流 (rate_limit 参数)
    - 路由分组/版本管理
    - CORS / 安全头配置化
    {!--< /tips >!--}
    """

    def __init__(self):
        """
        初始化路由管理器

        {!--< tips >!--}
        会自动创建 FastAPI 实例并设置核心路由
        {!--< /tips >!--}
        """
        self.app = FastAPI(
            title="ErisPulse Router", description="统一路由管理入口点",
            version=ERISPULSE_VERSION,
        )
        # HTTP路由：{module_name: {path: {method: handler}}}
        self._http_routes: dict[str, dict[str, dict[str, Callable]]] = defaultdict(dict)
        self._websocket_routes: dict[
            str, dict[str, tuple[Callable, Callable | None]]
        ] = defaultdict(dict)
        self.base_url = ""
        self._server_task: asyncio.Task | None = None
        self._uvicorn_server: uvicorn.Server | None = None
        self._local_ips: list[dict[str, str]] = []
        self._route_middlewares: dict[str, list] = defaultdict(list)
        self._global_middlewares: list = []
        self._rate_limit_store: dict[str, list[float]] = {}
        self._middleware_installed = False
        self._setup_core_routes()

    def _normalize_path(self, prefix: str, path: str) -> str:
        """
        标准化路径，确保格式正确

        :param prefix: str 路径前缀（如模块名）
        :param path: str 路径部分
        :return: str 标准化后的完整路径

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        # 去除首尾斜杠并合并
        parts = [part.strip("/") for part in [prefix, path] if part.strip("/")]
        return "/" + "/".join(parts)

    def _setup_core_routes(self) -> None:
        """
        设置系统核心路由

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """

        @self.app.get("/health")
        async def health_check() -> dict[str, str]:
            """
            健康检查端点

            :return: dict[str, str] 包含服务状态和版本信息
            """
            return {
                "status": "ok",
                "service": "ErisPulse Router",
                "version": ERISPULSE_VERSION,
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            }

        @self.app.get("/ping")
        async def ping() -> dict[str, Any]:
            """
            连通性检查端点

            :return: dict[str, Any] 包含响应状态和时间戳
            """
            return {"pong": True, "timestamp": datetime.now(timezone.utc).isoformat()}

    # 路由中间件 

    def _ensure_middleware_installed(self):
        """
        确保 FastAPI 级中间件已安装

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        if self._middleware_installed:
            return
        self._middleware_installed = True

        @self.app.middleware("http")
        async def route_middleware_pipeline(request: Request, call_next):
            path = request.url.path

            for mw in self._global_middlewares:
                if mw._before:
                    result = await mw._before(request) if inspect.iscoroutinefunction(mw._before) else mw._before(request)
                    if isinstance(result, Response):
                        return result

            for pattern, mws in self._route_middlewares.items():
                if self._match_path(pattern, path):
                    for mw in mws:
                        if mw._before:
                            result = await mw._before(request) if inspect.iscoroutinefunction(mw._before) else mw._before(request)
                            if isinstance(result, Response):
                                return result

            response = await call_next(request)

            for pattern, mws in reversed(list(self._route_middlewares.items())):
                if self._match_path(pattern, path):
                    for mw in reversed(mws):
                        if mw._after:
                            resp = await mw._after(request, response) if inspect.iscoroutinefunction(mw._after) else mw._after(request, response)
                            if resp is not None:
                                response = resp

            for mw in reversed(self._global_middlewares):
                if mw._after:
                    resp = await mw._after(request, response) if inspect.iscoroutinefunction(mw._after) else mw._after(request, response)
                    if resp is not None:
                        response = resp

            return response

    def middleware(self, *paths: str):
        """
        路由中间件装饰器

        :param paths: str 路径匹配模式 (支持通配符), 留空则为全局中间件
        :return: Callable 装饰器

        {!--< tips >!--}
        前置中间件签名: (request) -> request | Response
        后置中间件签名: (request, response) -> response
        根据函数参数数量自动判断是前置还是后置
        paths 参数为 glob 模式路径匹配，如 "/MyModule/*"，而非 (module_name, pattern)
        {!--< /tips >!--}

        :example:
        >>> @sdk.router.middleware()
        ... async def log_all(request):
        ...     return request
        >>>
        >>> @sdk.router.middleware("/MyModule/api/*")
        ... async def auth_check(request):
        ...     return request
        """
        self._ensure_middleware_installed()

        def decorator(func):
            sig = inspect.signature(func)
            params = list(sig.parameters.keys())
            is_after = len(params) >= 2 and "response" in params
            mw = FuncMiddleware(after=func) if is_after else FuncMiddleware(before=func)

            if paths:
                for p in paths:
                    self._route_middlewares[p].append(mw)
            else:
                self._global_middlewares.append(mw)
            return func
        return decorator

    def add_middleware(self, before: Callable = None, after: Callable = None,
                      *paths: str):
        """
        添加中间件函数

        :param before: Callable 前置中间件 (可选)
        :param after: Callable 后置中间件 (可选)
        :param paths: str 路径匹配模式, 留空为全局
        """
        self._ensure_middleware_installed()
        mw = FuncMiddleware(before=before, after=after)
        if paths:
            for p in paths:
                self._route_middlewares[p].append(mw)
        else:
            self._global_middlewares.append(mw)

    @staticmethod
    def _match_path(pattern: str, path: str) -> bool:
        """
        通配符路径匹配

        :param pattern: str 匹配模式
        :param path: str 实际路径
        :return: bool 是否匹配

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        if pattern == "*":
            return True
        if pattern.endswith("/**"):
            prefix = pattern[:-3]
            return path == prefix or path.startswith(prefix + "/")
        if pattern.endswith("/*"):
            prefix = pattern[:-2]
            return path.startswith(prefix + "/")
        return pattern == path

    # 装饰器路由

    def _http_decorate(self, full_path: str, module_name: str,
                       methods: list[str] = None, **kwargs):
        """
        HTTP 路由装饰器内部实现

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        def decorator(func):
            resolved_methods = methods or ["POST"]
            route_kwargs = {}
            for k in ("summary", "description", "tags", "response_model", "deprecated"):
                if k in kwargs and kwargs[k] is not None:
                    route_kwargs[k] = kwargs[k]

            route = APIRoute(
                path=full_path, endpoint=func, methods=resolved_methods,
                name=f"{module_name}_{full_path.replace('/', '_')}",
                **route_kwargs,
            )
            self.app.router.routes.append(route)

            for m in resolved_methods:
                self._http_routes[module_name].setdefault(full_path, {})[m] = func

            rate_limit = kwargs.get("rate_limit")
            if rate_limit:
                self._apply_rate_limit(full_path, rate_limit)

            logger.info(f"[{module_name}] 注册HTTP路由: {full_path} 方法: {resolved_methods}")
            return func
        return decorator

    def _ws_decorate(self, full_path: str, module_name: str, **kwargs):
        """
        WebSocket 路由装饰器内部实现

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        def decorator(func):
            auth_handler = kwargs.get("auth_handler")
            auto_accept = kwargs.get("auto_accept", True)
            self._register_ws_endpoint(full_path, module_name, func, auth_handler, auto_accept)
            return func
        return decorator

    def http(self, module_name: str, path: str,
             methods: list[str] = None, **kwargs):
        """
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

        :example:
        >>> @sdk.router.http("MyModule", "/api/data", methods=["GET", "POST"])
        ... async def handle_data(request):
        ...     return {"ok": True}
        """
        full_path = self._normalize_path(module_name, path)
        return self._http_decorate(full_path, module_name, methods, **kwargs)

    def get(self, module_name: str, path: str, **kwargs):
        """
        GET 路由装饰器

        :param module_name: str 模块名称 (必填)
        :param path: str 路由路径
        :return: Callable 装饰器
        """
        return self.http(module_name, path, methods=["GET"], **kwargs)

    def post(self, module_name: str, path: str, **kwargs):
        """
        POST 路由装饰器

        :param module_name: str 模块名称 (必填)
        :param path: str 路由路径
        :return: Callable 装饰器
        """
        return self.http(module_name, path, methods=["POST"], **kwargs)

    def put(self, module_name: str, path: str, **kwargs):
        """
        PUT 路由装饰器

        :param module_name: str 模块名称 (必填)
        :param path: str 路由路径
        :return: Callable 装饰器
        """
        return self.http(module_name, path, methods=["PUT"], **kwargs)

    def delete(self, module_name: str, path: str, **kwargs):
        """
        DELETE 路由装饰器

        :param module_name: str 模块名称 (必填)
        :param path: str 路由路径
        :return: Callable 装饰器
        """
        return self.http(module_name, path, methods=["DELETE"], **kwargs)

    def ws(self, module_name: str, path: str, **kwargs):
        """
        WebSocket 路由装饰器

        :param module_name: str 模块名称 (必填)
        :param path: str WebSocket 路径
        :param auth_handler: Callable 认证函数 (可选)
        :param auto_accept: bool 是否自动 accept (默认: True)

        {!--< tips >!--}
        推荐使用 auth_handler 进行连接确认，而非关闭 auto_accept。
        仅在需要完全控制连接流程时才设置 auto_accept=False。
        {!--< /tips >!--}

        :example:
        >>> @sdk.router.ws("MyModule", "/ws/chat")
        ... async def chat(websocket):
        ...     await websocket.send_text("Hello!")
        """
        full_path = self._normalize_path(module_name, path)
        return self._ws_decorate(full_path, module_name, **kwargs)

    # 传统注册 API

    def register_http_route(
        self,
        module_name: str,
        path: str,
        handler: Callable,
        methods: list[str] | None = None,
        rate_limit: str | dict | None = None,
        summary: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
        response_model: type | None = None,
        deprecated: bool | None = None,
    ) -> None:
        """
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

        :raises ValueError: 当路径和方法都已注册时抛出
        """
        if methods is None:
            methods = ["POST"]
        full_path = self._normalize_path(module_name, path)

        # 检查是否有冲突的方法
        conflicting_methods = []
        if full_path in self._http_routes[module_name]:
            for method in methods:
                if method in self._http_routes[module_name][full_path]:
                    conflicting_methods.append(method)

        if conflicting_methods:
            raise ValueError(f"路径 {full_path} 的方法 {conflicting_methods} 已注册")

        route_kwargs = {}
        for k, v in [("summary", summary), ("description", description),
                      ("tags", tags), ("response_model", response_model),
                      ("deprecated", deprecated)]:
            if v is not None:
                route_kwargs[k] = v

        # 创建路由
        route = APIRoute(
            path=full_path,
            endpoint=handler,
            methods=methods,
            name=f"{module_name}_{path.replace('/', '_')}_{methods[0].lower()}",
            **route_kwargs,
        )
        self.app.router.routes.append(route)

        # 按方法存储处理器
        if full_path not in self._http_routes[module_name]:
            self._http_routes[module_name][full_path] = {}

        for method in methods:
            self._http_routes[module_name][full_path][method] = handler

        if rate_limit:
            self._apply_rate_limit(full_path, rate_limit)

        logger.info(f"[{module_name}] 注册HTTP路由: {full_path} 方法: {methods}")

    def register_webhook(self, *args, **kwargs) -> None:
        """
        兼容性方法：注册HTTP路由（适配器旧接口）
        """
        return self.register_http_route(*args, **kwargs)

    def unregister_http_route(self, module_name: str, path: str) -> bool:
        """
        取消注册HTTP路由

        :param module_name: 模块名称
        :param path: 路由路径
        :return: bool 是否成功取消注册
        """
        try:
            full_path = self._normalize_path(module_name, path)
            if full_path not in self._http_routes[module_name]:
                logger.debug(f"\n取消注册的路由不存在: {full_path}\n")
                return False

            # 获取所有方法
            methods = list(self._http_routes[module_name][full_path].keys())
            logger.info(f"注销HTTP路由: {full_path} 方法: {methods}")
            del self._http_routes[module_name][full_path]

            # 从路由列表中移除匹配的路由
            self.app.router.routes = [
                route
                for route in self.app.router.routes
                if not (isinstance(route, APIRoute) and route.path == full_path)
            ]

            return True
        except Exception as e:
            logger.error(f"取消注册HTTP路由失败: {e}")
            return False

    def _register_ws_endpoint(self, full_path: str, module_name: str,
                               handler: Callable[[WebSocket], Awaitable[Any]],
                               auth_handler: Callable[[WebSocket], Awaitable[bool]] | None = None,
                               auto_accept: bool = True) -> None:
        """
        WebSocket 路由注册内部实现

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        if full_path in self._websocket_routes[module_name]:
            raise ValueError(f"WebSocket路径 {full_path} 已注册")

        async def websocket_endpoint(websocket: WebSocket) -> None:
            """
            WebSocket端点包装器

            {!--< internal-use >!--}
            {!--< /internal-use >!--}
            """
            # 根据 auto_accept 参数决定是否自动 accept
            if auto_accept:
                await websocket.accept()

            try:
                if auth_handler and not await auth_handler(websocket):
                    await websocket.close(code=1008)
                    return

                await handler(websocket)

            except WebSocketDisconnect:
                logger.debug(f"客户端断开: {full_path}")
            except Exception as e:
                logger.error(f"WebSocket错误: {e}")
                await websocket.close(code=1011)

        self.app.add_api_websocket_route(
            path=full_path,
            endpoint=websocket_endpoint,
            name=f"{module_name}_{full_path.replace('/', '_')}",
        )
        self._websocket_routes[module_name][full_path] = (handler, auth_handler)

        logger.info(
            f"[{module_name}] 注册WebSocket: {full_path}{'(需认证)' if auth_handler else ''}"
        )

    def register_websocket(
        self,
        module_name: str,
        path: str,
        handler: Callable[[WebSocket], Awaitable[Any]],
        auth_handler: Callable[[WebSocket], Awaitable[bool]] | None = None,
        auto_accept: bool = True,
    ) -> None:
        """
        注册WebSocket路由

        :param module_name: str 模块名称
        :param path: str WebSocket路径
        :param handler: Callable[[WebSocket], Awaitable[Any]] 主处理函数
        :param auth_handler: Optional[Callable[[WebSocket], Awaitable[bool]]] 认证函数
        :param auto_accept: bool 是否自动调用 websocket.accept()，默认 True

        {!--< tips >!--}
        推荐使用 auth_handler 进行连接确认，而非关闭 auto_accept。
        auth_handler 在连接建立后执行，返回 False 会自动关闭连接。
        仅在需要完全控制连接流程时才设置 auto_accept=False。
        {!--< /tips >!--}

        :raises ValueError: 当路径已注册时抛出
        """
        full_path = self._normalize_path(module_name, path)
        self._register_ws_endpoint(full_path, module_name, handler, auth_handler, auto_accept)

    def unregister_websocket(self, module_name: str, path: str) -> bool:
        """
        取消注册WebSocket路由

        :param module_name: 模块名称
        :param path: WebSocket路径
        :return: bool 是否成功取消注册
        """
        try:
            full_path = self._normalize_path(module_name, path)

            # 检查 WebSocket 路由是否存在于我们的内部记录中
            if (
                ws_routes := self._websocket_routes.get(module_name)
            ) and full_path in ws_routes:
                logger.info(f"注销WebSocket: {full_path}")
                del ws_routes[full_path]

                # 从 FastAPI 路由列表中移除对应的 WebSocket 路由
                # FastAPI 的 WebSocket 路由有 websocket_endpoint 属性
                self.app.router.routes = [
                    route
                    for route in self.app.router.routes
                    if not (hasattr(route, "path") and route.path == full_path)
                ]
                return True

            logger.debug(f"\n取消注册的路由不存在: {full_path}\n")
            return False
        except Exception as e:
            logger.error(f"注销WebSocket失败: {e}")
            return False

    def unregister_all_by_namespace(self, namespace: str) -> dict[str, int]:
        """
        清理指定命名空间下的所有路由

        :param namespace: 命名空间（适配器名或模块名）
        :return: dict 清理统计 {"http_count": int, "websocket_count": int}
        """
        result = {"http_count": 0, "websocket_count": 0}
        
        # 清理 HTTP 路由
        if namespace in self._http_routes:
            paths = list(self._http_routes[namespace].keys())
            for path in paths:
                if self.unregister_http_route(namespace, path):
                    result["http_count"] += 1
            # 清理空命名空间
            if namespace in self._http_routes:
                del self._http_routes[namespace]
        
        # 清理 WebSocket 路由
        if namespace in self._websocket_routes:
            paths = list(self._websocket_routes[namespace].keys())
            for path in paths:
                if self.unregister_websocket(namespace, path):
                    result["websocket_count"] += 1
            # 清理空命名空间
            if namespace in self._websocket_routes:
                del self._websocket_routes[namespace]

        if result["http_count"] > 0 or result["websocket_count"] > 0:
            logger.info(
                f"已清理命名空间 [{namespace}] 的路由: "
                f"HTTP={result['http_count']}, WebSocket={result['websocket_count']}"
            )

        return result

    def list_namespaces(self) -> dict[str, dict[str, list[str]]]:
        """
        列出所有已注册的命名空间及其路由

        :return: dict {namespace: {"http": [paths], "websocket": [paths]}}

        :example:
        >>> router.list_namespaces()
        {
            "onebot11": {
                "http": ["/onebot11/webhook", "/onebot11/callback"],
                "websocket": ["/onebot11/ws"]
            }
        }
        """
        result = {}

        for namespace, routes in self._http_routes.items():
            if namespace not in result:
                result[namespace] = {"http": [], "websocket": []}
            result[namespace]["http"] = list(routes.keys())

        for namespace, routes in self._websocket_routes.items():
            if namespace not in result:
                result[namespace] = {"http": [], "websocket": []}
            result[namespace]["websocket"] = list(routes.keys())

        return result

    # 路由分组

    def group(self, module_name: str, prefix: str, **kwargs) -> RouteGroup:
        """
        创建路由分组

        :param module_name: str 模块名称 (必填)
        :param prefix: str 路由前缀
        :param version: str 版本号 (可选)
        :param tags: list[str] API 标签 (可选)
        :param middlewares: list 分组中间件 (可选)
        :return: RouteGroup 路由分组实例

        :example:
        >>> api = sdk.router.group("MyModule", "/api", version="1")
        >>> @api.get("/users")
        ... async def users(request):
        ...     return {"users": []}
        """
        return RouteGroup(module_name, prefix, router=self, **kwargs)

    # 路由限流

    def _apply_rate_limit(self, full_path: str, limit: str | dict):
        """
        为路由应用限流

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        max_requests, window = self._parse_rate_limit(limit)

        self._ensure_middleware_installed()

        async def rate_limit_check(request: Request):
            client_ip = request.client.host if request.client else "unknown"
            key = f"route:{full_path}:{client_ip}"
            now = time.monotonic()

            if key not in self._rate_limit_store:
                self._rate_limit_store[key] = []

            self._rate_limit_store[key] = [t for t in self._rate_limit_store[key] if now - t < window]

            if len(self._rate_limit_store[key]) >= max_requests:
                retry_after = window - (now - self._rate_limit_store[key][0])
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    {"error": "Rate limit exceeded", "retry_after": int(retry_after)},
                    status_code=429,
                    headers={"Retry-After": str(int(retry_after))},
                )

            self._rate_limit_store[key].append(now)
            return request

        mw = FuncMiddleware(before=rate_limit_check)
        self._route_middlewares[full_path].append(mw)

    @staticmethod
    def _parse_rate_limit(limit: str | dict) -> tuple[int, int]:
        """
        解析限流规则

        :param limit: str|dict 限流规则
        :return: tuple[int, int] (max_requests, window_seconds)

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        if isinstance(limit, dict):
            return int(limit.get("requests", 10)), int(limit.get("window", 60))

        parts = limit.split("/")
        count = int(parts[0])
        unit = parts[1].lower() if len(parts) > 1 else "m"

        multipliers = {
            "s": 1, "second": 1, "seconds": 1,
            "m": 60, "minute": 60, "minutes": 60,
            "h": 3600, "hour": 3600, "hours": 3600,
        }
        return count, multipliers.get(unit, 60)

    # CORS / 安全头

    def setup_cors(self, allow_origins: list[str] = None,
                   allow_methods: list[str] = None,
                   allow_headers: list[str] = None,
                   allow_credentials: bool = False,
                   max_age: int = 600,
                   expose_headers: list[str] = None):
        """
        配置 CORS

        :param allow_origins: list[str] 允许的来源 (默认: ["*"])
        :param allow_methods: list[str] 允许的方法 (默认: ["*"])
        :param allow_headers: list[str] 允许的头 (默认: ["*"])
        :param allow_credentials: bool 允许凭据 (默认: False)
        :param max_age: int 预检缓存时间 (默认: 600)
        :param expose_headers: list[str] 暴露的响应头 (可选)

        :example:
        >>> sdk.router.setup_cors(
        ...     allow_origins=["https://example.com"],
        ...     allow_methods=["GET", "POST"],
        ... )
        """
        from fastapi.middleware.cors import CORSMiddleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=allow_origins or ["*"],
            allow_methods=allow_methods or ["*"],
            allow_headers=allow_headers or ["*"],
            allow_credentials=allow_credentials,
            max_age=max_age,
            expose_headers=expose_headers or [],
        )
        logger.info("已配置 CORS 中间件")

    def setup_security_headers(self, headers: dict[str, str] = None):
        """
        配置安全响应头

        :param headers: dict[str, str] 自定义安全头 (可选, 会合并默认值)

        :example:
        >>> sdk.router.setup_security_headers({
        ...     "Strict-Transport-Security": "max-age=31536000",
        ... })
        """
        defaults = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
        }
        final = {**defaults, **(headers or {})}

        @self.app.middleware("http")
        async def add_security_headers(request: Request, call_next):
            response = await call_next(request)
            for k, v in final.items():
                response.headers[k] = v
            return response

        logger.info("已配置安全响应头")

    def disable_docs(self):
        """
        关闭 API 文档端点（生产环境推荐）

        :example:
        >>> sdk.router.disable_docs()
        """
        self.app.docs_url = None
        self.app.redoc_url = None
        self.app.openapi_url = None

    def set_docs_info(self, title: str = None, description: str = None):
        """
        更新 API 文档信息

        :param title: str 文档标题 (可选)
        :param description: str 文档描述 (可选)
        """
        if title:
            self.app.title = title
        if description:
            self.app.description = description

    def _apply_config(self):
        """
        从配置文件自动应用 CORS 和安全头

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        try:
            from .config import config
            cors = config.getConfig("ErisPulse.router.cors")
            if cors and cors.get("enabled"):
                self.setup_cors(
                    allow_origins=cors.get("allow_origins", ["*"]),
                    allow_methods=cors.get("allow_methods", ["*"]),
                    allow_headers=cors.get("allow_headers", ["*"]),
                    allow_credentials=cors.get("allow_credentials", False),
                    max_age=cors.get("max_age", 600),
                )

            security = config.getConfig("ErisPulse.router.security")
            if security and security.get("enabled"):
                self.setup_security_headers(security.get("headers"))
        except Exception as e:
            logger.debug(f"应用路由配置失败: {e}")

    # ==================== 服务器管理 ====================

    def get_app(self) -> FastAPI:
        """
        获取FastAPI应用实例

        :return: FastAPI 应用实例
        """
        return self.app

    def _get_local_ips(self) -> None:
        """
        获取本机局域网IP地址

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        self._local_ips = []

        try:
            seen = set()
            for family, _, _, _, (ip, *_) in socket.getaddrinfo(
                socket.gethostname(), None
            ):
                if "%" in ip:
                    ip = ip.split("%")[0]
                if ip in seen:
                    continue
                seen.add(ip)

                try:
                    ip_obj = ipaddress.ip_address(ip)
                    if not ip_obj.is_loopback and ip_obj.is_private:
                        self._local_ips.append(
                            {
                                "type": f"lan_v{6 if family == socket.AF_INET6 else 4}",
                                "ip": ip,
                            }
                        )
                except ValueError:
                    continue
        except Exception as e:
            logger.debug(f"获取本地IP地址失败: {e}")

    async def start(
        self,
        host: str = "0.0.0.0",
        port: int = 8000,
        ssl_certfile: str | None = None,
        ssl_keyfile: str | None = None,
    ) -> None:
        """
        启动路由服务器

        :param host: str 监听地址(默认"0.0.0.0")
        :param port: int 监听端口(默认8000)
        :param ssl_certfile: str | None SSL证书路径
        :param ssl_keyfile: str | None SSL密钥路径

        :raises RuntimeError: 当服务器已在运行时抛出
        """
        try:
            if self._server_task and not self._server_task.done():
                raise RuntimeError("服务器已在运行中")

            self._get_local_ips()
            self._apply_config()

            config = uvicorn.Config(
                self.app,
                host=host,
                port=port,
                log_level="warning",
                ssl_certfile=ssl_certfile,
                ssl_keyfile=ssl_keyfile,
            )
            self._uvicorn_server = uvicorn.Server(config)

            self.base_url = f"http{'s' if ssl_certfile else ''}://{host}:{port}"
            display_url = self._format_display_url(self.base_url)
            registered_routes = [r.path for r in self.app.router.routes if hasattr(r, 'path')]
            logger.info(f"启动路由服务器 {display_url}")
            logger.debug(f"已注册 {len(registered_routes)} 条路由: {registered_routes}")

            self._server_task = asyncio.create_task(self._uvicorn_server._serve())

            await lifecycle.submit_event(
                "server.start",
                msg="路由服务器已启动",
                data={
                    "base_url": self.base_url,
                    "host": host,
                    "port": port,
                },
            )
        except Exception as e:
            display_url = self._format_display_url(self.base_url)
            await lifecycle.submit_event(
                "server.start",
                msg="路由服务器启动失败",
                data={
                    "base_url": self.base_url,
                    "host": host,
                    "port": port,
                },
            )
            logger.error(f"启动服务器失败: {e}")
            raise e

    async def stop(self) -> None:
        """
        停止服务器并清理所有路由
        """
        if hasattr(self, '_uvicorn_server') and self._uvicorn_server:
            self._uvicorn_server.should_exit = True

        if self._server_task:
            logger.debug("正在停止路由服务器...")
            try:
                await asyncio.wait_for(self._server_task, timeout=5.0)
                logger.debug("路由服务器已正常停止")
            except asyncio.CancelledError:
                logger.info("路由服务器已被取消")
            except asyncio.TimeoutError:
                self._server_task.cancel()
                try:
                    await self._server_task
                except (asyncio.CancelledError, Exception):
                    pass
                logger.warning("路由服务器停止超时，强制终止")
            except Exception as e:
                logger.error(f"路由服务器停止时发生错误: {e}", exc_info=True)
            finally:
                self._server_task = None
                self._uvicorn_server = None

        logger.debug("清理所有注册的路由...")
        self._http_routes.clear()
        self._websocket_routes.clear()
        self._rate_limit_store.clear()
        self._route_middlewares.clear()
        self._global_middlewares.clear()
        self._middleware_installed = False

        self.app.router.routes.clear()
        self._setup_core_routes()

        await lifecycle.submit_event("server.stop", msg="服务器已停止")

    def _format_display_url(self, url: str) -> str:
        """
        格式化URL显示

        :param url: str 原始URL
        :return: str 格式化后的URL
        """
        # 提取URL组件
        protocol = url.split("://")[0] if "://" in url else "http"
        host_with_path = url.split("://")[1] if "://" in url else url
        host = host_with_path.split("/")[0]
        path = "/" + host_with_path.split("/", 1)[1] if "/" in host_with_path else ""
        port = (
            host.rsplit(":", 1)[-1]
            if ":" in host and not host.startswith("[")
            else "8000"
        )

        # 特定地址直接返回
        if not any(x in host for x in ["0.0.0.0", "[::]"]):
            return url

        # 无本地IP或通配符地址
        if not self._local_ips:
            fallback = "127.0.0.1" if "0.0.0.0" in host else "localhost"
            return f"{url}\n  └─ 可访问: http://{fallback}:{port}{path}"

        # 树状显示
        lines = [url]
        lan_v4 = [ip["ip"] for ip in self._local_ips if ip["type"] == "lan_v4"]
        lan_v6 = [ip["ip"] for ip in self._local_ips if ip["type"] == "lan_v6"]

        if lan_v4:
            lines.append(
                f"  {'└─' if not lan_v6 else '├─'} 局域网IPv4: {protocol}://{lan_v4[0]}:{port}{path}"
            )
        if lan_v6:
            lines.append(f"  └─ 局域网IPv6: {protocol}://[{lan_v6[0]}]:{port}{path}")

        return "\n".join(lines)


router: RouterManager = RouterManager()

__all__ = [
    "router",
    "RouterManager",
    "RouteGroup",
    "HTTPHandler",
    "WebSocketHandler",
    "RoutePath",
]