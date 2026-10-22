#!/usr/bin/env python
"""
裸行为参数棘轮检查（工程健壮性规则 3 的机器执行）

扫描 ``src/ErisPulse/**``（排除 ``Core/constants.py`` 与 ``CLI/constants.py``
两个常量文件）中的裸数字行为参数：

- ``timeout=<数字>``
- ``sleep(<数字>)``（含 ``asyncio.sleep`` / ``time.sleep``）
- ``wait(timeout=<数字>)`` / ``join(timeout=<数字>)`` / ``result(timeout=<数字>)``

棘轮基线（import_layers_baseline.json 同款机制）：存量数量记入
``check_bare_params_baseline.json``，超过即失败——规则 3 要求新代码的
行为参数一律进常量文件，存量在触碰时逐步消化，只紧不松。

用法::

    python scripts/tools/check_bare_params.py                  # 检查
    python scripts/tools/check_bare_params.py --update-baseline  # 数量减少后下调基线
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

BASELINE_FILE = Path(__file__).parent / "baselines" / "check_bare_params_baseline.json"
SRC_ROOT = Path(__file__).parent.parent.parent / "src" / "ErisPulse"
EXEMPT_FILES = {"Core/constants.py", "CLI/constants.py"}

# 裸数字行为参数的模式（按行匹配，排除常量定义行与注释）
PATTERN = re.compile(
    r"(?:timeout|join|sleep)\s*[=(]\s*(?:\d+(?:\.\d+)?)\b"
)


def count_in_file(path: Path) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    for lineno, line in enumerate(
        path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1
    ):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if "Final[" in line or "Constants" in line:
            continue
        if PATTERN.search(line):
            hits.append((lineno, stripped[:80]))
    return hits


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--update-baseline", action="store_true")
    args = parser.parse_args()

    by_file: dict[str, list[str]] = {}
    for py in sorted(SRC_ROOT.rglob("*.py")):
        rel = py.relative_to(SRC_ROOT).as_posix()
        if rel in EXEMPT_FILES:
            continue
        hits = count_in_file(py)
        if hits:
            by_file[rel] = [f"{ln}: {text}" for ln, text in hits]

    total = sum(len(v) for v in by_file.values())

    if args.update_baseline:
        BASELINE_FILE.write_text(
            json.dumps({"total": total, "by_file": by_file}, ensure_ascii=False, indent=1) + "\n",
            encoding="utf-8",
        )
        print(f"[bare-params] 基线已更新: total={total}")
        return 0

    if BASELINE_FILE.exists():
        baseline = json.loads(BASELINE_FILE.read_text(encoding="utf-8"))
        base_total = int(baseline.get("total", 0))
    else:
        print(f"[bare-params] 基线文件缺失，当前裸参数总数 {total}（未设限）")
        base_total = None

    if base_total is not None and total > base_total:
        new_files = sorted(set(by_file) - set(baseline.get("by_file", {})))
        print(
            f"[bare-params] 裸行为参数总数 {total} 超过基线 {base_total}"
            f"（新增文件: {new_files or '见对比'}）。"
            "行为参数必须定义在 Core/constants.py（CLI 用 CLI/constants.py）；"
            "存量消化后可 --update-baseline 下调"
        )
        return 1

    print(f"[bare-params] 检查通过（裸参数总数 {total} / 基线 {base_total}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
