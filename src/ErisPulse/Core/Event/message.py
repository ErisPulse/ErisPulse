"""
ErisPulse 消息处理模块

提供基于装饰器的消息事件处理功能

{!--< tips >!--}
1. 支持私聊、群聊消息分类处理
2. 支持@消息特殊处理
3. 支持自定义条件过滤
4. 支持 pattern（glob 通配符）/ regex（正则）文本匹配过滤
{!--< /tips >!--}
"""

from collections.abc import Callable
from typing import Any

from ..constants import DETAIL_TYPE_GROUP, DETAIL_TYPE_PRIVATE, EVENT_TYPE_MESSAGE
from ..text_match import compile_text_matcher
from .base import BaseEventHandler


def _combine_conditions(
    *conditions: Callable[[Any], bool] | None,
) -> Callable[[Any], bool] | None:
    """
    {!--< internal-use >!--}
    组合多个条件函数为"全部满足"；过滤掉 None
    """
    valid = [c for c in conditions if c is not None]
    if not valid:
        return None
    if len(valid) == 1:
        return valid[0]

    def combined(event: Any) -> bool:
        return all(c(event) for c in valid)

    return combined


class MessageHandler:
    """
    消息事件处理器

    提供不同类型消息事件的处理功能
    """

    def __init__(self):
        self.handler = BaseEventHandler(EVENT_TYPE_MESSAGE, "message")

    def on_message(self, priority: int = 0, pattern: str | None = None, regex: str | None = None):
        """
        消息事件装饰器

        :param priority: 处理器优先级
        :param pattern: glob 通配符（``*`` / ``?`` / ``[seq]``），消息文本须匹配才触发
        :param regex: 正则表达式，消息文本须匹配（search）才触发；与 pattern 同时给定时须都匹配
        :return: 装饰器函数
        """

        def decorator(func: Callable):
            self.handler.register(
                func, priority, compile_text_matcher(pattern, regex)
            )
            return func

        return decorator

    def unregister(self, handler: Callable) -> bool:
        """
        取消注册的事件处理器

        :param handler: 要取消注册的处理器
        :return: 是否成功取消注册
        """
        return self.handler.unregister(handler)

    def remove_message_handler(self, handler: Callable) -> bool:
        """
        取消注册消息事件处理器

        :param handler: 要取消注册的处理器
        :return: 是否成功取消注册
        """
        return self.handler.unregister(handler)

    def on_private_message(self, priority: int = 0, pattern: str | None = None, regex: str | None = None):
        """
        私聊消息事件装饰器

        :param priority: 处理器优先级
        :param pattern: glob 通配符（``*`` / ``?`` / ``[seq]``），消息文本须匹配才触发
        :param regex: 正则表达式，消息文本须匹配（search）才触发；与 pattern 同时给定时须都匹配
        :return: 装饰器函数
        """

        def condition(event: dict[str, Any]) -> bool:
            return event.get("detail_type") == DETAIL_TYPE_PRIVATE

        def decorator(func: Callable):
            self.handler.register(
                func, priority, _combine_conditions(condition, compile_text_matcher(pattern, regex))
            )
            return func

        return decorator

    def remove_private_message_handler(self, handler: Callable) -> bool:
        """
        取消注册私聊消息事件处理器

        :param handler: 要取消注册的处理器
        :return: 是否成功取消注册
        """
        return self.handler.unregister(handler)

    def on_group_message(self, priority: int = 0, pattern: str | None = None, regex: str | None = None):
        """
        群聊消息事件装饰器

        :param priority: 处理器优先级
        :param pattern: glob 通配符（``*`` / ``?`` / ``[seq]``），消息文本须匹配才触发
        :param regex: 正则表达式，消息文本须匹配（search）才触发；与 pattern 同时给定时须都匹配
        :return: 装饰器函数
        """

        def condition(event: dict[str, Any]) -> bool:
            return event.get("detail_type") == DETAIL_TYPE_GROUP

        def decorator(func: Callable):
            self.handler.register(
                func, priority, _combine_conditions(condition, compile_text_matcher(pattern, regex))
            )
            return func

        return decorator

    def remove_group_message_handler(self, handler: Callable) -> bool:
        """
        取消注册群聊消息事件处理器

        :param handler: 要取消注册的处理器
        :return: 是否成功取消注册
        """
        return self.handler.unregister(handler)

    def on_at_message(self, priority: int = 0, pattern: str | None = None, regex: str | None = None):
        """
        @消息事件装饰器

        :param priority: 处理器优先级
        :param pattern: glob 通配符（``*`` / ``?`` / ``[seq]``），消息文本须匹配才触发
        :param regex: 正则表达式，消息文本须匹配（search）才触发；与 pattern 同时给定时须都匹配
        :return: 装饰器函数
        """

        def condition(event: dict[str, Any]) -> bool:
            # 检查消息中是否有@机器人
            message_segments = event.get("message", [])
            self_id = event.get("self", {}).get("user_id")

            for segment in message_segments:
                if (
                    segment.get("type") == "mention"
                    and segment.get("data", {}).get("user_id") == self_id
                ):
                    return True
            return False

        def decorator(func: Callable):
            self.handler.register(
                func, priority, _combine_conditions(condition, compile_text_matcher(pattern, regex))
            )
            return func

        return decorator

    def remove_at_message_handler(self, handler: Callable) -> bool:
        """
        取消注册@消息事件处理器

        :param handler: 要取消注册的处理器
        :return: 是否成功取消注册
        """
        return self.handler.unregister(handler)

    def _clear_message_handlers(self):
        """
        {!--< internal-use >!--}
        清除所有已注册的消息处理器

        :return: 被清除的处理器数量
        """
        return self.handler._clear_handlers()


message: MessageHandler = MessageHandler()
