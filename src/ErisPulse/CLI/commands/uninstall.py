"""
Uninstall 命令实现

支持卸载模块、适配器、CLI 扩展
"""

import sys
from argparse import ArgumentParser

from ..utils import PackageManager
from ..base import Command


class UninstallCommand(Command):
    
    name = "uninstall"
    description = "卸载模块/适配器包"
    
    def __init__(self):
        self.package_manager = PackageManager()
    
    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            'package',
            nargs='+',
            help='要卸载的包名（可指定多个）'
        )
    
    def execute(self, args):
        success = self.package_manager.uninstall_package(args.package)
        if not success:
            sys.exit(1)
