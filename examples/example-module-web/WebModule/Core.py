import os
from dataclasses import dataclass, field

# 推荐根导入（2.10+）：常用符号直接从 ErisPulse 根包导入
from ErisPulse import (
    SDK,
    BaseConfig,
    BaseModule,
    Event,
    ModuleMeta,
    WebSocketConnection,
    command,
    router,
)


class Main(BaseModule):
    """
    Web 能力示例模块

    演示 @router.http / @router.ws / @router.middleware 装饰器与
    router.app 逃生舱；路由与命令在模块加载上下文内注册（单参形态，
    自动归属本模块命名空间，卸载时随归属自动清理）
    """

    @dataclass
    class ConfigClass(BaseConfig):
        """WebModule 模块配置"""

        greeting: str = field(
            default="hello from WebModule",
            metadata={
                "description": "问候语前缀",
                "ui": {"widget": "text", "group": "basic", "order": 1},
            },
        )

    def __init__(self, sdk: SDK = None):
        self.sdk = sdk
        self.logger = self.sdk.logger.get_child("WebModule")
        self.logger.info("WebModule 初始化完成")

    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(
            name="WebModule",
            description="Web 能力示例模块",
            version="1.0.0",
            author="ErisDev",
            group="示例",
            tags=["示例", "web"],
        )

    async def on_load(self, event: dict) -> bool:
        self._register_routes()
        self._register_commands()
        self.logger.info("路由与命令已注册（卸载时随模块归属自动清理）")
        return True

    async def on_unload(self, event: dict) -> bool:
        return True

    def _register_routes(self):
        """注册路由（须在模块加载上下文内调用：单参形态依赖归属注入）"""

        @router.http("/hello", methods=["GET"])
        async def hello(request):
            # HttpRequest 自动注入（参数名 request 即命中）
            name = request.query.get("name", "world")
            return {"message": f"{self.cfg.greeting}, {name}!"}

        @router.http("/echo", methods=["POST"])
        async def echo(request):
            data = await request.json()
            return {
                "echo": data,
                "request_id": request.headers.get("x-request-id"),
                "method": request.method,
            }

        # 中间件：glob 路径匹配；令牌走环境变量，勿在代码中硬编码
        @router.middleware("/webmodule/*")
        async def token_middleware(request, call_next):
            expected = os.environ.get("ERISPULSE_WEB_TOKEN", "")
            if expected and request.headers.get("Authorization") != expected:
                return {"error": "Unauthorized"}
            return await call_next(request)

        # WebSocket 回显 + 生命周期钩子（断开 / 错误回调注册，无需手动 try/catch）
        @router.ws("/ws/echo")
        async def echo_ws(ws: WebSocketConnection):
            @ws.on_disconnect
            async def on_disconnect(ws, reason="unknown"):
                self.logger.debug(f"ws 断开: {reason}")

            @ws.on_error
            async def on_error(ws, error=""):
                self.logger.debug(f"ws 错误: {error}")

            async for msg in ws.iter_text():
                await ws.send_text(f"Echo: {msg}")

        # 逃生舱：直接在底层 FastAPI 实例上注册路由。
        # router.app 是当前 web 栈（FastAPI/Starlette）的实例——框架日后迁移
        # 底层 web 实现时，依赖其内部结构的代码会遇到破坏性变更；抽象层
        # （@router.http / HttpRequest）表达不了的场景才使用，并把依赖
        # 收敛在本模块单点，迁移时只需改这里
        @router.app.get("/webmodule/direct")
        async def direct_route():
            return {"via": "router.app escape hatch"}

    def _register_commands(self):
        """注册命令处理器"""

        @command("webhelp", help="列出本模块注册的 Web 端点")
        async def webhelp_command(event: Event):
            base = "/webmodule"
            await event.reply(
                f"HTTP: GET {base}/hello?name=xx | POST {base}/echo\n"
                f"WS: {base}/ws/echo\n"
                f"直连（逃生舱）: GET {base}/direct"
            )
