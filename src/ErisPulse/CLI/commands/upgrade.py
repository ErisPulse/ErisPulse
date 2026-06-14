"""
Upgrade 命令实现

升级组件
"""

import sys
from argparse import ArgumentParser

from rich.prompt import Confirm

from ..base import Command
from ..i18n import i18n
from ..utils import PackageManager


class UpgradeCommand(Command):
    """
    upgrade 命令

    升级组件（不指定包名则升级所有）
    """

    name = "upgrade"
    description = i18n.t("cli.upgrade.description")
    aliases = ["up"]

    def __init__(self):
        """
        初始化升级命令，创建包管理器实例
        """
        self.package_manager = PackageManager()

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            "package", nargs="*", help=i18n.t("cli.upgrade.package_help")
        )
        parser.add_argument(
            "--force", "-f", action="store_true", help=i18n.t("cli.upgrade.force_help")
        )
        parser.add_argument(
            "--pre", action="store_true", help=i18n.t("cli.upgrade.pre_help")
        )
        parser.add_argument(
            "--no-uv", action="store_true", help=i18n.t("cli.upgrade.no_uv_help")
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
                i18n.t("cli.upgrade.confirm_all"), default=False
            ):
                success = self.package_manager.upgrade_all()
                if not success:
                    sys.exit(1)
