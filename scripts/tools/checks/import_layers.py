#!/usr/bin/env python
"""
导入分层守门检查（架构重构配套闸门）

两类规则：

1. **硬性禁区**（出现即失败）——分层架构明令禁止的顶层依赖边：
   - ``Core/**`` 顶层导入根包（``from .. import sdk`` / ``from ... import sdk``）
     或 ``loaders``：Core 只能依赖 constants/i18n/logger/Bases 与自身，
     根包/sdk/loaders 属于上层（SDK 门面经 kernel 注入，见 2.11 架构重写）。
   - ``runtime/**`` 顶层导入 ``CLI``：运行时层不得反向依赖命令行层。
   - ``loaders/**`` 顶层导入 ``CLI``：加载器层不得反向依赖命令行层。
   函数内懒导入不受此限（循环依赖的过渡垫片，受第二类规则看管）。

2. **棘轮基线**（只紧不松）——函数内内部导入（懒导入）总数不得超过基线。
   懒导入是循环依赖的烟雾报警器：重构应持续减少而非增加。基线存于
   ``import_layers_baseline.json``；合法重构减少数量后，用
   ``--update-baseline`` 下调基线。

用法::

    python scripts/tools/check_import_layers.py                # 检查
    python scripts/tools/check_import_layers.py --update-baseline  # 重算基线

:note: TYPE_CHECKING 块与 ``__init__.py`` 的聚合重导不计数。
"""

from __future__ import annotations

import argparse
import ast
import json
import sys

from ..common import REPO_ROOT

BASELINE_FILE = REPO_ROOT / "scripts" / "tools" / "baselines" / "import_layers_baseline.json"
SRC_ROOT = REPO_ROOT / "src" / "ErisPulse"

# 硬性禁区：(区域, 禁止的顶层导入目标判定函数说明)
FORBIDDEN_TOP_LEVEL = [
    ("Core", "root-or-loaders"),
    ("runtime", "CLI"),
    ("loaders", "CLI"),
]


def _import_target(node: ast.Import | ast.ImportFrom) -> str | None:
    """返回导入目标的 ErisPulse 内部顶级包名（非内部导入返回 None）"""
    if isinstance(node, ast.Import):
        for alias in node.names:
            if alias.name.startswith("ErisPulse"):
                return alias.name
        return None
    if node.level > 0:
        # 相对导入：按层级折算为绝对前缀（由调用方提供文件相对位置后判定）
        return f".{'.' * (node.level - 1)}{node.module or ''}"
    if node.module and node.module.startswith("ErisPulse"):
        return node.module
    return None


def _resolve_relative(rel_file: str, target: str) -> str:
    """把相对导入目标折算为相对于 src/ErisPulse 的绝对路径前缀"""
    if not target.startswith("."):
        return target
    parts = rel_file.split("/")
    # 文件自身不在包内计数（__init__.py 属于所在包，包前缀同为去掉文件名）
    base = parts[:-1]
    dots = len(target) - len(target.lstrip("."))
    rest = target.lstrip(".")
    up = dots - 1  # 一层点表示当前包
    pkg = base[: len(base) - up] if up else base
    return ".".join(pkg + ([rest] if rest else []))


def _top_level_targets(tree: ast.Module) -> list[tuple[str, str]]:
    """收集模块顶层的内部导入（不深入函数体；TYPE_CHECKING 块除外）"""
    results: list[tuple[str, str]] = []

    def visit(node) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.If) and _is_type_checking(child.test):
                continue
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue  # 函数体内属懒导入，由棘轮规则计数
            if isinstance(child, (ast.Import, ast.ImportFrom)):
                target = _import_target(child)
                if target:
                    results.append((target, ast.unparse(child)[:100]))
            visit(child)

    visit(tree)
    return results


def _is_type_checking(test: ast.expr) -> bool:
    return (isinstance(test, ast.Name) and test.id == "TYPE_CHECKING") or (
        isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING"
    )


def _count_lazy_imports(tree: ast.Module) -> int:
    """统计函数/方法体内的内部导入数量（含 async def、try、if 内；TYPE_CHECKING 块除外）"""

    def visit(node) -> int:
        total = 0
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.If) and _is_type_checking(child.test):
                continue
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                total += _count_in_function(child)
            elif isinstance(child, (ast.Import, ast.ImportFrom)):
                if _import_target(child):
                    total += 1
            else:
                total += visit(child)
        return total

    return visit(tree)


def _count_in_function(func: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    total = 0
    for node in ast.walk(func):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if _import_target(node):
                total += 1
    return total


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="将当前懒导入总数写回基线文件（仅在数量减少时使用）",
    )
    args = parser.parse_args(argv)

    if not SRC_ROOT.exists():
        print(f"[import-layers] 源码目录不存在: {SRC_ROOT}")
        return 2

    failures: list[str] = []
    lazy_by_file: dict[str, int] = {}

    for py in sorted(SRC_ROOT.rglob("*.py")):
        rel = py.relative_to(SRC_ROOT).as_posix()
        area = rel.split("/")[0]
        try:
            tree = ast.parse(py.read_text(encoding="utf-8", errors="replace"), filename=str(py))
        except SyntaxError as e:
            failures.append(f"{rel}: 语法解析失败 {e}")
            continue

        # 规则 1：顶层硬性禁区
        for raw_target, stmt in _top_level_targets(tree):
            target = _resolve_relative(rel, raw_target)
            denied = False
            if area == "Core":
                # 根包（ErisPulse.sdk / ErisPulse 本体）与 loaders 属上层；
                # ErisPulse.Core.* 内部互导与 ErisPulse.runtime 的懒导入例外另计
                if target == "ErisPulse" or target.startswith(("ErisPulse.sdk", "ErisPulse.loaders")):
                    denied = True
            elif area in ("runtime", "loaders"):
                if target.startswith("ErisPulse.CLI"):
                    denied = True
            if denied:
                failures.append(f"{rel}: 顶层禁区导入 [{stmt}]")

        # 规则 2：懒导入棘轮
        n = _count_lazy_imports(tree)
        if n:
            lazy_by_file[rel] = n

    lazy_total = sum(lazy_by_file.values())

    if args.update_baseline:
        BASELINE_FILE.write_text(
            json.dumps({"lazy_total": lazy_total, "by_file": lazy_by_file}, ensure_ascii=False, indent=1) + "\n",
            encoding="utf-8",
        )
        print(f"[import-layers] 基线已更新: lazy_total={lazy_total}")
        return 0

    if BASELINE_FILE.exists():
        baseline = json.loads(BASELINE_FILE.read_text(encoding="utf-8"))
        base_total = int(baseline.get("lazy_total", 0))
        if lazy_total > base_total:
            merged = dict(baseline.get("by_file", {}))
            for f, n in lazy_by_file.items():
                if n > merged.get(f, 0):
                    merged[f] = n
            new_files = set(lazy_by_file) - set(baseline.get("by_file", {}))
            failures.append(
                f"懒导入总数 {lazy_total} 超过基线 {base_total}（新增文件: {sorted(new_files) or '见 by_file 对比'}）。"
                "循环依赖应以懒导入为最后手段；确属必要请先重构既有懒导入后再 --update-baseline"
            )
    else:
        print(f"[import-layers] 基线文件缺失，当前懒导入总数 {lazy_total}（未设限）")

    if failures:
        print(f"[import-layers] 违规 {len(failures)} 项:")
        for f in failures:
            print(f"  - {f}")
        return 1

    print(f"[import-layers] 检查通过（懒导入总数 {lazy_total} / 基线 {base_total if BASELINE_FILE.exists() else '未设限'}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
