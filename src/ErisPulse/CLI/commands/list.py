"""
List 命令实现

列出已安装的组件
"""

import asyncio
from argparse import ArgumentParser

from rich.table import Table
from rich.box import SIMPLE

from ..utils import PackageManager
from ..console import console
from ..base import Command


class ListCommand(Command):
    name = "list"
    description = "列出已安装的组件"

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
            "--outdated", "-o", action="store_true", help="仅显示可升级的包"
        )

    def execute(self, args):
        pkg_type = args.type
        outdated_only = args.outdated

        if pkg_type == "all":
            self._print_installed_packages("modules", outdated_only)
            self._print_installed_packages("adapters", outdated_only)
        else:
            self._print_installed_packages(pkg_type, outdated_only)

    def _print_installed_packages(self, pkg_type: str, outdated_only: bool = False):
        installed = self.package_manager.get_installed_packages()

        if pkg_type == "modules" and installed["modules"]:
            table = Table(
                box=SIMPLE, show_lines=False, header_style="bold", pad_edge=False
            )
            table.add_column("模块名", style="module", min_width=12)
            table.add_column("包名", min_width=20)
            table.add_column("版本", width=10)
            table.add_column("状态", width=8)
            table.add_column("描述")

            count = 0
            for name, info in installed["modules"].items():
                if outdated_only and not self._is_package_outdated(
                    info["package"], info["version"]
                ):
                    continue
                status = (
                    "[green]启用[/]" if info.get("enabled", True) else "[yellow]禁用[/]"
                )
                table.add_row(
                    name,
                    info["package"],
                    info["version"],
                    status,
                    info["summary"],
                )
                count += 1

            if count > 0:
                console.print(table)
                console.print(f"[dim]  {count} 个模块[/]")
            else:
                console.print("[dim]  没有符合条件的模块[/]")

        elif pkg_type == "adapters" and installed["adapters"]:
            table = Table(
                box=SIMPLE, show_lines=False, header_style="bold", pad_edge=False
            )
            table.add_column("适配器名", style="adapter", min_width=12)
            table.add_column("包名", min_width=20)
            table.add_column("版本", width=10)
            table.add_column("描述")

            count = 0
            for name, info in installed["adapters"].items():
                if outdated_only and not self._is_package_outdated(
                    info["package"], info["version"]
                ):
                    continue
                table.add_row(
                    name,
                    info["package"],
                    info["version"],
                    info["summary"],
                )
                count += 1

            if count > 0:
                console.print(table)
                console.print(f"[dim]  {count} 个适配器[/]")
            else:
                console.print("[dim]  没有符合条件的适配器[/]")

        elif not installed.get(pkg_type, {}):
            console.print(f"[dim]  没有{pkg_type}[/]")

    def _is_package_outdated(self, package_name: str, current_version: str) -> bool:
        remote_packages = asyncio.run(self.package_manager.get_remote_packages())
        for module_info in remote_packages["modules"].values():
            if module_info["package"] == package_name:
                return module_info["version"] != current_version
        for adapter_info in remote_packages["adapters"].values():
            if adapter_info["package"] == package_name:
                return adapter_info["version"] != current_version
        return False
