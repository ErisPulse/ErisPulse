"""
List-Remote 命令实现

列出远程可用的组件
"""

import asyncio
from argparse import ArgumentParser

from rich.table import Table
from rich.box import SIMPLE

from ..utils import PackageManager
from ..utils.display import section_header
from ..console import console
from ..base import Command


class ListRemoteCommand(Command):
    name = "list-remote"
    description = "列出远程可用的组件"

    def __init__(self):
        self.package_manager = PackageManager()

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            "--type",
            "-t",
            choices=["modules", "adapters", "all"],
            default="all",
            help="列出类型 (默认: all)",
        )
        parser.add_argument(
            "--refresh", "-r", action="store_true", help="强制刷新远程包列表"
        )

    def execute(self, args):
        with console.status("[bold green]正在获取远程包列表...", spinner="dots"):
            remote_packages = asyncio.run(
                self.package_manager.get_remote_packages(force_refresh=args.refresh)
            )

        pkg_type = args.type
        modules = remote_packages.get("modules", {})
        adapters = remote_packages.get("adapters", {})

        if pkg_type in ("all", "modules"):
            self._print_group("模块", modules, "module", "模块名")
        if pkg_type in ("all", "adapters"):
            self._print_group("适配器", adapters, "adapter", "适配器名")

        total = len(modules) + len(adapters)
        console.print(f"[dim]  共 {total} 个远程组件[/]")

    def _print_group(self, title: str, items: dict, style: str, name_col: str):
        if not items:
            return

        section_header(title)

        table = Table(box=SIMPLE, show_lines=False, header_style="bold", pad_edge=False)
        table.add_column(name_col, style=style, min_width=12)
        table.add_column("包名", min_width=20)
        table.add_column("最新版本", width=10)
        table.add_column("描述")

        for name, info in items.items():
            verified = info.get("verified", True)
            display_name = name if verified else f"{name}（未验证）"
            table.add_row(
                display_name,
                info.get("package", ""),
                info.get("version", ""),
                info.get("description", ""),
            )

        console.print(table)

        unverified_count = sum(1 for info in items.values() if not info.get("verified", True))
        summary = f"[dim]  {len(items)} 个{title}[/]"
        if unverified_count:
            summary += f"  [dim]({unverified_count} 个未验证)[/]"
        console.print(summary)
