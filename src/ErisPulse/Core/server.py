"""
ErisPulse Adapter Server
提供统一的适配器服务入口，支持HTTP和WebSocket路由

{!--< tips >!--}
1. 适配器只需注册路由，无需自行管理服务器
2. WebSocket支持自定义认证逻辑
3. 兼容FastAPI 0.68+ 版本
{!--< /tips >!--}
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.routing import APIRoute
from typing import Dict, List, Optional, Callable, Any, Awaitable, Tuple
from collections import defaultdict
from .logger import logger
import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve


class AdapterServer:
    """
    适配器服务器管理器
    
    {!--< tips >!--}
    核心功能：
    - HTTP/WebSocket路由注册
    - 生命周期管理
    - 统一错误处理
    {!--< /tips >!--}
    """

    def __init__(self):
        """
        初始化适配器服务器
        
        {!--< tips >!--}
        会自动创建FastAPI实例并设置核心路由
        {!--< /tips >!--}
        """
        self.app = FastAPI(
            title="ErisPulse Adapter Server",
            description="统一适配器服务入口点",
            version="1.0.0"
        )
        self._webhook_routes: Dict[str, Dict[str, Callable]] = defaultdict(dict)
        self._websocket_routes: Dict[str, Dict[str, Tuple[Callable, Optional[Callable]]]] = defaultdict(dict)
        self.base_url = ""
        self._server_task: Optional[asyncio.Task] = None
        self._setup_core_routes()

    def _setup_core_routes(self) -> None:
        """
        设置系统核心路由
        
        {!--< internal-use >!--}
        此方法仅供内部使用
        {!--< /internal-use >!--}
        """
        @self.app.get("/health")
        async def health_check() -> Dict[str, str]:
            """
            健康检查端点
            
            :return: 
                Dict[str, str]: 包含服务状态的字典
            """
            return {"status": "ok", "service": "ErisPulse Adapter Server"}
            
        @self.app.get("/routes")
        async def list_routes() -> Dict[str, Any]:
            """
            列出所有已注册路由
            
            :return: 
                Dict[str, Any]: 包含所有路由信息的字典，格式为:
                {
                    "http_routes": [
                        {
                            "path": "/adapter1/route1",
                            "adapter": "adapter1",
                            "methods": ["POST"]
                        },
                        ...
                    ],
                    "websocket_routes": [
                        {
                            "path": "/adapter1/ws",
                            "adapter": "adapter1",
                            "requires_auth": true
                        },
                        ...
                    ],
                    "base_url": self.base_url
                }
            """
            http_routes = []
            for adapter, routes in self._webhook_routes.items():
                for path, handler in routes.items():
                    route = self.app.router.routes[-1]  # 获取最后添加的路由
                    if isinstance(route, APIRoute) and route.path == path:
                        http_routes.append({
                            "path": path,
                            "adapter": adapter,
                            "methods": route.methods
                        })
            
            websocket_routes = []
            for adapter, routes in self._websocket_routes.items():
                for path, (handler, auth_handler) in routes.items():
                    websocket_routes.append({
                        "path": path,
                        "adapter": adapter,
                        "requires_auth": auth_handler is not None
                    })
            
            return {
                "http_routes": http_routes,
                "websocket_routes": websocket_routes,
                "base_url": self.base_url
            }

    def register_webhook(
        self, 
        adapter_name: str,
        path: str,
        handler: Callable,
        methods: List[str] = ["POST"]
    ) -> None:
        """
        注册HTTP路由
        
        :param adapter_name: str 适配器名称
        :param path: str 路由路径(如"/message")
        :param handler: Callable 处理函数
        :param methods: List[str] HTTP方法列表(默认["POST"])
        
        :raises ValueError: 当路径已注册时抛出
        
        {!--< tips >!--}
        路径会自动添加适配器前缀，如：/adapter_name/path
        {!--< /tips >!--}
        """
        full_path = f"/{adapter_name}{path}"
        
        if full_path in self._webhook_routes[adapter_name]:
            raise ValueError(f"路径 {full_path} 已注册")
            
        route = APIRoute(
            path=full_path,
            endpoint=handler,
            methods=methods,
            name=f"{adapter_name}{path}"
        )
        self.app.router.routes.append(route)
        self._webhook_routes[adapter_name][full_path] = handler
        logger.info(f"注册HTTP路由: {self.base_url}{full_path} 方法: {methods}")

    def register_websocket(
        self,
        adapter_name: str,
        path: str,
        handler: Callable[[WebSocket], Awaitable[Any]],
        auth_handler: Optional[Callable[[WebSocket], Awaitable[bool]]] = None,
    ) -> None:
        """
        注册WebSocket路由
        
        :param adapter_name: str 适配器名称
        :param path: str WebSocket路径(如"/ws")
        :param handler: Callable[[WebSocket], Awaitable[Any]] 主处理函数
        :param auth_handler: Optional[Callable[[WebSocket], Awaitable[bool]]] 认证函数
        
        :raises ValueError: 当路径已注册时抛出
        
        {!--< tips >!--}
        认证函数应返回布尔值，False将拒绝连接
        {!--< /tips >!--}
        """
        full_path = f"/{adapter_name}{path}"
        
        if full_path in self._websocket_routes[adapter_name]:
            raise ValueError(f"WebSocket路径 {full_path} 已注册")
            
        async def websocket_endpoint(websocket: WebSocket) -> None:
            """
            WebSocket端点包装器
            
            {!--< internal-use >!--}
            处理连接生命周期和错误处理
            {!--< /internal-use >!--}
            """
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
            name=f"{adapter_name}{path}"
        )
        self._websocket_routes[adapter_name][full_path] = (handler, auth_handler)
        logger.info(f"注册WebSocket: {self.base_url}{full_path} {'(需认证)' if auth_handler else ''}")

    def get_app(self) -> FastAPI:
        """
        获取FastAPI应用实例
        
        :return: 
            FastAPI: FastAPI应用实例
        """
        return self.app

    async def start(
        self,
        host: str = "0.0.0.0",
        port: int = 8000,
        ssl_certfile: Optional[str] = None,
        ssl_keyfile: Optional[str] = None
    ) -> None:
        """
        启动适配器服务器
        
        :param host: str 监听地址(默认"0.0.0.0")
        :param port: int 监听端口(默认8000)
        :param ssl_certfile: Optional[str] SSL证书路径
        :param ssl_keyfile: Optional[str] SSL密钥路径
        
        :raises RuntimeError: 当服务器已在运行时抛出
        """
        if self._server_task and not self._server_task.done():
            raise RuntimeError("服务器已在运行中")

        config = Config()
        config.bind = [f"{host}:{port}"]
        # config.loglevel = "debug"
        
        if ssl_certfile and ssl_keyfile:
            config.certfile = ssl_certfile
            config.keyfile = ssl_keyfile
        
        self.base_url = f"http{'s' if ssl_certfile else ''}://{host}:{port}"
        logger.info(f"启动服务器 {self.base_url}")
        
        self._server_task = asyncio.create_task(serve(self.app, config))

    async def stop(self) -> None:
        """
        停止服务器
        
        {!--< tips >!--}
        会等待所有连接正常关闭
        {!--< /tips >!--}
        """
        if self._server_task:
            self._server_task.cancel()
            try:
                await self._server_task
            except asyncio.CancelledError:
                logger.info("服务器已停止")
            self._server_task = None


adapter_server = AdapterServer()