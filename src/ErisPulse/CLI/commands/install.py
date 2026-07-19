"""
Install 命令实现

支持交互式和批量安装模块、适配器
"""

import asyncio
import sys
from argparse import ArgumentParser

from rich.prompt import Confirm, Prompt
from rich.text import Text

from ..base import Command
from ..console import console
from ..i18n import i18n
from ..utils import PackageManager
from ..utils.display import interactive_select_table


class InstallCommand(Command):
    """
    install 命令

    安装模块/适配器包，支持交互式与批量安装
    """

    name = "install"
    description = i18n.t("cli.install.description")
    aliases = ["i", "add"]

    def __init__(self):
        """
        初始化安装命令，创建包管理器实例
        """
        self.package_manager = PackageManager()

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            "package", nargs="*", help=i18n.t("cli.install.package_help")
        )
        parser.add_argument(
            "--upgrade",
            "-U",
            action="store_true",
            help=i18n.t("cli.install.upgrade_help"),
        )
        parser.add_argument(
            "--pre", action="store_true", help=i18n.t("cli.install.pre_help")
        )
        parser.add_argument(
            "-e",
            "--editable",
            action="append",
            metavar="PATH",
            help=i18n.t("cli.install.editable_help"),
        )
        parser.add_argument(
            "--user", action="store_true", help=i18n.t("cli.install.user_help")
        )
        parser.add_argument(
            "--no-deps", action="store_true", help=i18n.t("cli.install.no_deps_help")
        )
        parser.add_argument(
            "-t", "--target", metavar="DIR", help=i18n.t("cli.install.target_help")
        )
        parser.add_argument(
            "--index-url", metavar="URL", help=i18n.t("cli.install.index_url_help")
        )
        parser.add_argument(
            "--extra-index-url",
            action="append",
            metavar="URL",
            help=i18n.t("cli.install.extra_index_url_help"),
        )
        parser.add_argument(
            "--no-cache-dir",
            action="store_true",
            help=i18n.t("cli.install.no_cache_dir_help"),
        )
        parser.add_argument(
            "-r",
            "--requirement",
            metavar="FILE",
            help=i18n.t("cli.install.requirement_help"),
        )
        parser.add_argument(
            "-c",
            "--constraint",
            metavar="FILE",
            help=i18n.t("cli.install.constraint_help"),
        )
        parser.add_argument(
            "--force-reinstall",
            action="store_true",
            help=i18n.t("cli.install.force_reinstall_help"),
        )
        parser.add_argument(
            "--ignore-installed",
            action="store_true",
            help=i18n.t("cli.install.ignore_installed_help"),
        )
        parser.add_argument(
            "--compile", action="store_true", help=i18n.t("cli.install.compile_help")
        )
        parser.add_argument(
            "--no-compile",
            action="store_true",
            help=i18n.t("cli.install.no_compile_help"),
        )
        parser.add_argument(
            "--prefix", metavar="DIR", help=i18n.t("cli.install.prefix_help")
        )
        parser.add_argument("--src", metavar="DIR", help=i18n.t("cli.install.src_help"))
        parser.add_argument(
            "--config-settings",
            action="append",
            metavar="SETTINGS",
            help=i18n.t("cli.install.config_settings_help"),
        )
        parser.add_argument(
            "--no-binary",
            action="append",
            metavar="FORMAT",
            help=i18n.t("cli.install.no_binary_help"),
        )
        parser.add_argument(
            "--only-binary",
            action="append",
            metavar="FORMAT",
            help=i18n.t("cli.install.only_binary_help"),
        )
        parser.add_argument(
            "--prefer-binary",
            action="store_true",
            help=i18n.t("cli.install.prefer_binary_help"),
        )
        parser.add_argument(
            "--build-isolation",
            action="store_true",
            help=i18n.t("cli.install.build_isolation_help"),
        )
        parser.add_argument(
            "--no-build-isolation",
            action="store_true",
            help=i18n.t("cli.install.no_build_isolation_help"),
        )
        parser.add_argument(
            "--upgrade-strategy",
            choices=["eager", "only-if-needed", "to-satisfy-only"],
            help=i18n.t("cli.install.upgrade_strategy_help"),
        )
        parser.add_argument(
            "--break-system-packages",
            action="store_true",
            help=i18n.t("cli.install.break_system_packages_help"),
        )
        parser.add_argument(
            "--no-uv", action="store_true", help=i18n.t("cli.install.no_uv_help")
        )

    def _build_extra_pip_args(self, args) -> list:
        """
        根据解析后的命令行参数构建额外的 pip 安装参数列表

        :param args: [Namespace] 解析后的命令行参数

        :return: [list] 额外的 pip 命令行参数列表
        """
        extra = []
        if getattr(args, "user", False):
            extra.append("--user")
        if getattr(args, "no_deps", False):
            extra.append("--no-deps")
        if getattr(args, "target", None):
            extra.extend(["--target", args.target])
        if getattr(args, "index_url", None):
            extra.extend(["--index-url", args.index_url])
        if getattr(args, "extra_index_url", None):
            for url in args.extra_index_url:
                extra.extend(["--extra-index-url", url])
        if getattr(args, "no_cache_dir", False):
            extra.append("--no-cache-dir")
        if getattr(args, "constraint", None):
            extra.extend(["--constraint", args.constraint])
        if getattr(args, "force_reinstall", False):
            extra.append("--force-reinstall")
        if getattr(args, "ignore_installed", False):
            extra.append("--ignore-installed")
        if getattr(args, "compile", False):
            extra.append("--compile")
        if getattr(args, "no_compile", False):
            extra.append("--no-compile")
        if getattr(args, "prefix", None):
            extra.extend(["--prefix", args.prefix])
        if getattr(args, "src", None):
            extra.extend(["--src", args.src])
        if getattr(args, "config_settings", None):
            for settings in args.config_settings:
                extra.extend(["--config-settings", settings])
        if getattr(args, "no_binary", None):
            for fmt in args.no_binary:
                extra.extend(["--no-binary", fmt])
        if getattr(args, "only_binary", None):
            for fmt in args.only_binary:
                extra.extend(["--only-binary", fmt])
        if getattr(args, "prefer_binary", False):
            extra.append("--prefer-binary")
        if getattr(args, "build_isolation", False):
            extra.append("--build-isolation")
        if getattr(args, "no_build_isolation", False):
            extra.append("--no-build-isolation")
        if getattr(args, "upgrade_strategy", None):
            extra.extend(["--upgrade-strategy", args.upgrade_strategy])
        if getattr(args, "break_system_packages", False):
            extra.append("--break-system-packages")

        unknown_args = getattr(args, "_unknown_args", []) or []
        extra.extend(unknown_args)

        return extra

    def execute(self, args):
        self.package_manager.no_uv = getattr(args, "no_uv", False)
        editable_paths = getattr(args, "editable", None)
        requirement_file = getattr(args, "requirement", None)

        if args.package or editable_paths or requirement_file:
            success = True
            pm = self.package_manager
            extra = self._build_extra_pip_args(args)

            if editable_paths:
                for path in editable_paths:
                    if not pm.install_direct(
                        ["-e", path, *extra],
                        i18n.t("cli.install.installing_editable", path=path),
                    ):
                        success = False

            if requirement_file:
                if not pm.install_direct(
                    ["-r", requirement_file, *extra],
                    i18n.t(
                        "cli.install.installing_requirement",
                        requirement_file=requirement_file,
                    ),
                ):
                    success = False

            if args.package:
                if not pm.install_package(
                    args.package,
                    upgrade=args.upgrade,
                    pre=args.pre,
                    extra_pip_args=extra,
                ):
                    success = False

            if not success:
                sys.exit(1)
        else:
            self._interactive_install(args.upgrade, args.pre)

    def _interactive_install(self, upgrade: bool = False, pre: bool = False):
        """
        交互式安装向导，提供适配器、模块、搜索与自定义安装选项

        :param upgrade: [bool] 是否升级已安装的包 (默认: False)
        :param pre: [bool] 是否包含预发布版本 (默认: False)
        """
        with console.status(
            f"[bold green]{i18n.t('cli.install.fetching_packages')}[/]", spinner="dots"
        ):
            remote_packages = asyncio.run(self.package_manager.get_remote_packages())

        while True:
            console.print()
            console.print(Text(i18n.t("cli.install.select_type"), style="bold"))
            console.print(
                Text(f"    1.  {i18n.t('cli.install.type_adapter')}", style="adapter")
            )
            console.print(
                Text(f"    2.  {i18n.t('cli.install.type_module')}", style="module")
            )
            console.print(
                Text(f"    3.  {i18n.t('cli.install.type_search')}", style="info")
            )
            console.print(
                Text(f"    4.  {i18n.t('cli.install.type_custom')}", style="dim")
            )
            console.print(Text(f"    q.  {i18n.t('cli.install.quit')}", style="dim"))

            choice = Prompt.ask(
                "\n  {}".format(i18n.t("cli.install.enter_option")),
                choices=["1", "2", "3", "4", "q"],
                default="q",
            )

            if choice == "q":
                console.print(f"[info]{i18n.t('cli.install.exit_wizard')}[/]")
                break
            if choice == "1":
                self._install_adapters(remote_packages, upgrade, pre)
            elif choice == "2":
                self._install_modules(remote_packages, upgrade, pre)
            elif choice == "3":
                self._install_search(remote_packages, upgrade, pre)
            elif choice == "4":
                self._install_custom(upgrade, pre)

            if not Confirm.ask(
                f"\n  [cyan]{i18n.t('cli.install.continue_install')}[/]", default=False
            ):
                break

    def _install_adapters(self, remote_packages: dict, upgrade: bool, pre: bool):
        """
        交互式选择并安装适配器

        :param remote_packages: [dict] 远程包列表
        :param upgrade: [bool] 是否升级已安装的包
        :param pre: [bool] 是否包含预发布版本
        """
        adapters = remote_packages.get("adapters", {})
        if not adapters:
            console.print(f"[dim]  {i18n.t('cli.install.no_adapters')}[/]")
            return

        adapter_list = list(adapters.items())

        selected = interactive_select_table(
            i18n.t("cli.install.type_adapter"),
            adapter_list,
            columns=[
                {
                    "header": i18n.t("cli.list_remote.header_index"),
                    "style": "#A0B0C0",
                    "width": 4,
                },
                {
                    "header": i18n.t("cli.list_remote.header_adapter"),
                    "style": "adapter",
                },
                {"header": i18n.t("cli.list_remote.header_package")},
                {"header": i18n.t("cli.list_remote.header_desc")},
            ],
            row_builder=lambda table, idx, item, checked: table.add_row(
                ("● " if checked else "  ") + str(idx + 1),
                item[0]
                if item[1].get("verified", True)
                else i18n.t("cli.install.unverified", name=item[0]),
                item[1].get("package", ""),
                item[1].get("description", ""),
            ),
        )

        if not selected:
            return

        selected_names = [name for name, _ in selected]
        console.print(
            f"\n  [dim]{i18n.t('cli.install.selected', selected=', '.join(selected_names))}[/]"
        )
        if Confirm.ask(
            f"  [cyan]{i18n.t('cli.install.confirm_adapters', count=len(selected_names))}[/]",
            default=True,
        ):
            self.package_manager.install_package(
                selected_names, upgrade=upgrade, pre=pre
            )

    def _install_modules(self, remote_packages: dict, upgrade: bool, pre: bool):
        """
        交互式选择并安装模块

        :param remote_packages: [dict] 远程包列表
        :param upgrade: [bool] 是否升级已安装的包
        :param pre: [bool] 是否包含预发布版本
        """
        modules = remote_packages.get("modules", {})
        if not modules:
            console.print(f"[dim]  {i18n.t('cli.install.no_modules')}[/]")
            return

        module_list = list(modules.items())

        selected = interactive_select_table(
            i18n.t("cli.install.type_module"),
            module_list,
            columns=[
                {
                    "header": i18n.t("cli.list_remote.header_index"),
                    "style": "#A0B0C0",
                    "width": 4,
                },
                {"header": i18n.t("cli.list_remote.header_module"), "style": "module"},
                {"header": i18n.t("cli.list_remote.header_package")},
                {"header": i18n.t("cli.list_remote.header_desc")},
            ],
            row_builder=lambda table, idx, item, checked: table.add_row(
                ("● " if checked else "  ") + str(idx + 1),
                item[0]
                if item[1].get("verified", True)
                else i18n.t("cli.install.unverified", name=item[0]),
                item[1].get("package", ""),
                item[1].get("description", ""),
            ),
        )

        if not selected:
            return

        selected_names = [name for name, _ in selected]
        console.print(
            f"\n  [dim]{i18n.t('cli.install.selected', selected=', '.join(selected_names))}[/]"
        )
        if Confirm.ask(
            f"  [cyan]{i18n.t('cli.install.confirm_modules', count=len(selected_names))}[/]",
            default=True,
        ):
            self.package_manager.install_package(
                selected_names, upgrade=upgrade, pre=pre
            )

    def _install_search(self, remote_packages: dict, upgrade: bool, pre: bool):
        """
        搜索并安装

        {!--< internal-use >!--}

        :param remote_packages: [dict] 远程包列表
        :param upgrade: [bool] 是否升级
        :param pre: [bool] 是否包含预发布版本
        """
        from rich.box import SIMPLE
        from rich.table import Table

        from ..utils.display import section_header

        query = Prompt.ask(f"\n  [cyan]{i18n.t('cli.install.search_prompt')}[/]")
        if query.lower() == "q" or not query.strip():
            return

        results = self.package_manager.search_package(query.strip())
        installed = results.get("installed", [])
        remote = results.get("remote", [])

        total = len(installed) + len(remote)
        if total == 0:
            console.print(f"[dim]  {i18n.t('cli.install.no_results', query=query)}[/]")
            return

        # 显示已安装结果
        if installed:
            section_header(i18n.t("cli.install.installed_section"))
            table = Table(
                box=SIMPLE, show_lines=False, header_style="bold", pad_edge=False
            )
            table.add_column(i18n.t("cli.install.type_header"), width=8)
            table.add_column(
                i18n.t("cli.install.name_header"), style="bold", min_width=12
            )
            table.add_column(i18n.t("cli.install.pkg_header"), min_width=20)
            table.add_column(i18n.t("cli.install.ver_header"), width=10)
            table.add_column(i18n.t("cli.install.desc_header"))
            for item in installed:
                type_style = "adapter" if item["type"] == "adapter" else "module"
                table.add_row(
                    f"[{type_style}]{item['type']}[/]",
                    item["name"],
                    item["package"],
                    item.get("version", ""),
                    item.get("summary", ""),
                )
            console.print(table)
            console.print(
                f"[dim]  {i18n.t('cli.install.count_installed', count=len(installed))}[/]"
            )

        # 显示远程结果
        if remote:
            section_header(i18n.t("cli.install.remote_section"))
            table = Table(
                box=SIMPLE, show_lines=False, header_style="bold", pad_edge=False
            )
            table.add_column(i18n.t("cli.install.type_header"), width=8)
            table.add_column(
                i18n.t("cli.install.name_header"), style="bold", min_width=12
            )
            table.add_column(i18n.t("cli.install.pkg_header"), min_width=20)
            table.add_column(i18n.t("cli.install.ver_header"), width=10)
            table.add_column(i18n.t("cli.install.desc_header"))
            for item in remote:
                type_style = "adapter" if item["type"] == "adapter" else "module"
                table.add_row(
                    f"[{type_style}]{item['type']}[/]",
                    item["name"],
                    item["package"],
                    item.get("version", ""),
                    item.get("summary", ""),
                )
            console.print(table)
            console.print(
                f"[dim]  {i18n.t('cli.install.count_remote', count=len(remote))}[/]"
            )

        console.print(
            f"\n  [bold]{i18n.t('cli.install.total_results', total=total)}[/]"
        )

        # 序号选择安装
        if not remote:
            return

        console.print()
        for i, item in enumerate(remote, 1):
            type_style = "adapter" if item["type"] == "adapter" else "module"
            console.print(
                f"    [dim]{i:>2}.[/] [{type_style}]{item['name']}[/]"
                f"  [dim]{item['package']}[/]"
            )

        raw = Prompt.ask(
            f"\n  [cyan]{i18n.t('cli.install.select_install_prompt')}[/]",
            default="q",
        )
        if raw.lower() == "q" or not raw.strip():
            return

        selected = []
        for part in raw.strip().replace(" ", "").replace("，", ",").split(","):
            try:
                idx = int(part) - 1
                if 0 <= idx < len(remote):
                    selected.append(remote[idx]["package"])
            except ValueError:
                continue

        if selected and Confirm.ask(
            f"  [cyan]{i18n.t('cli.install.confirm_search_install', count=len(selected))}[/]",
            default=True,
        ):
            self.package_manager.install_package(selected, upgrade=upgrade, pre=pre)

    def _install_custom(self, upgrade: bool, pre: bool):
        """
        自定义安装，提示用户输入包名并安装

        :param upgrade: [bool] 是否升级已安装的包
        :param pre: [bool] 是否包含预发布版本
        """
        package_name = Prompt.ask(f"\n  [cyan]{i18n.t('cli.install.custom_prompt')}[/]")
        if package_name.lower() == "q":
            return
        if package_name:
            if Confirm.ask(
                f"  [cyan]{i18n.t('cli.install.confirm_custom_install', package_name=package_name)}[/]",
                default=True,
            ):
                self.package_manager.install_package(
                    [package_name], upgrade=upgrade, pre=pre
                )
