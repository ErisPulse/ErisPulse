"""
WebSocket 路由集成测试

使用 FastAPI TestClient 测试 WebSocket 连接、认证和消息收发。
"""

import pytest
from fastapi.testclient import TestClient

from ErisPulse.Core.router import RouterManager


@pytest.fixture
def router_mgr():
    mgr = RouterManager()
    mgr._http_routes.clear()
    mgr._websocket_routes.clear()
    return mgr


@pytest.fixture
def client(router_mgr):
    return TestClient(router_mgr.app)


class TestRouterWebSocketIntegration:
    """WebSocket 路由集成测试"""

    def test_basic_websocket_connect(self, router_mgr):
        """基本 WebSocket 连接和消息收发"""
        received_messages = []

        async def ws_handler(websocket):
            data = await websocket.receive_text()
            received_messages.append(data)
            await websocket.send_text(f"echo: {data}")

        router_mgr.register_websocket("ws_mod", "/ws", ws_handler)

        client = TestClient(router_mgr.app)

        with client.websocket_connect("/ws_mod/ws") as ws:
            ws.send_text("hello")
            response = ws.receive_text()
            assert response == "echo: hello"

        assert "hello" in received_messages

    def test_websocket_with_auth_accept(self, router_mgr):
        """WebSocket 认证通过"""
        auth_called = False

        async def auth_handler(websocket):
            nonlocal auth_called
            auth_called = True
            token = websocket.query_params.get("token", "")
            return token == "valid_token"

        async def ws_handler(websocket):
            await websocket.send_text("authenticated")

        router_mgr.register_websocket(
            "ws_mod",
            "/ws_auth",
            ws_handler,
            auth_handler=auth_handler,
            auto_accept=True,
        )

        client = TestClient(router_mgr.app)

        with client.websocket_connect("/ws_mod/ws_auth?token=valid_token") as ws:
            response = ws.receive_text()
            assert response == "authenticated"

        assert auth_called is True

    def test_websocket_with_auth_reject(self, router_mgr):
        """WebSocket 认证拒绝"""

        async def auth_handler(websocket):
            return False

        async def ws_handler(websocket):
            await websocket.send_text("should not reach")

        router_mgr.register_websocket(
            "ws_mod",
            "/ws_reject",
            ws_handler,
            auth_handler=auth_handler,
            auto_accept=True,
        )

        client = TestClient(router_mgr.app)

        with pytest.raises(Exception):
            with client.websocket_connect("/ws_mod/ws_reject") as ws:
                ws.receive_text()

    def test_websocket_no_auto_accept(self, router_mgr):
        """WebSocket 不自动 accept，手动 accept"""

        async def ws_handler(websocket):
            await websocket.accept()
            await websocket.send_text("manual accept")

        router_mgr.register_websocket(
            "ws_mod",
            "/ws_manual",
            ws_handler,
            auto_accept=False,
        )

        client = TestClient(router_mgr.app)

        with client.websocket_connect("/ws_mod/ws_manual") as ws:
            response = ws.receive_text()
            assert response == "manual accept"

    def test_websocket_unregister(self, router_mgr):
        """WebSocket 路由注销"""

        async def ws_handler(websocket):
            await websocket.receive_text()

        router_mgr.register_websocket("ws_mod", "/ws_temp", ws_handler)

        result = router_mgr.unregister_websocket("ws_mod", "/ws_temp")
        assert result is True

        result = router_mgr.unregister_websocket("ws_mod", "/ws_temp")
        assert result is False

    def test_websocket_duplicate_registration(self, router_mgr):
        """重复注册 WebSocket 路由"""

        async def h1(websocket):
            pass

        async def h2(websocket):
            pass

        router_mgr.register_websocket("ws_mod", "/ws_dup", h1)

        with pytest.raises(ValueError, match="已注册"):
            router_mgr.register_websocket("ws_mod", "/ws_dup", h2)

    def test_multiple_messages_in_one_connection(self, router_mgr):
        """单连接多消息"""

        async def ws_handler(websocket):
            while True:
                data = await websocket.receive_text()
                await websocket.send_text(data.upper())

        router_mgr.register_websocket("ws_mod", "/ws_multi", ws_handler)

        client = TestClient(router_mgr.app)

        with client.websocket_connect("/ws_mod/ws_multi") as ws:
            for msg in ["hello", "world", "test"]:
                ws.send_text(msg)
                response = ws.receive_text()
                assert response == msg.upper()

    def test_websocket_and_http_coexist(self, router_mgr):
        """WebSocket 和 HTTP 路由共存"""

        async def ws_handler(websocket):
            await websocket.send_text("ws_ok")

        async def http_handler():
            return {"http": "ok"}

        router_mgr.register_websocket("multi", "/ws", ws_handler)
        router_mgr.register_http_route("multi", "/api", http_handler, methods=["GET"])

        client = TestClient(router_mgr.app)

        with client.websocket_connect("/multi/ws") as ws:
            assert ws.receive_text() == "ws_ok"

        resp = client.get("/multi/api")
        assert resp.status_code == 200
