"""
ErisPulse AI Prompt 生成器

从 docs/ 目录读取文档，数据驱动地生成 AI 辅助开发用的 prompt 文档。
支持三种 prompt 类型：模块开发、适配器开发、全栈开发。

使用方法:
    python scripts/tools/generate-ai-prompts.py

    # 只为特定语言生成
    python scripts/tools/generate-ai-prompts.py --lang en

    # 启用详细输出（显示缺失文件警告）
    python scripts/tools/generate-ai-prompts.py --verbose
"""

import argparse
from pathlib import Path

from ..common import (
    REPO_ROOT,
    Logger,  # scripts/tools 公共日志器
)

# ---------------------------------------------------------------------------
# 日志器
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------
from .spec import (  # 规格源：清单集中在 spec.py（与 skills 共享）
    PROMPT_SPECS,
    PromptSpec,
    Section,
)

# ---------------------------------------------------------------------------
# 生成引擎
# ---------------------------------------------------------------------------


class PromptGenerator:
    """AI Prompt 生成器

    数据驱动设计：从 ``PROMPT_SPECS`` 配置逐个读取文档内容并拼接为完整的 prompt 文档。
    """

    def __init__(
        self,
        docs_dir: str | Path,
        output_dir: str | Path,
        lang: str | None = None,
        *,
        verbose: bool = False,
    ):
        """
        初始化 Prompt 生成器

        :param docs_dir: 文档根目录
        :param output_dir: prompt 输出目录
        :param lang: 指定语言代码，未指定时直接使用 ``docs_dir``
        :param verbose: 是否输出缺失文件的警告信息
        """
        self.docs_dir = Path(docs_dir)
        self.lang = lang
        self.actual_docs_dir = self.docs_dir / lang if lang else self.docs_dir
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.verbose = verbose

    # ---- 公开接口 ----

    @staticmethod
    def get_available_languages(docs_dir: Path) -> list[str]:
        """
        获取 docs/ 下可用的语言目录

        :param docs_dir: 文档根目录
        :return: 排序后的语言代码列表
        """
        return sorted(
            item.name
            for item in docs_dir.iterdir()
            if item.is_dir() and item.name != "_meta"
        )

    def generate_all(self) -> None:
        """生成 ``PROMPT_SPECS`` 中定义的所有 prompt 文档"""
        for spec in PROMPT_SPECS:
            content = self._generate(spec)
            self._write_prompt(spec.filename, content)
            Logger.log(f"  [GEN] {spec.filename}  {len(content):,} 字符")

    # ---- 核心生成逻辑 ----

    def _generate(self, spec: PromptSpec) -> str:
        """
        根据单个 ``PromptSpec`` 配置生成 prompt 文档

        拼接顺序：System Prompt -> 前置说明（可选）-> 外层标题（可选）-> 所有章节。

        :param spec: Prompt 配置
        :return: 完整 prompt 文本
        """
        parts: list[str] = []

        # 1. System prompt + 分隔线
        parts.append(spec.system_prompt)
        parts.append("\n---\n\n")

        # 2. 前置说明（仅 full 类型）
        if spec.preamble:
            parts.append(spec.preamble)
            parts.append("---\n\n")

        # 3. 最外层标题（非 full 类型）
        if spec.header:
            parts.append(self._section_header(spec.header))
            parts.append("\n")

        # 4. 遍历所有章节
        for section in spec.sections:
            self._render_section(parts, section)

        return "\n".join(parts)

    def _render_section(self, parts: list[str], section: Section) -> None:
        """
        渲染单个章节（含标题、可选子分组标签、文档条目）

        空标题的章节仅输出条目内容（用于 full 类型中的孤立条目）。

        :param parts: 用于拼接的可变字符串列表
        :param section: 待渲染的章节
        """
        if section.title:
            parts.append(self._section_header(section.title))

        # 子分组标签（仅 full 类型中的 "模块开发" / "适配器开发"）
        if section.subgroup:
            parts.append(self._subheader(section.subgroup))

        for entry in section.entries:
            if entry.title:
                parts.append(self._subsection_header(entry.title))
            content = self._read_file(entry.path)
            parts.append(content)
            parts.append("")

    # ---- 文件读取 ----

    # 纯导航尾段标题（多语言）—— 在 prompt 拼接时剥离以减少噪音
    _NAV_SECTION_TITLES = frozenset({
        # zh-CN / zh-TW
        "相关文档", "相关链接", "下一步", "接下来",
        "相關文檔", "相關連結",
        # en
        "Related Documentation", "Related Documents", "Related Links",
        "Next Steps", "See Also", "Further Reading",
        # ja
        "関連ドキュメント", "関連文書", "関連リンク", "参考リンク", "参考ドキュメント",
        # ru
        "Связанные документы", "Связанная документация",
        "Связанные ссылки", "Далее",
    })

    def _read_file(self, rel_path: str) -> str:
        """
        读取文档文件，缺失时返回空字符串并可选输出警告

        读取后剥离纯导航尾段（"相关文档"/"下一步" 等多语言变体），
        这些段落在拼接 prompt 时是纯链接噪音，剥离可降低 token、提升生成质量。
        手写文档不受影响，仅作用于 prompt 生成。

        :param rel_path: 相对于文档根目录的路径
        :return: 文件文本内容，文件不存在时返回空字符串
        """
        full_path = self.actual_docs_dir / rel_path
        if not full_path.exists():
            if self.verbose:
                Logger.log(f"  [MISS] {rel_path}  文件不存在")
            return ""
        content = full_path.read_text(encoding="utf-8")
        return self._strip_nav_sections(content)

    @staticmethod
    def _strip_nav_sections(content: str) -> str:
        """
        剥离纯导航尾段（``## 相关文档`` / ``## 下一步`` 等多语言变体）

        从匹配的 ``##`` 标题行开始、到下一个 ``##`` 标题或文件结尾为止的全部内容，
        均从结果中移除。

        :param content: 原始 Markdown 文本
        :return: 剥离导航段后的文本
        """
        titles = PromptGenerator._NAV_SECTION_TITLES
        lines = content.split("\n")
        result: list[str] = []
        in_nav = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("## ") and not stripped.startswith("### "):
                title = stripped[3:].strip()
                in_nav = title in titles
            if not in_nav:
                result.append(line)
        # 移除末尾多余空行
        return "\n".join(result).rstrip() + "\n" if result else ""

    # ---- 格式化辅助 ----

    @staticmethod
    def _section_header(title: str) -> str:
        """
        生成章节标题（带 ``=`` 分隔线）

        :param title: 章节标题
        :return: Markdown 文本
        """
        return f"\n{'=' * len(title)}\n{title}\n{'=' * len(title)}\n"

    @staticmethod
    def _subheader(title: str) -> str:
        """
        生成二级标题（带 ``-`` 分隔线）

        :param title: 二级标题文本
        :return: Markdown 文本
        """
        return f"\n{title}\n{'-' * len(title)}\n"

    @staticmethod
    def _subsection_header(title: str) -> str:
        """
        生成三级标题（``###`` 前缀）

        :param title: 三级标题文本
        :return: Markdown 文本
        """
        return f"\n### {title}\n"

    # ---- 输出 ----

    def _write_prompt(self, filename: str, content: str) -> None:
        """
        写入 prompt 文件

        :param filename: 输出文件名
        :param content: prompt 文本内容
        """
        filepath = self.output_dir / filename
        filepath.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------


def main(argv: "list[str] | None" = None) -> None:
    """命令行入口：解析参数并为指定语言或全部语言生成 prompt"""
    parser = argparse.ArgumentParser(
        description="ErisPulse AI Prompt 生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
示例:
  # 使用默认设置（为所有语言生成）
  python scripts/tools/generate-ai-prompts.py

  # 只为特定语言生成
  python scripts/tools/generate-ai-prompts.py --lang en

  # 启用详细输出（显示缺失文件警告）
  python scripts/tools/generate-ai-prompts.py --verbose
        """,
    )
    parser.add_argument("--docs", default="docs", help="文档目录 (默认: docs)")
    parser.add_argument(
        "--lang", help="指定语言代码（如: zh-CN, en, zh-TW），不指定则为所有语言生成"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="显示缺失文件警告")

    args = parser.parse_args(argv)
    docs_dir = REPO_ROOT / args.docs

    Logger.log("=" * 60)
    Logger.log("ErisPulse AI Prompt 生成器")
    Logger.log("=" * 60)
    Logger.log(f"文档目录: {docs_dir}")
    Logger.log(f"语言: {args.lang or '全部'}")
    Logger.log(f"详细模式: {'开启' if args.verbose else '关闭'}")
    Logger.log("")

    if args.lang:
        _process_language(docs_dir, args.lang, verbose=args.verbose)
    else:
        langs = PromptGenerator.get_available_languages(docs_dir)
        Logger.log(f"发现 {len(langs)} 个语言: {', '.join(langs)}")
        Logger.log("")
        for lang in langs:
            _process_language(docs_dir, lang, verbose=args.verbose)

    Logger.log("")
    Logger.log("=" * 60)
    Logger.log("所有语言的 AI prompt 文档生成完成")
    Logger.log("=" * 60)


def _process_language(docs_dir: Path, lang: str, *, verbose: bool = False) -> None:
    """
    处理单个语言的 prompt 生成

    :param docs_dir: 文档根目录
    :param lang: 语言代码
    :param verbose: 是否输出缺失文件警告
    """
    Logger.log(f"--- {lang} ---")
    Logger.log(f"  文档目录: {docs_dir / lang}")

    output_dir = docs_dir / lang / "ai-support" / "prompts"
    Logger.log(f"  输出目录: {output_dir}")
    Logger.log("")

    generator = PromptGenerator(docs_dir, output_dir, lang, verbose=verbose)
    generator.generate_all()
    Logger.log("")


if __name__ == "__main__":
    main()
