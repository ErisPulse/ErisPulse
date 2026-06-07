"""
路由发现与 SSE 功能集成测试

在完整 ErisPulse 环境中验证：
1. RouterManager 路由注册（HTTP / WS / SSE）
2. RouterManager 路由发现（list_namespaces / get_module_routes / get_module_urls）
3. RouterManager 前缀聚合（get_module_urls_matching）
4. AdapterManager 连接信息（get_connection_info）
5. SSE 路由注册与 SseEmitter
6. 路由注销与清理（unregister_sse / unregister_all_by_namespace）

使用方式：
    python tests/devs/test_router_discovery.py
"""

import asyncio
import sys

from ErisPulse import sdk


async def test_router_register_and_discovery():
    """测试路由注册与发现"""
    router = sdk.router

    router.register_http_route(
        "_test_rdisc", "/webhook", lambda r: {"ok": True}, methods=["POST"]
    )
    router.register_http_route(
        "_test_rdisc", "/callback", lambda r: {"ok": True}, methods=["GET", "POST"]
    )
    router.register_websocket("_test_rdisc", "/ws", lambda ws: None)
    router.register_sse("_test_rdisc", "/events", lambda sse: None)

    # --- list_namespaces ---
    ns = router.list_namespaces()
    assert "_test_rdisc" in ns, f"_test_rdisc not in namespaces: {list(ns.keys())}"
    assert "/_test_rdisc/webhook" in ns["_test_rdisc"]["http"]
    assert "/_test_rdisc/callback" in ns["_test_rdisc"]["http"]
    assert "/_test_rdisc/ws" in ns["_test_rdisc"]["websocket"]
    assert "/_test_rdisc/events" in ns["_test_rdisc"]["sse"]
    print("[PASS] list_namespaces")

    # --- get_module_routes ---
    routes = router.get_module_routes("_test_rdisc")
    http_paths = [r["path"] for r in routes["http"]]
    assert "/_test_rdisc/webhook" in http_paths
    assert "/_test_rdisc/callback" in http_paths

    webhook_route = next(
        r for r in routes["http"] if r["path"] == "/_test_rdisc/webhook"
    )
    assert webhook_route["methods"] == ["POST"], (
        f"webhook methods: {webhook_route['methods']}"
    )

    callback_route = next(
        r for r in routes["http"] if r["path"] == "/_test_rdisc/callback"
    )
    assert set(callback_route["methods"]) == {"GET", "POST"}, (
        f"callback methods: {callback_route['methods']}"
    )

    assert len(routes["websocket"]) == 1
    assert routes["websocket"][0]["path"] == "/_test_rdisc/ws"

    assert len(routes["sse"]) == 1
    assert routes["sse"][0]["path"] == "/_test_rdisc/events"
    assert routes["sse"][0]["streaming"] is True
    print("[PASS] get_module_routes")

    # --- get_module_urls ---
    urls = router.get_module_urls("_test_rdisc")
    base = urls["base_url"]
    print(f"  base_url = {base!r}")

    http_url_items = [(u["path"], u["method"]) for u in urls["http"]]
    assert ("/_test_rdisc/webhook", "POST") in http_url_items
    assert ("/_test_rdisc/callback", "GET") in http_url_items
    assert ("/_test_rdisc/callback", "POST") in http_url_items

    assert len(urls["websocket"]) == 1
    assert len(urls["sse"]) == 1

    if base:
        assert urls["http"][0]["url"].startswith(base)
        ws_url = urls["websocket"][0]["url"]
        assert ws_url.startswith("ws://") or ws_url.startswith("wss://")
        assert urls["sse"][0]["url"].startswith(base)
    print("[PASS] get_module_urls")

    router.unregister_all_by_namespace("_test_rdisc")


async def test_prefix_matching():
    """测试前缀聚合匹配"""
    router = sdk.router
    saved_base = router.base_url
    router.base_url = "http://localhost:8080"

    try:
        # 命名空间命名规则：prefix_suffix，前缀匹配条件 ns == prefix 或 ns.startswith(prefix + "_")
        # prefix="_pmx" 匹配 _pmx_bot1 (因为 _pmx_bot1.startswith("_pmx_"))
        router.register_http_route(
            "_pmx_bot1", "/webhook", lambda r: None, methods=["POST"]
        )
        router.register_http_route(
            "_pmx_bot2", "/webhook", lambda r: None, methods=["POST"]
        )
        router.register_http_route(
            "_pmx_disc", "/webhook", lambda r: None, methods=["POST"]
        )
        router.register_sse("_pmx_bot1", "/events", lambda sse: None)

        # --- 前缀匹配："_pmx" 匹配全部（_pmx_bot1, _pmx_bot2, _pmx_disc） ---
        urls_all = router.get_module_urls_matching("_pmx")
        assert len(urls_all["http"]) == 3
        assert len(urls_all["sse"]) == 1
        assert urls_all["sse"][0]["namespace"] == "_pmx_bot1"
        print("[PASS] get_module_urls_matching (broad prefix)")

        # --- 精确匹配 ---
        exact = router.get_module_urls_matching("_pmx_disc")
        assert len(exact["http"]) == 1
        assert exact["http"][0]["namespace"] == "_pmx_disc"
        print("[PASS] get_module_urls_matching (exact)")

        # --- 无匹配 ---
        empty = router.get_module_urls_matching("_pmx_nonexist_xyz")
        assert len(empty["http"]) == 0
        assert len(empty["websocket"]) == 0
        assert len(empty["sse"]) == 0
        print("[PASS] get_module_urls_matching (no match)")

    finally:
        router.unregister_all_by_namespace("_pmx_bot1")
        router.unregister_all_by_namespace("_pmx_bot2")
        router.unregister_all_by_namespace("_pmx_disc")
        router.base_url = saved_base


async def test_sse_register_and_unregister():
    """测试 SSE 路由注册与注销"""
    router = sdk.router

    router.register_sse("_sse_mod", "/stream1", lambda sse: None)
    router.register_sse("_sse_mod", "/stream2", lambda sse: None)

    routes = router.get_module_routes("_sse_mod")
    assert len(routes["sse"]) == 2
    print("[PASS] SSE register (2 routes)")

    ok = router.unregister_sse("_sse_mod", "/stream1")
    assert ok is True

    routes = router.get_module_routes("_sse_mod")
    assert len(routes["sse"]) == 1
    assert routes["sse"][0]["path"] == "/_sse_mod/stream2"
    print("[PASS] SSE unregister")

    ok = router.unregister_sse("_sse_mod", "/nonexist")
    assert ok is False
    print("[PASS] SSE unregister (nonexist)")

    router.unregister_all_by_namespace("_sse_mod")


async def test_unregister_all_by_namespace():
    """测试命名空间清理"""
    router = sdk.router

    router.register_http_route("_clean_mod", "/api", lambda r: None, methods=["GET"])
    router.register_websocket("_clean_mod", "/ws", lambda ws: None)
    router.register_sse("_clean_mod", "/events", lambda sse: None)

    result = router.unregister_all_by_namespace("_clean_mod")
    assert result["http_count"] == 1
    assert result["websocket_count"] == 1
    assert result["sse_count"] == 1
    print("[PASS] unregister_all_by_namespace")

    routes = router.get_module_routes("_clean_mod")
    assert len(routes["http"]) == 0
    assert len(routes["websocket"]) == 0
    assert len(routes["sse"]) == 0
    print("[PASS] cleanup verified")


async def test_sse_emitter():
    """测试 SseEmitter 协议格式化"""
    from ErisPulse.Core.Bases.router import SseEmitter

    sent = []
    closed = False

    async def on_send(payload):
        sent.append(payload)

    async def on_close():
        nonlocal closed
        closed = True

    sse = SseEmitter(on_send=on_send, on_close=on_close)

    # --- send dict ---
    await sse.send({"msg": "hello"}, event="update")
    assert len(sent) == 1
    assert "event: update\n" in sent[0]
    assert "id: 1\n" in sent[0]
    assert 'data: {"msg": "hello"}\n' in sent[0]
    assert sent[0].endswith("\n\n")
    print("[PASS] SseEmitter send (dict)")

    # --- send string ---
    await sse.send("plain text")
    assert len(sent) == 2
    assert "data: plain text\n" in sent[1]
    assert "id: 2\n" in sent[1]
    print("[PASS] SseEmitter send (string)")

    # --- send with retry ---
    await sse.send("retry test", retry=5000)
    assert len(sent) == 3
    assert "retry: 5000\n" in sent[2]
    print("[PASS] SseEmitter send (retry)")

    # --- send with custom id ---
    await sse.send("custom id", id="custom-42")
    assert len(sent) == 4
    assert "id: custom-42\n" in sent[3]
    print("[PASS] SseEmitter send (custom id)")

    # --- close ---
    assert sse.closed is False
    await sse.close()
    assert sse.closed is True
    assert closed is True
    print("[PASS] SseEmitter close")

    # --- send after close ---
    try:
        await sse.send("should fail")
        assert False, "should raise RuntimeError"
    except RuntimeError:
        pass
    print("[PASS] SseEmitter send after close raises")

    # --- close idempotent ---
    await sse.close()
    assert sse.closed is True
    print("[PASS] SseEmitter close idempotent")


async def test_sse_emitter_multiline():
    """测试 SseEmitter 多行数据"""
    from ErisPulse.Core.Bases.router import SseEmitter

    sent = []

    async def on_send(payload):
        sent.append(payload)

    sse = SseEmitter(on_send=on_send)
    await sse.send("line1\nline2\nline3")
    assert len(sent) == 1
    assert "data: line1\ndata: line2\ndata: line3\n" in sent[0]
    print("[PASS] SseEmitter multiline data")


async def test_connection_info():
    """测试 AdapterManager.get_connection_info"""
    from ErisPulse.Core.Bases.adapter import BaseAdapter

    class TestAdapter(BaseAdapter):
        async def call_api(self, **kw):
            pass

        async def start(self):
            pass

        async def shutdown(self):
            pass

    router = sdk.router

    sdk.adapter.register("_test_conn", TestAdapter)
    router.register_http_route("_test_conn", "/hook", lambda r: None, methods=["POST"])
    router.register_sse("_test_conn", "/events", lambda sse: None)

    info = sdk.adapter.get_connection_info("_test_conn")
    assert info is not None, "get_connection_info returned None"
    assert info["platform"] == "_test_conn"
    assert info["status"] == "stopped"
    assert "connection" in info
    assert len(info["connection"]["http_routes"]) == 1
    assert len(info["connection"]["sse_routes"]) == 1
    print("[PASS] get_connection_info")

    info = sdk.adapter.get_connection_info("_nonexist_xyz")
    assert info is None
    print("[PASS] get_connection_info (nonexist)")

    router.unregister_all_by_namespace("_test_conn")


async def test_route_group_sse():
    """测试 RouteGroup.sse()"""
    router = sdk.router
    group = router.group("_grp_test", "/api", version="1")

    @group.sse("/live")
    async def live(sse):
        await sse.send("tick")

    routes = router.get_module_routes("_grp_test")
    sse_paths = [r["path"] for r in routes["sse"]]
    assert any("live" in p for p in sse_paths), f"sse paths: {sse_paths}"
    print("[PASS] RouteGroup.sse")

    router.unregister_all_by_namespace("_grp_test")


async def main():
    print("=" * 60)
    print("  路由发现与 SSE 功能集成测试")
    print("=" * 60)

    success = await sdk.init()
    if not success:
        print("SDK 初始化失败，退出")
        return 1

    tests = [
        ("路由注册与发现", test_router_register_and_discovery),
        ("前缀聚合匹配", test_prefix_matching),
        ("SSE 注册与注销", test_sse_register_and_unregister),
        ("命名空间清理", test_unregister_all_by_namespace),
        ("SseEmitter 协议", test_sse_emitter),
        ("SseEmitter 多行数据", test_sse_emitter_multiline),
        ("AdapterManager 连接信息", test_connection_info),
        ("RouteGroup SSE", test_route_group_sse),
    ]

    passed = 0
    failed = 0

    for name, func in tests:
        print(f"\n--- {name} ---")
        try:
            await func()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"  FAIL: {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"  通过: {passed}, 失败: {failed}")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
