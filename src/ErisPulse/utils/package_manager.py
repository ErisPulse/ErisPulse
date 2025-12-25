"""
ErisPulse SDK 包管理器

提供包安装、卸载、升级和查询功能
"""

import os
import asyncio
import importlib.metadata
import json
import subprocess
import sys
import time
from typing import List, Dict, Tuple, Optional, Any

from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn
from rich.prompt import Confirm

from .console import console

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
            from ErisPulse.Core import module as module_manager
            return module_manager.is_enabled(module_name)
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
                "以下包升级失败:\n" + "\n".join(f"  - [error]{pkg}[/]" for pkg in failed),
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