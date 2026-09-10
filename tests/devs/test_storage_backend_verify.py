#!/usr/bin/env python3
"""
存储后端发布前验证脚本（2.8.0 多后端引擎 mysql / postgres 真机验证）

手动开发者工具（pytest 不会收集本文件：无 test_ 前缀用例函数）。
在目标项目的运行目录（含 config/config.toml）执行，对配置的存储后端
（或 --backend 指定的后端）逐项演练 2.8 存储引擎的核心能力并输出 PASS/FAIL：

    python tests/devs/test_storage_backend_verify.py                # 使用 config.toml 的 backend
    python tests/devs/test_storage_backend_verify.py --backend mysql
    python tests/devs/test_storage_backend_verify.py --backend postgres

连接参数取自 config.toml 的 [ErisPulse.storage.mysql] / [ErisPulse.storage.postgres]
（或对应 ERISPULSE_STORAGE_* 环境变量）。

覆盖项：
  KV 基本读写删 / 嵌套键 / JSON 值往返 / 批量读写删 / 全键枚举 /
  事务（提交与回滚）/ 查询构建器（含 ToDict）/ 建表-查在-删表 / 连接释放

退出码：全部通过 0；任一失败 1。

{!--< internal-use >!--}
发布工具脚本，不属于框架运行时。
{!--< /internal-use >!--}
"""

import argparse
import asyncio
import sys
import time

# Windows GBK 控制台兼容
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASS = "  [PASS]"
FAIL = "  [FAIL]"
_results: list[tuple[str, bool, str]] = []


def _record(name: str, ok: bool, detail: str = "") -> None:
    _results.append((name, ok, detail))
    print(f"{PASS if ok else FAIL} {name}" + (f" — {detail}" if detail and not ok else ""))


async def _verify(backend: str) -> bool:
    from ErisPulse.Core.storage import storage

    print(f"\n== 后端: {backend} ==\n")

    # 1. KV 基本读写
    await storage.aset("verify:basic", "hello")
    _record("KV 写入/读取", await storage.aget("verify:basic") == "hello")

    # 2. 嵌套键
    await storage.aset("verify:nested:a:b", 123)
    _record("KV 嵌套键", await storage.aget("verify:nested:a:b") == 123)

    # 3. JSON 值往返
    payload = {"list": [1, 2, 3], "nested": {"ok": True}, "ts": time.time()}
    await storage.aset("verify:json", payload)
    got = await storage.aget("verify:json")
    _record("JSON 值往返", got == payload)

    # 4. 批量读写
    await storage.aset_multi({f"verify:multi:{i}": {"i": i} for i in range(20)})
    multi = await storage.aget_multi([f"verify:multi:{i}" for i in range(20)])
    _record("批量读写(20)", len(multi) == 20 and multi["verify:multi:7"] == {"i": 7})

    # 5. 事务提交（事务块内操作自动路由到事务连接，无需传 conn）
    async with storage.atransaction():
        await storage.aset("verify:tx:commit", "in_tx")
    _record("事务提交", await storage.aget("verify:tx:commit") == "in_tx")

    # 6. 事务回滚：事务内写入可见 → 异常触发回滚 → 事务外消失
    ok, detail = False, ""
    try:
        async with storage.atransaction():
            await storage.aset("verify:tx:rollback", "pending")
            if await storage.aget("verify:tx:rollback") != "pending":
                raise RuntimeError("事务内读不到未提交写入")
            raise RuntimeError("intentional rollback")
    except RuntimeError as e:
        if "intentional rollback" in str(e):
            ok = (await storage.aget("verify:tx:rollback")) is None
            if not ok:
                detail = "回滚后仍读到值"
        else:
            ok, detail = False, str(e)
    _record("事务回滚", ok, detail)

    # 7. 查询构建器 + ToDict
    table = f"verify_{backend}_tbl"
    await storage.aCreateTable(table, {"id": "INTEGER PRIMARY KEY", "name": "TEXT"})
    _record("建表/表存在", await storage.aHasTable(table))
    storage.Table(table).Insert({"id": 1, "name": "alpha"}).Execute()
    storage.Table(table).Insert({"id": 2, "name": "beta"}).Execute()
    rows = await storage.Table(table).Select("id", "name").Where("id > ?", 0).ToDict().OrderBy("id").aExecute()
    _record("查询构建器+ToDict", rows == [{"id": 1, "name": "alpha"}, {"id": 2, "name": "beta"}], str(rows))
    count = await storage.Table(table).Where("name = ?", "beta").aCount()
    _record("条件计数", count == 1)

    # 8. 清理
    await storage.adelete_multi(
        ["verify:basic", "verify:nested:a:b", "verify:json", "verify:tx:commit", "verify:tx:rollback"]
        + [f"verify:multi:{i}" for i in range(20)]
    )
    keys = await storage.aget_all_keys()
    _record("删除/全键清理", not [k for k in keys if k.startswith("verify:")])
    await storage.aDropTable(table)
    _record("删表", not await storage.aHasTable(table))

    # 9. 连接释放
    await storage.aclose()
    _record("连接释放", True)

    failed = [r for r in _results if not r[1]]
    print(f"\n== 结果: {len(_results) - len(failed)}/{len(_results)} 通过 ==")
    return not failed


def main() -> int:
    parser = argparse.ArgumentParser(description="ErisPulse 存储后端发布前验证")
    parser.add_argument("--backend", choices=["sqlite", "mysql", "postgres"], default=None,
                        help="覆盖 config.toml 的 ErisPulse.storage.backend")
    args = parser.parse_args()

    if args.backend:
        import os

        os.environ["ERISPULSE_STORAGE_BACKEND"] = args.backend

    ok = asyncio.run(_verify(args.backend or "config"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
