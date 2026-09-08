"""
ErisPulse 交互会话管理

提供跨模块的交互会话（等待回复 / 会话租约）统一管理：

- **等待回复**：``command.wait_reply`` / ``Conversation`` 等交互式方法的底层等待表，
  按 ``platform:bot:user:target`` 会话键索引，支持 pattern / regex / validator 过滤；
- **归属维度**：每条等待记录注册时的 owner（模块名），模块卸载 / 适配器关闭时
  按维度精确取消挂起的等待，等待方立即收到 :class:`InteractionCancelled` 而非干等超时；
- **权限复查**：回复命中时复查 scope 身份维度（用户被拉黑）与模块维度
  （owner 模块在该会话被解绑），任一失败终止会话；
- **会话互斥**：``acquire()`` 声明对某会话的独占租约，其他模块的 ``acquire``
  与 ``wait_reply`` 可据此感知"该用户正被谁占用"。

{!--< tips >!--}
使用方式::

    from ErisPulse.Core.Event.interaction import interaction

    # 查询会话当前归属（谁正在与该用户交互）
    owner = interaction.get_owner_of(event)

    # 声明会话互斥租约（deny 策略：被占用时返回 None）
    lease = interaction.acquire(event)
    if lease is None:
        ...  # 会话被其他模块占用
    try:
        ...  # 独占交互
    finally:
        lease.release()

    # 上下文管理器形式
    with interaction.hold(event) as lease:
        ...

模块卸载 / 适配器关闭时，框架自动调用 ``cancel_by_owner`` / ``cancel_by_platform``
清理对应挂起会话，无需手动干预。
{!--< /tips >!--}
"""

import asyncio
import time
from typing import TYPE_CHECKING, Any

from ...runtime.context import current_owner
from ..Bases.errors import InteractionError
from ..constants import (
    DEFAULT_INTERACTION_LEASE_TTL_SECS,
    DEFAULT_MAX_SESSION_REMINDERS,
    UNKNOWN_PLATFORM,
)
from ..i18n import i18n
from ..logger import logger
from ..text_match import compile_text_matcher
from .session_type import get_send_type_and_target_id

if TYPE_CHECKING:
    from .wrapper import Event

# 等待条目类别：等待用户回复（future 驱动）与会话租约（TTL 驱动）
_KIND_WAIT = "wait"
_KIND_LEASE = "lease"

# 会话取消原因
REASON_CONFLICT = "conflict"  # 同会话被新的等待/租约取代
REASON_OWNER_UNLOAD = "owner_unload"  # 归属模块卸载
REASON_PLATFORM_STOP = "platform_stop"  # 适配器/平台关闭
REASON_REVOKED = "revoked"  # 权限复查失败（身份被拉黑或模块被解绑）
REASON_CANCELLED = "cancelled"  # 手动取消
REASON_CLEARED = "cleared"  # 全量清理


class InteractionCancelled(InteractionError):
    """
    交互会话被取消

    挂起的 ``wait_reply`` / 租约因非超时原因终止时设置到 future 上，
    等待方可捕获本异常获取原因；上层 ``wait_reply`` 将其转换为返回 None。

    :attribute reason: 取消原因（conflict / owner_unload / platform_stop / revoked / cancelled / cleared）
    :attribute wait_key: 关联的会话键
    """

    def __init__(self, reason: str, wait_key: str = ""):
        self.reason = reason
        self.wait_key = wait_key
        super().__init__(f"{reason}: {wait_key}" if wait_key else reason)


class _Entry:
    """{!--< internal-use >!--} 交互会话条目（等待回复或互斥租约）"""

    __slots__ = (
        "callback",
        "expires_at",
        "future",
        "key",
        "kind",
        "owner",
        "pattern",
        "platform",
        "regex",
        "timestamp",
        "ttl",
        "validator",
    )

    def __init__(self, kind: str, key: str, owner: str | None, platform: str | None):
        self.kind = kind
        self.key = key
        self.owner = owner
        self.platform = platform
        # wait 类别字段
        self.future: asyncio.Future | None = None
        self.callback: Any = None
        self.validator: Any = None
        self.pattern: str | None = None
        self.regex: str | None = None
        # lease 类别字段
        self.ttl: float = 0.0
        self.expires_at: float = 0.0
        # 公共
        self.timestamp: float = 0.0


class InteractionLease:
    """
    会话互斥租约

    由 :meth:`InteractionManager.acquire` 创建，声明对某会话（platform:bot:user:target）
    的独占占用。持有期间其他模块对该会话的 ``acquire`` 返回 None，
    新的 ``wait_reply`` 也会因会话被占用而无法与您的等待混淆（占用不阻断已有等待，
    但会拒绝新的租约竞争者）。

    支持同步上下文管理器用法；租约到期后自动失效（惰性检查），release 可提前释放。
    """

    def __init__(self, manager: "InteractionManager", entry: _Entry):
        self._manager = manager
        self._entry = entry
        self.key = entry.key
        self.owner = entry.owner
        self.expires_at = entry.expires_at

    @property
    def expired(self) -> bool:
        """租约是否已过期"""
        return time.monotonic() > self._entry.expires_at

    def renew(self, ttl: float | None = None) -> bool:
        """
        续租

        :param ttl: 续租时长（秒），None 表示使用原 TTL
        :return: 是否续租成功（会话已被他人抢占时失败）
        """
        return self._manager._renew_lease(self._entry, ttl)

    def release(self) -> bool:
        """
        释放租约

        :return: 是否释放成功（已过期或被抢占时返回 False）
        """
        return self._manager.release(self.key, self.owner)

    def __enter__(self) -> "InteractionLease":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.release()
        return False

    def __repr__(self) -> str:
        return f"<InteractionLease key={self.key!r} owner={self.owner!r} expires_at={self.expires_at:.1f}>"


class Reminder:
    """
    会话定时器句柄（:meth:`InteractionManager.add_reminder` 创建）

    到期自动执行动作；``cancel()`` 可提前手动取消。
    两种语义（由 ``cancellable_by_reply`` 决定）：

    - **remind**（可被回复取消）：用户在该会话回复后自动取消——
      "如果没在时限内回复就提醒"；
    - **escalate**（不被回复取消）：到期必达——"超时升级动作"
      （如通知主人 / 转人工），仅手动 cancel / 模块卸载 / 平台关闭才取消。

    模块卸载 / 适配器关闭时其挂起的定时器随归属清理自动取消。
    """

    __slots__ = (
        "_done",
        "_manager",
        "action",
        "cancellable_by_reply",
        "created_at",
        "delay",
        "key",
        "owner",
        "platform",
        "task",
    )

    def __init__(
        self,
        manager: "InteractionManager",
        key: str,
        owner: str | None,
        platform: str | None,
        delay: float,
        action: Any,
        cancellable_by_reply: bool,
    ):
        self._manager = manager
        self.key = key
        self.owner = owner
        self.platform = platform
        self.delay = delay
        self.action = action
        self.cancellable_by_reply = cancellable_by_reply
        self.created_at = time.monotonic()
        self.task: asyncio.Task | None = None
        self._done = False

    @property
    def expired(self) -> bool:
        """定时器是否已终结（到期执行 / 被取消）"""
        return self._done or (self.task is not None and self.task.done())

    def cancel(self) -> bool:
        """
        手动取消定时器

        :return: 是否取消成功（已到期执行过的返回 False）
        """
        return self._manager.cancel_reminder(self)

    def __repr__(self) -> str:
        state = "done" if self.expired else f"fires_in_{self.delay:.0f}s"
        kind = "escalate" if not self.cancellable_by_reply else "remind"
        return f"<Reminder {kind} key={self.key!r} {state}>"


class InteractionManager:
    """
    交互会话管理器

    统一管理等待回复与会话租约，按会话键（platform:bot:user:target）唯一索引，
    并维护 owner（归属模块）与 platform（适配器）两个反向索引，
    支持按维度精确取消挂起会话。
    """

    def __init__(self):
        # 主索引：wait_key -> entry（同键唯一，互斥语义的基础）
        self._entries: dict[str, _Entry] = {}
        # 会话级等待索引：session_key（platform:bot:target）-> entry（任何人可答）
        self._session_entries: dict[str, _Entry] = {}
        # 反向索引：owner -> {wait_key} / platform -> {wait_key}
        self._by_owner: dict[str, set[str]] = {}
        self._by_platform: dict[str, set[str]] = {}
        # 会话定时器：wait_key -> [Reminder]（独立于主索引，不参与互斥冲突）
        self._timers: dict[str, list[Reminder]] = {}
        self._timers_by_owner: dict[str, list[Reminder]] = {}
        self._timers_by_platform: dict[str, list[Reminder]] = {}

    # ==================== 会话键 ====================

    @staticmethod
    def make_key(event: Any) -> str:
        """
        {!--< internal-use >!--}
        从事件推导会话键（platform:bot:user:target）

        与命令等待回复的推导规则一致；事件可能为 Event 包装类或原始 dict。

        :param event: 事件数据（Event 或 dict）
        :return: 会话键字符串
        """
        platform = event.get("platform")
        user_id = event.get("user_id")
        _send_type, target_id = get_send_type_and_target_id(event, platform)
        self_info = event.get("self") or {}
        bot_id = self_info.get("account_id", "") or self_info.get("user_id", "")
        return f"{platform}:{bot_id}:{user_id}:{target_id}"

    @staticmethod
    def make_session_key(event: Any) -> str:
        """
        {!--< internal-use >!--}
        从事件推导会话域键（platform:bot:target，不含 user 维度）

        会话级等待（``wait_reply(scope="session")``）使用此键：
        同一会话（群 / 频道）中任何人的回复均可命中。

        :param event: 事件数据（Event 或 dict）
        :return: 会话域键字符串
        """
        platform = event.get("platform")
        _send_type, target_id = get_send_type_and_target_id(event, platform)
        self_info = event.get("self") or {}
        bot_id = self_info.get("account_id", "") or self_info.get("user_id", "")
        return f"{platform}:{bot_id}:{target_id}"

    # ==================== 索引维护 ====================

    def _index_add(self, entry: _Entry) -> None:
        """{!--< internal-use >!--} 将条目加入反向索引"""
        if entry.owner is not None:
            self._by_owner.setdefault(entry.owner, set()).add(entry.key)
        if entry.platform is not None:
            self._by_platform.setdefault(entry.platform, set()).add(entry.key)

    def _index_remove(self, entry: _Entry) -> None:
        """{!--< internal-use >!--} 将条目从反向索引移除"""
        if entry.owner is not None:
            keys = self._by_owner.get(entry.owner)
            if keys is not None:
                keys.discard(entry.key)
                if not keys:
                    del self._by_owner[entry.owner]
        if entry.platform is not None:
            keys = self._by_platform.get(entry.platform)
            if keys is not None:
                keys.discard(entry.key)
                if not keys:
                    del self._by_platform[entry.platform]

    def _remove(self, key: str) -> _Entry | None:
        """{!--< internal-use >!--} 移除条目并维护索引，返回被移除的条目"""
        entry = self._entries.pop(key, None)
        if entry is None:
            entry = self._session_entries.pop(key, None)
        if entry is not None:
            self._index_remove(entry)
        return entry

    def _find_entry(self, key: str) -> _Entry | None:
        """{!--< internal-use >!--} 按键查找条目（主索引与会话级索引均查）"""
        return self._entries.get(key) or self._session_entries.get(key)

    # ==================== 等待回复 ====================

    def register(
        self,
        event: Any,
        future: asyncio.Future,
        callback: Any = None,
        validator: Any = None,
        pattern: str | None = None,
        regex: str | None = None,
        owner: str | None = None,
        session_scope: bool = False,
    ) -> _Entry:
        """
        {!--< internal-use >!--}
        注册等待回复条目

        同一会话键已有等待时，旧等待被取消（等待方收到
        :class:`InteractionCancelled`（reason="conflict"）），
        修复旧实现中相互覆盖导致旧方干等超时的问题。

        :param event: 触发等待的原始事件
        :param future: 回复到达时 set_result 的 future
        :param callback: 回复回调（由调用方在 wait_reply 中执行）
        :param validator: 回复验证函数，验证失败则继续等待
        :param pattern: glob 文本过滤
        :param regex: 正则文本过滤
        :param owner: 归属者（模块名），None 时从 current_owner 上下文捕获
        :param session_scope: 会话级等待（同会话任何人的回复均可命中，键不含 user 维度）
        :return: 注册的条目（含推导的会话键）
        """
        if session_scope:
            key = self.make_session_key(event)
        else:
            key = self.make_key(event)
        platform = event.get("platform")
        if owner is None:
            owner = current_owner.get()

        # 同键旧等待/租约：显式取消而非静默覆盖
        old = self._entries.get(key) or self._session_entries.get(key)
        if old is not None:
            self._cancel_entry(key, old, REASON_CONFLICT)

        entry = _Entry(_KIND_WAIT, key, owner, platform)
        entry.future = future
        entry.callback = callback
        entry.validator = validator
        entry.pattern = pattern
        entry.regex = regex
        entry.timestamp = time.monotonic()

        if session_scope:
            self._session_entries[key] = entry
        else:
            self._entries[key] = entry
        self._index_add(entry)
        return entry

    async def resolve(self, event: "Event") -> bool:
        """
        {!--< internal-use >!--}
        尝试将消息事件匹配到挂起的等待（回复命中判定链）

        判定链：会话键命中 → pattern/regex 过滤 → validator 校验 →
        权限复查（scope 身份维度 + owner 模块维度）→ 唤醒等待方并认领事件。

        权限复查失败时终止整个等待（等待方收到 InteractionCancelled），
        消息本身不消费、继续走常规处理。

        :param event: 消息事件（Event 包装类）
        :return: 是否命中并消费了等待（True 时事件已被 mark_processed）
        """
        key = self.make_key(event)
        entry = self._entries.get(key)
        if entry is None or entry.kind != _KIND_WAIT or entry.future is None:
            # 会话级等待回退：同会话（群 / 频道）中任何人的回复均可命中
            session_key = self.make_session_key(event)
            s_entry = self._session_entries.get(session_key)
            if s_entry is None or s_entry.kind != _KIND_WAIT or s_entry.future is None:
                return False
            key = session_key
            entry = s_entry

        # pattern（glob）/ regex（正则）过滤：不匹配则继续等待（不消费 future）
        if entry.pattern or entry.regex:
            text_cond = compile_text_matcher(entry.pattern, entry.regex)
            if text_cond is not None and not text_cond(event):
                logger.trace(
                    i18n.t(
                        "core.interaction.reply_not_matched",
                        wait_key=key,
                        user_id=event.get("user_id", ""),
                        platform=event.get("platform", UNKNOWN_PLATFORM),
                    )
                )
                return False

        # validator 校验：失败则继续等待
        validator = entry.validator
        if validator is not None:
            try:
                if not validator(event):
                    logger.trace(
                        i18n.t(
                            "core.interaction.reply_validation_failed",
                            wait_key=key,
                            user_id=event.get("user_id", ""),
                        )
                    )
                    return False
            except Exception as e:
                logger.error(i18n.t("core.interaction.validator_error", error=e))
                return False

        # 权限复查：会话建立后被拉黑 / owner 模块被解绑 → 终止等待
        revoked_reason = self._check_revoked(entry, event)
        if revoked_reason:
            logger.trace(
                i18n.t(
                    "core.interaction.revoked",
                    wait_key=key,
                    reason=revoked_reason,
                    owner=entry.owner or "-",
                )
            )
            self._cancel_entry(key, entry, REASON_REVOKED)
            return False

        # 命中：唤醒等待方并移除条目
        self._remove(key)
        # 会话定时器联动：用户已回复，该会话挂起的 remind 自动取消（escalate 不受影响）
        self._cancel_reminders_for_key(key, only_reply_cancellable=True)
        if not entry.future.done():
            entry.future.set_result(event)

        # 认领事件（claim + 阻断），阻止低优先级处理器再介入
        mark_processed = getattr(event, "mark_processed", None)
        if callable(mark_processed):
            mark_processed()
        return True

    def _check_revoked(self, entry: _Entry, event: "Event") -> str | None:
        """
        {!--< internal-use >!--}
        回复命中的权限复查

        :param entry: 等待条目
        :param event: 回复事件
        :return: 撤销原因描述；通过复查时返回 None
        """
        from ..scope import scope

        platform = str(event.get("platform") or "")
        self_info = event.get("self") or {}
        bot_id = self_info.get("account_id", "") or self_info.get("user_id", "") or None
        user_id = event.get("user_id") or None
        session_id = scope.session_id_from_event(event) or None

        # ② 身份维度：用户 / 会话 / Bot / 适配器被拉黑
        if not scope.is_identity_allowed(platform, bot_id, session_id, user_id):
            return "identity"

        # ① 模块维度：owner 模块在该平台 / Bot / 会话已被解绑
        if entry.owner and not scope.is_allowed(platform, bot_id, entry.owner, session_id):
            return "scope"
        return None

    # ==================== 取消 ====================

    def _cancel_entry(self, key: str, entry: _Entry, reason: str) -> None:
        """{!--< internal-use >!--} 取消条目：移除索引并向等待方投递取消"""
        self._remove(key)
        if entry.kind == _KIND_WAIT and entry.future is not None and not entry.future.done():
            entry.future.set_exception(InteractionCancelled(reason, key))

    def cancel(self, key: str, reason: str = REASON_CANCELLED) -> bool:
        """
        取消指定会话键上的等待 / 租约

        :param key: 会话键（platform:bot:user:target）
        :param reason: 取消原因
        :return: 是否存在并取消了条目
        """
        entry = self._find_entry(key)
        if entry is None:
            return False
        self._cancel_entry(key, entry, reason)
        return True

    def cancel_by_owner(self, owner: str) -> int:
        """
        按归属者取消所有挂起会话（模块卸载链路调用）

        :param owner: 归属者（模块名）
        :return: 取消的会话数量
        """
        keys = list(self._by_owner.get(owner, ()))
        count = 0
        for key in keys:
            entry = self._find_entry(key)
            if entry is not None:
                self._cancel_entry(key, entry, REASON_OWNER_UNLOAD)
                count += 1
        # 归属定时器随卸载清理
        for reminder in list(self._timers_by_owner.get(owner, ())):
            if self.cancel_reminder(reminder):
                count += 1
        if count:
            logger.trace(i18n.t("core.interaction.cancelled_owner", owner=owner, count=count))
        return count

    def cancel_by_platform(self, platform: str) -> int:
        """
        按平台取消所有挂起会话（适配器关闭链路调用）

        :param platform: 平台名称
        :return: 取消的会话数量
        """
        keys = list(self._by_platform.get(platform, ()))
        count = 0
        for key in keys:
            entry = self._find_entry(key)
            if entry is not None:
                self._cancel_entry(key, entry, REASON_PLATFORM_STOP)
                count += 1
        # 归属定时器随平台关闭清理
        for reminder in list(self._timers_by_platform.get(platform, ())):
            if self.cancel_reminder(reminder):
                count += 1
        if count:
            logger.trace(i18n.t("core.interaction.cancelled_platform", platform=platform, count=count))
        return count

    def clear(self) -> int:
        """
        清除所有挂起会话（框架关闭链路调用）

        :return: 清除的会话数量
        """
        count = len(self._entries) + len(self._session_entries)
        for key in list(self._entries.keys()) + list(self._session_entries.keys()):
            entry = self._find_entry(key)
            if entry is not None:
                self._cancel_entry(key, entry, REASON_CLEARED)
        count += self._cancel_all_timers(REASON_CLEARED)
        return count

    # ==================== 会话互斥 ====================

    def _get_active_entry(self, key: str) -> _Entry | None:
        """{!--< internal-use >!--} 获取会话键上的活跃条目（租约惰性过期；含会话级索引）"""
        entry = self._find_entry(key)
        if entry is None:
            return None
        if entry.kind == _KIND_LEASE and time.monotonic() > entry.expires_at:
            logger.trace(i18n.t("core.interaction.lease_expired", wait_key=key, owner=entry.owner or "-"))
            self._remove(key)
            return None
        return entry

    def get_owner_of(self, event: Any) -> str | None:
        """
        查询会话当前归属（谁正在与该用户交互）

        可用于发送前避免打扰正在对话中的用户、或实现跨模块会话协调。

        :param event: 事件数据（Event 或 dict，用于推导会话键）
        :return: 占用者的 owner（模块名）；会话空闲时返回 None

        :example:
        >>> owner = sdk.interaction.get_owner_of(event)
        >>> if owner and owner != "MyModule":
        ...     ...  # 该用户正被其他模块占用
        """
        key = event if isinstance(event, str) else self.make_key(event)
        entry = self._get_active_entry(key)
        return entry.owner if entry else None

    def acquire(
        self,
        event: Any,
        owner: str | None = None,
        ttl: float = DEFAULT_INTERACTION_LEASE_TTL_SECS,
    ) -> InteractionLease | None:
        """
        获取会话互斥租约（deny 策略：被占用时返回 None）

        会话空闲时创建租约；已被等待回复或其他租约占用时返回 None。
        租约到期自动失效（惰性检查），也可显式 ``release()`` / ``renew()``。

        :param event: 事件数据（Event 或 dict，用于推导会话键）
        :param owner: 归属者（模块名），None 时从 current_owner 上下文捕获
        :param ttl: 租约存活时间（秒）
        :return: 租约对象；会话被占用时返回 None

        :example:
        >>> lease = sdk.interaction.acquire(event)
        >>> if lease is None:
        ...     return  # 会话正被其他模块占用
        >>> try:
        ...     ...  # 独占交互
        ... finally:
        ...     lease.release()
        """
        key = self.make_key(event)
        if owner is None:
            owner = current_owner.get()

        existing = self._get_active_entry(key)
        if existing is not None:
            logger.trace(
                i18n.t(
                    "core.interaction.lease_denied",
                    wait_key=key,
                    owner=existing.owner or "-",
                    requester=owner or "-",
                )
            )
            return None

        platform = event.get("platform") if not isinstance(event, str) else None
        entry = _Entry(_KIND_LEASE, key, owner, platform)
        entry.ttl = ttl
        entry.expires_at = time.monotonic() + ttl
        entry.timestamp = entry.expires_at - ttl

        self._entries[key] = entry
        self._index_add(entry)
        return InteractionLease(self, entry)

    def hold(
        self,
        event: Any,
        owner: str | None = None,
        ttl: float = DEFAULT_INTERACTION_LEASE_TTL_SECS,
    ):
        """
        会话互斥租约的上下文管理器形式

        退出时自动释放；获取失败抛出 :class:`SessionOccupiedError`。

        :param event: 事件数据
        :param owner: 归属者（模块名），None 时从 current_owner 上下文捕获
        :param ttl: 租约存活时间（秒）
        :return: 上下文管理器，yield :class:`InteractionLease`
        :raises SessionOccupiedError: 会话已被其他 owner 占用时

        :example:
        >>> with sdk.interaction.hold(event) as lease:
        ...     ...  # 独占交互，退出自动释放
        """
        return _LeaseContext(self, event, owner, ttl)

    def release(self, key: str, owner: str | None = None) -> bool:
        """
        释放指定会话的租约

        仅租约持有者（owner 匹配）可释放；owner 为 None 时仅当租约无归属才可释放。

        :param key: 会话键或事件数据
        :param owner: 请求释放者的 owner
        :return: 是否释放成功
        """
        key = key if isinstance(key, str) else self.make_key(key)
        entry = self._get_active_entry(key)
        if entry is None or entry.kind != _KIND_LEASE:
            return False
        if entry.owner != owner:
            return False
        self._remove(key)
        return True

    def _renew_lease(self, entry: _Entry, ttl: float | None) -> bool:
        """{!--< internal-use >!--} 续租"""
        current = self._get_active_entry(entry.key)
        if current is not entry:
            return False
        entry.ttl = ttl if ttl is not None else (entry.ttl or DEFAULT_INTERACTION_LEASE_TTL_SECS)
        entry.expires_at = time.monotonic() + entry.ttl
        return True

    # ==================== 会话定时器 ====================

    def add_reminder(
        self,
        event: Any,
        delay: float,
        action: Any,
        cancellable_by_reply: bool = True,
        owner: str | None = None,
    ) -> Reminder | None:
        """
        {!--< internal-use >!--}
        注册会话定时器（公开 API 为 ``Event.remind`` / ``Event.escalate``）

        :param event: 事件数据（用于推导会话键）
        :param delay: 延迟秒数
        :param action: 到期执行的异步回调（无参）
        :param cancellable_by_reply: 用户在该会话回复时是否自动取消（remind=True / escalate=False）
        :param owner: 归属者（模块名），None 时从 current_owner 捕获
        :return: 定时器句柄；超过单会话上限时返回 None

        :example:
        >>> reminder = sdk.interaction.add_reminder(event, 300, send_nudge)
        """
        if owner is None:
            owner = current_owner.get()
        key = self.make_key(event)
        platform = event.get("platform") if not isinstance(event, str) else None

        # 单会话活跃 remind 上限（escalate 不占名额——必达语义，随归属清理兜底）
        active = [r for r in self._timers.get(key, ()) if r.cancellable_by_reply and not r.expired]
        if cancellable_by_reply and len(active) >= DEFAULT_MAX_SESSION_REMINDERS:
            logger.trace(
                i18n.t(
                    "core.interaction.reminder_limit_reached",
                    wait_key=key,
                    limit=DEFAULT_MAX_SESSION_REMINDERS,
                )
            )
            return None

        reminder = Reminder(self, key, owner, platform, delay, action, cancellable_by_reply)
        self._timers.setdefault(key, []).append(reminder)
        if owner is not None:
            self._timers_by_owner.setdefault(owner, []).append(reminder)
        if platform:
            self._timers_by_platform.setdefault(platform, []).append(reminder)

        reminder.task = asyncio.get_running_loop().create_task(self._run_reminder(reminder))
        return reminder

    async def _run_reminder(self, reminder: Reminder) -> None:
        """{!--< internal-use >!--} 定时器执行体：到期后移除记录并执行动作（owner 归因到注册者）"""
        try:
            await asyncio.sleep(reminder.delay)
        except asyncio.CancelledError:
            return
        # 到期：从索引移除
        reminder._done = True
        self._remove_timer_refs(reminder)
        token = current_owner.set(reminder.owner)
        try:
            result = reminder.action()
            if asyncio.iscoroutine(result):
                await result
        except Exception as e:
            logger.trace(i18n.t("core.interaction.reminder_action_error", error=e))
        finally:
            current_owner.reset(token)

    def _remove_timer_refs(self, reminder: Reminder) -> None:
        """{!--< internal-use >!--} 从三个定时器索引移除"""
        key_list = self._timers.get(reminder.key)
        if key_list and reminder in key_list:
            key_list.remove(reminder)
            if not key_list:
                self._timers.pop(reminder.key, None)
        if reminder.owner is not None:
            owner_list = self._timers_by_owner.get(reminder.owner)
            if owner_list and reminder in owner_list:
                owner_list.remove(reminder)
                if not owner_list:
                    self._timers_by_owner.pop(reminder.owner, None)
        if reminder.platform:
            plat_list = self._timers_by_platform.get(reminder.platform)
            if plat_list and reminder in plat_list:
                plat_list.remove(reminder)
                if not plat_list:
                    self._timers_by_platform.pop(reminder.platform, None)

    def cancel_reminder(self, reminder: Reminder) -> bool:
        """
        取消定时器（手动 ``Reminder.cancel()`` 的实现）

        :param reminder: 定时器句柄
        :return: 是否取消成功（已到期执行过的返回 False）
        """
        if reminder._done:
            return False
        self._remove_timer_refs(reminder)
        reminder._done = True
        if reminder.task is not None and not reminder.task.done():
            reminder.task.cancel()
        reminder.task = None
        return True

    def _cancel_reminders_for_key(self, key: str, only_reply_cancellable: bool = True) -> int:
        """{!--< internal-use >!--} 取消指定会话键上的定时器（回复命中时调用）"""
        timers = self._timers.get(key)
        if not timers:
            return 0
        count = 0
        for reminder in list(timers):
            if only_reply_cancellable and not reminder.cancellable_by_reply:
                continue
            if self.cancel_reminder(reminder):
                count += 1
        if count:
            logger.trace(i18n.t("core.interaction.reminders_cancelled_by_reply", wait_key=key, count=count))
        return count

    def _cancel_all_timers(self, reason_hint: str) -> int:
        """{!--< internal-use >!--} 取消全部定时器（clear 时调用）"""
        count = 0
        for timers in list(self._timers.values()):
            for reminder in list(timers):
                if self.cancel_reminder(reminder):
                    count += 1
        if count:
            logger.trace(i18n.t("core.interaction.timers_cleared", count=count, reason=reason_hint))
        return count

    # ==================== 诊断 ====================

    def counts(self) -> dict[str, Any]:
        """
        获取挂起会话统计（诊断用）

        :return: 含 waits / leases / timers / owners 计数的字典

        :example:
        >>> sdk.interaction.counts()
        {'waits': 2, 'leases': 1, 'timers': 3, 'owners': {'Chat': 3}}
        """
        waits = sum(
            1
            for e in list(self._entries.values()) + list(self._session_entries.values())
            if e.kind == _KIND_WAIT
        )
        total = len(self._entries) + len(self._session_entries)
        timers = sum(len(v) for v in self._timers.values())
        owners: dict[str, int] = {}
        for entry in list(self._entries.values()) + list(self._session_entries.values()):
            if entry.owner is not None:
                owners[entry.owner] = owners.get(entry.owner, 0) + 1
        for reminder in self._timers_by_owner:
            owners[reminder] = owners.get(reminder, 0) + 1
        return {"waits": waits, "leases": total - waits, "timers": timers, "owners": owners}

    def __repr__(self) -> str:
        return f"<InteractionManager entries={len(self._entries)} owners={len(self._by_owner)}>"


class SessionOccupiedError(InteractionError):
    """会话已被其他模块占用（:meth:`InteractionManager.hold` 获取失败时抛出）"""

    def __init__(self, wait_key: str = "", owner: str | None = None):
        self.wait_key = wait_key
        self.owner = owner
        super().__init__(f"session occupied by {owner!r}: {wait_key}")


class _LeaseContext:
    """{!--< internal-use >!--} hold() 的上下文管理器实现"""

    def __init__(self, manager: InteractionManager, event: Any, owner: str | None, ttl: float):
        self._manager = manager
        self._event = event
        self._owner = owner
        self._ttl = ttl
        self._lease: InteractionLease | None = None

    def __enter__(self) -> InteractionLease:
        lease = self._manager.acquire(self._event, owner=self._owner, ttl=self._ttl)
        if lease is None:
            key = (
                self._event
                if isinstance(self._event, str)
                else self._manager.make_key(self._event)
            )
            raise SessionOccupiedError(key, self._manager.get_owner_of(key))
        self._lease = lease
        return lease

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if self._lease is not None:
            self._lease.release()
            self._lease = None
        return False


interaction: InteractionManager = InteractionManager()

__all__ = [
    "InteractionCancelled",
    "InteractionLease",
    "InteractionManager",
    "REASON_CANCELLED",
    "REASON_CLEARED",
    "REASON_CONFLICT",
    "REASON_OWNER_UNLOAD",
    "REASON_PLATFORM_STOP",
    "REASON_REVOKED",
    "Reminder",
    "SessionOccupiedError",
    "interaction",
]
