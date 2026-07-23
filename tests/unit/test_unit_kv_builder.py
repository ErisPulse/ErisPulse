"""
KVQueryBuilder 单元测试

基于内存 MockStorage 测试 KV 链式查询构建器的全部操作：
Insert / InsertMulti / Select / Where / Update / Delete / OrderBy / Limit / Offset /
Count / Exists / ExecuteOne，以及异步接口 aExecute / aCount / aExists / aExecuteOne。

覆盖键前缀隔离（SQL 数据落在 __erispulse_sql__ 前缀下，不污染用户键）。
"""

import pytest

from ErisPulse.Core.Bases.kv_builder import KVQueryBuilder
from ErisPulse.Core.Bases.storage import BaseStorage

# ==================== 内存 KV 后端 ====================


class MockStorage(BaseStorage):
    """内存字典后端，仅实现 KV 接口供 KVQueryBuilder 使用"""

    def __init__(self):
        self._data: dict[str, object] = {}

    # ---- 同步 KV ----
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

    # ---- 异步 KV（直接复用同步实现）----
    async def aget(self, key, default=None):
        return self._data.get(key, default)

    async def aset(self, key, value):
        self._data[key] = value
        return True

    async def adelete(self, key):
        return self.delete(key)

    async def aget_all_keys(self):
        return list(self._data.keys())

    # ---- transaction / Table ----
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
        for k in list(self._data.keys()):
            if k.startswith(prefix):
                del self._data[k]
        return True

    def HasTable(self, name):
        return self.get(f"__erispulse_sql__:{name}:schema") is not None


@pytest.fixture
def storage():
    s = MockStorage()
    s.CreateTable("users", {"name": "TEXT", "age": "INTEGER"})
    return s


# ==================== Insert / Select ====================


class TestInsertSelect:
    def test_insert_returns_one(self, storage):
        affected = storage.Table("users").Insert({"name": "Alice", "age": 30}).Execute()
        assert affected == 1

    def test_select_all_after_insert(self, storage):
        storage.Table("users").Insert({"name": "Alice", "age": 30}).Execute()
        storage.Table("users").Insert({"name": "Bob", "age": 25}).Execute()
        rows = storage.Table("users").Select("name", "age").Execute()
        assert len(rows) == 2
        assert ("Alice", 30) in rows
        assert ("Bob", 25) in rows

    def test_select_star_returns_all_values(self, storage):
        storage.Table("users").Insert({"name": "Alice", "age": 30}).Execute()
        rows = storage.Table("users").Select().Execute()
        assert len(rows) == 1
        # SELECT * 返回全部列值组成的元组
        assert set(rows[0]) == {"Alice", 30}


# ==================== Where ====================


class TestWhere:
    def test_where_greater_than(self, storage):
        for v in [1, 2, 3, 4, 5]:
            storage.Table("users").Insert({"name": f"u{v}", "age": v}).Execute()
        rows = storage.Table("users").Select("age").Where("age > ?", 3).Execute()
        assert rows == [(4,), (5,)]

    def test_where_equal(self, storage):
        for v in [1, 2, 3]:
            storage.Table("users").Insert({"name": f"u{v}", "age": v}).Execute()
        rows = storage.Table("users").Select("age").Where("age = ?", 2).Execute()
        assert rows == [(2,)]

    def test_where_like(self, storage):
        storage.Table("users").Insert({"name": "Alice", "age": 1}).Execute()
        storage.Table("users").Insert({"name": "Bob", "age": 2}).Execute()
        rows = storage.Table("users").Select("name").Where("name LIKE ?", "A%").Execute()
        assert rows == [("Alice",)]

    def test_where_not_equal(self, storage):
        for v in [1, 2, 3]:
            storage.Table("users").Insert({"name": f"u{v}", "age": v}).Execute()
        rows = storage.Table("users").Select("age").Where("age != ?", 2).Execute()
        assert sorted(r[0] for r in rows) == [1, 3]


# ==================== OrderBy / Limit / Offset ====================


class TestOrderLimitOffset:
    def test_order_by_asc(self, storage):
        for n in ["Charlie", "Alice", "Bob"]:
            storage.Table("users").Insert({"name": n, "age": 1}).Execute()
        rows = storage.Table("users").Select("name").OrderBy("name").Execute()
        assert rows == [("Alice",), ("Bob",), ("Charlie",)]

    def test_order_by_desc(self, storage):
        for n in ["Charlie", "Alice", "Bob"]:
            storage.Table("users").Insert({"name": n, "age": 1}).Execute()
        rows = storage.Table("users").Select("name").OrderBy("name", desc=True).Execute()
        assert rows == [("Charlie",), ("Bob",), ("Alice",)]

    def test_limit(self, storage):
        for v in range(10):
            storage.Table("users").Insert({"name": f"u{v}", "age": v}).Execute()
        rows = storage.Table("users").Select("age").Limit(3).Execute()
        assert len(rows) == 3

    def test_limit_offset(self, storage):
        for v in range(10):
            storage.Table("users").Insert({"name": f"u{v}", "age": v}).Execute()
        rows = storage.Table("users").Select("age").Limit(2).Offset(5).Execute()
        assert rows[0][0] == 5
        assert rows[1][0] == 6


# ==================== Update / Delete ====================


class TestUpdateDelete:
    def test_update_returns_affected_count(self, storage):
        storage.Table("users").Insert({"name": "Alice", "age": 10}).Execute()
        storage.Table("users").Insert({"name": "Bob", "age": 20}).Execute()
        affected = storage.Table("users").Update({"age": 99}).Where("name = ?", "Alice").Execute()
        assert affected == 1

    def test_update_modifies_row(self, storage):
        storage.Table("users").Insert({"name": "Alice", "age": 10}).Execute()
        storage.Table("users").Update({"age": 99}).Where("name = ?", "Alice").Execute()
        rows = storage.Table("users").Select("name", "age").Where("name = ?", "Alice").Execute()
        assert rows == [("Alice", 99)]

    def test_delete_returns_affected_count(self, storage):
        storage.Table("users").Insert({"name": "Alice", "age": 1}).Execute()
        storage.Table("users").Insert({"name": "Bob", "age": 2}).Execute()
        affected = storage.Table("users").Delete().Where("name = ?", "Bob").Execute()
        assert affected == 1

    def test_delete_actually_removes(self, storage):
        storage.Table("users").Insert({"name": "Alice", "age": 1}).Execute()
        storage.Table("users").Insert({"name": "Bob", "age": 2}).Execute()
        storage.Table("users").Delete().Where("name = ?", "Bob").Execute()
        assert storage.Table("users").Count() == 1


# ==================== Count / Exists / ExecuteOne ====================


class TestCountExists:
    def test_count_empty_table(self, storage):
        assert storage.Table("users").Count() == 0

    def test_count_after_inserts(self, storage):
        for v in range(3):
            storage.Table("users").Insert({"name": f"u{v}", "age": v}).Execute()
        assert storage.Table("users").Count() == 3

    def test_exists_false_when_empty(self, storage):
        assert storage.Table("users").Exists() is False

    def test_exists_true_after_insert(self, storage):
        storage.Table("users").Insert({"name": "Alice", "age": 1}).Execute()
        assert storage.Table("users").Exists() is True

    def test_count_with_where(self, storage):
        for v in range(5):
            storage.Table("users").Insert({"name": f"u{v}", "age": v}).Execute()
        # age > 2 -> age 3,4 -> 2 行
        assert storage.Table("users").Where("age > ?", 2).Count() == 2


class TestExecuteOne:
    def test_returns_first_matching(self, storage):
        storage.Table("users").Insert({"name": "Alice", "age": 1}).Execute()
        storage.Table("users").Insert({"name": "Bob", "age": 2}).Execute()
        row = storage.Table("users").Select("name").Where("name = ?", "Alice").ExecuteOne()
        assert row == ("Alice",)

    def test_returns_none_when_not_found(self, storage):
        storage.Table("users").Insert({"name": "Alice", "age": 1}).Execute()
        row = storage.Table("users").Select("name").Where("name = ?", "Nope").ExecuteOne()
        assert row is None


# ==================== InsertMulti ====================


class TestInsertMulti:
    def test_returns_inserted_count(self, storage):
        count = (
            storage.Table("users")
            .InsertMulti([{"name": "a", "age": 1}, {"name": "b", "age": 2}, {"name": "c", "age": 3}])
            .Execute()
        )
        assert count == 3

    def test_rows_actually_inserted(self, storage):
        storage.Table("users").InsertMulti([{"name": "a", "age": 1}, {"name": "b", "age": 2}]).Execute()
        assert storage.Table("users").Count() == 2


# ==================== 键前缀隔离 ====================


class TestKeyIsolation:
    def test_user_keys_not_polluted_by_sql(self, storage):
        storage.set("user_data", "hello")
        storage.Table("users").Insert({"name": "Alice", "age": 1}).Execute()

        all_keys = storage.get_all_keys()
        # 用户数据应原样存在
        assert "user_data" in all_keys
        # SQL 数据应全部落在 __erispulse_sql__ 前缀下
        sql_keys = [k for k in all_keys if "__erispulse_sql__" in k]
        assert len(sql_keys) > 0
        # 用户数据不会被误归入 SQL 前缀
        assert all("user_data" not in k for k in sql_keys)

    def test_table_prefix_uses_erispulse_sql(self, storage):
        storage.Table("users").Insert({"name": "Alice", "age": 1}).Execute()
        all_keys = storage.get_all_keys()
        # 行数据键应为 __erispulse_sql__:users:data:<id>
        data_keys = [k for k in all_keys if ":users:data:" in k]
        assert len(data_keys) == 1


# ==================== 异步接口 ====================


class TestAsyncInterface:
    async def test_aexecute_insert(self, storage):
        affected = await storage.Table("users").Insert({"name": "Alice", "age": 30}).aExecute()
        assert affected == 1

    async def test_acount(self, storage):
        await storage.Table("users").Insert({"name": "a", "age": 1}).aExecute()
        await storage.Table("users").Insert({"name": "b", "age": 2}).aExecute()
        count = await storage.Table("users").aCount()
        assert count == 2

    async def test_aexists(self, storage):
        assert await storage.Table("users").aExists() is False
        await storage.Table("users").Insert({"name": "a", "age": 1}).aExecute()
        assert await storage.Table("users").aExists() is True

    async def test_aexecute_one(self, storage):
        await storage.Table("users").Insert({"name": "Alice", "age": 1}).aExecute()
        await storage.Table("users").Insert({"name": "Bob", "age": 2}).aExecute()
        row = await storage.Table("users").Select("name").Where("name = ?", "Alice").aExecuteOne()
        assert row == ("Alice",)

    async def test_aexecute_one_none_when_missing(self, storage):
        await storage.Table("users").Insert({"name": "Alice", "age": 1}).aExecute()
        row = await storage.Table("users").Select("name").Where("name = ?", "Nope").aExecuteOne()
        assert row is None

    async def test_aexecute_update_and_delete(self, storage):
        await storage.Table("users").Insert({"name": "Alice", "age": 10}).aExecute()
        await storage.Table("users").Insert({"name": "Bob", "age": 20}).aExecute()

        affected = await storage.Table("users").Update({"age": 99}).Where("name = ?", "Alice").aExecute()
        assert affected == 1

        affected = await storage.Table("users").Delete().Where("name = ?", "Bob").aExecute()
        assert affected == 1
        assert await storage.Table("users").aCount() == 1


# ==================== 输入校验 ====================


class TestInputValidation:
    def test_insert_rejects_non_dict(self, storage):
        qb = storage.Table("users")
        qb._operation = "insert"
        qb._data = ["not", "a", "dict"]
        with pytest.raises(ValueError, match="字典"):
            qb.Execute()

    def test_unknown_operation_raises(self, storage):
        qb = storage.Table("users")
        qb._operation = "totally_unknown"
        with pytest.raises(ValueError, match="Unknown operation"):
            qb.Execute()
