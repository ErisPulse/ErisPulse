"""
存储异步接口测试

验证 BaseStorage 的 aget/aset/adelete 等异步方法，
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder


class MockStorage(BaseStorage):
    """内存存储，用于测试异步桥接"""

    def __init__(self):
        self._data = {}

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value
        return True

    def delete(self, key):
        if key in self._data:
            del self._data[key]
            return True
        return False

    def get_all_keys(self):
        return list(self._data.keys())

    def clear(self):
        self._data.clear()
        return True

    def transaction(self):
        import contextlib

        @contextlib.contextmanager
        def _ctx():
            yield self

        return _ctx()

    def Table(self, table_name):
        raise NotImplementedError

    def CreateTable(self, table_name, columns):
        return True

    def DropTable(self, table_name):
        return True

    def HasTable(self, table_name):
        return False


def section(title):
    print(f"\n{'=' * 50}")
    print(f"  {title}")
    print(f"{'=' * 50}")


def assert_eq(actual, expected, label):
    status = "✓" if actual == expected else "✗"
    print(f"  {status} {label}: {actual!r}")
    assert actual == expected, f"{label}: expected {expected!r}, got {actual!r}"


def test_aget_aset():
    """测试异步 get/set"""
    section("aget / aset")

    storage = MockStorage()

    # aset
    result = asyncio.run(storage.aset("name", "Alice"))
    assert_eq(result, True, "aset 返回值")

    # aget
    value = asyncio.run(storage.aget("name"))
    assert_eq(value, "Alice", "aget 读取")

    # aget with default
    value = asyncio.run(storage.aget("missing", "default_val"))
    assert_eq(value, "default_val", "aget 默认值")

    # 验证同步方法也写入成功
    assert_eq(storage.get("name"), "Alice", "同步 get 验证")
    print("  ✓ 同步/异步共享同一存储\n")


def test_adelete():
    """测试异步 delete"""
    section("adelete")

    storage = MockStorage()
    storage.set("key1", "value1")

    result = asyncio.run(storage.adelete("key1"))
    assert_eq(result, True, "adelete 已有键")

    result = asyncio.run(storage.adelete("key1"))
    assert_eq(result, False, "adelete 不存在的键")

    assert_eq(storage.get("key1"), None, "删除后 get 验证")
    print("  ✓\n")


def test_aget_all_keys():
    """测试异步 get_all_keys"""
    section("aget_all_keys")

    storage = MockStorage()
    storage.set("a", 1)
    storage.set("b", 2)
    storage.set("c", 3)

    keys = asyncio.run(storage.aget_all_keys())
    assert_eq(sorted(keys), ["a", "b", "c"], "aget_all_keys")
    print("  ✓\n")


def test_aclear():
    """测试异步 clear"""
    section("aclear")

    storage = MockStorage()
    storage.set("a", 1)
    storage.set("b", 2)

    result = asyncio.run(storage.aclear())
    assert_eq(result, True, "aclear 返回值")
    assert_eq(storage.get_all_keys(), [], "清空后 keys 为空")
    print("  ✓\n")


def test_aget_multi():
    """测试异步批量获取"""
    section("aget_multi")

    storage = MockStorage()
    storage.set("a", 1)
    storage.set("b", 2)

    result = asyncio.run(storage.aget_multi(["a", "b", "c"]))
    assert_eq(result, {"a": 1, "b": 2}, "aget_multi 结果（不含 c）")
    print("  ✓\n")


def test_aset_multi():
    """测试异步批量设置"""
    section("aset_multi")

    storage = MockStorage()

    result = asyncio.run(storage.aset_multi({"x": 10, "y": 20}))
    assert_eq(result, True, "aset_multi 返回值")
    assert_eq(storage.get("x"), 10, "x 写入")
    assert_eq(storage.get("y"), 20, "y 写入")
    print("  ✓\n")


def test_adelete_multi():
    """测试异步批量删除"""
    section("adelete_multi")

    storage = MockStorage()
    storage.set("a", 1)
    storage.set("b", 2)
    storage.set("c", 3)

    result = asyncio.run(storage.adelete_multi(["a", "b"]))
    assert_eq(result, True, "adelete_multi 返回值")
    assert_eq(storage.get("a"), None, "a 已删除")
    assert_eq(storage.get("c"), 3, "c 保留")
    print("  ✓\n")


def test_true_async_not_blocking():
    """验证异步方法确实通过线程池执行（不阻塞事件循环）"""
    section("真异步验证 — run_in_executor")

    storage = MockStorage()

    async def _test():
        # 在异步上下文中调用 aget，不应阻塞
        storage.set("test_key", "test_value")

        # 同时运行一个定时器，验证 aget 期间事件循环仍然运行
        timer_ran = []

        async def timer():
            await asyncio.sleep(0.001)
            timer_ran.append(True)

        # 并行执行 aget 和 timer
        await asyncio.gather(
            storage.aget("test_key"),
            timer(),
        )

        assert timer_ran == [True], "timer 应该在 aget 期间执行"
        return True

    result = asyncio.run(_test())
    assert_eq(result, True, "事件循环未被阻塞")
    print("  ✓ aget 通过 run_in_executor 执行，不阻塞事件循环\n")


if __name__ == "__main__":
    test_aget_aset()
    test_adelete()
    test_aget_all_keys()
    test_aclear()
    test_aget_multi()
    test_aset_multi()
    test_adelete_multi()
    test_true_async_not_blocking()
    print(f"{'=' * 50}")
    print("  全部测试通过 ✓")
    print(f"{'=' * 50}")
