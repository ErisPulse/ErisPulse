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
from .message_builder import MessageBuilder
from .meta import meta
from .notice import notice
from .request import request
from .session_type import (
    # 标准类型常量
    RECEIVE_TYPES,
    SEND_TYPES,
    # 自定义类型注册
    clear_custom_types,
    convert_to_receive_type,
    convert_to_send_type,
    # 类型获取方法
    get_id_field,
    get_receive_type,
    get_send_type_and_target_id,
    get_send_types,
    get_standard_types,
    get_target_id,
    # 自动推断方法
    infer_receive_type,
    # 工具方法
    is_standard_type,
    is_valid_send_type,
    # 自定义类型注册
    register_custom_type,
    unregister_custom_type,
)
from .wrapper import (
    CONFIRM_NO_WORDS,
    CONFIRM_YES_WORDS,
    Conversation,
    Event,
    _builtin_choose,
    _builtin_collect,
    _builtin_confirm,
    _builtin_wait_reply,
    get_platform_event_methods,
    register_event_method,
    register_event_mixin,
    unregister_event_method,
    unregister_platform_event_methods,
)

# 将 command 的命令分发器绑定到 message 的共享 BaseEventHandler，
# 使命令处理和消息处理共享同一个优先级队列。
# 命令分发器 _handle_message 以 DEFAULT_COMMAND_DISPATCHER_PRIORITY (100) 注册，
# 确保命令 /xxx 始终优先于 on_message / on_group_message 等处理器触发。
command.bind_message_handler(message.handler)


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
    "Conversation",
    "CONFIRM_YES_WORDS",
    "CONFIRM_NO_WORDS",
    "MessageBuilder",
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
    # 平台事件方法扩展
    "register_event_mixin",
    "register_event_method",
    "unregister_event_method",
    "unregister_platform_event_methods",
    "get_platform_event_methods",
    # 内置交互式方法实现
    "_builtin_wait_reply",
    "_builtin_confirm",
    "_builtin_choose",
    "_builtin_collect",
]
