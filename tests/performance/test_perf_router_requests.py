"""
路由请求性能测试

度量 HTTP 端点响应延迟和吞吐量。
"""

import pytest
from fastapi.testclient import TestClient
from ErisPulse.Core.router import RouterManager


@pytest.fixture
def perf_client():
    mgr = RouterManager()
    return TestClient(mgr.app)


@pytest.fixture
def perf_router():
    mgr = RouterManager()
    mgr._http_routes.clear()
    return mgr, TestClient(mgr.app)


class TestRouterRequestsPerformance:
    def test_health_endpoint_latency(self, perf_client):
        """健康检查端点延迟"""
        for _ in range(100):
            resp = perf_client.get("/health")
            assert resp.status_code == 200

    def test_ping_endpoint_latency(self, perf_client):
        """ping 端点延迟"""
        for _ in range(100):
            resp = perf_client.get("/ping")
            assert resp.status_code == 200

    def test_custom_get_endpoint(self, perf_router):
        """自定义 GET 端点"""
        router_mgr, client = perf_router

        async def handler():
            return {"ok": True}

        router_mgr.register_http_route("api", "/test", handler, methods=["GET"])

        for _ in range(100):
            resp = client.get("/api/test")
            assert resp.status_code == 200

    def test_custom_post_endpoint(self, perf_router):
        """自定义 POST 端点"""
        router_mgr, client = perf_router

        async def handler():
            return {"created": True}

        router_mgr.register_http_route("api", "/create", handler, methods=["POST"])

        for _ in range(100):
            resp = client.post("/api/create", json={"data": "test"})
            assert resp.status_code == 200

    def test_multiple_routes_latency(self, perf_router):
        """多路由延迟"""
        router_mgr, client = perf_router

        for i in range(10):

            async def handler(_i=i):
                return {"route": _i}

            router_mgr.register_http_route("api", f"/r{i}", handler, methods=["GET"])

        for i in range(10):
            resp = client.get(f"/api/r{i}")
            assert resp.status_code == 200
            assert resp.json()["route"] == i

    def test_path_normalization_latency(self, perf_router):
        """路径规范化延迟"""
        router_mgr, client = perf_router

        async def handler():
            return {"normalized": True}

        router_mgr.register_http_route("deep", "a/b/c/d/e", handler, methods=["GET"])

        for _ in range(100):
            resp = client.get("/deep/a/b/c/d/e")
            assert resp.status_code == 200

    def test_core_routes_stability(self, perf_client):
        """核心路由稳定性"""
        for _ in range(200):
            health = perf_client.get("/health")
            ping = perf_client.get("/ping")
            assert health.status_code == 200
            assert ping.status_code == 200

    def test_register_unregister_cycle(self, perf_router):
        """注册注销循环"""
        router_mgr, client = perf_router

        for i in range(20):
            route_num = i

            async def handler(_n=route_num):
                return {"n": _n}

            path = f"/cycle/r{i}"
            router_mgr.register_http_route("cycle", path, handler, methods=["GET"])
            resp = client.get(path)
            assert resp.status_code == 200

            router_mgr.unregister_http_route("cycle", path)
            resp = client.get(path)
            assert resp.status_code == 404
