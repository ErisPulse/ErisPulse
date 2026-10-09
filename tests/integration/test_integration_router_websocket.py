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

        # 断言稳定参数（路径），不依赖运行语言的本地化文案
        with pytest.raises(ValueError, match="/ws_dup"):
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


class TestConnectionPoolIntegration:
    """连接池自动登记集成测试（2.10+）"""

    @pytest.fixture(autouse=True)
    def _clean_connections(self):
        from ErisPulse import connections

        connections.clear()
        yield
        connections.clear()

    def test_ws_connection_auto_registered(self, router_mgr):
        """WS 连接建立时自动登记进连接池，断开自动注销"""
        seen = {}

        async def ws_handler(websocket):
            seen["id"] = websocket.id
            seen["namespace"] = websocket.namespace
            seen["owner"] = websocket.owner
            await websocket.send_text(websocket.id)
            # 保持连接直到客户端要求退出（handler 返回即触发注销）
            while True:
                if await websocket.receive_text() == "quit":
                    break

        router_mgr.register_websocket("pool_mod", "/ws", ws_handler)
        client = TestClient(router_mgr.app)

        from ErisPulse import connections

        with client.websocket_connect("/pool_mod/ws") as ws:
            cid = ws.receive_text()
            assert cid == seen["id"]
            assert cid.startswith("pool_mod:")
            assert seen["namespace"] == "pool_mod"
            assert seen["owner"] == "pool_mod"
            live = connections.list(namespace="pool_mod")
            assert [c.id for c in live] == [cid]
            ws.send_text("quit")

        # 连接断开后自动注销
        assert connections.list(namespace="pool_mod") == []

    def test_join_group_and_broadcast(self, router_mgr):
        """handler 内 join_group 后可被 connections.broadcast 定向推送"""
        from ErisPulse import connections

        async def ws_handler(websocket):
            websocket.join_group("it-room")
            await websocket.send_text("joined")
            cmd = await websocket.receive_text()
            if cmd == "broadcast":
                result = await connections.broadcast({"event": "go"}, group="it-room")
                await websocket.send_text(f"ok:{result.total}:{len(result.sent)}")

        router_mgr.register_websocket("pool_mod", "/ws_bcast", ws_handler)
        client = TestClient(router_mgr.app)

        with client.websocket_connect("/pool_mod/ws_bcast") as ws:
            assert ws.receive_text() == "joined"
            ws.send_text("broadcast")
            # 自身也在 it-room：先收到广播 JSON，再收到结果回执
            assert ws.receive_json() == {"event": "go"}
            assert ws.receive_text() == "ok:1:1"

    def test_track_false_skips_registration(self, router_mgr):
        """track=False 时连接不进连接池"""
        from ErisPulse import connections

        async def ws_handler(websocket):
            assert websocket.id == ""
            await websocket.send_text("untracked")

        router_mgr.register_websocket("pool_mod", "/ws_raw", ws_handler, track=False)
        client = TestClient(router_mgr.app)

        with client.websocket_connect("/pool_mod/ws_raw") as ws:
            assert ws.receive_text() == "untracked"
            assert connections.list(namespace="pool_mod") == []
