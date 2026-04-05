"""
ErisPulse 事件包装类

提供便捷的事件访问方法

{!--< tips >!--}
1. 继承自dict，完全兼容字典访问
2. 提供便捷方法简化事件处理
3. 支持点式访问 event.platform
4. 支持适配器通过 register_event_mixin / register_event_method 注册平台专有方法
{!--< /tips >!--}
"""

import inspect
import warnings
from typing import Any, Optional
from collections.abc import Callable, Awaitable
from .. import adapter, logger
from .session_type import (
    get_send_type_and_target_id,
    convert_to_send_type,
    infer_receive_type,
)


# ==================== 平台事件方法注册系统 ====================

# 注册表: {platform: {method_name: callable}}
_platform_event_methods: dict[str, dict[str, Callable]] = {}


def _get_event_builtin_names() -> set:
    """获取 Event 类的所有公开方法名，用于冲突检测"""
    return {
        name
        for name, member in inspect.getmembers(Event, predicate=inspect.isfunction)
        if not name.startswith("_")
    }


def register_event_mixin(platform: str, mixin_cls: type) -> int:
    """
    注册一个类的所有公开方法到指定平台

    适配器可以创建一个 Mixin 类集中定义平台专有方法，
    然后通过此函数一次性注册。

    :param platform: 平台名称（需与适配器注册名一致）
    :param mixin_cls: 包含平台方法的类
    :return: 成功注册的方法数量

    :example:
    >>> class EmailEventMixin:
    ...     def get_subject(self):
    ...         return self.get("email_raw", {}).get("subject", "")
    ...     def get_from(self):
    ...         return self.get("email_raw", {}).get("from", "")
    >>> register_event_mixin("email", EmailEventMixin)
    2
    """
    if platform not in _platform_event_methods:
        _platform_event_methods[platform] = {}

    builtin_names = _get_event_builtin_names()
    registered = 0

    for name, func in inspect.getmembers(mixin_cls, predicate=inspect.isfunction):
        if name.startswith("_"):
            continue
        if name in builtin_names:
            warnings.warn(
                f"register_event_mixin: 跳过方法 '{name}'，"
                f"与 Event 内置方法冲突 (platform={platform})",
                RuntimeWarning,
                stacklevel=2,
            )
            continue
        _platform_event_methods[platform][name] = func
        registered += 1

    logger.debug(f"[Event] 平台 '{platform}' 注册了 {registered} 个扩展方法")
    return registered


def register_event_method(platform: str):
    """
    装饰器：注册单个方法到指定平台

    适合少量方法或动态注册的场景。

    :param platform: 平台名称（需与适配器注册名一致）

    :example:
    >>> @register_event_method("email")
    ... def get_subject(self):
    ...     return self.get("email_raw", {}).get("subject", "")
    """

    def decorator(func: Callable) -> Callable:
        if platform not in _platform_event_methods:
            _platform_event_methods[platform] = {}

        name = func.__name__

        if name.startswith("_"):
            return func

        builtin_names = _get_event_builtin_names()

        if name in builtin_names:
            warnings.warn(
                f"register_event_method: 跳过方法 '{name}'，"
                f"与 Event 内置方法冲突 (platform={platform})",
                RuntimeWarning,
                stacklevel=2,
            )
            return func

        _platform_event_methods[platform][name] = func
        logger.debug(f"[Event] 平台 '{platform}' 注册了扩展方法 '{name}'")
        return func

    return decorator


def unregister_event_method(platform: str, name: str) -> bool:
    """
    注销指定平台的单个扩展方法

    :param platform: 平台名称
    :param name: 方法名
    :return: 是否成功注销
    """
    if (
        platform in _platform_event_methods
        and name in _platform_event_methods[platform]
    ):
        del _platform_event_methods[platform][name]
        return True
    return False


def unregister_platform_event_methods(platform: str) -> int:
    """
    注销指定平台的全部扩展方法

    适配器关闭时应调用此方法清理注册的方法。

    :param platform: 平台名称
    :return: 被注销的方法数量
    """
    if platform in _platform_event_methods:
        count = len(_platform_event_methods[platform])
        del _platform_event_methods[platform]
        logger.debug(f"[Event] 平台 '{platform}' 注销了 {count} 个扩展方法")
        return count
    return 0


def get_platform_event_methods(platform: str) -> list[str]:
    """
    查询指定平台已注册的扩展方法名列表

    :param platform: 平台名称
    :return: 方法名列表
    """
    if platform in _platform_event_methods:
        return list(_platform_event_methods[platform].keys())
    return []


class Event(dict):
    """
    事件包装类

    提供便捷的事件访问方法

    {!--< tips >!--}
    所有方法都是可选的，不影响原有字典访问方式
    {!--< /tips >!--}
    """

    def __init__(self, event_data: dict[str, Any]):
        """
        初始化事件包装器

        :param event_data: 原始事件数据
        """
        super().__init__(event_data)
        self._event_data = event_data

    # ==================== 核心必填字段方法 ====================

    def get_id(self) -> str:
        """
        获取事件ID

        :return: 事件ID
        """
        return self.get("id", "")

    def get_time(self) -> int:
        """
        获取事件时间戳

        :return: Unix时间戳（秒级）
        """
        return self.get("time", 0)

    def get_type(self) -> str:
        """
        获取事件类型

        :return: 事件类型（message/notice/request/meta等）
        """
        return self.get("type", "")

    def get_detail_type(self) -> str:
        """
        获取事件详细类型

        :return: 事件详细类型（private/group/friend等）
        """
        return self.get("detail_type", "")

    def get_platform(self) -> str:
        """
        获取平台名称

        :return: 平台名称
        """
        return self.get("platform", "")

    # ==================== 机器人信息方法 ====================

    def get_self_platform(self) -> str:
        """
        获取机器人平台

        :return: 机器人平台名称
        """
        return self.get("self", {}).get("platform", "")

    def get_self_user_id(self) -> str:
        """
        获取机器人用户ID

        :return: 机器人用户ID
        """
        return self.get("self", {}).get("user_id", "")

    def get_self_info(self) -> dict[str, Any]:
        """
        获取机器人完整信息

        :return: 机器人信息字典
        """
        return self.get("self", {})

    # ==================== 消息事件专用方法 ====================

    def get_message(self) -> list[dict[str, Any]]:
        """
        获取消息段数组

        :return: 消息段数组
        """
        return self.get("message", [])

    def get_alt_message(self) -> str:
        """
        获取消息备用文本

        :return: 消息备用文本
        """
        return self.get("alt_message", "")

    def get_text(self) -> str:
        """
        获取纯文本内容

        :return: 纯文本内容
        """
        return self.get_alt_message()

    def get_message_text(self) -> str:
        """
        获取纯文本内容（别名）

        :return: 纯文本内容
        """
        return self.get_alt_message()

    def has_mention(self) -> bool:
        """
        是否包含@消息

        :return: 是否包含@消息
        """
        message_segments = self.get_message()
        self_id = self.get_self_user_id()

        for segment in message_segments:
            if segment.get("type") == "mention":
                if segment.get("data", {}).get("user_id") == self_id:
                    return True
        return False

    def get_mentions(self) -> list[str]:
        """
        获取所有被@的用户ID列表

        :return: 被@的用户ID列表
        """
        message_segments = self.get_message()
        mentions = []

        for segment in message_segments:
            if segment.get("type") == "mention":
                user_id = segment.get("data", {}).get("user_id")
                if user_id:
                    mentions.append(user_id)

        return mentions

    def get_user_id(self) -> str:
        """
        获取发送者ID

        :return: 发送者用户ID
        """
        return self.get("user_id", "")

    def get_user_nickname(self) -> str:
        """
        获取发送者昵称

        :return: 发送者昵称
        """
        return self.get("user_nickname", "")

    def get_group_id(self) -> str:
        """
        获取群组ID

        :return: 群组ID（群聊消息）
        """
        return self.get("group_id", "")

    def get_channel_id(self) -> str:
        """
        获取频道ID

        :return: 频道ID（频道消息）
        """
        return self.get("channel_id", "")

    def get_guild_id(self) -> str:
        """
        获取服务器ID

        :return: 服务器ID（服务器消息）
        """
        return self.get("guild_id", "")

    def get_thread_id(self) -> str:
        """
        获取话题/子频道ID

        :return: 话题ID（话题消息）
        """
        return self.get("thread_id", "")

    def get_sender(self) -> dict[str, Any]:
        """
        获取发送者信息字典

        :return: 发送者信息字典
        """
        return {
            "user_id": self.get_user_id(),
            "nickname": self.get_user_nickname(),
            "group_id": self.get_group_id() if self.is_group_message() else None,
        }

    # ==================== 消息类型判断 ====================

    def is_message(self) -> bool:
        """
        是否为消息事件

        :return: 是否为消息事件
        """
        return self.get_type() == "message"

    def is_private_message(self) -> bool:
        """
        是否为私聊消息

        :return: 是否为私聊消息
        """
        return self.is_message() and self.get_detail_type() == "private"

    def is_group_message(self) -> bool:
        """
        是否为群聊消息

        :return: 是否为群聊消息
        """
        return self.is_message() and self.get_detail_type() == "group"

    def is_at_message(self) -> bool:
        """
        是否为@消息

        :return: 是否为@消息
        """
        return self.has_mention()

    # ==================== 通知事件专用方法 ====================

    def get_operator_id(self) -> str:
        """
        获取操作者ID

        :return: 操作者ID
        """
        return self.get("operator_id", "")

    def get_operator_nickname(self) -> str:
        """
        获取操作者昵称

        :return: 操作者昵称
        """
        return self.get("operator_nickname", "")

    # ==================== 通知类型判断 ====================

    def is_notice(self) -> bool:
        """
        是否为通知事件

        :return: 是否为通知事件
        """
        return self.get_type() == "notice"

    def is_group_member_increase(self) -> bool:
        """
        群成员增加

        :return: 是否为群成员增加事件
        """
        return self.is_notice() and self.get_detail_type() == "group_member_increase"

    def is_group_member_decrease(self) -> bool:
        """
        群成员减少

        :return: 是否为群成员减少事件
        """
        return self.is_notice() and self.get_detail_type() == "group_member_decrease"

    def is_friend_add(self) -> bool:
        """
        好友添加

        :return: 是否为好友添加事件
        """
        return self.is_notice() and self.get_detail_type() == "friend_add"

    def is_friend_delete(self) -> bool:
        """
        好友删除

        :return: 是否为好友删除事件
        """
        return self.is_notice() and self.get_detail_type() == "friend_delete"

    # ==================== 请求事件专用方法 ====================

    def get_comment(self) -> str:
        """
        获取请求附言

        :return: 请求附言
        """
        return self.get("comment", "")

    # ==================== 请求类型判断 ====================

    def is_request(self) -> bool:
        """
        是否为请求事件

        :return: 是否为请求事件
        """
        return self.get_type() == "request"

    def is_friend_request(self) -> bool:
        """
        是否为好友请求

        :return: 是否为好友请求
        """
        return self.is_request() and self.get_detail_type() == "friend"

    def is_group_request(self) -> bool:
        """
        是否为群组请求

        :return: 是否为群组请求
        """
        return self.is_request() and self.get_detail_type() == "group"

    # ==================== 回复功能 ====================

    def _get_adapter_and_target(self) -> tuple:
        """
        获取适配器实例和目标信息

        使用会话类型管理模块自动处理类型转换和ID获取

        :return: (适配器实例, 发送目标类型, 目标ID)
        """
        platform = self.get_platform()
        if not platform:
            raise ValueError("平台信息缺失")

        if not (adapter_instance := getattr(adapter, platform, None)):
            raise ValueError(f"找不到平台 {platform} 的适配器")

        # 使用会话类型管理模块获取发送类型和目标ID
        send_type, target_id = get_send_type_and_target_id(self, platform)

        if not target_id:
            raise ValueError(f"无法获取目标 ID (platform={platform})")

        return adapter_instance, send_type, target_id

    async def reply(
        self,
        content: str,
        method: str = "Text",
        at_users: list[str] = None,
        reply_to: str = None,
        at_all: bool = False,
        **kwargs,
    ) -> Any:
        """
        通用回复方法

        基于适配器的Text方法，但可以通过method参数指定其他发送方法

        :param content: 发送内容（文本、URL等，取决于method参数）
        :param method: 适配器发送方法，默认为"Text"
                       可选值: "Text", "Image", "Voice", "Video", "File" 等
        :param at_users: @用户列表（可选），如 ["user1", "user2"]
        :param reply_to: 回复消息ID（可选）
        :param at_all: 是否@全体成员（可选），默认为 False
        :param kwargs: 额外参数，例如Mention方法的user_id
        :return: 适配器发送方法的返回值

        :example:
        >>> # 简单回复
        >>> await event.reply("你好")
        >>>
        >>> # 发送图片
        >>> await event.reply("http://example.com/image.jpg", method="Image")
        >>>
        >>> # @用户
        >>> await event.reply("你好", at_users=["user123"])
        >>>
        >>> # 回复消息
        >>> await event.reply("回复内容", reply_to="msg_id")
        >>>
        >>> # @全体成员
        >>> await event.reply("公告", at_all=True)
        >>>
        >>> # 组合使用：@用户 + 回复消息
        >>> await event.reply("内容", at_users=["user1"], reply_to="msg_id")
        """
        adapter_instance, detail_type, target_id = self._get_adapter_and_target()

        # 构建发送链
        send_chain = adapter_instance.Send.To(detail_type, target_id)

        # 处理@用户
        if at_users:
            for user_id in at_users:
                if hasattr(send_chain, "At"):
                    send_chain = send_chain.At(user_id)

        # 处理@全体成员
        if at_all:
            if hasattr(send_chain, "AtAll"):
                send_chain = send_chain.AtAll()

        # 处理回复消息
        if reply_to:
            if hasattr(send_chain, "Reply"):
                send_chain = send_chain.Reply(reply_to)

        # 处理特殊方法（向后兼容）
        if method == "Mention" or method == "At":
            user_id = kwargs.get("user_id")
            if user_id is None:
                user_id = self.get_user_id()
            send_chain = send_chain.At(user_id)
            method = "Text"

        # 调用指定方法
        send_method = getattr(send_chain, method, None)
        if not send_method or not callable(send_method):
            raise ValueError(f"适配器不支持方法: {method}")

        return await send_method(content)

    # ==================== OB12 消息回复 ====================

    async def reply_ob12(self, message: list[dict[str, Any]] | dict[str, Any]) -> Any:
        """
        使用 OneBot12 消息段回复

        通过适配器的 Raw_ob12 方法发送 OneBot12 标准消息段，
        是 reply() 方法的 OB12 对应版本。

        :param message: OneBot12 消息段列表或单个消息段
            [
                {"type": "text", "data": {"text": "Hello"}},
                {"type": "image", "data": {"file": "https://..." }},
            ]
        :return: 适配器 Raw_ob12 的返回值（标准响应格式）

        :example:
        >>> # 简单文本回复
        >>> await event.reply_ob12([{"type": "text", "data": {"text": "收到"}}])
        >>>
        >>> # 配合 MessageBuilder 使用
        >>> from ErisPulse.Core import MessageBuilder
        >>> await event.reply_ob12(
        >>>     MessageBuilder()
        >>>         .reply(event.get_id())
        >>>         .text("收到你的消息")
        >>>         .build()
        >>> )
        >>>
        >>> # 发送复杂消息
        >>> await event.reply_ob12(
        >>>     MessageBuilder()
        >>>         .mention(event.get_user_id())
        >>>         .text("你好")
        >>>         .image("https://example.com/img.jpg")
        >>>         .build()
        >>> )
        """
        adapter_instance, detail_type, target_id = self._get_adapter_and_target()
        return await adapter_instance.Send.To(detail_type, target_id).Raw_ob12(message)

    # ==================== 等待回复功能 ====================

    async def wait_reply(
        self,
        prompt: str = None,
        timeout: float = 60.0,
        callback: Callable[[dict[str, Any]], Awaitable[Any]] = None,
        validator: Callable[[dict[str, Any]], bool] = None,
    ) -> Optional["Event"]:
        """
        等待用户回复

        :param prompt: 提示消息，如果提供会发送给用户
        :param timeout: 等待超时时间(秒)
        :param callback: 回调函数，当收到回复时执行
        :param validator: 验证函数，用于验证回复是否有效
        :return: 用户回复的事件数据，如果超时则返回None
        """
        from .command import command as command_handler

        result = await command_handler.wait_reply(
            event=self._event_data,
            prompt=prompt,
            timeout=timeout,
            callback=callback,
            validator=validator,
        )

        # 将结果转换为Event对象
        if result:
            return Event(result)
        return None

    # ==================== 原始数据和元信息 ====================

    def get_raw(self) -> dict[str, Any]:
        """
        获取原始事件数据

        :return: 原始事件数据字典
        """
        platform = self.get_platform()
        raw_key = f"{platform}_raw" if platform else "raw"
        return self.get(raw_key, {})

    def get_raw_type(self) -> str:
        """
        获取原始事件类型

        :return: 原始事件类型
        """
        platform = self.get_platform()
        raw_type_key = f"{platform}_raw_type" if platform else "raw_type"
        return self.get(raw_type_key, "")

    # ==================== 命令信息 ====================

    def get_command_name(self) -> str:
        """
        获取命令名称

        :return: 命令名称
        """
        return self.get("command", {}).get("name", "")

    def get_command_args(self) -> list[str]:
        """
        获取命令参数

        :return: 命令参数列表
        """
        return self.get("command", {}).get("args", [])

    def get_command_raw(self) -> str:
        """
        获取命令原始文本

        :return: 命令原始文本
        """
        return self.get("command", {}).get("raw", "")

    def get_command_info(self) -> dict[str, Any]:
        """
        获取完整命令信息

        :return: 命令信息字典
        """
        return self.get("command", {})

    def is_command(self) -> bool:
        """
        是否为命令

        :return: 是否为命令
        """
        return "command" in self and bool(self.get("command"))

    # ==================== 工具方法 ====================

    def to_dict(self) -> dict[str, Any]:
        """
        转换为字典

        :return: 事件数据字典
        """
        return dict(self)

    def is_processed(self) -> bool:
        """
        是否已被处理

        :return: 是否已被处理
        """
        return self.get("_processed", False)

    def mark_processed(self):
        """
        标记为已处理
        """
        self["_processed"] = True

    # ==================== 魔术方法 ====================

    def __getattr__(self, name: str) -> Any:
        """
        属性查找优先级：
        1. 平台注册的扩展方法（仅当前平台）
        2. 字典键访问（点式访问 event.platform 等）

        :param name: 属性名
        :return: 属性值
        :raises AttributeError: 属性不存在
        """
        # 1. 查找当前平台的扩展方法
        platform = dict.get(self, "platform", "")
        if (
            platform_methods := _platform_event_methods.get(platform)
        ) and name in platform_methods:
            func = platform_methods[name]
            # 使用方法描述符协议绑定 self，使 isinstance 检查和 super() 正常工作
            return func.__get__(self, type(self))

        # 2. 兜底：字典键访问
        try:
            return self[name]
        except KeyError:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{name}'"
            )

    def __dir__(self) -> list[str]:
        """
        让 dir(event) 包含当前平台注册的扩展方法名
        """
        names = super().__dir__()
        # 添加当前平台的扩展方法名
        platform = dict.get(self, "platform", "")
        platform_methods = _platform_event_methods.get(platform)
        if platform_methods:
            names = list(names) + list(platform_methods.keys())
        return sorted(set(names))

    def __repr__(self) -> str:
        """
        字符串表示

        :return: 字符串表示
        """
        event_type = self.get_type()
        detail_type = self.get_detail_type()
        platform = self.get_platform()
        return (
            f"Event(type={event_type}, detail_type={detail_type}, platform={platform})"
        )


__all__ = [
    "Event",
    # 平台事件方法注册
    "register_event_mixin",
    "register_event_method",
    "unregister_event_method",
    "unregister_platform_event_methods",
    "get_platform_event_methods",
]
