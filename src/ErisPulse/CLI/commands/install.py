"""
Install 命令实现

支持交互式和批量安装模块、适配器
"""

import sys
import asyncio
from argparse import ArgumentParser

from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.box import SIMPLE

from ..utils import PackageManager
from ..console import console
from ..base import Command


class InstallCommand(Command):
    name = "install"
    description = "安装模块/适配器包"
    
    def __init__(self):
        self.package_manager = PackageManager()
    
    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            'package',
            nargs='*',
            help='要安装的包名或模块/适配器简称（可指定多个）'
        )
        parser.add_argument(
            '--upgrade', '-U',
            action='store_true',
            help='升级已安装的包'
        )
        parser.add_argument(
            '--pre',
            action='store_true',
            help='包含预发布版本'
        )
        parser.add_argument(
            '-e', '--editable',
            action='append',
            metavar='PATH',
            help='以可编辑模式安装包（开发者模式，可多次指定）'
        )
        parser.add_argument(
            '--user',
            action='store_true',
            help='安装到用户目录'
        )
        parser.add_argument(
            '--no-deps',
            action='store_true',
            help='不安装依赖包'
        )
        parser.add_argument(
            '-t', '--target',
            metavar='DIR',
            help='安装到指定目录'
        )
        parser.add_argument(
            '--index-url',
            metavar='URL',
            help='指定包索引 URL'
        )
        parser.add_argument(
            '--extra-index-url',
            action='append',
            metavar='URL',
            help='额外的包索引 URL（可多次指定）'
        )
        parser.add_argument(
            '--no-cache-dir',
            action='store_true',
            help='禁用 pip 缓存'
        )
        parser.add_argument(
            '-r', '--requirement',
            metavar='FILE',
            help='从 requirements 文件安装'
        )
        parser.add_argument(
            '-c', '--constraint',
            metavar='FILE',
            help='使用约束文件限制版本'
        )
        parser.add_argument(
            '--force-reinstall',
            action='store_true',
            help='强制重新安装所有包'
        )
        parser.add_argument(
            '--ignore-installed',
            action='store_true',
            help='忽略已安装的包'
        )
        parser.add_argument(
            '--compile',
            action='store_true',
            help='编译 Python 源文件'
        )
        parser.add_argument(
            '--no-compile',
            action='store_true',
            help='不编译 Python 源文件'
        )
        parser.add_argument(
            '--prefix',
            metavar='DIR',
            help='安装前缀目录'
        )
        parser.add_argument(
            '--src',
            metavar='DIR',
            help='可编辑包的检出目录'
        )
        parser.add_argument(
            '--config-settings',
            action='append',
            metavar='SETTINGS',
            help='构建后端的配置设置（可多次指定）'
        )
        parser.add_argument(
            '--no-binary',
            action='append',
            metavar='FORMAT',
            help='不使用二进制包'
        )
        parser.add_argument(
            '--only-binary',
            action='append',
            metavar='FORMAT',
            help='只使用二进制包'
        )
        parser.add_argument(
            '--prefer-binary',
            action='store_true',
            help='优先使用二进制包'
        )
        parser.add_argument(
            '--build-isolation',
            action='store_true',
            help='启用构建隔离'
        )
        parser.add_argument(
            '--no-build-isolation',
            action='store_true',
            help='禁用构建隔离'
        )
        parser.add_argument(
            '--upgrade-strategy',
            choices=['eager', 'only-if-needed', 'to-satisfy-only'],
            help='升级策略'
        )
        parser.add_argument(
            '--break-system-packages',
            action='store_true',
            help='允许覆盖系统管理的包'
        )
    
    def _build_extra_pip_args(self, args) -> list:
        extra = []
        if getattr(args, 'user', False):
            extra.append('--user')
        if getattr(args, 'no_deps', False):
            extra.append('--no-deps')
        if getattr(args, 'target', None):
            extra.extend(['--target', args.target])
        if getattr(args, 'index_url', None):
            extra.extend(['--index-url', args.index_url])
        if getattr(args, 'extra_index_url', None):
            for url in args.extra_index_url:
                extra.extend(['--extra-index-url', url])
        if getattr(args, 'no_cache_dir', False):
            extra.append('--no-cache-dir')
        if getattr(args, 'constraint', None):
            extra.extend(['--constraint', args.constraint])
        if getattr(args, 'force_reinstall', False):
            extra.append('--force-reinstall')
        if getattr(args, 'ignore_installed', False):
            extra.append('--ignore-installed')
        if getattr(args, 'compile', False):
            extra.append('--compile')
        if getattr(args, 'no_compile', False):
            extra.append('--no-compile')
        if getattr(args, 'prefix', None):
            extra.extend(['--prefix', args.prefix])
        if getattr(args, 'src', None):
            extra.extend(['--src', args.src])
        if getattr(args, 'config_settings', None):
            for settings in args.config_settings:
                extra.extend(['--config-settings', settings])
        if getattr(args, 'no_binary', None):
            for fmt in args.no_binary:
                extra.extend(['--no-binary', fmt])
        if getattr(args, 'only_binary', None):
            for fmt in args.only_binary:
                extra.extend(['--only-binary', fmt])
        if getattr(args, 'prefer_binary', False):
            extra.append('--prefer-binary')
        if getattr(args, 'build_isolation', False):
            extra.append('--build-isolation')
        if getattr(args, 'no_build_isolation', False):
            extra.append('--no-build-isolation')
        if getattr(args, 'upgrade_strategy', None):
            extra.extend(['--upgrade-strategy', args.upgrade_strategy])
        if getattr(args, 'break_system_packages', False):
            extra.append('--break-system-packages')
        
        unknown_args = getattr(args, '_unknown_args', []) or []
        extra.extend(unknown_args)
        
        return extra
    
    def execute(self, args):
        editable_paths = getattr(args, 'editable', None)
        requirement_file = getattr(args, 'requirement', None)
        
        if args.package or editable_paths or requirement_file:
            success = True
            pm = self.package_manager
            extra = self._build_extra_pip_args(args)
            
            if editable_paths:
                for path in editable_paths:
                    if not pm.install_direct(['-e', path] + extra, f"可编辑安装 {path}"):
                        success = False
            
            if requirement_file:
                if not pm.install_direct(['-r', requirement_file] + extra, f"从文件安装 {requirement_file}"):
                    success = False
            
            if args.package:
                if not pm.install_package(
                    args.package,
                    upgrade=args.upgrade,
                    pre=args.pre,
                    extra_pip_args=extra
                ):
                    success = False
            
            if not success:
                sys.exit(1)
        else:
            self._interactive_install(args.upgrade, args.pre)
    
    def _interactive_install(self, upgrade: bool = False, pre: bool = False):
        """
        交互式安装界面
        
        :param upgrade: 是否升级模式
        :param pre: 是否包含预发布版本
        """
        console.print(Panel(
            "[bold cyan]ErisPulse 安装组件[/]\n"
            "选择您要安装的组件类型",
            title="欢迎",
            border_style="cyan"
        ))
        
        console.print("[info]正在获取远程包列表...[/]")
        remote_packages = asyncio.run(self.package_manager.get_remote_packages())
        console.print("[success]远程包列表获取完成[/]")
        console.print("")
        
        while True:
            console.print("[bold cyan]请选择组件类型:[/]")
            console.print("  1. 适配器")
            console.print("  2. 模块")
            console.print("  3. 自定义安装")
            console.print("  q. 退出")
            
            choice = Prompt.ask(
                "\n请输入选项 ",
                choices=["1", "2", "3", "q"],
                default="q"
            )
            
            if choice == "q":
                console.print("[info]退出安装向导[/]")
                break
            
            elif choice == "1":
                self._install_adapters(remote_packages, upgrade, pre)
            elif choice == "2":
                self._install_modules(remote_packages, upgrade, pre)
            elif choice == "3":
                self._install_custom(upgrade, pre)
            
            if not Confirm.ask("\n[cyan]是否继续安装其他组件？[/cyan]", default=False):
                break
    
    def _install_adapters(self, remote_packages: dict, upgrade: bool, pre: bool):
        console.print("\n[bold]可用的适配器:[/bold]")
        
        adapters = remote_packages.get("adapters", {})
        
        if not adapters:
            console.print("[yellow]没有可用的适配器[/yellow]")
            return
        
        table = Table(box=SIMPLE, header_style="adapter")
        table.add_column("序号", style="cyan")
        table.add_column("适配器名", style="adapter")
        table.add_column("包名")
        table.add_column("描述")
        
        adapter_list = list(adapters.items())
        for i, (name, info) in enumerate(adapter_list, 1):
            table.add_row(
                str(i),
                name,
                info.get("package", ""),
                info.get("description", "")
            )
        
        console.print(table)
        
        selected = Prompt.ask(
            "\n[cyan]请输入要安装的适配器序号（多个用逗号分隔，如: 1,3）或按 q 返回:[/cyan]"
        )
        
        if selected.lower() == 'q':
            return
        
        try:
            indices = [int(idx.strip()) for idx in selected.split(",")]
            selected_packages = []
            
            for idx in indices:
                if 1 <= idx <= len(adapter_list):
                    adapter_name = adapter_list[idx - 1][0]
                    selected_packages.append(adapter_name)
                    console.print(f"[green]已选择: {adapter_name}[/]")
                else:
                    console.print(f"[red]无效的序号: {idx}[/]")
            
            if selected_packages:
                if Confirm.ask(
                    f"\n[cyan]确认安装以下 {len(selected_packages)} 个适配器吗？[/cyan]",
                    default=True
                ):
                    self.package_manager.install_package(selected_packages, upgrade=upgrade, pre=pre)
        
        except ValueError:
            console.print("[red]输入格式错误，请输入数字序号[/]")
    
    def _install_modules(self, remote_packages: dict, upgrade: bool, pre: bool):
        console.print("\n[bold]可用的模块:[/bold]")
        
        modules = remote_packages.get("modules", {})
        
        if not modules:
            console.print("[yellow]没有可用的模块[/yellow]")
            return
        
        table = Table(box=SIMPLE, header_style="module")
        table.add_column("序号", style="cyan")
        table.add_column("模块名", style="module")
        table.add_column("包名")
        table.add_column("描述")
        
        module_list = list(modules.items())
        for i, (name, info) in enumerate(module_list, 1):
            table.add_row(
                str(i),
                name,
                info.get("package", ""),
                info.get("description", "")
            )
        
        console.print(table)
        
        selected = Prompt.ask(
            "\n[cyan]请输入要安装的模块序号（多个用逗号分隔，如: 1,3）或按 q 返回:[/cyan]"
        )
        
        if selected.lower() == 'q':
            return
        
        try:
            indices = [int(idx.strip()) for idx in selected.split(",")]
            selected_packages = []
            
            for idx in indices:
                if 1 <= idx <= len(module_list):
                    module_name = module_list[idx - 1][0]
                    selected_packages.append(module_name)
                    console.print(f"[green]已选择: {module_name}[/]")
                else:
                    console.print(f"[red]无效的序号: {idx}[/]")
            
            if selected_packages:
                if Confirm.ask(
                    f"\n[cyan]确认安装以下 {len(selected_packages)} 个模块吗？[/cyan]",
                    default=True
                ):
                    self.package_manager.install_package(selected_packages, upgrade=upgrade, pre=pre)
        
        except ValueError:
            console.print("[red]输入格式错误，请输入数字序号[/]")
    
    def _install_custom(self, upgrade: bool, pre: bool):
        package_name = Prompt.ask(
            "\n[cyan]请输入要安装的包名（或按 q 返回）:[/cyan]"
        )
        
        if package_name.lower() == 'q':
            return
        
        if package_name:
            if Confirm.ask(
                f"\n[cyan]确认安装包 {package_name} 吗？[/cyan]",
                default=True
            ):
                self.package_manager.install_package([package_name], upgrade=upgrade, pre=pre)
