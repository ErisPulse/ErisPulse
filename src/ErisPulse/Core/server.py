"""
ErisPulse 适配器服务器系统

提供统一的适配器服务入口。

{!--< tips >!--}
1. 适配器只需注册路由，无需自行管理服务器
2. 提供路由映射和代理功能
{!--< /tips >!--}
"""

from .logger import logger
from typing import Dict, List, Optional, Callable, Any
from fastapi.routing import APIRoute
from collections import defaultdict
from fastapi import FastAPI

class AdapterServer:
    """
    适配器服务器管理器
    """
    
    def __init__(self):
        self.app = FastAPI(title="ErisPulse Adapter Server")
        self._webhook_routes: Dict[str, Dict[str, Callable]] = defaultdict(dict)
        self.base_url = ""  # 适配器服务器地址
        self._setup_core_routes()
        
    def _setup_core_routes(self):
        """设置核心路由"""
        @self.app.get("/health")
        async def health_check():
            return {"status": "ok"}
            
        @self.app.get("/routes")
        async def list_routes():
            return {
                "webhooks": list(self._webhook_routes.keys()),
            }

    def register_webhook(
        self, 
        adapter_name: str,
        path: str,
        handler: Callable,
        methods: List[str] = ["POST"]
    ) -> None:
        """
        注册Webhook路由
        
        :param adapter_name: 适配器名称
        :param path: 路由路径(如"/message")
        :param handler: 处理函数
        :param methods: HTTP方法列表(默认["POST"])
        """
        full_path = f"/{adapter_name}{path}"
        
        if full_path in self._webhook_routes[adapter_name]:
            raise ValueError(f"路径 {full_path} 已经被注册")
            
        route = APIRoute(
            path=full_path,
            endpoint=handler,
            methods=methods,
            name=f"{adapter_name}{path}"
        )
        self.app.router.routes.append(route)
        
        self._webhook_routes[adapter_name][full_path] = handler
        logger.info(f"适配器{adapter_name}，注册了路由: {self.base_url}{adapter_name}{path}")

    def get_app(self) -> FastAPI:
        """
        获取FastAPI应用实例
        
        :return: FastAPI应用实例
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
        
        :param host: 监听主机(默认"0.0.0.0")
        :param port: 监听端口(默认8000)
        :param ssl_certfile: SSL证书文件路径(可选)
        :param ssl_keyfile: SSL密钥文件路径(可选)
        """
        from hypercorn.config import Config
        from hypercorn.asyncio import serve
        
        config = Config()
        config.bind = [f"{host}:{port}"]
        
        config.loglevel = "error"
        
        if ssl_certfile and ssl_keyfile:
            config.certfile = ssl_certfile
            config.keyfile = ssl_keyfile
        
        self.base_url = f"http{'s' if ssl_certfile else ''}://{host}:{port}/"
        logger.info(f"适配器服务器已启动，访问地址: {self.base_url}")
        
        await serve(self.app, config)

# 全局服务器实例
adapter_server = AdapterServer()
