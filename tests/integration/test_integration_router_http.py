"""
HTTP 路由集成测试

使用 FastAPI TestClient 测试路由注册、内置端点和自定义端点。
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


class TestRouterHTTPIntegration:
    """HTTP 路由集成测试"""

    def test_health_endpoint(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "service" in data
        assert "version" in data

    def test_ping_endpoint(self, client):
        resp = client.get("/ping")
        assert resp.status_code == 200
        data = resp.json()
        assert data["pong"] is True
        assert "timestamp" in data

    def test_register_custom_get_route(self, router_mgr):
        client = TestClient(router_mgr.app)

        async def handler():
            return {"info": "ok"}

        router_mgr.register_http_route("test_mod", "/info", handler, methods=["GET"])

        resp = client.get("/test_mod/info")
        assert resp.status_code == 200
        assert resp.json()["info"] == "ok"

    def test_register_custom_post_route(self, router_mgr):
        client = TestClient(router_mgr.app)

        async def handler():
            return {"result": "created"}

        router_mgr.register_http_route("api", "/create", handler, methods=["POST"])

        resp = client.post("/api/create")
        assert resp.status_code == 200

    def test_register_multiple_methods(self, router_mgr):
        client = TestClient(router_mgr.app)

        async def handler():
            return {"method": "ok"}

        router_mgr.register_http_route(
            "multi", "/endpoint", handler, methods=["GET", "POST"]
        )

        assert client.get("/multi/endpoint").status_code == 200
        assert client.post("/multi/endpoint").status_code == 200

    def test_unregister_route(self, router_mgr):
        client = TestClient(router_mgr.app)

        async def handler():
            return {"active": True}

        router_mgr.register_http_route("temp", "/data", handler, methods=["GET"])

        resp = client.get("/temp/data")
        assert resp.status_code == 200

        router_mgr.unregister_http_route("temp", "/data")

        resp = client.get("/temp/data")
        assert resp.status_code == 404

    def test_unregister_nonexistent_route(self, router_mgr):
        result = router_mgr.unregister_http_route("nope", "/nope")
        assert result is False

    def test_route_conflict_detection(self, router_mgr):
        async def h1():
            return {"a": 1}

        async def h2():
            return {"b": 2}

        router_mgr.register_http_route("m1", "/same", h1, methods=["GET"])

        with pytest.raises(ValueError, match="已注册"):
            router_mgr.register_http_route("m1", "/same", h2, methods=["GET"])

    def test_nonexistent_route_404(self, client):
        resp = client.get("/nonexistent/endpoint")
        assert resp.status_code == 404

    def test_path_normalization(self, router_mgr):
        client = TestClient(router_mgr.app)

        async def handler():
            return {"normalized": True}

        router_mgr.register_http_route("my_mod", "api/data", handler, methods=["GET"])

        resp = client.get("/my_mod/api/data")
        assert resp.status_code == 200
        assert resp.json()["normalized"] is True

    def test_multiple_modules_different_routes(self, router_mgr):
        client = TestClient(router_mgr.app)

        async def h1():
            return {"module": "a"}

        async def h2():
            return {"module": "b"}

        router_mgr.register_http_route("module_a", "/status", h1, methods=["GET"])
        router_mgr.register_http_route("module_b", "/status", h2, methods=["GET"])

        resp_a = client.get("/module_a/status")
        resp_b = client.get("/module_b/status")

        assert resp_a.status_code == 200
        assert resp_b.status_code == 200
        assert resp_a.json()["module"] == "a"
        assert resp_b.json()["module"] == "b"

    def test_webhook_alias(self, router_mgr):
        """register_webhook 是 register_http_route 的别名"""
        client = TestClient(router_mgr.app)

        async def handler():
            return {"webhook": True}

        router_mgr.register_webhook("wh", "/hook", handler, methods=["POST"])

        resp = client.post("/wh/hook")
        assert resp.status_code == 200

    def test_core_routes_after_unregister_all(self, router_mgr):
        """注销所有自定义路由后核心路由仍可用"""
        client = TestClient(router_mgr.app)

        async def handler():
            return {"custom": True}

        router_mgr.register_http_route("tmp", "/custom", handler, methods=["GET"])
        router_mgr.unregister_http_route("tmp", "/custom")

        assert client.get("/health").status_code == 200
        assert client.get("/ping").status_code == 200
