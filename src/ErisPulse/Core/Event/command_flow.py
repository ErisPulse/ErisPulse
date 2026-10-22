"""
命令多轮流控语法糖（``.got()`` 链）

在 ``@command`` 装饰器之上提供 NoneBot ``@matcher.got()`` 风格的声明式多轮
对话：入口处理器之后按声明顺序逐步收集值，收集值按参数名注入后续步骤函数。
底层编译到 :class:`Conversation`——每步一个分支，分支跳转自动保存检查点，
重启后经 ``Conversation.try_auto_resume`` 从存档分支继续（恢复工厂由本模块
在装饰期自动注册，owner 归属与卸载注销继承 Conversation 既有机制）。

{!--< tips >!--}
1. ``@command`` 返回 :class:`CommandFlow` 可调用代理（对原函数完全透明）
2. ``@flow.got("名字", prompt=...)`` 声明收集步骤，收集值按参数名注入步骤函数
3. 任一步超时 / 被打断 → 对话终态并清除检查点（与 wait_reply 语义一致）
{!--< /tips >!--}
"""

import inspect
from collections.abc import Callable
from typing import Any

from ..constants import DEFAULT_WAIT_TIMEOUT_SECS
from ..i18n import i18n

# 值类型别名：.got(type=...) 参数名与内建 type 同名（对外 API 名），注解走此别名
# 避免"参数遮蔽内建名"的类型自引用问题
FlowValueType = type

# 流程终态哨兵：_collect_value 返回它表示对话已死（超时/被打断），链条终止
_FLOW_ENDED = object()

# conv.context 中的保留键：收集值袋 / 当前步骤下标 / 流程身份
_CTX_COLLECTED = "__flow_collected__"
_CTX_INDEX = "__flow_index__"
_CTX_FLOW_NAME = "__flow_name__"


class _Step:
    """{!--< internal-use >!--} 单步声明（.got() 的注册期快照）"""

    __slots__ = (
        "cmdpass",
        "handler",
        "max_retries",
        "method",
        "name",
        "pattern",
        "prompt",
        "regex",
        "retry_prompt",
        "session",
        "timeout",
        "type",
        "validator",
    )

    def __init__(
        self,
        name: str,
        prompt: str | None,
        timeout: float,
        type: "FlowValueType | None",
        validator: Callable | None,
        pattern: str | None,
        regex: str | None,
        session: bool,
        cmdpass: bool | None,
        method: str,
        retry_prompt: str | None,
        max_retries: int,
    ):
        self.name = name
        self.prompt = prompt
        self.timeout = timeout
        self.type = type
        self.validator = validator
        self.pattern = pattern
        self.regex = regex
        self.session = session
        self.cmdpass = cmdpass
        self.method = method
        self.retry_prompt = retry_prompt
        self.max_retries = max_retries
        self.handler: Callable | None = None


class CommandFlow:
    """
    命令多轮流控代理（``@command`` 装饰器的返回值）

    对原函数完全透明的可调用代理：调用行为与原处理器一致（命令分发器照常
    执行入口处理器，属性访问 / ``__name__`` / docstring 全部转发），因此存量
    代码零影响。额外提供 :meth:`got` 装饰器声明后续收集步骤——步骤按声明
    顺序执行，收集值（含命令入口参数）按参数名注入步骤函数。

    流程编译到 Conversation：每步一个分支（分支跳转自动存检查点），重启后
    经自动注册的恢复工厂从存档分支继续（用户重新收到当前步骤的提问）。

    :example:
    >>> @command("weather")
    ... async def weather(event):
    ...     pass  # 入口：首个 .got 的 prompt 会自动发送，无需手动提问
    >>> @weather.got("city", prompt="请直接回复城市名")
    ... async def weather_city(event, city: str):
    ...     await event.reply(f"{city}：晴")
    >>> @weather.got("days", prompt="预报几天？", type=int)
    ... async def weather_days(event, city: str, days: int):
    ...     await event.reply(f"{city} 未来 {days} 天……")
    """

    def __init__(self, func: Callable, name: str | None = None):
        object.__setattr__(self, "_flow_func", func)
        object.__setattr__(self, "_flow_name", name or getattr(func, "__name__", None))
        object.__setattr__(self, "_flow_steps", [])
        object.__setattr__(self, "_flow_resume_registered", False)

    # ==================== 代理透明性 ====================

    def __getattr__(self, name: str) -> Any:
        # 属性访问转发到原函数（__name__ / __doc__ / 自定义属性等）
        func = object.__getattribute__(self, "_flow_func")
        return getattr(func, name)

    def __call__(self, *args: Any, **kwargs: Any):
        if not object.__getattribute__(self, "_flow_steps"):
            return self._flow_func(*args, **kwargs)
        return self._run_flow(*args, **kwargs)

    # ==================== 声明 API ====================

    def got(
        self,
        name: str,
        prompt: str | None = None,
        *,
        timeout: float | str = DEFAULT_WAIT_TIMEOUT_SECS,
        type: "FlowValueType | None" = None,
        validator: Callable | None = None,
        pattern: str | None = None,
        regex: str | None = None,
        session: bool = False,
        cmdpass: bool | None = None,
        method: str = "Text",
        retry_prompt: str | None = None,
        max_retries: int = 2,
    ) -> Callable:
        """
        声明一个收集步骤

        步骤按声明顺序执行；收到回复后按 ``type`` / 校验器解析值，解析失败
        自动重发 ``retry_prompt``（默认复用 ``prompt``）直至超过 ``max_retries``。
        任一步超时或被抢断 → 整条流程结束并清除检查点。

        :param name: 收集值名称（注入后续步骤函数的参数名；须在流程内唯一）
        :param prompt: 提示消息（进入该步骤时自动发送）
        :param timeout: 单步等待超时（秒数或 ``"90s"`` / ``"1h30m"`` 时长串）
        :param type: 值类型（``int`` / ``float`` / ``str`` 等；None = 原始文本）
        :param validator: 额外校验器（接收回复 Event，返回真值才接受；与
            ``Event.wait_reply`` 的 validator 语义一致）
        :param pattern: glob 通配符（回复不匹配时继续等待）
        :param regex: 正则（与 pattern 同时给定时须都匹配）
        :param session: 会话级等待（同会话任何人可命中）
        :param cmdpass: 命令放行三态（None = 跟随全局配置）
        :param method: 发送方法（默认 "Text"）
        :param retry_prompt: 解析失败时的重试提示（缺省复用 prompt）
        :param max_retries: 解析失败的最大重试次数
        :return: 原函数（装饰器语义，不改变被装饰对象）
        """

        def decorator(func: Callable) -> Callable:
            steps = object.__getattribute__(self, "_flow_steps")
            if any(step.name == name for step in steps):
                raise ValueError(
                    i18n.t("core.flow.duplicate_step", name=name, flow=self._flow_name)
                )
            step = _Step(
                name=name,
                prompt=prompt,
                timeout=self._parse_timeout(timeout),
                type=type,
                validator=validator,
                pattern=pattern,
                regex=regex,
                session=session,
                cmdpass=cmdpass,
                method="Text" if method is None else method,
                retry_prompt=retry_prompt,
                max_retries=max_retries,
            )
            step.handler = func
            steps.append(step)
            self._ensure_resume_factory()
            return func

        return decorator

    # ==================== 运行时（编译到 Conversation） ====================

    async def _run_flow(self, *args: Any, **kwargs: Any) -> Any:
        from .wrapper import Event

        result = self._flow_func(*args, **kwargs)
        if inspect.isawaitable(result):
            result = await result
        event = args[0] if args else kwargs.get("event")
        if not isinstance(event, Event) or not object.__getattribute__(self, "_flow_steps"):
            return result

        first_timeout = object.__getattribute__(self, "_flow_steps")[0].timeout
        conv = event.conversation(timeout=first_timeout)
        self._mount_branches(conv)
        conv.context[_CTX_COLLECTED] = dict(kwargs)
        conv.context[_CTX_INDEX] = 0
        conv.context[_CTX_FLOW_NAME] = object.__getattribute__(self, "_flow_name")
        conv.start("__flow_step_0", event)
        return result

    def _mount_branches(self, conv: Any) -> None:
        """{!--< internal-use >!--} 把步骤链编译为 Conversation 分支"""
        steps = object.__getattribute__(self, "_flow_steps")
        for index in range(len(steps)):
            conv.branch(f"__flow_step_{index}")(self._make_branch(index))

    def _make_branch(self, index: int) -> Callable:
        async def _branch(conv, event):
            steps = object.__getattribute__(self, "_flow_steps")
            step = steps[index]
            value = await self._collect_value(conv, step, event)
            if value is _FLOW_ENDED:
                return
            collected = conv.context.setdefault(_CTX_COLLECTED, {})
            collected[step.name] = value
            conv.context[_CTX_INDEX] = index + 1

            handler = step.handler
            if handler is not None:
                result = handler(event, **self._bind(handler, collected))
                if inspect.isawaitable(result):
                    await result

            nxt = index + 1
            if nxt < len(steps):
                conv.goto(f"__flow_step_{nxt}", event)
            else:
                conv.stop()  # 流程完成：终态清除检查点

        return _branch

    @staticmethod
    async def _collect_value(conv: Any, step: _Step, event: Any) -> Any:
        """{!--< internal-use >!--} 单步收集（含类型解析与重试）；失败返回 _FLOW_ENDED"""
        prompt = step.prompt
        attempts = 0
        while True:
            reply = await event.wait_reply(
                prompt=prompt,
                timeout=step.timeout,
                validator=step.validator,
                pattern=step.pattern,
                regex=step.regex,
                session=step.session,
                cmdpass=step.cmdpass,
            )
            if reply is None:
                # 超时 / 被打断：对话终态（stop 清除检查点）
                conv.stop()
                return _FLOW_ENDED
            try:
                return CommandFlow._coerce(step, reply)
            except Exception:
                attempts += 1
                if attempts > step.max_retries:
                    conv.stop()
                    return _FLOW_ENDED
                prompt = step.retry_prompt or step.prompt or i18n.t("core.flow.value_invalid")

    @staticmethod
    def _coerce(step: _Step, reply: Any) -> Any:
        """{!--< internal-use >!--} 从回复事件提取文本并按步骤类型解析"""
        get_text = getattr(reply, "get_text", None)
        text = get_text() if callable(get_text) else ""
        if not text:
            text = reply.get("message_text", "") if isinstance(reply, dict) else ""
        if step.type is None or step.type is str:
            return text
        if step.type is int:
            return int(str(text).strip())
        if step.type is float:
            return float(str(text).strip())
        return step.type(text)

    @staticmethod
    def _bind(handler: Callable, collected: dict[str, Any]) -> dict[str, Any]:
        """{!--< internal-use >!--} 收集值按参数名注入步骤函数（只传声明了的参数）"""
        try:
            params = inspect.signature(handler).parameters
        except (TypeError, ValueError):
            return {}
        kwargs: dict[str, Any] = {}
        for name, param in params.items():
            if name == "event" or name.startswith("_"):
                continue
            if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
                continue
            if name in collected:
                kwargs[name] = collected[name]
        return kwargs

    @staticmethod
    def _parse_timeout(timeout: "float | str") -> float:
        if isinstance(timeout, (int, float)):
            return float(timeout)
        from .command_args import parse_duration

        return parse_duration(str(timeout))

    # ==================== 重启自动恢复 ====================

    def _ensure_resume_factory(self) -> None:
        """{!--< internal-use >!--} 注册恢复工厂（幂等；装饰期调用，owner 归属当场捕获）"""
        if object.__getattribute__(self, "_flow_resume_registered"):
            return
        object.__setattr__(self, "_flow_resume_registered", True)
        from .conversation import Conversation

        Conversation.register_resume_handler()(self._resume_factory)

    def _resume_factory(self, event: Any) -> Any:
        """
        {!--< internal-use >!--}
        恢复工厂：检查点属于本流程时重建对话（重挂分支），否则返回 None 交给下一个工厂
        """
        from .conversation import Conversation

        try:
            from ..storage import storage

            data = storage.get(Conversation._checkpoint_key(event))
        except Exception:
            return None
        if not isinstance(data, dict) or not data.get("alive", False):
            return None
        context = data.get("context") or {}
        if context.get(_CTX_FLOW_NAME) != object.__getattribute__(self, "_flow_name"):
            return None

        conv = event.conversation(timeout=DEFAULT_WAIT_TIMEOUT_SECS)
        self._mount_branches(conv)
        return conv
