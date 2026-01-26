"""
List-Remote 命令实现

列出远程可用的组件
"""

import asyncio
from argparse import ArgumentParser

from rich.table import Table
from rich.box import SIMPLE

from ...package_manager import PackageManager
from ...console import console
from ..base import Command


class ListRemoteCommand(Command):
    """远程列表命令"""
    
    name = "list-remote"
    description = "列出远程可用的组件"
    
    def __init__(self):
        """初始化命令"""
        self.package_manager = PackageManager()
    
    def add_arguments(self, parser: ArgumentParser):
        """添加命令参数"""
        parser.add_argument(
            '--type', '-t',
            choices=['modules', 'adapters', 'cli', 'all'],
            default='all',
            help='列出类型 (默认: all)'
        )
        parser.add_argument(
            '--refresh', '-r',
            action='store_true',
            help='强制刷新远程包列表'
        )
    
    def execute(self, args):
        """执行命令"""
        pkg_type = args.type
        force_refresh = args.refresh
        
        if pkg_type == "all":
            self._print_remote_packages("modules", force_refresh)
            self._print_remote_packages("adapters", force_refresh)
            self._print_remote_packages("cli", force_refresh)
        else:
            self._print_remote_packages(pkg_type, force_refresh)
    
    def _print_remote_packages(self, pkg_type: str, force_refresh: bool = False):
        """
        打印远程包信息
        
        :param pkg_type: 包类型 (modules/adapters/cli)
        :param force_refresh: 是否强制刷新缓存
        """
        remote_packages = asyncio.run(
            self.package_manager.get_remote_packages(force_refresh=force_refresh)
        )
        
        if pkg_type == "modules" and remote_packages["modules"]:
            table = Table(
                title="远程模块",
                box=SIMPLE,
                header_style="module"
            )
            table.add_column("模块名", style="module")
            table.add_column("包名")
            table.add_column("最新版本")
            table.add_column("描述")
            
            for name, info in remote_packages["modules"].items():
                table.add_row(
                    name,
                    info["package"],
                    info["version"],
                    info.get("description", "")
                )
            
            console.print(table)
            
        elif pkg_type == "adapters" and remote_packages["adapters"]:
            table = Table(
                title="远程适配器",
                box=SIMPLE,
                header_style="adapter"
            )
            table.add_column("适配器名", style="adapter")
            table.add_column("包名")
            table.add_column("最新版本")
            table.add_column("描述")
            
            for name, info in remote_packages["adapters"].items():
                table.add_row(
                    name,
                    info["package"],
                    info["version"],
                    info.get("description", "")
                )
            
            console.print(table)
            
        elif pkg_type == "cli" and remote_packages.get("cli_extensions"):
            table = Table(
                title="远程CLI扩展",
                box=SIMPLE,
                header_style="cli"
            )
            table.add_column("命令名", style="cli")
            table.add_column("包名")
            table.add_column("最新版本")
            table.add_column("描述")
            
            for name, info in remote_packages["cli_extensions"].items():
                table.add_row(
                    name,
                    info["package"],
                    info["version"],
                    info.get("description", "")
                )
            
            console.print(table)
        elif not remote_packages.get(pkg_type.replace("cli", "cli_extensions"), {}):
            console.print(f"[dim]远程没有找到 {pkg_type}[/]")
