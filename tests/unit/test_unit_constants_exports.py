"""
Core/constants.py 公共常量导出完整性守护

模块级公共常量（非下划线开头）必须全部列入 ``__all__``，防止
``import *`` 与文档生成遗漏；反向校验 ``__all__`` 无悬空引用。
"""

import ast
from pathlib import Path

CONSTANTS_FILE = (
    Path(__file__).resolve().parents[2] / "src" / "ErisPulse" / "Core" / "constants.py"
)


def _parse():
    tree = ast.parse(CONSTANTS_FILE.read_text(encoding="utf-8"))
    defined: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            defined.add(node.target.id)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    defined.add(target.id)
    all_list: set[str] | None = None
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets
        ):
            all_list = set(ast.literal_eval(node.value))
    return defined, all_list


def test_public_constants_all_exported():
    defined, all_list = _parse()
    assert all_list is not None, "constants.py 缺少 __all__"
    missing = {n for n in defined if not n.startswith("_")} - all_list
    assert not missing, f"未列入 __all__ 的公共常量: {sorted(missing)}"


def test_all_has_no_dangling_reference():
    defined, all_list = _parse()
    assert all_list is not None
    extra = all_list - defined
    assert not extra, f"__all__ 引用了不存在的常量: {sorted(extra)}"
