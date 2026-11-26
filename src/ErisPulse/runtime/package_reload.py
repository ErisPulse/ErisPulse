"""
ErisPulse 已安装发行版热重载监控

监控已加载模块 / 适配器来源发行版的文件变化（pip 升级 / 直接修改包文件），
变化时自动重载对应组件——升级即生效，无需重启或手动调用 reload。

由 ``ErisPulse.SDK`` 的同名私有方法薄委托调用；SDK 上保留方法形态，
以便测试与子类按 ``patch.object(SDK, "_start_package_reload_watcher")`` 方式补丁。

{!--< tips >!--}
1. 经 ``ErisPulse.framework.auto_reload`` 配置节启用（默认关闭）
2. 仅监控带发行版信息的组件（entry-points 安装包）；本地插件与运行时注册组件不在监控面
3. 监控范围 ACL：allow 白名单（空 = 全部）+ deny 黑名单（优先），元素支持 glob
{!--< /tips >!--}
"""

from __future__ import annotations

import fnmatch
import hashlib
import time
from dataclasses import dataclass, field
from importlib.metadata import entry_points
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..Core.constants import (
    ADAPTER_ENTRY_POINT_GROUP,
    AUTO_RELOAD_POLL_INTERVAL_SECS,
    AUTO_RELOAD_TRIGGER_COOLDOWN_SECS,
    MODULE_ENTRY_POINT_GROUP,
)
from ..Core.i18n import i18n
from ..Core.logger import logger
from .frame_config import get_framework_value
from .hot_reload import HotReloadWatcherBase

if TYPE_CHECKING:
    from ..sdk import SDK


def _normalize_dist_name(name: str) -> str:
    """发行版名按 PEP 503 归一（``-`` / ``_`` / ``.`` 等价、小写）"""
    import re

    return re.sub(r"[-_.]+", "-", name).lower()


def _iter_entry_points(group: str) -> list[Any]:
    """按组读取 entry-points（3.10 / 3.11+ 两种返回形态兼容）"""
    eps = entry_points()
    if hasattr(eps, "select"):
        return list(eps.select(group=group))
    return list(eps.get(group, []))  # type: ignore[attr-defined]


@dataclass
class _DistWatch:
    """单个发行版的监控状态：组件清单与文件签名快照"""

    dist_name: str
    components: list[tuple[str, str]] = field(default_factory=list)  # (kind, 组件名)
    files: dict[Path, tuple[int, int]] = field(default_factory=dict)  # 路径 → (mtime_ns, size)
    hashes: dict[Path, str] = field(default_factory=dict)  # 路径 → sha256


class PackageReloadWatcher(HotReloadWatcherBase):
    """
    已安装发行版热重载监控器

    后台守护线程按固定间隔对受监控发行版做两级签名扫描（mtime/size 快扫、
    命中后 sha256 确认），变化经主事件循环逐组件调用重载管理器。

    监控范围 ACL：deny 优先于 allow；allow 为空表示"除 deny 外全部已加载
    组件"。名单元素支持 glob，组件名与发行版名均参与匹配（按 PEP 503 归一）。

    :param sdk: SDK 实例（组件清单与重载编排的来源）
    :param interval: 轮询间隔秒数（缺省读 ``framework.auto_reload.interval``）
    :param allow: 白名单（组件名或发行版名，glob 支持；空 = 全部）
    :param deny: 黑名单（优先于 allow）
    """

    def __init__(
        self,
        sdk: SDK,
        *,
        interval: float | None = None,
        allow: list[str] | None = None,
        deny: list[str] | None = None,
    ):
        super().__init__(interval=interval if interval is not None else AUTO_RELOAD_POLL_INTERVAL_SECS)
        self._sdk = sdk
        self._allow = tuple(allow or ())
        self._deny = tuple(deny or ())
        self._watches: dict[str, _DistWatch] = {}  # 归一发行版名 → 监控状态
        self._last_trigger: dict[str, float] = {}

    # ==================== 生命周期钩子 ====================

    def _prepare(self) -> bool:
        """{!--< internal-use >!--} 解析监控对象并建立文件签名；无可监控发行版时返回 False"""
        self._refresh_watches()
        return bool(self._watches)

    def _begin(self) -> None:
        """{!--< internal-use >!--} 启动轮询守护线程"""
        self._start_polling_thread("ErisPulse-PackageReload")

    def _shutdown(self) -> None:
        """{!--< internal-use >!--} 停止轮询守护线程"""
        self._shutdown_polling_thread(AUTO_RELOAD_TRIGGER_COOLDOWN_SECS)

    # ==================== 监控对象解析 ====================

    def _list_hits(self, component: str, dist_name: str, patterns: tuple[str, ...]) -> bool:
        """名单匹配：任一模式（归一后 fnmatch）命中组件名或发行版名"""
        candidates = (_normalize_dist_name(component), _normalize_dist_name(dist_name))
        for pattern in patterns:
            normalized = _normalize_dist_name(pattern)
            if any(fnmatch.fnmatchcase(candidate, normalized) for candidate in candidates):
                return True
        return False

    def _target_matches(self, component: str, dist_name: str) -> bool:
        """监控范围 ACL：deny 命中即排除；allow 空表示全部，非空则须命中"""
        if self._list_hits(component, dist_name, self._deny):
            return False
        if not self._allow:
            return True
        return self._list_hits(component, dist_name, self._allow)

    def _resolve_watches(self) -> dict[str, _DistWatch]:
        """经 entry-points 反查当前已加载组件的来源发行版"""
        try:
            loaded_modules = set(self._sdk.module.list_items())
        except Exception:
            loaded_modules = set()
        try:
            loaded_adapters = set(self._sdk.adapter.list_items())
        except Exception:
            loaded_adapters = set()

        found: dict[str, _DistWatch] = {}
        for group, kind, loaded in (
            (MODULE_ENTRY_POINT_GROUP, "module", loaded_modules),
            (ADAPTER_ENTRY_POINT_GROUP, "adapter", loaded_adapters),
        ):
            for ep in _iter_entry_points(group):
                if ep.name not in loaded:
                    continue
                dist = ep.dist
                if dist is None:
                    continue
                try:
                    dist_name = str((dist.metadata or {}).get("Name") or dist.name)
                except Exception:
                    continue
                if not self._target_matches(ep.name, dist_name):
                    continue
                watch = found.get(_normalize_dist_name(dist_name))
                if watch is None:
                    watch = _DistWatch(dist_name=dist_name)
                    found[_normalize_dist_name(dist_name)] = watch
                watch.components.append((kind, ep.name))
        return found

    def _collect_files(self, watch: _DistWatch) -> None:
        """登记发行版的 .py 文件签名（mtime/size 与 sha256）"""
        watch.files.clear()
        watch.hashes.clear()
        dist = self._find_dist(watch.dist_name)
        if dist is None:
            return
        for package_file in dist.files or []:
            if not str(package_file).endswith(".py"):
                continue
            try:
                path = Path(dist.locate_file(package_file))
                if not path.is_file():
                    continue
                st = path.stat()
            except OSError:
                continue
            watch.files[path] = (st.st_mtime_ns, st.st_size)
            digest = self._file_hash(path)
            if digest is not None:
                watch.hashes[path] = digest

    def _find_dist(self, dist_name: str) -> Any:
        """按发行版名查找 Distribution 对象（跨组复用同一份缓存映射）"""
        for group in (MODULE_ENTRY_POINT_GROUP, ADAPTER_ENTRY_POINT_GROUP):
            for ep in _iter_entry_points(group):
                dist = ep.dist
                if dist is None:
                    continue
                try:
                    name = str((dist.metadata or {}).get("Name") or dist.name)
                except Exception:
                    continue
                if _normalize_dist_name(name) == _normalize_dist_name(dist_name):
                    return dist
        return None

    def _refresh_watches(self) -> None:
        """重解析监控对象并重建全部文件签名"""
        self._watches = self._resolve_watches()
        for watch in self._watches.values():
            try:
                self._collect_files(watch)
            except OSError as e:
                logger.warning(
                    i18n.t("runtime.package_reload.snapshot_failed", dist=watch.dist_name, error=e)
                )

    @staticmethod
    def _file_hash(path: Path) -> str | None:
        """文件 sha256（不可读时为 None）"""
        try:
            digest = hashlib.sha256()
            with path.open("rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    digest.update(chunk)
            return digest.hexdigest()
        except OSError:
            return None

    # ==================== 扫描与触发 ====================

    def _scan_once(self) -> list[tuple[_DistWatch, list[tuple[str, str]]]]:
        """单轮扫描，返回发生实质变化的 (发行版, 组件) 列表"""
        changed: list[tuple[_DistWatch, list[tuple[str, str]]]] = []
        for watch in self._watches.values():
            if not watch.files:
                continue
            differing: list[Path] = []
            for path, signature in watch.files.items():
                try:
                    st = path.stat()
                except OSError:
                    differing.append(path)  # 文件消失（卸载 / 升级窗口）
                    continue
                if (st.st_mtime_ns, st.st_size) != signature:
                    differing.append(path)
            if not differing:
                continue
            confirmed = [path for path in differing if self._hash_changed(watch, path)]
            if confirmed:
                changed.append((watch, list(watch.components)))
        return changed

    def _hash_changed(self, watch: _DistWatch, path: Path) -> bool:
        """sha256 确认（mtime 抖动不算变化）；新哈希回写快照

        文件消失（卸载 / 升级窗口）且快照有记录时视为变化；从未可读的
        文件不计入。
        """
        digest = self._file_hash(path)
        old = watch.hashes.get(path)
        if digest is None:
            return old is not None
        watch.hashes[path] = digest
        return old != digest

    def _poll_once(self) -> None:
        """{!--< internal-use >!--} 单轮扫描：冷却过滤 → 刷新签名 → 主循环调度重载"""
        changed = self._scan_once()
        for watch, components in changed:
            now = time.monotonic()
            if now - self._last_trigger.get(watch.dist_name, 0.0) < AUTO_RELOAD_TRIGGER_COOLDOWN_SECS:
                continue
            self._last_trigger[watch.dist_name] = now
            # 先刷新签名（重载失败不回滚快照——保持旧值会形成失败风暴；
            # 文件再次变化时自然重试）
            try:
                self._collect_files(watch)
            except OSError as e:
                logger.debug(
                    i18n.t("runtime.package_reload.snapshot_failed", dist=watch.dist_name, error=e)
                )
            self._schedule(
                self._reload(watch, components),
                skip_log_key="runtime.package_reload.no_loop",
            )

    async def _reload(self, watch: _DistWatch, components: list[tuple[str, str]]) -> None:
        """逐组件调用对应管理器的重载（自带快照回滚与依赖级联）"""
        labels: list[str] = []
        for kind, name in components:
            manager = self._sdk.module if kind == "module" else self._sdk.adapter
            try:
                ok = await manager.reload(name)
            except Exception as e:
                logger.warning(
                    i18n.t(
                        "runtime.package_reload.failed",
                        dist=watch.dist_name,
                        name=name,
                        error=e,
                    )
                )
                continue
            if ok:
                labels.append(name)
            else:
                logger.warning(
                    i18n.t(
                        "runtime.package_reload.failed",
                        dist=watch.dist_name,
                        name=name,
                        error="reload returned False",
                    )
                )
        if labels:
            logger.info(
                i18n.t(
                    "runtime.package_reload.triggered",
                    dist=watch.dist_name,
                    components=", ".join(labels),
                )
            )


def start_package_reload(sdk: SDK) -> None:
    """
    {!--< internal-use >!--}
    按 ``framework.auto_reload`` 配置启动发行版热重载监控

    幂等：已有监控实例先停止再重建。
    """
    stop_package_reload(sdk)

    if not get_framework_value("auto_reload.enabled", False):
        return
    interval = get_framework_value("auto_reload.interval", AUTO_RELOAD_POLL_INTERVAL_SECS)
    allow = get_framework_value("auto_reload.allow", [])
    deny = get_framework_value("auto_reload.deny", [])
    watcher = PackageReloadWatcher(
        sdk,
        interval=float(interval) if interval else None,
        allow=list(allow) if allow else None,
        deny=list(deny) if deny else None,
    )
    if watcher.start():
        sdk._package_reload_watcher = watcher
        logger.info(
            i18n.t(
                "core.sdk.package_hot_reload.enabled",
                count=len(watcher._watches),
            )
        )


def stop_package_reload(sdk: SDK) -> None:
    """
    {!--< internal-use >!--}
    停止发行版热重载监控（幂等）
    """
    watcher = getattr(sdk, "_package_reload_watcher", None)
    if watcher is not None:
        watcher.stop()
        sdk._package_reload_watcher = None


__all__ = ["PackageReloadWatcher", "start_package_reload", "stop_package_reload"]
