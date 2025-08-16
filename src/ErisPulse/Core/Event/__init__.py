from .. import adapter
"""
ErisPulse 事件处理模块

提供统一的事件处理接口，支持命令、消息、通知、请求和元事件处理
"""

from .cmd import command
from .message import message
from .notice import notice
from .request import request
from .meta import meta
from .manager import event_manager
from . import exceptions
from .. import config

# 初始化默认配置
def _setup_default_config():
    """
    设置默认配置
    
    {!--< internal-use >!--}
    内部使用的方法，用于初始化默认配置
    """
    default_config = {
        "command": {
            "prefix": "/",
            "case_sensitive": True
        },
        "message": {
            "ignore_self": True
        }
    }
    
    current_config = config.getConfig("ErisPulse.event")
    if current_config is None:
        config.setConfig("ErisPulse.event", default_config)

_setup_default_config()

__all__ = [
    "command",
    "message", 
    "notice",
    "request",
    "meta",
    "event_manager",
    "exceptions"
]