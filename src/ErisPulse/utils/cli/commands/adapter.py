"""
Adapter 命令实现

支持启用和禁用适配器
"""

import sys
from argparse import ArgumentParser

from ...package_manager import PackageManager
from ...console import console
from ..base import Command


class AdapterCommand(Command):
    """适配器管理命令"""
    
    name = "adapter"
    description = "适配器管理（启用/禁用）"
    
    def __init__(self):
        """初始化命令"""
        self.package_manager = PackageManager()
    
    def add_arguments(self, parser: ArgumentParser):
        """添加命令参数"""
        subparsers = parser.add_subparsers(
            dest='adapter_command',
            metavar="<子命令>",
            help="适配器操作"
        )
        
        # 启用适配器子命令
        enable_parser = subparsers.add_parser('enable', help='启用适配器')
        enable_parser.add_argument('adapter', help='要启用的适配器名')
        
        # 禁用适配器子命令
        disable_parser = subparsers.add_parser('disable', help='禁用适配器')
        disable_parser.add_argument('adapter', help='要禁用的适配器名')
        
        # 列出适配器状态子命令
        list_parser = subparsers.add_parser('list', help='列出适配器状态')
        list_parser.add_argument(
            '--all', '-a',
            action='store_true',
            help='显示所有适配器（包括未安装的）'
        )
    
    def execute(self, args):
        """执行命令"""
        from ErisPulse import config
        from ErisPulse.Core import adapter as adapter_manager
        
        installed = self.package_manager.get_installed_packages()
        
        if args.adapter_command == "enable":
            # 启用适配器
            if args.adapter not in installed["adapters"]:
                console.print(f"[error]适配器 [bold]{args.adapter}[/] 不存在或未安装[/]")
                sys.exit(1)
            
            # 设置配置
            config.setConfig(f"ErisPulse.adapters.status.{args.adapter}", True)
            console.print(f"[success]适配器 [bold]{args.adapter}[/] 已启用[/]")
            console.print("[info]注意: 适配器状态更改后需要重启项目才能生效[/]")
        
        elif args.adapter_command == "disable":
            # 禁用适配器
            if args.adapter not in installed["adapters"]:
                console.print(f"[error]适配器 [bold]{args.adapter}[/] 不存在或未安装[/]")
                sys.exit(1)
            
            # 设置配置
            config.setConfig(f"ErisPulse.adapters.status.{args.adapter}", False)
            console.print(f"[warning]适配器 [bold]{args.adapter}[/] 已禁用[/]")
            console.print("[info]注意: 适配器状态更改后需要重启项目才能生效[/]")
        
        elif args.adapter_command == "list":
            # 列出适配器状态
            self._list_adapters(installed, args.all)
        
        else:
            # 没有指定子命令，显示帮助
            console.print("[info]请指定子命令: enable, disable 或 list[/]")
    
    def _list_adapters(self, installed, show_all: bool):
        """
        列出适配器状态
        
        :param installed: 已安装的包信息
        :param show_all: 是否显示所有适配器
        """
        from rich.table import Table
        from rich.box import SIMPLE
        import asyncio
        
        table = Table(
            title="适配器状态",
            box=SIMPLE,
            header_style="adapter"
        )
        table.add_column("适配器名", style="adapter")
        table.add_column("状态", style="cyan")
        table.add_column("包名")
        table.add_column("描述")
        
        # 获取已安装的适配器
        for name, info in installed["adapters"].items():
            from ErisPulse import config
            status = config.getConfig(f"ErisPulse.adapters.status.{name}", False)
            status_str = "[green]已启用[/]" if status else "[yellow]已禁用[/]"
            table.add_row(
                name,
                status_str,
                info["package"],
                info["summary"]
            )
        
        # 如果需要显示所有适配器，获取远程适配器
        if show_all:
            remote_packages = asyncio.run(self.package_manager.get_remote_packages())
            remote_adapters = remote_packages.get("adapters", {})
            
            for name, info in remote_adapters.items():
                if name not in installed["adapters"]:
                    table.add_row(
                        name,
                        "[dim]未安装[/]",
                        info.get("package", ""),
                        info.get("description", "")
                    )
        
        console.print(table)
