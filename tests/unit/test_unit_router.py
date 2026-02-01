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
            methods=["GET"]
        )
        
        # 验证
        assert "test_module" in router_manager._http_routes
        assert "/test_module/test" in router_manager._http_routes["test_module"]
        assert router_manager._http_routes["test_module"]["/test_module/test"] == test_handler
    
    def test_register_http_route_multiple_methods(self, router_manager):
        """测试注册多种HTTP方法的路由"""
        async def test_handler():
            return {"status": "ok"}
        
        # 执行
        router_manager.register_http_route(
            module_name="test_module",
            path="/test",
            handler=test_handler,
            methods=["GET", "POST", "PUT"]
        )
        
        # 验证路由存在
        route_exists = False
        for route in router_manager.app.router.routes:
            if hasattr(route, 'path') and route.path == "/test_module/test":
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
            module_name="test_module",
            path="/test",
            handler=handler1
        )
        
        # 第二次注册（应该抛出异常）
        with pytest.raises(ValueError, match="路径.*已注册"):
            router_manager.register_http_route(
                module_name="test_module",
                path="/test",
                handler=handler2
            )
    
    def test_unregister_http_route(self, router_manager):
        """测试取消注册HTTP路由"""
        async def test_handler():
            return {"status": "ok"}
        
        # 先注册
        router_manager.register_http_route(
            module_name="test_module",
            path="/test",
            handler=test_handler
        )
        
        # 执行取消注册
        result = router_manager.unregister_http_route("test_module", "/test")
        
        # 验证
        assert result is True
        assert "/test_module/test" not in router_manager._http_routes.get("test_module", {})
    
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
            module_name="test_module",
            path="/ws",
            handler=ws_handler
        )
        
        # 验证
        assert "test_module" in router_manager._websocket_routes
        assert "/test_module/ws" in router_manager._websocket_routes["test_module"]
        handler, auth = router_manager._websocket_routes["test_module"]["/test_module/ws"]
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
            auth_handler=auth_handler
        )
        
        # 验证
        handler, auth = router_manager._websocket_routes["test_module"]["/test_module/ws"]
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
            module_name="test_module",
            path="/ws",
            handler=handler1
        )
        
        # 第二次注册（应该抛出异常）
        with pytest.raises(ValueError, match="WebSocket路径.*已注册"):
            router_manager.register_websocket(
                module_name="test_module",
                path="/ws",
                handler=handler2
            )
    
    def test_unregister_websocket(self, router_manager):
        """测试取消注册WebSocket路由"""
        async def ws_handler(websocket: WebSocket):
            await websocket.close()
        
        # 先注册
        router_manager.register_websocket(
            module_name="test_module",
            path="/ws",
            handler=ws_handler
        )
        
        # 执行取消注册
        result = router_manager.unregister_websocket("test_module", "/ws")
        
        # 验证
        assert result is True
        assert "/test_module/ws" not in router_manager._websocket_routes.get("test_module", {})
    
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
            module_name="test_module",
            path="/webhook",
            handler=webhook_handler
        )
        
        # 验证（应该等同于register_http_route）
        assert "test_module" in router_manager._http_routes
        assert "/test_module/webhook" in router_manager._http_routes["test_module"]
    
    # ==================== 核心路由测试 ====================
    
    def test_core_routes_registered(self, router_manager):
        """测试核心路由已注册"""
        # 检查health路由
        health_exists = False
        routes_exists = False
        
        for route in router_manager.app.router.routes:
            if hasattr(route, 'path'):
                if route.path == "/health":
                    health_exists = True
                elif route.path == "/routes":
                    routes_exists = True
        
        # 验证
        assert health_exists, "health路由未注册"
        assert routes_exists, "routes路由未注册"
    
    # ==================== 服务器生命周期测试 ====================
    
    @pytest.mark.asyncio
    async def test_server_start(self, router_manager):
        """测试启动服务器"""
        # Mock serve函数
        with patch('ErisPulse.Core.router.serve', new_callable=AsyncMock) as mock_serve:
            mock_serve.return_value = None
            
            # 执行
            await router_manager.start(host="127.0.0.1", port=8888)
            
            # 验证
            assert router_manager.base_url == "http://127.0.0.1:8888"
            assert router_manager._server_task is not None
            mock_serve.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_server_start_with_ssl(self, router_manager):
        """测试启动带SSL的服务器"""
        with patch('ErisPulse.Core.router.serve', new_callable=AsyncMock) as mock_serve:
            mock_serve.return_value = None
            
            # 执行
            await router_manager.start(
                host="127.0.0.1",
                port=8888,
                ssl_certfile="cert.pem",
                ssl_keyfile="key.pem"
            )
            
            # 验证
            assert router_manager.base_url == "https://127.0.0.1:8888"
            mock_serve.assert_called_once()
            
            # 验证配置
            call_args = mock_serve.call_args
            config = call_args[0][1]  # 第二个参数是Config对象
            assert config.certfile == "cert.pem"
            assert config.keyfile == "key.pem"
    
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
    
    # ==================== URL格式化测试 ====================
    
    def test_format_display_url_localhost(self, router_manager):
        """测试格式化localhost URL"""
        # 执行
        result = router_manager._format_display_url("http://0.0.0.0:8000")
        
        # 验证
        assert result == "http://0.0.0.0:8000 (可访问: http://127.0.0.1:8000)"
    
    def test_format_display_url_ipv6(self, router_manager):
        """测试格式化IPv6 URL"""
        # 执行
        result = router_manager._format_display_url("http://[::]:8000")
        
        # 验证
        assert result == "http://[::]:8000 (可访问: http://localhost:8000)"
    
    def test_format_display_url_normal(self, router_manager):
        """测试格式化正常URL"""
        # 执行
        result = router_manager._format_display_url("http://example.com:8000")
        
        # 验证
        assert result == "http://example.com:8000"


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
        routes = [route.path for route in router.app.router.routes if hasattr(route, 'path')]
        
        # 验证核心路由存在
        assert "/health" in routes
        assert "/routes" in routes


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
            module_name="test_module",
            path="/lifecycle",
            handler=test_handler
        )
        
        # 验证已注册
        assert "/test_module/lifecycle" in router_manager._http_routes["test_module"]
