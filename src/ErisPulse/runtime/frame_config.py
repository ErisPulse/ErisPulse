"""
ErisPulse 框架配置管理模块

提供默认配置定义及配置完整性管理功能
"""

import copy
from typing import Any, Dict, Optional, Union

from ..Core.constants import (
    CONFIG_ROOT_KEY,
    DEFAULT_COMMAND_ALLOW_SPACE_PREFIX,
    DEFAULT_COMMAND_CASE_SENSITIVE,
    DEFAULT_COMMAND_MUST_AT_BOT,
    DEFAULT_COMMAND_PREFIX,
    DEFAULT_I18N_LANGUAGE,
    DEFAULT_LAZY_LOADING_ENABLED,
    DEFAULT_LOG_LEVEL,
    DEFAULT_LOG_MEMORY_LIMIT,
    DEFAULT_MESSAGE_IGNORE_SELF,
    DEFAULT_SERVER_HOST,
    DEFAULT_SERVER_PORT,
    DEFAULT_UNINIT_TIMEOUT_SECS,
    DEFAULT_USE_GLOBAL_DB,
)

# 默认配置
DEFAULT_ERISPULSE_CONFIG = {
    "server": {
        "host": DEFAULT_SERVER_HOST,
        "port": DEFAULT_SERVER_PORT,
        "ssl_certfile": None,
        "ssl_keyfile": None,
    },
    "logger": {
        "level": DEFAULT_LOG_LEVEL,
        "format": "rich",
        "log_files": [],
        "memory_limit": DEFAULT_LOG_MEMORY_LIMIT,
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
            "prefix": DEFAULT_COMMAND_PREFIX,
            "case_sensitive": DEFAULT_COMMAND_CASE_SENSITIVE,
            "allow_space_prefix": DEFAULT_COMMAND_ALLOW_SPACE_PREFIX,
            "must_at_bot": DEFAULT_COMMAND_MUST_AT_BOT,
        },
    },
    "framework": {
        "enable_lazy_loading": DEFAULT_LAZY_LOADING_ENABLED,
        "uninit_timeout": DEFAULT_UNINIT_TIMEOUT_SECS,
    },
    "i18n": {
        "language": DEFAULT_I18N_LANGUAGE,
    },
}


def _get_config_service():
    from ..Core.config import config as global_config

    return global_config


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
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


def _ensure_erispulse_config_structure(config_dict: Dict[str, Any]) -> Dict[str, Any]:
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


def get_erispulse_config() -> Dict[str, Any]:
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

    # 如果配置有变化，更新到存储
    if original_snapshot != complete_config:
        config_service.setConfig(CONFIG_ROOT_KEY, complete_config)

    return complete_config


def get_config(section: Optional[str] = None) -> Union[Dict[str, Any], Any]:
    """
    获取 ErisPulse 配置

    :param section: 配置部分名称（如 "server"、"logger" 等），None 表示获取完整配置
    :return: 配置字典或配置项
    """
    erispulse_config = get_erispulse_config()

    if section is None:
        return erispulse_config
    return erispulse_config.get(section, {})


def update_erispulse_config(new_config: Dict[str, Any]) -> bool:
    """
    更新 ErisPulse 配置，自动补全缺失的配置项

    :param new_config: 新的配置字典
    :return: 是否更新成功
    """
    config_service = _get_config_service()

    # 获取当前配置并深合并新配置
    current = get_erispulse_config()
    merged = _deep_merge(current, new_config)

    # 确保合并后的配置结构完整
    complete_config = _ensure_erispulse_config_structure(merged)

    return config_service.setConfig(CONFIG_ROOT_KEY, complete_config)


def get_server_config() -> Dict[str, Any]:
    """
    获取服务器配置，确保结构完整

    :return: 服务器配置字典
    """
    return get_config("server")


def get_logger_config() -> Dict[str, Any]:
    """
    获取日志配置，确保结构完整

    :return: 日志配置字典
    """
    return get_config("logger")


def get_storage_config() -> Dict[str, Any]:
    """
    获取存储模块配置

    :return: 存储配置字典
    """
    return get_config("storage")


def get_event_config() -> Dict[str, Any]:
    """
    获取事件系统配置

    :return: 事件系统配置字典
    """
    return get_config("event")


def get_framework_config() -> Dict[str, Any]:
    """
    获取框架配置

    :return: 框架配置字典
    """
    return get_config("framework")


def get_i18n_config() -> Dict[str, Any]:
    """
    获取国际化配置

    :return: 国际化配置字典
    """
    return get_config("i18n")


__all__ = [
    "DEFAULT_ERISPULSE_CONFIG",
    "get_erispulse_config",
    "get_config",
    "update_erispulse_config",
    "get_server_config",
    "get_logger_config",
    "get_storage_config",
    "get_event_config",
    "get_framework_config",
    "get_i18n_config",
]
