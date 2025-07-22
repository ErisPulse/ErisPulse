"""
ErisPulse SDK 命令行工具

提供ErisPulse生态系统的包管理、模块控制和开发工具功能。

{!--< tips >!--}
1. 需要Python 3.8+环境
2. Windows平台需要colorama支持ANSI颜色
{!--< /tips >!--}
"""

import argparse
import importlib.metadata
import subprocess
import sys
import os
import time
import json
import asyncio
from urllib.parse import urlparse
from typing import List, Dict, Tuple, Optional, Callable, Any
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
from rich.markdown import Markdown
from rich.highlighter import RegexHighlighter

# 确保在Windows上启用颜色
if sys.platform == "win32":
    from colorama import init
    init()

class CommandHighlighter(RegexHighlighter):
    """
    高亮CLI命令和参数
    
    {!--< tips >!--}
    使用正则表达式匹配命令行参数和选项
    {!--< /tips >!--}
    """
    highlights = [
        r"(?P<switch>\-\-?\w+)",
        r"(?P<option>\[\w+\])",
        r"(?P<command>\b\w+\b)",
    ]

# 主题配置
theme = Theme({
    "info": "dim cyan",
    "success": "bold green",
    "warning": "bold yellow",
    "error": "bold red",
    "title": "bold magenta",
    "default": "default",
    "progress": "green",
    "progress.remaining": "white",
    "cmd": "bold blue",
    "param": "italic cyan",
    "switch": "bold yellow",
    "module": "bold green",
    "adapter": "bold yellow",
    "cli": "bold magenta",
})

# 全局控制台实例
console = Console(
    theme=theme, 
    color_system="auto", 
    force_terminal=True,
    highlighter=CommandHighlighter()
)

class PackageManager:
    """
    ErisPulse包管理器
    
    提供包安装、卸载、升级和查询功能
    
    {!--< tips >!--}
    1. 支持本地和远程包管理
    2. 包含1小时缓存机制
    {!--< /tips >!--}
    """
    REMOTE_SOURCES = [
        "https://erisdev.com/packages.json",
        "https://raw.githubusercontent.com/ErisPulse/ErisPulse-ModuleRepo/main/packages.json"
    ]
    
    CACHE_EXPIRY = 3600  # 1小时缓存
    
    def __init__(self):
        """初始化包管理器"""
        self._cache = {}
        self._cache_time = {}
        
    async def _fetch_remote_packages(self, url: str) -> Optional[dict]:
        """
        从指定URL获取远程包数据
        
        :param url: 远程包数据URL
        :return: 解析后的JSON数据，失败返回None
        
        :raises ClientError: 网络请求失败时抛出
        :raises JSONDecodeError: JSON解析失败时抛出
        """
        import aiohttp
        from aiohttp import ClientError, ClientTimeout
        
        timeout = ClientTimeout(total=10)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.text()
                        return json.loads(data)
        except (ClientError, asyncio.TimeoutError, json.JSONDecodeError) as e:
            console.print(f"[warning]获取远程包数据失败 ({url}): {e}[/]")
            return None
    
    async def get_remote_packages(self, force_refresh: bool = False) -> dict:
        """
        获取远程包列表，带缓存机制
        
        :param force_refresh: 是否强制刷新缓存
        :return: 包含模块和适配器的字典
        
        :return:
            dict: {
                "modules": {模块名: 模块信息},
                "adapters": {适配器名: 适配器信息},
                "cli_extensions": {扩展名: 扩展信息}
            }
        """
        # 检查缓存
        cache_key = "remote_packages"
        if not force_refresh and cache_key in self._cache:
            if time.time() - self._cache_time[cache_key] < self.CACHE_EXPIRY:
                return self._cache[cache_key]
        
        last_error = None
        result = {"modules": {}, "adapters": {}, "cli_extensions": {}}
        
        for url in self.REMOTE_SOURCES:
            data = await self._fetch_remote_packages(url)
            if data:
                result["modules"].update(data.get("modules", {}))
                result["adapters"].update(data.get("adapters", {}))
                result["cli_extensions"].update(data.get("cli_extensions", {}))
                break
        
        # 更新缓存
        self._cache[cache_key] = result
        self._cache_time[cache_key] = time.time()
        
        return result
    
    def get_installed_packages(self) -> Dict[str, Dict[str, Dict[str, str]]]:
        """
        获取已安装的包信息
        
        :return: 已安装包字典，包含模块、适配器和CLI扩展
        
        :return:
            dict: {
                "modules": {模块名: 模块信息},
                "adapters": {适配器名: 适配器信息},
                "cli_extensions": {扩展名: 扩展信息}
            }
        """
        packages = {
            "modules": {},
            "adapters": {},
            "cli_extensions": {}
        }
        
        try:
            # 查找模块和适配器
            for dist in importlib.metadata.distributions():
                if "ErisPulse-" in dist.metadata["Name"]:
                    entry_points = dist.entry_points
                    for ep in entry_points:
                        if ep.group == "erispulse.module":
                            packages["modules"][ep.name] = {
                                "package": dist.metadata["Name"],
                                "version": dist.version,
                                "summary": dist.metadata["Summary"],
                                "enabled": self._is_module_enabled(ep.name)
                            }
                        elif ep.group == "erispulse.adapter":
                            packages["adapters"][ep.name] = {
                                "package": dist.metadata["Name"],
                                "version": dist.version,
                                "summary": dist.metadata["Summary"]
                            }
            
            # 查找CLI扩展
            entry_points = importlib.metadata.entry_points()
            if hasattr(entry_points, 'select'):
                cli_entries = entry_points.select(group='erispulse.cli')
            else:
                cli_entries = entry_points.get('erispulse.cli', [])
            
            for entry in cli_entries:
                dist = entry.dist
                packages["cli_extensions"][entry.name] = {
                    "package": dist.metadata["Name"],
                    "version": dist.version,
                    "summary": dist.metadata["Summary"]
                }
                
        except Exception as e:
            console.print(f"[error]获取已安装包信息失败: {e}[/]")
            import traceback
            console.print(traceback.format_exc())
        
        return packages
    
    def _is_module_enabled(self, module_name: str) -> bool:
        """
        检查模块是否启用
        
        :param module_name: 模块名称
        :return: 模块是否启用
        
        :raises ImportError: 核心模块不可用时抛出
        """
        try:
            from ErisPulse.Core import mods
            return mods.get_module_status(module_name)
        except ImportError:
            return True
        except Exception:
            return False
    
    def _run_pip_command(self, args: List[str], description: str) -> bool:
        """
        执行pip命令
        
        :param args: pip命令参数列表
        :param description: 进度条描述
        :return: 命令是否成功执行
        """
        with Progress(
            TextColumn(f"[progress.description]{description}"),
            BarColumn(complete_style="progress.download"),
            transient=True
        ) as progress:
            task = progress.add_task("", total=100)
            
            try:
                process = subprocess.Popen(
                    [sys.executable, "-m", "pip"] + args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        progress.update(task, advance=1)
                        
                return process.returncode == 0
            except subprocess.CalledProcessError as e:
                console.print(f"[error]命令执行失败: {e}[/]")
                return False
    
    def install_package(self, package_name: str, upgrade: bool = False) -> bool:
        """
        安装指定包
        
        :param package_name: 要安装的包名
        :param upgrade: 是否升级已安装的包
        :return: 安装是否成功
        """
        cmd = ["install"]
        if upgrade:
            cmd.append("--upgrade")
        cmd.append(package_name)
        
        success = self._run_pip_command(cmd, f"安装 {package_name}")
        
        if success:
            console.print(f"[success]包 {package_name} 安装成功[/]")
        else:
            console.print(f"[error]包 {package_name} 安装失败[/]")
            
        return success
    
    def uninstall_package(self, package_name: str) -> bool:
        """
        卸载指定包
        
        :param package_name: 要卸载的包名
        :return: 卸载是否成功
        """
        success = self._run_pip_command(
            ["uninstall", "-y", package_name],
            f"卸载 {package_name}"
        )
        
        if success:
            console.print(f"[success]包 {package_name} 卸载成功[/]")
        else:
            console.print(f"[error]包 {package_name} 卸载失败[/]")
            
        return success
    
    def upgrade_all(self) -> bool:
        """
        升级所有已安装的ErisPulse包
        
        :return: 升级是否成功
        
        :raises KeyboardInterrupt: 用户取消操作时抛出
        """
        installed = self.get_installed_packages()
        all_packages = set()
        
        for pkg_type in ["modules", "adapters", "cli_extensions"]:
            for pkg_info in installed[pkg_type].values():
                all_packages.add(pkg_info["package"])
        
        if not all_packages:
            console.print("[info]没有找到可升级的ErisPulse包[/]")
            return False
            
        console.print(Panel(
            f"找到 [bold]{len(all_packages)}[/] 个可升级的包:\n" + 
            "\n".join(f"  - [package]{pkg}[/]" for pkg in sorted(all_packages)),
            title="升级列表"
        ))
        
        if not Confirm.ask("确认升级所有包吗？", default=False):
            return False
            
        results = {}
        for pkg in sorted(all_packages):
            results[pkg] = self.install_package(pkg, upgrade=True)
            
        failed = [pkg for pkg, success in results.items() if not success]
        if failed:
            console.print(Panel(
                f"以下包升级失败:\n" + "\n".join(f"  - [error]{pkg}[/]" for pkg in failed),
                title="警告",
                style="warning"
            ))
            return False
            
        return True

class ReloadHandler(FileSystemEventHandler):
    """
    文件系统事件处理器
    
    实现热重载功能，监控文件变化并重启进程
    
    {!--< tips >!--}
    1. 支持.py文件修改重载
    2. 支持配置文件修改重载
    {!--< /tips >!--}
    """

    def __init__(self, script_path: str, reload_mode: bool = False):
        """
        初始化处理器
        
        :param script_path: 要监控的脚本路径
        :param reload_mode: 是否启用重载模式
        """
        super().__init__()
        self.script_path = os.path.abspath(script_path)
        self.process = None
        self.last_reload = time.time()
        self.reload_mode = reload_mode
        self.start_process()
        self.watched_files = set()

    def start_process(self):
        """启动监控进程"""
        if self.process:
            self._terminate_process()
            
        console.print(f"[bold]启动进程: [path]{self.script_path}[/][/]")
        try:
            self.process = subprocess.Popen(
                [sys.executable, self.script_path],
                stdin=sys.stdin,
                stdout=sys.stdout,
                stderr=sys.stderr
            )
            self.last_reload = time.time()
        except Exception as e:
            console.print(f"[error]启动进程失败: {e}[/]")
            raise

    def _terminate_process(self):
        """
        终止当前进程
        
        :raises subprocess.TimeoutExpired: 进程终止超时时抛出
        """
        try:
            self.process.terminate()
            # 等待最多2秒让进程正常退出
            self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            console.print("[warning]进程未正常退出，强制终止...[/]")
            self.process.kill()
            self.process.wait()
        except Exception as e:
            console.print(f"[error]终止进程时出错: {e}[/]")

    def on_modified(self, event):
        """
        文件修改事件处理
        
        :param event: 文件系统事件
        """
        now = time.time()
        if now - self.last_reload < 1.0:  # 防抖
            return
            
        if event.src_path.endswith(".py") and self.reload_mode:
            self._handle_reload(event, "文件变动")
        elif event.src_path.endswith(("config.toml", ".env")):
            self._handle_reload(event, "配置变动")

    def _handle_reload(self, event, reason: str):
        """
        处理重载逻辑
        
        :param event: 文件系统事件
        :param reason: 重载原因描述
        """
        console.print(f"\n[reload]{reason}: [path]{event.src_path}[/][/]")
        self._terminate_process()
        self.start_process()

class CLI:
    """
    ErisPulse命令行接口
    
    提供完整的命令行交互功能
    
    {!--< tips >!--}
    1. 支持动态加载第三方命令
    2. 支持模块化子命令系统
    {!--< /tips >!--}
    """
    
    def __init__(self):
        """初始化CLI"""
        self.parser = self._create_parser()
        self.package_manager = PackageManager()
        self.observer = None
        self.handler = None
        
    def _create_parser(self) -> argparse.ArgumentParser:
        """
        创建命令行参数解析器
        
        :return: 配置好的ArgumentParser实例
        """
        parser = argparse.ArgumentParser(
            prog="epsdk",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description="ErisPulse SDK 命令行工具\n\n一个功能强大的模块化系统管理工具，用于管理ErisPulse生态系统中的模块、适配器和扩展。",
        )
        parser._positionals.title = "命令"
        parser._optionals.title = "选项"
        
        # 全局选项
        parser.add_argument(
            "--version", "-V",
            action="store_true",
            help="显示版本信息"
        )
        parser.add_argument(
            "--verbose", "-v",
            action="count",
            default=0,
            help="增加输出详细程度 (-v, -vv, -vvv)"
        )
        
        # 子命令
        subparsers = parser.add_subparsers(
            dest='command',
            metavar="<命令>",
            help="要执行的操作"
        )
        
        # 安装命令
        install_parser = subparsers.add_parser(
            'install',
            help='安装模块/适配器包'
        )
        install_parser.add_argument(
            'package',
            help='要安装的包名或模块/适配器简称'
        )
        install_parser.add_argument(
            '--upgrade', '-U',
            action='store_true',
            help='升级已安装的包'
        )
        install_parser.add_argument(
            '--pre',
            action='store_true',
            help='包含预发布版本'
        )
        
        # 卸载命令
        uninstall_parser = subparsers.add_parser(
            'uninstall',
            help='卸载模块/适配器包'
        )
        uninstall_parser.add_argument(
            'package',
            help='要卸载的包名'
        )
        
        # 模块管理命令
        module_parser = subparsers.add_parser(
            'module',
            help='模块管理'
        )
        module_subparsers = module_parser.add_subparsers(
            dest='module_command',
            metavar="<子命令>"
        )
        
        # 启用模块
        enable_parser = module_subparsers.add_parser(
            'enable',
            help='启用模块'
        )
        enable_parser.add_argument(
            'module',
            help='要启用的模块名'
        )
        
        # 禁用模块
        disable_parser = module_subparsers.add_parser(
            'disable',
            help='禁用模块'
        )
        disable_parser.add_argument(
            'module',
            help='要禁用的模块名'
        )
        
        # 列表命令
        list_parser = subparsers.add_parser(
            'list',
            help='列出已安装的组件'
        )
        list_parser.add_argument(
            '--type', '-t',
            choices=['modules', 'adapters', 'cli', 'all'],
            default='all',
            help='列出类型 (默认: all)'
        )
        list_parser.add_argument(
            '--outdated', '-o',
            action='store_true',
            help='仅显示可升级的包'
        )
        
        # 远程列表命令
        list_remote_parser = subparsers.add_parser(
            'list-remote',
            help='列出远程可用的组件'
        )
        list_remote_parser.add_argument(
            '--type', '-t',
            choices=['modules', 'adapters', 'cli', 'all'],
            default='all',
            help='列出类型 (默认: all)'
        )
        list_remote_parser.add_argument(
            '--refresh', '-r',
            action='store_true',
            help='强制刷新远程包列表'
        )
        
        # 升级命令
        upgrade_parser = subparsers.add_parser(
            'upgrade',
            help='升级组件'
        )
        upgrade_parser.add_argument(
            'package',
            nargs='?',
            help='要升级的包名 (可选，不指定则升级所有)'
        )
        upgrade_parser.add_argument(
            '--force', '-f',
            action='store_true',
            help='跳过确认直接升级'
        )
        
        # 运行命令
        run_parser = subparsers.add_parser(
            'run',
            help='运行主程序'
        )
        run_parser.add_argument(
            'script',
            nargs='?',
            help='要运行的主程序路径 (默认: main.py)'
        )
        run_parser.add_argument(
            '--reload',
            action='store_true',
            help='启用热重载模式'
        )
        run_parser.add_argument(
            '--no-reload',
            action='store_true',
            help='禁用热重载模式'
        )
        
        # 初始化命令
        init_parser = subparsers.add_parser(
            'init',
            help='初始化ErisPulse项目'
        )
        init_parser.add_argument(
            '--force', '-f',
            action='store_true',
            help='强制覆盖现有配置'
        )
        
        # 加载第三方命令
        self._load_external_commands(subparsers)
        
        return parser
    
    def _get_external_commands(self) -> List[str]:
        """
        获取所有已注册的第三方命令名称
        
        :return: 第三方命令名称列表
        """
        try:
            entry_points = importlib.metadata.entry_points()
            if hasattr(entry_points, 'select'):
                cli_entries = entry_points.select(group='erispulse.cli')
            else:
                cli_entries = entry_points.get('erispulse.cli', [])
            return [entry.name for entry in cli_entries]
        except Exception:
            return []

    def _load_external_commands(self, subparsers):
        """
        加载第三方CLI命令
        
        :param subparsers: 子命令解析器
        
        :raises ImportError: 加载命令失败时抛出
        """
        try:
            entry_points = importlib.metadata.entry_points()
            if hasattr(entry_points, 'select'):
                cli_entries = entry_points.select(group='erispulse.cli')
            else:
                cli_entries = entry_points.get('erispulse.cli', [])
            
            for entry in cli_entries:
                try:
                    cli_func = entry.load()
                    if callable(cli_func):
                        cli_func(subparsers, console)
                    else:
                        console.print(f"[warning]模块 {entry.name} 的入口点不是可调用对象[/]")
                except Exception as e:
                    console.print(f"[error]加载第三方命令 {entry.name} 失败: {e}[/]")
        except Exception as e:
            console.print(f"[warning]加载第三方CLI命令失败: {e}[/]")
    
    def _print_version(self):
        """打印版本信息"""
        from ErisPulse import __version__
        console.print(Panel(
            f"[title]ErisPulse SDK[/] 版本: [bold]{__version__}[/]",
            subtitle=f"Python {sys.version.split()[0]}",
            style="title"
        ))
    
    def _print_installed_packages(self, pkg_type: str, outdated_only: bool = False):
        """
        打印已安装包信息
        
        :param pkg_type: 包类型 (modules/adapters/cli/all)
        :param outdated_only: 是否只显示可升级的包
        """
        installed = self.package_manager.get_installed_packages()
        
        if pkg_type == "modules" and installed["modules"]:
            table = Table(
                title="已安装模块",
                box=SIMPLE,
                header_style="module"
            )
            table.add_column("模块名", style="module")
            table.add_column("包名")
            table.add_column("版本")
            table.add_column("状态")
            table.add_column("描述")
            
            for name, info in installed["modules"].items():
                if outdated_only and not self._is_package_outdated(info["package"], info["version"]):
                    continue
                    
                status = "[green]已启用[/]" if info.get("enabled", True) else "[yellow]已禁用[/]"
                table.add_row(
                    name,
                    info["package"],
                    info["version"],
                    status,
                    info["summary"]
                )
            
            console.print(table)
            
        if pkg_type == "adapters" and installed["adapters"]:
            table = Table(
                title="已安装适配器",
                box=SIMPLE,
                header_style="adapter"
            )
            table.add_column("适配器名", style="adapter")
            table.add_column("包名")
            table.add_column("版本")
            table.add_column("描述")
            
            for name, info in installed["adapters"].items():
                if outdated_only and not self._is_package_outdated(info["package"], info["version"]):
                    continue
                    
                table.add_row(
                    name,
                    info["package"],
                    info["version"],
                    info["summary"]
                )
            
            console.print(table)
            
        if pkg_type == "cli" and installed["cli_extensions"]:
            table = Table(
                title="已安装CLI扩展",
                box=SIMPLE,
                header_style="cli"
            )
            table.add_column("命令名", style="cli")
            table.add_column("包名")
            table.add_column("版本")
            table.add_column("描述")
            
            for name, info in installed["cli_extensions"].items():
                if outdated_only and not self._is_package_outdated(info["package"], info["version"]):
                    continue
                    
                table.add_row(
                    name,
                    info["package"],
                    info["version"],
                    info["summary"]
                )
            
            console.print(table)
    
    def _print_remote_packages(self, pkg_type: str):
        """
        打印远程包信息
        
        :param pkg_type: 包类型 (modules/adapters/cli/all)
        """
        remote_packages = asyncio.run(self.package_manager.get_remote_packages())
        
        if pkg_type == "modules" and remote_packages["modules"]:
            table = Table(
                title="远程模块",
                box=SIMPLE,
                header_style="module"
            )
            table.add_column("模块名", style="module")
            table.add_column("包名")
            table.add_column("最新版本")
            table.add_column("描述")
            
            for name, info in remote_packages["modules"].items():
                table.add_row(
                    name,
                    info["package"],
                    info["version"],
                    info["description"]
                )
            
            console.print(table)
            
        if pkg_type == "adapters" and remote_packages["adapters"]:
            table = Table(
                title="远程适配器",
                box=SIMPLE,
                header_style="adapter"
            )
            table.add_column("适配器名", style="adapter")
            table.add_column("包名")
            table.add_column("最新版本")
            table.add_column("描述")
            
            for name, info in remote_packages["adapters"].items():
                table.add_row(
                    name,
                    info["package"],
                    info["version"],
                    info["description"]
                )
            
            console.print(table)
            
        if pkg_type == "cli" and remote_packages.get("cli_extensions"):
            table = Table(
                title="远程CLI扩展",
                box=SIMPLE,
                header_style="cli"
            )
            table.add_column("命令名", style="cli")
            table.add_column("包名")
            table.add_column("最新版本")
            table.add_column("描述")
            
            for name, info in remote_packages["cli_extensions"].items():
                table.add_row(
                    name,
                    info["package"],
                    info["version"],
                    info["description"]
                )
            
            console.print(table)
    
    def _is_package_outdated(self, package_name: str, current_version: str) -> bool:
        """
        检查包是否过时
        
        :param package_name: 包名
        :param current_version: 当前版本
        :return: 是否有新版本可用
        """
        remote_packages = asyncio.run(self.package_manager.get_remote_packages())
        
        # 检查模块
        for module_info in remote_packages["modules"].values():
            if module_info["package"] == package_name:
                return module_info["version"] != current_version
                
        # 检查适配器
        for adapter_info in remote_packages["adapters"].values():
            if adapter_info["package"] == package_name:
                return adapter_info["version"] != current_version
                
        # 检查CLI扩展
        for cli_info in remote_packages.get("cli_extensions", {}).values():
            if cli_info["package"] == package_name:
                return cli_info["version"] != current_version
                
        return False
    
    def _resolve_package_name(self, short_name: str) -> Optional[str]:
        """
        解析简称到完整包名
        
        :param short_name: 模块/适配器简称
        :return: 完整包名，未找到返回None
        """
        remote_packages = asyncio.run(self.package_manager.get_remote_packages())
        
        # 检查模块
        if short_name in remote_packages["modules"]:
            return remote_packages["modules"][short_name]["package"]
            
        # 检查适配器
        if short_name in remote_packages["adapters"]:
            return remote_packages["adapters"][short_name]["package"]
            
        return None
    
    def _setup_watchdog(self, script_path: str, reload_mode: bool):
        """
        设置文件监控
        
        :param script_path: 要监控的脚本路径
        :param reload_mode: 是否启用重载模式
        """
        watch_dirs = [
            os.path.dirname(os.path.abspath(script_path)),
        ]
        
        # 添加配置目录
        config_dir = os.path.abspath(os.getcwd())
        if config_dir not in watch_dirs:
            watch_dirs.append(config_dir)
        
        self.handler = ReloadHandler(script_path, reload_mode)
        self.observer = Observer()
        
        for d in watch_dirs:
            if os.path.exists(d):
                self.observer.schedule(
                    self.handler, 
                    d, 
                    recursive=reload_mode
                )
                console.print(f"[dim]监控目录: [path]{d}[/][/]")
        
        self.observer.start()
        
        mode_desc = "[bold]开发重载模式[/]" if reload_mode else "[bold]配置监控模式[/]"
        console.print(Panel(
            f"{mode_desc}\n监控目录: [path]{', '.join(watch_dirs)}[/]",
            title="热重载已启动",
            border_style="info"
        ))
    
    def _cleanup(self):
        """清理资源"""
        if self.observer:
            self.observer.stop()
            if self.handler and self.handler.process:
                self.handler._terminate_process()
            self.observer.join()
    
    def run(self):
        """
        运行CLI
        
        :raises KeyboardInterrupt: 用户中断时抛出
        :raises Exception: 命令执行失败时抛出
        """
        args = self.parser.parse_args()
        
        if args.version:
            self._print_version()
            return
            
        if not args.command:
            self.parser.print_help()
            return
            
        try:
            if args.command == "install":
                full_package = self._resolve_package_name(args.package)
                if full_package:
                    console.print(f"[info]找到远程包: [bold]{args.package}[/] → [package]{full_package}[/][/]")
                    self.package_manager.install_package(full_package, args.upgrade)
                else:
                    self.package_manager.install_package(args.package, args.upgrade)
                    
            elif args.command == "uninstall":
                self.package_manager.uninstall_package(args.package)
                
            elif args.command == "module":
                from ErisPulse.Core import mods
                installed = self.package_manager.get_installed_packages()
                
                if args.module_command == "enable":
                    if args.module not in installed["modules"]:
                        console.print(f"[error]模块 [bold]{args.module}[/] 不存在或未安装[/]")
                    else:
                        mods.set_module_status(args.module, True)
                        console.print(f"[success]模块 [bold]{args.module}[/] 已启用[/]")
                        
                elif args.module_command == "disable":
                    if args.module not in installed["modules"]:
                        console.print(f"[error]模块 [bold]{args.module}[/] 不存在或未安装[/]")
                    else:
                        mods.set_module_status(args.module, False)
                        console.print(f"[warning]模块 [bold]{args.module}[/] 已禁用[/]")
                else:
                    self.parser.parse_args(["module", "--help"])
                    
            elif args.command == "list":
                pkg_type = args.type
                if pkg_type == "all":
                    self._print_installed_packages("modules", args.outdated)
                    self._print_installed_packages("adapters", args.outdated)
                    self._print_installed_packages("cli", args.outdated)
                else:
                    self._print_installed_packages(pkg_type, args.outdated)
                    
            elif args.command == "list-remote":
                pkg_type = args.type
                if pkg_type == "all":
                    self._print_remote_packages("modules")
                    self._print_remote_packages("adapters")
                    self._print_remote_packages("cli")
                else:
                    self._print_remote_packages(pkg_type)
                    
            elif args.command == "upgrade":
                if args.package:
                    self.package_manager.install_package(args.package, upgrade=True)
                else:
                    if args.force or Confirm.ask("确定要升级所有ErisPulse组件吗？"):
                        self.package_manager.upgrade_all()
                        
            elif args.command == "run":
                script = args.script or "main.py"
                if not os.path.exists(script):
                    console.print(f"[error]找不到指定文件: [path]{script}[/][/]")
                    return
                    
                reload_mode = args.reload and not args.no_reload
                self._setup_watchdog(script, reload_mode)
                
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    console.print("\n[info]正在安全关闭...[/]")
                    self._cleanup()
                    console.print("[success]已安全退出[/]")
                    
            elif args.command == "init":
                from ErisPulse import sdk
                sdk.init()
                console.print("[success]ErisPulse项目初始化完成[/]")
                
            # 处理第三方命令
            elif args.command in self._get_external_commands():
                # 获取第三方命令的处理函数并执行
                entry_points = importlib.metadata.entry_points()
                if hasattr(entry_points, 'select'):
                    cli_entries = entry_points.select(group='erispulse.cli')
                else:
                    cli_entries = entry_points.get('erispulse.cli', [])
                
                for entry in cli_entries:
                    if entry.name == args.command:
                        cli_func = entry.load()
                        if callable(cli_func):
                            # 创建一个新的解析器来解析第三方命令的参数
                            subparser = self.parser._subparsers._group_actions[0].choices[args.command]
                            parsed_args = subparser.parse_args(sys.argv[2:])
                            # 调用第三方命令处理函数
                            parsed_args.func(parsed_args)
                        break
                
        except KeyboardInterrupt:
            console.print("\n[warning]操作被用户中断[/]")
            self._cleanup()
        except Exception as e:
            console.print(f"[error]执行命令时出错: {e}[/]")
            if args.verbose >= 1:
                import traceback
                console.print(traceback.format_exc())
            self._cleanup()
            sys.exit(1)

def main():
    """
    CLI入口点
    
    {!--< tips >!--}
    1. 创建CLI实例并运行
    2. 处理全局异常
    {!--< /tips >!--}
    """
    cli = CLI()
    cli.run()

if __name__ == "__main__":
    main()