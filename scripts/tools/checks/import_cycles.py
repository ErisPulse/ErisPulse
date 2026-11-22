#!/usr/bin/env python
"""
导入循环依赖检查（顶层环边棘轮）

AST 扫描 ``src/ErisPulse`` 全部模块的**顶层无条件内部导入**，构建模块级
有向图，按强连通分量（SCC）报告环并门禁。语义与 basedpyright
``reportImportCycles`` 对齐：

- 函数体内导入（懒导入）与 ``TYPE_CHECKING`` 块不构成顶层边；
- ``__init__.py`` 的顶层聚合导入参与建图（包聚合点正是环的高发穿越面）；
- ``from pkg import sub`` 同时计入包节点边与子模块边（包初始化确实执行）；
- 子模块向**自身所在包** ``__init__`` 的边不计（父包必先于子模块初始化，
  该向边属结构性恒真，不构成运行时风险）。

用法::

    python -m scripts.tools check import-cycles                 # 门禁（发现环即非零退出）
    python -m scripts.tools check import-cycles --report        # 仅打印环清单，不设退出码

:note: 解环靠依赖单向化 / 注入 / 具体符号路径；改 lazy 不消顶层环（懒导入
    由 ``check import-layers`` 的棘轮基线看管）。
"""

from __future__ import annotations

import argparse
import ast
import itertools
import sys
from collections import defaultdict
from pathlib import Path

from ..common import REPO_ROOT

SRC_ROOT = REPO_ROOT / "src" / "ErisPulse"
PKG_ROOT = "ErisPulse"


# ==============================================================================
# 模块发现
# ==============================================================================


def _discover_modules() -> dict[str, Path]:
    """返回 模块名 -> 文件路径 映射（包 ``__init__.py`` 映射为包节点）"""
    modules: dict[str, Path] = {}
    for path in sorted(SRC_ROOT.rglob("*.py")):
        rel = path.relative_to(SRC_ROOT)
        parts = list(rel.parts)
        if parts[-1] == "__init__.py":
            parts = parts[:-1]
        else:
            parts[-1] = parts[-1][:-3]
        modules[".".join([PKG_ROOT, *parts])] = path
    return modules


def _module_of_file(path: Path, modules: dict[str, Path]) -> str | None:
    for name, file in modules.items():
        if file == path:
            return name
    return None


# ==============================================================================
# 顶层导入收集
# ==============================================================================


def _is_type_checking(test: ast.expr) -> bool:
    return (isinstance(test, ast.Name) and test.id == "TYPE_CHECKING") or (
        isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING"
    )


def _collect_top_level_imports(tree: ast.Module) -> list[tuple[ast.Import | ast.ImportFrom, int]]:
    """收集模块顶层（含类体、try/if 分支；不含函数体与 TYPE_CHECKING 块）的导入语句"""

    results: list[tuple[ast.Import | ast.ImportFrom, int]] = []

    def visit(node: ast.AST, in_class: bool) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.If) and _is_type_checking(child.test):
                continue
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if isinstance(child, (ast.Import, ast.ImportFrom)):
                results.append((child, child.lineno))
            elif isinstance(child, ast.ClassDef):
                visit(child, True)
            else:
                visit(child, in_class)

    visit(tree, False)
    return results


def _resolve_targets(
    node: ast.Import | ast.ImportFrom, module_name: str, modules: dict[str, Path]
) -> list[str]:
    """把一条导入语句解析为若干被导入模块名（含包节点）"""
    if isinstance(node, ast.Import):
        return [a.name for a in node.names if a.name == PKG_ROOT or a.name.startswith(f"{PKG_ROOT}.")]

    if node.level > 0:
        # 相对导入：按当前模块包前缀折算绝对目标
        parts = module_name.split(".")
        if modules[module_name].name == "__init__.py":
            anchor = parts  # 包节点：自身即包
        else:
            anchor = parts[:-1]
        up = node.level - 1  # 一层点表示当前包
        base = anchor[: len(anchor) - up] if up else anchor
        prefix = base + ([node.module] if node.module else [])
    else:
        if not node.module or not (node.module == PKG_ROOT or node.module.startswith(f"{PKG_ROOT}.")):
            return []
        prefix = node.module.split(".")

    prefix_str = ".".join(prefix)
    targets: list[str] = []
    if node.module is not None or node.level > 0:
        # `from pkg.mod import x` / `from . import x`：导入的包/模块本体
        if prefix_str in modules:
            targets.append(prefix_str)
    for alias in node.names:
        sub = f"{prefix_str}.{alias.name}"
        if sub in modules:
            targets.append(sub)
    return targets


def _is_own_package(target: str, module_name: str) -> bool:
    """target 是否为 module 自身所在包的 __init__ 节点"""
    return target.count(".") >= 1 and target == module_name.rpartition(".")[0]


# ==============================================================================
# 建图与找环
# ==============================================================================


def _build_graph(modules: dict[str, Path]) -> dict[str, dict[str, int]]:
    """邻接表：源模块 -> {目标模块: 首个导入行号}"""
    graph: dict[str, dict[str, int]] = defaultdict(dict)
    for module_name, path in modules.items():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node, lineno in _collect_top_level_imports(tree):
            for target in _resolve_targets(node, module_name, modules):
                if target == module_name or _is_own_package(target, module_name):
                    continue
                graph[module_name].setdefault(target, lineno)
    return graph


def _find_sccs(graph: dict[str, dict[str, int]]) -> list[list[str]]:
    """Tarjan 强连通分量；仅保留节点数 > 1 的分量（环）"""
    index_counter = [0]
    stack: list[str] = []
    lowlink: dict[str, int] = {}
    index: dict[str, int] = {}
    on_stack: set[str] = set()
    result: list[list[str]] = []

    def strongconnect(v: str) -> None:
        index[v] = index_counter[0]
        lowlink[v] = index_counter[0]
        index_counter[0] += 1
        stack.append(v)
        on_stack.add(v)

        for w in graph.get(v, {}):
            if w not in index:
                strongconnect(w)
                lowlink[v] = min(lowlink[v], lowlink[w])
            elif w in on_stack:
                lowlink[v] = min(lowlink[v], index[w])

        if lowlink[v] == index[v]:
            component = []
            while True:
                w = stack.pop()
                on_stack.discard(w)
                component.append(w)
                if w == v:
                    break
            if len(component) > 1:
                result.append(sorted(component))

    for v in sorted(graph):
        if v not in index:
            strongconnect(v)
    return result


def _cycle_path(scc: list[str], graph: dict[str, dict[str, int]]) -> list[str]:
    """在 SCC 内走一条简单环，返回节点序列（首尾相同）"""
    members = set(scc)
    start = scc[0]
    path = [start]
    seen = {start}
    current = start
    while True:
        nxt = next((t for t in sorted(graph.get(current, {})) if t in members), None)
        if nxt is None:
            break
        if nxt in seen:
            path.append(nxt)
            return path
        seen.add(nxt)
        path.append(nxt)
        current = nxt
    path.append(start)
    return path


# ==============================================================================
# main
# ==============================================================================


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="导入循环依赖检查（顶层环边棘轮）")
    parser.add_argument("--report", action="store_true", help="仅打印环清单，不设非零退出码")
    args = parser.parse_args(argv)

    modules = _discover_modules()
    graph = _build_graph(modules)
    sccs = _find_sccs(graph)

    if not sccs:
        print(f"import-cycles: PASS（{len(modules)} 个模块，顶层环边为 0）")
        return 0

    print(f"import-cycles: FAIL（发现 {len(sccs)} 个环）")
    for i, scc in enumerate(sccs, 1):
        print(f"\n--- 环 {i}（{len(scc)} 个模块）---")
        path = _cycle_path(scc, graph)
        for src, dst in itertools.pairwise(path):
            line = graph.get(src, {}).get(dst)
            loc = f"{modules[src].relative_to(REPO_ROOT)}:{line}" if line else modules[src]
            print(f"  {src}  --{loc}-->  {dst}")
    if not args.report:
        print("\n解环手段：依赖单向化 / 注入 / 具体符号路径（改 lazy 不消顶层环）")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
