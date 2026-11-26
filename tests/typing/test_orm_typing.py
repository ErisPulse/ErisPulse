"""
ORM 类型注解回归测试（静态 + 运行时双层）

静态层：本目录纳入 basedpyright 检查范围（pyproject ``[tool.basedpyright]``
include）。字段按值类型注解（``age: int = Field(...)``）声明时，类访问比较
（``User.age > 18``）在类型检查器视角为 ``bool``（注解屏蔽描述符协议，
SQLModel 同款"虚拟类型"现象），条件入口签名必须保持 ``Condition | bool``
边界——一旦收窄回纯 ``Condition``，下方各调用点将重新产生
invalid-argument-type 错误并被 CI 门禁拦截。

运行时层：真 ``bool`` 入参拒绝、``where_in`` 字段校验与 IN 编译、
条件组合编译、关系查询集条件追加。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from ErisPulse.Core.Bases.model import Condition, Field, Model, QuerySet, relationship


class TypingUser(Model):
    id: int = Field(primary_key=True, autoincrement=True)
    name: str = Field(max_length=64, default="")
    posts = relationship("TypingPost", foreign_key="user_id")


class TypingPost(Model):
    id: int = Field(primary_key=True, autoincrement=True)
    user_id: int = Field(foreign_key="typing_users.id")
    title: str = Field(default="")


# ---- 静态层：调用点存在性即断言（检查器视角必须零错误） ----


def test_where_accepts_column_comparison_static() -> None:
    """where 直接消费类访问比较（回退为纯 Condition 签名时本用例静态报错）"""
    qs = TypingUser.where(TypingUser.id > 1)
    assert isinstance(qs, QuerySet)
    qs2: QuerySet[TypingUser] = TypingUser.where(
        (TypingUser.id > 1) & (TypingUser.name == "x")
    )
    assert qs2 is not None
    assert TypingUser.where_in("id", [1, 2, 3]) is not None
    assert TypingUser.all() is not None


if TYPE_CHECKING:

    async def _typed_rows_static_proof(qs: QuerySet[TypingUser]) -> None:  # pyright: ignore[reportUnusedFunction]
        """静态断言：first()/all() 元素为模型实例（typed rows，仅签名检查不执行）"""
        first = await qs.first()
        if first is not None:
            first.name.upper()
        rows = await qs.all()
        rows[0].name.upper()


# ---- 运行时层 ----


def test_where_compiles_column_comparison() -> None:
    """类访问比较运行时产物为 Condition（非 bool）"""
    qs = TypingUser.where(TypingUser.id > 1)
    assert isinstance(qs._condition, Condition)
    sql, params = qs._condition.compile()
    assert sql == '"id" > ?'
    assert params == [1]


async def test_where_rejects_runtime_bool() -> None:
    """真 bool 入参无法编译为 SQL 条件，运行时显式拒绝（异步入口须 await 触发函数体）"""
    with pytest.raises(TypeError, match="plain bool"):
        TypingUser.where(True)
    with pytest.raises(TypeError, match="plain bool"):
        TypingUser.where(TypingUser.id > 1, False)
    with pytest.raises(TypeError, match="plain bool"):
        await TypingUser.count(False)
    with pytest.raises(TypeError, match="plain bool"):
        await TypingUser.delete_all(True)
    with pytest.raises(TypeError, match="plain bool"):
        await TypingUser.update_all(False, name="x")
    with pytest.raises(TypeError, match="plain bool"):
        user = TypingUser(id=1)
        user.posts.where(True)


def test_multi_condition_and_compile() -> None:
    """多条件 AND 组合编译"""
    qs = TypingUser.where(TypingUser.id > 1, TypingUser.name == "x")
    assert isinstance(qs._condition, Condition)
    sql, params = qs._condition.compile()
    assert sql == '("id" > ? AND "name" = ?)'
    assert params == [1, "x"]


def test_where_in_compiles_and_validates() -> None:
    """where_in 编译 IN 片段；未知字段定义期报错"""
    qs = TypingUser.where_in("id", [1, 2, 3])
    assert isinstance(qs._condition, Condition)
    sql, params = qs._condition.compile()
    assert sql == '"id" IN (?, ?, ?)'
    assert params == [1, 2, 3]
    with pytest.raises(ValueError, match="where_in"):
        TypingUser.where_in("nope", [1])


def test_where_in_empty_collection_always_false() -> None:
    """空集合 IN 编译为恒假片段"""
    qs = TypingUser.where_in("id", [])
    assert isinstance(qs._condition, Condition)
    sql, _ = qs._condition.compile()
    assert sql == "1=0"


def test_condition_combinator_rejects_runtime_bool() -> None:
    """真 bool 经 &/| 组合链漏入时同样显式拒绝（两侧操作数顺序均覆盖）"""
    cond = TypingUser.id > 1
    with pytest.raises(TypeError, match="plain bool"):
        _ = cond & True
    with pytest.raises(TypeError, match="plain bool"):
        _ = True & cond
    with pytest.raises(TypeError, match="plain bool"):
        _ = cond | False
    with pytest.raises(TypeError, match="plain bool"):
        _ = False | cond


def test_related_many_where_appends_condition() -> None:
    """关系查询集条件追加（与外键条件 AND 组合）"""
    user = TypingUser(id=1, name="u")
    posts = user.posts
    filtered = posts.where(TypingPost.title == "t")
    assert isinstance(filtered._condition, Condition)
    sql, params = filtered._condition.compile()
    assert sql == '("user_id" = ? AND "title" = ?)'
    assert params == [1, "t"]
