"""
KVQueryBuilder 测试

测试基于 KV 的链式 SQL 查询：Insert/Select/Update/Delete/Where/OrderBy/Limit/Count
以及异步接口 aExecute/aCount/aExists

使用内存 MockStorage 作为后端。
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder
from ErisPulse.Core.Bases.kv_builder import KVQueryBuilder


class MockStorage(BaseStorage):
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
        return KVQueryBuilder(self, table_name)

    def CreateTable(self, name, columns):
        self.set(f"__erispulse_sql__:{name}:schema", columns)
        self.set(f"__erispulse_sql__:{name}:next_id", 1)
        return True

    def DropTable(self, name):
        prefix = f"__erispulse_sql__:{name}:"
        for k in self.get_all_keys():
            if k.startswith(prefix):
                self.delete(k)
        return True

    def HasTable(self, name):
        return self.get(f"__erispulse_sql__:{name}:schema") is not None


def sec(title):
    print(f"\n{'=' * 50}")
    print(f"  {title}")
    print(f"{'=' * 50}")


def ok(msg=""):
    print(f"  ✓ {msg}")


def test_insert_and_select():
    """基本 Insert + Select"""
    sec("Insert + Select")
    s = MockStorage()
    s.CreateTable("users", {"name": "TEXT", "age": "INTEGER"})

    s.Table("users").Insert({"name": "Alice", "age": 30}).Execute()
    s.Table("users").Insert({"name": "Bob", "age": 25}).Execute()

    rows = s.Table("users").Select("name", "age").Execute()
    assert len(rows) == 2; ok(f"2 行: {rows}")


def test_where():
    """Where 过滤"""
    sec("Where 过滤")
    s = MockStorage()
    s.CreateTable("t", {"v": "INTEGER"})
    for v in [1, 2, 3, 4, 5]:
        s.Table("t").Insert({"v": v}).Execute()

    rows = s.Table("t").Select("v").Where("v > ?", 3).Execute()
    assert rows == [(4,), (5,)]; ok(f"v > 3: {rows}")

    rows = s.Table("t").Select("v").Where("v = ?", 2).Execute()
    assert rows == [(2,),]; ok(f"v = 2: {rows}")


def test_order_by():
    """OrderBy 排序"""
    sec("OrderBy 排序")
    s = MockStorage()
    s.CreateTable("t", {"name": "TEXT"})
    for n in ["Charlie", "Alice", "Bob"]:
        s.Table("t").Insert({"name": n}).Execute()

    rows = s.Table("t").Select("name").OrderBy("name").Execute()
    assert rows == [("Alice",), ("Bob",), ("Charlie",)]; ok(f"升序: {rows}")

    rows = s.Table("t").Select("name").OrderBy("name", desc=True).Execute()
    assert rows == [("Charlie",), ("Bob",), ("Alice",)]; ok(f"降序: {rows}")


def test_limit_offset():
    """Limit + Offset"""
    sec("Limit + Offset")
    s = MockStorage()
    s.CreateTable("t", {"v": "INTEGER"})
    for v in range(10):
        s.Table("t").Insert({"v": v}).Execute()

    rows = s.Table("t").Select("v").Limit(3).Execute()
    assert len(rows) == 3; ok(f"Limit 3: {[r[0] for r in rows]}")

    rows = s.Table("t").Select("v").Limit(2).Offset(5).Execute()
    assert rows[0][0] == 5 and rows[1][0] == 6; ok(f"Offset 5: {[r[0] for r in rows]}")


def test_update_and_delete():
    """Update + Delete"""
    sec("Update + Delete")
    s = MockStorage()
    s.CreateTable("t", {"name": "TEXT", "score": "INTEGER"})
    s.Table("t").Insert({"name": "Alice", "score": 10}).Execute()
    s.Table("t").Insert({"name": "Bob", "score": 20}).Execute()

    affected = s.Table("t").Update({"score": 99}).Where("name = ?", "Alice").Execute()
    assert affected == 1; ok(f"Update 影响 {affected} 行")

    rows = s.Table("t").Select("name", "score").Where("name = ?", "Alice").Execute()
    assert rows == [("Alice", 99)]; ok(f"更新后: {rows}")

    affected = s.Table("t").Delete().Where("name = ?", "Bob").Execute()
    assert affected == 1; ok(f"Delete 影响 {affected} 行")
    assert s.Table("t").Count() == 1; ok("Count = 1")


def test_count_exists():
    """Count + Exists"""
    sec("Count + Exists")
    s = MockStorage()
    s.CreateTable("t", {"x": "TEXT"})

    assert s.Table("t").Count() == 0; ok("空表 Count = 0")
    assert s.Table("t").Exists() is False; ok("空表 Exists = False")

    s.Table("t").Insert({"x": "a"}).Execute()
    assert s.Table("t").Count() == 1; ok("Count = 1")
    assert s.Table("t").Exists() is True; ok("Exists = True")


def test_insert_multi():
    """批量插入"""
    sec("InsertMulti")
    s = MockStorage()
    s.CreateTable("t", {"v": "INTEGER"})

    count = s.Table("t").InsertMulti([{"v": 1}, {"v": 2}, {"v": 3}]).Execute()
    assert count == 3; ok(f"InsertMulti 返回 {count}")
    assert s.Table("t").Count() == 3; ok("Count = 3")


def test_execute_one():
    """ExecuteOne"""
    sec("ExecuteOne")
    s = MockStorage()
    s.CreateTable("t", {"name": "TEXT"})
    s.Table("t").Insert({"name": "Alice"}).Execute()
    s.Table("t").Insert({"name": "Bob"}).Execute()

    row = s.Table("t").Select("name").Where("name = ?", "Alice").ExecuteOne()
    assert row == ("Alice",); ok(f"ExecuteOne: {row}")

    row = s.Table("t").Select("name").Where("name = ?", "Nope").ExecuteOne()
    assert row is None; ok("不存在时返回 None")


# ==================== 异步接口 ====================

def test_async_crud():
    """异步 CRUD"""
    sec("异步 aExecute / aCount / aExists")

    async def _test():
        s = MockStorage()
        s.CreateTable("t", {"v": "INTEGER"})

        await s.Table("t").Insert({"v": 1}).aExecute()
        await s.Table("t").Insert({"v": 2}).aExecute()

        count = await s.Table("t").aCount()
        assert count == 2; ok(f"aCount = {count}")

        exists = await s.Table("t").aExists()
        assert exists is True; ok(f"aExists = {exists}")

        row = await s.Table("t").aExecuteOne()
        assert row is not None; ok(f"aExecuteOne: {row}")

        return True

    asyncio.run(_test())
    ok("全部异步操作完成")


def test_keys_not_polluted():
    """键不污染 — SQL 数据在 __erispulse_sql__ 前缀下"""
    sec("键隔离验证")
    s = MockStorage()
    s.set("user_data", "hello")
    s.CreateTable("t", {"v": "TEXT"})
    s.Table("t").Insert({"v": "x"}).Execute()

    all_keys = s.get_all_keys()
    # 用户数据不包含 SQL 前缀
    assert "user_data" in all_keys
    assert any("__erispulse_sql__" in k for k in all_keys); ok("SQL 数据在 __erispulse_sql__ 前缀下")
    assert all("user_data" not in k for k in all_keys if "__erispulse_sql__" in k); ok("用户数据不在 SQL 前缀下")
    print()


if __name__ == "__main__":
    test_insert_and_select()
    test_where()
    test_order_by()
    test_limit_offset()
    test_update_and_delete()
    test_count_exists()
    test_insert_multi()
    test_execute_one()
    test_async_crud()
    test_keys_not_polluted()
    print(f"{'=' * 50}")
    print("  全部测试通过 ✓")
    print(f"{'=' * 50}")
