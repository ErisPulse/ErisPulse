"""
事件处理器过滤链单元测试（2.8.0 统一控制面管线）

验证 ``BaseEventHandler._process_event`` 的三重 AND 过滤：
条件函数（代码内）× 模块维度（scope.platforms/bots/sessions）
× 文本过滤（scope.handlers.<module> pattern/regex）。
"""

import pytest

from ErisPulse.Core.Event.base import BaseEventHandler
from ErisPulse.Core.scope import scope
from ErisPulse.runtime.context import owner_scope


@pytest.fixture
def isolated_scope():
    """隔离全局 scope 单例配置，测试后恢复"""
    saved = {
        key: dict(value) if isinstance(value, dict) else value
        for key, value in scope._bindings.items()
    }
    yield scope
    scope._bindings.clear()
    scope._bindings.update(saved)
    scope._invalidate_cache()


def _make_event(**overrides) -> dict:
    event = {
        "platform": "test",
        "user_id": "u1",
        "type": "message",
        "detail_type": "private",
        "alt_message": "签到成功",
    }
    event.update(overrides)
    return event


class TestFilterChain:
    """三重 AND 过滤链管线测试"""

    async def test_condition_false_blocks_handler(self, isolated_scope):
        """条件函数返回 False → 处理器不执行"""
        ran = []

        def cond(event):
            return False

        h = BaseEventHandler("")
        with owner_scope("TestModule"):
            h.register(lambda e: ran.append(1), condition=cond)

        await h._process_event(_make_event())
        assert ran == []

    async def test_condition_true_allows_handler(self, isolated_scope):
        """条件函数返回 True（无 scope 限制）→ 处理器执行"""
        ran = []

        def cond(event):
            return True

        h = BaseEventHandler("")
        with owner_scope("TestModule"):
            h.register(lambda e: ran.append(1), condition=cond)

        await h._process_event(_make_event())
        assert ran == [1]

    async def test_module_dimension_blocked_blocks_handler(self, isolated_scope):
        """模块维度 blocked 命中 owner → 处理器不执行（静默）"""
        ran = []
        isolated_scope._bindings["platforms"]["test"] = {"blocked": ["TestModule"]}
        isolated_scope._invalidate_cache()

        h = BaseEventHandler("")
        with owner_scope("TestModule"):
            h.register(lambda e: ran.append(1))

        await h._process_event(_make_event())
        assert ran == []

    async def test_module_dimension_modules_whitelist_blocks_other(self, isolated_scope):
        """模块维度白名单未命中 owner → 处理器不执行"""
        ran = []
        isolated_scope._bindings["platforms"]["test"] = {"modules": ["OtherModule"]}
        isolated_scope._invalidate_cache()

        h = BaseEventHandler("")
        with owner_scope("TestModule"):
            h.register(lambda e: ran.append(1))

        await h._process_event(_make_event())
        assert ran == []

    async def test_handler_pattern_mismatch_blocks_handler(self, isolated_scope):
        """scope.handlers pattern 不命中文本 → 处理器不执行"""
        ran = []
        isolated_scope._bindings["handlers"]["TestModule"] = {"pattern": "打卡*"}
        isolated_scope._invalidate_cache()

        h = BaseEventHandler("")
        with owner_scope("TestModule"):
            h.register(lambda e: ran.append(1))

        # 事件文本为"签到成功"，不匹配"打卡*"
        await h._process_event(_make_event())
        assert ran == []

    async def test_handler_regex_hit_allows_handler(self, isolated_scope):
        """scope.handlers regex 命中文本 → 处理器执行"""
        ran = []
        isolated_scope._bindings["handlers"]["TestModule"] = {"regex": "re:\\d+元"}
        isolated_scope._invalidate_cache()

        h = BaseEventHandler("")
        with owner_scope("TestModule"):
            h.register(lambda e: ran.append(1))

        await h._process_event(_make_event(alt_message="支付42元"))
        assert ran == [1]

    async def test_triple_and_all_must_pass(self, isolated_scope):
        """三重过滤同时生效：条件与文本均命中但模块被禁 → 不执行"""
        ran = []
        isolated_scope._bindings["handlers"]["TestModule"] = {"pattern": "签到*"}
        isolated_scope._bindings["platforms"]["test"] = {"blocked": ["TestModule"]}
        isolated_scope._invalidate_cache()

        h = BaseEventHandler("")
        with owner_scope("TestModule"):
            h.register(lambda e: ran.append(1), condition=lambda e: True)

        await h._process_event(_make_event())  # 文本命中，但模块维度拒绝
        assert ran == []

    async def test_ownerless_handler_bypasses_scope_filters(self, isolated_scope):
        """无 owner（框架级）处理器跳过模块维度与文本过滤"""
        ran = []
        isolated_scope._bindings["handlers"]["TestModule"] = {"pattern": "打卡*"}
        isolated_scope._bindings["platforms"]["test"] = {"blocked": ["TestModule"]}
        isolated_scope._invalidate_cache()

        h = BaseEventHandler("")
        # 不在 owner_scope 内注册 → owner 为空
        h.register(lambda e: ran.append(1))

        await h._process_event(_make_event())
        assert ran == [1]

    async def test_scope_exempt_handler_bypasses_scope_filters(self, isolated_scope):
        """scope_exempt=True 处理器跳过模块维度与文本过滤"""
        ran = []
        isolated_scope._bindings["platforms"]["test"] = {"blocked": ["TestModule"]}
        isolated_scope._invalidate_cache()

        h = BaseEventHandler("")
        with owner_scope("TestModule"):
            h.register(lambda e: ran.append(1), scope_exempt=True)

        await h._process_event(_make_event())
        assert ran == [1]
