"""
ErisPulse 运行时配置和管理模块

提供框架启动时的配置管理、异常处理等基础功能

{!--< tips >!--}
内部使用模块，框架启动时自动加载
{!--< /tips >!--}
"""

from .exceptions import (
    ExceptionHandler,
    global_exception_handler,
    async_exception_handler,
    setup_exception_handling
)

from .frame_config import (
    DEFAULT_ERISPULSE_CONFIG,
    get_erispulse_config,
    get_config,
    update_erispulse_config,
    get_server_config,
    get_logger_config,
    get_storage_config,
    get_event_config,
    get_framework_config
)

__all__ = [
    # 异常处理
    'ExceptionHandler',
    'global_exception_handler',
    'async_exception_handler',
    'setup_exception_handling',
    
    # 配置管理
    'DEFAULT_ERISPULSE_CONFIG',
    'get_erispulse_config',
    'get_config',
    'update_erispulse_config',
    'get_server_config',
    'get_logger_config',
    'get_storage_config',
    'get_event_config',
    'get_framework_config',
]
