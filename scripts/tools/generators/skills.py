#!/usr/bin/env python
"""
Agent Skills 自动构建器（从 docs/{lang} 生成标准 Agent Skills 技能库）

与 ai_prompts 并存（提示词面向"整段注入"工作流，本脚本产出
标准 Agent Skills 结构——skills/<name>/SKILL.md，frontmatter 含
name/description，供支持技能机制的 AI 助手按任务自动激活）。

数据来源与映射：
- 每篇文档开头的「什么时候需要读这篇」触发描述（zh-CN 为准）→ 技能
  description 的素材（AI 判断何时激活的依据；缺失时以首段兜底并输出警告
  ——触发描述全覆盖是本生成器的质量前提，请为缺失文档补齐）
- 各语言文档正文（剥离导航尾段）→ 对应语言技能正文，逐篇标注来源路径
  与仓库链接

产物：docs/{lang}/ai-support/skills/<name>/SKILL.md（每语言一套）。
属构建产物，**不提交进仓库**（.gitignore 已排除），由 CI 上传为
workflow artifact 并随 `docs-generated` 持久分支发布。

用法::

    python scripts/tools/generate-skills.py                # 全语言生成
    python scripts/tools/generate-skills.py --lang zh-CN   # 单语言
    python scripts/tools/generate-skills.py --out <dir>    # 自定义输出根
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from ..common import REPO_ROOT
from .spec import SKILL_SPECS, SkillSpec  # 规格源：与 ai_prompts 共享

DOCS_ROOT = REPO_ROOT / "docs"
SOURCE_LANG = "zh-CN"
REPO_URL = "https://github.com/ErisPulse/ErisPulse"

# 与 ai_prompts 的导航剥离同口径：正文剥离文末导航尾段
_NAV_SECTION_TITLES = ("相关文档", "下一步", "延伸阅读", "Related", "Next")

_SKILL_INTRO = {
    "zh-CN": (
        "本技能由 ErisPulse 文档自动构建（generate-skills.py）。\n"
        f"仓库：{REPO_URL}\n"
        "各节末尾标注了来源文档路径，需要最新内容请以仓库 docs/zh-CN/ 为准。\n"
    ),
}
_INTRO_FALLBACK = (
    "This skill is auto-built from the ErisPulse documentation.\n"
    f"Repository: {REPO_URL}\n"
    "Source paths are annotated per section; see docs/ in the repository for the latest content.\n"
)


_TRIGGER_MARKERS = (
    "什么时候需要读这篇",
    "When to read this",
    "いつこのドキュメントを読むべきか",
    "Когда читать этот документ",
    "什麼時候需要讀這篇",
)


def _strip_nav(text: str) -> str:
    """剥离文末导航尾段（相关文档/下一步/延伸阅读/Related/Next）"""
    lines = text.splitlines()
    out: list[str] = []
    skipping = False
    for line in lines:
        if line.startswith("#"):
            title = line.lstrip("#").strip()
            skipping = any(title.startswith(t) for t in _NAV_SECTION_TITLES)
        if not skipping:
            out.append(line)
    return "\n".join(out).strip()


def _extract_trigger(text: str) -> str:
    """提取触发描述素材：优先各语言的「什么时候需要读这篇」，回退首段非标题文本"""
    for marker in _TRIGGER_MARKERS:
        m = re.search(re.escape(marker) + r"[^：:]*[：:]\s*([^\n]+)", text)
        if m:
            return m.group(1).strip()
    m = re.search(r"> \[!TIP\][^\n]*\n>\s*([^\n]+)", text)
    if m:
        return m.group(1).strip()
    for line in text.splitlines():
        s = line.strip()
        if s and not s.startswith(("#", ">", "!", "[", "-")) and not s.startswith("---"):
            return s
    return ""


def _read_doc(docs_lang_dir: Path, rel: str) -> str:
    path = docs_lang_dir / rel
    if not path.exists():
        print(f"  [warn] 文档缺失: {docs_lang_dir.name}/{rel}", file=sys.stderr)
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def build_skill(spec: SkillSpec, docs_lang_dir: Path, out_dir: Path) -> tuple[bool, list[str]]:
    """构建单个技能；返回 (是否成功, 缺触发描述的文档列表)"""
    sections: list[str] = []
    triggers: list[str] = []
    missing: list[str] = []

    for doc in spec.docs:
        raw = _read_doc(docs_lang_dir, doc.path)
        if not raw:
            continue
        trigger = _extract_trigger(raw)
        if not trigger:
            missing.append(doc.path)
        else:
            triggers.append(trigger)
        body = _strip_nav(raw)
        source = f"{REPO_URL}/blob/main/docs/{docs_lang_dir.name}/{doc.path}"
        sections.append(
            f"## {doc.title}\n\n"
            f"> 来源: `docs/{docs_lang_dir.name}/{doc.path}`（{source}）\n\n"
            f"{body}\n"
        )

    if triggers:
        cleaned: list[str] = []
        for t in triggers:
            for tail in ("不需要则跳过，不影响其它功能的使用。", "不需要则跳过。"):
                t = t.replace(tail, "")
            t = t.strip().rstrip("。；;") + "。"
            if t not in cleaned:
                cleaned.append(t)
        description = f"适用于：{spec.audience}。覆盖场景：{''.join(cleaned)}"
    else:
        description = f"适用于：{spec.audience}。"
    if len(description) > 1024:
        description = description[:1021] + "..."

    skill_dir = out_dir / spec.name
    skill_dir.mkdir(parents=True, exist_ok=True)
    intro = _SKILL_INTRO.get(docs_lang_dir.name, _INTRO_FALLBACK)
    content = (
        f"---\nname: {spec.name}\n"
        f"description: \"{description}\"\n"
        "---\n\n"
        f"# ErisPulse {spec.title}\n\n"
        f"{intro}\n"
        + "\n".join(sections)
    )
    (skill_dir / "SKILL.md").write_text(content, encoding="utf-8", newline="\n")
    return True, missing


def available_langs() -> list[str]:
    return sorted(
        d.name for d in DOCS_ROOT.iterdir() if d.is_dir() and d.name != "_meta"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lang", default=None, help="仅生成单语言（默认全语言）")
    parser.add_argument("--out", default=None, help="自定义输出根（默认 docs/<lang>/ai-support/skills）")
    args = parser.parse_args(argv)

    langs = [args.lang] if args.lang else available_langs()
    all_missing: list[str] = []
    built = 0

    for lang in langs:
        docs_lang_dir = DOCS_ROOT / lang
        if not docs_lang_dir.exists():
            print(f"  [skip] docs/{lang} 不存在", file=sys.stderr)
            continue
        out_root = (
            Path(args.out) / lang if args.out else docs_lang_dir / "ai-support" / "skills"
        )
        for spec in SKILL_SPECS:
            ok, missing = build_skill(spec, docs_lang_dir, out_root)
            built += int(ok)
            all_missing.extend(f"{lang}/{m}" for m in missing)
        print(f"  [built] docs/{lang}/ai-support/skills/ ({len(SKILL_SPECS)} 个技能)")

    if all_missing:
        print(
            "\n[warn] 以下文档缺少「什么时候需要读这篇」触发描述，"
            "description 使用了首段兜底（请补齐后重新生成）：",
            file=sys.stderr,
        )
        for m in all_missing:
            print(f"  - {m}", file=sys.stderr)

    print(f"\n[done] {built} 个技能已生成（构建产物，不提交进仓库）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
