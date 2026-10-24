#!/usr/bin/env python
"""
静默吞异常棘轮检查（工程健壮性规则 1 的机器执行）

统计 ``src/ErisPulse/**`` 中 ``except ...:`` 体内仅含 ``pass`` 的处理器
（完全静默吞异常），以棘轮基线约束：**只紧不松**——新增静默吞异常即失败。

规则背景见 ``docs/zh-CN/styleguide/engineering.md`` 第 1 条：探测型/降级型
允许 `pass` 但应有安全默认语义；资源释放与数据写入路径必须留痕。本检查
不做语义判定（那是评审的职责），只保证总量不回潮。

用法::

    python scripts/tools/check_silent_except.py                  # 检查
    python scripts/tools/check_silent_except.py --update-baseline  # 消化存量后下调基线
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

from ..common import REPO_ROOT

BASELINE_FILE = REPO_ROOT / "scripts" / "tools" / "baselines" / "check_silent_except_baseline.json"
SRC_ROOT = REPO_ROOT / "src" / "ErisPulse"


def count_in_file(path: Path) -> int:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return 0
    n = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            body = node.body
            if len(body) == 1 and isinstance(body[0], ast.Pass):
                n += 1
    return n


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--update-baseline", action="store_true")
    args = parser.parse_args(argv)

    by_file: dict[str, int] = {}
    for py in sorted(SRC_ROOT.rglob("*.py")):
        rel = py.relative_to(SRC_ROOT).as_posix()
        n = count_in_file(py)
        if n:
            by_file[rel] = n
    total = sum(by_file.values())

    if args.update_baseline:
        BASELINE_FILE.write_text(
            json.dumps({"total": total, "by_file": by_file}, ensure_ascii=False, indent=1) + "\n",
            encoding="utf-8",
        )
        print(f"[silent-except] 基线已更新: total={total}")
        return 0

    if BASELINE_FILE.exists():
        baseline = json.loads(BASELINE_FILE.read_text(encoding="utf-8"))
        base_total = int(baseline.get("total", 0))
        if total > base_total:
            new_files = sorted(set(by_file) - set(baseline.get("by_file", {})))
            print(
                f"[silent-except] 静默吞异常总数 {total} 超过基线 {base_total}"
                f"（新增文件: {new_files or '见对比'}）。"
                "资源释放/数据写入路径必须留痕（logger.debug 起步），"
                "存量消化后可 --update-baseline 下调"
            )
            return 1
    else:
        print(f"[silent-except] 基线文件缺失，当前总数 {total}（未设限）")

    print(f"[silent-except] 检查通过（静默吞异常总数 {total} / 基线 {base_total if BASELINE_FILE.exists() else '未设限'}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
