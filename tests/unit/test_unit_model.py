"""
数据模型层（ORM）单元测试

测试 Field 声明与描述符语义（类访问=列表达式 / 实例访问=行值）、Active
Record CRUD（create / get / where / save / delete / 批量操作）、查询表达式
编译与组合、自动建表（DDL 方言记号）、JSON 列序列化、共享约束校验器引擎，
以及 sqlite 内存/临时库全链路。
"""

import os
import tempfile

import pytest

from ErisPulse.Core.Bases import Field, Model
from ErisPulse.Core.Bases.config_schema import (
    python_type_category,
    validate_field_constraints,
)
from ErisPulse.Core.storage import StorageManager


@pytest.fixture
def sm():
    """独立临时 sqlite 后端（互不污染）"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".db", delete=False) as f:
        temp_path = f.name
    StorageManager._instance = None
    manager = StorageManager.__new__(StorageManager)
    manager.db_path = temp_path
    manager._init_db()
    manager._initialized = True
    yield manager
    StorageManager._instance = None
    for ext in ["", "-wal", "-shm"]:
        path = temp_path + ext
        if os.path.exists(path):
            try:
                os.remove(path)
            except PermissionError:
                pass


def make_user_model(sm):
    """构造挂载到临时后端的 User 模型（各测试独立类与表）"""

    class User(Model):
        __storage__ = sm
        __tablename__ = "orm_users"

        id: int = Field(primary_key=True, autoincrement=True)
        name: str = Field(max_length=64)
        age: int = Field(default=0, ge=0, le=150)
        tags: list = Field(default_factory=list)

    return User


@pytest.mark.asyncio
async def test_create_and_get_roundtrip(sm):
    User = make_user_model(sm)
    assert await User.create_table()
    assert await User.has_table()

    alice = await User.create(name="Alice", age=20, tags=["a", "b"])
    assert alice.id is not None  # 自增主键回填

    got = await User.get(id=alice.id)
    assert got is not alice  # 逐行实例
    assert (got.name, got.age, got.tags) == ("Alice", 20, ["a", "b"])  # JSON 反序列化


@pytest.mark.asyncio
async def test_default_factory_and_defaults(sm):
    User = make_user_model(sm)
    await User.create_table()

    u = await User.create(name="NoAge")
    assert u.age == 0 and u.tags == []
    got = await User.get(id=u.id)
    assert got.age == 0 and got.tags == []


@pytest.mark.asyncio
async def test_query_expressions(sm):
    User = make_user_model(sm)
    await User.create_table()
    await User.create(name="A", age=10)
    await User.create(name="B", age=20)
    await User.create(name="C", age=30)

    assert [u.name for u in await User.where(User.age > 15).all()] == ["B", "C"]
    assert [u.name for u in await User.where((User.age > 5) & (User.age < 25)).all()] == ["A", "B"]
    assert [u.name for u in await User.where((User.age > 25) | (User.age < 15)).all()] == ["A", "C"]
    assert [u.name for u in await User.where(User.name.in_(["A", "C"])).all()] == ["A", "C"]

    ordered = await User.all().order_by("-age").all()
    assert [u.name for u in ordered] == ["C", "B", "A"]
    assert (await User.all().order_by("-age").first()).name == "C"
    assert await User.where(User.age > 999).first() is None


@pytest.mark.asyncio
async def test_save_and_delete_instance(sm):
    User = make_user_model(sm)
    await User.create_table()
    u = await User.create(name="Old", age=1, tags=["t"])

    u.name = "New"
    u.tags = ["x", "y"]
    await u.save()
    got = await User.get(id=u.id)
    assert (got.name, got.tags) == ("New", ["x", "y"])

    await got.delete()
    assert await User.get(id=u.id) is None
    assert await User.count() == 0


@pytest.mark.asyncio
async def test_bulk_update_delete_count(sm):
    User = make_user_model(sm)
    await User.create_table()
    await User.create(name="a", age=5)
    await User.create(name="b", age=15)

    assert await User.update_all(User.age < 10, age=8) == 1
    assert await User.count(User.age == 8) == 1
    assert await User.delete_all(User.age >= 15) == 1
    assert await User.count() == 1


@pytest.mark.asyncio
async def test_shared_constraint_validator(sm):
    """共享约束校验器：required / choices / ge / le / max_length"""
    User = make_user_model(sm)
    await User.create_table()

    with pytest.raises(ValueError):  # 必填（name 无默认值）
        await User.create(age=5)
    with pytest.raises(ValueError):  # max_length
        await User.create(name="x" * 100)
    with pytest.raises(ValueError):  # ge/le
        await User.create(name="ok", age=999)

    # 校验器纯函数直测
    assert validate_field_constraints("age", 20, min_value=0, max_value=150) == []
    assert validate_field_constraints("age", -1, min_value=0) != []
    assert validate_field_constraints("role", "x", choices=["a", "b"]) != []
    assert validate_field_constraints("bio", "x" * 10, max_length=5) != []
    assert validate_field_constraints("opt", "", required=True) != []
    assert validate_field_constraints("opt", None, required=False) == []  # 非必填空值跳过


@pytest.mark.asyncio
async def test_null_and_unique_columns(sm):
    class Item(Model):
        __storage__ = sm
        __tablename__ = "orm_items"

        id: int = Field(primary_key=True, autoincrement=True)
        code: str = Field(unique=True, max_length=16)
        note: str = Field(default="", nullable=True)

    await Item.create_table()
    await Item.create(code="X1", note=None)
    await Item.create(code="X2")  # nullable 缺省 None 可入库
    with pytest.raises(ValueError):  # code 必填（无默认值）
        await Item.create(note="n")


class TestDeclaration:
    """声明期语义（无需数据库）"""

    def test_snake_case_table_name(self):
        class UserProfile(Model):
            pass

        assert UserProfile.table_name() == "user_profile"

    def test_tablename_override_validated(self):
        class T1(Model):
            __tablename__ = "custom_t"

        assert T1.table_name() == "custom_t"

        with pytest.raises(ValueError):

            class T2(Model):
                __tablename__ = "bad name; drop"

    def test_class_access_returns_column_expr(self):
        class User(Model):
            id: int = Field(primary_key=True)

        assert User.id.column == "id"
        cond = User.id == 1
        sql, params = cond.compile()
        assert sql == '"id" = ?' and params == [1]

    def test_instance_access_returns_value(self):
        class User(Model):
            name: str = Field(default="n")

        assert User(name="x").name == "x"

    def test_base_model_alias(self):
        from ErisPulse.Core.Bases import BaseModel

        assert BaseModel is Model

    def test_unknown_init_field_rejected(self):
        class User(Model):
            name: str = Field(default="")

        with pytest.raises(TypeError):
            User(nope=1)

    def test_python_type_category_shared(self):
        """共享类型注册表：config 的 TOML 映射与 ORM 同源"""
        assert python_type_category(int) == "int"
        assert python_type_category(bool) == "bool"
        assert python_type_category(list) == "list"
        assert python_type_category("str") == "str"


@pytest.mark.asyncio
async def test_no_pk_model_requires_no_backfill(sm):
    class Setting(Model):
        __storage__ = sm
        __tablename__ = "orm_settings"

        key: str = Field(primary_key=True, max_length=32)
        value: str = Field(default="")

    await Setting.create_table()
    s = await Setting.create(key="k", value="v")
    assert s.key == "k"
    assert (await Setting.get(key="k")).value == "v"
    s.value = "v2"
    await s.save()
    assert (await Setting.get(key="k")).value == "v2"
