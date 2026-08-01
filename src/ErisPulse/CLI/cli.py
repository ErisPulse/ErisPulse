"""
主 CLI 类

ErisPulse 命令行接口主入口
"""

import importlib
import pkgutil
import sys
import traceback
from argparse import ArgumentParser, RawDescriptionHelpFormatter

from rich.panel import Panel
from rich.text import Text

from .base import Command
from .console import console, print_banner
from .i18n import i18n
from .registry import CommandRegistry


class CLI:
    """
    ErisPulse 命令行接口主类

    提供完整的命令行交互功能
    """

    def __init__(self):
        """初始化 CLI"""
        self.registry = CommandRegistry()
        self.parser = self._create_parser()
        self._register_builtin_commands()

    def _create_parser(self) -> ArgumentParser:
        """
        创建命令行参数解析器

        :return: 配置好的 ArgumentParser 实例
        """
        parser = ArgumentParser(
            prog="epsdk",
            formatter_class=RawDescriptionHelpFormatter,
            description=i18n.t("cli.parser.description"),
        )
        parser._positionals.title = i18n.t("cli.parser.positionals_title")
        parser._optionals.title = i18n.t("cli.parser.optionals_title")

        # 全局选项
        parser.add_argument(
            "--version",
            "-V",
            action="store_true",
            help=i18n.t("cli.parser.version_help"),
        )
        parser.add_argument(
            "--verbose",
            "-v",
            action="count",
            default=0,
            help=i18n.t("cli.parser.verbose_help"),
        )
        parser.add_argument(
            "--no-color",
            action="store_true",
            default=False,
            help=i18n.t("cli.parser.no_color_help"),
        )
        parser.add_argument(
            "--yes",
            "-y",
            action="store_true",
            default=False,
            help=i18n.t("cli.parser.yes_help"),
        )

        # 子命令
        subparsers = parser.add_subparsers(
            dest="command",
            metavar=i18n.t("cli.parser.command_meta"),
            help=i18n.t("cli.parser.command_help"),
        )

        self.subparsers = subparsers
        return parser

    def _auto_discover_commands(self):
        """
        自动发现并注册 commands 目录中的所有命令

        动态扫描 commands 目录，查找所有继承自 Command 基类的命令类
        并自动注册到命令注册表中。
        """
        # 获取 commands 包的路径
        commands_package = "ErisPulse.CLI.commands"

        try:
            # 遍历 commands 包中的所有模块
            for _importer, module_name, _ispkg in pkgutil.iter_modules(
                importlib.import_module(commands_package).__path__,
                prefix=f"{commands_package}.",
            ):
                # 跳过 __init__ 和 __pycache__ 目录
                if module_name.endswith(".__init__") or "__pycache__" in module_name:
                    continue

                try:
                    # 动态导入模块
                    module = importlib.import_module(module_name)

                    # 查找模块中所有继承自 Command 的类
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)

                        # 检查是否是 Command 的子类（排除 Command 基类本身）
                        if (
                            isinstance(attr, type)
                            and issubclass(attr, Command)
                            and attr is not Command
                        ):
                            try:
                                # 实例化并注册命令
                                command_instance = attr()
                                self.registry.register(command_instance)
                            except Exception as e:
                                console.print(
                                    f"[warning]{i18n.t('cli.discover.instantiate_failed', name=attr_name, error=e)}[/]"
                                )

                except Exception as e:
                    console.print(
                        f"[warning]{i18n.t('cli.discover.load_failed', name=module_name, error=e)}[/]"
                    )

        except ImportError as e:
            console.print(
                f"[warning]{i18n.t('cli.discover.import_failed', error=e)}[/]"
            )

    def _register_builtin_commands(self):
        """注册所有内置命令（通过自动发现）"""
        self._auto_discover_commands()

        # 添加所有命令的参数（同时注册命令别名）
        for command in self.registry.get_all():
            parser = self.subparsers.add_parser(
                command.name,
                aliases=getattr(command, "aliases", None) or [],
                help=command.description,
            )
            command.add_arguments(parser)

    def _print_version(self):
        """打印版本信息"""
        from ErisPulse import __version__

        console.print(
            Panel(
                f"[title]{i18n.t('cli.run.version_text', version=__version__)}[/]",
                subtitle=f"Python {sys.version.split()[0]}",
                style="title",
            )
        )

    def _print_quickstart(self) -> None:
        """
        打印 Quick Start 面板

        在 ``epsdk`` 不带任何子命令时输出，帮助新用户在 30 秒内看到
        三步走路径（安装 / 创建项目 / 运行），降低首次使用门槛。
        """
        steps = [
            (
                i18n.t("cli.run.quickstart.step1_label"),
                i18n.t("cli.run.quickstart.step1_cmd"),
            ),
            (
                i18n.t("cli.run.quickstart.step2_label"),
                i18n.t("cli.run.quickstart.step2_cmd"),
            ),
            (
                i18n.t("cli.run.quickstart.step3_label"),
                i18n.t("cli.run.quickstart.step3_cmd"),
            ),
        ]
        lines: list[str] = []
        for idx, (label, cmd) in enumerate(steps, start=1):
            lines.append(f"[bold]{idx}. {label}[/]  [cmd]{cmd}[/]")
        lines.append("")
        lines.append(f"[dim]{i18n.t('cli.run.quickstart.docs_hint')}[/]")
        lines.append(f"[dim]{i18n.t('cli.run.quickstart.run_help_hint')}[/]")

        console.print(
            Panel(
                "\n".join(lines),
                title=f"[title]{i18n.t('cli.run.quickstart.title')}[/]",
                subtitle=i18n.t("cli.run.quickstart.subtitle"),
                border_style="info",
            )
        )

    def _check_command_typo(self) -> None:
        """
        在 argparse 解析之前检查命令拼写

        argparse 的子命令 choices 验证遇到无效命令时会直接打印错误并退出，
        无法附加自定义提示。因此在此提前拦截，给出"你是不是想用 xxx"的拼写建议。
        """
        # 所有有效命令（规范名 + 别名），用于检查输入是否有效
        all_valid = set(self.registry.list_all()) | set(
            self.registry.list_aliases().keys()
        )
        # 仅规范命令名作为建议候选（不含短别名/缩写，避免扰民）
        canonical_names = self.registry.list_all()

        # 从 sys.argv 中找到第一个非选项参数（即命令名）
        cmd = None
        for arg in sys.argv[1:]:
            if not arg.startswith("-"):
                cmd = arg
                break

        if not cmd or cmd in all_valid:
            return

        # 命令无效，给出拼写建议（前缀加成确保 ins → install 而非 list）
        from .hints import best_match_with_prefix

        print_banner()
        suggestion = best_match_with_prefix(
            cmd, canonical_names, cutoff=0.5
        )

        if suggestion:
            from .console import print_suggestion

            print_suggestion(
                title=i18n.t("cli.run.unknown_command", command=cmd),
                suggestions=[f"epsdk {suggestion} --help"],
            )
        else:
            console.print(
                f"[error]{i18n.t('cli.run.unknown_command', command=cmd)}[/]"
            )
            self.parser.print_help()
        sys.exit(1)

    def _maybe_show_language_hint(self) -> None:
        """
        在前几次启动时提醒用户确认语言

        由于检测到的语言可能不正确，提示会同时展示所有支持语言，
        确保用户总能看懂。显示 {LANG_HINT_MAX_SHOWS} 次后自动静默消失。
        """
        from .i18n import LANG_HINT_MAX_SHOWS, LANGUAGE_NAMES, SUPPORTED_LANGUAGES

        shown_count = i18n.get_lang_hint_shown_count()
        if shown_count >= LANG_HINT_MAX_SHOWS:
            return

        current = i18n.get_language()
        current_name = LANGUAGE_NAMES.get(current, current)
        remaining = LANG_HINT_MAX_SHOWS - shown_count - 1

        lines = []
        for lang in SUPPORTED_LANGUAGES:
            msg = i18n.t_in(
                lang,
                "cli.lang_hint.message",
                lang=current_name,
                remaining=remaining,
            )
            # \[ 转义使 Rich 显示字面方括号，消息中的 [cyan] 等标签正常解析
            if lang == current:
                lines.append(f"\\[{lang}] [bold]{msg}[/]")
            else:
                lines.append(f"\\[{lang}] [dim]{msg}[/]")

        console.print()
        console.print(
            Panel(
                "\n".join(lines),
                border_style="info",
                title=i18n.t("cli.lang_hint.title"),
            )
        )
        i18n.increment_lang_hint()

    def run(self):
        """
        运行 CLI

        :raises KeyboardInterrupt: 用户中断时抛出
        :raises Exception: 命令执行失败时抛出
        """
        # 在 argparse 之前检查命令拼写（argparse 的 choices 验证会直接报错退出）
        self._check_command_typo()

        args, unknown = self.parser.parse_known_args()
        args._unknown_args = unknown

        # --no-color：禁用 Rich 控制台着色（CI / 日志采集场景）
        if getattr(args, "no_color", False):
            console.no_color = True

        print_banner()

        # 前几次启动时提醒用户确认语言（检测错误时用户仍可看懂多语言提示）
        self._maybe_show_language_hint()

        # 处理版本选项
        if args.version:
            self._print_version()
            return

        # 没有指定命令时显示 Quick Start + 帮助
        if not args.command:
            if unknown:
                console.print(
                    f"[warning]{i18n.t('cli.run.unknown_args', args=' '.join(unknown))}[/]"
                )
            self._print_quickstart()
            self.parser.print_help()
            return

        # 将别名解析为规范命令名
        canonical = self.registry.resolve(args.command) or args.command

        if unknown and canonical not in ("install", "create"):
            console.print(
                f"[warning]{i18n.t('cli.run.unknown_args', args=' '.join(unknown))}[/]"
            )

        try:
            # 执行命令
            command = self.registry.get(canonical)
            if command:
                console.print()
                console.print(
                    Text("  ── ", style="dim"),
                    Text(command.description, style="bold"),
                    sep="",
                )
                console.print()
                command.execute(args)
            else:
                # 拼写建议：检查是否输入了与已知命令相似的名称
                from .hints import best_match_with_prefix

                suggestion = best_match_with_prefix(
                    args.command, self.registry.list_all(), cutoff=0.5
                )
                if suggestion:
                    console.print(
                        f"[hint]{i18n.t('cli.run.did_you_mean', name=suggestion)}[/]"
                    )
                console.print(
                    f"[error]{i18n.t('cli.run.unknown_command', command=args.command)}[/]"
                )
                self.parser.print_help()
                sys.exit(1)

        except KeyboardInterrupt:
            console.print(f"\n[warning]{i18n.t('cli.run.user_interrupted')}[/]")
            sys.exit(1)
        except Exception as e:
            console.print(f"[error]{i18n.t('cli.run.exec_error', error=e)}[/]")
            # 场景化友好提示：根据异常类型给出下一步建议
            from .hints import suggest_for_exception

            hint_key = suggest_for_exception(e)
            if hint_key:
                console.print(f"[hint]{i18n.t(hint_key)}[/]")
            if args.verbose >= 1:
                console.print(traceback.format_exc())
            sys.exit(1)
