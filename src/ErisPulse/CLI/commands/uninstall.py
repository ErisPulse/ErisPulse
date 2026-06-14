"""
Uninstall 命令实现

支持卸载模块、适配器
"""

import sys
from argparse import ArgumentParser

from ..base import Command
from ..console import console
from ..i18n import i18n
from ..utils import PackageManager
from ..utils.display import interactive_select_table


class UninstallCommand(Command):
    """
    uninstall 命令

    卸载模块/适配器包
    """

    name = "uninstall"
    description = i18n.t("cli.uninstall.description")
    aliases = ["rm", "remove"]

    def __init__(self):
        """
        初始化卸载命令，创建包管理器实例
        """
        self.package_manager = PackageManager()

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            "package", nargs="*", help=i18n.t("cli.uninstall.package_help")
        )
        parser.add_argument(
            "--no-uv", action="store_true", help=i18n.t("cli.uninstall.no_uv_help")
        )

    def execute(self, args):
        self.package_manager.no_uv = getattr(args, "no_uv", False)
        if args.package:
            success = self.package_manager.uninstall_package(args.package)
            if not success:
                sys.exit(1)
        else:
            self._interactive_uninstall()

    def _interactive_uninstall(self):
        """
        交互式卸载向导，展示已安装的适配器与模块并卸载所选包
        """
        installed = self.package_manager.get_installed_packages()

        all_packages = []
        for name, info in installed.get("adapters", {}).items():
            all_packages.append(
                {
                    "type": i18n.t("cli.uninstall.type_adapter"),
                    "name": name,
                    "package": info["package"],
                    "version": info["version"],
                }
            )
        for name, info in installed.get("modules", {}).items():
            all_packages.append(
                {
                    "type": i18n.t("cli.uninstall.type_module"),
                    "name": name,
                    "package": info["package"],
                    "version": info["version"],
                }
            )

        if not all_packages:
            console.print(f"[dim]  {i18n.t('cli.uninstall.no_packages')}[/]")
            return

        selected = interactive_select_table(
            i18n.t("cli.uninstall.select_title"),
            all_packages,
            columns=[
                {
                    "header": i18n.t("cli.uninstall.header_index"),
                    "style": "#A0B0C0",
                    "width": 4,
                },
                {
                    "header": i18n.t("cli.uninstall.header_type"),
                    "style": "bold",
                    "width": 6,
                },
                {"header": i18n.t("cli.uninstall.header_name")},
                {"header": i18n.t("cli.uninstall.header_package")},
                {"header": i18n.t("cli.uninstall.header_version"), "width": 10},
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
