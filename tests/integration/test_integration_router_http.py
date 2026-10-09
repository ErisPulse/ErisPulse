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
        # 健康检查返回各组件状态
        assert "status" in data
        assert "router" in data
        assert "storage" in data
        assert "adapter" in data
        assert "module" in data
        assert data["status"] in ("ok", "degraded")

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

        # 断言稳定参数（路径），不依赖运行语言的本地化文案
        with pytest.raises(ValueError, match="/same"):
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


class TestTupleResponseConvention:
    """HTTP 元组返回约定（2.10+）：(body, status[, headers]) → 对应状态码 JSON"""

    def test_tuple_body_status_async(self, router_mgr):
        async def handler():
            return {"error": "unauthorized"}, 401

        router_mgr.register_http_route("tuple_mod", "/a", handler, methods=["GET"])
        client = TestClient(router_mgr.app)
        resp = client.get("/tuple_mod/a")
        assert resp.status_code == 401
        assert resp.json() == {"error": "unauthorized"}

    def test_tuple_body_status_sync(self, router_mgr):
        def handler():
            return {"error": "boom"}, 502

        router_mgr.register_http_route("tuple_mod", "/b", handler, methods=["GET"])
        client = TestClient(router_mgr.app)
        resp = client.get("/tuple_mod/b")
        assert resp.status_code == 502
        assert resp.json() == {"error": "boom"}

    def test_tuple_with_headers(self, router_mgr):
        async def handler():
            return {"ok": True}, 201, {"X-Custom": "yes"}

        router_mgr.register_http_route("tuple_mod", "/c", handler, methods=["GET"])
        client = TestClient(router_mgr.app)
        resp = client.get("/tuple_mod/c")
        assert resp.status_code == 201
        assert resp.headers["x-custom"] == "yes"
        assert resp.json() == {"ok": True}

    def test_dict_return_unchanged(self, router_mgr):
        """dict 返回保持既有行为（200 JSON）"""
        async def handler():
            return {"data": 1}

        router_mgr.register_http_route("tuple_mod", "/d", handler, methods=["GET"])
        client = TestClient(router_mgr.app)
        resp = client.get("/tuple_mod/d")
        assert resp.status_code == 200
        assert resp.json() == {"data": 1}

    def test_respond_helper(self, router_mgr):
        """respond() 帮助函数：message 合并进响应体"""
        from ErisPulse import respond

        async def handler():
            return respond({"user_id": 1}, status_code=401, message="unauthorized")

        router_mgr.register_http_route("tuple_mod", "/e", handler, methods=["GET"])
        client = TestClient(router_mgr.app)
        resp = client.get("/tuple_mod/e")
        assert resp.status_code == 401
        assert resp.json() == {"user_id": 1, "message": "unauthorized"}

    def test_request_injected_handler_tuple(self, router_mgr):
        """注入 HttpRequest 的 handler 同样支持元组返回"""
        from ErisPulse.Core.Bases import HttpRequest

        async def handler(request: HttpRequest):
            return {"msg": "teapot"}, 418

        router_mgr.register_http_route("tuple_mod", "/f", handler, methods=["GET"])
        client = TestClient(router_mgr.app)
        resp = client.get("/tuple_mod/f")
        assert resp.status_code == 418
        assert resp.json() == {"msg": "teapot"}
