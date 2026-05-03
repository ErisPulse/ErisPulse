"""
存储管理 SQL 链式查询单元测试

测试 SQLiteQueryBuilder、AlterTableBuilder 及 StorageManager 新增的表管理方法
"""

import pytest
import os
import sqlite3
import tempfile

from ErisPulse.Core.storage import StorageManager, SQLiteQueryBuilder, AlterTableBuilder
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder


# ==================== Fixtures ====================


@pytest.fixture
def temp_db_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".db", delete=False) as f:
        temp_path = f.name

    yield temp_path

    for ext in ["", "-wal", "-shm"]:
        file_path = temp_path + ext
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except PermissionError:
                pass


@pytest.fixture
def sm(temp_db_file):
    StorageManager._instance = None

    manager = StorageManager.__new__(StorageManager)
    manager.db_path = temp_db_file
    manager._init_db()
    manager._initialized = True

    yield manager

    StorageManager._instance = None


@pytest.fixture
def users_table(sm):
    sm.CreateTable("users", {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "name": "TEXT NOT NULL",
        "age": "INTEGER DEFAULT 0",
    })
    yield
    sm.DropTable("users")


# ==================== ABC 基类测试 ====================


class TestABCContracts:
    def test_base_storage_is_abstract(self):
        with pytest.raises(TypeError):
            BaseStorage()

    def test_base_query_builder_is_abstract(self):
        with pytest.raises(TypeError):
            BaseQueryBuilder(None, "test")

    def test_storage_manager_inherits_base_storage(self):
        assert issubclass(StorageManager, BaseStorage)

    def test_sqlite_query_builder_inherits_base(self):
        assert issubclass(SQLiteQueryBuilder, BaseQueryBuilder)


# ==================== CreateTable / DropTable / HasTable ====================


class TestTableManagement:

    def test_create_table(self, sm):
        result = sm.CreateTable("test_create", {
            "id": "INTEGER PRIMARY KEY",
            "name": "TEXT",
        })
        assert result is True
        assert sm.HasTable("test_create") is True
        sm.DropTable("test_create")

    def test_create_table_already_exists(self, sm):
        sm.CreateTable("dup_table", {"id": "INTEGER PRIMARY KEY"})
        result = sm.CreateTable("dup_table", {"id": "INTEGER PRIMARY KEY"})
        assert result is True
        sm.DropTable("dup_table")

    def test_drop_table(self, sm):
        sm.CreateTable("drop_me", {"id": "INTEGER PRIMARY KEY"})
        assert sm.HasTable("drop_me") is True

        result = sm.DropTable("drop_me")
        assert result is True
        assert sm.HasTable("drop_me") is False

    def test_drop_nonexistent_table(self, sm):
        result = sm.DropTable("nonexistent_table")
        assert result is True

    def test_has_table_false(self, sm):
        assert sm.HasTable("no_such_table") is False

    def test_has_table_config(self, sm):
        assert sm.HasTable("config") is True

    def test_create_table_not_ready(self):
        StorageManager._instance = None
        manager = StorageManager.__new__(StorageManager)
        manager._initialized = False
        assert manager.CreateTable("t", {"id": "INTEGER"}) is False
        StorageManager._instance = None

    def test_drop_table_not_ready(self):
        StorageManager._instance = None
        manager = StorageManager.__new__(StorageManager)
        manager._initialized = False
        assert manager.DropTable("t") is False
        StorageManager._instance = None

    def test_has_table_not_ready(self):
        StorageManager._instance = None
        manager = StorageManager.__new__(StorageManager)
        manager._initialized = False
        assert manager.HasTable("t") is False
        StorageManager._instance = None


# ==================== SQLiteQueryBuilder — Insert ====================


class TestInsert:

    def test_insert_single_row(self, sm, users_table):
        result = sm.Table("users").Insert({"name": "Alice", "age": 30}).Execute()
        assert isinstance(result, int)
        assert result >= 1

        rows = sm.Table("users").Select("name", "age").Execute()
        assert rows == [("Alice", 30)]

    def test_insert_multiple_rows(self, sm, users_table):
        sm.Table("users").Insert({"name": "Alice", "age": 30}).Execute()
        sm.Table("users").Insert({"name": "Bob", "age": 25}).Execute()

        rows = sm.Table("users").Select("name").OrderBy("name").Execute()
        assert rows == [("Alice",), ("Bob",)]


class TestInsertMulti:

    def test_insert_multi(self, sm, users_table):
        result = sm.Table("users").InsertMulti([
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
            {"name": "Charlie", "age": 35},
        ]).Execute()
        assert isinstance(result, int)
        assert result == 3

        count = sm.Table("users").Count()
        assert count == 3

    def test_insert_multi_empty_list(self, sm, users_table):
        with pytest.raises(ValueError, match="非空列表"):
            sm.Table("users").InsertMulti([]).Execute()


# ==================== SQLiteQueryBuilder — Select ====================


class TestSelect:

    def test_select_all(self, sm, users_table):
        sm.Table("users").Insert({"name": "Alice", "age": 30}).Execute()

        rows = sm.Table("users").Select().Execute()
        assert len(rows) == 1
        assert rows[0][1] == "Alice"

    def test_select_specific_columns(self, sm, users_table):
        sm.Table("users").Insert({"name": "Alice", "age": 30}).Execute()

        rows = sm.Table("users").Select("name", "age").Execute()
        assert rows == [("Alice", 30)]

    def test_execute_one(self, sm, users_table):
        sm.Table("users").Insert({"name": "Alice", "age": 30}).Execute()

        row = sm.Table("users").Select("name", "age").Where("name = ?", "Alice").ExecuteOne()
        assert row == ("Alice", 30)

    def test_execute_one_no_result(self, sm, users_table):
        row = sm.Table("users").Select("name").Where("name = ?", "Nobody").ExecuteOne()
        assert row is None


# ==================== SQLiteQueryBuilder — Where ====================


class TestWhere:

    def test_single_where(self, sm, users_table):
        sm.Table("users").InsertMulti([
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ]).Execute()

        rows = sm.Table("users").Select("name").Where("age > ?", 26).Execute()
        assert rows == [("Alice",)]

    def test_multiple_where_and(self, sm, users_table):
        sm.Table("users").InsertMulti([
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
            {"name": "Charlie", "age": 35},
        ]).Execute()

        rows = (
            sm.Table("users")
            .Select("name")
            .Where("age > ?", 26)
            .Where("age < ?", 36)
            .OrderBy("name")
            .Execute()
        )
        assert rows == [("Alice",), ("Charlie",)]


# ==================== SQLiteQueryBuilder — OrderBy / Limit / Offset ====================


class TestOrderByLimitOffset:

    def test_order_by_asc(self, sm, users_table):
        sm.Table("users").InsertMulti([
            {"name": "Charlie", "age": 35},
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ]).Execute()

        rows = sm.Table("users").Select("name").OrderBy("name").Execute()
        assert rows == [("Alice",), ("Bob",), ("Charlie",)]

    def test_order_by_desc(self, sm, users_table):
        sm.Table("users").InsertMulti([
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
            {"name": "Charlie", "age": 35},
        ]).Execute()

        rows = sm.Table("users").Select("name").OrderBy("age", desc=True).Execute()
        assert rows == [("Charlie",), ("Alice",), ("Bob",)]

    def test_limit(self, sm, users_table):
        for i in range(10):
            sm.Table("users").Insert({"name": f"user{i}", "age": i}).Execute()

        rows = sm.Table("users").Select("name").OrderBy("age").Limit(3).Execute()
        assert len(rows) == 3
        assert rows[0] == ("user0",)

    def test_limit_offset(self, sm, users_table):
        for i in range(10):
            sm.Table("users").Insert({"name": f"user{i}", "age": i}).Execute()

        rows = (
            sm.Table("users")
            .Select("name")
            .OrderBy("age")
            .Limit(3)
            .Offset(5)
            .Execute()
        )
        assert len(rows) == 3
        assert rows[0] == ("user5",)


# ==================== SQLiteQueryBuilder — Update ====================


class TestUpdate:

    def test_update_with_where(self, sm, users_table):
        sm.Table("users").InsertMulti([
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ]).Execute()

        result = sm.Table("users").Update({"age": 31}).Where("name = ?", "Alice").Execute()
        assert isinstance(result, int)

        row = sm.Table("users").Select("age").Where("name = ?", "Alice").ExecuteOne()
        assert row == (31,)

        row = sm.Table("users").Select("age").Where("name = ?", "Bob").ExecuteOne()
        assert row == (25,)

    def test_update_all(self, sm, users_table):
        sm.Table("users").InsertMulti([
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ]).Execute()

        sm.Table("users").Update({"age": 99}).Execute()

        rows = sm.Table("users").Select("age").OrderBy("name").Execute()
        assert rows == [(99,), (99,)]


# ==================== SQLiteQueryBuilder — Delete ====================


class TestDelete:

    def test_delete_with_where(self, sm, users_table):
        sm.Table("users").InsertMulti([
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ]).Execute()

        result = sm.Table("users").Delete().Where("name = ?", "Alice").Execute()
        assert isinstance(result, int)

        count = sm.Table("users").Count()
        assert count == 1

    def test_delete_all(self, sm, users_table):
        sm.Table("users").InsertMulti([
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ]).Execute()

        sm.Table("users").Delete().Execute()
        assert sm.Table("users").Count() == 0


# ==================== SQLiteQueryBuilder — Count / Exists ====================


class TestCountExists:

    def test_count_all(self, sm, users_table):
        sm.Table("users").InsertMulti([
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ]).Execute()

        assert sm.Table("users").Count() == 2

    def test_count_with_where(self, sm, users_table):
        sm.Table("users").InsertMulti([
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ]).Execute()

        assert sm.Table("users").Where("age > ?", 26).Count() == 1

    def test_count_empty(self, sm, users_table):
        assert sm.Table("users").Count() == 0

    def test_exists_true(self, sm, users_table):
        sm.Table("users").Insert({"name": "Alice", "age": 30}).Execute()

        assert sm.Table("users").Where("name = ?", "Alice").Exists() is True

    def test_exists_false(self, sm, users_table):
        assert sm.Table("users").Where("name = ?", "Nobody").Exists() is False


# ==================== SQLiteQueryBuilder — copy / clear ====================


class TestCopyClear:

    def test_copy_preserves_state(self, sm, users_table):
        sm.Table("users").InsertMulti([
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
            {"name": "Charlie", "age": 35},
        ]).Execute()

        base = sm.Table("users").Where("age > ?", 20)
        copy1 = base.copy().Select("name").OrderBy("name").Limit(2).Execute()
        copy2 = base.copy().Count()

        assert copy1 == [("Alice",), ("Bob",)]
        assert copy2 == 3

    def test_clear_resets_state(self, sm, users_table):
        sm.Table("users").Insert({"name": "Alice", "age": 30}).Execute()

        builder = sm.Table("users").Select("name").Where("age > ?", 0)
        builder.clear()

        builder.Select("name").Where("name = ?", "Alice")
        rows = builder.Execute()
        assert rows == [("Alice",)]

    def test_repr(self, sm, users_table):
        builder = sm.Table("users").Select("name")
        assert "users" in repr(builder)
        assert "select" in repr(builder)


# ==================== SQLiteQueryBuilder — Error Handling ====================


class TestQueryBuilderErrors:

    def test_execute_without_operation(self, sm, users_table):
        with pytest.raises(ValueError, match="未设置操作类型"):
            sm.Table("users").Execute()

    def test_insert_wrong_type(self, sm, users_table):
        builder = sm.Table("users")
        builder._operation = "insert"
        builder._data = "not_a_dict"
        with pytest.raises(ValueError, match="字典类型"):
            builder.Execute()

    def test_update_wrong_type(self, sm, users_table):
        builder = sm.Table("users")
        builder._operation = "update"
        builder._data = "not_a_dict"
        with pytest.raises(ValueError, match="字典类型"):
            builder.Execute()


# ==================== AlterTableBuilder ====================


class TestAlterTable:

    def test_add_column(self, sm, users_table):
        sm.Table("users").Insert({"name": "Alice", "age": 30}).Execute()

        result = sm.AlterTable("users").AddColumn("email", "TEXT").Execute()
        assert result is True

        sm.Table("users").Update({"email": "alice@example.com"}).Where("name = ?", "Alice").Execute()
        row = sm.Table("users").Select("name", "email").Where("name = ?", "Alice").ExecuteOne()
        assert row == ("Alice", "alice@example.com")

    def test_rename_table(self, sm, users_table):
        sm.Table("users").Insert({"name": "Alice", "age": 30}).Execute()

        result = sm.AlterTable("users").RenameTo("members").Execute()
        assert result is True

        assert sm.HasTable("users") is False
        assert sm.HasTable("members") is True

        rows = sm.Table("members").Select("name").Execute()
        assert rows == [("Alice",)]

        sm.DropTable("members")

    def test_alter_empty_operations(self, sm, users_table):
        result = sm.AlterTable("users").Execute()
        assert result is True

    def test_alter_nonexistent_table(self, sm):
        result = sm.AlterTable("no_such_table").AddColumn("col", "TEXT").Execute()
        assert result is False


# ==================== 事务中的链式操作 ====================


class TestTransactionWithChain:

    def test_chain_in_transaction(self, sm, users_table):
        with sm.transaction():
            sm.Table("users").Insert({"name": "Alice", "age": 30}).Execute()
            sm.Table("users").Insert({"name": "Bob", "age": 25}).Execute()

        assert sm.Table("users").Count() == 2

    def test_chain_transaction_rollback(self, sm, users_table):
        sm.Table("users").Insert({"name": "Alice", "age": 30}).Execute()

        try:
            with sm.transaction():
                sm.Table("users").Delete().Where("name = ?", "Alice").Execute()
                raise Exception("force rollback")
        except Exception:
            pass

        assert sm.Table("users").Where("name = ?", "Alice").Exists() is True


# ==================== BaseStorage 默认方法委托测试 ====================


class TestBaseStorageDefaults:

    def test_keys_delegates_to_get_all_keys(self, sm):
        sm.set("k1", "v1")
        sm.set("k2", "v2")

        assert sorted(sm.keys()) == sorted(sm.get_all_keys())

    def test_get_multi_uses_get(self, sm):
        sm.set("a", 1)
        sm.set("b", 2)

        result = sm.get_multi(["a", "b", "c"])
        assert result == {"a": 1, "b": 2}

    def test_set_multi_uses_set(self, sm):
        result = sm.set_multi({"x": 10, "y": 20})
        assert result is True
        assert sm.get("x") == 10
        assert sm.get("y") == 20

    def test_delete_multi_uses_delete(self, sm):
        sm.set_multi({"x": 10, "y": 20})
        result = sm.delete_multi(["x", "y"])
        assert result is True
        assert sm.get("x") is None
        assert sm.get("y") is None
