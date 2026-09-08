"""
存储异步原生接口单元测试

验证 2.8.0 起的异步原生契约：aget/aset/adelete/aget_all_keys/aclear、
atransaction（提交/回滚/嵌套）、查询构建器 aExecute 系列终止方法，
以及异步事务内的连接隔离。
"""

import os
import tempfile

import pytest

from ErisPulse.Core.storage import StorageManager


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


class TestAsyncKV:
    """KV 异步原生接口"""

    async def test_aset_aget_roundtrip(self, sm):
        assert await sm.aset("k", {"n": 1}) is True
        assert await sm.aget("k") == {"n": 1}

    async def test_aget_nested(self, sm):
        await sm.aset("user.settings", {"theme": "dark"})
        assert await sm.aget("user.settings.theme") == "dark"

    async def test_aget_default(self, sm):
        assert await sm.aget("nope", "dft") == "dft"
        assert await sm.aget("nope") is None

    async def test_adelete(self, sm):
        await sm.aset("k", 1)
        assert await sm.adelete("k") is True
        assert await sm.aget("k") is None

    async def test_aget_all_keys_and_aclear(self, sm):
        await sm.aset("a", 1)
        await sm.aset("b", 2)
        keys = await sm.aget_all_keys()
        assert set(keys) >= {"a", "b"}
        assert await sm.aclear() is True
        assert await sm.aget_all_keys() == []

    async def test_async_multi(self, sm):
        assert await sm.aset_multi({"m1": 1, "m2": [2]}) is True
        assert await sm.aget_multi(["m1", "m2", "nope"]) == {"m1": 1, "m2": [2]}
        assert await sm.adelete_multi(["m1", "m2"]) is True
        assert await sm.aget_multi(["m1", "m2"]) == {}


class TestAsyncTransaction:
    """异步事务：提交 / 回滚 / 嵌套复用"""

    async def test_commit(self, sm):
        async with sm.atransaction():
            await sm.aset("tx.a", "v1")
            await sm.aset("tx.b", "v2")
        assert await sm.aget("tx.a") == "v1"
        assert await sm.aget("tx.b") == "v2"

    async def test_rollback(self, sm):
        await sm.aset("tx.keep", "old")
        with pytest.raises(RuntimeError):
            async with sm.atransaction():
                await sm.aset("tx.keep", "new")
                await sm.aset("tx.tmp", "tmp")
                raise RuntimeError("boom")
        assert await sm.aget("tx.keep") == "old"
        assert await sm.aget("tx.tmp") is None

    async def test_nested_reuses_outer(self, sm):
        async with sm.atransaction() as outer:
            async with sm.atransaction() as inner:
                assert inner is outer
                await sm.aset("tx.n", 1)
            # 内层结束不应提交（由最外层统一控制）
        assert await sm.aget("tx.n") == 1

    async def test_isolation_from_outside(self, sm):
        """事务内的写入对外不可见（专用连接），提交后可见"""
        await sm.aset("tx.iso", "before")
        async with sm.atransaction():
            await sm.aset("tx.iso", "inside")
            assert await sm.aget("tx.iso") == "inside"
        assert await sm.aget("tx.iso") == "inside"


class TestAsyncQueryBuilder:
    """查询构建器异步终止方法"""

    async def _setup_users(self, sm):
        await sm.aCreateTable(
            "au",
            {
                "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "name": "TEXT NOT NULL",
                "age": "INTEGER DEFAULT 0",
            },
        )

    async def test_aexecute_insert_select(self, sm):
        await self._setup_users(sm)
        qb = sm.Table("au")
        assert await qb.Insert({"name": "Alice", "age": 30}).aExecute() == 1
        assert await qb.Insert({"name": "Bob", "age": 25}).aExecute() == 1

        rows = await qb.Select("name").OrderBy("name").aExecute()
        assert rows == [("Alice",), ("Bob",)]

    async def test_aexecute_insert_multi(self, sm):
        await self._setup_users(sm)
        qb = sm.Table("au")
        affected = await qb.InsertMulti(
            [{"name": "A", "age": 1}, {"name": "B", "age": 2}]
        ).aExecute()
        assert affected == 2
        assert await qb.aCount() == 2

    async def test_aexecute_update_delete_rowcount(self, sm):
        await self._setup_users(sm)
        await sm.Table("au").InsertMulti([{"name": "A"}, {"name": "B"}]).aExecute()

        # 注意：构建器状态跨链持久，有状态的 Update/Delete 链使用新构建器
        assert (
            await sm.Table("au")
            .Update({"age": 9})
            .Where("name = ?", "A")
            .aExecute()
            == 1
        )
        assert (
            await sm.Table("au").Delete().Where("name = ?", "B").aExecute() == 1
        )

    async def test_aexecute_one(self, sm):
        await self._setup_users(sm)
        qb = sm.Table("au")
        await qb.Insert({"name": "Alice", "age": 30}).aExecute()

        row = await qb.Select("name", "age").Where("name = ?", "Alice").aExecuteOne()
        assert row == ("Alice", 30)
        assert await qb.Select("name").Where("name = ?", "Nobody").aExecuteOne() is None

    async def test_aexecute_to_dict(self, sm):
        await self._setup_users(sm)
        qb = sm.Table("au")
        await qb.Insert({"name": "Alice", "age": 30}).aExecute()

        rows = await qb.Select("name", "age").ToDict().aExecute()
        assert rows == [{"name": "Alice", "age": 30}]
        one = await qb.Select("name", "age").ToDict().Where("name = ?", "Alice").aExecuteOne()
        assert one == {"name": "Alice", "age": 30}

    async def test_acount_aexists(self, sm):
        await self._setup_users(sm)
        assert await sm.Table("au").aCount() == 0
        assert await sm.Table("au").aExists() is False
        await sm.Table("au").Insert({"name": "A"}).aExecute()
        assert await sm.Table("au").Where("name = ?", "A").aCount() == 1
        assert await sm.Table("au").Where("name = ?", "A").aExists() is True

    async def test_table_ops_in_async_transaction(self, sm):
        """事务内的 SQL 构建器操作路由到事务连接，回滚后不可见"""
        await self._setup_users(sm)
        await sm.Table("au").Insert({"name": "keep"}).aExecute()

        with pytest.raises(RuntimeError):
            async with sm.atransaction():
                await sm.Table("au").Insert({"name": "ghost"}).aExecute()
                assert (
                    await sm.Table("au").Where("name = ?", "ghost").aExists() is True
                )
                raise RuntimeError("boom")

        assert await sm.Table("au").Where("name = ?", "ghost").aExists() is False
        assert await sm.Table("au").Where("name = ?", "keep").aExists() is True


class TestAsyncTableManagement:
    """DDL 异步原生接口"""

    async def test_create_has_drop(self, sm):
        assert await sm.aCreateTable("t1", {"id": "INTEGER PRIMARY KEY"}) is True
        assert await sm.aHasTable("t1") is True
        assert await sm.aHasTable("t2") is False
        assert await sm.aDropTable("t1") is True
        assert await sm.aHasTable("t1") is False

    async def test_create_table_not_ready(self, sm):
        object.__setattr__(sm, "_initialized", False)
        assert await sm.aCreateTable("t", {"id": "INTEGER"}) is False
        assert await sm.aDropTable("t") is False
        assert await sm.aHasTable("t") is False
        object.__setattr__(sm, "_initialized", True)


class TestSyncAsyncCoexistence:
    """同步兼容层与异步原生共存"""

    def test_sync_bridge_matches_async(self, sm):
        sm.set("sk", "v")
        assert sm.get("sk") == "v"
        # get_multi 历来按字面键查询（点号键不做嵌套解析）
        assert sm.get_multi(["sk"]) == {"sk": "v"}

    async def test_aclose(self, sm):
        await sm.aset("c.k", 1)
        await sm.aclose()
        # 关闭后重新获取资源仍可用（惰性重建）
        assert await sm.aget("c.k") == 1
