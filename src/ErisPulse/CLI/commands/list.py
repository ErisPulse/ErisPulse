"""
List 命令实现

列出已安装的组件
"""

import asyncio
from argparse import ArgumentParser

from rich.box import SIMPLE
from rich.table import Table

from ..base import Command
from ..console import console
from ..i18n import i18n
from ..utils import PackageManager


class ListCommand(Command):
    """
    list 命令

    列出已安装的组件
    """

    name = "list"
    description = i18n.t("cli.list.description")
    aliases = ["l", "ls"]

    def __init__(self):
        """
        初始化 ListCommand，创建包管理器实例
        """
        self.package_manager = PackageManager()

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            "--type",
            "-t",
            choices=["modules", "adapters", "all"],
            default="all",
            help=i18n.t("cli.list.type_help"),
        )
        parser.add_argument(
            "--outdated",
            "-o",
            action="store_true",
            help=i18n.t("cli.list.outdated_help"),
        )

    def execute(self, args):
        pkg_type = args.type
        outdated_only = args.outdated

        # 仅在需要时一次性拉取远程索引，避免逐包重复 asyncio.run / 网络请求
        remote_packages = None
        if outdated_only:
            try:
                remote_packages = asyncio.run(
                    self.package_manager.get_remote_packages()
                )
            except Exception:
                remote_packages = None

        if pkg_type == "all":
            self._print_installed_packages("modules", outdated_only, remote_packages)
            self._print_installed_packages("adapters", outdated_only, remote_packages)
        else:
            self._print_installed_packages(pkg_type, outdated_only, remote_packages)

    def _print_installed_packages(
        self, pkg_type: str, outdated_only: bool = False, remote_packages: dict | None = None
    ):
        """
        以表格形式打印已安装的模块或适配器

        :param pkg_type: [str] 组件类型 (modules 或 adapters)
        :param outdated_only: [bool] 是否仅显示可升级的包 (默认: False)
        :param remote_packages: [Optional[dict]] 预取的远程索引，避免逐包重复拉取 (默认: None)
        """
        installed = self.package_manager.get_installed_packages()

        if pkg_type == "modules" and installed["modules"]:
            table = Table(
                box=SIMPLE, show_lines=False, header_style="bold", pad_edge=False
            )
            table.add_column(
                i18n.t("cli.list.header_module"), style="module", min_width=12
            )
            table.add_column(i18n.t("cli.list.header_package"), min_width=20)
            table.add_column(i18n.t("cli.list.header_version"), width=10)
            table.add_column(i18n.t("cli.list.header_status"), width=8)
            table.add_column(i18n.t("cli.list.header_desc"))

            count = 0
            for name, info in installed["modules"].items():
                if outdated_only and not self._is_package_outdated(
                    info["package"], info["version"], remote_packages
                ):
                    continue
                status = (
                    f"[green]{i18n.t('cli.list.status_enabled')}[/]"
                    if info.get("enabled", True)
                    else f"[yellow]{i18n.t('cli.list.status_disabled')}[/]"
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
                console.print(
                    f"[dim]  {i18n.t('cli.list.count_modules', count=count)}[/]"
                )
                # 展示模块注册的脚本入口
                self._print_package_scripts(installed["modules"])
            else:
                console.print(f"[dim]  {i18n.t('cli.list.no_modules')}[/]")

        elif pkg_type == "adapters" and installed["adapters"]:
            table = Table(
                box=SIMPLE, show_lines=False, header_style="bold", pad_edge=False
            )
            table.add_column(
                i18n.t("cli.list.header_adapter"), style="adapter", min_width=12
            )
            table.add_column(i18n.t("cli.list.header_package"), min_width=20)
            table.add_column(i18n.t("cli.list.header_version"), width=10)
            table.add_column(i18n.t("cli.list.header_desc"))

            count = 0
            for name, info in installed["adapters"].items():
                if outdated_only and not self._is_package_outdated(
                    info["package"], info["version"], remote_packages
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
                console.print(
                    f"[dim]  {i18n.t('cli.list.count_adapters', count=count)}[/]"
                )
            else:
                console.print(f"[dim]  {i18n.t('cli.list.no_adapters')}[/]")

        elif not installed.get(pkg_type, {}):
            console.print(
                f"[dim]  {i18n.t('cli.list.no_packages', pkg_type=pkg_type)}[/]"
            )

    def _is_package_outdated(
        self,
        package_name: str,
        current_version: str,
        remote_packages: dict | None = None,
    ) -> bool:
        """
        判断指定包是否存在较新的远程版本

        :param package_name: [str] 包名
        :param current_version: [str] 当前已安装的版本号
        :param remote_packages: [Optional[dict]] 预取的远程索引，传入时跳过再次拉取 (默认: None)

        :return: [bool] 存在更新版本返回 True，否则 False
        """
        if remote_packages is None:
            remote_packages = asyncio.run(self.package_manager.get_remote_packages())
        for module_info in remote_packages["modules"].values():
            if module_info["package"] == package_name:
                return module_info["version"] != current_version
        for adapter_info in remote_packages["adapters"].values():
            if adapter_info["package"] == package_name:
                return adapter_info["version"] != current_version
        return False

    def _print_package_scripts(self, packages: dict) -> None:
        """
        发现并展示已安装模块包注册的 console_scripts 入口

        :param packages: [dict] 模块信息字典 {name: {package, version, ...}}
        """
        import importlib.metadata

        all_scripts: list[tuple[str, str]] = []

        def _iter_scripts():
            for module_name, info in packages.items():
                package_name = info.get("package", "")
                if not package_name:
                    continue
                try:
                    dist = importlib.metadata.distribution(package_name)
                    yield from (
                        (module_name, ep.name)
                        for ep in dist.entry_points
                        if ep.group == "console_scripts"
                    )
                except Exception:
                    continue

        all_scripts.extend(_iter_scripts())

        if not all_scripts:
            return

        console.print()
        console.print(f"  [dim]{i18n.t('cli.list.scripts_header')}[/]")
        for module_name, script_name in all_scripts:
            console.print(f"  [module]{module_name}[/]  [cyan]{script_name}[/]")
