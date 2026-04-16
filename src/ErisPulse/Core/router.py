"""
ErisPulse 路由系统

提供统一的HTTP和WebSocket路由管理，支持多适配器路由注册和生命周期管理。

{!--< tips >!--}
1. 适配器只需注册路由，无需自行管理服务器
2. WebSocket支持自定义认证逻辑
{!--< /tips >!--}
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.routing import APIRoute
from typing import Any, TypeAlias
from collections.abc import Callable, Awaitable
from collections import defaultdict
from .logger import logger
from .lifecycle import lifecycle
import asyncio
import socket
import ipaddress
import sys
import importlib.metadata
from datetime import datetime
from hypercorn.config import Config
from hypercorn.asyncio import serve

ERISPULSE_VERSION = "UnknownVersion"

try:
    ERISPULSE_VERSION = importlib.metadata.version("ErisPulse")
except importlib.metadata.PackageNotFoundError:
    pass

HTTPHandler: TypeAlias = Callable
WebSocketHandler: TypeAlias = Callable[[WebSocket], Awaitable[Any]]
RoutePath: TypeAlias = str


class RouterManager:
    """
    路由管理器

    {!--< tips >!--}
    核心功能：
    - HTTP/WebSocket路由注册
    - 生命周期管理
    - 统一错误处理
    {!--< /tips >!--}
    """

    def __init__(self):
        """
        初始化路由管理器

        {!--< tips >!--}
        会自动创建FastAPI实例并设置核心路由
        {!--< /tips >!--}
        """
        self.app = FastAPI(
            title="ErisPulse Router", description="统一路由管理入口点", version="1.0.0"
        )
        # HTTP路由：{module_name: {path: {method: handler}}}
        self._http_routes: dict[str, dict[str, dict[str, Callable]]] = defaultdict(dict)
        self._websocket_routes: dict[
            str, dict[str, tuple[Callable, Callable | None]]
        ] = defaultdict(dict)
        self.base_url = ""
        self._server_task: asyncio.Task | None = None
        self._local_ips: list[dict[str, str]] = []
        self._setup_core_routes()

    def _normalize_path(self, prefix: str, path: str) -> str:
        """
        标准化路径，确保格式正确

        :param prefix: str 路径前缀（如模块名）
        :param path: str 路径部分

        :return:
            str: 标准化后的完整路径

        {!--< internal-use >!--}
        此方法仅供内部使用
        {!--< /internal-use >!--}
        """
        # 去除首尾斜杠并合并
        parts = [part.strip("/") for part in [prefix, path] if part.strip("/")]
        return "/" + "/".join(parts)

    def _setup_core_routes(self) -> None:
        """
        设置系统核心路由

        {!--< internal-use >!--}
        此方法仅供内部使用
        {!--< /internal-use >!--}
        """

        @self.app.get("/health")
        async def health_check() -> dict[str, str]:
            """
            健康检查端点

            :return:
                dict[str, str]: 包含服务状态和版本信息的字典
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

            :return:
                dict[str, Any]: 包含响应状态和时间戳的字典
            """
            return {"pong": True, "timestamp": datetime.utcnow().isoformat() + "Z"}

    def register_http_route(
        self,
        module_name: str,
        path: str,
        handler: Callable,
        methods: list[str] = ["POST"],
    ) -> None:
        """
        注册HTTP路由

        :param module_name: str 模块名称
        :param path: str 路由路径
        :param handler: Callable 处理函数
        :param methods: list[str] HTTP方法列表(默认["POST"])

        :raises ValueError: 当路径和方法都已注册时抛出
        """
        full_path = self._normalize_path(module_name, path)

        # 检查是否有冲突的方法
        conflicting_methods = []
        if full_path in self._http_routes[module_name]:
            for method in methods:
                if method in self._http_routes[module_name][full_path]:
                    conflicting_methods.append(method)

        if conflicting_methods:
            raise ValueError(f"路径 {full_path} 的方法 {conflicting_methods} 已注册")

        # 创建路由
        route = APIRoute(
            path=full_path,
            endpoint=handler,
            methods=methods,
            name=f"{module_name}_{path.replace('/', '_')}_{methods[0].lower()}",
        )
        self.app.router.routes.append(route)

        # 按方法存储处理器
        if full_path not in self._http_routes[module_name]:
            self._http_routes[module_name][full_path] = {}

        for method in methods:
            self._http_routes[module_name][full_path][method] = handler

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

        :return:
            bool: 是否成功取消注册
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
            routes = self.app.router.routes
            self.app.router.routes = [
                route
                for route in routes
                if not (isinstance(route, APIRoute) and route.path == full_path)
            ]

            return True
        except Exception as e:
            logger.error(f"取消注册HTTP路由失败: {e}")
            return False

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

        :raises ValueError: 当路径已注册时抛出
        """
        full_path = self._normalize_path(module_name, path)

        if full_path in self._websocket_routes[module_name]:
            raise ValueError(f"WebSocket路径 {full_path} 已注册")

        async def websocket_endpoint(websocket: WebSocket) -> None:
            """
            WebSocket端点包装器
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
            name=f"{module_name}_{path.replace('/', '_')}",
        )
        self._websocket_routes[module_name][full_path] = (handler, auth_handler)

        logger.info(
            f"[{module_name}] 注册WebSocket: {full_path}{'(需认证)' if auth_handler else ''}"
        )

    def unregister_websocket(self, module_name: str, path: str) -> bool:
        """
        取消注册WebSocket路由

        :param module_name: 模块名称
        :param path: WebSocket路径

        :return:
            bool: 是否成功取消注册
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
        :return: 清理统计 {http_count: int, websocket_count: int}

        :example:
        >>> router.unregister_all_by_namespace("my_adapter")
        {"http_count": 3, "websocket_count": 1}
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

        :return: {namespace: {"http": [paths], "websocket": [paths]}}

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

    def get_app(self) -> FastAPI:
        """
        获取FastAPI应用实例

        :return:
            FastAPI: FastAPI应用实例
        """
        return self.app

    def _get_local_ips(self) -> None:
        """
        获取本机局域网IP地址

        {!--< internal-use >!--}
        此方法仅供内部使用
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

            # 获取本地IP地址
            self._get_local_ips()

            config = Config()
            config.bind = [f"{host}:{port}"]
            config.loglevel = "warning"

            if ssl_certfile and ssl_keyfile:
                config.certfile = ssl_certfile
                config.keyfile = ssl_keyfile

            self.base_url = f"http{'s' if ssl_certfile else ''}://{host}:{port}"
            display_url = self._format_display_url(self.base_url)
            logger.info(f"启动路由服务器 {display_url}\n")

            self._server_task = asyncio.create_task(serve(self.app, config))  # type: ignore || 原因: Hypercorn与FastAPIl类型不兼容

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
        # 停止服务器
        if self._server_task:
            self._server_task.cancel()
            try:
                await asyncio.wait_for(self._server_task, timeout=5.0)
            except (asyncio.CancelledError, asyncio.TimeoutError, Exception):
                 logger.info("路由服务器已停止")
            self._server_task = None

        # 清理所有注册的路由
        logger.debug("清理所有注册的路由...")
        self._http_routes.clear()
        self._websocket_routes.clear()

        # 重新设置核心路由（因为要清空 FastAPI 的路由表）
        self.app.router.routes.clear()
        self._setup_core_routes()

        await lifecycle.submit_event("server.stop", msg="服务器已停止")

    def _format_display_url(self, url: str) -> str:
        """
        格式化URL显示

        :param url: str 原始URL
        :return:
            str: 格式化后的URL
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
    "HTTPHandler",
    "WebSocketHandler", 
    "RoutePath",
]