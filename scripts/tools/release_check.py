#!/usr/bin/env python3
"""
发布三面版本一致性校验

校验 版本号（pyproject.toml）与 CHANGELOG 最新条目 一致；CI 的 tag 触发场景下
额外校验 tag 名（`v<version>` / `<version>` 两种形态均可）。

uv.lock 入库后成为事实源之一（CI 依赖解析与安全审计都基于它），因此同时校验
uv.lock 中根包（项目自身）的 version 与 pyproject 一致——lock 文件按 PEP 440
规范化存储版本（如 ``2.9.0-dev.1`` → ``2.9.0.dev1``），比对前先归一化。

背景：此前 tag 创建（auto-tag-release）、PyPI 发布（pypi-publish）各自用 sed
从 pyproject 抽版本、且 tag 创建隐式依赖 CHANGELOG 段落存在，三处解析曾因
CHANGELOG 格式漂移出过事故（-de. → -dev. 补丁）。本脚本是单一事实源校验：
任一发布工作流的首步调用，不一致即失败阻断。

使用方法:
    python scripts/tools/release_check.py                 # 校验 pyproject == CHANGELOG == uv.lock
    python scripts/tools/release_check.py --tag v2.9.0    # 额外校验 tag 名
"""

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PYPROJECT = REPO_ROOT / "pyproject.toml"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"
UV_LOCK = REPO_ROOT / "uv.lock"

# CHANGELOG 条目标题：## [2.9.0-dev.1] - 2026/09/27
CHANGELOG_HEAD_RE = re.compile(r"^##\s+\[(?P<version>[^\]\s]+)\]", re.MULTILINE)

# uv.lock 根包条目：[[package]] name = "ErisPulse" 附近紧跟的 version
UV_LOCK_ROOT_PACKAGE = "ErisPulse"
UV_LOCK_PACKAGE_RE = re.compile(
    r'^\[\[package\]\]\s*\nname\s*=\s*"(?P<name>[^"]+)"\s*\nversion\s*=\s*"(?P<version>[^"]+)"',
    re.MULTILINE,
)


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


def normalize_version(version: str) -> str:
    """
    按 PEP 440 规范化版本号（比对 uv.lock 用）

    uv.lock 以规范化形态存储版本（``2.9.0-dev.1`` → ``2.9.0.dev1``）。
    标准库 ``packaging`` 在运行环境可用则直接用；不可用时退化为小写化
    的保守比对（dev 发布环境自带 packaging，此兜底仅服务极端场景）。

    :param version: 原始版本号
    :return: 规范化后的版本号字符串
    """
    try:
        from packaging.version import Version

        return str(Version(version))
    except Exception:
        return version.strip().lower()


def uv_lock_root_version() -> str | None:
    """
    从 uv.lock 提取根包（本项目自身）的版本

    :return: 版本号字符串；lock 不存在或未找到根包条目时返回 None
    """
    if not UV_LOCK.exists():
        return None
    content = UV_LOCK.read_text(encoding="utf-8")
    for match in UV_LOCK_PACKAGE_RE.finditer(content):
        # uv.lock 中包名按 PEP 503 规范化存储（ErisPulse → erispulse）
        if match.group("name").lower() == UV_LOCK_ROOT_PACKAGE.lower():
            return match.group("version")
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="发布三面版本一致性校验")
    parser.add_argument("--tag", default=None, help="tag 触发场景传入 tag 名（如 v2.9.0）")
    args = parser.parse_args()

    errors: list[str] = []

    project = pyproject_version()
    changelog = changelog_latest_version()
    print(f"pyproject version : {project}")
    print(f"CHANGELOG 最新条目 : {changelog}")

    if project != changelog:
        errors.append(f"pyproject version ({project}) 与 CHANGELOG 最新条目 ({changelog}) 不一致")

    lock_version = uv_lock_root_version()
    if lock_version is None:
        if UV_LOCK.exists():
            errors.append(f"uv.lock 中未找到根包 {UV_LOCK_ROOT_PACKAGE} 的版本条目")
        else:
            print("uv.lock           : 不存在（跳过）")
    else:
        print(f"uv.lock 根包版本   : {lock_version}")
        if normalize_version(lock_version) != normalize_version(project):
            errors.append(
                f"uv.lock 根包版本 ({lock_version}) 与 pyproject version ({project}) 不一致"
                "——请运行 uv lock / uv sync 后一并提交"
            )

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
