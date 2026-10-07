#!/usr/bin/env python3
"""
发布版本一致性校验

校验 版本号（pyproject.toml）与 CHANGELOG 最新条目 一致；CI 的 tag 触发场景下
额外校验 tag 名（`v<version>` / `<version>` 两种形态均可）。

背景：此前 tag 创建（auto-tag-release）、PyPI 发布（pypi-publish）各自用 sed
从 pyproject 抽版本、且 tag 创建隐式依赖 CHANGELOG 段落存在，三处解析曾因
CHANGELOG 格式漂移出过事故（-de. → -dev. 补丁）。本脚本是单一事实源校验：
任一发布工作流的首步调用，不一致即失败阻断。

使用方法:
    python scripts/tools/release_check.py                 # 校验 pyproject == CHANGELOG
    python scripts/tools/release_check.py --tag v2.9.0    # 额外校验 tag 名
"""

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PYPROJECT = REPO_ROOT / "pyproject.toml"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"

# CHANGELOG 条目标题：## [2.9.0-dev.2] - 2026/10/03
CHANGELOG_HEAD_RE = re.compile(r"^##\s+\[(?P<version>[^\]\s]+)\]", re.MULTILINE)


def pyproject_version() -> str:
    for line in PYPROJECT.read_text(encoding="utf-8").splitlines():
        match = re.match(r'^version\s*=\s*"([^"]+)"', line.strip())
        if match:
            return match.group(1)
    raise RuntimeError(f"{PYPROJECT} 中未找到 version 字段")


def changelog_latest_version() -> str:
    for line in CHANGELOG.read_text(encoding="utf-8").splitlines():
        match = CHANGELOG_HEAD_RE.match(line)
        if match:
            return match.group("version")
    raise RuntimeError(f"{CHANGELOG} 中未找到任何版本条目标题（## [x.y.z]）")


def main() -> int:
    parser = argparse.ArgumentParser(description="发布版本一致性校验")
    parser.add_argument("--tag", default=None, help="tag 触发场景传入 tag 名（如 v2.9.0）")
    args = parser.parse_args()

    errors: list[str] = []

    project = pyproject_version()
    changelog = changelog_latest_version()
    print(f"pyproject version : {project}")
    print(f"CHANGELOG 最新条目 : {changelog}")

    if project != changelog:
        errors.append(f"pyproject version ({project}) 与 CHANGELOG 最新条目 ({changelog}) 不一致")

    if args.tag:
        tag_version = args.tag.lstrip("vV")
        print(f"tag               : {args.tag} (解析为 {tag_version})")
        if tag_version != project:
            errors.append(f"tag ({args.tag}) 与 pyproject version ({project}) 不一致")
        prerelease = re.search(r"(a|b|rc|alpha|beta|pre|dev)\.?\d*", tag_version) is not None
        print(f"预发布             : {'是' if prerelease else '否'}")

    if errors:
        print("\n校验失败:")
        for err in errors:
            print(f"  - {err}")
        return 1
    print("\n发布版本一致性校验通过 ✔")
    return 0


if __name__ == "__main__":
    sys.exit(main())
