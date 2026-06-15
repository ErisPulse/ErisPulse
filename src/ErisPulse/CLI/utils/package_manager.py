"""
ErisPulse SDK 包管理器

提供包安装、卸载、升级和查询功能
"""

import asyncio
import json
import os
import re
import shutil
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

from rich.panel import Panel
from rich.prompt import Confirm

from ...finders import AdapterFinder, ModuleFinder
from ..console import console
from ..i18n import i18n

# 版本号解析正则：支持 release 段 + 可选预发布后缀 (dev/a/alpha/b/beta/rc)
# 例如 2.5.0-dev.1 / 2.5.0a1 / 2.4.5 均可解析
_VERSION_RE = re.compile(
    r"^\s*v?(?P<release>\d+(?:\.\d+)*)"
    r"(?:[-._]?(?P<pre>dev|alpha|beta|rc|a|b|c|pre)[-._]?(?P<num>\d+))?",
    re.IGNORECASE,
)
# 预发布类型排序权重：正式版 > rc > beta > alpha > dev
_PRE_RELEASE_RANK = {
    "dev": 0,
    "alpha": 1,
    "a": 1,
    "beta": 2,
    "b": 2,
    "rc": 3,
    "c": 3,
    "pre": 3,
}


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
        "https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/packages.json",
    ]

    CACHE_EXPIRY = 3600  # 1小时缓存

    @staticmethod
    def _sanitize_proxy_url(url: str) -> str:
        """
        对代理URL中的密码进行脱敏处理

        :param url: [str] 原始代理URL
        :return: [str] 密码被替换为 *** 的脱敏URL
        """
        from urllib.parse import urlparse, urlunparse

        try:
            parsed = urlparse(url)
            if parsed.password:
                netloc = f"{parsed.username}:***@{parsed.hostname}"
                if parsed.port:
                    netloc += f":{parsed.port}"
                return urlunparse(parsed._replace(netloc=netloc))
        except Exception:
            pass
        return url

    def __init__(self):
        """初始化包管理器，设置缓存、查找器、代理与 uv 相关状态"""
        self._cache = {}
        self._cache_time = {}
        self._pypi_cache = {}  # PyPI版本缓存
        self._pypi_cache_time = {}  # PyPI版本缓存时间
        self._module_finder = ModuleFinder()
        self._adapter_finder = AdapterFinder()
        self._system_proxy = None
        self._system_proxy_checked = False
        self._uv_command = None  # 缓存的 uv 命令前缀
        self._uv_checked = False  # 是否已检测过 uv
        self.no_uv = False  # 由 CLI 命令设置：是否禁用 uv（--no-uv）

    @staticmethod
    def _parse_size(size_str: str) -> float:
        """
        将带单位的尺寸字符串解析为字节数

        :param size_str: [str] 尺寸字符串，如 "10MB"
        :return: [float] 对应的字节数，无法解析时返回 0
        """
        units = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4}
        match = re.match(r"(\d+(?:\.\d+)?)\s*([KMGT]?B)", size_str, re.IGNORECASE)
        if match:
            value = float(match.group(1))
            unit = match.group(2).upper()
            return value * units.get(unit, 1)
        return 0

    def _get_system_proxy(self) -> Optional[Dict[str, str]]:
        """
        获取系统代理配置，优先读取环境变量，其次读取Windows注册表

        :return: [Optional[Dict[str, str]]] 代理配置字典，无代理时返回 None
        """
        if self._system_proxy_checked:
            return self._system_proxy

        self._system_proxy_checked = True
        result = {}

        for key, env_var in (
            ("http", "HTTP_PROXY"),
            ("https", "HTTPS_PROXY"),
            ("https", "https_proxy"),
            ("http", "http_proxy"),
        ):
            val = os.environ.get(env_var) or os.environ.get("ALL_PROXY")
            if val and key not in result:
                result[key] = val

        if result:
            self._system_proxy = result
            return result

        if sys.platform == "win32":
            try:
                import winreg

                key_path = (
                    r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
                )
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
        """
        解析Windows注册表中的代理服务器字符串为协议到URL的映射

        :param proxy_server: [str] Windows代理服务器字符串
        :return: [Dict[str, str]] 协议到代理URL的映射
        """
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
        """
        根据URL的协议获取对应的代理地址

        :param url: [str] 目标URL
        :return: [Optional[str]] 对应的代理URL，无匹配代理时返回 None
        """
        proxies = self._get_system_proxy()
        if not proxies:
            return None
        if url.startswith("https://") and "https" in proxies:
            return proxies["https"]
        if url.startswith("http://") and "http" in proxies:
            return proxies["http"]
        return proxies.get("https") or proxies.get("http")

    def _build_subprocess_env(self) -> Dict[str, str]:
        """
        构建子进程环境变量，未设置时注入系统代理配置

        :return: [Dict[str, str]] 包含代理配置的环境变量字典
        """
        env = os.environ.copy()
        proxies = self._get_system_proxy()
        if proxies:
            if "http" in proxies and not env.get("HTTP_PROXY"):
                env["HTTP_PROXY"] = proxies["http"]
            if "https" in proxies and not env.get("HTTPS_PROXY"):
                env["HTTPS_PROXY"] = proxies["https"]
        return env

    def _http_get(self, url: str, timeout: int = 15) -> Optional[str]:
        """
        发起HTTP GET请求并返回响应文本，自动应用系统代理

        :param url: [str] 请求URL
        :param timeout: [int] 超时时间(秒) (默认: 15)
        :return: [Optional[str]] 响应文本，请求失败时返回 None
        """
        proxy = self._get_proxy_for_url(url)

        handlers = []
        if proxy:
            handlers.append(
                urllib.request.ProxyHandler(
                    {
                        "http": proxy,
                        "https": proxy,
                    }
                )
            )

        opener = urllib.request.build_opener(*handlers)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ErisPulse/CLI"})
            resp = opener.open(req, timeout=timeout)
            return resp.read().decode("utf-8")
        except ssl.SSLError as e:
            console.print(f"[error]{i18n.t('cli.package.ssl_error', error=e)}[/]")
            if proxy:
                console.print(f"[dim]{i18n.t('cli.package.ssl_error_proxy_hint')}[/]")
            return None
        except Exception:
            return None

    def _fetch_remote_packages_sync(self, url: str) -> Optional[dict]:
        """
        同步获取并解析远程包列表JSON

        :param url: [str] 远程包列表URL
        :return: [Optional[dict]] 解析后的包列表字典，失败时返回 None
        """
        text = self._http_get(url)
        if text:
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                pass
        return None

    async def _fetch_remote_packages(self, url: str) -> Optional[dict]:
        """
        异步获取远程包列表

        :param url: [str] 远程包列表URL
        :return: [Optional[dict]] 解析后的包列表字典，失败时返回 None
        """
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(
                None, self._fetch_remote_packages_sync, url
            )
        except Exception:
            return None

    async def get_remote_packages(self, force_refresh: bool = False) -> dict:
        """
        获取远程包列表，带缓存机制

        :param force_refresh: [bool] 是否强制刷新缓存 (默认: False)
        :return: [dict] 包含 modules 和 adapters 信息的字典
        """
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
            console.print(f"[warning]{i18n.t('cli.package.fetch_remote_failed')}[/]")
            proxy = self._get_system_proxy()
            if proxy:
                safe_proxy = {k: self._sanitize_proxy_url(v) for k, v in proxy.items()}
                console.print(
                    f"[dim]{i18n.t('cli.package.proxy_detected', proxy=safe_proxy)}[/]"
                )
            else:
                console.print(f"[dim]{i18n.t('cli.package.no_proxy_detected')}[/]")

        self._cache[cache_key] = result
        self._cache_time[cache_key] = time.time()

        return result

    def get_installed_packages(self) -> Dict[str, Dict[str, Dict[str, str]]]:
        """
        获取已安装的模块和适配器信息

        :return: [Dict[str, Dict[str, Dict[str, str]]] 包含 modules 和 adapters 信息的字典
        """
        packages = {"modules": {}, "adapters": {}}

        try:
            module_entries = self._module_finder.find_all()
            for entry in module_entries:
                if hasattr(entry, "dist") and entry.dist:
                    packages["modules"][entry.name] = {
                        "package": entry.dist.name,
                        "version": entry.dist.version,
                        "summary": entry.dist.metadata.get("Summary", ""),
                        "enabled": self._is_module_enabled(entry.name),
                    }

            adapter_entries = self._adapter_finder.find_all()
            for entry in adapter_entries:
                if hasattr(entry, "dist") and entry.dist:
                    packages["adapters"][entry.name] = {
                        "package": entry.dist.name,
                        "version": entry.dist.version,
                        "summary": entry.dist.metadata.get("Summary", ""),
                    }

        except Exception as e:
            console.print(
                f"[error]{i18n.t('cli.package.get_installed_failed', error=e)}[/]"
            )
            import traceback

            console.print(traceback.format_exc())

        return packages

    def _is_module_enabled(self, module_name: str) -> bool:
        """
        检查指定模块是否已启用

        :param module_name: [str] 模块名称
        :return: [bool] 模块已启用返回 True，无法判断时默认返回 True
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
        将名称标准化为小写并去除首尾空白

        :param name: [str] 原始名称
        :return: [str] 标准化后的名称
        """
        return name.lower().strip()

    async def _find_package_by_alias(self, alias: str) -> Optional[str]:
        """
        通过别名查找实际的包名，依次匹配已安装包和远程包

        :param alias: [str] 别名或包名
        :return: [Optional[str]] 实际的包名，未找到时返回 None
        """
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
        """
        在已安装的模块和适配器中按名称查找实际包名

        :param name: [str] 包名或别名
        :return: [Optional[str]] 已安装的实际包名，未找到时返回 None
        """
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
        """
        检查已安装包的可用更新

        :return: [Dict[str, Tuple[str, str]]] 包名到(当前版本, 最新版本)的映射
        """
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
                    if (
                        remote_version
                        and self._compare_versions(remote_version, current_version) > 0
                    ):
                        updates[package_name] = (current_version, remote_version)

        return updates

    def _get_pypi_version_sync(self, package_name: str) -> Optional[str]:
        """
        同步从PyPI获取指定包的最新版本号

        :param package_name: [str] 包名
        :return: [Optional[str]] 最新版本号，失败时返回 None
        """
        url = f"https://pypi.org/pypi/{package_name}/json"
        text = self._http_get(url)
        if text:
            try:
                data = json.loads(text)
                return data["info"]["version"]
            except (json.JSONDecodeError, KeyError):
                pass
        return None

    async def _get_pypi_package_version(
        self, package_name: str, force_refresh: bool = False
    ) -> Optional[str]:
        """
        异步获取指定包的PyPI最新版本，带缓存机制

        :param package_name: [str] 包名
        :param force_refresh: [bool] 是否强制刷新缓存 (默认: False)
        :return: [Optional[str]] 最新版本号，失败时返回 None
        """
        cache_key = package_name.lower()
        if not force_refresh and cache_key in self._pypi_cache:
            if time.time() - self._pypi_cache_time[cache_key] < self.CACHE_EXPIRY:
                return self._pypi_cache[cache_key]

        loop = asyncio.get_event_loop()
        try:
            version = await loop.run_in_executor(
                None, self._get_pypi_version_sync, package_name
            )
        except Exception:
            version = None

        if version:
            self._pypi_cache[cache_key] = version
            self._pypi_cache_time[cache_key] = time.time()
        return version

    def _is_uv_disabled(self) -> bool:
        """是否禁用 uv：CLI --no-uv 优先，其次环境变量 ERISPULSE_NO_UV"""
        if getattr(self, "no_uv", False):
            return True
        return str(os.environ.get("ERISPULSE_NO_UV", "")).lower() in (
            "1",
            "true",
            "yes",
        )

    def _detect_uv(self) -> Optional[List[str]]:
        """
        检测可用的 uv 命令。

        优先使用 PATH 上的独立 uv 二进制（用户可能是全局安装，
        而非作为 pip 包安装在当前环境），其次回退到 python -m uv。

        :return: [Optional[List[str]]] 形如 ["uv"] 或 [python, "-m", "uv"] 的命令前缀；未找到返回 None
        """
        if self._uv_checked:
            return self._uv_command

        self._uv_checked = True

        # 1. 独立的 uv 二进制（最常见，全局安装）
        if shutil.which("uv"):
            self._uv_command = ["uv"]
            return self._uv_command

        # 2. 作为 pip 包安装的 uv: python -m uv
        try:
            result = subprocess.run(
                [sys.executable, "-m", "uv", "--version"],
                capture_output=True,
                timeout=5,
            )
            if result.returncode == 0:
                self._uv_command = [sys.executable, "-m", "uv"]
        except Exception:
            pass

        return self._uv_command

    def _get_uv_command(self) -> Optional[List[str]]:
        """
        返回应使用的 uv 命令前缀。

        当通过 --no-uv 禁用或 uv 不可用时返回 None。

        :return: [Optional[List[str]]] uv 命令前缀或 None
        """
        if self._is_uv_disabled():
            return None
        return self._detect_uv()

    def _get_target_python(self) -> str:
        """
        返回应当作为安装目标的 Python 解释器路径。

        若用户激活了虚拟环境 (VIRTUAL_ENV) 但 epsdk 自身运行在别处
        （例如通过 pipx 全局安装），则返回该虚拟环境的 Python，
        以确保包安装到用户期望的环境中而非全局。

        :return: [str] 目标 Python 解释器路径
        """
        venv = os.environ.get("VIRTUAL_ENV")
        if not venv:
            return sys.executable

        # epsdk 已在该虚拟环境内运行
        try:
            venv_root = os.path.normcase(os.path.abspath(venv)) + os.sep
            exe_root = os.path.normcase(os.path.abspath(sys.executable))
            if exe_root.startswith(venv_root):
                return sys.executable
        except Exception:
            pass

        # 定位虚拟环境的 python
        if sys.platform == "win32":
            candidate = os.path.join(venv, "Scripts", "python.exe")
        else:
            candidate = os.path.join(venv, "bin", "python")

        return candidate if os.path.exists(candidate) else sys.executable

    def _execute_backend(
        self, base_cmd: List[str], args: List[str], description: str, backend: str
    ) -> bool:
        """
        使用指定的后端 (uv/pip) 执行命令并实时输出到当前终端。

        :param base_cmd: [List[str]] 后端命令前缀，如 ["uv", "pip"] 或 [python, "-m", "pip"]
        :param args: [List[str]] 传递给后端的子命令与参数
        :param description: [str] 展示给用户的操作描述
        :param backend: [str] 后端名称 (uv/pip)，用于展示与错误提示
        :return: [bool] 执行成功返回 True
        """
        env = self._build_subprocess_env()

        proxies = self._get_system_proxy()
        proxy_hint = ""
        if proxies:
            safe_proxy = self._sanitize_proxy_url(
                proxies.get("https", proxies.get("http", ""))
            )
            proxy_hint = f" [dim](proxy: {safe_proxy})[/]"

        console.print(
            f"\n[bold blue]⚙ {description}[/] [dim]({backend})[/]{proxy_hint}"
        )
        console.print("[dim]─────────────────────────────────────────────────[/]")

        try:
            process = subprocess.Popen(
                base_cmd + args,
                env=env,
                stdout=sys.stdout,
                stderr=sys.stderr,
            )
        except FileNotFoundError as e:
            console.print(
                f"[error]{i18n.t('cli.package.backend_not_found', backend=backend, error=e)}[/]"
            )
            return False
        except Exception as e:
            console.print(
                f"[error]{i18n.t('cli.package.backend_start_failed', backend=backend, error=e)}[/]"
            )
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
            console.print(
                f"\n[warning]{i18n.t('cli.package.operation_interrupted')}[/]"
            )
            return False

        console.print("[dim]─────────────────────────────────────────────────[/]")

        return process.returncode == 0

    def _run_pip_command_with_output(self, args: List[str], description: str) -> bool:
        """
        执行 pip 类操作 (install/uninstall)。

        策略：
        1. 优先使用 uv（自动识别独立二进制或 python -m uv）；
           uv 会自动遵循当前虚拟环境 (VIRTUAL_ENV)。
        2. uv 不可用或执行失败时，回退到 pip，
           并将目标 Python 解析为当前虚拟环境的解释器，
           避免安装到全局环境。

        :param args: [List[str]] pip 子命令与参数，如 ["install", "--upgrade", pkg]
        :param description: [str] 展示给用户的操作描述
        :return: [bool] 执行成功返回 True
        """
        uv_cmd = self._get_uv_command()
        if uv_cmd:
            if self._execute_backend(uv_cmd + ["pip"], args, description, "uv"):
                return True
            console.print(f"[warning]{i18n.t('cli.package.uv_fallback_to_pip')}[/]")

        pip_cmd = [self._get_target_python(), "-m", "pip"]
        return self._execute_backend(pip_cmd, args, description, "pip")

    def _version_key(self, version: str) -> tuple:
        """
        将版本号解析为可比较的元组键

        遵循项目命名规则排序：正式版 > rc > beta > alpha > dev。
        例如 2.4.5-dev.1 先于 2.4.5 正式版。

        :param version: [str] 版本号字符串
        :return: [tuple] 可直接用于排序/比较的元组键
        """
        match = _VERSION_RE.match(str(version).strip().lstrip("vV"))
        if not match:
            # 无法解析时退化为基础键，保证不抛异常
            return ((0, 0, 0, 0), (1,), str(version))

        release = tuple(int(x) for x in match.group("release").split("."))
        # release 段对齐到固定长度，确保 (2.5) 与 (2.5.0) 可正确比较
        padded = release + (0,) * max(0, 4 - len(release))

        pre_type = match.group("pre")
        if pre_type is None:
            # 正式版：预发布键高于任何预发布版本
            pre_key = (1,)
        else:
            rank = _PRE_RELEASE_RANK.get(pre_type.lower(), 1)
            pre_num = int(match.group("num") or 0)
            pre_key = (0, rank, pre_num)

        return (padded, pre_key, "")

    def _compare_versions(self, version1: str, version2: str) -> int:
        """
        比较两个版本号的大小

        :param version1: [str] 第一个版本号
        :param version2: [str] 第二个版本号
        :return: [int] version1 大于/等于/小于 version2 时分别返回 1/0/-1
        """
        k1 = self._version_key(version1)
        k2 = self._version_key(version2)
        if k1 > k2:
            return 1
        elif k1 < k2:
            return -1
        else:
            return 0

    def _check_sdk_compatibility(self, min_sdk_version: str) -> Tuple[bool, str]:
        """
        检查当前SDK版本是否满足最低版本要求

        :param min_sdk_version: [str] 所需的最低SDK版本
        :return: [Tuple[bool, str]] (是否兼容, 提示信息)
        """
        try:
            from ErisPulse import __version__

            current_version = __version__
        except ImportError:
            current_version = "unknown"

        if current_version == "unknown":
            return True, i18n.t("cli.package.sdk_version_unknown")

        try:
            compatibility = self._compare_versions(current_version, min_sdk_version)
            if compatibility >= 0:
                return (
                    True,
                    i18n.t(
                        "cli.package.sdk_compatible",
                        current=current_version,
                        required=min_sdk_version,
                    ),
                )
            else:
                return (
                    False,
                    i18n.t(
                        "cli.package.sdk_incompatible",
                        current=current_version,
                        required=min_sdk_version,
                    ),
                )
        except Exception:
            return True, i18n.t("cli.package.sdk_compat_check_failed")

    async def _get_package_info(self, package_name: str) -> Optional[Dict[str, Any]]:
        """
        从远程包列表中获取指定包的详细信息

        :param package_name: [str] 包名
        :return: [Optional[Dict[str, Any]]] 包信息字典，未找到时返回 None
        """
        normalized_name = self._normalize_name(package_name)
        remote_packages = await self.get_remote_packages()

        for name, info in remote_packages["modules"].items():
            if self._normalize_name(name) == normalized_name:
                return info

        for name, info in remote_packages["adapters"].items():
            if self._normalize_name(name) == normalized_name:
                return info

        return None

    def install_package(
        self,
        package_names: List[str],
        upgrade: bool = False,
        pre: bool = False,
        extra_pip_args: List[str] = None,
    ) -> bool:
        """
        安装一个或多个包，支持别名映射、未验证包确认和SDK兼容性检查

        :param package_names: [List[str]] 待安装的包名或别名列表
        :param upgrade: [bool] 是否升级已安装的包 (默认: False)
        :param pre: [bool] 是否允许预发布版本 (默认: False)
        :param extra_pip_args: [Optional[List[str]]] 附加的pip参数 (默认: None)
        :return: [bool] 全部安装成功返回 True
        """
        all_success = True

        for package_name in package_names:
            actual_package = asyncio.run(self._find_package_by_alias(package_name))

            if actual_package:
                console.print(
                    f"[info]{i18n.t('cli.package.alias_found', alias=f'[bold]{package_name}[/]', package=f'[package]{actual_package}[/]')}[/]"
                )
                current_package_name = actual_package
            else:
                console.print(
                    f"[info]{i18n.t('cli.package.alias_not_found_install', package=f'[package]{package_name}[/]')}[/]"
                )
                current_package_name = package_name

            package_info = asyncio.run(self._get_package_info(package_name))
            if package_info and not package_info.get("verified", True):
                console.print(
                    Panel(
                        i18n.t(
                            "cli.package.unverified_warning",
                            package=f"[package]{current_package_name}[/]",
                            author=package_info.get(
                                "author", i18n.t("cli.package.unknown")
                            ),
                            repository=package_info.get(
                                "repository", i18n.t("cli.package.unknown")
                            ),
                        ),
                        title=i18n.t("cli.package.unverified_title"),
                        border_style="yellow",
                    )
                )
                if not Confirm.ask(
                    i18n.t("cli.package.confirm_install"), default=False
                ):
                    console.print(f"[info]{i18n.t('cli.package.install_cancelled')}[/]")
                    all_success = False
                    continue

            if package_info and "min_sdk_version" in package_info:
                is_compatible, message = self._check_sdk_compatibility(
                    package_info["min_sdk_version"]
                )
                if not is_compatible:
                    console.print(
                        Panel(
                            i18n.t(
                                "cli.package.compat_warning_install",
                                package=f"[package]{current_package_name}[/]",
                                version=package_info["min_sdk_version"],
                                message=message,
                            ),
                            title=i18n.t("cli.package.compat_warning_title"),
                            border_style="warning",
                        )
                    )
                    if not Confirm.ask(
                        i18n.t("cli.package.confirm_install"), default=False
                    ):
                        console.print(
                            f"[info]{i18n.t('cli.package.install_cancelled')}[/]"
                        )
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

            success = self._run_pip_command_with_output(
                cmd, i18n.t("cli.package.installing", package=current_package_name)
            )

            if success:
                console.print(
                    f"[success]{i18n.t('cli.package.install_success', package=current_package_name)}[/]"
                )
            else:
                console.print(
                    f"[error]{i18n.t('cli.package.install_failed', package=current_package_name)}[/]"
                )
                all_success = False

        return all_success

    def install_direct(
        self, pip_args: List[str], description: str = "pip install"
    ) -> bool:
        """
        直接使用给定参数执行pip安装

        :param pip_args: [List[str]] pip install 的参数列表
        :param description: [str] 展示给用户的操作描述 (默认: "pip install")
        :return: [bool] 执行成功返回 True
        """
        cmd = ["install"] + pip_args
        success = self._run_pip_command_with_output(cmd, description)

        if success:
            console.print(
                f"[success]{i18n.t('cli.package.operation_success', description=description)}[/]"
            )
        else:
            console.print(
                f"[error]{i18n.t('cli.package.operation_failed', description=description)}[/]"
            )

        return success

    def uninstall_package(
        self, package_names: List[str], skip_confirm: bool = False
    ) -> bool:
        """
        卸载一个或多个包，支持别名映射和确认提示

        :param package_names: [List[str]] 待卸载的包名或别名列表
        :param skip_confirm: [bool] 是否跳过确认提示 (默认: False)
        :return: [bool] 全部卸载成功返回 True
        """
        all_success = True

        packages_to_uninstall = []

        for package_name in package_names:
            actual_package = asyncio.run(self._find_package_by_alias(package_name))

            if actual_package:
                console.print(
                    f"[info]{i18n.t('cli.package.alias_mapping', alias=f'[bold]{package_name}[/]', package=f'[package]{actual_package}[/]')}[/]"
                )
                packages_to_uninstall.append(actual_package)
            else:
                installed_package = self._find_installed_package_by_name(package_name)
                if installed_package:
                    package_name = installed_package
                    console.print(
                        f"[info]{i18n.t('cli.package.installed_package_found', package=f'[bold]{package_name}[/]')}[/]"
                    )
                    packages_to_uninstall.append(package_name)
                else:
                    console.print(
                        f"[warning]{i18n.t('cli.package.uninstall_alias_not_found', package=f'[package]{package_name}[/]')}[/]"
                    )
                    packages_to_uninstall.append(package_name)

        if not skip_confirm:
            package_list = "\n".join(
                [f"  - [package]{pkg}[/]" for pkg in packages_to_uninstall]
            )
            if not Confirm.ask(
                i18n.t("cli.package.confirm_uninstall", packages=package_list),
                default=False,
            ):
                console.print(f"[info]{i18n.t('cli.package.operation_cancelled')}[/]")
                return False

        for package_name in packages_to_uninstall:
            success = self._run_pip_command_with_output(
                ["uninstall", "-y", package_name],
                i18n.t("cli.package.uninstalling", package=package_name),
            )

            if success:
                console.print(
                    f"[success]{i18n.t('cli.package.uninstall_success', package=package_name)}[/]"
                )
            else:
                console.print(
                    f"[error]{i18n.t('cli.package.uninstall_failed', package=package_name)}[/]"
                )
                all_success = False

        return all_success

    def upgrade_all(self) -> bool:
        """
        检查并升级所有有可用更新的ErisPulse包

        :return: [bool] 全部升级成功返回 True
        """
        updates = asyncio.run(self.check_package_updates())

        if not updates:
            console.print(f"[success]{i18n.t('cli.package.all_up_to_date')}[/]")
            return True

        console.print(
            Panel(
                i18n.t("cli.package.updates_found", count=f"[bold]{len(updates)}[/]")
                + "\n"
                + "\n".join(
                    f"  - [package]{pkg}[/] [dim]{current_ver}[/] → [success]{new_ver}[/]"
                    for pkg, (current_ver, new_ver) in updates.items()
                ),
                title=i18n.t("cli.package.upgrade_list_title"),
            )
        )

        if not Confirm.ask(i18n.t("cli.package.confirm_upgrade_all"), default=False):
            console.print(f"[info]{i18n.t('cli.package.operation_cancelled')}[/]")
            return False

        results = {}
        for pkg in sorted(updates.keys()):
            console.print(
                f"\n[info]{i18n.t('cli.package.upgrading_package', package=f'[package]{pkg}[/]')}[/]"
            )
            results[pkg] = self.install_package([pkg], upgrade=True)

        success_count = sum(1 for success in results.values() if success)
        console.print(
            f"\n[success]{i18n.t('cli.package.upgrade_complete', success=success_count, total=len(results))}[/]"
        )

        failed = [pkg for pkg, success in results.items() if not success]
        if failed:
            console.print(
                Panel(
                    i18n.t("cli.package.upgrade_failed_list")
                    + "\n"
                    + "\n".join(f"  - [error]{pkg}[/]" for pkg in failed),
                    title=i18n.t("cli.package.warning_title"),
                    style="warning",
                )
            )
            return False

        return True

    def upgrade_package(self, package_names: List[str], pre: bool = False) -> bool:
        """
        升级指定包到最新版本

        :param package_names: [List[str]] 待升级的包名或别名列表
        :param pre: [bool] 是否允许预发布版本 (默认: False)
        :return: [bool] 全部升级成功返回 True
        """
        all_success = True

        for package_name in package_names:
            actual_package = asyncio.run(self._find_package_by_alias(package_name))

            if actual_package:
                console.print(
                    f"[info]{i18n.t('cli.package.package_found', package=f'[package]{actual_package}[/]')}[/]"
                )
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

            remote_version = asyncio.run(
                self._get_pypi_package_version(current_package_name)
            )

            if current_version:
                if remote_version:
                    comparison = self._compare_versions(remote_version, current_version)
                    if comparison <= 0:
                        console.print(
                            f"[success]{i18n.t('cli.package.already_latest', package=current_package_name, version=current_version)}[/]"
                        )
                        continue
                    else:
                        console.print(
                            f"[info]{i18n.t('cli.package.version_update_available', package=current_package_name, old=current_version, new=remote_version)}[/]"
                        )
                else:
                    console.print(
                        f"[info]{i18n.t('cli.package.current_version_info', package=current_package_name, version=current_version)}[/]"
                    )
            else:
                console.print(
                    f"[warning]{i18n.t('cli.package.install_info_not_found', package=current_package_name)}[/]"
                )

            package_info = asyncio.run(self._get_package_info(current_package_name))
            if package_info and "min_sdk_version" in package_info:
                is_compatible, message = self._check_sdk_compatibility(
                    package_info["min_sdk_version"]
                )
                if not is_compatible:
                    console.print(
                        Panel(
                            i18n.t(
                                "cli.package.compat_warning_upgrade",
                                package=f"[package]{current_package_name}[/]",
                                version=package_info["min_sdk_version"],
                                message=message,
                            ),
                            title=i18n.t("cli.package.compat_warning_title"),
                            border_style="warning",
                        )
                    )
                    if not Confirm.ask(
                        i18n.t("cli.package.confirm_upgrade"), default=False
                    ):
                        console.print(
                            f"[info]{i18n.t('cli.package.upgrade_cancelled')}[/]"
                        )
                        all_success = False
                        continue
                else:
                    console.print(f"[success]{message}[/]")

            cmd = ["install", "--upgrade"]
            if pre:
                cmd.append("--pre")
            cmd.append(current_package_name)

            success = self._run_pip_command_with_output(
                cmd, i18n.t("cli.package.upgrading", package=current_package_name)
            )

            if success:
                console.print(
                    f"[success]{i18n.t('cli.package.upgrade_success', package=current_package_name)}[/]"
                )
            else:
                console.print(
                    f"[error]{i18n.t('cli.package.upgrade_failed', package=current_package_name)}[/]"
                )
                all_success = False

        return all_success

    def search_package(self, query: str) -> Dict[str, List[Dict[str, str]]]:
        """
        在已安装和远程包中搜索匹配查询的包

        :param query: [str] 搜索关键词
        :return: [Dict[str, List[Dict[str, str]]] 包含 installed 和 remote 匹配结果的字典
        """
        normalized_query = self._normalize_name(query)
        results = {"installed": [], "remote": []}

        installed = self.get_installed_packages()
        for pkg_type in ["modules", "adapters"]:
            for name, info in installed[pkg_type].items():
                if (
                    normalized_query in self._normalize_name(name)
                    or normalized_query in self._normalize_name(info["package"])
                    or normalized_query in self._normalize_name(info["summary"])
                ):
                    results["installed"].append(
                        {
                            "type": pkg_type[:-1]
                            if pkg_type.endswith("s")
                            else pkg_type,
                            "name": name,
                            "package": info["package"],
                            "version": info["version"],
                            "summary": info["summary"],
                        }
                    )

        remote = asyncio.run(self.get_remote_packages())
        for pkg_type in ["modules", "adapters"]:
            for name, info in remote[pkg_type].items():
                if (
                    normalized_query in self._normalize_name(name)
                    or normalized_query in self._normalize_name(info["package"])
                    or normalized_query
                    in self._normalize_name(info.get("description", ""))
                    or normalized_query in self._normalize_name(info.get("summary", ""))
                ):
                    results["remote"].append(
                        {
                            "type": pkg_type[:-1]
                            if pkg_type.endswith("s")
                            else pkg_type,
                            "name": name,
                            "package": info["package"],
                            "version": info["version"],
                            "summary": info.get("description", info.get("summary", "")),
                        }
                    )

        return results

    def get_installed_version(self) -> str:
        """
        获取已安装的ErisPulse SDK版本号

        :return: [str] SDK版本号，无法获取时返回 "unknown"
        """
        try:
            from ErisPulse import __version__

            return __version__
        except ImportError:
            return "unknown"

    def _get_pypi_versions_sync(self) -> List[Dict[str, Any]]:
        """
        同步从PyPI获取ErisPulse的所有可用版本，按版本号降序排列

        :return: [List[Dict[str, Any]]] 版本信息列表，失败时返回空列表
        """
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
                        "pre_release": self._is_pre_release(version_str),
                    }
                    versions.append(release_info)
            versions.sort(key=lambda x: self._version_key(x["version"]), reverse=True)
            return versions
        except (json.JSONDecodeError, KeyError, Exception):
            return []

    async def get_pypi_versions(self) -> List[Dict[str, Any]]:
        """
        异步获取ErisPulse在PyPI上的所有可用版本

        :return: [List[Dict[str, Any]]] 版本信息列表，失败时返回空列表
        """
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, self._get_pypi_versions_sync)
        except Exception:
            console.print(f"[error]{i18n.t('cli.package.pypi_versions_failed')}[/]")
            return []

    def _is_pre_release(self, version: str) -> bool:
        """
        判断版本号是否为预发布版本

        :param version: [str] 版本号字符串
        :return: [bool] 是预发布版本返回 True
        """
        pre_release_pattern = re.compile(r"(a|b|rc|dev|alpha|beta)\d*", re.IGNORECASE)
        return bool(pre_release_pattern.search(version))

    def update_self(self, target_version: str = None, force: bool = False) -> bool:
        """
        更新ErisPulse SDK到指定版本或最新版本

        :param target_version: [Optional[str]] 目标版本号，为空则更新到最新版本 (默认: None)
        :param force: [bool] 是否强制更新到当前已安装的目标版本 (默认: False)
        :return: [bool] 更新成功返回 True
        """
        current_version = self.get_installed_version()

        if target_version and target_version == current_version and not force:
            console.print(
                f"[info]{i18n.t('cli.package.already_target_version', version=f'[bold]{current_version}[/]')}[/]"
            )
            return True

        package_spec = "ErisPulse"
        if target_version:
            if not re.match(r"^[a-zA-Z0-9._+\-]+$", target_version):
                console.print(
                    f"[error]{i18n.t('cli.package.invalid_version', version=target_version)}[/]"
                )
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

            console.print(f"[info]{i18n.t('cli.package.starting_update')}[/]")
            console.print(f"[info]{i18n.t('cli.package.rerun_cli_later')}[/]")

            subprocess.Popen(
                [sys.executable, script_path],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )

            return True
        else:
            if target_version:
                update_desc = i18n.t(
                    "cli.package.update_desc_with_version", version=target_version
                )
            else:
                update_desc = i18n.t("cli.package.update_desc_latest")

            success = self._run_pip_command_with_output(
                ["install", "--upgrade", package_spec],
                update_desc,
            )

            if success:
                new_version = target_version or i18n.t("cli.package.latest_version")
                console.print(
                    f"[success]{i18n.t('cli.package.sdk_update_success', old=current_version, new=new_version)}[/]"
                )
                if not target_version:
                    console.print(f"[info]{i18n.t('cli.package.restart_cli')}[/]")
            else:
                console.print(f"[error]{i18n.t('cli.package.sdk_update_failed')}[/]")

            return success
