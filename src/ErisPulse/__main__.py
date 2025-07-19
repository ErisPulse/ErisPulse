import argparse
import importlib.metadata
import subprocess
import sys
import os
import time
import json
import asyncio
from urllib.parse import urlparse
from typing import List, Dict, Tuple, Optional
from importlib.metadata import version, PackageNotFoundError
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Rich console setup
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.text import Text
from rich.box import SIMPLE, ROUNDED, DOUBLE
from rich.style import Style
from rich.theme import Theme
from rich.layout import Layout
from rich.live import Live

# 确保在Windows上启用颜色
import sys
if sys.platform == "win32":
    from colorama import init
    init()

theme = Theme({
    "info": "cyan",
    "success": "green",
    "warning": "yellow",
    "error": "red",
    "title": "magenta",
    "default": "default",
    "progress": "green",
    "progress.remaining": "white",
})

console = Console(theme=theme, color_system="auto", force_terminal=True)

class PyPIManager:
    """
    PyPI包管理器
    
    负责与PyPI交互，包括搜索、安装、卸载和升级ErisPulse模块/适配器
    """
    REMOTE_SOURCES = [
        "https://erisdev.com/packages.json",
        "https://raw.githubusercontent.com/ErisPulse/ErisPulse-ModuleRepo/main/packages.json"
    ]
    
    @staticmethod
    async def get_remote_packages() -> dict:
        """
        获取远程包列表
        
        从配置的远程源获取所有可用的ErisPulse模块和适配器

        :return: 
            Dict[str, Dict]: 包含模块和适配器的字典
                - modules: 模块字典 {模块名: 模块信息}
                - adapters: 适配器字典 {适配器名: 适配器信息}
                
        :raises ClientError: 当网络请求失败时抛出
        :raises asyncio.TimeoutError: 当请求超时时抛出
        """
        import aiohttp
        from aiohttp import ClientError, ClientTimeout
        
        timeout = ClientTimeout(total=5)
        last_error = None
        
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(PyPIManager.REMOTE_SOURCES[0]) as response:
                    if response.status == 200:
                        data = await response.text()
                        data = json.loads(data)
                        return {
                            "modules": data.get("modules", {}),
                            "adapters": data.get("adapters", {})
                        }
        except (ClientError, asyncio.TimeoutError) as e:
            last_error = e
            console.print(Panel(
                f"官方源请求失败，尝试备用源: {e}",
                title="警告",
                style="warning"
            ))
        
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(PyPIManager.REMOTE_SOURCES[1]) as response:
                    if response.status == 200:
                        data = await response.text()
                        data = json.loads(data)
                        return {
                            "modules": data.get("modules", {}),
                            "adapters": data.get("adapters", {})
                        }
        except (ClientError, asyncio.TimeoutError) as e:
            last_error = e
            
        if last_error:
            console.print(Panel(
                f"获取远程模块列表失败: {last_error}",
                title="错误",
                style="error"
            ))
        return {"modules": {}, "adapters": {}}
    
    @staticmethod
    def get_installed_packages() -> Dict[str, Dict[str, str]]:
        """
        获取已安装的包信息
        
        :return: 
            Dict[str, Dict[str, Dict[str, str]]]: 已安装包字典
                - modules: 已安装模块 {模块名: 模块信息}
                - adapters: 已安装适配器 {适配器名: 适配器信息}
        """
        packages = {
            "modules": {},
            "adapters": {}
        }
        
        try:
            # 查找模块
            for dist in importlib.metadata.distributions():
                if "ErisPulse-" in dist.metadata["Name"]:
                    entry_points = dist.entry_points
                    for ep in entry_points:
                        if ep.group == "erispulse.module":
                            packages["modules"][ep.name] = {
                                "package": dist.metadata["Name"],
                                "version": dist.version,
                                "summary": dist.metadata["Summary"]
                            }
                        elif ep.group == "erispulse.adapter":
                            packages["adapters"][ep.name] = {
                                "package": dist.metadata["Name"],
                                "version": dist.version,
                                "summary": dist.metadata["Summary"]
                            }
        except Exception as e:
            console.print(Panel(
                f"获取已安装包信息失败: {e}",
                title="错误",
                style="error"
            ))
        
        return packages
    
    @staticmethod
    def uv_install_package(package_name: str, upgrade: bool = False) -> bool:
        """
        优先使用uv安装包
        
        :param package_name: str 要安装的包名
        :param upgrade: bool 是否升级已安装的包 (默认: False)
        :return: bool 安装是否成功
        """
        try:
            # 检查uv是否可用
            uv_check = subprocess.run(["uv", "--version"], capture_output=True)
            if uv_check.returncode != 0:
                return False  # uv不可用
            
            cmd = ["uv", "pip", "install"]
            if upgrade:
                cmd.append("--upgrade")
            cmd.append(package_name)
            
            with console.status(f"使用uv安装 {package_name}..."):
                result = subprocess.run(cmd, check=True)
                return result.returncode == 0
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    @staticmethod
    def install_package(package_name: str, upgrade: bool = False) -> bool:
        """
        安装指定包 (修改后优先尝试uv)
        
        :param package_name: str 要安装的包名
        :param upgrade: bool 是否升级已安装的包 (默认: False)
        :return: bool 安装是否成功
        """
        # 优先尝试uv安装
        if PyPIManager.uv_install_package(package_name, upgrade):
            console.print(Panel(
                f"包 {package_name} 安装成功 (使用uv)",
                title="成功",
                style="success"
            ))
            return True
            
        # 回退到pip安装
        try:
            cmd = [sys.executable, "-m", "pip", "install"]
            if upgrade:
                cmd.append("--upgrade")
            cmd.append(package_name)
            
            with console.status(f"使用pip安装 {package_name}..."):
                result = subprocess.run(cmd, check=True)
                if result.returncode == 0:
                    console.print(Panel(
                        f"包 {package_name} 安装成功",
                        title="成功",
                        style="success"
                    ))
                    return True
                return False
        except subprocess.CalledProcessError as e:
            console.print(Panel(
                f"安装包 {package_name} 失败: {e}",
                title="错误",
                style="error"
            ))
            return False
    
    @staticmethod
    def uninstall_package(package_name: str) -> bool:
        """
        卸载指定包
        
        :param package_name: str 要卸载的包名
        :return: bool 卸载是否成功
        """
        try:
            with console.status(f"正在卸载 {package_name}..."):
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "uninstall", "-y", package_name],
                    check=True
                )
                if result.returncode == 0:
                    console.print(Panel(
                        f"包 {package_name} 卸载成功",
                        title="成功",
                        style="success"
                    ))
                    return True
                return False
        except subprocess.CalledProcessError as e:
            console.print(Panel(
                f"卸载包 {package_name} 失败: {e}",
                title="错误",
                style="error"
            ))
            return False
    
    @staticmethod
    def upgrade_all() -> bool:
        """
        升级所有已安装的ErisPulse包
        
        :return: bool 升级是否成功
        """
        try:
            installed = PyPIManager.get_installed_packages()
            all_packages = set()
            
            for pkg_type in ["modules", "adapters"]:
                for pkg_info in installed[pkg_type].values():
                    all_packages.add(pkg_info["package"])
            
            if not all_packages:
                console.print(Panel(
                    "没有找到可升级的ErisPulse包",
                    title="提示",
                    style="info"
                ))
                return False
                
            console.print(Panel(
                f"找到 {len(all_packages)} 个可升级的包:\n" + 
                "\n".join(f"  - {pkg}" for pkg in all_packages),
                title="升级列表",
                style="info"
            ))
            
            if not Confirm.ask("确认升级所有包吗？", default=False):
                return False
                
            for pkg in all_packages:
                PyPIManager.install_package(pkg, upgrade=True)
                
            return True
        except Exception as e:
            console.print(Panel(
                f"升级包失败: {e}",
                title="错误",
                style="error"
            ))
            return False

class ReloadHandler(FileSystemEventHandler):
    """
    热重载处理器
    
    监控文件变化并自动重启脚本
    """
    def __init__(self, script_path, reload_mode=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.script_path = script_path
        self.process = None
        self.last_reload = time.time()
        self.reload_mode = reload_mode
        self.start_process()

    def start_process(self):
        """
        启动/重启被监控的进程
        """
        if self.process:
            self.process.terminate()
            self.process.wait()
            
        console.print(f"[bold green]启动进程:[/] {self.script_path}")
        self.process = subprocess.Popen([sys.executable, self.script_path])
        self.last_reload = time.time()

    def on_modified(self, event):
        """
        文件修改事件处理
        
        :param event: FileSystemEvent 文件系统事件对象
        """
        now = time.time()
        if now - self.last_reload < 1.0:
            return
            
        if event.src_path.endswith(".py") and self.reload_mode:
            console.print(f"\n[cyan][热重载] 文件发生变动: {event.src_path}[/]")
            self.start_process()
        elif event.src_path.endswith("config.toml"):
            console.print(f"\n[cyan][热重载] 配置发生变动: {event.src_path}[/]")
            self.start_process()

def start_reloader(script_path, reload_mode=False):
    """
    启动热重载监控
    
    :param script_path: str 要监控的脚本路径
    :param reload_mode: bool 是否启用完整重载模式 (默认: False)
    """
    if not os.path.exists(script_path):
        console.print(Panel(
            f"找不到指定文件: {script_path}",
            title="错误",
            style="error"
        ))
        return
    watch_dirs = [
        os.path.dirname(os.path.abspath(script_path)),
    ]

    handler = ReloadHandler(script_path, reload_mode)
    observer = Observer()

    for d in watch_dirs:
        if os.path.exists(d):
            if reload_mode:
                # 完整重载模式：监控所有.py文件
                observer.schedule(handler, d, recursive=True)
            else:
                # 普通模式：只监控config.toml
                observer.schedule(handler, d, recursive=False)

    observer.start()
    console.print("\n[bold green][热重载] 已启动[/]")
    mode_desc = "开发重载模式" if reload_mode else "配置监控模式"
    console.print(f"[dim]模式: {mode_desc}, 监控目录: {', '.join(watch_dirs)}[/]\n")
    try:
        first_interrupt = True
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        if first_interrupt:
            first_interrupt = False
            console.print("\n[bold green]正在安全关闭热重载...[/]")
            console.print("[bold red]再次按下Ctrl+C以强制关闭[/]")
            try:
                observer.stop()
                if handler.process:
                    handler.process.terminate()
                observer.join()
            except KeyboardInterrupt:
                console.print("[bold red]强制关闭热重载[/]")
                raise
        else:
            console.print(Panel("[bold red]强制关闭热重载[/]"))
            raise

def get_erispulse_version():
    """
    获取当前安装的ErisPulse版本
    
    :return: str ErisPulse版本号或"unknown version"
    """
    try:
        return version("ErisPulse")
    except PackageNotFoundError:
        return "unknown version"

def main():
    """
    CLI主入口
    
    解析命令行参数并执行相应命令
    """
    
    parser = argparse.ArgumentParser(
        prog="epsdk",
        formatter_class=argparse.RawTextHelpFormatter,
        description=f"ErisPulse SDK 命令行工具 {get_erispulse_version()}"
    )
    parser._positionals.title = "基本"
    parser._optionals.title = "可选"
    
    parser.add_argument("--version", action="store_true", help="显示版本信息")
    
    subparsers = parser.add_subparsers(
        dest='command', 
        metavar="<命令>",
    )

    # 安装命令
    install_parser = subparsers.add_parser('install', help='安装模块/适配器包')
    install_parser.add_argument('package', type=str, help='要安装的包名')
    install_parser.add_argument('--upgrade', '-U', action='store_true', help='升级已安装的包')
    
    # 卸载命令
    uninstall_parser = subparsers.add_parser('uninstall', help='卸载模块/适配器包')
    uninstall_parser.add_argument('package', type=str, help='要卸载的包名')
    
    # 启用命令
    enable_parser = subparsers.add_parser('enable', help='启用模块')
    enable_parser.add_argument('module', type=str, help='要启用的模块名')

    # 禁用命令
    disable_parser = subparsers.add_parser('disable', help='禁用模块')
    disable_parser.add_argument('module', type=str, help='要禁用的模块名')

    # 列表命令
    list_parser = subparsers.add_parser('list', help='列出已安装的模块/适配器')
    list_parser.add_argument('--type', '-t', choices=['modules', 'adapters', 'all'], default='all', 
                           help='列出类型 (modules: 仅模块, adapters: 仅适配器, all: 全部)')
    
    # 远程列表命令
    list_remote_parser = subparsers.add_parser('list-remote', help='列出远程可用的模块和适配器')
    list_remote_parser.add_argument('--type', '-t', choices=['modules', 'adapters', 'all'], default='all',
                                  help='列出类型 (modules: 仅模块, adapters: 仅适配器, all: 全部)')
    # 升级命令
    upgrade_parser = subparsers.add_parser('upgrade', help='升级所有模块/适配器')
    upgrade_parser.add_argument('--force', '-f', action='store_true', help='跳过确认直接升级')
    
    # 运行命令
    run_parser = subparsers.add_parser('run', help='运行指定主程序')
    run_parser.add_argument('script', type=str, help='要运行的主程序路径')
    run_parser.add_argument('--reload', action='store_true', help='启用热重载模式')
    
    args = parser.parse_args()
    
    if args.version:
        console.print(f"[green]ErisPulse {get_erispulse_version()}[/]")
        return
        
    if not args.command:
        parser.print_help()
    
    try:
        if args.command == "install":
            import asyncio
            # 首先检查是否是远程模块/适配器的简称
            remote_packages = asyncio.run(PyPIManager.get_remote_packages())
            full_package_name = None
            
            # 检查模块
            if args.package in remote_packages["modules"]:
                full_package_name = remote_packages["modules"][args.package]["package"]
            # 检查适配器
            elif args.package in remote_packages["adapters"]:
                full_package_name = remote_packages["adapters"][args.package]["package"]
            
            # 如果找到远程包，使用完整包名安装
            if full_package_name:
                console.print(Panel(
                    f"找到远程包: [bold]{args.package}[/] → [blue]{full_package_name}[/]",
                    title="信息",
                    style="info"
                ))
                PyPIManager.install_package(full_package_name, args.upgrade)
            else:
                # 否则按原样安装
                PyPIManager.install_package(args.package, args.upgrade)
            
        elif args.command == "uninstall":
            PyPIManager.uninstall_package(args.package)

        elif args.command == "enable":
            from ErisPulse.Core import mods
            installed = PyPIManager.get_installed_packages()
            if args.module not in installed["modules"]:
                console.print(Panel(
                    f"模块 [red]{args.module}[/] 不存在或未安装",
                    title="错误",
                    style="error"
                ))
            else:
                mods.set_module_status(args.module, True)
                console.print(Panel(
                    f"模块 [green]{args.module}[/] 已启用",
                    title="成功",
                    style="success"
                ))
                
        elif args.command == "disable":
            from ErisPulse.Core import mods
            installed = PyPIManager.get_installed_packages()
            if args.module not in installed["modules"]:
                console.print(Panel(
                    f"模块 [red]{args.module}[/] 不存在或未安装",
                    title="错误",
                    style="error"
                ))
            else:
                mods.set_module_status(args.module, False)
                console.print(Panel(
                    f"模块 [yellow]{args.module}[/] 已禁用",
                    title="成功",
                    style="warning"
                ))
                
        elif args.command == "list":
            installed = PyPIManager.get_installed_packages()
            
            if args.type in ["modules", "all"] and installed["modules"]:
                table = Table(title="已安装模块", box=SIMPLE)
                table.add_column("模块名", style="green")
                table.add_column("包名", style="blue")
                table.add_column("版本")
                table.add_column("描述")
                
                for name, info in installed["modules"].items():
                    table.add_row(name, info["package"], info["version"], info["summary"])
                
                console.print(table)
                
            if args.type in ["adapters", "all"] and installed["adapters"]:
                table = Table(title="已安装适配器", box=SIMPLE)
                table.add_column("适配器名", style="yellow")
                table.add_column("包名", style="blue")
                table.add_column("版本")
                table.add_column("描述")
                
                for name, info in installed["adapters"].items():
                    table.add_row(name, info["package"], info["version"], info["summary"])
                
                console.print(table)
                
            if not installed["modules"] and not installed["adapters"]:
                console.print(Panel(
                    "没有安装任何ErisPulse模块或适配器",
                    title="提示",
                    style="info"
                ))
                
        elif args.command == "upgrade":
            if args.force or Confirm.ask("确定要升级所有ErisPulse模块和适配器吗？", default=False):
                PyPIManager.upgrade_all()
                
        elif args.command == "run":
            start_reloader(args.script, args.reload)
        elif args.command == "list-remote":
            import asyncio
            try:
                remote_packages = asyncio.run(PyPIManager.get_remote_packages())
                
                if args.type in ["modules", "all"] and remote_packages["modules"]:
                    table = Table(title="远程模块", box=SIMPLE)
                    table.add_column("模块名", style="green")
                    table.add_column("包名", style="blue")
                    table.add_column("版本")
                    table.add_column("描述")
                    
                    for name, info in remote_packages["modules"].items():
                        table.add_row(name, info["package"], info["version"], info["description"])
                    
                    console.print(table)
                    
                if args.type in ["adapters", "all"] and remote_packages["adapters"]:
                    table = Table(title="远程适配器", box=SIMPLE)
                    table.add_column("适配器名", style="yellow")
                    table.add_column("包名", style="blue")
                    table.add_column("版本")
                    table.add_column("描述")
                    
                    for name, info in remote_packages["adapters"].items():
                        table.add_row(name, info["package"], info["version"], info["description"])
                    
                    console.print(table)
                    
                if not remote_packages["modules"] and not remote_packages["adapters"]:
                    console.print(Panel(
                        "没有找到远程模块或适配器",
                        title="提示",
                        style="info"
                    ))
                    
            except Exception as e:
                console.print(Panel(
                    f"获取远程列表失败: {e}",
                    title="错误",
                    style="error"
                ))
        
    except KeyboardInterrupt as e:
        pass
    except Exception as e:
        console.print(Panel(
            f"执行命令时出错: {e}",
            title="错误",
            style="error"
        ))

if __name__ == "__main__":
    main()