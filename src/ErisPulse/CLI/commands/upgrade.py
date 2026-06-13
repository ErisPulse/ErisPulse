"""
Upgrade 命令实现

升级组件
"""

import sys
from argparse import ArgumentParser
from rich.prompt import Confirm

from ..utils import PackageManager
from ..base import Command


class UpgradeCommand(Command):
    """
    upgrade 命令

    升级组件（不指定包名则升级所有）
    """

    name = "upgrade"
    description = "升级组件（不指定包名则升级所有）"
    aliases = ["up"]

    def __init__(self):
        """
        初始化升级命令，创建包管理器实例
        """
        self.package_manager = PackageManager()

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            "package", nargs="*", help="要升级的包名 (可选，不指定则升级所有)"
        )
        parser.add_argument(
            "--force", "-f", action="store_true", help="跳过确认直接升级"
        )
        parser.add_argument("--pre", action="store_true", help="包含预发布版本")
        parser.add_argument(
            "--no-uv", action="store_true", help="禁用 uv，强制使用 pip 升级"
        )

    def execute(self, args):
        self.package_manager.no_uv = getattr(args, "no_uv", False)
        if args.package:
            # 升级指定包
            success = self.package_manager.upgrade_package(args.package, pre=args.pre)
            if not success:
                sys.exit(1)
        else:
            # 升级所有包
            if args.force or Confirm.ask(
                "确定要升级所有ErisPulse组件吗？", default=False
            ):
                success = self.package_manager.upgrade_all()
                if not success:
                    sys.exit(1)
