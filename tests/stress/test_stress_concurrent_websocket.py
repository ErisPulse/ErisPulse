"""
并发 WebSocket 压力测试

测试大量并发 WebSocket 连接和消息收发。
"""

import pytest
from fastapi.testclient import TestClient
from ErisPulse.Core.router import RouterManager


@pytest.fixture
def ws_router():
    mgr = RouterManager()
    mgr._http_routes.clear()
    mgr._websocket_routes.clear()
    return mgr


class TestConcurrentWebSocketStress:
    def test_50_sequential_connections(self, ws_router):
        """50 个顺序 WebSocket 连接"""
        connection_count = 0

        async def ws_handler(websocket):
            nonlocal connection_count
            connection_count += 1
            data = await websocket.receive_text()
            await websocket.send_text(f"ack:{data}")

        ws_router.register_websocket("stress", "/ws_seq", ws_handler)

        client = TestClient(ws_router.app)

        for i in range(50):
            with client.websocket_connect("/stress/ws_seq") as ws:
                ws.send_text(f"msg_{i}")
                resp = ws.receive_text()
                assert resp == f"ack:msg_{i}"

        assert connection_count == 50

    def test_multi_message_per_connection(self, ws_router):
        """单连接 100 条消息"""
        received_count = 0

        async def ws_handler(websocket):
            nonlocal received_count
            while True:
                data = await websocket.receive_text()
                received_count += 1
                await websocket.send_text(f"ok:{data}")

        ws_router.register_websocket("stress", "/ws_multi", ws_handler)

        client = TestClient(ws_router.app)

        with client.websocket_connect("/stress/ws_multi") as ws:
            for i in range(100):
                ws.send_text(f"m{i}")
                resp = ws.receive_text()
                assert resp == f"ok:m{i}"

        assert received_count == 100

    def test_long_message_content(self, ws_router):
        """长消息内容"""
        long_text = "x" * 10000

        async def ws_handler(websocket):
            data = await websocket.receive_text()
            await websocket.send_text(f"len:{len(data)}")

        ws_router.register_websocket("stress", "/ws_long", ws_handler)

        client = TestClient(ws_router.app)

        with client.websocket_connect("/stress/ws_long") as ws:
            ws.send_text(long_text)
            resp = ws.receive_text()
            assert resp == f"len:10000"

    def test_rapid_connect_disconnect_cycles(self, ws_router):
        """快速连接断开循环"""
        connect_count = 0

        async def ws_handler(websocket):
            nonlocal connect_count
            connect_count += 1
            await websocket.receive_text()

        ws_router.register_websocket("stress", "/ws_cycle", ws_handler)

        client = TestClient(ws_router.app)

        for _ in range(30):
            with client.websocket_connect("/stress/ws_cycle") as ws:
                ws.send_text("ping")

        assert connect_count == 30

    def test_websocket_auth_under_stress(self, ws_router):
        """认证 WebSocket 压力"""
        auth_attempts = 0
        auth_passes = 0

        async def auth_handler(websocket):
            nonlocal auth_attempts, auth_passes
            auth_attempts += 1
            idx = websocket.query_params.get("idx", "")
            if int(idx) % 2 == 0:
                auth_passes += 1
                return True
            return False

        async def ws_handler(websocket):
            await websocket.send_text("granted")

        ws_router.register_websocket(
            "stress",
            "/ws_auth_stress",
            ws_handler,
            auth_handler=auth_handler,
            auto_accept=True,
        )

        client = TestClient(ws_router.app)

        success_count = 0
        fail_count = 0

        for i in range(20):
            try:
                with client.websocket_connect(f"/stress/ws_auth_stress?idx={i}") as ws:
                    resp = ws.receive_text()
                    assert resp == "granted"
                    success_count += 1
            except Exception:
                fail_count += 1

        assert auth_attempts == 20
        assert success_count == 10
        assert fail_count == 10

    def test_websocket_and_http_mix(self, ws_router):
        """WebSocket 和 HTTP 混合请求"""

        async def ws_handler(websocket):
            await websocket.send_text("ws")

        async def http_handler():
            return {"http": True}

        ws_router.register_websocket("mix", "/ws", ws_handler)
        ws_router.register_http_route("mix", "/api", http_handler, methods=["GET"])

        client = TestClient(ws_router.app)

        for i in range(20):
            if i % 2 == 0:
                with client.websocket_connect("/mix/ws") as ws:
                    assert ws.receive_text() == "ws"
            else:
                resp = client.get("/mix/api")
                assert resp.status_code == 200
