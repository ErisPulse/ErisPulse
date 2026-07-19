"""
SendDSL 批量构建系统

提供 :class:`SendBuilder`，支持在一条链路中构建多个发送方法，
最后统一执行。规则统一作用于整批（Plan C）：每条发送各自应用
Timeout/Retry（失败继续、重试失败的），整批层面统一 Hook/OnError/OnProgress。

进入方式：``adapter.Send.To("user", "123").Build().Text("...").Image("...")``
执行方式：``await builder.send_all()`` （默认并行，``.Sequential()`` 切换串行）

{!--< tips >!--}
1. Build() 之前的 At/AtAll/Reply/规则会继承到整批
2. 默认并行执行，需要保证消息顺序时调用 .Sequential()
3. 失败的条目会自动重试（沿用 Retry 规则），其他条目继续发送
{!--< /tips >!--}
"""

import asyncio
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .send_rules import _invoke_callback, _is_success

if TYPE_CHECKING:
    from .adapter import SendDSL


@dataclass
class BatchContext:
    """
    批量发送的实时执行上下文

    在批量执行过程中持续更新，并传递给 OnProgress / OnError 回调。

    :ivar task_id: 批次唯一标识
    :ivar total: 批次总条数
    :ivar completed: 已完成条数（成功 + 失败）
    :ivar succeeded: 成功条数
    :ivar failed: 失败条数
    :ivar stage: 批次阶段：
        ``"pending"``（待执行）、``"sending"``（执行中）、
        ``"success"``（全部成功）、``"partial"``（部分成功）、
        ``"failed"``（全部失败）
    :ivar results: 每条结果（按意图顺序），失败的为 None
    :ivar errors: 每条错误（按意图顺序），成功的为 None
    :ivar started_at: 开始时间戳
    :ivar finished_at: 结束时间戳，未结束时为 None
    :ivar extra: 预留扩展字段
    """

    task_id: str
    total: int = 0
    completed: int = 0
    succeeded: int = 0
    failed: int = 0
    stage: str = "pending"
    results: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    started_at: float = field(default_factory=time.monotonic)
    finished_at: float | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def elapsed(self) -> float:
        """已耗时（秒）"""
        end = self.finished_at if self.finished_at is not None else time.monotonic()
        return max(0.0, end - self.started_at)

    def to_dict(self) -> dict[str, Any]:
        """转为可序列化字典（用于日志/上报）"""
        return {
            "task_id": self.task_id,
            "total": self.total,
            "completed": self.completed,
            "succeeded": self.succeeded,
            "failed": self.failed,
            "stage": self.stage,
            "elapsed": self.elapsed,
            "results": self.results,
            "errors": [repr(e) if e is not None else None for e in self.errors],
            "extra": dict(self.extra),
        }


class SendBuilder:
    """
    批量发送构建器

    通过 :meth:`SendDSL.Build` 进入构建模式。在此模式下，发送方法
    （Text/Image 等）不再立即执行，而是累积为发送意图，最后通过
    :meth:`send_all` 统一执行。

    规则统一作用于整批：
    - ``Timeout`` / ``Retry``：应用到每条发送（失败继续，重试失败的）
    - ``Hook``：整批全部成功后触发一次，接收 ``results`` 列表
    - ``OnError``：批次存在失败时触发一次，接收 :class:`BatchContext`
    - ``OnProgress``：每条完成时触发，接收 :class:`BatchContext`

    :example:
    >>> results = await (adapter.Send.To("user", "123")
    ...                  .Build()
    ...                  .Text("第一句")
    ...                  .Image("pic.jpg")
    ...                  .Retry(2)
    ...                  .send_all())
    >>> # results = [Text结果, Image结果]
    """

    def __init__(self, send_dsl: "SendDSL"):
        """
        从 SendDSL 实例构建批量发送器

        :param send_dsl: 进入 Build 前的 SendDSL 实例（继承其上下文与规则）
        """
        self._adapter = send_dsl._adapter
        self._target_type = send_dsl._target_type
        self._target_id = send_dsl._target_id
        self._account_id = send_dsl._account_id
        # 修饰器（作用于整批所有消息）
        self._at_user_ids: list[str] = list(send_dsl._at_user_ids)
        self._reply_message_id: str | None = send_dsl._reply_message_id
        self._at_all: bool = send_dsl._at_all
        # 规则（从 SendDSL 继承，hooks 深拷贝）
        self._rules: dict[str, Any] = dict(send_dsl._rules) if send_dsl._rules else {}
        if self._rules.get("hooks"):
            self._rules["hooks"] = list(self._rules["hooks"])
        # 发送意图队列：[(method_name, args, kwargs), ...]
        self._intents: list[tuple[str, tuple, dict]] = []
        # 执行模式：默认并行
        self._sequential: bool = False
        # 整批延迟
        self._defer: float = float(self._rules.get("defer", 0.0) or 0.0)

    # ==================== 修饰器（作用于整批）====================

    def At(self, user_id: str) -> "SendBuilder":
        """
        @指定用户（作用于整批所有消息）

        :param user_id: 要@的用户ID
        :return: SendBuilder实例自身
        """
        self._at_user_ids.append(user_id)
        return self

    def AtAll(self) -> "SendBuilder":
        """@全体成员（作用于整批所有消息）"""
        self._at_all = True
        return self

    def Reply(self, message_id: str) -> "SendBuilder":
        """
        回复指定消息（作用于整批所有消息）

        :param message_id: 要回复的消息ID
        """
        self._reply_message_id = message_id
        return self

    # ==================== 执行模式 ====================

    def Sequential(self) -> "SendBuilder":
        """
        切换为串行执行（按意图顺序依次发送）

        保证消息到达顺序，但总耗时为各条耗时之和。

        :return: SendBuilder实例自身
        """
        self._sequential = True
        return self

    def Parallel(self) -> "SendBuilder":
        """
        切换为并行执行（默认）

        并发发送所有意图，总耗时约等于最慢的一条。不保证消息到达顺序。

        :return: SendBuilder实例自身
        """
        self._sequential = False
        return self

    # ==================== 批量规则 ====================

    def Retry(self, times: int = 1) -> "SendBuilder":
        """
        设置每条发送的失败重试次数（作用于每条，非整批重试）

        :param times: 重试次数（不含首次），默认 1
        """
        self._rules["retry"] = max(1, int(times) + 1)
        return self

    def Timeout(self, seconds: float) -> "SendBuilder":
        """
        设置每条发送的单次超时时间

        :param seconds: 超时秒数
        """
        self._rules["timeout"] = max(0.0, float(seconds))
        return self

    def Defer(self, seconds: float = 1.0) -> "SendBuilder":
        """
        延迟执行整批发送

        :param seconds: 延迟秒数
        """
        self._defer = max(0.0, float(seconds))
        return self

    def Hook(self, callback: Callable) -> "SendBuilder":
        """
        附加整批成功后的回调

        仅当批次全部成功时触发一次，回调签名为 ``callback(results: list)``。

        :param callback: 回调函数（同步或协程），接收结果列表
        """
        self._rules.setdefault("hooks", []).append(callback)
        return self

    def OnError(self, callback: Callable) -> "SendBuilder":
        """
        设置批次失败回调

        批次存在任意失败条目时触发一次，回调签名为 ``callback(ctx: BatchContext)``。

        :param callback: 回调函数（同步或协程）
        """
        self._rules["on_error"] = callback
        return self

    def OnProgress(self, callback: Callable) -> "SendBuilder":
        """
        设置批次进度回调

        每条意图完成时触发，回调签名为 ``callback(ctx: BatchContext)``。

        :param callback: 回调函数（同步或协程）
        """
        self._rules["on_progress"] = callback
        return self

    # ==================== 捕获发送意图 ====================

    def __getattr__(self, name: str):
        """
        捕获发送方法为意图

        任何非下划线、非已定义方法的属性访问，都会被视为发送方法，
        返回一个函数；调用后把 (方法名, 参数) 存入意图队列，返回 self 以继续链式。
        """
        if name.startswith("_"):
            raise AttributeError(name)
        # 防御：双下划线魔法方法等
        if name == "send_all":
            raise AttributeError(name)

        def _capture(*args, **kwargs):
            self._intents.append((name, args, kwargs))
            return self

        return _capture

    # ==================== 执行 ====================

    def send_all(self) -> asyncio.Task:
        """
        执行整批发送

        根据执行模式（默认并行 / .Sequential() 串行）发送所有意图，
        失败的条目自动重试（沿用 Retry 规则），其他条目继续发送。

        :return: ``asyncio.Task``，await 后返回每条结果的列表（按意图顺序）
        """
        try:
            return asyncio.create_task(self._run())
        except RuntimeError:
            return asyncio.ensure_future(self._run())

    async def _run(self) -> list:
        from .send_rules import apply_send_rules

        total = len(self._intents)
        ctx = BatchContext(
            task_id=uuid.uuid4().hex[:12],
            total=total,
            results=[None] * total,
            errors=[None] * total,
        )
        on_progress = self._rules.get("on_progress")
        on_error = self._rules.get("on_error")
        hooks = self._rules.get("hooks", []) or []
        per_retry = self._rules.get("retry", 1)
        per_timeout = self._rules.get("timeout")

        # 延迟
        if self._defer > 0:
            await asyncio.sleep(self._defer)

        ctx.stage = "sending"
        await _invoke_callback(on_progress, ctx)

        # 整批生命周期事件：message.sending
        await self._emit_lifecycle("message.sending")

        async def _exec_one(idx: int):
            method_name, args, kwargs = self._intents[idx]
            send_inst = self._make_send_instance()
            method = self._resolve_method(send_inst, method_name)
            if method is None:
                err = AttributeError(
                    f"平台 {self._adapter.__class__.__name__} 未实现 {method_name} 发送方法"
                )
                ctx.errors[idx] = err
                ctx.results[idx] = None
                ctx.completed += 1
                ctx.failed += 1
                await _invoke_callback(on_progress, ctx)
                return

            item_rules: dict[str, Any] = {"retry": per_retry}
            if per_timeout:
                item_rules["timeout"] = per_timeout

            send_ctx_meta = {
                "platform": getattr(self._adapter, "_platform", "") or "",
                "method": method_name,
                "detail_type": self._target_type or "",
                "target_id": self._target_id or "",
                "bot_id": self._account_id or "",
            }

            def factory():
                task = method(send_inst, *args, **kwargs)
                if not isinstance(task, asyncio.Task):
                    if asyncio.iscoroutine(task):
                        task = asyncio.ensure_future(task)
                    else:
                        async def _const():
                            return task
                        task = asyncio.ensure_future(_const())
                return task

            try:
                wrapped = apply_send_rules(
                    factory, rules=item_rules, send_ctx=send_ctx_meta
                )
                result = await wrapped
                ctx.results[idx] = result
                if _is_success(result):
                    ctx.succeeded += 1
                else:
                    ctx.failed += 1
                    ctx.errors[idx] = result
            except BaseException as exc:
                ctx.results[idx] = None
                ctx.errors[idx] = exc
                ctx.failed += 1
            ctx.completed += 1
            await _invoke_callback(on_progress, ctx)

        if self._sequential:
            for idx in range(total):
                await _exec_one(idx)
        elif total > 0:
            await asyncio.gather(*[_exec_one(i) for i in range(total)])

        # 结果判定
        if total == 0 or ctx.failed == 0:
            ctx.stage = "success"
        elif ctx.succeeded == 0:
            ctx.stage = "failed"
        else:
            ctx.stage = "partial"
        ctx.finished_at = time.monotonic()

        # 整批生命周期事件：message.sent
        await self._emit_lifecycle("message.sent")

        # 通知最终阶段（success/partial/failed）
        await _invoke_callback(on_progress, ctx)

        # Hook（全部成功）
        if ctx.stage == "success":
            for hook in hooks:
                try:
                    ret = hook(ctx.results)
                    if asyncio.iscoroutine(ret):
                        await ret
                except Exception as exc:
                    from ..logger import logger

                    logger.warning(f"SendBuilder Hook 执行异常: {exc!r}")

        # OnError（存在失败）
        if ctx.failed > 0 and on_error is not None:
            await _invoke_callback(on_error, ctx)

        return ctx.results

    def _make_send_instance(self):
        """
        创建一个带当前 modifiers/target 的 SendDSL 实例（用于调用原始发送方法）

        直接使用适配器实例上当前的 Send 类构造，绕过 __getattribute__ 的包装，
        由本构建器自行管理规则与生命周期。
        """
        # 优先使用适配器实例上的 Send 类（支持实例级覆盖），
        # 回退到类属性（标准嵌套类定义）
        sample = getattr(self._adapter, "Send", None)
        if sample is not None:
            send_cls = sample if isinstance(sample, type) else type(sample)
        else:
            send_cls = self._adapter.__class__.Send
        inst = send_cls(
            self._adapter, self._target_type, self._target_id, self._account_id
        )
        inst._at_user_ids = list(self._at_user_ids)
        inst._at_all = self._at_all
        inst._reply_message_id = self._reply_message_id
        return inst

    def _resolve_method(self, send_inst, method_name: str):
        """
        在 SendDSL 实例的类上解析发送方法（大小写不敏感）

        :return: 未绑定的方法对象，或 None（未找到）
        """
        cls = type(send_inst)
        # 精确匹配优先
        method = getattr(cls, method_name, None)
        if callable(method) and not method_name.startswith("_"):
            return method
        # 大小写不敏感回退
        for attr in dir(cls):
            if attr.startswith("_"):
                continue
            if attr.lower() == method_name.lower():
                candidate = getattr(cls, attr)
                if callable(candidate):
                    return candidate
        return None

    async def _emit_lifecycle(self, event: str) -> None:
        """触发整批的生命周期事件"""
        try:
            from ..lifecycle import lifecycle

            await lifecycle.emit(
                event,
                {
                    "platform": getattr(self._adapter, "_platform", "") or "",
                    "method": "Batch",
                    "detail_type": self._target_type or "",
                    "target_id": self._target_id or "",
                    "bot_id": self._account_id or "",
                },
            )
        except Exception:
            # 生命周期事件失败不应影响批量发送
            pass
