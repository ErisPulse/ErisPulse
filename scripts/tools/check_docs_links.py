#!/usr/bin/env python3
"""
docs 内部相对链接检查

扫描 docs/zh-CN 下全部 Markdown 的相对链接（`[text](path)` 与引用式链接），
校验目标文件存在（`#锚点` 仅剥离不做存在性校验——GitHub 对 CJK 标题的 slug 规则
无法可靠离线复现）。只校验仓库内部相对路径，不访问网络。
自动跳过 `ai-support/` 与 `api-reference/auto_api/`（两者均为生成产物：前者由
generate-ai-prompts.py 生成，后者由 generate-api-docs.py 从 docstring 生成，其
相对链接随生成目录层级变化，不适用源目录校验——死链应修源 docstring 后由 CI 重新生成）。
对应 AGENTS 规则 16 的痛点：删除/移动 zh-CN 文档时其它语言与引用易留死链。

使用方法:
    python scripts/tools/check_docs_links.py                # 检查 docs/zh-CN，死链退出码 1
    python scripts/tools/check_docs_links.py --root docs    # 指定根目录
"""

import argparse
import re
import sys
from pathlib import Path

# Markdown 链接：[text](target)——排除图片在 targets 中单独处理也兼容（! 前缀不匹配此模式）
LINK_RE = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
# 引用式定义：[id]: target
REF_DEF_RE = re.compile(r"^\s{0,3}\[[^\]]+\]:\s+(\S+)", re.MULTILINE)
# 代码围栏（围栏内内容不检查）
FENCE_RE = re.compile(r"^\s*(```|~~~)")


def strip_fence_blocks(text: str) -> str:
    lines, in_fence, out = text.splitlines(), False, []
    for line in lines:
        if FENCE_RE.match(line):
            in_fence = not in_fence
            out.append("")
            continue
        out.append("" if in_fence else line)
    return "\n".join(out)


def iter_md_files(root: Path):
    yield from sorted(root.rglob("*.md"))


def check_file(path: Path, allow_missing_anchor: bool) -> list[str]:
    problems: list[str] = []
    raw = path.read_text(encoding="utf-8")
    text = strip_fence_blocks(raw)
    targets = LINK_RE.findall(text) + REF_DEF_RE.findall(text)
    base = path.parent
    for target in targets:
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        clean = target.split("#", 1)[0]
        if not clean:
            continue  # 纯锚点：不做存在性校验（CJK 标题 slug 无法离线可靠复现）
        resolved = (base / clean).resolve()
        if resolved.suffix == "" and not resolved.exists() and (base / clean.rstrip("/")).is_dir():
            continue  # 目录链接（以 / 结尾）
        if not resolved.exists():
            problems.append(f"{path}: 死链 -> {target}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description="docs 内部相对链接检查")
    parser.add_argument("--root", default="docs/zh-CN", help="扫描根目录（默认 docs/zh-CN）")
    args = parser.parse_args()

    root = Path(args.root)
    if not root.is_dir():
        print(f"根目录不存在: {root}")
        return 2

    problems: list[str] = []
    checked = 0
    for md in iter_md_files(root):
        if "ai-support" in md.parts or "auto_api" in md.parts:
            continue  # 自动生成目录，不检查（死链修源头后由 CI 重新生成）
        checked += 1
        problems.extend(check_file(md, False))

    print(f"已检查 {checked} 个 Markdown 文件（{root}）")
    if problems:
        print(f"\n发现 {len(problems)} 处链接问题:")
        for line in problems:
            print(f"  {line}")
        return 1
    print("内部链接全部有效 ✔")
    return 0


if __name__ == "__main__":
    sys.exit(main())
