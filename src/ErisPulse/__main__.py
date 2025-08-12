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
        "https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/packages.json"
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
            entry_points = importlib.metadata.entry_points()
            
            # 处理模块
            if hasattr(entry_points, 'select'):
                module_entries = entry_points.select(group='erispulse.module')
            else:
                module_entries = entry_points.get('erispulse.module', [])
            
            for entry in module_entries:
                dist = entry.dist
                packages["modules"][entry.name] = {
                    "package": dist.metadata["Name"],
                    "version": dist.version,
                    "summary": dist.metadata["Summary"],
                    "enabled": self._is_module_enabled(entry.name)
                }
            
            # 处理适配器
            if hasattr(entry_points, 'select'):
                adapter_entries = entry_points.select(group='erispulse.adapter')
            else:
                adapter_entries = entry_points.get('erispulse.adapter', [])
            
            for entry in adapter_entries:
                dist = entry.dist
                packages["adapters"][entry.name] = {
                    "package": dist.metadata["Name"],
                    "version": dist.version,
                    "summary": dist.metadata["Summary"]
                }
            
            # 查找CLI扩展
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
            print(f"[error] 获取已安装包信息失败: {e}")
            import traceback
            print(traceback.format_exc())
        
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
    
    def _normalize_name(self, name: str) -> str:
        """
        标准化包名，统一转为小写以实现大小写不敏感比较
        
        :param name: 原始名称
        :return: 标准化后的名称
        """
        return name.lower().strip()
    
    async def _find_package_by_alias(self, alias: str) -> Optional[str]:
        """
        通过别名查找实际包名（大小写不敏感）
        
        :param alias: 包别名
        :return: 实际包名，未找到返回None
        """
        normalized_alias = self._normalize_name(alias)
        remote_packages = await self.get_remote_packages()
        
        # 检查模块
        for name, info in remote_packages["modules"].items():
            if self._normalize_name(name) == normalized_alias:
                return info["package"]
                
        # 检查适配器
        for name, info in remote_packages["adapters"].items():
            if self._normalize_name(name) == normalized_alias:
                return info["package"]
                
        # 检查CLI扩展
        for name, info in remote_packages.get("cli_extensions", {}).items():
            if self._normalize_name(name) == normalized_alias:
                return info["package"]
                
        return None
    
    def _find_installed_package_by_name(self, name: str) -> Optional[str]:
        """
        在已安装包中查找实际包名（大小写不敏感）
        
        :param name: 包名或别名
        :return: 实际包名，未找到返回None
        """
        normalized_name = self._normalize_name(name)
        installed = self.get_installed_packages()
        
        # 在已安装的模块中查找
        for module_info in installed["modules"].values():
            if self._normalize_name(module_info["package"]) == normalized_name:
                return module_info["package"]
                    
        # 在已安装的适配器中查找
        for adapter_info in installed["adapters"].values():
            if self._normalize_name(adapter_info["package"]) == normalized_name:
                return adapter_info["package"]
                    
        # 在已安装的CLI扩展中查找
        for cli_info in installed["cli_extensions"].values():
            if self._normalize_name(cli_info["package"]) == normalized_name:
                return cli_info["package"]
                
        return None

    def _run_pip_command_with_output(self, args: List[str], description: str) -> Tuple[bool, str, str]:
        """
        执行pip命令并捕获输出
        
        :param args: pip命令参数列表
        :param description: 进度条描述
        :return: (是否成功, 标准输出, 标准错误)
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
                    universal_newlines=True,
                    bufsize=1  # 行缓冲
                )
                
                stdout_lines = []
                stderr_lines = []
                
                # 使用超时机制避免永久阻塞
                import threading
                import queue
                
                def read_output(pipe, lines_list):
                    try:
                        for line in iter(pipe.readline, ''):
                            lines_list.append(line)
                            progress.update(task, advance=5)  # 每行增加进度
                        pipe.close()
                    except Exception:
                        pass
                
                stdout_thread = threading.Thread(target=read_output, args=(process.stdout, stdout_lines))
                stderr_thread = threading.Thread(target=read_output, args=(process.stderr, stderr_lines))
                
                stdout_thread.start()
                stderr_thread.start()
                
                # 等待进程结束，最多等待5分钟
                try:
                    process.wait(timeout=300)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                    console.print("[warning]命令执行超时，已强制终止[/]")
                    return False, "", "命令执行超时"
                
                stdout_thread.join(timeout=10)
                stderr_thread.join(timeout=10)
                
                stdout = ''.join(stdout_lines)
                stderr = ''.join(stderr_lines)
                
                return process.returncode == 0, stdout, stderr
            except subprocess.CalledProcessError as e:
                console.print(f"[error]命令执行失败: {e}[/]")
                return False, "", str(e)
            except Exception as e:
                console.print(f"[error]执行过程中发生异常: {e}[/]")
                return False, "", str(e)

    def _compare_versions(self, version1: str, version2: str) -> int:
        """
        比较两个版本号
        
        :param version1: 版本号1
        :param version2: 版本号2
        :return: 1 if version1 > version2, -1 if version1 < version2, 0 if equal
        """
        from packaging import version as comparison
        try:
            v1 = comparison.parse(version1)
            v2 = comparison.parse(version2)
            if v1 > v2:
                return 1
            elif v1 < v2:
                return -1
            else:
                return 0
        except comparison.InvalidVersion:
            # 如果无法解析，使用字符串比较作为后备
            if version1 > version2:
                return 1
            elif version1 < version2:
                return -1
            else:
                return 0

    def _check_sdk_compatibility(self, min_sdk_version: str) -> Tuple[bool, str]:
        """
        检查SDK版本兼容性
        
        :param min_sdk_version: 所需的最小SDK版本
        :return: (是否兼容, 当前版本信息)
        """
        try:
            from ErisPulse import __version__
            current_version = __version__
        except ImportError:
            current_version = "unknown"
        
        if current_version == "unknown":
            return True, "无法确定当前SDK版本"
        
        try:
            compatibility = self._compare_versions(current_version, min_sdk_version)
            if compatibility >= 0:
                return True, f"当前SDK版本 {current_version} 满足最低要求 {min_sdk_version}"
            else:
                return False, f"当前SDK版本 {current_version} 低于最低要求 {min_sdk_version}"
        except Exception:
            return True, "无法验证SDK版本兼容性"

    async def _get_package_info(self, package_name: str) -> Optional[Dict[str, Any]]:
        """
        获取包的详细信息（包括min_sdk_version等）
        
        :param package_name: 包名或别名
        :return: 包信息字典
        """
        # 首先尝试通过别名查找
        normalized_name = self._normalize_name(package_name)
        remote_packages = await self.get_remote_packages()
        
        # 检查模块
        for name, info in remote_packages["modules"].items():
            if self._normalize_name(name) == normalized_name:
                return info
        
        # 检查适配器
        for name, info in remote_packages["adapters"].items():
            if self._normalize_name(name) == normalized_name:
                return info
        
        # 检查CLI扩展
        for name, info in remote_packages.get("cli_extensions", {}).items():
            if self._normalize_name(name) == normalized_name:
                return info
        
        return None

    def install_package(self, package_names: List[str], upgrade: bool = False, pre: bool = False) -> bool:
        """
        安装指定包（支持多个包）
        
        :param package_names: 要安装的包名或别名列表
        :param upgrade: 是否升级已安装的包
        :param pre: 是否包含预发布版本
        :return: 安装是否成功
        """
        all_success = True
        
        for package_name in package_names:
            # 首先尝试通过别名查找实际包名
            actual_package = asyncio.run(self._find_package_by_alias(package_name))
            
            if actual_package:
                console.print(f"[info]找到别名映射: [bold]{package_name}[/] → [package]{actual_package}[/][/]") 
                current_package_name = actual_package
            else:
                console.print(f"[info]未找到别名，将直接安装: [package]{package_name}[/][/]")
                current_package_name = package_name

            # 检查SDK版本兼容性
            package_info = asyncio.run(self._get_package_info(package_name))
            if package_info and "min_sdk_version" in package_info:
                is_compatible, message = self._check_sdk_compatibility(package_info["min_sdk_version"])
                if not is_compatible:
                    console.print(Panel(
                        f"[warning]SDK版本兼容性警告[/]\n"
                        f"包 [package]{current_package_name}[/] 需要最低SDK版本 {package_info['min_sdk_version']}\n"
                        f"{message}\n\n"
                        f"继续安装可能会导致问题。",
                        title="兼容性警告",
                        border_style="warning"
                    ))
                    if not Confirm.ask("是否继续安装？", default=False):
                        console.print("[info]已取消安装[/]")
                        all_success = False
                        continue
                else:
                    console.print(f"[success]{message}[/]")

            # 构建pip命令
            cmd = ["install"]
            if upgrade:
                cmd.append("--upgrade")
            if pre:
                cmd.append("--pre")
            cmd.append(current_package_name)
            
            # 执行安装命令
            success, stdout, stderr = self._run_pip_command_with_output(cmd, f"安装 {current_package_name}")
            
            if success:
                console.print(Panel(
                    f"[success]包 {current_package_name} 安装成功[/]\n\n"
                    f"[dim]{stdout}[/]",
                    title="安装完成",
                    border_style="success"
                ))
            else:
                console.print(Panel(
                    f"[error]包 {current_package_name} 安装失败[/]\n\n"
                    f"[dim]{stderr}[/]",
                    title="安装失败",
                    border_style="error"
                ))
                all_success = False
        
        return all_success
    
    def uninstall_package(self, package_names: List[str]) -> bool:
        """
        卸载指定包（支持多个包，支持别名）
        
        :param package_names: 要卸载的包名或别名列表
        :return: 卸载是否成功
        """
        all_success = True
        
        packages_to_uninstall = []
        
        # 首先处理所有包名，查找实际包名
        for package_name in package_names:
            # 首先尝试通过别名查找实际包名
            actual_package = asyncio.run(self._find_package_by_alias(package_name))
            
            if actual_package:
                console.print(f"[info]找到别名映射: [bold]{package_name}[/] → [package]{actual_package}[/][/]") 
                packages_to_uninstall.append(actual_package)
            else:
                # 如果找不到别名映射，检查是否是已安装的包
                installed_package = self._find_installed_package_by_name(package_name)
                if installed_package:
                    package_name = installed_package
                    console.print(f"[info]找到已安装包: [bold]{package_name}[/][/]") 
                    packages_to_uninstall.append(package_name)
                else:
                    console.print(f"[warning]未找到别名映射，将尝试直接卸载: [package]{package_name}[/][/]")
                    packages_to_uninstall.append(package_name)

        # 确认卸载操作
        package_list = "\n".join([f"  - [package]{pkg}[/]" for pkg in packages_to_uninstall])
        if not Confirm.ask(f"确认卸载以下包吗？\n{package_list}", default=False):
            console.print("[info]操作已取消[/]")
            return False

        # 执行卸载命令
        for package_name in packages_to_uninstall:
            success, stdout, stderr = self._run_pip_command_with_output(
                ["uninstall", "-y", package_name],
                f"卸载 {package_name}"
            )
            
            if success:
                console.print(Panel(
                    f"[success]包 {package_name} 卸载成功[/]\n\n"
                    f"[dim]{stdout}[/]",
                    title="卸载完成",
                    border_style="success"
                ))
            else:
                console.print(Panel(
                    f"[error]包 {package_name} 卸载失败[/]\n\n"
                    f"[dim]{stderr}[/]",
                    title="卸载失败",
                    border_style="error"
                ))
                all_success = False
        
        return all_success
    
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
            results[pkg] = self.install_package([pkg], upgrade=True)
            
        failed = [pkg for pkg, success in results.items() if not success]
        if failed:
            console.print(Panel(
                f"以下包升级失败:\n" + "\n".join(f"  - [error]{pkg}[/]" for pkg in failed),
                title="警告",
                style="warning"
            ))
            return False
            
        return True

    def upgrade_package(self, package_names: List[str], pre: bool = False) -> bool:
        """
        升级指定包（支持多个包）
        
        :param package_names: 要升级的包名或别名列表
        :param pre: 是否包含预发布版本
        :return: 升级是否成功
        """
        all_success = True
        
        for package_name in package_names:
            # 首先尝试通过别名查找实际包名
            actual_package = asyncio.run(self._find_package_by_alias(package_name))
            
            if actual_package:
                console.print(f"[info]找到别名映射: [bold]{package_name}[/] → [package]{actual_package}[/][/]") 
                current_package_name = actual_package
            else:
                current_package_name = package_name

            # 检查SDK版本兼容性
            package_info = asyncio.run(self._get_package_info(package_name))
            if package_info and "min_sdk_version" in package_info:
                is_compatible, message = self._check_sdk_compatibility(package_info["min_sdk_version"])
                if not is_compatible:
                    console.print(Panel(
                        f"[warning]SDK版本兼容性警告[/]\n"
                        f"包 [package]{current_package_name}[/] 需要最低SDK版本 {package_info['min_sdk_version']}\n"
                        f"{message}\n\n"
                        f"继续升级可能会导致问题。",
                        title="兼容性警告",
                        border_style="warning"
                    ))
                    if not Confirm.ask("是否继续升级？", default=False):
                        console.print("[info]已取消升级[/]")
                        all_success = False
                        continue
                else:
                    console.print(f"[success]{message}[/]")

            # 构建pip命令
            cmd = ["install", "--upgrade"]
            if pre:
                cmd.append("--pre")
            cmd.append(current_package_name)
            
            # 执行升级命令
            success, stdout, stderr = self._run_pip_command_with_output(cmd, f"升级 {current_package_name}")
            
            if success:
                console.print(Panel(
                    f"[success]包 {current_package_name} 升级成功[/]\n\n"
                    f"[dim]{stdout}[/]",
                    title="升级完成",
                    border_style="success"
                ))
            else:
                console.print(Panel(
                    f"[error]包 {current_package_name} 升级失败[/]\n\n"
                    f"[dim]{stderr}[/]",
                    title="升级失败",
                    border_style="error"
                ))
                all_success = False
        
        return all_success

    def search_package(self, query: str) -> Dict[str, List[Dict[str, str]]]:
        """
        搜索包（本地和远程）
        
        :param query: 搜索关键词
        :return: 匹配的包信息
        """
        normalized_query = self._normalize_name(query)
        results = {"installed": [], "remote": []}
        
        # 搜索已安装的包
        installed = self.get_installed_packages()
        for pkg_type in ["modules", "adapters", "cli_extensions"]:
            for name, info in installed[pkg_type].items():
                if (normalized_query in self._normalize_name(name) or 
                    normalized_query in self._normalize_name(info["package"]) or
                    normalized_query in self._normalize_name(info["summary"])):
                    results["installed"].append({
                        "type": pkg_type[:-1] if pkg_type.endswith("s") else pkg_type,  # 移除复数s
                        "name": name,
                        "package": info["package"],
                        "version": info["version"],
                        "summary": info["summary"]
                    })
        
        # 搜索远程包
        remote = asyncio.run(self.get_remote_packages())
        for pkg_type in ["modules", "adapters", "cli_extensions"]:
            for name, info in remote[pkg_type].items():
                if (normalized_query in self._normalize_name(name) or 
                    normalized_query in self._normalize_name(info["package"]) or
                    normalized_query in self._normalize_name(info.get("description", "")) or
                    normalized_query in self._normalize_name(info.get("summary", ""))):
                    results["remote"].append({
                        "type": pkg_type[:-1] if pkg_type.endswith("s") else pkg_type,  # 移除复数s
                        "name": name,
                        "package": info["package"],
                        "version": info["version"],
                        "summary": info.get("description", info.get("summary", ""))
                    })
        
        return results

    def get_installed_version(self) -> str:
        """
        获取当前安装的ErisPulse版本
        
        :return: 当前版本号
        """
        try:
            from ErisPulse import __version__
            return __version__
        except ImportError:
            return "unknown"
    
    async def get_pypi_versions(self) -> List[Dict[str, Any]]:
        """
        从PyPI获取ErisPulse的所有可用版本
        
        :return: 版本信息列表
        """
        import aiohttp
        from aiohttp import ClientError, ClientTimeout
        from packaging import version as comparison
        
        timeout = ClientTimeout(total=10)
        url = "https://pypi.org/pypi/ErisPulse/json"
        
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        versions = []
                        for version_str, releases in data["releases"].items():
                            if releases:  # 只包含有文件的版本
                                release_info = {
                                    "version": version_str,
                                    "uploaded": releases[0].get("upload_time_iso_8601", ""),
                                    "pre_release": self._is_pre_release(version_str)
                                }
                                versions.append(release_info)
                        
                        # 使用版本比较函数正确排序版本
                        versions.sort(key=lambda x: comparison.parse(x["version"]), reverse=True)
                        return versions
        except (ClientError, asyncio.TimeoutError, json.JSONDecodeError, KeyError, Exception) as e:
            console.print(f"[error]获取PyPI版本信息失败: {e}[/]")
            return []
    
    def _is_pre_release(self, version: str) -> bool:
        """
        判断版本是否为预发布版本
        
        :param version: 版本号
        :return: 是否为预发布版本
        """
        import re
        # 检查是否包含预发布标识符 (alpha, beta, rc, dev等)
        pre_release_pattern = re.compile(r'(a|b|rc|dev|alpha|beta)\d*', re.IGNORECASE)
        return bool(pre_release_pattern.search(version))

    def update_self(self, target_version: str = None, force: bool = False) -> bool:
        """
        更新ErisPulse SDK本身
        
        :param target_version: 目标版本号，None表示更新到最新版本
        :param force: 是否强制更新
        :return: 更新是否成功
        """
        current_version = self.get_installed_version()
        
        if target_version and target_version == current_version and not force:
            console.print(f"[info]当前已是目标版本 [bold]{current_version}[/][/]")
            return True
        
        # 确定要安装的版本
        package_spec = "ErisPulse"
        if target_version:
            package_spec += f"=={target_version}"
        
        # 检查是否在Windows上且尝试更新自身
        if sys.platform == "win32":
            # 构建更新脚本
            update_script = f"""
import time
import subprocess
import sys
import os

# 等待原进程结束
time.sleep(2)

# 执行更新命令
try:
    result = subprocess.run([
        sys.executable, "-m", "pip", "install", "--upgrade", "{package_spec}"
    ], capture_output=True, text=True, timeout=300)
    
    if result.returncode == 0:
        print("更新成功!")
        print(result.stdout)
    else:
        print("更新失败:")
        print(result.stderr)
except Exception as e:
    print(f"更新过程中出错: {{e}}")

# 清理临时脚本
try:
    os.remove(__file__)
except:
    pass
"""
            # 创建临时更新脚本
            import tempfile
            script_path = os.path.join(tempfile.gettempdir(), "epsdk_update.py")
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(update_script)
            
            # 启动更新进程并退出当前进程
            console.print("[info]正在启动更新进程...[/]")
            console.print("[info]请稍后重新运行CLI以使用新版本[/]")
            
            subprocess.Popen([
                sys.executable, script_path
            ], creationflags=subprocess.CREATE_NEW_CONSOLE)
            
            return True
        else:
            # 非Windows平台
            success, stdout, stderr = self._run_pip_command_with_output(
                ["install", "--upgrade", package_spec],
                f"更新 ErisPulse SDK {f'到 {target_version}' if target_version else '到最新版本'}"
            )
            
            if success:
                new_version = target_version or "最新版本"
                console.print(Panel(
                    f"[success]ErisPulse SDK 更新成功[/]\n"
                    f"  当前版本: [bold]{current_version}[/]\n"
                    f"  更新版本: [bold]{new_version}[/]\n\n"
                    f"[dim]{stdout}[/]",
                    title="更新完成",
                    border_style="success"
                ))
                
                if not target_version:
                    console.print("[info]请重新启动CLI以使用新版本[/]")
            else:
                console.print(Panel(
                    f"[error]ErisPulse SDK 更新失败[/]\n\n"
                    f"[dim]{stderr}[/]",
                    title="更新失败",
                    border_style="error"
                ))
                
            return success

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
        处理热重载逻辑
        :param event: 文件系统事件
        :param reason: 重载原因
        """
        from ErisPulse.Core import adapter, logger
        # 在重载前确保所有适配器正确停止
        try:
            # 检查适配器是否正在运行
            if hasattr(adapter, '_started_instances') and adapter._started_instances:
                logger.info("正在停止适配器...")
                # 创建新的事件循环来运行异步停止操作
                import asyncio
                import threading
                
                # 如果在主线程中
                if threading.current_thread() is threading.main_thread():
                    try:
                        # 尝试获取当前事件循环
                        loop = asyncio.get_running_loop()
                        # 在新线程中运行适配器停止
                        stop_thread = threading.Thread(target=lambda: asyncio.run(adapter.shutdown()))
                        stop_thread.start()
                        stop_thread.join(timeout=10)  # 最多等待10秒
                    except RuntimeError:
                        # 没有运行中的事件循环
                        asyncio.run(adapter.shutdown())
                else:
                    # 在非主线程中，创建新的事件循环
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    new_loop.run_until_complete(adapter.shutdown())
                
                logger.info("适配器已停止")
        except Exception as e:
            logger.warning(f"停止适配器时出错: {e}")
        
        # 原有的重载逻辑
        logger.info(f"检测到文件变更 ({reason})，正在重启...")
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
            help='安装模块/适配器包（支持多个，用空格分隔）'
        )
        install_parser.add_argument(
            'package',
            nargs='+',  # 改为接受多个参数
            help='要安装的包名或模块/适配器简称（可指定多个）'
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
            help='卸载模块/适配器包（支持多个，用空格分隔）'
        )
        uninstall_parser.add_argument(
            'package',
            nargs='+',  # 改为接受多个参数
            help='要卸载的包名（可指定多个）'
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
            help='升级组件（支持多个，用空格分隔）'
        )
        upgrade_parser.add_argument(
            'package',
            nargs='*',  # 改为接受可选的多个参数
            help='要升级的包名 (可选，不指定则升级所有)'
        )
        upgrade_parser.add_argument(
            '--force', '-f',
            action='store_true',
            help='跳过确认直接升级'
        )
        upgrade_parser.add_argument(
            '--pre',
            action='store_true',
            help='包含预发布版本'
        )
        
        # 搜索命令
        search_parser = subparsers.add_parser(
            'search',
            help='搜索模块/适配器包'
        )
        search_parser.add_argument(
            'query',
            help='搜索关键词'
        )
        search_parser.add_argument(
            '--installed', '-i',
            action='store_true',
            help='仅搜索已安装的包'
        )
        search_parser.add_argument(
            '--remote', '-r',
            action='store_true',
            help='仅搜索远程包'
        )
        
        # 自更新命令
        self_update_parser = subparsers.add_parser(
            'self-update',
            help='更新ErisPulse SDK本身'
        )
        self_update_parser.add_argument(
            'version',
            nargs='?',
            help='要更新到的版本号 (可选，默认为最新版本)'
        )
        self_update_parser.add_argument(
            '--pre',
            action='store_true',
            help='包含预发布版本'
        )
        self_update_parser.add_argument(
            '--force', '-f',
            action='store_true',
            help='强制更新，即使版本相同'
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
        解析简称到完整包名（大小写不敏感）
        
        :param short_name: 模块/适配器简称
        :return: 完整包名，未找到返回None
        """
        normalized_name = self.package_manager._normalize_name(short_name)
        remote_packages = asyncio.run(self.package_manager.get_remote_packages())
        
        # 检查模块
        for name, info in remote_packages["modules"].items():
            if self.package_manager._normalize_name(name) == normalized_name:
                return info["package"]
                
        # 检查适配器
        for name, info in remote_packages["adapters"].items():
            if self.package_manager._normalize_name(name) == normalized_name:
                return info["package"]
                
        return None
    
    def _print_search_results(self, query: str, results: Dict[str, List[Dict[str, str]]]):
        """
        打印搜索结果
        
        :param query: 搜索关键词
        :param results: 搜索结果
        """
        if not results["installed"] and not results["remote"]:
            console.print(f"[info]未找到与 '[bold]{query}[/]' 匹配的包[/]")
            return

        # 打印已安装的包
        if results["installed"]:
            table = Table(
                title="已安装的包",
                box=SIMPLE,
                header_style="info"
            )
            table.add_column("类型")
            table.add_column("名称")
            table.add_column("包名")
            table.add_column("版本")
            table.add_column("描述")
            
            for item in results["installed"]:
                table.add_row(
                    item["type"],
                    item["name"],
                    item["package"],
                    item["version"],
                    item["summary"]
                )
            
            console.print(table)
        
        # 打印远程包
        if results["remote"]:
            table = Table(
                title="远程包",
                box=SIMPLE,
                header_style="info"
            )
            table.add_column("类型")
            table.add_column("名称")
            table.add_column("包名")
            table.add_column("版本")
            table.add_column("描述")
            
            for item in results["remote"]:
                table.add_row(
                    item["type"],
                    item["name"],
                    item["package"],
                    item["version"],
                    item["summary"]
                )
            
            console.print(table)
    
    def _print_version_list(self, versions: List[Dict[str, Any]], include_pre: bool = False):
        """
        打印版本列表
        
        :param versions: 版本信息列表
        :param include_pre: 是否包含预发布版本
        """
        if not versions:
            console.print("[info]未找到可用版本[/]")
            return
        
        table = Table(
            title="可用版本",
            box=SIMPLE,
            header_style="info"
        )
        table.add_column("序号")
        table.add_column("版本")
        table.add_column("类型")
        table.add_column("上传时间")
        
        displayed = 0
        version_list = []
        for version_info in versions:
            # 如果不包含预发布版本，则跳过预发布版本
            if not include_pre and version_info["pre_release"]:
                continue
                
            version_list.append(version_info)
            version_type = "[yellow]预发布[/]" if version_info["pre_release"] else "[green]稳定版[/]"
            table.add_row(
                str(displayed + 1),
                version_info["version"],
                version_type,
                version_info["uploaded"][:10] if version_info["uploaded"] else "未知"
            )
            displayed += 1
            
            # 只显示前10个版本
            if displayed >= 10:
                break
        
        if displayed == 0:
            console.print("[info]没有找到符合条件的版本[/]")
        else:
            console.print(table)
        return version_list
    
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
                success = self.package_manager.install_package(
                    args.package,  # 现在是列表
                    upgrade=args.upgrade,
                    pre=args.pre
                )
                if not success:
                    sys.exit(1)
                    
            elif args.command == "uninstall":
                success = self.package_manager.uninstall_package(args.package)  # 现在是列表
                if not success:
                    sys.exit(1)
                    
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
                    success = self.package_manager.upgrade_package(
                        args.package,  # 现在是列表
                        pre=args.pre
                    )
                    if not success:
                        sys.exit(1)
                else:
                    if args.force or Confirm.ask("确定要升级所有ErisPulse组件吗？", default=False):
                        success = self.package_manager.upgrade_all()
                        if not success:
                            sys.exit(1)
                            
            elif args.command == "search":
                results = self.package_manager.search_package(args.query)
                
                # 根据选项过滤结果
                if args.installed:
                    results["remote"] = []
                elif args.remote:
                    results["installed"] = []
                    
                self._print_search_results(args.query, results)
                    
            elif args.command == "self-update":
                current_version = self.package_manager.get_installed_version()
                console.print(Panel(
                    f"[title]ErisPulse SDK 自更新[/]\n"
                    f"当前版本: [bold]{current_version}[/]",
                    title_align="left"
                ))
                
                # 获取可用版本
                with console.status("[bold green]正在获取版本信息...", spinner="dots"):
                    versions = asyncio.run(self.package_manager.get_pypi_versions())
                
                if not versions:
                    console.print("[error]无法获取版本信息[/]")
                    sys.exit(1)
                
                # 交互式选择更新选项
                if not args.version:
                    # 显示最新版本
                    stable_versions = [v for v in versions if not v["pre_release"]]
                    pre_versions = [v for v in versions if v["pre_release"]]
                    
                    latest_stable = stable_versions[0] if stable_versions else None
                    latest_pre = pre_versions[0] if pre_versions and args.pre else None
                    
                    choices = []
                    choice_versions = {}
                    choice_index = {}
                    
                    if latest_stable:
                        choice = f"最新稳定版 ({latest_stable['version']})"
                        choices.append(choice)
                        choice_versions[choice] = latest_stable['version']
                        choice_index[len(choices)] = choice
                        
                    if args.pre and latest_pre:
                        choice = f"最新预发布版 ({latest_pre['version']})"
                        choices.append(choice)
                        choice_versions[choice] = latest_pre['version']
                        choice_index[len(choices)] = choice
                        
                    # 添加其他选项
                    choices.append("查看所有版本")
                    choices.append("手动指定版本")
                    choices.append("取消")
                    
                    # 创建数字索引映射
                    for i, choice in enumerate(choices, 1):
                        choice_index[i] = choice
                    
                    # 显示选项
                    console.print("\n[info]请选择更新选项:[/]")
                    for i, choice in enumerate(choices, 1):
                        console.print(f"  {i}. {choice}")
                    
                    while True:
                        try:
                            selected_input = Prompt.ask(
                                "请输入选项编号",
                                default="1"
                            )
                            
                            if selected_input.isdigit():
                                selected_index = int(selected_input)
                                if selected_index in choice_index:
                                    selected = choice_index[selected_index]
                                    break
                                else:
                                    console.print("[warning]请输入有效的选项编号[/]")
                            else:
                                # 检查是否是选项文本
                                if selected_input in choices:
                                    selected = selected_input
                                    break
                                else:
                                    console.print("[warning]请输入有效的选项编号或选项名称[/]")
                        except KeyboardInterrupt:
                            console.print("\n[info]操作已取消[/]")
                            sys.exit(0)
                    
                    if selected == "取消":
                        console.print("[info]操作已取消[/]")
                        sys.exit(0)
                    elif selected == "手动指定版本":
                        target_version = Prompt.ask("请输入要更新到的版本号")
                        if not any(v['version'] == target_version for v in versions):
                            console.print(f"[warning]版本 {target_version} 可能不存在[/]")
                            if not Confirm.ask("是否继续？", default=False):
                                sys.exit(0)
                    elif selected == "查看所有版本":
                        version_list = self._print_version_list(versions, include_pre=args.pre)
                        if not version_list:
                            console.print("[info]没有可用版本[/]")
                            sys.exit(0)
                            
                        # 显示版本选择
                        console.print("\n[info]请选择要更新到的版本:[/]")
                        while True:
                            try:
                                version_input = Prompt.ask("请输入版本序号或版本号")
                                if version_input.isdigit():
                                    version_index = int(version_input)
                                    if 1 <= version_index <= len(version_list):
                                        target_version = version_list[version_index - 1]['version']
                                        break
                                    else:
                                        console.print("[warning]请输入有效的版本序号[/]")
                                else:
                                    # 检查是否是有效的版本号
                                    if any(v['version'] == version_input for v in version_list):
                                        target_version = version_input
                                        break
                                    else:
                                        console.print("[warning]请输入有效的版本序号或版本号[/]")
                            except KeyboardInterrupt:
                                console.print("\n[info]操作已取消[/]")
                                sys.exit(0)
                    else:
                        target_version = choice_versions[selected]
                else:
                    target_version = args.version
                
                # 确认更新
                if target_version == current_version and not args.force:
                    console.print(f"[info]当前已是目标版本 [bold]{current_version}[/][/]")
                    sys.exit(0)
                elif not args.force:
                    if not Confirm.ask(f"确认将ErisPulse SDK从 [bold]{current_version}[/] 更新到 [bold]{target_version}[/] 吗？", default=False):
                        console.print("[info]操作已取消[/]")
                        sys.exit(0)
                
                # 执行更新
                success = self.package_manager.update_self(target_version, args.force)
                if not success:
                    sys.exit(1)
                    
            elif args.command == "run":
                script = args.script or "main.py"
                if not os.path.exists(script):
                    console.print(f"[error]找不到指定文件: [path]{script}[/][/]")
                    return
                    
                reload_mode = args.reload and not args.no_reload
                self._setup_watchdog(script, reload_mode)
                
                try:
                    while True:
                        time.sleep(0.5)
                except KeyboardInterrupt:
                    console.print("\n[info]正在安全关闭...[/]")
                    self._cleanup_adapters()
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
    
    def _cleanup_adapters(self):
        """
        清理适配器资源
        """
        from ErisPulse import adapter, logger
        try:
            import asyncio
            import threading
            
            # 检查是否有正在运行的适配器
            if (hasattr(adapter, '_started_instances') and 
                adapter._started_instances):
                
                logger.info("正在停止所有适配器...")
                
                if threading.current_thread() is threading.main_thread():
                    try:
                        loop = asyncio.get_running_loop()
                        if loop.is_running():
                            # 在新线程中运行
                            stop_thread = threading.Thread(
                                target=lambda: asyncio.run(adapter.shutdown())
                            )
                            stop_thread.start()
                            stop_thread.join(timeout=5)
                        else:
                            asyncio.run(adapter.shutdown())
                    except RuntimeError:
                        asyncio.run(adapter.shutdown())
                else:
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    new_loop.run_until_complete(adapter.shutdown())
                    
                logger.info("适配器已全部停止")
        except Exception as e:
            logger.error(f"清理适配器资源时出错: {e}")

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