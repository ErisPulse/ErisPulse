"""
ErisPulse 运行时配置和管理模块

提供框架启动时的配置管理、异常处理等基础功能

{!--< tips >!--}
内部使用模块，框架启动时自动加载
{!--< /tips >!--}
"""

# config_schema 的符号通过 __getattr__ 懒加载
# （避免在 runtime 初始化阶段触发 Core.Bases 完整加载链，导致循环引用）
# 注意：i18n_schema 的 BaseI18n / I18nKey 已不再从 runtime 导出，请从 Core.Bases 导入
from .diagnostics import (
    extract_user_frame,
    format_diagnostic_block,
    log_diagnostic,
)
from .exceptions import (
    ExceptionHandler,
    async_exception_handler,
    global_exception_handler,
    setup_exception_handling,
)
from .frame_config import (
    DEFAULT_ERISPULSE_CONFIG,
    get_master_config,
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
from .hints import (
    best_match,
    best_match_with_prefix,
    suggest_for_attribute_error,
    suggest_similar,
)
from .tasks import spawn_background

__all__ = [
    # 配置管理
    "DEFAULT_ERISPULSE_CONFIG",
    "AdapterConfig",  # ← BaseConfig 的别名
    # 通用配置 Schema（适配器/模块/外部项目均可使用）
    "BaseConfig",
    "BotAccountConfig",
    # 异常处理
    "ExceptionHandler",
    "async_exception_handler",
    "best_match",
    "best_match_with_prefix",
    "dataclass_to_defaults_dict",
    "dataclass_to_toml_with_comments",
    "dict_to_dataclass",
    # 异常诊断
    "extract_user_frame",
    "format_diagnostic_block",
    "get_config",
    "get_config_schema",
    "get_erispulse_config",
    "get_event_config",
    "get_framework_config",
    "get_i18n_config",
    "get_logger_config",
    "get_master_config",
    "get_server_config",
    "get_storage_config",
    "global_exception_handler",
    # 异常诊断
    "log_diagnostic",
    "register_config_i18n",
    "resolve_config_schema",
    "setup_exception_handling",
    "spawn_background",
    "suggest_for_attribute_error",
    # 友好提示
    "suggest_similar",
    "update_erispulse_config",
    "validate_config",
]


# config_schema 中定义的符号采用懒加载
# 这些类型/函数的实际定义在 Core.Bases 包中，立即导入会触发
# Core.Bases.__init__ → module → loaders → lifecycle → runtime 的循环引用
# （i18n_schema 的 BaseI18n / I18nKey 不再从 runtime 导出，请从 Core.Bases 导入）
_LAZY_FROM_CONFIG_SCHEMA = {
    "AdapterConfig",
    "BaseConfig",
    "BotAccountConfig",
    "dataclass_to_defaults_dict",
    "dataclass_to_toml_with_comments",
    "dict_to_dataclass",
    "get_config_schema",
    "register_config_i18n",
    "resolve_config_schema",
    "validate_config",
}


def __getattr__(name: str):
    """首次访问时从 Core.Bases.config_schema 懒加载 Schema 类型与工具函数"""
    if name in _LAZY_FROM_CONFIG_SCHEMA:
        from ..Core.Bases.config_schema import __dict__ as _src

        if name in _src:
            globals()[name] = _src[name]
            return _src[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
