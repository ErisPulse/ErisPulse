"""
ErisPulse 事件包装类

提供便捷的事件访问方法

{!--< tips >!--}
1. 继承自dict，完全兼容字典访问
2. 提供便捷方法简化事件处理
3. 支持点式访问 event.platform
4. 支持适配器通过 register_event_mixin / register_event_method 注册平台专有方法
5. 建议在处理器参数中使用类型注解以获得 IDE 自动补全: async def handler(event: Event)
{!--< /tips >!--}
"""

import asyncio
import inspect
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Optional, TypedDict

from .. import adapter, logger
from ..constants import (
    CONFIRM_NO_WORDS,
    CONFIRM_YES_WORDS,
    CONVERSATION_KEY_PREFIX,
    DEFAULT_INTERACTION_CHECKPOINT_TTL_SECS,
    DEFAULT_MAX_RETRIES,
    DEFAULT_SEND_METHOD,
    DEFAULT_WAIT_TIMEOUT_SECS,
    DETAIL_TYPE_FRIEND,
    DETAIL_TYPE_FRIEND_DECREASE,
    DETAIL_TYPE_FRIEND_INCREASE,
    DETAIL_TYPE_GROUP,
    DETAIL_TYPE_GROUP_MEMBER_DECREASE,
    DETAIL_TYPE_GROUP_MEMBER_INCREASE,
    DETAIL_TYPE_PRIVATE,
    EVENT_TYPE_MESSAGE,
    EVENT_TYPE_NOTICE,
    EVENT_TYPE_REQUEST,
    TEXT_METHOD_INDICATORS,
)
from ..i18n import i18n
from .session_type import (
    get_send_type_and_target_id,
)


class EventData(TypedDict, total=False):
    """
    OneBot12 标准事件数据结构

    {!--< tips >!--}
    所有字段均为可选（total=False），实际字段取决于事件类型。
    详见 [适配器标准化转换规范](../../standards/event-conversion.md)
    {!--< /tips >!--}

    :ivar id: str 事件唯一标识符
    :ivar time: int Unix时间戳（秒级）
    :ivar type: str 事件类型（message/notice/request/meta）
    :ivar detail_type: str 事件详细类型（详见会话类型标准）
    :ivar sub_type: str 子类型
    :ivar platform: str 平台名称
    :ivar self: dict 机器人信息（含 platform, user_id）
    :ivar message_id: str 消息ID
    :ivar message: list 消息段数组
    :ivar alt_message: str 纯文本消息
    :ivar user_id: str 用户ID
    :ivar user_nickname: str 用户昵称
    :ivar group_id: str 群组ID
    :ivar guild_id: str 频道ID
    :ivar channel_id: str 子频道ID
    :ivar thread_id: str 主题ID
    :ivar operator_id: str 操作者ID
    :ivar comment: str 请求附言
    :ivar request_id: str 请求标识符
    """
    id: str
    time: int
    type: str
    detail_type: str
    sub_type: str
    platform: str
    self: dict
    message_id: str
    message: list
    alt_message: str
    user_id: str
    user_nickname: str
    group_id: str
    guild_id: str
    channel_id: str
    thread_id: str
    operator_id: str
    comment: str
    request_id: str


# ==================== 平台事件方法注册系统 ====================

# 注册表: {platform: {method_name: callable}}
# platform 为 "*" 时表示跨所有平台生效（通配符）
_platform_event_methods: dict[str, dict[str, Callable]] = {}


def register_event_mixin(platform: str, mixin_cls: type) -> int:
    """
    注册一个类的所有公开方法到指定平台

    适配器可以创建一个 Mixin 类集中定义平台专有方法，
    然后通过此函数一次性注册。

    注册的方法会通过 Event.__getattribute__ 优先于内置方法生效，
    因此可以覆写 confirm / choose / collect / wait_reply 等内置交互式方法。

    :param platform: 平台名称（需与适配器注册名一致），传 "*" 表示对所有平台生效
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

    registered = 0

    for name, func in inspect.getmembers(mixin_cls, predicate=inspect.isfunction):
        if name.startswith("_"):
            continue
        _platform_event_methods[platform][name] = func
        registered += 1

    logger.trace(i18n.t("core.event.registered_extensions", platform=platform, count=registered))
    return registered


def register_event_method(platform: str):
    """
    装饰器：注册单个方法到指定平台

    适合少量方法或动态注册的场景。

    注册的方法会通过 Event.__getattribute__ 优先于内置方法生效，
    因此可以覆写 confirm / choose / collect / wait_reply 等内置交互式方法。

    :param platform: 平台名称（需与适配器注册名一致），传 "*" 表示对所有平台生效

    :example:
    >>> @register_event_method("email")
    ... def get_subject(self):
    ...     return self.get("email_raw", {}).get("subject", "")
    >>>
    >>> # 跨平台通配符
    >>> @register_event_method("*")
    ... def ai_chat(self, prompt):
    ...     return await self.reply(f"AI: {prompt}")
    """

    def decorator(func: Callable) -> Callable:
        if platform not in _platform_event_methods:
            _platform_event_methods[platform] = {}

        name = func.__name__

        if name.startswith("_"):
            return func

        _platform_event_methods[platform][name] = func
        logger.trace(i18n.t("core.event.registered_extension", platform=platform, name=name))
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
        logger.trace(i18n.t("core.event.unregistered_extensions", platform=platform, count=count))
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


# ==================== 内置交互式方法实现 ====================


async def _builtin_wait_reply(
    event: "Event",
    prompt: str | None = None,
    timeout: float = DEFAULT_WAIT_TIMEOUT_SECS,
    callback: Callable[[dict[str, Any]], Awaitable[Any]] | None = None,
    validator: Callable[[dict[str, Any]], bool] | None = None,
    method: str = DEFAULT_SEND_METHOD,
    pattern: str | None = None,
    regex: str | None = None,
) -> Optional["Event"]:
    """
    内置 wait_reply 实现

    供覆写函数调用以复用内置等待逻辑。

    :param pattern: glob 通配符，回复文本不匹配时继续等待（超时返回 None）
    :param regex: 正则表达式，回复文本不匹配时继续等待（与 pattern 同时给定时须都匹配）
    """
    from .command import command as command_handler

    result = await command_handler.wait_reply(
        event=event._event_data if isinstance(event, Event) else event,
        prompt=prompt,
        timeout=timeout,
        callback=callback,
        validator=validator,
        method=method,
        pattern=pattern,
        regex=regex,
    )

    if result:
        return Event(result)
    return None


async def _builtin_confirm(
    event: "Event",
    prompt: str | None = None,
    timeout: float = DEFAULT_WAIT_TIMEOUT_SECS,
    yes_words: set[str] | frozenset[str] | None = None,
    no_words: set[str] | frozenset[str] | None = None,
    method: str = DEFAULT_SEND_METHOD,
    hint: bool = False,
) -> bool | None:
    """
    内置 confirm 实现

    供覆写函数调用以复用内置确认逻辑。
    """
    _yes = frozenset(w.lower() for w in (yes_words or CONFIRM_YES_WORDS))
    _no = frozenset(w.lower() for w in (no_words or CONFIRM_NO_WORDS))
    _all = _yes | _no

    def validator(event_dict: dict[str, Any]) -> bool:
        text = event_dict.get("alt_message", "").strip().lower()
        return text in _all

    actual_prompt = prompt
    if hint and prompt:
        from ..constants import CONFIRM_HINT_WORDS

        lang = i18n.get_language() or "zh-CN"
        yes_word, no_word = CONFIRM_HINT_WORDS.get(lang, CONFIRM_HINT_WORDS["en"])
        actual_prompt = i18n.t(
            "core.event.confirm_hint",
            prompt=prompt,
            yes=yes_word,
            no=no_word,
            default=f"{prompt} ({yes_word}/{no_word})",
        )

    result = await _builtin_wait_reply(
        event,
        prompt=actual_prompt,
        timeout=timeout,
        validator=validator,
        method=method,
    )

    if result is None:
        return None

    text = result.get("alt_message", "").strip().lower()
    return text in _yes


def _format_options(
    options: list[str],
    fmt: str | Callable[[list[str]], str],
    method: str = DEFAULT_SEND_METHOD,
) -> str:
    """
    格式化选项列表为文本

    :param options: 选项列表
    :param fmt: 格式类型，支持 "auto"（根据 method 自动选择）、"list"、"inline"、"md"、"html" 或自定义函数
    :param method: 发送方法名，fmt="auto" 时用于推断合适的格式
    :return: 格式化后的选项文本
    """
    if callable(fmt):
        return fmt(options)

    # auto：根据 method 选择内置样式
    if fmt == "auto":
        method_lower = method.lower()
        if "md" in method_lower or "markdown" in method_lower:
            fmt = "md"
        elif "html" in method_lower or "h5" in method_lower:
            fmt = "html"
        else:
            fmt = "list"

    if fmt == "inline":
        return " | ".join(f"{i + 1}.{opt}" for i, opt in enumerate(options))
    if fmt == "md":
        # Markdown 无序列表样式
        return "\n".join(f"- {i + 1}. {opt}" for i, opt in enumerate(options))
    if fmt == "html":
        # Html 无序列表 + 手动编号（<ol> 在不同渲染器可能显示为罗马数字/字母）
        items = "".join(f"<li>{i + 1}. {opt}</li>" for i, opt in enumerate(options))
        return f"<ul>{items}</ul>"
    # 默认 "list"
    return "\n".join(f"{i + 1}. {opt}" for i, opt in enumerate(options))


def _merge_prompt_options(
    prompt: str,
    options_text: str,
    placeholder: str = "{options}",
) -> str:
    """
    将选项文本合并到提示消息中

    如果 prompt 包含占位符（默认 ``{options}``），则替换占位符；
    否则将选项追加到 prompt 末尾（用换行分隔）。

    :param prompt: 提示消息（可能包含占位符）
    :param options_text: 已格式化的选项文本
    :param placeholder: 占位符标记，prompt 中出现该标记的位置将被替换为选项文本
    :return: 合并后的完整提示消息
    """
    if placeholder and placeholder in prompt:
        return prompt.replace(placeholder, options_text)
    return f"{prompt}\n{options_text}" if prompt else options_text

def _is_text_method(method: str) -> bool:
    """
    判断发送方法是否为文本类（内容可拼接选项文本）

    通过大小写不敏感的子串匹配：方法名包含 text/md/markdown/html/h5 即视为文本类。
    设计原则是“只要不是明确的富媒体就合并”，减少拆分消息的情况。

    :param method: 发送方法名
    :return: True 表示该方法是文本类，选项可直接拼接到末尾
    """
    method_lower = method.lower()
    return any(ind in method_lower for ind in TEXT_METHOD_INDICATORS)


async def _builtin_choose(
    event: "Event",
    prompt: str,
    options: list[str],
    timeout: float = DEFAULT_WAIT_TIMEOUT_SECS,
    method: str = DEFAULT_SEND_METHOD,
    options_format: str | Callable[[list[str]], str] = "auto",
    merge_prompt: bool = False,
    placeholder: str = "{options}",
) -> int | None:
    """
    内置 choose 实现

    供覆写函数调用以复用内置选择逻辑。

    发送行为取决于 method 和 merge_prompt：
    - 文本类方法 (Text/Markdown/md/Html/h5 等): 选项默认拼接到 prompt 末尾，一条消息发送
    - 非文本方法 (Image/Voice 等) + merge_prompt=False: 先发富媒体 prompt，再发 Text 选项
    - 任意方法 + merge_prompt=True: 强制合并为一条消息发送（用用户指定的 method）
    - prompt 含占位符（默认 ``{options}``，可通过 placeholder 自定义）时，替换该位置；否则追加到末尾
    - options_format="auto" 时根据 method 自动选择内置样式（Markdown→无序列表，Html→有序列表）
    """
    if not options:
        raise ValueError(i18n.t("core.event.option_list_empty"))

    options_text = _format_options(options, options_format, method)

    index_map = {str(i + 1): i for i in range(len(options))}
    lower_text_map = {opt.lower(): i for i, opt in enumerate(options)}
    valid_inputs = set(index_map.keys()) | set(lower_text_map.keys())

    def validator(event_dict: dict[str, Any]) -> bool:
        text = event_dict.get("alt_message", "").strip().lower()
        return text in valid_inputs

    if _is_text_method(method) or merge_prompt:
        # 文本类方法 或 强制合并：选项拼入 prompt，用用户指定的 method 一条消息发送
        full_prompt = _merge_prompt_options(prompt, options_text, placeholder) if prompt else options_text
        result = await _builtin_wait_reply(
            event,
            prompt=full_prompt,
            timeout=timeout,
            validator=validator,
            method=method,
        )
    else:
        # 非文本方法：先发 prompt（用用户的 method），再发选项（用 Text）
        if prompt:
            await event.reply(prompt, method=method)
        result = await _builtin_wait_reply(
            event,
            prompt=options_text,
            timeout=timeout,
            validator=validator,
            method=DEFAULT_SEND_METHOD,
        )

    if result is None:
        return None

    text = result.get("alt_message", "").strip().lower()
    if text in index_map:
        return index_map[text]
    if text in lower_text_map:
        return lower_text_map[text]
    return None


async def _builtin_collect(
    event: "Event",
    fields: list[dict[str, Any]],
    timeout_per_field: float = 60.0,
) -> dict[str, str] | None:
    """
    内置 collect 实现

    供覆写函数调用以复用内置收集逻辑。
    每个 field 支持 `method` 键来指定发送方法。
    """
    if not fields:
        return {}

    result = {}

    for field in fields:
        key = field.get("key")
        if not key:
            from ..logger import logger as _logger

            _logger.warning(i18n.t("core.event.collect_field_missing_key", field=field))
            continue

        prompt = field.get("prompt", i18n.t("core.event.collect_default_prompt", key=key))
        validator = field.get("validator")
        retry_prompt = field.get("retry_prompt", i18n.t("core.event.collect_invalid_retry"))
        max_retries = field.get("max_retries", DEFAULT_MAX_RETRIES)
        method = field.get("method", DEFAULT_SEND_METHOD)
        options = field.get("options")
        options_format = field.get("options_format", "auto")
        merge_prompt = field.get("merge_prompt", False)
        placeholder = field.get("placeholder", "{options}")

        if options:
            reply = await _builtin_choose(
                event,
                prompt=prompt,
                options=options,
                timeout=timeout_per_field,
                method=method,
                options_format=options_format,
                merge_prompt=merge_prompt,
                placeholder=placeholder,
            )
            if reply is None:
                return None
            result[key] = options[reply]
            continue

        reply = await _builtin_wait_reply(
            event,
            prompt=prompt,
            timeout=timeout_per_field,
            method=method,
        )

        if reply is None:
            return None

        if validator:
            retries = 0
            while not validator(reply):
                retries += 1
                if retries >= max_retries:
                    return None
                reply = await _builtin_wait_reply(
                    event,
                    prompt=retry_prompt,
                    timeout=timeout_per_field,
                    method=method,
                )
                if reply is None:
                    return None

        result[key] = reply.get("alt_message", "").strip()

    return result


def _normalize_modifier(mod) -> tuple[str, tuple, dict]:
    """
    {!--< internal-use >!--}
    归一化修饰方法定义为 (name, args, kwargs)

    支持以下形式：
    - ``"Name"``                            → ``("Name", (), {})``
    - ``("Name",)``                         → ``("Name", (), {})``
    - ``("Name", arg1, arg2, ...)``         → ``("Name", (arg1, arg2, ...), {})``
    - ``("Name", (arg1, arg2), kwargs_dict)`` → 显式位置参数 + 关键字参数

    :param mod: str|tuple - 修饰方法定义（字符串或元组）
    :return: tuple - ``(方法名, 位置参数元组, 关键字参数字典)``
    """
    if isinstance(mod, str):
        return mod, (), {}
    name = mod[0]
    if len(mod) == 1:
        return name, (), {}
    if len(mod) == 3 and isinstance(mod[2], dict):
        args = mod[1] if isinstance(mod[1], (list, tuple)) else (mod[1],)
        return name, tuple(args), mod[2]
    return name, tuple(mod[1:]), {}


@dataclass
class Expectation:
    """
    等待期望描述（:meth:`Event.expect` 创建，传给 :meth:`Event.select` 做多路等待）

    本身不注册任何等待——仅在 ``select()`` 调用时统一注册，
    任一路命中即返回该路结果，其余自动取消。

    :attribute pattern: glob 文本过滤（``*`` / ``?`` / ``[seq]``）
    :attribute regex: 正则文本过滤（与 pattern 同时给定时须都匹配）
    :attribute validator: 回复校验函数（接收 Event，返回 bool）
    :attribute user: 限定回复者 user_id（None 不限定）
    :attribute session: 会话级等待（同会话任何人可命中，忽略 user）
    """

    pattern: str | None = None
    regex: str | None = None
    validator: Any = None
    user: str | None = None
    session: bool = False


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

    def get_self_account_id(self) -> str:
        """
        获取机器人账户标识（多Bot模式）

        优先返回 account_id（ErisPulse扩展），若不存在则回退到 user_id（OB12标准）

        :return: 机器人账户标识，单Bot模式下返回空字符串
        """
        self_info = self.get("self", {})
        return self_info.get("account_id", "") or self_info.get("user_id", "")

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

    def is_master(self) -> bool:
        """
        检查事件发送者是否为框架主人

        基于 ``ErisPulse.master.users`` 配置和运行时添加的主人列表判断。

        :return: 是否为框架主人

        :example:
        >>> if event.is_master():
        ...     await event.reply("主人你好")
        """
        from ..master import master

        return master.is_master(
            self.get_platform(),
            self.get_user_id(),
        )

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

    def get_target_id(self) -> str:
        """
        获取当前会话的目标ID（统一接口）

        根据事件类型自动返回对应的目标ID：
        群聊 → group_id，频道 → channel_id，私聊 → user_id，以此类推。

        :return: 目标ID字符串，无法确定时返回空字符串

        :example:
        >>> target = event.get_target_id()
        >>> # 群聊事件 → group_id
        >>> # 私聊事件 → user_id
        """
        for key in (
            "group_id",
            "channel_id",
            "guild_id",
            "thread_id",
            "user_id",
        ):
            value = self.get(key, "")
            if value:
                return str(value)
        return ""

    def get_session_id(self) -> str:
        """
        生成会话唯一标识

        格式: ``{platform}:{detail_type}:{target_id}``
        如: ``telegram:private:12345``、``qq:group:67890``

        用于存储、上下文管理等需要唯一标识会话的场景。

        :return: 会话标识字符串

        :example:
        >>> session_id = event.get_session_id()
        >>> # "qq:group:123456"
        """
        return f"{self.get_platform()}:{self.get_detail_type()}:{self.get_target_id()}"

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
        return self.get_type() == EVENT_TYPE_MESSAGE

    def is_private_message(self) -> bool:
        """
        是否为私聊消息

        :return: 是否为私聊消息
        """
        return self.is_message() and self.get_detail_type() == DETAIL_TYPE_PRIVATE

    def is_group_message(self) -> bool:
        """
        是否为群聊消息

        :return: 是否为群聊消息
        """
        return self.is_message() and self.get_detail_type() == DETAIL_TYPE_GROUP

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
        return self.get_type() == EVENT_TYPE_NOTICE

    def is_group_member_increase(self) -> bool:
        """
        群成员增加

        :return: 是否为群成员增加事件
        """
        return (
            self.is_notice()
            and self.get_detail_type() == DETAIL_TYPE_GROUP_MEMBER_INCREASE
        )

    def is_group_member_decrease(self) -> bool:
        """
        群成员减少

        :return: 是否为群成员减少事件
        """
        return (
            self.is_notice()
            and self.get_detail_type() == DETAIL_TYPE_GROUP_MEMBER_DECREASE
        )

    def is_friend_add(self) -> bool:
        """
        好友添加

        :return: 是否为好友添加事件
        """
        return (
            self.is_notice() and self.get_detail_type() == DETAIL_TYPE_FRIEND_INCREASE
        )

    def is_friend_delete(self) -> bool:
        """
        好友删除

        :return: 是否为好友删除事件
        """
        return (
            self.is_notice() and self.get_detail_type() == DETAIL_TYPE_FRIEND_DECREASE
        )

    # ==================== 请求事件专用方法 ====================

    def get_comment(self) -> str:
        """
        获取请求附言

        :return: 请求附言
        """
        return self.get("comment", "")

    def get_request_id(self) -> str:
        """
        获取请求ID

        用于标识可操作的请求，配合 approve()/reject() 使用。

        :return: 请求ID，不存在时返回空字符串
        """
        return self.get("request_id", "")

    async def approve(self, comment: str | None = None) -> Any:
        """
        同意当前请求事件

        通过适配器的 Request DSL 执行同意操作。
        仅对请求类型事件（type == "request"）有效。

        :param comment: 附带备注信息（可选，部分平台支持）
        :return: 标准响应格式

        :raises ValueError: 当事件不是请求类型或缺少必要字段时

        :example:
        >>> @request.on_friend_request()
        ... async def handle_friend_request(event):
        ...     await event.approve()
        ...     # 带备注
        ...     await event.approve(comment="欢迎添加好友")
        """
        return await self._handle_request_action("accept", comment)

    async def reject(self, comment: str | None = None) -> Any:
        """
        拒绝当前请求事件

        通过适配器的 Request DSL 执行拒绝操作。
        仅对请求类型事件（type == "request"）有效。

        :param comment: 附带备注信息（可选，部分平台支持）
        :return: 标准响应格式

        :raises ValueError: 当事件不是请求类型或缺少必要字段时

        :example:
        >>> @request.on_group_request()
        ... async def handle_group_request(event):
        ...     await event.reject()
        """
        return await self._handle_request_action("reject", comment)

    async def _handle_request_action(self, action: str, comment: str | None = None) -> Any:
        """
        执行请求操作的内部方法

        :param action: 操作类型 ("accept" / "reject")
        :param comment: 附带备注
        :return: 标准响应格式
        :raises ValueError: 当缺少必要字段时
        """
        if not self.is_request():
            raise ValueError(
                i18n.t(
                    "core.event.not_request_type",
                    type=self.get_type(),
                    action=action,
                )
            )

        platform = self.get_platform()
        if not platform:
            raise ValueError(i18n.t("core.event.missing_platform"))

        adapter_instance = getattr(adapter, platform, None)
        if not adapter_instance:
            available = (
                list(adapter._adapters.keys()) if hasattr(adapter, "_adapters") else []
            )
            raise ValueError(
                i18n.t(
                    "core.event.adapter_not_found",
                    platform=platform,
                    available=available,
                )
            )

        request_id = self.get_request_id()
        if not request_id:
            raise ValueError(
                i18n.t("core.event.request_missing_id", action=action)
            )

        bot_id = self.get("self", {}).get("account_id", "") or self.get("self", {}).get(
            "user_id", ""
        )

        handler = adapter_instance.Request(request_id)

        if bot_id:
            handler = handler.Using(bot_id)

        method = getattr(handler, action)
        kwargs = {}
        if comment:
            kwargs["comment"] = comment
        return await method(**kwargs)

    # ==================== 请求类型判断 ====================

    def is_request(self) -> bool:
        """
        是否为请求事件

        :return: 是否为请求事件
        """
        return self.get_type() == EVENT_TYPE_REQUEST

    def is_friend_request(self) -> bool:
        """
        是否为好友请求

        :return: 是否为好友请求
        """
        return self.is_request() and self.get_detail_type() == DETAIL_TYPE_FRIEND

    def is_group_request(self) -> bool:
        """
        是否为群组请求

        :return: 是否为群组请求
        """
        return self.is_request() and self.get_detail_type() == DETAIL_TYPE_GROUP

    # ==================== 回复功能 ====================

    def _get_adapter_and_target(self) -> tuple[Any, str, str, str]:
        """
        获取适配器实例和目标信息

        使用会话类型管理模块自动处理类型转换和ID获取

        :return: (适配器实例, 发送目标类型, 目标ID, 账户ID)
        """
        platform = self.get_platform()
        if not platform:
            raise ValueError(
                i18n.t("core.event.missing_platform_with_id", event_id=self.get_id())
            )

        if not (adapter_instance := getattr(adapter, platform, None)):
            available = (
                list(adapter._adapters.keys()) if hasattr(adapter, "_adapters") else []
            )
            raise ValueError(
                i18n.t(
                    "core.event.adapter_not_found",
                    platform=platform,
                    available=available,
                )
            )

        # 使用会话类型管理模块获取发送类型和目标ID
        send_type, target_id = get_send_type_and_target_id(self, platform)

        if not target_id:
            raise ValueError(
                i18n.t(
                    "core.event.target_id_not_found",
                    platform=platform,
                    detail_type=self.get_detail_type(),
                    user_id=self.get_user_id(),
                    group_id=self.get_group_id(),
                )
            )

        bot_id = self.get("self", {}).get("account_id", "") or self.get("self", {}).get(
            "user_id", ""
        )

        return adapter_instance, send_type, target_id, bot_id

    async def reply(
        self,
        content: str,
        method: str | None = None,
        at_sender: bool = False,
        quote: bool = False,
        at_users: list[str] | None = None,
        reply_to: str | None = None,
        at_all: bool = False,
        via: list | None = None,
        **kwargs,
    ) -> Any:
        """
        通用回复方法

        基于适配器的Text方法，但可以通过method参数指定其他发送方法

        :param content: 发送内容（文本、URL等，取决于method参数）
        :param method: str - 适配器发送方法（默认: "Text"）
                       可选值: "Text", "Image", "Voice", "Video", "File" 等；
                       使用 via 时必须显式指定
        :param at_sender: 是否@发送者（自动从事件中提取 user_id）
        :param quote: 是否引用回复当前消息（自动从事件中提取 message_id）
        :param at_users: @用户列表（可选），如 ["user1", "user2"]
        :param reply_to: 回复消息ID（可选，手动指定）
        :param at_all: 是否@全体成员（可选），默认为 False
        :param via: list - 经由的平台修饰方法链（可选，默认: None），按顺序在发送方法前应用。
                    每个元素可为：
                    - ``"Name"``（无参）
                    - ``("Name", arg1, arg2, ...)``（位置参数）
                    - ``("Name", (arg1, ...), {kw: val})``（位置+关键字参数）
                    例如 ``[("Expire", 3600), ("ForMember", "uid")]`` 等价于
                    ``.Expire(3600).ForMember("uid")``。
                    当需要连续多个修饰方法、或 method 强依赖修饰方法时使用；
                    更复杂的场景建议用 :meth:`send_chain`
        :param kwargs: 额外参数，例如Mention方法的user_id
        :return: Any - 适配器发送方法的返回值

        :raises ValueError: 当适配器不支持指定的发送方法/修饰方法时

        :example:
        >>> # 简单回复
        >>> await event.reply("你好")
        >>>
        >>> # 回复并@发送者
        >>> await event.reply("你好", at_sender=True)
        >>>
        >>> # 回复并引用当前消息
        >>> await event.reply("收到", quote=True)
        >>>
        >>> # 发送图片
        >>> await event.reply("http://example.com/image.jpg", method="Image")
        >>>
        >>> # @指定用户
        >>> await event.reply("你好", at_users=["user123"])
        >>>
        >>> # @全体成员
        >>> await event.reply("公告", at_all=True)
        >>>
        >>> # 平台专有修饰方法链 + 看板发送
        >>> await event.reply("看板内容", method="Board",
        ...                   via=[("Expire", 3600), ("ForMember", "uid")])
        """
        if via and method is None:
            logger.warning(
                i18n.t(
                    "core.event.reply_via_without_method",
                    default_method=DEFAULT_SEND_METHOD,
                )
            )
        if method is None:
            method = DEFAULT_SEND_METHOD

        adapter_instance, detail_type, target_id, bot_id = (
            self._get_adapter_and_target()
        )

        # 构建发送链
        send_chain = adapter_instance.Send.To(detail_type, target_id)

        # 多Bot: 使用接收事件的Bot发送
        if bot_id:
            send_chain = send_chain.Using(bot_id)

        # 处理@发送者
        if at_sender:
            sender_id = self.get_user_id()
            if sender_id and hasattr(send_chain, "At"):
                send_chain = send_chain.At(sender_id)

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
        # quote=True 时自动获取当前消息ID
        if quote and not reply_to:
            reply_to = self.get("message_id", "")
        if reply_to:
            if hasattr(send_chain, "Reply"):
                send_chain = send_chain.Reply(reply_to)

        # 处理特殊方法（向后兼容）
        if method == "Mention" or method == "At":
            user_id = kwargs.get("user_id")
            if user_id is None:
                user_id = self.get_user_id()
            send_chain = send_chain.At(user_id)
            method = DEFAULT_SEND_METHOD

        # 应用用户自定义修饰方法（平台专有，如 Expire / ForMember）
        if via:
            for mod in via:
                name, m_args, m_kwargs = _normalize_modifier(mod)
                mod_attr = getattr(send_chain, name, None)
                if not mod_attr or not callable(mod_attr):
                    raise ValueError(
                        i18n.t("core.event.modifier_not_supported", name=name)
                    )
                send_chain = mod_attr(*m_args, **m_kwargs)
                if send_chain is None:
                    raise ValueError(
                        i18n.t("core.event.modifier_must_return_chain", name=name)
                    )

        # 调用指定方法
        send_method = getattr(send_chain, method, None)
        if not send_method or not callable(send_method):
            raise ValueError(
                i18n.t("core.event.method_not_supported", method=method)
            )

        result = send_method(content)
        return await result if inspect.isawaitable(result) else result

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
        adapter_instance, detail_type, target_id, bot_id = (
            self._get_adapter_and_target()
        )
        send_chain = adapter_instance.Send.To(detail_type, target_id)
        if bot_id:
            send_chain = send_chain.Using(bot_id)
        return await send_chain.Raw_ob12(message)

    # ==================== 发送链获取 ====================

    def send_chain(self):
        """
        获取已配置好目标和发送账号的发送链

        返回已设置 ``To``（目标）和 ``Using``（发送账号）的 SendDSL 实例，
        可自由追加修饰方法（At/Reply/平台专有修饰）和发送方法。

        适用于 :meth:`reply` 无法覆盖的场景：
        - 平台专有修饰方法（如云虎的 Expire/ExpireAt/ForMember）
        - 需要连续多个修饰方法
        - 无内容参数的动作型发送方法（如 DismissBoard）

        :return: SendDSL - 已设置目标和发送账号的发送链实例

        :raises ValueError: 当事件缺少 platform 字段或找不到对应适配器时

        :example:
        >>> # 平台专有修饰方法 + 看板发送
        >>> await event.send_chain().Expire(3600).Board("一小时后过期")
        >>>
        >>> # 连续多个修饰方法
        >>> await (event.send_chain()
        ...        .Expire(3600)
        ...        .ForMember("114514")
        ...        .Board("看板内容", content_type="markdown"))
        >>>
        >>> # 内置修饰方法同样可用
        >>> await event.send_chain().At("123").Reply("msg_id").Text("hi")
        >>>
        >>> # 无内容参数的动作型方法
        >>> await event.send_chain().DismissBoard()
        """
        adapter_instance, detail_type, target_id, bot_id = (
            self._get_adapter_and_target()
        )
        send_chain = adapter_instance.Send.To(detail_type, target_id)
        if bot_id:
            send_chain = send_chain.Using(bot_id)
        return send_chain

    # ==================== 平台能力查询 ====================

    def supports(self, method: str) -> bool:
        """
        检查当前事件所在平台是否支持某发送方法

        :param method: 发送方法名，如 "Image"、"Voice"、"Video"
        :return: 是否支持

        :example:
        >>> if event.supports("Image"):
        ...     await event.reply(url, method="Image")
        """
        platform = self.get_platform()
        try:
            return method in adapter.list_sends(platform)
        except (ValueError, AttributeError):
            return False

    def available_methods(self) -> list[str]:
        """
        列出当前平台所有可用发送方法

        :return: 发送方法名列表

        :example:
        >>> methods = event.available_methods()
        >>> # ["Text", "Image", "Voice", ...]
        """
        platform = self.get_platform()
        try:
            return adapter.list_sends(platform)
        except (ValueError, AttributeError):
            return []

    # ==================== 等待回复功能 ====================

    async def wait_reply(
        self,
        prompt: str | None = None,
        timeout: float = DEFAULT_WAIT_TIMEOUT_SECS,
        callback: Callable[[dict[str, Any]], Awaitable[Any]] | None = None,
        validator: Callable[[dict[str, Any]], bool] | None = None,
        method: str = DEFAULT_SEND_METHOD,
        pattern: str | None = None,
        regex: str | None = None,
    ) -> Optional["Event"]:
        """
        等待用户回复

        :param prompt: 提示消息，如果提供会发送给用户
        :param timeout: 等待超时时间(秒)
        :param callback: 回调函数，当收到回复时执行
        :param validator: 验证函数，用于验证回复是否有效
        :param method: 发送方法，默认为 "Text"（可选: "Image", "Markdown", "Html" 等）
        :param pattern: glob 通配符（``*`` / ``?`` / ``[seq]``），回复文本不匹配时继续等待
        :param regex: 正则表达式，回复文本不匹配时继续等待（与 pattern 同时给定时须都匹配）
        :return: 用户回复的事件数据，如果超时则返回None

        :example:
        >>> reply = await event.wait_reply(prompt="请输入金额:", regex=r"\\d+\\s*元")
        """
        return await _builtin_wait_reply(
            self, prompt, timeout, callback, validator, method, pattern, regex
        )

    # ==================== 交互式对话方法 ====================

    async def confirm(
        self,
        prompt: str | None = None,
        timeout: float = DEFAULT_WAIT_TIMEOUT_SECS,
        yes_words: set[str] | frozenset[str] | None = None,
        no_words: set[str] | frozenset[str] | None = None,
        method: str = DEFAULT_SEND_METHOD,
        hint: bool = False,
    ) -> bool | None:
        """
        等待用户确认 (是/否)

        自动发送提示消息并等待用户回复，识别内置中英文确认词。
        内置确认词: 是/yes/y/确认/确定/好/ok/true/对/嗯/行/同意/没问题... (否/no/n/取消/不/不要/cancel/false/错/拒绝...)

        :param prompt: str - 提示消息（可选，发送后等待回复）
        :param timeout: float - 超时时间(秒)（默认: 60.0）
        :param yes_words: set[str] - 自定义确认词集合（默认: 内置 CONFIRM_YES_WORDS）
        :param no_words: set[str] - 自定义否定词集合（默认: 内置 CONFIRM_NO_WORDS）
        :param method: str - 发送方法（默认: "Text"，可选: "Image", "Markdown" 等）
        :param hint: bool - 是否在提示消息末尾自动追加确认词提示，如 "（是/否）"（默认: False）
        :return: bool|None - True=确认, False=否定, None=超时

        :example:
        >>> if await event.confirm("确定要执行此操作吗？", hint=True):
        ...     await event.reply("已执行")
        >>> # 发送图片作为确认提示
        >>> if await event.confirm("https://example.com/image.jpg", method="Image"):
        ...     await event.reply("已确认")
        """
        return await _builtin_confirm(
            self, prompt, timeout, yes_words, no_words, method, hint
        )

    async def choose(
        self,
        prompt: str,
        options: list[str],
        timeout: float = DEFAULT_WAIT_TIMEOUT_SECS,
        method: str = DEFAULT_SEND_METHOD,
        options_format: str | Callable[[list[str]], str] = "auto",
        merge_prompt: bool = False,
        placeholder: str = "{options}",
    ) -> int | None:
        """
        等待用户从选项中选择

        自动发送编号选项列表，用户可回复编号或选项文本。

        发送行为取决于 method 和 merge_prompt：
        - 文本类方法 (Text/Markdown/md/Html/h5 等): 选项默认拼接到 prompt 末尾，一条消息发送
        - 非文本方法 (Image/Voice 等) + merge_prompt=False (默认): 先发富媒体 prompt，再发 Text 选项
        - 任意方法 + merge_prompt=True: 强制合并为一条消息发送（用用户指定的 method）
        - prompt 含占位符（默认 ``{options}``，可通过 placeholder 自定义）时，替换该位置；否则追加到末尾

        :param prompt: str - 提示消息（必须）。可含占位符指定选项插入位置
        :param options: list[str] - 选项列表（不能为空）
        :param timeout: float - 超时时间(秒)（默认: 60.0）
        :param method: str - 发送方法（默认: "Text"）
        :param options_format: str|callable - 选项格式（默认: "auto"，根据 method 自动选择内置样式）
            - "auto": 根据 method 自动选择（Markdown→无序列表，Html→有序列表，其他→纯文本列表）
            - "list": 每行一个，如 ``1. 选项A\n2. 选项B``
            - "inline": 单行展示，如 ``1.选项A | 2.选项B``
            - "md": Markdown 无序列表，如 ``- 1. 选项A\n- 2. 选项B``
            - "html": Html 有序列表，如 ``<ol><li>1. 选项A</li>...</ol>``
            - callable: 自定义函数，接收 ``list[str]`` 返回 ``str``
        :param merge_prompt: bool - 是否合并为一条消息（默认: False）
            合并时使用用户指定的 method（如 Markdown/Html/Image 等），尊重用户选择
        :param placeholder: str - 选项插入占位符（默认: ``{options}``），
            prompt 中出现该标记的位置将被替换为选项文本；设为空字符串则始终追加到末尾
        :return: int|None - 选中选项的索引(0-based), 超时返回 None

        :raises ValueError: 当 options 为空时

        :example:
        >>> # 基本用法（prompt 和选项分两条消息）
        >>> choice = await event.choose("请选择颜色:", ["红", "绿", "蓝"])
        >>> # 合并模式：用 Markdown 一条消息发送
        >>> choice = await event.choose("请选择:", ["A", "B"],
        ...     method="Markdown", merge_prompt=True)
        >>> # 占位符：控制选项插入位置
        >>> choice = await event.choose(
        ...     "## 任务选择\n{options}\n请回复编号",
        ...     ["下载", "上传"], method="Markdown", merge_prompt=True)
        >>> # 自定义占位符
        >>> choice = await event.choose(
        ...     "请选择: [choices]",
        ...     ["A", "B"], placeholder="[choices]")
        """
        return await _builtin_choose(
            self, prompt, options, timeout, method, options_format, merge_prompt, placeholder
        )

    async def collect(
        self,
        fields: list[dict[str, Any]],
        timeout_per_field: float = 60.0,
    ) -> dict[str, str] | None:
        """
        多步骤收集信息 (表单式)

        依次向用户发送提示消息并收集回复，每个字段可配置验证器和重试逻辑

        :param fields: list[dict] - 字段列表，每个字段为字典:
            - key: str - 字段键名（必须）
            - prompt: str - 提示消息（默认: "请输入 {key}"）
            - validator: callable - 验证函数，接收 Event 对象，返回 bool（可选）
            - retry_prompt: str - 验证失败时的重试提示（默认: "输入无效，请重新输入"）
            - max_retries: int - 最大重试次数（默认: 3）
            - method: str - 发送方法（默认: "Text"，可选: "Image", "Markdown" 等）
            - options: list[str] - 可选值列表，提供时该字段变为选择题（可选）
            - options_format: str|callable - 选项格式（默认: "auto"，详见 choose()）
            - merge_prompt: bool - 是否合并为一条消息（默认: False）
            - placeholder: str - 选项插入占位符（默认: "{options}"，详见 choose()）
        :param timeout_per_field: float - 每个字段的超时时间(秒)（默认: 60.0）
        :return: dict|None - 收集到的数据字典, 任何步骤超时或重试耗尽返回 None

        :example:
        >>> data = await event.collect([
        ...     {"key": "name", "prompt": "请输入姓名"},
        ...     {"key": "age", "prompt": "请输入年龄",
        ...      "validator": lambda e: e.get("alt_message", "").strip().isdigit()},
        ...     {"key": "avatar", "prompt": "请发送头像图片", "method": "Image"},
        ... ])
        >>> if data:
        ...     await event.reply(f"姓名: {data['name']}, 年龄: {data['age']}")
        """
        return await _builtin_collect(self, fields, timeout_per_field)

    async def wait_for(
        self,
        event_type: str = "message",
        condition: Callable[["Event"], bool] | None = None,
        timeout: float = DEFAULT_WAIT_TIMEOUT_SECS,
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
                    raw = (
                        event_data if isinstance(event_data, dict) else dict(event_data)
                    )
                    try:
                        future.set_result(raw)
                    except asyncio.InvalidStateError:
                        pass
            except Exception as _e:
                logger.trace(i18n.t("core.event.wait_handler_error", error=_e))

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

    def conversation(
        self, timeout: float = DEFAULT_WAIT_TIMEOUT_SECS
    ) -> "Conversation":
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

    def remind(self, delay: float, text: str | None = None, *, callback: Any = None) -> Any:
        """
        会话定时提醒：delay 秒后无回复则提醒 / 执行回调

        挂在当前会话上的定时器——用户**在该会话回复后自动取消**
        （"如果没在时限内回复就提醒"）；也可 ``reminder.cancel()`` 手动取消；
        归属模块卸载 / 适配器关闭时随归属清理自动取消。

        :param delay: 延迟秒数
        :param text: 到期发送到当前会话的提醒文本（与 callback 二选一，同时给定时文本优先）
        :param callback: 到期执行的回调（同步或异步，接收当前 Event 为参数）
        :return: :class:`~ErisPulse.Core.Event.interaction.Reminder` 句柄；超过单会话上限时返回 None
        :raises RuntimeError: text 与 callback 均未提供时

        :example:
        >>> reminder = event.remind(300, "还在吗？不想聊就回复「退出」哦")
        >>> # 用户 5 分钟内回复 → 提醒自动取消；未回复 → 到期发送

        {!--< tips >!--}
        单会话同时最多挂 5 个活跃提醒（超出返回 None）。
        {!--< /tips >!--}
        """
        if text is None and callback is None:
            raise ValueError(i18n.t("core.interaction.remind_requires_action"))

        from .interaction import interaction

        event_ref = self

        async def _fire():
            if text is not None:
                await event_ref.reply(text)
            elif callback is not None:
                result = callback(event_ref)
                if asyncio.iscoroutine(result):
                    await result

        return interaction.add_reminder(self, delay, _fire, cancellable_by_reply=True)

    def escalate(self, delay: float, callback: Any) -> Any:
        """
        超时升级：delay 秒后执行升级回调（**不被用户回复取消**）

        与 :meth:`remind` 的差异：remind 是"没回复就提醒、回复即取消"，
        escalate 是"到点必达"的升级动作（如长时间无处理通知主人、转人工），
        仅手动 ``cancel()`` / 模块卸载 / 适配器关闭才取消。

        :param delay: 延迟秒数
        :param callback: 到期执行的回调（同步或异步，接收当前 Event 为参数）
        :return: :class:`~ErisPulse.Core.Event.interaction.Reminder` 句柄

        :example:
        >>> event.escalate(1800, lambda e: notify_master("工单 30 分钟未处理"))
        """
        from .interaction import interaction

        event_ref = self

        async def _fire():
            result = callback(event_ref)
            if asyncio.iscoroutine(result):
                await result

        return interaction.add_reminder(self, delay, _fire, cancellable_by_reply=False)

    async def history(self, n: int = 20) -> list[dict[str, Any]]:
        """
        查询当前会话的近期消息（会话收件箱）

        返回当前会话（platform:detail_type:target_id）最近的消息流，
        含用户与机器人双方，按时间升序。收件箱未启用或无记录时返回空列表。

        :param n: 返回的最大条数（默认 20）
        :return: 消息列表，每条含 role / text / ts / event_id

        :example:
        >>> messages = await event.history(10)
        >>> for m in messages:
        ...     print(m["role"], ":", m["text"])
        """
        from ..transcript import transcript

        return transcript.get(self, n)

    @staticmethod
    def expect(
        pattern: str | None = None,
        regex: str | None = None,
        validator: Any = None,
        user: str | None = None,
        session: bool = False,
    ) -> Expectation:
        """
        构造一条等待期望（不注册，传给 :meth:`select` 做多路等待）

        :param pattern: glob 文本过滤（``*`` / ``?`` / ``[seq]``）
        :param regex: 正则文本过滤（与 pattern 同时给定时须都匹配）
        :param validator: 回复校验函数（接收 Event，返回 bool）
        :param user: 限定回复者 user_id（None 不限定）
        :param session: 会话级等待——同会话任何人可命中（忽略 user）
        :return: 期望描述对象

        :example:
        >>> which, reply = await event.select(
        ...     event.expect(pattern="同意*", user="10001"),
        ...     event.expect(pattern="拒绝*", user="10002"),
        ...     timeout=60,
        ... )
        """
        return Expectation(
            pattern=pattern,
            regex=regex,
            validator=validator,
            user=user,
            session=session,
        )

    async def select(
        self, *expectations: Expectation, timeout: float | None = None
    ) -> "tuple[int | None, Event | None]":
        """
        多路等待：同时挂起多条期望，任一命中即返回该路结果（先到先得）

        典型场景：同时等待"管理员同意"与"用户回复"、多人协作投票等。
        未命中的等待在返回前自动取消；全部超时返回 ``(None, None)``。
        命中的事件已被框架认领（mark_processed），不会被低优先级处理器重复消费。

        :param expectations: :meth:`expect` 构造的期望描述（至少一条）
        :param timeout: 统一超时秒数（None 表示不限时）
        :return: ``(命中的期望下标, 回复事件)``；超时返回 ``(None, None)``
        :raises ValueError: 未提供任何期望时

        :example:
        >>> which, reply = await event.select(
        ...     event.expect(pattern="同意*", user="10001"),
        ...     event.expect(pattern="拒绝*", user="10002"),
        ...     timeout=60,
        ... )
        >>> if which is None:
        ...     await event.reply("超时未收到审批")
        >>> elif which == 0:
        ...     await event.reply("已同意")
        """
        if not expectations:
            raise ValueError(i18n.t("core.interaction.select_requires_expectations"))

        from .interaction import interaction

        loop = asyncio.get_running_loop()
        entries = []
        futures = []
        for exp in expectations:
            evt = self
            # 不同 user 的期望构造键区分的变体事件（同 user 多路也因事件副本独立而互不冲突）
            if exp.user is not None:
                evt = Event(dict(self))
                evt["user_id"] = exp.user
            future = loop.create_future()
            entry = interaction.register(
                evt,
                future,
                pattern=exp.pattern,
                regex=exp.regex,
                validator=exp.validator,
                session_scope=exp.session,
            )
            entries.append(entry)
            futures.append(future)

        try:
            done, _pending = await asyncio.wait(
                futures, timeout=timeout, return_when=asyncio.FIRST_COMPLETED
            )
        finally:
            # 无论命中 / 超时 / 被取消，未消费的等待全部清理（已命中的条目已被移除，取消为幂等空操作）
            for entry in entries:
                interaction.cancel(entry.key)

        if not done:
            return None, None

        done_future = next(iter(done))
        return futures.index(done_future), done_future.result()

    def message_tx(self) -> "_MessageTx":
        """
        开启消息事务

        事务内的所有出站发送（reply / Send DSL）自动记入回执账本；
        以异常退出事务时，已发送的消息按逆序自动撤回。

        撤回是**能力感知**的：适配器未实现 ``delete_message`` 时跳过撤回
        （账本仍正常记录），平台不支持撤回的消息不报错。

        :return: 异步上下文管理器

        :example:
        >>> async with event.message_tx():
        ...     await event.reply("正在处理，请稍候")
        ...     result = await do_something()
        ...     await event.reply(f"完成: {result}")
        >>> # do_something() 抛出异常时，前面两条消息自动撤回

        {!--< tips >!--}
        嵌套事务各自独立记账；事务外发送不记账（零开销）。
        {!--< /tips >!--}
        """
        return _MessageTx()

    def to_dict(self) -> dict[str, Any]:
        """
        转换为字典（过滤内部键）

        过滤以 ``_`` 开头的内部键（如 ``_processed``/``_propagation_stopped``），
        只返回事件数据。

        :return: 事件数据字典
        """
        return {k: v for k, v in self.items() if not k.startswith("_")}

    def is_processed(self) -> bool:
        """
        是否已被处理

        :return: 是否已被处理
        """
        return self.get("_processed", False)

    def mark_processed(self, claim: bool = True, stop: bool = True):
        """
        标记事件为已处理

        认领与阻断是两个**正交**的语义，可独立控制：

        - **认领（claim）**：标记事件已被本处理器处理（写入 ``_processed``）。
          命令分发器看到已认领的事件会跳过去重，避免同一消息被多个命令处理器
          重复处理。典型场景：命令匹配成功后认领，阻止命令分发器再介入。
        - **阻断（stop）**：阻止事件向更低优先级处理器传播（写入
          ``_propagation_stopped``）。低优先级处理器（如 ``on_message``）将不再
          看到该事件。典型场景：高优先级处理器已完整处理事件，不希望低优先级再执行。

        参数组合：
        - ``mark_processed()``：认领 + 阻断（默认）
        - ``mark_processed(stop=False)``：仅认领，不阻断 —— 事件继续流向低优先级观察者
        - ``mark_processed(claim=False)``：仅阻断，不认领 —— 低优先级不执行，但不做去重

        :param claim: 是否认领事件（标记已处理，命令分发去重）（默认 True）
        :param stop: 是否阻断向低优先级处理器传播（默认 True）

        :example:
        >>> event.mark_processed()            # 认领 + 阻断（默认）
        >>> event.mark_processed(stop=False)  # 仅认领，低优先级仍能看到
        >>> event.mark_processed(claim=False) # 仅阻断，不标记已处理
        """
        if claim:
            self["_processed"] = True
        if stop:
            self["_propagation_stopped"] = True

    def done(self, claim: bool = True, stop: bool = True):
        """
        标记事件完成（:meth:`mark_processed` 的别名）

        与 :meth:`mark_processed` 完全等价，提供更简洁的写法。

        :param claim: 是否认领事件（标记已处理，命令分发去重）（默认 True）
        :param stop: 是否阻断向低优先级处理器传播（默认 True）

        :example:
        >>> @command("help")
        ... async def help_cmd(event):
        ...     event.done()            # 认领 + 阻断（命令处理完的标准做法）
        >>>
        >>> @message.on_message(priority=50)
        ... async def observer(event):
        ...     event.done(stop=False)  # 仅认领，低优先级仍能看到（日志/统计）
        >>>
        >>> @message.on_message(priority=100)
        ... async def firewall(event):
        ...     if denied(event):
        ...         event.done(claim=False)  # 仅阻断，不标记已处理
        """
        self.mark_processed(claim=claim, stop=stop)

    def is_stopped(self) -> bool:
        """
        事件传播是否已被阻断（是否已停止向低优先级处理器传播）

        对应 ``done(stop=True)`` / ``mark_processed(stop=True)`` 的阻断效果。

        :return: 是否已阻断传播
        """
        return self.get("_propagation_stopped", False)

    # ==================== 魔术方法 ====================

    def __getattribute__(self, name: str) -> Any:
        """
        属性查找优先级:
        1. 当前平台的注册方法覆写（优先于内置方法）
        2. 通配符 "*" 平台的注册方法
        3. 内置方法/属性（正常解析）

        :param name: str - 属性名
        :return: Any - 属性值
        """
        platform = dict.get(self, "platform", "")
        # 1. 当前平台特定方法
        platform_methods = _platform_event_methods.get(platform)
        if platform_methods and name in platform_methods:
            func = platform_methods[name]
            return func.__get__(self, type(self))
        # 2. 通配符方法
        wildcard_methods = _platform_event_methods.get("*")
        if wildcard_methods and name in wildcard_methods:
            func = wildcard_methods[name]
            return func.__get__(self, type(self))

        return object.__getattribute__(self, name)

    def __getattr__(self, name: str) -> Any:
        """
        属性查找优先级:
        1. 当前平台的扩展方法
        2. 通配符 "*" 平台的扩展方法
        3. 字典键访问（点式访问 event.platform 等）

        :param name: str - 属性名
        :return: Any - 属性值
        :raises AttributeError: 属性不存在
        """
        platform = dict.get(self, "platform", "")
        # 1. 当前平台特定方法
        if (
            platform_methods := _platform_event_methods.get(platform)
        ) and name in platform_methods:
            func = platform_methods[name]
            return func.__get__(self, type(self))

        # 2. 通配符方法
        if (
            wildcard_methods := _platform_event_methods.get("*")
        ) and name in wildcard_methods:
            func = wildcard_methods[name]
            return func.__get__(self, type(self))

        # 3. 兜底：字典键访问
        try:
            return self[name]
        except KeyError as _err:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{name}'"
            ) from _err

    def __dir__(self) -> list[str]:
        """
        让 dir(event) 包含当前平台和通配符注册的扩展方法名
        """
        names = super().__dir__()
        # 添加当前平台的扩展方法名
        platform = dict.get(self, "platform", "")
        platform_methods = _platform_event_methods.get(platform)
        if platform_methods:
            names = list(names) + list(platform_methods.keys())
        # 添加通配符平台的扩展方法名
        wildcard_methods = _platform_event_methods.get("*")
        if wildcard_methods:
            names = list(names) + list(wildcard_methods.keys())
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



# 对话恢复工厂注册表：[(factory, platform | None)]
# 由 Conversation.register_resume_handler 装饰器写入，
# 框架在消息事件入口通过 Conversation.try_auto_resume 消费。
_conversation_resume_handlers: list[tuple[Callable, str | None]] = []


def _consume_task_exception(task: "asyncio.Task") -> None:
    """{!--< internal-use >!--} 消费后台检查点任务的异常（防未检索告警）"""
    if task.done() and not task.cancelled():
        exc = task.exception()
        if exc is not None:
            del exc


async def _rollback_receipts(receipts: list[dict[str, str]]) -> None:
    """
    {!--< internal-use >!--}
    逆序撤回消息事务账本中的消息（能力感知）

    适配器未实现 ``delete_message``（Api 能力缺失）时跳过该条并记录 TRACE 日志；
    单条撤回失败不中断后续撤回。

    :param receipts: 消息回执账本
    """
    for receipt in reversed(receipts):
        platform = receipt.get("platform")
        message_id = receipt.get("message_id")
        if not platform or not message_id:
            continue
        try:
            adapter_instance = getattr(adapter, platform, None)
            if adapter_instance is None:
                continue
            api = getattr(adapter_instance, "Api", None)
            if api is None or not hasattr(api, "delete_message"):
                logger.trace(
                    i18n.t(
                        "core.interaction.message_tx_no_capability",
                        platform=platform,
                        message_id=message_id,
                    )
                )
                continue
            await api.delete_message(message_id=message_id)
        except Exception as _e:
            logger.trace(
                i18n.t(
                    "core.interaction.message_tx_rollback_failed",
                    message_id=message_id,
                    error=_e,
                )
            )


class _MessageTx:
    """
    {!--< internal-use >!--}
    消息事务上下文管理器（由 :meth:`Event.message_tx` 创建）

    事务内所有出站发送自动记入回执账本；异常退出时逆序撤回已发送的消息
    （适配器需实现 ``delete_message``，未实现时跳过）。正常退出不撤回。
    """

    async def __aenter__(self) -> "_MessageTx":
        from ...runtime.context import send_receipts

        self._token = send_receipts.set([])
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        from ...runtime.context import send_receipts

        receipts = send_receipts.get() or []
        send_receipts.reset(self._token)
        if exc_type is not None and receipts:
            await _rollback_receipts(receipts)
        return False



class Conversation:
    """
    多轮对话上下文

    提供在同一会话中进行多轮交互的便捷方法，支持分支跳转、上下文持久化

    {!--< tips >!--}
    1. 通过 event.conversation() 方法创建
    2. 超时后自动标记为非活跃状态
    3. 支持链式调用 say() 方法
    4. 支持 branch() 定义分支和 goto() 跳转
    5. 支持 context 字典存储对话状态
    6. 支持 save()/resume() 持久化到 storage
    {!--< /tips >!--}
    """

    def __init__(self, event: "Event", timeout: float = DEFAULT_WAIT_TIMEOUT_SECS):
        """
        初始化对话上下文

        :param event: Event - 事件对象
        :param timeout: float - 默认超时时间(秒)（默认: 60.0）
        """
        self._event = event
        self._timeout = timeout
        self._alive = True
        self._branches: dict[str, Callable] = {}
        self._current_branch: str | None = None
        self._branch_task: asyncio.Task | None = None
        self.context: dict[str, Any] = {}
        # 恢复时由 resume(with_history=N) 从会话收件箱带回的最近消息
        self.recent_history: list[dict[str, Any]] = []

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

    async def wait(
        self,
        prompt: str | None = None,
        timeout: float | None = None,
        method: str = DEFAULT_SEND_METHOD,
    ) -> Optional["Event"]:
        """
        等待用户回复

        :param prompt: str - 提示消息（可选）
        :param timeout: float - 超时时间(秒)，默认使用对话的超时设置
        :param method: str - 发送方法（默认: "Text"）
        :return: Event|None - 用户回复的事件, 超时返回 None
        """
        if not self._alive:
            return None
        result = await self._event.wait_reply(
            prompt=prompt,
            timeout=timeout if timeout is not None else self._timeout,
            method=method,
        )
        if result is None:
            self._alive = False
            self._schedule_checkpoint_clear()
        return result

    async def confirm(self, prompt: str | None = None, **kwargs) -> bool | None:
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

    async def choose(self, prompt: str, options: list[str], **kwargs) -> int | None:
        """
        等待用户选择

        :param prompt: str - 提示消息
        :param options: list[str] - 选项列表
        :return: int|None - 选中索引或 None
        """
        if not self._alive:
            return None
        return await self._event.choose(
            prompt,
            options,
            timeout=kwargs.pop("timeout", self._timeout),
            **kwargs,
        )

    async def collect(self, fields: list[dict], **kwargs) -> dict | None:
        """
        多步骤收集信息

        :param fields: list[dict] - 字段列表，支持 condition 字段:
            - condition: callable - 接收已收集数据 dict, 返回 bool 决定是否收集此字段
        :return: dict|None - 收集到的数据字典或 None
        """
        if not self._alive:
            return None

        filtered_fields = []
        for f in fields:
            cond = f.get("condition")
            if cond is not None:
                try:
                    if not cond(self.context):
                        continue
                except Exception as _e:
                    logger.trace(i18n.t("core.event.conversation_condition_error", error=_e))
                    continue
            filtered_fields.append(f)

        result = await self._event.collect(
            filtered_fields,
            timeout_per_field=kwargs.pop("timeout_per_field", self._timeout),
            **kwargs,
        )
        if result is None:
            self._alive = False
            self._schedule_checkpoint_clear()
        else:
            self.context.update(result)
        return result

    def stop(self):
        """
        结束对话

        终态自动清除已保存的对话检查点。
        """
        self._alive = False
        if self._branch_task and not self._branch_task.done():
            self._branch_task.cancel()
        self._schedule_checkpoint_clear()

    def remind(self, delay: float, text: str | None = None, *, callback: Any = None) -> Any:
        """
        会话定时提醒（转发到当前对话事件的 ``Event.remind``）

        delay 秒后无回复则发送提醒文本 / 执行回调；用户在会话回复后自动取消。

        :param delay: 延迟秒数
        :param text: 到期发送的提醒文本（与 callback 二选一）
        :param callback: 到期执行的回调（接收当前 Event 为参数）
        :return: Reminder 句柄；超过单会话上限时返回 None

        :example:
        >>> conv.remind(120, "还在考虑吗？需要帮助请输入「帮助」")
        """
        return self._event.remind(delay, text, callback=callback)

    def escalate(self, delay: float, callback: Any) -> Any:
        """
        超时升级（转发到当前对话事件的 ``Event.escalate``，不被回复取消）

        :param delay: 延迟秒数
        :param callback: 到期执行的回调（接收当前 Event 为参数）
        :return: Reminder 句柄
        """
        return self._event.escalate(delay, callback)

    # 分支系统

    def branch(self, name: str):
        """
        注册分支处理器

        :param name: str 分支名称
        :return: Callable 装饰器

        :example:
        >>> conv = event.conversation()
        >>>
        >>> @conv.branch("menu")
        ... async def menu_branch(conv, event):
        ...     await conv.say("1.饮品 2.主食")
        ...     resp = await conv.wait()
        ...     if resp and resp.get_text() == "1":
        ...         conv.goto("drink")
        ...
        >>> @conv.branch("drink")
        ... async def drink_branch(conv, event):
        ...     await conv.say("请选择饮品")
        ...     resp = await conv.wait()
        ...     conv.context["drink"] = resp.get_text()
        ...     conv.goto("confirm")
        ...
        >>> conv.start("menu")
        """

        def decorator(func: Callable):
            self._branches[name] = func
            return func

        return decorator

    def goto(self, branch_name: str, event: "Event | None" = None):
        """
        跳转到指定分支

        :param branch_name: str 目标分支名称
        :param event: Event 传递给分支的事件对象 (可选)

        :raises ValueError: 当目标分支不存在时

        :example:
        >>> conv.goto("drink")
        """
        if branch_name not in self._branches:
            raise ValueError(
                i18n.t("core.event.branch_not_defined", name=branch_name)
            )
        self._current_branch = branch_name
        # 分支跳转自动保存检查点（重启后可从当前分支恢复）
        self._schedule_checkpoint()

        evt = event or self._event

        if self._branch_task and not self._branch_task.done():
            self._branch_task.cancel()

        async def _run_branch():
            handler = self._branches[branch_name]
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(self, evt)
                else:
                    handler(self, evt)
            except asyncio.CancelledError:
                pass
            except Exception as e:
                from ..logger import logger as _logger

                _logger.warning(i18n.t("core.event.branch_exec_error", name=branch_name, error=e))
                self._alive = False

        try:
            loop = asyncio.get_running_loop()
            self._branch_task = loop.create_task(_run_branch())
        except RuntimeError:
            pass

    def start(self, branch_name: str, event: "Event | None" = None):
        """
        启动对话，从指定分支开始

        :param branch_name: str 起始分支名称
        :param event: Event 初始事件对象 (可选)

        :raises ValueError: 当起始分支不存在时

        :example:
        >>> conv.start("menu")
        """
        self._alive = True
        self.goto(branch_name, event)

    def get_current_branch(self) -> str | None:
        """
        获取当前分支名称

        :return: str|None 当前分支名, 未在分支中时返回 None
        """
        return self._current_branch

    def has_branch(self, name: str) -> bool:
        """
        检查分支是否存在

        :param name: str 分支名称
        :return: bool 是否存在
        """
        return name in self._branches

    # ==================== 持久化（自动检查点） ====================

    @staticmethod
    def _checkpoint_key(event: "Event") -> str:
        """
        {!--< internal-use >!--}
        生成对话检查点存储键（含 target 维度，避免同一用户多会话互覆）

        :param event: 事件对象
        :return: 存储键（conversation:{platform}:{user_id}:{target_id}）
        """
        platform = event.get_platform() if hasattr(event, "get_platform") else event.get("platform", "")
        user_id = event.get_user_id() if hasattr(event, "get_user_id") else event.get("user_id", "")
        key = f"{CONVERSATION_KEY_PREFIX}:{platform}:{user_id}"
        target_id = event.get_target_id() if hasattr(event, "get_target_id") else event.get("target_id", "")
        if target_id:
            key = f"{key}:{target_id}"
        return key

    @staticmethod
    def _checkpoint_ttl() -> float:
        """
        {!--< internal-use >!--}
        读取检查点过期时长（ErisPulse.interaction.checkpoint_ttl，秒）

        :return: 过期秒数
        """
        try:
            from ...runtime.frame_config import get_erispulse_config

            return float(
                get_erispulse_config()
                .get("interaction", {})
                .get("checkpoint_ttl", DEFAULT_INTERACTION_CHECKPOINT_TTL_SECS)
            )
        except Exception:
            return DEFAULT_INTERACTION_CHECKPOINT_TTL_SECS

    def _schedule_checkpoint(self):
        """{!--< internal-use >!--} 后台保存检查点（分支跳转自动触发，失败静默）"""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        task = loop.create_task(self._checkpoint(save=True))
        task.add_done_callback(_consume_task_exception)

    def _schedule_checkpoint_clear(self):
        """{!--< internal-use >!--} 后台清除检查点（对话终态自动触发，失败静默）"""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        task = loop.create_task(self._checkpoint(save=False))
        task.add_done_callback(_consume_task_exception)

    async def _checkpoint(self, save: bool):
        """{!--< internal-use >!--} 检查点写入/清除的统一异常兜底"""
        try:
            if save:
                await self.save()
            else:
                await self.clear_saved()
        except Exception as _e:
            logger.trace(i18n.t("core.event.conversation_checkpoint_failed", error=_e))

    async def save(self):
        """
        保存对话状态到 storage（自动检查点）

        分支跳转（goto/start）时框架自动调用；也可手动调用强制存档。
        存储键含 target 维度（conversation:{platform}:{user_id}:{target_id}），
        同一用户在不同会话中的对话互不覆盖。

        :example:
        >>> await conv.save()

        {!--< tips >!--}
        保存内容包括: 当前分支、上下文数据、活跃状态、存档时间。
        超过 ``ErisPulse.interaction.checkpoint_ttl``（默认 24h）的存档在恢复时被丢弃。
        {!--< /tips >!--}
        """
        try:
            from ..storage import storage

            key = self._checkpoint_key(self._event)
            storage.set(
                key,
                {
                    "version": 2,
                    "branch": self._current_branch,
                    "context": self.context,
                    "alive": self._alive,
                    "timeout": self._timeout,
                    "saved_at": time.time(),
                },
            )
        except Exception:
            logger.trace("[Conversation] save failed")

    async def resume(self, event: "Event | None" = None, with_history: int = 10) -> bool:
        """
        从 storage 恢复对话状态（含会话接管与历史带回）

        恢复流程：读取检查点（含 target 维度新键，旧格式自动迁移）→
        **会话接管**（自动 acquire 会话租约，被其他模块占用时放弃恢复）→
        落地上下文并从收件箱带回最近消息到 :attr:`recent_history`。

        超过 checkpoint_ttl 的存档视为过期，丢弃并返回 False。

        :param event: Event 新的事件对象 (可选, 不传则使用原事件)
        :param with_history: 恢复时从会话收件箱带回的最近消息条数（0 关闭）
        :return: bool 是否恢复成功

        :example:
        >>> conv = event.conversation()
        >>> # ... 注册分支 ...
        >>> if await conv.resume():
        ...     conv.goto(conv.get_current_branch())

        {!--< tips >!--}
        需要在 resume() 之前先注册好所有分支；注册分支后也可使用
        :meth:`register_resume_handler` 声明恢复工厂，由框架在重启后
        首条命中消息自动完成恢复。
        {!--< /tips >!--}
        """
        try:
            from ..storage import storage
            from .interaction import interaction

            evt = event or self._event
            key = self._checkpoint_key(evt)
            data = storage.get(key)
            if not isinstance(data, dict):
                # 旧格式兼容：尝试不含 target 的旧键，命中则迁移至新键
                platform = evt.get_platform() if hasattr(evt, "get_platform") else evt.get("platform", "")
                user_id = evt.get_user_id() if hasattr(evt, "get_user_id") else evt.get("user_id", "")
                old_key = f"{CONVERSATION_KEY_PREFIX}:{platform}:{user_id}"
                data = storage.get(old_key)
                if isinstance(data, dict):
                    storage.delete(old_key)
                    storage.set(key, data)
                else:
                    return False

            # 过期检查点丢弃
            saved_at = data.get("saved_at")
            if (
                isinstance(saved_at, (int, float))
                and (time.time() - saved_at) > self._checkpoint_ttl()
            ):
                storage.delete(key)
                logger.trace(i18n.t("core.event.conversation_checkpoint_expired"))
                return False

            # 会话接管：恢复的对话持有该会话租约（被其他模块占用时放弃恢复，避免对话打架）
            if interaction.acquire(evt) is None:
                logger.trace(i18n.t("core.event.conversation_session_occupied"))
                return False

            self.context = data.get("context", {})
            self._current_branch = data.get("branch")
            self._alive = data.get("alive", False)
            if event:
                self._event = event

            # 历史带回：从收件箱取最近消息（AI 模块恢复后 LLM 上下文不断档）
            if with_history:
                try:
                    from ..transcript import transcript as _transcript

                    self.recent_history = _transcript.get(evt, with_history)
                except Exception:
                    self.recent_history = []
            return True
        except Exception as _e:
            logger.trace(i18n.t("core.event.conversation_resume_failed", error=_e))
        return False

    async def clear_saved(self):
        """
        清除保存的对话状态

        同时清理含 target 的新键与旧格式键。

        :example:
        >>> await conv.clear_saved()
        """
        try:
            from ..storage import storage

            evt = self._event
            storage.delete(self._checkpoint_key(evt))
            platform = evt.get_platform() if hasattr(evt, "get_platform") else evt.get("platform", "")
            user_id = evt.get_user_id() if hasattr(evt, "get_user_id") else evt.get("user_id", "")
            storage.delete(f"{CONVERSATION_KEY_PREFIX}:{platform}:{user_id}")
        except Exception as _e:
            logger.trace(i18n.t("core.event.conversation_clear_failed", error=_e))

    # ==================== 重启自动恢复 ====================

    @classmethod
    def register_resume_handler(cls, platform: str | None = None) -> Callable:
        """
        注册对话恢复工厂（类装饰器方法，模块加载时调用）

        框架在重启后收到该会话的首条消息时，若存在有效检查点，
        会调用已注册的工厂重建 Conversation（模块需在工厂内重新注册所有分支），
        随后自动 ``goto`` 到存档分支继续对话。

        :param platform: 仅匹配指定平台的事件；None 表示匹配所有平台
        :return: 装饰器

        :example:
        >>> @Conversation.register_resume_handler()
        ... def make_conversation(event) -> Conversation:
        ...     conv = event.conversation()
        ...     @conv.branch("menu")
        ...     async def menu(conv, event): ...
        ...     return conv
        """
        def decorator(func: Callable):
            _conversation_resume_handlers.append((func, platform))
            return func

        return decorator

    @classmethod
    async def try_auto_resume(cls, event: "Event") -> bool:
        """
        {!--< internal-use >!--}
        尝试对当前消息事件自动恢复挂起的对话（框架在消息入口调用）

        无已注册恢复工厂时立即返回（零开销路径）；存在有效检查点且
        某工厂成功重建对话时，恢复上下文、认领事件并跳转到存档分支。

        :param event: 消息事件（Event 包装类）
        :return: 是否完成了自动恢复（事件已被消费）
        """
        if not _conversation_resume_handlers:
            return False

        try:
            from ..storage import storage

            data = storage.get(cls._checkpoint_key(event))
        except Exception:
            return False
        if not isinstance(data, dict) or not data.get("alive", False):
            return False

        branch = data.get("branch")
        if not branch:
            return False

        # 过期检查点直接丢弃
        saved_at = data.get("saved_at")
        if (
            isinstance(saved_at, (int, float))
            and (time.time() - saved_at) > cls._checkpoint_ttl()
        ):
            try:
                from ..storage import storage as _storage

                _storage.delete(cls._checkpoint_key(event))
            except Exception:
                pass
            return False

        event_platform = event.get("platform")
        for handler, platform_filter in _conversation_resume_handlers:
            if platform_filter and event_platform != platform_filter:
                continue
            try:
                if inspect.iscoroutinefunction(handler):
                    conv = await handler(event)
                else:
                    conv = handler(event)
            except Exception as _e:
                logger.trace(i18n.t("core.event.conversation_resume_failed", error=_e))
                continue
            if conv is None:
                continue
            # 恢复上下文并从存档分支继续
            conv.context = data.get("context", {}) or {}
            timeout = data.get("timeout")
            if isinstance(timeout, (int, float)):
                conv._timeout = timeout
            mark_processed = getattr(event, "mark_processed", None)
            if callable(mark_processed):
                mark_processed()
            conv.goto(branch, event)
            logger.trace(i18n.t("core.event.conversation_auto_resumed", branch=branch))
            return True
        return False


__all__ = [
    "CONFIRM_NO_WORDS",
    "CONFIRM_YES_WORDS",
    "Conversation",
    "Event",
    "_builtin_choose",
    "_builtin_collect",
    "_builtin_confirm",
    # 内置交互式方法实现（供平台 Mixin 覆写时调用）
    "_builtin_wait_reply",
    "get_platform_event_methods",
    "register_event_method",
    # 平台事件方法注册
    "register_event_mixin",
    "unregister_event_method",
    "unregister_platform_event_methods",
]
