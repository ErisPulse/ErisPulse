"""
ErisPulse 多轮对话上下文模块

提供 Conversation（多轮对话原语与检查点持久化）、消息事务（_MessageTx）
与对话恢复工厂注册表；由 ``ErisPulse.Core.Event.wrapper`` re-export，
既有导入路径（``ErisPulse.Core.Event.wrapper.Conversation`` 等）不变。

{!--< tips >!--}
1. 通过 event.conversation() 方法创建对话上下文
2. 支持 say/wait/confirm/choose/collect 等对话原语与 branch/goto 分支跳转
3. 分支跳转自动保存检查点，重启后可 save()/resume() 或自动恢复
{!--< /tips >!--}
"""

import asyncio
import inspect
import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Optional

from .. import adapter, logger
from ..constants import (
    CONVERSATION_CHECKPOINT_GC_INTERVAL_SECS,
    CONVERSATION_KEY_PREFIX,
    DEFAULT_INTERACTION_CHECKPOINT_TTL_SECS,
    DEFAULT_SEND_METHOD,
    DEFAULT_WAIT_TIMEOUT_SECS,
)
from ..i18n import i18n

if TYPE_CHECKING:
    from .wrapper import Event

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

        # 首条消息到达时惰性启动过期检查点周期清理（一次性，失败静默）
        _start_checkpoint_gc()

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

    @classmethod
    async def _gc_expired_checkpoints(cls) -> int:
        """
        {!--< internal-use >!--}
        主动清理过期对话检查点（周期任务调用）

        枚举 `conversation:` 前缀的全部存储键，按 `saved_at` 与
        `ErisPulse.interaction.checkpoint_ttl` 判定过期并删除——补全
        "仅在 resume 时惰性清理"的缺口，长期未恢复的存档不再永久驻留。

        :return: 清理的存档数量
        """
        from ..storage import storage

        cutoff = time.time() - cls._checkpoint_ttl()
        prefix = CONVERSATION_KEY_PREFIX + ":"
        removed = 0
        try:
            keys = await storage.aget_all_keys()
        except Exception:
            return 0
        for key in keys:
            if not str(key).startswith(prefix):
                continue
            try:
                data = await storage.aget(key)
                saved_at = data.get("saved_at") if isinstance(data, dict) else None
                if isinstance(saved_at, (int, float)) and saved_at < cutoff:
                    if await storage.adelete(key):
                        removed += 1
            except Exception:
                continue
        if removed:
            logger.info(i18n.t("core.event.conversation_checkpoint_gc", removed=removed))
        return removed


# ==================== 检查点主动 GC 周期任务（2.8.3）====================

_checkpoint_gc_started = False


def _start_checkpoint_gc():
    """{!--< internal-use >!--} 惰性启动过期检查点周期清理（仅启动一次，失败静默）"""
    global _checkpoint_gc_started
    if _checkpoint_gc_started:
        return
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return
    _checkpoint_gc_started = True
    task = loop.create_task(_checkpoint_gc_loop())
    task.add_done_callback(_consume_task_exception)


async def _checkpoint_gc_loop():
    """{!--< internal-use >!--} 周期清理循环（CONVERSATION_CHECKPOINT_GC_INTERVAL_SECS 间隔）"""
    while True:
        await asyncio.sleep(CONVERSATION_CHECKPOINT_GC_INTERVAL_SECS)
        try:
            await Conversation._gc_expired_checkpoints()
        except asyncio.CancelledError:
            raise
        except Exception:
            pass
