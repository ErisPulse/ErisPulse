"""
ErisPulse SDK 包管理器

提供包安装、卸载、升级和查询功能
"""

import os
import re
import asyncio
import json
import ssl
import subprocess
import sys
import time
import urllib.request
import urllib.error
from typing import List, Dict, Tuple, Optional, Any

from rich.panel import Panel
from rich.prompt import Confirm

from ..console import console
from ...finders import ModuleFinder, AdapterFinder


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
        self._cache = {}
        self._cache_time = {}
        self._pypi_cache = {}  # PyPI版本缓存
        self._pypi_cache_time = {}  # PyPI版本缓存时间
        self._module_finder = ModuleFinder()
        self._adapter_finder = AdapterFinder()
        self._system_proxy = None
        self._system_proxy_checked = False

    @staticmethod
    def _parse_size(size_str: str) -> float:
        units = {'B': 1, 'KB': 1024, 'MB': 1024 ** 2, 'GB': 1024 ** 3, 'TB': 1024 ** 4}
        match = re.match(r'(\d+(?:\.\d+)?)\s*([KMGT]?B)', size_str, re.IGNORECASE)
        if match:
            value = float(match.group(1))
            unit = match.group(2).upper()
            return value * units.get(unit, 1)
        return 0

    def _get_system_proxy(self) -> Optional[Dict[str, str]]:
        if self._system_proxy_checked:
            return self._system_proxy

        self._system_proxy_checked = True
        result = {}

        for key, env_var in (("http", "HTTP_PROXY"), ("https", "HTTPS_PROXY"), ("https", "https_proxy"), ("http", "http_proxy")):
            val = os.environ.get(env_var) or os.environ.get("ALL_PROXY")
            if val and key not in result:
                result[key] = val

        if result:
            self._system_proxy = result
            return result

        if sys.platform == "win32":
            try:
                import winreg
                key_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as reg_key:
                    proxy_enable, _ = winreg.QueryValueEx(reg_key, "ProxyEnable")
                    if proxy_enable:
                        proxy_server, _ = winreg.QueryValueEx(reg_key, "ProxyServer")
                        if proxy_server:
                            self._system_proxy = self._parse_windows_proxy(proxy_server)
                            return self._system_proxy
            except Exception:
                pass

        self._system_proxy = None
        return None

    @staticmethod
    def _parse_windows_proxy(proxy_server: str) -> Dict[str, str]:
        result = {}
        if "=" in proxy_server:
            for part in proxy_server.split(";"):
                part = part.strip()
                if "=" in part:
                    proto, addr = part.split("=", 1)
                    proto = proto.strip().lower()
                    addr = addr.strip()
                    if not addr.startswith("http"):
                        addr = f"http://{addr}"
                    if proto in ("http", "https"):
                        result[proto] = addr
        else:
            addr = proxy_server.strip()
            if not addr.startswith("http"):
                addr = f"http://{addr}"
            result["http"] = addr
            result["https"] = addr
        return result

    def _get_proxy_for_url(self, url: str) -> Optional[str]:
        proxies = self._get_system_proxy()
        if not proxies:
            return None
        if url.startswith("https://") and "https" in proxies:
            return proxies["https"]
        if url.startswith("http://") and "http" in proxies:
            return proxies["http"]
        return proxies.get("https") or proxies.get("http")

    def _build_subprocess_env(self) -> Dict[str, str]:
        env = os.environ.copy()
        proxies = self._get_system_proxy()
        if proxies:
            if "http" in proxies and not env.get("HTTP_PROXY"):
                env["HTTP_PROXY"] = proxies["http"]
            if "https" in proxies and not env.get("HTTPS_PROXY"):
                env["HTTPS_PROXY"] = proxies["https"]
        return env

    def _http_get(self, url: str, timeout: int = 15) -> Optional[str]:
        proxy = self._get_proxy_for_url(url)

        for verify_ssl in (True, False):
            handlers = []
            if proxy:
                handlers.append(urllib.request.ProxyHandler({
                    'http': proxy,
                    'https': proxy,
                }))
            if not verify_ssl:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                handlers.append(urllib.request.HTTPSHandler(context=ctx))

            opener = urllib.request.build_opener(*handlers)
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'ErisPulse/CLI'})
                resp = opener.open(req, timeout=timeout)
                return resp.read().decode('utf-8')
            except Exception:
                if verify_ssl and proxy:
                    continue
                return None
        return None

    def _fetch_remote_packages_sync(self, url: str) -> Optional[dict]:
        text = self._http_get(url)
        if text:
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                pass
        return None

    async def _fetch_remote_packages(self, url: str) -> Optional[dict]:
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, self._fetch_remote_packages_sync, url)
        except Exception:
            return None

    async def get_remote_packages(self, force_refresh: bool = False) -> dict:
        cache_key = "remote_packages"
        if not force_refresh and cache_key in self._cache:
            if time.time() - self._cache_time[cache_key] < self.CACHE_EXPIRY:
                return self._cache[cache_key]

        result = {"modules": {}, "adapters": {}}

        for url in self.REMOTE_SOURCES:
            data = await self._fetch_remote_packages(url)
            if data:
                result["modules"].update(data.get("modules", {}))
                result["adapters"].update(data.get("adapters", {}))
                break

        if not result["modules"] and not result["adapters"]:
            console.print("[warning]无法获取远程包列表，请检查网络连接或代理设置[/]")
            proxy = self._get_system_proxy()
            if proxy:
                console.print(f"[dim]  检测到代理: {proxy}[/]")
            else:
                console.print("[dim]  未检测到系统代理，如需使用代理请设置 HTTPS_PROXY 环境变量[/]")

        self._cache[cache_key] = result
        self._cache_time[cache_key] = time.time()

        return result

    def get_installed_packages(self) -> Dict[str, Dict[str, Dict[str, str]]]:
        packages = {
            "modules": {},
            "adapters": {}
        }

        try:
            module_entries = self._module_finder.find_all()
            for entry in module_entries:
                if hasattr(entry, 'dist') and entry.dist:
                    packages["modules"][entry.name] = {
                        "package": entry.dist.name,
                        "version": entry.dist.version,
                        "summary": entry.dist.metadata.get("Summary", ""),
                        "enabled": self._is_module_enabled(entry.name)
                    }

            adapter_entries = self._adapter_finder.find_all()
            for entry in adapter_entries:
                if hasattr(entry, 'dist') and entry.dist:
                    packages["adapters"][entry.name] = {
                        "package": entry.dist.name,
                        "version": entry.dist.version,
                        "summary": entry.dist.metadata.get("Summary", "")
                    }

        except Exception as e:
            console.print(f"[error] 获取已安装包信息失败: {e}[/]")
            import traceback
            console.print(traceback.format_exc())

        return packages

    def _is_module_enabled(self, module_name: str) -> bool:
        try:
            from ErisPulse.Core import module as module_manager
            return module_manager.is_enabled(module_name)
        except ImportError:
            return True
        except Exception:
            return False

    def _normalize_name(self, name: str) -> str:
        return name.lower().strip()

    async def _find_package_by_alias(self, alias: str) -> Optional[str]:
        normalized_alias = self._normalize_name(alias)
        remote_packages = await self.get_remote_packages()

        installed_package = self._find_installed_package_by_name(alias)
        if installed_package:
            return installed_package

        for name, info in remote_packages["modules"].items():
            if self._normalize_name(name) == normalized_alias:
                return info["package"]
            if self._normalize_name(info["package"]) == normalized_alias:
                return info["package"]

        for name, info in remote_packages["adapters"].items():
            if self._normalize_name(name) == normalized_alias:
                return info["package"]
            if self._normalize_name(info["package"]) == normalized_alias:
                return info["package"]

        return None

    def _find_installed_package_by_name(self, name: str) -> Optional[str]:
        normalized_name = self._normalize_name(name)
        installed = self.get_installed_packages()

        for module_info in installed["modules"].values():
            if self._normalize_name(module_info["package"]) == normalized_name:
                return module_info["package"]

        for adapter_info in installed["adapters"].values():
            if self._normalize_name(adapter_info["package"]) == normalized_name:
                return adapter_info["package"]

        return None

    async def check_package_updates(self) -> Dict[str, Tuple[str, str]]:
        installed = self.get_installed_packages()
        remote_packages = await self.get_remote_packages()

        updates = {}

        remote_index = {}
        for pkg_type in ["modules", "adapters"]:
            for name, info in remote_packages[pkg_type].items():
                remote_index[info["package"]] = info["version"]

        for pkg_type in ["modules", "adapters"]:
            for entry_name, pkg_info in installed[pkg_type].items():
                current_version = pkg_info["version"]
                package_name = pkg_info["package"]

                if package_name in remote_index:
                    remote_version = remote_index[package_name]
                    comparison = self._compare_versions(remote_version, current_version)
                    if comparison > 0:
                        updates[package_name] = (current_version, remote_version)
                else:
                    remote_version = await self._get_pypi_package_version(package_name)
                    if remote_version and self._compare_versions(remote_version, current_version) > 0:
                        updates[package_name] = (current_version, remote_version)

        return updates

    def _get_pypi_version_sync(self, package_name: str) -> Optional[str]:
        url = f"https://pypi.org/pypi/{package_name}/json"
        text = self._http_get(url)
        if text:
            try:
                data = json.loads(text)
                return data["info"]["version"]
            except (json.JSONDecodeError, KeyError):
                pass
        return None

    async def _get_pypi_package_version(self, package_name: str, force_refresh: bool = False) -> Optional[str]:
        cache_key = package_name.lower()
        if not force_refresh and cache_key in self._pypi_cache:
            if time.time() - self._pypi_cache_time[cache_key] < self.CACHE_EXPIRY:
                return self._pypi_cache[cache_key]

        loop = asyncio.get_event_loop()
        try:
            version = await loop.run_in_executor(None, self._get_pypi_version_sync, package_name)
        except Exception:
            version = None

        if version:
            self._pypi_cache[cache_key] = version
            self._pypi_cache_time[cache_key] = time.time()
        return version

    def _run_pip_command_with_output(self, args: List[str], description: str) -> bool:
        env = self._build_subprocess_env()

        proxies = self._get_system_proxy()
        proxy_hint = ""
        if proxies:
            proxy_hint = f" [dim](proxy: {proxies.get('https', proxies.get('http', ''))})[/]"

        console.print(f"\n[bold blue]⚙ {description}[/]{proxy_hint}")
        console.print("[dim]─────────────────────────────────────────────────[/]")

        try:
            process = subprocess.Popen(
                [sys.executable, "-m", "pip"] + args,
                env=env,
                stdout=sys.stdout,
                stderr=sys.stderr,
            )
        except Exception as e:
            console.print(f"[error]启动pip失败: {e}[/]")
            return False

        try:
            while process.poll() is None:
                time.sleep(0.5)
        except KeyboardInterrupt:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            console.print("\n[warning]操作被用户中断[/]")
            return False

        console.print("[dim]─────────────────────────────────────────────────[/]")

        return process.returncode == 0

    def _compare_versions(self, version1: str, version2: str) -> int:
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
            if version1 > version2:
                return 1
            elif version1 < version2:
                return -1
            else:
                return 0

    def _check_sdk_compatibility(self, min_sdk_version: str) -> Tuple[bool, str]:
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
        normalized_name = self._normalize_name(package_name)
        remote_packages = await self.get_remote_packages()

        for name, info in remote_packages["modules"].items():
            if self._normalize_name(name) == normalized_name:
                return info

        for name, info in remote_packages["adapters"].items():
            if self._normalize_name(name) == normalized_name:
                return info

        return None

    def install_package(self, package_names: List[str], upgrade: bool = False, pre: bool = False, extra_pip_args: List[str] = None) -> bool:
        all_success = True

        for package_name in package_names:
            actual_package = asyncio.run(self._find_package_by_alias(package_name))

            if actual_package:
                console.print(f"[info]找到别名映射: [bold]{package_name}[/] → [package]{actual_package}[/][/]")
                current_package_name = actual_package
            else:
                console.print(f"[info]未找到别名，将直接安装: [package]{package_name}[/][/]")
                current_package_name = package_name

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

            cmd = ["install"]
            if upgrade:
                cmd.append("--upgrade")
            if pre:
                cmd.append("--pre")
            if extra_pip_args:
                cmd.extend(extra_pip_args)
            cmd.append(current_package_name)

            success = self._run_pip_command_with_output(cmd, f"安装 {current_package_name}")

            if success:
                console.print(f"[success]✔ 包 {current_package_name} 安装成功[/]")
            else:
                console.print(f"[error]✘ 包 {current_package_name} 安装失败[/]")
                all_success = False

        return all_success

    def install_direct(self, pip_args: List[str], description: str = "pip install") -> bool:
        cmd = ["install"] + pip_args
        success = self._run_pip_command_with_output(cmd, description)

        if success:
            console.print(f"[success]✔ {description} 成功[/]")
        else:
            console.print(f"[error]✘ {description} 失败[/]")

        return success

    def uninstall_package(self, package_names: List[str], skip_confirm: bool = False) -> bool:
        all_success = True

        packages_to_uninstall = []

        for package_name in package_names:
            actual_package = asyncio.run(self._find_package_by_alias(package_name))

            if actual_package:
                console.print(f"[info]  别名映射: [bold]{package_name}[/] → [package]{actual_package}[/][/]")
                packages_to_uninstall.append(actual_package)
            else:
                installed_package = self._find_installed_package_by_name(package_name)
                if installed_package:
                    package_name = installed_package
                    console.print(f"[info]  找到已安装包: [bold]{package_name}[/][/]")
                    packages_to_uninstall.append(package_name)
                else:
                    console.print(f"[warning]  未找到别名，将尝试直接卸载: [package]{package_name}[/][/]")
                    packages_to_uninstall.append(package_name)

        if not skip_confirm:
            package_list = "\n".join([f"  - [package]{pkg}[/]" for pkg in packages_to_uninstall])
            if not Confirm.ask(f"确认卸载以下包吗？\n{package_list}", default=False):
                console.print("[info]  操作已取消[/]")
                return False

        for package_name in packages_to_uninstall:
            success = self._run_pip_command_with_output(
                ["uninstall", "-y", package_name],
                f"卸载 {package_name}"
            )

            if success:
                console.print(f"[success]✔ 包 {package_name} 卸载成功[/]")
            else:
                console.print(f"[error]✘ 包 {package_name} 卸载失败[/]")
                all_success = False

        return all_success

    def upgrade_all(self) -> bool:
        updates = asyncio.run(self.check_package_updates())

        if not updates:
            console.print("[success]所有ErisPulse包已是最新版本[/]")
            return True

        console.print(Panel(
            f"找到 [bold]{len(updates)}[/] 个可升级的包:\n" +
            "\n".join(
                f"  - [package]{pkg}[/] [dim]{current_ver}[/] → [success]{new_ver}[/]"
                for pkg, (current_ver, new_ver) in updates.items()
            ),
            title="升级列表"
        ))

        if not Confirm.ask("确认升级以上包吗？", default=False):
            console.print("[info]操作已取消[/]")
            return False

        results = {}
        for pkg in sorted(updates.keys()):
            console.print(f"\n[info]正在升级 [package]{pkg}[/]...")
            results[pkg] = self.install_package([pkg], upgrade=True)

        success_count = sum(1 for success in results.values() if success)
        console.print(f"\n[success]升级完成: {success_count}/{len(results)} 个包成功[/]")

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
        all_success = True

        for package_name in package_names:
            actual_package = asyncio.run(self._find_package_by_alias(package_name))

            if actual_package:
                console.print(f"[info]找到包: [package]{actual_package}[/][/]")
                current_package_name = actual_package
            else:
                current_package_name = package_name

            installed = self.get_installed_packages()
            current_version = None
            for pkg_type in ["modules", "adapters"]:
                for pkg_info in installed[pkg_type].values():
                    if pkg_info["package"] == current_package_name:
                        current_version = pkg_info["version"]
                        break
                if current_version:
                    break

            remote_version = asyncio.run(self._get_pypi_package_version(current_package_name))

            if current_version:
                if remote_version:
                    comparison = self._compare_versions(remote_version, current_version)
                    if comparison <= 0:
                        console.print(f"[success]{current_package_name} 已是最新版本 ({current_version})[/]")
                        continue
                    else:
                        console.print(f"[info]{current_package_name}: {current_version} → {remote_version}[/]")
                else:
                    console.print(f"[info]{current_package_name}: 当前版本 {current_version}[/]")
            else:
                console.print(f"[warning]未找到 {current_package_name} 的安装信息[/]")

            package_info = asyncio.run(self._get_package_info(current_package_name))
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

            cmd = ["install", "--upgrade"]
            if pre:
                cmd.append("--pre")
            cmd.append(current_package_name)

            success = self._run_pip_command_with_output(cmd, f"升级 {current_package_name}")

            if success:
                console.print(f"[success]✔ 包 {current_package_name} 升级成功[/]")
            else:
                console.print(f"[error]✘ 包 {current_package_name} 升级失败[/]")
                all_success = False

        return all_success

    def search_package(self, query: str) -> Dict[str, List[Dict[str, str]]]:
        normalized_query = self._normalize_name(query)
        results = {"installed": [], "remote": []}

        installed = self.get_installed_packages()
        for pkg_type in ["modules", "adapters"]:
            for name, info in installed[pkg_type].items():
                if (normalized_query in self._normalize_name(name) or
                    normalized_query in self._normalize_name(info["package"]) or
                    normalized_query in self._normalize_name(info["summary"])):
                    results["installed"].append({
                        "type": pkg_type[:-1] if pkg_type.endswith("s") else pkg_type,
                        "name": name,
                        "package": info["package"],
                        "version": info["version"],
                        "summary": info["summary"]
                    })

        remote = asyncio.run(self.get_remote_packages())
        for pkg_type in ["modules", "adapters"]:
            for name, info in remote[pkg_type].items():
                if (normalized_query in self._normalize_name(name) or
                    normalized_query in self._normalize_name(info["package"]) or
                    normalized_query in self._normalize_name(info.get("description", "")) or
                    normalized_query in self._normalize_name(info.get("summary", ""))):
                    results["remote"].append({
                        "type": pkg_type[:-1] if pkg_type.endswith("s") else pkg_type,
                        "name": name,
                        "package": info["package"],
                        "version": info["version"],
                        "summary": info.get("description", info.get("summary", ""))
                    })

        return results

    def get_installed_version(self) -> str:
        try:
            from ErisPulse import __version__
            return __version__
        except ImportError:
            return "unknown"

    def _get_pypi_versions_sync(self) -> List[Dict[str, Any]]:
        from packaging import version as comparison

        url = "https://pypi.org/pypi/ErisPulse/json"
        text = self._http_get(url)
        if not text:
            return []
        try:
            data = json.loads(text)
            versions = []
            for version_str, releases in data["releases"].items():
                if releases:
                    release_info = {
                        "version": version_str,
                        "uploaded": releases[0].get("upload_time_iso_8601", ""),
                        "pre_release": self._is_pre_release(version_str)
                    }
                    versions.append(release_info)
            versions.sort(key=lambda x: comparison.parse(x["version"]), reverse=True)
            return versions
        except (json.JSONDecodeError, KeyError, Exception):
            return []

    async def get_pypi_versions(self) -> List[Dict[str, Any]]:
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, self._get_pypi_versions_sync)
        except Exception:
            console.print("[error]获取PyPI版本信息失败[/]")
            return []

    def _is_pre_release(self, version: str) -> bool:
        pre_release_pattern = re.compile(r'(a|b|rc|dev|alpha|beta)\d*', re.IGNORECASE)
        return bool(pre_release_pattern.search(version))

    def update_self(self, target_version: str = None, force: bool = False) -> bool:
        current_version = self.get_installed_version()

        if target_version and target_version == current_version and not force:
            console.print(f"[info]当前已是目标版本 [bold]{current_version}[/][/]")
            return True

        package_spec = "ErisPulse"
        if target_version:
            if not re.match(r'^[a-zA-Z0-9._+\-]+$', target_version):
                console.print(f"[error]无效的版本号: {target_version}[/]")
                return False
            package_spec += f"=={target_version}"

        if sys.platform == "win32":
            update_script = f"""
import time
import subprocess
import sys
import os

time.sleep(2)

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

try:
    os.remove(__file__)
except:
    pass
"""
            import tempfile
            script_path = os.path.join(tempfile.gettempdir(), "epsdk_update.py")
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(update_script)

            console.print("[info]正在启动更新进程...[/]")
            console.print("[info]请稍后重新运行CLI以使用新版本[/]")

            subprocess.Popen([
                sys.executable, script_path
            ], creationflags=subprocess.CREATE_NEW_CONSOLE)

            return True
        else:
            success = self._run_pip_command_with_output(
                ["install", "--upgrade", package_spec],
                f"更新 ErisPulse SDK {f'到 {target_version}' if target_version else '到最新版本'}"
            )

            if success:
                new_version = target_version or "最新版本"
                console.print(f"[success]✔ ErisPulse SDK 更新成功: {current_version} → {new_version}[/]")
                if not target_version:
                    console.print("[info]请重新启动CLI以使用新版本[/]")
            else:
                console.print(f"[error]✘ ErisPulse SDK 更新失败[/]")

            return success
