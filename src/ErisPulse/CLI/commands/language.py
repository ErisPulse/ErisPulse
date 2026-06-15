"""
Language 命令实现

查看与切换 CLI 显示语言
"""

import sys
from argparse import ArgumentParser

from rich.text import Text

from ..base import Command
from ..console import console
from ..i18n import LANGUAGE_NAMES, SUPPORTED_LANGUAGES, i18n
from ..utils.display import section_header


class LanguageCommand(Command):
    """
    language 命令

    查看/切换 CLI 显示语言
    """

    name = "i18n"
    description = i18n.t("cli.language.description")
    aliases = ["language", "lang"]

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            "lang",
            nargs="?",
            default=None,
            help=i18n.t("cli.language.lang_help"),
        )
        parser.add_argument(
            "--list",
            "-l",
            action="store_true",
            help=i18n.t("cli.language.list_help"),
        )

    def execute(self, args):
        current = i18n.get_language()

        if args.list:
            self._show_languages(current)
            return

        if args.lang:
            target = self._normalize_lang(args.lang)
            if target is None:
                console.print(
                    f"[error]{i18n.t('cli.language.unsupported', lang=args.lang)}[/]"
                )
                self._show_languages(current)
                sys.exit(1)
            i18n.set_language(target)
            console.print(
                f"[success]{i18n.t('cli.language.switched', lang=LANGUAGE_NAMES.get(target, target))}[/]"
            )
            return

        self._interactive_select(current)

    def _interactive_select(self, current: str) -> None:
        """
        交互式选择语言

        :param current: [str] 当前语言代码
        """
        section_header(i18n.t("cli.language.select_title"))

        options = SUPPORTED_LANGUAGES
        for idx, lang in enumerate(options, 1):
            name = LANGUAGE_NAMES.get(lang, lang)
            if lang == current:
                console.print(
                    Text(f"    {idx}.  {name}  [{current}]  ✓", style="success")
                )
            else:
                console.print(Text(f"    {idx}.  {name}  [{lang}]", style="info"))

        console.print()

        while True:
            try:
                choice = input(f"  {i18n.t('cli.language.enter_choice')} ").strip()
            except (EOFError, KeyboardInterrupt):
                console.print()
                return

            if choice.isdigit():
                idx = int(choice)
                if 1 <= idx <= len(options):
                    target = options[idx - 1]
                    i18n.set_language(target)
                    console.print(
                        f"\n[success]{i18n.t('cli.language.switched', lang=LANGUAGE_NAMES.get(target, target))}[/]"
                    )
                    return
            console.print(f"[warning]{i18n.t('cli.language.invalid_choice')}[/]")

    @staticmethod
    def _show_languages(current: str) -> None:
        """
        列出所有支持的语言

        :param current: [str] 当前语言代码
        """
        for lang in SUPPORTED_LANGUAGES:
            name = LANGUAGE_NAMES.get(lang, lang)
            mark = " ✓" if lang == current else ""
            console.print(f"  [{lang}] {name}{mark}")

    @staticmethod
    def _normalize_lang(lang: str) -> str | None:
        """
        将用户输入的语言标识归一化为支持的语言代码

        :param lang: [str] 用户输入（如 zh、zh-CN、en、ja、ru 等）
        :return: [str | None] 归一化后的语言代码，不支持时返回 None
        """
        # 复用 i18n 模块的 locale 解析逻辑
        from ..i18n import _resolve_nearest

        resolved = _resolve_nearest(lang)
        if resolved in SUPPORTED_LANGUAGES:
            return resolved
        return None
