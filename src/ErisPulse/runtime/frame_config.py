"""
ErisPulse 框架配置管理模块

提供默认配置定义及配置完整性管理功能
"""

import copy
import os
from typing import Any

from ..Core.constants import (
    CONFIG_ROOT_KEY,
    DEFAULT_COMMAND_ALLOW_SPACE_PREFIX,
    DEFAULT_COMMAND_CASE_SENSITIVE,
    DEFAULT_COMMAND_MUST_AT_BOT,
    DEFAULT_COMMAND_PREFIX,
    DEFAULT_HANDLER_MAX_CONCURRENCY,
    DEFAULT_I18N_LANGUAGE,
    DEFAULT_LAZY_LOADING_ENABLED,
    DEFAULT_LOG_BACKUP_COUNT,
    DEFAULT_LOG_LEVEL,
    DEFAULT_LOG_MAX_SIZE_MB,
    DEFAULT_LOG_MEMORY_LIMIT,
    DEFAULT_LOG_ROTATION,
    DEFAULT_LOG_ROTATION_WHEN,
    DEFAULT_MESSAGE_IGNORE_SELF,
    DEFAULT_OFFLINE_BOT_EXPIRY_SECS,
    DEFAULT_PROACTIVE_GC_FULL_EVERY,
    DEFAULT_PROACTIVE_GC_GEN0_MIN,
    DEFAULT_PROACTIVE_GC_GENERATION,
    DEFAULT_PROACTIVE_GC_IDLE_ONLY,
    DEFAULT_PROACTIVE_GC_INTERVAL_SECS,
    DEFAULT_PROACTIVE_GC_MEMORY_GROWTH_MB,
    DEFAULT_SERVER_AUTO_START,
    DEFAULT_SERVER_HOST,
    DEFAULT_SERVER_PORT,
    DEFAULT_STRICT_MODE,
    DEFAULT_UNINIT_TIMEOUT_SECS,
    DEFAULT_USE_GLOBAL_DB,
)

# 默认配置
DEFAULT_ERISPULSE_CONFIG = {
    "server": {
        "host": DEFAULT_SERVER_HOST,
        "port": DEFAULT_SERVER_PORT,
        "auto_start": DEFAULT_SERVER_AUTO_START,
        "ssl_certfile": None,
        "ssl_keyfile": None,
    },
    "logger": {
        "level": DEFAULT_LOG_LEVEL,
        "format": "rich",
        "log_files": [],
        # 日志目录模式（与 log_files 互斥，log_files 显式路径优先）：
        # 设置后日志自动写入该目录并支持自动分段
        "log_dir": "",
        "log_rotation": DEFAULT_LOG_ROTATION,          # 分段方式: "size" | "date" | "none"
        "log_max_size_mb": DEFAULT_LOG_MAX_SIZE_MB,    # size 模式单文件上限（MB）
        "log_backup_count": DEFAULT_LOG_BACKUP_COUNT,  # 保留的历史日志文件数
        "log_rotation_when": DEFAULT_LOG_ROTATION_WHEN,  # date 模式轮转周期
        "memory_limit": DEFAULT_LOG_MEMORY_LIMIT,
        # 屏蔽指定日志等级（如 ["EVENT"] 隐藏消息收发内容，用于隐私保护）
        "exclude_levels": [],
    },
    "storage": {
        "use_global_db": DEFAULT_USE_GLOBAL_DB,
    },
    "modules": {},
    "adapters": {},
    "event": {
        "message": {
            "ignore_self": DEFAULT_MESSAGE_IGNORE_SELF,
        },
        "command": {
            # prefix 可以是字符串（单个前缀）或列表（多个前缀）
            "prefix": DEFAULT_COMMAND_PREFIX,
            "case_sensitive": DEFAULT_COMMAND_CASE_SENSITIVE,
            "allow_space_prefix": DEFAULT_COMMAND_ALLOW_SPACE_PREFIX,
            "must_at_bot": DEFAULT_COMMAND_MUST_AT_BOT,
        },
    },
    # 框架主人系统配置
    # users 为 dict 时按平台指定: {"yunhu": ["123"], "telegram": ["456"]}
    # users 为 list 时为全局主人（所有平台生效）: ["123", "456"]
    "master": {
        "users": {},
    },
    "framework": {
        "enable_lazy_loading": DEFAULT_LAZY_LOADING_ENABLED,
        # 本地插件文件夹：相对项目根目录，支持字符串或列表
        "plugins_dir": "plugins",
        "uninit_timeout": DEFAULT_UNINIT_TIMEOUT_SECS,
        "strict_mode": DEFAULT_STRICT_MODE,
        "strict_mode_exceptions": {
            "modules": [],
            "adapters": [],
        },
        # 性能优化与主动 GC 配置
        "handler_max_concurrency": DEFAULT_HANDLER_MAX_CONCURRENCY,
        "proactive_gc_interval": DEFAULT_PROACTIVE_GC_INTERVAL_SECS,
        "proactive_gc_generation": DEFAULT_PROACTIVE_GC_GENERATION,
        "proactive_gc_full_every": DEFAULT_PROACTIVE_GC_FULL_EVERY,
        "proactive_gc_memory_growth_mb": DEFAULT_PROACTIVE_GC_MEMORY_GROWTH_MB,
        "proactive_gc_idle_only": DEFAULT_PROACTIVE_GC_IDLE_ONLY,
        "proactive_gc_gen0_min": DEFAULT_PROACTIVE_GC_GEN0_MIN,
        "offline_bot_expiry": DEFAULT_OFFLINE_BOT_EXPIRY_SECS,
    },
    "i18n": {
        "language": DEFAULT_I18N_LANGUAGE,
    },
    # 模块作用域系统：绑定模块与适配器 Bot / 平台 / 会话。
    # 默认允许全部模块；配置绑定后才开始过滤。
    # 解析优先级：会话级 > Bot 级 > 平台级。
    # default_allow = false 时开启"隐式拒绝"严格模式（未匹配白名单即拒绝）。
    # 平台级: platforms.<platform> = {modules: [...], blocked: [...]}
    # Bot 级: bots.<platform>.<bot_id> = {modules: [...], blocked: [...]}
    # 会话级: sessions.<platform>.<session_id> = {modules: [...], blocked: [...]}
    "scope": {
        "default_allow": True,
        "cache_size": 1024,
        "platforms": {},
        "bots": {},
        "sessions": {},
    },
}


def _get_config_service():
    from ..Core.config import config as global_config

    return global_config


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """
    深度合并两个字典，override 中的值覆盖 base 中的对应值

    :param base: 基础字典
    :param override: 覆盖字典
    :return: 合并后的新字典
    """
    result = copy.deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def _iter_leaf_diff(
    old: dict[str, Any], new: dict[str, Any], prefix: str = ""
) -> list[tuple[str, Any]]:
    """
    递归比较两棵配置字典，返回新增或值变化的叶子键（点分路径）

    仅收集 new 中相对 old 发生变化的叶子，用于把整棵配置的持久化
    拆分为细粒度叶子写入，避免整棵覆盖导致用户热更新丢失。

    {!--< internal-use >!--}
    语义：只增改、不处理删除（本模块的合并语义仅新增/覆盖叶子值）。
    {!--< /internal-use >!--}

    :param old: 变更前的配置字典
    :param new: 变更后的配置字典
    :param prefix: 递归时的路径前缀
    :return: [(点分路径, 叶子值), ...]
    """
    diffs: list[tuple[str, Any]] = []
    for key, value in new.items():
        path = f"{prefix}.{key}" if prefix else key
        old_value = old.get(key) if isinstance(old, dict) else None
        if isinstance(value, dict):
            if isinstance(old_value, dict):
                diffs.extend(_iter_leaf_diff(old_value, value, path))
            else:
                # 旧值不存在或非 dict：递归收集新子树的全部叶子
                diffs.extend(_iter_leaf_diff({}, value, path))
        elif old_value != value:
            diffs.append((path, value))
    return diffs


def _ensure_erispulse_config_structure(config_dict: dict[str, Any]) -> dict[str, Any]:
    """
    确保 ErisPulse 配置结构完整，补全缺失的配置项

    :param config_dict: 当前配置
    :return: 补全后的完整配置
    """

    # 深度合并配置
    for section, default_values in DEFAULT_ERISPULSE_CONFIG.items():
        if section not in config_dict:
            config_dict[section] = copy.deepcopy(default_values)
            continue

        if not isinstance(config_dict[section], dict):
            config_dict[section] = copy.deepcopy(default_values)
            continue

        for key, default_value in default_values.items():
            if key not in config_dict[section]:
                config_dict[section][key] = (
                    copy.deepcopy(default_value)
                    if isinstance(default_value, dict)
                    else default_value
                )

    return config_dict


def get_erispulse_config() -> dict[str, Any]:
    """
    获取 ErisPulse 框架配置，自动补全缺失的配置项并保存

    :return: 完整的 ErisPulse 配置字典
    """
    config_service = _get_config_service()

    # 获取现有配置
    current_config = config_service.getConfig(CONFIG_ROOT_KEY)

    # 如果完全没有配置，设置默认配置
    if current_config is None:
        default_copy = copy.deepcopy(DEFAULT_ERISPULSE_CONFIG)
        config_service.setConfig(CONFIG_ROOT_KEY, default_copy)
        return default_copy

    # 保存原始配置的快照用于比较
    original_snapshot = copy.deepcopy(current_config)

    # 检查并补全缺失的配置项
    complete_config = _ensure_erispulse_config_structure(current_config)

    # 如果配置有变化，按叶子键写入缺失的默认项，
    # 避免整棵 ErisPulse 覆盖导致用户对其它子键的热更新被陈旧快照冲掉
    if original_snapshot != complete_config:
        for path, value in _iter_leaf_diff(original_snapshot, complete_config):
            config_service.setConfig(f"{CONFIG_ROOT_KEY}.{path}", value)

    # 环境变量覆盖（Docker / 12-factor）：ERISPULSE_SERVER_PORT 等
    # 仅对返回副本应用，不持久化到缓存；每调用每生效
    result = copy.deepcopy(complete_config)
    _apply_env_overrides(result, CONFIG_ROOT_KEY)
    return result


def _apply_env_overrides(config: dict[str, Any], root: str = CONFIG_ROOT_KEY) -> None:
    """
    {!--< internal-use >!--}
    递归对配置字典应用环境变量覆盖

    命名规则：``ErisPulse.server.port`` → ``ERISPULSE_SERVER_PORT``
    （将点路径大写、``.`` 替换为 ``_``）。仅覆盖叶子值，按原值类型做 coerce。
    """
    _apply_env_to_subtree(config, root)


def _apply_env_to_subtree(d: dict[str, Any], path: str) -> None:
    for key, val in list(d.items()):
        full_path = f"{path}.{key}"
        if isinstance(val, dict):
            _apply_env_to_subtree(val, full_path)
        else:
            env_name = full_path.upper().replace(".", "_")
            env_val = os.environ.get(env_name)
            if env_val is not None:
                d[key] = _coerce_env_value(val, env_val)


def _coerce_env_value(original: Any, env_str: str) -> Any:
    """按原值类型把环境变量字符串转换为对应 Python 类型"""
    s = env_str.strip()
    if isinstance(original, bool):
        return s.lower() in ("1", "true", "yes", "on")
    if isinstance(original, int) and not isinstance(original, bool):
        try:
            return int(s)
        except ValueError:
            return env_str
    if isinstance(original, float):
        try:
            return float(s)
        except ValueError:
            return env_str
    if isinstance(original, list):
        return [x.strip() for x in s.split(",")] if s else []
    return env_str


def get_config(section: str | None = None) -> dict[str, Any] | Any:
    """
    获取 ErisPulse 配置

    :param section: 配置部分名称（如 "server"、"logger" 等），None 表示获取完整配置
    :return: 配置字典或配置项
    """
    erispulse_config = get_erispulse_config()

    if section is None:
        return erispulse_config
    return erispulse_config.get(section, {})


def update_erispulse_config(new_config: dict[str, Any]) -> bool:
    """
    更新 ErisPulse 配置，自动补全缺失的配置项

    :param new_config: 新的配置字典
    :return: 是否更新成功
    """
    config_service = _get_config_service()

    # 基线使用缓存中的原始配置（不含环境变量覆盖），避免把环境覆盖持久化到文件
    current_raw = config_service.getConfig(CONFIG_ROOT_KEY)
    if not isinstance(current_raw, dict):
        current_raw = {}
    baseline = _ensure_erispulse_config_structure(copy.deepcopy(current_raw))

    # 获取当前配置并深合并新配置
    merged = _deep_merge(baseline, new_config)

    # 确保合并后的配置结构完整
    complete_config = _ensure_erispulse_config_structure(merged)

    # 仅按叶子键写入变化，避免整棵覆盖冲掉用户对其它子键的热更新
    for path, value in _iter_leaf_diff(baseline, complete_config):
        config_service.setConfig(f"{CONFIG_ROOT_KEY}.{path}", value)
    return True


def get_server_config() -> dict[str, Any]:
    """
    获取服务器配置，确保结构完整

    :return: 服务器配置字典
    """
    return get_config("server")


def get_logger_config() -> dict[str, Any]:
    """
    获取日志配置，确保结构完整

    :return: 日志配置字典
    """
    return get_config("logger")


def get_storage_config() -> dict[str, Any]:
    """
    获取存储模块配置

    :return: 存储配置字典
    """
    return get_config("storage")


def get_event_config() -> dict[str, Any]:
    """
    获取事件系统配置

    :return: 事件系统配置字典
    """
    return get_config("event")


def get_framework_config() -> dict[str, Any]:
    """
    获取框架配置

    :return: 框架配置字典
    """
    return get_config("framework")


def get_i18n_config() -> dict[str, Any]:
    """
    获取国际化配置

    :return: 国际化配置字典
    """
    return get_config("i18n")


def get_master_config() -> dict[str, Any]:
    """
    获取框架主人系统配置

    :return: 框架主人配置字典
    """
    return get_config("master")


__all__ = [
    "DEFAULT_ERISPULSE_CONFIG",
    "get_config",
    "get_erispulse_config",
    "get_event_config",
    "get_framework_config",
    "get_i18n_config",
    "get_logger_config",
    "get_master_config",
    "get_server_config",
    "get_storage_config",
    "update_erispulse_config",
]
