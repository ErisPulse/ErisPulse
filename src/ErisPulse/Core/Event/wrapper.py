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

import asyncio
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


CONFIRM_YES_WORDS = frozenset({
    "是", "yes", "y", "确认", "确定", "好", "好的",
    "ok", "okay", "true", "对", "嗯", "行",
    "同意", "没问题", "可以", "当然", "嗯嗯", "是的",
})

CONFIRM_NO_WORDS = frozenset({
    "否", "no", "n", "取消", "不", "不要", "不行",
    "cancel", "false", "错", "不对", "别",
    "拒绝", "不可以", "算了", "不需要", "不是",
})


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

        if result:
            return Event(result)
        return None

    # ==================== 交互式对话方法 ====================

    async def confirm(
        self,
        prompt: str = None,
        timeout: float = 60.0,
        yes_words: set[str] | frozenset[str] = None,
        no_words: set[str] | frozenset[str] = None,
    ) -> Optional[bool]:
        """
        等待用户确认 (是/否)

        自动发送提示消息并等待用户回复，识别内置中英文确认词。
        内置确认词: 是/yes/y/确认/确定/好/ok/true/对/嗯/行/同意/没问题... (否/no/n/取消/不/不要/cancel/false/错/拒绝...)

        :param prompt: str - 提示消息（可选，发送后等待回复）
        :param timeout: float - 超时时间(秒)（默认: 60.0）
        :param yes_words: set[str] - 自定义确认词集合（默认: 内置 CONFIRM_YES_WORDS）
        :param no_words: set[str] - 自定义否定词集合（默认: 内置 CONFIRM_NO_WORDS）
        :return: bool|None - True=确认, False=否定, None=超时

        :raises ValueError: 当 yes_words 或 no_words 为空集合时

        :example:
        >>> if await event.confirm("确定要执行此操作吗？"):
        ...     await event.reply("已执行")
        >>> # 自定义确认词
        >>> if await event.confirm("继续吗？", yes_words={"go", "run"}, no_words={"stop", "quit"}):
        ...     await event.reply("开始执行")
        """
        _yes = frozenset(w.lower() for w in (yes_words or CONFIRM_YES_WORDS))
        _no = frozenset(w.lower() for w in (no_words or CONFIRM_NO_WORDS))
        _all = _yes | _no
        _yes = frozenset(w.lower() for w in (yes_words or CONFIRM_YES_WORDS))
        _no = frozenset(w.lower() for w in (no_words or CONFIRM_NO_WORDS))
        _all = _yes | _no

        def validator(event_dict: dict[str, Any]) -> bool:
            text = event_dict.get("alt_message", "").strip().lower()
            return text in _all

        result = await self.wait_reply(prompt=prompt, timeout=timeout, validator=validator)

        if result is None:
            return None

        text = result.get("alt_message", "").strip().lower()
        return text in _yes

    async def choose(
        self,
        prompt: str,
        options: list[str],
        timeout: float = 60.0,
    ) -> Optional[int]:
        """
        等待用户从选项中选择

        自动发送编号选项列表 (1.选项1 2.选项2 ...)，用户可回复编号或选项文本

        :param prompt: str - 提示消息（必须）
        :param options: list[str] - 选项列表（不能为空）
        :param timeout: float - 超时时间(秒)（默认: 60.0）
        :return: int|None - 选中选项的索引(0-based), 超时返回 None

        :raises ValueError: 当 options 为空时

        :example:
        >>> choice = await event.choose("请选择颜色:", ["红", "绿", "蓝"])
        >>> if choice is not None:
        ...     await event.reply(f"你选择了: {['红','绿','蓝'][choice]}")
        """
        if not options:
            raise ValueError("选项列表不能为空")

        options_text = "\n".join(f"{i + 1}. {opt}" for i, opt in enumerate(options))
        full_prompt = f"{prompt}\n{options_text}" if prompt else options_text

        index_map = {str(i + 1): i for i in range(len(options))}
        lower_text_map = {opt.lower(): i for i, opt in enumerate(options)}
        valid_inputs = set(index_map.keys()) | set(lower_text_map.keys())

        def validator(event_dict: dict[str, Any]) -> bool:
            text = event_dict.get("alt_message", "").strip().lower()
            return text in valid_inputs

        result = await self.wait_reply(prompt=full_prompt, timeout=timeout, validator=validator)

        if result is None:
            return None

        text = result.get("alt_message", "").strip().lower()
        if text in index_map:
            return index_map[text]
        if text in lower_text_map:
            return lower_text_map[text]
        return None

    async def collect(
        self,
        fields: list[dict[str, Any]],
        timeout_per_field: float = 60.0,
    ) -> Optional[dict[str, str]]:
        """
        多步骤收集信息 (表单式)

        依次向用户发送提示消息并收集回复，每个字段可配置验证器和重试逻辑

        :param fields: list[dict] - 字段列表，每个字段为字典:
            - key: str - 字段键名（必须）
            - prompt: str - 提示消息（默认: "请输入 {key}"）
            - validator: callable - 验证函数，接收 Event 对象，返回 bool（可选）
            - retry_prompt: str - 验证失败时的重试提示（默认: "输入无效，请重新输入"）
            - max_retries: int - 最大重试次数（默认: 3）
        :param timeout_per_field: float - 每个字段的超时时间(秒)（默认: 60.0）
        :return: dict|None - 收集到的数据字典, 任何步骤超时或重试耗尽返回 None

        :example:
        >>> data = await event.collect([
        ...     {"key": "name", "prompt": "请输入姓名"},
        ...     {"key": "age", "prompt": "请输入年龄",
        ...      "validator": lambda e: e.get("alt_message", "").strip().isdigit()},
        ... ])
        >>> if data:
        ...     await event.reply(f"姓名: {data['name']}, 年龄: {data['age']}")
        """
        if not fields:
            return {}

        result = {}

        for field in fields:
            key = field.get("key")
            if not key:
                continue

            prompt = field.get("prompt", f"请输入 {key}")
            validator = field.get("validator")
            retry_prompt = field.get("retry_prompt", "输入无效，请重新输入")
            max_retries = field.get("max_retries", 3)

            reply = await self.wait_reply(prompt=prompt, timeout=timeout_per_field)

            if reply is None:
                return None

            if validator:
                retries = 0
                while not validator(reply):
                    retries += 1
                    if retries >= max_retries:
                        return None
                    reply = await self.wait_reply(prompt=retry_prompt, timeout=timeout_per_field)
                    if reply is None:
                        return None

            result[key] = reply.get("alt_message", "").strip()

        return result

    async def wait_for(
        self,
        event_type: str = "message",
        condition: Callable[["Event"], bool] = None,
        timeout: float = 60.0,
    ) -> Optional["Event"]:
        """
        等待满足条件的任意事件

        不限于同一用户/会话，可监听任意类型事件

        :param event_type: str - 事件类型 (message/notice/request/meta 等，默认: message)
        :param condition: callable - 条件函数，接收 Event 对象，返回 bool（可选）
        :param timeout: float - 超时时间(秒)（默认: 60.0）
        :return: Event|None - 匹配的事件, 超时返回 None

        :example:
        >>> # 等待群成员加入通知
        >>> evt = await event.wait_for(
        ...     "notice",
        ...     condition=lambda e: e.get_detail_type() == "group_member_increase",
        ...     timeout=120,
        ... )
        >>>
        >>> # 等待任意消息包含特定关键词
        >>> evt = await event.wait_for(
        ...     condition=lambda e: "hello" in e.get_text(),
        ... )
        """
        loop = asyncio.get_running_loop()
        future = loop.create_future()

        async def _temp_handler(event_data):
            if future.done():
                return
            evt = event_data if isinstance(event_data, Event) else Event(event_data)
            try:
                if condition is None or condition(evt):
                    if not future.done():
                        raw = event_data if isinstance(event_data, dict) else dict(event_data)
                        future.set_result(raw)
            except Exception:
                pass

        handler_wrapper = {"func": _temp_handler, "platform": None}
        adapter._onebot_handlers[event_type].append(handler_wrapper)

        try:
            raw_result = await asyncio.wait_for(future, timeout=timeout)
            return Event(raw_result) if raw_result is not None else None
        except asyncio.TimeoutError:
            return None
        finally:
            try:
                adapter._onebot_handlers[event_type].remove(handler_wrapper)
            except (ValueError, KeyError):
                pass

    def conversation(self, timeout: float = 60.0) -> "Conversation":
        """
        创建多轮对话上下文

        :param timeout: 默认超时时间(秒)
        :return: Conversation 对象

        :example:
        >>> conv = event.conversation(timeout=30)
        >>> await conv.say("欢迎！请问有什么需要帮助的？")
        >>> while conv.is_active:
        ...     resp = await conv.wait()
        ...     if resp is None:
        ...         await conv.say("会话超时，再见！")
        ...         break
        ...     if resp.get_text() == "退出":
        ...         await conv.say("再见！")
        ...         break
        """
        return Conversation(self, timeout=timeout)

    # ==================== 原始数据和元信息 ====================

    def get_raw(self) -> dict[str, Any]:
        """
        获取原始事件数据

        :return: dict - 原始事件数据字典
        """
        platform = self.get_platform()
        raw_key = f"{platform}_raw" if platform else "raw"
        return self.get(raw_key, {})

    def get_raw_type(self) -> str:
        """
        获取原始事件类型

        :return: str - 原始事件类型
        """
        platform = self.get_platform()
        raw_type_key = f"{platform}_raw_type" if platform else "raw_type"
        return self.get(raw_type_key, "")

    # ==================== 命令信息 ====================

    def get_command_name(self) -> str:
        """
        获取命令名称

        :return: str - 命令名称
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
        属性查找优先级:
        1. 平台注册的扩展方法（仅当前平台）
        2. 字典键访问（点式访问 event.platform 等）

        :param name: str - 属性名
        :return: Any - 属性值
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


class Conversation:
    """
    多轮对话上下文

    提供在同一会话中进行多轮交互的便捷方法

    {!--< tips >!--}
    1. 通过 event.conversation() 方法创建
    2. 超时后自动标记为非活跃状态
    3. 支持链式调用 say() 方法
    {!--< /tips >!--}
    """

    def __init__(self, event: "Event", timeout: float = 60.0):
        """
        初始化对话上下文

        :param event: Event - 事件对象
        :param timeout: float - 默认超时时间(秒)（默认: 60.0）
        """
        self._event = event
        self._timeout = timeout
        self._alive = True

    @property
    def is_active(self) -> bool:
        """
        对话是否处于活跃状态

        :return: bool - 是否活跃
        """
        return self._alive

    async def say(self, content: str, **kwargs) -> "Conversation":
        """
        发送消息

        :param content: str - 消息内容
        :return: Conversation - self（支持链式调用）
        """
        await self._event.reply(content, **kwargs)
        return self

    async def wait(self, prompt: str = None, timeout: float = None) -> Optional["Event"]:
        """
        等待用户回复

        :param prompt: str - 提示消息（可选）
        :param timeout: float - 超时时间(秒)，默认使用对话的超时设置
        :return: Event|None - 用户回复的事件, 超时返回 None
        """
        if not self._alive:
            return None
        result = await self._event.wait_reply(
            prompt=prompt,
            timeout=timeout if timeout is not None else self._timeout,
        )
        if result is None:
            self._alive = False
        return result

    async def confirm(self, prompt: str = None, **kwargs) -> Optional[bool]:
        """
        等待用户确认

        :param prompt: str - 提示消息
        :return: bool|None - True/False/None
        """
        if not self._alive:
            return None
        return await self._event.confirm(
            prompt=prompt,
            timeout=kwargs.pop("timeout", self._timeout),
            **kwargs,
        )

    async def choose(self, prompt: str, options: list[str], **kwargs) -> Optional[int]:
        """
        等待用户选择

        :param prompt: str - 提示消息
        :param options: list[str] - 选项列表
        :return: int|None - 选中索引或 None
        """
        if not self._alive:
            return None
        return await self._event.choose(
            prompt, options,
            timeout=kwargs.pop("timeout", self._timeout),
            **kwargs,
        )

    async def collect(self, fields: list[dict], **kwargs) -> Optional[dict]:
        """
        多步骤收集信息

        :param fields: list[dict] - 字段列表
        :return: dict|None - 收集到的数据字典或 None
        """
        if not self._alive:
            return None
        result = await self._event.collect(
            fields,
            timeout_per_field=kwargs.pop("timeout_per_field", self._timeout),
            **kwargs,
        )
        if result is None:
            self._alive = False
        return result

    def stop(self):
        """
        结束对话
        """
        self._alive = False


__all__ = [
    "Event",
    "Conversation",
    "CONFIRM_YES_WORDS",
    "CONFIRM_NO_WORDS",
    # 平台事件方法注册
    "register_event_mixin",
    "register_event_method",
    "unregister_event_method",
    "unregister_platform_event_methods",
    "get_platform_event_methods",
]
