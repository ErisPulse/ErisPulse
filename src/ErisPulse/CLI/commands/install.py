"""
Install 命令实现

支持交互式和批量安装模块、适配器
"""

import sys
import asyncio
from argparse import ArgumentParser

from rich.prompt import Confirm, Prompt
from rich.text import Text

from ..utils import PackageManager
from ..utils.display import interactive_select_table
from ..console import console
from ..base import Command


class InstallCommand(Command):
    """
    install 命令

    安装模块/适配器包，支持交互式与批量安装
    """

    name = "install"
    description = "安装模块/适配器包"
    aliases = ["i", "add"]

    def __init__(self):
        """
        初始化安装命令，创建包管理器实例
        """
        self.package_manager = PackageManager()

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            "package", nargs="*", help="要安装的包名或模块/适配器简称（可指定多个）"
        )
        parser.add_argument(
            "--upgrade", "-U", action="store_true", help="升级已安装的包"
        )
        parser.add_argument("--pre", action="store_true", help="包含预发布版本")
        parser.add_argument(
            "-e",
            "--editable",
            action="append",
            metavar="PATH",
            help="以可编辑模式安装包（开发者模式，可多次指定）",
        )
        parser.add_argument("--user", action="store_true", help="安装到用户目录")
        parser.add_argument("--no-deps", action="store_true", help="不安装依赖包")
        parser.add_argument("-t", "--target", metavar="DIR", help="安装到指定目录")
        parser.add_argument("--index-url", metavar="URL", help="指定包索引 URL")
        parser.add_argument(
            "--extra-index-url",
            action="append",
            metavar="URL",
            help="额外的包索引 URL（可多次指定）",
        )
        parser.add_argument("--no-cache-dir", action="store_true", help="禁用 pip 缓存")
        parser.add_argument(
            "-r", "--requirement", metavar="FILE", help="从 requirements 文件安装"
        )
        parser.add_argument(
            "-c", "--constraint", metavar="FILE", help="使用约束文件限制版本"
        )
        parser.add_argument(
            "--force-reinstall", action="store_true", help="强制重新安装所有包"
        )
        parser.add_argument(
            "--ignore-installed", action="store_true", help="忽略已安装的包"
        )
        parser.add_argument("--compile", action="store_true", help="编译 Python 源文件")
        parser.add_argument(
            "--no-compile", action="store_true", help="不编译 Python 源文件"
        )
        parser.add_argument("--prefix", metavar="DIR", help="安装前缀目录")
        parser.add_argument("--src", metavar="DIR", help="可编辑包的检出目录")
        parser.add_argument(
            "--config-settings",
            action="append",
            metavar="SETTINGS",
            help="构建后端的配置设置（可多次指定）",
        )
        parser.add_argument(
            "--no-binary", action="append", metavar="FORMAT", help="不使用二进制包"
        )
        parser.add_argument(
            "--only-binary", action="append", metavar="FORMAT", help="只使用二进制包"
        )
        parser.add_argument(
            "--prefer-binary", action="store_true", help="优先使用二进制包"
        )
        parser.add_argument(
            "--build-isolation", action="store_true", help="启用构建隔离"
        )
        parser.add_argument(
            "--no-build-isolation", action="store_true", help="禁用构建隔离"
        )
        parser.add_argument(
            "--upgrade-strategy",
            choices=["eager", "only-if-needed", "to-satisfy-only"],
            help="升级策略",
        )
        parser.add_argument(
            "--break-system-packages", action="store_true", help="允许覆盖系统管理的包"
        )
        parser.add_argument(
            "--no-uv", action="store_true", help="禁用 uv，强制使用 pip 安装"
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
                        ["-e", path] + extra, f"可编辑安装 {path}"
                    ):
                        success = False

            if requirement_file:
                if not pm.install_direct(
                    ["-r", requirement_file] + extra, f"从文件安装 {requirement_file}"
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
        with console.status("[bold green]正在获取远程包列表...", spinner="dots"):
            remote_packages = asyncio.run(self.package_manager.get_remote_packages())

        while True:
            console.print()
            console.print(Text("  请选择组件类型:", style="bold"))
            console.print(Text("    1.  适配器", style="adapter"))
            console.print(Text("    2.  模块", style="module"))
            console.print(Text("    3.  搜索安装", style="info"))
            console.print(Text("    4.  自定义安装", style="dim"))
            console.print(Text("    q.  退出", style="dim"))

            choice = Prompt.ask(
                "\n  请输入选项", choices=["1", "2", "3", "4", "q"], default="q"
            )

            if choice == "q":
                console.print("[info]  退出安装向导[/]")
                break
            elif choice == "1":
                self._install_adapters(remote_packages, upgrade, pre)
            elif choice == "2":
                self._install_modules(remote_packages, upgrade, pre)
            elif choice == "3":
                self._install_search(remote_packages, upgrade, pre)
            elif choice == "4":
                self._install_custom(upgrade, pre)

            if not Confirm.ask("\n  [cyan]是否继续安装其他组件？[/]", default=False):
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
            console.print("[dim]  没有可用的适配器[/]")
            return

        adapter_list = list(adapters.items())

        selected = interactive_select_table(
            "适配器",
            adapter_list,
            columns=[
                {"header": "序号", "style": "#A0B0C0", "width": 4},
                {"header": "适配器名", "style": "adapter"},
                {"header": "包名"},
                {"header": "描述"},
            ],
            row_builder=lambda table, idx, item, checked: table.add_row(
                ("● " if checked else "  ") + str(idx + 1),
                item[0] if item[1].get("verified", True) else f"{item[0]}（未验证）",
                item[1].get("package", ""),
                item[1].get("description", ""),
            ),
        )

        if not selected:
            return

        selected_names = [name for name, _ in selected]
        console.print(f"\n  [dim]已选择: [bold]{', '.join(selected_names)}[/][/]")
        if Confirm.ask(
            f"  [cyan]确认安装 {len(selected_names)} 个适配器？[/]", default=True
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
            console.print("[dim]  没有可用的模块[/]")
            return

        module_list = list(modules.items())

        selected = interactive_select_table(
            "模块",
            module_list,
            columns=[
                {"header": "序号", "style": "#A0B0C0", "width": 4},
                {"header": "模块名", "style": "module"},
                {"header": "包名"},
                {"header": "描述"},
            ],
            row_builder=lambda table, idx, item, checked: table.add_row(
                ("● " if checked else "  ") + str(idx + 1),
                item[0] if item[1].get("verified", True) else f"{item[0]}（未验证）",
                item[1].get("package", ""),
                item[1].get("description", ""),
            ),
        )

        if not selected:
            return

        selected_names = [name for name, _ in selected]
        console.print(f"\n  [dim]已选择: [bold]{', '.join(selected_names)}[/][/]")
        if Confirm.ask(
            f"  [cyan]确认安装 {len(selected_names)} 个模块？[/]", default=True
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
        from rich.table import Table
        from rich.box import SIMPLE
        from ..utils.display import section_header

        query = Prompt.ask("\n  [cyan]请输入搜索关键词（或 q 返回）[/]")
        if query.lower() == "q" or not query.strip():
            return

        results = self.package_manager.search_package(query.strip())
        installed = results.get("installed", [])
        remote = results.get("remote", [])

        total = len(installed) + len(remote)
        if total == 0:
            console.print(f"[dim]  未找到与 '{query}' 相关的组件[/]")
            return

        # 显示已安装结果
        if installed:
            section_header("已安装")
            table = Table(
                box=SIMPLE, show_lines=False, header_style="bold", pad_edge=False
            )
            table.add_column("类型", width=8)
            table.add_column("名称", style="bold", min_width=12)
            table.add_column("包名", min_width=20)
            table.add_column("版本", width=10)
            table.add_column("描述")
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
            console.print(f"[dim]  {len(installed)} 个已安装[/]")

        # 显示远程结果
        if remote:
            section_header("远程可用")
            table = Table(
                box=SIMPLE, show_lines=False, header_style="bold", pad_edge=False
            )
            table.add_column("类型", width=8)
            table.add_column("名称", style="bold", min_width=12)
            table.add_column("包名", min_width=20)
            table.add_column("版本", width=10)
            table.add_column("描述")
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
            console.print(f"[dim]  {len(remote)} 个远程组件[/]")

        console.print(f"\n  [bold]共找到 {total} 个结果[/]")

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
            "\n  [cyan]输入序号安装（多个用逗号分隔，q 跳过）[/]",
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
            f"  [cyan]确认安装 {len(selected)} 个包？[/]", default=True
        ):
            self.package_manager.install_package(selected, upgrade=upgrade, pre=pre)

    def _install_custom(self, upgrade: bool, pre: bool):
        """
        自定义安装，提示用户输入包名并安装

        :param upgrade: [bool] 是否升级已安装的包
        :param pre: [bool] 是否包含预发布版本
        """
        package_name = Prompt.ask("\n  [cyan]请输入要安装的包名（或 q 返回）[/]")
        if package_name.lower() == "q":
            return
        if package_name:
            if Confirm.ask(f"  [cyan]确认安装 {package_name}？[/]", default=True):
                self.package_manager.install_package(
                    [package_name], upgrade=upgrade, pre=pre
                )
