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
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.routing import APIRoute
from starlette.staticfiles import StaticFiles
from typing import Any, TypeAlias
from collections.abc import Callable, Awaitable
from collections import defaultdict
from .logger import logger
from .lifecycle import lifecycle
from .Bases.router import HttpRequest, WebSocketConnection, SseEmitter
from .Bases.errors import WebSocketDisconnect as _EPWebSocketDisconnect
from .constants import (
    DEFAULT_SERVER_HOST,
    DEFAULT_SERVER_PORT,
    SERVER_SHUTDOWN_TIMEOUT_SECS,
    DEFAULT_RATE_LIMIT_WINDOW_SECS,
    DEFAULT_RATE_LIMIT_MAX_REQUESTS,
    DEFAULT_HTTP_METHODS,
    DEFAULT_WS_AUTO_ACCEPT,
    DEFAULT_CORS_ORIGINS,
    DEFAULT_CORS_METHODS,
    DEFAULT_CORS_HEADERS,
    DEFAULT_CORS_MAX_AGE_SECS,
    DEFAULT_SECURITY_HEADERS,
    WS_CLOSE_POLICY_VIOLATION,
    WS_CLOSE_INTERNAL_ERROR,
    WILDCARD_IPV4,
    WILDCARD_IPV6,
    FALLBACK_IPV4,
    FALLBACK_IPV6_HOST,
    CONFIG_KEY_ROUTER_CORS,
    CONFIG_KEY_ROUTER_SECURITY,
)
import asyncio
import functools
import inspect
import os
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

# 用于自动注入的请求参数名集合
_REQUEST_LIKE_NAMES = frozenset({"request", "req"})


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

    def __init__(
        self,
        module_name: str,
        prefix: str,
        version: str = None,
        tags: list[str] = None,
        middlewares: list = None,
        router: "RouterManager" = None,
    ):
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

    def sse(self, path: str, **kwargs):
        """
        SSE (Server-Sent Events) 路由装饰器

        :param path: str 路由路径
        """
        resolved = self._resolve_path(path)
        return self._router._sse_decorate(resolved, self._module_name, **kwargs)

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
            self._module_name,
            new_prefix,
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
            title="ErisPulse Router",
            description="统一路由管理入口点",
            version=ERISPULSE_VERSION,
        )
        # HTTP路由：{module_name: {path: {method: handler}}}
        self._http_routes: dict[str, dict[str, dict[str, Callable]]] = defaultdict(dict)
        self._websocket_routes: dict[
            str, dict[str, tuple[Callable, Callable | None, bool]]
        ] = defaultdict(dict)
        self._sse_routes: dict[str, dict[str, Callable]] = defaultdict(dict)
        self.base_url = ""
        self._server_task: asyncio.Task | None = None
        self._uvicorn_server: uvicorn.Server | None = None
        self._local_ips: list[dict[str, str]] = []
        self._route_middlewares: dict[str, list] = defaultdict(list)
        self._global_middlewares: list = []
        self._rate_limit_store: dict[str, list[float]] = {}
        self._middleware_installed = False
        self._setup_core_routes()
        self._setup_error_pages()

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

    # 自动注入

    def _make_http_endpoint(self, handler: Callable) -> Callable:
        """
        根据处理器签名创建 FastAPI 兼容的 HTTP 端点

        自动检测第一个参数的类型注解：
        - fastapi.Request → 直接透传（向后兼容）
        - HttpRequest / 无注解且名称类似 request → 注入 HttpRequest 包装
        - 其他类型 / 非请求参数名 → 不注入

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        sig = inspect.signature(handler)
        params = list(sig.parameters.values())

        if not params:
            return handler

        first_param = params[0]

        # 跳过 *args / **kwargs
        if first_param.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            return handler

        first_ann = first_param.annotation

        # 用户显式使用 FastAPI Request → 直接透传
        if first_ann is Request:
            return handler

        # 判断是否需要注入
        should_wrap = False
        if first_ann is HttpRequest:
            should_wrap = True
        elif first_param.name in _REQUEST_LIKE_NAMES:
            # 无注解或其它注解但名称类似 request → 注入
            should_wrap = True

        if not should_wrap:
            return handler

        # 构建新签名：第一个参数注解替换为 FastAPI Request
        first_name = first_param.name
        new_params = [
            first_param.replace(annotation=Request),
            *params[1:],
        ]

        @functools.wraps(handler)
        async def wrapper(**kwargs):
            raw_request = kwargs.pop(first_name, None)
            http_request = HttpRequest(raw_request)
            result = handler(http_request, **kwargs)
            if inspect.isawaitable(result):
                result = await result
            return result

        wrapper.__signature__ = sig.replace(
            parameters=new_params,
            return_annotation=sig.return_annotation,
        )
        return wrapper

    def _make_ws_handler(self, handler: Callable) -> Callable:
        """
        根据处理器签名创建 WebSocket 处理器包装

        - fastapi.WebSocket 注解 → 提取 .raw 透传
        - WebSocketConnection / 无注解 → 直接传递 WebSocketConnection

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        sig = inspect.signature(handler)
        params = list(sig.parameters.values())

        extract_raw = False
        has_first = False
        if params and params[0].kind not in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            has_first = True
            first_ann = params[0].annotation
            if first_ann is not inspect.Parameter.empty and first_ann is WebSocket:
                extract_raw = True

        if not has_first:
            # 无参数处理器
            async def _wrapper(ws_conn, *, _h=handler):
                result = _h()
                if inspect.isawaitable(result):
                    await result

            return _wrapper

        if extract_raw:

            async def _wrapper(ws_conn, *, _h=handler):
                result = _h(ws_conn.raw)
                if inspect.isawaitable(result):
                    await result

            return _wrapper

        async def _wrapper(ws_conn, *, _h=handler):
            result = _h(ws_conn)
            if inspect.isawaitable(result):
                await result

        return _wrapper

    def _make_ws_auth_handler(self, auth_handler: Callable) -> Callable:
        """
        根据签名创建 WebSocket 认证处理器包装

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        sig = inspect.signature(auth_handler)
        params = list(sig.parameters.values())

        extract_raw = False
        has_first = False
        if params and params[0].kind not in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            has_first = True
            first_ann = params[0].annotation
            if first_ann is not inspect.Parameter.empty and first_ann is WebSocket:
                extract_raw = True

        if not has_first:

            async def _wrapper(ws_conn, *, _h=auth_handler):
                result = _h()
                if inspect.isawaitable(result):
                    return await result
                return result

            return _wrapper

        if extract_raw:

            async def _wrapper(ws_conn, *, _h=auth_handler):
                result = _h(ws_conn.raw)
                if inspect.isawaitable(result):
                    return await result
                return result

            return _wrapper

        async def _wrapper(ws_conn, *, _h=auth_handler):
            result = _h(ws_conn)
            if inspect.isawaitable(result):
                return await result
            return result

        return _wrapper

    def _make_sse_endpoint(self, handler: Callable) -> Callable:
        """
        根据处理器签名创建 SSE 端点包装器

        自动检测处理器是否需要 HttpRequest 参数。
        为处理器创建 SseEmitter 实例，通过回调桥接 SSE 协议到底层 StreamingResponse。

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        sig = inspect.signature(handler)
        params = list(sig.parameters.values())

        wants_request = False
        if params:
            first = params[0]
            if first.annotation in (HttpRequest, Request):
                wants_request = True
            elif first.annotation is SseEmitter:
                wants_request = False
            elif first.name in _REQUEST_LIKE_NAMES:
                wants_request = True

        async def wrapper(request: Request):
            queue: asyncio.Queue = asyncio.Queue()
            is_closed = False

            async def on_send(payload: str):
                if not is_closed:
                    await queue.put(payload)

            async def on_close():
                nonlocal is_closed
                if not is_closed:
                    is_closed = True
                    await queue.put(None)

            if wants_request:
                sse = SseEmitter(on_send=on_send, on_close=on_close, request=request)
                handler_task = asyncio.create_task(handler(HttpRequest(request), sse))
            else:
                sse = SseEmitter(on_send=on_send, on_close=on_close, request=request)
                handler_task = asyncio.create_task(handler(sse))

            async def generator():
                yield ":ok\n\n"
                while True:
                    payload = await queue.get()
                    if payload is None:
                        break
                    yield payload

            try:
                response = StreamingResponse(
                    generator(),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "X-Accel-Buffering": "no",
                    },
                )
                return response
            except Exception:
                handler_task.cancel()
                raise

        return wrapper

    def _register_sse_endpoint(
        self,
        full_path: str,
        module_name: str,
        handler: Callable,
        **kwargs,
    ) -> None:
        """
        SSE 路由注册内部实现

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        if full_path in self._sse_routes.get(module_name, {}):
            raise ValueError(f"SSE路径 {full_path} 已在模块 {module_name} 中注册")

        endpoint = self._make_sse_endpoint(handler)
        route = APIRoute(
            path=full_path,
            endpoint=endpoint,
            methods=["GET"],
            name=f"{module_name}_{full_path.replace('/', '_')}_sse",
            **{
                k: v
                for k, v in kwargs.items()
                if k
                in ("summary", "description", "tags", "response_model", "deprecated")
            },
        )
        self.app.router.routes.append(route)
        self._sse_routes[module_name][full_path] = handler

        logger.info(f"[{module_name}] 注册SSE路由: {full_path}")

    @staticmethod
    async def _run_ws_hooks(
        ws_conn: WebSocketConnection, hook_type: str, **kwargs
    ) -> None:
        """
        执行 WebSocket 生命周期钩子

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        hooks = (
            ws_conn._on_disconnect_handlers
            if hook_type == "disconnect"
            else ws_conn._on_error_handlers
        )
        for hook in hooks:
            try:
                result = hook(ws_conn, **kwargs)
                if inspect.isawaitable(result):
                    await result
            except Exception as e:
                logger.debug(f"WebSocket lifecycle hook error: {e}")

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

        @self.app.get("/", include_in_schema=False)
        async def root_page(request: Request) -> HTMLResponse:
            dashboard_available = False
            try:
                import ErisPulse as _pkg

                _sdk = _pkg.sdk
                dashboard_available = hasattr(_sdk, "Dashboard") and _sdk.Dashboard
            except Exception:
                pass

            dashboard_html = ""
            if dashboard_available:
                dashboard_html = """
      <a class="card dash-link" href="/Dashboard">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/>
          <rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>
        </svg>
        <span>Dashboard</span>
      </a>"""

            html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ErisPulse</title>
<style>
  * {{ margin:0;padding:0;box-sizing:border-box }}
  html {{ -webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale }}
  :root {{
    --bg:#0E1520;--bg-card:#151C28;--tx:#E2E8F0;--tx2:#A0B0C0;--tx3:#5A6C7D;
    --bd:rgba(40,53,69,.6);--accent:#7DBFE0;--accent2:rgba(125,191,224,.08)
  }}
  @media (prefers-color-scheme:light) {{
    :root {{
      --bg:#F4F7FB;--bg-card:#FFFFFF;--tx:#2C3E50;--tx2:#5A6C7D;--tx3:#A0B0C0;
      --bd:#DDE3EC;--accent:#7EB8D8;--accent2:rgba(126,184,216,.05)
    }}
  }}
  body {{
    font-family:'Inter',-apple-system,BlinkMacSystemFont,'SF Pro Display','SF Pro Text','Helvetica Neue','PingFang SC','Microsoft YaHei',sans-serif;
    background:var(--bg);color:var(--tx);
    min-height:100vh;min-height:100dvh;
    display:flex;align-items:center;justify-content:center;
    padding:2rem;position:relative;overflow:hidden
  }}
  body::before {{
    content:'';position:absolute;inset:0;
    background:radial-gradient(ellipse 75% 55% at 50% 38%,var(--accent2) 0%,transparent 70%);
    pointer-events:none
  }}
  .hero {{ display:flex;flex-direction:column;align-items:center;position:relative;z-index:1 }}
  .mascot-wrap {{ position:relative;margin-bottom:2rem;animation:pop .6s cubic-bezier(.34,1.56,.64,1) both }}
  @keyframes pop {{ from{{opacity:0;transform:scale(.85)}} to{{opacity:1;transform:scale(1)}} }}
  .mascot {{ width:280px;height:280px;object-fit:contain;border-radius:36px }}
  .content {{ text-align:center;animation:fadeUp .6s .1s cubic-bezier(.23,1,.32,1) both }}
  @keyframes fadeUp {{ from{{opacity:0;transform:translateY(12px)}} to{{opacity:1;transform:translateY(0)}} }}
  h1 {{ font-size:2rem;font-weight:600;letter-spacing:-.015em;color:var(--tx);margin-bottom:.15rem }}
  .ver {{ font-size:.68rem;font-weight:500;color:var(--tx3);letter-spacing:.06em;margin-bottom:1.2rem }}
  p.sub {{ font-size:.9rem;font-weight:400;color:var(--tx2);margin-bottom:1.8rem }}
  .card {{
    display:inline-flex;align-items:center;gap:.55rem;
    padding:.55rem 1.2rem;
    background:var(--bg-card);border:1px solid var(--bd);border-radius:50px;
    text-decoration:none;color:var(--accent);font-size:.8rem;font-weight:500;
    transition:all .25s cubic-bezier(.25,.1,.25,1)
  }}
  .card:hover {{ border-color:var(--accent);transform:translateY(-1px);box-shadow:0 4px 14px rgba(125,191,224,.12) }}
  .card:active {{ transform:scale(.97) }}
  .endpoints {{
    margin-top:2.2rem;font-size:.66rem;font-weight:400;color:var(--tx3);letter-spacing:.04em;
    display:flex;gap:.5rem;justify-content:center
  }}
  .endpoints a {{ color:var(--tx3);text-decoration:none;transition:color .2s }}
  .endpoints a:hover {{ color:var(--tx2) }}
  .links {{ margin-top:.4rem;display:flex;gap:.9rem;justify-content:center;flex-wrap:wrap }}
  .links a {{ font-size:.66rem;font-weight:400;color:var(--tx3);text-decoration:none;transition:color .2s }}
  .links a:hover {{ color:var(--accent) }}
  .deco {{ position:absolute;border-radius:50%;pointer-events:none;z-index:0 }}
  .deco-1 {{ width:100px;height:100px;background:rgba(126,184,216,.06);top:10%;right:12% }}
  .deco-2 {{ width:70px;height:70px;background:rgba(126,184,216,.05);bottom:15%;left:10% }}
</style>
</head>
<body>
  <div class="deco deco-1"></div><div class="deco deco-2"></div>
  <div class="hero">
    <div class="mascot-wrap">
      <img class="mascot" src="https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/.github/assets/mascot-hero.png" alt="ErisPulse" onerror="this.style.display='none'" />
    </div>
    <div class="content">
      <h1>ErisPulse</h1>
      <p class="ver">v{ERISPULSE_VERSION}</p>
      <p class="sub">你似乎访问了根路径，这里没有内容哦~</p>
      {dashboard_html}
      <div class="endpoints"><a href="/health">Health</a> &middot; <a href="/ping">Ping</a></div>
      <div class="links">
        <a href="https://github.com/ErisPulse/ErisPulse" target="_blank">GitHub</a>
        <a href="https://www.erisdev.com" target="_blank">文档</a>
        <a href="https://pypi.org/project/ErisPulse/" target="_blank">PyPI</a>
        <a href="https://github.com/ErisPulse/ErisPulse/discussions" target="_blank">社区</a>
      </div>
    </div>
  </div>
</body>
</html>"""
            return HTMLResponse(content=html)

    def _setup_error_pages(self) -> None:
        """
        设置错误页面和静态资源

        {!--< internal-use >!--}
        注册 web_status/ 包目录的静态文件服务（/status-assets），
        并为 GET 请求添加 ErisPulse 主题化错误页面。
        POST 等非 GET 请求仍然返回 JSON 格式的错误响应。
        {!--< /internal-use >!--}
        """
        from ..web_status import PACKAGE_DIR as _ws_dir

        if os.path.isdir(_ws_dir):
            self.app.mount(
                "/status-assets", StaticFiles(directory=_ws_dir), name="status-assets"
            )

        page_css = """
  * { margin:0;padding:0;box-sizing:border-box }
  html { -webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale }
  :root {
    --bg:#0E1520;--bg-card:#151C28;--tx:#E2E8F0;--tx2:#A0B0C0;--tx3:#5A6C7D;
    --bd:rgba(40,53,69,.6);--accent:#7DBFE0;--accent2:rgba(125,191,224,.08)
  }
  @media (prefers-color-scheme:light) {
    :root {
      --bg:#F4F7FB;--bg-card:#FFFFFF;--tx:#2C3E50;--tx2:#5A6C7D;--tx3:#A0B0C0;
      --bd:#DDE3EC;--accent:#7EB8D8;--accent2:rgba(126,184,216,.05)
    }
  }
  body {
    font-family:'Inter',-apple-system,BlinkMacSystemFont,'SF Pro Display','SF Pro Text','Helvetica Neue','PingFang SC','Microsoft YaHei',sans-serif;
    background:var(--bg);color:var(--tx);
    min-height:100vh;min-height:100dvh;
    display:flex;align-items:center;justify-content:center;
    text-align:center;padding:2rem;position:relative;overflow:hidden
  }
  body::before {
    content:'';position:absolute;inset:0;
    background:radial-gradient(ellipse 75% 55% at 50% 38%,var(--accent2) 0%,transparent 70%);
    pointer-events:none
  }
  .page-card { max-width:480px;width:100%;position:relative;z-index:1;animation:pop .6s cubic-bezier(.34,1.56,.64,1) both }
  @keyframes pop { from{opacity:0;transform:scale(.88)} to{opacity:1;transform:scale(1)} }
  .page-img { width:240px;height:240px;object-fit:contain;border-radius:24px;margin-bottom:2rem;filter:drop-shadow(0 4px 20px rgba(125,191,224,.08)) }
  .page-code { font-size:4rem;font-weight:600;letter-spacing:6px;color:var(--accent2);margin-bottom:-1.2rem;user-select:none }
  .page-title { font-size:1.25rem;font-weight:600;color:var(--tx);line-height:1.5;letter-spacing:-.01em;margin-bottom:.5rem }
  .page-desc { font-size:.85rem;font-weight:400;color:var(--tx2);line-height:1.6;margin-bottom:2.2rem }
  .page-link {
    display:inline-block;padding:.55rem 1.6rem;
    background:var(--bg-card);border:1px solid var(--bd);border-radius:50px;
    color:var(--accent);text-decoration:none;font-size:.82rem;font-weight:500;
    transition:all .25s cubic-bezier(.25,.1,.25,1)
  }
  .page-link:hover { border-color:var(--accent);transform:translateY(-1px);box-shadow:0 4px 14px rgba(125,191,224,.12) }
  .page-link:active { transform:scale(.97) }
"""

        def _html(code: int, img: str, title: str, desc: str = "") -> str:
            desc_html = f'<p class="page-desc">{desc}</p>' if desc else ""
            return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{code} — ErisPulse</title>
<style>{page_css}</style>
</head>
<body>
  <div class="page-card">
    <div class="page-code">{code}</div>
    <img class="page-img" src="/status-assets/{img}" alt="" onerror="this.style.display='none'" />
    <h1 class="page-title">{title}</h1>
    {desc_html}
    <a class="page-link" href="/">返回首页</a>
  </div>
</body>
</html>"""

        @self.app.exception_handler(404)
        async def _h404(request: Request, exc):
            if request.method == "GET" and "text/html" in request.headers.get(
                "accept", ""
            ):
                return HTMLResponse(
                    content=_html(
                        404,
                        "4xx.png",
                        "你是怎么找到这里的？",
                        "这个页面似乎不存在，或者从未存在过。",
                    ),
                    status_code=404,
                )
            return JSONResponse(
                status_code=404,
                content={"status": "error", "code": 404, "message": "Not Found"},
            )

        @self.app.exception_handler(403)
        async def _h403(request: Request, exc):
            if request.method == "GET" and "text/html" in request.headers.get(
                "accept", ""
            ):
                return HTMLResponse(
                    content=_html(
                        403,
                        "4xx.png",
                        "嗯？这里不对外开放哦~",
                        "你可能没有访问这个资源的权限。",
                    ),
                    status_code=403,
                )
            return JSONResponse(
                status_code=403,
                content={"status": "error", "code": 403, "message": "Forbidden"},
            )

        @self.app.exception_handler(500)
        async def _h500(request: Request, exc):
            logger.error(f"未处理的异常: {exc}")
            if request.method == "GET" and "text/html" in request.headers.get(
                "accept", ""
            ):
                return HTMLResponse(
                    content=_html(
                        500,
                        "5xx.png",
                        "耶耶~搞怪成功!服务器飞走辣~！",
                        "我们已经记录了这个问题，请稍后再试。",
                    ),
                    status_code=500,
                )
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "code": 500,
                    "message": "Internal Server Error",
                },
            )

        @self.app.exception_handler(502)
        async def _h502(request: Request, exc):
            if request.method == "GET" and "text/html" in request.headers.get(
                "accept", ""
            ):
                return HTMLResponse(
                    content=_html(
                        502,
                        "5xx.png",
                        "耶耶~搞怪成功!服务器飞走辣~！",
                        "上游服务似乎不太对劲。",
                    ),
                    status_code=502,
                )
            return JSONResponse(
                status_code=502,
                content={"status": "error", "code": 502, "message": "Bad Gateway"},
            )

        @self.app.exception_handler(503)
        async def _h503(request: Request, exc):
            if request.method == "GET" and "text/html" in request.headers.get(
                "accept", ""
            ):
                return HTMLResponse(
                    content=_html(
                        503,
                        "5xx.png",
                        "耶耶~搞怪成功!服务器飞走辣~！",
                        "服务暂时不可用，请稍后再来。",
                    ),
                    status_code=503,
                )
            return JSONResponse(
                status_code=503,
                content={
                    "status": "error",
                    "code": 503,
                    "message": "Service Unavailable",
                },
            )

        @self.app.exception_handler(Exception)
        async def _h_generic(request: Request, exc: Exception):
            logger.error(f"未处理的异常: {exc}")
            if request.method == "GET" and "text/html" in request.headers.get(
                "accept", ""
            ):
                return HTMLResponse(
                    content=_html(
                        500,
                        "unknow.png",
                        "诶？发生了什么……",
                        "有些事情我们也没预料到，正在排查中。",
                    ),
                    status_code=500,
                )
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "code": 500,
                    "message": "Internal Server Error",
                },
            )

    def _restore_routes_from_records(self) -> None:
        """
        将内部记录中已有的路由重新注册到当前 FastAPI 实例

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        restored_http = 0
        for module_name, paths in self._http_routes.items():
            for full_path, method_map in paths.items():
                methods = list(method_map.keys())
                if not methods:
                    continue
                handler = method_map[methods[0]]
                endpoint = self._make_http_endpoint(handler)
                route = APIRoute(
                    path=full_path,
                    endpoint=endpoint,
                    methods=methods,
                    name=f"{module_name}_{full_path.replace('/', '_')}",
                )
                self.app.router.routes.append(route)
                restored_http += 1

        restored_ws = 0
        for module_name, paths in self._websocket_routes.items():
            for full_path, (handler, auth_handler, auto_accept) in paths.items():
                # 直接在 FastAPI 上注册，跳过重复检查（记录已存在）
                wrapped_handler = self._make_ws_handler(handler)
                wrapped_auth = (
                    self._make_ws_auth_handler(auth_handler) if auth_handler else None
                )

                async def _ws_endpoint(
                    websocket: WebSocket,
                    *,
                    _wh=wrapped_handler,
                    _wa=wrapped_auth,
                    _path=full_path,
                    _mod=module_name,
                    _accept=auto_accept,
                ):
                    ws_conn = WebSocketConnection(websocket)
                    if _accept:
                        await websocket.accept()
                    try:
                        if _wa:
                            if not await _wa(ws_conn):
                                await websocket.close(code=WS_CLOSE_POLICY_VIOLATION)
                                return
                        await lifecycle.emit(
                            "server.websocket.connect",
                            {
                                "path": _path,
                                "module_name": _mod,
                                "client_ip": websocket.client.host
                                if websocket.client
                                else None,
                            },
                        )
                        await _wh(ws_conn)
                    except (WebSocketDisconnect, _EPWebSocketDisconnect):
                        await self._run_ws_hooks(
                            ws_conn, "disconnect", reason="client_disconnect"
                        )
                        await lifecycle.emit(
                            "server.websocket.disconnect",
                            {
                                "path": _path,
                                "module_name": _mod,
                                "reason": "client_disconnect",
                            },
                        )
                    except asyncio.CancelledError:
                        await self._run_ws_hooks(
                            ws_conn, "disconnect", reason="cancelled"
                        )
                        await lifecycle.emit(
                            "server.websocket.disconnect",
                            {
                                "path": _path,
                                "module_name": _mod,
                                "reason": "cancelled",
                            },
                        )
                        raise
                    except Exception as e:
                        await self._run_ws_hooks(ws_conn, "error", error=str(e))
                        await self._run_ws_hooks(ws_conn, "disconnect", reason="error")
                        await lifecycle.emit(
                            "server.websocket.disconnect",
                            {
                                "path": _path,
                                "module_name": _mod,
                                "reason": "error",
                                "error": str(e),
                            },
                        )
                        logger.error(f"WebSocket错误: {e}")
                        try:
                            await websocket.close(code=WS_CLOSE_INTERNAL_ERROR)
                        except Exception:
                            pass

                self.app.add_api_websocket_route(
                    path=full_path,
                    endpoint=_ws_endpoint,
                    name=f"{module_name}_{full_path.replace('/', '_')}",
                )
                restored_ws += 1

        restored_sse = 0
        for module_name, paths in self._sse_routes.items():
            for full_path, handler in paths.items():
                self._register_sse_endpoint(full_path, module_name, handler)
                restored_sse += 1

        if restored_http or restored_ws or restored_sse:
            logger.debug(
                f"已恢复路由: HTTP={restored_http}, WebSocket={restored_ws}, SSE={restored_sse}"
            )

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

        # 如果 app 已启动过（middleware_stack 已构建），无法再添加中间件
        # 此时跳过，已有的中间件仍会生效
        try:

            @self.app.middleware("http")
            async def route_middleware_pipeline(request: Request, call_next):
                path = request.url.path

                # 钩子: HTTP请求接收
                await lifecycle.emit(
                    "server.request",
                    {
                        "method": request.method,
                        "path": path,
                        "client_ip": request.client.host if request.client else None,
                    },
                )

                for mw in self._global_middlewares:
                    if mw._before:
                        result = (
                            await mw._before(request)
                            if inspect.iscoroutinefunction(mw._before)
                            else mw._before(request)
                        )
                        if isinstance(result, Response):
                            return result

                for pattern, mws in self._route_middlewares.items():
                    if self._match_path(pattern, path):
                        for mw in mws:
                            if mw._before:
                                result = (
                                    await mw._before(request)
                                    if inspect.iscoroutinefunction(mw._before)
                                    else mw._before(request)
                                )
                                if isinstance(result, Response):
                                    return result

                response = await call_next(request)

                # 钩子: HTTP响应发送
                await lifecycle.emit(
                    "server.response",
                    {
                        "method": request.method,
                        "path": path,
                        "status_code": response.status_code,
                        "client_ip": request.client.host if request.client else None,
                    },
                )

                for pattern, mws in reversed(list(self._route_middlewares.items())):
                    if self._match_path(pattern, path):
                        for mw in reversed(mws):
                            if mw._after:
                                resp = (
                                    await mw._after(request, response)
                                    if inspect.iscoroutinefunction(mw._after)
                                    else mw._after(request, response)
                                )
                                if resp is not None:
                                    response = resp

                for mw in reversed(self._global_middlewares):
                    if mw._after:
                        resp = (
                            await mw._after(request, response)
                            if inspect.iscoroutinefunction(mw._after)
                            else mw._after(request, response)
                        )
                        if resp is not None:
                            response = resp

                return response
        except RuntimeError:
            logger.debug("FastAPI 应用已启动，跳过中间件安装（已有中间件继续生效）")

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

    def add_middleware(
        self, before: Callable = None, after: Callable = None, *paths: str
    ):
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

    def _http_decorate(
        self, full_path: str, module_name: str, methods: list[str] = None, **kwargs
    ):
        """
        HTTP 路由装饰器内部实现

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """

        def decorator(func):
            resolved_methods = methods or DEFAULT_HTTP_METHODS
            route_kwargs = {}
            for k in ("summary", "description", "tags", "response_model", "deprecated"):
                if k in kwargs and kwargs[k] is not None:
                    route_kwargs[k] = kwargs[k]

            route = APIRoute(
                path=full_path,
                endpoint=self._make_http_endpoint(func),
                methods=resolved_methods,
                name=f"{module_name}_{full_path.replace('/', '_')}",
                **route_kwargs,
            )
            self.app.router.routes.append(route)

            for m in resolved_methods:
                self._http_routes[module_name].setdefault(full_path, {})[m] = func

            rate_limit = kwargs.get("rate_limit")
            if rate_limit:
                self._apply_rate_limit(full_path, rate_limit)

            logger.info(
                f"[{module_name}] 注册HTTP路由: {full_path} 方法: {resolved_methods}"
            )
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
            self._register_ws_endpoint(
                full_path, module_name, func, auth_handler, auto_accept
            )
            return func

        return decorator

    def http(self, module_name: str, path: str, methods: list[str] = None, **kwargs):
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

    def sse(self, module_name: str, path: str, **kwargs):
        """
        SSE (Server-Sent Events) 路由装饰器

        :param module_name: str 模块名称 (必填)
        :param path: str SSE 端点路径
        :param summary: str API 摘要 (可选)
        :param description: str API 描述 (可选)
        :param tags: list[str] API 标签 (可选)

        :example:
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
        """
        full_path = self._normalize_path(module_name, path)
        return self._sse_decorate(full_path, module_name, **kwargs)

    def _sse_decorate(self, full_path: str, module_name: str, **kwargs):
        """
        SSE 路由装饰器内部实现

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """

        def decorator(func):
            self._register_sse_endpoint(full_path, module_name, func, **kwargs)
            return func

        return decorator

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
        for k, v in [
            ("summary", summary),
            ("description", description),
            ("tags", tags),
            ("response_model", response_model),
            ("deprecated", deprecated),
        ]:
            if v is not None:
                route_kwargs[k] = v

        # 创建路由
        route = APIRoute(
            path=full_path,
            endpoint=self._make_http_endpoint(handler),
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

    def _register_ws_endpoint(
        self,
        full_path: str,
        module_name: str,
        handler: Callable[[WebSocket], Awaitable[Any]],
        auth_handler: Callable[[WebSocket], Awaitable[bool]] | None = None,
        auto_accept: bool = True,
    ) -> None:
        """
        WebSocket 路由注册内部实现

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        if full_path in self._websocket_routes[module_name]:
            raise ValueError(f"WebSocket路径 {full_path} 已注册")

        wrapped_handler = self._make_ws_handler(handler)
        wrapped_auth = (
            self._make_ws_auth_handler(auth_handler) if auth_handler else None
        )

        async def websocket_endpoint(websocket: WebSocket) -> None:
            """
            WebSocket端点包装器

            {!--< internal-use >!--}
            {!--< /internal-use >!--}
            """
            if auto_accept:
                await websocket.accept()

            ws_conn = WebSocketConnection(websocket)

            try:
                if wrapped_auth:
                    if not await wrapped_auth(ws_conn):
                        await websocket.close(code=WS_CLOSE_POLICY_VIOLATION)
                        return

                # 钩子: WebSocket连接建立
                await lifecycle.emit(
                    "server.websocket.connect",
                    {
                        "path": full_path,
                        "module_name": module_name,
                        "client_ip": websocket.client.host
                        if websocket.client
                        else None,
                    },
                )

                await wrapped_handler(ws_conn)

            except (WebSocketDisconnect, _EPWebSocketDisconnect):
                await self._run_ws_hooks(
                    ws_conn, "disconnect", reason="client_disconnect"
                )
                # 钩子: WebSocket客户端断开
                await lifecycle.emit(
                    "server.websocket.disconnect",
                    {
                        "path": full_path,
                        "module_name": module_name,
                        "reason": "client_disconnect",
                    },
                )
                logger.debug(f"客户端断开: {full_path}")
            except asyncio.CancelledError:
                await self._run_ws_hooks(ws_conn, "disconnect", reason="cancelled")
                await lifecycle.emit(
                    "server.websocket.disconnect",
                    {
                        "path": full_path,
                        "module_name": module_name,
                        "reason": "cancelled",
                    },
                )
                logger.debug(f"WebSocket连接被取消: {full_path}")
                raise
            except Exception as e:
                await self._run_ws_hooks(ws_conn, "error", error=str(e))
                await self._run_ws_hooks(ws_conn, "disconnect", reason="error")
                # 钩子: WebSocket异常断开
                await lifecycle.emit(
                    "server.websocket.disconnect",
                    {
                        "path": full_path,
                        "module_name": module_name,
                        "reason": "error",
                        "error": str(e),
                    },
                )
                logger.error(f"WebSocket错误: {e}")
                try:
                    await websocket.close(code=WS_CLOSE_INTERNAL_ERROR)
                except Exception:
                    pass

        self.app.add_api_websocket_route(
            path=full_path,
            endpoint=websocket_endpoint,
            name=f"{module_name}_{full_path.replace('/', '_')}",
        )
        self._websocket_routes[module_name][full_path] = (
            handler,
            auth_handler,
            auto_accept,
        )

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
        self._register_ws_endpoint(
            full_path, module_name, handler, auth_handler, auto_accept
        )

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

    def register_sse(
        self,
        module_name: str,
        path: str,
        handler: Callable,
        **kwargs,
    ) -> None:
        """
        注册 SSE (Server-Sent Events) 路由

        SSE 路由为 HTTP GET 端点，返回 ``text/event-stream`` 流式响应。
        处理器接收 ``SseEmitter`` 实例（以及可选的 ``HttpRequest``），
        通过 ``sse.send()`` 推送事件，调用 ``sse.close()`` 断开连接。

        :param module_name: str 模块名称
        :param path: str SSE 端点路径
        :param handler: Callable 事件处理器, 签名: ``async def handler(sse)`` 或 ``async def handler(request, sse)``

        :raises ValueError: 当路径已注册时抛出

        :example:
        >>> async def event_stream(sse):
        ...     for i in range(10):
        ...         await sse.send({"count": i})
        ...         await asyncio.sleep(1)
        >>> router.register_sse("MyModule", "/events", event_stream)
        """
        full_path = self._normalize_path(module_name, path)
        self._register_sse_endpoint(full_path, module_name, handler, **kwargs)

    def unregister_sse(self, module_name: str, path: str) -> bool:
        """
        取消注册 SSE 路由

        :param module_name: 模块名称
        :param path: SSE 路径
        :return: bool 是否成功取消注册
        """
        try:
            full_path = self._normalize_path(module_name, path)

            if (
                sse_routes := self._sse_routes.get(module_name)
            ) and full_path in sse_routes:
                logger.info(f"注销SSE: {full_path}")
                del sse_routes[full_path]

                self.app.router.routes = [
                    route
                    for route in self.app.router.routes
                    if not (
                        isinstance(route, APIRoute)
                        and route.path == full_path
                        and "GET" in route.methods
                    )
                ]
                return True

            logger.debug(f"\n取消注册的SSE路由不存在: {full_path}\n")
            return False
        except Exception as e:
            logger.error(f"注销SSE失败: {e}")
            return False

    def unregister_all_by_namespace(self, namespace: str) -> dict[str, int]:
        """
        清理指定命名空间下的所有路由

        :param namespace: 命名空间（适配器名或模块名）
        :return: dict 清理统计 {"http_count": int, "websocket_count": int, "sse_count": int}
        """
        result = {"http_count": 0, "websocket_count": 0, "sse_count": 0}

        # 清理 HTTP 路由
        if namespace in self._http_routes:
            paths = list(self._http_routes[namespace].keys())
            for path in paths:
                self._http_routes[namespace].pop(path, None)
                result["http_count"] += 1
            self.app.router.routes = [
                route
                for route in self.app.router.routes
                if not (isinstance(route, APIRoute) and route.path in paths)
            ]
            if namespace in self._http_routes:
                del self._http_routes[namespace]

        if namespace in self._websocket_routes:
            paths = list(self._websocket_routes[namespace].keys())
            for path in paths:
                self._websocket_routes[namespace].pop(path, None)
                result["websocket_count"] += 1
            self.app.router.routes = [
                route
                for route in self.app.router.routes
                if not (hasattr(route, "path") and route.path in paths)
            ]
            if namespace in self._websocket_routes:
                del self._websocket_routes[namespace]

        if namespace in self._sse_routes:
            paths = list(self._sse_routes[namespace].keys())
            for path in paths:
                self._sse_routes[namespace].pop(path, None)
                result["sse_count"] += 1
            self.app.router.routes = [
                route
                for route in self.app.router.routes
                if not (
                    isinstance(route, APIRoute)
                    and "GET" in route.methods
                    and route.path in paths
                )
            ]
            if namespace in self._sse_routes:
                del self._sse_routes[namespace]

        if (
            result["http_count"] > 0
            or result["websocket_count"] > 0
            or result["sse_count"] > 0
        ):
            logger.info(
                f"已清理命名空间 [{namespace}] 的路由: "
                f"HTTP={result['http_count']}, WebSocket={result['websocket_count']}, SSE={result['sse_count']}"
            )

        return result

    def list_namespaces(self) -> dict[str, dict[str, list[str]]]:
        """
        列出所有已注册的命名空间及其路由

        :return: dict {namespace: {"http": [paths], "websocket": [paths], "sse": [paths]}}

        :example:
        >>> router.list_namespaces()
        {
            "onebot11": {
                "http": ["/onebot11/webhook", "/onebot11/callback"],
                "websocket": ["/onebot11/ws"],
                "sse": ["/onebot11/events"]
            }
        }
        """
        result = {}

        for namespace, routes in self._http_routes.items():
            if namespace not in result:
                result[namespace] = {"http": [], "websocket": [], "sse": []}
            result[namespace]["http"] = list(routes.keys())

        for namespace, routes in self._websocket_routes.items():
            if namespace not in result:
                result[namespace] = {"http": [], "websocket": [], "sse": []}
            result[namespace]["websocket"] = list(routes.keys())

        for namespace, routes in self._sse_routes.items():
            if namespace not in result:
                result[namespace] = {"http": [], "websocket": [], "sse": []}
            result[namespace]["sse"] = list(routes.keys())

        return result

    def get_module_routes(self, module_name: str) -> dict[str, list[dict]]:
        """
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

        :example:
        >>> router.get_module_routes("onebot11")
        {
            "http": [{"path": "/onebot11/webhook", "methods": ["POST"]}],
            "websocket": [{"path": "/onebot11/ws", "auth": true}],
            "sse": [{"path": "/onebot11/events", "streaming": true}]
        }
        """
        result: dict[str, list[dict]] = {"http": [], "websocket": [], "sse": []}

        for path, method_map in self._http_routes.get(module_name, {}).items():
            result["http"].append(
                {
                    "path": path,
                    "methods": sorted(method_map.keys()),
                }
            )

        for path, (_, auth_handler, _) in self._websocket_routes.get(
            module_name, {}
        ).items():
            result["websocket"].append(
                {
                    "path": path,
                    "auth": auth_handler is not None,
                }
            )

        for path in self._sse_routes.get(module_name, {}):
            result["sse"].append({"path": path, "streaming": True})

        return result

    def get_module_urls(self, module_name: str) -> dict[str, Any]:
        """
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

        :example:
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
        """
        base = getattr(self, "base_url", "")
        result: dict[str, Any] = {
            "base_url": base,
            "http": [],
            "websocket": [],
            "sse": [],
        }

        for path, method_map in self._http_routes.get(module_name, {}).items():
            url = f"{base}{path}" if base else path
            for method in method_map:
                result["http"].append(
                    {
                        "path": path,
                        "method": method,
                        "url": url,
                    }
                )

        if base:
            ws_base = base.replace("https://", "wss://").replace("http://", "ws://")
        else:
            ws_base = ""

        for path, (_, _, _) in self._websocket_routes.get(module_name, {}).items():
            ws_url = f"{ws_base}{path}" if ws_base else path
            result["websocket"].append(
                {
                    "path": path,
                    "url": ws_url,
                }
            )

        for path in self._sse_routes.get(module_name, {}):
            url = f"{base}{path}" if base else path
            result["sse"].append(
                {
                    "path": path,
                    "url": url,
                }
            )

        return result

    def get_module_urls_matching(self, prefix: str) -> dict[str, Any]:
        """
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

        :example:
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
        """
        base = getattr(self, "base_url", "")
        result: dict[str, Any] = {
            "base_url": base,
            "http": [],
            "websocket": [],
            "sse": [],
        }

        if base:
            ws_base = base.replace("https://", "wss://").replace("http://", "ws://")
        else:
            ws_base = ""

        matched = [
            ns
            for ns in set(
                list(self._http_routes.keys())
                + list(self._websocket_routes.keys())
                + list(self._sse_routes.keys())
            )
            if ns == prefix or ns.startswith(f"{prefix}_")
        ]

        for ns in matched:
            for path, method_map in self._http_routes.get(ns, {}).items():
                url = f"{base}{path}" if base else path
                for method in method_map:
                    result["http"].append(
                        {"path": path, "method": method, "url": url, "namespace": ns}
                    )

            for path, (_, _, _) in self._websocket_routes.get(ns, {}).items():
                ws_url = f"{ws_base}{path}" if ws_base else path
                result["websocket"].append(
                    {"path": path, "url": ws_url, "namespace": ns}
                )

            for path in self._sse_routes.get(ns, {}):
                url = f"{base}{path}" if base else path
                result["sse"].append({"path": path, "url": url, "namespace": ns})

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

            self._rate_limit_store[key] = [
                t for t in self._rate_limit_store[key] if now - t < window
            ]

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
            return int(limit.get("requests", DEFAULT_RATE_LIMIT_MAX_REQUESTS)), int(
                limit.get("window", DEFAULT_RATE_LIMIT_WINDOW_SECS)
            )

        parts = limit.split("/")
        count = int(parts[0])
        unit = parts[1].lower() if len(parts) > 1 else "m"

        multipliers = {
            "s": 1,
            "second": 1,
            "seconds": 1,
            "m": 60,
            "minute": 60,
            "minutes": 60,
            "h": 3600,
            "hour": 3600,
            "hours": 3600,
        }
        return count, multipliers.get(unit, 60)

    # CORS / 安全头

    def setup_cors(
        self,
        allow_origins: list[str] = None,
        allow_methods: list[str] = None,
        allow_headers: list[str] = None,
        allow_credentials: bool = False,
        max_age: int = DEFAULT_CORS_MAX_AGE_SECS,
        expose_headers: list[str] = None,
    ):
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
            allow_origins=allow_origins or DEFAULT_CORS_ORIGINS,
            allow_methods=allow_methods or DEFAULT_CORS_METHODS,
            allow_headers=allow_headers or DEFAULT_CORS_HEADERS,
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
        defaults = DEFAULT_SECURITY_HEADERS
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

            cors = config.getConfig(CONFIG_KEY_ROUTER_CORS)
            if cors and cors.get("enabled"):
                self.setup_cors(
                    allow_origins=cors.get("allow_origins", ["*"]),
                    allow_methods=cors.get("allow_methods", ["*"]),
                    allow_headers=cors.get("allow_headers", ["*"]),
                    allow_credentials=cors.get("allow_credentials", False),
                    max_age=cors.get("max_age", DEFAULT_CORS_MAX_AGE_SECS),
                )

            security = config.getConfig(CONFIG_KEY_ROUTER_SECURITY)
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
        host: str = DEFAULT_SERVER_HOST,
        port: int = DEFAULT_SERVER_PORT,
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

            self._ensure_middleware_installed()
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
            registered_routes = [
                r.path for r in self.app.router.routes if hasattr(r, "path")
            ]
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
        if hasattr(self, "_uvicorn_server") and self._uvicorn_server:
            self._uvicorn_server.should_exit = True

        if self._server_task:
            logger.debug("正在停止路由服务器...")
            try:
                await asyncio.wait_for(
                    self._server_task, timeout=SERVER_SHUTDOWN_TIMEOUT_SECS
                )
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
            else str(DEFAULT_SERVER_PORT)
        )

        # 特定地址直接返回
        if not any(x in host for x in [WILDCARD_IPV4, WILDCARD_IPV6]):
            return url

        # 无本地IP或通配符地址
        if not self._local_ips:
            fallback = FALLBACK_IPV4 if WILDCARD_IPV4 in host else FALLBACK_IPV6_HOST
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
    "HttpRequest",
    "WebSocketConnection",
    "WebSocketDisconnect",
]
