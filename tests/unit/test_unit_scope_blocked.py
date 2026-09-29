"""
scope.blocked 生命周期事件单元测试（方向十一配套：拦截可观测）

验证：作用域模块维度 / 身份维度拦截时广播 `scope.blocked` 生命周期事件，
放行时不广播；`is_shadow` 影子状态不影响事件广播。
"""

import asyncio
import importlib

from ErisPulse.Core.scope import ScopeManager

# importlib.import_module 返回真实子模块（Core.scope 包属性被单例遮蔽）
scope_module = importlib.import_module("ErisPulse.Core.scope")
lifecycle_module = importlib.import_module("ErisPulse.Core.lifecycle")


def _make_mgr(default_allow=True):
    mgr = ScopeManager()
    mgr._stats.update(
        {
            "module_calls": 0,
            "module_filtered": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "identity_checks": 0,
            "identity_denied": 0,
        }
    )
    if not default_allow:
        mgr.set_default_allow(False)
    return mgr


class TestScopeBlockedEvent:
    """scope.blocked：作用域拦截生命周期事件"""

    def test_module_dimension_blocked_fires_event(self):
        """模块维度：拦截时广播 scope.blocked，放行时不广播"""
        from ErisPulse.Core.lifecycle import lifecycle

        mgr = _make_mgr(default_allow=True)
        mgr.set_module("onebot11", modules=["chat"], persist=False)

        seen = []

        async def _hook(data):
            seen.append(dict(data or {}))

        lifecycle.register("scope.blocked", _hook)

        async def _run():
            assert mgr.is_allowed("onebot11", "123456", "ghost") is False
            await asyncio.sleep(0.05)
            assert mgr.is_allowed("onebot11", "123456", "chat") is True
            await asyncio.sleep(0.05)

        asyncio.run(_run())

        assert len(seen) == 1
        assert seen[0]["dimension"] == "module"
        assert seen[0]["module"] == "ghost"

    def test_identity_dimension_blocked_fires_event(self):
        """身份维度：拒绝时广播 scope.blocked"""
        from ErisPulse.Core.lifecycle import lifecycle

        mgr = _make_mgr(default_allow=True)
        mgr.set_identity("onebot11", user_id="baduser", deny=True, persist=False)

        seen = []

        async def _hook(data):
            seen.append(dict(data or {}))

        lifecycle.register("scope.blocked", _hook)

        async def _run():
            assert mgr.is_identity_allowed("onebot11", "123456", None, "baduser") is False
            await asyncio.sleep(0.05)
            assert mgr.is_identity_allowed("onebot11", "123456", None, "good") is True
            await asyncio.sleep(0.05)

        asyncio.run(_run())

        assert len(seen) == 1
        assert seen[0]["dimension"] == "identity"
        assert seen[0]["user_id"] == "baduser"

    def test_cache_hit_does_not_refire(self):
        """缓存命中不重复广播（同一组合只在缓存失效时触发）"""
        from ErisPulse.Core.lifecycle import lifecycle

        mgr = _make_mgr(default_allow=True)
        mgr.set_module("onebot11", blocked=["*"], persist=False)

        seen = []

        async def _hook(data):
            seen.append(dict(data or {}))

        lifecycle.register("scope.blocked", _hook)

        async def _run():
            for _ in range(5):
                assert mgr.is_allowed("onebot11", "123456", "room") is False
            await asyncio.sleep(0.05)

        asyncio.run(_run())

        assert len(seen) == 1
