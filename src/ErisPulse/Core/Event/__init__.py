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
from .wrapper import Event
from .session_type import (
    # 标准类型常量
    RECEIVE_TYPES,
    SEND_TYPES,
    
    # 自定义类型注册
    register_custom_type,
    unregister_custom_type,
    
    # 类型获取方法
    get_id_field,
    get_receive_type,
    convert_to_send_type,
    convert_to_receive_type,
    
    # 自动推断方法
    infer_receive_type,
    get_target_id,
    get_send_type_and_target_id,
    
    # 工具方法
    is_standard_type,
    is_valid_send_type,
    get_standard_types,
    get_send_types,
    clear_custom_types,
)

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

__all__ = [
    "command",
    "message", 
    "notice",
    "request",
    "meta",
    "Event",
    # 会话类型管理
    "RECEIVE_TYPES",
    "SEND_TYPES",
    "register_custom_type",
    "unregister_custom_type",
    "get_id_field",
    "get_receive_type",
    "convert_to_send_type",
    "convert_to_receive_type",
    "infer_receive_type",
    "get_target_id",
    "get_send_type_and_target_id",
    "is_standard_type",
    "is_valid_send_type",
    "get_standard_types",
    "get_send_types",
    "clear_custom_types",
]
