"""
Module 命令实现

支持启用和禁用模块
"""

import sys
from argparse import ArgumentParser

from ...package_manager import PackageManager
from ...console import console
from ..base import Command


class ModuleCommand(Command):
    """模块管理命令"""
    
    name = "module"
    description = "模块管理（启用/禁用）"
    
    def __init__(self):
        """初始化命令"""
        self.package_manager = PackageManager()
    
    def add_arguments(self, parser: ArgumentParser):
        """添加命令参数"""
        subparsers = parser.add_subparsers(
            dest='module_command',
            metavar="<子命令>",
            help="模块操作"
        )
        
        # 启用模块子命令
        enable_parser = subparsers.add_parser('enable', help='启用模块')
        enable_parser.add_argument('module', help='要启用的模块名')
        
        # 禁用模块子命令
        disable_parser = subparsers.add_parser('disable', help='禁用模块')
        disable_parser.add_argument('module', help='要禁用的模块名')
    
    def execute(self, args):
        """执行命令"""
        from ErisPulse.Core import module as module_manager
        
        installed = self.package_manager.get_installed_packages()
        
        if args.module_command == "enable":
            if args.module not in installed["modules"]:
                console.print(f"[error]模块 [bold]{args.module}[/] 不存在或未安装[/]")
                sys.exit(1)
            else:
                module_manager.enable(args.module)
                console.print(f"[success]模块 [bold]{args.module}[/] 已启用[/]")
        
        elif args.module_command == "disable":
            if args.module not in installed["modules"]:
                console.print(f"[error]模块 [bold]{args.module}[/] 不存在或未安装[/]")
                sys.exit(1)
            else:
                module_manager.disable(args.module)
                console.print(f"[warning]模块 [bold]{args.module}[/] 已禁用[/]")
        
        else:
            # 没有指定子命令，显示帮助
            console.print("[info]请指定子命令: enable 或 disable[/]")
