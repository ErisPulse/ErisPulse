#!/usr/bin/env python3
"""
ORM 真机验证（方向四：内置 ORM 在 mysql / postgres 上发布前验证）

用法与 test_storage_backend_verify.py 相同：在含 config/config.toml 的
运行目录执行，--backend 覆盖 ErisPulse.storage.backend。

覆盖项：自动建表 / create 与自增回填 / 字段类型（bool/float/JSON 列）/
约束校验失败抛错 / save 更新 / where 查询 / count / delete / 自动迁移
（新增列 ADD COLUMN）/ 关系映射（has-many + belongs-to）/ 环境事务回滚。

退出码：全部通过 0；任一失败 1。
"""

import argparse
import asyncio
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASS = "  [PASS]"
FAIL = "  [FAIL]"
_results: "list[tuple[str, bool, str]]" = []


def _record(name: str, ok: bool, detail: str = "") -> None:
    _results.append((name, ok, detail))
    print(f"{PASS if ok else FAIL} {name}" + (f" — {detail}" if detail and not ok else ""))


async def _verify(backend: str) -> bool:
    from ErisPulse.Core.Bases import Field, Model, relationship
    from ErisPulse.Core.storage import storage

    print(f"\n== 后端: {backend} ==\n")

    class OrmVUser(Model):
        id: int = Field(primary_key=True, autoincrement=True)
        name: str = Field(max_length=64)
        age: int = Field(default=0, ge=0)
        active: bool = Field(default=True)
        tags: list = Field(default=None, nullable=True)
        posts = relationship("OrmVPost", foreign_key="user_id")

    class OrmVPost(Model):
        id: int = Field(primary_key=True, autoincrement=True)
        title: str = Field(max_length=128)
        user_id: int = Field(foreign_key=f"{OrmVUser.table_name()}.id")
        author = relationship("OrmVUser", foreign_key="user_id")  # belongs-to

    # 起始清场：DB 持久，跨运行残留会让计数类断言失真
    try:
        await storage.aDropTable(OrmVPost.table_name())
        await storage.aDropTable(OrmVUser.table_name())
    except Exception:
        pass

    # 1. 自动建表
    await OrmVUser.create_table()
    await OrmVPost.create_table()
    _record("自动建表", await storage.aHasTable(OrmVUser.table_name()) and await storage.aHasTable(OrmVPost.table_name()))

    # 2. create 与自增回填 + bool 字段
    alice = await OrmVUser.create(name="alice", age=30, active=True)
    _record("create/自增回填", alice.id is not None and alice.id >= 1)
    _record("bool 字段往返", alice.active is True)

    # 3. JSON 列往返
    bob = await OrmVUser.create(name="bob", age=17, tags=["a", "b", {"k": 1}])
    again = await OrmVUser.where(OrmVUser.id == bob.id).first()
    _record(
        "JSON 列往返",
        again is not None and again.tags == ["a", "b", {"k": 1}],
        f"got tags={getattr(again, 'tags', '<no-row>')!r}",
    )

    # 4. 约束校验失败抛错（ge=0）
    rejected = False
    try:
        await OrmVUser.create(name="bad", age=-1)
    except ValueError:
        rejected = True
    _record("约束校验拒绝", rejected)

    # 5. save 更新
    alice.age = 31
    n = await alice.save()
    fresh = await OrmVUser.where(OrmVUser.id == alice.id).first()
    _record("save 更新", n == 1 and fresh is not None and fresh.age == 31, f"n={n}")

    # 6. where 查询
    adults = await OrmVUser.where(OrmVUser.age >= 18).all()
    _record(
        "where 查询",
        {u.name for u in adults} == {"alice"},
        f"got={sorted(u.name for u in adults)}",
    )

    # 7. count
    count = await OrmVUser.count()
    _record("count", count == 2, f"got={count}")

    # 8. 自动迁移：同表名的 V2 声明（新增列）再建表 → ADD COLUMN
    # （迁移由模型声明驱动：_fields 在 __init_subclass__ 一次性收集，
    #   动态往类上挂 Field 不会进入迁移比对）
    class OrmVUserV2(Model):
        __tablename__ = OrmVUser.table_name()
        id: int = Field(primary_key=True, autoincrement=True)
        name: str = Field(max_length=64)
        age: int = Field(default=0, ge=0)
        active: bool = Field(default=True)
        tags: list = Field(default=None, nullable=True)
        nickname: str = Field(max_length=32, nullable=True)

    await OrmVUserV2.create_table()
    cols = await storage.aGetTableColumns(OrmVUser.table_name())
    _record("自动迁移(ADD COLUMN)", "nickname" in cols)

    # 9. 关系映射 has-many / belongs-to
    post = await OrmVPost.create(title="hello", user_id=alice.id)
    alice_posts = await alice.posts.all()
    _record("关系 has-many", len(alice_posts) == 1 and alice_posts[0].title == "hello")
    back = await post.author
    _record("关系 belongs-to", back is not None and back.id == alice.id)

    # 10. 环境事务回滚：事务内 create 可见 → 回滚后消失
    before = await OrmVUser.count()
    try:
        async with storage.atransaction():
            await OrmVUser.create(name="ghost", age=99)
            if await OrmVUser.count() != before + 1:
                raise RuntimeError("事务内读不到未提交写入")
            raise RuntimeError("intentional rollback")
    except RuntimeError as e:
        if "intentional rollback" not in str(e):
            _record("环境事务回滚", False, str(e))
        else:
            _record("环境事务回滚", await OrmVUser.count() == before)
    else:
        _record("环境事务回滚", False, "异常未触发回滚路径")

    # 11. delete
    n = await bob.delete()
    _record("delete", n == 1 and (await OrmVUser.where(OrmVUser.id == bob.id).first()) is None)

    # 12. 清理表
    await storage.aDropTable(OrmVPost.table_name())
    await storage.aDropTable(OrmVUser.table_name())
    _record("清理表", not await storage.aHasTable(OrmVUser.table_name()) and not await storage.aHasTable(OrmVPost.table_name()))

    failed = [r for r in _results if not r[1]]
    print(f"\n== 结果: {len(_results) - len(failed)}/{len(_results)} 通过 ==")
    return not failed


def main() -> int:
    parser = argparse.ArgumentParser(description="ErisPulse ORM 真机验证")
    parser.add_argument("--backend", choices=["sqlite", "mysql", "postgres"], default=None)
    args = parser.parse_args()

    if args.backend:
        import os

        os.environ["ERISPULSE_STORAGE_BACKEND"] = args.backend

    ok = asyncio.run(_verify(args.backend or "config"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
