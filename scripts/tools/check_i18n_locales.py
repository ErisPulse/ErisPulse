#!/usr/bin/env python3
"""
i18n 五语言键一致性检查

比对 src/ErisPulse/Core/i18n/locales/ 下五个语言文件（zh_cn / zh_tw / en / ja / ru）
的翻译键集合，报告缺失键与多余键。框架要求新增翻译键时五语言同步（AGENTS 规则 12），
本脚本供开发自检与 CI 门禁使用。

使用方法:
    python scripts/tools/check_i18n_locales.py            # 检查全部，不一致时退出码 1
    python scripts/tools/check_i18n_locales.py --base en  # 指定基准语言（默认 zh_cn）
    python scripts/tools/check_i18n_locales.py --fix-report  # 额外输出可粘贴的缺失键清单
"""

import argparse
import ast
import sys
from pathlib import Path

LOCALES_DIR = Path(__file__).resolve().parent.parent.parent / "src" / "ErisPulse" / "Core" / "i18n" / "locales"
LANGS = ["zh_cn", "zh_tw", "en", "ja", "ru"]


def load_keys(lang: str) -> dict[str, str]:
    """以字面量方式读取某语言文件的键集合（不触发框架初始化）"""
    path = LOCALES_DIR / f"{lang}.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "TRANSLATIONS" for t in node.targets
        ):
            if isinstance(node.value, ast.Dict):
                return {
                    ast.literal_eval(k): ast.literal_eval(v)
                    for k, v in zip(node.value.keys, node.value.values)
                    if isinstance(k, ast.Constant)
                }
    raise RuntimeError(f"{path} 中未找到 TRANSLATIONS 字典")


def main() -> int:
    parser = argparse.ArgumentParser(description="i18n 五语言键一致性检查")
    parser.add_argument("--base", default="zh_cn", choices=LANGS, help="基准语言（默认 zh_cn）")
    parser.add_argument(
        "--fix-report", action="store_true", help="输出各语言缺失键的原文行（便于粘贴补齐）"
    )
    args = parser.parse_args()

    all_keys = {lang: load_keys(lang) for lang in LANGS}
    base_keys = set(all_keys[args.base])

    problems: list[str] = []
    for lang in LANGS:
        if lang == args.base:
            continue
        keys = set(all_keys[lang])
        missing = sorted(base_keys - keys)
        extra = sorted(keys - base_keys)
        for key in missing:
            problems.append(f"[{lang}] 缺失键: {key}")
            if args.fix_report:
                problems.append(f"    {lang}.py 缺行: {key!r}: {all_keys[args.base][key]!r},")
        for key in extra:
            problems.append(f"[{lang}] 多余键: {key}")

    total = len(base_keys)
    print(f"基准 {args.base}: {total} 键；比对语言: {', '.join(l for l in LANGS if l != args.base)}")
    if problems:
        print(f"\n发现 {len(problems)} 处不一致:")
        for line in problems:
            print(f"  {line}")
        return 1
    print("五语言键集合一致 ✔")
    return 0


if __name__ == "__main__":
    sys.exit(main())
