"""
Uninstall 命令实现

支持卸载模块、适配器
"""

import sys
from argparse import ArgumentParser

from ..utils import PackageManager
from ..utils.display import interactive_select_table
from ..console import console
from ..base import Command


class UninstallCommand(Command):
    name = "uninstall"
    description = "卸载模块/适配器包"
    
    def __init__(self):
        self.package_manager = PackageManager()
    
    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            'package',
            nargs='*',
            help='要卸载的包名（可指定多个）'
        )
    
    def execute(self, args):
        if args.package:
            success = self.package_manager.uninstall_package(args.package)
            if not success:
                sys.exit(1)
        else:
            self._interactive_uninstall()
    
    def _interactive_uninstall(self):
        installed = self.package_manager.get_installed_packages()
        
        all_packages = []
        for name, info in installed.get("adapters", {}).items():
            all_packages.append({
                "type": "适配器",
                "name": name,
                "package": info["package"],
                "version": info["version"],
            })
        for name, info in installed.get("modules", {}).items():
            all_packages.append({
                "type": "模块",
                "name": name,
                "package": info["package"],
                "version": info["version"],
            })
        
        if not all_packages:
            console.print("[dim]  没有已安装的包[/]")
            return

        selected = interactive_select_table(
            "选择要卸载的包",
            all_packages,
            columns=[
                {"header": "序号", "style": "#A0B0C0", "width": 4},
                {"header": "类型", "style": "bold", "width": 6},
                {"header": "名称"},
                {"header": "包名"},
                {"header": "版本", "width": 10},
            ],
            row_builder=lambda table, idx, item, checked: table.add_row(
                ("● " if checked else "  ") + str(idx + 1),
                item["type"],
                item["name"],
                item["package"],
                item["version"],
            ),
        )

        if not selected:
            return

        selected_packages = [pkg["package"] for pkg in selected]
        self.package_manager.uninstall_package(selected_packages)
