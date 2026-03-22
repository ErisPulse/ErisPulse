"""
Uninstall 命令实现

支持卸载模块、适配器、CLI 扩展
"""

import sys
from argparse import ArgumentParser

from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.box import SIMPLE

from ..utils import PackageManager
from ..console import console
from ..base import Command


class UninstallCommand(Command):
    
    name = "uninstall"
    description = "卸载模块/适配器包（不指定包名时进入交互式卸载）"
    
    def __init__(self):
        self.package_manager = PackageManager()
    
    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            'package',
            nargs='*',
            help='要卸载的包名（可指定多个）'
        )
    
    def execute(self, args):
        if args.package:
            # 直接卸载指定包
            success = self.package_manager.uninstall_package(args.package)
            if not success:
                sys.exit(1)
        else:
            # 交互式卸载
            self._interactive_uninstall()
    
    def _interactive_uninstall(self):
        console.print(Panel(
            "[bold cyan]ErisPulse 卸载向导[/]\n"
            "选择要卸载的包",
            title="卸载向导",
            border_style="cyan"
        ))
        
        # 获取已安装的包
        installed = self.package_manager.get_installed_packages()
        
        # 收集所有已安装的包
        all_packages = []
        
        # 添加适配器
        for name, info in installed.get("adapters", {}).items():
            all_packages.append({
                "type": "适配器",
                "name": name,
                "package": info["package"],
                "version": info["version"]
            })
        
        # 添加模块
        for name, info in installed.get("modules", {}).items():
            all_packages.append({
                "type": "模块",
                "name": name,
                "package": info["package"],
                "version": info["version"]
            })
        
        # 添加 CLI 扩展
        for name, info in installed.get("cli_extensions", {}).items():
            all_packages.append({
                "type": "CLI",
                "name": name,
                "package": info["package"],
                "version": info["version"]
            })
        
        if not all_packages:
            console.print("[yellow]没有已安装的包[/]")
            return
        
        # 显示包列表
        table = Table(box=SIMPLE)
        table.add_column("序号", style="cyan")
        table.add_column("类型", style="bold")
        table.add_column("名称")
        table.add_column("包名")
        table.add_column("版本")
        
        for i, pkg in enumerate(all_packages, 1):
            table.add_row(
                str(i),
                pkg["type"],
                pkg["name"],
                pkg["package"],
                pkg["version"]
            )
        
        console.print(table)
        
        # 选择要卸载的包
        selected = Prompt.ask(
            "\n[cyan]请输入要卸载的包序号（多个用逗号分隔，如: 1,3）或按 q 退出:[/cyan]"
        )
        
        if selected.lower() == 'q':
            console.print("[info]退出卸载向导[/]")
            return
        
        try:
            indices = [int(idx.strip()) for idx in selected.split(",")]
            selected_packages = []
            
            for idx in indices:
                if 1 <= idx <= len(all_packages):
                    pkg_info = all_packages[idx - 1]
                    selected_packages.append(pkg_info["package"])
                    console.print(f"[green]已选择: {pkg_info['name']} ({pkg_info['package']})[/]")
                else:
                    console.print(f"[red]无效的序号: {idx}[/]")
            
            if selected_packages:
                # 卸载选中的包
                success = self.package_manager.uninstall_package(selected_packages)
                if not success:
                    sys.exit(1)
        
        except ValueError:
            console.print("[red]输入格式错误，请输入数字序号[/]")
