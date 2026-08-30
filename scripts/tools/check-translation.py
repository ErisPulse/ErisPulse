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
    """线程安全的标准输出日志器"""

    _lock = threading.Lock()

    @classmethod
    def log(cls, msg: str):
        """
        输出一行日志

        :param msg: 日志内容
        """
        with cls._lock:
            sys.stdout.write(msg + "\n")
            sys.stdout.flush()


def _has_chinese_chars(text: str) -> bool:
    """
    判断文本中是否包含中文字符

    :param text: 待检测文本
    :return: 包含中文字符返回 True，否则 False
    """
    return any(0x4E00 <= ord(ch) <= 0x9FFF for ch in text)


def extract_headings(content: str) -> List[Dict]:
    """
    从 Markdown 内容中提取标题结构

    自动跳过代码块内的伪标题，仅识别行首 ``#`` 至 ``######`` 的标题。

    :param content: Markdown 文本
    :return: 标题信息列表，每项包含 ``level`` 与 ``text``
    """
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
    """
    检测翻译文件中的乱码与未翻译残留

    针对不同目标语言采用不同策略：
    - 所有语言：检测 Unicode 替换字符 U+FFFD
    - 中文：检测形似 "字?字" 的乱码片段
    - 英文/俄文：检测正文（排除代码块）中残留的中文字符

    :param content: 翻译后的文本
    :param target_lang: 目标语言代码
    :return: 问题描述列表
    """
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


# 译文中的翻译提示词泄露特征（模型偶发将翻译规则回显进译文）。
# 仅匹配绝不可能出现在正文中的“提示词残留”，避免误伤正常内容。
LEAK_PATTERN = re.compile(
    r"(?:return|send)\s+the\s+(?:complete\s+)?translated\s+Markdown|"
    r"once\s+again,?\s+please\s+(?:note|adhere|follow)|"
    r"reminder:?\s+if\s+the\s+document\s+contains\s+(?:a\s+)?language|"
    r"Path\s+Replacement\s+Rules?|"
    r"language\s+switch(?:ing)?\s+line|"
    r"replace\s+`?docs/[a-z-]+/`?\s+in\s+document\s+links|"
    r"for\s+example:\s+`?docs/[a-z-]+/.*should\s+be\s+changed\s+to|"
    r"for\s+links\s+pointing\s+to\s+non-current\s+language\s+version\s+files|"
    r"(?:this\s+)?ensures?\s+(?:that\s+)?links\s+point\s+to\s+the\s+correct\s+language\s+version|"
    r"请直接返回翻译后的完整Markdown内容|"
    r"請直接返回翻譯後的完整|"
    r"再次提醒：?如果(?:文档|文檔|文件)|"
    r"语言切换行本地化|"
    r"你是一个专业的技术文档翻译专家|"
    r"请将以下Markdown文档翻译成|"
    r"这段中文提示|"
    r"言語切り替え行がある場合|"
    r"翻訳後の完全なMarkdown|"
    r"верните непосредственно переведенный|"
    r"еще раз напоминаем|"
    r"переведенный полный Markdown-документ|"
    r"строки переключения языка",
    re.IGNORECASE,
)


def detect_prompt_leaks(content: str) -> List[str]:
    """
    检测译文中残留的翻译提示词（模型回显的规则）。

    提示词泄露通常以独立段落出现，行不区别语言（译文可能被翻译为各语言）。
    仅统计命中次数，用于在翻译质量检查中标记译文污染。

    :param content: 译文文本
    :return: 问题描述列表
    """
    hits = LEAK_PATTERN.findall(content)
    if hits:
        return [f"{len(hits)} 处翻译提示词残留"]
    return []


class TranslationChecker:
    """翻译质量检查器

    扫描源文档与各目标语言文档，检测缺失、截断、乱码以及 Markdown 结构问题。
    支持可选地清理问题文件的翻译缓存，以便下次重新翻译。
    """

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
        """
        初始化检查器

        :param docs_dir: 文档根目录 (默认: docs)
        :param cache_dir: 翻译缓存目录，用于 --fix 模式删除问题文件缓存
        """
        self.docs_dir = Path(docs_dir)
        self.source_dir = self.docs_dir / "zh-CN"
        self.cache_dir = Path(cache_dir)
        self.summary = {"checked": 0, "errors": 0, "warnings": 0, "missing": 0}

    def _scan_source(self) -> List[Path]:
        """
        扫描源语言目录下的所有 Markdown 文件

        :return: 源文件路径列表（已排序）
        """
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
        """
        检查单个源文件与其对应目标文件的差异

        检查项包括：文件缺失、读取异常、长度比、H1 标题数量、代码块闭合与乱码。

        :param src: 源文件路径
        :param tgt: 目标文件路径
        :param lang: 目标语言代码
        :param rel: 相对于源语言目录的相对路径（用于日志输出）
        :return: 问题列表，每项包含 ``severity``、``type``、``message``
        """
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

        for li in detect_prompt_leaks(tgt_content):
            issues.append({"severity": "error", "type": "prompt_leak", "message": li})

        return issues

    def _delete_cache(self, rel: str, lang: str):
        """
        删除指定文件与语言的翻译缓存

        同时兼容两种缓存命名：嵌套缓存 ``{cache_dir}/{lang}/{rel}.cache``
        与扁平缓存 ``{cache_dir}/{rel}.cache``。

        :param rel: 文件相对路径
        :param lang: 目标语言代码
        :return: 成功删除返回 True，未找到缓存返回 False
        """
        for candidate in [
            self.cache_dir / lang / f"{rel}.cache",
            self.cache_dir / f"{rel}.cache",
        ]:
            if candidate.exists():
                candidate.unlink()
                return True
        return False

    def run(self, langs: Optional[List[str]] = None, fix: bool = False) -> Dict:
        """
        执行翻译质量检查

        依次扫描每个目标语言下与源文档一一对应的 Markdown 文件，
        以及根目录的 README 翻译文件，生成检查报告。

        :param langs: 待检查的目标语言列表，None 表示自动发现
        :param fix: 是否在检查过程中删除错误文件的翻译缓存
        :return: 检查报告字典，包含 ``summary``、``results``、``fix_mode``、``fixed_caches``
        """
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
                        for li in detect_prompt_leaks(tc):
                            rm_issues.append(
                                {
                                    "severity": "error",
                                    "type": "prompt_leak",
                                    "message": li,
                                }
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
    """命令行入口：解析参数并运行检查器"""
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
