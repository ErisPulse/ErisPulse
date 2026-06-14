"""
List-Remote 命令实现

列出远程可用的组件
"""

import asyncio
from argparse import ArgumentParser

from rich.box import SIMPLE
from rich.table import Table

from ..base import Command
from ..console import console
from ..i18n import i18n
from ..utils import PackageManager
from ..utils.display import section_header


class ListRemoteCommand(Command):
    """
    list-remote 命令

    列出远程可用的组件
    """

    name = "list-remote"
    description = i18n.t("cli.list_remote.description")
    aliases = ["lr"]

    def __init__(self):
        """
        初始化 ListRemoteCommand，创建包管理器实例
        """
        self.package_manager = PackageManager()

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            "--type",
            "-t",
            choices=["modules", "adapters", "all"],
            default="all",
            help=i18n.t("cli.list_remote.type_help"),
        )
        parser.add_argument(
            "--refresh",
            "-r",
            action="store_true",
            help=i18n.t("cli.list_remote.refresh_help"),
        )

    def execute(self, args):
        with console.status(
            f"[bold green]{i18n.t('cli.list_remote.fetching')}[/]", spinner="dots"
        ):
            remote_packages = asyncio.run(
                self.package_manager.get_remote_packages(force_refresh=args.refresh)
            )

        pkg_type = args.type
        modules = remote_packages.get("modules", {})
        adapters = remote_packages.get("adapters", {})

        if pkg_type in ("all", "modules"):
            self._print_group(
                i18n.t("cli.list_remote.group_modules"),
                modules,
                "module",
                i18n.t("cli.list_remote.header_module"),
            )
        if pkg_type in ("all", "adapters"):
            self._print_group(
                i18n.t("cli.list_remote.group_adapters"),
                adapters,
                "adapter",
                i18n.t("cli.list_remote.header_adapter"),
            )

        total = len(modules) + len(adapters)
        console.print(f"[dim]  {i18n.t('cli.list_remote.total_count', total=total)}[/]")

    def _print_group(self, title: str, items: dict, style: str, name_col: str):
        """
        以表格形式打印一组远程组件

        :param title: [str] 分组标题
        :param items: [dict] 组件信息字典
        :param style: [str] 名称列的显示样式
        :param name_col: [str] 名称列的列标题
        """
        if not items:
            return

        section_header(title)

        table = Table(box=SIMPLE, show_lines=False, header_style="bold", pad_edge=False)
        table.add_column(name_col, style=style, min_width=12)
        table.add_column(i18n.t("cli.list_remote.header_package"), min_width=20)
        table.add_column(i18n.t("cli.list_remote.header_version"), width=10)
        table.add_column(i18n.t("cli.list_remote.header_desc"))

        for name, info in items.items():
            verified = info.get("verified", True)
            display_name = (
                name if verified else i18n.t("cli.list_remote.unverified", name=name)
            )
            table.add_row(
                display_name,
                info.get("package", ""),
                info.get("version", ""),
                info.get("description", ""),
            )

        console.print(table)

        unverified_count = sum(
            1 for info in items.values() if not info.get("verified", True)
        )
        summary = f"[dim]  {i18n.t('cli.list_remote.group_summary', count=len(items), title=title)}[/]"
        if unverified_count:
            summary += f"  [dim]{i18n.t('cli.list_remote.unverified_count', count=unverified_count)}[/]"
        console.print(summary)
