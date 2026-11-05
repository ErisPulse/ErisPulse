"""
嵌套生命周期（ownership.nest）单元测试

覆盖声明/解绑、环检测、回收顺序、子先亡、同步级联、超时与审计面。
"""

import asyncio

import pytest

from ErisPulse.Core.lifecycle import lifecycle
from ErisPulse.Core.ownership import ownership
from ErisPulse.runtime.context import owner_scope


@pytest.fixture(autouse=True)
def _clean_nested_state():
    ownership._nested_children.clear()
    ownership._nested_parents.clear()
    ownership._nested_inflight.clear()
    yield
    ownership._nested_children.clear()
    ownership._nested_parents.clear()
    ownership._nested_inflight.clear()


class TestNestApi:
    def test_nest_and_unnest(self):
        assert ownership.nest("parent", "child") is True
        assert ownership.nested_children("parent") == frozenset({"child"})
        assert ownership.unnest("parent", "child") is True
        assert ownership.nested_children("parent") == frozenset()
        assert ownership.unnest("parent", "child") is False

    def test_duplicate_nest_idempotent(self):
        assert ownership.nest("parent", "child") is True
        assert ownership.nest("parent", "child") is True
        assert len(ownership._nested_children["parent"]) == 1

    def test_self_cycle_rejected(self):
        assert ownership.nest("a", "a") is False
        assert ownership.nested_children("a") == frozenset()

    def test_reverse_chain_rejected(self):
        assert ownership.nest("a", "b") is True
        assert ownership.nest("b", "c") is True
        assert ownership.nest("c", "a") is False
        assert ownership.nested_children("c") == frozenset()

    def test_empty_names_rejected(self):
        assert ownership.nest("", "child") is False
        assert ownership.nest("parent", "") is False

    def test_multiple_parents(self):
        assert ownership.nest("p1", "child") is True
        assert ownership.nest("p2", "child") is True
        assert ownership.nested_children("p1") == frozenset({"child"})
        assert ownership.nested_children("p2") == frozenset({"child"})


class TestReclaimOrder:
    async def test_children_reclaimed_reverse_order_before_parent(
        self, monkeypatch
    ):
        ownership.nest("parent", "child_a")
        ownership.nest("parent", "child_b")
        order: list[str] = []

        async def fake_reclaim_tasks(owner: str):
            order.append(owner)
            return {}

        monkeypatch.setattr(ownership, "reclaim_tasks", fake_reclaim_tasks)
        monkeypatch.setattr(ownership, "reclaim_sync", lambda owner: {})

        result = await ownership.reclaim("parent")
        assert order == ["child_b", "child_a", "parent"]
        assert result["nested_children"] == 2
        assert ownership.nested_children("parent") == frozenset()

    async def test_recursive_grandchildren(self, monkeypatch):
        ownership.nest("parent", "child")
        ownership.nest("child", "grandchild")
        order: list[str] = []

        async def fake_reclaim_tasks(owner: str):
            order.append(owner)
            return {}

        monkeypatch.setattr(ownership, "reclaim_tasks", fake_reclaim_tasks)
        monkeypatch.setattr(ownership, "reclaim_sync", lambda owner: {})

        await ownership.reclaim("parent")
        assert order == ["grandchild", "child", "parent"]

    async def test_child_independent_reclaim_unnests(self):
        ownership.nest("parent", "child")
        await ownership.reclaim("child")
        assert ownership.nested_children("parent") == frozenset()

    def test_reclaim_sync_cascades_child_resources(self):
        def handler(data):
            pass

        with owner_scope("nested_child_sync"):
            lifecycle.register("test.nest.event", handler)

        assert ownership.counts("nested_child_sync").get("lifecycle_hooks") == 1
        ownership.nest("nested_parent_sync", "nested_child_sync")
        result = ownership.reclaim_sync("nested_parent_sync")
        assert result["nested_children"] == 1
        assert ownership.counts("nested_child_sync").get("lifecycle_hooks", 0) == 0
        assert ownership.nested_children("nested_parent_sync") == frozenset()

    def test_reclaim_sync_skips_cascade_when_inflight(self):
        def handler(data):
            pass

        with owner_scope("nested_inflight_child"):
            lifecycle.register("test.nest.event", handler)

        ownership.nest("nested_inflight_parent", "nested_inflight_child")
        assert ownership.begin_nested_reclaim("nested_inflight_parent") is True
        ownership.reclaim_sync("nested_inflight_parent")
        # 同步路径让位于异步级联，子资源保留
        assert ownership.counts("nested_inflight_child").get("lifecycle_hooks") == 1
        assert ownership.nested_children("nested_inflight_parent") == frozenset(
            {"nested_inflight_child"}
        )
        ownership.unnest("nested_inflight_parent", "nested_inflight_child")
        ownership.reclaim_sync("nested_inflight_child")

    async def test_timeout_removes_relation(self, monkeypatch):
        monkeypatch.setattr(
            "ErisPulse.Core.constants.CLEANUP_CALLBACK_TIMEOUT_SECS", 0.01
        )
        ownership.nest("parent_timeout", "child_timeout")

        async def slow_reclaim(owner: str):
            await asyncio.sleep(0.2)
            return {}

        monkeypatch.setattr(ownership, "reclaim", slow_reclaim)
        result = await ownership.reclaim_nested("parent_timeout")
        assert result == {"nested_children": 1}
        assert ownership.nested_children("parent_timeout") == frozenset()


    async def test_module_unload_cascades_nested(self):
        from ErisPulse.Core.Bases import BaseModule
        from ErisPulse.Core.module import ModuleManager

        class NestedParentModule(BaseModule):
            async def on_load(self, event):
                return True

            async def on_unload(self, event):
                return True

        manager = ModuleManager()
        manager._modules.clear()
        manager._module_classes.clear()
        manager._loaded_modules.clear()
        manager._module_info.clear()
        manager.register("nested_parent_module", NestedParentModule)
        assert await manager.load("nested_parent_module") is True

        def handler(data):
            pass

        with owner_scope("nested_module_child"):
            lifecycle.register("test.nest.event", handler)
        ownership.nest("nested_parent_module", "nested_module_child")

        assert await manager.unload("nested_parent_module") is True
        assert ownership.counts("nested_module_child").get("lifecycle_hooks", 0) == 0
        assert ownership.nested_children("nested_parent_module") == frozenset()


class TestCountsAndOrphans:
    def test_counts_include_nested(self):
        ownership.nest("parent", "child_a")
        ownership.nest("parent", "child_b")
        assert ownership.counts("parent")["nested"] == 2
        assert ownership.counts("child_a") == {}

    def test_orphans_excludes_governed_nested(self, monkeypatch):
        from ErisPulse.Core.module import module as module_manager

        ownership.nest("parent", "child")
        table = {
            "parent": {"commands": 1},
            "child": {"commands": 1},
            "ghost": {"commands": 1},
        }
        monkeypatch.setattr(ownership, "counts", lambda owner=None: table)
        monkeypatch.setattr(
            module_manager, "_module_classes", {"parent": object}, raising=False
        )
        orphan_names = [item["owner"] for item in ownership.orphans()]
        assert orphan_names == ["ghost"]

    def test_orphans_reports_child_when_parent_gone(self, monkeypatch):
        ownership.nest("missing_parent", "child")
        table = {
            "missing_parent": {"commands": 1},
            "child": {"commands": 1},
        }
        monkeypatch.setattr(ownership, "counts", lambda owner=None: table)
        orphan_names = [item["owner"] for item in ownership.orphans()]
        assert orphan_names == ["child", "missing_parent"]
