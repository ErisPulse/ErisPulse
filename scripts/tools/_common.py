#!/usr/bin/env python3
"""
scripts/tools 公共设施

集中维护翻译/生成脚本间曾经各自复制、已出现漂移的逻辑：
- Logger：线程安全标准输出日志器（此前 6 份逐字复制）
- IGNORE_DIRS：文档扫描排除目录（此前 3 份复制）
- count_fences：Markdown 围栏行计数（此前 5 处实现、``~~~``/缩进语义不一致）
- LEAK_PATTERN：翻译提示词泄露特征（此前 translate-docs 与 check-translation
  双份维护且已漂移——检查侧超集为准，"翻译放行、检查报错"的假阳性即源于此）

注意：本目录脚本以 `python scripts/tools/xxx.py` 直接运行，脚本目录自动进入
sys.path，因此用 `from _common import ...` 平铺导入。
"""

import re
import sys
import threading

# ==============================================================================
# 文档扫描排除目录（生成产物不参与翻译/质检）
# ==============================================================================

IGNORE_DIRS = ["ai-support/prompts", "api-reference/auto_api", "_meta"]

# ==============================================================================
# 线程安全日志器
# ==============================================================================


class Logger:
    """线程安全的标准输出日志器（单例语义：直接用类方法）"""

    _lock = threading.Lock()

    @classmethod
    def log(cls, msg: str):
        """输出一行日志"""
        with cls._lock:
            sys.stdout.write(msg + "\n")
            sys.stdout.flush()

    @classmethod
    def write(cls, text: str):
        """输出文本（不追加换行）"""
        with cls._lock:
            sys.stdout.write(text)
            sys.stdout.flush()

    @classmethod
    def progress(cls, rel_path: str, target_lang: str, status: str, detail: str = ""):
        """输出翻译进度行（状态标签统一在此映射）"""
        tag = {
            "skip": "[SKIP]",
            "trans": "[TRANS]",
            "done": "[DONE]",
            "fail": "[FAIL]",
            "retry": "[RETRY]",
            "check": "[CHECK]",
            "check_pass": "[PASS]",
            "check_fail": "[CHK!]",
            "rate_limit": "[429]",
        }.get(status, f"[{status.upper()}]")
        line = f"  {tag} {rel_path} -> {target_lang}"
        if detail:
            line += f"  {detail}"
        cls.log(line)


# ==============================================================================
# Markdown 围栏计数
# ==============================================================================

# 行首允许缩进；`` ``` `` 与 `` ~~~ `` 均为围栏（CommonMark）
_FENCE_LINE_RE = re.compile(r"^\s*(?:`{3,}|~{3,})")


def count_fences(text: str) -> int:
    """
    统计 Markdown 围栏行数（`` ``` `` / `` ~~~ ``，含任意 info string，允许行首缩进）

    此前各脚本五处实现语义不一（有的不认 ``~~~``、有的不容缩进），导致同一文件
    "翻译器判完好、检查器判围栏损坏"的假阳性——一律以本函数为准。

    :param text: Markdown 文本
    :return: 围栏行数量
    """
    return sum(1 for line in text.split("\n") if _FENCE_LINE_RE.match(line))


# ==============================================================================
# 翻译提示词泄露特征（模型偶发把翻译规则回显进译文，曾随缓存复用复活）
# ==============================================================================

# 特征均为"绝不可能出现在正常文档正文中的提示词残留"，宁严勿漏。
# 覆盖 zh-CN / zh-TW / en / ja / ru 全部已观测变体。
# 单一事实源：translate-docs.py（翻译时拦截）与 check-translation.py（质检时复核）
# 均引用本正则——此前两份独立维护且已漂移，统一取并集（更严格的检查侧版本）。
LEAK_PATTERN = re.compile(
    r"(?:return|send)\s+the\s+(?:complete\s+)?translated\s+Markdown|"
    r"once\s+again,?\s+(?:please\s+)?(?:note|adhere|follow|if\s+the\s+document)|"
    r"reminder:?\s+if\s+the\s+document\s+contains\s+(?:a\s+)?language|"
    r"format\s+requirement\s+in\s+point\s+\d+\s+above|"
    r"Path\s+Replacement\s+Rules?|"
    r"language\s+switch(?:ing)?\s+line|"
    r"replace\s+`?docs/[a-z-]+/`?\s+in\s+document\s+links|"
    r"for\s+example:\s+`?docs/[a-z-]+/.*should\s+be\s+changed\s+to|"
    r"for\s+links\s+pointing\s+to\s+non-current\s+language\s+version\s+files|"
    r"(?:this\s+)?ensures?\s+(?:that\s+)?links\s+point\s+to\s+the\s+correct\s+language\s+version|"
    r"请直接返回翻译后的完整|"
    r"請直接返回翻譯後的完整|"
    r"再次提醒：?如果(?:文档|文檔|文件)|"
    r"上方第\s*8\s*[条條]|"
    r"语言切换行本地化|"
    r"你是一个专业的技术文档翻译专家|"
    r"请将以下\s*Markdown|"
    r"请将以下Markdown文档翻译成|"
    r"这段中文提示|"
    r"各言語の切り替え行|"
    r"言語切り替え行がある場合|"
    r"上記の第8条|"
    r"翻訳後の完全な(?:Markdown)?|"
    r"верните\s+непосредственно|"
    r"еще\s+раз\s+напоминаем|"
    r"переведенный\s+полный\s+Markdown-документ|"
    r"строки\s+переключения\s+языка",
    re.IGNORECASE,
)
