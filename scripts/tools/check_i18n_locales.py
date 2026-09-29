#!/usr/bin/env python3
"""
i18n 五语言键一致性检查

比对框架内全部 i18n locales 目录（Core 与 CLI 两套：src/ErisPulse/{Core,CLI}/i18n/locales/）
下五个语言文件（zh_cn / zh_tw / en / ja / ru）的翻译键集合，报告缺失键与多余键。
框架要求新增翻译键时五语言同步（AGENTS 规则 12），本脚本供开发自检与 CI 门禁使用。
（历史上只查 Core，CLI 那套 500+ 键完全在门禁外——已修复为自动发现全部 locales 目录。）

使用方法:
    python scripts/tools/check_i18n_locales.py            # 检查全部，不一致时退出码 1
    python scripts/tools/check_i18n_locales.py --base en  # 指定基准语言（默认 zh_cn）
    python scripts/tools/check_i18n_locales.py --fix-report  # 额外输出可粘贴的缺失键清单
"""

import argparse
import ast
import sys
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parent.parent.parent / "src" / "ErisPulse"
LANGS = ["zh_cn", "zh_tw", "en", "ja", "ru"]


def discover_locales_dirs() -> "list[Path]":
    """自动发现 src/ErisPulse 下全部 i18n/locales 目录（Core / CLI 及未来新增套件）"""
    return sorted(p / "locales" for p in SRC_ROOT.rglob("i18n") if (p / "locales").is_dir())


def load_keys_from(locales_dir: Path, lang: str) -> dict[str, str]:
    """以字面量方式读取某语言文件的键集合（不触发框架初始化）"""
    path = locales_dir / f"{lang}.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "TRANSLATIONS" for t in node.targets
        ):
            if isinstance(node.value, ast.Dict):
                return {
                    ast.literal_eval(k): ast.literal_eval(v)
                    for k, v in zip(node.value.keys, node.value.values, strict=True)
                    if isinstance(k, ast.Constant)
                }
    raise RuntimeError(f"{path} 中未找到 TRANSLATIONS 字典")


def check_dir(locales_dir: Path, base: str, fix_report: bool) -> "tuple[int, list[str]]":
    """检查单个 locales 目录，返回 (基准键数, 问题列表)"""
    all_keys = {lang: load_keys_from(locales_dir, lang) for lang in LANGS}
    base_keys = set(all_keys[base])
    suite = locales_dir.parent.parent.name
    problems: list[str] = []
    for lang in LANGS:
        if lang == base:
            continue
        keys = set(all_keys[lang])
        for key in sorted(base_keys - keys):
            problems.append(f"[{suite}/{lang}] 缺失键: {key}")
            if fix_report:
                problems.append(f"    缺行: {key!r}: {all_keys[base][key]!r},")
        problems.extend(f"[{suite}/{lang}] 多余键: {key}" for key in sorted(keys - base_keys))
    return len(base_keys), problems


def main() -> int:
    parser = argparse.ArgumentParser(description="i18n 五语言键一致性检查（自动发现全部 locales 目录）")
    parser.add_argument("--base", default="zh_cn", choices=LANGS, help="基准语言（默认 zh_cn）")
    parser.add_argument(
        "--fix-report", action="store_true", help="输出各语言缺失键的原文行（便于粘贴补齐）"
    )
    args = parser.parse_args()

    dirs = discover_locales_dirs()
    if not dirs:
        print(f"未发现任何 i18n/locales 目录（搜索根: {SRC_ROOT}）")
        return 2

    others = ", ".join(lang for lang in LANGS if lang != args.base)
    all_problems: list[str] = []
    for locales_dir in dirs:
        total, problems = check_dir(locales_dir, args.base, args.fix_report)
        print(f"[{locales_dir.parent.parent.name}] 基准 {args.base}: {total} 键；比对: {others}")
        all_problems.extend(problems)

    if all_problems:
        print(f"\n发现 {len(all_problems)} 处不一致:")
        for line in all_problems:
            print(f"  {line}")
        return 1
    print("\n全部 locales 目录键集合一致 ✔")
    return 0


if __name__ == "__main__":
    sys.exit(main())
