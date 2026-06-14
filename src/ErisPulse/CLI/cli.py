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
        parser._positionals.title = "命令"
        parser._optionals.title = "选项"

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
            for importer, module_name, ispkg in pkgutil.iter_modules(
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

    def run(self):
        """
        运行 CLI

        :raises KeyboardInterrupt: 用户中断时抛出
        :raises Exception: 命令执行失败时抛出
        """
        args, unknown = self.parser.parse_known_args()
        args._unknown_args = unknown

        print_banner()

        # 处理版本选项
        if args.version:
            self._print_version()
            return

        # 没有指定命令时显示帮助
        if not args.command:
            if unknown:
                console.print(
                    f"[warning]{i18n.t('cli.run.unknown_args', args=' '.join(unknown))}[/]"
                )
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
            if args.verbose >= 1:
                console.print(traceback.format_exc())
            sys.exit(1)
