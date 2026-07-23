"""
SendDSL 发送规则系统

为 SendDSL 提供统一的发送规则装饰器（超时/重试/回调/延迟/优先级/进度上下文）。

规则通过链式方法附加到 SendDSL 实例（存储于 ``_rules`` 字典），
最终在发送方法返回 Task 时，由 :func:`apply_send_rules` 统一应用。

设计目标：
1. 对现有适配器零侵入 —— 适配器只需返回 ``asyncio.Task``，规则由框架统一处理
2. 无规则时完全保持原有行为（向后兼容）
3. 规则可叠加、可乱序、可跨 To/Using/Account 传播

{!--< tips >!--}
1. 规则方法（Hook/Retry/Timeout 等）返回 self，必须在发送方法（Text/Image 等）之前调用
2. 规则随 To/Using/Account 创建的新实例传播，避免链式调用中规则丢失
3. SendContext 在规则执行过程中实时更新，供 OnProgress/OnError 回调读取
{!--< /tips >!--}
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

from ..constants import STATUS_OK


@dataclass
class SendContext:
    """
    发送任务的实时执行上下文

    在发送过程中持续更新，并传递给 OnProgress / OnError 回调，
    便于业务层监控发送阶段、重试次数、耗时及介入决策。

    :ivar task_id: 任务唯一标识（自动生成的短 ID）
    :ivar platform: 平台标识
    :ivar method: 发送方法名（如 ``Text``、``Raw_ob12``）
    :ivar target_type: 目标类型（如 ``user``、``group``）
    :ivar target_id: 目标 ID
    :ivar bot_id: 发送账号 ID
    :ivar stage: 当前阶段：
        ``"pending"``（排队中）、``"sending"``（发送中）、
        ``"retrying"``（重试中）、``"success"``（成功）、
        ``"failed"``（失败）、``"timeout"``（超时）、
        ``"cancelled"``（取消）、``"dropped"``（被优先级丢弃）
    :ivar attempt: 当前尝试次数（0 表示首次，N 表示第 N+1 次重试）
    :ivar max_attempts: 最大尝试次数（含首次）
    :ivar started_at: 任务开始时间戳（``time.monotonic()``）
    :ivar finished_at: 任务结束时间戳（``time.monotonic()``），未结束时为 None
    :ivar error: 失败/超时/取消时的异常对象，成功时为 None
    :ivar result: 成功时的发送结果
    :ivar extra: 预留扩展字段
    """

    task_id: str
    platform: str = ""
    method: str = ""
    target_type: str = ""
    target_id: str = ""
    bot_id: str = ""
    stage: str = "pending"
    attempt: int = 0
    max_attempts: int = 1
    started_at: float = field(default_factory=time.monotonic)
    finished_at: float | None = None
    error: BaseException | None = None
    result: Any = None
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def elapsed(self) -> float:
        """
        已耗时（秒）

        :return: 从 started_at 到当前时间（若已结束则为 finished_at）的秒数
        """
        end = self.finished_at if self.finished_at is not None else time.monotonic()
        return max(0.0, end - self.started_at)

    def to_dict(self) -> dict[str, Any]:
        """
        转为可序列化字典（用于日志/上报）

        :return: 包含上下文字段的字典，error 字段被转为字符串
        """
        return {
            "task_id": self.task_id,
            "platform": self.platform,
            "method": self.method,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "bot_id": self.bot_id,
            "stage": self.stage,
            "attempt": self.attempt,
            "max_attempts": self.max_attempts,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "elapsed": self.elapsed,
            "error": repr(self.error) if self.error is not None else None,
            "result": self.result,
            "extra": dict(self.extra),
        }


def _is_success(result: Any) -> bool:
    """
    判断发送结果是否为成功

    约定：标准响应 dict 中 ``status == "ok"`` 视为成功；
    非 dict 结果（无法判断）默认视为成功，避免误触发重试。

    :param result: 发送方法的返回值
    :return: 是否成功
    """
    if isinstance(result, dict):
        return result.get("status") == STATUS_OK
    return True


async def _invoke_callback(callback: Any, ctx: Any) -> None:
    """
    安全调用用户回调（兼容同步/异步），异常被吞掉不影响主流程

    :param callback: 用户回调（同步函数或协程函数）
    :param ctx: 上下文对象（SendContext 或 BatchContext）
    """
    if callback is None:
        return
    try:
        ret = callback(ctx)
        if asyncio.iscoroutine(ret):
            await ret
    except Exception as exc:
        from ..logger import logger

        logger.warning(f"SendDSL 规则回调执行异常: {exc!r}")


def apply_send_rules(
    base_task_factory: Any,
    *,
    rules: dict[str, Any],
    send_ctx: dict[str, Any],
) -> asyncio.Task:
    """
    根据 ``_rules`` 包装一次发送，返回统一处理后的 Task

    该函数：
    1. 构建 SendContext
    2. 处理延迟（Defer）
    3. 处理优先级丢弃（Priority）
    4. 在重试循环中执行 ``base_task_factory``（每次重试重新调用工厂获取新 Task）
    5. 应用超时（Timeout）
    6. 触发 OnProgress / OnError / Hook 回调

    :param base_task_factory: 无参可调用对象，每次调用返回一个新的 ``asyncio.Task``
        （重试时需要重新发起，因此用工厂而非固定 Task）
    :param rules: SendDSL 的 ``_rules`` 字典
    :param send_ctx: 基础发送上下文（platform/method/target_type/target_id/bot_id）
    :return: 统一包装后的 ``asyncio.Task``
    """

    max_attempts = max(1, int(rules.get("retry", 1)))
    timeout = rules.get("timeout")
    defer = rules.get("defer", 0.0) or 0.0
    drop_if_busy = rules.get("drop_if_busy", False)
    priority = rules.get("priority", 0)
    on_progress = rules.get("on_progress")
    on_error = rules.get("on_error")
    hooks = rules.get("hooks", []) or []

    import uuid

    ctx = SendContext(
        task_id=uuid.uuid4().hex[:12],
        platform=send_ctx.get("platform", ""),
        method=send_ctx.get("method", ""),
        target_type=send_ctx.get("detail_type", "") or send_ctx.get("target_type", ""),
        target_id=send_ctx.get("target_id", ""),
        bot_id=send_ctx.get("bot_id", ""),
        max_attempts=max_attempts,
        extra={"priority": priority},
    )

    async def _run():
        ctx.stage = "pending"

        # 优先级丢弃：若启用且当前存在积压，直接放弃本次发送
        if drop_if_busy and _PriorityQueue.is_busy():
            ctx.stage = "dropped"
            ctx.finished_at = time.monotonic()
            await _invoke_callback(on_progress, ctx)
            return {
                "status": "failed",
                "retcode": 10002,
                "data": None,
                "message_id": "",
                "message": "发送因队列积压被丢弃（低优先级）",
            }

        # 延迟发送
        if defer > 0:
            await asyncio.sleep(defer)

        last_result: Any = None

        # 优先级准入（可选）：登记后自动清理
        if drop_if_busy:
            _PriorityQueue.enter(ctx.task_id)

        try:
            for attempt in range(max_attempts):
                ctx.attempt = attempt
                ctx.stage = "retrying" if attempt > 0 else "sending"
                await _invoke_callback(on_progress, ctx)

                try:
                    task = base_task_factory()
                    if timeout and timeout > 0:
                        result = await asyncio.wait_for(asyncio.ensure_future(task), timeout)
                    else:
                        result = await task
                except asyncio.TimeoutError as exc:
                    ctx.stage = "timeout"
                    ctx.error = exc
                    await _invoke_callback(on_progress, ctx)
                    # 超时也尝试重试
                    if attempt + 1 < max_attempts:
                        continue
                    ctx.finished_at = time.monotonic()
                    await _invoke_callback(on_error, ctx)
                    raise
                except asyncio.CancelledError as exc:
                    ctx.stage = "cancelled"
                    ctx.error = exc
                    ctx.finished_at = time.monotonic()
                    await _invoke_callback(on_progress, ctx)
                    await _invoke_callback(on_error, ctx)
                    raise
                except Exception as exc:
                    ctx.stage = "failed"
                    ctx.error = exc
                    await _invoke_callback(on_progress, ctx)
                    if attempt + 1 < max_attempts:
                        continue
                    ctx.finished_at = time.monotonic()
                    await _invoke_callback(on_error, ctx)
                    raise

                # 成功
                last_result = result
                if not _is_success(result):
                    # 业务层返回 failed，触发重试
                    ctx.stage = "failed"
                    ctx.error = None
                    await _invoke_callback(on_progress, ctx)
                    if attempt + 1 < max_attempts:
                        continue
                    # 重试耗尽且仍失败
                    ctx.finished_at = time.monotonic()
                    await _invoke_callback(on_error, ctx)
                    return result

                # 真正成功
                ctx.stage = "success"
                ctx.result = result
                ctx.error = None
                ctx.finished_at = time.monotonic()
                await _invoke_callback(on_progress, ctx)

                # Hook 回调（仅成功时执行）
                for hook in hooks:
                    try:
                        ret = hook(result)
                        if asyncio.iscoroutine(ret):
                            await ret
                    except Exception as exc:
                        from ..logger import logger

                        logger.warning(f"SendDSL Hook 执行异常: {exc!r}")

                return result

            # 理论不可达（循环已覆盖）
            return last_result
        finally:
            if drop_if_busy:
                _PriorityQueue.leave(ctx.task_id)

    try:
        return asyncio.create_task(_run())
    except RuntimeError:
        return asyncio.ensure_future(_run())


class _PriorityQueue:
    """
    优先级丢弃的轻量级并发跟踪器（进程内、非持久化）

    通过统计当前在途发送任务数量判断是否"积压"。
    当 ``drop_if_busy`` 启用且在途任务超过阈值时，新消息直接放弃。

    阈值可通过 ``rules["priority_threshold"]`` 配置（默认 64）。
    """

    _inflight: int = 0
    _threshold: int = 64

    @classmethod
    def is_busy(cls) -> bool:
        """判断当前是否处于积压状态"""
        return cls._inflight >= cls._threshold

    @classmethod
    def enter(cls, task_id: str) -> None:
        """登记一个在途发送任务"""
        cls._inflight += 1

    @classmethod
    def leave(cls, task_id: str) -> None:
        """注销一个在途发送任务"""
        if cls._inflight > 0:
            cls._inflight -= 1

    @classmethod
    def set_threshold(cls, threshold: int) -> None:
        """设置积压阈值"""
        cls._threshold = max(1, int(threshold))

    @classmethod
    def reset(cls) -> None:
        """重置状态（主要用于测试）"""
        cls._inflight = 0


__all__ = [
    "SendContext",
    "apply_send_rules",
]
