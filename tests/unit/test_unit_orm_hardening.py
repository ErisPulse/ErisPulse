"""
ORM 硬化单元测试（真机验证发现问题的回归钉）

覆盖：Condition 真值判断拒绝、first() 不污染原查询集、迁移 DDL 的
可空性参数化、bool 字段读回跨后端归一化（sqlite 返回 int → bool）。
"""

import os
import tempfile

import pytest

from ErisPulse.Core.Bases import Field, Model
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
def storage_manager(temp_db_file):
    StorageManager._instance = None

    manager = StorageManager.__new__(StorageManager)
    manager.db_path = temp_db_file
    manager._init_db()
    manager._initialized = True

    yield manager

    StorageManager._instance = None


class HardUser(Model):
    __storage__ = None  # 测试内注入 sqlite 管理器

    id: int = Field(primary_key=True, autoincrement=True)
    name: str = Field(max_length=64)
    age: int = Field(default=0)
    active: bool = Field(default=True)

    async def on_unload(self, ctx=None):
        pass


class TestConditionBool:
    def test_truthiness_rejected(self):
        cond = HardUser.age == 18
        with pytest.raises(TypeError):
            bool(cond)

    def test_combinators_still_work(self):
        cond = (HardUser.age > 1) & (HardUser.age < 9)
        assert cond is not None  # & / | 组合不受 __bool__ 影响


class TestFirstClone:
    def test_first_does_not_pollute(self, storage_manager):
        HardUser.__storage__ = storage_manager

        async def _run():
            await HardUser.create_table()
            for i in range(3):
                await HardUser.create(name=f"u{i}", age=20 + i)

            qs = HardUser.where(HardUser.age >= 0)
            first = await qs.first()
            rows = await qs.all()  # first() 不得把原查询集的 LIMIT 留下
            return first, rows

        try:
            first, rows = asyncio_run(_run())
            assert first is not None
            assert len(rows) == 3
        finally:
            HardUser.__storage__ = None


class TestColumnDefinitionNullable:
    def test_default_emits_not_null(self):
        ddl = Field(max_length=8).column_definition()
        assert "NOT NULL" in ddl

    def test_nullable_override_omits_not_null(self):
        ddl = Field(max_length=8).column_definition(nullable_override=True)
        assert "NOT NULL" not in ddl
        assert "VARCHAR(8)" in ddl


class TestBoolHydration:
    def test_sqlite_bool_readback_normalized(self, storage_manager):
        HardUser.__storage__ = storage_manager

        async def _run():
            await HardUser.create_table()
            on = await HardUser.create(name="on", active=True)
            off = await HardUser.create(name="off", active=False)
            on_row = await HardUser.where(HardUser.id == on.id).first()
            off_row = await HardUser.where(HardUser.id == off.id).first()
            return on_row, off_row

        try:
            on_row, off_row = asyncio_run(_run())
            assert on_row.active is True
            assert off_row.active is False
        finally:
            HardUser.__storage__ = None


def asyncio_run(coro):
    import asyncio

    return asyncio.run(coro)
