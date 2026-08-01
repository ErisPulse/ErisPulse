"""
ErisPulse 适配器基础模块

提供适配器和消息发送DSL的基类实现

{!--< tips >!--}
1. 用于实现与不同平台的交互接口
2. 提供统一的消息发送DSL风格接口
{!--< /tips >!--}
"""

import asyncio
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    # Self 用于让链式方法返回子类类型，使 IDE 能补全平台特有方法
    # typing.Self 仅在 3.11+ 提供，3.10 需 typing_extensions 兜底
    from typing_extensions import Self

from ..constants import (
    DEFAULT_SEND_METHOD,
    DEFAULT_SEND_TARGET_TYPE,
    LOG_MESSAGE_TRUNCATE_CHARS,
    RETCODE_NOT_IMPLEMENTED,
    RETCODE_OK,
    STATUS_FAILED,
    STATUS_OK,
)

_CHAIN_MODIFIER_NAMES = frozenset({
    "At", "AtAll", "Reply", "To", "Using", "Account",
    # 发送规则装饰器（返回 self，不触发包装）
    "Hook", "Retry", "Timeout", "Defer", "Priority", "PriorityThreshold",
    "OnProgress", "OnError",
    # 批量构建模式入口（返回 SendBuilder，不触发包装）
    "Build",
})


# SendDSL._rules 中的键名集合，用于判断是否启用了发送规则
_RULE_KEYS = frozenset({
    "hooks", "retry", "timeout", "defer",
    "priority", "drop_if_busy", "priority_threshold",
    "on_progress", "on_error",
})


def _has_rules(send_dsl: "SendDSL") -> bool:
    """
    判断 SendDSL 实例是否附加了发送规则

    :param send_dsl: SendDSL 实例
    :return: 是否存在任意已设置的规则
    """
    rules = getattr(send_dsl, "_rules", None)
    if not rules:
        return False
    for key in _RULE_KEYS:
        val = rules.get(key)
        if key == "hooks":
            if val:
                return True
        elif val is not None and val is not False:
            return True
    return False


def _copy_rules(rules: dict) -> dict:
    """
    复制规则字典（深拷贝可变值，如 hooks 列表）

    用于 To/Using/Account 创建新实例时避免共享可变状态。
    标量值（retry/timeout/defer 等）浅拷贝即可，
    仅 hooks 列表需要创建新列表。

    :param rules: 原始规则字典
    :return: 独立的规则字典副本
    """
    copied = dict(rules)
    hooks = copied.get("hooks")
    if hooks:
        copied["hooks"] = list(hooks)
    return copied


def _wrap_to_task(result: Any):
    """
    将任意返回值包装为 Task（用于重试路径的兼容处理）

    :param result: 原始方法返回值
    :return: asyncio.Task
    """
    if asyncio.iscoroutine(result):
        return asyncio.ensure_future(result)
    async def _const():
        return result
    return asyncio.ensure_future(_const())


def _wrap_send_method(method_name: str, original_method: Callable, send_dsl: "SendDSL"):
    """
    为发送方法注入生命周期钩子

    仅对返回 Task/Awaitable 的发送方法生效，链式修饰方法（返回 SendDSL）不受影响。
    不改变原方法的返回值类型或执行行为，仅在 Task 上添加回调来触发钩子。
    """

    def hooked(*args, **kwargs):
        # 嵌套委托防护：若当前已在规则包装执行中（如 Text 内部调用 Raw_ob12），
        # 内层调用不重复应用规则与生命周期事件，直接返回原始结果
        already_wrapping = getattr(send_dsl, "_in_rule_wrap", False)

        if already_wrapping:
            return original_method(*args, **kwargs)

        # 标记进入规则包装执行，防止内部委托方法（Text → Raw_ob12）重复包装
        send_dsl._in_rule_wrap = True
        try:
            result = original_method(*args, **kwargs)
        finally:
            send_dsl._in_rule_wrap = False

        if isinstance(result, SendDSL):
            return result

        if not isinstance(result, asyncio.Task):
            return result

        platform = getattr(send_dsl._adapter, "_platform", "") or ""
        send_ctx = {
            "platform": platform,
            "method": method_name,
            "detail_type": send_dsl._target_type or "",
            "target_id": send_dsl._target_id or "",
            "bot_id": send_dsl._account_id or "",
        }

        from ..adapter import _msg_logger

        target_type = send_dsl._target_type or ""
        target_id = send_dsl._target_id or ""
        log_target = (
            f"{target_type}/{target_id}"
            if target_type and target_id
            else target_id or "?"
        )
        if method_name in ("Text", "Markdown", "Html") and args:
            content = str(args[0])
            if len(content) > LOG_MESSAGE_TRUNCATE_CHARS:
                content = content[:LOG_MESSAGE_TRUNCATE_CHARS] + "..."
            _msg_logger.event(
                f"[Send] {platform}/{method_name} -> {log_target}: {content}"
            )
        else:
            _msg_logger.event(f"[Send] {platform}/{method_name} -> {log_target}")

        # 预判是否有生命周期监听者：无监听时跳过 Task 创建与 emit 调度，
        # 避免每条发送消息都无条件 spawn 两个后台任务
        from ..lifecycle import lifecycle

        _has_sending_hooks = lifecycle.has_handlers("message.sending")
        _has_sent_hooks = lifecycle.has_handlers("message.sent")

        async def _emit_hooks():
            await lifecycle.emit("message.sending", send_ctx)

        async def _emit_hooks_done(_):
            await lifecycle.emit("message.sent", send_ctx)

        # fire-and-forget：交给事件循环调度，无需保留引用
        if _has_sending_hooks:
            from ...runtime.tasks import spawn_background

            spawn_background(_emit_hooks())

        # 若附加了发送规则，用规则执行器统一包装 Task
        if _has_rules(send_dsl):
            from .send_rules import apply_send_rules

            # base_task_factory 每次重试需要重新发起，因此返回 result（首次）或重新调用
            # 这里使用工厂模式：首次返回已创建的 result，后续重试重新调用 original_method
            call_args = (args, kwargs)
            first_called = {"done": False}

            def _base_task_factory():
                if not first_called["done"]:
                    first_called["done"] = True
                    return result
                # 重试：重新调用原始发送方法（重试子任务不重复触发生命周期事件，
                # 仅最终包装任务完成时统一触发 message.sent）
                send_dsl._in_rule_wrap = True
                try:
                    retry_result = original_method(*call_args[0], **call_args[1])
                finally:
                    send_dsl._in_rule_wrap = False
                if not isinstance(retry_result, asyncio.Task):
                    retry_result = asyncio.ensure_future(_wrap_to_task(retry_result))
                return retry_result

            wrapped = apply_send_rules(
                _base_task_factory,
                rules=send_dsl._rules,
                send_ctx=send_ctx,
            )
            # message.sent 绑定到包装任务完成（覆盖整体重试流程），
            # 不绑定到首次内部 result（避免失败重试时提前触发）
            if _has_sent_hooks:
                wrapped.add_done_callback(
                    lambda t: asyncio.ensure_future(_emit_hooks_done(t))
                )
            return wrapped

        # 无规则：保持原有行为，message.sent 在单次发送完成后触发
        if _has_sent_hooks:
            result.add_done_callback(lambda t: asyncio.ensure_future(_emit_hooks_done(t)))
        return result

    return hooked


class SendDSL:
    """
    消息发送DSL基类

    用于实现 Send.To(...).Func(...) 风格的链式调用接口

    内置支持 At/AtAll/Reply 修饰器，适配器子类无需重复实现。
    内置标准发送方法（Text/Image/Voice/Video/File），默认委托给 Raw_ob12，
    适配器只需实现 Raw_ob12 即可获得全部标准发送能力，也可覆盖单个方法以提供平台特定逻辑。
    通过 send_context 属性可显式获取发送上下文（目标类型、目标ID、发送账号）。
    通过 _apply_modifiers() 方法可自动将修饰器状态合并到消息段。

    {!--< tips >!--}
    1. 适配器必须实现 Raw_ob12（OneBot12 消息段 → 平台 API 的统一入口）
    2. 标准发送方法（Text/Image/Voice/Video/File）已内置并委托给 Raw_ob12，无需子类重复实现
    3. 子类可覆盖标准方法以提供平台特定逻辑，也可添加平台特有方法（如 Sticker）
    4. At/AtAll/Reply 已内置实现，无需子类覆盖
    5. 使用 self.send_context 获取发送上下文
    6. 使用 self._apply_modifiers(message) 合并修饰器到消息段
    7. 链式修饰方法（To/Using/At/Hook/Retry 等）返回 Self，使 IDE 能在链式调用中补全子类方法
    {!--< /tips >!--}
    """

    def __init__(
        self,
        adapter: "BaseAdapter",
        target_type: str | None = None,
        target_id: str | None = None,
        account_id: str | None = None,
        rules: dict | None = None,
    ):
        """
        初始化DSL发送器

        :param adapter: 所属适配器实例
        :param target_type: 目标类型(可选)
        :param target_id: 目标ID(可选)
        :param account_id: 发送账号(可选)
        :param rules: 已附加的发送规则字典(可选，用于 To/Using/Account 传播)
        """
        self._adapter = adapter
        self._target_type = target_type
        self._target_id = target_id
        self._target_to = target_id
        self._account_id = account_id
        self._at_user_ids: list[str] = []
        self._reply_message_id: str | None = None
        self._at_all: bool = False
        # 发送规则（超时/重试/回调/延迟/优先级/进度上下文）
        # 注意：hooks 为列表，必须深拷贝以避免多实例共享同一列表
        self._rules: dict = _copy_rules(rules) if rules else {}
        # 防止嵌套方法委托（如 Text → Raw_ob12）重复应用规则的标记
        self._in_rule_wrap: bool = False

    def __getattribute__(self, name):
        attr = object.__getattribute__(self, name)

        if name.startswith("_") or not callable(attr):
            return attr

        if name in _CHAIN_MODIFIER_NAMES:
            return attr

        return _wrap_send_method(name, attr, self)

    def __getattr__(self, name: str):
        """
        动态属性访问处理，实现大小写不敏感调用

        1. 如果找到匹配的方法（忽略大小写），返回该方法
        2. 如果没找到，打印警告并抛出 AttributeError

        :param name: 属性名
        :return: 匹配的方法或属性
        :raises AttributeError: 当属性不存在时抛出
        """
        for attr_name in dir(self.__class__):
            if attr_name.startswith("_"):
                continue

            if attr_name.lower() == name.lower():
                attr = getattr(self.__class__, attr_name)
                if callable(attr):
                    resolved = attr.__get__(self, self.__class__)
                    if attr_name not in _CHAIN_MODIFIER_NAMES:
                        return _wrap_send_method(attr_name, resolved, self)
                    return resolved
                return attr

        from ..logger import logger

        logger.warning(
            f"平台 {self._adapter.__class__.__name__} 未实现 {name} 发送方法"
        )

        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )

    def At(self, user_id: str) -> "Self":
        """
        @指定用户（可链式多次调用）

        :param user_id: 要@的用户ID
        :return: SendDSL实例自身，支持链式调用

        :example:
        >>> await adapter.Send.To("group", "123").At("456").Text("Hello")
        >>> await adapter.Send.To("group", "123").At("456").At("789").Text("@多人")
        """
        self._at_user_ids.append(user_id)
        return self

    def AtAll(self) -> "Self":
        """
        @全体成员

        :return: SendDSL实例自身，支持链式调用

        :example:
        >>> await adapter.Send.To("group", "123").AtAll().Text("公告")
        """
        self._at_all = True
        return self

    def Reply(self, message_id: str) -> "Self":
        """
        回复指定消息

        :param message_id: 要回复的消息ID
        :return: SendDSL实例自身，支持链式调用

        :example:
        >>> await adapter.Send.To("group", "123").Reply("msg_456").Text("回复内容")
        """
        self._reply_message_id = message_id
        return self

    def _apply_modifiers(self, message) -> list[dict]:
        """
        将 At/AtAll/Reply 修饰器应用到消息段

        修饰器按以下顺序添加到消息段前：
        1. mention_all (@全体)
        2. mention (@用户，按调用顺序)
        3. reply (回复)

        :param message: OneBot12 消息段（dict 或 list[dict]）
        :return: 合并后的消息段列表

        :example:
        >>> segments = self._apply_modifiers([
        >>>     {"type": "text", "data": {"text": "Hello"}}
        >>> ])
        """
        if isinstance(message, dict):
            segments = [message]
        else:
            segments = list(message)

        modifier_segments = []

        if self._at_all:
            modifier_segments.append({"type": "mention_all", "data": {}})

        modifier_segments.extend(
            {"type": "mention", "data": {"user_id": uid}}
            for uid in self._at_user_ids
        )

        if self._reply_message_id:
            modifier_segments.append(
                {"type": "reply", "data": {"message_id": self._reply_message_id}}
            )

        return modifier_segments + segments

    @property
    def send_context(self) -> dict:
        """
        获取当前发送上下文（目标信息 + 发送账号）

        :return: 包含 target_type, target_id, account_id 的字典

        :example:
        >>> ctx = self.send_context
        >>> # {"target_type": "group", "target_id": "123", "account_id": "bot1"}
        >>> await self._adapter.call_api(
        >>>     endpoint="/send_message",
        >>>     message=segments,
        >>>     **self.send_context,
        >>>     **kwargs
        >>> )
        """
        return {
            "target_type": self._target_type,
            "target_id": self._target_id,
            "account_id": self._account_id,
        }

    def Raw_ob12(self, message, **kwargs) -> Awaitable[Any]:
        """
        发送 OneBot12 格式消息段（必须由适配器子类重写）

        :param message: OneBot12 消息段列表或单个消息段
        :param kwargs: 其他参数
        :return: asyncio.Task
        """
        from ..logger import logger

        logger.error(
            f"平台 {self._adapter.__class__.__name__} 未实现 Raw_ob12 方法，"
            f"消息未被发送。适配器必须实现此方法以支持 OneBot12 消息段发送。"
        )

        async def _not_impl():
            return {
                "status": STATUS_FAILED,
                "retcode": RETCODE_NOT_IMPLEMENTED,
                "data": None,
                "message_id": "",
                "message": f"平台 {self._adapter.__class__.__name__} 未实现 Raw_ob12 方法",
            }

        try:
            return asyncio.create_task(_not_impl())
        except RuntimeError:
            return asyncio.ensure_future(_not_impl())

    # ==================== 标准发送方法 ====================
    # 这些方法提供类型签名供 IDE 补全，默认实现委托给 Raw_ob12。
    # 适配器子类可覆盖以提供平台特定逻辑，无需覆盖时自动走 Raw_ob12。

    def Text(self, text: str) -> Awaitable[Any]:
        """
        发送文本消息

        默认实现委托给 :meth:`Raw_ob12`，适配器可覆盖以提供平台特定逻辑。

        :param text: 文本内容
        :return: asyncio.Task，await 后返回标准响应格式

        :example:
        >>> await adapter.Send.To("user", "123").Text("Hello")
        """
        return self.Raw_ob12([{"type": "text", "data": {"text": text}}])

    def Image(self, file: str | bytes) -> Awaitable[Any]:
        """
        发送图片消息

        默认实现委托给 :meth:`Raw_ob12`，适配器可覆盖以提供平台特定逻辑。

        :param file: 图片文件（URL、路径或二进制数据）
        :return: asyncio.Task，await 后返回标准响应格式

        :example:
        >>> await adapter.Send.To("user", "123").Image("https://example.com/img.png")
        """
        return self.Raw_ob12([{"type": "image", "data": {"file": file}}])

    def Voice(self, file: str | bytes) -> Awaitable[Any]:
        """
        发送语音消息

        默认实现委托给 :meth:`Raw_ob12`（OneBot12 ``audio`` 段），
        适配器可覆盖以提供平台特定逻辑。

        :param file: 语音文件（URL、路径或二进制数据）
        :return: asyncio.Task，await 后返回标准响应格式

        :example:
        >>> await adapter.Send.To("user", "123").Voice("https://example.com/voice.mp3")
        """
        return self.Raw_ob12([{"type": "audio", "data": {"file": file}}])

    def Video(self, file: str | bytes) -> Awaitable[Any]:
        """
        发送视频消息

        默认实现委托给 :meth:`Raw_ob12`，适配器可覆盖以提供平台特定逻辑。

        :param file: 视频文件（URL、路径或二进制数据）
        :return: asyncio.Task，await 后返回标准响应格式

        :example:
        >>> await adapter.Send.To("user", "123").Video("https://example.com/video.mp4")
        """
        return self.Raw_ob12([{"type": "video", "data": {"file": file}}])

    def File(self, file: str | bytes, filename: str | None = None) -> Awaitable[Any]:
        """
        发送文件

        默认实现委托给 :meth:`Raw_ob12`，适配器可覆盖以提供平台特定逻辑。

        :param file: 文件（URL、路径或二进制数据）
        :param filename: 文件名（可选，部分平台需要）
        :return: asyncio.Task，await 后返回标准响应格式

        :example:
        >>> await adapter.Send.To("user", "123").File("https://example.com/doc.pdf")
        """
        data = {"file": file}
        if filename is not None:
            data["filename"] = filename
        return self.Raw_ob12([{"type": "file", "data": data}])

    def To(self, target_type: str | None = None, target_id: str | int | None = None) -> "Self":
        """
        设置消息目标

        支持自动类型转换（遵循 :ref:`session-type` 规范）：
        - 如果 ``target_type`` 是接收类型（如 ``"private"``），自动转换为对应的发送类型（``"user"``）
        - 如果只提供 ``target_id``（字符串或数字）但未指定类型，默认推断为 ``"user"``
        - 发送类型（``"user"``/``"group"``/``"channel"``/``"guild"``/``"thread"``）保持原样

        :param target_type: 目标类型（接收类型或发送类型均可，None 时自动推断）
        :param target_id: 目标ID（可选）
        :return: SendDSL 实例

        :example:
        >>> # 标准用法（直接指定发送类型）
        >>> adapter.Send.To("user", "123").Text("Hello")
        >>> # 自动转换 private → user
        >>> adapter.Send.To("private", "123").Text("Hello")
        >>> # 简化形式（默认推断为 user）
        >>> adapter.Send.To("123").Text("Hello")
        """

        # 处理简化形式：只提供一个参数作为 target_id
        if target_id is None and target_type is not None:
            target_id = target_type
            target_type = None

        # 如果没有明确指定 target_type，尝试推断
        if target_type is None:
            if target_id is not None:
                target_type = DEFAULT_SEND_TARGET_TYPE

        # 按会话类型规范自动转换：接收类型 → 发送类型
        # （例如 "private" → "user"，其他类型保持原样）
        from ..Event.session_type import convert_to_send_type

        target_type = convert_to_send_type(target_type)

        instance = self.__class__(
            self._adapter,
            target_type,
            str(target_id) if target_id is not None else None,
            str(self._account_id) if self._account_id is not None else None,
        )
        if self._rules:
            instance._rules = _copy_rules(self._rules)
        return instance

    def Using(self, account_id: str | int) -> "Self":
        """
        设置发送账号

        :param _account_id: 发送账号
        :return: SendDSL实例

        :example:
        >>> adapter.Send.Using("bot1").To("123").Text("Hello")
        >>> adapter.Send.To("123").Using("bot1").Text("Hello")  # 支持乱序
        """
        instance = self.__class__(
            self._adapter,
            self._target_type,
            self._target_id,
            str(account_id),
        )
        if self._rules:
            instance._rules = _copy_rules(self._rules)
        return instance

    def Account(self, account_id: str | int) -> "Self":
        """
        设置发送账号

        :param _account_id: 发送账号
        :return: SendDSL实例

        :example:
        >>> adapter.Send.Account("bot1").To("123").Text("Hello")
        >>> adapter.Send.To("123").Account("bot1").Text("Hello")  # 支持乱序
        """
        instance = self.__class__(
            self._adapter,
            self._target_type,
            self._target_id,
            str(account_id),
        )
        if self._rules:
            instance._rules = _copy_rules(self._rules)
        return instance

    # ==================== 发送规则装饰器 ====================

    def Hook(self, callback: Callable) -> "Self":
        """
        附加发送成功后的回调钩子

        仅当发送最终成功（包括重试成功）时执行，失败/超时/取消不触发。
        可链式多次调用以添加多个 Hook，按添加顺序依次执行。

        :param callback: 回调函数，签名为 ``callback(result)``，可为同步或协程函数
        :return: SendDSL实例自身，支持链式调用

        :example:
        >>> await adapter.Send.To("user", "123").Hook(
        ...     lambda r: print("发送成功！")
        ... ).Text("你好")
        >>>
        >>> async def on_success(result):
        ...     print(f"消息ID: {result.get('message_id')}")
        >>> await adapter.Send.To("user", "123").Hook(on_success).Text("异步回调")
        """
        self._rules.setdefault("hooks", []).append(callback)
        return self

    def Retry(self, times: int = 1) -> "Self":
        """
        设置失败自动重试次数

        含首次发送共尝试 ``times + 1`` 次。重试触发条件：
        - 发送抛出异常
        - 发送超时（配合 :meth:`Timeout` 使用）
        - 发送返回 ``status == "failed"`` 的响应

        :param times: 重试次数（不含首次发送），默认 1
        :return: SendDSL实例自身，支持链式调用

        :example:
        >>> # 首次失败后重试2次，共3次尝试
        >>> await adapter.Send.To("user", "123").Retry(2).Text("带重试")
        """
        self._rules["retry"] = max(1, int(times) + 1)
        return self

    def Timeout(self, seconds: float) -> "Self":
        """
        设置单次发送超时时间

        超时后取消当前尝试。若同时设置了 :meth:`Retry`，超时也会触发重试。

        :param seconds: 超时秒数
        :return: SendDSL实例自身，支持链式调用

        :example:
        >>> await adapter.Send.To("user", "123").Timeout(10).Text("带超时")
        """
        self._rules["timeout"] = max(0.0, float(seconds))
        return self

    def Defer(self, seconds: float = 1.0) -> "Self":
        """
        延迟发送

        在实际发起发送前等待 ``seconds`` 秒。用于延迟提醒、定时消息等场景。
        注意：此延迟为进程内定时，重启进程会丢失，不提供持久化。

        :param seconds: 延迟秒数，默认 1.0
        :return: SendDSL实例自身，支持链式调用

        :example:
        >>> # 5秒后发送
        >>> await adapter.Send.To("user", "123").Defer(5).Text("迟到消息")
        """
        self._rules["defer"] = max(0.0, float(seconds))
        return self

    def Priority(self, level: int = 0, *, drop_if_busy: bool = False) -> "Self":
        """
        设置消息优先级

        优先级会被记录到 :class:`SendContext` 的 ``extra["priority"]``，
        供业务层监控或自定义调度使用。

        当 ``drop_if_busy=True`` 时，启用积压丢弃：若当前在途发送任务数
        超过阈值（默认 64，可通过 :meth:`PriorityThreshold` 调整），
        直接放弃本次发送（返回 ``stage="dropped"``），避免队列堆积。

        :param level: 优先级数值，越大越优先（默认 0）
        :param drop_if_busy: 是否在队列积压时丢弃本消息（默认 False）
        :return: SendDSL实例自身，支持链式调用

        :example:
        >>> # 低优先级消息，积压时自动丢弃
        >>> await (adapter.Send.To("user", "123")
        ...       .Priority(-1, drop_if_busy=True)
        ...       .Text("可放弃的通知"))
        """
        self._rules["priority"] = int(level)
        if drop_if_busy:
            self._rules["drop_if_busy"] = True
        return self

    def PriorityThreshold(self, threshold: int) -> "Self":
        """
        设置优先级丢弃的积压阈值（全局生效）

        配合 :meth:`Priority` 的 ``drop_if_busy=True`` 使用。

        :param threshold: 在途发送任务数阈值，超过则丢弃新消息
        :return: SendDSL实例自身，支持链式调用
        """
        from .send_rules import _PriorityQueue

        _PriorityQueue.set_threshold(threshold)
        return self

    def OnProgress(self, callback: Callable) -> "Self":
        """
        设置进度回调

        在发送的各个阶段（pending/sending/retrying/success/failed/timeout/cancelled/dropped）
        调用，传入实时更新的 :class:`SendContext`。可据此实现监控、日志、介入决策。

        :param callback: 回调函数，签名为 ``callback(ctx: SendContext)``，
            可为同步或协程函数
        :return: SendDSL实例自身，支持链式调用

        :example:
        >>> def on_progress(ctx):
        ...     print(f"阶段: {ctx.stage}, 尝试: {ctx.attempt + 1}/{ctx.max_attempts}")
        ...     if ctx.stage == "failed":
        ...         print(f"错误: {ctx.error!r}")
        >>> task = (adapter.Send.To("user", "123")
        ...        .Retry(3).Timeout(10).OnProgress(on_progress).Text("监控"))
        """
        self._rules["on_progress"] = callback
        return self

    def OnError(self, callback: Callable) -> "Self":
        """
        设置错误回调

        当发送最终失败（重试耗尽仍失败、超时、取消）时调用一次，
        传入最终的 :class:`SendContext`（``ctx.error`` 为异常对象，超时时为
        :class:`asyncio.TimeoutError`）。

        与 :meth:`OnProgress` 的区别：OnProgress 在每个阶段都触发，
        OnError 仅在最终失败时触发一次。

        :param callback: 回调函数，签名为 ``callback(ctx: SendContext)``，
            可为同步或协程函数
        :return: SendDSL实例自身，支持链式调用

        :example:
        >>> async def on_error(ctx):
        ...     await admin_notify(f"发送失败: {ctx.target_id} {ctx.error!r}")
        >>> await (adapter.Send.To("user", "123")
        ...       .Retry(2).OnError(on_error).Text("带错误处理"))
        """
        self._rules["on_error"] = callback
        return self

    # ==================== 批量构建模式 ====================

    def Build(self):
        """
        进入批量构建模式，返回 :class:`SendBuilder`

        在构建模式下，发送方法（Text/Image 等）不再立即执行，而是累积为发送意图，
        最后通过 ``send_all()`` 统一执行。规则统一作用于整批。

        进入 Build 之前的 At/AtAll/Reply 修饰器和已设置的规则会继承到整批。

        :return: :class:`SendBuilder` 实例

        :example:
        >>> # 构建多条消息，统一发送
        >>> results = await (adapter.Send.To("user", "123")
        ...                  .Build()
        ...                  .Text("第一句")
        ...                  .Image("pic.jpg")
        ...                  .Text("第二句")
        ...                  .send_all())
        >>> # results = [Text结果, Image结果, Text结果]
        >>>
        >>> # 串行执行 + 重试失败的
        >>> await (adapter.Send.To("group", "456")
        ...        .Build()
        ...        .Sequential()
        ...        .Retry(2)
        ...        .Text("保证顺序1").Text("保证顺序2")
        ...        .send_all())
        """
        from .send_builder import SendBuilder

        return SendBuilder(self)


class RequestDSL:
    """
    请求操作 DSL 基类

    用于对请求事件（好友请求、群邀请等）执行同意/拒绝操作。
    采用与 Send 一致的工厂实例模式：``adapter.Request("req_id").accept()``

    适配器只需在内部类中重写 ``accept`` / ``reject`` 即可。

    {!--< tips >!--}
    1. 使用 ``adapter.Request(request_id).accept()`` 同意请求
    2. 使用 ``adapter.Request(request_id).reject()`` 拒绝请求
    3. 适配器重写 ``accept`` / ``reject`` 实现平台逻辑
    4. 基类默认返回 ``retcode=10002``（不支持的操作）
    {!--< /tips >!--}
    """

    def __init__(
        self,
        adapter: "BaseAdapter",
        request_id: str | None = None,
        account_id: str | None = None,
    ):
        """
        初始化请求操作 DSL

        :param adapter: 所属适配器实例
        :param request_id: 请求ID
        :param account_id: 执行操作的 Bot 账号
        """
        self._adapter = adapter
        self._request_id = request_id
        self._account_id = account_id

    def __call__(self, request_id: str) -> "Self":
        """
        设置请求ID，返回新的 RequestDSL 实例

        使得 ``adapter.Request("req_id")`` 可以直接调用

        :param request_id: 请求ID
        :return: 新的 RequestDSL 实例
        """
        return self.__class__(self._adapter, request_id, self._account_id)

    def Using(self, account_id: str | int) -> "Self":
        """
        指定执行操作的 Bot 账号

        :param account_id: 账号标识
        :return: 新的 RequestDSL 实例

        :example:
        >>> adapter.Request("req_123").Using("bot1").accept()
        """
        return self.__class__(self._adapter, self._request_id, str(account_id))

    def accept(self, **kwargs) -> Awaitable[Any]:
        """
        同意请求

        :param kwargs: 平台扩展参数（如 comment 备注）
        :return: asyncio.Task，await 后返回标准响应格式

        :example:
        >>> result = await adapter.Request("req_123").accept()
        >>> result = await adapter.Request("req_123").accept(comment="欢迎")
        """
        return self._create_task(self._do_accept(**kwargs))

    def reject(self, **kwargs) -> Awaitable[Any]:
        """
        拒绝请求

        :param kwargs: 平台扩展参数（如 comment 拒绝理由）
        :return: asyncio.Task，await 后返回标准响应格式

        :example:
        >>> result = await adapter.Request("req_123").reject()
        >>> result = await adapter.Request("req_123").reject(comment="暂不添加")
        """
        return self._create_task(self._do_reject(**kwargs))

    async def _do_accept(self, **kwargs) -> dict[str, Any]:
        """
        同意请求的具体实现（适配器子类重写）

        :param kwargs: 平台扩展参数
        :return: 标准响应格式
        """
        return self._not_implemented_response("accept")

    async def _do_reject(self, **kwargs) -> dict[str, Any]:
        """
        拒绝请求的具体实现（适配器子类重写）

        :param kwargs: 平台扩展参数
        :return: 标准响应格式
        """
        return self._not_implemented_response("reject")

    def _not_implemented_response(self, action: str) -> dict[str, Any]:
        """
        生成「未实现」的标准错误响应

        :param action: 操作名称（accept/reject）
        :return: 标准错误响应字典
        """
        from ..logger import logger

        platform_name = self._adapter.__class__.__name__
        logger.warning(
            f"平台 {platform_name} 未实现 Request.{action}() 方法，"
            f"请求 {self._request_id} 未被处理。"
        )
        return {
            "status": STATUS_FAILED,
            "retcode": RETCODE_NOT_IMPLEMENTED,
            "data": None,
            "message_id": "",
            "message": f"平台 {platform_name} 未实现请求操作 ({action})",
        }

    def _create_task(self, coro) -> Awaitable[Any]:
        """创建 asyncio.Task"""
        try:
            return asyncio.create_task(coro)
        except RuntimeError:
            return asyncio.ensure_future(coro)

    @property
    def request_context(self) -> dict:
        """
        获取当前请求操作上下文

        :return: 包含 request_id, account_id 的字典
        """
        return {
            "request_id": self._request_id,
            "account_id": self._account_id,
        }


class ApiDSL:
    """
    标准 API 动作 DSL 基类

    提供 OneBot12 标准动作（get_user_info / get_group_info 等）的强类型方法，
    模块开发者只需面向标准接口编程，由适配器负责映射到平台原生 API。

    与 SendDSL（消息发送）、RequestDSL（请求操作）并行，覆盖 OneBot12
    标准动作中的「信息查询 / 状态变更 / 消息管理 / 文件操作」四类操作。

    {!--< tips >!--}
    1. 标准方法默认委托给 ``adapter.call_api(action_name, ...)``，适配器可按需覆盖
    2. 使用 ``adapter.Api.Using("bot1").get_user_info("123")`` 指定 Bot 账号
    3. 平台扩展动作通过 ``call("prefix.action", **params)`` 调用
    4. 所有方法返回标准 API 响应格式（status / retcode / data / message_id / message）
    5. 适配器可覆盖单个标准方法以映射到平台 API，无需全部实现
    {!--< /tips >!--}
    """

    def __init__(
        self,
        adapter: "BaseAdapter",
        account_id: str | None = None,
    ):
        """
        初始化标准 API 动作 DSL

        :param adapter: 所属适配器实例
        :param account_id: 执行操作的 Bot 账号（可选）
        """
        self._adapter = adapter
        self._account_id = account_id

    def Using(self, account_id: str | int) -> "Self":
        """
        指定执行操作的 Bot 账号

        :param account_id: 账号标识
        :return: 新的 ApiDSL 实例

        :example:
        >>> info = await adapter.myplatform.Api.Using("bot1").get_user_info("123")
        """
        return self.__class__(self._adapter, str(account_id))

    @property
    def api_context(self) -> dict:
        """
        获取当前 API 操作上下文

        :return: 包含 account_id 的字典
        """
        return {
            "account_id": self._account_id,
        }

    def _merge_context(self, params: dict) -> dict:
        """
        将 api_context 合并到参数字典

        :param params: 业务参数
        :return: 合并后的参数字典
        """
        merged = dict(params)
        merged.update(self.api_context)
        return merged

    # ==================== 用户相关动作 ====================

    async def get_self_info(self) -> dict[str, Any]:
        """
        获取机器人自身信息

        :return: 标准响应，data 包含 user_id / user_name / user_displayname

        :example:
        >>> result = await adapter.myplatform.Api.get_self_info()
        >>> my_name = result["data"]["user_name"]
        """
        return await self._adapter.call_api(
            "get_self_info", **self._merge_context({})
        )

    async def get_user_info(self, user_id: str) -> dict[str, Any]:
        """
        获取用户信息

        :param user_id: 用户 ID（可以是好友，也可以是陌生人）
        :return: 标准响应，data 包含 user_id / user_name / user_displayname / user_remark

        :example:
        >>> result = await adapter.myplatform.Api.get_user_info("123456")
        >>> user_name = result["data"]["user_name"]
        """
        return await self._adapter.call_api(
            "get_user_info", **self._merge_context({"user_id": str(user_id)})
        )

    async def get_friend_list(self) -> dict[str, Any]:
        """
        获取好友列表

        :return: 标准响应，data 为好友信息列表

        :example:
        >>> result = await adapter.myplatform.Api.get_friend_list()
        >>> friends = result["data"]
        """
        return await self._adapter.call_api(
            "get_friend_list", **self._merge_context({})
        )

    # ==================== 群组相关动作 ====================

    async def get_group_info(self, group_id: str) -> dict[str, Any]:
        """
        获取群信息

        :param group_id: 群 ID
        :return: 标准响应，data 包含 group_id / group_name

        :example:
        >>> result = await adapter.myplatform.Api.get_group_info("123456")
        >>> group_name = result["data"]["group_name"]
        """
        return await self._adapter.call_api(
            "get_group_info", **self._merge_context({"group_id": str(group_id)})
        )

    async def get_group_list(self) -> dict[str, Any]:
        """
        获取群列表

        :return: 标准响应，data 为群信息列表

        :example:
        >>> result = await adapter.myplatform.Api.get_group_list()
        >>> groups = result["data"]
        """
        return await self._adapter.call_api(
            "get_group_list", **self._merge_context({})
        )

    async def get_group_member_info(
        self, group_id: str, user_id: str
    ) -> dict[str, Any]:
        """
        获取群成员信息

        :param group_id: 群 ID
        :param user_id: 用户 ID
        :return: 标准响应，data 包含 user_id / user_name / user_displayname

        :example:
        >>> result = await adapter.myplatform.Api.get_group_member_info("123", "456")
        >>> member = result["data"]
        """
        return await self._adapter.call_api(
            "get_group_member_info",
            **self._merge_context({"group_id": str(group_id), "user_id": str(user_id)})
        )

    async def get_group_member_list(self, group_id: str) -> dict[str, Any]:
        """
        获取群成员列表

        :param group_id: 群 ID
        :return: 标准响应，data 为群成员信息列表

        :example:
        >>> result = await adapter.myplatform.Api.get_group_member_list("123456")
        >>> members = result["data"]
        """
        return await self._adapter.call_api(
            "get_group_member_list",
            **self._merge_context({"group_id": str(group_id)})
        )

    async def set_group_name(self, group_id: str, group_name: str) -> dict[str, Any]:
        """
        设置群名称

        :param group_id: 群 ID
        :param group_name: 新群名称
        :return: 标准响应

        :example:
        >>> await adapter.myplatform.Api.set_group_name("123456", "新群名")
        """
        return await self._adapter.call_api(
            "set_group_name",
            **self._merge_context({"group_id": str(group_id), "group_name": group_name})
        )

    async def leave_group(self, group_id: str) -> dict[str, Any]:
        """
        退出群

        :param group_id: 群 ID
        :return: 标准响应

        :example:
        >>> await adapter.myplatform.Api.leave_group("123456")
        """
        return await self._adapter.call_api(
            "leave_group", **self._merge_context({"group_id": str(group_id)})
        )

    # ==================== 消息管理动作 ====================

    async def delete_message(self, message_id: str) -> dict[str, Any]:
        """
        撤回 / 删除消息

        :param message_id: 消息 ID
        :return: 标准响应

        :example:
        >>> await adapter.myplatform.Api.delete_message("msg_123456")
        """
        return await self._adapter.call_api(
            "delete_message",
            **self._merge_context({"message_id": str(message_id)})
        )

    # ==================== 文件相关动作 ====================

    async def upload_file(
        self,
        *,
        type: str,
        name: str,
        url: str | None = None,
        path: str | None = None,
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
        sha256: str | None = None,
    ) -> dict[str, Any]:
        """
        上传文件

        :param type: 上传方式（``url`` / ``path`` / ``data``）
        :param name: 文件名（如 ``foo.jpg``）
        :param url: 文件 URL（``type="url"`` 时必须传入）
        :param path: 文件路径（``type="path"`` 时必须传入）
        :param data: 文件数据（``type="data"`` 时必须传入）
        :param headers: 下载 URL 时附加的 HTTP 请求头（可选）
        :param sha256: 文件数据的 SHA256 校验和（可选）
        :return: 标准响应，data 包含 file_id

        :example:
        >>> result = await adapter.Api.upload_file(
        ...     type="url", name="logo.jpg", url="https://example.com/logo.jpg"
        ... )
        >>> file_id = result["data"]["file_id"]
        """
        params: dict[str, Any] = {"type": type, "name": name}
        if url is not None:
            params["url"] = url
        if path is not None:
            params["path"] = path
        if data is not None:
            params["data"] = data
        if headers is not None:
            params["headers"] = headers
        if sha256 is not None:
            params["sha256"] = sha256
        return await self._adapter.call_api(
            "upload_file", **self._merge_context(params)
        )

    async def get_file(
        self, file_id: str, type: str = "url"
    ) -> dict[str, Any]:
        """
        获取文件

        :param file_id: 文件 ID
        :param type: 获取方式（``url`` / ``path`` / ``data``），默认 ``url``
        :return: 标准响应，data 包含 name / url 或 path 或 data

        :example:
        >>> result = await adapter.myplatform.Api.get_file("file_abc", "url")
        >>> download_url = result["data"]["url"]
        """
        return await self._adapter.call_api(
            "get_file",
            **self._merge_context({"file_id": str(file_id), "type": type})
        )

    # ==================== 通用扩展动作 ====================

    async def call(self, action: str, **params: Any) -> dict[str, Any]:
        """
        调用平台扩展动作（逃生舱）

        用于调用 OneBot12 标准之外的平台扩展动作。
        建议使用 ``{prefix}.{action}`` 命名（如 ``telegram.send_sticker``），
        遵循 OneBot12 扩展规则。

        :param action: 动作名称（标准动作名或 ``{prefix}.{action}`` 扩展动作名）
        :param params: 动作参数
        :return: 标准响应格式

        :example:
        >>> # 调用平台扩展动作
        >>> result = await adapter.myplatform.Api.call(
        ...     "telegram.send_sticker", sticker_id="CAACAgIAAxkBAA..."
        ... )
        >>>
        >>> # 也可用于调用标准动作（等价于直接调用对应方法）
        >>> result = await adapter.myplatform.Api.call(
        ...     "get_user_info", user_id="123"
        ... )
        """
        return await self._adapter.call_api(
            action, **self._merge_context(params)
        )


class BaseAdapter(ABC):
    """
    适配器基类

    提供与外部平台交互的标准接口，子类必须实现必要方法

    {!--< tips >!--}
    1. 必须实现call_api, start和shutdown方法
    2. Send 子类只需实现 Raw_ob12，即可获得全部标准发送方法（Text/Image/Voice/Video/File）
    3. 可以自定义Request类实现平台特定的请求操作逻辑
    4. 通过on装饰器注册事件处理器
    5. 支持OneBot12协议的事件处理
    6. 通过 ConfigClass / AccountConfigClass 声明配置类，框架自动管理配置
    7. 通过 self.cfg / self.accounts 访问类型安全的配置对象（实时读取）
    8. 通过 self.emit_meta() 发送 meta 事件
    9. 通过 self.make_response() / self.make_error() 构造标准化响应
    10. 通过 I18nClass 声明翻译键集合，框架自动注册到 i18n 系统
    {!--< /tips >!--}
    """

    ConfigClass: type | None = None
    AccountConfigClass: type | None = None
    I18nClass: type | None = None
    EventMixin: type | None = None

    _platform: str = ""
    _sdk: Any = None

    class Request(RequestDSL):
        """
        请求操作 DSL 实现

        适配器子类重写 ``accept`` / ``reject`` 以实现平台特定逻辑。

        {!--< tips >!--}
        1. 默认实现返回 ``retcode=10002``（不支持的操作）
        2. 适配器应重写 ``accept`` / ``reject`` 方法
        3. 通过 ``self._adapter.call_api()`` 调用平台 API
        4. 通过 ``self._request_id`` 获取请求标识
        5. 通过 ``self._account_id`` 获取 Bot 账号
        {!--< /tips >!--}
        """

        ...

    class Api(ApiDSL):
        """
        标准 API 动作 DSL 实现

        提供跨平台的 OneBot12 标准动作接口（信息查询、群管理、消息撤回、文件操作等）。

        {!--< tips >!--}
        1. 默认实现委托给 ``adapter.call_api(action_name, ...)``，零配置可用
        2. 适配器可覆盖单个标准方法以映射到平台原生 API
        3. 平台扩展动作通过 ``call("prefix.action", **params)`` 调用
        4. 使用 ``adapter.Api.Using("bot1")`` 指定 Bot 账号
        {!--< /tips >!--}
        """

        ...

    class Send(SendDSL):
        """
        消息发送DSL实现

        {!--< tips >!--}
        1. 必须重写 Raw_ob12 方法（OneBot12 消息段 → 平台 API）
        2. 标准方法（Text/Image/Voice/Video/File）已从 SendDSL 基类继承，默认委托 Raw_ob12
        3. 如需平台特定逻辑，可覆盖单个标准方法（如 Text）
        4. 可添加平台特有的发送方法（如 Sticker）
        {!--< /tips >!--}
        """

        def Example(self, text: str) -> Awaitable[Any]:
            """
            示例消息发送方法

            :param text: 文本内容
            :return: 异步任务
            :example:
            >>> await adapter.Send.To("123").Example("Hello")
            """
            mock_response = {
                "status": STATUS_OK,
                "retcode": RETCODE_OK,
                "data": {"message_id": "1234567890", "time": 1755801512},
                "message_id": "1234567890",
                "message": "",
                "echo": None,
                "example_raw": {
                    "result": "success",
                },
            }

            async def _send_example():
                from ..logger import logger

                logger.info(f"发送示例消息: {text}")
                return mock_response

            return asyncio.create_task(_send_example())

        def Raw_ob12(self, message, **kwargs: Any) -> Awaitable[Any]:
            """
            发送 OneBot12 格式消息段（必须由适配器子类重写）

            此方法是反向转换（OneBot12 → 平台）的统一入口，适配器必须重写此方法。
            未重写时，基类默认实现会记录错误日志并返回标准错误响应。

            推荐使用框架提供的辅助方法：
            - self._apply_modifiers(message) - 合并 At/AtAll/Reply 修饰器到消息段
            - self.send_context - 获取发送上下文 (target_type, target_id, account_id)

            :param message: OneBot12 格式的消息段数组或单个消息段
                [
                    {"type": "text", "data": {"text": "Hello"}},
                    {"type": "image", "data": {"file": "https://..."}},
                ]
            :param kwargs: 其他参数
            :return: asyncio.Task，await 后返回标准响应格式

            :example:
            >>> # 用户调用
            >>> await adapter.Send.To("user", "123").Raw_ob12([
            >>>     {"type": "text", "data": {"text": "Hello"}},
            >>>     {"type": "image", "data": {"file": "https://..."}}
            >>> ])
            >>>
            >>> # 适配器子类重写示例（推荐：使用框架辅助方法）
            >>> def Raw_ob12(self, message, **kwargs):
            >>>     async def _do_send():
            >>>         segments = self._apply_modifiers(message)
            >>>         return await self._adapter.call_api(
            >>>             endpoint="/send_message",
            >>>             message=segments,
            >>>             **self.send_context,
            >>>             **kwargs
            >>>         )
            >>>     return asyncio.create_task(_do_send())
            """

            async def _send_raw():
                from ..logger import logger

                logger.error(
                    f"适配器 {self._adapter.__class__.__name__} 未实现 Raw_ob12 方法，"
                    f"消息未被发送。适配器必须实现此方法以支持 OneBot12 消息段发送。"
                )
                return {
                    "status": STATUS_FAILED,
                    "retcode": RETCODE_NOT_IMPLEMENTED,
                    "data": None,
                    "message_id": "",
                    "message": f"适配器 {self._adapter.__class__.__name__} 未实现 Raw_ob12 方法",
                }

            try:
                return asyncio.create_task(_send_raw())
            except RuntimeError:
                return asyncio.ensure_future(_send_raw())

    def __init__(self, sdk=None):
        super().__init__()
        self._sdk = sdk
        if sdk:
            self.sdk = sdk
            self.logger = sdk.logger.get_child(self.__class__.__name__, relative=False)

        # Send/Request/Api 在类上是嵌套类，实例化后替换为实例。
        # pyright 无法识别这种"实例属性覆盖嵌套类属性"的模式，故显式 cast。
        self.Send = cast("SendDSL", self.__class__.Send(self))  # pyright: ignore[reportAttributeAccessIssue]
        self.Request = cast("RequestDSL", self.__class__.Request(self))  # pyright: ignore[reportAttributeAccessIssue]
        self.Api = cast("ApiDSL", self.__class__.Api(self))  # pyright: ignore[reportAttributeAccessIssue]

        self._config_instance = None
        self._accounts_data = None

        # 注册 I18nClass 中声明的翻译键（在生成配置之前）
        self._ensure_i18n_registered()
        # EventMixin 的注册由 AdapterManager 在注入 _platform 后调用

        # 初始化时确保配置模板存在
        if self.ConfigClass is not None:
            self._ensure_config_exists()
            # 向后兼容：子类可覆写 _load_config() 实现自定义加载
            custom_cfg = self._load_config()
            if custom_cfg is not None:
                self._config_instance = custom_cfg
        if self.AccountConfigClass is not None:
            self._ensure_accounts_exist()
            # 向后兼容：子类可覆写 _load_accounts() 实现自定义加载
            custom = self._load_accounts()
            if custom is not None:
                self._accounts_data = custom
            else:
                self._accounts_data = self.accounts

    def _load_accounts(self) -> dict | None:
        """
        {!--< internal-use >!--}
        加载账户配置（可被子类覆写）

        子类可覆写此方法实现自定义账户加载逻辑（如全局配置合并、旧格式迁移等）。
        返回 None 时使用默认配置存储读取逻辑。

        :return: 账户配置字典，或 None 表示使用默认逻辑
        """
        return None

    def _load_config(self):
        """
        {!--< internal-use >!--}
        加载适配器配置（可被子类覆写）

        子类可覆写此方法实现自定义配置加载逻辑（如旧格式迁移等）。
        返回 None 时使用默认配置存储读取逻辑。

        :return: 配置实例，或 None 表示使用默认逻辑
        """
        return

    @abstractmethod
    async def call_api(self, endpoint: str, **params: Any) -> Any:
        """
        调用平台API的抽象方法

        :param endpoint: API端点
        :param params: API参数
        :return: API调用结果
        :raises NotImplementedError: 必须由子类实现
        """
        raise NotImplementedError("适配器必须实现call_api方法")

    @abstractmethod
    async def start(self) -> None:
        """
        启动适配器的抽象方法

        :raises NotImplementedError: 必须由子类实现
        """
        raise NotImplementedError("适配器必须实现start方法")

    @abstractmethod
    async def shutdown(self) -> None:
        """
        关闭适配器的抽象方法

        :raises NotImplementedError: 必须由子类实现
        """
        raise NotImplementedError("适配器必须实现shutdown方法")

    @property
    def cfg(self):
        """
        类型安全的配置对象（实时读取）

        每次访问都从配置存储读取最新值，确保用户修改配置后立即生效。
        返回的 dataclass 实例是只读快照，修改它不会回写存储。

        :return: AdapterConfig / BaseConfig 实例
        :raises AttributeError: 未声明 ConfigClass 时抛出

        {!--< tips >!--}
        推荐使用 ``self.cfg`` 而非 ``self.config``，
        后者已弃用且可能被子类属性覆盖产生冲突。
        {!--< /tips >!--}
        """
        if self.ConfigClass is None:
            raise AttributeError(
                "未声明 ConfigClass，请设置 MyAdapter.ConfigClass = MyConfig"
            )

        from ..config import config as config_mgr
        from .config_schema import dict_to_dataclass

        # 适配器的 EventMixin 在 AdapterManager.register() 注入 _platform 后注册
        # __init__ 阶段 _platform 尚未注入，因此不在此处调用

        data = config_mgr.getConfig(self._get_config_key())
        if data is None:
            # 配置不存在时生成默认模板后重试
            self._ensure_config_exists()
            data = config_mgr.getConfig(self._get_config_key()) or {}
        return dict_to_dataclass(self.ConfigClass, data)

    @cfg.setter
    def cfg(self, value):
        """设置配置实例，同时同步写入配置存储（保证实时性）"""
        self._config_instance = value
        if value is not None:
            from dataclasses import asdict

            from ..config import config as config_mgr

            try:
                config_mgr.setConfig(self._get_config_key(), asdict(value))
            except Exception:
                pass

    @property
    def config(self):
        """
        ``self.cfg`` 的兼容别名

        功能与 ``self.cfg`` 完全一致，推荐新代码使用 ``self.cfg``。
        """
        return self.cfg

    @config.setter
    def config(self, value):
        self.cfg = value

    @property
    def accounts(self) -> dict:
        """
        类型安全的账户配置字典（实时读取）

        每次访问都从配置存储读取最新值，确保用户修改账户配置后立即生效。

        :return: 账户配置字典 {name: config_instance}
        :raises AttributeError: 未声明 AccountConfigClass 时抛出
        """
        if self.AccountConfigClass is None:
            raise AttributeError(
                "未声明 AccountConfigClass，请设置 MyAdapter.AccountConfigClass = MyBotConfig"
            )

        from ..config import config as config_mgr
        from .config_schema import dict_to_dataclass, validate_config

        key = f"{self._get_config_key()}.accounts"
        data = config_mgr.getConfig(key)
        if data is None:
            # 配置不存在时生成默认账户模板后重试
            self._ensure_accounts_exist()
            data = config_mgr.getConfig(key) or {}

        accounts = {}
        for name, account_data in data.items():
            if not isinstance(account_data, dict):
                continue
            instance = dict_to_dataclass(self.AccountConfigClass, account_data)
            errors = validate_config(instance)
            if errors:
                self._get_logger().error(
                    f"账户 {name} 配置校验失败: {', '.join(errors)}"
                )
                continue
            accounts[name] = instance

        return accounts

    @accounts.setter
    def accounts(self, value):
        """设置账户配置字典，同时同步写入配置存储"""
        self._accounts_data = value
        if value is not None:
            from dataclasses import asdict

            from ..config import config as config_mgr

            key = f"{self._get_config_key()}.accounts"
            try:
                config_mgr.setConfig(
                    key, {name: asdict(cfg) for name, cfg in value.items()}
                )
            except Exception:
                pass

    @property
    def enabled_accounts(self) -> dict:
        """
        仅返回 enabled=True 的账户

        :return: 启用的账户配置字典
        """
        return {k: v for k, v in self.accounts.items() if v.enabled}

    @property
    def platform(self) -> str:
        """
        获取平台名称

        :return: 平台名称字符串
        """
        return self._platform

    def _get_config_key(self) -> str:
        """
        配置键名（默认用类名，可被子类覆写）

        :return: 配置键名字符串
        """
        return self.__class__.__name__

    def _get_logger(self):
        """获取 logger，兼容 sdk 未注入的场景"""
        if hasattr(self, "logger"):
            return self.logger
        try:
            from ..logger import logger

            return logger
        except ImportError:
            import logging

            return logging.getLogger(self.__class__.__name__)

    def _ensure_config_exists(self):
        """
        确保全局配置模板存在，不存在则生成默认配置

        {!--< internal-use >!--}
        会先行调用 _ensure_i18n_registered() 注册声明的翻译键，
        确保配置描述引用的 i18n 键在生成模板时已可用。
        {!--< /internal-use >!--}
        """
        # 先行注册 i18n 键（在生成配置之前），保证配置描述中的 i18n 键可用
        self._ensure_i18n_registered()

        if self.ConfigClass is None:
            return
        from ..config import config as config_mgr
        from .config_schema import (
            dataclass_to_defaults_dict,
            dataclass_to_toml_with_comments,
        )

        key = self._get_config_key()
        data = config_mgr.getConfig(key)

        if data is None:
            data = dataclass_to_defaults_dict(self.ConfigClass)
            toml_str = dataclass_to_toml_with_comments(self.ConfigClass)
            config_mgr.setConfig(key, data, immediate=True)
            self._get_logger().info(f"已生成 {key} 默认配置模板:\n{toml_str}")

    def _ensure_i18n_registered(self):
        """
        注册 I18nClass 中声明的翻译键到 i18n 系统

        使用适配器配置键名（默认为类名）作为键名前缀和 domain，便于统一卸载。
        方法是幂等的，多次调用不会产生副作用（重复注册会覆盖旧值）。

        {!--< internal-use >!--}
        由 __init__() 在生成配置之前隐式调用。
        {!--< /internal-use >!--}
        """
        if self.I18nClass is None:
            return
        from .i18n_schema import BaseI18n

        if not isinstance(self.I18nClass, type) or not issubclass(self.I18nClass, BaseI18n):
            # 非法声明静默跳过（避免影响适配器初始化流程）
            return

        prefix = f"{self._get_config_key()}."
        domain = self._get_config_key()
        try:
            self.I18nClass.register(prefix=prefix, domain=domain)
        except Exception:
            # i18n 注册失败不应中断适配器初始化
            self._get_logger().debug(
                f"{self.__class__.__name__}.I18nClass.register() 失败",
                exc_info=True,
            )

    def _ensure_event_mixin_registered(self):
        """
        注册 EventMixin 中声明的事件扩展方法

        适配器声明 ``EventMixin`` 时，框架自动将其注册到适配器的平台
        （即 ``self._platform``），而不是通配符。

        {!--< internal-use >!--}
        由 __init__() 隐式调用。
        {!--< /internal-use >!--}
        """
        if self.EventMixin is None:
            return
        if not isinstance(self.EventMixin, type):
            return

        from ..Event import register_event_mixin

        platform = self._platform or "*"
        try:
            register_event_mixin(platform, self.EventMixin)
        except Exception:
            self._get_logger().debug(
                f"{self.__class__.__name__}.EventMixin 注册失败",
                exc_info=True,
            )

    def _ensure_accounts_exist(self):
        """
        确保多账户配置模板存在，不存在则生成默认账户配置

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        if self.AccountConfigClass is None:
            return
        from ..config import config as config_mgr
        from .config_schema import dataclass_to_defaults_dict

        key = f"{self._get_config_key()}.accounts"
        data = config_mgr.getConfig(key)

        if data is None:
            default_account = dataclass_to_defaults_dict(self.AccountConfigClass)
            data = {"default": default_account}
            config_mgr.setConfig(key, data, immediate=True)
            self._get_logger().info(f"已生成 {key} 默认账户配置")

    def _resolve_account(self, account_id: str | None = None) -> tuple:
        """
        解析目标账户

        - account_id 为 None → 返回第一个启用的账户
        - account_id 匹配账户名 → 返回该账户
        - account_id 匹配 bot_id 等字段 → 返回该账户
        - 未找到 → 抛出 ValueError

        匹配字段优先级：账户名 > dataclass 中名为 bot_id 的字段 > 任意 str 类型字段

        :param account_id: 账户标识（账户名、bot_id 等）
        :return: (账户名, 账户配置实例) 元组
        :raises ValueError: 未找到可用账户时抛出
        """
        from dataclasses import fields as dc_fields

        # 单账户适配器（未声明 AccountConfigClass 或未填充 _accounts_data）
        if self._accounts_data is None:
            return None, None

        accounts = self._accounts_data

        if account_id is not None:
            if account_id in accounts:
                return account_id, accounts[account_id]

            for name, cfg in accounts.items():
                if hasattr(cfg, "bot_id") and cfg.bot_id == account_id:
                    return name, cfg

            for name, cfg in accounts.items():
                for f in dc_fields(cfg):
                    if f.name in ("enabled", "name"):
                        continue
                    val = getattr(cfg, f.name)
                    if isinstance(val, str) and val == account_id:
                        return name, cfg

        for name, cfg in accounts.items():
            if cfg.enabled:
                return name, cfg

        raise ValueError(f"未找到可用账户 (account_id={account_id})")

    async def emit_meta(self, detail_type: str, bot_id: str, **extra_info):
        """
        发送 meta 事件的便捷方法

        :param detail_type: "connect" | "disconnect" | "heartbeat"
        :param bot_id: Bot 用户 ID
        :param extra_info: 扩展字段（user_name, nickname, avatar 等）
        """
        if not self._platform:
            raise RuntimeError("平台名未注入，请确保适配器已注册后再使用 emit_meta")

        from ..adapter import adapter

        await adapter.emit(
            {
                "type": "meta",
                "detail_type": detail_type,
                "platform": self._platform,
                "self": {
                    "platform": self._platform,
                    "user_id": str(bot_id),
                    **extra_info,
                },
            }
        )

    def make_response(
        self,
        *,
        status: str = STATUS_OK,
        retcode: int = RETCODE_OK,
        data=None,
        message_id: str = "",
        message: str = "",
        raw=None,
    ) -> dict:
        """
        构造标准化响应

        :param status: 状态码（"ok" | "failed"）
        :param retcode: 返回码
        :param data: 响应数据
        :param message_id: 消息 ID
        :param message: 响应消息
        :param raw: 原始平台响应
        :return: 标准响应字典
        """
        resp = {
            "status": status,
            "retcode": retcode,
            "data": data,
            "message_id": message_id,
            "message": message,
        }
        if self._platform:
            resp[f"{self._platform}_raw"] = raw
        return resp

    def make_error(
        self,
        retcode: int = 34000,
        message: str = "",
        raw=None,
    ) -> dict:
        """
        构造错误响应

        :param retcode: 错误码
        :param message: 错误消息
        :param raw: 原始平台响应
        :return: 标准错误响应字典
        """
        return self.make_response(
            status="failed",
            retcode=retcode,
            message=message,
            raw=raw,
        )

    def on_config_update(self, old_config, new_config):  # noqa: B027
        """
        配置变更回调（可选实现）

        子类可覆写此方法以响应配置热更新。默认实现为空操作。

        :param old_config: 变更前的配置实例
        :param new_config: 变更后的配置实例
        """
        ...

    async def emit(self, *args, **kwargs):
        raise NotImplementedError(
            "适配器的 emit 方法已被弃用。请使用 adapter.emit() 通过 AdapterManager 提交事件。"
            "如果你是适配器开发者，请查看 ErisPulse 文档进行更新。"
        )

    def send(
        self, target_type: str, target_id: str, message: Any, **kwargs: Any
    ) -> asyncio.Task:
        """
        发送消息的便捷方法，返回一个 asyncio Task

        :param target_type: 目标类型
        :param target_id: 目标ID
        :param message: 消息内容
        :param kwargs: 其他参数
            - method: 发送方法名(默认为"Text")
        :return: asyncio.Task 对象，用户可以自主决定是否等待

        :raises AttributeError: 当发送方法不存在时抛出

        :example:
        >>> task = adapter.send("user", "123", "Hello")
        >>> # 用户可以选择等待: result = await task
        >>> # 或者不等待让其在后台执行
        >>> await adapter.send("group", "456", "Hello", method="Markdown")  # 直接等待
        """

        async def _send_wrapper():
            method_name = kwargs.pop("method", DEFAULT_SEND_METHOD)
            method = getattr(self.Send.To(target_type, target_id), method_name, None)  # pyright: ignore[reportArgumentType]
            if not method:
                raise AttributeError(
                    f"未找到 {method_name} 方法，请确保已在 Send 类中定义"
                )
            return await method(message, **kwargs)

        try:
            return asyncio.create_task(_send_wrapper())
        except RuntimeError:
            return asyncio.ensure_future(_send_wrapper())


__all__ = [
    "ApiDSL",
    "BaseAdapter",
    "RequestDSL",
    "SendDSL",
]
