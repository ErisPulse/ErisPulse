"""
ErisPulse 翻译质量检查器

检查翻译文件质量：缺失、截断、乱码、Markdown结构损坏

使用方法:
    python scripts/tools/check-translation.py
    python scripts/tools/check-translation.py --lang en ja
    python scripts/tools/check-translation.py --fix
    python scripts/tools/check-translation.py --json
"""

import os
import re
import json
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import threading

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


class Logger:
    _lock = threading.Lock()

    @classmethod
    def log(cls, msg: str):
        with cls._lock:
            sys.stdout.write(msg + "\n")
            sys.stdout.flush()


def _has_chinese_chars(text: str) -> bool:
    return any(0x4E00 <= ord(ch) <= 0x9FFF for ch in text)


def extract_headings(content: str) -> List[Dict]:
    headings = []
    in_code_block = False
    for line in content.split("\n"):
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        m = re.match(r"^(#{1,6})\s+(.+)$", line)
        if m:
            headings.append({"level": len(m.group(1)), "text": m.group(2).strip()})
    return headings


def detect_garbled(content: str, target_lang: str) -> List[str]:
    issues = []
    if "\ufffd" in content:
        issues.append(f"含{content.count(chr(0xFFFD))}个替换字符(U+FFFD)")
    if target_lang in {"zh-CN", "zh-TW"}:
        garbled = re.findall(r"[\u4e00-\u9fff]\?{1,3}[\u4e00-\u9fff]", content)
        if garbled:
            issues.append(f"{len(garbled)}处疑似乱码")
    if target_lang in {"en", "ru"}:
        lines = content.split("\n")
        code_block = False
        zh_lines = []
        for i, line in enumerate(lines, 1):
            if line.strip().startswith("```"):
                code_block = not code_block
                continue
            if code_block:
                continue
            if _has_chinese_chars(line):
                zh_lines.append(i)
        if zh_lines:
            issues.append(f"{len(zh_lines)}行含中文字符 (行: {zh_lines[:5]})")
    return issues


class TranslationChecker:
    MIN_RATIO = 0.25
    WARN_RATIO = 0.35
    IGNORE_DIRS = ["ai-support/prompts", "api-reference/auto_api", "_meta"]
    LANG_NAMES = {
        "zh-CN": "简体中文",
        "zh-TW": "繁体中文",
        "en": "English",
        "ja": "日本語",
        "ru": "Русский",
    }

    def __init__(
        self, docs_dir: str = "docs", cache_dir: str = ".github/.translate_cache"
    ):
        self.docs_dir = Path(docs_dir)
        self.source_dir = self.docs_dir / "zh-CN"
        self.cache_dir = Path(cache_dir)
        self.summary = {"checked": 0, "errors": 0, "warnings": 0, "missing": 0}

    def _scan_source(self) -> List[Path]:
        files = []
        if not self.source_dir.exists():
            return files
        for root, dirs, fns in os.walk(self.source_dir):
            dirs[:] = [
                d
                for d in dirs
                if not any(
                    Path(root) / d == self.source_dir / ig.replace("/", os.sep)
                    for ig in self.IGNORE_DIRS
                )
            ]
            for fn in fns:
                if fn.endswith(".md"):
                    files.append(Path(root) / fn)
        return sorted(files)

    def check_file(self, src: Path, tgt: Path, lang: str, rel: str) -> List[Dict]:
        issues = []
        if not tgt.exists():
            self.summary["missing"] += 1
            return [
                {"severity": "error", "type": "missing", "message": "目标文件不存在"}
            ]

        try:
            src_content = src.read_text(encoding="utf-8")
            tgt_content = tgt.read_text(encoding="utf-8")
        except Exception:
            return [{"severity": "error", "type": "read_error", "message": "读取失败"}]

        sl, tl = len(src_content), len(tgt_content)
        if sl > 200 and tl < sl * self.MIN_RATIO:
            issues.append(
                {
                    "severity": "error",
                    "type": "truncated",
                    "message": f"截断 ({tl}/{sl}, {tl / sl:.0%})",
                }
            )
        elif sl > 200 and tl < sl * self.WARN_RATIO:
            issues.append(
                {
                    "severity": "warning",
                    "type": "short",
                    "message": f"偏短 ({tl}/{sl}, {tl / sl:.0%})",
                }
            )

        src_h1 = [h for h in extract_headings(src_content) if h["level"] == 1]
        tgt_h1 = [h for h in extract_headings(tgt_content) if h["level"] == 1]
        if src_h1 and len(tgt_h1) < len(src_h1):
            issues.append(
                {
                    "severity": "warning",
                    "type": "heading",
                    "message": f"标题不匹配 (源{len(src_h1)}/目标{len(tgt_h1)})",
                }
            )

        src_fences = len(re.findall(r"^```", src_content, re.MULTILINE))
        tgt_fences = len(re.findall(r"^```", tgt_content, re.MULTILINE))
        if src_fences % 2 != 0:
            pass
        elif tgt_fences % 2 != 0:
            diff = tgt_fences - src_fences
            if abs(diff) > 2:
                issues.append(
                    {
                        "severity": "error",
                        "type": "unclosed_code",
                        "message": f"代码块未关闭 (目标{tgt_fences}个，源{src_fences}个```)",
                    }
                )

        for gi in detect_garbled(tgt_content, lang):
            issues.append({"severity": "error", "type": "garbled", "message": gi})

        return issues

    def _delete_cache(self, rel: str, lang: str):
        for candidate in [
            self.cache_dir / lang / f"{rel}.cache",
            self.cache_dir / f"{rel}.cache",
        ]:
            if candidate.exists():
                candidate.unlink()
                return True
        return False

    def run(self, langs: Optional[List[str]] = None, fix: bool = False) -> Dict:
        if langs is None:
            langs = sorted(
                d.name
                for d in self.docs_dir.iterdir()
                if d.is_dir() and d.name not in ["_meta", "zh-CN"]
            )

        Logger.log("=" * 60)
        Logger.log("翻译质量检查")
        Logger.log("=" * 60)
        Logger.log(f"检查语言: {', '.join(langs)}")
        Logger.log("")

        all_results: Dict[str, Dict[str, List[Dict]]] = {}
        fixed = 0

        for lang in langs:
            Logger.log(f"--- {self.LANG_NAMES.get(lang, lang)} ({lang}) ---")
            lang_results: Dict[str, List[Dict]] = {}
            sources = self._scan_source()

            for src in sources:
                rel = str(src.relative_to(self.source_dir)).replace("\\", "/")
                tgt = self.docs_dir / lang / rel
                issues = self.check_file(src, tgt, lang, rel)
                self.summary["checked"] += 1

                if issues:
                    lang_results[rel] = issues
                    for issue in issues:
                        if issue["severity"] == "error":
                            self.summary["errors"] += 1
                        else:
                            self.summary["warnings"] += 1
                        tag = "[ERROR]" if issue["severity"] == "error" else "[WARN]"
                        Logger.log(
                            f"  {tag} [{issue['type']}] {rel}: {issue['message']}"
                        )
                        if fix and issue["severity"] == "error":
                            if self._delete_cache(rel, lang):
                                fixed += 1
                                Logger.log(f"    -> 已删除缓存")

            # root README
            root_src = Path("README.md")
            if root_src.exists():
                tgt_rm = Path(f"README.{lang}.md")
                rm_issues = []
                if not tgt_rm.exists():
                    rm_issues.append(
                        {
                            "severity": "error",
                            "type": "missing",
                            "message": f"README.{lang}.md 不存在",
                        }
                    )
                    self.summary["missing"] += 1
                    self.summary["errors"] += 1
                else:
                    try:
                        sc = root_src.read_text(encoding="utf-8")
                        tc = tgt_rm.read_text(encoding="utf-8")
                        sl, tl = len(sc), len(tc)
                        if sl > 200 and tl < sl * self.WARN_RATIO:
                            severity = (
                                "error" if tl < sl * self.MIN_RATIO else "warning"
                            )
                            rm_issues.append(
                                {
                                    "severity": severity,
                                    "type": "truncated",
                                    "message": f"README截断 ({tl}/{sl}, {tl / sl:.0%})",
                                }
                            )
                            self.summary[
                                "errors" if severity == "error" else "warnings"
                            ] += 1
                        tgt_fences = len(re.findall(r"^```", tc, re.MULTILINE))
                        if tgt_fences % 2 != 0:
                            rm_issues.append(
                                {
                                    "severity": "error",
                                    "type": "unclosed_code",
                                    "message": f"README代码块未关闭 ({tgt_fences}个```)",
                                }
                            )
                            self.summary["errors"] += 1
                        for gi in detect_garbled(tc, lang):
                            rm_issues.append(
                                {"severity": "error", "type": "garbled", "message": gi}
                            )
                            self.summary["errors"] += 1
                    except Exception:
                        pass
                if rm_issues:
                    lang_results[f"README.{lang}.md"] = rm_issues
                    for issue in rm_issues:
                        tag = "[ERROR]" if issue["severity"] == "error" else "[WARN]"
                        Logger.log(
                            f"  {tag} [{issue['type']}] README.{lang}.md: {issue['message']}"
                        )
                    if fix:
                        for issue in rm_issues:
                            if issue["severity"] == "error":
                                cache_candidates = [
                                    self.cache_dir / f"README.{lang}.md.cache",
                                    self.cache_dir / "README.md.cache"
                                    if lang == "en"
                                    else None,
                                ]
                                for cand in cache_candidates:
                                    if cand and cand.exists():
                                        cand.unlink()
                                        fixed += 1
                                        Logger.log(f"    -> 已删除缓存")

            if not lang_results:
                Logger.log("  [OK] 无问题")
            all_results[lang] = lang_results
            Logger.log("")

        report = {
            "version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "summary": self.summary,
            "fix_mode": fix,
            "fixed_caches": fixed,
            "results": all_results,
        }

        Logger.log("=" * 60)
        Logger.log(
            f"检查: {self.summary['checked']} | "
            f"错误: {self.summary['errors']} | "
            f"警告: {self.summary['warnings']} | "
            f"缺失: {self.summary['missing']}"
        )
        if fix:
            Logger.log(f"已删除缓存: {fixed}")
        Logger.log("=" * 60)

        return report


def main():
    parser = argparse.ArgumentParser(description="ErisPulse 翻译质量检查器")
    parser.add_argument("--docs", default="docs")
    parser.add_argument("--cache", default=".github/.translate_cache")
    parser.add_argument("--lang", nargs="+")
    parser.add_argument("--fix", action="store_true", help="删除问题文件缓存")
    parser.add_argument("--json", action="store_true", help="输出JSON报告")
    parser.add_argument("--output", help="JSON报告路径")

    args = parser.parse_args()
    checker = TranslationChecker(docs_dir=args.docs, cache_dir=args.cache)
    report = checker.run(langs=args.lang, fix=args.fix)

    if args.json or args.output:
        path = args.output or "translation-check-report.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        Logger.log(f"报告已保存: {path}")

    sys.exit(1 if report["summary"]["errors"] > 0 else 0)


if __name__ == "__main__":
    main()
