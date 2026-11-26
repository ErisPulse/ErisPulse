"""
ErisPulse 框架默认配置声明（``ErisPulse.framework`` 节唯一真相源）

默认值单源化：框架节的手写字典 / full.example 静态模板 / 文案表 /
文档表格全部从本声明派生（B1-4 逐步切换消费端）。运行时消费面不变——
:mod:`ErisPulse.runtime.frame_config` 用 :func:`dataclass_to_defaults_dict`
把声明折叠为字典默认值，合并快照 / env 覆盖 / 热更新机制照旧按字典工作。

声明类为裸 dataclass（不继承 Core.Bases 的 BaseConfig）：框架节默认值
折叠与模板渲染只依赖 ``fields()``，去基可让本模块在 Core 装配期内被
frame_config 惰性导入而不触发 Bases 包全量装配（无循环导入）。

description 使用 i18n 字典格式（``{"i18n": key, "default": 兜底文本}``）；
对应五语言翻译键在 B1-4 生成器切换批次随渲染面一并注册。

调优常量批次（B1-2）：``txn_*`` / ``sync_warn_cooldown`` / ``cross_receipt_window``
/ ``handler_slow_threshold`` 为第一批"立即生效"型——消费点运行时经
:func:`ErisPulse.runtime.frame_config.get_framework_value` 惰性读取，
Core/constants 同名常量保持为声明默认值（兼容直接引用方，不再新增）。
"""

from dataclasses import MISSING, dataclass, field, fields, is_dataclass
from typing import Any

from ..Core.constants import (
    AUTO_RELOAD_POLL_INTERVAL_SECS,
    DEFAULT_CROSS_RECEIPT_POLICY,
    DEFAULT_CROSS_RECEIPT_WINDOW_SECS,
    DEFAULT_EVENT_DEDUPE_ENABLED,
    DEFAULT_HANDLER_MAX_CONCURRENCY,
    DEFAULT_LAZY_LOADING_ENABLED,
    DEFAULT_MEMORY_TRACING,
    DEFAULT_OFFLINE_BOT_EXPIRY_SECS,
    DEFAULT_PLUGINS_DIR_NAME,
    DEFAULT_PROACTIVE_GC_FULL_EVERY,
    DEFAULT_PROACTIVE_GC_GEN0_MIN,
    DEFAULT_PROACTIVE_GC_GENERATION,
    DEFAULT_PROACTIVE_GC_IDLE_ONLY,
    DEFAULT_PROACTIVE_GC_INTERVAL_SECS,
    DEFAULT_PROACTIVE_GC_MEMORY_GROWTH_MB,
    DEFAULT_STRICT_MODE,
    DEFAULT_UNINIT_TIMEOUT_SECS,
    HANDLER_QUEUE_MAX_PENDING,
    HANDLER_SLOW_THRESHOLD_SECS,
    STORAGE_SYNC_IN_ASYNC_WARN_COOLDOWN_SECS,
    STORAGE_TXN_BEGIN_TIMEOUT_SECS,
    STORAGE_TXN_COMMIT_TIMEOUT_SECS,
    STORAGE_TXN_SLOW_WARN_SECS,
    SYNC_IN_ASYNC_BRIDGE_WAIT_SECS,
)


@dataclass
class StrictModeExceptionsConfig:
    """strict_mode 放行名单：名单内组件不参与严格模式校验"""

    modules: list[str] = field(
        default_factory=list,
        metadata={"description": {"i18n": "core.config.framework.strict_mode_exceptions.modules", "default": "exempt module names (glob supported)"}},
    )
    adapters: list[str] = field(
        default_factory=list,
        metadata={"description": {"i18n": "core.config.framework.strict_mode_exceptions.adapters", "default": "exempt adapter names (glob supported)"}},
    )


@dataclass
class StrictConfig:
    """严格模式作用域开关：按域开启严格校验（级别语义随 strict_mode）"""

    sync_in_async: bool = field(
        default=False,
        metadata={"description": {"i18n": "core.config.framework.strict.sync_in_async", "default": "raise StrictModeError instead of warning when sync storage APIs are called from async context (development aid)"}},
    )


@dataclass
class AutoReloadConfig:
    """已安装发行版热重载：来源包文件变化后自动重载对应模块 / 适配器（升级即生效）

    监控范围 ACL（与 strict_mode_exceptions / watch_ignore_dirs 同族）：
    deny 优先于 allow；allow 为空表示"除 deny 外全部已加载组件"。
    """

    enabled: bool = field(
        default=False,
        metadata={"description": {"i18n": "core.config.framework.auto_reload.enabled", "default": "watch installed distributions of loaded modules/adapters and hot-reload them on file change (pip upgrade takes effect without restart)"}},
    )
    interval: float = field(
        default=AUTO_RELOAD_POLL_INTERVAL_SECS,
        metadata={"description": {"i18n": "core.config.framework.auto_reload.interval", "default": "polling interval in seconds (mtime/size scan; sha256 only computed on hit)"}},
    )
    allow: list[str] = field(
        default_factory=list,
        metadata={"description": {"i18n": "core.config.framework.auto_reload.allow", "default": "watchlist: component or distribution names (glob supported); empty = all loaded components"}},
    )
    deny: list[str] = field(
        default_factory=list,
        metadata={"description": {"i18n": "core.config.framework.auto_reload.deny", "default": "blocklist: never watch these component or distribution names (glob supported); takes precedence over allow"}},
    )


@dataclass
class FrameworkConfig:
    """框架运行参数：加载行为、严格模式、性能与主动 GC、去重与多账户策略"""

    enable_lazy_loading: bool = field(
        default=DEFAULT_LAZY_LOADING_ENABLED,
        metadata={"description": {"i18n": "core.config.framework.enable_lazy_loading", "default": "defer adapter/module loading until first access"}},
    )
    plugins_dir: str = field(
        default=DEFAULT_PLUGINS_DIR_NAME,
        metadata={"description": {"i18n": "core.config.framework.plugins_dir", "default": "local plugins folder (relative to project root)"}},
    )
    uninit_timeout: int = field(
        default=DEFAULT_UNINIT_TIMEOUT_SECS,
        metadata={"description": {"i18n": "core.config.framework.uninit_timeout", "default": "framework uninitialize timeout in seconds"}},
    )
    strict_mode: int = field(
        default=DEFAULT_STRICT_MODE,
        metadata={"description": {"i18n": "core.config.framework.strict_mode", "default": "strict mode level (0=off, 1=log, 2=fatal on undeclared config keys)"}},
    )
    strict_mode_exceptions: StrictModeExceptionsConfig = field(
        default_factory=StrictModeExceptionsConfig,
        metadata={"description": {"i18n": "core.config.framework.strict_mode_exceptions", "default": "components exempt from strict mode checks"}},
    )
    handler_max_concurrency: int = field(
        default=DEFAULT_HANDLER_MAX_CONCURRENCY,
        metadata={"description": {"i18n": "core.config.framework.handler_max_concurrency", "default": "max concurrent handler tasks per platform"}},
    )
    handler_queue_max_pending: int = field(
        default=HANDLER_QUEUE_MAX_PENDING,
        metadata={"description": {"i18n": "core.config.framework.handler_queue_max_pending", "default": "max pending handler tasks before backpressure (0=unlimited)"}},
    )
    proactive_gc_interval: int = field(
        default=DEFAULT_PROACTIVE_GC_INTERVAL_SECS,
        metadata={"description": {"i18n": "core.config.framework.proactive_gc_interval", "default": "proactive GC cycle interval in seconds (0=disabled)"}},
    )
    proactive_gc_generation: int = field(
        default=DEFAULT_PROACTIVE_GC_GENERATION,
        metadata={"description": {"i18n": "core.config.framework.proactive_gc_generation", "default": "gc.freeze generation per cycle (0=all young objects)"}},
    )
    proactive_gc_full_every: int = field(
        default=DEFAULT_PROACTIVE_GC_FULL_EVERY,
        metadata={"description": {"i18n": "core.config.framework.proactive_gc_full_every", "default": "run a full collection every N cycles"}},
    )
    proactive_gc_memory_growth_mb: int = field(
        default=DEFAULT_PROACTIVE_GC_MEMORY_GROWTH_MB,
        metadata={"description": {"i18n": "core.config.framework.proactive_gc_memory_growth_mb", "default": "trigger extra collection when RSS grows by this many MB"}},
    )
    proactive_gc_idle_only: bool = field(
        default=DEFAULT_PROACTIVE_GC_IDLE_ONLY,
        metadata={"description": {"i18n": "core.config.framework.proactive_gc_idle_only", "default": "run proactive GC only when the event loop is idle"}},
    )
    proactive_gc_gen0_min: int = field(
        default=DEFAULT_PROACTIVE_GC_GEN0_MIN,
        metadata={"description": {"i18n": "core.config.framework.proactive_gc_gen0_min", "default": "skip gen0 collection below this allocation count"}},
    )
    offline_bot_expiry: int = field(
        default=DEFAULT_OFFLINE_BOT_EXPIRY_SECS,
        metadata={"description": {"i18n": "core.config.framework.offline_bot_expiry", "default": "expire offline bot cache entries after this many seconds"}},
    )
    watch_ignore_dirs: list[str] | None = field(
        default=None,
        metadata={"description": {"i18n": "core.config.framework.watch_ignore_dirs", "default": "dirs ignored by hot-reload watchers; null=builtin list, []=ignore nothing"}},
    )
    event_dedupe: bool = field(
        default=DEFAULT_EVENT_DEDUPE_ENABLED,
        metadata={"description": {"i18n": "core.config.framework.event_dedupe", "default": "drop repeated event deliveries with the same event id (hot-reloadable)"}},
    )
    memory_tracing: bool = field(
        default=DEFAULT_MEMORY_TRACING,
        metadata={"description": {"i18n": "core.config.framework.memory_tracing", "default": "enable tracemalloc diagnostics (about 2x allocation-path CPU; troubleshooting only)"}},
    )
    cross_account_policy: str = field(
        default=DEFAULT_CROSS_RECEIPT_POLICY,
        metadata={"description": {"i18n": "core.config.framework.cross_account_policy", "default": "multi-account duplicate receipt policy: off / mark / drop"}},
    )
    session_accounts: dict = field(
        default_factory=dict,
        metadata={"description": {"i18n": "core.config.framework.session_accounts", "default": "session-to-account bindings: {platform: {session_id: bot_id}} (hot-reloadable)"}},
    )
    watch_include_plugin_dirs: bool = field(
        default=True,
        metadata={"description": {"i18n": "core.config.framework.watch_include_plugin_dirs", "default": "hand plugin dirs to the plugin hot-reload watcher instead of full restart"}},
    )
    # ---- 调优常量第一批（立即生效型：消费点经 get_framework_value 惰性读取） ----
    txn_begin_timeout: float = field(
        default=STORAGE_TXN_BEGIN_TIMEOUT_SECS,
        metadata={"description": {"i18n": "core.config.framework.txn_begin_timeout", "default": "storage transaction BEGIN timeout in seconds"}},
    )
    txn_commit_timeout: float = field(
        default=STORAGE_TXN_COMMIT_TIMEOUT_SECS,
        metadata={"description": {"i18n": "core.config.framework.txn_commit_timeout", "default": "storage transaction commit/rollback timeout in seconds"}},
    )
    txn_slow_warn: float = field(
        default=STORAGE_TXN_SLOW_WARN_SECS,
        metadata={"description": {"i18n": "core.config.framework.txn_slow_warn", "default": "warn when a transaction stays open longer than this many seconds"}},
    )
    sync_warn_cooldown: float = field(
        default=STORAGE_SYNC_IN_ASYNC_WARN_COOLDOWN_SECS,
        metadata={"description": {"i18n": "core.config.framework.sync_warn_cooldown", "default": "cooldown between sync-in-async warnings per call site, in seconds"}},
    )
    cross_receipt_window: float = field(
        default=DEFAULT_CROSS_RECEIPT_WINDOW_SECS,
        metadata={"description": {"i18n": "core.config.framework.cross_receipt_window", "default": "cross-account duplicate receipt matching window in seconds"}},
    )
    handler_slow_threshold: float = field(
        default=HANDLER_SLOW_THRESHOLD_SECS,
        metadata={"description": {"i18n": "core.config.framework.handler_slow_threshold", "default": "warn when a single handler runs longer than this many seconds"}},
    )
    strict: StrictConfig = field(
        default_factory=StrictConfig,
        metadata={"description": {"i18n": "core.config.framework.strict", "default": "strict-mode scope switches"}},
    )
    auto_reload: AutoReloadConfig = field(
        default_factory=AutoReloadConfig,
        metadata={"description": {"i18n": "core.config.framework.auto_reload", "default": "hot-reload loaded modules/adapters when their installed distribution changes"}},
    )
    sync_in_async_bridge_wait: float = field(
        default=SYNC_IN_ASYNC_BRIDGE_WAIT_SECS,
        metadata={"description": {"i18n": "core.config.framework.sync_in_async_bridge_wait", "default": "max seconds a sync storage call from async context may wait on the bridge (0=unlimited); on timeout the call fails softly"}},
    )


def _fold_defaults(config_class: type) -> dict[str, Any]:
    """把 dataclass 声明折叠为默认值字典（下划线前缀与 example 字段排除）"""
    result: dict[str, Any] = {}
    for f in fields(config_class):
        if f.name.startswith("_") or (f.metadata or {}).get("example", False):
            continue
        nested = f.type if isinstance(f.type, type) and is_dataclass(f.type) else None
        if nested is not None:
            result[f.name] = _fold_defaults(nested)
        elif f.default_factory is not MISSING:  # type: ignore[misc]
            result[f.name] = f.default_factory()
        elif f.default is not MISSING:  # type: ignore[misc]
            result[f.name] = f.default
        else:
            result[f.name] = None
    return result


_FRAMEWORK_DEFAULTS_CACHE: dict[str, Any] | None = None


def framework_defaults() -> dict[str, Any]:
    """
    FrameworkConfig 声明折叠（结果缓存）

    本模块自带折叠、零 Core 依赖——供 frame_config 在 Core 装配窗口内
    （Logger 构造触发快照构建）安全调用。
    """
    global _FRAMEWORK_DEFAULTS_CACHE
    if _FRAMEWORK_DEFAULTS_CACHE is None:
        _FRAMEWORK_DEFAULTS_CACHE = _fold_defaults(FrameworkConfig)
    return _FRAMEWORK_DEFAULTS_CACHE


__all__ = ["AutoReloadConfig", "FrameworkConfig", "StrictConfig", "StrictModeExceptionsConfig", "framework_defaults"]
