"""
ErisPulse 运行时配置和管理模块

提供框架启动时的配置管理、异常处理等基础功能

{!--< tips >!--}
内部使用模块，框架启动时自动加载
{!--< /tips >!--}
"""

from .config_schema import (
    AdapterConfig,
    BotAccountConfig,
    I18nConfig,
    dataclass_to_defaults_dict,
    dataclass_to_toml_with_comments,
    dict_to_dataclass,
    get_config_schema,
    validate_config,
)
from .exceptions import (
    ExceptionHandler,
    async_exception_handler,
    global_exception_handler,
    setup_exception_handling,
)
from .frame_config import (
    DEFAULT_ERISPULSE_CONFIG,
    get_config,
    get_erispulse_config,
    get_event_config,
    get_framework_config,
    get_i18n_config,
    get_logger_config,
    get_server_config,
    get_storage_config,
    update_erispulse_config,
)

__all__ = [
    # 异常处理
    "ExceptionHandler",
    "global_exception_handler",
    "async_exception_handler",
    "setup_exception_handling",
    # 配置管理
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
    # 适配器配置 Schema
    "AdapterConfig",
    "BotAccountConfig",
    "I18nConfig",
    "dataclass_to_toml_with_comments",
    "dataclass_to_defaults_dict",
    "dict_to_dataclass",
    "validate_config",
    "get_config_schema",
]
