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
from ..utils.package_manager import resolve_target_python


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
        py_exec, _py_source = resolve_target_python()
        self.package_manager = PackageManager(python_executable=py_exec)

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
        remote_unavailable = False
        if outdated_only:
            try:
                remote_packages = asyncio.run(
                    self.package_manager.get_remote_packages()
                )
            except Exception:
                remote_packages = None
            # 索引拉取失败（异常或双源均空）：区分"全是最新"与"无法检查"
            remote_unavailable = remote_packages is None or not (
                remote_packages.get("modules") or remote_packages.get("adapters")
            )

        if pkg_type == "all":
            self._print_installed_packages(
                "modules", outdated_only, remote_packages, remote_unavailable
            )
            self._print_installed_packages(
                "adapters", outdated_only, remote_packages, remote_unavailable
            )
        else:
            self._print_installed_packages(
                pkg_type, outdated_only, remote_packages, remote_unavailable
            )

    def _print_installed_packages(
        self,
        pkg_type: str,
        outdated_only: bool = False,
        remote_packages: dict | None = None,
        remote_unavailable: bool = False,
    ):
        """
        以表格形式打印已安装的模块或适配器

        :param pkg_type: [str] 组件类型 (modules 或 adapters)
        :param outdated_only: [bool] 是否仅显示可升级的包 (默认: False)
        :param remote_packages: [Optional[dict]] 预取的远程索引，避免逐包重复拉取 (默认: None)
        :param remote_unavailable: [bool] 远程索引是否不可达（空结果区分文案用，默认: False）
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
            elif outdated_only and remote_unavailable:
                console.print(f"[dim]  {i18n.t('cli.list.outdated_unavailable')}[/]")
            elif outdated_only:
                console.print(f"[dim]  {i18n.t('cli.list.no_outdated')}[/]")
            else:
                console.print(f"[dim]  {i18n.t('cli.list.no_modules')}[/]")
                console.print(f"[dim]  {i18n.t('cli.list.empty_hint')}[/]")

        elif pkg_type == "adapters" and installed["adapters"]:
            table = Table(
                box=SIMPLE, show_lines=False, header_style="bold", pad_edge=False
            )
            table.add_column(
                i18n.t("cli.list.header_adapter"), style="adapter", min_width=12
            )
            table.add_column(i18n.t("cli.list.header_package"), min_width=20)
            table.add_column(i18n.t("cli.list.header_version"), width=10)
            table.add_column(i18n.t("cli.list.header_status"), width=8)
            table.add_column(i18n.t("cli.list.header_desc"))

            count = 0
            for name, info in installed["adapters"].items():
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
                    f"[dim]  {i18n.t('cli.list.count_adapters', count=count)}[/]"
                )
            elif outdated_only and remote_unavailable:
                console.print(f"[dim]  {i18n.t('cli.list.outdated_unavailable')}[/]")
            elif outdated_only:
                console.print(f"[dim]  {i18n.t('cli.list.no_outdated')}[/]")
            else:
                console.print(f"[dim]  {i18n.t('cli.list.no_adapters')}[/]")
                console.print(f"[dim]  {i18n.t('cli.list.empty_hint')}[/]")

        elif not installed.get(pkg_type, {}):
            console.print(
                f"[dim]  {i18n.t('cli.list.no_packages', pkg_type=pkg_type)}[/]"
            )
            console.print(f"[dim]  {i18n.t('cli.list.empty_hint')}[/]")

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
        # 仅"远端更新"才算可升级：本地 dev/git 安装版本比远端新时不再误报
        from ...runtime.version import compare_versions

        for module_info in remote_packages["modules"].values():
            if module_info["package"] == package_name:
                return compare_versions(module_info["version"], current_version) > 0
        for adapter_info in remote_packages["adapters"].values():
            if adapter_info["package"] == package_name:
                return compare_versions(adapter_info["version"], current_version) > 0
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
