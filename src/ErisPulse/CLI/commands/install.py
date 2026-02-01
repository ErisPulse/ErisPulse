"""
Install 命令实现

支持交互式和批量安装模块、适配器、CLI 扩展
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
    description = "安装模块/适配器包（不指定包名时进入交互式安装）"
    
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
    
    def execute(self, args):
        if args.package:
            # 批量安装
            success = self.package_manager.install_package(
                args.package,
                upgrade=args.upgrade,
                pre=args.pre
            )
            if not success:
                sys.exit(1)
        else:
            # 交互式安装
            self._interactive_install(args.upgrade, args.pre)
    
    def _interactive_install(self, upgrade: bool = False, pre: bool = False):
        """
        交互式安装界面
        
        :param upgrade: 是否升级模式
        :param pre: 是否包含预发布版本
        """
        console.print(Panel(
            "[bold cyan]ErisPulse 交互式安装向导[/]\n"
            "选择您要安装的组件类型",
            title="欢迎",
            border_style="cyan"
        ))
        
        # 预加载远程包列表，避免每次选择都请求
        console.print("[info]正在获取远程包列表...[/]")
        remote_packages = asyncio.run(self.package_manager.get_remote_packages())
        console.print("[success]远程包列表获取完成[/]")
        console.print("")
        
        while True:
            console.print("[bold cyan]请选择组件类型:[/]")
            console.print("  1. 适配器")
            console.print("  2. 模块")
            console.print("  3. CLI 扩展")
            console.print("  4. 自定义安装")
            console.print("  q. 退出")
            
            choice = Prompt.ask(
                "\n请输入选项 [1/2/3/4/q]",
                choices=["1", "2", "3", "4", "q"],
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
                self._install_cli_extensions(remote_packages, upgrade, pre)
            elif choice == "4":
                self._install_custom(upgrade, pre)
            
            # 询问是否继续
            if not Confirm.ask("\n[cyan]是否继续安装其他组件？[/cyan]", default=False):
                break
    
    def _install_adapters(self, remote_packages: dict, upgrade: bool, pre: bool):
        """安装适配器"""
        console.print("\n[bold]可用的适配器:[/bold]")
        
        adapters = remote_packages.get("adapters", {})
        
        if not adapters:
            console.print("[yellow]没有可用的适配器[/yellow]")
            return
        
        # 显示适配器列表
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
        
        # 选择适配器
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
                # 确认安装
                if Confirm.ask(
                    f"\n[cyan]确认安装以下 {len(selected_packages)} 个适配器吗？[/cyan]",
                    default=True
                ):
                    self.package_manager.install_package(selected_packages, upgrade=upgrade, pre=pre)
        
        except ValueError:
            console.print("[red]输入格式错误，请输入数字序号[/]")
    
    def _install_modules(self, remote_packages: dict, upgrade: bool, pre: bool):
        """安装模块"""
        console.print("\n[bold]可用的模块:[/bold]")
        
        modules = remote_packages.get("modules", {})
        
        if not modules:
            console.print("[yellow]没有可用的模块[/yellow]")
            return
        
        # 显示模块列表
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
        
        # 选择模块
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
                # 确认安装
                if Confirm.ask(
                    f"\n[cyan]确认安装以下 {len(selected_packages)} 个模块吗？[/cyan]",
                    default=True
                ):
                    self.package_manager.install_package(selected_packages, upgrade=upgrade, pre=pre)
        
        except ValueError:
            console.print("[red]输入格式错误，请输入数字序号[/]")
    
    def _install_cli_extensions(self, remote_packages: dict, upgrade: bool, pre: bool):
        """安装 CLI 扩展"""
        console.print("\n[bold]可用的 CLI 扩展:[/bold]")
        
        cli_extensions = remote_packages.get("cli_extensions", {})
        
        if not cli_extensions:
            console.print("[yellow]没有可用的 CLI 扩展[/yellow]")
            return
        
        # 显示 CLI 扩展列表
        table = Table(box=SIMPLE, header_style="cli")
        table.add_column("序号", style="cyan")
        table.add_column("命令名", style="cli")
        table.add_column("包名")
        table.add_column("描述")
        
        cli_list = list(cli_extensions.items())
        for i, (name, info) in enumerate(cli_list, 1):
            table.add_row(
                str(i),
                name,
                info.get("package", ""),
                info.get("description", "")
            )
        
        console.print(table)
        
        # 选择 CLI 扩展
        selected = Prompt.ask(
            "\n[cyan]请输入要安装的 CLI 扩展序号（多个用逗号分隔，如: 1,3）或按 q 返回:[/cyan]"
        )
        
        if selected.lower() == 'q':
            return
        
        try:
            indices = [int(idx.strip()) for idx in selected.split(",")]
            selected_packages = []
            
            for idx in indices:
                if 1 <= idx <= len(cli_list):
                    cli_name = cli_list[idx - 1][0]
                    selected_packages.append(cli_name)
                    console.print(f"[green]已选择: {cli_name}[/]")
                else:
                    console.print(f"[red]无效的序号: {idx}[/]")
            
            if selected_packages:
                # 确认安装
                if Confirm.ask(
                    f"\n[cyan]确认安装以下 {len(selected_packages)} 个 CLI 扩展吗？[/cyan]",
                    default=True
                ):
                    self.package_manager.install_package(selected_packages, upgrade=upgrade, pre=pre)
        
        except ValueError:
            console.print("[red]输入格式错误，请输入数字序号[/]")
    
    def _install_custom(self, upgrade: bool, pre: bool):
        """自定义安装"""
        package_name = Prompt.ask(
            "\n[cyan]请输入要安装的包名（或按 q 返回）:[/cyan]"
        )
        
        if package_name.lower() == 'q':
            return
        
        if package_name:
            # 确认安装
            if Confirm.ask(
                f"\n[cyan]确认安装包 {package_name} 吗？[/cyan]",
                default=True
            ):
                self.package_manager.install_package([package_name], upgrade=upgrade, pre=pre)
