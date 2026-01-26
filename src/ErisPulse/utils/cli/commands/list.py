"""
List 命令实现

列出已安装的组件
"""

import asyncio
from argparse import ArgumentParser

from rich.table import Table
from rich.box import SIMPLE

from ...package_manager import PackageManager
from ...console import console
from ..base import Command


class ListCommand(Command):
    """列表命令"""
    
    name = "list"
    description = "列出已安装的组件"
    
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
            '--outdated', '-o',
            action='store_true',
            help='仅显示可升级的包'
        )
    
    def execute(self, args):
        """执行命令"""
        pkg_type = args.type
        outdated_only = args.outdated
        
        if pkg_type == "all":
            self._print_installed_packages("modules", outdated_only)
            self._print_installed_packages("adapters", outdated_only)
            self._print_installed_packages("cli", outdated_only)
        else:
            self._print_installed_packages(pkg_type, outdated_only)
    
    def _print_installed_packages(self, pkg_type: str, outdated_only: bool = False):
        """
        打印已安装包信息
        
        :param pkg_type: 包类型 (modules/adapters/cli)
        :param outdated_only: 是否只显示可升级的包
        """
        installed = self.package_manager.get_installed_packages()
        
        if pkg_type == "modules" and installed["modules"]:
            table = Table(
                title="已安装模块",
                box=SIMPLE,
                header_style="module"
            )
            table.add_column("模块名", style="module")
            table.add_column("包名")
            table.add_column("版本")
            table.add_column("状态")
            table.add_column("描述")
            
            for name, info in installed["modules"].items():
                if outdated_only and not self._is_package_outdated(info["package"], info["version"]):
                    continue
                    
                status = "[green]已启用[/]" if info.get("enabled", True) else "[yellow]已禁用[/]"
                table.add_row(
                    name,
                    info["package"],
                    info["version"],
                    status,
                    info["summary"]
                )
            
            console.print(table)
            
        elif pkg_type == "adapters" and installed["adapters"]:
            table = Table(
                title="已安装适配器",
                box=SIMPLE,
                header_style="adapter"
            )
            table.add_column("适配器名", style="adapter")
            table.add_column("包名")
            table.add_column("版本")
            table.add_column("描述")
            
            for name, info in installed["adapters"].items():
                if outdated_only and not self._is_package_outdated(info["package"], info["version"]):
                    continue
                    
                table.add_row(
                    name,
                    info["package"],
                    info["version"],
                    info["summary"]
                )
            
            console.print(table)
            
        elif pkg_type == "cli" and installed["cli_extensions"]:
            table = Table(
                title="已安装CLI扩展",
                box=SIMPLE,
                header_style="cli"
            )
            table.add_column("命令名", style="cli")
            table.add_column("包名")
            table.add_column("版本")
            table.add_column("描述")
            
            for name, info in installed["cli_extensions"].items():
                if outdated_only and not self._is_package_outdated(info["package"], info["version"]):
                    continue
                    
                table.add_row(
                    name,
                    info["package"],
                    info["version"],
                    info["summary"]
                )
            
            console.print(table)
        elif not installed.get(pkg_type.replace("cli", "cli_extensions"), {}):
            console.print(f"[dim]没有找到已安装的 {pkg_type}[/]")
    
    def _is_package_outdated(self, package_name: str, current_version: str) -> bool:
        """
        检查包是否过时
        
        :param package_name: 包名
        :param current_version: 当前版本
        :return: 是否有新版本可用
        """
        remote_packages = asyncio.run(self.package_manager.get_remote_packages())
        
        # 检查模块
        for module_info in remote_packages["modules"].values():
            if module_info["package"] == package_name:
                return module_info["version"] != current_version
                
        # 检查适配器
        for adapter_info in remote_packages["adapters"].values():
            if adapter_info["package"] == package_name:
                return adapter_info["version"] != current_version
                
        # 检查CLI扩展
        for cli_info in remote_packages.get("cli_extensions", {}).values():
            if cli_info["package"] == package_name:
                return cli_info["version"] != current_version
                
        return False
