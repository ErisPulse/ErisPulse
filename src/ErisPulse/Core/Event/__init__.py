"""
ErisPulse 事件处理模块

提供统一的事件处理接口，支持命令、消息、通知、请求和元事件处理

{!--< tips >!--}
1. 所有事件处理都基于OneBot12标准事件格式
2. 通过装饰器方式注册事件处理器
3. 支持优先级和条件过滤
{!--< /tips >!--}
"""

from .command import command
from .message import message
from .notice import notice
from .request import request
from .meta import meta
from . import exceptions
from .. import config

def _clear_all_handlers():
    """
    {!--< internal-use >!--}
    清除所有已注册的事件处理器和命令
    """
    # 清除命令处理器
    command._clear_commands()
    
    # 清除各类事件处理器
    message._clear_message_handlers()
    notice._clear_notice_handlers()
    request._clear_request_handlers()
    meta._clear_meta_handlers()

# 初始化默认配置
def _setup_default_config():
    """
    {!--< internal-use >!--}
    设置默认配置
    """
    default_config = {
        "command": {
            "prefix": "/",
            "case_sensitive": True,
            "allow_space_prefix": False
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
    "exceptions"
]