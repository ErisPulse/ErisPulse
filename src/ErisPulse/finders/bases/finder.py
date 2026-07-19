"""
ErisPulse 基础发现器

定义发现器的抽象基类，提供通用的发现器接口和结构

{!--< tips >!--}
1. 所有具体发现器应继承自 BaseFinder
2. 子类需实现 _get_entry_point_group 方法
3. 支持缓存机制，避免重复查询
{!--< /tips >!--}
"""

import importlib.metadata
import json
import subprocess
import sys
import time
from abc import ABC, abstractmethod
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from ...Core.logger import logger


class _RemoteDist:
    """
    远程环境的 Distribution 轻量代理

    模拟 ``importlib.metadata.Distribution`` 的必要接口（name / version / metadata），
    用于在跨环境查询时提供与本地 Distribution 一致的访问体验。
    """

    def __init__(self, name: str | None, version: str | None, summary: str = ""):
        self.name = name
        self.version = version
        self._summary = summary

    @property
    def metadata(self):
        """模拟 Distribution.metadata，提供 Summary 等字段的查询"""
        return {"Summary": self._summary}


class _RemoteEntryPoint:
    """
    远程环境的 EntryPoint 轻量代理

    模拟 ``importlib.metadata.EntryPoint`` 的必要接口
    （name / value / group / dist / load()），
    用于跨环境查询时与本地 EntryPoint 对象保持一致的外部访问模式。

    {!--< tips >!--}
    ``load()`` 仅在目标环境与当前环境一致时有意义；跨环境时调用 ``load()``
    会抛出 ``RuntimeError``，应通过 ``value`` 自行解析。
    {!--< /tips >!--}
    """

    def __init__(self, data: dict):
        self.name: str = data.get("name", "")
        self.value: str = data.get("value", "")
        self.group: str = data.get("group", "")
        dist_name = data.get("dist_name")
        dist_version = data.get("dist_version")
        summary = data.get("summary", "") or ""
        self.dist = (
            _RemoteDist(dist_name, dist_version, summary)
            if dist_name
            else None
        )

    def load(self):
        """
        加载 entry-point 引用对象

        :raises RuntimeError: 跨环境查询时不支持在当前进程加载目标环境的对象
        """
        raise RuntimeError(
            "_RemoteEntryPoint.load() 不可用：跨环境查询无法在当前进程加载"
            "目标环境的 entry-point 对象，请通过 .value 自行解析或使用"
            "目标环境直接调用。"
        )

    def __repr__(self) -> str:
        return f"_RemoteEntryPoint(name={self.name!r}, value={self.value!r}, group={self.group!r})"



class BaseFinder(ABC):
    """
    基础发现器抽象类

    提供通用的发现器接口和缓存功能

    {!--< tips >!--}
    子类需要实现：
    - _get_entry_point_group: 返回 entry-point 组名
    {!--< /tips >!--}

    {!--< internal-use >!--}
    此类仅供内部使用，不应直接实例化
    {!--< /internal-use >!--}
    """

    def __init__(self, python_executable: str | None = None):
        """
        初始化基础发现器

        :param python_executable: [str | None] 目标 Python 解释器路径。
            当指定且与当前解释器不同时，通过子进程查询该环境的 entry-points，
            用于跨环境场景（如 epsdk 安装在 pipx，用户包在项目 venv）。
            默认为 None，表示查询当前解释器环境。
        """
        self._cache: dict[str, Any] | None = None
        self._cache_time: float | None = None
        self._cache_expiry: int = 60  # 缓存有效期60秒
        self._python_executable = python_executable or sys.executable

    @abstractmethod
    def _get_entry_point_group(self) -> str:
        """
        获取 entry-point 组名

        :return: entry-point 组名

        {!--< internal-use >!--}
        子类必须实现此方法
        {!--< /internal-use >!--}
        """
        ...

    def _is_remote_target(self) -> bool:
        """
        判断是否查询远程目标环境（非当前解释器）

        :return: [bool] 目标环境与当前解释器不同时返回 True
        """
        import os

        try:
            target = os.path.normcase(str(Path(self._python_executable).resolve()))
            current = os.path.normcase(str(Path(sys.executable).resolve()))
            return target != current
        except Exception:
            return False

    def _fetch_remote_entry_points(self, group_name: str) -> list[Any]:
        """
        通过子进程查询目标 Python 环境的 entry-points

        :param group_name: [str] entry-point 组名
        :return: [list[Any]] EntryPoint 或兼容对象的列表

        {!--< internal-use >!--}
        当目标环境不是当前解释器时，运行子进程获取该环境的 entry-points，
        返回模拟 ``importlib.metadata.EntryPoint`` 接口的轻量对象。
        {!--< /internal-use >!--}
        """
        # 使用 venv 的 site-packages，避免子进程加载用户项目的代码
        script = (
            "import json, importlib.metadata\n"
            "eps = importlib.metadata.entry_points()\n"
            f"group = {group_name!r}\n"
            "if hasattr(eps, 'select'):\n"
            "    entries = list(eps.select(group=group))\n"
            "else:\n"
            "    entries = list(eps.get(group, []))\n"
            "out = []\n"
            "for e in entries:\n"
            "    dist_name = e.dist.name if e.dist else None\n"
            "    dist_version = e.dist.version if e.dist else None\n"
            "    summary = ''\n"
            "    if e.dist:\n"
            "        try:\n"
            "            summary = e.dist.metadata.get('Summary', '') or ''\n"
            "        except Exception:\n"
            "            pass\n"
            "    out.append({\n"
            "        'name': e.name, 'value': e.value, 'group': e.group,\n"
            "        'dist_name': dist_name, 'dist_version': dist_version,\n"
            "        'summary': summary,\n"
            "    })\n"
            "print(json.dumps(out))\n"
        )
        try:
            result = subprocess.run(
                [self._python_executable, "-c", script],
                capture_output=True,
                timeout=30,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                logger.error(
                    f"查询目标环境 {self._python_executable} 的 entry-points 失败: "
                    f"{result.stderr.strip()}"
                )
                return []
            data = json.loads(result.stdout)
            return [_RemoteEntryPoint(d) for d in data]
        except Exception as e:
            logger.error(f"查询目标环境 {self._python_executable} 失败: {e}")
            return []

    def _get_entry_points(self) -> list[Any]:
        """
        获取所有 entry-points

        :return: entry-point 对象列表

        {!--< internal-use >!--}
        内部方法，使用缓存机制获取 entry-points。
        当配置了目标 Python 解释器且与当前不同时，通过子进程查询目标环境。
        {!--< /internal-use >!--}
        """
        group_name = self._get_entry_point_group()

        # 检查缓存
        if self._cache is not None and self._cache_time is not None:
            if time.time() - self._cache_time < self._cache_expiry:
                return list(self._cache.values())

        logger.trace(f"正在从 entry-points 查找 {group_name}...")

        try:
            if self._is_remote_target():
                # 查询目标 Python 环境（跨环境场景）
                entries = self._fetch_remote_entry_points(group_name)
            else:
                # 加载 entry-points（当前环境）
                entry_points = importlib.metadata.entry_points()

                if hasattr(entry_points, "select"):
                    entries = list(entry_points.select(group=group_name))
                else:
                    entries = list(entry_points.get(group_name, []))  # type: ignore[attr-defined]

            # 更新缓存
            self._cache = {entry.name: entry for entry in entries}
            self._cache_time = time.time()

            logger.trace(f"找到 {len(entries)} 个 {group_name} entry-points")

            return entries

        except Exception as e:
            logger.error(f"查找 {group_name} entry-points 失败: {e}")
            return []

    def find_all(self) -> list[Any]:
        """
        查找所有 entry-points

        :return: entry-point 对象列表
        """
        return self._get_entry_points()

    def find_by_name(self, name: str) -> Any | None:
        """
        按名称查找 entry-point

        :param name: entry-point 名称
        :return: entry-point 对象，未找到返回 None
        """
        self._ensure_cache()
        return self._cache.get(name) if self._cache else None

    def get_entry_point_map(self) -> dict[str, Any]:
        """
        获取 entry-point 映射字典

        :return: {name: entry_point} 字典
        """
        self._ensure_cache()
        return self._cache.copy() if self._cache else {}

    def _ensure_cache(self) -> None:
        """
        确保缓存已加载且未过期
        """
        if self._cache is None or self._cache_time is None:
            self._get_entry_points()
            return

        if time.time() - self._cache_time >= self._cache_expiry:
            self._get_entry_points()

    def get_group_name(self) -> str:
        """
        获取 entry-point 组名

        :return: entry-point 组名
        """
        return self._get_entry_point_group()

    def get_top_level_modules(self, package_name: str) -> list[str]:
        """
        获取指定 PyPI 包的顶层 Python 模块名

        :param package_name: PyPI 包名
        :return: 顶层 Python 模块名列表

        {!--< tips >!--}
        通过读取包的 top_level.txt 获取顶层模块名。
        如果 top_level.txt 不可用，则从 entry-points 的模块路径推导。
        用于重启时清理 sys.modules 缓存。
        {!--< /tips >!--}
        """
        try:
            dist = importlib.metadata.distribution(package_name)
            if top_level := dist.read_text("top_level.txt"):
                return [
                    name.strip()
                    for name in top_level.strip().splitlines()
                    if name.strip()
                ]
        except Exception as e:
            logger.trace(f"读取 {package_name} 的 top_level.txt 失败: {e}")

        top_level_set = set()
        for entry in self.find_all():
            if not (
                hasattr(entry, "dist")
                and entry.dist
                and entry.dist.name == package_name
            ):
                continue
            try:
                value = entry.value
                module_path = value.split(":")[0]
                top_level_name = module_path.split(".")[0]
                if top_level_name:
                    top_level_set.add(top_level_name)
            except Exception:
                continue
        return list(top_level_set)

    def clear_cache(self) -> None:
        """
        清除缓存

        {!--< tips >!--}
        当安装/卸载包后调用此方法清除缓存
        {!--< /tips >!--}
        """
        self._cache = None
        self._cache_time = None
        logger.trace("发现器缓存已清除")

    def set_cache_expiry(self, expiry: int) -> None:
        """
        设置缓存过期时间

        :param expiry: 过期时间（秒）

        {!--< internal-use >!--}
        内部方法，用于调整缓存策略
        {!--< /internal-use >!--}
        """
        self._cache_expiry = expiry

    def __iter__(self) -> Iterator[Any]:
        """
        迭代器接口

        :return: entry-point 迭代器
        """
        return iter(self._get_entry_points())

    def __len__(self) -> int:
        """
        返回 entry-point 数量

        :return: entry-point 数量
        """
        return len(self._get_entry_points())

    def __contains__(self, name: str) -> bool:
        """
        检查 entry-point 是否存在

        :param name: entry-point 名称
        :return: 是否存在
        """
        return self.find_by_name(name) is not None

    def __repr__(self) -> str:
        """
        返回发现器的字符串表示

        :return: 字符串表示
        """
        return f"{self.__class__.__name__}(group='{self._get_entry_point_group()}')"
