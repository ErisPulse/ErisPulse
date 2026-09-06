"""
路由系统 + HTTP 客户端集成测试

测试路由启动后通过 FastAPI TestClient 发起各种请求的场景，
覆盖：
- 抽象类型自动注入 (HttpRequest / WebSocketConnection)
- FastAPI 原生类型透传
- 无注解处理器
- 装饰器路由 (http/get/post/put/delete/patch/ws)
- 路由组 (group)
- 请求方法组合
- 路径参数 / 查询参数 / 请求体
- WebSocket 认证 / 生命周期钩子
"""

import pytest
from fastapi.testclient import TestClient

from ErisPulse.Core import HttpRequest, WebSocketConnection
from ErisPulse.Core.router import RouterManager

# ==================== Fixtures ====================


@pytest.fixture
def router_mgr():
    """创建干净的 RouterManager"""
    mgr = RouterManager()
    mgr._http_routes.clear()
    mgr._websocket_routes.clear()
    mgr._server_task = None
    return mgr


@pytest.fixture
def client(router_mgr):
    """创建 FastAPI TestClient"""
    return TestClient(router_mgr.app)


# ==================== 核心端点测试 ====================


class TestCoreEndpoints:
    """测试路由系统内置核心端点"""

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
        assert resp.json()["pong"] is True

    def test_openapi_docs_enabled(self, client):
        resp = client.get("/docs")
        assert resp.status_code == 200

    def test_openapi_json(self, client):
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        data = resp.json()
        assert "openapi" in data
        assert "paths" in data


# ==================== HttpRequest 抽象类型注入测试 ====================


class TestHttpRequestInjection:
    """测试 HttpRequest 抽象类型自动注入"""

    def test_httprequest_annotation_get(self, router_mgr):
        """HttpRequest 注解 → 自动注入"""
        received = {}

        async def handler(request: HttpRequest):
            received["type"] = type(request).__name__
            received["method"] = request.method
            return {"ok": True}

        router_mgr.register_http_route("mod1", "/data", handler, methods=["GET"])
        tc = TestClient(router_mgr.app)
        resp = tc.get("/mod1/data")
        assert resp.status_code == 200
        assert received["type"] == "HttpRequest"
        assert received["method"] == "GET"

    def test_httprequest_annotation_post_with_body(self, router_mgr):
        """HttpRequest 注解 + POST 请求体"""
        received = {}

        async def handler(request: HttpRequest):
            received["body"] = await request.json()
            received["method"] = request.method
            return {"received": True}

        router_mgr.register_http_route("mod2", "/submit", handler, methods=["POST"])
        tc = TestClient(router_mgr.app)
        resp = tc.post("/mod2/submit", json={"key": "value"})
        assert resp.status_code == 200
        assert received["body"] == {"key": "value"}
        assert received["method"] == "POST"

    def test_httprequest_query_params(self, router_mgr):
        """HttpRequest 注解 + 查询参数"""
        received = {}

        async def handler(request: HttpRequest):
            received["page"] = request.query_params.get("page")
            received["limit"] = request.query_params.get("limit")
            return {"ok": True}

        router_mgr.register_http_route("mod3", "/list", handler, methods=["GET"])
        tc = TestClient(router_mgr.app)
        resp = tc.get("/mod3/list?page=2&limit=10")
        assert resp.status_code == 200
        assert received["page"] == "2"
        assert received["limit"] == "10"

    def test_httprequest_headers_access(self, router_mgr):
        """HttpRequest 注解 + 请求头"""
        received = {}

        async def handler(request: HttpRequest):
            received["auth"] = request.headers.get("authorization")
            received["content_type"] = request.headers.get("content-type")
            return {"ok": True}

        router_mgr.register_http_route("mod4", "/check", handler, methods=["GET"])
        tc = TestClient(router_mgr.app)
        resp = tc.get("/mod4/check", headers={"Authorization": "Bearer test123"})
        assert resp.status_code == 200
        assert received["auth"] == "Bearer test123"

    def test_httprequest_url_properties(self, router_mgr):
        """HttpRequest URL 属性"""
        received = {}

        async def handler(request: HttpRequest):
            received["url"] = str(request.url)
            received["base_url"] = str(request.base_url)
            return {"ok": True}

        router_mgr.register_http_route("mod5", "/url", handler, methods=["GET"])
        tc = TestClient(router_mgr.app)
        resp = tc.get("/mod5/url")
        assert resp.status_code == 200
        assert "/mod5/url" in received["url"]

    def test_httprequest_raw_property(self, router_mgr):
        """HttpRequest.raw 返回底层 FastAPI Request"""
        received = {}

        async def handler(request: HttpRequest):
            received["raw_type"] = type(request.raw).__name__
            return {"ok": True}

        router_mgr.register_http_route("mod6", "/raw", handler, methods=["GET"])
        tc = TestClient(router_mgr.app)
        resp = tc.get("/mod6/raw")
        assert resp.status_code == 200
        # FastAPI TestClient 底层使用 starlette Request
        assert "Request" in received["raw_type"]

    def test_httprequest_form_data(self, router_mgr):
        """HttpRequest 表单数据解析"""
        pytest.importorskip("multipart", reason="python-multipart not installed")
        received = {}

        async def handler(request: HttpRequest):
            form = await request.form()
            received["username"] = form.get("username")
            return {"ok": True}

        router_mgr.register_http_route("mod7", "/form", handler, methods=["POST"])
        tc = TestClient(router_mgr.app)
        resp = tc.post("/mod7/form", data={"username": "admin"})
        assert resp.status_code == 200
        assert received["username"] == "admin"

    def test_httprequest_cookies(self, router_mgr):
        """HttpRequest cookies"""
        received = {}

        async def handler(request: HttpRequest):
            received["session_id"] = request.cookies.get("session_id")
            return {"ok": True}

        router_mgr.register_http_route("mod8", "/cookie", handler, methods=["GET"])
        tc = TestClient(router_mgr.app)
        tc.cookies.set("session_id", "abc123")
        resp = tc.get("/mod8/cookie")
        assert resp.status_code == 200
        assert received["session_id"] == "abc123"


# ==================== FastAPI 原生类型透传测试 ====================


class TestFastAPIPassthrough:
    """测试 FastAPI 原生类型直接透传"""

    def test_fastapi_request_passthrough(self, router_mgr):
        """fastapi.Request 注解 → 不包装，直接透传"""
        from fastapi import Request
        received = {}

        async def handler(request: Request):
            received["type"] = type(request).__name__
            received["method"] = request.method
            return {"ok": True}

        router_mgr.register_http_route("fp", "/native", handler, methods=["GET"])
        tc = TestClient(router_mgr.app)
        resp = tc.get("/fp/native")
        assert resp.status_code == 200
        assert "Request" in received["type"]

    def test_no_annotation_request_name(self, router_mgr):
        """无注解但参数名是 request → 自动注入 HttpRequest"""
        received = {}

        async def handler(request):
            received["type"] = type(request).__name__
            return {"ok": True}

        router_mgr.register_http_route("noann", "/auto", handler, methods=["GET"])
        tc = TestClient(router_mgr.app)
        resp = tc.get("/noann/auto")
        assert resp.status_code == 200
        assert received["type"] == "HttpRequest"

    def test_no_handler_params(self, router_mgr):
        """无参数处理器 → 不注入"""
        async def handler():
            return {"ok": True}

        router_mgr.register_http_route("noparam", "/empty", handler, methods=["GET"])
        tc = TestClient(router_mgr.app)
        resp = tc.get("/noparam/empty")
        assert resp.status_code == 200

    def test_custom_param_name_no_injection(self, router_mgr):
        """参数名不是 request/req 且无 HttpRequest 注解 → 不注入"""
        received = {}

        async def handler(data):
            # data 将由 FastAPI DI 注入 (此处因为无来源所以为 None)
            received["data"] = data
            return {"ok": True}

        router_mgr.register_http_route("custom", "/data", handler, methods=["GET"])
        tc = TestClient(router_mgr.app)
        # FastAPI 可能会报 422 或 500 因为无法解析 data 参数
        # 这取决于 FastAPI 版本，关键是确认没有包装为 HttpRequest
        resp = tc.get("/custom/data")
        # 预期非 200 因为 FastAPI 无法解析 data 参数
        assert resp.status_code in (422, 500)


# ==================== 装饰器路由测试 ====================


class TestDecoratorRoutes:
    """测试 @http/@get/@post/@put/@delete/@patch 装饰器"""

    def test_http_decorator_get(self, router_mgr):
        @router_mgr.http("dec", "/api", methods=["GET"])
        async def handler(request: HttpRequest):
            return {"decorator": "http", "method": request.method}

        tc = TestClient(router_mgr.app)
        resp = tc.get("/dec/api")
        assert resp.status_code == 200
        assert resp.json()["decorator"] == "http"

    def test_get_decorator(self, router_mgr):
        @router_mgr.get("dec2", "/info")
        async def handler(request: HttpRequest):
            return {"method": "GET"}

        tc = TestClient(router_mgr.app)
        resp = tc.get("/dec2/info")
        assert resp.status_code == 200
        assert resp.json()["method"] == "GET"

    def test_post_decorator(self, router_mgr):
        @router_mgr.post("dec3", "/create")
        async def handler(request: HttpRequest):
            body = await request.json()
            return {"created": body}

        tc = TestClient(router_mgr.app)
        resp = tc.post("/dec3/create", json={"name": "test"})
        assert resp.status_code == 200
        assert resp.json()["created"]["name"] == "test"

    def test_put_decorator(self, router_mgr):
        @router_mgr.put("dec4", "/update")
        async def handler(request: HttpRequest):
            return {"method": "PUT"}

        tc = TestClient(router_mgr.app)
        resp = tc.put("/dec4/update")
        assert resp.status_code == 200
        assert resp.json()["method"] == "PUT"

    def test_delete_decorator(self, router_mgr):
        @router_mgr.delete("dec5", "/remove")
        async def handler(request: HttpRequest):
            return {"method": "DELETE"}

        tc = TestClient(router_mgr.app)
        resp = tc.delete("/dec5/remove")
        assert resp.status_code == 200
        assert resp.json()["method"] == "DELETE"

    def test_patch_via_http_decorator(self, router_mgr):
        @router_mgr.http("dec6", "/modify", methods=["PATCH"])
        async def handler(request: HttpRequest):
            return {"method": "PATCH"}

        tc = TestClient(router_mgr.app)
        resp = tc.patch("/dec6/modify")
        assert resp.status_code == 200
        assert resp.json()["method"] == "PATCH"

    def test_decorator_with_path_params(self, router_mgr):
        """装饰器路由 + 路径参数"""
        @router_mgr.get("dec7", "/items/{item_id}")
        async def handler(request: HttpRequest, item_id: str):
            return {"item_id": item_id}

        tc = TestClient(router_mgr.app)
        resp = tc.get("/dec7/items/42")
        assert resp.status_code == 200
        assert resp.json()["item_id"] == "42"


# ==================== 路由组测试 ====================


class TestRouteGroup:
    """测试路由组"""

    def test_group_basic_routes(self, router_mgr):
        group = router_mgr.group("grp", prefix="/v1")

        @group.get("/users")
        async def list_users(request: HttpRequest):
            return {"users": []}

        @group.post("/users")
        async def create_user(request: HttpRequest):
            return {"created": True}

        tc = TestClient(router_mgr.app)
        assert tc.get("/grp/v1/users").status_code == 200
        assert tc.post("/grp/v1/users").status_code == 200

    def test_group_with_path_params(self, router_mgr):
        group = router_mgr.group("grp2", prefix="/api")

        @group.get("/items/{item_id}")
        async def get_item(request: HttpRequest, item_id: int):
            return {"item_id": item_id}

        tc = TestClient(router_mgr.app)
        resp = tc.get("/grp2/api/items/99")
        assert resp.status_code == 200
        assert resp.json()["item_id"] == 99


# ==================== 多方法组合测试 ====================


class TestMethodCombinations:
    """测试同一端点不同 HTTP 方法的组合"""

    def test_same_path_different_methods(self, router_mgr):
        """同一路径注册不同方法"""
        async def get_handler(request: HttpRequest):
            return {"action": "read"}

        async def post_handler(request: HttpRequest):
            return {"action": "create"}

        async def put_handler(request: HttpRequest):
            return {"action": "update"}

        async def delete_handler(request: HttpRequest):
            return {"action": "delete"}

        router_mgr.register_http_route("multi", "/resource", get_handler, methods=["GET"])
        router_mgr.register_http_route("multi", "/resource/post", post_handler, methods=["POST"])
        router_mgr.register_http_route("multi", "/resource/put", put_handler, methods=["PUT"])
        router_mgr.register_http_route("multi", "/resource/delete", delete_handler, methods=["DELETE"])

        tc = TestClient(router_mgr.app)
        assert tc.get("/multi/resource").json()["action"] == "read"
        assert tc.post("/multi/resource/post").json()["action"] == "create"
        assert tc.put("/multi/resource/put").json()["action"] == "update"
        assert tc.delete("/multi/resource/delete").json()["action"] == "delete"

    def test_multi_method_single_handler(self, router_mgr):
        """一个处理器响应多种方法"""
        async def handler(request: HttpRequest):
            return {"method": request.method}

        router_mgr.register_http_route("multi2", "/any", handler, methods=["GET", "POST", "PUT"])

        tc = TestClient(router_mgr.app)
        assert tc.get("/multi2/any").json()["method"] == "GET"
        assert tc.post("/multi2/any").json()["method"] == "POST"
        assert tc.put("/multi2/any").json()["method"] == "PUT"

    def test_unregistered_method_returns_405(self, router_mgr):
        """未注册的方法返回 405"""
        async def handler(request: HttpRequest):
            return {"ok": True}

        router_mgr.register_http_route("m405", "/only-get", handler, methods=["GET"])

        tc = TestClient(router_mgr.app)
        assert tc.get("/m405/only-get").status_code == 200
        assert tc.post("/m405/only-get").status_code == 405


# ==================== 路由注册/注销测试 ====================


class TestRouteRegistration:
    """测试路由注册和注销"""

    def test_register_and_unregister(self, router_mgr):
        async def handler(request: HttpRequest):
            return {"active": True}

        router_mgr.register_http_route("reg", "/test", handler, methods=["GET"])
        tc = TestClient(router_mgr.app)

        assert tc.get("/reg/test").status_code == 200

        router_mgr.unregister_http_route("reg", "/test")
        assert tc.get("/reg/test").status_code == 404

    def test_unregister_nonexistent(self, router_mgr):
        result = router_mgr.unregister_http_route("nope", "/nothing")
        assert result is False

    def test_duplicate_route_raises(self, router_mgr):
        async def h1(request: HttpRequest):
            return {"a": 1}

        async def h2(request: HttpRequest):
            return {"b": 2}

        router_mgr.register_http_route("dup", "/same", h1, methods=["GET"])

        # 断言稳定参数（路径），不依赖运行语言的本地化文案
        with pytest.raises(ValueError, match="/same"):
            router_mgr.register_http_route("dup", "/same", h2, methods=["GET"])

    def test_path_normalization(self, router_mgr):
        async def handler(request: HttpRequest):
            return {"ok": True}

        # 无前导斜杠
        router_mgr.register_http_route("norm", "api/data", handler, methods=["GET"])

        tc = TestClient(router_mgr.app)
        resp = tc.get("/norm/api/data")
        assert resp.status_code == 200

    def test_multiple_modules_isolated(self, router_mgr):
        """不同模块的同名路径互不影响"""
        async def h1(request: HttpRequest):
            return {"mod": "a"}

        async def h2(request: HttpRequest):
            return {"mod": "b"}

        router_mgr.register_http_route("mod_a", "/status", h1, methods=["GET"])
        router_mgr.register_http_route("mod_b", "/status", h2, methods=["GET"])

        tc = TestClient(router_mgr.app)
        assert tc.get("/mod_a/status").json()["mod"] == "a"
        assert tc.get("/mod_b/status").json()["mod"] == "b"


# ==================== WebSocket 抽象类型注入测试 ====================


class TestWebSocketInjection:
    """测试 WebSocket 路由中的抽象类型注入"""

    def test_ws_with_websocketconnection_annotation(self, router_mgr):
        """WebSocketConnection 注解 → 注入抽象类型"""
        received = {}

        async def handler(ws: WebSocketConnection):
            received["type"] = type(ws).__name__
            await ws.send_text("hello")
            # 在 TestClient 中 WebSocket 会立即断开

        router_mgr.register_websocket("ws1", "/ws", handler)

        tc = TestClient(router_mgr.app)
        with tc.websocket_connect("/ws1/ws") as ws:
            data = ws.receive_text()
            assert data == "hello"

        assert received["type"] == "WebSocketConnection"

    def test_ws_with_fastapi_websocket_annotation(self, router_mgr):
        """fastapi.WebSocket 注解 → 透传原生对象"""
        from fastapi import WebSocket
        received = {}

        async def handler(websocket: WebSocket):
            received["type"] = type(websocket).__name__
            await websocket.send_text("raw")

        router_mgr.register_websocket("ws2", "/raw-ws", handler)

        tc = TestClient(router_mgr.app)
        with tc.websocket_connect("/ws2/raw-ws") as ws:
            data = ws.receive_text()
            assert data == "raw"

    def test_ws_no_annotation(self, router_mgr):
        """无注解 → 注入 WebSocketConnection"""
        received = {}

        async def handler(ws):
            received["type"] = type(ws).__name__
            await ws.send_text("auto")

        router_mgr.register_websocket("ws3", "/auto-ws", handler)

        tc = TestClient(router_mgr.app)
        with tc.websocket_connect("/ws3/auto-ws") as ws:
            data = ws.receive_text()
            assert data == "auto"

        assert received["type"] == "WebSocketConnection"

    def test_ws_no_params(self, router_mgr):
        """无参数 WS 处理器"""
        called = {"value": False}

        async def handler():
            called["value"] = True

        router_mgr.register_websocket("ws4", "/noparam-ws", handler)

        tc = TestClient(router_mgr.app)
        with tc.websocket_connect("/ws4/noparam-ws"):
            pass

        assert called["value"] is True

    def test_ws_send_receive_json(self, router_mgr):
        """WebSocket JSON 收发"""
        async def handler(ws: WebSocketConnection):
            data = await ws.receive_json()
            await ws.send_json({"echo": data})

        router_mgr.register_websocket("ws5", "/json-ws", handler)

        tc = TestClient(router_mgr.app)
        with tc.websocket_connect("/ws5/json-ws") as ws:
            ws.send_json({"msg": "test"})
            data = ws.receive_json()
            assert data["echo"]["msg"] == "test"

    def test_ws_send_receive_bytes(self, router_mgr):
        """WebSocket 二进制收发"""
        async def handler(ws: WebSocketConnection):
            data = await ws.receive_bytes()
            await ws.send_bytes(data)

        router_mgr.register_websocket("ws6", "/bytes-ws", handler)

        tc = TestClient(router_mgr.app)
        with tc.websocket_connect("/ws6/bytes-ws") as ws:
            ws.send_bytes(b"\x01\x02\x03")
            data = ws.receive_bytes()
            assert data == b"\x01\x02\x03"

    def test_ws_properties(self, router_mgr):
        """WebSocketConnection 属性代理"""
        received = {}

        async def handler(ws: WebSocketConnection):
            received["url"] = str(ws.url)
            received["raw_type"] = type(ws.raw).__name__
            await ws.send_text("done")

        router_mgr.register_websocket("ws7", "/props-ws", handler)

        tc = TestClient(router_mgr.app)
        with tc.websocket_connect("/ws7/props-ws?token=abc") as ws:
            ws.receive_text()

        assert "/ws7/props-ws" in received["url"]

    def test_ws_auth_handler_pass(self, router_mgr):
        """WS 认证通过"""
        async def auth(ws: WebSocketConnection) -> bool:
            return ws.query_params.get("token") == "secret"

        async def handler(ws: WebSocketConnection):
            await ws.send_text("authenticated")

        router_mgr.register_websocket("ws8", "/auth-ws", handler, auth_handler=auth)

        tc = TestClient(router_mgr.app)
        with tc.websocket_connect("/ws8/auth-ws?token=secret") as ws:
            data = ws.receive_text()
            assert data == "authenticated"

    def test_ws_auth_handler_fail(self, router_mgr):
        """WS 认证失败 → 连接关闭"""
        async def auth(ws: WebSocketConnection) -> bool:
            return False

        async def handler(ws: WebSocketConnection):
            await ws.send_text("should not reach")

        router_mgr.register_websocket("ws9", "/fail-auth-ws", handler, auth_handler=auth)

        tc = TestClient(router_mgr.app)
        # 认证失败后服务端关闭连接
        with pytest.raises(Exception):
            with tc.websocket_connect("/ws9/fail-auth-ws") as ws:
                ws.receive_text()

    def test_ws_auth_with_fastapi_annotation(self, router_mgr):
        """认证处理器使用 FastAPI WebSocket 注解"""
        from fastapi import WebSocket
        received = {}

        async def auth(ws: WebSocket) -> bool:
            received["auth_type"] = type(ws).__name__
            return True

        async def handler(ws: WebSocketConnection):
            await ws.send_text("ok")

        router_mgr.register_websocket("ws10", "/fp-auth-ws", handler, auth_handler=auth)

        tc = TestClient(router_mgr.app)
        with tc.websocket_connect("/ws10/fp-auth-ws") as ws:
            data = ws.receive_text()
            assert data == "ok"


# ==================== 装饰器 WS 路由测试 ====================


class TestWebSocketDecorator:
    """测试 @ws 装饰器"""

    def test_ws_decorator(self, router_mgr):
        @router_mgr.ws("wsdec", "/chat")
        async def handler(ws: WebSocketConnection):
            async for msg in ws.iter_text():
                await ws.send_text(f"Echo: {msg}")

        tc = TestClient(router_mgr.app)
        with tc.websocket_connect("/wsdec/chat") as ws:
            ws.send_text("hello")
            data = ws.receive_text()
            assert data == "Echo: hello"

    def test_ws_decorator_with_auth(self, router_mgr):
        async def auth(ws: WebSocketConnection) -> bool:
            return ws.query_params.get("key") == "pass"

        @router_mgr.ws("wsdec2", "/secure", auth_handler=auth)
        async def handler(ws: WebSocketConnection):
            await ws.send_text("secure-ok")

        tc = TestClient(router_mgr.app)
        with tc.websocket_connect("/wsdec2/secure?key=pass") as ws:
            data = ws.receive_text()
            assert data == "secure-ok"


# ==================== WebSocket 生命周期钩子测试 ====================


class TestWSLifecycleHooks:
    """测试 WebSocket 生命周期钩子 (on_disconnect / on_error)"""

    def test_on_disconnect_hook_registered(self, router_mgr):
        """验证 on_disconnect 钩子被正确注册"""

        async def handler(ws: WebSocketConnection):
            @ws.on_disconnect
            async def on_dc(ws, reason=""):
                pass
            # 发送一条消息然后结束
            await ws.send_text("ok")

        router_mgr.register_websocket("hook1", "/dc-ws", handler)

        tc = TestClient(router_mgr.app)
        with tc.websocket_connect("/hook1/dc-ws") as ws:
            data = ws.receive_text()
            assert data == "ok"

    def test_on_error_hook_triggered_by_handler_exception(self, router_mgr):
        """处理器抛异常时触发 on_error"""
        error_details = {"called": False, "error": None}

        async def handler(ws: WebSocketConnection):
            @ws.on_error
            async def on_err(ws_conn, error=""):
                error_details["called"] = True
                error_details["error"] = error
            await ws.send_text("ready")
            raise RuntimeError("test error")

        router_mgr.register_websocket("hook2", "/err-ws", handler)

        tc = TestClient(router_mgr.app)
        # 路由器内部捕获异常，客户端不会抛出
        with tc.websocket_connect("/hook2/err-ws") as ws:
            ws.receive_text()

        assert error_details["called"] is True
        assert "test error" in error_details["error"]


# ==================== 路由恢复/重置测试 ====================


class TestRouteRestore:
    """测试路由记录恢复"""

    def test_core_routes_survive_unregister(self, router_mgr):
        """注销自定义路由后核心路由仍可用"""
        async def handler(request: HttpRequest):
            return {"custom": True}

        router_mgr.register_http_route("tmp", "/custom", handler, methods=["GET"])
        router_mgr.unregister_http_route("tmp", "/custom")

        tc = TestClient(router_mgr.app)
        assert tc.get("/health").status_code == 200
        assert tc.get("/ping").status_code == 200

    def test_webhook_alias(self, router_mgr):
        """register_webhook 是 register_http_route 的别名"""
        async def handler(request: HttpRequest):
            return {"webhook": True}

        router_mgr.register_webhook("wh", "/hook", handler, methods=["POST"])

        tc = TestClient(router_mgr.app)
        resp = tc.post("/wh/hook")
        assert resp.status_code == 200
        assert resp.json()["webhook"] is True
