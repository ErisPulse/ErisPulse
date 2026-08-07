"""
路由管理单元测试

测试RouterManager的HTTP/WebSocket路由注册、生命周期管理功能
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from fastapi import WebSocket, WebSocketDisconnect

from ErisPulse.Core.router import RouterManager, router


# ==================== RouterManager 基础测试 ====================


class TestRouterManager:
    """路由管理器测试类"""

    @pytest.fixture
    def router_manager(self):
        """创建路由管理器实例"""
        manager = RouterManager()
        yield manager

    # ==================== 基础功能测试 ====================

    def test_router_creation(self, router_manager):
        """测试路由管理器创建"""
        # 验证
        assert router_manager is not None
        assert router_manager.app is not None
        assert router_manager._http_routes is not None
        assert router_manager._websocket_routes is not None

    def test_get_app(self, router_manager):
        """测试获取FastAPI应用"""
        # 执行
        app = router_manager.get_app()

        # 验证
        assert app is not None
        assert app is router_manager.app

    # ==================== HTTP路由测试 ====================

    def test_register_http_route(self, router_manager):
        """测试注册HTTP路由"""

        # 定义处理函数
        async def test_handler():
            return {"status": "ok"}

        # 执行
        router_manager.register_http_route(
            module_name="test_module",
            path="/test",
            handler=test_handler,
            methods=["GET"],
        )

        # 验证
        assert "test_module" in router_manager._http_routes
        assert "/test_module/test" in router_manager._http_routes["test_module"]
        assert (
            router_manager._http_routes["test_module"]["/test_module/test"]["GET"]
            == test_handler
        )

    def test_register_http_route_multiple_methods(self, router_manager):
        """测试注册多种HTTP方法的路由"""

        async def test_handler():
            return {"status": "ok"}

        # 执行
        router_manager.register_http_route(
            module_name="test_module",
            path="/test",
            handler=test_handler,
            methods=["GET", "POST", "PUT"],
        )

        # 验证路由存在
        route_exists = False
        for route in router_manager.app.router.routes:
            if hasattr(route, "path") and route.path == "/test_module/test":
                route_exists = True
                break

        assert route_exists

    def test_register_duplicate_http_route(self, router_manager):
        """测试注册重复的HTTP路由"""

        async def handler1():
            return {"handler1"}

        async def handler2():
            return {"handler2"}

        # 第一次注册
        router_manager.register_http_route(
            module_name="test_module", path="/test", handler=handler1
        )

        # 第二次注册（应该抛出异常）
        with pytest.raises(ValueError, match="路径.*已注册"):
            router_manager.register_http_route(
                module_name="test_module", path="/test", handler=handler2
            )

    def test_unregister_http_route(self, router_manager):
        """测试取消注册HTTP路由"""

        async def test_handler():
            return {"status": "ok"}

        # 先注册
        router_manager.register_http_route(
            module_name="test_module", path="/test", handler=test_handler
        )

        # 执行取消注册
        result = router_manager.unregister_http_route("test_module", "/test")

        # 验证
        assert result is True
        assert "/test_module/test" not in router_manager._http_routes.get(
            "test_module", {}
        )

    def test_unregister_nonexistent_http_route(self, router_manager):
        """测试取消注册不存在的HTTP路由"""
        # 执行
        result = router_manager.unregister_http_route("test_module", "/nonexistent")

        # 验证（应该返回False）
        assert result is False

    # ==================== WebSocket路由测试 ====================

    def test_register_websocket(self, router_manager):
        """测试注册WebSocket路由"""

        async def ws_handler(websocket: WebSocket):
            await websocket.accept()
            await websocket.send_text("Hello")
            await websocket.close()

        # 执行
        router_manager.register_websocket(
            module_name="test_module", path="/ws", handler=ws_handler
        )

        # 验证
        assert "test_module" in router_manager._websocket_routes
        assert "/test_module/ws" in router_manager._websocket_routes["test_module"]
        handler, auth, auto_accept = router_manager._websocket_routes["test_module"][
            "/test_module/ws"
        ]
        assert handler is ws_handler
        assert auth is None

    def test_register_websocket_with_auth(self, router_manager):
        """测试注册带认证的WebSocket路由"""

        async def ws_handler(websocket: WebSocket):
            await websocket.accept()
            await websocket.close()

        async def auth_handler(websocket: WebSocket):
            # 简单认证逻辑
            return True

        # 执行
        router_manager.register_websocket(
            module_name="test_module",
            path="/ws",
            handler=ws_handler,
            auth_handler=auth_handler,
        )

        # 验证
        handler, auth, auto_accept = router_manager._websocket_routes["test_module"][
            "/test_module/ws"
        ]
        assert handler is ws_handler
        assert auth is auth_handler

    def test_register_duplicate_websocket(self, router_manager):
        """测试注册重复的WebSocket路由"""

        async def handler1(websocket: WebSocket):
            await websocket.close()

        async def handler2(websocket: WebSocket):
            await websocket.close()

        # 第一次注册
        router_manager.register_websocket(
            module_name="test_module", path="/ws", handler=handler1
        )

        # 第二次注册（应该抛出异常）
        with pytest.raises(ValueError, match="WebSocket路径.*已注册"):
            router_manager.register_websocket(
                module_name="test_module", path="/ws", handler=handler2
            )

    def test_unregister_websocket(self, router_manager):
        """测试取消注册WebSocket路由"""

        async def ws_handler(websocket: WebSocket):
            await websocket.close()

        # 先注册
        router_manager.register_websocket(
            module_name="test_module", path="/ws", handler=ws_handler
        )

        # 执行取消注册
        result = router_manager.unregister_websocket("test_module", "/ws")

        # 验证
        assert result is True
        assert "/test_module/ws" not in router_manager._websocket_routes.get(
            "test_module", {}
        )

    def test_unregister_nonexistent_websocket(self, router_manager):
        """测试取消注册不存在的WebSocket路由"""
        # 执行
        result = router_manager.unregister_websocket("test_module", "/nonexistent")

        # 验证（应该返回False）
        assert result is False

    # ==================== 兼容性方法测试 ====================

    def test_register_webhook_compat(self, router_manager):
        """测试register_webhook兼容性方法"""

        async def webhook_handler():
            return {"status": "ok"}

        # 执行
        router_manager.register_webhook(
            module_name="test_module", path="/webhook", handler=webhook_handler
        )

        # 验证（应该等同于register_http_route）
        assert "test_module" in router_manager._http_routes
        assert "/test_module/webhook" in router_manager._http_routes["test_module"]

    # ==================== 核心路由测试 ====================

    def test_core_routes_registered(self, router_manager):
        """测试核心路由已注册"""
        # 检查health路由和ping路由
        health_exists = False
        ping_exists = False

        for route in router_manager.app.router.routes:
            if hasattr(route, "path"):
                if route.path == "/health":
                    health_exists = True
                elif route.path == "/ping":
                    ping_exists = True

        # 验证
        assert health_exists, "health路由未注册"
        assert ping_exists, "ping路由未注册"

    # ==================== 服务器生命周期测试 ====================

    @pytest.mark.asyncio
    async def test_server_start(self, router_manager):
        """测试启动服务器"""
        mock_server = MagicMock()
        mock_server._serve = AsyncMock(return_value=None)
        with (
            patch("ErisPulse.Core.router.uvicorn.Server", return_value=mock_server),
            patch("ErisPulse.Core.router.uvicorn.Config", return_value=MagicMock()),
        ):
            await router_manager.start(host="127.0.0.1", port=8888)

            assert router_manager.base_url == "http://127.0.0.1:8888"
            assert router_manager._server_task is not None

    @pytest.mark.asyncio
    async def test_server_start_with_ssl(self, router_manager):
        """测试启动带SSL的服务器"""
        mock_server = MagicMock()
        mock_server._serve = AsyncMock(return_value=None)
        with (
            patch("ErisPulse.Core.router.uvicorn.Server", return_value=mock_server),
            patch("ErisPulse.Core.router.uvicorn.Config") as mock_config_cls,
        ):
            await router_manager.start(
                host="127.0.0.1",
                port=8888,
                ssl_certfile="cert.pem",
                ssl_keyfile="key.pem",
            )

            assert router_manager.base_url == "https://127.0.0.1:8888"
            mock_config_cls.assert_called_once()
            call_kwargs = mock_config_cls.call_args[1]
            assert call_kwargs["ssl_certfile"] == "cert.pem"
            assert call_kwargs["ssl_keyfile"] == "key.pem"

    @pytest.mark.asyncio
    async def test_server_start_port_in_use(self, router_manager):
        """测试端口被占用时同步抛出清晰错误，不自动顺延端口"""
        import socket as _socket

        # 真实占用一个端口，验证 pre-bind 探测生效
        blocker = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
        blocker.bind(("127.0.0.1", 18999))
        blocker.listen(1)
        try:
            with pytest.raises(RuntimeError, match="已被占用"):
                await router_manager.start(host="127.0.0.1", port=18999)
            # 探测失败发生在 uvicorn 启动前，不产生服务器任务
            assert router_manager._server_task is None
            assert router_manager._uvicorn_server is None
        finally:
            blocker.close()

    @pytest.mark.asyncio
    async def test_server_start_already_running(self, router_manager):
        """测试启动已运行的服务器"""
        # Mock第一个服务器任务
        mock_task = Mock()
        mock_task.done.return_value = False
        router_manager._server_task = mock_task

        # 执行（应该抛出异常）
        with pytest.raises(RuntimeError, match="服务器已在运行中"):
            await router_manager.start(host="127.0.0.1", port=8888)

    @pytest.mark.asyncio
    async def test_server_stop(self, router_manager):
        """测试停止服务器"""

        # 创建真实的异步任务
        async def dummy_server():
            await asyncio.sleep(100)  # 长时间运行，会被取消

        mock_task = asyncio.create_task(dummy_server())
        mock_task.cancel = Mock(side_effect=mock_task.cancel)
        router_manager._server_task = mock_task

        # 执行
        await router_manager.stop()

        # 验证
        assert router_manager._server_task is None

    @pytest.mark.asyncio
    async def test_server_stop_with_cancel_error(self, router_manager):
        """测试停止服务器时处理CancelError"""
        import asyncio

        # Mock服务器任务，使用 AsyncMock 模拟 CancelError
        async def mock_task_fn():
            raise asyncio.CancelledError()

        mock_task = asyncio.create_task(mock_task_fn())
        mock_task.cancel = Mock()
        router_manager._server_task = mock_task

        # 执行（不应该抛出异常）
        await router_manager.stop()

        # 验证
        assert router_manager._server_task is None

    @pytest.mark.asyncio
    async def test_server_stop_without_task(self, router_manager):
        """测试停止未启动的服务器"""
        # 执行（不应该抛出异常）
        await router_manager.stop()

        # 验证
        assert router_manager._server_task is None


# ==================== 全局路由实例测试 ====================


class TestGlobalRouter:
    """全局路由实例测试"""

    def test_global_router_exists(self):
        """测试全局路由实例存在"""
        assert router is not None
        assert isinstance(router, RouterManager)

    def test_global_router_singleton(self):
        """测试全局路由是单例"""
        from ErisPulse.Core.router import router as router1
        from ErisPulse.Core.router import router as router2

        # 验证
        assert router1 is router2

    def test_global_router_has_core_routes(self):
        """测试全局路由有核心路由"""
        routes = [
            route.path for route in router.app.router.routes if hasattr(route, "path")
        ]

        # 验证核心路由存在
        assert "/health" in routes
        assert "/ping" in routes


# ==================== 集成测试 ====================


class TestRouterIntegration:
    """路由系统集成测试"""

    @pytest.fixture
    def router_manager(self):
        """创建路由管理器实例"""
        manager = RouterManager()
        yield manager

    @pytest.mark.asyncio
    async def test_http_route_lifecycle(self, router_manager):
        """测试HTTP路由完整生命周期"""
        call_count = []

        async def test_handler():
            call_count.append(1)
            return {"count": len(call_count)}

        # 注册路由
        router_manager.register_http_route(
            module_name="test_module", path="/lifecycle", handler=test_handler
        )

        # 验证已注册
        assert "/test_module/lifecycle" in router_manager._http_routes["test_module"]


# ==================== 装饰器路由测试 ====================


class TestDecoratorRoutes:
    """装饰器路由测试"""

    @pytest.fixture
    def router_manager(self):
        """创建路由管理器实例"""
        manager = RouterManager()
        yield manager

    def test_http_decorator(self, router_manager):
        """测试@http装饰器"""

        @router_manager.http("mod", "/api", methods=["GET"])
        async def handler():
            return {"ok": True}

        assert "mod" in router_manager._http_routes
        assert "/mod/api" in router_manager._http_routes["mod"]

    def test_get_decorator(self, router_manager):
        """测试@get装饰器"""

        @router_manager.get("mod", "/info")
        async def handler():
            return {"info": True}

        routes = router_manager._http_routes["mod"]["/mod/info"]
        assert "GET" in routes

    def test_post_decorator(self, router_manager):
        """测试@post装饰器"""

        @router_manager.post("mod", "/data")
        async def handler():
            return {"created": True}

        routes = router_manager._http_routes["mod"]["/mod/data"]
        assert "POST" in routes

    def test_put_decorator(self, router_manager):
        """测试@put装饰器"""

        @router_manager.put("mod", "/item")
        async def handler():
            return {"updated": True}

        routes = router_manager._http_routes["mod"]["/mod/item"]
        assert "PUT" in routes

    def test_delete_decorator(self, router_manager):
        """测试@delete装饰器"""

        @router_manager.delete("mod", "/item")
        async def handler():
            return {"deleted": True}

        routes = router_manager._http_routes["mod"]["/mod/item"]
        assert "DELETE" in routes

    def test_ws_decorator(self, router_manager):
        """测试@ws装饰器"""

        @router_manager.ws("mod", "/ws")
        async def handler(websocket):
            pass

        assert "mod" in router_manager._websocket_routes
        assert "/mod/ws" in router_manager._websocket_routes["mod"]

    def test_ws_decorator_with_auth(self, router_manager):
        """测试@ws装饰器带认证"""

        async def auth(ws):
            return True

        @router_manager.ws("mod", "/secure", auth_handler=auth)
        async def handler(websocket):
            pass

        _, stored_auth, _ = router_manager._websocket_routes["mod"]["/mod/secure"]
        assert stored_auth is auth

    def test_decorator_returns_function(self, router_manager):
        """测试装饰器返回原函数"""

        async def my_handler():
            return "ok"

        result = router_manager.get("mod", "/test")(my_handler)
        assert result is my_handler


# ==================== 路由分组测试 ====================


class TestRouteGroup:
    """路由分组测试"""

    @pytest.fixture
    def router_manager(self):
        manager = RouterManager()
        yield manager

    def test_create_group(self, router_manager):
        """测试创建路由分组"""
        group = router_manager.group("mod", "/api")
        assert group is not None
        assert group._module_name == "mod"
        assert group._prefix == "/api"

    def test_group_get_route(self, router_manager):
        """测试分组内注册GET路由"""
        group = router_manager.group("mod", "/api")

        @group.get("/users")
        async def list_users():
            return []

        assert "mod" in router_manager._http_routes

    def test_group_post_route(self, router_manager):
        """测试分组内注册POST路由"""
        group = router_manager.group("mod", "/api")

        @group.post("/users")
        async def create_user():
            return {}

        assert "mod" in router_manager._http_routes

    def test_group_with_version(self, router_manager):
        """测试带版本号的分组"""
        group = router_manager.group("mod", "/api", version="1")

        @group.get("/items")
        async def items():
            return []

        routes = [r for r in router_manager.app.router.routes if hasattr(r, "path")]
        paths = [r.path for r in routes]
        assert any("v1" in p and "items" in p for p in paths)

    def test_group_ws_route(self, router_manager):
        """测试分组内WebSocket路由"""
        group = router_manager.group("mod", "/api")

        @group.ws("/live")
        async def live(ws):
            pass

        assert "mod" in router_manager._websocket_routes

    def test_nested_group(self, router_manager):
        """测试嵌套分组"""
        api = router_manager.group("mod", "/api")
        users = api.group("/users")

        @users.get("/")
        async def list_users():
            return []

        assert "mod" in router_manager._http_routes

    def test_group_tags_propagation(self, router_manager):
        """测试标签传播"""
        group = router_manager.group("mod", "/api", tags=["API"])

        @group.get("/data")
        async def data():
            return {}

        route = None
        for r in router_manager.app.router.routes:
            if hasattr(r, "path") and "data" in r.path:
                route = r
                break

        if route and hasattr(route, "tags"):
            assert "API" in route.tags


# ==================== 路由中间件测试 ====================


class TestRouteMiddleware:
    """路由中间件测试"""

    @pytest.fixture
    def router_manager(self):
        manager = RouterManager()
        yield manager

    def test_middleware_decorator_global(self, router_manager):
        """测试全局中间件装饰器"""

        @router_manager.middleware()
        async def log_all(request):
            return request

        assert len(router_manager._global_middlewares) == 1

    def test_middleware_decorator_path_specific(self, router_manager):
        """测试路径特定中间件"""

        @router_manager.middleware("/mod/*")
        async def auth(request):
            return request

        assert "/mod/*" in router_manager._route_middlewares
        assert len(router_manager._route_middlewares["/mod/*"]) == 1

    def test_middleware_before_detection(self, router_manager):
        """测试前置中间件自动检测（单参数）"""

        @router_manager.middleware()
        def before_mw(request):
            return request

        mw = router_manager._global_middlewares[0]
        assert mw._before is not None
        assert mw._after is None

    def test_middleware_after_detection(self, router_manager):
        """测试后置中间件自动检测（双参数含response）"""

        @router_manager.middleware()
        def after_mw(request, response):
            return response

        mw = router_manager._global_middlewares[0]
        assert mw._before is None
        assert mw._after is not None

    def test_add_middleware_functional(self, router_manager):
        """测试函数式添加中间件"""

        async def before(req):
            return req

        async def after(req, resp):
            return resp

        router_manager.add_middleware(before=before, after=after)
        assert len(router_manager._global_middlewares) >= 1

    def test_match_path_exact(self, router_manager):
        """测试精确路径匹配"""
        assert router_manager._match_path("/mod/api", "/mod/api") is True
        assert router_manager._match_path("/mod/api", "/mod/other") is False

    def test_match_path_wildcard(self, router_manager):
        """测试通配符路径匹配"""
        assert router_manager._match_path("/mod/*", "/mod/api") is True
        assert router_manager._match_path("/mod/*", "/mod/") is True
        assert router_manager._match_path("/mod/*", "/other/api") is False

    def test_match_path_double_star(self, router_manager):
        """测试双星号路径匹配"""
        assert router_manager._match_path("/mod/**", "/mod") is True
        assert router_manager._match_path("/mod/**", "/mod/api/deep") is True

    def test_match_path_star_only(self, router_manager):
        """测试星号匹配所有"""
        assert router_manager._match_path("*", "/anything") is True


# ==================== 限流测试 ====================


class TestRateLimit:
    """路由限流测试"""

    @pytest.fixture
    def router_manager(self):
        manager = RouterManager()
        yield manager

    def test_parse_rate_limit_string(self, router_manager):
        """测试解析限流规则字符串"""
        count, window = router_manager._parse_rate_limit("10/minute")
        assert count == 10
        assert window == 60

    def test_parse_rate_limit_seconds(self, router_manager):
        """测试解析秒级限流"""
        count, window = router_manager._parse_rate_limit("5/second")
        assert count == 5
        assert window == 1

    def test_parse_rate_limit_hours(self, router_manager):
        """测试解析小时级限流"""
        count, window = router_manager._parse_rate_limit("100/hour")
        assert count == 100
        assert window == 3600

    def test_parse_rate_limit_dict(self, router_manager):
        """测试解析字典限流规则"""
        count, window = router_manager._parse_rate_limit(
            {"requests": 20, "window": 120}
        )
        assert count == 20
        assert window == 120

    def test_decorator_with_rate_limit(self, router_manager):
        """测试装饰器带限流"""

        @router_manager.get("mod", "/limited", rate_limit="10/minute")
        async def handler():
            return {"ok": True}

        assert len(router_manager._route_middlewares) > 0

    def test_register_http_route_with_rate_limit(self, router_manager):
        """测试传统注册带限流"""

        async def handler():
            return {"ok": True}

        router_manager.register_http_route(
            module_name="mod",
            path="/limited",
            handler=handler,
            methods=["GET"],
            rate_limit="5/minute",
        )

        assert len(router_manager._route_middlewares) > 0

    def test_cleanup_respects_per_route_window(self, router_manager):
        """回归测试：限流清理应按各路由实际窗口清理，而非固定默认窗口

        见 BUG-027：此前清理任务用固定 60s 窗口，导致 100/hour 限流规则
        的时间戳被提前清除，限流实际退化为 ~100/minute。
        """
        import time as _time

        now = _time.monotonic()
        # hour 级限流路由（窗口 3600s）：90 秒前的请求仍在窗口内
        hour_key = "route:/api/h:1.2.3.4"
        router_manager._rate_limit_store[hour_key] = [now - 90]
        router_manager._rate_limit_windows[hour_key] = 3600
        # minute 级限流路由（窗口 60s）：90 秒前的请求已超出窗口
        min_key = "route:/api/m:1.2.3.4"
        router_manager._rate_limit_store[min_key] = [now - 90]
        router_manager._rate_limit_windows[min_key] = 60

        removed = router_manager._cleanup_expired_rate_limits()

        # hour 路由时间戳在 3600s 窗口内，必须保留
        assert hour_key in router_manager._rate_limit_store
        # minute 路由时间戳已超出 60s 窗口，应被清除
        assert min_key not in router_manager._rate_limit_store
        assert min_key not in router_manager._rate_limit_windows
        assert removed == 1


# ==================== CORS / 安全头测试 ====================


class TestCorsAndSecurity:
    """CORS和安全头测试"""

    @pytest.fixture
    def router_manager(self):
        manager = RouterManager()
        yield manager

    def test_setup_cors(self, router_manager):
        """测试配置CORS"""
        router_manager.setup_cors(
            allow_origins=["https://example.com"],
            allow_methods=["GET", "POST"],
        )
        assert len(router_manager.app.user_middleware) > 0

    def test_setup_security_headers(self, router_manager):
        """测试配置安全头"""
        router_manager.setup_security_headers()
        assert len(router_manager.app.user_middleware) > 0

    def test_setup_security_headers_custom(self, router_manager):
        """测试自定义安全头"""
        router_manager.setup_security_headers(
            {
                "X-Custom": "test",
            }
        )
        assert len(router_manager.app.user_middleware) > 0

    def test_disable_docs(self, router_manager):
        """测试禁用API文档"""
        router_manager.disable_docs()
        assert router_manager.app.docs_url is None
        assert router_manager.app.redoc_url is None
        assert router_manager.app.openapi_url is None

    def test_set_docs_info(self, router_manager):
        """测试设置文档信息"""
        router_manager.set_docs_info(title="Test API", description="Test Desc")
        assert router_manager.app.title == "Test API"
        assert router_manager.app.description == "Test Desc"


# ==================== 命名空间管理测试 ====================


class TestNamespaceManagement:
    """命名空间管理测试"""

    @pytest.fixture
    def router_manager(self):
        manager = RouterManager()
        yield manager

    def test_list_namespaces(self, router_manager):
        """测试列出命名空间"""

        async def handler():
            return {}

        router_manager.register_http_route("mod_a", "/test", handler)
        router_manager.register_http_route("mod_b", "/test", handler)

        ns = router_manager.list_namespaces()
        assert "mod_a" in ns
        assert "mod_b" in ns

    def test_unregister_all_by_namespace(self, router_manager):
        """测试清理命名空间下所有路由"""

        async def handler():
            return {}

        async def ws_handler(ws):
            pass

        router_manager.register_http_route("mod", "/api", handler)
        router_manager.register_websocket("mod", "/ws", ws_handler)

        result = router_manager.unregister_all_by_namespace("mod")
        assert result["http_count"] == 1
        assert result["websocket_count"] == 1

    def test_unregister_all_nonexistent(self, router_manager):
        """测试清理不存在的命名空间"""
        result = router_manager.unregister_all_by_namespace("nonexistent")
        assert result["http_count"] == 0
        assert result["websocket_count"] == 0
